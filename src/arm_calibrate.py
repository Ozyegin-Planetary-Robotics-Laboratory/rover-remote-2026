"""
arm_calibrate.py  (v3)
========================
Fixes vs v2:
  1. raw_read_position() now uses struct.unpack signed int16 — not inline
     unsigned bit shift. This is why position showed 6416° instead of -137.6°.
  2. Nudge now uses set_velocity_loop for a fixed duration instead of
     set_position_velocity_loop, avoiding the malformed-frame issue with the
     velocity byte bug.  Much simpler and more reliable for calibration.
  3. Position is re-read after every nudge to confirm motion happened.
"""

import sys
import json
import time
import struct
import argparse
import datetime

# ── Change this import to match your filename ─────────────────────────────────
from arm_lib_can import (
    start_bus, stop_bus,
    set_origin_here, set_velocity_loop,
    bus,
)
import arm_lib_can as arm_lib

from arm_config import (
    DOFS,
    motor_to_output,
    output_to_motor,
    validate_dofs,
)

CALIBRATION_FILE = "arm_calibration.json"
READ_RETRIES     = 40
READ_TIMEOUT     = 0.1   # seconds per recv() attempt
NUDGE_SPEED      = 50    # RPM at the motor shaft during jog
NUDGE_DURATION   = 0.6   # seconds of jog per keypress
DEBUG            = False


# ─── CAN read (FIXED: struct signed int16) ────────────────────────────────────

def drain_buffer():
    """Discard all messages currently sitting in the receive buffer."""
    while True:
        msg = arm_lib.bus.recv(timeout=0.0)  # non-blocking
        if msg is None:
            break


def raw_read_position(motor_id: int) -> float | None:
    """
    Scan the CAN bus for a status frame from motor_id.
    Returns position in MOTOR degrees (signed), or None if no response.

    AK60 data layout:
      bytes [0:2]  position  signed int16 big-endian,  unit = 0.1°
      bytes [2:4]  speed     signed int16 big-endian,  unit = 0.1 rpm
      bytes [4:6]  current   unsigned int16 big-endian, unit = 0.01 A
      byte  [6]    temperature °C
      byte  [7]    error code
    """
    # Flush stale buffered messages so we don't read a pre-move position
    drain_buffer()
    # Send a velocity=0 ping to prompt a fresh status broadcast
    set_velocity_loop(motor_id, 0)
    time.sleep(0.05)

    for attempt in range(READ_RETRIES):
        try:
            msg = arm_lib.bus.recv(timeout=READ_TIMEOUT)
            if msg is None:
                if DEBUG:
                    print(f"    [CAN] timeout on attempt {attempt+1}")
                continue

            node_id = msg.arbitration_id & 0xFF

            if DEBUG:
                data_hex = " ".join(f"{b:02X}" for b in msg.data)
                print(f"    [CAN] node={node_id:3d}  data=[{data_hex}]")

            if node_id != motor_id:
                continue

            if len(msg.data) < 8:
                print(f"    ⚠ Short frame from motor {motor_id}")
                continue

            error_code = msg.data[7]
            if error_code != 0:
                print(f"    ⚠ Motor {motor_id} error: {error_code}")
                continue

            # ── SIGNED int16 decode ──────────────────────────────────────
            pos_deg   = struct.unpack(">h", bytes(msg.data[0:2]))[0] / 10.0
            speed_rpm = struct.unpack(">h", bytes(msg.data[2:4]))[0] * 10.0
            cur_amps  = struct.unpack(">H", bytes(msg.data[4:6]))[0] / 100.0
            temp_c    = msg.data[6]

            if DEBUG:
                print(f"    → pos={pos_deg:.1f}°  speed={speed_rpm:.0f}rpm  "
                      f"current={cur_amps:.2f}A  temp={temp_c}°C")

            return pos_deg

        except Exception as e:
            print(f"    ⚠ recv error: {e}")

    return None


# ─── Velocity jog  ────────────────────────────────────────────────────────────

def jog(motor_id: int, direction: float):
    """
    Run the motor at NUDGE_SPEED for NUDGE_DURATION seconds then stop.
    Uses set_velocity_loop — a simple 4-byte frame with no known bugs.
    Reads position before and after so you can see if it moved.
    """
    pos_before = raw_read_position(motor_id)
    if pos_before is None:
        print("    ✗ Could not read position before jog.")
        return

    gear = next(
        cfg["gear"] for cfg in DOFS.values() if cfg["motor_id"] == motor_id
    )
    print(f"    Before: motor={pos_before:.1f}°  "
          f"output={motor_to_output(pos_before, gear):.2f}°")

    speed = NUDGE_SPEED * direction
    print(f"    Jogging at {speed:+.0f} RPM for {NUDGE_DURATION}s ...")
    set_velocity_loop(motor_id, speed)
    time.sleep(NUDGE_DURATION)
    set_velocity_loop(motor_id, 0)
    time.sleep(0.2)

    pos_after = raw_read_position(motor_id)
    if pos_after is None:
        print("    ✗ Could not read position after jog.")
        return

    delta_motor = pos_after - pos_before
    delta_output = motor_to_output(delta_motor, gear)
    print(f"    After:  motor={pos_after:.1f}°  "
          f"output={motor_to_output(pos_after, gear):.2f}°  "
          f"(moved {delta_motor:+.1f}° motor / {delta_output:+.2f}° output)")

    if abs(delta_motor) < 0.5:
        print("    ⚠ Motor did not move.  Check enable pin and motor mode.")


# ─── Calibrate one DOF ────────────────────────────────────────────────────────

def calibrate_dof(dof_name: str, cfg: dict) -> dict | None:
    motor_id = cfg["motor_id"]
    gear     = cfg["gear"]
    label    = cfg["label"]

    if motor_id is None:
        print(f"\n[{dof_name}] Motor ID not set — skipping.\n")
        return None

    print(f"\n{'='*60}")
    print(f"  Calibrating {dof_name} — {label}")
    print(f"  Motor ID: {motor_id}   Gear: {gear}:1")
    print(f"  Output limits: [{cfg['min']}°, {cfg['max']}°]")
    print(f"{'='*60}")
    print(f"  +  or  f  →  jog positive  ({NUDGE_SPEED} RPM × {NUDGE_DURATION}s)")
    print(f"  -  or  b  →  jog negative")
    print(f"  s         →  read position")
    print(f"  0         →  SET ORIGIN HERE")
    print(f"  q         →  skip")
    print()

    print("  Reading initial position ...")
    pos = raw_read_position(motor_id)
    if pos is None:
        print(f"  ✗ No response from motor {motor_id}.")
        print(f"     • Run: candump can1  — do you see node ID {motor_id} in last byte of arb ID?")
        print(f"     • Check motor is powered and in servo mode.")
        choice = input("  Continue anyway? [y/N] > ").strip().lower()
        if choice != "y":
            return None
    else:
        print(f"  motor={pos:.1f}°  output={motor_to_output(pos, gear):.2f}°\n")

    while True:
        cmd = input(f"  [{dof_name}] > ").strip().lower()

        if cmd in ("+", "f"):
            jog(motor_id, +1.0)

        elif cmd in ("-", "b"):
            jog(motor_id, -1.0)

        elif cmd == "s":
            pos = raw_read_position(motor_id)
            if pos is not None:
                print(f"    motor={pos:.1f}°  output={motor_to_output(pos, gear):.2f}°")
            else:
                print("    ✗ No response.")

        elif cmd == "0":
            print(f"    Zeroing motor {motor_id} ...")
            set_origin_here(motor_id)
            time.sleep(0.3)
            pos_after = raw_read_position(motor_id)
            if pos_after is not None:
                print(f"    ✓ Now reads {pos_after:.1f}°  (should be ~0.0°)")
            else:
                print(f"    ⚠ Command sent, could not confirm readback.")

            record = {
                "dof":           dof_name,
                "label":         label,
                "motor_id":      motor_id,
                "gear_ratio":    gear,
                "position_after_zero": pos_after,
                "calibrated_at": datetime.datetime.now().isoformat(),
            }
            input("  Press Enter for next DOF > ")
            return record

        elif cmd == "q":
            print(f"  Skipping {dof_name}.")
            return None

        else:
            print("  Unknown: use +, -, s, 0, q")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    global DEBUG
    parser = argparse.ArgumentParser()
    parser.add_argument("--dof",   choices=list(DOFS.keys()))
    parser.add_argument("--debug", action="store_true")
    args   = parser.parse_args()
    DEBUG  = args.debug

    validate_dofs()

    try:
        with open(CALIBRATION_FILE) as f:
            cal_records = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        cal_records = {}

    print("Starting CAN bus ...")
    start_bus()
    time.sleep(0.5)

    dofs_to_do = {args.dof: DOFS[args.dof]} if args.dof else DOFS

    for dof_name, cfg in dofs_to_do.items():
        record = calibrate_dof(dof_name, cfg)
        if record:
            cal_records[dof_name] = record

    with open(CALIBRATION_FILE, "w") as f:
        json.dump(cal_records, f, indent=2)
    print(f"\nCalibration saved to {CALIBRATION_FILE}")

    stop_bus()
    print("Done.")


if __name__ == "__main__":
    main()