import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Register() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState({ text: '', isError: false });
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:8000/auth/register', {
        method: 'POST',
        mode: 'cors',  // Explicitly enable CORS
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({ email, password })
      });
      
      // First check if the response is OK
      if (!response.ok) {
        // Try to parse error response
        try {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Registration failed');
        } catch (parseError) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
      }

      const data = await response.json();
      setMessage({ text: 'Registration successful! Redirecting...', isError: false });
      setTimeout(() => navigate('/login'), 2000);
    } catch (err) {
      console.error('Registration error:', err);
      setMessage({ 
        text: err.message.includes('Failed to fetch') 
          ? 'Network error - please check your connection' 
          : err.message,
        isError: true 
      });
    }
  };

  return (
    <div className="auth-form">
   <h3 className="header-title">Critical Thinking Assessment 🧠</h3>

      <h2>Register</h2>
      {message.text && (
        <p style={{ color: message.isError ? 'red' : 'green' }}>{message.text}</p>
      )}
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength="6"
        />
        <button type="submit">Register</button>
      </form>
      <p>Already have an account? <a href="/login">Login</a></p>
    </div>
  );
}