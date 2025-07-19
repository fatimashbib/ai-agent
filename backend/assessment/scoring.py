import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV
from joblib import dump, load
import pickle
import os

MODEL_PATH = "scoring_model.joblib"
SCALER_PATH = "scaler.pkl"

class Scorer:
    def __init__(self):
        # Load model and scaler if available
        if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
            self.model = load(MODEL_PATH)
            with open(SCALER_PATH, 'rb') as f:
                self.scaler = pickle.load(f)
            print(f"Loaded model and scaler from disk.")
        else:
            # Initialize model and scaler and train fresh
            self.model = RandomForestRegressor(random_state=42)
            self.scaler = StandardScaler()
            self._initial_train()
    
    def _initial_train(self):
        # More realistic synthetic training data (replace with your real data)
        # Features: [text_length, correct(0/1), num_options, explanation_length, question_index]
        X_train = np.array([
            [120, 1, 4, 40, 0],   # correct, detailed explanation
            [100, 1, 3, 35, 1],
            [150, 1, 5, 50, 2],
            [90, 0, 4, 20, 3],    # wrong answer, short explanation
            [110, 0, 4, 15, 4],
            [80,  0, 3, 10, 5],
            [130, 1, 4, 45, 6],
            [95,  0, 4, 5,  7],
            [140, 1, 5, 60, 8],
            [85,  0, 3, 25, 9],
            # Add more examples to improve generalization
        ])
        y_train = np.array([9, 8, 10, 3, 2, 1, 9, 1, 10, 3])

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)

        # Hyperparameter tuning with GridSearchCV (optional but recommended)
        param_grid = {
            'n_estimators': [100, 150],
            'max_depth': [None, 10, 20],
            'min_samples_split': [2, 5]
        }
        grid = GridSearchCV(RandomForestRegressor(random_state=42), param_grid, cv=3)
        grid.fit(X_train_scaled, y_train)

        self.model = grid.best_estimator_
        print(f"Trained model with best params: {grid.best_params_}")

        # Save model and scaler
        dump(self.model, MODEL_PATH)
        with open(SCALER_PATH, 'wb') as f:
            pickle.dump(self.scaler, f)
        print(f"Model and scaler saved.")

    def retrain(self, X_new, y_new):
        """
        Retrain the model with new data and save it.
        """
        X_new_scaled = self.scaler.transform(X_new)  # scale new data using existing scaler
        self.model.fit(X_new_scaled, y_new)
        dump(self.model, MODEL_PATH)
        print(f"Retrained model saved to {MODEL_PATH}")

    def rule_based_score(self, questions, answers):
        """
        Calculate rule-based score based on correct answers.
        """
        score = 0
        for q_idx, answer in answers.items():
            question = next(q for q in questions if q['id'] == q_idx)
            if answer == question['correct_index']:
                score += 1
        return (score / len(questions)) * 100

    def ml_based_score(self, questions, answers):
        """
        Calculate ML-based predicted score.
        """
        features = []
        for q_idx, q in enumerate(questions):
            feat = [
                len(q['text']),
                int(answers.get(q['id'], -1) == q['correct_index']),
                len(q['options']),
                len(q.get('explanation', '')),
                q_idx
            ]
            features.append(feat)

        # Scale features before prediction
        features_scaled = self.scaler.transform(features)
        print("Features for prediction (scaled):", features_scaled)

        preds = self.model.predict(features_scaled)
        print("Predicted scores per question:", preds)
        avg_score = preds.mean()
        return avg_score


if __name__ == "__main__":
    scorer = Scorer()

    # Example new training data for retraining (must be scaled inside retrain)
    X_new = np.array([
        [110, 1, 4, 30, 0],
        [95,  0, 4, 20, 1],
        [130, 1, 5, 40, 2],
        [85,  1, 3, 25, 3],
    ])
    y_new = np.array([8, 3, 9, 7])
    scorer.retrain(X_new, y_new)

    # Example questions & answers for scoring
    questions = [
        {"id": 1, "text": "What is AI?", "options": ["Tech", "Food"], "correct_index": 0, "explanation": "AI means Artificial Intelligence."},
        {"id": 2, "text": "What is 2+2?", "options": ["3", "4"], "correct_index": 1, "explanation": "Basic math."},
    ]
    answers = {
        1: 0,  # correct
        2: 0,  # wrong
    }

    rule_score = scorer.rule_based_score(questions, answers)
    ml_score = scorer.ml_based_score(questions, answers)

    print(f"Rule-based score: {rule_score:.2f}%")
    print(f"ML-based score: {ml_score:.2f}/10")
