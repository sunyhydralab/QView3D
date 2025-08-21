import asyncio
import discord
from discord.ext import commands
from threading import Thread
from datetime import datetime
from os import PathLike
from config.config import Config

# Set up the bot with the necessary intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(Config['command_prefix'], intents=intents)

class DiscordBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

def run_discord_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    @bot.event
    async def on_ready():
        print(f'Logged in as {bot.user.name}')

    @bot.command()
    async def testembedformatting(ctx):
        from Classes.Issues import Issue
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

    bot.run(Config['discord_token'])
    
def start_discord_bot():
    discord_thread = Thread(target=run_discord_bot)
    discord_thread.start()

def sync_send_discord_message(message):
    if not bot.is_ready():
        print("Bot is not ready yet.")
        return
    channel_id = int(Config.get("discord_issues_channel", 0))
    if not channel_id:
        print("Discord channel ID is not configured properly.")
        return
    channel = bot.get_channel(channel_id)
    if channel is None:
        print(f"Channel with ID {channel_id} not found or inaccessible.")
        return
    try:
        bot.loop.create_task(channel.send(message))
        print("Message sent successfully!")
    except Exception as e:
        print(f"An error occurred while sending the message: {type(e).__name__} - {e}")

def sync_send_discord_embed(embed):
    if not bot.is_ready():
        print("Bot is not ready yet.")
        return
    channel_id = int(Config.get("discord_issues_channel", 0))
    if not channel_id:
        print("Discord channel ID is not configured properly.")
        return
    channel = bot.get_channel(channel_id)
    if channel is None:
        print(f"Channel with ID {channel_id} not found or inaccessible.")
        return
    try:
        bot.loop.create_task(channel.send(embed=embed))
    except Exception as e:
        print(f"An error occurred while sending the embed: {type(e).__name__} - {e}")

def sync_send_discord_file(file_path: str | bytes | PathLike, message: str = None):
    if not bot.is_ready():
        print("Bot is not ready yet.")
        return
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
            bot.loop.create_task(channel.send(message or "", file=file))
    except Exception as e:
        print(f"An error occurred while sending the file: {type(e).__name__} - {e}")