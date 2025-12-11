#!/usr/bin/env python3
"""
Centralized Google Sheets authentication module.
This module provides a single point of configuration for Google Sheets access,
making it easy to switch between service account and OAuth authentication.
"""
import os
import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path


def get_gspread_client():
    """
    Get an authenticated gspread client.
    
    Currently uses service account authentication.
    Can be extended to support OAuth in the future.
    
    Returns:
        gspread.Client: Authenticated gspread client
        
    Raises:
        FileNotFoundError: If credentials file not found
        Exception: If authentication fails
    """
    auth_mode = os.environ.get('GOOGLE_AUTH_MODE', 'service_account')
    
    if auth_mode == 'service_account':
        return _get_service_account_client()
    elif auth_mode == 'oauth':
        # Placeholder for future OAuth implementation
        raise NotImplementedError("OAuth authentication not yet implemented")
    else:
        raise ValueError(f"Unknown GOOGLE_AUTH_MODE: {auth_mode}")


def _get_service_account_client():
    """Get gspread client using service account credentials."""
    # Get credentials file path from environment or use default
    base_dir = Path(__file__).resolve().parent
    default_path = base_dir / "credentials.json"
    creds_path = os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE', str(default_path))
    creds_file = Path(creds_path)
    
    if not creds_file.exists():
        raise FileNotFoundError(
            f"Google service account credentials not found at {creds_file}. "
            f"Please ensure GOOGLE_SERVICE_ACCOUNT_FILE environment variable "
            f"points to a valid credentials.json file, or place credentials.json "
            f"in the project root."
        )
    
    # Define required scopes
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    
    # Authenticate and return client
    creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
    client = gspread.authorize(creds)
    return client


# Placeholder for future OAuth implementation
def _get_oauth_client():
    """
    Get gspread client using OAuth credentials.
    
    This is a placeholder for future implementation.
    Will require:
    - GOOGLE_OAUTH_CLIENT_ID
    - GOOGLE_OAUTH_CLIENT_SECRET
    - Token storage/refresh logic
    """
    raise NotImplementedError(
        "OAuth authentication not yet implemented. "
        "Use service_account mode for now."
    )
