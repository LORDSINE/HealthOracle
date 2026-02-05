import os
import numpy as np
import pandas as pd
import joblib


class StandardScalerSimple:
    def __init__(self):
        self.mean_ = None
        self.scale_ = None

    def fit(self, X):
        self.mean_ = X.mean(axis=0)
        self.scale_ = X.std(axis=0)
        self.scale_ = np.where(self.scale_ == 0, 1.0, self.scale_)
        return self

    def transform(self, X):
        return (X - self.mean_) / self.scale_

    def fit_transform(self, X):
        return self.fit(X).transform(X)


class LogisticRegressionScratch:
    def __init__(self, lr=0.05, max_iter=4000, tol=1e-6, class_weight=None, random_state=42):
        self.lr = lr
        self.max_iter = max_iter
        self.tol = tol
        self.class_weight = class_weight
        self.random_state = random_state
        self.coef_ = None
        self.intercept_ = None

    @staticmethod
    def _sigmoid(z):
        z = np.clip(z, -500, 500)
        return 1.0 / (1.0 + np.exp(-z))

    def _compute_sample_weights(self, y):
        if not self.class_weight:
            return np.ones_like(y, dtype=float)
        if self.class_weight == "balanced":
            classes, counts = np.unique(y, return_counts=True)
            total = y.shape[0]
            weights = {c: total / (len(classes) * cnt) for c, cnt in zip(classes, counts)}
        elif isinstance(self.class_weight, dict):
            weights = self.class_weight
        else:
            return np.ones_like(y, dtype=float)
        return np.array([weights[int(label)] for label in y], dtype=float)

    def fit(self, X, y):
        rng = np.random.default_rng(self.random_state)
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)

        n_samples, n_features = X.shape
        self.coef_ = rng.normal(scale=0.01, size=n_features)
        self.intercept_ = 0.0

        sample_w = self._compute_sample_weights(y)
        prev_loss = None

        for _ in range(self.max_iter):
            linear = X @ self.coef_ + self.intercept_
            probs = self._sigmoid(linear)

            eps = 1e-12
            loss = -np.average(
                sample_w * (y * np.log(probs + eps) + (1 - y) * np.log(1 - probs + eps))
            )

            error = (probs - y) * sample_w
            grad_w = (X.T @ error) / n_samples
            grad_b = error.mean()

            self.coef_ -= self.lr * grad_w
            self.intercept_ -= self.lr * grad_b

            if prev_loss is not None and abs(prev_loss - loss) < self.tol:
                break
            prev_loss = loss

        return self

    def predict_proba(self, X):
        X = np.asarray(X, dtype=float)
        probs = self._sigmoid(X @ self.coef_ + self.intercept_)
        return np.column_stack([1 - probs, probs])

    def predict(self, X, threshold=0.5):
        probs = self.predict_proba(X)[:, 1]
        return (probs >= threshold).astype(int)


class LogisticRegressionBundle:
    def __init__(self, scaler, model):
        self.scaler = scaler
        self.model = model

    def predict_proba(self, X):
        X = np.asarray(X, dtype=float)
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)

    def predict(self, X, threshold=0.5):
        X = np.asarray(X, dtype=float)
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled, threshold=threshold)


def get_model_path():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, 'joblib')


def get_logistic_regression_model():
    joblib_dir = get_model_path()
    model_path = os.path.join(joblib_dir, 'logistic_regression.joblib')

    if os.path.exists(model_path):
        try:
            print("Loading pre-trained Logistic Regression model")
            loaded = joblib.load(model_path)
            if isinstance(loaded, dict) and "scaler" in loaded and "model" in loaded:
                return LogisticRegressionBundle(loaded["scaler"], loaded["model"])
            if isinstance(loaded, LogisticRegressionBundle):
                return loaded
            return loaded
        except Exception as e:
            print(f"Failed to load pre-trained Logistic Regression model ({e}). Deleting and retraining")
            try:
                os.remove(model_path)
            except Exception:
                pass

    print("Training Logistic Regression model")

    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'health_data_ml_01.csv')
    df = pd.read_csv(data_path)

    feature_cols = ['HighBP', 'HighChol', 'BMI', 'Smoker', 'PhysActivity',
                    'GenHlth', 'MentHlth', 'PhysHlth', 'DiffWalk', 'Sex', 'Age', 'Diabetes_binary']

    X = df[feature_cols].to_numpy(dtype=float)
    y = df['HeartDiseaseorAttack'].to_numpy(dtype=int)

    scaler = StandardScalerSimple()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegressionScratch(
        lr=0.05,
        max_iter=5000,
        tol=1e-7,
        class_weight="balanced",
        random_state=42
    )
    model.fit(X_scaled, y)

    os.makedirs(joblib_dir, exist_ok=True)
    bundle = LogisticRegressionBundle(scaler, model)
    joblib.dump(bundle, model_path)
    print(f"Logistic Regression model trained and saved to {model_path}")

    return bundle


def get_feature_names():
    return [
        'HighBP', 'HighChol', 'BMI', 'Smoker', 'PhysActivity',
        'GenHlth', 'MentHlth', 'PhysHlth', 'DiffWalk', 'Sex', 'Age', 'Diabetes_binary'
    ]


if __name__ == '__main__':
    model = get_logistic_regression_model()
    print("Logistic Regression Model Features:", get_feature_names())
    if isinstance(model, LogisticRegressionBundle):
        print("Scaler mean shape:", model.scaler.mean_.shape)
        print("Coef shape:", model.model.coef_.shape)
