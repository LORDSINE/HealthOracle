"""Health Oracle Flask Application - Modular Structure

This is the main Flask application entry point. All business logic has been
organized into modular components for better maintainability.

Modules:
- database.py: Database operations and user management
- email_service.py: Email sending functionality (OTP delivery)
- auth.py: Authentication routes (login, signup, Google OAuth)
- user_routes.py: User management routes (dashboard, profile, prediction, etc.)
- password_reset.py: Password reset functionality with OTP verification
"""

import os
from flask import Flask, redirect, url_for, render_template
from dotenv import load_dotenv

# Import all route functions from modular files
from database import init_db
from auth import login, auth_google, signup, google_link, google_success, signup_success
from user_routes import (dashboard, profile, dataset, prediction, eda, logout,
                         eda_overview, eda_target, eda_numerical, eda_categorical,
                         eda_correlation, eda_risk, eda_stats, eda_interactions)
from password_reset import forgot_password

# Load environment variables from .env if present
load_dotenv()

# Initialize Flask application
app = Flask(__name__)
app.secret_key = "dev-secret-key"

# Initialize database on startup
init_db()

# ============================================================================
# HOME ROUTE
# ============================================================================

@app.route('/')
def home():
    """Redirect to login page."""
    return redirect(url_for('login'))

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

app.add_url_rule('/login', 'login', login, methods=['GET', 'POST'])
app.add_url_rule('/auth/google', 'auth_google', auth_google, methods=['POST'])
app.add_url_rule('/signup', 'signup', signup, methods=['GET', 'POST'])
app.add_url_rule('/signup-success/<user_id>', 'signup_success', signup_success)
app.add_url_rule('/google-link', 'google_link', google_link, methods=['GET', 'POST'])
app.add_url_rule('/google-success/<user_id>', 'google_success', google_success)
app.add_url_rule('/forgot', 'forgot_password', forgot_password, methods=['GET', 'POST'])

# ============================================================================
# USER ROUTES
# ============================================================================

app.add_url_rule('/dashboard', 'dashboard', dashboard)
app.add_url_rule('/profile', 'profile', profile, methods=['GET', 'POST'])
app.add_url_rule('/dataset', 'dataset', dataset)
app.add_url_rule('/eda', 'eda', eda)
app.add_url_rule('/prediction', 'prediction', prediction)
app.add_url_rule('/logout', 'logout', logout)

# EDA API Endpoints
app.add_url_rule('/api/eda/overview', 'eda_overview', eda_overview)
app.add_url_rule('/api/eda/target', 'eda_target', eda_target)
app.add_url_rule('/api/eda/numerical', 'eda_numerical', eda_numerical)
app.add_url_rule('/api/eda/categorical', 'eda_categorical', eda_categorical)
app.add_url_rule('/api/eda/correlation', 'eda_correlation', eda_correlation)
app.add_url_rule('/api/eda/risk', 'eda_risk', eda_risk)
app.add_url_rule('/api/eda/stats', 'eda_stats', eda_stats)
app.add_url_rule('/api/eda/interactions', 'eda_interactions', eda_interactions)

# Error route for model not implemented
@app.route('/error/503')
def trigger_503():
    """Trigger 503 error for model not implemented."""
    from flask import abort
    abort(503)

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors - Page Not Found."""
    return render_template('errors/404.html'), 404

@app.errorhandler(400)
def bad_request(e):
    """Handle 400 errors - Bad Request."""
    return render_template('errors/400.html'), 400

@app.errorhandler(403)
def forbidden(e):
    """Handle 403 errors - Forbidden."""
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors - Internal Server Error."""
    return render_template('errors/500.html'), 500

@app.errorhandler(503)
def service_unavailable(e):
    """Handle 503 errors - Service Unavailable."""
    return render_template('errors/503.html'), 503

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    app.run(debug=True, port=5000)
