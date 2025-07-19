import numpy as np
from sklearn.ensemble import RandomForestRegressor
from joblib import dump, load
import os

MODEL_PATH = "scoring_model.joblib"

class Scorer:
    def __init__(self):
        if os.path.exists(MODEL_PATH):
            self.model = load(MODEL_PATH)
            print(f"Loaded model from {MODEL_PATH}")
        else:
            self.model = RandomForestRegressor(random_state=42, n_estimators=100)
            self._initial_train()
    
    def _initial_train(self):
        # ======= Synthetic training data =======
        # Features:
        # [question text length, answered correctly (0/1), number of options, explanation length, question index]
# Add more "wrong answer" examples with low scores
        X_train = np.array([
            [80, 1, 4, 35, 0],   # Correct
            [90, 1, 4, 45, 1],
            [75, 1, 3, 30, 2],
            [85, 1, 4, 40, 3],
            [95, 0, 4, 35, 4],   # Wrong with explanation
            [70, 0, 3, 20, 5],   # Wrong, short
            [100, 0, 5, 50, 6],  # Wrong, long explanation (shouldn't get high score)
            [60, 0, 4, 25, 7],
            [100, 0, 4, 60, 8],  # Another bad case
            [85, 0, 4, 20, 9],
        ])
        y_train = np.array([9, 9, 8, 9, 4, 2, 3, 2, 2, 3])


        self.model.fit(X_train, y_train)
        dump(self.model, MODEL_PATH)
        print(f"Trained new model and saved to {MODEL_PATH}")
    
    def retrain(self, X_new, y_new):
        """
        Retrain the model with new data and save it.

        Args:
            X_new (np.ndarray): New feature data (2D array).
            y_new (np.ndarray): New target scores (1D array).
        """
        self.model.fit(X_new, y_new)
        dump(self.model, MODEL_PATH)
        print(f"Retrained model saved to {MODEL_PATH}")
    
    def rule_based_score(self, questions, answers):
        """
        Calculate rule-based score based on correct answers.

        Args:
            questions (list): List of question dicts with 'id' and 'correct_index'.
            answers (dict): Dict of {question_id: selected_answer_index}.

        Returns:
            float: Percentage score (0-100).
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

        Args:
            questions (list): List of question dicts.
            answers (dict): Dict of {question_id: selected_answer_index}.

        Returns:
            float: Average predicted score on scale 0-10.
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

        print("Features for prediction:", features)
        preds = self.model.predict(features)
        print("Predicted scores per question:", preds)
        avg_score = preds.mean()
        return avg_score


if __name__ == "__main__":
    scorer = Scorer()

    # Example new training data for retraining
    X_new = np.array([
        [65, 1, 4, 20, 0],
        [90, 0, 5, 40, 1],
        [75, 1, 3, 30, 2],
        [85, 1, 4, 25, 3],
    ])
    y_new = np.array([8, 4, 7, 9])

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
