#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash
from core.sheets import get_worksheet, append_job_row, replace_job_by_link, replace_last_job, extract_spreadsheet_id
from core.jobs import process_job_url, validate_job_url
from core.salary import normalize_salary
from google_client import get_oauth_flow, credentials_to_dict, credentials_from_dict

# Load environment variables from .env file (for local development)
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')


def require_oauth(f):
    """Decorator to ensure user is authenticated with Google OAuth."""
    def decorated_function(*args, **kwargs):
        if 'credentials' not in session:
            # Store the intended destination
            session['next_url'] = request.url
            flash('Please log in with Google to continue', 'warning')
            return redirect(url_for('auth_google'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@app.route('/')
def index():
    """Step 1: Ask user for Google Sheet link (requires OAuth)."""
    # Check if user is authenticated
    if 'credentials' not in session:
        return redirect(url_for('auth_google'))
    return render_template('index.html')


@app.route('/auth/google')
def auth_google():
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
        
        return redirect(authorization_url)
    
    except Exception as e:
        flash(f'Error initiating Google login: {str(e)}', 'error')
        return render_template('error.html', error=str(e))


@app.route('/oauth2callback')
def oauth2callback():
    """Handle OAuth callback from Google."""
    try:
        # Verify state
        state = session.get('state')
        if not state or state != request.args.get('state'):
            flash('Invalid state parameter. Please try logging in again.', 'error')
            return redirect(url_for('index'))
        
        # Exchange authorization code for credentials
        flow = get_oauth_flow()
        flow.fetch_token(authorization_response=request.url)
        
        # Store credentials in session
        credentials = flow.credentials
        session['credentials'] = credentials_to_dict(credentials)
        
        flash('Successfully logged in with Google!', 'success')
        
        # Redirect to intended destination or index
        next_url = session.pop('next_url', None)
        return redirect(next_url or url_for('index'))
    
    except Exception as e:
        flash(f'Error completing Google login: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/logout')
def logout():
    """Log out user by clearing session."""
    session.clear()
    flash('Successfully logged out', 'success')
    return redirect(url_for('index'))


@app.route('/set_sheet', methods=['POST'])
@require_oauth
def set_sheet():
    """Validate and store the Google Sheet link."""
    sheet_url = request.form.get('sheet_url', '').strip()
    
    if not sheet_url:
        flash('Please provide a Google Sheet URL or ID', 'error')
        return redirect(url_for('index'))
    
    try:
        # Validate that we can access the sheet with OAuth credentials
        sheet_id = extract_spreadsheet_id(sheet_url)
        credentials_dict = session.get('credentials')
        ws = get_worksheet(sheet_id, credentials_dict)
        
        # Store in session
        session['sheet_url'] = sheet_id
        flash('Sheet connected successfully!', 'success')
        return redirect(url_for('job'))
    
    except Exception as e:
        flash(f'Could not connect to Google Sheets. Please make sure you have access to this sheet and try logging in with Google again.', 'error')
        return redirect(url_for('index'))


@app.route('/job', methods=['GET', 'POST'])
@require_oauth
def job():
    """Step 2: Ask user for job URL (GET) or parse and review (POST)."""
    if 'sheet_url' not in session:
        flash('Please set your Google Sheet first', 'warning')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # User submitted a job URL for parsing
        job_url = request.form.get('job_url', '').strip()
        
        if not job_url:
            flash('Please provide a job URL', 'error')
            return redirect(url_for('job'))
        
        # Validate URL format
        is_valid, error_msg = validate_job_url(job_url)
        if not is_valid:
            flash(error_msg, 'error')
            return redirect(url_for('job'))
        
        # Check if it's a Handshake URL - ask for text input
        if 'handshake' in job_url.lower():
            session['pending_handshake_url'] = job_url
            return render_template('handshake_text.html', job_url=job_url)
        
        try:
            # Process the job URL (parse only, don't save yet)
            job_data = process_job_url(job_url)
            
            # Render review/edit form with parsed data
            return render_template('review_job.html', data=job_data)
        
        except Exception as e:
            flash(f'Error processing job: {str(e)}', 'error')
            return redirect(url_for('job'))
    
    # GET request - show job URL input form
    return render_template('job.html')


@app.route('/parse_handshake', methods=['POST'])
@require_oauth
def parse_handshake():
    """Parse Handshake job from copied text."""
    if 'sheet_url' not in session:
        flash('Please set your Google Sheet first', 'warning')
        return redirect(url_for('index'))
    
    job_text = request.form.get('job_text', '').strip()
    job_url = session.get('pending_handshake_url', '')
    
    if not job_text:
        flash('Please paste the job description text', 'error')
        return render_template('handshake_text.html', job_url=job_url)
    
    try:
        from core.jobs import parse_handshake_text_wrapper
        job_data = parse_handshake_text_wrapper(job_text, job_url)
        
        # Clear session
        session.pop('pending_handshake_url', None)
        
        # Render review/edit form with parsed data
        return render_template('review_job.html', data=job_data)
    
    except Exception as e:
        flash(f'Error parsing Handshake job: {str(e)}', 'error')
        return render_template('handshake_text.html', job_url=job_url)


@app.route('/add_job', methods=['POST'])
@require_oauth
def add_job():
    """Save reviewed/edited job data to Google Sheets."""
    if 'sheet_url' not in session:
        flash('Please set your Google Sheet first', 'warning')
        return redirect(url_for('index'))
    
    try:
        # Collect all fields from the review form
        job_data = {
            'position': request.form.get('position', '').strip(),
            'company': request.form.get('company', '').strip(),
            'location': request.form.get('location', '').strip(),
            'salary': request.form.get('salary', '').strip(),
            'job_type': request.form.get('job_type', '').strip(),
            'remote': request.form.get('remote', '').strip(),
            'link': request.form.get('link', '').strip(),
            'source': request.form.get('source', '').strip(),
            'status': request.form.get('status', 'Applied').strip(),
            'notes': request.form.get('notes', '').strip(),
        }
        
        # Normalize salary (convert hourly/monthly to annual)
        if job_data['salary']:
            job_data['salary'] = normalize_salary(job_data['salary'])
        
        # Check if user wants to replace last job (manual override)
        replace_last = request.form.get('replace_last_job') == 'on'
        
        # Get the worksheet with OAuth credentials
        sheet_id = session['sheet_url']
        credentials_dict = session.get('credentials')
        ws = get_worksheet(sheet_id, credentials_dict)
        
        if replace_last:
            # Replace the most recent job (row 2)
            success = replace_last_job(ws, job_data)
            if success:
                flash('Job replaced successfully! (Old entry moved to Trash)', 'success')
            else:
                flash('No previous job to replace. Adding as new entry.', 'warning')
        else:
            # Check for duplicate by URL
            from core.sheets import find_job_by_link
            existing_row = find_job_by_link(ws, job_data.get('link', ''))
            
            if existing_row:
                # Duplicate found - send back to URL input page
                flash('⚠️ This job URL already exists in your sheet! Please add a different job.', 'error')
                return redirect(url_for('job'))
            else:
                # No duplicate - add new job
                append_job_row(ws, job_data)
                flash('Job added successfully!', 'success')
        
        return render_template('success.html', job_data=job_data)
    
    except Exception as e:
        flash(f'Error saving job: {str(e)}', 'error')
        return redirect(url_for('job'))


if __name__ == '__main__':
    app.run(debug=True)
