"""
arm_config.py
=============
Shared configuration for the rover arm.
Motor IDs, gear ratios, joint limits, and calibration helpers.

COORDINATE CONVENTION:
  - All joint angles are in OUTPUT degrees (after the reducer).
  - Motor position = output_angle * gear_ratio  (sent to set_position_loop)
  - Output angle   = motor_position / gear_ratio (read from can_recive)
  - "0°" for every DOF is the calibrated zero set via set_origin_here().

DOF ZERO REFERENCE:
  DOF1 (base yaw)    : facing straight forward from the rover body
  DOF2 (shoulder)    : arm link pointing straight up
  DOF3 (elbow)       : forearm pointing straight up (collinear with DOF2 link)
  DOF4 (wrist)       : wrist link pointing straight up (collinear with DOF3 link)
"""

# ─── Motor IDs on the CAN bus ────────────────────────────────────────────────
# Fill in DOF1_ID once you have confirmed it on the bus.
DOF1_MOTOR_ID = 12
DOF2_MOTOR_ID = 16
DOF3_MOTOR_ID = 13
DOF4_MOTOR_ID = 14

# ─── External reducer gear ratios (output / motor) ──────────────────────────
DOF1_GEAR = 20.0
DOF2_GEAR = 62.0
DOF3_GEAR = 62.0
DOF4_GEAR = 10.5

# ─── Joint limits in OUTPUT degrees ─────────────────────────────────────────
# Positive = forward / down from zero; Negative = backward / up
DOF1_MIN, DOF1_MAX = -135.0, 135.0   # Base yaw
DOF2_MIN, DOF2_MAX =  -15.0,  90.0   # Shoulder  (-15 = slightly past vertical)
DOF3_MIN, DOF3_MAX =  -15.0, 135.0   # Elbow
DOF4_MIN, DOF4_MAX =  -15.0, 110.0   # Wrist

# ─── Convenience structures ───────────────────────────────────────────────────
DOFS = {
    "DOF1": {
        "motor_id": DOF1_MOTOR_ID,
        "gear":     DOF1_GEAR,
        "min":      DOF1_MIN,
        "max":      DOF1_MAX,
        "label":    "Base Yaw",
    },
    "DOF2": {
        "motor_id": DOF2_MOTOR_ID,
        "gear":     DOF2_GEAR,
        "min":      DOF2_MIN,
        "max":      DOF2_MAX,
        "label":    "Shoulder",
    },
    "DOF3": {
        "motor_id": DOF3_MOTOR_ID,
        "gear":     DOF3_GEAR,
        "min":      DOF3_MIN,
        "max":      DOF3_MAX,
        "label":    "Elbow",
    },
    "DOF4": {
        "motor_id": DOF4_MOTOR_ID,
        "gear":     DOF4_GEAR,
        "min":      DOF4_MIN,
        "max":      DOF4_MAX,
        "label":    "Wrist",
    },
}

# ─── Default motion parameters ────────────────────────────────────────────────
# All in OUTPUT (joint) units.  The arm functions multiply by gear ratio.
DEFAULT_CALIBRATION_RPM   = 5.0    # RPM at the output during calibration nudge
DEFAULT_CALIBRATION_ACCEL = 20.0   # RPM/s at the output during calibration nudge
DEFAULT_CONTROL_RPM       = 10.0   # RPM at the output during slider control
DEFAULT_CONTROL_ACCEL     = 30.0   # RPM/s at the output during slider control

# ─── Helper functions ────────────────────────────────────────────────────────

def motor_to_output(motor_degrees: float, gear: float) -> float:
    """Convert motor encoder position (degrees) to output joint angle (degrees)."""
    return motor_degrees / gear

def output_to_motor(output_degrees: float, gear: float) -> float:
    """Convert desired output joint angle (degrees) to motor position (degrees)."""
    return output_degrees * gear

def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, value))

def validate_dofs():
    """Print a summary of the config and warn about unset IDs."""
    print("=== Arm Configuration ===")
    for name, cfg in DOFS.items():
        status = "OK" if cfg["motor_id"] is not None else "⚠ MOTOR ID NOT SET"
        motor_min = output_to_motor(cfg["min"], cfg["gear"])
        motor_max = output_to_motor(cfg["max"], cfg["gear"])
        print(
            f"  {name} ({cfg['label']:12s}) | ID: {str(cfg['motor_id']):>4s} | "
            f"Gear: {cfg['gear']:5.1f} | "
            f"Output: [{cfg['min']:6.1f}°, {cfg['max']:6.1f}°] | "
            f"Motor:  [{motor_min:8.1f}°, {motor_max:8.1f}°]  {status}"
        )
    print()

if __name__ == "__main__":
    validate_dofs()
