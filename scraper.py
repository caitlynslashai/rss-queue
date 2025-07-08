import feedparser
import requests
from bs4 import BeautifulSoup
from readability import Document
from llm_handler import get_characteristics
import json
from scoring import score
import heapq

# Load priority queue from persistent storage
priority_queue = [] # Start with an empty list by default
try:
    with open('config/priority_queue.json', 'r') as f:
        # Load the data from the file
        priority_queue_data = json.load(f)
        # Check if the loaded data is a list before using it
        if isinstance(priority_queue_data, list):
            priority_queue = priority_queue_data
            # IMPORTANT: heapify the list in-place. Do not reassign it.
            heapq.heapify(priority_queue)
except (FileNotFoundError, json.JSONDecodeError):
    # If file doesn't exist or is empty/invalid, just use the empty list
    pass

# Save already-processed URLs to a set
try:
    with open('config/processed_urls.txt', 'r') as f:
        processed_urls = {line.strip() for line in f}
except FileNotFoundError:
    processed_urls = set()

# Get a list of feeds to check from feeds.txt
try:
    with open('config/feeds.txt', 'r') as f:    
        feeds = {line.strip() for line in f}
except FileNotFoundError:
    feeds = set()

with open('config/rules.json', 'r') as f:
    rules = json.load(f)

# Load configuration
try:
    with open('config/config.json', 'r') as f:
        config = json.load(f)
        TRUNCATION_LENGTH = config.get('TRUNCATION_LENGTH', 2000)
except FileNotFoundError:
    TRUNCATION_LENGTH = 2000

def get_text(url):
    """Uses Requests, Readability, BeautifulSoup to take a URL and get the text of the body
    
    Args:
        url (str): The URL of the article to process
        
    Returns:
        str: The extracted text content from the article"""

    try:
        # Use requests library to fetch the URL
        response = requests.get(url)    
        response.raise_for_status()  # Raise an exception for bad status codes
        # Readability and Soup to find the page's main content
        doc = Document(response.text)
        soup = BeautifulSoup(doc.summary(), 'html.parser')
        text = soup.get_text()
        return text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return ""  # Return empty string on error
    
# Iterate through each feed
for f in feeds:
    feed = feedparser.parse(f) 
    for a in feed["entries"]:
        url = a['link']
        if url not in processed_urls:
            # Mark the URL as processed so it doesn't get double-checked
            processed_urls.add(url)

            text = get_text(url)
            truncated = text[:TRUNCATION_LENGTH]                

            article_score = score(get_characteristics(model="openai", text=truncated), rules=rules)
            article_job = (article_score, url, a['title'])

            heapq.heappush(priority_queue, article_job)


# Save processed URLs back to persistent storage
with open('config/processed_urls.txt', 'w') as f:
        for url in processed_urls:
            f.write(url + "\n")

# Save priority queue back to persistent storage
with open('config/priority_queue.json', 'w') as f:
    json.dump(priority_queue, f, indent=2)

#  Empty and print pqueue after storage for debugging
print("\n--- Prioritized Reading List ---")
while priority_queue:
    # Get the next highest priority article
    job = heapq.heappop(priority_queue)
    priority = -job[0] # Convert priority back to positive for display
    url = job[1]
    title = job[2]
    print(f"Priority: {priority} | Title: {title} | URL: {url}")
