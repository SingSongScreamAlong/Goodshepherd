import React, { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import './Auth.css';

export function VerifyEmail({ token, onSuccess, onBackClick }) {
  const { verifyEmail, error, clearError } = useAuth();
  const [loading, setLoading] = useState(true);
  const [success, setSuccess] = useState(false);
  const [localError, setLocalError] = useState(null);

  useEffect(() => {
    const verify = async () => {
      if (!token) {
        setLocalError('Invalid verification link');
        setLoading(false);
        return;
      }

      clearError();
      try {
        await verifyEmail(token);
        setSuccess(true);
        onSuccess?.();
      } catch (err) {
        setLocalError(err.message);
      } finally {
        setLoading(false);
      }
    };

    verify();
  }, [token, verifyEmail, clearError, onSuccess]);

  if (loading) {
    return (
      <div className="auth-form-container">
        <div className="auth-loading">
          <div className="auth-spinner"></div>
        </div>
        <h2>Verifying Email</h2>
        <p className="auth-subtitle">Please wait while we verify your email address...</p>
      </div>
    );
  }

  if (success) {
    return (
      <div className="auth-form-container">
        <div className="auth-success-icon">✓</div>
        <h2>Email Verified!</h2>
        <p className="auth-subtitle">
          Your email has been successfully verified. You now have full access to Good Shepherd.
        </p>
        <button
          type="button"
          className="auth-button primary"
          onClick={onBackClick}
        >
          Continue to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="auth-form-container">
      <div className="auth-error-icon">!</div>
      <h2>Verification Failed</h2>
      <p className="auth-subtitle">
        {localError || error || 'This verification link is invalid or has expired.'}
      </p>
      <button
        type="button"
        className="auth-button primary"
        onClick={onBackClick}
      >
        Back to Dashboard
      </button>
    </div>
  );
}

export default VerifyEmail;
