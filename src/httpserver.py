#!/usr/bin/env python3
import http.server
import socketserver
import os
import asyncio
import websockets
import threading
import subprocess
import json
import psutil # For checking if processes are running

# Configuration
HTTP_PORT = 8060
WEBSOCKET_PORT = 8766
# Serving the WWW folder
DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'www')

# Store active continuous processes
continuous_processes = {}
process_lock = threading.Lock()

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        # Suppress logging to stdout, or adjust as needed
        # super().log_message(format, *args)
        pass

async def read_stream_and_send(stream, websocket, message_type, window_id):
    while True:
        line = await stream.readline()
        if not line:
            break
        try:
            await websocket.send(json.dumps({
                "type": message_type,
                "window_id": window_id,
                "output": line.decode().strip()
            }))
        except websockets.exceptions.ConnectionClosedOK:
            print(f"WebSocket connection closed for {window_id}")
            break
        except Exception as e:
            print(f"Error sending message for {window_id}: {e}")
            break

async def handle_continuous_command(websocket, command, window_id):
    print(f"Starting continuous command: {command} for window: {window_id}")
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        with process_lock:
            continuous_processes[window_id] = process

        await asyncio.gather(
            read_stream_and_send(process.stdout, websocket, "continuous_output", window_id),
            read_stream_and_send(process.stderr, websocket, "continuous_output", window_id)
        )
        await process.wait()
        print(f"Continuous command finished: {command} for window: {window_id} with exit code {process.returncode}")
    except asyncio.CancelledError:
        print(f"Continuous command {command} for window {window_id} cancelled.")
        if process.returncode is None:
            process.terminate()
            await process.wait()
    except Exception as e:
        print(f"Error running continuous command {command} for window {window_id}: {e}")
        try:
            await websocket.send(json.dumps({
                "type": "error",
                "window_id": window_id,
                "message": f"Error in continuous command: {e}"
            }))
        except websockets.exceptions.ConnectionClosedOK:
            pass
    finally:
        with process_lock:
            if window_id in continuous_processes:
                del continuous_processes[window_id]


async def terminal_handler(websocket, path):
    print(f"WebSocket client connected from {websocket.remote_address}")
    try:
        while True:
            message_str = await websocket.recv()
            message = json.loads(message_str)

            if message["type"] == "terminal_command":
                command = message["command"]
                print(f"Executing terminal command: {command}")
                try:
                    process = await asyncio.create_subprocess_shell(
                        command,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    response_output = stdout.decode() + stderr.decode()
                    await websocket.send(json.dumps({
                        "type": "terminal_output",
                        "output": response_output
                    }))
                except Exception as e:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": str(e)
                    }))
            elif message["type"] == "start_continuous":
                command = message["command"]
                window_id = message["window_id"]
                with process_lock:
                    if window_id in continuous_processes and continuous_processes[window_id].returncode is None:
                        print(f"Command for window {window_id} already running.")
                        continue
                
                # Start as a background task
                asyncio.create_task(handle_continuous_command(websocket, command, window_id))
                await websocket.send(json.dumps({
                    "type": "info",
                    "window_id": window_id,
                    "message": f"Started continuous command: {command}"
                }))
            elif message["type"] == "stop_continuous":
                window_id = message["window_id"]
                with process_lock:
                    process = continuous_processes.get(window_id)
                    if process and process.returncode is None:
                        print(f"Stopping continuous command for window: {window_id}")
                        process.terminate()  # or process.kill()
                        await process.wait()
                        del continuous_processes[window_id]
                        await websocket.send(json.dumps({
                            "type": "info",
                            "window_id": window_id,
                            "message": f"Stopped continuous command for window: {window_id}"
                        }))
                    else:
                        await websocket.send(json.dumps({
                            "type": "info",
                            "window_id": window_id,
                            "message": f"No active continuous command found for window: {window_id}"
                        }))
            else:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {message['type']}"
                }))
    except websockets.exceptions.ConnectionClosedOK:
        print(f"WebSocket client {websocket.remote_address} disconnected normally.")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"WebSocket client {websocket.remote_address} disconnected with error: {e}")
    except json.JSONDecodeError:
        print(f"Received non-JSON message from {websocket.remote_address}")
    except Exception as e:
        print(f"Unexpected error in terminal_handler for {websocket.remote_address}: {e}")
    finally:
        # Clean up any remaining continuous processes associated with this websocket
        windows_to_stop = []
        with process_lock:
            for window_id, process in continuous_processes.items():
                # Check if the process is still running and associated with this websocket
                # This part is tricky as a process is not directly linked to a websocket client in this setup
                # For now, let's just terminate all processes if any error occurs to ensure a clean state.
                # A more robust solution would track websocket per process.
                if process and process.returncode is None:
                    windows_to_stop.append(window_id)
        
        for window_id in windows_to_stop:
            with process_lock:
                process = continuous_processes.pop(window_id)
                if process.returncode is None:
                    print(f"Terminating orphaned continuous command for window: {window_id}")
                    process.terminate()
                    await process.wait()


def start_websocket_server_async():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    start_server = websockets.serve(terminal_handler, "0.0.0.0", WEBSOCKET_PORT)
    loop.run_until_complete(start_server)
    loop.run_forever()

# Create and start the HTTP server
httpd = socketserver.TCPServer(("", HTTP_PORT), Handler)

# Start WebSocket server in a new thread
websocket_thread = threading.Thread(target=start_websocket_server_async)
websocket_thread.daemon = True
websocket_thread.start()

print(f"HTTP Server running at http://0.0.0.0:{HTTP_PORT}")
print(f"WebSocket Server running at ws://0.0.0.0:{WEBSOCKET_PORT}")
print(f"Serving files from: {DIRECTORY}")

try:
    httpd.serve_forever()
except KeyboardInterrupt:
    print("\nServer shutting down...")
    httpd.server_close()
    # Terminate all running continuous processes on server shutdown
    with process_lock:
        for window_id, process in continuous_processes.items():
            if process.returncode is None:
                print(f"Terminating continuous command for window: {window_id} during shutdown.")
                process.terminate()
