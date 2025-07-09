import os
from dotenv import load_dotenv  
import discord
from discord.ext import commands
from discord import app_commands


QUEUE_FILE_PATH = 'config/priority_queue.json'
LOCK_FILE_PATH =  'config/queue.lock'
# Load the DOTENV to set the 'token' variable to the DISCORD_BOT_TOKEN
load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

# This requires the 'message_content' intent.

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix="!", intents=intents)

# Start the bot and sync all commands
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    try:
        synced = await client.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

# A basic hello command. Not really necessary to the bot's function
@client.tree.command(name="hello")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hey {interaction.user.mention}! This is a slash command!", ephemeral=True)

# TODO: Finish function
@client.tree.command(name="next", brief="Grabs the next item from the priority queue")
async def next(interaction: discord.Interaction):
    await interaction.response.send_message

client.run(token)

