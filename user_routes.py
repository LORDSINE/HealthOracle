"""User routes and dashboard functionality."""

from flask import render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db, get_user_by_id, update_password
from eda_analysis import (
    get_dataset_overview,
    analyze_target_distribution,
    analyze_numerical_features,
    analyze_categorical_features,
    analyze_correlations,
    analyze_risk_factors,
    analyze_statistical_tests,
    analyze_feature_interactions
)

def dashboard():
    """Dashboard page showing user information and project overview."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    if not user:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', user_name=user['name'], user_id=user['user_id'])

def profile():
    """User profile page with personal information and password change."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    if not user:
        return redirect(url_for('login'))
    
    password_error = None
    password_success = None
    
    if request.method == 'POST':
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not all([current_password, new_password, confirm_password]):
            password_error = 'All fields are required'
        elif new_password != confirm_password:
            password_error = 'New passwords do not match'
        elif len(new_password) < 8:
            password_error = 'Password must be at least 8 characters long'
        elif not check_password_hash(user['password_hash'], current_password):
            password_error = 'Current password is incorrect'
        else:
            # Update password
            password_hash = generate_password_hash(new_password)
            update_password(session['user_id'], password_hash)
            password_success = 'Password updated successfully!'
    
    return render_template(
        'profile.html',
        user_name=user['name'],
        user_id=user['user_id'],
        email=user['email'],
        password_error=password_error,
        password_success=password_success
    )

def dataset():
    """Dataset page showing available datasets and features."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    if not user:
        return redirect(url_for('login'))
    
    return render_template('dataset.html', user_name=user['name'], user_id=user['user_id'])

def prediction():
    """Health prediction page."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    if not user:
        return redirect(url_for('login'))
    
    return render_template('prediction.html', user_name=user['name'], user_id=user['user_id'])

def eda():
    """Exploratory Data Analysis page."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    if not user:
        return redirect(url_for('login'))
    
    return render_template('eda.html', user_name=user['name'], user_id=user['user_id'])

def eda_overview():
    """API endpoint for dataset overview."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = get_dataset_overview()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def eda_target():
    """API endpoint for target distribution analysis."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = analyze_target_distribution()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def eda_numerical():
    """API endpoint for numerical features analysis."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = analyze_numerical_features()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def eda_categorical():
    """API endpoint for categorical features analysis."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = analyze_categorical_features()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def eda_correlation():
    """API endpoint for correlation analysis."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = analyze_correlations()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def eda_risk():
    """API endpoint for risk factor analysis."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = analyze_risk_factors()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def eda_stats():
    """API endpoint for statistical tests."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = analyze_statistical_tests()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def eda_interactions():
    """API endpoint for feature interaction analysis."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = analyze_feature_interactions()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def logout():
    """Log out the user by clearing the session."""
    session.clear()
    return redirect(url_for('login'))
