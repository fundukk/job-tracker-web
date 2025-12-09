#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from core.sheets import get_worksheet, append_job_row, extract_spreadsheet_id
from core.jobs import process_job_url

app = Flask(__name__)
app.secret_key = "CHANGE_THIS_SECRET"  # Change this to a random secret key in production


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


@app.route('/job')
def job():
    """Step 2: Ask user for job URL."""
    if 'sheet_url' not in session:
        flash('Please set your Google Sheet first', 'warning')
        return redirect(url_for('index'))
    
    return render_template('job.html')


@app.route('/add_job', methods=['POST'])
def add_job():
    """Process job URL and add to sheet."""
    if 'sheet_url' not in session:
        flash('Please set your Google Sheet first', 'warning')
        return redirect(url_for('index'))
    
    job_url = request.form.get('job_url', '').strip()
    
    if not job_url:
        flash('Please provide a job URL', 'error')
        return redirect(url_for('job'))
    
    try:
        # Get the worksheet
        sheet_id = session['sheet_url']
        ws = get_worksheet(sheet_id)
        
        # Process the job URL
        job_data = process_job_url(job_url)
        
        # Add to sheet
        append_job_row(ws, job_data)
        
        return render_template('success.html', job_data=job_data)
    
    except Exception as e:
        flash(f'Error processing job: {str(e)}', 'error')
        return redirect(url_for('job'))


if __name__ == '__main__':
    app.run(debug=True)
