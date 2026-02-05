from flask import render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db, get_user_by_id, update_password, save_prediction, get_user_predictions
from eda_analysis import (
    get_dataset_overview,
    analyze_target_distribution,
    analyze_numerical_features,
    analyze_categorical_features,
    analyze_correlations,
    analyze_risk_factors,
    analyze_statistical_tests,
    analyze_feature_interactions,
    evaluate_models
)

def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    if not user:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', user_name=user['name'], user_id=user['user_id'])

def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    if not user:
        return redirect(url_for('login'))
    
    # Get prediction history
    predictions = get_user_predictions(session['user_id'])
    
    return render_template(
        'profile.html',
        user_name=user['name'],
        user_id=user['user_id'],
        user_email=user['email'],
        predictions=predictions
    )

def dataset():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    if not user:
        return redirect(url_for('login'))
    
    return render_template('dataset.html', user_name=user['name'], user_id=user['user_id'])

def prediction():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    if not user:
        return redirect(url_for('login'))
    
    return render_template('prediction.html', user_name=user['name'], user_id=user['user_id'])

def eda():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    if not user:
        return redirect(url_for('login'))
    
    return render_template('eda.html', user_name=user['name'], user_id=user['user_id'])

def modeling():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    if not user:
        return redirect(url_for('login'))
    
    return render_template('modeling.html', user_name=user['name'], user_id=user['user_id'])

def eda_overview():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = get_dataset_overview()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def eda_target():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = analyze_target_distribution()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def eda_numerical():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = analyze_numerical_features()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def eda_categorical():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = analyze_categorical_features()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def eda_correlation():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = analyze_correlations()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def eda_risk():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = analyze_risk_factors()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def eda_stats():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = analyze_statistical_tests()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def eda_interactions():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = analyze_feature_interactions()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def eda_model_evaluation():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = evaluate_models()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def age_to_category(age):
    age = int(age)
    if age < 18:
        return 1
    elif age <= 24:
        return 1
    elif age <= 29:
        return 2
    elif age <= 34:
        return 3
    elif age <= 39:
        return 4
    elif age <= 44:
        return 5
    elif age <= 49:
        return 6
    elif age <= 54:
        return 7
    elif age <= 59:
        return 8
    elif age <= 64:
        return 9
    elif age <= 69:
        return 10
    elif age <= 74:
        return 11
    elif age <= 79:
        return 12
    else:
        return 13

def predict_health_risk():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        from models.predictor import get_predictor
        
        data = request.get_json()
        model_name = data.get('model', 'random_forest')
        
        # Convert actual age to BRFSS category (1-13)
        age_category = age_to_category(data.get('Age', 25))
        
        # Prepare prediction data with required features
        prediction_data = {
            'HighBP': int(data.get('HighBP', 0)),
            'HighChol': int(data.get('HighChol', 0)),
            'BMI': float(data.get('BMI', 25)),
            'Smoker': int(data.get('Smoker', 0)),
            'PhysActivity': int(data.get('PhysActivity', 0)),
            'GenHlth': int(data.get('GenHlth', 3)),
            'MentHlth': float(data.get('MentHlth', 0)),
            'PhysHlth': float(data.get('PhysHlth', 0)),
            'DiffWalk': int(data.get('DiffWalk', 0)),
            'Sex': int(data.get('Sex', 0)),
            'Age': float(age_category)
        }
        
        predictor = get_predictor()
        result = predictor.predict(prediction_data, model_name)
        
        # Save prediction to history
        save_prediction(
            session['user_id'],
            model_name.replace('_', ' ').title(),
            round(result['probability'] * 100, 1),
            result['risk_level']
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def logout():
    session.clear()
    return redirect(url_for('login'))
