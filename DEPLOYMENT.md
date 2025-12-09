# Deployment Guide

This guide covers how to run the Job Tracker web application locally and how to deploy it to production platforms like Render.com.

---

## Local Development Setup

### Prerequisites

- Python 3.7 or higher
- Git
- Google Service Account credentials (see README.md for setup)

### Step 1: Clone the Repository

```bash
git clone https://github.com/fundukk/job-application-tracker.git
cd job-application-tracker/job-tracker-web
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Credentials

1. Place your `credentials.json` file in the project root
   - This file contains your Google Service Account credentials
   - **NEVER commit this file to Git** (already in .gitignore)

2. (Optional) Create `config.json` for local configuration
   - Also ignored by Git for security

### Step 5: Run the Application

**Option A: Using Flask development server**
```bash
flask run
```

**Option B: Using Python directly**
```bash
python app.py
```

The app will be available at `http://localhost:5000` or `http://127.0.0.1:5000`

### Step 6: Test the Application

1. Open browser to `http://localhost:5000`
2. Enter your Google Sheet URL
3. Add a job URL to test the scraping functionality
4. Verify data appears in your Google Sheet

---

## Production Deployment (Render.com)

Render.com is a modern Platform-as-a-Service (PaaS) that makes deployment simple.

### Prerequisites

- GitHub account with your repository pushed
- Render.com account (free tier available)
- Google Service Account credentials

### Step 1: Prepare Your Repository

1. **Ensure all code is pushed to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Verify `.gitignore` excludes secrets:**
   - `credentials.json` ✓
   - `config.json` ✓
   - `venv/` ✓
   - `.env` files ✓

3. **Ensure `requirements.txt` is up to date:**
   ```bash
   pip freeze > requirements.txt
   ```

### Step 2: Add Production Dependencies

Add `gunicorn` to `requirements.txt` (if not already present):

```bash
pip install gunicorn
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Add gunicorn for production"
git push
```

### Step 3: Create a New Web Service on Render

1. **Log in to Render.com**
   - Go to https://render.com
   - Sign in or create account

2. **Create New Web Service**
   - Click "New +" button → "Web Service"
   - Connect your GitHub account if not already connected
   - Select repository: `fundukk/job-application-tracker`

3. **Configure Service Settings**

   | Setting | Value |
   |---------|-------|
   | **Name** | `job-tracker-web` |
   | **Region** | Choose closest to your users |
   | **Branch** | `main` |
   | **Root Directory** | `job-tracker-web` |
   | **Runtime** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `gunicorn app:app` |
   | **Instance Type** | Free (or paid for production) |

4. **Advanced Settings (Optional)**
   - **Auto-Deploy**: Enable (deploys on every push to main)
   - **Health Check Path**: `/` (optional)

### Step 4: Configure Environment Variables

Render doesn't support file uploads directly, so you need to handle `credentials.json` carefully.

#### Option A: Environment Variable (Recommended)

1. Copy the **entire contents** of your `credentials.json` file

2. In Render dashboard, go to **Environment** tab

3. Add a new environment variable:
   - **Key**: `GOOGLE_CREDENTIALS_JSON`
   - **Value**: Paste the entire JSON contents

4. Update `core/sheets.py` to read from environment variable:

```python
import os
import json

def get_gspread_client():
    # Try environment variable first (production)
    creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    if creds_json:
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
    else:
        # Fall back to file (local development)
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            'credentials.json',
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
    
    return gspread.authorize(creds)
```

#### Option B: Secret Files (Render Paid Plans)

If you have a paid Render plan, you can use Secret Files:

1. Go to **Environment** tab
2. Scroll to **Secret Files**
3. Add file:
   - **Filename**: `credentials.json`
   - **Contents**: Paste your JSON contents

This creates the file at runtime without committing to Git.

### Step 5: Deploy

1. Click **"Create Web Service"**
2. Render will automatically:
   - Clone your repository
   - Install dependencies
   - Start your app with gunicorn

3. Monitor the deployment logs in real-time
4. Once complete, you'll see "Your service is live 🎉"

### Step 6: Access Your App

- Your app will be available at: `https://job-tracker-web.onrender.com`
- Or custom domain if configured

### Step 7: Test Production Deployment

1. Visit your Render URL
2. Test with a Google Sheet URL
3. Add a job URL
4. Verify data appears in Google Sheet
5. Check Render logs for any errors

---

## Deployment to Other Platforms

### Heroku

1. **Install Heroku CLI**
   ```bash
   brew install heroku/brew/heroku
   ```

2. **Create Procfile**
   ```
   web: gunicorn app:app
   ```

3. **Deploy**
   ```bash
   heroku login
   heroku create job-tracker-web
   heroku config:set GOOGLE_CREDENTIALS_JSON='<paste JSON here>'
   git push heroku main
   ```

### Railway.app

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub"
3. Select repository
4. Set root directory: `job-tracker-web`
5. Add environment variable: `GOOGLE_CREDENTIALS_JSON`
6. Railway auto-detects Python and deploys

### DigitalOcean App Platform

1. Go to https://cloud.digitalocean.com/apps
2. Click "Create App" → GitHub
3. Select repository and branch
4. Set source directory: `job-tracker-web`
5. Run Command: `gunicorn app:app`
6. Add environment variables
7. Deploy

---

## Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_CREDENTIALS_JSON` | Google Service Account JSON (as string) | Yes (production) |
| `FLASK_ENV` | Set to `production` for production | Recommended |
| `FLASK_SECRET_KEY` | Secret key for session management | Recommended |
| `PORT` | Port to run on (auto-set by most PaaS) | Auto |

---

## Troubleshooting

### Build Failures

**Issue**: Dependencies fail to install
- **Solution**: Verify `requirements.txt` has no typos
- Run `pip install -r requirements.txt` locally first

**Issue**: Python version mismatch
- **Solution**: Add `runtime.txt` with: `python-3.11.0`

### Runtime Errors

**Issue**: `credentials.json not found`
- **Solution**: Ensure environment variable is set correctly
- Update code to read from `GOOGLE_CREDENTIALS_JSON` env var

**Issue**: Google Sheets API errors
- **Solution**: Verify service account email is added to sheet with edit permissions
- Check API is enabled in Google Cloud Console

**Issue**: Session errors
- **Solution**: Set `FLASK_SECRET_KEY` environment variable
- Add to `app.py`: `app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-key-only')`

### Performance Issues

**Issue**: Slow response times
- **Solution**: Upgrade from free tier to paid tier
- Implement caching for job scraping results

**Issue**: App goes to sleep (free tier)
- **Solution**: Use a service like UptimeRobot to ping your app
- Or upgrade to paid tier for 24/7 uptime

---

## Security Best Practices

### ✅ DO

- Store secrets in environment variables, never in code
- Use `.gitignore` to exclude `credentials.json`, `config.json`, `.env`
- Use HTTPS in production (handled by PaaS automatically)
- Rotate service account keys periodically
- Restrict service account permissions to only Sheets API
- Add rate limiting for job scraping endpoints
- Validate and sanitize all user inputs

### ❌ DON'T

- Commit `credentials.json` or any secrets to Git
- Use the same credentials for development and production
- Share service account keys publicly
- Disable HTTPS/SSL
- Ignore security updates for dependencies

---

## Monitoring and Logs

### Render Logs

- Access via Render dashboard → Your Service → "Logs" tab
- Shows real-time application logs
- Filter by date/time range

### Adding Custom Logging

Add to `app.py`:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Use in routes
@app.route('/add_job', methods=['POST'])
def add_job():
    logger.info(f"Job URL submitted: {job_url}")
    # ... rest of code
```

---

## Scaling Considerations

### When to Scale

- Response times > 3 seconds consistently
- Multiple concurrent users
- High job scraping volume
- Need for 24/7 uptime

### Scaling Options

1. **Vertical Scaling**: Upgrade instance type (more CPU/RAM)
2. **Horizontal Scaling**: Add more instances (requires load balancer)
3. **Caching**: Implement Redis for session + job data caching
4. **Queue System**: Use Celery + Redis for background job scraping
5. **CDN**: Serve static files from CloudFlare or similar

---

## Backup and Recovery

### Database (Google Sheets)

- Google Sheets has built-in version history
- Access: File → Version history → See version history
- Can restore to any previous version

### Code

- Use Git tags for releases: `git tag v1.0.0`
- Keep production branch stable
- Test in staging before production deploy

### Credentials

- Store backup of `credentials.json` in secure location (1Password, LastPass, etc.)
- Document service account email for recovery
- Keep note of which Google Cloud project it belongs to

---

## CI/CD Pipeline (Optional Advanced)

For automated testing and deployment, add GitHub Actions workflow:

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Render

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd job-tracker-web
          pip install -r requirements.txt
      
      - name: Run tests (if you add them)
        run: |
          cd job-tracker-web
          pytest
      
      - name: Trigger Render Deploy
        run: |
          curl ${{ secrets.RENDER_DEPLOY_HOOK }}
```

---

## Support and Resources

- **Flask Documentation**: https://flask.palletsprojects.com/
- **Render Documentation**: https://render.com/docs
- **Google Sheets API**: https://developers.google.com/sheets/api
- **Project README**: [README.md](README.md)
- **Architecture Guide**: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## Quick Reference Commands

```bash
# Local development
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
python app.py

# Update dependencies
pip freeze > requirements.txt

# Check for security vulnerabilities
pip install safety
safety check

# Git workflow
git add .
git commit -m "Your message"
git push origin main

# View logs (when running locally)
python app.py  # logs appear in terminal

# Deactivate virtual environment
deactivate
```

---

**Last Updated**: December 2025  
**Maintainer**: fundukk  
**Repository**: https://github.com/fundukk/job-application-tracker
