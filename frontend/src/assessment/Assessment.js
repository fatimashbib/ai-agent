import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import './styles.css';

export default function Assessment() {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();

  const generateTest = async () => {
    setLoading(true);
    try {
      const response = await fetch('/assessment/generate-test', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${user.token}`,
          'Content-Type': 'application/json'
        }
      });
      const data = await response.json();
      setQuestions(data.questions);
      setAnswers({});
      setResults(null);
    } catch (err) {
      console.error('Failed to generate test:', err);
    } finally {
      setLoading(false);
    }
  };

  const submitTest = async () => {
    setLoading(true);
    try {
      const response = await fetch('/assessment/evaluate-test', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${user.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ answers })
      });
      setResults(await response.json());
    } catch (err) {
      console.error('Failed to submit test:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="assessment-container">
      {questions.length === 0 ? (
        <button 
          onClick={generateTest}
          disabled={loading}
          className="generate-btn"
        >
          {loading ? 'Generating...' : 'Generate Critical Thinking Test'}
        </button>
      ) : (
        <>
          <div className="questions-section">
            {questions.map((q, i) => (
              <div key={i} className="question-card">
                <h3>Question {i+1}: {q.text}</h3>
                <div className="options">
                  {q.options.map((opt, j) => (
                    <label key={j} className="option">
                      <input
                        type="radio"
                        name={`q${i}`}
                        checked={answers[i] === j}
                        onChange={() => setAnswers({...answers, [i]: j})}
                      />
                      {opt}
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <button 
            onClick={submitTest}
            disabled={loading || Object.keys(answers).length < questions.length}
            className="submit-btn"
          >
            {loading ? 'Evaluating...' : 'Submit Test'}
          </button>
        </>
      )}
      
      {results && (
        <div className="results-section">
          <h2>Your Results</h2>
          <div className="score-card">
            <h3>Rule-Based Score</h3>
            <div className="score-value">{results.rule_based.score.toFixed(1)}%</div>
          </div>
          <div className="score-card">
            <h3>AI-Evaluated Score</h3>
            <div className="score-value">{results.ml_based.score.toFixed(1)}/10</div>
          </div>
          <div className="feedback">
            <h3>Feedback</h3>
            <p>{results.feedback}</p>
          </div>
        </div>
      )}
    </div>
  );
}