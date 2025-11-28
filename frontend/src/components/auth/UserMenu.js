import React, { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import './Auth.css';

export function UserMenu() {
  const { user, logout, isAuthenticated } = useAuth();
  const [showDropdown, setShowDropdown] = useState(false);

  if (!isAuthenticated) {
    return null;
  }

  const initials = user?.name
    ? user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : user?.email?.[0]?.toUpperCase() || '?';

  return (
    <div className="user-menu">
      <button
        className="user-menu-trigger"
        onClick={() => setShowDropdown(!showDropdown)}
        aria-expanded={showDropdown}
      >
        <span className="user-avatar">{initials}</span>
        <span className="user-name">{user?.name || user?.email}</span>
        <span className="user-menu-arrow">▼</span>
      </button>

      {showDropdown && (
        <>
          <div
            className="user-menu-backdrop"
            onClick={() => setShowDropdown(false)}
          />
          <div className="user-menu-dropdown">
            <div className="user-menu-header">
              <span className="user-avatar large">{initials}</span>
              <div className="user-menu-info">
                <span className="user-menu-name">{user?.name || 'User'}</span>
                <span className="user-menu-email">{user?.email}</span>
              </div>
            </div>

            <div className="user-menu-divider" />

            <div className="user-menu-roles">
              {user?.roles?.map(role => (
                <span key={role} className="user-role-badge">{role}</span>
              ))}
            </div>

            <div className="user-menu-divider" />

            <button
              className="user-menu-item"
              onClick={() => {
                setShowDropdown(false);
                // Could navigate to settings
              }}
            >
              Settings
            </button>

            <button
              className="user-menu-item danger"
              onClick={() => {
                setShowDropdown(false);
                logout();
              }}
            >
              Sign Out
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default UserMenu;
