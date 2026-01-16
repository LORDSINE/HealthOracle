"""Email service for sending OTPs and notifications."""

import os
import smtplib
from email.message import EmailMessage

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
    except Exception as exc:
        print(f"[ERROR] Failed to send OTP email: {exc}")
        return False, str(exc)
