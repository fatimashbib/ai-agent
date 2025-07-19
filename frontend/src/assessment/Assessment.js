import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import './styles.css';

export default function Assessment() {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [testId, setTestId] = useState(null); // <-- Added testId state
  const { token } = useAuth();
  const navigate = useNavigate();

  if (!token) {
    navigate('/login');
    return null;
  }

  const generateTest = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/assessment/generate-test', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      if (!response.ok) throw new Error('Failed to generate test');
      const data = await response.json();
      setQuestions(data.questions);
      setAnswers({});
      setResults(null);
      setTestId(data.test_id); // <-- Save test_id from response
    } catch (err) {
      console.error('Failed to generate test:', err);
    } finally {
      setLoading(false);
    }
  };

  const submitTest = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/assessment/evaluate-test', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          test_id: testId,   // <-- Include test_id in request body
          answers: answers
        })
      });
      if (!response.ok) throw new Error('Failed to submit test');
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
                <h3>Question {i + 1}: {q.text}</h3>
                <div className="options">
                  {q.options.map((opt, j) => (
                    <label key={j} className="option">
                      <input
                        type="radio"
                        name={`q${i}`}
                        checked={answers[q.id] === j}
                        onChange={() => setAnswers({ ...answers, [q.id]: j })}
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
          {results.feedback && (
            <div className="feedback">
              <h3>Overview</h3>
              <p>{results.feedback.overview}</p>

              <h3>Strengths</h3>
              <ul>
                {results.feedback.strengths.map((point, i) => <li key={i}>{point}</li>)}
              </ul>

              <h3>Areas for Improvement</h3>
              <ul>
                {results.feedback.improvements.map((point, i) => <li key={i}>{point}</li>)}
              </ul>
            </div>
          )}


        </div>
      )}
    </div>
  );
}
