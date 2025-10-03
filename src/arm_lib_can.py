import os
import can
import time
import subprocess  
import math
import logging 
#from invs import *
#import pygame
#pygame.init()
#mv_1 mv_2 ---> front_right
#mv_3 mv_4 ---> back_right

#logging.basicConfig(level=logging.DEBUG)

id = 14

control_modes = {"SET_DUTY":0, "SET_CURRENT":1, "SET_CURRENT_BRAKE":2, "SET_RPM":3, "SET_POS":4, "SET_ORIGIN_HERE":5, "SET_POS_SPD":6}
can_channel = "can1"
tx_timeout =  0.1 #second
rx_timeout =  0.1 #second
can_bitrate = 1000000
rpm_constant = 200

heading_offset = None
magnetic_declination = None

initial_run = 1

bus = None

motors_dictionary = {"mv_1":16, "mv_2":12, "mv_3":13, "mv_4":14} #Put -1 if motor can not be reachable
motors_directiones = {"mv_1":1, "mv_2":-1, "mv_3":1, "mv_4":-1} #Put -1 for reverse

motor_situations = {value: [0, 0, 0, 0, 0, 0, 0, 0] for key,value in motors_dictionary.items()}


buffer_vertical = [0]
buffer_angular = [0]

buffer_length = 5


def start_bus():
    global bus
    subprocess.run(["sudo", "ip", "link", "set", can_channel, "up", "type", "can", "bitrate", str(can_bitrate)])
    bus = can.interface.Bus(channel=can_channel, bustype="socketcan", bitrate = can_bitrate) #Open the bus.


def can_transmit(arb_id, message_data): #arbitation_id(hex) first 21 bits are for select control mode, last 8 bits are for motor_id  &&&& message_data is a array consists of 8bit parts
    global bus
    global fail_counter

    message = can.Message(arbitration_id=arb_id, data = message_data, is_extended_id= True,)

    try:
        bus.send(message, timeout=tx_timeout)

    except can.CanError as e:
        print(f"Failed to send message! Error: {e}")
        fail_counter += 1


def pad_to_eight(input_list):
    return input_list + [0] * (8 - len(input_list))


def can_recive():
        global motor_situations
        global fail_counter

        try:
            message = bus.recv(timeout=rx_timeout)

            if message is None:
                print("No message recived!")
                fail_counter += 1
                return None

            if len(message.data) != 8:
                print("Incorrect number of data bytes received.")
                return None

            recived_id = int(bin(int(message.arbitration_id))[2:].zfill(29)[-8:], 2)
            error_code = message.data[7]

            if error_code != 0:
                print("Error in motor: " + str(recived_id) + " --- Error Code: " + str(error_code))
                return error_code

            message_parser(message, recived_id)
                 
        except can.CanError:
            print("Failed to recive message!")
            fail_counter += 1
    

def message_parser(message, received_id):
    motor_situations[received_id] = pad_to_eight(
        [message.data[0], message.data[1], message.data[2], message.data[3], message.data[4], message.data[5], message.data[6], message.data[7]])

    high_byte_of_position = message.data[0]
    low_byte_of_position = message.data[1]
    high_byte_of_speed = message.data[2]
    low_byte_of_speed = message.data[3]
    high_byte_of_current = message.data[4]
    low_byte_of_current = message.data[5]
    motor_temperature = message.data[6]  # In celcius degree

    position_recived = int(bin(high_byte_of_position)[2:].zfill(8) + bin(low_byte_of_position)[2:].zfill(8),
                           2) / 10.0  # Position in degrees
    speed_recived = int(bin(high_byte_of_speed)[2:].zfill(8) + bin(low_byte_of_speed)[2:].zfill(8),
                        2) * 10.0  # Speed in rpm
    current_recived = int(bin(high_byte_of_current)[2:].zfill(8) + bin(low_byte_of_current)[2:].zfill(8),
                          2) / 100.0  # Current in amps

    return received_id, position_recived, speed_recived, current_recived, motor_temperature  # ,recived_situation


def set_duty(motor_id, duty_cycle):
    if (duty_cycle <= -1) or (1 <= duty_cycle):
        print("Incorrect duty cycle!")
        return None

    duty = duty_cycle * 100000
    duty = bin(int(duty))
    duty = duty[duty.index("b") + 1:].zfill(32)

    if duty_cycle < 0:
        flipped = ''.join('1' if bit == '0' else '0' for bit in duty)
        duty = bin(int(flipped, 2) + 1)[2:].zfill(len(duty))

    duty_bytes = [int(duty[0:8], 2), int(duty[8:16], 2), int(duty[16:24], 2), int(duty[24:32], 2)]

    sitaution_id = bin(control_modes["SET_DUTY"])[2:].zfill(21)
    motor_id_ = bin(motor_id)[2:].zfill(8)
    arb_id = int(sitaution_id + motor_id_, 2)

    can_transmit(arb_id, duty_bytes)


def set_current_loop(motor_id, float_current): #A
    if (float_current <= -60) or (60 <= float_current):
        print("Incorrect float current!")
        return None

    current = float_current * 1000
    current = bin(int(current))
    current = current[current.index("b") + 1:].zfill(32)

    if float_current < 0:
        flipped = ''.join('1' if bit == '0' else '0' for bit in current)
        current = bin(int(flipped, 2) + 1)[2:].zfill(len(current))
    curret_bytes = [int(current[0:8], 2), int(current[8:16], 2), int(current[16:24], 2), int(current[24:32], 2)]

    sitaution_id = bin(control_modes["SET_CURRENT"])[2:].zfill(21)
    motor_id_ = bin(motor_id)[2:].zfill(8)
    arb_id = int(sitaution_id + motor_id_, 2)

    can_transmit(arb_id, curret_bytes)


def set_current_brake(motor_id, brake_current): #A
    if (brake_current <= 0) or (60 <= brake_current):
        print("Incorrect brake current!")
        return None

    current = brake_current * 1000
    current = bin(int(current))
    current = current[current.index("b") + 1:].zfill(32)

    if brake_current < 0:
        flipped = ''.join('1' if bit == '0' else '0' for bit in current)
        current = bin(int(flipped, 2) + 1)[2:].zfill(len(current))

    curret_bytes = [int(current[0:8], 2), int(current[8:16], 2), int(current[16:24], 2), int(current[24:32], 2)]

    sitaution_id = bin(control_modes["SET_CURRENT_BRAKE"])[2:].zfill(21)
    motor_id_ = bin(motor_id)[2:].zfill(8)
    arb_id = int(sitaution_id + motor_id_, 2)

    can_transmit(arb_id, curret_bytes)


def set_velocity_loop(motor_id, velocity, rpm_constant = rpm_constant): #RPM
    if (velocity <= -1e5/rpm_constant) or (1e5/rpm_constant <= velocity):
        print("Incorrect rpm!")
        return None

    velocity_ = bin(int(velocity * rpm_constant))
    velocity_ = velocity_[velocity_.index("b") + 1:].zfill(32)

    if velocity < 0:
        flipped = ''.join('1' if bit == '0' else '0' for bit in velocity_)
        velocity_ = bin(int(flipped, 2) + 1)[2:].zfill(len(velocity_))

    velocity_bytes = [int(velocity_[0:8], 2), int(velocity_[8:16], 2), int(velocity_[16:24], 2),
                      int(velocity_[24:32], 2)]

    sitaution_id = bin(control_modes["SET_RPM"])[2:].zfill(21)
    motor_id_ = bin(motor_id)[2:].zfill(8)
    arb_id = int(sitaution_id + motor_id_, 2)

    can_transmit(arb_id, velocity_bytes)


def set_position_loop(motor_id, position): #Degree
    if (position <= -36000) or (36000 <= position):
        print("Incorrect position!")
        return None

    position_ = bin(int(position * 1e4))
    position_ = position_[position_.index("b") + 1:].zfill(32)

    if position < 0:
        flipped = ''.join('1' if bit == '0' else '0' for bit in position_)
        position_ = bin(int(flipped, 2) + 1)[2:].zfill(len(position_))

    position_bytes = [int(position_[0:8], 2), int(position_[8:16], 2), int(position_[16:24], 2),
                      int(position_[24:32], 2)]

    sitaution_id = bin(control_modes["SET_POS"])[2:].zfill(21)
    motor_id_ = bin(motor_id)[2:].zfill(8)
    arb_id = int(sitaution_id + motor_id_, 2)

    can_transmit(arb_id, position_bytes)


def set_origin_here(motor_id):
    set_position = [int(bin(1)[2:].zfill(32),2)]

    sitaution_id = bin(control_modes["SET_ORIGIN_HERE"])[2:].zfill(21)
    motor_id_ = bin(motor_id)[2:].zfill(8)
    arb_id = int(sitaution_id + motor_id_,2)
        
    can_transmit(arb_id,set_position)


def set_position_velocity_loop(motor_id, position, velocity, acceleration, rpm_constant = rpm_constant): #Degree, RPM , RPM/s
    if (position <= -36000) or (36000 <= position):
        print("Incorrect position")
        return None

    if (velocity <= -327680/rpm_constant) or (327680/rpm_constant <= velocity):
        print("Incorrect velocity")
        return None

    if (acceleration <= 0) or (327670 <= acceleration):
        print("Incorrect acceleration")
        return None

    position_ = bin(int(position * 1e4))
    position_ = position_[position_.index("b") + 1:].zfill(32)

    if position < 0:
        flipped = ''.join('1' if bit == '0' else '0' for bit in position_)
        position_ = bin(int(flipped, 2) + 1)[2:].zfill(len(position_))

    velocity_ = bin(int(velocity * rpm_constant / 10))
    velocity_ = velocity_[velocity_.index("b") + 1:].zfill(16)

    if velocity < 0:
        flipped = ''.join('1' if bit == '0' else '0' for bit in velocity_)
        velocity_ = bin(int(flipped, 2) + 1)[2:].zfill(len(velocity_))

    acceleration_ = bin(int(acceleration / 10))
    acceleration_ = acceleration_[acceleration_.index("b") + 1:].zfill(16)

    sitaution_id = bin(control_modes["SET_POS_SPD"])[2:].zfill(21)
    motor_id_ = bin(motor_id)[2:].zfill(8)
    arb_id = int(sitaution_id + motor_id_, 2)

    send_bytes = [int(position_[0:8], 2), int(position_[8:16], 2), int(position_[16:24], 2), int(position_[24:32], 2),
                  int(velocity_[0:8], 2), int(position_[8:16], 2), int(acceleration_[0:8], 2),
                  int(acceleration_[8:16], 2)]

    can_transmit(arb_id, send_bytes)


def stop_bus():
    bus.shutdown()
    subprocess.run(["sudo", "ip", "link", "set", can_channel, "down"])


if __name__ == "__main__":
    start_bus()
    for _ in range(20):
        set_velocity_loop(id, 25, 200)
    stop_bus()
