"""Password reset functionality with OTP verification."""

import random
import time
from flask import render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash
from database import get_db, get_user_by_id
from email_service import send_email_otp

# Store OTPs temporarily (in production, use Redis or similar)
OTP_STORE = {}

def forgot_password():
    """Handle forgot password requests and OTP verification."""
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
                user = get_user_by_id(user_id)
                
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
                    from database import update_password
                    update_password(user_id, password_hash)
                    del OTP_STORE[user_id]
                    return redirect(url_for('login', message='Password reset successful! Please login with your new password.'))
            else:
                error = "Session expired. Please request a new OTP."

    return render_template('forgot.html', error=error, message=message, email=email, user_id=user_id, show_otp=show_otp)
