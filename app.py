import os
from flask import Flask, redirect, url_for, render_template
from dotenv import load_dotenv
from database import init_db
from auth import login, auth_google, signup, google_link, google_success, signup_success
from user_routes import dashboard, profile, dataset, prediction, logout
from password_reset import forgot_password

load_dotenv()

app = Flask(__name__)
app.secret_key = "dev-secret-key"

init_db()


@app.route('/')
def home():
    """Redirect to login page."""
    return redirect(url_for('login'))

# auth routes
app.add_url_rule('/login', 'login', login, methods=['GET', 'POST'])
app.add_url_rule('/auth/google', 'auth_google', auth_google, methods=['POST'])
app.add_url_rule('/signup', 'signup', signup, methods=['GET', 'POST'])
app.add_url_rule('/signup-success/<user_id>', 'signup_success', signup_success)
app.add_url_rule('/google-link', 'google_link', google_link, methods=['GET', 'POST'])
app.add_url_rule('/google-success/<user_id>', 'google_success', google_success)
app.add_url_rule('/forgot', 'forgot_password', forgot_password, methods=['GET', 'POST'])

# user routes
app.add_url_rule('/dashboard', 'dashboard', dashboard)
app.add_url_rule('/profile', 'profile', profile, methods=['GET', 'POST'])
app.add_url_rule('/dataset', 'dataset', dataset)
app.add_url_rule('/prediction', 'prediction', prediction)
app.add_url_rule('/logout', 'logout', logout)


# error handlers
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



if __name__ == '__main__':
    app.run(debug=False, port=5000)
