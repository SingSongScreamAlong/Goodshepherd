/**
 * Authentication hook and context
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import * as authService from '../services/authService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Initialize auth state from storage
  useEffect(() => {
    const initAuth = async () => {
      try {
        if (authService.isAuthenticated()) {
          const storedUser = authService.getStoredUser();
          if (storedUser) {
            setUser(storedUser);
          }
          // Verify token is still valid
          try {
            const currentUser = await authService.getCurrentUser();
            setUser(currentUser);
          } catch {
            // Token invalid, clear auth
            authService.clearAuth();
            setUser(null);
          }
        }
      } catch (err) {
        console.error('Auth initialization error:', err);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = useCallback(async (email, password) => {
    setError(null);
    try {
      const { user: userData } = await authService.login(email, password);
      setUser(userData);
      return userData;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  const register = useCallback(async (email, password, name) => {
    setError(null);
    try {
      const userData = await authService.register(email, password, name);
      // Auto-login after registration
      await login(email, password);
      return userData;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [login]);

  const logout = useCallback(() => {
    authService.logout();
    setUser(null);
    setError(null);
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const userData = await authService.getCurrentUser();
      setUser(userData);
      return userData;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  const requestPasswordReset = useCallback(async (email) => {
    setError(null);
    try {
      return await authService.requestPasswordReset(email);
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  const confirmPasswordReset = useCallback(async (token, newPassword) => {
    setError(null);
    try {
      return await authService.confirmPasswordReset(token, newPassword);
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  const verifyEmail = useCallback(async (token) => {
    setError(null);
    try {
      const result = await authService.verifyEmail(token);
      await refreshUser();
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [refreshUser]);

  const resendVerification = useCallback(async () => {
    setError(null);
    try {
      return await authService.resendVerificationEmail();
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  const changePassword = useCallback(async (currentPassword, newPassword) => {
    setError(null);
    try {
      return await authService.changePassword(currentPassword, newPassword);
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  const value = {
    user,
    loading,
    error,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    refreshUser,
    requestPasswordReset,
    confirmPasswordReset,
    verifyEmail,
    resendVerification,
    changePassword,
    clearError: () => setError(null),
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default useAuth;
