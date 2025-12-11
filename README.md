# Job Application Tracker

A Flask web application that scrapes job postings from LinkedIn and Handshake, parses job details automatically, and saves them to Google Sheets for easy tracking.

## Features

- 🔍 **Automatic Job Parsing**: Paste a job URL and the app extracts position, company, location, salary, and more
- 📋 **Multi-Platform Support**: Works with LinkedIn, Handshake, Indeed, Glassdoor, and other job boards
- ✏️ **Review & Edit**: Review parsed data and make corrections before saving
- 💰 **Salary Normalization**: Automatically converts hourly/monthly salaries to annual equivalents
- 🔄 **Duplicate Detection**: Prevents adding the same job URL twice
- 🗑️ **Trash Sheet**: Replaced/deleted jobs are moved to a separate "Trash" sheet
- 📊 **Google Sheets Integration**: All data stored in your own Google Sheet

## Project Structure

```
job-tracker-web/
├── app.py                    # Flask application and routes (entrypoint)
├── google_client.py          # Google Sheets authentication module
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
├── core/                    # Core functionality
│   ├── jobs.py              # Job URL parsing logic
│   ├── sheets.py            # Google Sheets operations
│   ├── salary.py            # Salary normalization
│   └── parsers/             # Platform-specific parsers
├── templates/               # HTML templates
└── static/                  # CSS and static files
```

## Local Development Setup

### Prerequisites

- Python 3.8 or higher
- Google Cloud service account with Sheets API enabled
- Google Sheet for storing job applications

### Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd job-tracker-web
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up Google Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **Google Sheets API** and **Google Drive API**
4. Create a service account:
   - Go to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Give it a name and click "Create"
   - Grant it "Editor" role
   - Click "Done"
5. Create a key:
   - Click on the service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create New Key"
   - Choose **JSON** format
   - Download the file and save it as `credentials.json` in the project root

### Step 5: Create Google Sheet

1. Create a new Google Sheet
2. Share it with the service account email (found in `credentials.json` under `client_email`)
3. Give it **Editor** permissions
4. Copy the sheet URL or ID

### Step 6: Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and set:
```bash
SECRET_KEY=your-random-secret-key-here
GOOGLE_SERVICE_ACCOUNT_FILE=credentials.json
```

Generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 7: Run the Application

**Option A: Flask Development Server**
```bash
flask run
```

**Option B: Gunicorn (Production-like)**
```bash
gunicorn app:app
```

Visit `http://127.0.0.1:5000` in your browser.

## Deployment to Render

### Step 1: Prepare Your Repository

1. Ensure all changes are committed to Git
2. Push to GitHub:
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

### Step 2: Create Render Web Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" and select "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `job-tracker` (or your choice)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free (or your preference)

### Step 3: Set Environment Variables

In the Render dashboard, go to "Environment" and add:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | Generate using `python -c "import secrets; print(secrets.token_hex(32))"` |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | `/etc/secrets/credentials.json` |

### Step 4: Add Credentials as Secret File

1. In Render dashboard, go to "Environment" > "Secret Files"
2. Click "Add Secret File"
3. Set filename: `/etc/secrets/credentials.json`
4. Paste the **entire contents** of your `credentials.json` file
5. Click "Save"

### Step 5: Deploy

1. Click "Create Web Service"
2. Render will automatically build and deploy your app
3. Once deployed, visit your app URL (e.g., `https://job-tracker-xyz.onrender.com`)

## Deployment to Railway

### Step 1: Prepare Repository
Same as Render - ensure code is pushed to GitHub.

### Step 2: Create Railway Project

1. Go to [Railway](https://railway.app/)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository

### Step 3: Configure Build & Start Commands

Railway auto-detects Python apps, but verify:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

### Step 4: Set Environment Variables

In Railway settings > Variables, add:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | Your random secret key |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | `credentials.json` |

### Step 5: Upload Credentials

Railway doesn't have built-in secret files. Use one of these methods:

**Method A: Base64 Environment Variable**
```bash
# Encode credentials to base64
base64 -i credentials.json | tr -d '\n' > credentials_b64.txt
```

Add environment variable:
- `GOOGLE_CREDENTIALS_BASE64`: (paste the base64 string)

Then update `google_client.py` to decode it:
```python
import base64
import json
import tempfile

b64_creds = os.environ.get('GOOGLE_CREDENTIALS_BASE64')
if b64_creds:
    creds_json = base64.b64decode(b64_creds)
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write(creds_json.decode())
        creds_file = Path(f.name)
```

**Method B: Railway Volumes**
Use Railway's volume feature to persist the credentials file.

### Step 6: Deploy
Railway will auto-deploy. Monitor logs for any issues.

## Usage Guide

### 1. Connect Your Google Sheet
On the homepage, paste your Google Sheet URL or ID and click "Continue".

### 2. Add a Job

#### For LinkedIn, Indeed, Glassdoor:
1. Copy the job posting URL
2. Paste it into the input field
3. Click "Add Job"
4. Review the auto-parsed data
5. Edit any incorrect fields
6. Click "Save Job"

#### For Handshake:
1. Paste the Handshake job URL
2. On the next page, open the job posting
3. Select all text on the page (Cmd+A / Ctrl+A)
4. Copy the text (Cmd+C / Ctrl+C)
5. Paste into the textarea
6. Click "Continue"
7. Review and edit the parsed data
8. Click "Save Job"

### 3. Special Features

**Duplicate Prevention**
- If you try to add a job URL that already exists in your sheet, the app will reject it and ask for a different job

**Replace Most Recent Job**
- Check this box if you want to replace the last job you added (useful for mistakes)
- The old job will be moved to the "Trash" sheet

**Automatic Salary Conversion**
The app converts salaries to annual equivalents:
- `$25/hr` → `$25.00/hr (~$52,000/yr)`
- `$5000/mo` → `$5,000/mo (~$60,000/yr, ~$28.85/hr)`
- `$120k/yr` → `$120,000/yr (~$57.69/hr)`

## Troubleshooting

### "Google service account credentials not found"
**Local Development:**
- Ensure `credentials.json` exists in the project root directory

**Render Deployment:**
- Verify the secret file is configured at `/etc/secrets/credentials.json`
- Check that you pasted the entire JSON contents

**Railway Deployment:**
- Verify environment variable `GOOGLE_CREDENTIALS_BASE64` is set
- Or check that volume mount contains `credentials.json`

### "Error connecting to sheet"
- **Service Account Access**: Ensure the service account email (from `credentials.json`) is added to your Google Sheet with Editor permissions
- **Sheet URL**: Verify the sheet URL or ID is correct
- **APIs Enabled**: Confirm Google Sheets API and Google Drive API are enabled in Google Cloud Console

### Parser Returns Empty Fields
- Some job boards may block automated scraping
- Handshake requires manual text paste (this is by design)
- Use the review/edit page to manually fill in any missing fields

### Import Errors / Module Not Found
```bash
# Ensure you're in the virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Port Already in Use
```bash
# Find and kill the process using port 5000
lsof -ti:5000 | xargs kill -9

# Or run on a different port
flask run --port 5001
```

## Development

### Project Architecture

- **`app.py`**: Main Flask application with all routes
- **`google_client.py`**: Centralized Google Sheets authentication (easy to switch auth methods)
- **`core/sheets.py`**: Google Sheets CRUD operations
- **`core/jobs.py`**: Job URL processing and parser routing
- **`core/salary.py`**: Salary normalization utilities
- **`core/parsers/`**: Platform-specific parsing logic

### Adding a New Job Board Parser

1. Create a new parser file in `core/parsers/yoursite.py`
2. Implement parsing logic following the pattern in existing parsers
3. Update `core/jobs.py` to route URLs to your new parser
4. Test with sample URLs from that job board

Example:
```python
# core/parsers/yoursite.py
def parse_yoursite_job(html, job_url):
    soup = BeautifulSoup(html, 'html.parser')
    
    position = soup.select_one('.job-title').text.strip()
    company = soup.select_one('.company-name').text.strip()
    # ... extract other fields
    
    return {
        'position': position,
        'company': company,
        # ... other fields
    }
```

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | `dev-secret-change-in-production` | Flask session secret key |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Yes | `credentials.json` | Path to Google service account JSON file |
| `GOOGLE_AUTH_MODE` | No | `service_account` | Authentication mode (for future OAuth support) |

## Security Notes

⚠️ **Never commit sensitive files:**
- `credentials.json` - Contains your Google service account private key
- `.env` - Contains your secret keys and configuration

These are already in `.gitignore`, but always double-check before pushing to GitHub.

## License

MIT License - see LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For issues or questions:
- Open a GitHub Issue
- Check existing documentation in the `/docs` folder
- Review troubleshooting section above

---

**Happy job hunting! 🎯**
