import React, { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import './Auth.css';

export function ResetPasswordForm({ token, onSuccess, onBackClick }) {
  const { confirmPasswordReset, error, clearError } = useAuth();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState(null);
  const [success, setSuccess] = useState(false);

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
      await confirmPasswordReset(token, password);
      setSuccess(true);
      onSuccess?.();
    } catch (err) {
      setLocalError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="auth-form-container">
        <div className="auth-success-icon">✓</div>
        <h2>Password Reset</h2>
        <p className="auth-subtitle">
          Your password has been successfully reset. You can now sign in with your new password.
        </p>
        <button
          type="button"
          className="auth-button primary"
          onClick={onBackClick}
        >
          Sign In
        </button>
      </div>
    );
  }

  if (!token) {
    return (
      <div className="auth-form-container">
        <div className="auth-error-icon">!</div>
        <h2>Invalid Link</h2>
        <p className="auth-subtitle">
          This password reset link is invalid or has expired.
        </p>
        <button
          type="button"
          className="auth-button primary"
          onClick={onBackClick}
        >
          Back to Sign In
        </button>
      </div>
    );
  }

  return (
    <div className="auth-form-container">
      <h2>Set New Password</h2>
      <p className="auth-subtitle">Enter your new password below.</p>

      <form onSubmit={handleSubmit} className="auth-form">
        {(localError || error) && (
          <div className="auth-error">{localError || error}</div>
        )}

        <div className="auth-field">
          <label htmlFor="new-password">New Password</label>
          <input
            id="new-password"
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
          <label htmlFor="confirm-new-password">Confirm Password</label>
          <input
            id="confirm-new-password"
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
          {loading ? 'Resetting...' : 'Reset Password'}
        </button>

        <button
          type="button"
          className="auth-button secondary"
          onClick={onBackClick}
        >
          Cancel
        </button>
      </form>
    </div>
  );
}

export default ResetPasswordForm;
