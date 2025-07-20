import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import './styles.css';

export default function Assessment() {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [testId, setTestId] = useState(null);
  const [previousTests, setPreviousTests] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const { token, user } = useAuth();
  const navigate = useNavigate();

  const calculateTestDuration = (createdAt, completedAt) => {
    if (!createdAt || !completedAt) return 'N/A';

    const created = new Date(createdAt);
    const completed = new Date(completedAt);
    const durationMs = completed - created;

    // Convert milliseconds to minutes and seconds
    const minutes = Math.floor(durationMs / 60000);
    const seconds = Math.floor((durationMs % 60000) / 1000);

    return `${minutes}m ${seconds}s`;
  };

  useEffect(() => {
    if (token) {
      fetchPreviousTests();
    }
  }, [token]);

  if (!token) {
    navigate('/login');
    return null;
  }

  const toggleDropdown = () => setDropdownOpen(!dropdownOpen);

  const logout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
    }
    navigate('/login');
  };


  const fetchPreviousTests = async () => {
    try {
      const response = await fetch('http://localhost:8000/assessment/test-history', {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) throw new Error('Failed to fetch test history');
      const data = await response.json();

      // No need to parse feedback as it's already an object
      setPreviousTests(data.tests || []); // Ensure we always have an array
    } catch (err) {
      console.error('Failed to fetch test history:', err);
      setPreviousTests([]); // Set empty array on error
    }
  };

  const generateTest = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/assessment/generate-test', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
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
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          test_id: testId,
          answers: answers,
        }),
      });
      if (!response.ok) throw new Error('Failed to submit test');
      const result = await response.json();
      setResults(result);
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
      score: {
        value: test.score,
        percentage: test.score,
        rule_based_strength: test.rule_based_strength,
        ml_based_strength: test.ml_based_strength
      },
      feedback: test.feedback || {
        overview: 'Previous test results',
        strengths: [],
        improvements: [],
      }
    });
    setShowHistory(false);
  };

  return (
    <div className="assessment-container">
      <div className="assessment-header">
        <h1 className="header-title">Critical Thinking Assessment</h1>

        <div className="header-controls">
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
            <button onClick={generateTest} disabled={loading} className="generate-btn">
              {loading ? 'Generating...' : 'New Test'}
            </button>
          </div>

          <div className="user-dropdown">
            <button onClick={toggleDropdown} className="user-button">
              {user?.email || 'User'} ▼
            </button>
            {dropdownOpen && (
              <div className="dropdown-content">
                <div className="user-email">{user?.email}</div>
                <button onClick={logout} className="logout-btn">
                  Logout
                </button>
              </div>
            )}
          </div>
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
                  <div className="test-meta">
                    <p>Date: {new Date(test.created_at).toLocaleDateString()}</p>
                    <p>Time taken: {calculateTestDuration(test.created_at, test.completed_at)}</p>
                  </div>
                  <div className="test-scores">
                    <span>Score: {test.score}/100</span>
                    <span>Strength: {test.rule_based_strength}</span>
                  </div>
                  <button onClick={() => viewTestResults(test)} className="view-results-btn">
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
              <div key={q.id} className="question-card">
                <h3>Question {i + 1}: {q.text}</h3>
                <div className="options">
                  {q.options.map((opt, j) => (
                    <label key={j} className="option">
                      <input
                        type="radio"
                        name={`q${q.id}`}
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
              <h3>Overall Score</h3>
              <div className="score-value">{results.score.value}/100</div>
            </div>

            <div className="strength-cards">
              <div className={`strength-card ${results.score.rule_based_strength.toLowerCase()}`}>
                <h3>Rule-Based Evaluation</h3>
                <div className="strength-value">
                  {results.score.rule_based_strength}
                </div>

              </div>

              <div className={`strength-card ${results.score.ml_based_strength.toLowerCase()}`}>
                <h3>AI Evaluation</h3>
                <div className="strength-value">
                  {results.score.ml_based_strength}
                </div>

              </div>
            </div>
          </div>

          {/* Rest of your feedback section remains the same */}
          {results.feedback && (
            <div className="feedback">
              <h3>Overview</h3>
              <p>{results.feedback.overview}</p>

              <h3>Strengths</h3>
              <ul>
                {results.feedback.strengths.map((point, i) => (
                  <li key={i}>{point}</li>
                ))}
              </ul>

              <h3>Areas for Improvement</h3>
              <ul>
                {results.feedback.improvements.map((point, i) => (
                  <li key={i}>{point}</li>
                ))}
              </ul>
            </div>
          )}


        </div>
      )}
    </div>
  );
}