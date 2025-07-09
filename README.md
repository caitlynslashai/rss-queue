# RSS Queue

An intelligent RSS feed aggregator that uses AI to classify and prioritize articles based on your interests. The system fetches articles from RSS feeds, analyzes their content using OpenAI's API, and creates a prioritized reading queue based on customizable topic preferences.

## Features

- **AI-Powered Classification**: Uses OpenAI's GPT models to automatically categorize articles by topic
- **Customizable Scoring**: Define your own topic preferences with positive/negative scoring weights
- **Persistent Queue**: Maintains a priority queue of articles across runs
- **Duplicate Prevention**: Tracks processed URLs to avoid re-processing articles
- **Discord Bot Integration**: Optional Discord bot for notifications and interaction
- **Automated Scheduling**: Windows Task Scheduler integration for regular updates

## Project Structure

```
rss-queue/
├── scraper.py          # Main RSS scraping and processing logic
├── llm_handler.py      # OpenAI API integration for content classification
├── scoring.py          # Article scoring based on topic rules
├── bot.py              # Discord bot (optional)
├── setup.ps1           # Windows setup script
├── run_scraper.bat     # Batch file for running scraper
├── requirements.txt    # Python dependencies
└── config/
    ├── config.json     # General configuration
    ├── feeds.txt       # Your RSS feed URLs (create from example)
    ├── feeds.example.txt # Example RSS feeds
    ├── rules.json      # Topic scoring rules (create from example)
    ├── rules.example.json # Example topic rules
    ├── priority_queue.json # Persistent article queue
    └── processed_urls.txt  # Tracking file for processed articles
```

## Setup

### Prerequisites

- Python 3.8+
- OpenAI API key
- (Optional) Discord bot token for bot functionality

### Installation - Windows

1. **Clone the repository**:
   ```bash
   git clone https://github.com/caitlynslashai/rss-queue.git
   cd rss-queue
   ```

2. **Run automated setup**:
   - Open PowerShell **as Administrator**
   - Navigate to the project directory
   - Allow script execution:
     ```powershell
     Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
     ```
   - Run the setup script:
     ```powershell
     .\setup.ps1
     ```

The setup script will:
- Create a Python virtual environment
- Install required dependencies
- Set up Windows Task Scheduler for automated runs
- Create necessary configuration files

### Manual Installation

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   DISCORD_BOT_TOKEN=your_discord_bot_token_here  # Optional
   ```

4. **Set up configuration files**:
   ```bash
   # Copy example files and customize
   copy config\feeds.example.txt config\feeds.txt
   copy config\rules.example.json config\rules.json
   ```

## Configuration

### RSS Feeds (`config/feeds.txt`)

Add your RSS feed URLs, one per line:
```
https://example.com/feed.xml
https://anotherblog.com/rss
```

### Topic Rules (`config/rules.json`)

Define scoring weights for different topics. Higher scores = higher priority:

```json
{
    "topic_rules": {
        "AI Safety": 100,
        "Technology": 75,
        "Politics": -25,
        "Celebrity": -100,
        "Default": 0
    }
}
```

- **Positive scores**: Topics you want to prioritize
- **Negative scores**: Topics you want to deprioritize  
- **Default**: Score for unclassified content

### General Settings (`config/config.json`)

```json
{
    "TRUNCATION_LENGTH": 2000
}
```

- `TRUNCATION_LENGTH`: Maximum characters sent to AI for classification (affects API costs)

## Usage

### Manual Run

```bash
python scraper.py
```

This will:
1. Fetch new articles from your RSS feeds
2. Classify each article using AI
3. Add articles to the priority queue
4. Display the prioritized reading list

### Automated Runs

The setup script configures Windows Task Scheduler to run the scraper automatically. You can modify the schedule through Task Scheduler or by editing the setup script.

### Discord Bot (Optional)

Run the Discord bot for notifications:
```bash
python bot.py
```

Make sure to:
1. Set `DISCORD_BOT_TOKEN` in your `.env` file
2. Invite the bot to your server with appropriate permissions
3. The bot includes slash commands (like `/hello`)

## How It Works

1. **Feed Processing**: The scraper reads RSS feeds from `config/feeds.txt`
2. **Content Extraction**: Uses Readability and BeautifulSoup to extract article text
3. **AI Classification**: Sends truncated content to OpenAI for topic classification
4. **Scoring**: Applies your custom rules to generate priority scores
5. **Queue Management**: Maintains a persistent priority queue of articles
6. **Output**: Displays articles in priority order for reading

## API Costs

The system uses OpenAI's `gpt-4o-nano` model for cost efficiency. Costs depend on:
- Number of new articles processed
- `TRUNCATION_LENGTH` setting (longer = more expensive)
- Frequency of runs

Typical costs are minimal for personal use with a few RSS feeds.

## Troubleshooting

### Common Issues

- **OpenAI API errors**: Check your API key and account credits
- **No articles found**: Verify RSS feed URLs are valid and accessible

### Logs

Check `scraper.log` for detailed execution logs and error messages.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source. See the repository for license details.
