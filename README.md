# Job Application Tracker

A production-ready Flask web application that scrapes job postings from LinkedIn, Handshake, and other platforms, parses job details automatically, and saves them to Google Sheets for easy tracking.

## Features

- 🔐 **Google OAuth 2.0**: Secure authentication with your Google account
- 🔍 **Automatic Job Parsing**: Paste a job URL and extract position, company, location, salary, and more
- 📋 **Multi-Platform Support**: Works with LinkedIn, Handshake, Indeed, Glassdoor, and other job boards
- ✏️ **Review & Edit**: Review parsed data and make corrections before saving
- 💰 **Salary Normalization**: Automatically converts hourly/monthly salaries to annual equivalents
- 🔄 **Duplicate Detection**: Prevents adding the same job URL twice
- 🗑️ **Trash Sheet**: Replaced/deleted jobs are moved to a separate "Trash" sheet
- 📊 **Google Sheets Integration**: All data stored in your own Google Sheet
- 🧪 **Test Suite**: Comprehensive pytest tests for reliability
- 📝 **Structured Logging**: Production-ready logging for debugging

## Architecture

This application follows Flask best practices with a modular structure:

```
job-tracker-web/
├── app/                     # Main application package
│   ├── __init__.py          # Flask app factory with logging and error handlers
│   ├── auth.py              # Google OAuth 2.0 authentication blueprint
│   ├── routes.py            # Main UI routes blueprint
│   ├── sheets.py            # Google Sheets operations
│   └── parsers/             # Job parsing modules
│       ├── __init__.py      # Parser registry and main interface
│       ├── linkedin.py      # LinkedIn parser
│       ├── handshake.py     # Handshake parser
│       └── generic.py       # Fallback parser
├── app.py                   # Application entry point
├── requirements.txt         # Python dependencies
├── pytest.ini              # Test configuration
├── tests/                   # Unit tests
├── templates/               # HTML templates
└── static/                  # CSS and static files
```

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Google Cloud project with OAuth 2.0 credentials
- Google account for authentication

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <your-repo-url>
   cd job-tracker-web
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Google OAuth** (see detailed instructions below)

3. **Set environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

4. **Run the app**:
   ```bash
   flask run
   ```

5. **Run tests**:
   ```bash
   pytest
   ```

## Google OAuth 2.0 Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **Google Sheets API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Sheets API" and enable it

### Step 2: Configure OAuth Consent Screen

1. Go to "APIs & Services" > "OAuth consent screen"
2. Choose "External" user type
3. Fill in app information:
   - App name: "Job Tracker"
   - User support email: Your email
   - Developer contact: Your email
4. Add scopes:
   - `https://www.googleapis.com/auth/spreadsheets`
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`
   - `openid`
5. Add test users (for development): Your Google account email

### Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Choose "Web application"
4. Configure authorized redirect URIs:
   - For local: `http://localhost:5000/oauth2callback`
   - For production: `https://your-app.onrender.com/oauth2callback`
5. Download the JSON file (keep it secure!)

### Step 4: Configure Environment Variables

Create `.env` file:
```bash
SECRET_KEY=your-random-secret-key-here
GOOGLE_OAUTH_CLIENT_SECRET_FILE=/path/to/client_secret.json
OAUTH_REDIRECT_URI=http://localhost:5000/oauth2callback  # Optional, for local dev
```

Generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Deployment to Render

### Step 1: Prepare Repository

```bash
git add .
git commit -m "Deploy to Render"
git push origin main
```

### Step 2: Create Render Web Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" > "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `job-tracker-web`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

### Step 3: Set Environment Variables

| Key | Value |
|-----|-------|
| `SECRET_KEY` | Random 32+ character string |
| `GOOGLE_OAUTH_CLIENT_SECRET_FILE` | `/etc/secrets/google_oauth_client_secret.json` |

### Step 4: Add Secret File

In Render dashboard:
1. Go to your service > "Settings"
2. Find "Secret Files" section
3. Click "Add Secret File"
   - **Filename**: `/etc/secrets/google_oauth_client_secret.json`
   - **Contents**: Paste your OAuth client secret JSON

### Step 5: Update OAuth Redirect URI

1. Go to Google Cloud Console > "Credentials"
2. Edit your OAuth client
3. Add authorized redirect URI:
   ```
   https://your-app.onrender.com/oauth2callback
   ```

### Step 6: Deploy

Click "Create Web Service" and wait for deployment to complete.

## Usage

1. **Visit the app** and log in with Google
2. **Enter your Google Sheet URL** (any Sheet you have Editor access to)
3. **Paste a job URL** from LinkedIn, Handshake, Indeed, etc.
4. **Review the parsed data** and make any corrections
5. **Save to Sheet** - the job is added with today's date

### Supported Job Boards

- ✅ LinkedIn
- ✅ Handshake (with text paste option)
- ✅ Indeed
- ✅ Glassdoor
- ✅ Generic fallback for other sites

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_parsers_linkedin.py

# Run with verbose output
pytest -v
```

### Adding a New Parser

1. Create `app/parsers/yoursite.py`
2. Implement `parse(html: str, job_url: str) -> dict` function
3. Add to `PARSERS` dict in `app/parsers/__init__.py`
4. Write tests in `tests/test_parsers_yoursite.py`

### Code Structure

- **Factory Pattern**: `create_app()` in `app/__init__.py` creates and configures the Flask app
- **Blueprints**: Routes organized into `auth_bp` (authentication) and `main_bp` (app routes)
- **Logging**: Structured logging configured at app startup, logs to stdout
- **Error Handling**: Centralized error handlers for 400/401/403/404/500
- **OAuth Flow**: Automatic token refresh with session-based credential storage

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | - | Flask session secret (32+ random chars) |
| `GOOGLE_OAUTH_CLIENT_SECRET_FILE` | Yes | - | Path to OAuth client secret JSON |
| `OAUTH_REDIRECT_URI` | No | Production URL | OAuth callback URL (for local dev) |
| `LOG_LEVEL` | No | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Troubleshooting

### "Please log in with Google to continue"

- Your OAuth session expired
- Click the login link to re-authenticate

### "Could not connect to your Google Sheet"

- Make sure you have Editor access to the Sheet
- Verify the Sheet URL is correct
- Try logging out and back in

### "Error parsing job"

- Some job sites may have changed their HTML structure
- Try the generic fallback or report an issue

### OAuth Errors

- Verify redirect URI matches exactly in Google Console
- Check that OAuth client secret file is properly configured
- Ensure all required scopes are added to consent screen

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `pytest`
5. Submit a pull request

## License

MIT License - see LICENSE file

## Security Notes

- Never commit `client_secret.json` or `.env` files
- Use environment variables for all secrets
- OAuth tokens are stored in session (server-side only)
- Credentials automatically refresh when expired
