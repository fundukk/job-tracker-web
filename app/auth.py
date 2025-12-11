#!/usr/bin/env python3
"""
Google OAuth 2.0 authentication blueprint.
Handles login, logout, and OAuth callback for the job tracker app.
"""
import os
import logging
from functools import wraps
from pathlib import Path
from flask import Blueprint, request, redirect, url_for, session, flash, current_app
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# OAuth 2.0 scopes required for Google Sheets access
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid"
]

# OAuth redirect URI - read from environment or use production default
REDIRECT_URI = os.environ.get(
    'OAUTH_REDIRECT_URI',
    'https://job-tracker-web.onrender.com/oauth2callback'
)


def get_oauth_flow():
    """
    Create and return a Google OAuth Flow object.
    
    Returns:
        Flow: Configured OAuth flow
        
    Raises:
        FileNotFoundError: If client secret file not found
        KeyError: If GOOGLE_OAUTH_CLIENT_SECRET_FILE env var not set
    """
    client_secret_file = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET_FILE')
    
    if not client_secret_file:
        logger.error("GOOGLE_OAUTH_CLIENT_SECRET_FILE environment variable not set")
        raise KeyError(
            "GOOGLE_OAUTH_CLIENT_SECRET_FILE environment variable not set. "
            "Please configure this in your Render dashboard."
        )
    
    client_secret_path = Path(client_secret_file)
    
    if not client_secret_path.exists():
        logger.error(f"OAuth client secret file not found at {client_secret_path}")
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
        'scopes': credentials.scopes,
        'expiry': credentials.expiry.isoformat() if credentials.expiry else None
    }


def credentials_from_dict(credentials_dict):
    """
    Reconstruct OAuth credentials from a dictionary.
    
    Args:
        credentials_dict: Dictionary containing credentials data
        
    Returns:
        Credentials: google.oauth2.credentials.Credentials object
    """
    from datetime import datetime
    
    expiry = None
    if credentials_dict.get('expiry'):
        expiry = datetime.fromisoformat(credentials_dict['expiry'])
    
    return Credentials(
        token=credentials_dict['token'],
        refresh_token=credentials_dict.get('refresh_token'),
        token_uri=credentials_dict['token_uri'],
        client_id=credentials_dict['client_id'],
        client_secret=credentials_dict['client_secret'],
        scopes=credentials_dict['scopes'],
        expiry=expiry
    )


def refresh_credentials_if_needed(credentials_dict):
    """
    Check if credentials are expired and refresh if possible.
    
    Args:
        credentials_dict: Dictionary containing credentials data
        
    Returns:
        tuple: (updated_credentials_dict, was_refreshed)
        
    Raises:
        Exception: If refresh fails
    """
    credentials = credentials_from_dict(credentials_dict)
    
    # Check if token is expired
    if credentials.expired and credentials.refresh_token:
        try:
            logger.info("Access token expired, refreshing...")
            credentials.refresh(Request())
            logger.info("Access token refreshed successfully")
            return credentials_to_dict(credentials), True
        except Exception as e:
            logger.error(f"Failed to refresh access token: {str(e)}")
            raise
    
    return credentials_dict, False


def require_oauth(f):
    """
    Decorator to ensure user is authenticated with Google OAuth.
    Automatically refreshes expired tokens if refresh token is available.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'credentials' not in session:
            # Store the intended destination
            session['next_url'] = request.url
            flash('Please log in with Google to continue', 'warning')
            logger.info(f"Unauthenticated access to {request.path}, redirecting to login")
            return redirect(url_for('auth.login'))
        
        # Try to refresh credentials if expired
        try:
            credentials_dict = session['credentials']
            updated_creds, was_refreshed = refresh_credentials_if_needed(credentials_dict)
            
            if was_refreshed:
                session['credentials'] = updated_creds
                logger.info("Session credentials updated with refreshed token")
        
        except Exception as e:
            # Refresh failed - clear session and force re-login
            logger.warning(f"Token refresh failed, clearing session: {str(e)}")
            session.clear()
            flash('Your session has expired. Please log in again.', 'warning')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated_function


@auth_bp.route('/auth/google')
@auth_bp.route('/login')
def login():
    """Initiate Google OAuth flow."""
    try:
        flow = get_oauth_flow()
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent screen to get refresh token
        )
        
        # Store state in session for verification
        session['state'] = state
        
        logger.info("Redirecting user to Google OAuth consent screen")
        return redirect(authorization_url)
    
    except Exception as e:
        logger.error(f"Error initiating Google login: {str(e)}", exc_info=True)
        flash(f'Error initiating Google login: {str(e)}', 'error')
        return redirect(url_for('main.index'))


@auth_bp.route('/oauth2callback')
def oauth2callback():
    """Handle OAuth callback from Google."""
    try:
        # Verify state
        state = session.get('state')
        if not state or state != request.args.get('state'):
            logger.warning("Invalid state parameter in OAuth callback")
            flash('Invalid state parameter. Please try logging in again.', 'error')
            return redirect(url_for('main.index'))
        
        # Exchange authorization code for credentials
        flow = get_oauth_flow()
        
        # IMPORTANT: For production HTTPS, we need to use the full callback URL
        # request.url might be http:// even when accessed via https:// on Render
        authorization_response = request.url
        if authorization_response.startswith('http://'):
            authorization_response = authorization_response.replace('http://', 'https://', 1)
        
        flow.fetch_token(authorization_response=authorization_response)
        
        # Store credentials in session
        credentials = flow.credentials
        session['credentials'] = credentials_to_dict(credentials)
        
        logger.info("User successfully authenticated with Google OAuth")
        flash('Successfully logged in with Google!', 'success')
        
        # Redirect to intended destination or index
        next_url = session.pop('next_url', None)
        return redirect(next_url or url_for('main.index'))
    
    except Exception as e:
        logger.error(f"Error completing Google login: {str(e)}", exc_info=True)
        flash(f'Error completing Google login: {str(e)}', 'error')
        return redirect(url_for('main.index'))


@auth_bp.route('/logout')
def logout():
    """Log out user by clearing session."""
    logger.info("User logged out")
    session.clear()
    flash('Successfully logged out', 'success')
    return redirect(url_for('main.index'))
