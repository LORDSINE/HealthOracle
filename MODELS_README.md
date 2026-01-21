# ML Models Implementation Summary

## Directory Structure Created
```
models/
├── __init__.py                      # Package initialization
├── joblib/                          # Directory for trained model files
│   ├── .gitkeep                     # Placeholder for git
│   ├── svm_model.pkl               # SVM trained model (created on first run)
│   ├── logistic_regression_model.pkl  # LR trained model (created on first run)
│   └── random_forest_model.pkl      # RF trained model (created on first run)
├── svm_model.py                     # SVM model training and loading
├── logistic_regression_model.py     # Logistic Regression model training and loading
├── random_forest_model.py           # Random Forest model training and loading
└── predictor.py                     # Unified prediction interface
```

## Files Created

### 1. **models/svm_model.py**
- Support Vector Machine model
- Features: StandardScaler + SVC with RBF kernel
- Checks for pre-trained model, trains if not found
- Stores model in `joblib/svm_model.pkl`

### 2. **models/logistic_regression_model.py**
- Logistic Regression model
- Features: StandardScaler + LogisticRegression
- Checks for pre-trained model, trains if not found
- Stores model in `joblib/logistic_regression_model.pkl`

### 3. **models/random_forest_model.py**
- Random Forest Classifier model
- 100 trees with balanced class weights
- Checks for pre-trained model, trains if not found
- Stores model in `joblib/random_forest_model.pkl`

### 4. **models/predictor.py**
- Unified `ModelPredictor` class for all models
- Handles feature loading and data preprocessing
- Provides risk assessment (Low/Medium/High Risk)
- Returns prediction probabilities for all classes

### 5. **Updated app.py**
- Added `/api/predict` endpoint for model predictions
- Imported `predict_health_risk` function
- Added `abort` import for error handling

### 6. **Updated user_routes.py**
- Added `predict_health_risk()` API endpoint
- Collects form data and calls model predictor
- Returns JSON with prediction results

### 7. **Updated prediction.html**
- Added new form fields for all model features:
  - Age, Sex, Height, Weight (with BMI calculation)
  - Health Conditions: High BP, High Cholesterol
  - Lifestyle: Smoking, Physical Activity, Walking Difficulty
  - Health Metrics: Mental Health, Physical Health (days per month)
  - Diet: Fruits, Vegetables consumption
  - Habits: Heavy Alcohol Consumption
  - Socioeconomic: Education Level, Income Level
- Updated JavaScript:
  - Form validation before prediction
  - Data collection from all inputs
  - Async API call to `/api/predict`
  - Beautiful results display with risk classification
  - Probability visualization

## Model Training Flow

### First Time (No joblib directory):
1. User clicks "Generate Risk Prediction"
2. Selects a model (SVM, LR, or RF)
3. API calls `/api/predict`
4. `get_predictor()` initializes models
5. Each model checks for `joblib/<model>.pkl`
6. If not found, models train from `health_data_clean(1).csv`
7. Models saved to respective `.pkl` files
8. Prediction made and returned
9. Results displayed in modal

### Subsequent Runs (joblib directory exists):
1. Models loaded directly from `.pkl` files
2. No training occurs (fast prediction)
3. Prediction made and returned immediately

## Features Used for Prediction

The models are trained on 16 features (after removing leakage and low correlation columns):
- HighBP, HighChol, BMI, Smoker, PhysActivity
- Fruits, Veggies, HvyAlcoholConsump
- GenHlth, MentHlth, PhysHlth
- DiffWalk, Sex, Age
- Education, Income

Target variable: `HeartDiseaseorAttack` (binary: 0 or 1)

## Risk Assessment Logic

Results are classified as:
- **Low Risk**: Probability < 50%
- **Medium Risk**: Probability 50-70%
- **High Risk**: Probability ≥ 70%

## Next Steps

1. The models will auto-train on first prediction request
2. Subsequent predictions will use cached models
3. Users can compare results across all three models
4. Models can be retrained by deleting the joblib directory
