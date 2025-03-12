import asyncio
from os import PathLike
from threading import Thread
import discord
from discord.ext import commands
from datetime import datetime
from models.config import Config

# Set up the bot with the necessary intents
print("Loading Discord bot config...")
intents = discord.Intents.default()
intents.messages = True  # Enable messages
intents.message_content = True  # Enable message content

bot = commands.Bot(Config['command_prefix'], intents=intents)

class DiscordBot(commands.Cog):
    # TODO: maybe use this?
    def __init__(self, bot):
        self.bot = bot
        self.token = Config['discord_token']
        self.issues_channel = Config['discord_issues_channel']
        self.issues_role = Config['discord_issues_role']

    def run(self):
        self.bot.run(self.token)


def run_discord_bot():
    print("starting run discord bot")
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
        from globals import current_app
        if current_app:
            with current_app.app.context():
                from models.issues import Issue
                try:
                    raise Exception("Test issue")
                except Exception as e:
                    Issue.create_issue("CODE ISSUE: Print Failed: Test Issue", e)
        else:
            print("Current app is not set")

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
        asyncio.run_coroutine_threadsafe(channel.send(message), bot.loop)
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


print("Discord bot configuration loaded")