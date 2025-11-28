import React, { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import './Auth.css';

export function ForgotPasswordForm({ onSuccess, onBackClick }) {
  const { requestPasswordReset, error, clearError } = useAuth();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!email) {
      setLocalError('Please enter your email address');
      return;
    }

    setLoading(true);
    try {
      await requestPasswordReset(email);
      setSubmitted(true);
      onSuccess?.();
    } catch (err) {
      setLocalError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="auth-form-container">
        <div className="auth-success-icon">✓</div>
        <h2>Check Your Email</h2>
        <p className="auth-subtitle">
          If an account exists for <strong>{email}</strong>, we've sent password reset instructions.
        </p>
        <p className="auth-hint">
          Didn't receive the email? Check your spam folder or try again.
        </p>
        <button
          type="button"
          className="auth-button secondary"
          onClick={onBackClick}
        >
          Back to Sign In
        </button>
      </div>
    );
  }

  return (
    <div className="auth-form-container">
      <h2>Reset Password</h2>
      <p className="auth-subtitle">
        Enter your email and we'll send you instructions to reset your password.
      </p>

      <form onSubmit={handleSubmit} className="auth-form">
        {(localError || error) && (
          <div className="auth-error">{localError || error}</div>
        )}

        <div className="auth-field">
          <label htmlFor="reset-email">Email</label>
          <input
            id="reset-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            autoComplete="email"
            disabled={loading}
            required
          />
        </div>

        <button type="submit" className="auth-button primary" disabled={loading}>
          {loading ? 'Sending...' : 'Send Reset Link'}
        </button>

        <button
          type="button"
          className="auth-button secondary"
          onClick={onBackClick}
        >
          Back to Sign In
        </button>
      </form>
    </div>
  );
}

export default ForgotPasswordForm;
