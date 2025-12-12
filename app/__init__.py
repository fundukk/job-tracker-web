#!/usr/bin/env python3
"""
Flask application factory for job-tracker-web.
Provides a create_app() function that configures the Flask app, logging, and blueprints.
"""
import os
import logging
from flask import Flask
from dotenv import load_dotenv


def create_app():
    """
    Application factory pattern for Flask.
    
    Returns:
        Flask: Configured Flask application instance
    """
    # Load environment variables from .env file (for local development)
    load_dotenv()
    
    # Validate required OAuth environment variables at startup
    required_vars = ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        error_msg = f"FATAL: Missing required environment variables: {', '.join(missing_vars)}"
        print(f"\n{'='*80}\n{error_msg}\n{'='*80}\n")
        raise EnvironmentError(
            f"{error_msg}. "
            "Please set these in your .env file (local) or environment (production)."
        )
    
    # Log OAuth config status
    client_id_prefix = os.environ.get('GOOGLE_CLIENT_ID', '')[:20]
    test_users_count = len([e for e in os.environ.get('GOOGLE_TEST_USERS', '').split(',') if e.strip()])
    print(f"OAuth Config - Client ID prefix: {client_id_prefix}..., Test users: {test_users_count}")
    
    # Create Flask app instance
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')
    
    # Configure secret key for sessions
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
    
    # GUARD: Ensure sessions are per-user (client-side signed cookies by default in Flask)
    # Flask's default session type uses signed cookies (per-client, not shared)
    # No SESSION_TYPE override means we're using secure, per-user sessions
    app.logger.info("GUARD – Using Flask default session (client-side signed cookies, per-user)")
    app.logger.info(f"GUARD – Session configured with secret_key (first 10 chars): {app.secret_key[:10]}...")
    
    # Configure logging
    configure_logging(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    app.logger.info("Job Tracker Web app initialized successfully")
    
    return app


def configure_logging(app):
    """
    Configure structured logging for the application.
    
    Args:
        app: Flask application instance
    """
    # Set log level based on environment
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set Flask's logger to use configured level
    app.logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Reduce noise from werkzeug in production
    if not app.debug:
        logging.getLogger('werkzeug').setLevel(logging.WARNING)


def register_blueprints(app):
    """
    Register all Flask blueprints.
    
    Args:
        app: Flask application instance
    """
    from app.auth import auth_bp
    from app.routes import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)


def register_error_handlers(app):
    """
    Register centralized error handlers for common HTTP errors.
    
    Args:
        app: Flask application instance
    """
    from flask import render_template, request
    
    @app.errorhandler(400)
    def bad_request(e):
        app.logger.warning(f"Bad request: {request.method} {request.path} - {str(e)}")
        return render_template('error.html', 
                             error="Bad Request",
                             message="The request was malformed. Please try again."), 400
    
    @app.errorhandler(401)
    def unauthorized(e):
        app.logger.warning(f"Unauthorized access: {request.method} {request.path}")
        return render_template('error.html',
                             error="Unauthorized",
                             message="Please log in with Google to access this page."), 401
    
    @app.errorhandler(403)
    def forbidden(e):
        app.logger.warning(f"Forbidden access: {request.method} {request.path}")
        return render_template('error.html',
                             error="Forbidden",
                             message="You don't have permission to access this resource."), 403
    
    @app.errorhandler(404)
    def not_found(e):
        app.logger.info(f"Page not found: {request.method} {request.path}")
        return render_template('error.html',
                             error="Page Not Found",
                             message="The page you're looking for doesn't exist."), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f"Internal error: {request.method} {request.path} - {str(e)}", 
                        exc_info=True)
        return render_template('error.html',
                             error="Internal Server Error",
                             message="Something went wrong on our end. Please try again later."), 500


# Lazy initialization for production (gunicorn)
# The app is only created when this attribute is accessed
_app = None


def get_app():
    """Get or create the Flask application instance (lazy initialization)."""
    global _app
    if _app is None:
        _app = create_app()
    return _app


# For gunicorn: expose app as a module-level variable that creates on first access
# This uses a property-like pattern via __getattr__
def __getattr__(name):
    """
    Module-level __getattr__ for lazy app initialization.
    This allows 'from app import app' to work without immediate initialization.
    """
    if name == 'app':
        return get_app()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
