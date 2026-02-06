import os
from flask import Flask, redirect, url_for, render_template, abort
from dotenv import load_dotenv
from database import init_db
from auth import login, auth_google, signup, google_link, google_success, signup_success
from user_routes import (
    dashboard, profile, dataset, dataset_preview, dataset_download, prediction, logout, eda, predict_health_risk, modeling,
    eda_overview, eda_target, eda_numerical, eda_categorical, eda_correlation, eda_risk, eda_stats, eda_interactions, eda_model_evaluation
)
from password_reset import forgot_password

load_dotenv()

app = Flask(__name__)
app.secret_key = "dev-secret-key"

init_db()


@app.route('/')
def home():
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
app.add_url_rule('/profile', 'profile', profile)
app.add_url_rule('/dataset', 'dataset', dataset)
app.add_url_rule('/api/dataset/preview', 'dataset_preview', dataset_preview)
app.add_url_rule('/api/dataset/download', 'dataset_download', dataset_download)
app.add_url_rule('/eda', 'eda', eda)
app.add_url_rule('/modeling', 'modeling', modeling)
app.add_url_rule('/prediction', 'prediction', prediction)
app.add_url_rule('/api/predict', 'predict_health_risk', predict_health_risk, methods=['POST'])
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
app.add_url_rule('/api/eda/model-evaluation', 'eda_model_evaluation', eda_model_evaluation)

# Error route for model not implemented
@app.route('/error/503')
def trigger_503():
    from flask import abort
    abort(503)

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(400)
def bad_request(e):
    return render_template('errors/400.html'), 400

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

@app.errorhandler(503)
def service_unavailable(e):
    return render_template('errors/503.html'), 503



if __name__ == '__main__':
    app.run(debug=True, port=5000)
