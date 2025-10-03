import os
import glob
import json
import math
import pyudev
import serial
import threading
from time import sleep
from servo_serial import *
#from NeuroLocoMiddleware.SoftRealtimeLoop import SoftRealtimeLoop

motor_speeds = {"mv_1": 0, "mv_2": 0, "mv_3": 0, "mv_4": 0}

motors_dictionary = {"mv_1": "/dev/ttyUSB0","mv_2": "/dev/ttyUSB7",
                     "mv_3": "/dev/ttyUSB3", "mv_4": "/dev/ttyUSB4"}  # Put serial ports. None means no port

#motors_dictionary = {"mv_1":motors_dictionary["mv_1"], "mv_2": motors_dictionary["mv_2"],
#		             "mv_3": motors_dictionary["mv_3"], "mv_4": motors_dictionary["mv_4"]}

im = {v:k for k, v in motors_dictionary.items()}
#motors_dictionary = json.load(open("/home/kaine/.motor_dict.json","r"))
motors_directions = {"mv_1": 1, "mv_2": 1, "mv_3": 1, "mv_4": 1}  # Put -1 for reverse
debug=1
#locoMotorInfo = [] #{value: [0, 0, 0, 0, 0, 0, 0, 0] for key,value in motors_dictionary.items()}
def identify_arduinos():
    color_port = None
    science_dc_port = None
    science_sensor_port = None

    context = pyudev.Context()
    ports = []

    # collect only CH340 tty devices
    for device in context.list_devices(subsystem="tty"):
        vid = device.get("ID_VENDOR_ID")
        pid = device.get("ID_MODEL_ID")
        if vid == "1a86" and pid == "7523":  # CH340
            ports.append(device.device_node)

    for port in ports:
        try:
            with serial.Serial(port, 115200, timeout=2) as ser:
                time.sleep(2)  # give Arduino time to reset

                # Send handshake
                ser.write(b"\n")
                ser.flush()

                # Read response
                response = ser.readline().decode(errors="ignore").strip()
                print(f"[{port}] → '{response}'")

                if "ARCIBI" in response.upper():
                    color_port = port
                elif "SAYINSDISI" in response.upper():
                    science_dc_port = port
                elif "SAYINS" in response.upper():
                    science_sensor_port = port

        except Exception as e:
            print(f"Could not open {port}: {e}")

    return {
        "color": color_port,
        "science_dc": science_dc_port,
        "science_sensor": science_sensor_port
    }

idardres = identify_arduinos()
print(idardres)

color_port=idardres["color"]
science_dc_port=idardres["science_dc"]
science_sensor_port=idardres["science_sensor"]
if color_port:
    color_serial = serial.Serial(port=color_port, baudrate=115200)
    print("")
    def change_color(c):
        if c == "red":
            color_serial.write(b'r\n')
        elif c == "green":
            color_serial.write(b'g\n')
        elif c == "blue":
            color_serial.write(b'b\n')
        else:
            color_serial.write(c)
else:
    def change_color(c):
        return 0
    print("No golor")




if science_sensor_port:
    science_sensor_serial = serial.Serial(port=science_sensor_port, baudrate=115200)
    def read_sensor_info():
        science_sensor_serial.write(b'\n')
        line = science_sensor_serial.readline().decode().strip()
        print("---", line)

        if line.startswith("HX1:"):
            parts = line.split(',')
            hx1 = int(parts[0].split(':')[1])
            hx2 = int(parts[1].split(':')[1])
            a3 = int(parts[2].split(':')[1])
            temp = int(parts[3].split(':')[1])
            return {"HX1":hx1,"HX2":hx2,"A3":a3,"TEMP":temp}
        return None
else:
    def read_sensor_info():
        return 0
    print("No science-sensor detected")

if science_dc_port:
    science_dc_serial = serial.Serial(port=science_dc_port, baudrate=115200)
    def science_dc_ctl(c):
        if c=="DOWN":
            science_dc_serial.write(b"l\n")
        if c=="UP":
            science_dc_serial.write(b"o\n")
        if c=="DRILLSTART":
            science_dc_serial.write(b"i\n")
        if c=="DRILLSTOP":
            science_dc_serial.write(b"k\n")
        if c=="SYSTEMSTOP":
            science_dc_serial.write(b"x\n")
        if science_sensor_port:
            if c=="GRIPPEROPEN":
                science_sensor_serial.write(b"o\n")
            if c=="GRIPPERCLOSE":
                science_sensor_serial.write(b"l\n")
        return c
else:
    def science_dc_ctl(c):
        return 0

#del motors_dictionary["color"]
port_list = list(motors_dictionary.values())



rpm_constant = 200

update_frequency = 20  # Hz

threads = []
stop_event = threading.Event()
sending_thread = None  # Declare globally so it's accessible in stop function
initial_run = True
dev_list = []


def read_motors_dictionary():
    global motors_dictionary

    try:
        with open(f'/home/{os.getlogin()}/.motor_dict.json', 'r') as f:
            motors_dictionary = json.load(f)
            print(f"Motor dictionary loaded: {motors_dictionary}")

    except FileNotFoundError:
        print("Motor dictionary file not found. Using default values.")

    except json.JSONDecodeError:
        print("Error decoding JSON from motor dictionary file. Using default values.")

def start_devs():
    global initial_run
    global dev_list
    if initial_run:
        for port in port_list:
            dev = TMotorManager_servo_serial(port=port, baud=962100)
            dev_list.append(dev)
        sleep(0.6)
        for dev in dev_list:
            dev.__enter__()
            dev.enter_velocity_control()
            dev.set_zero_position()
            dev.update()
        initial_run = False

def send_velocity_uart(port_list, speed_list):
    global motors_dictionary, motor_speeds, motors_directions, baudrate, stop_event, rpm_constant, update_frequency, initial_run, dev_list
    speed_list[2]=-1*speed_list[2]
    speed_list[0]=-1*speed_list[0]
    #loop = SoftRealtimeLoop(dt=10, report=True, fade=0.8)
    for _ in range(1): #for t in loop:
        for i, dev in enumerate(dev_list):
            # print(i, dev)
            dev.set_output_velocity_radians_per_second(speed_list[i])
            dev.update()
            # print(f"\r {dev}", end='')



def start_uart_com():
    global sending_thread, stop_event
    stop_event.clear()  # Make sure the event is cleared before starting
    sending_thread = threading.Thread(target=start_sending_data)
    sending_thread.start()


def stop_uart_com():
    global sending_thread
    stop_event.set()  # Signal all threads to stop
    if sending_thread is not None:
        sending_thread.join()  # Wait for start_sending_data to finish

    for thread in threads:
        thread.join()  # Wait for all motor threads to finish
    print("All threads stopped.")


def linear_velocity_multiplier_function(y, dead_zone):
    b = 50
    if y < 0:
        c = -b * math.e ** dead_zone
        return -(b * math.e ** -y + c)

    else:
        c = -b * math.e ** dead_zone
        return b * math.e ** y + c


def angular_velocity_multiplier_function(x, dead_zone):
    b = 50
    if x < 0:
        c = -b * math.e ** dead_zone
        return -(b * math.e ** -x + c)

    else:
        c = -b * math.e ** dead_zone
        return b * math.e ** x + c


def sticks_2_velocities(x,
                        y):  # mv_1 --> front_left !!!!!!!!!  mv_2--> front_right !!!!!!! mv_3-->back_left !!!!!!!!!! mv_4----->back_right

    x_dead_zone = 0.1
    y_dead_zone = 0.1
    diffrential_constant = 0.5
    maneuverability_constant = 0.4
    speed_constant = 0.35

    if (-x_dead_zone < x < x_dead_zone) and (-y_dead_zone < y < y_dead_zone):
        return [0, 0, 0, 0]
    elif (-x_dead_zone < x < x_dead_zone):
        y_ = speed_constant * linear_velocity_multiplier_function(y, y_dead_zone)
        y_front = speed_constant * diffrential_constant * y_ * 2
        y_back = speed_constant * (1 - diffrential_constant) * y_ * 2

        return [y_front, y_front, y_back, y_back]

    elif (-y_dead_zone < y < y_dead_zone):
        x_ =  speed_constant * angular_velocity_multiplier_function(x, x_dead_zone)
        return [x_, -x_, x_, -x_]

    else:
        y_ = speed_constant * linear_velocity_multiplier_function(y, y_dead_zone)
        x_ = speed_constant * angular_velocity_multiplier_function(x, x_dead_zone)

        y_front = diffrential_constant * y_ * 2 * (1 - maneuverability_constant)
        y_back = (1 - diffrential_constant) * y_ * 2 * (1 - maneuverability_constant)
        x_front = diffrential_constant * x_ * 2 * maneuverability_constant
        x_back = (1 - diffrential_constant) * x_ * 2 * maneuverability_constant

        return [y_front + x_front, y_front - x_front, y_back + x_back, y_back - x_back]


def velocity_control_loco(x, y, mp):
    global motors_speeds

    velocities = sticks_2_velocities(x, y)

    newVelocities = [0, 0, 0, 0]
    if "h" in mp:
        newVelocities[0] = velocities[1]
        newVelocities[1] = velocities[0]
        newVelocities[2] = velocities[3]
        newVelocities[3] = velocities[2]
    if "v" in mp:
        newVelocities[0] = -velocities[0]
        newVelocities[1] = -velocities[1]
        newVelocities[2] = -velocities[2]
        newVelocities[3] = -velocities[3]
    else:
        newVelocities = velocities

    velocities = newVelocities

    for i in range(4):
        motor_name = "mv_" + str(i + 1)
        motor_speeds[motor_name] = velocities[i]*((-1)*i%2)
    send_velocity_uart(port_list, velocities)

def get_loco_motor_info():
    locoMotorInfo=[]
    for i in dev_list:
        locoMotorInfo.append(str(i))
    return locoMotorInfo


if __name__ == "__main__":

    start_devs()
    #read_motors_dictionary()
    if 1:
        start_devs()
        for _ in range(1800):
            velocity_control_loco(0.1,0.0, "")
        print(get_loco_motor_info())
        #change_color(b'g')
        stop_uart_com()
