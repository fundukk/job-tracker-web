#!/usr/bin/env python3
"""Google Sheets integration using OAuth 2.0."""
import os
import gspread
from pathlib import Path
from datetime import date
from google_client import get_gspread_client as get_client

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
    """
    return get_client(credentials_dict)


def extract_spreadsheet_id(sheet_url_or_id: str) -> str:
    """Extract ID from a Google Sheet URL or return raw ID."""
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
    """
    client = get_gspread_client(credentials_dict)
    sheet_id = extract_spreadsheet_id(sheet_url_or_id)
    
    # Open spreadsheet by ID
    sh = client.open_by_key(sheet_id)
    ws = sh.sheet1
    
    # Ensure header row exists
    first_row = ws.row_values(1)
    if not first_row or len(first_row) < len(COLUMNS):
        ws.insert_row(COLUMNS, 1)
    
    return ws


def append_job_row(ws, job_data: dict):
    """Append a row with job_data fields to the Google Sheet."""
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
    ws.insert_row(row, 2, value_input_option="USER_ENTERED")


def find_job_by_link(ws, link: str) -> int:
    """Find row number containing the given link. Returns 0 if not found."""
    if not link:
        return 0
    
    try:
        # Get all values from the Link column (column E, index 5)
        all_values = ws.get_all_values()
        
        # Skip header row, search from row 2 onwards
        for idx, row in enumerate(all_values[1:], start=2):
            # Link is in column 5 (index 4)
            if len(row) > 4 and row[4].strip() == link.strip():
                return idx
        
        return 0
    except Exception:
        return 0


def get_trash_sheet(ws):
    """Return the worksheet titled 'Trash', creating it with headers if missing."""
    sh = ws.spreadsheet
    title = "Trash"
    try:
        trash = sh.worksheet(title)
    except Exception:
        # Create sheet with enough rows/cols
        try:
            trash = sh.add_worksheet(title=title, rows=1000, cols=max(10, len(COLUMNS)))
        except Exception:
            return None
    
    # Ensure header row exists
    try:
        first = trash.row_values(1)
        if not first or len(first) < len(COLUMNS):
            trash.insert_row(COLUMNS, 1)
    except Exception:
        pass
    
    return trash


def move_row_to_trash(ws, row_index: int) -> bool:
    """
    Copy a row into the Trash sheet and delete it from the original sheet.
    Returns True if moved successfully, False otherwise.
    """
    try:
        # Read row values and pad to column count
        row_vals = ws.row_values(row_index)
        if len(row_vals) < len(COLUMNS):
            row_vals += [""] * (len(COLUMNS) - len(row_vals))
        
        trash = get_trash_sheet(ws)
        if trash is None:
            return False
        
        # Insert at top (row 2) to keep newest items near top
        try:
            trash.insert_row(row_vals, 2, value_input_option="USER_ENTERED")
        except Exception:
            # Fallback to append if insert fails
            try:
                trash.append_row(row_vals, value_input_option="USER_ENTERED")
            except Exception:
                return False
        
        # After copying, delete original row
        try:
            ws.delete_rows(row_index)
        except Exception:
            # If delete failed, don't consider it moved
            return False
        
        return True
    except Exception:
        return False


def replace_job_by_link(ws, job_data: dict):
    """
    Replace existing job with same link, or add new if not found.
    Moves old entry to Trash sheet before replacing.
    Returns True if replaced, False if added new.
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
        # Move old row to Trash (this deletes it from main sheet)
        moved = move_row_to_trash(ws, existing_row)
        if not moved:
            # Fallback: just delete if trash failed
            try:
                ws.delete_rows(existing_row)
            except Exception:
                pass
        
        # Insert new entry at row 2 (top, after header)
        ws.insert_row(row, 2, value_input_option="USER_ENTERED")
        return True  # Replaced
    else:
        # Add new at row 2
        ws.insert_row(row, 2, value_input_option="USER_ENTERED")
        return False  # Added new


def replace_last_job(ws, job_data: dict):
    """
    Replace the most recent job (row 2) with new data.
    Moves old entry to Trash before replacing.
    Returns True if replaced successfully, False otherwise.
    """
    try:
        all_rows = ws.get_all_values()
        if len(all_rows) <= 1:  # Only header or empty
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
        
        # Move row 2 to Trash (this deletes it)
        moved = move_row_to_trash(ws, 2)
        if not moved:
            # Fallback: just delete
            try:
                ws.delete_rows(2)
            except Exception:
                pass
        
        # Insert new entry at row 2
        ws.insert_row(row, 2, value_input_option="USER_ENTERED")
        return True
    
    except Exception:
        return False
