import React, { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import './Auth.css';

export function LoginForm({ onSuccess, onRegisterClick, onForgotPasswordClick }) {
  const { login, error, clearError } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!email || !password) {
      setLocalError('Please enter email and password');
      return;
    }

    setLoading(true);
    try {
      await login(email, password);
      onSuccess?.();
    } catch (err) {
      setLocalError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-form-container">
      <h2>Sign In</h2>
      <p className="auth-subtitle">Welcome back to Good Shepherd</p>

      <form onSubmit={handleSubmit} className="auth-form">
        {(localError || error) && (
          <div className="auth-error">{localError || error}</div>
        )}

        <div className="auth-field">
          <label htmlFor="login-email">Email</label>
          <input
            id="login-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            autoComplete="email"
            disabled={loading}
            required
          />
        </div>

        <div className="auth-field">
          <label htmlFor="login-password">Password</label>
          <input
            id="login-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            autoComplete="current-password"
            disabled={loading}
            required
          />
        </div>

        <button type="submit" className="auth-button primary" disabled={loading}>
          {loading ? 'Signing in...' : 'Sign In'}
        </button>

        <div className="auth-links">
          <button
            type="button"
            className="auth-link"
            onClick={onForgotPasswordClick}
          >
            Forgot password?
          </button>
        </div>

        <div className="auth-divider">
          <span>Don't have an account?</span>
        </div>

        <button
          type="button"
          className="auth-button secondary"
          onClick={onRegisterClick}
        >
          Create Account
        </button>
      </form>
    </div>
  );
}

export default LoginForm;
