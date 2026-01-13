from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import os

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

@app.route('/datasets')
def datasets():
    patient_id = session.get('patient_id')
    if not patient_id:
        return redirect(url_for('home'))
    
    return render_template('datasets.html', patient_id=patient_id)

@app.route('/dataset/<dataset_name>')
def dataset_overview(dataset_name):
    patient_id = session.get('patient_id')
    if not patient_id:
        return redirect(url_for('home'))
    
    data_path = os.path.join(os.path.dirname(__file__), 'data')
    
    if dataset_name == 'diabetes':
        file_path = os.path.join(data_path, 'Diabetes_data.csv')
        title = "Diabetes Dataset"
        description = "Comprehensive health data for diabetes prediction and analysis."
    elif dataset_name == 'heart':
        file_path = os.path.join(data_path, 'heart_data.csv')
        title = "Heart Disease Dataset"
        description = "Clinical data for heart disease prediction and analysis."
    else:
        return redirect(url_for('datasets'))
    
    try:
        df = pd.read_csv(file_path)
        
        # Get dataset statistics
        stats = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'memory_usage': f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB",
        }
        
        # Get column information
        columns_info = []
        for col in df.columns:
            columns_info.append({
                'name': col,
                'dtype': str(df[col].dtype),
                'non_null': df[col].count(),
                'null': df[col].isnull().sum(),
                'unique': df[col].nunique()
            })
        
        # Get first few rows for preview
        preview_data = df.head(10).to_dict('records')
        
        return render_template('dataset_overview.html', 
                             patient_id=patient_id,
                             title=title,
                             description=description,
                             stats=stats,
                             columns=columns_info,
                             preview=preview_data,
                             dataset_name=dataset_name)
    except Exception as e:
        return render_template('dataset_overview.html', 
                             error=f"Error loading dataset: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True, port=5000)