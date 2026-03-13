"""
arm_control_ui.py
=================
PyQt5 GUI for controlling the rover arm via joint-angle sliders.

Install deps if needed:
    pip install PyQt5 python-can

Usage:
    python3 arm_control_ui.py

Features:
  • One slider per DOF, scaled to OUTPUT degree limits.
  • Live position readback display (polls CAN bus in a background thread).
  • "Go" button sends the current slider values simultaneously.
  • "Stop" button sends velocity=0 to all motors (emergency stop).
  • Individual "Zero" buttons per DOF (re-runs set_origin_here for that DOF).
  • Status bar shows fail counter and last error.
  • Slider labels update in real time as you drag.
  • Only sends a command when slider is released (mouse-up) OR Go is pressed,
    so you don't flood the bus while dragging.
"""

import sys
import time
import threading
import json

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QSlider, QPushButton, QGroupBox,
    QStatusBar, QFrame, QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor, QPalette

# ── Arm library and config imports ───────────────────────────────────────────
from arm_lib import (
    start_bus, stop_bus,
    set_position_velocity_loop, set_velocity_loop, set_origin_here,
    can_recive,
)
from arm_config import (
    DOFS,
    DEFAULT_CONTROL_RPM,
    DEFAULT_CONTROL_ACCEL,
    motor_to_output,
    output_to_motor,
    clamp,
    validate_dofs,
)

CALIBRATION_FILE = "arm_calibration.json"
SLIDER_RESOLUTION = 1000   # Internal slider steps (1000 steps per degree range)
POLL_INTERVAL_MS  = 200    # CAN readback poll interval


# ─── Background CAN poller ────────────────────────────────────────────────────

class CANPoller(QObject):
    """Runs in a separate thread, emits position updates to the GUI."""
    position_updated = pyqtSignal(int, float)   # (motor_id, output_degrees)
    error_occurred   = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._running = False

    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            try:
                result = can_recive()
                if result and isinstance(result, tuple):
                    motor_id, motor_pos = result[0], result[1]
                    # Find which DOF this motor belongs to
                    for cfg in DOFS.values():
                        if cfg["motor_id"] == motor_id:
                            output_ang = motor_to_output(motor_pos, cfg["gear"])
                            self.position_updated.emit(motor_id, output_ang)
                            break
            except Exception as e:
                self.error_occurred.emit(str(e))
            time.sleep(POLL_INTERVAL_MS / 1000.0)


# ─── Single DOF control panel ─────────────────────────────────────────────────

class DOFPanel(QGroupBox):
    """
    Widget for one DOF: slider + labels + zero button + readback display.
    """
    command_ready = pyqtSignal(str, float)   # (dof_name, output_degrees)

    def __init__(self, dof_name: str, cfg: dict, parent=None):
        super().__init__(cfg["label"], parent)
        self.dof_name   = dof_name
        self.cfg        = cfg
        self.motor_id   = cfg["motor_id"]
        self.gear       = cfg["gear"]
        self.joint_min  = cfg["min"]
        self.joint_max  = cfg["max"]
        self._build_ui()

    def _build_ui(self):
        layout = QGridLayout()
        self.setLayout(layout)

        # ── Target label ──────────────────────────────────────────────────
        self.target_label = QLabel("Target: 0.0°")
        self.target_label.setFont(QFont("Monospace", 10, QFont.Bold))
        layout.addWidget(self.target_label, 0, 0)

        # ── Readback label ────────────────────────────────────────────────
        self.readback_label = QLabel("Actual: —.—°")
        self.readback_label.setFont(QFont("Monospace", 10))
        self.readback_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.readback_label, 0, 1)

        # ── Motor ID / gear info ──────────────────────────────────────────
        id_str = str(self.motor_id) if self.motor_id is not None else "NOT SET"
        info   = QLabel(f"Motor: {id_str}   Gear: {self.gear}:1   "
                        f"Range: [{self.joint_min}°, {self.joint_max}°]")
        info.setStyleSheet("color: #aaaaaa; font-size: 9px;")
        layout.addWidget(info, 1, 0, 1, 2)

        # ── Slider ────────────────────────────────────────────────────────
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(SLIDER_RESOLUTION)
        self.slider.setValue(self._deg_to_slider(0.0))
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(SLIDER_RESOLUTION // 10)
        self.slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.slider.valueChanged.connect(self._on_slider_change)
        self.slider.sliderReleased.connect(self._on_slider_release)

        # Disable if motor ID not set
        if self.motor_id is None:
            self.slider.setEnabled(False)

        layout.addWidget(self.slider, 2, 0, 1, 2)

        # ── Min / Max labels ──────────────────────────────────────────────
        lim_layout = QHBoxLayout()
        lim_layout.addWidget(QLabel(f"{self.joint_min}°"))
        lim_layout.addStretch()
        lim_layout.addWidget(QLabel("0°"))
        lim_layout.addStretch()
        lim_layout.addWidget(QLabel(f"{self.joint_max}°"))
        layout.addLayout(lim_layout, 3, 0, 1, 2)

        # ── Zero button ───────────────────────────────────────────────────
        self.zero_btn = QPushButton("Set Origin Here")
        self.zero_btn.setToolTip(
            "Calls set_origin_here() — physically bring this joint to its\n"
            "zero reference BEFORE pressing this button!"
        )
        self.zero_btn.setStyleSheet(
            "QPushButton { background-color: #7a3c00; color: white; }"
            "QPushButton:hover { background-color: #b05a00; }"
        )
        self.zero_btn.clicked.connect(self._on_zero)
        if self.motor_id is None:
            self.zero_btn.setEnabled(False)
        layout.addWidget(self.zero_btn, 4, 0)

        # ── Send button (single DOF) ──────────────────────────────────────
        self.send_btn = QPushButton("Send")
        self.send_btn.setStyleSheet(
            "QPushButton { background-color: #1a5276; color: white; }"
            "QPushButton:hover { background-color: #2874a6; }"
        )
        self.send_btn.clicked.connect(self._on_slider_release)
        if self.motor_id is None:
            self.send_btn.setEnabled(False)
        layout.addWidget(self.send_btn, 4, 1)

    # ── Conversion helpers ────────────────────────────────────────────────────

    def _deg_to_slider(self, deg: float) -> int:
        clamped = clamp(deg, self.joint_min, self.joint_max)
        ratio   = (clamped - self.joint_min) / (self.joint_max - self.joint_min)
        return int(ratio * SLIDER_RESOLUTION)

    def _slider_to_deg(self, value: int) -> float:
        ratio = value / SLIDER_RESOLUTION
        return self.joint_min + ratio * (self.joint_max - self.joint_min)

    def get_target_deg(self) -> float:
        return self._slider_to_deg(self.slider.value())

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_slider_change(self, value: int):
        deg = self._slider_to_deg(value)
        self.target_label.setText(f"Target: {deg:+.1f}°")

    def _on_slider_release(self):
        deg = self.get_target_deg()
        self.command_ready.emit(self.dof_name, deg)

    def _on_zero(self):
        if self.motor_id is not None:
            set_origin_here(self.motor_id)
            self.slider.setValue(self._deg_to_slider(0.0))
            self.readback_label.setText("Actual: 0.0° (zeroed)")
            self.readback_label.setStyleSheet("color: #27ae60;")

    # ── Public update ─────────────────────────────────────────────────────────

    def update_readback(self, output_deg: float):
        self.readback_label.setText(f"Actual: {output_deg:+.1f}°")
        # Colour-code: green if close to target, orange if far
        diff = abs(output_deg - self.get_target_deg())
        if diff < 1.0:
            self.readback_label.setStyleSheet("color: #27ae60;")
        elif diff < 5.0:
            self.readback_label.setStyleSheet("color: #f39c12;")
        else:
            self.readback_label.setStyleSheet("color: #e74c3c;")


# ─── Main window ─────────────────────────────────────────────────────────────

class ArmControlWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rover Arm Control")
        self.setMinimumWidth(700)
        self._panels: dict[str, DOFPanel] = {}
        self._build_ui()
        self._start_can()
        self._load_calibration()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # Title
        title = QLabel("🦾  Rover Arm Control")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Calibration info banner
        self.cal_banner = QLabel("⚠ Calibration file not found — zero positions may be wrong!")
        self.cal_banner.setStyleSheet(
            "background-color: #7d6608; color: white; padding: 4px; border-radius: 3px;"
        )
        self.cal_banner.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.cal_banner)

        # DOF panels
        for dof_name, cfg in DOFS.items():
            panel = DOFPanel(dof_name, cfg)
            panel.command_ready.connect(self._send_command)
            self._panels[dof_name] = panel
            main_layout.addWidget(panel)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #555;")
        main_layout.addWidget(sep)

        # Global control buttons
        btn_layout = QHBoxLayout()

        self.go_btn = QPushButton("▶  Send All")
        self.go_btn.setFixedHeight(44)
        self.go_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.go_btn.setStyleSheet(
            "QPushButton { background-color: #1e8449; color: white; border-radius: 4px; }"
            "QPushButton:hover { background-color: #27ae60; }"
        )
        self.go_btn.clicked.connect(self._send_all)
        btn_layout.addWidget(self.go_btn)

        self.stop_btn = QPushButton("⬛  STOP ALL")
        self.stop_btn.setFixedHeight(44)
        self.stop_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.stop_btn.setStyleSheet(
            "QPushButton { background-color: #c0392b; color: white; border-radius: 4px; }"
            "QPushButton:hover { background-color: #e74c3c; }"
        )
        self.stop_btn.clicked.connect(self._stop_all)
        btn_layout.addWidget(self.stop_btn)

        main_layout.addLayout(btn_layout)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready.  CAN bus initialising...")

    # ── CAN setup ────────────────────────────────────────────────────────────

    def _start_can(self):
        try:
            start_bus()
            self.status_bar.showMessage("CAN bus OK.")
        except Exception as e:
            self.status_bar.showMessage(f"CAN bus error: {e}")

        self.poller = CANPoller()
        self.poller.position_updated.connect(self._on_position_update)
        self.poller.error_occurred.connect(
            lambda msg: self.status_bar.showMessage(f"CAN error: {msg}")
        )
        self.poller.start()

    def _load_calibration(self):
        try:
            with open(CALIBRATION_FILE, "r") as f:
                records = json.load(f)
            ts_list = [r.get("calibrated_at", "?") for r in records.values()]
            last_ts = max(ts_list) if ts_list else "?"
            self.cal_banner.setText(f"✓ Calibration loaded  (last: {last_ts})")
            self.cal_banner.setStyleSheet(
                "background-color: #1e8449; color: white; padding: 4px; border-radius: 3px;"
            )
        except (FileNotFoundError, json.JSONDecodeError):
            pass   # Keep the warning banner

    # ── Commands ─────────────────────────────────────────────────────────────

    def _send_command(self, dof_name: str, output_deg: float):
        """Send a position command for a single DOF."""
        cfg      = DOFS[dof_name]
        motor_id = cfg["motor_id"]
        gear     = cfg["gear"]
        if motor_id is None:
            self.status_bar.showMessage(f"{dof_name}: motor ID not set, skipping.")
            return

        motor_pos   = output_to_motor(output_deg, gear)
        motor_rpm   = DEFAULT_CONTROL_RPM   * gear
        motor_accel = DEFAULT_CONTROL_ACCEL * gear

        set_position_velocity_loop(motor_id, motor_pos, motor_rpm, motor_accel)
        self.status_bar.showMessage(
            f"{dof_name} → {output_deg:+.1f}° output  "
            f"({motor_pos:+.0f}° motor  @  {motor_rpm:.0f} RPM)"
        )

    def _send_all(self):
        """Send position commands for all DOFs simultaneously."""
        for dof_name, panel in self._panels.items():
            self._send_command(dof_name, panel.get_target_deg())

    def _stop_all(self):
        """Emergency stop — send velocity=0 to every motor."""
        for cfg in DOFS.values():
            if cfg["motor_id"] is not None:
                set_velocity_loop(cfg["motor_id"], 0)
        self.status_bar.showMessage("⬛  ALL MOTORS STOPPED")

    # ── Readback ─────────────────────────────────────────────────────────────

    def _on_position_update(self, motor_id: int, output_deg: float):
        for dof_name, cfg in DOFS.items():
            if cfg["motor_id"] == motor_id:
                self._panels[dof_name].update_readback(output_deg)
                break

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        self._stop_all()
        self.poller.stop()
        time.sleep(0.3)
        stop_bus()
        event.accept()


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    validate_dofs()
    app = QApplication(sys.argv)

    # Dark theme
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window,          QColor(30,  30,  30))
    palette.setColor(QPalette.WindowText,      QColor(220, 220, 220))
    palette.setColor(QPalette.Base,            QColor(20,  20,  20))
    palette.setColor(QPalette.AlternateBase,   QColor(40,  40,  40))
    palette.setColor(QPalette.ToolTipBase,     QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText,     QColor(0,   0,   0))
    palette.setColor(QPalette.Text,            QColor(220, 220, 220))
    palette.setColor(QPalette.Button,          QColor(50,  50,  50))
    palette.setColor(QPalette.ButtonText,      QColor(220, 220, 220))
    palette.setColor(QPalette.BrightText,      QColor(255, 0,   0))
    palette.setColor(QPalette.Highlight,       QColor(42,  130, 218))
    palette.setColor(QPalette.HighlightedText, QColor(0,   0,   0))
    app.setPalette(palette)

    window = ArmControlWindow()
    window.show()
    sys.exit(app.exec_())
