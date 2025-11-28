import React, { useState, useEffect } from 'react';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';
import ForgotPasswordForm from './ForgotPasswordForm';
import ResetPasswordForm from './ResetPasswordForm';
import VerifyEmail from './VerifyEmail';
import './Auth.css';

export function AuthModal({ isOpen, onClose, initialView = 'login', token = null }) {
  const [view, setView] = useState(initialView);

  useEffect(() => {
    setView(initialView);
  }, [initialView]);

  useEffect(() => {
    // Handle escape key
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onClose?.();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSuccess = () => {
    onClose?.();
  };

  const renderContent = () => {
    switch (view) {
      case 'register':
        return (
          <RegisterForm
            onSuccess={handleSuccess}
            onLoginClick={() => setView('login')}
          />
        );
      case 'forgot-password':
        return (
          <ForgotPasswordForm
            onSuccess={() => {}}
            onBackClick={() => setView('login')}
          />
        );
      case 'reset-password':
        return (
          <ResetPasswordForm
            token={token}
            onSuccess={() => setView('login')}
            onBackClick={() => setView('login')}
          />
        );
      case 'verify-email':
        return (
          <VerifyEmail
            token={token}
            onSuccess={handleSuccess}
            onBackClick={handleSuccess}
          />
        );
      case 'login':
      default:
        return (
          <LoginForm
            onSuccess={handleSuccess}
            onRegisterClick={() => setView('register')}
            onForgotPasswordClick={() => setView('forgot-password')}
          />
        );
    }
  };

  return (
    <div className="auth-modal-overlay" onClick={onClose}>
      <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
        <button className="auth-modal-close" onClick={onClose} aria-label="Close">
          ×
        </button>
        {renderContent()}
      </div>
    </div>
  );
}

export default AuthModal;
