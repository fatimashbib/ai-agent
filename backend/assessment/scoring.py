import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from joblib import dump, load
import pickle
import os

MODEL_PATH = "strength_model.joblib"
SCALER_PATH = "strength_scaler.pkl"
LABEL_ENCODER_PATH = "label_encoder.pkl"

class Scorer:
    def __init__(self):
        self.strength_evaluator = StrengthEvaluator()
    
    def calculate_score(self, questions: list, answers: dict) -> float:
        """
        Calculate the test score based on correct answers
        """
        correct = 0
        for q in questions:
            if q['id'] in answers and answers[q['id']] == q['correct_index']:
                correct += 1
        return (correct / len(questions)) * 100 if questions else 0

    def evaluate_strength(self, score: float, time_seconds: float) -> dict:
        """
        Evaluate strength using both rule-based and ML-based approaches
        """
        return {
            "rule_based": self.strength_evaluator.predict_rule_strength(score, time_seconds),
            "ml_based": self.strength_evaluator.predict_ml_strength(score, time_seconds)
        }


class StrengthEvaluator:
    def __init__(self):
        # Load or train ML model for strength prediction
        if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH) and os.path.exists(LABEL_ENCODER_PATH):
            self.model = load(MODEL_PATH)
            with open(SCALER_PATH, 'rb') as f:
                self.scaler = pickle.load(f)
            with open(LABEL_ENCODER_PATH, 'rb') as f:
                self.label_encoder = pickle.load(f)
            print("Loaded ML model, scaler, and label encoder.")
        else:
            self.model = RandomForestClassifier(random_state=42)
            self.scaler = StandardScaler()
            self.label_encoder = LabelEncoder()
            self._initial_train()

    def _initial_train(self):
        # Example training data: [score, time_seconds]
        X_train = np.array([
            [85, 250],  # Strong
            [75, 400],  # Moderate
            [60, 550],  # Moderate
            [40, 700],  # Weak
            [90, 200],  # Strong
            [55, 650],  # Weak
            [70, 300],  # Moderate
            [30, 800],  # Weak
        ])
        y_train = np.array([
            "Strong",
            "Moderate",
            "Moderate",
            "Weak",
            "Strong",
            "Weak",
            "Moderate",
            "Weak",
        ])

        y_encoded = self.label_encoder.fit_transform(y_train)
        X_scaled = self.scaler.fit_transform(X_train)
        self.model.fit(X_scaled, y_encoded)

        dump(self.model, MODEL_PATH)
        with open(SCALER_PATH, 'wb') as f:
            pickle.dump(self.scaler, f)
        with open(LABEL_ENCODER_PATH, 'wb') as f:
            pickle.dump(self.label_encoder, f)
        print("Trained ML model and saved.")

    def predict_ml_strength(self, score: float, time_seconds: float) -> str:
        X = np.array([[score, time_seconds]])
        X_scaled = self.scaler.transform(X)
        pred_encoded = self.model.predict(X_scaled)[0]
        return self.label_encoder.inverse_transform([pred_encoded])[0]

    def predict_rule_strength(self, score: float, time_seconds: float) -> str:
        # Simple fixed thresholds for rule-based strength
        if score >= 80 and time_seconds <= 300:
            return "Strong"
        elif score >= 50 and time_seconds <= 600:
            return "Moderate"
        else:
            return "Weak"


if __name__ == "__main__":
    evaluator = StrengthEvaluator()
    scorer = Scorer()

    score = 78
    time_sec = 420

    rule_strength = evaluator.predict_rule_strength(score, time_sec)
    ml_strength = evaluator.predict_ml_strength(score, time_sec)

    print(f"Rule-based strength: {rule_strength}")
    print(f"ML-based strength: {ml_strength}")