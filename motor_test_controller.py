"""
Motor Test Controller - Handles TalonFX motor testing via CANivore
Performs velocity ramp tests with data collection for voltage, current, RPM, and power
"""

import os
import time
import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

# Ensure we are targeting hardware (CTRE uses env var)
os.environ.setdefault("CTR_TARGET", "Hardware")  # CTRE: set CTR_TARGET=Hardware for physical devices

try:
    import phoenix6
    from phoenix6 import hardware, configs, controls, signals, unmanaged, StatusCode
    PHOENIX6_AVAILABLE = True
except ImportError:
    PHOENIX6_AVAILABLE = False
    print("Warning: phoenix6 not available. Motor control will not work.")


@dataclass
class TestDataPoint:
    """Single measurement point during motor test"""
    timestamp: float  # Seconds since test start
    voltage: float  # Volts (motor voltage - PWM output)
    bus_voltage: float  # Volts (supply/bus voltage)
    current: float  # Amps
    rpm: float  # Revolutions per minute
    distance: float  # Distance lifted in inches
    input_power: float  # Watts (V * I)
    output_power: float  # Watts (calculated from weight lift)


@dataclass
class TestResult:
    """Complete test results for weight lift test"""
    motor_id: str
    max_current_limit: float
    weight_lbs: float  # Weight being lifted in pounds
    spool_diameter: float  # Spool diameter in inches
    max_lift_distance: float  # Target lift distance in inches
    distance_lifted: float  # Actual distance lifted in inches
    max_rpm_achieved: float
    test_duration: float  # Seconds
    avg_power: float  # Average power calculated as Work/Time (Watts)
    completed: bool  # True if reached target distance, False if timed out
    data_points: List[TestDataPoint] = field(default_factory=list)
    error_message: Optional[str] = None


class MotorTestController:
    """Controls motor testing via CANivore and TalonFX for weight lift tests"""
    
    # Test configuration constants
    TEST_TIMEOUT = 10.0  # seconds
    SAMPLE_RATE = 100  # Hz (samples per second) - data collection rate
    TALON_CAN_ID = 1  # Default CAN ID for the motor under test
    CANIVORE_NAME = "*"  # "*" = any CANivore on Windows; or set to your CANivore name/serial
    
    # Weight lift test defaults
    DEFAULT_SPOOL_DIAMETER = 2.0  # inches
    DEFAULT_WEIGHT_LBS = 5.0  # pounds
    DEFAULT_MAX_LIFT_DISTANCE = 18.0  # inches
    
    def __init__(self, canivore_name: str = CANIVORE_NAME, talon_can_id: int = TALON_CAN_ID, 
                 gear_ratio: float = 1.0, spool_diameter: float = DEFAULT_SPOOL_DIAMETER,
                 weight_lbs: float = DEFAULT_WEIGHT_LBS, lift_direction_cw: bool = True,
                 max_lift_distance: float = DEFAULT_MAX_LIFT_DISTANCE):
        """Initialize motor test controller for weight lift testing
        
        Args:
            canivore_name: Name of the CANivore device
            talon_can_id: CAN ID of the TalonFX motor controller
            gear_ratio: Gear ratio (motor:spool). E.g., 2.0 means motor spins 2x faster than spool
            spool_diameter: Diameter of the spool in inches
            weight_lbs: Weight to lift in pounds
            lift_direction_cw: True for clockwise (positive), False for counter-clockwise
            max_lift_distance: Maximum distance to lift in inches
        """
        self.canivore_name = canivore_name
        self.talon_can_id = talon_can_id
        self.gear_ratio = gear_ratio
        self.spool_diameter = spool_diameter
        self.weight_lbs = weight_lbs
        self.lift_direction_cw = lift_direction_cw
        self.max_lift_distance = max_lift_distance
        self.talon: Optional['hardware.TalonFX'] = None
        self.is_initialized = False
        self.test_running = False
        self.is_jogging = False
        
        # Status signals
        self.velocity_signal: Optional['signals.StatusSignal'] = None
        self.voltage_signal: Optional['signals.StatusSignal'] = None
        self.bus_voltage_signal: Optional['signals.StatusSignal'] = None
        self.current_signal: Optional['signals.StatusSignal'] = None
        self.position_signal: Optional['signals.StatusSignal'] = None  # For tracking rotations
        
    def check_canivore_available(self) -> bool:
        """Check if CANivore is connected and accessible
        
        Returns:
            True if CANivore is available, False otherwise
        """
        if not PHOENIX6_AVAILABLE:
            return False
        
        try:
            # If we can import phoenix6 and it initializes, CANivore is likely available
            # Just check if we can create a TalonFX instance without exceptions
            test_talon = hardware.TalonFX(self.talon_can_id, self.canivore_name)
            # If we got here, CANivore is available (even if motor isn't responding yet)
            return True
        except Exception as e:
            print(f"CANivore check failed: {e}")
            return False
    
    def initialize(self) -> Tuple[bool, str]:
        """Initialize TalonFX motor controller
        
        Returns:
            Tuple of (success, message)
        """
        if not PHOENIX6_AVAILABLE:
            return False, "phoenix6 library not available"
        
        try:
            # Create TalonFX instance
            self.talon = hardware.TalonFX(self.talon_can_id, self.canivore_name)
            
            # Try to verify the motor is actually responding
            version_signal = self.talon.get_version()
            refresh_status = version_signal.refresh()
            
            # Check if we got a valid firmware version (indicates motor is connected)
            if hasattr(refresh_status, 'status') and refresh_status.status != StatusCode.OK:
                return False, f"Motor not responding on ID {self.talon_can_id}"
            
            # Configure closed-loop velocity PID gains
            # For velocity control, k_v (feedforward) is critical
            slot0 = configs.Slot0Configs()
            slot0.k_p = 0.5   # Proportional gain - increased for faster response
            slot0.k_i = 0.0   # Integral gain - start with 0
            slot0.k_d = 0.0   # Derivative gain - start with 0
            slot0.k_v = 0.12  # Velocity feedforward - critical for reaching target velocity
                              # 12V / 6000 RPM (100 RPS) ≈ 0.12 V per RPS
            self.talon.configurator.apply(slot0)
            
            # Set neutral mode to Brake (motor holds position when not commanded)
            motor_output = configs.MotorOutputConfigs()
            motor_output.neutral_mode = signals.NeutralModeValue.BRAKE
            self.talon.configurator.apply(motor_output)
            
            # Set up status signals for data collection
            self.velocity_signal = self.talon.get_velocity()
            self.voltage_signal = self.talon.get_motor_voltage()
            self.bus_voltage_signal = self.talon.get_supply_voltage()
            self.current_signal = self.talon.get_stator_current()
            self.position_signal = self.talon.get_position()  # For tracking rotations
            
            # Optimize signal update frequencies for our sample rate
            self.velocity_signal.set_update_frequency(self.SAMPLE_RATE)
            self.voltage_signal.set_update_frequency(self.SAMPLE_RATE)
            self.bus_voltage_signal.set_update_frequency(self.SAMPLE_RATE)
            self.current_signal.set_update_frequency(self.SAMPLE_RATE)
            self.position_signal.set_update_frequency(self.SAMPLE_RATE)
            
            self.is_initialized = True
            return True, "TalonFX initialized successfully"
            
        except Exception as e:
            return False, f"Error initializing TalonFX: {str(e)}"
    
    def run_test(self, motor_id: str, max_current: float, 
                 callback=None) -> TestResult:
        """Run weight lift test - lift weight at max current until distance reached
        
        Args:
            motor_id: Identifier for the motor being tested
            max_current: Maximum allowed current in amps
            callback: Optional callback function(data_point) called for each sample
            
        Returns:
            TestResult object with all collected data
        """
        if not self.is_initialized:
            return TestResult(
                motor_id=motor_id,
                max_current_limit=max_current,
                weight_lbs=self.weight_lbs,
                spool_diameter=self.spool_diameter,
                max_lift_distance=self.max_lift_distance,
                distance_lifted=0.0,
                max_rpm_achieved=0.0,
                test_duration=0.0,
                avg_power=0.0,
                completed=False,
                error_message="Controller not initialized"
            )
        
        # Create result object
        result = TestResult(
            motor_id=motor_id,
            max_current_limit=max_current,
            weight_lbs=self.weight_lbs,
            spool_diameter=self.spool_diameter,
            max_lift_distance=self.max_lift_distance,
            distance_lifted=0.0,
            max_rpm_achieved=0.0,
            test_duration=0.0,
            avg_power=0.0,
            completed=False
        )
        
        try:
            # Set current limit for this test using CurrentLimitsConfigs
            current_config = configs.CurrentLimitsConfigs()
            current_config.stator_current_limit_enable = True
            current_config.stator_current_limit = max_current
            self.talon.configurator.apply(current_config)
            
            # Calculate spool circumference in inches
            spool_circumference = math.pi * self.spool_diameter
            
            # Calculate target motor rotations to lift max distance
            # distance = (motor_rotations / gear_ratio) * circumference
            # motor_rotations = distance * gear_ratio / circumference
            target_motor_rotations = (self.max_lift_distance * self.gear_ratio) / spool_circumference
            
            # Get starting position
            start_position = self.position_signal.refresh().value  # rotations
            
            # Create duty cycle control request - apply full voltage in direction based on lift_direction_cw
            # Stator current limit will cap the actual current draw
            duty_cycle = 1.0 if self.lift_direction_cw else -1.0  # 100% duty cycle
            voltage_control = controls.DutyCycleOut(duty_cycle)
            
            # Mark test as running
            self.test_running = True
            
            # Start the test
            start_time = time.time()
            sample_interval = 1.0 / self.SAMPLE_RATE
            next_sample_time = start_time
            
            # Enable the motor controller
            if hasattr(unmanaged, 'feed_enable'):
                unmanaged.feed_enable(0.100)  # 100ms timeout
            
            max_rpm_achieved = 0.0
            sample_count = 0
            current_distance = 0.0
            
            # Timing markers for steady-state power calculation (4" to 12")
            POWER_START_DISTANCE = 4.0  # inches
            POWER_END_DISTANCE = 12.0   # inches
            power_start_time = None
            power_end_time = None
            
            # Constants for power calculation
            # Force (Newtons) = Weight (lbs) × 4.448 N/lb
            weight_newtons = self.weight_lbs * 4.448
            
            while self.test_running:
                current_time = time.time()
                elapsed = current_time - start_time
                
                # Check timeout
                if elapsed >= self.TEST_TIMEOUT:
                    result.error_message = f"Test timed out after {self.TEST_TIMEOUT} seconds"
                    break
                
                # Command motor with full voltage (current limit caps power)
                self.talon.set_control(voltage_control)
                
                # Feed the enable signal
                if hasattr(unmanaged, 'feed_enable'):
                    unmanaged.feed_enable(0.100)
                
                # Sample data at specified rate
                if current_time >= next_sample_time:
                    # Read current values from motor
                    velocity_rps = self.velocity_signal.refresh().value
                    voltage = self.voltage_signal.refresh().value
                    bus_voltage = self.bus_voltage_signal.refresh().value
                    current = self.current_signal.refresh().value
                    position = self.position_signal.refresh().value  # motor rotations
                    
                    # Calculate motor RPM and spool RPM
                    motor_rpm = abs(velocity_rps * 60.0)
                    spool_rpm = motor_rpm / self.gear_ratio
                    max_rpm_achieved = max(max_rpm_achieved, spool_rpm)
                    
                    # Calculate distance lifted
                    # Delta rotations from start (absolute value for direction-independence)
                    motor_rotations_delta = abs(position - start_position)
                    spool_rotations = motor_rotations_delta / self.gear_ratio
                    current_distance = spool_rotations * spool_circumference  # inches
                    
                    # Calculate input power
                    input_power = abs(voltage * current)
                    
                    # Calculate instantaneous mechanical output power
                    # P = Force × velocity = Weight × lift_velocity
                    # lift_velocity (m/s) = spool_rpm / 60 * circumference_meters
                    circumference_meters = spool_circumference * 0.0254  # inches to meters
                    lift_velocity_mps = (spool_rpm / 60.0) * circumference_meters
                    output_power = weight_newtons * lift_velocity_mps  # Watts
                    
                    # Create data point
                    data_point = TestDataPoint(
                        timestamp=elapsed,
                        voltage=voltage,
                        bus_voltage=bus_voltage,
                        current=abs(current),
                        rpm=spool_rpm,
                        distance=current_distance,
                        input_power=input_power,
                        output_power=output_power
                    )
                    
                    result.data_points.append(data_point)
                    sample_count += 1
                    
                    # Call callback if provided (for live updating)
                    # Only update graph every 20 samples to avoid blocking (5 Hz graph updates)
                    if callback and sample_count % 20 == 0:
                        callback(data_point)
                    
                    # Schedule next sample
                    next_sample_time += sample_interval
                    
                    # Check if we've reached target distance
                    if current_distance >= self.max_lift_distance:
                        result.completed = True
                        print(f"Max distance {self.max_lift_distance}\" reached at {elapsed:.2f}s")
                        break
                    
                    # Track timing for power calculation window
                    if power_start_time is None and current_distance >= POWER_START_DISTANCE:
                        power_start_time = elapsed
                        print(f"Power window start at {POWER_START_DISTANCE}\" ({elapsed:.2f}s)")
                    
                    if power_end_time is None and current_distance >= POWER_END_DISTANCE:
                        power_end_time = elapsed
                        print(f"Power window end at {POWER_END_DISTANCE}\" ({elapsed:.2f}s)")
                
                # Small sleep to prevent busy waiting
                time.sleep(0.001)
            
            # Test complete - record results
            end_time = time.time()
            result.test_duration = end_time - start_time
            result.max_rpm_achieved = max_rpm_achieved
            result.distance_lifted = current_distance
            
            # Calculate average power from steady-state window (4" to 12")
            # Work (Joules) = Force (N) × Distance (m)
            if power_start_time is not None and power_end_time is not None:
                power_window_distance = POWER_END_DISTANCE - POWER_START_DISTANCE  # 8 inches
                power_window_time = power_end_time - power_start_time
                distance_meters = power_window_distance * 0.0254  # inches to meters
                work_joules = weight_newtons * distance_meters
                if power_window_time > 0:
                    result.avg_power = work_joules / power_window_time  # Watts
                    print(f"Steady-state power: {result.avg_power:.1f}W (4\"-12\" in {power_window_time:.2f}s)")
            else:
                # Fallback: use total distance/time if we didn't reach the window
                distance_meters = current_distance * 0.0254
                work_joules = weight_newtons * distance_meters
                if result.test_duration > 0:
                    result.avg_power = work_joules / result.test_duration
                print(f"Warning: Did not reach 12\", using total avg power: {result.avg_power:.1f}W")
            
            print(f"Test complete: {current_distance:.2f}\" in {result.test_duration:.2f}s, Avg Power: {result.avg_power:.1f}W")
            
            # Brake the motor
            self._brake_motor()
            
        except Exception as e:
            result.error_message = f"Test error: {str(e)}"
            self._emergency_stop()
        finally:
            self.test_running = False
        
        return result
    def stop_test(self):
        """Stop the currently running test"""
        print("Stop test requested")
        self.test_running = False
    
    def _brake_motor(self):
        """Carefully brake the motor to a stop"""
        if not self.talon:
            return
        
        try:
            # Use velocity control to gradually slow down
            velocity_control = controls.VelocityVoltage(0).with_slot(0)
            
            # Ramp down over ~1 second, but check stop flag frequently
            start_time = time.time()
            while time.time() - start_time < 1.0:
                # Check if we should abort braking
                if not self.test_running:
                    break
                    
                current_velocity = self.velocity_signal.refresh().value
                target_velocity = current_velocity * 0.8  # Slow down by 20% each iteration
                
                if abs(target_velocity) < 0.5:  # Close enough to stopped
                    break
                
                self.talon.set_control(velocity_control.with_velocity(target_velocity))
                
                if hasattr(unmanaged, 'feed_enable'):
                    unmanaged.feed_enable(0.100)
                
                time.sleep(0.05)
            
            # Finally set to neutral/coast
            self.talon.set_control(controls.NeutralOut())
            
        except Exception as e:
            print(f"Error during braking: {e}")
            self._emergency_stop()
    
    def _emergency_stop(self):
        """Emergency stop - immediately disable motor"""
        if self.talon:
            try:
                self.talon.set_control(controls.NeutralOut())
            except:
                pass
    
    def shutdown(self):
        """Clean shutdown of motor controller"""
        self.test_running = False
        self.is_jogging = False
        if self.talon:
            self._emergency_stop()
        self.is_initialized = False
    
    def jog_motor(self, rpm: float):
        """Jog the motor at the specified RPM
        
        Args:
            rpm: Target RPM (positive for forward/up, negative for reverse/down)
        """
        if not self.is_initialized or not self.talon:
            return False
        
        if not PHOENIX6_AVAILABLE:
            return False
        
        try:
            # Convert RPM to rotations per second
            rps = (rpm * self.gear_ratio) / 60.0
            
            # Create velocity control request
            velocity_control = controls.VelocityVoltage(rps).with_slot(0)
            
            # Set jogging state
            self.is_jogging = True
            
            # Command the motor
            self.talon.set_control(velocity_control)
            
            # Feed the enable signal
            if hasattr(unmanaged, 'feed_enable'):
                unmanaged.feed_enable(0.100)
            
            return True
            
        except Exception as e:
            print(f"Error jogging motor: {e}")
            return False
    
    def stop_jog(self):
        """Stop jogging the motor"""
        self.is_jogging = False
        if self.talon:
            try:
                self.talon.set_control(controls.NeutralOut())
            except Exception as e:
                print(f"Error stopping jog: {e}")


# Convenience function for quick testing
def quick_test(max_rpm: float = 1000, max_current: float = 20) -> TestResult:
    """Run a quick test with default settings
    
    Args:
        max_rpm: Target RPM
        max_current: Current limit in amps
        
    Returns:
        TestResult object
    """
    controller = MotorTestController()
    
    success, message = controller.initialize()
    if not success:
        print(f"Initialization failed: {message}")
        return TestResult(
            motor_id="test",
            max_rpm_target=max_rpm,
            max_current_limit=max_current,
            max_rpm_achieved=0.0,
            test_duration=0.0,
            completed=False,
            error_message=message
        )
    
    print(f"Starting test: {max_rpm} RPM, {max_current}A limit")
    result = controller.run_test("test-motor", max_rpm, max_current)
    
    controller.shutdown()
    
    print(f"\nTest complete:")
    print(f"  Duration: {result.test_duration:.2f}s")
    print(f"  Max RPM achieved: {result.max_rpm_achieved:.1f}")
    print(f"  Data points collected: {len(result.data_points)}")
    print(f"  Completed: {result.completed}")
    if result.error_message:
        print(f"  Error: {result.error_message}")
    
    return result


if __name__ == "__main__":
    # Test the controller
    quick_test()
