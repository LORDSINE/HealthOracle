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
    
    # Check if we need to migrate from patient_id to user_id
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        # Check if the table has patient_id column (old schema)
        cursor = conn.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'patient_id' in columns and 'user_id' not in columns:
            # Migrate from patient_id to user_id
            print("Migrating database schema from patient_id to user_id...")
            conn.execute('ALTER TABLE users RENAME COLUMN patient_id TO user_id')
            conn.commit()
    else:
        # Create new table with user_id
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT
            )
        ''')
        conn.commit()
    
    conn.close()

def get_next_user_id():
    """Generate next user_id in sequence P0001, P0002, etc."""
    conn = get_db()
    cursor = conn.execute('SELECT MAX(CAST(SUBSTR(user_id, 2) AS INTEGER)) as max_id FROM users WHERE user_id LIKE "P%"')
    result = cursor.fetchone()
    conn.close()
    
    max_id = result['max_id'] if result and result['max_id'] else 0
    next_id = max_id + 1
    return f"P{next_id:04d}"

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
        user_id = request.form.get('user_id', '').strip()
        password = request.form.get('password', '')

        # Frontend validation on backend
        if not user_id or not password:
            error = "User ID and password are required."
        else:
            conn = get_db()
            user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
            conn.close()

            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user_id
                return redirect(url_for('dashboard'))
            else:
                error = "Invalid user ID or password."

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

        # Check if user already exists with this email
        conn = get_db()
        user = conn.execute('SELECT user_id FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        # Check where the request is coming from (login or signup page)
        is_signup = request.referrer and 'signup' in request.referrer
        
        if user:
            # User exists - login directly to dashboard
            session['user_id'] = user['user_id']
            session['google_linked'] = True
            return jsonify({'redirect': url_for('dashboard')})
        else:
            # No existing account
            if is_signup:
                # Coming from signup page - go to google_link to create account
                session['google_email'] = email
                session['google_sub'] = payload.get('sub')
                return jsonify({'redirect': url_for('google_link')})
            else:
                # Coming from login page - reject (must signup first)
                return jsonify({'error': 'No account found with this email. Please sign up first.'}), 400
    except Exception as exc:  # pragma: no cover - verification errors
        return jsonify({'error': f'Google verification failed: {exc}'}), 400



@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    conn = get_db()
    user = conn.execute('SELECT name FROM users WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    
    user_name = user['name'] if user else user_id
    return render_template('dashboard.html', user_id=user_id, user_name=user_name)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))



@app.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    error = None
    message = None
    email = ''
    user_id = ''
    show_otp = False

    if request.method == 'POST':
        action = request.form.get('action', 'send_otp')

        if action == 'send_otp':
            email = request.form.get('email', '').strip()
            user_id = request.form.get('user_id', '').strip()

            if not email or not user_id:
                error = "Please enter both email and user ID."
            else:
                conn = get_db()
                user = conn.execute('SELECT email FROM users WHERE user_id = ?', (user_id,)).fetchone()
                conn.close()
                
                if not user:
                    error = "User ID not found."
                elif user['email'] != email:
                    error = "Email doesn't match our records."
                else:
                    otp = str(random.randint(100000, 999999))
                    OTP_STORE[user_id] = {
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
            user_id = request.form.get('user_id', '').strip()
            otp = request.form.get('otp', '').strip()
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            if not otp or not new_password or not confirm_password:
                error = "All fields are required."
                show_otp = True
            elif len(new_password) < 8:
                error = "Password must be at least 8 characters."
                show_otp = True
            elif new_password != confirm_password:
                error = "Passwords do not match."
                show_otp = True
            elif user_id in OTP_STORE:
                stored_otp = OTP_STORE[user_id]
                if time.time() - stored_otp['timestamp'] > 600:
                    error = "OTP expired. Please request a new one."
                    del OTP_STORE[user_id]
                elif stored_otp['otp'] != otp:
                    error = "Invalid OTP. Please try again."
                    show_otp = True
                elif stored_otp.get('email') != email:
                    error = "Email mismatch."
                    show_otp = True
                else:
                    # Update password in database
                    password_hash = generate_password_hash(new_password)
                    conn = get_db()
                    conn.execute('UPDATE users SET password_hash = ? WHERE user_id = ?', (password_hash, user_id))
                    conn.commit()
                    conn.close()
                    del OTP_STORE[user_id]
                    return redirect(url_for('login', message='Password reset successful! Please login with your new password.'))
            else:
                error = "Session expired. Please request a new OTP."

    return render_template('forgot.html', error=error, message=message, email=email, user_id=user_id, show_otp=show_otp)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    form_data = {
        'full_name': '',
        'email': '',
        'phone': '',
        'country_code': '+977'
    }

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        country_code = request.form.get('country_code', '+977').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        # Store form data to repopulate on error
        form_data = {
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'country_code': country_code
        }

        # Validation
        if not full_name:
            error = "Full name is required."
        elif not email or '@' not in email:
            error = "Please enter a valid email address."
        elif not password:
            error = "Password is required."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif not confirm:
            error = "Please confirm your password."
        elif password != confirm:
            error = "Passwords do not match."
        elif phone:
            # Phone validation based on country code (only if provided)
            digits_only = ''.join(filter(str.isdigit, phone))
            valid_phone = False
            
            if country_code == '+977':
                # Nepal: must be 10 digits starting with 97 or 98
                valid_phone = len(digits_only) == 10 and (digits_only.startswith('97') or digits_only.startswith('98'))
                if not valid_phone:
                    error = "Please enter a valid number."
            else:
                # Other countries: basic 10+ digit validation
                valid_phone = len(digits_only) >= 10
                if not valid_phone:
                    error = "Please enter a valid phone number (at least 10 digits)."
        
        if not error:
            # Generate user_id and check if email already exists
            conn = get_db()
            existing = conn.execute('SELECT user_id FROM users WHERE email = ?', (email,)).fetchone()
            if existing:
                error = "Email already exists. Please use a different email or login."
                conn.close()
            else:
                user_id = get_next_user_id()
                password_hash = generate_password_hash(password)
                # Format phone with country code
                full_phone = f"{country_code} {phone}" if phone else None
                try:
                    conn.execute(
                        'INSERT INTO users (user_id, password_hash, name, email, phone) VALUES (?, ?, ?, ?, ?)',
                        (user_id, password_hash, full_name, email, full_phone)
                    )
                    conn.commit()
                    conn.close()
                    # Redirect to success page showing the user_id
                    return redirect(url_for('signup_success', user_id=user_id))
                except Exception as e:
                    error = f"Error creating account: {str(e)}"
                    conn.close()

    google_client_id = os.getenv('GOOGLE_CLIENT_ID', '')
    return render_template('signup.html', error=error, google_client_id=google_client_id, form_data=form_data)


@app.route('/signup-success/<user_id>')
def signup_success(user_id):
    """Show success message with generated user_id for signup"""
    conn = get_db()
    user = conn.execute('SELECT email, name FROM users WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    
    if not user:
        return redirect(url_for('signup'))
    
    return render_template('signup_success.html', user_id=user_id, email=user['email'], name=user['name'])



@app.route('/google-link', methods=['GET', 'POST'])
def google_link():
    error = None
    email = session.get('google_email')
    user_id = None
    new_account = False

    if not email:
        return redirect(url_for('login', message='Please sign in with Google first.'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        country_code = request.form.get('country_code', '+977').strip()

        if not full_name:
            error = "Full name is required."
        else:
            # Check if email already exists (safety check)
            conn = get_db()
            existing = conn.execute('SELECT user_id FROM users WHERE email = ?', (email,)).fetchone()
            if existing:
                conn.close()
                error = "This email is already registered. Please use the login page."
            else:
                conn.close()
                # Validate phone if provided
                if phone:
                    digits_only = ''.join(filter(str.isdigit, phone))
                    valid_phone = False
                    
                    if country_code == '+977':
                        # Nepal: must be 10 digits starting with 97 or 98
                        valid_phone = len(digits_only) == 10 and (digits_only.startswith('97') or digits_only.startswith('98'))
                        if not valid_phone:
                            error = "Please enter a valid number."
                    else:
                        # Other countries: basic 10+ digit validation
                        valid_phone = len(digits_only) >= 10
                        if not valid_phone:
                            error = "Please enter a valid phone number (at least 10 digits)."
        
        if not error:
            # Generate user_id for new Google account
            conn = get_db()
            existing = conn.execute('SELECT user_id FROM users WHERE email = ?', (email,)).fetchone()
            
            if existing:
                # If account exists, just link it
                user_id = existing['user_id']
                session['user_id'] = user_id
                session['google_linked'] = True
                conn.close()
                return redirect(url_for('dashboard'))
            else:
                # Create new account for Google user
                user_id = get_next_user_id()
                # Generate a random password for Google users (they won't need it)
                temp_password = os.urandom(16).hex()
                password_hash = generate_password_hash(temp_password)
                # Format phone with country code
                full_phone = f"{country_code} {phone}" if phone else None
                
                try:
                    conn.execute(
                        'INSERT INTO users (user_id, password_hash, name, email, phone) VALUES (?, ?, ?, ?, ?)',
                        (user_id, password_hash, full_name, email, full_phone)
                    )
                    conn.commit()
                    session['user_id'] = user_id
                    session['google_linked'] = True
                    conn.close()
                    # Redirect to dashboard
                    return redirect(url_for('dashboard'))
                except Exception as e:
                    error = f"Error creating account: {str(e)}"
                    conn.close()

    return render_template('google_link.html', email=email, error=error)


@app.route('/google-success/<user_id>')
def google_success(user_id):
    """Show success message with generated user_id for Google signup"""
    email = session.get('google_email')
    if not email:
        return redirect(url_for('login'))
    
    return render_template('google_success.html', user_id=user_id, email=email)

@app.route('/dataset')
def dataset():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    conn = get_db()
    user = conn.execute('SELECT name FROM users WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    
    user_name = user['name'] if user else user_id
    return render_template('dataset.html', user_id=user_id, user_name=user_name)

@app.route('/prediction')
def prediction():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    conn = get_db()
    user = conn.execute('SELECT name FROM users WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    
    user_name = user['name'] if user else user_id
    return render_template('prediction.html', user_id=user_id, user_name=user_name)

@app.route('/diabetes')
def diab():
    return render_template('diabetes.html')

@app.route('/heart')
def heart():
    return render_template('heart.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)