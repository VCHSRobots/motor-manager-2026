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
    input_power: float  # Watts (V * I)
    output_power: float  # Watts (calculated from acceleration)


@dataclass
class TestResult:
    """Complete test results"""
    motor_id: str
    max_rpm_target: float
    max_current_limit: float
    max_rpm_achieved: float
    test_duration: float  # Seconds
    completed: bool  # True if reached target RPM, False if timed out
    data_points: List[TestDataPoint] = field(default_factory=list)
    error_message: Optional[str] = None


class MotorTestController:
    """Controls motor testing via CANivore and TalonFX"""
    
    # Test configuration constants
    TEST_TIMEOUT = 10.0  # seconds
    SAMPLE_RATE = 100  # Hz (samples per second) - data collection rate
    HOLD_TIME_AT_MAX = 3.0  # seconds to hold at max RPM before shutdown
    TALON_CAN_ID = 1  # Default CAN ID for the motor under test
    CANIVORE_NAME = "*"  # "*" = any CANivore on Windows; or set to your CANivore name/serial
    
    # Flywheel moment of inertia (kg⋅m²)
    # TODO: Measure actual flywheel and update this value
    FLYWHEEL_INERTIA = 0.05  # Default placeholder value
    
    def __init__(self, canivore_name: str = CANIVORE_NAME, talon_can_id: int = TALON_CAN_ID, gear_ratio: float = 1.0):
        """Initialize motor test controller
        
        Args:
            canivore_name: Name of the CANivore device
            talon_can_id: CAN ID of the TalonFX motor controller
            gear_ratio: Gear ratio (motor:flywheel). E.g., 2.0 means motor spins 2x faster than flywheel
        """
        self.canivore_name = canivore_name
        self.talon_can_id = talon_can_id
        self.gear_ratio = gear_ratio
        self.talon: Optional['hardware.TalonFX'] = None
        self.is_initialized = False
        self.test_running = False
        
        # Status signals
        self.velocity_signal: Optional['signals.StatusSignal'] = None
        self.voltage_signal: Optional['signals.StatusSignal'] = None
        self.bus_voltage_signal: Optional['signals.StatusSignal'] = None
        self.current_signal: Optional['signals.StatusSignal'] = None
        
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
            
            # Set up status signals for data collection
            self.velocity_signal = self.talon.get_velocity()
            self.voltage_signal = self.talon.get_motor_voltage()
            self.bus_voltage_signal = self.talon.get_supply_voltage()
            self.current_signal = self.talon.get_stator_current()
            
            # Optimize signal update frequencies for our sample rate
            self.velocity_signal.set_update_frequency(self.SAMPLE_RATE)
            self.voltage_signal.set_update_frequency(self.SAMPLE_RATE)
            self.bus_voltage_signal.set_update_frequency(self.SAMPLE_RATE)
            self.current_signal.set_update_frequency(self.SAMPLE_RATE)
            
            self.is_initialized = True
            return True, "TalonFX initialized successfully"
            
        except Exception as e:
            return False, f"Error initializing TalonFX: {str(e)}"
    
    def run_test(self, motor_id: str, max_rpm: float, max_current: float, 
                 callback=None) -> TestResult:
        """Run motor test with velocity ramp and data collection
        
        Args:
            motor_id: Identifier for the motor being tested
            max_rpm: Target maximum flywheel RPM (motor will spin faster by gear_ratio)
            max_current: Maximum allowed current in amps
            callback: Optional callback function(data_point) called for each sample
            
        Returns:
            TestResult object with all collected data
        """
        if not self.is_initialized:
            return TestResult(
                motor_id=motor_id,
                max_rpm_target=max_rpm,
                max_current_limit=max_current,
                max_rpm_achieved=0.0,
                test_duration=0.0,
                completed=False,
                error_message="Controller not initialized"
            )
        
        # Create result object
        result = TestResult(
            motor_id=motor_id,
            max_rpm_target=max_rpm,
            max_current_limit=max_current,
            max_rpm_achieved=0.0,
            test_duration=0.0,
            completed=False
        )
        
        try:
            # Set current limit for this test using CurrentLimitsConfigs
            current_config = configs.CurrentLimitsConfigs()
            current_config.stator_current_limit_enable = True
            current_config.stator_current_limit = max_current
            self.talon.configurator.apply(current_config)
            
            # Convert flywheel RPM to motor RPM (motor spins faster by gear_ratio)
            motor_max_rpm = max_rpm * self.gear_ratio
            
            # Convert motor RPM to rotations per second for TalonFX
            max_rps = motor_max_rpm / 60.0
            
            # Create velocity control request
            velocity_control = controls.VelocityVoltage(0).with_slot(0)
            
            # Mark test as running
            self.test_running = True
            
            # Start the test
            start_time = time.time()
            sample_interval = 1.0 / self.SAMPLE_RATE
            next_sample_time = start_time
            
            # Previous values for calculating acceleration/output power
            prev_rpm = 0.0
            prev_time = start_time
            
            # Enable the motor controller
            if hasattr(unmanaged, 'feed_enable'):
                unmanaged.feed_enable(0.100)  # 100ms timeout
            
            max_rpm_achieved = 0.0
            sample_count = 0  # Track samples for less frequent graph updates
            max_rpm_reached_time = None  # Track when we reached max RPM
            
            while self.test_running:
                current_time = time.time()
                elapsed = current_time - start_time
                
                # Check timeout
                if elapsed >= self.TEST_TIMEOUT:
                    result.error_message = "Test timed out after 10 seconds"
                    break
                
                # Command motor to target velocity
                self.talon.set_control(velocity_control.with_velocity(max_rps))
                
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
                    
                    # Convert motor RPM to flywheel RPM
                    motor_rpm = velocity_rps * 60.0
                    flywheel_rpm = motor_rpm / self.gear_ratio
                    rpm = flywheel_rpm
                    max_rpm_achieved = max(max_rpm_achieved, rpm)
                    
                    # Calculate input power
                    input_power = voltage * current
                    
                    # Calculate output power using moment of inertia
                    # P = τ × ω = I × α × ω
                    delta_rpm = rpm - prev_rpm
                    delta_time = current_time - prev_time
                    if delta_time > 0:
                        # Angular acceleration in rad/s²
                        omega = rpm * 2 * math.pi / 60.0  # Current angular velocity in rad/s
                        alpha = (delta_rpm / 60.0) * 2 * math.pi / delta_time  # Angular acceleration
                        output_power = self.FLYWHEEL_INERTIA * alpha * omega
                    else:
                        output_power = 0.0
                    
                    # Create data point
                    data_point = TestDataPoint(
                        timestamp=elapsed,
                        voltage=voltage,
                        bus_voltage=bus_voltage,
                        current=current,
                        rpm=rpm,
                        input_power=input_power,
                        output_power=output_power
                    )
                    
                    result.data_points.append(data_point)
                    sample_count += 1
                    
                    # Call callback if provided (for live updating)
                    # Only update graph every 20 samples to avoid blocking (5 Hz graph updates)
                    if callback and sample_count % 20 == 0:
                        callback(data_point)
                    
                    # Update previous values
                    prev_rpm = rpm
                    prev_time = current_time
                    
                    # Schedule next sample
                    next_sample_time += sample_interval
                    
                    # Check if we've reached or exceeded target RPM (flywheel RPM)
                    if rpm >= max_rpm and max_rpm_reached_time is None:
                        # First time reaching/exceeding max RPM - start hold timer (never reset)
                        max_rpm_reached_time = current_time
                        print(f"Max RPM reached at {elapsed:.2f}s, starting {self.HOLD_TIME_AT_MAX}s timer")
                    
                    # Check if hold timer has expired
                    if max_rpm_reached_time is not None:
                        if current_time - max_rpm_reached_time >= self.HOLD_TIME_AT_MAX:
                            # Hold time expired - complete test
                            result.completed = True
                            print(f"Hold timer expired after {self.HOLD_TIME_AT_MAX}s, test complete")
                            break
                
                # Small sleep to prevent busy waiting
                time.sleep(0.001)
            
            # Test complete - record results
            result.test_duration = time.time() - start_time
            result.max_rpm_achieved = max_rpm_achieved
            
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
        if self.talon:
            self._emergency_stop()
        self.is_initialized = False


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
