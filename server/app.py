import asyncio
from flask import Flask, jsonify, request, Response, url_for, send_from_directory
from threading import Thread
from flask_cors import CORS 
import os 
from models.db import db
from models.PrinterStatusService import PrinterStatusService
from flask_migrate import Migrate
from dotenv import load_dotenv, set_key
from controllers.ports import getRegisteredPrinters
import shutil
from flask_socketio import SocketIO
from datetime import datetime, timedelta
from sqlalchemy import text
import json
from models.config import Config
import discord
import threading
from discord.ext import commands
import certifi

os.environ["SSL_CERT_FILE"] = certifi.where()

# moved this up here so we can pass the app to the PrinterStatusService
# Basic app setup 
app = Flask(__name__, static_folder='../client/dist')
app.config.from_object(__name__) # update application instantly 

# moved this before importing the blueprints so that it can be accessed by the PrinterStatusService
printer_status_service = PrinterStatusService(app)

# Initialize SocketIO, which will be used to send printer status updates to the frontend
# and this specific socketit will be used throughout the backend

if Config.get('environment') == 'production':
    async_mode = 'eventlet'  # Use 'eventlet' for production
else:
    async_mode = 'threading'  # Use 'threading' for development

socketio = SocketIO(app, cors_allowed_origins="*", engineio_logger=False, socketio_logger=False, async_mode=async_mode) # make it eventlet on production!
app.socketio = socketio  # Add the SocketIO object to the app object

# IMPORTING BLUEPRINTS 
from controllers.ports import ports_bp
from controllers.jobs import jobs_bp
from controllers.statusService import status_bp, getStatus 
from controllers.issues import issue_bp

CORS(app)

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        res = Response()
        res.headers['X-Content-Type-Options'] = '*'
        res.headers['Access-Control-Allow-Origin'] = '*'
        res.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        res.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return res

# Serve static files
@app.route('/')
def serve_static(path='index.html'):
    return send_from_directory(app.static_folder, path)

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(os.path.join(app.static_folder, 'assets'), filename)

# start database connection
load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))
database_file = os.path.join(basedir, Config.get('database_uri'))
databaseuri = 'sqlite:///' + database_file
app.config['SQLALCHEMY_DATABASE_URI'] = databaseuri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

migrate = Migrate(app, db)

# # Register the display_bp Blueprint
app.register_blueprint(ports_bp)
app.register_blueprint(jobs_bp)
app.register_blueprint(status_bp)
app.register_blueprint(issue_bp)
    
@app.socketio.on('ping')
def handle_ping():
    app.socketio.emit('pong')

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
def sync_send_discord_file(file_path: str, message: str = None):
    """
    Sends a file to a specified Discord channel with an optional message.
    
    :param channel: The channel where the file will be sent.
    :param file_path: The path to the file to be uploaded.
    :param message: The optional message to send with the file.
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
        # Creating printer threads from registered printers on server start 
        res = getRegisteredPrinters() # gets registered printers from DB 
        data = res[0].get_json() # converts to JSON 
        printers_data = data.get("printers", []) # gets the values w/ printer data
        printer_status_service.create_printer_threads(printers_data)
        
        # Create in-memory uploads folder 
        uploads_folder = os.path.join('../uploads')
        tempcsv = os.path.join('../tempcsv')

        if os.path.exists(uploads_folder):
            # Remove the uploads folder and all its contents
            shutil.rmtree(uploads_folder)
            shutil.rmtree(tempcsv)

            # Recreate it as an empty directory
            os.makedirs(uploads_folder)
            os.makedirs(tempcsv)

            print("Uploads folder recreated as an empty directory.")
        else:
            # Create the uploads folder if it doesn't exist
            os.makedirs(uploads_folder)
            os.makedirs(tempcsv)
            print("Uploads folder created successfully.")  
    except Exception as e:
        print(f"Unexpected error: {e}")
            

if __name__ == "__main__":
    # If hits last line in GCode file: 
        # query for status ("done printing"), update. Use frontend to update status to "ready" once user removes print from plate. 
        # Before sending to printer, query for status. If error, throw error. 
    # since we are using socketio, we need to use socketio.run instead of app.run
    # which passes the app anyways
    socketio.run(app, debug=True)  # Replace app.run with socketio.run
    
def create_app():
    return app