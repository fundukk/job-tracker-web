#!/usr/bin/env python3
"""
Centralized Google Sheets authentication module.
Now uses OAuth 2.0 (3-legged) flow instead of service account.
"""
import os
import json
import gspread
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

# OAuth 2.0 scopes required for Google Sheets access
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid"
]

# OAuth redirect URI (must match Google Cloud Console configuration)
REDIRECT_URI = "https://job-tracker-web.onrender.com/oauth2callback"


def get_oauth_flow():
    """
    Create and return a Google OAuth Flow object.
    
    Returns:
        Flow: Configured OAuth flow
        
    Raises:
        FileNotFoundError: If client secret file not found
        KeyError: If GOOGLE_OAUTH_CLIENT_SECRET_FILE env var not set
    """
    # Get client secret file path from environment
    client_secret_file = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET_FILE')
    
    if not client_secret_file:
        raise KeyError(
            "GOOGLE_OAUTH_CLIENT_SECRET_FILE environment variable not set. "
            "Please configure this in your Render dashboard."
        )
    
    client_secret_path = Path(client_secret_file)
    
    if not client_secret_path.exists():
        raise FileNotFoundError(
            f"OAuth client secret file not found at {client_secret_path}. "
            f"Please ensure the secret file is configured in Render."
        )
    
    # Create OAuth flow
    flow = Flow.from_client_secrets_file(
        client_secret_file,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    
    return flow


def credentials_to_dict(credentials):
    """
    Convert OAuth credentials to a dictionary for session storage.
    
    Args:
        credentials: google.oauth2.credentials.Credentials object
        
    Returns:
        dict: Serializable credentials dictionary
    """
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }


def credentials_from_dict(credentials_dict):
    """
    Reconstruct OAuth credentials from a dictionary.
    
    Args:
        credentials_dict: Dictionary containing credentials data
        
    Returns:
        Credentials: google.oauth2.credentials.Credentials object
    """
    return Credentials(
        token=credentials_dict['token'],
        refresh_token=credentials_dict.get('refresh_token'),
        token_uri=credentials_dict['token_uri'],
        client_id=credentials_dict['client_id'],
        client_secret=credentials_dict['client_secret'],
        scopes=credentials_dict['scopes']
    )


def get_gspread_client(credentials_dict):
    """
    Get an authenticated gspread client using OAuth credentials.
    
    Args:
        credentials_dict: Dictionary containing OAuth credentials from session
        
    Returns:
        gspread.Client: Authenticated gspread client
        
    Raises:
        ValueError: If credentials_dict is None or invalid
    """
    if not credentials_dict:
        raise ValueError(
            "No OAuth credentials found. Please log in with Google first."
        )
    
    # Reconstruct credentials from dictionary
    credentials = credentials_from_dict(credentials_dict)
    
    # Authorize and return gspread client
    client = gspread.authorize(credentials)
    return client
