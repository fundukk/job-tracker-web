# Quick Start: Deploy to Render in 5 Minutes

This is the fastest way to get your job tracker live on the internet.

## Step 1: Push to GitHub (1 minute)

```bash
cd /Users/funduk/Desktop/JOBs/job-tracker-web

# Make sure everything is committed
git add .
git commit -m "Ready for deployment"
git push origin main
```

## Step 2: Create Render Web Service (2 minutes)

1. Go to https://dashboard.render.com/
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account (if not already)
4. Select your repository: `job-application-tracker`
5. Fill in:
   - **Name**: `job-tracker` (or anything you want)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
6. Click **"Create Web Service"** (don't deploy yet!)

## Step 3: Add Environment Variables (1 minute)

In the Render dashboard, go to **Environment** tab:

### Add Variables:
Click "Add Environment Variable" for each:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | Run this in terminal to generate: `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | `/etc/secrets/credentials.json` |

## Step 4: Add Secret File (1 minute)

Still in the **Environment** tab:

1. Scroll to **"Secret Files"**
2. Click **"Add Secret File"**
3. **Filename**: `/etc/secrets/credentials.json`
4. **Contents**: 
   - Open your local `credentials.json` file
   - Copy the ENTIRE contents (all the JSON)
   - Paste into the text box
5. Click **"Save"**

## Step 5: Deploy! (30 seconds)

1. Render will automatically start deploying
2. Wait for build to complete (2-3 minutes)
3. Once deployed, you'll see a URL like: `https://job-tracker-xyz.onrender.com`
4. Click the URL to visit your app!

## Step 6: Test Your App (1 minute)

1. Visit your Render URL
2. Paste your Google Sheet URL
3. Try adding a LinkedIn job
4. Check that it appears in your Google Sheet

**Done! 🎉**

---

## Troubleshooting

### Build Failed
- Check the **Logs** tab in Render dashboard
- Look for missing dependencies or syntax errors

### "Credentials not found"
- Verify the secret file path is exactly `/etc/secrets/credentials.json`
- Make sure you pasted the entire JSON contents (including `{` and `}`)

### "Permission denied" on Google Sheet
- Share your Google Sheet with the service account email
- The email is in `credentials.json` under `client_email`
- Grant **Editor** permissions

### App loads but can't parse jobs
- This is normal! The app is working
- LinkedIn/other sites may block requests from cloud servers
- Use Handshake text paste method, or add jobs manually

---

## Next Steps

- Read full `README.md` for detailed documentation
- Check `DEPLOYMENT_CHECKLIST.md` for best practices
- Monitor your app in Render dashboard

**Your job tracker is now live on the internet!** 🚀
