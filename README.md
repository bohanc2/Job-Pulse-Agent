# Ascendo AI Community Jobs

An intelligent job aggregation platform that collects and displays job opportunities from multiple sources.

## Features

- 🔍 **Multi-source Data Collection**: Adzuna API, RSS feeds, and company URLs with LLM-powered extraction
- 🔄 **Auto Refresh**: Hourly updates with smart keyword rotation
- 🎯 **Smart Collection**: Collects until API limit, auto-resumes next day
- ⚠️ **API Limit Detection**: Automatic detection with user notifications
- 🔎 **Advanced Search**: Whole-word matching on titles and company names
- 🏷️ **Smart Filtering**: Filter by job level and salary
- 🗄️ **PostgreSQL Support**: Production-ready with auto-migrations

## Tech Stack

**Backend**: Python 3.11+, Flask 3.0.0, Gunicorn  
**Database**: SQLAlchemy 2.0.23, SQLite (dev) / PostgreSQL (production)  
**Data Collection**: Adzuna API, BeautifulSoup4, Feedparser, Requests  
**AI/LLM**: Google Gemini 2.0 Flash Lite (primary), OpenAI GPT-4o-mini (fallback)  
**Scheduler**: APScheduler 3.10.4  
**Frontend**: HTML5, CSS3, Vanilla JavaScript

## Quick Start

### Prerequisites

- Python 3.8+
- Adzuna API credentials ([Get free account](https://developer.adzuna.com/))

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Job-Pulse-Agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   Create a `.env` file:
   ```env
   # Required
   ADZUNA_APP_ID=your_app_id_here
   ADZUNA_APP_KEY=your_app_key_here
   
   # Optional (for URL collection)
   GEMINI_API_KEY=your_gemini_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   ```
   http://localhost:5000
   ```

## Usage

### Adding Data Sources

1. Open the web interface → Click **"⚙️ Admin Settings"**
2. Select source type and enter information
3. Click **"Add Source"**

**Supported Types:**
- **Adzuna API**: Enter keywords (e.g., "software engineer") or leave empty for all jobs
- **RSS Feed**: Enter full RSS feed URL
- **Company URL**: Enter careers page URL (requires LLM API key)

### Searching Jobs

- **Search Box**: Searches job titles and company names (whole-word matching)
- **Location**: Filter by location
- **Level Filter**: Entry, Mid-level, Senior
- **Pay Filter**: Minimum salary threshold

### Manual Refresh

Click **"🔄 Refresh Now"** in Admin Settings to trigger immediate collection (runs in background).

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ADZUNA_APP_ID` | Yes | Adzuna API Application ID |
| `ADZUNA_APP_KEY` | Yes | Adzuna API Application Key |
| `GEMINI_API_KEY` | No | Google Gemini API Key (recommended for URL collection) |
| `OPENAI_API_KEY` | No | OpenAI API Key (fallback for URL collection) |
| `ADZUNA_MAX_PAGES` | No | Max pages per collection (default: unlimited) |
| `ADZUNA_USE_KEYWORD_ROTATION` | No | Enable keyword rotation (default: true) |
| `ADZUNA_KEYWORDS` | No | Comma-separated keywords (default: 10 common categories) |
| `FLASK_ENV` | No | `production` or `development` (default: development) |
| `DATABASE_URL` | No | PostgreSQL connection string (auto-provided by Render) |

## Smart Collection Features

- **Keyword Rotation**: Automatically rotates through keywords each hour
- **API Limit Management**: Detects 429 errors and stops gracefully, auto-resumes next day
- **Continuous Collection**: Collects until daily limit reached (when `ADZUNA_MAX_PAGES` not set)

## API Endpoints

- `GET /api/jobs` - Get paginated jobs with filters
- `GET /api/refresh-status` - Get collection status and statistics
- `GET /api/sources` - Get all data sources
- `POST /api/sources` - Add new data source
- `DELETE /api/sources/<id>` - Delete data source (hard deletion)
- `POST /api/refresh-now` - Trigger manual refresh
- `POST /api/cleanup-duplicates` - Clean up duplicate jobs

## Project Structure

```
Job-Pulse-Agent/
├── app.py                      # Flask main application
├── scheduler.py                # Scheduled tasks manager
├── data_collectors/            # Data collection modules
│   ├── api_collector.py        # Adzuna API collector
│   ├── rss_collector.py        # RSS feed collector
│   └── url_collector.py        # URL collector with LLM
├── models/                     # Database models
│   └── database.py             # SQLAlchemy models
├── templates/                  # HTML templates
└── static/                     # CSS and JavaScript
```

## Troubleshooting

**No jobs appearing?**
- Verify Adzuna API credentials in `.env`
- Ensure at least one data source is added
- Click "🔄 Refresh Now" to trigger collection

**API limit reached?**
- Normal behavior - collection auto-resumes tomorrow
- You can still view previously collected jobs

**URL collection not working?**
- Verify `GEMINI_API_KEY` or `OPENAI_API_KEY` is set
- Ensure webpage contains readable job listings

**Database errors?**
- Delete `database.db` and restart (SQLite will be recreated)

## Deployment

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

**Quick Summary:**
1. Push code to GitHub
2. Create Render Web Service
3. Configure environment variables
4. Create PostgreSQL database
5. Deploy

## License

This project is provided as-is for educational and personal use.

---

**Built with ❤️ for the Ascendo AI Community**
