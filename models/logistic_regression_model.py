"""Logistic Regression model for heart disease prediction."""
import os
import pandas as pd
import joblib
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split


def get_model_path():
    """Get the joblib directory path."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, 'joblib')


def get_logistic_regression_model():
    """
    Load or train the Logistic Regression model.
    
    If the model exists in the joblib directory, load it.
    Otherwise, train it from the dataset and save it.
    
    Returns:
        Pipeline: The trained or loaded Logistic Regression model.
    """
    joblib_dir = get_model_path()
    model_path = os.path.join(joblib_dir, 'logistic_regression.joblib')
    
    # If model already exists, try loading it; if it fails, delete and retrain
    if os.path.exists(model_path):
        try:
            print("Loading pre-trained Logistic Regression model...")
            return joblib.load(model_path)
        except Exception as e:
            print(f"Failed to load pre-trained Logistic Regression model ({e}). Deleting and retraining...")
            try:
                os.remove(model_path)
            except Exception:
                pass
    
    # Otherwise, train the model
    print("Training Logistic Regression model...")
    
    # Load and prepare data
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'health_data_clean(1).csv')
    df = pd.read_csv(data_path)
    
    # Select only required features
    feature_cols = ['HighBP', 'HighChol', 'BMI', 'Smoker', 'PhysActivity',
                    'GenHlth', 'MentHlth', 'PhysHlth', 'DiffWalk', 'Sex', 'Age']
    
    X = df[feature_cols]
    y = df['HeartDiseaseorAttack']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )
    
    # Create and train pipeline - use probability=True for calibrated predictions
    logistic_model = Pipeline([
        ("scaler", StandardScaler()),
        ("logistic", LogisticRegression(
            max_iter=5000,
            random_state=42,
            solver='lbfgs',
            C=1.0,
            class_weight='balanced'  # Handle class imbalance
        ))
    ])
    
    logistic_model.fit(X_train, y_train)
    
    # Create joblib directory if it doesn't exist
    os.makedirs(joblib_dir, exist_ok=True)
    
    # Save the model
    joblib.dump(logistic_model, model_path)
    print(f"Logistic Regression model trained and saved to {model_path}")
    
    return logistic_model


def get_feature_names():
    """Get the list of feature names used by the model."""
    return [
        'HighBP', 'HighChol', 'BMI', 'Smoker', 'PhysActivity',
        'GenHlth', 'MentHlth', 'PhysHlth', 'DiffWalk', 'Sex', 'Age'
    ]


if __name__ == '__main__':
    model = get_logistic_regression_model()
    print("Logistic Regression Model Features:", get_feature_names())
