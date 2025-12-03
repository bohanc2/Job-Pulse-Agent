# Ascendo AI Community Jobs

An intelligent job aggregation platform that collects and displays job opportunities from multiple sources.

## Features

- 🔍 **Multi-source Data Collection**: Collects jobs from Adzuna API, RSS feeds, and company URLs
- 🔄 **Auto Refresh**: Automatically updates the database every hour with smart keyword rotation
- 🎯 **Smart Collection**: Continuously collects jobs until API limit is reached, then automatically resumes the next day
- 🔑 **Keyword Rotation**: Intelligently rotates through different job keywords each hour to collect diverse jobs without exceeding API limits
- ⚠️ **API Limit Detection**: Automatically detects when daily API limit is reached and displays user-friendly notifications
- 📊 **Real-time Status**: Displays job count, company count, and last refresh time with API limit status
- 🔎 **Advanced Search**: Search jobs by title, company, description, and location
- 🎨 **Beautiful UI**: Modern Morandi blue color scheme for a comfortable viewing experience
- 🏷️ **Smart Filtering**: Filter by job level (Entry, Mid-level, Senior) and minimum salary
- ➕ **Extensible**: Users can add new data sources through the web interface
- 📱 **Responsive Design**: Works seamlessly on desktop and mobile devices
- 🗄️ **PostgreSQL Support**: Production-ready with connection pooling and automatic migrations

## Tech Stack

- **Backend**: Python 3.11+ + Flask 3.0.0
- **Database**: SQLite (development) / PostgreSQL (production) with automatic migrations
- **Data Collection**: Adzuna API, BeautifulSoup, Feedparser, Requests
- **Frontend**: HTML5 + CSS3 + Vanilla JavaScript
- **Scheduler**: APScheduler for automatic hourly updates with keyword rotation
- **AI Service**: OpenAI API (optional, for enhanced job classification)
- **Production Server**: Gunicorn with connection pooling
- **Deployment**: Render.com ready with Procfile and runtime configuration

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Adzuna API credentials (free account available at https://developer.adzuna.com/)

## Installation & Setup

### Step 1: Clone or Download the Project

```bash
# If using git
git clone <repository-url>
cd Ascendo

# Or simply navigate to the project directory
cd path/to/Ascendo
```

### Step 2: Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

**Note**: If you encounter issues with `lxml` on Windows, you may need to install it separately:
```bash
pip install lxml
```

### Step 3: Configure Environment Variables

Create a `.env` file in the project root directory:

```bash
# Windows (PowerShell)
New-Item -Path .env -ItemType File

# Linux/Mac
touch .env
```

Add the following content to `.env`:

```env
# Adzuna API Credentials (Required)
ADZUNA_APP_ID=your_app_id_here
ADZUNA_APP_KEY=your_app_key_here

# OpenAI API Key (Optional - for AI features)
OPENAI_API_KEY=your_openai_api_key_here
```

#### How to Get Adzuna API Credentials

1. Visit https://developer.adzuna.com/
2. Sign up for a free account
3. Create a new application
4. Copy your `Application ID` and `Application Key`
5. Paste them into your `.env` file

**Note**: The Adzuna API is free and provides access to job listings from multiple job boards.

### Step 4: Run the Application

```bash
python app.py
```

The application will:
- Initialize the database
- Start the scheduler for automatic updates
- Begin collecting jobs from configured data sources
- Start the Flask web server

### Step 5: Access the Application

Open your web browser and navigate to:
```
http://localhost:5000
```

## Usage Guide

### Adding Data Sources

1. Open the web interface at http://localhost:5000
2. Scroll to the bottom and click **"⚙️ Admin Settings"**
3. In the "Add Data Source" section:
   - Select a source type from the dropdown
   - Enter the required information
   - Click **"Add Source"**

#### Supported Data Source Types

**1. Adzuna API** (Recommended)
- **Usage**: Enter search keywords (e.g., "software engineer", "data scientist")
- **Leave empty**: To fetch all available jobs
- **Example**: `software engineer`, `field service`, or leave blank for all jobs
- **Note**: Requires Adzuna API credentials in `.env` file

**2. RSS Feed**
- **Usage**: Enter the full RSS feed URL
- **Example**: `https://example.com/jobs.rss`
- **Note**: Must be a valid RSS/XML feed containing job listings

**3. Company URL**
- **Usage**: Enter the company's careers page URL
- **Example**: `https://company.com/careers`
- **Note**: The system will attempt to scrape job listings from the page

### Searching and Filtering Jobs

#### Search Features
- **Job Title Search**: Enter keywords in the search box (e.g., "software engineer")
- **Location Search**: Enter location in the location box (e.g., "New York", "California")
- **Combined Search**: Use both fields together for more precise results

#### Filter Options

**Level Filter** (Dropdown)
- **Entry Level**: Intern, new graduate, entry-level positions
- **Mid-level**: All positions that don't have "senior" and are not entry level
- **Senior Level**: Positions with "senior" in title or description

**Pay Filter** (Dropdown)
- **From $0**: Show all jobs
- **From $10,000**: Minimum salary threshold
- **From $50,000**: Minimum salary threshold
- **From $100,000**: Minimum salary threshold

**Details Button**
- Click to expand job descriptions (shows first 3 lines)
- Click again to hide descriptions

### Viewing Job Details

Each job card displays:
- **Job Title**: The position title
- **Company Name**: With company icon (initials)
- **Meta Information**: Category, location, work model, and estimated salary (all in one row)
- **Description**: Click "Details" button to view (optional)
- **Apply Button**: Direct link to the original job posting
- **Time Posted**: Relative time (e.g., "2 days ago")

### Manual Refresh

To manually trigger a data collection:
1. Open **"⚙️ Admin Settings"**
2. Click **"🔄 Refresh Now"** button
3. Wait for the collection to complete (may take a few minutes)

**Note**: Manual refresh runs asynchronously and won't block the interface. Collection continues in the background.

## Smart Collection Features

### Intelligent Keyword Rotation

The system automatically rotates through different job keywords each hour to collect diverse jobs:

- **Default Keywords**: software engineer, data scientist, product manager, marketing, sales, designer, developer, analyst, consultant, manager
- **Customizable**: Set your own keywords via `ADZUNA_KEYWORDS` environment variable
- **Benefit**: Collects thousands of jobs over time without exceeding daily API limits

**Example Collection Schedule**:
- **Hour 1**: Collect "software engineer" jobs (500 jobs)
- **Hour 2**: Collect "data scientist" jobs (500 jobs)
- **Hour 3**: Collect "product manager" jobs (500 jobs)
- ...continues through all keywords
- **Result**: 5,000+ unique jobs collected over 10 hours

### API Limit Management

- **Continuous Collection**: Collects jobs until daily API limit is reached (no fixed page limit)
- **Automatic Detection**: Detects when limit is reached (429 error) and stops gracefully
- **User Notification**: Displays clear notification banner when limit is reached
- **Auto Resume**: Automatically resumes collection the next day at midnight UTC
- **No Manual Intervention**: Fully automated process

**How It Works**:
1. System starts collecting jobs continuously
2. When API returns 429 (rate limit), collection stops
3. User sees notification: "Daily API limit reached. Collection will automatically resume tomorrow."
4. Next day, system automatically resets and continues collection

### Collection Strategy Options

**Option 1: Unlimited Collection (Recommended)**
- Don't set `ADZUNA_MAX_PAGES`
- System collects until API limit is reached
- Maximum jobs collected per day (depends on your API tier)

**Option 2: Conservative Collection**
- Set `ADZUNA_MAX_PAGES=10` (500 jobs per collection)
- Safer for free tier accounts
- Prevents hitting limit unexpectedly

**Option 3: Custom Keywords**
- Set `ADZUNA_KEYWORDS=field service,technical support,customer success`
- Focus on specific job categories
- Rotates through your custom keywords

## Project Structure

```
Job-Pulse-Agent/
├── app.py                      # Flask main application
├── ai_service.py               # AI service (optional, works without OpenAI API)
├── scheduler.py                # Scheduled tasks manager with keyword rotation
├── requirements.txt            # Python dependencies
├── runtime.txt                 # Python version specification
├── Procfile                    # Production server configuration
├── .env                        # Environment variables (create this file, not in repo)
├── .gitignore                  # Git ignore rules
├── README.md                   # This file - project documentation
├── DEPLOYMENT.md               # Render deployment guide
├── database.db                 # SQLite database (auto-created, not in repo)
├── data_collectors/            # Data collection modules
│   ├── __init__.py
│   ├── collector_manager.py   # Manages all collectors
│   ├── api_collector.py        # Adzuna API collector with limit detection
│   ├── rss_collector.py        # RSS feed collector
│   └── url_collector.py        # URL scraper
├── models/                     # Database models
│   ├── __init__.py
│   └── database.py             # SQLAlchemy models with auto-migration
├── templates/                  # HTML templates
│   └── index.html              # Main page template
└── static/                     # Static files
    ├── style.css               # Stylesheet (Morandi blue theme)
    └── script.js               # Frontend JavaScript with API limit notifications
```

## API Endpoints

The application provides the following REST API endpoints:

### GET `/api/jobs`
Get paginated list of jobs with optional filters.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20)
- `search` (string): Search term for title, company, or description
- `location` (string): Filter by location
- `level` (string): Filter by level (`entry`, `mid`, `senior`)
- `pay` (string): Minimum salary threshold (`0`, `10000`, `50000`, `100000`)

**Example:**
```
GET /api/jobs?page=1&per_page=20&search=engineer&location=California&level=senior&pay=50000
```

### GET `/api/refresh-status`
Get current refresh status and statistics.

**Response:**
```json
{
  "last_refresh": "2025-11-30T10:50:14.780668",
  "jobs_count": 5290,
  "sources_count": 2,
  "companies_count": 2303,
  "api_limit_reached": false,
  "api_limit_date": null
}
```

**Response Fields:**
- `last_refresh`: ISO timestamp of last data collection
- `jobs_count`: Total number of active jobs in database
- `sources_count`: Number of active data sources
- `companies_count`: Number of unique companies
- `api_limit_reached`: Boolean indicating if daily API limit was reached
- `api_limit_date`: ISO timestamp when limit was reached (null if not reached)

### GET `/api/sources`
Get all configured data sources.

### POST `/api/sources`
Add a new data source.

**Request Body:**
```json
{
  "type": "api",
  "url": "software engineer",
  "name": "Adzuna - Software Engineer"
}
```

### DELETE `/api/sources/<source_id>`
Delete (deactivate) a data source.

### POST `/api/refresh-now`
Manually trigger immediate data collection from all sources (non-blocking, runs in background).

**Response:**
```json
{
  "success": true,
  "message": "Refresh started in background. Check logs for progress."
}
```

### GET `/api/debug/jobs-count`
Debug endpoint to check job count in database (for troubleshooting).

**Response:**
```json
{
  "total_jobs": 5000,
  "active_jobs": 5000,
  "inactive_jobs": 0,
  "sample_jobs": [...]
}
```

## Database Schema

### Jobs Table
- `id`: Primary key
- `title`: Job title
- `company`: Company name
- `location`: Job location
- `description`: Full job description
- `url`: Unique job URL (used for deduplication)
- `source`: Source type (`api`, `rss`, `url`)
- `source_name`: Name of the data source
- `level`: Job level (`entry`, `mid`, `senior`, `executive`)
- `posted_date`: Original posting date
- `collected_date`: When the job was collected/updated
- `is_active`: Whether the job is currently active

### Job Sources Table
- `id`: Primary key
- `type`: Source type
- `url`: Source URL or search query
- `name`: Display name
- `is_active`: Whether the source is active
- `created_date`: When the source was added

### Refresh Status Table
- `id`: Primary key
- `last_refresh`: Last data collection timestamp
- `jobs_count`: Total number of active jobs
- `sources_count`: Number of active data sources
- `api_limit_reached`: Boolean flag for API limit status
- `api_limit_date`: Timestamp when API limit was reached (for daily reset)

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ADZUNA_APP_ID` | Yes | Adzuna API Application ID |
| `ADZUNA_APP_KEY` | Yes | Adzuna API Application Key |
| `OPENAI_API_KEY` | No | OpenAI API Key (for AI features) |
| `ADZUNA_MAX_PAGES` | No | Maximum pages per collection (default: unlimited, collects until API limit) |
| `ADZUNA_USE_KEYWORD_ROTATION` | No | Enable keyword rotation (default: true) |
| `ADZUNA_KEYWORDS` | No | Comma-separated keywords for rotation (default: 10 common job categories) |
| `FLASK_ENV` | No | Environment mode: `production` or `development` (default: development) |
| `DATABASE_URL` | No | PostgreSQL connection string (auto-provided by Render, uses SQLite if not set) |

### Port Configuration

By default, the application runs on port 5000. To change the port, edit `app.py`:

```python
app.run(debug=True, host='0.0.0.0', port=5000)  # Change 5000 to your desired port
```

## Troubleshooting

### Application Won't Start

**Issue**: Port 5000 is already in use
- **Solution**: Change the port in `app.py` or stop the process using port 5000

**Issue**: Module not found errors
- **Solution**: Ensure all dependencies are installed: `pip install -r requirements.txt`

**Issue**: Database errors
- **Solution**: Delete `database.db` and restart the application (database will be recreated)

### No Jobs Appearing

**Issue**: No jobs collected
- **Check**: Verify Adzuna API credentials in `.env` file
- **Check**: Ensure at least one data source is added
- **Check**: Click "🔄 Refresh Now" to manually trigger collection
- **Check**: Check browser console for JavaScript errors

**Issue**: Jobs not updating
- **Solution**: The system updates every hour automatically, or click "🔄 Refresh Now"

### API Collection Issues

**Issue**: Adzuna API returns no results
- **Check**: Verify API credentials are correct
- **Check**: Check API rate limits (free tier has limits)
- **Note**: First collection may take several minutes to fetch all jobs

**Issue**: "Daily API limit reached" notification appears
- **Explanation**: This is normal behavior - the system has collected the maximum allowed jobs for today
- **Action**: No action needed - collection will automatically resume tomorrow
- **Note**: You can still view and search all previously collected jobs

**Issue**: Collection stops before expected
- **Check**: Verify `ADZUNA_MAX_PAGES` is not set too low
- **Check**: Check if API limit was reached (see notification banner)
- **Solution**: Remove `ADZUNA_MAX_PAGES` to collect until limit, or increase the value

**Issue**: RSS feed not working
- **Check**: Verify the RSS URL is accessible and valid
- **Check**: Ensure the feed contains job listings in a standard format

**Issue**: URL scraping not working
- **Note**: Web scraping may fail if the website structure changes or blocks scrapers
- **Solution**: Try using RSS feed or API if available

## Development

### Running in Development Mode

The application runs in debug mode by default:
- Auto-reloads on code changes
- Detailed error messages
- Debug console enabled

### Adding New Data Collectors

1. Create a new collector class in `data_collectors/`
2. Implement the `collect(url)` method
3. Register it in `data_collectors/collector_manager.py`
4. Add the option to the source type dropdown in `templates/index.html`

### Database Migrations

The system automatically handles database migrations:
- **SQLite (Development)**: Automatically creates tables and adds new columns
- **PostgreSQL (Production)**: Auto-migration on startup, adds missing columns automatically
- **No Manual Steps**: Schema changes are detected and applied automatically

**Manual Migration** (if needed):
1. The system automatically detects and adds new columns
2. For major schema changes, the migration logic in `init_db()` handles it
3. No manual SQL scripts required

## Performance Notes

- **Initial Collection**: First data collection may take 10-30 minutes depending on the number of jobs
- **Hourly Updates**: With keyword rotation, each hour collects jobs for a different keyword (500 jobs per keyword)
- **Continuous Collection**: When limit is not set, system collects until API limit is reached (can collect 1000+ jobs in one session)
- **Pagination**: Jobs are displayed 20 per page by default
- **Search Performance**: Search is performed on the database, optimized with indexes
- **Database**: PostgreSQL connection pooling ensures stable performance under load

## Security Considerations

- **API Keys**: Never commit `.env` file to version control
- **Database**: SQLite is suitable for development; use PostgreSQL for production
- **CORS**: Currently enabled for all origins (restrict in production)
- **Input Validation**: User inputs are sanitized, but additional validation recommended for production

## License

This project is provided as-is for educational and personal use.

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review browser console for JavaScript errors
3. Check application logs in the terminal
4. Verify all environment variables are set correctly

## Changelog

### Current Version
- ✅ Multi-source data collection (Adzuna API, RSS, URL)
- ✅ Automatic hourly updates with smart keyword rotation
- ✅ Advanced search and filtering
- ✅ Beautiful Morandi blue UI
- ✅ Job level classification (Entry, Mid, Senior)
- ✅ Salary-based filtering
- ✅ Responsive design
- ✅ Real-time statistics with API limit status
- ✅ Smart API limit detection and user notifications
- ✅ Continuous collection until daily limit reached
- ✅ Automatic daily limit reset
- ✅ PostgreSQL support with connection pooling
- ✅ Asynchronous data collection (non-blocking)
- ✅ Database auto-migration for schema updates

## Cloud Deployment (Render)

This application can be easily deployed to Render.com for free hosting.

### Prerequisites for Deployment

- GitHub account
- Render account (sign up at https://render.com)
- Adzuna API credentials

### Deployment Steps

#### Step 1: Push Code to GitHub

1. Create a new repository on GitHub
2. Push your code to the repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/ascendo-jobs.git
   git push -u origin main
   ```

#### Step 2: Create Render Web Service

1. Log in to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `ascendo-jobs` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Plan**: Free (or choose a paid plan)

#### Step 3: Configure Environment Variables

In Render Dashboard → Your Service → Environment, add:

```
ADZUNA_APP_ID=your_app_id_here
ADZUNA_APP_KEY=your_app_key_here
OPENAI_API_KEY=your_openai_key_here (optional)
FLASK_ENV=production
ADZUNA_USE_KEYWORD_ROTATION=true (optional, default: true)
ADZUNA_KEYWORDS=software engineer,data scientist,product manager (optional)
ADZUNA_MAX_PAGES=10 (optional, default: unlimited)
```

**Recommended Settings**:
- `ADZUNA_USE_KEYWORD_ROTATION=true`: Enable smart keyword rotation
- `ADZUNA_MAX_PAGES`: Leave unset to collect until API limit, or set to 10-20 for conservative collection

#### Step 4: Create PostgreSQL Database

1. In Render Dashboard, click **"New +"** → **"PostgreSQL"**
2. Name it (e.g., `ascendo-db`)
3. Select **Free** plan
4. Render will automatically provide `DATABASE_URL` environment variable
5. Go back to your Web Service → Environment
6. The `DATABASE_URL` should already be there (automatically linked)

#### Step 5: Deploy

1. Click **"Create Web Service"**
2. Render will automatically:
   - Clone your repository
   - Install dependencies
   - Build the application
   - Start the service
3. Wait for deployment to complete (usually 2-5 minutes)
4. Your app will be available at: `https://your-service-name.onrender.com`

### Post-Deployment

1. **First Data Collection**: The app will start collecting jobs automatically. This may take 10-30 minutes for the first run.
2. **Access Admin Panel**: Navigate to your deployed URL and click "⚙️ Admin Settings" to manage data sources.
3. **Monitor Logs**: Check Render Dashboard → Logs for any errors or issues.

### Important Notes

- **Free Tier Limitations**: 
  - Services spin down after 15 minutes of inactivity
  - First request after spin-down may take 30-60 seconds
  - Consider upgrading to a paid plan for always-on service
  
- **Database**: PostgreSQL is automatically configured via `DATABASE_URL`
- **SSL**: Render provides free SSL certificates automatically
- **Custom Domain**: You can add a custom domain in Settings → Custom Domain

### Troubleshooting Deployment

**Issue**: Build fails
- Check that `Procfile` exists and is correct
- Verify `requirements.txt` includes all dependencies
- Check build logs in Render Dashboard

**Issue**: Application crashes on startup
- Verify all environment variables are set
- Check that `DATABASE_URL` is configured
- Review application logs

**Issue**: Database connection errors
- Ensure PostgreSQL service is created and linked
- Verify `DATABASE_URL` is in environment variables
- Check that `psycopg2-binary` is in requirements.txt

---

**Built with ❤️ for the Ascendo AI Community**
