import os
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


def get_model_path():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, 'joblib')


def get_random_forest_model():
    joblib_dir = get_model_path()
    model_path = os.path.join(joblib_dir, 'random_forest.joblib')
    
    # If model already exists, try loading it; if it fails, delete and retrain
    if os.path.exists(model_path):
        try:
            print("Loading pre-trained Random Forest model...")
            return joblib.load(model_path)
        except Exception as e:
            print(f"Failed to load pre-trained Random Forest model ({e}). Deleting and retraining...")
            try:
                os.remove(model_path)
            except Exception:
                pass
    
    # Otherwise, train the model
    print("Training Random Forest model...")
    
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
    
    # Create and train model
    rf_model = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    
    rf_model.fit(X_train, y_train)
    
    # Create joblib directory if it doesn't exist
    os.makedirs(joblib_dir, exist_ok=True)
    
    # Save the model
    joblib.dump(rf_model, model_path)
    print(f"Random Forest model trained and saved to {model_path}")
    
    return rf_model


def get_feature_names():
    return [
        'HighBP', 'HighChol', 'BMI', 'Smoker', 'PhysActivity',
        'GenHlth', 'MentHlth', 'PhysHlth', 'DiffWalk', 'Sex', 'Age', 'Diabetes_binary'
    ]


if __name__ == '__main__':
    model = get_random_forest_model()
    print("Random Forest Model Features:", get_feature_names())
