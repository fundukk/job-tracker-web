Refactor to production-ready Flask application with OAuth 2.0

Major architectural refactoring to follow Flask best practices and improve
maintainability, security, and testability.

## Application Structure

- Implemented Flask factory pattern with create_app() in app/__init__.py
- Organized code into blueprints: auth_bp (OAuth) and main_bp (routes)
- Modular package structure under app/ directory
- Separated concerns: auth, routes, sheets, parsers

## OAuth 2.0 Improvements

- Added automatic token refresh for expired credentials
- Proper state verification in OAuth callback
- Session-based credential storage with expiry tracking
- Configurable redirect URI via OAUTH_REDIRECT_URI env var
- HTTPS handling fix for production deployments (Render)

## Logging & Error Handling

- Configured structured logging with configurable log levels
- Added centralized error handlers for 400/401/403/404/500
- User-friendly error messages in templates
- Detailed logging throughout parsers, sheets, and auth modules
- Request context included in error logs

## Parsers Refactoring

- Split core/jobs.py into modular parsers under app/parsers/
- linkedin.py: LinkedIn-specific parsing with error handling
- handshake.py: Handshake HTML and text parsing
- generic.py: Fallback parser for other job sites
- Wrapped all parsing in try/except for graceful degradation
- Pure functions for easy testing
- Comprehensive logging for debugging

## Google Sheets Operations

- Moved to app/sheets.py with improved error handling
- Better exception management for API failures
- Logging for all sheet operations
- Graceful handling of missing/invalid credentials

## Test Suite

- Added pytest with 20+ unit tests
- Tests for LinkedIn parser (test_parsers_linkedin.py)
- Tests for Handshake parser (test_parsers_handshake.py)  
- Tests for sheets helpers (test_sheets_helpers.py)
- Mocked external dependencies (no real API calls)
- pytest.ini configuration with coverage support

## Documentation

- Complete rewrite of README.md focused on OAuth 2.0
- Removed all service account references
- Clear deployment instructions for Render
- Environment variable reference
- Troubleshooting guide
- Architecture diagram

## File Changes

New files:
- app/__init__.py - Flask factory with logging and error handlers
- app/auth.py - OAuth authentication blueprint
- app/routes.py - Main application routes blueprint
- app/sheets.py - Google Sheets operations
- app/parsers/__init__.py - Parser registry and interface
- app/parsers/linkedin.py - LinkedIn parser
- app/parsers/handshake.py - Handshake parser
- app/parsers/generic.py - Generic parser
- tests/test_parsers_linkedin.py
- tests/test_parsers_handshake.py
- tests/test_sheets_helpers.py
- tests/README.md
- pytest.ini
- REFACTORING_SUMMARY.md
- validate_refactor.py

Modified files:
- app.py - Now minimal entry point using factory
- requirements.txt - Added pytest and pytest-mock
- README.md - Complete rewrite for OAuth 2.0

Deprecated (can be deleted):
- google_client.py - Logic moved to app/auth.py
- core/sheets.py - Moved to app/sheets.py
- core/jobs.py - Split into app/parsers/
- core/parsers/ - Moved to app/parsers/

## Breaking Changes

- Service account authentication removed
- Users must log in with Google OAuth
- GOOGLE_SERVICE_ACCOUNT_FILE env var replaced with GOOGLE_OAUTH_CLIENT_SECRET_FILE

## Migration Required

1. Set up OAuth 2.0 in Google Cloud Console
2. Download OAuth client secret JSON
3. Update environment variables
4. Add secret file to Render
5. Update redirect URI in Google Console

TESTING: All imports validated successfully ✅
