#!/usr/bin/env python3
import asyncio
import websockets
import json
import socket
import signal
import os
import time
import serial
from threading import Timer
import pyudev


from loco_lib_uart import velocity_control_loco, start_devs, change_color, get_loco_motor_info, dev_list, im
from arm_lib_can import set_velocity_loop, start_bus, bus, set_current_brake, motor_situations, can_recive

def scictl(c):
    return c

#try:
#    from RGBGPIO2 import *
#except:
#    pass

# Configuration
WS_PORT = 8765          # WebSocket server port
LSU_PORT = os.getenv("LSU_PORT", "/dev/ttyACM0")


# Track active connections
active_connections = set()

armSpeed = 10

# Limit switch
latestArmCrash = 0
limitSwitchIgnoreInterval = 20
bus= 0

armAvaliable = True # KOLU BUNLA AÇ

if armAvaliable:
    start_bus() # KOL
    import dynamixellib

from loco_lib_uart import science_sensor_serial



start_devs() # LOCO
try:
    lsu_ser=serial.Serial(LSU_PORT, 115200, timeout=0.1)
    limitswitch=True
except:
    limitswitch=False

dynamixelChanged = False
dynamixelUSB = "/dev/ttyUSB0" # wll choose automatically after



context = pyudev.Context()
# deviceFilterStrings = ["HUB", "Hub", "Linux"]

for device in context.list_devices(subsystem='tty'):
    path = device.get('ID_PATH')
    serialId = device.get('ID_SERIAL')
    if path and serialId:
        # dynamixel
        if "AD01UZ2Y" in serialId:
            dynamixelUSB = device.device_node
            print("dynamixel: " + device.device_node)
        # nano
        elif "1a86_USB_Serial" in serialId:
            print("nano: " + device.device_node)

        # print(f"{device.device_node} - {serial} - {path}")
        print(f"{device.device_node} - {path}")


# Handle WebSocket connections - updated to make path parameter optional
async def handle_websocket(websocket, path=None):
    global dynamixelChanged
    client_address = websocket.remote_address
    print(f"New connection from {client_address}")

    active_connections.add(websocket)

    try:
        await websocket.send(json.dumps({"status": "connected", "message": "Connected to bridge"}))
        change_color(b'x\n')
        change_color('red')
        async for message in websocket:
            #print(message)
            try:
                data = json.loads(message)
                if len(data["commands"]) > 0: print(data)
                # print(data)
                # commands = data["commands"]

                locoLinear = 0
                locoAngular = 0
                dynamixel = False
                DOFs = [False, False, False, False] # DOF1, DOF2, DOF3, DOF4
                mp = ""

                for i in data["commands"]:
                    li = i.split("#")
                    command = li[0]
                    value = float(li[1])
                    parameter = ""
                    if len(li) > 2: parameter = li[2]

                    if command == "LocoLinear":
                        locoLinear = value
                        mp = parameter
                    elif command == "LocoAngular":
                        locoAngular = value
                        mp = parameter

                    elif command == "DOF1Left":
                        set_velocity_loop(12, armSpeed/3 * value, 200)
                        DOFs[0] = True
                    elif command == "DOF1Right":
                        set_velocity_loop(12, -armSpeed/3 * value, 200)
                        DOFs[0] = True
                    elif command == "DOF1":
                        set_velocity_loop(12, armSpeed/3 * value, 200)
                        DOFs[0] = True

                    elif command == "DOF2Up":
                        set_velocity_loop(16, -armSpeed * value, 200)
                        DOFs[1] = True
                    elif command == "DOF2Down":
                        set_velocity_loop(16, armSpeed * value, 200)
                        DOFs[1] = True
                    elif command == "DOF2":
                        set_velocity_loop(16, -armSpeed * value, 200)
                        DOFs[1] = True

                    elif command == "DOF3Up":
                        set_velocity_loop(13, armSpeed * value, 200)
                        DOFs[2] = True
                    elif command == "DOF3Down":
                        set_velocity_loop(13, -armSpeed * value, 200)
                        DOFs[2] = True

                    elif command == "DOF4Up":
                        set_velocity_loop(14, -armSpeed/6 * value, 200)
                        DOFs[3] = True
                    elif command == "DOF4Down":
                        set_velocity_loop(14, armSpeed/6 * value, 200)
                        DOFs[3] = True

                    elif command == "EndEffectorCCW":
                        dynamixellib.set_speed(int(-30 * value))
                        dynamixel = True
                    elif command == "EndEffectorCW":
                        dynamixellib.set_speed(int(30 * value))
                        dynamixel = True

                    elif command == "GripperOpen":
                        science_sensor_serial.write(b'o\n')
                    elif command == "GripperClose":
                        science_sensor_serial.write(b'l\n')


                    elif command == "PanTiltUp":
                        science_sensor_serial.write(b'UP\n')
                    elif command == "PanTiltDown":
                        science_sensor_serial.write(b'DOWN\n')
                    elif command == "PanTiltLeft": 
                        science_sensor_serial.write(b'LEFT\n')
                    elif command == "PanTiltRight":
                        science_sensor_serial.write(b'RIGHT\n')

                    # elif command == "ScienceUp":
                    #     science_dc_ctl('SCIENCEUP')
                    # elif command == "ScienceDown":
                    #     science_dc_ctl('SCIENCEDOWN')
                    # elif command == "ScienceStop":
                    #     science_dc_ctl('SYSTEMSTOP')
                    # elif command == "DrillStart":
                    #     science_dc_ctl('DRILLSTART')
                    # elif command == "DrillStop":
                    #     science_dc_ctl('DRILLSTOP')
                    
                    elif command == "Led":
                        change_color(b'x\n')
                        timer1 = None
                        timer2 = None
                        print("LED KOMUTU BU:", command, value)
                        # change_color(["red","blue","green"][int(value)%3])
                        if value == 1: timer1 = Timer(0.5, change_color, ["red"])
                        elif value == 2: timer1 = Timer(0.5, change_color, ["green"])
                        elif value == 3: timer1 = Timer(0.5, change_color, ["blue"])
                        elif value == 4: timer1 = Timer(0.5, change_color, ["red"]); timer2 = Timer(1.0, change_color, ["green"])
                        elif value == 5: timer1 = Timer(0.5, change_color, ["red"]); timer2 = Timer(1.0, change_color, ["blue"])
                        elif value == 6: timer1 = Timer(0.5, change_color, ["green"]); timer2 = Timer(1.0, change_color, ["blue"])

                        if(timer1): timer1.start()
                        if(timer2): timer2.start()

                velocity_control_loco(locoAngular/4, locoLinear/2, mp)

                # Hold dof position if no command
                if not DOFs[0] and armAvaliable:
                    set_velocity_loop(12, 0, 200)
                if not DOFs[1] and armAvaliable:
                    set_velocity_loop(16, 0, 200)
                if not DOFs[2] and armAvaliable:
                    set_velocity_loop(13, 0, 200)
                if not DOFs[3] and armAvaliable:
                    set_velocity_loop(14, 0, 200)

                # Stop dynamixel if no command
                if not dynamixelChanged and dynamixel:
                    dynamixelChanged = True
                elif dynamixelChanged and not dynamixel:
                    dynamixelChanged = False
                    dynamixellib.set_speed(0)

                # Timestamp
                timestamp = int(time.time() * 1000)
                #print(limitswitch, lsu_ser)
                if armAvaliable:
                    can_recive()

                if limitswitch:
                    limiswitchres = CheckLimitSwitch()
                else:
                    limiswitchres = "No limit switch detected"
                parsedLocoMotorInfo = ParseLocoMotorInfo(get_loco_motor_info())
                message = {
                    "loco": parsedLocoMotorInfo,
                    "arm": motor_situations,
                    "crash": limiswitchres
                }
                await websocket.send(json.dumps({"status": "still_connected", "message": message, "timestamp": timestamp}))
                # print(message)
            except json.JSONDecodeError:
                print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!Invalid JSON received: {message}")
                await websocket.send(json.dumps({"status": "error", "message": "Invalid JSON format"}))

            except Exception as e:
                print(f"Error processing message: {e}")
                os.system("resetcan1.sh")

                await websocket.send(json.dumps({"status": "error", "message": str(e)}))

    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed from {client_address}: {e.code} - {e.reason}")
    finally:
        active_connections.remove(websocket)
        print(f"Connection from {client_address} closed, {len(active_connections)} active connections")

def CheckLimitSwitch():
    global limitSwitchIgnoreInterval, latestArmCrash
    line = lsu_ser.readline()
    arduinoMessage = line.decode(errors="ignore")
    currentTime = int(time.time() * 1000)
    #print(line)
    if arduinoMessage == "1\r\n":
        if currentTime > limitSwitchIgnoreInterval + latestArmCrash:
            print("CRASH")
            return True
        latestArmCrash = int(time.time() * 1000)


def ParseLocoMotorInfo(loco_list):
    result = []
    for info in loco_list:
        datas = info.split("|")
        parsed = {}

        # First part (Motor + Port)
        first = datas[0].split(" ", 1)
        parsed["Motor"] = im[first[1].split(":")[1]]

        if len(first) > 1 and ":" in first[1]:
            k, v = first[1].split(":", 1)
            parsed[k.strip()] = v.strip()

        # Remaining parts
        for d in datas[1:]:
            if ":" in d:
                k, v = d.split(":", 1)
                key = k.strip()
                value = v.strip()

                # Try converting to float if numeric
                try:
                    # remove units (letters, /, etc.)
                    num_str = "".join(ch for ch in value if (ch.isdigit() or ch in ".-"))
                    parsed[key] = float(num_str)
                except ValueError:
                    parsed[key] = value  # keep as string if not numeric

        result.append(parsed)
    return result

# Graceful shutdown
async def shutdown():
    print("Shutting down server...")

    if active_connections:
        print(f"Closing {len(active_connections)} active connections...")
        await asyncio.gather(*(conn.close(1001, "Server shutdown") for conn in active_connections), return_exceptions=True)

# Main function
async def main():
    print(f"Web to Motor Bridge")
    print(f"WebSocket server starting on port {WS_PORT}")

    # Create the server
    server = await websockets.serve(handle_websocket, "0.0.0.0", WS_PORT)
    print("Server started successfully. Press Ctrl+C to stop.")

    try:
        await asyncio.Future()  # Keep running forever
    except asyncio.CancelledError:
        await shutdown()
    finally:
        server.close()
        await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer shutting down...")
