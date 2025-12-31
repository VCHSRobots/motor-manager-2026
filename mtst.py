import os
import time
import threading
import tkinter as tk
from tkinter import ttk

# --- CTRE Phoenix 6 imports ---
from phoenix6 import unmanaged
from phoenix6.hardware import TalonFX
from phoenix6.controls import VelocityVoltage
from phoenix6.configs import Slot0Configs

# -----------------------------
# User settings
# -----------------------------
DEVICE_ID = 1          # Set this to your Talon FX CAN ID
CANBUS = "*"           # "*" = any CANivore on Windows; or set to your CANivore name/serial
MAX_RPM = 6000         # UI slider max
ENABLE_TIMEOUT_S = 0.100   # feed_enable timeout in seconds
CONTROL_HZ = 50            # how often to refresh setControl + feed_enable

# -----------------------------
# Ensure we are targeting hardware (CTRE uses env var)
# -----------------------------
os.environ.setdefault("CTR_TARGET", "Hardware")  # CTRE: set CTR_TARGET=Hardware for physical devices

class TalonFXVelocityController:
    def __init__(self, device_id: int, canbus: str):
        self.talon = TalonFX(device_id, canbus)
        self._running = False
        self._target_rpm = 0.0
        self._lock = threading.Lock()

        # Basic closed-loop slot gains (you MUST tune for your system)
        # Start with something small; you can refine in Tuner X.
        slot0 = Slot0Configs()
        slot0.k_p = 0.10
        slot0.k_i = 0.0
        slot0.k_d = 0.0
        slot0.k_v = 0.0
        self.talon.configurator.apply(slot0)

        # Velocity closed-loop request using Voltage output, Slot 0
        self.request = VelocityVoltage(0).with_slot(0)

        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def set_target_rpm(self, rpm: float):
        with self._lock:
            self._target_rpm = float(rpm)

    def start(self):
        with self._lock:
            self._running = True

    def stop(self):
        with self._lock:
            self._running = False
        # Send zero velocity once immediately
        self._set_velocity_rps(0.0)

    def close(self):
        self._stop_event.set()
        self._thread.join(timeout=1.0)
        self.stop()

    def _set_velocity_rps(self, rps: float):
        # CTRE: velocity closed-loop setpoint is in rotations per second
        self.talon.set_control(self.request.with_velocity(rps))

    def _loop(self):
        dt = 1.0 / CONTROL_HZ
        while not self._stop_event.is_set():
            # CTRE requirement: feed enable periodically in non-FRC apps
            unmanaged.feed_enable(ENABLE_TIMEOUT_S)

            with self._lock:
                running = self._running
                rpm = self._target_rpm

            if running:
                rps = rpm / 60.0
                self._set_velocity_rps(rps)
            else:
                # Keep it explicitly at 0 while stopped
                self._set_velocity_rps(0.0)

            time.sleep(dt)

class App(tk.Tk):
    def __init__(self, ctrl: TalonFXVelocityController):
        super().__init__()
        self.title("Talon FX RPM Controller (Phoenix 6)")
        self.ctrl = ctrl

        self.rpm_var = tk.DoubleVar(value=0.0)
        self.state_var = tk.StringVar(value="STOPPED")

        frm = ttk.Frame(self, padding=12)
        frm.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frm, text="Target RPM").grid(row=0, column=0, sticky="w")
        self.slider = ttk.Scale(
            frm,
            from_=0,
            to=MAX_RPM,
            orient="horizontal",
            variable=self.rpm_var,
            command=self._on_slider,
            length=420,
        )
        self.slider.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(4, 8))

        self.rpm_label = ttk.Label(frm, text="0 RPM")
        self.rpm_label.grid(row=2, column=0, sticky="w")

        ttk.Label(frm, textvariable=self.state_var).grid(row=2, column=2, sticky="e")

        self.start_btn = ttk.Button(frm, text="Start", command=self._start)
        self.start_btn.grid(row=3, column=0, sticky="ew", pady=(10, 0))

        self.stop_btn = ttk.Button(frm, text="Stop", command=self._stop)
        self.stop_btn.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=(10, 0))

        self.quit_btn = ttk.Button(frm, text="Quit", command=self._quit)
        self.quit_btn.grid(row=3, column=2, sticky="ew", padx=(8, 0), pady=(10, 0))

        frm.columnconfigure(0, weight=1)
        frm.columnconfigure(1, weight=1)
        frm.columnconfigure(2, weight=1)

        # periodic UI refresh
        self.after(100, self._ui_tick)

    def _on_slider(self, _evt=None):
        rpm = self.rpm_var.get()
        self.ctrl.set_target_rpm(rpm)
        self.rpm_label.config(text=f"{rpm:0.0f} RPM")

    def _start(self):
        self.ctrl.start()
        self.state_var.set("RUNNING")

    def _stop(self):
        self.ctrl.stop()
        self.state_var.set("STOPPED")

    def _quit(self):
        try:
            self.ctrl.close()
        finally:
            self.destroy()

    def _ui_tick(self):
        # Could add live telemetry here later (measured velocity, current, etc.)
        self.after(100, self._ui_tick)

if __name__ == "__main__":
    # Make sure CTR_TARGET is hardware (CTRE requirement when host supports simulation+hw)
    os.environ["CTR_TARGET"] = "Hardware"

    ctrl = TalonFXVelocityController(DEVICE_ID, CANBUS)
    app = App(ctrl)
    app.mainloop()
