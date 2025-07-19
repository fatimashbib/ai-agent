import React, { useState } from 'react';

export default function Recommendation() {
  const [score, setScore] = useState('');
  const [topic, setTopic] = useState('math');
  const [recommendation, setRecommendation] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:8000/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ score: parseInt(score), topic })
      });
      
      if (response.ok) {
        const data = await response.json();
        setRecommendation(data.recommendation);
      }
    } catch (err) {
      console.error('Failed to get recommendation');
    }
  };

  return (
    <div className="auth-form">
      <h2>Get Learning Recommendation</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="number"
          placeholder="Your score (0-100)"
          value={score}
          onChange={(e) => setScore(e.target.value)}
          min="0"
          max="100"
          required
        />
        <select value={topic} onChange={(e) => setTopic(e.target.value)}>
          <option value="math">Math</option>
          <option value="physics">Physics</option>
          <option value="history">History</option>
        </select>
        <button type="submit">Get Recommendation</button>
      </form>
      
      {recommendation && (
        <div className="recommendation-result">
          <h3>AI Recommends:</h3>
          <p>{recommendation}</p>
        </div>
      )}
    </div>
  );
}