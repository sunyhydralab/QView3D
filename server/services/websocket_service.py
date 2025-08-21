import asyncio
import logging
import threading
import traceback
import uuid
import os
import websockets
from websockets.asyncio.server import Server
from Classes.EventEmitter import EventEmitter

# Moved from globals.py - WebSocket-specific global state
emulator_connections = {}
event_emitter = EventEmitter()

async def websocket_server():
    print("Websocket Server")
    logger = logging.getLogger("websockets.server")
    file_output = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../logs/websocket.log"))
    file_handler = logging.FileHandler(file_output)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.info("Websocket Server begins...")
    
    async def handle_client(websocket):
        client_id = str(uuid.uuid4())
        logger.debug(f"Emulator websocket connected: {client_id}")
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
                    msg = f"Emulator connected: {fake_name} ({fake_hwid}) on port {fake_port}"
                    print(msg)
                    logger.debug(msg)
                    break
            while True:
                message = await websocket.recv()
                msg = f"Received message from {client_id}: {message}"
                print(msg)
                logger.debug(msg)
                assert isinstance(message, str), f"Received non-string message: {message}, Type: ({type(message)})"
                event_emitter.emit("message_received", client_id, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Emulator '{client_id}' has been disconnected.")
        except Exception:
            logger.error(f"Error with client {client_id}: {traceback.format_exc()}")
        finally:
             if client_id in emulator_connections:
                del emulator_connections[client_id]

    try:
        logger.info("serving emu port on localhost:8001")
        server: Server = await websockets.serve(handle_client, "localhost", 8001)
        await server.wait_closed()
    except Exception:
        print(f"WebSocket server error: {traceback.format_exc()}")

def start_websocket():
    print("Starting WebSocket server...")
    asyncio.run(websocket_server())