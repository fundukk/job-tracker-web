#!/usr/bin/env python3
"""Google Sheets integration using service account."""
import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
from datetime import date

# Path to credentials file (should be in the same directory as app.py)
BASE_DIR = Path(__file__).resolve().parent.parent
SERVICE_ACCOUNT_FILE = BASE_DIR / "credentials.json"

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


def get_gspread_client():
    """Authorize using credentials.json and return a gspread client."""
    if not SERVICE_ACCOUNT_FILE.exists():
        raise FileNotFoundError(
            f"credentials.json not found at {SERVICE_ACCOUNT_FILE}. "
            "Please place your Google service account credentials file in the project root."
        )
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    return client


def extract_spreadsheet_id(sheet_url_or_id: str) -> str:
    """Extract ID from a Google Sheet URL or return raw ID."""
    raw = (sheet_url_or_id or "").strip()
    
    # If it's a full URL, extract the ID
    if "docs.google.com" in raw and "/d/" in raw:
        return raw.split("/d/", 1)[1].split("/", 1)[0].strip()
    
    # Otherwise assume it's already an ID
    return raw


def get_worksheet(sheet_url_or_id: str):
    """Return the first worksheet of the sheet."""
    client = get_gspread_client()
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
