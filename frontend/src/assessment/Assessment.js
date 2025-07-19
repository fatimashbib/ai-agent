import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import './styles.css';

export default function Assessment() {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [testId, setTestId] = useState(null);
  const [previousTests, setPreviousTests] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const { token } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (token) {
      fetchPreviousTests();
    }
  }, [token]);

  if (!token) {
    navigate('/login');
    return null;
  }

  const fetchPreviousTests = async () => {
    try {
      const response = await fetch('http://localhost:8000/assessment/test-history', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (!response.ok) throw new Error('Failed to fetch test history');
      const data = await response.json();
      setPreviousTests(data.tests);
    } catch (err) {
      console.error('Failed to fetch test history:', err);
    }
  };

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
      setTestId(data.test_id);
      setShowHistory(false);
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
          test_id: testId,
          answers: answers
        })
      });
      if (!response.ok) throw new Error('Failed to submit test');
      const result = await response.json();
      setResults(result);
      // Refresh the test history after submission
      await fetchPreviousTests();
    } catch (err) {
      console.error('Failed to submit test:', err);
    } finally {
      setLoading(false);
    }
  };

  const viewTestResults = (test) => {
    setQuestions([]);
    setResults({
      rule_based: { score: test.rule_based_score },
      ml_based: { score: test.ml_based_score },
      feedback: test.feedback || {
        overview: "Previous test results",
        strengths: [],
        improvements: []
      }
    });
    setShowHistory(false);
  };

  return (
    <div className="assessment-container">
      <div className="assessment-header">
        <h1>Critical Thinking Assessment</h1>
        <div className="action-buttons">
          <button
            onClick={() => {
              setQuestions([]);
              setResults(null);
              setShowHistory(!showHistory);
            }}
            className="history-btn"
          >
            {showHistory ? 'Hide History' : 'Tests History'}
          </button>
          <button
            onClick={generateTest}
            disabled={loading}
            className="generate-btn"
          >
            {loading ? 'Generating...' : 'New Test'}
          </button>
        </div>
      </div>

      {showHistory ? (
        <div className="test-history">
          <h2>Your Test History</h2>
          {previousTests.length === 0 ? (
            <p>No previous tests found. Generate a new test to get started!</p>
          ) : (
            <div className="test-list">
              {previousTests.map((test, index) => (
                <div key={test.id} className="test-card">
                  <h3>Test #{previousTests.length - index}</h3>
                  <p>Date: {new Date(test.created_at).toLocaleString()}</p>
                  <div className="test-scores">
                    <span>Rule-Based: {test.rule_based_score.toFixed(1)}%</span>
                    <span>AI-Evaluated: {test.ml_based_score.toFixed(1)}/10</span>
                  </div>
                  <button
                    onClick={() => viewTestResults(test)}
                    className="view-results-btn"
                  >
                    View Details
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : questions.length === 0 && !results ? (
        <div className="welcome-message">
          <h2>Welcome to the Critical Thinking Assessment</h2>
          <p>Click "New Test" to begin a new assessment or "View Previous Tests" to see your history.</p>
        </div>
      ) : questions.length > 0 ? (
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
      ) : null}

      {results && (
        <div className="results-section">
          <h2>Your Results</h2>
          <div className="score-cards">
            <div className="score-card">
              <h3>Rule-Based Score</h3>
              <div className="score-value">{results.rule_based.score.toFixed(1)}%</div>
            </div>
            <div className="score-card">
              <h3>AI-Evaluated Score</h3>
              <div className="score-value">{results.ml_based.score.toFixed(1)}/10</div>
            </div>
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
          <button
            onClick={generateTest}
            disabled={loading}
            className="generate-btn"
          >
            {loading ? 'Generating...' : 'Take Another Test'}
          </button>
        </div>
      )}
    </div>
  );
}