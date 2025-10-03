#!/bin/bash

# Function to handle script termination
cleanup() {
    echo "Stopping scripts..."
    sudo pkill -f driver.py
    sudo pkill -f httpserver.py
    exit 0
}
echo "Stopping scripts..."
sudo pkill -f driver.py
#pkill python #Remove later
#pkill python3
#sudo pkill -f httpserver.py
# Trap signals (e.g., Ctrl+C or terminal close) to ensure cleanup runs
trap cleanup SIGINT SIGTERM EXIT

# Run the scripts in the foreground (so they stop when the terminal closes)
./src/driver.py &
#python -m http.server --directory src/www/ 8060 &
./src/httpserver.py

# Wait to keep the script running until interrupted
wait
