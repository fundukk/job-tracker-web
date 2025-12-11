#!/usr/bin/env python3
"""
Job Tracker Web Application
Entry point for the Flask application using factory pattern.
"""
from app import create_app

# Create the Flask application instance
app = create_app()

if __name__ == '__main__':
    # Run in development mode
    app.run(debug=True)
