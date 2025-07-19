import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [message, setMessage] = useState({ text: '', isError: false });
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ text: '', isError: false });

    try {
      const formPayload = new URLSearchParams();
      formPayload.append('username', formData.email);
      formPayload.append('password', formData.password);

      const response = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        credentials: 'include',
        body: formPayload
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
      }

      const data = await response.json();
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user_email', data.user_email);
      
      setMessage({ text: 'Login successful! Redirecting...', isError: false });
      setTimeout(() => navigate('/dashboard'), 1000);

    } catch (err) {
      console.error('Login error:', err);
      setMessage({ 
        text: err.message.includes('Failed to fetch') 
          ? 'Network error - please check your connection' 
          : err.message,
        isError: true 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-form">
      <h2>Login</h2>
      {message.text && (
        <p style={{ color: message.isError ? 'red' : 'green' }}>{message.text}</p>
      )}
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          name="email"
          placeholder="Email"
          value={formData.email}
          onChange={handleChange}
          required
          disabled={loading}
        />
        <input
          type="password"
          name="password"
          placeholder="Password"
          value={formData.password}
          onChange={handleChange}
          required
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
      <p>Don't have an account? <a href="/register">Register</a></p>
    </div>
  );
}