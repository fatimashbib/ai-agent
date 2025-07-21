import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from joblib import dump, load
import pickle
import os
import time

MODEL_PATH = "strength_model.joblib"
SCALER_PATH = "strength_scaler.pkl"
LABEL_ENCODER_PATH = "label_encoder.pkl"

class Scorer:
    def __init__(self):
        self.strength_evaluator = StrengthEvaluator()

    def calculate_score(self, questions: list, answers: dict) -> float:
        correct = 0
        for q in questions:
            if q['id'] in answers and answers[q['id']] == q['correct_index']:
                correct += 1
        return (correct / len(questions)) * 100 if questions else 0

    def evaluate_strength(self, score: float, time_seconds: float) -> dict:
        return {
            "rule_based": self.strength_evaluator.predict_rule_strength(score, time_seconds),
            "ml_based": self.strength_evaluator.predict_ml_strength(score, time_seconds)
        }

class StrengthEvaluator:
    def __init__(self):
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

            start_time = time.time()
            dataset_size = self._initial_train(start_time)
            duration = time.time() - start_time

            if duration <= 180:
                dump(self.model, MODEL_PATH)
                with open(SCALER_PATH, 'wb') as f:
                    pickle.dump(self.scaler, f)
                with open(LABEL_ENCODER_PATH, 'wb') as f:
                    pickle.dump(self.label_encoder, f)
                print(f"✅ Trained with {dataset_size} samples in {duration:.2f} seconds.")
            else:
                print(f"❌ Training took too long ({duration:.2f} seconds). Model not saved.")

    def _initial_train(self, start_time):
        X_train = []
        y_train = []

        def add_data(label, score_range, time_range, count):
            for _ in range(count):
                score = np.random.randint(score_range[0], score_range[1])
                time_val = np.random.randint(time_range[0], time_range[1])
                X_train.append([score, time_val])
                y_train.append(label)

        # Add Strong examples (score ≥ 80 and time ≤ 300)
        add_data("Strong", (80, 101), (100, 301), 200)

        # Add Moderate examples:
        # Case 1: score between 50 and 79, time up to 600
        add_data("Moderate", (50, 80), (250, 601), 150)
        # Case 2: score ≥ 80 but time > 300 (should NOT be Strong)
        add_data("Moderate", (80, 101), (301, 601), 100)

        # Add Weak examples:
        # Case 1: score < 50 and time > 500
        add_data("Weak", (0, 50), (500, 901), 150)
        # Case 2: score 50–79 and time > 600
        add_data("Weak", (50, 80), (601, 901), 100)

        X_train = np.array(X_train)
        y_train = np.array(y_train)

        y_encoded = self.label_encoder.fit_transform(y_train)
        X_scaled = self.scaler.fit_transform(X_train)
        self.model.fit(X_scaled, y_encoded)

        return len(y_train)

    def predict_ml_strength(self, score: float, time_seconds: float) -> str:
        X = np.array([[score, time_seconds]])
        X_scaled = self.scaler.transform(X)
        pred_encoded = self.model.predict(X_scaled)[0]
        return self.label_encoder.inverse_transform([pred_encoded])[0]

    def predict_rule_strength(self, score: float, time_seconds: float) -> str:
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
