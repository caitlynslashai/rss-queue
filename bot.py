import os
import json
import heapq
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks

# --- Configuration ---
load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# --- Robust Path Configuration ---
# Get the absolute path of the directory where this script (bot.py) is located.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Build absolute paths to the config files. This makes the script runnable from any directory.
CONFIG_DIR = os.path.join(SCRIPT_DIR, 'config')
# Define paths for the queue and the lock file
QUEUE_FILE_PATH = os.path.join(CONFIG_DIR, 'priority_queue.json')
LOCK_FILE_PATH = os.path.join(CONFIG_DIR, 'queue.lock')


# --- Bot Setup ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

# This list will act as the fast, in-memory cache for the priority queue.
in_memory_queue = []


# --- Bot Events ---
@bot.event
async def on_ready():
    """Event handler for when the bot has successfully connected."""
    print(f'We have logged in as {bot.user}')
    
    # Load the persistent queue from disk into the in-memory cache on startup.
    load_queue_from_disk()
    
    # Start the background task to periodically save the queue to disk.
    sync_queue_to_disk.start()
    
    try:
        # Sync the slash commands to Discord.
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Error syncing commands: {e}")


# --- Bot Commands ---
@bot.tree.command(name="next", description="Grabs the next highest-priority article from the queue.")
async def next_article(interaction: discord.Interaction):
    """Fetches and posts the top item from the in-memory queue."""

    # Defer the response to let Discord know we're working on it.
    await interaction.response.defer()

    if not in_memory_queue:
        await interaction.followup.send("The reading queue is empty!")
        return

    # Pop the highest-priority item directly from the fast in-memory queue.
    job = heapq.heappop(in_memory_queue)
    url = job[1]

    # Send the URL as a plain text message.
    await interaction.followup.send(url)


# --- Background Task ---
@tasks.loop(minutes=1.0)
async def sync_queue_to_disk():
    """Periodically saves the in-memory queue back to the persistent file."""
    
    # Wait if the scraper is currently using the file.
    while os.path.exists(LOCK_FILE_PATH):
        await asyncio.sleep(1)

    try:
        # Acquire the lock for writing.
        with open(LOCK_FILE_PATH, 'w') as f:
            pass

        # Save the current state of the in-memory queue to the JSON file.
        with open(QUEUE_FILE_PATH, 'w') as f:
            json.dump(in_memory_queue, f, indent=2)
        
        print(f"[{discord.utils.utcnow()}] Synced queue to disk. Current size: {len(in_memory_queue)}")

    except Exception as e:
        print(f"Error during background queue sync: {e}")
    finally:
        # Always release the lock.
        if os.path.exists(LOCK_FILE_PATH):
            os.remove(LOCK_FILE_PATH)


# --- Helper Function ---
def load_queue_from_disk():
    """Loads the queue from the JSON file into the in-memory cache."""
    global in_memory_queue
    try:
        # We don't need to lock here, as this only runs once on startup
        # before the scraper or any commands are active.
        with open(QUEUE_FILE_PATH, 'r') as f:
            loaded_list = json.load(f)
            if isinstance(loaded_list, list):
                in_memory_queue = loaded_list
                heapq.heapify(in_memory_queue)
                print(f"Successfully loaded {len(in_memory_queue)} items from disk into memory.")
            else:
                in_memory_queue = []
    except (FileNotFoundError, json.JSONDecodeError):
        print("No existing queue file found. Starting with an empty queue.")
        in_memory_queue = []


# --- Run the Bot ---
if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("ERROR: DISCORD_BOT_TOKEN not found in .env file.")
