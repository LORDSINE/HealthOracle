from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "dev-secret-key"

USERS = {
    "patient123": "password123",
    "patient456": "password456",
}


@app.route('/', methods=['GET', 'POST'])
def home():
    error = None
    if request.method == 'POST':
        patient_id = request.form.get('patient_id', '').strip()
        password = request.form.get('password', '')

        if USERS.get(patient_id) == password:
            session['patient_id'] = patient_id
            return redirect(url_for('dashboard'))

        error = "Invalid patient ID or password."

    return render_template('index.html', error=error)


@app.route('/dashboard')
def dashboard():
    patient_id = session.get('patient_id')
    if not patient_id:
        return redirect(url_for('home'))

    return render_template('dashboard.html', patient_id=patient_id)


@app.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    error = None
    message = None
    phone = ''

    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        if phone:
            message = f"A verification code was sent to {phone}."
        else:
            error = "Please enter a valid phone number."

    return render_template('forgot.html', error=error, message=message, phone=phone)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None

    if request.method == 'POST':
        patient_id = request.form.get('patient_id', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not all([patient_id, full_name, email, password, confirm]):
            error = "All fields are required."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif password != confirm:
            error = "Passwords do not match."
        elif patient_id in USERS:
            error = "Patient ID already exists."
        else:
            USERS[patient_id] = password
            session['patient_id'] = patient_id
            return redirect(url_for('dashboard'))

    return render_template('signup.html', error=error)


@app.route('/google-link', methods=['GET', 'POST'])
def google_link():
    error = None
    email = session.get('google_email', 'user@gmail.com')

    if request.method == 'POST':
        patient_id = request.form.get('patient_id', '').strip()

        if not patient_id:
            error = "Patient ID is required."
        else:
            session['patient_id'] = patient_id
            return redirect(url_for('dashboard'))

    return render_template('google_link.html', email=email, error=error)

@app.route('/diabetes')
def diab():
    return render_template('diabetes.html')

@app.route('/heart')
def heart():
    return render_template('heart.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)