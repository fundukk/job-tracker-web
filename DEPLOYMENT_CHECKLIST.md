# Deployment Checklist

Use this checklist before deploying to production (Render, Railway, etc.).

## Pre-Deployment Checks

### ✅ Code Quality
- [ ] All sensitive data removed from code (no hardcoded credentials)
- [ ] `credentials.json` is in `.gitignore`
- [ ] `.env` is in `.gitignore`
- [ ] No `print()` debugging statements in production code
- [ ] All TODO comments resolved or documented

### ✅ Dependencies
- [ ] `requirements.txt` is up to date
- [ ] All imports in code are listed in `requirements.txt`
- [ ] Test locally: `pip install -r requirements.txt` in fresh venv

### ✅ Environment Configuration
- [ ] `.env.example` exists with all required variables
- [ ] No real secrets in `.env.example` (only placeholders)
- [ ] `app.py` uses `os.environ.get()` for all config
- [ ] `SECRET_KEY` is loaded from environment, not hardcoded

### ✅ Flask App
- [ ] `app.py` exposes Flask instance named `app`
- [ ] Can import successfully: `from app import app`
- [ ] App runs with gunicorn: `gunicorn app:app`
- [ ] All routes tested locally

### ✅ Google Sheets Authentication
- [ ] Service account JSON file created
- [ ] Google Sheets API enabled in GCP
- [ ] Google Drive API enabled in GCP
- [ ] Service account email added to target Google Sheet with Editor access
- [ ] `google_client.py` reads credentials path from environment variable

### ✅ Git & GitHub
- [ ] All changes committed
- [ ] No sensitive files committed (check `git status`)
- [ ] Code pushed to GitHub
- [ ] Repository is accessible to deployment platform

## Render Deployment

### Environment Variables
Set these in Render dashboard > Environment:

| Variable | Example | Required |
|----------|---------|----------|
| `SECRET_KEY` | `abc123...` | ✅ Yes |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | `/etc/secrets/credentials.json` | ✅ Yes |

### Secret Files
Add in Render dashboard > Environment > Secret Files:

| Filename | Contents |
|----------|----------|
| `/etc/secrets/credentials.json` | Entire contents of your service account JSON |

### Build Configuration
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Environment**: Python 3

### Post-Deployment
- [ ] App deployed successfully
- [ ] Visit app URL and test homepage
- [ ] Test adding a job
- [ ] Verify data appears in Google Sheet
- [ ] Check logs for any errors

## Railway Deployment

### Environment Variables
Set in Railway settings > Variables:

| Variable | Required |
|----------|----------|
| `SECRET_KEY` | ✅ Yes |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | ✅ Yes |
| `GOOGLE_CREDENTIALS_BASE64` | If using base64 method |

### Credentials Setup

**Option A: Base64 Environment Variable**
```bash
base64 -i credentials.json | tr -d '\n' > credentials_b64.txt
```
Copy contents to `GOOGLE_CREDENTIALS_BASE64` environment variable.

**Option B: Railway Volume**
Mount volume and upload `credentials.json` directly.

### Build Configuration
Railway auto-detects Python apps, but verify:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

### Post-Deployment
- [ ] App deployed successfully
- [ ] Test all functionality
- [ ] Monitor logs for errors

## Testing After Deployment

### Basic Functionality
- [ ] Homepage loads
- [ ] Can connect to Google Sheet
- [ ] LinkedIn job parsing works
- [ ] Handshake text paste works
- [ ] Review/edit form works
- [ ] Job saves to Google Sheet correctly
- [ ] Duplicate detection works
- [ ] Trash sheet created and populated

### Error Handling
- [ ] Invalid URLs show error message
- [ ] Duplicate URLs rejected properly
- [ ] Form validation works
- [ ] Error messages are user-friendly

### Google Sheets Integration
- [ ] Jobs appear in correct order (newest at top)
- [ ] All 11 columns populated correctly
- [ ] DateApplied auto-filled with today's date
- [ ] Trash sheet exists and receives replaced jobs

## Common Issues & Solutions

### "Module not found" errors
- Check `requirements.txt` includes all dependencies
- Redeploy to rebuild with updated requirements

### "Credentials not found"
- Verify secret file path matches `GOOGLE_SERVICE_ACCOUNT_FILE`
- Check secret file contents are valid JSON
- On Railway, ensure base64 decoding logic is correct

### "Permission denied" on Google Sheet
- Share sheet with service account email from credentials.json
- Grant Editor (not Viewer) permissions
- Verify APIs are enabled in Google Cloud Console

### App crashes on startup
- Check deployment logs for errors
- Verify all environment variables are set
- Test `gunicorn app:app` locally first

### Routes return 404
- Ensure all template files in `templates/` directory
- Check static files in `static/` directory
- Verify `app.py` imports are correct

## Rollback Plan

If deployment fails:
1. Check logs in platform dashboard
2. Revert last commit if code issue: `git revert HEAD`
3. Push revert: `git push origin main`
4. Platform will auto-redeploy previous working version

## Monitoring

After deployment, monitor:
- [ ] Application logs (first 24 hours)
- [ ] Error rates in platform dashboard
- [ ] Response times
- [ ] Google Sheets write operations

## Security Reminders

- ✅ Never commit `credentials.json`
- ✅ Never commit `.env` file
- ✅ Rotate `SECRET_KEY` if exposed
- ✅ Rotate service account key if exposed
- ✅ Use HTTPS in production (Render/Railway provide this)
- ✅ Limit service account permissions to only what's needed

## Performance Tips

- Consider upgrading from free tier if handling high traffic
- Monitor Render/Railway usage metrics
- Optimize Google Sheets API calls if hitting rate limits
- Enable caching for static assets

---

**Last Updated**: December 2025
