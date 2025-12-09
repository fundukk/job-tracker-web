# Architecture Overview

## Visual Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Flask Web App                            │
│                       (app.py)                               │
│  Routes: / → /set_sheet → /job → /add_job → /success       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
          ┌──────────────────────────┐
          │   Job Processing Layer   │
          │    (core/jobs.py)        │
          │                          │
          │  ┌──────────────────┐   │
          │  │ USE_NEW_PARSER   │   │ ← Feature Flag
          │  │   True/False     │   │
          │  └────────┬─────────┘   │
          └───────────┼──────────────┘
                      │
         ┌────────────┴─────────────┐
         │                          │
      [True]                     [False]
         │                          │
         ↓                          ↓
┌────────────────────┐    ┌────────────────────┐
│  New Parser System │    │  Legacy Parser     │
│  (core/parsers/)   │    │  (inline)          │
└────────┬───────────┘    └────────┬───────────┘
         │                         │
         ↓                         │
┌─────────────────────────────────────────────────┐
│           Domain-Based Routing                  │
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │LinkedIn  │  │Handshake │  │ Generic  │    │
│  │.parse()  │  │.parse()  │  │.parse()  │    │
│  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
         ┌────────────────────┐
         │ Standardized Data  │
         │   (common schema)  │
         └─────────┬──────────┘
                   │
                   ↓
         ┌────────────────────┐
         │  Google Sheets API │
         │   (core/sheets.py) │
         └────────────────────┘
```

## Data Flow

### Request Flow
```
User Input (Job URL)
    ↓
Flask Route (/add_job)
    ↓
fetch_job_html() → HTTP Request → Raw HTML
    ↓
parse_job_html() → Check Feature Flag
    ↓
    ├─ [True] → Route by domain → Call specific parser
    └─ [False] → Use legacy parser
    ↓
Standardized job_data dict
    ↓
append_job_row() → Write to Google Sheet
    ↓
Success Page
```

### Parser Selection Flow
```
Job URL: "https://linkedin.com/jobs/view/123"
    ↓
Extract domain: "linkedin.com"
    ↓
Check USE_NEW_PARSER flag
    ↓
    ├─ [True]
    │   └─ if "linkedin.com" in domain:
    │       └─ linkedin.parse(html, url)
    │           └─ Returns: {title, company, location, ...}
    │
    └─ [False]
        └─ Legacy parse_job_html()
            └─ Returns: {title, company, location, ...}
```

## Module Dependencies

```
app.py
  ├─ imports: Flask, session, flash
  ├─ imports: core.sheets (get_worksheet, append_job_row)
  └─ imports: core.jobs (process_job_url)

core/jobs.py
  ├─ imports: requests, BeautifulSoup
  ├─ imports: urlparse (for domain routing)
  └─ conditional imports:
      ├─ IF USE_NEW_PARSER == True:
      │   └─ core.parsers (linkedin, handshake, generic)
      └─ ELSE:
          └─ (uses inline legacy code)

core/parsers/linkedin.py
  ├─ imports: BeautifulSoup
  ├─ imports: datetime (for date)
  └─ imports: re (for regex patterns)

core/parsers/handshake.py
  ├─ imports: BeautifulSoup
  ├─ imports: datetime (for date)
  └─ imports: re (for regex patterns)

core/parsers/generic.py
  ├─ imports: BeautifulSoup
  ├─ imports: datetime (for date)
  ├─ imports: re (for regex patterns)
  └─ imports: urlparse (for platform detection)

core/sheets.py
  ├─ imports: gspread
  ├─ imports: google.oauth2 (Credentials)
  └─ imports: pathlib (for file paths)
```

## File Size & Complexity

```
Project Overview:
├─ app.py                 (~100 lines) - Flask routes
├─ core/
│   ├─ jobs.py           (~150 lines) - Router + legacy parser
│   ├─ sheets.py         (~100 lines) - Google Sheets API
│   └─ parsers/
│       ├─ linkedin.py   (~100 lines) - Platform parser
│       ├─ handshake.py  (~100 lines) - Platform parser
│       └─ generic.py    (~100 lines) - Platform parser
├─ templates/            (~150 lines total) - HTML
├─ static/style.css      (~200 lines) - Styling
└─ docs/                 (~2000 lines total) - Documentation
    ├─ README.md
    ├─ MIGRATION.md
    ├─ DEV_GUIDE.md
    └─ SUMMARY.md

Total Code: ~850 lines
Total Docs: ~2000 lines
```

## Feature Flag States

### State 1: Legacy (Current)
```
USE_NEW_PARSER = False

┌─────────┐
│  Flask  │
└────┬────┘
     │
     ↓
┌─────────────┐
│  jobs.py    │
│  (inline)   │  ← Simple placeholder parser
└──────┬──────┘
       │
       ↓
  Google Sheets

Status: ✅ STABLE
Risk:   🟢 NONE
```

### State 2: New System (Testing)
```
USE_NEW_PARSER = True

┌─────────┐
│  Flask  │
└────┬────┘
     │
     ↓
┌──────────────────┐
│  jobs.py         │
│  (router)        │
└────┬────┬────┬───┘
     │    │    │
     ↓    ↓    ↓
  [L]  [H]  [G]     ← Platform-specific parsers
     │    │    │
     └────┴────┘
          ↓
    Google Sheets

Status: 🔄 TESTING
Risk:   🟡 LOW (can revert instantly)
```

### State 3: Mixed (Gradual)
```
USE_NEW_PARSER = True (with custom routing)

┌─────────┐
│  Flask  │
└────┬────┘
     │
     ↓
┌──────────────────────────┐
│  jobs.py (router)        │
│                          │
│  if linkedin → NEW       │ ✅
│  if handshake → LEGACY   │ (keep stable)
│  else → NEW              │ ✅
└───┬─────────────┬────────┘
    │             │
    ↓             ↓
  [NEW]       [LEGACY]
    │             │
    └─────┬───────┘
          ↓
    Google Sheets

Status: 🔄 MIGRATION
Risk:   🟡 MEDIUM (partial rollout)
```

## Error Handling Flow

```
User submits job URL
    ↓
fetch_job_html()
    ├─ Success → Continue
    └─ Error → Catch & flash error message
    ↓
parse_job_html()
    ├─ Parser succeeds → Return full data
    ├─ Parser partial → Return with empty fields
    └─ Parser fails → Return with error in 'notes'
    ↓
append_job_row()
    ├─ Success → Show success page
    └─ Error → Catch & flash error message
    ↓
Success page OR Job page with error
```

## Testing Strategy

```
Development Workflow:

1. Local Testing
   ├─ USE_NEW_PARSER = True
   ├─ Test with real URLs
   └─ Verify data in test sheet

2. Staging/Branch Testing
   ├─ Git branch: feature/new-parsers
   ├─ USE_NEW_PARSER = True
   └─ Team testing

3. Production Deployment
   ├─ Merge to main
   ├─ USE_NEW_PARSER = False (initially)
   ├─ Monitor for stability
   └─ Flip to True when confident

4. Rollback (if needed)
   └─ USE_NEW_PARSER = False (1 line change)
```

## Future Extensions

### Adding OAuth (Option B)
```
Current:
core/
├─ sheets.py (service account)
└─ jobs.py

Future:
core/
├─ sheets.py (service account - unchanged)
├─ jobs.py (unchanged)
└─ auth/          ← NEW
    ├─ oauth.py   ← OAuth flow
    └─ session.py ← User session management

app.py changes:
├─ Add /login route
├─ Add /callback route
└─ Add session management
```

### Adding Unit Tests
```
Current:
job-tracker-web/
├─ core/
└─ templates/

Future:
job-tracker-web/
├─ core/
├─ templates/
└─ tests/         ← NEW
    ├─ test_parsers.py
    ├─ test_sheets.py
    ├─ test_routes.py
    └─ fixtures/
        ├─ linkedin_sample.html
        └─ handshake_sample.html
```

### Adding Parser Versioning
```
Current:
core/parsers/
├─ linkedin.py
└─ handshake.py

Future:
core/parsers/
├─ linkedin_v1.py (stable)
├─ linkedin_v2.py (new features)
├─ handshake_v1.py
└─ handshake_v2.py

With version selection:
USE_LINKEDIN_V2 = True
```

## Performance Considerations

```
Current Performance:
┌─────────────────────┐
│ Fetch HTML: ~1-2s   │ (network request)
├─────────────────────┤
│ Parse HTML: ~0.1s   │ (BeautifulSoup)
├─────────────────────┤
│ Write Sheet: ~0.5s  │ (Google API)
├─────────────────────┤
│ Total: ~2-3s        │ (acceptable)
└─────────────────────┘

Optimization Opportunities:
├─ Cache HTML fetches
├─ Compile regex patterns once
├─ Limit BeautifulSoup scope
└─ Batch sheet writes (future)
```

## Security Considerations

```
Current Security:
✅ Service account (no user passwords)
✅ credentials.json not in git
✅ Session secret key
✅ No SQL injection (no SQL)
✅ HTTPS for external APIs

Future Security:
├─ Add rate limiting
├─ Add input validation
├─ Add CSRF protection
└─ Add OAuth scope limits
```

---

## Quick Decision Matrix

| Scenario | Action | Risk |
|----------|--------|------|
| Need to deploy now | Keep `USE_NEW_PARSER = False` | 🟢 None |
| Want to test locally | Set `USE_NEW_PARSER = True` | 🟢 None (local) |
| Migration ready | Set `USE_NEW_PARSER = True` + test | 🟡 Low |
| Issues found | Set `USE_NEW_PARSER = False` | 🟢 None |
| Add new platform | Create new parser file | 🟡 Low |
| Major refactor | Create feature branch | 🟡 Medium |

---

## Summary

**Architecture Goals: ✅ ACHIEVED**
- ✅ Modular and extensible
- ✅ Safe and stable
- ✅ Easy to test
- ✅ Simple to understand
- ✅ Ready for future growth
