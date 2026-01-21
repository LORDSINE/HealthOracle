"""Support Vector Machine model for heart disease prediction."""
import os
import pandas as pd
import joblib
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split


def get_model_path():
    """Get the joblib directory path."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, 'joblib')


def get_svm_model():
    """
    Load or train the SVM model.
    
    If the model exists in the joblib directory, load it.
    Otherwise, train it from the dataset and save it.
    
    Returns:
        Pipeline: The trained or loaded SVM model.
    """
    joblib_dir = get_model_path()
    model_path = os.path.join(joblib_dir, 'svm.joblib')
    
    # If model already exists, try loading it; if it fails, delete and retrain
    if os.path.exists(model_path):
        try:
            print("Loading pre-trained SVM model...")
            return joblib.load(model_path)
        except Exception as e:
            print(f"Failed to load pre-trained SVM model ({e}). Deleting and retraining...")
            try:
                os.remove(model_path)
            except Exception:
                pass
    
    # Otherwise, train the model
    print("Training SVM model...")
    
    # Load and prepare data (using normalized dataset)
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'health_data_ml_01.csv')
    df = pd.read_csv(data_path)
    
    # Select only required features (all values already normalized 0-1)
    feature_cols = ['HighBP', 'HighChol', 'BMI', 'Smoker', 'PhysActivity',
                    'GenHlth', 'MentHlth', 'PhysHlth', 'DiffWalk', 'Sex', 'Age', 'Diabetes_binary']
    
    X = df[feature_cols]
    y = df['HeartDiseaseorAttack']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )
    
    # Create and train pipeline
    svm_model = Pipeline([
        ("scaler", StandardScaler()),
        ("svc", SVC(
            kernel="rbf",
            C=1.0,
            gamma="scale",
            class_weight="balanced",
            probability=True
        ))
    ])
    
    svm_model.fit(X_train, y_train)
    
    # Create joblib directory if it doesn't exist
    os.makedirs(joblib_dir, exist_ok=True)
    
    # Save the model
    joblib.dump(svm_model, model_path)
    print(f"SVM model trained and saved to {model_path}")
    
    return svm_model


def get_feature_names():
    """Get the list of feature names used by the model."""
    return [
        'HighBP', 'HighChol', 'BMI', 'Smoker', 'PhysActivity',
        'GenHlth', 'MentHlth', 'PhysHlth', 'DiffWalk', 'Sex', 'Age', 'Diabetes_binary'
    ]


if __name__ == '__main__':
    model = get_svm_model()
    print("SVM Model Features:", get_feature_names())
