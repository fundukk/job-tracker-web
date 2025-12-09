# Parser Migration Guide

This document explains how to safely migrate from the legacy parser to the new modular parser system.

## Overview

The project now has **two parser systems**:

1. **Legacy Parser** (current, stable) - Simple placeholder in `core/jobs.py`
2. **New Modular Parser** (future, extensible) - Separate modules in `core/parsers/`

You can switch between them using the `USE_NEW_PARSER` flag in `core/jobs.py`.

## Architecture

### New Structure

```
core/
├── jobs.py              # Main entry point with feature flag
├── sheets.py            # Google Sheets integration (unchanged)
└── parsers/             # NEW: Modular parser system
    ├── __init__.py      # Parser registry
    ├── linkedin.py      # LinkedIn-specific parser
    ├── handshake.py     # Handshake-specific parser
    └── generic.py       # Fallback for other sites
```

### Standardized Schema

All parsers return the same structure:

```python
{
    "date_added": "2025-12-09",      # ISO date
    "platform": "LinkedIn",           # LinkedIn | Handshake | Indeed | Other
    "company": "Example Corp",
    "title": "Software Engineer",
    "location": "San Francisco, CA",
    "salary": "$120k-150k/yr",
    "job_type": "Full-time",         # Full-time | Part-time | Contract | Internship
    "remote": "Hybrid",               # Remote | Hybrid | On-site
    "url": "https://...",
    "status": "Not applied",
    "notes": ""                       # Errors or additional info
}
```

**Missing fields = empty strings** (never errors)

## Migration Steps

### Phase 1: Keep Current System (NOW)

✅ **Status: DONE**

- Legacy parser still active
- New parsers created but not used
- `USE_NEW_PARSER = False`
- Zero risk to current functionality

**Action:** None required. Everything works as before.

---

### Phase 2: Test New Parsers (NEXT)

🔄 **When ready to test:**

1. **Enable new parser system:**
   ```python
   # In core/jobs.py, change:
   USE_NEW_PARSER = True
   ```

2. **Test with real job URLs:**
   - LinkedIn job
   - Handshake job
   - Indeed job (generic parser)

3. **Verify Google Sheet:**
   - Check all fields are populated correctly
   - Confirm no data loss
   - Test error handling

4. **If issues found:**
   ```python
   # Immediately revert:
   USE_NEW_PARSER = False
   ```
   Then fix parsers without affecting production.

---

### Phase 3: Migrate Custom Logic (FUTURE)

Once new parsers are stable, migrate your CLI script logic:

#### From CLI script (`job_tracker.py`):

Your CLI has advanced parsers:
- `scrape_linkedin_job()` - More sophisticated LinkedIn parsing
- `parse_handshake_text()` - Text-based Handshake parsing
- `scrape_handshake_job()` - HTML-based Handshake parsing

#### To Web parsers:

1. **Copy proven logic:**
   ```bash
   # Example: Migrate LinkedIn scraper
   # From: job_tracker.py:scrape_linkedin_job()
   # To:   core/parsers/linkedin.py:parse()
   ```

2. **Adapt to web context:**
   - CLI uses `input()` → Web uses pre-fetched HTML
   - CLI has interactive prompts → Web returns structured data
   - Keep error handling defensive

3. **Test incrementally:**
   - Migrate one parser at a time
   - Test thoroughly before moving to next
   - Keep legacy flag as safety net

---

### Phase 4: Add New Platforms (FUTURE)

To add a new job platform:

1. **Create new parser:**
   ```bash
   touch core/parsers/indeed.py
   ```

2. **Implement standard interface:**
   ```python
   def parse(html: str, job_url: str) -> dict:
       # Your parsing logic
       return {
           "date_added": date.today().isoformat(),
           "platform": "Indeed",
           "company": "",
           "title": "",
           # ... all required fields
       }
   ```

3. **Register in router:**
   ```python
   # In core/jobs.py
   elif "indeed.com" in domain:
       return indeed.parse(html, job_url)
   ```

4. **Test and deploy**

---

## Feature Flag Strategy

### Development Workflow

```python
# Branch: main (production)
USE_NEW_PARSER = False  # Safe, tested legacy code

# Branch: feature/new-parsers (development)
USE_NEW_PARSER = True   # Testing new parser system
```

### Rollback Strategy

If new parsers cause issues:

```python
# Immediate rollback (no code changes needed)
USE_NEW_PARSER = False

# Fix parsers in development branch
# Re-test thoroughly
# Flip flag again when ready
```

### Gradual Migration

You can even mix parsers:

```python
# In core/jobs.py
if USE_NEW_PARSER:
    if "linkedin.com" in domain:
        return linkedin.parse(html, job_url)  # New
    elif "handshake.com" in domain:
        return legacy_handshake_parse(html)   # Keep old one for now
    else:
        return generic.parse(html, job_url)   # New
```

---

## Testing Checklist

Before setting `USE_NEW_PARSER = True` permanently:

- [ ] Test LinkedIn job parsing
- [ ] Test Handshake job parsing
- [ ] Test Indeed job parsing (generic)
- [ ] Test unknown domain (generic)
- [ ] Verify all fields in Google Sheet
- [ ] Test with missing data (partial job posts)
- [ ] Test error handling (404, timeout, invalid HTML)
- [ ] Confirm no data loss vs legacy parser
- [ ] Test with 10+ real job URLs
- [ ] Create test cases for regression testing

---

## Benefits of New System

### 1. **Modularity**
- Each platform in separate file
- Easy to maintain and debug
- Clear separation of concerns

### 2. **Testability**
- Each parser can be unit tested independently
- Mock HTML fixtures for consistent tests
- No side effects between parsers

### 3. **Extensibility**
- Add new platforms without touching existing code
- Version parsers individually
- A/B test parsing strategies

### 4. **Safety**
- Feature flag = instant rollback
- Legacy parser always available
- Zero-downtime migrations

### 5. **Collaboration**
- Different developers can work on different parsers
- Clear interfaces prevent conflicts
- Easy code reviews

---

## Future Enhancements

Once new parser system is stable:

### 1. Add Parser Versioning
```python
core/parsers/
    linkedin_v1.py
    linkedin_v2.py  # New improved version
```

### 2. Add Parser Tests
```python
tests/
    test_linkedin_parser.py
    test_handshake_parser.py
    fixtures/
        linkedin_sample.html
        handshake_sample.html
```

### 3. Add Parser Metrics
```python
# Track success rates per parser
parser_stats = {
    "linkedin": {"success": 150, "failures": 2},
    "handshake": {"success": 80, "failures": 1},
}
```

### 4. Add OAuth (Option B)
```python
core/
    auth/
        oauth.py
        session.py
```

---

## Questions?

**Q: When should I enable the new parser?**
A: When you have time to test thoroughly and can monitor results.

**Q: What if new parser fails?**
A: Flip `USE_NEW_PARSER = False` immediately. Zero downtime.

**Q: Can I use both parsers?**
A: Yes! You can route some domains to new, some to legacy.

**Q: How do I migrate my CLI logic?**
A: Copy your proven parsing functions into the new parser files, adapting for web context.

**Q: Is this safe for production?**
A: Yes. The flag system ensures zero risk until you're ready.

---

## Summary

✅ **Current state:** Safe, stable, tested
🔄 **Migration path:** Clear, gradual, reversible
🚀 **Future:** Modular, testable, extensible

**Next step:** When ready, flip `USE_NEW_PARSER = True` and test!
