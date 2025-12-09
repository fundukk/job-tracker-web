# Job Tracker Web App

A Flask-based web application for tracking job applications. Users can connect their Google Sheet and automatically parse job postings to add them as entries.

## Features

- 🔗 Connect to any Google Sheet via URL or ID
- 📝 Parse job postings from various sources (LinkedIn, Indeed, Handshake, etc.)
- ✅ Automatically extract job details (position, company, location, salary, etc.)
- 📊 Add parsed data directly to your Google Sheet
- 🔒 Uses Google service account (no OAuth required)

## Prerequisites

- Python 3.7+
- Google Cloud service account with Sheets API enabled
- `credentials.json` file from your service account

## Installation

1. **Clone or download this project**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Add your service account credentials:**
   - Place your `credentials.json` file in the project root directory (same folder as `app.py`)
   - This file should contain your Google service account credentials

4. **Share your Google Sheet:**
   - Open your Google Sheet
   - Click "Share" button
   - Add your service account email (found in `credentials.json` as `client_email`)
   - Give it **Editor** access

## Running the App

### Option 1: Using Flask CLI
```bash
flask run
```

### Option 2: Using Python
```bash
python app.py
```

The app will start at `http://127.0.0.1:5000`

## Usage

1. **Step 1 - Connect Sheet:**
   - Open the web app in your browser
   - Enter your Google Sheet URL or ID
   - Click "Connect Sheet"

2. **Step 2 - Add Job:**
   - Paste the job posting URL
   - Click "Add Job"
   - The app will scrape and parse the job details
   - Data will be automatically added to your sheet

3. **Success:**
   - View the parsed job details
   - Add another job or change sheets

## Project Structure

```
job-tracker-web/
│
├─ app.py                 # Flask application and routes
│
├─ core/                  # Core modules
│   ├─ __init__.py
│   ├─ sheets.py         # Google Sheets integration
│   ├─ jobs.py           # Job scraping with parser routing
│   └─ parsers/          # Modular parser system
│       ├─ __init__.py
│       ├─ linkedin.py   # LinkedIn parser
│       ├─ handshake.py  # Handshake parser
│       └─ generic.py    # Generic/fallback parser
│
├─ templates/            # HTML templates
│   ├─ index.html        # Step 1: Connect sheet
│   ├─ job.html          # Step 2: Add job
│   └─ success.html      # Success page
│
├─ static/               # Static files
│   └─ style.css         # Styles
│
├─ requirements.txt      # Python dependencies
├─ credentials.json      # Google service account (NOT in git)
├─ README.md            # This file
└─ MIGRATION.md         # Parser migration guide
```

## Parser Architecture

The project uses a **modular parser system** with a feature flag for safe migrations:

### Current Structure

```
core/
├── jobs.py              # Main entry point with USE_NEW_PARSER flag
└── parsers/             # Modular parser system
    ├── linkedin.py      # LinkedIn-specific parser
    ├── handshake.py     # Handshake-specific parser
    └── generic.py       # Fallback for other sites
```

### Feature Flag

The `USE_NEW_PARSER` flag in `core/jobs.py` lets you switch between:
- **Legacy parser** (simple placeholder, currently active)
- **New modular parsers** (extensible, ready for your custom logic)

```python
# In core/jobs.py
USE_NEW_PARSER = False  # Safe default, uses simple placeholder
```

### Adding Your Own Parsing Logic

**Option 1: Keep it simple (current)**
- Edit `parse_job_html()` in `core/jobs.py`
- Add your scraping logic directly

**Option 2: Use modular system (recommended)**
1. Set `USE_NEW_PARSER = True` in `core/jobs.py`
2. Edit parser files in `core/parsers/`:
   - `linkedin.py` - LinkedIn-specific parsing
   - `handshake.py` - Handshake-specific parsing
   - `generic.py` - Fallback for other sites
3. Each parser follows the same interface:
   ```python
   def parse(html: str, job_url: str) -> dict:
       return {"title": "...", "company": "...", ...}
   ```

**See [MIGRATION.md](MIGRATION.md) for detailed migration guide.**

### Changing the Secret Key

Before deploying to production, change the `app.secret_key` in `app.py`:
```python
app.secret_key = "your-random-secret-key-here"
```

Generate a secure random key:
```python
import secrets
print(secrets.token_hex(32))
```

## Expected Sheet Format

The app expects these columns in your Google Sheet (will be auto-created if missing):

| DateApplied | Company | Location | Position | Link | Salary | JobType | Remote | Status | Source | Notes |
|-------------|---------|----------|----------|------|--------|---------|--------|--------|--------|-------|

## Troubleshooting

### "credentials.json not found"
- Make sure `credentials.json` is in the project root directory
- Check the file name is exactly `credentials.json`

### "Permission denied" or "Unable to access sheet"
- Verify you've shared the Google Sheet with your service account email
- Check that the service account has **Editor** access
- Confirm the Sheets API is enabled in your Google Cloud project

### Scraping errors
- Some websites block automated requests
- You may need to add more sophisticated headers or use Selenium
- Consider rate limiting to avoid being blocked

## Security Notes

- Never commit `credentials.json` to version control
- Add `credentials.json` to `.gitignore`
- Use environment variables for the secret key in production
- Consider adding rate limiting for production use

## License

MIT License - feel free to modify and use as needed.
