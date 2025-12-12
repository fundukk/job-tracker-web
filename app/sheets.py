#!/usr/bin/env python3
"""
Google Sheets integration using OAuth 2.0.
Handles all sheet operations for the job tracker application.
"""
import logging
import gspread
from datetime import date
from google.oauth2.credentials import Credentials
# DEBUG – REMOVE AFTER DIAGNOSIS
try:
    from googleapiclient.errors import HttpError
except ImportError:
    HttpError = None

logger = logging.getLogger(__name__)

# Expected column headers for the job tracker sheet
COLUMNS = [
    "DateApplied",
    "Company",
    "Location",
    "Position",
    "Link",
    "Salary",
    "JobType",
    "Remote",
    "Status",
    "Source",
    "Notes",
]


def get_gspread_client(credentials_dict):
    """
    Authorize using OAuth credentials and return a gspread client.
    
    Args:
        credentials_dict: OAuth credentials from Flask session
        
    Returns:
        gspread.Client: Authorized client
        
    Raises:
        ValueError: If credentials_dict is None or invalid
        gspread.exceptions.GSpreadException: If authorization fails
    """
    if not credentials_dict:
        logger.error("No credentials provided to get_gspread_client")
        raise ValueError("No OAuth credentials found. Please log in with Google first.")
    
    try:
        # Reconstruct credentials from dictionary
        from datetime import datetime
        
        expiry = None
        if credentials_dict.get('expiry'):
            expiry = datetime.fromisoformat(credentials_dict['expiry'])
        
        credentials = Credentials(
            token=credentials_dict['token'],
            refresh_token=credentials_dict.get('refresh_token'),
            token_uri=credentials_dict['token_uri'],
            client_id=credentials_dict['client_id'],
            client_secret=credentials_dict['client_secret'],
            scopes=credentials_dict['scopes'],
            expiry=expiry
        )
        
        # Authorize and return gspread client
        client = gspread.authorize(credentials)
        logger.debug("Successfully authorized gspread client")
        return client
    
    except KeyError as e:
        logger.error(f"Invalid credentials dictionary, missing key: {e}")
        raise ValueError(f"Invalid credentials format: missing {e}")
    except Exception as e:
        logger.error(f"Failed to authorize gspread client: {str(e)}", exc_info=True)
        raise


def extract_spreadsheet_id(sheet_url_or_id: str) -> str:
    """
    Extract ID from a Google Sheet URL or return raw ID.
    
    Args:
        sheet_url_or_id: Full Google Sheet URL or just the ID
        
    Returns:
        str: The spreadsheet ID
        
    Example:
        >>> extract_spreadsheet_id("https://docs.google.com/spreadsheets/d/ABC123/edit")
        'ABC123'
        >>> extract_spreadsheet_id("ABC123")
        'ABC123'
    """
    raw = (sheet_url_or_id or "").strip()
    
    # If it's a full URL, extract the ID
    if "docs.google.com" in raw and "/d/" in raw:
        return raw.split("/d/", 1)[1].split("/", 1)[0].strip()
    
    # Otherwise assume it's already an ID
    return raw


def get_worksheet(sheet_url_or_id: str, credentials_dict):
    """
    Return the first worksheet of the sheet.
    
    Args:
        sheet_url_or_id: Google Sheet URL or ID
        credentials_dict: OAuth credentials from Flask session
        
    Returns:
        gspread.Worksheet: The first worksheet
        
    Raises:
        gspread.exceptions.SpreadsheetNotFound: If sheet doesn't exist
        gspread.exceptions.APIError: If API call fails
    """
    try:
        client = get_gspread_client(credentials_dict)
        sheet_id = extract_spreadsheet_id(sheet_url_or_id)
        
        # DEBUG – REMOVE AFTER DIAGNOSIS: Log credentials scopes
        if credentials_dict:
            scopes = credentials_dict.get('scopes', [])
            logger.info(f"DEBUG – OAuth scopes attached: {scopes}")
        
        logger.info(f"Opening spreadsheet: {sheet_id}")
        
        # Open spreadsheet by ID
        sh = client.open_by_key(sheet_id)
        ws = sh.sheet1
        
        # Ensure header row exists
        first_row = ws.row_values(1)
        if not first_row or len(first_row) < len(COLUMNS):
            logger.info("Inserting header row into sheet")
            ws.insert_row(COLUMNS, 1)
        
        logger.info(f"Successfully opened worksheet: {ws.title}")
        return ws
    
    except gspread.exceptions.SpreadsheetNotFound:
        logger.error(f"Spreadsheet not found: {sheet_url_or_id}")
        raise
    except gspread.exceptions.APIError as e:
        # DEBUG – REMOVE AFTER DIAGNOSIS: Extract Google error details
        logger.error(f"Google API error accessing sheet: {str(e)}", exc_info=True)
        if HttpError and isinstance(e, HttpError):
            logger.error(f"DEBUG – HTTP status code: {e.resp.status}")
            logger.error(f"DEBUG – HTTP reason: {e.resp.reason}")
            try:
                logger.error(f"DEBUG – Error content: {e.content.decode('utf-8')}")
            except:
                logger.error(f"DEBUG – Error content (raw): {e.content}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error opening worksheet: {str(e)}", exc_info=True)
        # DEBUG – REMOVE AFTER DIAGNOSIS: Log exception type and traceback
        logger.error(f"DEBUG – Exception type: {type(e).__name__}")
        raise


def check_write_access(ws) -> bool:
    """
    Verify that the current user has write access to the worksheet.

    Performs a minimal no-op update (writes the same value back) to avoid
    modifying content while still exercising write permissions.

    Returns:
        bool: True if write succeeds, False if forbidden or fails.
    """
    try:
        # Read existing value from header cell and write it back
        val = ws.cell(1, 1).value or ""
        ws.update_cell(1, 1, val)
        return True
    except gspread.exceptions.APIError as e:
        # 403 typically indicates insufficient permissions
        logger.warning(f"Write access check failed: {str(e)}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error during write access check: {str(e)}")
        return False
    except gspread.exceptions.APIError as e:
        logger.error(f"Google API error accessing sheet: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error opening worksheet: {str(e)}", exc_info=True)
        raise


def append_job_row(ws, job_data: dict):
    """
    Append a row with job_data fields to the Google Sheet.
    
    Args:
        ws: gspread.Worksheet instance
        job_data: Dictionary containing job fields
        
    Raises:
        gspread.exceptions.APIError: If API call fails
    """
    try:
        # Create row data in the correct column order
        row = [
            date.today().isoformat(),  # DateApplied
            job_data.get("company", ""),
            job_data.get("location", ""),
            job_data.get("position", ""),
            job_data.get("link", ""),
            job_data.get("salary", ""),
            job_data.get("job_type", ""),
            job_data.get("remote", ""),
            job_data.get("status", "Applied"),
            job_data.get("source", ""),
            job_data.get("notes", ""),
        ]
        
        # Insert at row 2 (right after header) to keep newest entries at top
        logger.info(f"Appending job: {job_data.get('position')} at {job_data.get('company')}")
        ws.insert_row(row, 2, value_input_option="USER_ENTERED")
        logger.info("Successfully appended job row")
    
    except gspread.exceptions.APIError as e:
        logger.error(f"Google API error appending row: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error appending row: {str(e)}", exc_info=True)
        raise


def find_job_by_link(ws, link: str) -> int:
    """
    Find row number containing the given link.
    
    Args:
        ws: gspread.Worksheet instance
        link: Job URL to search for
        
    Returns:
        int: Row number if found, 0 otherwise
    """
    if not link:
        return 0
    
    try:
        # Get all values from the Link column (column E, index 5)
        logger.debug(f"Searching for duplicate job URL: {link}")
        all_values = ws.get_all_values()
        
        # Skip header row, search from row 2 onwards
        for idx, row in enumerate(all_values[1:], start=2):
            # Link is in column 5 (index 4)
            if len(row) > 4 and row[4].strip() == link.strip():
                logger.info(f"Found duplicate job at row {idx}")
                return idx
        
        logger.debug("No duplicate job found")
        return 0
    
    except Exception as e:
        logger.warning(f"Error searching for job by link: {str(e)}")
        return 0


def get_trash_sheet(ws):
    """
    Return the worksheet titled 'Trash', creating it with headers if missing.
    
    Args:
        ws: gspread.Worksheet instance
        
    Returns:
        gspread.Worksheet or None: Trash worksheet if successful, None otherwise
    """
    sh = ws.spreadsheet
    title = "Trash"
    
    try:
        trash = sh.worksheet(title)
        logger.debug("Found existing Trash sheet")
    except Exception:
        # Create sheet with enough rows/cols
        try:
            logger.info("Creating new Trash sheet")
            trash = sh.add_worksheet(title=title, rows=1000, cols=max(10, len(COLUMNS)))
        except Exception as e:
            logger.error(f"Failed to create Trash sheet: {str(e)}")
            return None
    
    # Ensure header row exists
    try:
        first = trash.row_values(1)
        if not first or len(first) < len(COLUMNS):
            logger.info("Inserting header row into Trash sheet")
            trash.insert_row(COLUMNS, 1)
    except Exception as e:
        logger.warning(f"Failed to insert header in Trash sheet: {str(e)}")
    
    return trash


def move_row_to_trash(ws, row_index: int) -> bool:
    """
    Copy a row into the Trash sheet and delete it from the original sheet.
    
    Args:
        ws: gspread.Worksheet instance
        row_index: Row number to move (1-indexed)
        
    Returns:
        bool: True if moved successfully, False otherwise
    """
    try:
        # Read row values and pad to column count
        row_vals = ws.row_values(row_index)
        if len(row_vals) < len(COLUMNS):
            row_vals += [""] * (len(COLUMNS) - len(row_vals))
        
        trash = get_trash_sheet(ws)
        if trash is None:
            logger.warning("Could not get Trash sheet, skipping move")
            return False
        
        # Insert at top (row 2) to keep newest items near top
        try:
            trash.insert_row(row_vals, 2, value_input_option="USER_ENTERED")
            logger.info(f"Copied row {row_index} to Trash")
        except Exception as e:
            # Fallback to append if insert fails
            logger.warning(f"Insert failed, attempting append: {str(e)}")
            try:
                trash.append_row(row_vals, value_input_option="USER_ENTERED")
            except Exception as e2:
                logger.error(f"Failed to append to Trash: {str(e2)}")
                return False
        
        # After copying, delete original row
        try:
            ws.delete_rows(row_index)
            logger.info(f"Deleted row {row_index} from main sheet")
        except Exception as e:
            logger.error(f"Failed to delete row {row_index}: {str(e)}")
            return False
        
        return True
    
    except Exception as e:
        logger.error(f"Error moving row to trash: {str(e)}", exc_info=True)
        return False


def replace_job_by_link(ws, job_data: dict):
    """
    Replace existing job with same link, or add new if not found.
    Moves old entry to Trash sheet before replacing.
    
    Args:
        ws: gspread.Worksheet instance
        job_data: Dictionary containing job fields
        
    Returns:
        bool: True if replaced, False if added new
    """
    link = job_data.get("link", "")
    existing_row = find_job_by_link(ws, link)
    
    # Create row data
    row = [
        date.today().isoformat(),  # DateApplied
        job_data.get("company", ""),
        job_data.get("location", ""),
        job_data.get("position", ""),
        job_data.get("link", ""),
        job_data.get("salary", ""),
        job_data.get("job_type", ""),
        job_data.get("remote", ""),
        job_data.get("status", "Applied"),
        job_data.get("source", ""),
        job_data.get("notes", ""),
    ]
    
    if existing_row:
        logger.info(f"Replacing existing job at row {existing_row}")
        # Move old row to Trash (this deletes it from main sheet)
        moved = move_row_to_trash(ws, existing_row)
        if not moved:
            # Fallback: just delete if trash failed
            try:
                ws.delete_rows(existing_row)
            except Exception as e:
                logger.warning(f"Failed to delete existing row: {str(e)}")
        
        # Insert new entry at row 2 (top, after header)
        ws.insert_row(row, 2, value_input_option="USER_ENTERED")
        return True  # Replaced
    else:
        logger.info("No existing job found, adding as new")
        # Add new at row 2
        ws.insert_row(row, 2, value_input_option="USER_ENTERED")
        return False  # Added new


def replace_last_job(ws, job_data: dict):
    """
    Replace the most recent job (row 2) with new data.
    Moves old entry to Trash before replacing.
    
    Args:
        ws: gspread.Worksheet instance
        job_data: Dictionary containing job fields
        
    Returns:
        bool: True if replaced successfully, False otherwise
    """
    try:
        all_rows = ws.get_all_values()
        if len(all_rows) <= 1:  # Only header or empty
            logger.info("No existing jobs to replace")
            return False
        
        # Create new row data
        row = [
            date.today().isoformat(),  # DateApplied
            job_data.get("company", ""),
            job_data.get("location", ""),
            job_data.get("position", ""),
            job_data.get("link", ""),
            job_data.get("salary", ""),
            job_data.get("job_type", ""),
            job_data.get("remote", ""),
            job_data.get("status", "Applied"),
            job_data.get("source", ""),
            job_data.get("notes", ""),
        ]
        
        logger.info("Replacing last job (row 2)")
        # Move row 2 to Trash (this deletes it)
        moved = move_row_to_trash(ws, 2)
        if not moved:
            # Fallback: just delete
            try:
                ws.delete_rows(2)
            except Exception as e:
                logger.warning(f"Failed to delete row 2: {str(e)}")
        
        # Insert new entry at row 2
        ws.insert_row(row, 2, value_input_option="USER_ENTERED")
        logger.info("Successfully replaced last job")
        return True
    
    except Exception as e:
        logger.error(f"Error replacing last job: {str(e)}", exc_info=True)
        return False
