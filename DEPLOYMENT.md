# Render Deployment Guide

This guide will help you deploy Ascendo AI Community Jobs to Render.com.

## Pre-Deployment Preparation

### 1. Ensure All Files Are Ready

✅ Files that should be created:
- `Procfile` - Render startup command
- `runtime.txt` - Python version specification
- `requirements.txt` - Includes gunicorn and psycopg2-binary
- `models/database.py` - Supports PostgreSQL
- `app.py` - Supports production environment configuration

### 2. Prepare Git Repository

```bash
# Initialize Git (if not already done)
git init

# Ensure .gitignore contains the following
# .env
# __pycache__/
# *.db
# *.pyc

# Commit all files
git add .
git commit -m "Prepare for Render deployment"

# Push to GitHub
git remote add origin https://github.com/yourusername/ascendo-jobs.git
git branch -M main
git push -u origin main
```

## Render Deployment Steps

### Step 1: Create Render Account

1. Visit https://render.com
2. Sign in with your GitHub account (recommended)
3. Authorize Render to access your GitHub repositories

### Step 2: Create PostgreSQL Database

1. In Render Dashboard, click **"New +"**
2. Select **"PostgreSQL"**
3. Configure:
   - **Name**: `ascendo-db` (or your preferred name)
   - **Database**: `ascendo` (optional, default is fine)
   - **User**: Auto-generated
   - **Region**: Choose the region closest to you
   - **Plan**: Free (or choose a paid plan)
4. Click **"Create Database"**
5. Note the database connection information (usually not needed manually, Render handles it automatically)

### Step 3: Create Web Service

1. In Render Dashboard, click **"New +"**
2. Select **"Web Service"**
3. Connect your GitHub repository:
   - If already authorized, select your repository
   - If not, click "Connect GitHub" and authorize
4. Select the `Ascendo` repository
5. Configure the service:

   **Basic Settings:**
   - **Name**: `ascendo-jobs` (or your preferred name)
   - **Region**: Choose the same region as the database (recommended)
   - **Branch**: `main` (or your main branch)
   - **Root Directory**: Leave empty (if project is in root directory)

   **Build & Start:**
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

   **Plan:**
   - **Plan**: Free (or choose a paid plan)

### Step 4: Configure Environment Variables

In the Web Service settings page, find the **"Environment"** section and add the following variables:

```
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
OPENAI_API_KEY=your_openai_key (optional)
FLASK_ENV=production
ADZUNA_MAX_PAGES=10 (optional, default is 10 pages, 50 jobs per page)
ADZUNA_USE_KEYWORD_ROTATION=true (optional, default is true)
ADZUNA_KEYWORDS=software engineer,data scientist,product manager,marketing,sales (optional)
```

**Important**: 
- `DATABASE_URL` is automatically provided from the PostgreSQL service, no need to add manually
- `ADZUNA_MAX_PAGES`: Limits the maximum number of pages per collection to avoid exceeding Adzuna API daily request limits (free tier has daily limits)
- `ADZUNA_USE_KEYWORD_ROTATION`: When enabled (default), the scheduler will rotate through different keywords each hour to collect more diverse jobs without exceeding API limits
- `ADZUNA_KEYWORDS`: Comma-separated list of keywords to rotate through. If not set, uses default keywords covering various job categories

### Step 5: Link Database

1. In Web Service settings page, find the **"Connections"** section
2. Click **"Link Database"**
3. Select your created PostgreSQL database
4. Render will automatically add `DATABASE_URL` to environment variables

### Step 6: Deploy

1. Click **"Create Web Service"**
2. Render will start building and deploying:
   - Clone repository
   - Install dependencies (approximately 2-3 minutes)
   - Build application
   - Start service
3. Wait for deployment to complete (usually 3-5 minutes)
4. After successful deployment, you will see a green "Live" status

### Step 7: Access Application

After deployment, your application will be available at:
```
https://your-service-name.onrender.com
```

## Post-Deployment Operations

### 1. Verify Deployment

1. Visit your application URL
2. Check if the page loads normally
3. Check if Admin Settings is accessible
4. View Render Dashboard → Logs to confirm there are no errors

### 2. Initial Data Collection

- After application starts, the scheduler will automatically begin working
- Initial collection may take 10-30 minutes
- Can be manually triggered via Admin Settings → "🔄 Refresh Now"

**Smart Keyword Rotation (Recommended)**:
- By default, the scheduler uses keyword rotation to collect more diverse jobs
- Each hour, it collects jobs for a different keyword (e.g., "software engineer", "data scientist", etc.)
- This allows you to collect thousands of jobs over time without exceeding daily API limits
- Example: With 10 keywords and 10 pages each, you can collect 5,000 unique jobs over 10 hours
- Customize keywords via `ADZUNA_KEYWORDS` environment variable

### 3. Monitoring and Logs

- **Logs**: Render Dashboard → Your Service → Logs
- **Metrics**: Render Dashboard → Your Service → Metrics
- **Events**: Render Dashboard → Your Service → Events

## Common Issues

### Q: Deployment fails, build error
**A**: Check:
- Whether `Procfile` exists and format is correct
- Whether `requirements.txt` includes all dependencies
- Whether Python version is correct (runtime.txt)
- View specific error messages in build logs

### Q: Application crashes immediately after startup
**A**: Check:
- Whether all environment variables are set
- Whether `DATABASE_URL` is correct (should be automatically provided)
- View error messages in application logs

### Q: Database connection fails
**A**: Check:
- Whether PostgreSQL service is created and running
- Whether Web Service is linked to the database
- Whether `DATABASE_URL` environment variable exists

### Q: Free tier service hibernation
**A**: 
- Render free tier hibernates after 15 minutes of inactivity
- First access to a hibernated service takes 30-60 seconds to wake up
- Consider using a paid plan to keep the service always running
- Or use an external service to periodically ping your URL to keep it active

## Upgrade to Paid Plan

If you need:
- Always-on service (no hibernation)
- Faster response times
- More resources
- Priority support

You can upgrade to Render's paid plan (starting at $7/month).

## Custom Domain

1. In Web Service settings, find **"Custom Domains"**
2. Click **"Add Custom Domain"**
3. Enter your domain name
4. Follow the instructions to configure DNS records
5. Render will automatically provide SSL certificate

## Database Backup

1. In PostgreSQL service settings
2. Find the **"Backups"** section
3. You can manually create backups or set up automatic backups
4. Paid plans include automatic daily backups

## Update Application

When you push new code to GitHub:
1. Render will automatically detect changes
2. Automatically trigger new deployment
3. Zero-downtime deployment (blue-green deployment)

## Rollback Deployment

If you need to rollback to a previous version:
1. In Render Dashboard → Your Service → Events
2. Find the previous successful deployment
3. Click "Redeploy"

## Cost Estimation

### Free Tier
- Web Service: Free (with hibernation limitations)
- PostgreSQL: Free (requires upgrade or data export after 90 days)
- Total: $0/month

### Starter Plan
- Web Service: $7/month
- PostgreSQL: $0/month (free tier available)
- Total: $7/month

## Security Recommendations

1. **Environment Variables**: Never commit API keys to Git
2. **Database**: Use strong passwords (Render auto-generates)
3. **HTTPS**: Render automatically provides SSL certificates
4. **Backup**: Regularly backup database
5. **Monitoring**: Regularly check logs and metrics

## Support

If you encounter issues:
1. Check Render documentation: https://render.com/docs
2. Check application logs
3. View Render community forum
4. Contact Render support (paid users)

---

**After deployment, your application will be accessible via the internet without requiring users to install anything themselves!**

