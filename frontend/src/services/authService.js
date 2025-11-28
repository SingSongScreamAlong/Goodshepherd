/**
 * Authentication service for API communication
 */

const API_BASE = process.env.REACT_APP_API_BASE ?? '';

// Token storage keys
const ACCESS_TOKEN_KEY = 'gs_access_token';
const REFRESH_TOKEN_KEY = 'gs_refresh_token';
const USER_KEY = 'gs_user';

/**
 * Get stored access token
 */
export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

/**
 * Get stored refresh token
 */
export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Store tokens
 */
export function setTokens(accessToken, refreshToken) {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }
}

/**
 * Clear all auth data
 */
export function clearAuth() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/**
 * Get stored user data
 */
export function getStoredUser() {
  const userData = localStorage.getItem(USER_KEY);
  return userData ? JSON.parse(userData) : null;
}

/**
 * Store user data
 */
export function setStoredUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/**
 * Make authenticated API request
 */
export async function authFetch(url, options = {}) {
  const token = getAccessToken();
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(url, {
    ...options,
    headers,
  });
  
  // If unauthorized, try to refresh token
  if (response.status === 401 && getRefreshToken()) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      // Retry with new token
      headers['Authorization'] = `Bearer ${getAccessToken()}`;
      return fetch(url, { ...options, headers });
    }
  }
  
  return response;
}

/**
 * Register a new user
 */
export async function register(email, password, name = null) {
  const response = await fetch(`${API_BASE}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Registration failed');
  }
  
  return response.json();
}

/**
 * Login user
 */
export async function login(email, password) {
  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }
  
  const data = await response.json();
  setTokens(data.access_token, data.refresh_token);
  
  // Fetch user info
  const user = await getCurrentUser();
  setStoredUser(user);
  
  return { tokens: data, user };
}

/**
 * Logout user
 */
export function logout() {
  clearAuth();
}

/**
 * Refresh access token
 */
export async function refreshAccessToken() {
  const token = getAccessToken();
  if (!token) return false;
  
  try {
    const response = await fetch(`${API_BASE}/api/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });
    
    if (!response.ok) {
      clearAuth();
      return false;
    }
    
    const data = await response.json();
    setTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    clearAuth();
    return false;
  }
}

/**
 * Get current user info
 */
export async function getCurrentUser() {
  const response = await authFetch(`${API_BASE}/api/auth/me`);
  
  if (!response.ok) {
    throw new Error('Failed to get user info');
  }
  
  const user = await response.json();
  setStoredUser(user);
  return user;
}

/**
 * Request password reset
 */
export async function requestPasswordReset(email) {
  const response = await fetch(`${API_BASE}/api/auth/password-reset/request`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Password reset request failed');
  }
  
  return response.json();
}

/**
 * Confirm password reset
 */
export async function confirmPasswordReset(token, newPassword) {
  const response = await fetch(`${API_BASE}/api/auth/password-reset/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token, new_password: newPassword }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Password reset failed');
  }
  
  return response.json();
}

/**
 * Verify email
 */
export async function verifyEmail(token) {
  const response = await fetch(`${API_BASE}/api/auth/verify-email`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Email verification failed');
  }
  
  return response.json();
}

/**
 * Resend verification email
 */
export async function resendVerificationEmail() {
  const response = await authFetch(`${API_BASE}/api/auth/resend-verification`, {
    method: 'POST',
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to resend verification email');
  }
  
  return response.json();
}

/**
 * Change password
 */
export async function changePassword(currentPassword, newPassword) {
  const response = await authFetch(`${API_BASE}/api/auth/change-password`, {
    method: 'POST',
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Password change failed');
  }
  
  return response.json();
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated() {
  return !!getAccessToken();
}
