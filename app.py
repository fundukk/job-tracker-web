#!/usr/bin/env python3
"""
Job Tracker Web Application
Entry point for local development with Flask's built-in server.
For production, gunicorn imports directly from: app:app
"""
from app import app

if __name__ == '__main__':
    # Run in development mode
    app.run(debug=True)
