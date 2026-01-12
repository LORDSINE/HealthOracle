# 🏥 Health Oracle

A Flask-based health monitoring web application with secure authentication, email OTP verification, and Google Sign-In integration.

## 📋 Features

- **User Authentication**: Secure login/signup system with password hashing
- **Email OTP Verification**: Password reset via email OTP
- **Google Sign-In**: OAuth 2.0 integration for seamless login
- **SQLite Database**: Persistent user data storage
- **Responsive UI**: Clean and modern user interface

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Gmail account (for sending OTP emails)
- Google Cloud Project (for Google Sign-In)

### Installation

1. **Clone the repository**
   \`\`\`bash
   git clone https://github.com/LORDSINE/HealthOracle.git
   cd HealthOracle
   \`\`\`

2. **Create virtual environment**
   \`\`\`bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   \`\`\`

3. **Install dependencies**
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

4. **Configure environment variables** (see Configuration section below)

5. **Run the application**
   \`\`\`bash
   python app.py
   \`\`\`

6. **Access the app**
   - Open browser and go to: \`http://localhost:5000\`

---

## ⚙️ Configuration

### Setting up \`.env\` file

Create a \`.env\` file in the root directory with the following variables:

\`\`\`env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com

# SMTP Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_SENDER=your-email@gmail.com
\`\`\`

### 📧 Email OTP Setup (Gmail)

The application uses Gmail's SMTP server to send OTP emails for password reset functionality.

#### Step-by-step Guide:

1. **Enable 2-Step Verification**
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Find "How you sign in to Google"
   - Click on "2-Step Verification" and follow the setup

2. **Generate App Password**
   - In the same Security page, scroll to "2-Step Verification"
   - Scroll down to "App passwords" at the bottom
   - Click "App passwords"
   - Select app: **Mail**
   - Select device: **Other (Custom name)** → Enter "HealthOracle"
   - Click **Generate**
   - Copy the 16-character password (format: \`xxxx xxxx xxxx xxxx\`)

3. **Update \`.env\` file**
   \`\`\`env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx  # The app password from step 2
   EMAIL_SENDER=your-email@gmail.com
   \`\`\`

4. **How it works**
   - User enters email and patient ID on forgot password page
   - System verifies the email matches the patient ID in database
   - 6-digit OTP is generated and sent to the user's email
   - OTP is valid for 10 minutes
   - User enters OTP to reset password

#### Testing Email OTP:
\`\`\`bash
# Start the Flask app
python app.py

# Navigate to: http://localhost:5000/forgot
# Enter registered email and patient ID
# Check your email inbox for the OTP
\`\`\`

---

### 🔐 Google Sign-In Setup

The application uses Google OAuth 2.0 for secure sign-in functionality.

#### Step-by-step Guide:

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Click "Select a project" → "New Project"
   - Enter project name: "HealthOracle"
   - Click "Create"

2. **Enable Google+ API**
   - In the left menu: **APIs & Services** → **Library**
   - Search for "Google+ API"
   - Click on it and press "Enable"

3. **Configure OAuth Consent Screen**
   - Go to **APIs & Services** → **OAuth consent screen**
   - Select "External" user type → Click "Create"
   - Fill in:
     - App name: \`Health Oracle\`
     - User support email: Your email
     - Developer contact: Your email
   - Click "Save and Continue"
   - Skip "Scopes" → Click "Save and Continue"
   - Add test users (your Gmail) → Click "Save and Continue"

4. **Create OAuth 2.0 Credentials**
   - Go to **APIs & Services** → **Credentials**
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: **Web application**
   - Name: "HealthOracle Web Client"
   - Authorized JavaScript origins:
     - \`http://localhost:5000\`
     - \`http://127.0.0.1:5000\`
   - Authorized redirect URIs:
     - \`http://localhost:5000/auth/google\`
   - Click "Create"
   - Copy the **Client ID**

5. **Update \`.env\` file**
   \`\`\`env
   GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
   \`\`\`

6. **How it works**
   - User clicks "Sign in with Google" button on login page
   - Google's authentication popup appears
   - User selects their Google account
   - Google verifies and sends credential token to our app
   - App validates the token and creates/logs in the user
   - User is redirected to the dashboard

#### Testing Google Sign-In:
\`\`\`bash
# Start the Flask app
python app.py

# Navigate to: http://localhost:5000/login
# Click "Sign in with Google" button
# Select your Google account
# You should be logged in and redirected to dashboard
\`\`\`

---

## 🗄️ Database

The application uses **SQLite** for data persistence.

### Database Schema

**Users Table:**
\`\`\`sql
CREATE TABLE users (
    patient_id TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT
);
\`\`\`

### View Database Contents

Run the provided script to view all registered users:
\`\`\`bash
python view_db.py
\`\`\`

Output example:
\`\`\`
📊 HEALTH ORACLE - USER DATABASE
+--------------+--------------+--------------------------+------------+
| Patient ID   | Name         | Email                    | Phone      |
+==============+==============+==========================+============+
| P12345       | John Doe     | john@example.com         | 1234567890 |
+--------------+--------------+--------------------------+------------+
Total Users: 1
\`\`\`

---

## 📁 Project Structure

\`\`\`
HealthOracle/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in git)
├── .gitignore             # Git ignore rules
├── view_db.py             # Database viewer script
├── healthoracle.db        # SQLite database (not in git)
├── data/                  # Dataset files
│   ├── Diabetes_data.csv
│   └── heart_data.csv
├── static/
│   └── style.css          # CSS styles
└── templates/             # HTML templates
    ├── base.html
    ├── login.html
    ├── signup.html
    ├── forgot.html
    ├── dashboard.html
    └── google_link.html
\`\`\`

---

## 🔒 Security Features

1. **Password Hashing**: Uses Werkzeug's \`generate_password_hash\` (PBKDF2-SHA256)
2. **Session Management**: Flask sessions with secret key
3. **OTP Expiration**: OTPs expire after 10 minutes
4. **Environment Variables**: Sensitive data in \`.env\` (not committed to git)
5. **Google OAuth**: Secure token validation

---

## 🐛 Troubleshooting

### Email OTP Not Working

**Problem**: OTP emails not being received

**Solutions**:
1. Check spam/junk folder
2. Verify Gmail app password is correct
3. Ensure 2-Step Verification is enabled
4. Check \`.env\` file has correct SMTP settings
5. Test SMTP connection:
   \`\`\`python
   python -c "import smtplib; s=smtplib.SMTP('smtp.gmail.com',587); s.starttls(); print('Connection OK')"
   \`\`\`

### Google Sign-In Not Working

**Problem**: "Error 400: redirect_uri_mismatch"

**Solutions**:
1. Verify redirect URI in Google Cloud Console matches exactly:
   - \`http://localhost:5000/auth/google\`
2. Check JavaScript origins include:
   - \`http://localhost:5000\`
3. Clear browser cache and cookies
4. Ensure \`GOOGLE_CLIENT_ID\` in \`.env\` matches the one from Google Cloud Console

### Database Issues

**Problem**: Users not persisting after restart

**Solutions**:
1. Check \`healthoracle.db\` file exists
2. Verify database permissions (read/write)
3. Delete database and restart app to recreate:
   \`\`\`bash
   rm healthoracle.db
   python app.py
   \`\`\`

---

## 👥 Contributors

- **Team Members**: LORDSINE Organization
- **Project**: 5th Semester Project

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Flask Framework
- Google OAuth 2.0
- Gmail SMTP Service
- SQLite Database

---

## 📞 Support

For issues or questions, please open an issue on GitHub or contact the development team.

**Happy Coding! 🚀**
