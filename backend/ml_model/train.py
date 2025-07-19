import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from joblib import dump

# Sample data - replace with your dataset
data = {
    'score': [30, 70, 90, 40],
    'topic': ['math', 'physics', 'math', 'history'],
    'recommendation': ['video', 'article', 'quiz', 'video']
}
df = pd.DataFrame(data)

# Train model
model = RandomForestClassifier()
X = pd.get_dummies(df[['score', 'topic']])
y = df['recommendation']
model.fit(X, y)

# Save model
dump(model, 'model.joblib')
print("Model trained and saved!")
