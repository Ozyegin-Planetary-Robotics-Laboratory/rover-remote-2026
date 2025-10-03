from dynamixel_sdk import * 
import pyudev

context = pyudev.Context()

# Find dynamixel usb 
for device in context.list_devices(subsystem='tty'):
    path = device.get('ID_PATH')
    serialId = device.get('ID_SERIAL')
    if path and serialId:
        # dynamixel
        if "AD01UZ2Y" in serialId:
            dynamixelUSB = device.device_node
            print("dynamixel: " + device.device_node)
        # print(f"{device.device_node} - {serial} - {path}")



# Configs
DEVICENAME = dynamixelUSB
BAUDRATE = 1000000
DXL_ID = 1
PROTOCOL_VERSION = 1.0

# Control Table Addresses
ADDR_TORQUE_ENABLE     = 24
ADDR_CW_ANGLE_LIMIT    = 6
ADDR_CCW_ANGLE_LIMIT   = 8
ADDR_MOVING_SPEED      = 32

# Initialize Port and Packet Handlers
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

# Open Port
if not portHandler.openPort():
    print("Failed to open port")
    exit()

# Set Baudrate
if not portHandler.setBaudRate(BAUDRATE):
    print("Failed to set baudrate")
    exit()

# Enable Torque
dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, 1)
if dxl_comm_result != COMM_SUCCESS:
    print(f"{packetHandler.getTxRxResult(dxl_comm_result)}")
    # exit()

# Set Wheel Mode
packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_CW_ANGLE_LIMIT, 0)
packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_CCW_ANGLE_LIMIT, 0)

# Speed Control Function
def set_speed(speed):
    """
    Set speed in wheel mode.
    speed: -1023 to +1023
    Negative = clockwise, Positive = counter-clockwise
    """
    speed = max(-1023, min(1023, speed)) 
    if speed >= 0:
        value = speed
    else:
        value = -speed + 1024

    packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MOVING_SPEED, value)

# Test Setup
if __name__ == "__main__":
    import time

    print("? Starting motor demo...")

    set_speed(300)
    time.sleep(2)

    set_speed(-600)
    time.sleep(2)

    set_speed(0)
    print("? Motor stopped.")

    portHandler.closePort()
