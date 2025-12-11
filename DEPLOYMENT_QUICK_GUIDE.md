# Quick Deployment Guide

## Pre-Deployment Checklist

- [ ] All imports validated: `python3 validate_refactor.py`
- [ ] Tests passing: `source venv/bin/activate && pytest`
- [ ] OAuth client secret downloaded from Google Cloud Console
- [ ] .env file configured locally (for testing)

## Local Testing

1. **Activate virtual environment**:
   ```bash
   source venv/bin/activate
   ```

2. **Run tests**:
   ```bash
   pytest -v
   ```

3. **Test the app locally**:
   ```bash
   flask run
   ```
   Visit http://localhost:5000

4. **Test OAuth flow**:
   - Log in with Google
   - Connect a test Google Sheet
   - Add a test job
   - Verify it appears in the sheet

## Deploy to Render

### 1. Commit and Push

```bash
git add .
git commit -F COMMIT_MESSAGE.md
git push origin main
```

### 2. Configure Render

Environment Variables:
```
SECRET_KEY=<your-secret-key-from-python-c-import-secrets-print-secrets-token-hex-32>
GOOGLE_OAUTH_CLIENT_SECRET_FILE=/etc/secrets/google_oauth_client_secret.json
```

Secret Files:
- Filename: `/etc/secrets/google_oauth_client_secret.json`
- Contents: Paste your OAuth client secret JSON

### 3. Update OAuth Redirect URI

In Google Cloud Console > Credentials > OAuth 2.0 Client ID:
```
https://your-app.onrender.com/oauth2callback
```

### 4. Deploy

Render will automatically deploy when you push to GitHub.

## Post-Deployment Testing

1. Visit your deployed URL
2. Click "Log in with Google"
3. Approve OAuth consent
4. Enter Google Sheet URL
5. Add a test job
6. Verify in sheet

## Troubleshooting

### Imports fail locally
```bash
source venv/bin/activate
pip install -r requirements.txt
python3 validate_refactor.py
```

### Tests fail
```bash
pytest -v  # See detailed error messages
```

### OAuth errors in production
- Check Render logs
- Verify GOOGLE_OAUTH_CLIENT_SECRET_FILE points to /etc/secrets/...
- Verify redirect URI matches exactly
- Check secret file is uploaded correctly

### "Module not found" errors
Make sure you're using the refactored imports:
- ❌ `from google_client import ...`
- ✅ `from app.auth import ...`
- ❌ `from core.sheets import ...`
- ✅ `from app.sheets import ...`

## Optional Cleanup

After verifying deployment works, delete old files:

```bash
rm google_client.py
rm -rf core/parsers/
rm README_OLD.md
rm COMMIT_MESSAGE.md
rm validate_refactor.py
rm DEPLOYMENT_QUICK_GUIDE.md  # This file
git add .
git commit -m "Clean up deprecated files"
git push origin main
```

## Success Criteria

✅ All tests passing locally
✅ App runs locally with `flask run`
✅ Can log in with Google locally
✅ Can add jobs locally
✅ Deployed to Render without errors
✅ Can log in on production
✅ Can add jobs on production
✅ Jobs appear in Google Sheet

## Support

If you get stuck:
1. Check REFACTORING_SUMMARY.md
2. Check README.md troubleshooting section
3. Review Render logs
4. Test locally first
