#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash
from core.sheets import get_worksheet, append_job_row, replace_job_by_link, replace_last_job, extract_spreadsheet_id
from core.jobs import process_job_url, validate_job_url
from core.salary import normalize_salary

# Load environment variables from .env file (for local development)
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')


@app.route('/')
def index():
    """Step 1: Ask user for Google Sheet link."""
    return render_template('index.html')


@app.route('/set_sheet', methods=['POST'])
def set_sheet():
    """Validate and store the Google Sheet link."""
    sheet_url = request.form.get('sheet_url', '').strip()
    
    if not sheet_url:
        flash('Please provide a Google Sheet URL or ID', 'error')
        return redirect(url_for('index'))
    
    try:
        # Validate that we can access the sheet
        sheet_id = extract_spreadsheet_id(sheet_url)
        ws = get_worksheet(sheet_id)
        
        # Store in session
        session['sheet_url'] = sheet_id
        flash('Sheet connected successfully!', 'success')
        return redirect(url_for('job'))
    
    except Exception as e:
        flash(f'Error connecting to sheet: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/job', methods=['GET', 'POST'])
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
        
        # Get the worksheet
        sheet_id = session['sheet_url']
        ws = get_worksheet(sheet_id)
        
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
        
        return render_template('success.html', job_data=job_data)
    
    except Exception as e:
        flash(f'Error saving job: {str(e)}', 'error')
        return redirect(url_for('job'))


if __name__ == '__main__':
    app.run(debug=True)
