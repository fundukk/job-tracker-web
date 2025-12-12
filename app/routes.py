#!/usr/bin/env python3
"""
Main application routes blueprint.
Handles job tracker UI and job processing routes.
"""
import logging
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.auth import require_oauth
from app.sheets import (
    get_worksheet,
    append_job_row,
    replace_last_job,
    extract_spreadsheet_id,
    find_job_by_link,
    check_write_access,
)
from app.parsers import process_job_url, validate_job_url, parse_handshake_text_wrapper
from core.salary import normalize_salary

logger = logging.getLogger(__name__)

# Create blueprint
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Step 1: Ask user for Google Sheet link (requires OAuth)."""
    # Check if user is authenticated
    if 'credentials' not in session:
        logger.info("Unauthenticated user visiting index, redirecting to login")
        return redirect(url_for('auth.login'))
    
    logger.info("Authenticated user viewing index page")
    return render_template('index.html', user_email=session.get('user_email'))


@main_bp.route('/set_sheet', methods=['POST'])
@require_oauth
def set_sheet():
    """Validate and store the Google Sheet link."""
    sheet_url = request.form.get('sheet_url', '').strip()
    
    if not sheet_url:
        flash('Please provide a Google Sheet URL or ID', 'error')
        return redirect(url_for('main.index'))
    
    try:
        # Validate that we can access the sheet with OAuth credentials
        sheet_id = extract_spreadsheet_id(sheet_url)
        credentials_dict = session.get('credentials')
        user_email = session.get('user_email', 'unknown')
        
        logger.info(f"Attempting to connect to sheet: {sheet_id} (user: {user_email})")
        ws = get_worksheet(sheet_id, credentials_dict)
        logger.info(f"Sheet opened successfully, checking write access...")
        
        # Explicitly verify write access to surface read-only issues upfront
        try:
            write_ok = check_write_access(ws)
            logger.info(f"Write access check result: {write_ok}")
        except Exception as e:
            logger.warning(f"Write access check threw exception: {str(e)}", exc_info=True)
            write_ok = False
        
        if not write_ok:
            msg = 'Connected to the sheet, but it appears read-only. '
            if user_email and user_email != 'unknown':
                msg += f"Please share the sheet with Editor access to {user_email}. "
            else:
                msg += 'Please share the sheet with Editor access to your logged-in Google account. '
            msg += 'Then try connecting again.'
            logger.warning(f"Sheet is read-only: {sheet_id}")
            flash(msg, 'error')
            return redirect(url_for('main.index'))
        
        # Store in session
        session['sheet_url'] = sheet_id
        logger.info(f"Successfully connected to sheet: {sheet_id}")
        flash('Sheet connected successfully!', 'success')
        return redirect(url_for('main.job'))
    
    except Exception as e:
        logger.error(f"Failed to connect to Google Sheet: {str(e)}", exc_info=True)
        user_email = session.get('user_email', 'unknown')
        msg = 'Could not connect to your Google Sheet. '
        if user_email and user_email != 'unknown':
            msg += f"Ensure the sheet is shared with Editor access to {user_email}. "
        else:
            msg += 'Ensure the sheet is shared with your Google account. '
        msg += 'If needed, log out and sign in with the correct account.'
        flash(msg, 'error')
        return redirect(url_for('main.index'))


@main_bp.route('/job', methods=['GET', 'POST'])
@require_oauth
def job():
    """Step 2: Ask user for job URL (GET) or parse and review (POST)."""
    if 'sheet_url' not in session:
        flash('Please set your Google Sheet first', 'warning')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # User submitted a job URL for parsing
        job_url = request.form.get('job_url', '').strip()
        
        if not job_url:
            flash('Please provide a job URL', 'error')
            return redirect(url_for('main.job'))
        
        # Validate URL format
        is_valid, error_msg = validate_job_url(job_url)
        if not is_valid:
            logger.warning(f"Invalid job URL submitted: {job_url} - {error_msg}")
            flash(error_msg, 'error')
            return redirect(url_for('main.job'))
        
        # Check if it's a Handshake URL - ask for text input
        if 'handshake' in job_url.lower():
            session['pending_handshake_url'] = job_url
            logger.info(f"Handshake URL detected, requesting text input: {job_url}")
            return render_template('handshake_text.html', job_url=job_url)
        
        try:
            # Process the job URL (parse only, don't save yet)
            logger.info(f"Processing job URL: {job_url}")
            job_data = process_job_url(job_url)
            logger.info(f"Successfully parsed job: {job_data.get('position', 'Unknown')} at {job_data.get('company', 'Unknown')}")
            
            # Render review/edit form with parsed data
            return render_template('review_job.html', data=job_data)
        
        except Exception as e:
            logger.error(f"Error processing job URL {job_url}: {str(e)}", exc_info=True)
            flash(f'Error processing job: {str(e)}', 'error')
            return redirect(url_for('main.job'))
    
    # GET request - show job URL input form
    logger.info("User viewing job URL input form")
    return render_template('job.html')


@main_bp.route('/parse_handshake', methods=['POST'])
@require_oauth
def parse_handshake():
    """Parse Handshake job from copied text."""
    if 'sheet_url' not in session:
        flash('Please set your Google Sheet first', 'warning')
        return redirect(url_for('main.index'))
    
    job_text = request.form.get('job_text', '').strip()
    job_url = session.get('pending_handshake_url', '')
    
    if not job_text:
        flash('Please paste the job description text', 'error')
        return render_template('handshake_text.html', job_url=job_url)
    
    try:
        logger.info(f"Parsing Handshake job text for URL: {job_url}")
        job_data = parse_handshake_text_wrapper(job_text, job_url)
        logger.info(f"Successfully parsed Handshake job: {job_data.get('position', 'Unknown')}")
        
        # Clear session
        session.pop('pending_handshake_url', None)
        
        # Render review/edit form with parsed data
        return render_template('review_job.html', data=job_data)
    
    except Exception as e:
        logger.error(f"Error parsing Handshake job: {str(e)}", exc_info=True)
        flash(f'Error parsing Handshake job: {str(e)}', 'error')
        return render_template('handshake_text.html', job_url=job_url)


@main_bp.route('/add_job', methods=['POST'])
@require_oauth
def add_job():
    """Save reviewed/edited job data to Google Sheets."""
    if 'sheet_url' not in session:
        flash('Please set your Google Sheet first', 'warning')
        return redirect(url_for('main.index'))
    
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
        
        logger.info(f"Adding job: {job_data.get('position')} at {job_data.get('company')}")
        
        # Normalize salary (convert hourly/monthly to annual)
        if job_data['salary']:
            original_salary = job_data['salary']
            job_data['salary'] = normalize_salary(job_data['salary'])
            if original_salary != job_data['salary']:
                logger.info(f"Normalized salary: {original_salary} → {job_data['salary']}")
        
        # Check if user wants to replace last job (manual override)
        replace_last = request.form.get('replace_last_job') == 'on'
        
        # Get the worksheet with OAuth credentials
        sheet_id = session['sheet_url']
        credentials_dict = session.get('credentials')
        ws = get_worksheet(sheet_id, credentials_dict)
        
        if replace_last:
            # Replace the most recent job (row 2)
            logger.info("Replacing last job entry")
            success = replace_last_job(ws, job_data)
            if success:
                logger.info("Successfully replaced last job")
                flash('Job replaced successfully! (Old entry moved to Trash)', 'success')
            else:
                logger.warning("No previous job to replace, adding as new entry")
                flash('No previous job to replace. Adding as new entry.', 'warning')
        else:
            # Check for duplicate by URL
            existing_row = find_job_by_link(ws, job_data.get('link', ''))
            
            if existing_row:
                # Duplicate found - send back to URL input page
                logger.warning(f"Duplicate job URL found at row {existing_row}: {job_data.get('link')}")
                flash('⚠️ This job URL already exists in your sheet! Please add a different job.', 'error')
                return redirect(url_for('main.job'))
            else:
                # No duplicate - add new job
                logger.info("Adding new job to sheet")
                append_job_row(ws, job_data)
                logger.info("Successfully added new job")
                flash('Job added successfully!', 'success')
        
        return render_template('success.html', job_data=job_data)
    
    except Exception as e:
        logger.error(f"Error saving job to sheet: {str(e)}", exc_info=True)
        flash(
            'Error saving job to your sheet. Please check your connection and try again.',
            'error'
        )
        return redirect(url_for('main.job'))
