import React, { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import './Auth.css';

export function RegisterForm({ onSuccess, onLoginClick }) {
  const { register, error, clearError } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState(null);

  const validatePassword = (pwd) => {
    if (pwd.length < 8) {
      return 'Password must be at least 8 characters';
    }
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!email || !password) {
      setLocalError('Please fill in all required fields');
      return;
    }

    const passwordError = validatePassword(password);
    if (passwordError) {
      setLocalError(passwordError);
      return;
    }

    if (password !== confirmPassword) {
      setLocalError('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      await register(email, password, name || null);
      onSuccess?.();
    } catch (err) {
      setLocalError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-form-container">
      <h2>Create Account</h2>
      <p className="auth-subtitle">Join Good Shepherd for situational awareness</p>

      <form onSubmit={handleSubmit} className="auth-form">
        {(localError || error) && (
          <div className="auth-error">{localError || error}</div>
        )}

        <div className="auth-field">
          <label htmlFor="register-name">Name (optional)</label>
          <input
            id="register-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Your name"
            autoComplete="name"
            disabled={loading}
          />
        </div>

        <div className="auth-field">
          <label htmlFor="register-email">Email *</label>
          <input
            id="register-email"
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
          <label htmlFor="register-password">Password *</label>
          <input
            id="register-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="At least 8 characters"
            autoComplete="new-password"
            disabled={loading}
            required
          />
        </div>

        <div className="auth-field">
          <label htmlFor="register-confirm">Confirm Password *</label>
          <input
            id="register-confirm"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Repeat password"
            autoComplete="new-password"
            disabled={loading}
            required
          />
        </div>

        <button type="submit" className="auth-button primary" disabled={loading}>
          {loading ? 'Creating account...' : 'Create Account'}
        </button>

        <div className="auth-divider">
          <span>Already have an account?</span>
        </div>

        <button
          type="button"
          className="auth-button secondary"
          onClick={onLoginClick}
        >
          Sign In
        </button>
      </form>
    </div>
  );
}

export default RegisterForm;
