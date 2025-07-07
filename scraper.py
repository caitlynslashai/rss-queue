import feedparser
import requests
from bs4 import BeautifulSoup
from readability import Document

# Save already-processed URLs to a set
try:
    with open('processed_urls.txt', 'r') as f:
        processed_urls = {line.strip() for line in f}
except FileNotFoundError:
    processed_urls = set()

# Get a list of feeds to check from feeds.txt
try:
    with open('feeds.txt', 'r') as f:
        feeds = {line.strip() for line in f}
except FileNotFoundError:
    feeds = set()

# Iterate through each feed
for f in feeds:
    feed = feedparser.parse(f) 
    for a in feed["entries"]:
        url = a['link']
        if url not in processed_urls:
            # Mark the URL as processed so it doesn't get double-checked
            processed_urls.add(url)

            # Use requests library to fetch the URL
            response = requests.get(url)    
            # Readability and Soup to find the page's main content
            doc = Document(response.text)
            soup = BeautifulSoup(doc.summary(), 'html.parser')
            text = soup.get_text()

            print(text[0:100])

# Save processed URLs back to persistent storage
with open('processed_urls.txt', 'w') as f:
          for url in processed_urls:
               f.write(url + "\n")
          

