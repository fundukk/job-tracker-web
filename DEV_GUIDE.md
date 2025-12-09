# Developer Quick Reference

## Parser System Overview

### Feature Flag Location
```
File: core/jobs.py
Line: ~12
Flag: USE_NEW_PARSER = False
```

### How to Switch Parsers

**Enable new modular parsers:**
```python
USE_NEW_PARSER = True
```

**Revert to legacy parser:**
```python
USE_NEW_PARSER = False
```

### Parser Files

| File | Purpose | Status |
|------|---------|--------|
| `core/jobs.py` | Router with feature flag | ✅ Active |
| `core/parsers/linkedin.py` | LinkedIn parsing | 🔄 Ready (not active) |
| `core/parsers/handshake.py` | Handshake parsing | 🔄 Ready (not active) |
| `core/parsers/generic.py` | Fallback parsing | 🔄 Ready (not active) |

## Standardized Schema

Every parser MUST return this exact structure:

```python
{
    "date_added": "2025-12-09",      # ISO date string
    "platform": "LinkedIn",           # str: LinkedIn | Handshake | Indeed | Other
    "company": "Example Corp",        # str: company name
    "title": "Software Engineer",     # str: job title
    "location": "San Francisco, CA",  # str: City, State
    "salary": "$120k-150k/yr",       # str: formatted salary
    "job_type": "Full-time",         # str: Full-time | Part-time | Contract | Internship
    "remote": "Hybrid",               # str: Remote | Hybrid | On-site
    "url": "https://...",            # str: job URL
    "status": "Not applied",          # str: application status
    "notes": ""                       # str: errors or additional info
}
```

**Rules:**
- All keys required (no missing keys)
- Missing data = empty string `""`
- Never raise exceptions (catch and add to `notes`)
- Date must be ISO format: `date.today().isoformat()`

## Adding a New Parser

### 1. Create Parser File

```bash
touch core/parsers/indeed.py
```

### 2. Implement Parse Function

```python
from bs4 import BeautifulSoup
from datetime import date

def parse(html: str, job_url: str) -> dict:
    """Parse Indeed job posting."""
    soup = BeautifulSoup(html, "html.parser")
    
    job_data = {
        "date_added": date.today().isoformat(),
        "platform": "Indeed",
        "company": "",
        "title": "",
        "location": "",
        "salary": "",
        "job_type": "",
        "remote": "",
        "url": job_url,
        "status": "Not applied",
        "notes": "",
    }
    
    try:
        # Your parsing logic here
        # Extract title, company, etc.
        pass
    except Exception as e:
        job_data["notes"] = f"Parsing error: {str(e)}"
    
    return job_data
```

### 3. Add to Router

```python
# In core/jobs.py, inside parse_job_html():
if USE_NEW_PARSER:
    domain = urlparse(job_url).netloc.lower()
    
    if "linkedin.com" in domain:
        return linkedin.parse(html, job_url)
    elif "indeed.com" in domain:  # <-- Add this
        from core.parsers import indeed
        return indeed.parse(html, job_url)
    # ... rest of routing
```

### 4. Test

```python
# Test with real URL
job_url = "https://indeed.com/viewjob?jk=123456"
html = fetch_job_html(job_url)
result = parse_job_html(html, job_url)
print(result)
```

## Git Workflow

### Development Branch Strategy

```bash
# Main branch - stable, legacy parser
git checkout main
# USE_NEW_PARSER = False

# Feature branch - new parser development
git checkout -b feature/new-parsers
# Change USE_NEW_PARSER = True
# Test and develop new parsers

# When ready to merge
git checkout main
git merge feature/new-parsers
# Set USE_NEW_PARSER = False (safety)
# Test in production
# When confident, flip to True
```

### Safe Deployment

```bash
# 1. Deploy with flag OFF
git push origin main
# USE_NEW_PARSER = False

# 2. Monitor in production

# 3. Enable flag via config (not code)
# Or do a small code change:
git commit -m "Enable new parser system"
git push origin main
```

## Testing Checklist

```bash
# Test each parser individually
python -c "
from core.parsers import linkedin
html = open('test_linkedin.html').read()
result = linkedin.parse(html, 'https://linkedin.com/jobs/view/123')
print(result)
"

# Test routing
python -c "
from core.jobs import process_job_url
result = process_job_url('https://linkedin.com/jobs/view/123')
print(result)
"

# Test with Flask app
flask run
# Visit http://127.0.0.1:5000
# Add a test job
```

## Common Tasks

### Migrate CLI Logic to Web Parser

```python
# FROM: job_tracker.py (CLI)
def scrape_linkedin_job(url: str):
    # ... CLI logic with print() and input()
    return position, company, location, ...

# TO: core/parsers/linkedin.py (Web)
def parse(html: str, job_url: str) -> dict:
    # ... same parsing logic
    # BUT: no print(), no input()
    # Return structured dict
    return {
        "title": position,
        "company": company,
        "location": location,
        # ... rest of schema
    }
```

### Debug Parser Issues

```python
# Add debug logging to parser
def parse(html: str, job_url: str) -> dict:
    import logging
    logger = logging.getLogger(__name__)
    
    logger.debug(f"Parsing URL: {job_url}")
    logger.debug(f"HTML length: {len(html)}")
    
    # ... parsing logic
    
    logger.debug(f"Extracted: {job_data}")
    return job_data
```

### Handle Missing Data Gracefully

```python
def parse(html: str, job_url: str) -> dict:
    job_data = {...}  # Initialize with empty strings
    
    try:
        # Try to extract title
        title = soup.find("h1")
        if title:
            job_data["title"] = title.get_text(strip=True)
        # If not found, stays empty string (not None, not error)
        
    except Exception as e:
        # Log error but continue
        job_data["notes"] = f"Error: {str(e)}"
    
    return job_data  # Always returns valid structure
```

## Performance Tips

### 1. Lazy Import Parsers

```python
# In core/jobs.py
if USE_NEW_PARSER:
    # Don't import all parsers at module level
    # Import only when needed:
    if "linkedin.com" in domain:
        from core.parsers import linkedin
        return linkedin.parse(html, job_url)
```

### 2. Cache Compiled Regexes

```python
# In parser file
import re

# Compile once at module level
SALARY_PATTERN = re.compile(
    r'\$\s*[\d,]+(?:\.\d+)?(?:\s*k)?...',
    re.IGNORECASE
)

def parse(html: str, job_url: str) -> dict:
    # Use compiled pattern (faster)
    match = SALARY_PATTERN.search(html)
```

### 3. Limit BeautifulSoup Scope

```python
def parse(html: str, job_url: str) -> dict:
    # Only parse what you need
    soup = BeautifulSoup(html, "html.parser")
    
    # Find specific section first
    job_section = soup.find("div", class_="job-details")
    if job_section:
        # Parse only this section (faster)
        title = job_section.find("h1")
```

## Rollback Plan

### Immediate Rollback (< 1 minute)

```python
# In core/jobs.py
USE_NEW_PARSER = False  # Change this line
# Save file
# Restart Flask: Ctrl+C, then `python app.py`
```

### Gradual Rollback (selective)

```python
# Keep new parsers for some platforms
if USE_NEW_PARSER:
    if "linkedin.com" in domain:
        return linkedin.parse(html, job_url)  # New (working)
    elif "handshake.com" in domain:
        # Rollback handshake only
        return old_handshake_parse(html, job_url)
```

## File Organization

```
Current (Clean):
core/
├── jobs.py              (1 file, router logic)
└── parsers/             (separate concerns)
    ├── linkedin.py      (1 platform)
    ├── handshake.py     (1 platform)
    └── generic.py       (fallback)

Future (Extensible):
core/
├── jobs.py
└── parsers/
    ├── linkedin.py
    ├── handshake.py
    ├── indeed.py        (new platform)
    ├── glassdoor.py     (new platform)
    └── generic.py
```

## Next Steps

1. ✅ Structure created (DONE)
2. 🔄 Test new parsers with `USE_NEW_PARSER = True`
3. 🔄 Migrate CLI logic to web parsers
4. 🔄 Add unit tests
5. 🔄 Deploy with confidence
6. 🚀 Add more platforms as needed

---

**Quick Links:**
- [MIGRATION.md](MIGRATION.md) - Detailed migration guide
- [README.md](README.md) - User documentation
- `core/jobs.py` - Feature flag location
- `core/parsers/` - Parser modules
