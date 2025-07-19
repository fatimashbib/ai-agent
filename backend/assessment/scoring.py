import numpy as np
from sklearn.ensemble import RandomForestClassifier
from joblib import dump, load
import os

MODEL_PATH = "scoring_model.joblib"

class Scorer:
    def __init__(self):
        if os.path.exists(MODEL_PATH):
            self.model = load(MODEL_PATH)
        else:
            self.model = RandomForestClassifier()
            # Initialize with dummy data - replace with real training data
            X = np.random.rand(100, 5)
            y = np.random.randint(0, 10, 100)
            self.model.fit(X, y)
            dump(self.model, MODEL_PATH)
    
    def rule_based_score(self, questions, answers):
        score = 0
        for q_idx, answer in answers.items():
            if answer == questions[q_idx]['correct_index']:
                score += 1
        return (score / len(questions)) * 100
    
    def ml_based_score(self, questions, answers):
        features = []
        for q_idx, q in enumerate(questions):
            features.append([
                len(q['text']),  # Question complexity
                int(answers.get(str(q_idx), -1) == q['correct_index']),
                len(q['options']),
                len(q['explanation']),
                q_idx  # Position in test
            ])
        return self.model.predict(features).mean() * 10