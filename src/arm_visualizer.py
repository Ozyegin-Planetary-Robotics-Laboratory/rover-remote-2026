#!/usr/bin/env python3
"""
3D Robotic Arm Visualizer with Live CAN Bus Feedback
=====================================================
Reads motor feedback from candump and displays the 4-DOF arm in real-time 3D.

WORKFLOW:
  1. Start the program — arm shows pointing straight UP (home position)
  2. CAN data streams in — you see raw angles updating in the panel, but the
     3D view stays frozen at straight-up
  3. Press "Calibrate" — current raw angles are captured as the zero reference
  4. Now the 3D view updates LIVE: angle = (raw - offset), arm moves in real-time

Usage:
    python3 arm_visualizer.py                  # Live candump on can1
    python3 arm_visualizer.py --manual         # Manual sliders only (no CAN)
    python3 arm_visualizer.py --channel can0   # Different CAN channel
    python3 arm_visualizer.py --signed         # Signed 16-bit position values
"""

import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import subprocess
import threading
import re
import argparse
import time

# ─── Motor Configuration (from your CAN control code) ──────────────────────
MOTOR_IDS = {
    16: {"name": "DOF1 Base/Yaw",  "short": "Yaw",      "index": 0},  # mv_1
    12: {"name": "DOF2 Shoulder",   "short": "Shoulder",  "index": 1},  # mv_2
    13: {"name": "DOF3 Elbow",      "short": "Elbow",     "index": 2},  # mv_3
    14: {"name": "DOF4 Wrist",      "short": "Wrist",     "index": 3},  # mv_4
}

# Segment lengths in meters (from your commented URDF links)
SEGMENT_LENGTHS = [0.48065, 0.42053, 0.40736]
END_EFFECTOR_LENGTH = 0.15

COLORS = ['#2196F3', '#4CAF50', '#FF9800', '#E91E63']
DOF_NAMES = ["DOF1 — Base Yaw", "DOF2 — Shoulder", "DOF3 — Elbow", "DOF4 — Wrist"]
DOF_CAN_IDS = [16, 12, 13, 14]


class ArmVisualizer:
    def __init__(self, root, can_channel="can1", manual_only=False, signed_pos=False):
        self.root = root
        self.root.title("4-DOF Robotic Arm Visualizer")
        self.root.configure(bg='#1e1e1e')

        self.can_channel = can_channel
        self.manual_only = manual_only

        # ── State ──
        # Raw angles coming directly from CAN (absolute encoder values)
        self.raw_angles = [0.0, 0.0, 0.0, 0.0]
        self.raw_received = [False, False, False, False]

        # Home offsets — set when user presses Calibrate
        self.home_offsets = [0.0, 0.0, 0.0, 0.0]

        # Whether calibration has been done (3D view is frozen until True)
        self.is_calibrated = False

        # Display angles (what the 3D view uses) — stays [0,0,0,0] until calibrated
        self.display_angles = [0.0, 0.0, 0.0, 0.0]

        # Direction multipliers — user can flip per DOF
        self.directions = [1, 1, 1, 1]

        # Options
        self.signed_position = tk.BooleanVar(value=signed_pos)
        self.manual_mode = tk.BooleanVar(value=manual_only)

        # CAN state
        self.candump_process = None
        self.running = True
        self.message_count = 0

        # Lock for thread-safe raw_angles access
        self.lock = threading.Lock()

        self._setup_style()
        self._build_gui()

        if not manual_only:
            self._start_candump()
        else:
            self.status_label.config(text="Manual mode — use sliders", foreground='#FFB74D')

        self._update_loop()

    # ─── Style ──────────────────────────────────────────────────────────
    def _setup_style(self):
        s = ttk.Style()
        s.theme_use('clam')
        s.configure('Dark.TFrame', background='#2d2d2d')
        s.configure('Dark.TLabelframe', background='#2d2d2d', foreground='#e0e0e0')
        s.configure('Dark.TLabelframe.Label', background='#2d2d2d', foreground='#e0e0e0',
                     font=('Segoe UI', 10, 'bold'))
        s.configure('Dark.TLabel', background='#2d2d2d', foreground='#e0e0e0',
                     font=('Consolas', 10))
        s.configure('Dark.TCheckbutton', background='#2d2d2d', foreground='#e0e0e0')
        s.configure('Flip.TButton', font=('Segoe UI', 9))
        s.configure('Status.TLabel', background='#2d2d2d', font=('Consolas', 9))
        s.configure('Cal.TButton', font=('Segoe UI', 11, 'bold'), padding=6)

    # ─── GUI ────────────────────────────────────────────────────────────
    def _build_gui(self):
        main = ttk.Frame(self.root, style='Dark.TFrame')
        main.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # ── Left panel ──
        left = ttk.Frame(main, style='Dark.TFrame', width=340)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=4)
        left.pack_propagate(False)

        # Scrollable area
        canvas_frame = tk.Canvas(left, bg='#2d2d2d', highlightthickness=0)
        scrollbar = ttk.Scrollbar(left, orient=tk.VERTICAL, command=canvas_frame.yview)
        scroll_inner = ttk.Frame(canvas_frame, style='Dark.TFrame')

        scroll_inner.bind("<Configure>",
            lambda e: canvas_frame.configure(scrollregion=canvas_frame.bbox("all")))
        canvas_frame.create_window((0, 0), window=scroll_inner, anchor="nw")
        canvas_frame.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ── CALIBRATE BUTTON (prominent) ──
        cal_frame = ttk.LabelFrame(scroll_inner, text="Calibration",
                                    style='Dark.TLabelframe', padding=8)
        cal_frame.pack(fill=tk.X, pady=(5, 6), padx=4)

        self.cal_status = ttk.Label(cal_frame,
                                     text="⏳ 3D view frozen — press Calibrate when arm is at home",
                                     style='Dark.TLabel', foreground='#FFB74D',
                                     wraplength=280)
        self.cal_status.pack(anchor=tk.W, pady=(0, 6))

        self.cal_button = ttk.Button(cal_frame,
                                      text="⟳ CALIBRATE (set current as straight-up)",
                                      style='Cal.TButton',
                                      command=self._calibrate)
        self.cal_button.pack(fill=tk.X)

        # ── DOF displays ──
        self.raw_labels = []
        self.offset_labels = []
        self.calib_labels = []
        self.eff_labels = []
        self.dir_indicators = []

        for i in range(4):
            f = ttk.LabelFrame(scroll_inner, text=f"{DOF_NAMES[i]}  [CAN ID={DOF_CAN_IDS[i]}]",
                                style='Dark.TLabelframe', padding=5)
            f.pack(fill=tk.X, pady=2, padx=4)

            rl = ttk.Label(f, text="CAN Raw: —", style='Dark.TLabel', foreground='#999')
            rl.pack(anchor=tk.W)
            self.raw_labels.append(rl)

            ol = ttk.Label(f, text="Offset:  —", style='Dark.TLabel', foreground='#888')
            ol.pack(anchor=tk.W)
            self.offset_labels.append(ol)

            cl = ttk.Label(f, text="Calib:   0.0°", style='Dark.TLabel', foreground='#bbb')
            cl.pack(anchor=tk.W)
            self.calib_labels.append(cl)

            el = ttk.Label(f, text="Eff:     0.0°", style='Dark.TLabel', foreground=COLORS[i])
            el.pack(anchor=tk.W)
            self.eff_labels.append(el)

            bf = ttk.Frame(f, style='Dark.TFrame')
            bf.pack(fill=tk.X, pady=(3, 0))

            di = ttk.Label(bf, text="Dir: +1 ▸ normal", style='Dark.TLabel', foreground='#81C784')
            di.pack(side=tk.LEFT)
            self.dir_indicators.append(di)

            ttk.Button(bf, text="⟲ Flip", width=8, style='Flip.TButton',
                       command=lambda idx=i: self._flip_direction(idx)).pack(side=tk.RIGHT)

        # ── Options ──
        opt = ttk.LabelFrame(scroll_inner, text="Options", style='Dark.TLabelframe', padding=5)
        opt.pack(fill=tk.X, pady=4, padx=4)

        ttk.Checkbutton(opt, text="Signed position (two's complement)",
                         variable=self.signed_position,
                         style='Dark.TCheckbutton').pack(anchor=tk.W)

        # ── Manual sliders ──
        sl_frame = ttk.LabelFrame(scroll_inner, text="Manual Override",
                                    style='Dark.TLabelframe', padding=5)
        sl_frame.pack(fill=tk.X, pady=4, padx=4)

        ttk.Checkbutton(sl_frame, text="Enable manual mode",
                         variable=self.manual_mode,
                         style='Dark.TCheckbutton').pack(anchor=tk.W, pady=(0, 4))

        self.sliders = []
        slider_names = ["Yaw", "Shoulder", "Elbow", "Wrist"]
        for i in range(4):
            sf = ttk.Frame(sl_frame, style='Dark.TFrame')
            sf.pack(fill=tk.X, pady=1)
            ttk.Label(sf, text=f"{slider_names[i]}:", style='Dark.TLabel', width=9).pack(side=tk.LEFT)
            s = ttk.Scale(sf, from_=-180, to=180, orient=tk.HORIZONTAL,
                          command=lambda val, idx=i: self._slider_changed(idx, val))
            s.set(0)
            s.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.sliders.append(s)

        # ── Status ──
        self.status_label = ttk.Label(scroll_inner, text="Starting...",
                                       style='Status.TLabel', foreground='#999')
        self.status_label.pack(anchor=tk.W, padx=6, pady=(6, 2))

        self.msg_label = ttk.Label(scroll_inner, text="Messages: 0",
                                    style='Status.TLabel', foreground='#666')
        self.msg_label.pack(anchor=tk.W, padx=6)

        # ── Right panel: 3D Plot ──
        self.fig = plt.Figure(figsize=(8, 7), dpi=100, facecolor='#1e1e1e')
        self.ax = self.fig.add_subplot(111, projection='3d', facecolor='#252525')
        self.fig.subplots_adjust(left=0, right=1, top=0.95, bottom=0.02)

        self.canvas = FigureCanvasTkAgg(self.fig, master=main)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    # ─── Calibration ────────────────────────────────────────────────────
    def _calibrate(self):
        """Snapshot current raw angles as the home (straight-up) reference."""
        with self.lock:
            missing = [str(i+1) for i in range(4) if not self.raw_received[i]]

        if missing and not self.manual_mode.get():
            self.cal_status.config(
                text=f"⚠ No CAN data yet for DOF {', '.join(missing)}. Move arm or check CAN.",
                foreground='#EF5350')
            return

        with self.lock:
            for i in range(4):
                self.home_offsets[i] = self.raw_angles[i]

        self.is_calibrated = True
        self.cal_status.config(
            text="✓ Calibrated! 3D view is now LIVE.",
            foreground='#81C784')
        self.cal_button.config(text="⟳ Re-calibrate (reset home to current)")

    # ─── Direction Flip ─────────────────────────────────────────────────
    def _flip_direction(self, idx):
        self.directions[idx] *= -1
        di = self.dir_indicators[idx]
        if self.directions[idx] == 1:
            di.config(text="Dir: +1 ▸ normal", foreground='#81C784')
        else:
            di.config(text="Dir: −1 ▸ reversed", foreground='#EF5350')

    def _slider_changed(self, idx, val):
        if self.manual_mode.get():
            self.display_angles[idx] = float(val)

    # ─── Forward Kinematics ─────────────────────────────────────────────
    def _compute_arm_points(self):
        """
        Home = straight up along +Y. Returns [(x,y,z), ...] for each joint.
        DOF1 = yaw around Y.  DOF2,3,4 = pitch joints (tilt from vertical).
        """
        a = [np.radians(self.display_angles[i] * self.directions[i]) for i in range(4)]
        yaw = a[0]

        points = [(0.0, 0.0, 0.0)]
        cumulative_pitch = 0.0
        x, y, z = 0.0, 0.0, 0.0

        lengths = SEGMENT_LENGTHS + [END_EFFECTOR_LENGTH]

        for i in range(len(lengths)):
            if i < 3:
                cumulative_pitch += a[i + 1]

            L = lengths[i]
            dy = L * np.cos(cumulative_pitch)
            horiz = L * np.sin(cumulative_pitch)
            dx = horiz * np.sin(yaw)
            dz = horiz * np.cos(yaw)

            x += dx; y += dy; z += dz
            points.append((x, y, z))

        return points

    # ─── Main Update Loop ───────────────────────────────────────────────
    def _update_loop(self):
        if not self.running:
            return

        # ── Compute display angles ──
        if self.manual_mode.get():
            pass  # display_angles set by sliders directly
        elif self.is_calibrated:
            with self.lock:
                for i in range(4):
                    self.display_angles[i] = self.raw_angles[i] - self.home_offsets[i]
        # else: display_angles stays [0,0,0,0] → arm points straight up

        # ── Update labels ──
        with self.lock:
            raw_snap = list(self.raw_angles)
            recv_snap = list(self.raw_received)
        off_snap = list(self.home_offsets)

        for i in range(4):
            if recv_snap[i]:
                self.raw_labels[i].config(text=f"CAN Raw: {raw_snap[i]:>+8.1f}°", foreground='#ccc')
            else:
                self.raw_labels[i].config(text="CAN Raw: —", foreground='#666')

            if self.is_calibrated:
                self.offset_labels[i].config(text=f"Offset:  {off_snap[i]:>+8.1f}°")
                calib = self.display_angles[i]
                eff = calib * self.directions[i]
                self.calib_labels[i].config(text=f"Calib:   {calib:>+8.1f}°")
                self.eff_labels[i].config(text=f"Eff:     {eff:>+8.1f}°")
            else:
                self.offset_labels[i].config(text="Offset:  —")
                self.calib_labels[i].config(text="Calib:   0.0°")
                self.eff_labels[i].config(text="Eff:     0.0°")

        self.msg_label.config(text=f"Messages: {self.message_count}")

        # ── Redraw 3D ──
        self._draw_arm()

        self.root.after(50, self._update_loop)

    # ─── 3D Drawing ─────────────────────────────────────────────────────
    def _draw_arm(self):
        self.ax.clear()

        points = self._compute_arm_points()
        mx = [p[0] for p in points]
        my = [p[2] for p in points]
        mz = [p[1] for p in points]

        for i in range(len(points) - 1):
            lw = 6 if i < 3 else 2.5
            ls = '-' if i < 3 else '--'
            self.ax.plot3D([mx[i], mx[i+1]], [my[i], my[i+1]], [mz[i], mz[i+1]],
                           color=COLORS[min(i, 3)], linewidth=lw, linestyle=ls,
                           solid_capstyle='round')

        for i in range(len(points) - 1):
            sz = 120 if i == 0 else 80
            mk = 's' if i == 0 else 'o'
            self.ax.scatter(mx[i], my[i], mz[i], color=COLORS[min(i, 3)],
                           s=sz, marker=mk, zorder=5, edgecolors='white', linewidths=0.5)

        self.ax.scatter(mx[-1], my[-1], mz[-1], color='#FF1744',
                       s=60, marker='^', zorder=5, edgecolors='white', linewidths=0.5)

        reach = sum(SEGMENT_LENGTHS) + END_EFFECTOR_LENGTH
        g = reach * 0.8
        for v in np.linspace(-g, g, 7):
            self.ax.plot3D([v, v], [-g, g], [0, 0], color='#444', linewidth=0.3, alpha=0.4)
            self.ax.plot3D([-g, g], [v, v], [0, 0], color='#444', linewidth=0.3, alpha=0.4)

        self.ax.plot3D([0, 0], [0, 0], [0, reach * 1.1],
                       color='#555', linewidth=0.5, linestyle=':', alpha=0.5)

        self.ax.quiver(0, g * 0.7, 0, 0, g * 0.2, 0,
                       color='#FF9800', arrow_length_ratio=0.3, linewidth=1.5, alpha=0.7)
        self.ax.text(0, g * 0.95, 0.02, "FRONT", color='#FF9800', fontsize=8, ha='center', alpha=0.7)

        lim = reach * 1.1
        self.ax.set_xlim([-lim, lim])
        self.ax.set_ylim([-lim, lim])
        self.ax.set_zlim([-0.05, lim * 1.3])
        self.ax.set_xlabel('X (m)', color='#888', fontsize=9, labelpad=5)
        self.ax.set_ylabel('Z (m)', color='#888', fontsize=9, labelpad=5)
        self.ax.set_zlabel('Height Y (m)', color='#888', fontsize=9, labelpad=5)
        self.ax.tick_params(colors='#666', labelsize=7)
        for axis in [self.ax.xaxis, self.ax.yaxis, self.ax.zaxis]:
            axis.pane.fill = False
            axis.pane.set_edgecolor('#333')
        self.ax.grid(True, alpha=0.15, color='#666')

        eff = [self.display_angles[i] * self.directions[i] for i in range(4)]
        state = "LIVE" if self.is_calibrated else "FROZEN (calibrate first)"
        title = (f"[{state}]  Yaw:{eff[0]:+.1f}°  Sh:{eff[1]:+.1f}°  "
                 f"El:{eff[2]:+.1f}°  Wr:{eff[3]:+.1f}°")
        self.ax.set_title(title, color='#ccc', fontsize=10, pad=10, fontfamily='monospace')

        ee = points[-1]
        self.ax.text2D(0.02, 0.02,
                       f"EE: ({ee[0]:+.3f}, {ee[1]:+.3f}, {ee[2]:+.3f}) m",
                       transform=self.ax.transAxes, color='#FF1744',
                       fontsize=9, fontfamily='monospace')

        self.canvas.draw_idle()

    # ─── CAN Parsing ────────────────────────────────────────────────────
    def _parse_candump_line(self, line):
        """Parse candump output and update raw_angles (thread-safe)."""
        try:
            line = line.strip()
            if not line:
                return

            match = re.search(
                r'([0-9A-Fa-f]{3,8})\s+\[(\d+)\]\s+((?:[0-9A-Fa-f]{2}\s*)+)',
                line
            )
            if not match:
                return

            arb_id = int(match.group(1), 16)
            data_bytes = [int(b, 16) for b in match.group(3).strip().split()]

            motor_id = arb_id & 0xFF
            if motor_id not in MOTOR_IDS:
                return
            if len(data_bytes) < 2:
                return

            raw_pos = (data_bytes[0] << 8) | data_bytes[1]
            if self.signed_position.get() and raw_pos >= 32768:
                raw_pos -= 65536

            position_deg = raw_pos / 10.0
            dof_index = MOTOR_IDS[motor_id]["index"]

            with self.lock:
                self.raw_angles[dof_index] = position_deg
                self.raw_received[dof_index] = True

            self.message_count += 1

            name = MOTOR_IDS[motor_id]["short"]
            self.root.after(0, lambda n=name, p=position_deg:
                self.status_label.config(text=f"CAN ← {n} = {p:+.1f}°", foreground='#81C784'))

        except Exception:
            pass

    # ─── CAN Reader Thread ──────────────────────────────────────────────
    def _candump_reader(self):
        try:
            self.candump_process = subprocess.Popen(
                ['candump', self.can_channel],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, bufsize=1
            )
            self.root.after(0, lambda: self.status_label.config(
                text=f"candump {self.can_channel} connected ✓", foreground='#81C784'))

            for line in self.candump_process.stdout:
                if not self.running:
                    break
                self._parse_candump_line(line)

            if self.running:
                ret = self.candump_process.wait()
                self.root.after(0, lambda: self.status_label.config(
                    text=f"candump exited ({ret}). Use manual mode.", foreground='#EF5350'))

        except FileNotFoundError:
            self.root.after(0, lambda: self.status_label.config(
                text="candump not found! Install can-utils.", foreground='#EF5350'))
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(
                text=f"CAN error: {str(e)[:50]}", foreground='#EF5350'))

    def _start_candump(self):
        threading.Thread(target=self._candump_reader, daemon=True).start()

    # ─── Cleanup ────────────────────────────────────────────────────────
    def on_close(self):
        self.running = False
        if self.candump_process:
            try:
                self.candump_process.terminate()
            except Exception:
                pass
        plt.close(self.fig)
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser(description="4-DOF Robotic Arm Visualizer")
    parser.add_argument('--channel', default='can1', help='CAN channel (default: can1)')
    parser.add_argument('--manual', action='store_true', help='Start in manual-only mode')
    parser.add_argument('--signed', action='store_true', help='Signed 16-bit positions')
    args = parser.parse_args()

    root = tk.Tk()
    root.geometry("1350x800")
    root.minsize(1000, 650)

    app = ArmVisualizer(root, can_channel=args.channel,
                        manual_only=args.manual, signed_pos=args.signed)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()