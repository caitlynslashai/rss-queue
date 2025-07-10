import os
import json
import time
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from scoring import score # Import the scoring function

# --- Configuration ---
load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# --- Robust Path Configuration ---
# Get the absolute path of the directory where this script (bot.py) is located.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Build absolute paths to the config files. This makes the script runnable from any directory.
CONFIG_DIR = os.path.join(SCRIPT_DIR, 'config')
ARTICLES_FILE_PATH = os.path.join(CONFIG_DIR, 'articles.json')
RULES_FILE_PATH = os.path.join(CONFIG_DIR, 'rules.json')
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, 'config.json')
LOCK_FILE_PATH = os.path.join(CONFIG_DIR, 'articles.lock')


# --- Bot Setup ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

# This list will act as the in-memory cache for the articles database.
in_memory_articles = []


# --- Bot Events ---
@bot.event
async def on_ready():
    """Event handler for when the bot has successfully connected."""
    print(f'We have logged in as {bot.user}')
    
    load_articles_from_disk()
    
    sync_articles_to_disk.start()
    
    try:
        # Sync the slash commands to Discord.
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Error syncing commands: {e}")


# --- Bot Commands ---
@bot.tree.command(name="next", description="Scores the queue and grabs the highest-priority article.")
async def next_article(interaction: discord.Interaction):
    """
    Scores all articles based on the latest rules, then fetches, posts,
    and removes the top item from the queue.
    """
    await interaction.response.defer()

    # Load the latest rules and scoring configuration on every call.
    try:
        with open(RULES_FILE_PATH, 'r') as f:
            rules = json.load(f)
        with open(CONFIG_FILE_PATH, 'r') as f:
            config = json.load(f)
            scoring_config = config.get("SCORING_RULES", [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        await interaction.followup.send(f"Error: A required configuration file could not be loaded. Details: {e}")
        return

    if not in_memory_articles:
        await interaction.followup.send("The reading queue is empty!")
        return

    # --- Scoring and Sorting Logic ---
    start_time = time.perf_counter()

    scored_articles = []
    # Loop through the in-memory articles and score each one using the generic engine.
    for article in in_memory_articles:
        article_score = score(
            characteristics=article.get('characteristics', {}),
            rules=rules,
            source_url=article.get('source_url', ''),
            scoring_config=scoring_config
        )
        scored_articles.append((article_score, article))

    # Sort the list by score in descending order.
    scored_articles.sort(key=lambda x: x[0], reverse=True)
    
    end_time = time.perf_counter()
    duration = end_time - start_time
    print(f"Scoring and sorting {len(scored_articles)} articles took {duration:.4f} seconds.")

    # Get the top article from the sorted list.
    top_article_data = scored_articles[0]
    top_article_score = top_article_data[0]
    top_article_dict = top_article_data[1]

    # Remove the article from the main in-memory list so it isn't served again.
    in_memory_articles.remove(top_article_dict)

    # Send the URL and score as the response.
    url_to_send = top_article_dict.get('url', 'URL not found.')
    await interaction.followup.send(f"**Score: {top_article_score}**\n{url_to_send}")


# --- Background Task ---
@tasks.loop(minutes=1.0)
async def sync_articles_to_disk():
    """Periodically saves the in-memory articles database back to the persistent file."""
    
    # Wait if the scraper is currently using the file.
    while os.path.exists(LOCK_FILE_PATH):
        await asyncio.sleep(1)

    try:
        # Acquire the lock for writing.
        with open(LOCK_FILE_PATH, 'w') as f:
            pass

        # Save the current state of the in-memory articles list to the JSON file.
        with open(ARTICLES_FILE_PATH, 'w') as f:
            json.dump(in_memory_articles, f, indent=2)
        
        print(f"[{discord.utils.utcnow()}] Synced articles to disk. Current size: {len(in_memory_articles)}")

    except Exception as e:
        print(f"Error during background articles sync: {e}")
    finally:
        # Always release the lock.
        if os.path.exists(LOCK_FILE_PATH):
            os.remove(LOCK_FILE_PATH)


# --- Helper Function ---
def load_articles_from_disk():
    """Loads the articles from the JSON file into the in-memory cache."""
    global in_memory_articles
    try:
        # We don't need to lock here, as this only runs once on startup
        # before the scraper or any commands are active.
        with open(ARTICLES_FILE_PATH, 'r') as f:
            loaded_list = json.load(f)
            if isinstance(loaded_list, list):
                in_memory_articles = loaded_list
                print(f"Successfully loaded {len(in_memory_articles)} articles from disk into memory.")
            else:
                in_memory_articles = []
    except (FileNotFoundError, json.JSONDecodeError):
        print("No existing articles file found. Starting with an empty list.")
        in_memory_articles = []


# --- Run the Bot ---
if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("ERROR: DISCORD_BOT_TOKEN not found in .env file.")
