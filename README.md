# CubeMars AK70 Rover Control Repository

This repository contains files that control the CubeMars AK70 motor and use a virtual or physical joystick controller to drive the rover.

## Overview

### `index.html`
- Website UI  
- WebSocket communication

### `httpserver.py`
- Serves the HTML UI over the network

### `driver.py`
- Retrieves controller data  
- Sends commands to the motors

### `arm_lib_can.py`
- Functions that convert inputs to velocity commands  
- Sends CAN messages to motors
  
### `loco_lib_uart.py`
- Converts joystick inputs to velocity commands  
- Sends UART messages to motors

### `rover-remote.sh`
- Starts necessary Python scripts
- `make run-rover`
