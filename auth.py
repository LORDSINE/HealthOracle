"""Authentication routes and OAuth integration."""

import os
from flask import render_template, request, session, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from database import get_db, get_user_by_id, get_user_by_email, create_user, get_next_user_id

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')

def login():
    """Handle user login."""
    error = None
    
    if request.method == 'POST':
        user_id = request.form.get('user_id', '').upper()
        password = request.form.get('password', '')
        
        if not user_id or not password:
            error = 'User ID and password are required.'
        else:
            user = get_user_by_id(user_id)
            
            if not user:
                error = 'Invalid user ID or password.'
            elif not check_password_hash(user['password_hash'], password):
                error = 'Invalid user ID or password.'
            else:
                session.clear()
                session['user_id'] = user_id
                return redirect(url_for('dashboard'))
    
    message = request.args.get('message')
    google_client_id = os.getenv('GOOGLE_CLIENT_ID', '')
    return render_template('login.html', error=error, message=message, google_client_id=google_client_id)

def auth_google():
    """Handle Google OAuth authentication via JSON request."""
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
        name = payload.get('name', 'User')
        
        if not email:
            return jsonify({'error': 'Email not found in token'}), 400

        # Check if user already exists with this email
        user = get_user_by_email(email)
        
        if user:
            # User exists, log them in
            session.clear()
            session['user_id'] = user['user_id']
            session['google_linked'] = True
            return jsonify({'redirect': url_for('dashboard')})
        else:
            # New user, store in session and go to linking page
            session['google_email'] = email
            session['google_name'] = name
            session['google_sub'] = payload.get('sub')
            return jsonify({'redirect': url_for('google_link')})
    
    except Exception as exc:
        return jsonify({'error': f'Google verification failed: {str(exc)}'}), 400

def signup():
    """Handle user registration."""
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
                valid_phone = len(digits_only) == 10 and (digits_only.startswith('97') or digits_only.startswith('98'))
                if not valid_phone:
                    error = "Please enter a valid number."
            else:
                valid_phone = len(digits_only) >= 10
                if not valid_phone:
                    error = "Please enter a valid phone number (at least 10 digits)."
        
        if not error:
            # Check if email already exists
            existing = get_user_by_email(email)
            if existing:
                error = "Email already exists. Please use a different email or login."
            else:
                user_id = get_next_user_id()
                password_hash = generate_password_hash(password)
                # Format phone with country code
                full_phone = f"{country_code} {phone}" if phone else None
                
                try:
                    create_user(user_id, password_hash, full_name, email, full_phone)
                    # Redirect to success page showing the user_id
                    return redirect(url_for('signup_success', user_id=user_id))
                except Exception as e:
                    error = f"Error creating account: {str(e)}"

    google_client_id = os.getenv('GOOGLE_CLIENT_ID', '')
    return render_template('signup.html', error=error, google_client_id=google_client_id, form_data=form_data)

def signup_success(user_id):
    """Show success message with generated user_id for signup."""
    user = get_user_by_id(user_id)
    
    if not user:
        return redirect(url_for('signup'))
    
    return render_template('signup_success.html', user_id=user_id, email=user['email'], name=user['name'])

def google_link():
    """Link Google account to existing user or create new account."""
    error = None
    email = session.get('google_email')
    name = session.get('google_name', 'User')
    
    if not email:
        return redirect(url_for('login', message='Please sign in with Google first.'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        country_code = request.form.get('country_code', '+977').strip()

        if not full_name:
            error = "Full name is required."
        else:
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
            # Check if email already has an account
            existing_user = get_user_by_email(email)
            
            if existing_user:
                # If account exists, just link it
                user_id = existing_user['user_id']
                session['user_id'] = user_id
                session['google_linked'] = True
                # Clean up Google session vars
                session.pop('google_email', None)
                session.pop('google_name', None)
                session.pop('google_sub', None)
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
                    create_user(user_id, password_hash, full_name, email, full_phone)
                    session['user_id'] = user_id
                    session['google_linked'] = True
                    # Clean up Google session vars
                    session.pop('google_email', None)
                    session.pop('google_name', None)
                    session.pop('google_sub', None)
                    return redirect(url_for('dashboard'))
                except Exception as e:
                    error = f"Error creating account: {str(e)}"

    return render_template('google_link.html', email=email, name=name, error=error)

def google_success(user_id):
    """Show success message with generated user_id for Google signup."""
    email = session.get('google_email')
    if not email:
        return redirect(url_for('login'))
    
    return render_template('google_success.html', user_id=user_id, email=email)
