import feedparser
import requests
from bs4 import BeautifulSoup
from readability import Document
from llm_handler import get_characteristics
import json
from time import sleep, time
import os

# --- Configuration ---
# Define paths for the data and lock files
ARTICLES_FILE_PATH = 'config/articles.json'
PROCESSED_URLS_FILE_PATH = 'config/processed_urls.txt'
FEEDS_FILE_PATH = 'config/feeds.txt'
RULES_FILE_PATH = 'config/rules.json'
CONFIG_FILE_PATH = 'config/config.json'
LOCK_FILE_PATH = 'config/articles.lock' # The lock now protects articles.json

# --- Main Script Logic ---

def get_text(url: str) -> str:
    """
    Uses Requests, Readability, and BeautifulSoup to get the text of an article.
    
    Args:
        url (str): The URL of the article to process.
        
    Returns:
        str: The extracted text content from the article.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        doc = Document(response.text)
        soup = BeautifulSoup(doc.summary(), 'html.parser')
        text = soup.get_text()
        return text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return ""

def load_from_file(file_path, default_value):
    """Helper function to load data from a file, returning a default if it fails."""
    try:
        with open(file_path, 'r') as f:
            if file_path.endswith('.json'):
                return json.load(f)
            else: # Assumes .txt file for URLs
                return {line.strip() for line in f}
    except (FileNotFoundError, json.JSONDecodeError):
        return default_value

# --- Start of Execution ---

# Start timing the process
start_time = time()
print(f"Starting scraper process at {time()}")

# Load existing data
processed_urls = load_from_file(PROCESSED_URLS_FILE_PATH, set())
feeds = load_from_file(FEEDS_FILE_PATH, set())
config = load_from_file(CONFIG_FILE_PATH, {})
TRUNCATION_LENGTH = config.get('TRUNCATION_LENGTH', 2000)

# Wait for the lock file to be released by the bot
print("Checking for articles lock...")
while os.path.exists(LOCK_FILE_PATH):
    print("Articles file is locked, waiting...")
    sleep(1)

try:
    # 1. Acquire the lock
    print("Acquiring articles lock...")
    with open(LOCK_FILE_PATH, 'w') as f:
        pass

    # 2. Load the existing articles database
    articles = load_from_file(ARTICLES_FILE_PATH, [])
    
    # 3. Iterate through feeds and process new articles
    print("Checking for new articles...")
    new_articles_found = 0
    for feed_url in feeds:
        feed = feedparser.parse(feed_url)
        for entry in feed["entries"]:
            url = entry['link']
            if url not in processed_urls:
                new_articles_found += 1
                print(f"  - Found new article: {entry['title']}")
                
                # Mark as processed immediately
                processed_urls.add(url)

                text = get_text(url)
                if not text:
                    print(f"    - Skipping article due to fetch error.")
                    continue
                
                truncated_text = text[:TRUNCATION_LENGTH]
                
                # Get all characteristics from the LLM
                characteristics = get_characteristics(model="openai", text=truncated_text)
                
                if characteristics:
                    # Construct the new article object
                    new_article = {
                        "url": url,
                        "title": entry['title'],
                        "source_url": feed_url,
                        # Use .model_dump() to convert the Pydantic object to a dictionary
                        "characteristics": characteristics.model_dump() 
                    }
                    articles.append(new_article)
                    print(f"    - Successfully processed and added to database.")
                else:
                    print(f"    - Skipping article due to LLM processing error.")

    if new_articles_found == 0:
        print("No new articles found.")

    # 4. Save the updated articles database
    with open(ARTICLES_FILE_PATH, 'w') as f:
        json.dump(articles, f, indent=2)

finally:
    # 5. Release the lock
    print("Releasing articles lock...")
    if os.path.exists(LOCK_FILE_PATH):
        os.remove(LOCK_FILE_PATH)

# Save the updated list of processed URLs
with open(PROCESSED_URLS_FILE_PATH, 'w') as f:
    for url in processed_urls:
        f.write(url + "\n")

# Calculate and log total time
end_time = time()
total_time = end_time - start_time
print(f"Scraper run complete. Total time: {total_time:.2f} seconds")
