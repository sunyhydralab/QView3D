import asyncio
import threading
from os import PathLike
from threading import Thread
import traceback
import uuid
import os
import shutil
import websockets
from websockets.asyncio.server import Server
from MyFlaskApp import MyFlaskApp
from globals import emulator_connections, event_emitter
import discord
from discord.ext import commands
import certifi
from datetime import datetime
from models.config import Config


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
        server: Server = await websockets.serve(handle_client, "localhost", 8001)
        await server.wait_closed()
    except Exception:
        print(f"WebSocket server error: {traceback.format_exc()}")

def start_websocket():
    print("Starting WebSocket server...")
    asyncio.run(websocket_server())


os.environ["SSL_CERT_FILE"] = certifi.where()

websocket_thread = threading.Thread(target=start_websocket, daemon=True)
websocket_thread.start()


# moved this up here so we can pass the app to the PrinterStatusService
# Basic app setup

app = MyFlaskApp()

# Set up the bot with the necessary intents
intents = discord.Intents.default()
intents.messages = True  # Enable messages
intents.message_content = True  # Enable message content

bot = commands.Bot(Config['command_prefix'], intents=intents)

class DiscordBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

def run_discord_bot():
    loop = asyncio.new_event_loop()  # Create a new event loop for this thread
    asyncio.set_event_loop(loop)  # Set it as the current event loop for this thread

    # Add the bot cog
    @bot.event
    async def on_ready():
        print(f'Logged in as {bot.user.name}')
        if Config['discord_enabled']:
            channel = bot.get_channel(int(Config['discord_issues_channel']))
            #await channel.send("Discord bot is online and ready!")

    @bot.command()
    async def testembedformatting(ctx):
        from models.issues import Issue
        try:
            raise Exception("Test issue")
        except Exception as e:
            Issue.create_issue("CODE ISSUE: Print Failed: Test Issue", e)

    @bot.command()
    async def testissue(ctx):
        embed = discord.Embed(title='New Issue Created',
                description='A issue occurred when running a job',
                color=discord.Color.red())
            
        embed.add_field(name='Issue', value="Issue details here...", inline=False)
        embed.add_field(name='ID', value="Issue id here...", inline=False)
            
        embed.timestamp = datetime.utcnow()
            
        await ctx.send(embed=embed)
    
    @bot.command()
    async def testfile(ctx):
        roleid = Config['discord_issues_role']
        role_message = '<@&{role_id}>'.format(role_id=roleid)
        
        sync_send_discord_file("../INFO.log", role_message)

    @bot.command()
    async def testsync(ctx):
        embed = discord.Embed(title='New Issue Created',
                              description='A issue occurred when running a job',
                              color=discord.Color.red())

        embed.add_field(name='Issue', value="Issue details here...", inline=False)
        embed.add_field(name='ID', value="Issue id here...", inline=False)

        sync_send_discord_embed(embed=embed)
        await ctx.send("sent!")

    # Start the bot
    bot.run(Config['discord_token'])
    
def start_discord_bot():
    discord_thread = Thread(target=run_discord_bot)
    discord_thread.start()

async def send_discord_message(message):
    if bot.is_ready():
        channel = bot.get_channel(int(Config['discord_issues_channel']))
        
        if channel is not None:
            await channel.send(message)
        else:
            print("Discord channel not found.")

def sync_send_discord_message(message):
    """
    Send a Discord message from a synchronous context, interacting with the bot's event loop.

    Parameters:
        message (str): The message to send.
    """
    print("Attempting to send embed to Discord...")

    # Check if the bot is ready
    if not bot.is_ready():
        print("Bot is not ready yet.")
        return

    # Get the Discord channel
    channel_id = int(Config.get("discord_issues_channel", 0))
    if not channel_id:
        print("Discord channel ID is not configured properly.")
        return

    channel = bot.get_channel(channel_id)
    if channel is None:
        print(f"Channel with ID {channel_id} not found or inaccessible.")
        return

    print(f"Channel {channel_id} found. Attempting to send the embed...")

    try:
        # Submit the coroutine to the bot's event loop
        asyncio.run_coroutine_threadsafe(channel.send(message), bot.loop)
        print("Embed sent successfully!")
    except Exception as e:
        print(f"An error occurred while sending the embed: {type(e).__name__} - {e}")

def sync_send_discord_embed(embed):
    """
    Send a Discord embed message from a synchronous context, interacting with the bot's event loop.

    :param embed: The embed to send.
    """

    # Check if the bot is ready
    if not bot.is_ready():
        print("Bot is not ready yet.")
        return

    # Get the Discord channel
    channel_id = int(Config.get("discord_issues_channel", 0))
    if not channel_id:
        print("Discord channel ID is not configured properly.")
        return

    channel = bot.get_channel(channel_id)
    if channel is None:
        print(f"Channel with ID {channel_id} not found or inaccessible.")
        return

    try:
        # Submit the coroutine to the bot's event loop
        asyncio.run_coroutine_threadsafe(channel.send(embed=embed), bot.loop)
    except Exception as e:
        print(f"An error occurred while sending the embed: {type(e).__name__} - {e}")


# this gets called like
# await send_discord_file(channel, file_path, "Here's an important file:")
def sync_send_discord_file(file_path: str | bytes | PathLike, message: str = None):
    """
    Sends a file to a specified Discord channel with an optional message.
    :param str | bytes | PathLike file_path: The path to the file to be uploaded.
    :param str message: The optional message to send with the file.
    """
    # Check if the bot is ready
    if not bot.is_ready():
        print("Bot is not ready yet.")
        return

    # Get the Discord channel
    channel_id = int(Config.get("discord_issues_channel", 0))
    if not channel_id:
        print("Discord channel ID is not configured properly.")
        return

    channel = bot.get_channel(channel_id)
    if channel is None:
        print(f"Channel with ID {channel_id} not found or inaccessible.")
        return

    try:
        with open(file_path, 'rb') as f:
            file = discord.File(f, filename=file_path.split("/")[-1])
            # Submit the coroutine to the bot's event loop
            asyncio.run_coroutine_threadsafe(channel.send(message or "", file=file), bot.loop)
    except Exception as e:
        print(f"An error occurred while sending the embed: {type(e).__name__} - {e}")


if Config['discord_enabled']:
    start_discord_bot()

# own thread
with app.app_context():
    try:
        # Define directory paths for uploads and tempcsv
        uploads_folder = os.path.abspath('../uploads')
        tempcsv = os.path.abspath('../tempcsv')
        # Check if directories exist and handle them accordingly
        for folder in [uploads_folder, tempcsv]:
            if os.path.exists(folder):
                # Remove the folder and all its contents
                shutil.rmtree(folder)
                app.logger.info(f"{folder} removed and will be recreated.")
            # Recreate the folder
            os.makedirs(folder)
            app.logger.info(f"{folder} recreated as an empty directory.")

    except Exception as e:
        # Log any exceptions for troubleshooting
        app.handle_errors_and_logging(e)

def run_socketio(app):
    try:
        app.socketio.run(app, allow_unsafe_werkzeug=True)
    except Exception as e:
        app.handle_errors_and_logging(e)

if __name__ == "__main__":
    # If hits last line in GCode file: 
        # query for status ("done printing"), update. Use frontend to update status to "ready" once user removes print from plate. 
        # Before sending to printer, query for status. If error, throw error. 
    # since we are using socketio, we need to use socketio.run instead of app.run
    # which passes the app anyways
    run_socketio(app)  # Replace app.run with socketio.run
