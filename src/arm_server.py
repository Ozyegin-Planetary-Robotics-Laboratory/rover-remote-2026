#!/usr/bin/env python3
"""
Robotic Arm Visualizer + IK Controller — WebSocket Server
==========================================================
Reads CAN bus feedback (candump) from AK60 motors in servo mode,
computes joint angles with gear reduction, pushes data to browser.
Also receives IK target angles from browser and sends CAN position commands.

Usage:
    python3 arm_server.py                    # candump on can1
    python3 arm_server.py --channel can0     # different CAN channel
    python3 arm_server.py --mock             # fake data for testing without CAN
"""

import asyncio
import json
import struct
import subprocess
import re
import argparse
import math
import time
import os
from pathlib import Path
from arm_inverse_kinematics import solve_target_for_repo, solution_rad_to_deg_dict

# ─── Motor / Arm Configuration ──────────────────────────────────────────────

MOTOR_CONFIG = {
    16: {"name": "Shoulder", "dof": 2, "gear": 62.0},
    13: {"name": "Elbow",    "dof": 3, "gear": 62.0},
    14: {"name": "Wrist",    "dof": 4, "gear": 10.5},
}

DOF_TO_CAN = {cfg["dof"]: can_id for can_id, cfg in MOTOR_CONFIG.items()}

# Motor direction multipliers from original code:
# mv_2(id16)=-1, mv_3(id13)=1, mv_4(id14)=-1
MOTOR_DIRECTIONS = {16: -1, 13: 1, 14: -1}

SEGMENTS = [0.48065, 0.42053, 0.40736]

JOINT_LIMITS = {
    2: (-15.0, 90.0),
    3: (-15.0, 135.0),
    4: (-15.0, 110.0),
}

CMD_VELOCITY = 5000       # eRPM
CMD_ACCELERATION = 30000  # eRPM/s²

# ─── State ───────────────────────────────────────────────────────────────────

class ArmState:
    def __init__(self):
        self.raw_motor_deg = {16: 0.0, 13: 0.0, 14: 0.0}
        self.received = {16: False, 13: False, 14: False}
        self.offsets = {16: 0.0, 13: 0.0, 14: 0.0}
        self.calibrated = False
        self.directions = {16: 1, 13: 1, 14: 1}
        self.motor_speed = {16: 0.0, 13: 0.0, 14: 0.0}
        self.motor_current = {16: 0.0, 13: 0.0, 14: 0.0}
        self.motor_temp = {16: 0, 13: 0, 14: 0}
        self.motor_error = {16: 0, 13: 0, 14: 0}
        self.message_count = 0

        # IK state
        self.ik_enabled = False
        self.ik_target_angles = {2: 0.0, 3: 0.0, 4: 0.0}
        self.ik_target_point = (0.0, sum(SEGMENTS))

    def get_joint_angles_deg(self):
        angles = {}
        for can_id, cfg in MOTOR_CONFIG.items():
            raw = self.raw_motor_deg[can_id]
            offset = self.offsets[can_id]
            direction = self.directions[can_id]
            gear = cfg["gear"]
            if self.calibrated:
                motor_delta = (raw - offset) * direction
                joint_deg = motor_delta / gear
            else:
                joint_deg = 0.0
            angles[cfg["dof"]] = joint_deg
        return angles

    def calibrate(self):
        for can_id in MOTOR_CONFIG:
            self.offsets[can_id] = self.raw_motor_deg[can_id]
        self.calibrated = True

    def compute_2d_points(self, angles_deg=None):
        if angles_deg is None:
            angles_deg = self.get_joint_angles_deg()
        points = [(0.0, 0.0)]
        cumulative = 0.0
        x, y = 0.0, 0.0
        for i, seg_len in enumerate(SEGMENTS):
            dof = i + 2
            cumulative += math.radians(angles_deg.get(dof, 0.0))
            x += seg_len * math.sin(cumulative)
            y += seg_len * math.cos(cumulative)
            points.append((round(x, 5), round(y, 5)))
        return points

    def to_json(self):
        angles = self.get_joint_angles_deg()
        points = self.compute_2d_points()

        motor_info = {}
        for can_id, cfg in MOTOR_CONFIG.items():
            motor_info[str(can_id)] = {
                "name": cfg["name"], "dof": cfg["dof"],
                "raw_deg": round(self.raw_motor_deg[can_id], 2),
                "offset_deg": round(self.offsets[can_id], 2),
                "joint_deg": round(angles[cfg["dof"]], 2),
                "gear": cfg["gear"],
                "direction": self.directions[can_id],
                "received": self.received[can_id],
                "speed": round(self.motor_speed[can_id], 1),
                "current": round(self.motor_current[can_id], 2),
                "temp": self.motor_temp[can_id],
                "error": self.motor_error[can_id],
            }

        target_pts = self.compute_2d_points(self.ik_target_angles) if self.ik_enabled else None

        return json.dumps({
            "type": "state",
            "calibrated": self.calibrated,
            "points": points,
            "angles": {str(k): round(v, 2) for k, v in angles.items()},
            "motors": motor_info,
            "msg_count": self.message_count,
            "timestamp": round(time.time(), 3),
            "ik_enabled": self.ik_enabled,
            "ik_target_angles": {str(k): round(v, 2) for k, v in self.ik_target_angles.items()},
            "ik_target_points": target_pts,
            "ik_target_xy": list(self.ik_target_point),
        })


state = ArmState()
clients = set()

# ─── CAN Parsing ─────────────────────────────────────────────────────────────

def parse_candump_line(line):
    line = line.strip()
    if not line:
        return
    match = re.search(
        r'([0-9A-Fa-f]{3,8})\s+\[(\d+)\]\s+((?:[0-9A-Fa-f]{2}\s*)+)', line
    )
    if not match:
        return
    arb_id = int(match.group(1), 16)
    data_hex = match.group(3).strip().split()
    data_bytes = [int(b, 16) for b in data_hex]
    motor_id = arb_id & 0xFF
    if motor_id not in MOTOR_CONFIG or len(data_bytes) < 8:
        return

    pos_raw = (data_bytes[0] << 8) | data_bytes[1]
    if pos_raw >= 0x8000: pos_raw -= 0x10000
    spd_raw = (data_bytes[2] << 8) | data_bytes[3]
    if spd_raw >= 0x8000: spd_raw -= 0x10000
    cur_raw = (data_bytes[4] << 8) | data_bytes[5]
    if cur_raw >= 0x8000: cur_raw -= 0x10000

    state.raw_motor_deg[motor_id] = pos_raw * 0.1
    state.received[motor_id] = True
    state.motor_speed[motor_id] = spd_raw * 10.0
    state.motor_current[motor_id] = cur_raw * 0.01
    state.motor_temp[motor_id] = data_bytes[6]
    state.motor_error[motor_id] = data_bytes[7]
    state.message_count += 1

# ─── CAN Command Sending ────────────────────────────────────────────────────

async def send_pos_spd_cmd(channel, motor_id, position_deg, velocity_erpm, accel):
    """
    Send SET_POS_SPD (mode 6) via cansend.
    position_deg: absolute motor shaft position in degrees.
    """
    arb_id = (6 << 8) | motor_id

    pos_raw = int(position_deg * 10000.0)
    if pos_raw < 0:
        pos_raw = pos_raw + (1 << 32)
    pos_raw &= 0xFFFFFFFF

    vel_raw = int(velocity_erpm / 10.0)
    if vel_raw < 0:
        vel_raw = vel_raw + (1 << 16)
    vel_raw &= 0xFFFF

    acc_raw = int(accel / 10.0) & 0xFFFF

    data = [
        (pos_raw >> 24) & 0xFF, (pos_raw >> 16) & 0xFF,
        (pos_raw >> 8) & 0xFF, pos_raw & 0xFF,
        (vel_raw >> 8) & 0xFF, vel_raw & 0xFF,
        (acc_raw >> 8) & 0xFF, acc_raw & 0xFF,
    ]

    hex_data = ''.join(f'{b:02X}' for b in data)
    frame = f"{arb_id:08X}#{hex_data}"

    try:
        proc = await asyncio.create_subprocess_exec(
            'cansend', channel, frame,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.wait()
    except Exception as e:
        print(f"[CAN-TX] Error motor {motor_id}: {e}")


async def send_ik_targets(channel):
    """Convert IK target joint angles -> motor positions and send CAN commands."""
    if not state.calibrated or not state.ik_enabled:
        return

    for dof, target_joint_deg in state.ik_target_angles.items():
        can_id = DOF_TO_CAN.get(dof)
        if can_id is None:
            continue

        gear = MOTOR_CONFIG[can_id]["gear"]
        direction = MOTOR_DIRECTIONS.get(can_id, 1) * state.directions[can_id]

        motor_target = target_joint_deg * gear * direction + state.offsets[can_id]

        await send_pos_spd_cmd(channel, can_id, motor_target, CMD_VELOCITY, CMD_ACCELERATION)

# ─── CAN Reader ──────────────────────────────────────────────────────────────

async def candump_reader(channel):
    try:
        proc = await asyncio.create_subprocess_exec(
            'stdbuf', '-oL', 'candump', channel,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        proc = await asyncio.create_subprocess_exec(
            'candump', channel,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
    print(f"[CAN] candump {channel} started (pid {proc.pid})")

    lc = 0
    while True:
        line = await proc.stdout.readline()
        if not line:
            break
        parse_candump_line(line.decode('utf-8', errors='ignore'))
        lc += 1
        if lc <= 3 or lc % 500 == 0:
            print(f"[CAN] Line #{lc}: {line.decode().strip()}")

    ret = await proc.wait()
    print(f"[CAN] candump exited code {ret}")


async def mock_can_data():
    print("[MOCK] Generating fake CAN data")
    state.calibrated = True
    while True:
        for can_id, cfg in MOTOR_CONFIG.items():
            gear = cfg["gear"]
            if state.ik_enabled:
                target_joint = state.ik_target_angles.get(cfg["dof"], 0.0)
                target_motor = target_joint * gear * MOTOR_DIRECTIONS.get(can_id, 1)
                current = state.raw_motor_deg[can_id]
                state.raw_motor_deg[can_id] += (target_motor - current) * 0.15
            state.received[can_id] = True
            state.motor_temp[can_id] = 35
            state.message_count += 1
        await asyncio.sleep(0.05)

# ─── HTTP + WebSocket Server ─────────────────────────────────────────────────

CLIENT_HTML_PATH = Path(__file__).parent / "arm_client.html"

async def main(args):
    try:
        from aiohttp import web
    except ImportError:
        print("Installing aiohttp...")
        p = await asyncio.create_subprocess_exec(
            'pip', 'install', 'aiohttp', '--break-system-packages',
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        await p.wait()
        from aiohttp import web

    if args.mock:
        asyncio.create_task(mock_can_data())
    else:
        asyncio.create_task(candump_reader(args.channel))

    async def handle_index(request):
        if CLIENT_HTML_PATH.exists():
            return web.FileResponse(CLIENT_HTML_PATH)
        return web.Response(text="arm_client.html not found", status=404)

    async def handle_ws(request):
        ws_resp = web.WebSocketResponse()
        await ws_resp.prepare(request)
        clients.add(ws_resp)
        remote = request.remote
        print(f"[WS] Client connected: {remote}")

        try:
            async for msg in ws_resp:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                    except json.JSONDecodeError:
                        continue
                    cmd = data.get("cmd")

                    if cmd == "calibrate":
                        state.calibrate()
                        state.ik_target_point = (0.0, sum(SEGMENTS))
                        state.ik_target_angles = {2: 0.0, 3: 0.0, 4: 0.0}
                        state.ik_enabled = False
                        await ws_resp.send_json({
                            "type": "info",
                            "message": "Calibrated! Home = straight up. IK disabled."
                        })

                    elif cmd == "flip_direction":
                        can_id = int(data.get("can_id", 0))
                        if can_id in MOTOR_CONFIG:
                            state.directions[can_id] *= -1
                            await ws_resp.send_json({
                                "type": "info",
                                "message": f"Flipped {MOTOR_CONFIG[can_id]['name']} dir -> {state.directions[can_id]:+d}"
                            })

                    elif cmd == "ik_enable":
                        state.ik_enabled = data.get("enabled", False)
                        if state.ik_enabled:
                            pts = state.compute_2d_points()
                            ee = pts[-1]
                            state.ik_target_point = (ee[0], ee[1])
                            state.ik_target_angles = dict(state.get_joint_angles_deg())
                        print(f"[IK] {'ENABLED' if state.ik_enabled else 'DISABLED'}")

                    elif cmd == "ik_target":
                        if state.ik_enabled and state.calibrated:
                            angles = data.get("angles", {})
                            for k, v in angles.items():
                                state.ik_target_angles[int(k)] = float(v)
                            pt = data.get("target_xy", [0, 0])
                            state.ik_target_point = (pt[0], pt[1])

                elif msg.type == web.WSMsgType.ERROR:
                    break
        except Exception as e:
            print(f"[WS] Error: {e}")
        finally:
            clients.discard(ws_resp)
            print(f"[WS] Client disconnected: {remote}")
        return ws_resp

    async def broadcast_loop(app):
        while True:
            if state.ik_enabled and state.calibrated and not args.mock:
                await send_ik_targets(args.channel)
            if clients:
                payload = state.to_json()
                dead = set()
                for c in clients:
                    try:
                        await c.send_str(payload)
                    except Exception:
                        dead.add(c)
                clients.difference_update(dead)
            await asyncio.sleep(0.05)

    async def on_start(app):
        app['bg'] = asyncio.create_task(broadcast_loop(app))
    async def on_stop(app):
        app['bg'].cancel()
        try: await app['bg']
        except asyncio.CancelledError: pass

    app = web.Application()
    app.router.add_get('/ws', handle_ws)
    app.router.add_get('/', handle_index)
    app.router.add_get('/index.html', handle_index)
    app.on_startup.append(on_start)
    app.on_cleanup.append(on_stop)

    print(f"[SERVER] http://0.0.0.0:{args.port}")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", args.port)
    await site.start()
    await asyncio.Future()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--channel', default='can1')
    parser.add_argument('--port', type=int, default=8766)
    parser.add_argument('--mock', action='store_true')
    args = parser.parse_args()
    asyncio.run(main(args))
###
def solve_and_store_ik_target(self, x, y, z, phi_deg=0.0, elbow_up=False):
    # hedef noktayı 4 dof açılarına ceviriyoruz
    sol = solve_target_for_repo(x, y, z, phi_deg=phi_deg, elbow_up=elbow_up)

    # radyandan dereceye ceviriyoruz
    sol_deg = solution_rad_to_deg_dict(sol)

    # state icine yazıyoruz
    self.ik_target_angles = {
        1: sol_deg[1],
        2: sol_deg[2],
        3: sol_deg[3],
        4: sol_deg[4],
    }

    # hedef noktayı da saklayalım
    self.ik_target_point = (x, y, z)

    return self.ik_target_angles
