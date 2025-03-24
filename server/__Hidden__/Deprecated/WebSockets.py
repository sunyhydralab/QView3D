from globals import emulator_connections, event_emitter
import asyncio
import websockets
import traceback
# import threading
import uuid
import certifi
import socket
import os
from websockets.asyncio.server import Server

async def websocket_server():
    async def handle_client(websocket):
        client_id = str(uuid.uuid4())

        print(f"Emulator websocket connected: {client_id}")

        emulator_connections[client_id] = websocket

        try:
            while True:
                message = await websocket.recv()
                assert isinstance(message, str), f"Received non-string message: {message}, Type: ({type(message)})"
                event_emitter.emit("message_received", client_id, message)
                fake_port = None
                fake_name = None
                fake_hwid = None
                if not hasattr(emulator_connections[client_id],"fake_port"):
                    fake_port = message.split('port":"')[-1].split('",')[0]
                    if fake_port:
                        emulator_connections[client_id].fake_port = fake_port
                    fake_name = message.split('Name":"')[-1].split('",')[0]
                    if fake_name:
                        emulator_connections[client_id].fake_name = fake_name
                    fake_hwid = message.split('Hwid":"')[-1].split('",')[0]
                    if fake_hwid:
                        emulator_connections[client_id].fake_hwid = fake_hwid
                if fake_hwid is not None and fake_name is not None and fake_port is not None:
                    break
            while True:
                message = await websocket.recv()
                print(f"Received message: {message}")
                assert isinstance(message, str), f"Received non-string message: {message}, Type: ({type(message)})"
                event_emitter.emit("message_received", client_id, message)
        except websockets.exceptions.ConnectionClosed:
            # Handle disconnection gracefully
            print(f"Emulator '{client_id}' has been disconnected.")
        except Exception:
            # Handle any other exception (unexpected disconnection, etc.)
            print(f"Error with client {client_id}: {traceback.format_exc()}")
        finally:
             if client_id in emulator_connections:
                del emulator_connections[client_id]

    try:
        try:
            socket.socket().connect_ex(('localhost', 8001))
        except ConnectionRefusedError:
            server: Server = await websockets.serve(handle_client, "localhost", 8001)
            await server.wait_closed()
    except Exception:
        print(f"WebSocket server error: {traceback.format_exc()}")

def start_websocket():
    print("Starting WebSocket server...")
    asyncio.run(websocket_server())


os.environ["SSL_CERT_FILE"] = certifi.where()
#
# websocket_thread = threading.Thread(target=start_websocket, daemon=True)
# websocket_thread.start()