import React from 'react';
import { useAuth } from '../../hooks/useAuth';

/**
 * Protected route component that requires authentication
 * and optionally specific roles.
 */
export function ProtectedRoute({
  children,
  requiredRoles = [],
  fallback = null,
  onUnauthorized = null,
}) {
  const { isAuthenticated, user, loading } = useAuth();

  // Show loading state
  if (loading) {
    return (
      <div className="protected-route-loading">
        <div className="loading-spinner" />
        <p>Loading...</p>
      </div>
    );
  }

  // Not authenticated
  if (!isAuthenticated) {
    if (onUnauthorized) {
      onUnauthorized('unauthenticated');
    }
    return fallback || (
      <div className="protected-route-unauthorized">
        <h2>Authentication Required</h2>
        <p>Please sign in to access this content.</p>
      </div>
    );
  }

  // Check roles if required
  if (requiredRoles.length > 0) {
    const userRoles = user?.roles || [];
    const hasRequiredRole = requiredRoles.some(role => 
      userRoles.includes(role) || userRoles.includes('admin')
    );

    if (!hasRequiredRole) {
      if (onUnauthorized) {
        onUnauthorized('forbidden');
      }
      return fallback || (
        <div className="protected-route-forbidden">
          <h2>Access Denied</h2>
          <p>You don't have permission to access this content.</p>
          <p className="required-roles">
            Required role: {requiredRoles.join(' or ')}
          </p>
        </div>
      );
    }
  }

  return children;
}

/**
 * Higher-order component for protecting components
 */
export function withAuth(WrappedComponent, options = {}) {
  return function AuthenticatedComponent(props) {
    return (
      <ProtectedRoute {...options}>
        <WrappedComponent {...props} />
      </ProtectedRoute>
    );
  };
}

/**
 * Hook for checking permissions in components
 */
export function usePermissions() {
  const { user, isAuthenticated } = useAuth();
  const userRoles = user?.roles || [];

  const hasRole = (role) => {
    if (!isAuthenticated) return false;
    return userRoles.includes(role) || userRoles.includes('admin');
  };

  const hasAnyRole = (roles) => {
    if (!isAuthenticated) return false;
    return roles.some(role => hasRole(role));
  };

  const hasAllRoles = (roles) => {
    if (!isAuthenticated) return false;
    return roles.every(role => hasRole(role));
  };

  const isAdmin = () => hasRole('admin');
  const isAnalyst = () => hasAnyRole(['admin', 'analyst']);
  const isOperator = () => hasAnyRole(['admin', 'analyst', 'operator']);
  const isViewer = () => hasAnyRole(['admin', 'analyst', 'operator', 'viewer']);

  return {
    hasRole,
    hasAnyRole,
    hasAllRoles,
    isAdmin,
    isAnalyst,
    isOperator,
    isViewer,
    roles: userRoles,
  };
}

export default ProtectedRoute;
