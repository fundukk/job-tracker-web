# Job Tracker Web - Tests

This directory contains unit tests for the job tracker application.

## Running Tests

Install dependencies:
```bash
pip install -r requirements.txt
```

Run all tests:
```bash
pytest
```

Run with verbose output:
```bash
pytest -v
```

Run specific test file:
```bash
pytest tests/test_parsers_linkedin.py
```

Run with coverage:
```bash
pytest --cov=app
```

## Test Organization

- `test_parsers_linkedin.py` - Tests for LinkedIn job parser
- `test_parsers_handshake.py` - Tests for Handshake job parser  
- `test_sheets_helpers.py` - Tests for Google Sheets helper functions

## Writing Tests

Follow these conventions:
1. Group tests in classes by functionality
2. Use descriptive test names that explain what's being tested
3. Include both positive and negative test cases
4. Mock external dependencies (Google APIs, HTTP requests)
5. Test error handling and edge cases
