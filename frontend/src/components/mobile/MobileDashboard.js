/**
 * Mobile-Optimized Missionary Dashboard
 * Designed for low-bandwidth, offline-first operation
 */

import React, { useState, useEffect, useCallback } from 'react';
import { getEvents, saveEvents, isOnline, queueAction, getUnacknowledgedAlerts } from '../../services/offlineStorage';

// Threat level colors
const THREAT_COLORS = {
  critical: '#dc2626',
  high: '#ea580c',
  medium: '#ca8a04',
  low: '#16a34a',
  minimal: '#6b7280',
};

/**
 * Connection status indicator
 */
function ConnectionStatus({ online }) {
  return (
    <div className={`connection-status ${online ? 'online' : 'offline'}`}>
      <span className="status-dot" />
      <span className="status-text">{online ? 'Online' : 'Offline'}</span>
    </div>
  );
}

/**
 * Quick check-in button
 */
function CheckInButton({ onCheckIn, lastCheckIn, loading }) {
  const timeSinceCheckIn = lastCheckIn
    ? Math.floor((Date.now() - new Date(lastCheckIn).getTime()) / (1000 * 60 * 60))
    : null;

  return (
    <button
      className={`checkin-button ${loading ? 'loading' : ''}`}
      onClick={onCheckIn}
      disabled={loading}
    >
      <span className="checkin-icon">✓</span>
      <span className="checkin-text">
        {loading ? 'Checking in...' : 'Check In Safe'}
      </span>
      {timeSinceCheckIn !== null && (
        <span className="checkin-time">
          Last: {timeSinceCheckIn < 1 ? 'Just now' : `${timeSinceCheckIn}h ago`}
        </span>
      )}
    </button>
  );
}

/**
 * Alert card for mobile
 */
function AlertCard({ alert, onAcknowledge }) {
  const threatColor = THREAT_COLORS[alert.threat_level] || THREAT_COLORS.minimal;

  return (
    <div className="alert-card" style={{ borderLeftColor: threatColor }}>
      <div className="alert-header">
        <span className="alert-threat" style={{ backgroundColor: threatColor }}>
          {alert.threat_level?.toUpperCase()}
        </span>
        <span className="alert-time">
          {new Date(alert.timestamp || alert.fetched_at).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </span>
      </div>
      <h3 className="alert-title">{alert.title}</h3>
      <p className="alert-summary">
        {alert.summary?.substring(0, 120)}
        {alert.summary?.length > 120 ? '...' : ''}
      </p>
      <div className="alert-footer">
        <span className="alert-region">📍 {alert.region || 'Unknown'}</span>
        {onAcknowledge && (
          <button className="alert-ack-btn" onClick={() => onAcknowledge(alert.id)}>
            Got it
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Daily brief section
 */
function DailyBrief({ events, region }) {
  const criticalCount = events.filter(e => e.threat_level === 'critical').length;
  const highCount = events.filter(e => e.threat_level === 'high').length;
  const totalCount = events.length;

  return (
    <div className="daily-brief">
      <h2 className="brief-title">📋 Daily Brief</h2>
      <div className="brief-stats">
        <div className="stat-item critical">
          <span className="stat-value">{criticalCount}</span>
          <span className="stat-label">Critical</span>
        </div>
        <div className="stat-item high">
          <span className="stat-value">{highCount}</span>
          <span className="stat-label">High</span>
        </div>
        <div className="stat-item total">
          <span className="stat-value">{totalCount}</span>
          <span className="stat-label">Total</span>
        </div>
      </div>
      {region && (
        <p className="brief-region">Monitoring: {region}</p>
      )}
    </div>
  );
}

/**
 * Emergency contacts section
 */
function EmergencyContacts({ contacts }) {
  const defaultContacts = contacts || [
    { name: 'Emergency Line', number: '+1-800-555-0100', type: 'emergency' },
    { name: 'Regional Coordinator', number: '+1-800-555-0101', type: 'coordinator' },
    { name: 'Local Embassy', number: '+1-800-555-0102', type: 'embassy' },
  ];

  return (
    <div className="emergency-contacts">
      <h3 className="contacts-title">🆘 Emergency Contacts</h3>
      <div className="contacts-list">
        {defaultContacts.map((contact, i) => (
          <a
            key={i}
            href={`tel:${contact.number}`}
            className={`contact-item ${contact.type}`}
          >
            <span className="contact-name">{contact.name}</span>
            <span className="contact-number">{contact.number}</span>
          </a>
        ))}
      </div>
    </div>
  );
}

/**
 * Main Mobile Dashboard Component
 */
export default function MobileDashboard({ userRegion = null }) {
  const [online, setOnline] = useState(isOnline());
  const [events, setEvents] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [checkingIn, setCheckingIn] = useState(false);
  const [lastCheckIn, setLastCheckIn] = useState(null);
  const [activeTab, setActiveTab] = useState('alerts');

  // Monitor online status
  useEffect(() => {
    const handleOnline = () => setOnline(true);
    const handleOffline = () => setOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Load data
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // Get cached events
      const cachedEvents = await getEvents({
        region: userRegion,
        limit: 50,
      });
      setEvents(cachedEvents);

      // Get unacknowledged alerts
      const unackAlerts = await getUnacknowledgedAlerts();
      setAlerts(unackAlerts);

      // If online, fetch fresh data
      if (online) {
        try {
          const response = await fetch('/api/events/recent?limit=50');
          if (response.ok) {
            const freshEvents = await response.json();
            setEvents(freshEvents.events || []);
            await saveEvents(freshEvents.events || []);
          }
        } catch (err) {
          console.log('Using cached data');
        }
      }
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  }, [online, userRegion]);

  useEffect(() => {
    loadData();
    // Load last check-in time
    const stored = localStorage.getItem('lastCheckIn');
    if (stored) setLastCheckIn(stored);
  }, [loadData]);

  // Handle check-in
  const handleCheckIn = async () => {
    setCheckingIn(true);
    const checkInData = {
      type: 'CHECK_IN',
      timestamp: new Date().toISOString(),
      location: null, // Could add geolocation
      status: 'safe',
    };

    try {
      if (online) {
        await fetch('/api/checkin', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(checkInData),
        });
      } else {
        // Queue for later sync
        await queueAction(checkInData);
      }

      const now = new Date().toISOString();
      setLastCheckIn(now);
      localStorage.setItem('lastCheckIn', now);
    } catch (err) {
      // Queue for later even if request fails
      await queueAction(checkInData);
      const now = new Date().toISOString();
      setLastCheckIn(now);
      localStorage.setItem('lastCheckIn', now);
    } finally {
      setCheckingIn(false);
    }
  };

  // Handle alert acknowledgment
  const handleAcknowledge = async (alertId) => {
    setAlerts(prev => prev.filter(a => a.id !== alertId));
    // Would also update IndexedDB
  };

  // Filter events by threat level for display
  const criticalEvents = events.filter(e => 
    e.threat_level === 'critical' || e.threat_level === 'high'
  ).slice(0, 10);

  return (
    <div className="mobile-dashboard">
      <style>{`
        .mobile-dashboard {
          display: flex;
          flex-direction: column;
          min-height: 100vh;
          background: #f9fafb;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          -webkit-font-smoothing: antialiased;
        }

        /* Header */
        .mobile-header {
          position: sticky;
          top: 0;
          z-index: 100;
          background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
          color: white;
          padding: 16px;
          padding-top: max(16px, env(safe-area-inset-top));
        }

        .header-top {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .app-title {
          font-size: 1.25rem;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .connection-status {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          border-radius: 12px;
          font-size: 0.75rem;
          background: rgba(255, 255, 255, 0.1);
        }

        .connection-status.online .status-dot {
          background: #22c55e;
        }

        .connection-status.offline .status-dot {
          background: #ef4444;
        }

        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }

        /* Check-in button */
        .checkin-button {
          width: 100%;
          padding: 16px;
          background: #22c55e;
          border: none;
          border-radius: 12px;
          color: white;
          font-size: 1.125rem;
          font-weight: 600;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
          cursor: pointer;
          transition: all 0.2s;
          box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
        }

        .checkin-button:active {
          transform: scale(0.98);
        }

        .checkin-button.loading {
          background: #86efac;
        }

        .checkin-icon {
          font-size: 1.5rem;
        }

        .checkin-time {
          font-size: 0.75rem;
          opacity: 0.9;
        }

        /* Tab navigation */
        .tab-nav {
          display: flex;
          background: white;
          border-bottom: 1px solid #e5e7eb;
          position: sticky;
          top: 0;
          z-index: 50;
        }

        .tab-btn {
          flex: 1;
          padding: 14px;
          background: none;
          border: none;
          border-bottom: 3px solid transparent;
          font-size: 0.875rem;
          color: #6b7280;
          cursor: pointer;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
        }

        .tab-btn.active {
          color: #1e3a5f;
          border-bottom-color: #1e3a5f;
          font-weight: 500;
        }

        .tab-icon {
          font-size: 1.25rem;
        }

        .tab-badge {
          background: #dc2626;
          color: white;
          font-size: 0.625rem;
          padding: 2px 6px;
          border-radius: 10px;
          position: absolute;
          top: 8px;
          right: calc(50% - 20px);
        }

        /* Content area */
        .content-area {
          flex: 1;
          padding: 16px;
          padding-bottom: max(16px, env(safe-area-inset-bottom));
        }

        /* Daily brief */
        .daily-brief {
          background: white;
          border-radius: 12px;
          padding: 16px;
          margin-bottom: 16px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .brief-title {
          margin: 0 0 12px 0;
          font-size: 1rem;
          font-weight: 600;
        }

        .brief-stats {
          display: flex;
          gap: 12px;
        }

        .stat-item {
          flex: 1;
          text-align: center;
          padding: 12px;
          border-radius: 8px;
          background: #f3f4f6;
        }

        .stat-item.critical {
          background: #fee2e2;
        }

        .stat-item.high {
          background: #ffedd5;
        }

        .stat-value {
          display: block;
          font-size: 1.5rem;
          font-weight: 600;
        }

        .stat-label {
          font-size: 0.75rem;
          color: #6b7280;
        }

        .brief-region {
          margin: 12px 0 0 0;
          font-size: 0.875rem;
          color: #6b7280;
        }

        /* Alert cards */
        .alerts-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .alert-card {
          background: white;
          border-radius: 12px;
          padding: 14px;
          border-left: 4px solid #6b7280;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .alert-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .alert-threat {
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 0.625rem;
          font-weight: 600;
          color: white;
        }

        .alert-time {
          font-size: 0.75rem;
          color: #6b7280;
        }

        .alert-title {
          margin: 0 0 8px 0;
          font-size: 0.9375rem;
          font-weight: 500;
          line-height: 1.4;
        }

        .alert-summary {
          margin: 0 0 12px 0;
          font-size: 0.8125rem;
          color: #4b5563;
          line-height: 1.5;
        }

        .alert-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .alert-region {
          font-size: 0.75rem;
          color: #6b7280;
        }

        .alert-ack-btn {
          padding: 6px 12px;
          background: #e0e7ff;
          border: none;
          border-radius: 6px;
          color: #3730a3;
          font-size: 0.75rem;
          font-weight: 500;
          cursor: pointer;
        }

        /* Emergency contacts */
        .emergency-contacts {
          background: white;
          border-radius: 12px;
          padding: 16px;
          margin-top: 16px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .contacts-title {
          margin: 0 0 12px 0;
          font-size: 1rem;
          font-weight: 600;
        }

        .contacts-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .contact-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px;
          background: #f9fafb;
          border-radius: 8px;
          text-decoration: none;
          color: inherit;
        }

        .contact-item.emergency {
          background: #fee2e2;
        }

        .contact-name {
          font-weight: 500;
          font-size: 0.875rem;
        }

        .contact-number {
          color: #3b82f6;
          font-size: 0.875rem;
        }

        /* Loading state */
        .loading-state {
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 40px;
          color: #6b7280;
        }

        /* Empty state */
        .empty-state {
          text-align: center;
          padding: 40px 20px;
          color: #6b7280;
        }

        .empty-icon {
          font-size: 3rem;
          margin-bottom: 12px;
        }

        /* Pull to refresh indicator */
        .refresh-indicator {
          text-align: center;
          padding: 12px;
          color: #6b7280;
          font-size: 0.875rem;
        }
      `}</style>

      {/* Header */}
      <header className="mobile-header">
        <div className="header-top">
          <h1 className="app-title">
            <span>🛡️</span>
            <span>Good Shepherd</span>
          </h1>
          <ConnectionStatus online={online} />
        </div>
        <CheckInButton
          onCheckIn={handleCheckIn}
          lastCheckIn={lastCheckIn}
          loading={checkingIn}
        />
      </header>

      {/* Tab Navigation */}
      <nav className="tab-nav">
        <button
          className={`tab-btn ${activeTab === 'alerts' ? 'active' : ''}`}
          onClick={() => setActiveTab('alerts')}
          style={{ position: 'relative' }}
        >
          <span className="tab-icon">🔔</span>
          <span>Alerts</span>
          {alerts.length > 0 && (
            <span className="tab-badge">{alerts.length}</span>
          )}
        </button>
        <button
          className={`tab-btn ${activeTab === 'brief' ? 'active' : ''}`}
          onClick={() => setActiveTab('brief')}
        >
          <span className="tab-icon">📋</span>
          <span>Brief</span>
        </button>
        <button
          className={`tab-btn ${activeTab === 'contacts' ? 'active' : ''}`}
          onClick={() => setActiveTab('contacts')}
        >
          <span className="tab-icon">📞</span>
          <span>Contacts</span>
        </button>
      </nav>

      {/* Content */}
      <main className="content-area">
        {loading && (
          <div className="loading-state">Loading...</div>
        )}

        {!loading && activeTab === 'alerts' && (
          <>
            {alerts.length > 0 && (
              <div className="alerts-list" style={{ marginBottom: 16 }}>
                <h3 style={{ margin: '0 0 12px', fontSize: '0.875rem', color: '#dc2626' }}>
                  ⚠️ Unacknowledged Alerts
                </h3>
                {alerts.map(alert => (
                  <AlertCard
                    key={alert.id}
                    alert={alert}
                    onAcknowledge={handleAcknowledge}
                  />
                ))}
              </div>
            )}

            <h3 style={{ margin: '0 0 12px', fontSize: '0.875rem', color: '#6b7280' }}>
              Recent High-Priority Events
            </h3>
            <div className="alerts-list">
              {criticalEvents.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">✅</div>
                  <p>No critical alerts in your region</p>
                </div>
              ) : (
                criticalEvents.map(event => (
                  <AlertCard key={event.id} alert={event} />
                ))
              )}
            </div>
          </>
        )}

        {!loading && activeTab === 'brief' && (
          <>
            <DailyBrief events={events} region={userRegion} />
            <h3 style={{ margin: '16px 0 12px', fontSize: '0.875rem', color: '#6b7280' }}>
              All Recent Events
            </h3>
            <div className="alerts-list">
              {events.slice(0, 20).map(event => (
                <AlertCard key={event.id} alert={event} />
              ))}
            </div>
          </>
        )}

        {!loading && activeTab === 'contacts' && (
          <EmergencyContacts />
        )}
      </main>
    </div>
  );
}
