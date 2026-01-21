"""Prediction utilities for all models."""
import os
import warnings

warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from .logistic_regression_model import (
    get_logistic_regression_model,
    get_feature_names as get_lr_features,
)
from .random_forest_model import get_random_forest_model, get_feature_names as get_rf_features


class ModelPredictor:
    """Unified predictor for all models with lazy loading."""

    def __init__(self):
        """Set up feature list and lazy model cache without loading models."""
        # Use feature list from logistic regression (same for both models)
        self.feature_names = get_lr_features()
        # Cache for loaded models: {'logistic_regression': model, 'random_forest': model}
        self._models = {}

    def _get_model(self, model_name: str):
        """Load and cache only the requested model."""
        if model_name in self._models:
            return self._models[model_name]

        if model_name == 'logistic_regression':
            model = get_logistic_regression_model()
        elif model_name == 'random_forest':
            model = get_random_forest_model()
        else:
            raise ValueError(f"Unknown model: {model_name}. Available: logistic_regression, random_forest")

        self._models[model_name] = model
        return model

    def predict(self, data_dict, model_name='random_forest'):
        """
        Make prediction using the specified model.
        
        Args:
            data_dict (dict): Dictionary with feature names as keys and values
            model_name (str): Name of the model to use ('svm', 'logistic_regression', 'random_forest')
        
        Returns:
            dict: Prediction result with probability and risk level
        """
        # Create DataFrame from input data with only required features
        data_to_use = {key: data_dict.get(key, 0) for key in self.feature_names}
        df = pd.DataFrame([data_to_use])
        
        # Ensure all features are present in correct order
        X = df[self.feature_names]
        
        # Load only the requested model
        model = self._get_model(model_name)
        
        # Make prediction
        prediction = model.predict(X)[0]
        probability = model.predict_proba(X)[0]
        
        # Get the disease probability (class 1 = has disease)
        disease_probability = float(probability[1])
        
        # Determine risk level based on disease probability
        if disease_probability >= 0.7:
            risk_level = 'High Risk'
        elif disease_probability >= 0.5:
            risk_level = 'Medium Risk'
        else:
            risk_level = 'Low Risk'
        
        return {
            'prediction': int(prediction),
            'has_heart_disease': int(prediction == 1),
            'probability': disease_probability,
            'risk_level': risk_level,
            'model_used': model_name,
            'class_probabilities': {
                'no_disease': float(probability[0]),
                'has_disease': float(probability[1])
            }
        }
    
    def get_feature_list(self):
        """Get the list of required features for prediction."""
        return self.feature_names


# Global predictor instance
_predictor = None


def get_predictor():
    """Get or create the global predictor instance."""
    global _predictor
    if _predictor is None:
        _predictor = ModelPredictor()
    return _predictor
