# Testing the Review Flow

## ✅ What Changed

The job tracker now has a **review/edit step** before saving to Google Sheets.

### Old Flow
```
/job → parse URL → immediately save → success page
```

### New Flow
```
/job → parse URL → review_job.html (edit form) → /add_job → success page
```

---

## 🧪 How to Test

### Step 1: Start the Application
```bash
cd /Users/funduk/Desktop/JOBs/job-tracker-web
source venv/bin/activate
python app.py
```

### Step 2: Connect Google Sheet
1. Go to `http://localhost:5000`
2. Enter your Google Sheet URL
3. Click "Connect"

### Step 3: Add a Job URL
1. On `/job` page, paste a job URL (e.g., from LinkedIn, Indeed, Handshake)
2. Click "Add Job"

### Step 4: Review and Edit
You should now see the **review page** with:
- All parsed fields pre-filled (position, company, location, etc.)
- Ability to edit ANY field
- Empty fields for data that wasn't parsed
- A "Save to Google Sheet" button

### Step 5: Edit if Needed
- Modify any field that was incorrectly parsed
- Fill in missing fields manually
- Add notes

### Step 6: Save
- Click "💾 Save to Google Sheet"
- You'll be redirected to the success page
- Check your Google Sheet to confirm the data was saved

---

## 🔍 What to Verify

### ✅ Parsing Still Works
- Job URL is parsed correctly
- Data appears in review form
- Source is detected (LinkedIn, Indeed, etc.)

### ✅ Manual Editing Works
- All fields are editable
- Changes are preserved when saving
- Empty fields can be filled manually

### ✅ Validation Works
- Cannot save without at least position OR company
- Error message appears if validation fails

### ✅ Google Sheets Integration Works
- Data saves to correct row (row 2, pushing old data down)
- All fields appear in correct columns
- Date is automatically added

### ✅ Navigation Works
- Can cancel and go back to `/job`
- Can add another job after success
- Can change sheet from success page

---

## 🐛 Common Issues

### Issue: "Template not found"
**Fix**: Make sure `review_job.html` exists in `templates/` folder

### Issue: Data not saving
**Fix**: Check that all form field names match the dictionary keys in `app.py`:
- position
- company
- location
- salary
- job_type
- remote
- link
- source
- status
- notes

### Issue: Parsing errors
**Fix**: The parser might fail on some sites. That's okay - the review form will be empty, and you can fill it manually.

---

## 📝 Form Fields Reference

All these fields are included in the review form:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| position | text | yes* | Job title |
| company | text | yes* | Company name |
| location | text | no | City, State |
| salary | text | no | Compensation |
| job_type | select | no | Full-time, Internship, etc. |
| remote | select | no | Remote, Hybrid, On-site |
| source | text | no | Auto-detected, read-only |
| status | select | no | Applied (default) |
| notes | textarea | no | Additional info |
| link | hidden | no | Original job URL |

*At least one of position or company is required

---

## 🎯 Expected Behavior

### Scenario 1: Perfect Parse
- LinkedIn job URL with all data
- Review form shows: position, company, location, maybe salary
- User just clicks "Save" → success

### Scenario 2: Partial Parse
- Generic job site
- Review form shows: position and source only
- User fills in company, location manually → success

### Scenario 3: Failed Parse
- Unknown site or blocked by bot detection
- Review form shows: only source and link
- User fills in ALL fields manually → success

### Scenario 4: Edit Parsed Data
- Indeed job URL
- Parser gets wrong company name
- User corrects it in review form → saves correctly

---

## ✨ Benefits of New Flow

1. **Control**: Always verify data before saving
2. **Flexibility**: Manual entry when parser fails
3. **Accuracy**: Fix parsing mistakes immediately
4. **Transparency**: See what was parsed vs. what's missing
5. **No Data Loss**: Even failed parses can be saved manually

---

## 🚀 Next Steps

After testing, you can:
1. Improve parsers in `core/parsers/` (when `USE_NEW_PARSER = True`)
2. Add more fields to the review form
3. Add client-side validation (JavaScript)
4. Add auto-save to session (prevent data loss on refresh)
5. Add "Save and Add Another" button
