import os
import random
import smtplib
import sqlite3
import time
from email.message import EmailMessage
from werkzeug.security import generate_password_hash, check_password_hash

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

# Load environment variables from .env if present
load_dotenv()

app = Flask(__name__)
app.secret_key = "dev-secret-key"

# Database configuration
DATABASE = 'healthoracle.db'

def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with schema."""
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            patient_id TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Store OTPs temporarily (in production, use Redis or similar)
OTP_STORE = {}


def send_email_otp(recipient: str, otp: str):
    """Send OTP via SMTP; falls back to console log if SMTP config is missing."""
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("EMAIL_SENDER", "no-reply@example.com")

    if not smtp_host or not smtp_user or not smtp_password:
        print(f"[DEV ONLY] OTP for {recipient}: {otp}")
        return True, "demo"

    try:
        msg = EmailMessage()
        msg["Subject"] = "Your Health Oracle OTP"
        msg["From"] = sender
        msg["To"] = recipient
        msg.set_content(
            f"Your one-time password is {otp}. It expires in 10 minutes."
        )

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        return True, None
    except Exception as exc:  # pragma: no cover - demo fallback
        print(f"[ERROR] Failed to send OTP email: {exc}")
        return False, str(exc)


@app.route('/')
def home():
    # Redirect to login page
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        patient_id = request.form.get('patient_id', '').strip()
        password = request.form.get('password', '')

        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE patient_id = ?', (patient_id,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['patient_id'] = patient_id
            return redirect(url_for('dashboard'))

        error = "Invalid patient ID or password."

    message = request.args.get('message')
    google_client_id = os.getenv('GOOGLE_CLIENT_ID', '')
    return render_template('login.html', error=error, message=message, google_client_id=google_client_id)


@app.route('/auth/google', methods=['POST'])
def auth_google():
    credential = request.json.get('credential') if request.is_json else None
    client_id = os.getenv('GOOGLE_CLIENT_ID')

    if not credential:
        return jsonify({'error': 'Missing Google credential'}), 400
    if not client_id:
        return jsonify({'error': 'GOOGLE_CLIENT_ID not configured'}), 400

    try:
        payload = id_token.verify_oauth2_token(
            credential, google_requests.Request(), client_id
        )
        email = payload.get('email')
        if not email:
            return jsonify({'error': 'Email not found in token'}), 400

        session['google_email'] = email
        session['google_sub'] = payload.get('sub')
        return jsonify({'redirect': url_for('google_link')})
    except Exception as exc:  # pragma: no cover - verification errors
        return jsonify({'error': f'Google verification failed: {exc}'}), 400



@app.route('/dashboard')
def dashboard():
    patient_id = session.get('patient_id')
    if not patient_id:
        return redirect(url_for('login'))

    conn = get_db()
    user = conn.execute('SELECT name FROM users WHERE patient_id = ?', (patient_id,)).fetchone()
    conn.close()
    
    patient_name = user['name'] if user else patient_id
    return render_template('dashboard.html', patient_id=patient_id, patient_name=patient_name)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))



@app.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    error = None
    message = None
    email = ''
    show_otp = False

    if request.method == 'POST':
        action = request.form.get('action', 'send_otp')

        if action == 'send_otp':
            email = request.form.get('email', '').strip()
            patient_id = request.form.get('patient_id', '').strip()

            if not email or not patient_id:
                error = "Please enter both email and patient ID."
            else:
                conn = get_db()
                user = conn.execute('SELECT email FROM users WHERE patient_id = ?', (patient_id,)).fetchone()
                conn.close()
                
                if not user:
                    error = "Patient ID not found."
                elif user['email'] != email:
                    error = "Email doesn't match our records."
                else:
                    otp = str(random.randint(100000, 999999))
                    OTP_STORE[patient_id] = {
                        'otp': otp,
                        'email': email,
                        'timestamp': time.time()
                    }
                    sent, send_error = send_email_otp(email, otp)
                    if sent:
                        message = "OTP sent to your email. Please check your inbox (or spam)."
                        if send_error == "demo":
                            message += f" (Dev preview: {otp})"
                        show_otp = True
                    else:
                        error = f"Failed to send OTP: {send_error}"

        elif action == 'verify_otp':
            email = request.form.get('email', '').strip()
            patient_id = request.form.get('patient_id', '').strip()
            otp = request.form.get('otp', '').strip()
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            if patient_id in OTP_STORE:
                stored_otp = OTP_STORE[patient_id]
                if time.time() - stored_otp['timestamp'] > 600:
                    error = "OTP expired. Please request a new one."
                    del OTP_STORE[patient_id]
                elif stored_otp['otp'] != otp:
                    error = "Invalid OTP. Please try again."
                    show_otp = True
                elif stored_otp.get('email') != email:
                    error = "Email mismatch."
                    show_otp = True
                elif len(new_password) < 8:
                    error = "Password must be at least 8 characters."
                    show_otp = True
                elif new_password != confirm_password:
                    error = "Passwords do not match."
                    show_otp = True
                else:
                    # Update password in database
                    password_hash = generate_password_hash(new_password)
                    conn = get_db()
                    conn.execute('UPDATE users SET password_hash = ? WHERE patient_id = ?', (password_hash, patient_id))
                    conn.commit()
                    conn.close()
                    del OTP_STORE[patient_id]
                    return redirect(url_for('login', message='Password reset successful! Please login with your new password.'))
            else:
                error = "Session expired. Please request a new OTP."

    return render_template('forgot.html', error=error, message=message, email=email, show_otp=show_otp)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None

    if request.method == 'POST':
        patient_id = request.form.get('patient_id', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not all([patient_id, full_name, email, password, confirm]):
            error = "All fields are required."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif password != confirm:
            error = "Passwords do not match."
        else:
            conn = get_db()
            existing = conn.execute('SELECT patient_id FROM users WHERE patient_id = ?', (patient_id,)).fetchone()
            if existing:
                error = "Patient ID already exists."
                conn.close()
            else:
                password_hash = generate_password_hash(password)
                conn.execute(
                    'INSERT INTO users (patient_id, password_hash, name, email, phone) VALUES (?, ?, ?, ?, ?)',
                    (patient_id, password_hash, full_name, email, phone or None)
                )
                conn.commit()
                conn.close()
                # Redirect to login page after successful signup
                return redirect(url_for('login', message='Account created successfully! Please login.'))

    return render_template('signup.html', error=error)



@app.route('/google-link', methods=['GET', 'POST'])
def google_link():
    error = None
    email = session.get('google_email')

    if not email:
        return redirect(url_for('login', message='Please sign in with Google first.'))

    if request.method == 'POST':
        patient_id = request.form.get('patient_id', '').strip()

        if not patient_id:
            error = "Patient ID is required."
        elif patient_id not in USERS:
            error = "Patient ID not found in our database. Please sign up first."
        else:
            # Link Google account with existing patient ID
            session['patient_id'] = patient_id
            session['google_linked'] = True
            return redirect(url_for('dashboard'))

    return render_template('google_link.html', email=email, error=error)

@app.route('/dataset')
def dataset():
    patient_id = session.get('patient_id')
    if not patient_id:
        return redirect(url_for('login'))
    
    conn = get_db()
    user = conn.execute('SELECT name FROM users WHERE patient_id = ?', (patient_id,)).fetchone()
    conn.close()
    
    patient_name = user['name'] if user else patient_id
    return render_template('dataset.html', patient_id=patient_id, patient_name=patient_name)

@app.route('/prediction')
def prediction():
    patient_id = session.get('patient_id')
    if not patient_id:
        return redirect(url_for('login'))
    
    conn = get_db()
    user = conn.execute('SELECT name FROM users WHERE patient_id = ?', (patient_id,)).fetchone()
    conn.close()
    
    patient_name = user['name'] if user else patient_id
    return render_template('prediction.html', patient_id=patient_id, patient_name=patient_name)

@app.route('/diabetes')
def diab():
    return render_template('diabetes.html')

@app.route('/heart')
def heart():
    return render_template('heart.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)