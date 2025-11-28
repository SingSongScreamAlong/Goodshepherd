/**
 * One-Tap Check-In Page
 * Quick safety check-in for missionaries
 */

import React, { useState, useEffect } from 'react';
import { queueAction, isOnline, getSetting, saveSetting } from '../../services/offlineStorage';

/**
 * Status option button
 */
function StatusOption({ status, icon, label, selected, onClick, color }) {
  return (
    <button
      className={`status-option ${selected ? 'selected' : ''}`}
      onClick={() => onClick(status)}
      style={{
        '--status-color': color,
        borderColor: selected ? color : '#e5e7eb',
        backgroundColor: selected ? `${color}15` : 'white',
      }}
    >
      <span className="status-icon">{icon}</span>
      <span className="status-label">{label}</span>
    </button>
  );
}

/**
 * Location display
 */
function LocationDisplay({ location, loading, error, onRetry }) {
  if (loading) {
    return (
      <div className="location-display loading">
        <span className="location-icon">📍</span>
        <span>Getting location...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="location-display error">
        <span className="location-icon">⚠️</span>
        <span>Location unavailable</span>
        <button className="retry-btn" onClick={onRetry}>Retry</button>
      </div>
    );
  }

  if (location) {
    return (
      <div className="location-display success">
        <span className="location-icon">📍</span>
        <span>
          {location.lat.toFixed(4)}, {location.lon.toFixed(4)}
        </span>
      </div>
    );
  }

  return null;
}

/**
 * Check-in history item
 */
function CheckInHistoryItem({ checkIn }) {
  const statusColors = {
    safe: '#22c55e',
    caution: '#f59e0b',
    help: '#dc2626',
  };

  return (
    <div className="history-item">
      <div
        className="history-status"
        style={{ backgroundColor: statusColors[checkIn.status] || '#6b7280' }}
      />
      <div className="history-content">
        <span className="history-time">
          {new Date(checkIn.timestamp).toLocaleString()}
        </span>
        {checkIn.note && (
          <span className="history-note">{checkIn.note}</span>
        )}
        {!checkIn.synced && (
          <span className="history-pending">⏳ Pending sync</span>
        )}
      </div>
    </div>
  );
}

/**
 * Main Check-In Page Component
 */
export default function CheckInPage({ onComplete }) {
  const [status, setStatus] = useState('safe');
  const [note, setNote] = useState('');
  const [location, setLocation] = useState(null);
  const [locationLoading, setLocationLoading] = useState(false);
  const [locationError, setLocationError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [history, setHistory] = useState([]);
  const [online] = useState(isOnline());

  // Load check-in history
  useEffect(() => {
    const loadHistory = async () => {
      const stored = await getSetting('checkInHistory', []);
      setHistory(stored.slice(0, 10));
    };
    loadHistory();
  }, []);

  // Get location
  const getLocation = () => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation not supported');
      return;
    }

    setLocationLoading(true);
    setLocationError(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          lat: position.coords.latitude,
          lon: position.coords.longitude,
          accuracy: position.coords.accuracy,
        });
        setLocationLoading(false);
      },
      (error) => {
        setLocationError(error.message);
        setLocationLoading(false);
      },
      {
        enableHighAccuracy: false,
        timeout: 10000,
        maximumAge: 60000,
      }
    );
  };

  // Auto-get location on mount
  useEffect(() => {
    getLocation();
  }, []);

  // Handle check-in submission
  const handleSubmit = async () => {
    setSubmitting(true);

    const checkInData = {
      type: 'CHECK_IN',
      status,
      note: note.trim() || null,
      location,
      timestamp: new Date().toISOString(),
      synced: false,
    };

    try {
      if (online) {
        const response = await fetch('/api/checkin', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(checkInData),
        });

        if (response.ok) {
          checkInData.synced = true;
        }
      }

      if (!checkInData.synced) {
        await queueAction(checkInData);
      }

      // Save to history
      const newHistory = [checkInData, ...history].slice(0, 20);
      await saveSetting('checkInHistory', newHistory);
      setHistory(newHistory);

      // Save last check-in time
      localStorage.setItem('lastCheckIn', checkInData.timestamp);

      setSubmitted(true);

      // Auto-close after delay
      setTimeout(() => {
        if (onComplete) onComplete();
      }, 2000);

    } catch (err) {
      console.error('Check-in failed:', err);
      // Still queue for later
      await queueAction(checkInData);
      setSubmitted(true);
    } finally {
      setSubmitting(false);
    }
  };

  // Success screen
  if (submitted) {
    return (
      <div className="checkin-page success-screen">
        <style>{styles}</style>
        <div className="success-content">
          <div className="success-icon">✓</div>
          <h1 className="success-title">Check-In Recorded</h1>
          <p className="success-message">
            {online
              ? 'Your status has been sent to your coordinator.'
              : 'Your check-in will be synced when you\'re back online.'}
          </p>
          <button className="done-btn" onClick={onComplete}>
            Done
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="checkin-page">
      <style>{styles}</style>

      <header className="checkin-header">
        <h1>Safety Check-In</h1>
        <p>Let your team know you're okay</p>
      </header>

      <main className="checkin-content">
        {/* Status selection */}
        <section className="status-section">
          <h2>How are you?</h2>
          <div className="status-options">
            <StatusOption
              status="safe"
              icon="✓"
              label="I'm Safe"
              color="#22c55e"
              selected={status === 'safe'}
              onClick={setStatus}
            />
            <StatusOption
              status="caution"
              icon="⚠️"
              label="Caution"
              color="#f59e0b"
              selected={status === 'caution'}
              onClick={setStatus}
            />
            <StatusOption
              status="help"
              icon="🆘"
              label="Need Help"
              color="#dc2626"
              selected={status === 'help'}
              onClick={setStatus}
            />
          </div>
        </section>

        {/* Location */}
        <section className="location-section">
          <h2>Location</h2>
          <LocationDisplay
            location={location}
            loading={locationLoading}
            error={locationError}
            onRetry={getLocation}
          />
        </section>

        {/* Optional note */}
        <section className="note-section">
          <h2>Add a note (optional)</h2>
          <textarea
            className="note-input"
            placeholder="Any additional information..."
            value={note}
            onChange={(e) => setNote(e.target.value)}
            maxLength={500}
            rows={3}
          />
        </section>

        {/* Submit button */}
        <button
          className={`submit-btn ${status}`}
          onClick={handleSubmit}
          disabled={submitting}
        >
          {submitting ? 'Sending...' : 'Send Check-In'}
        </button>

        {!online && (
          <p className="offline-notice">
            📴 You're offline. Check-in will be sent when connected.
          </p>
        )}

        {/* History */}
        {history.length > 0 && (
          <section className="history-section">
            <h2>Recent Check-Ins</h2>
            <div className="history-list">
              {history.slice(0, 5).map((item, i) => (
                <CheckInHistoryItem key={i} checkIn={item} />
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

const styles = `
  .checkin-page {
    min-height: 100vh;
    background: #f9fafb;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }

  .checkin-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
    color: white;
    padding: 24px 20px;
    padding-top: max(24px, env(safe-area-inset-top));
    text-align: center;
  }

  .checkin-header h1 {
    margin: 0 0 8px 0;
    font-size: 1.5rem;
    font-weight: 600;
  }

  .checkin-header p {
    margin: 0;
    opacity: 0.9;
    font-size: 0.9375rem;
  }

  .checkin-content {
    padding: 20px;
    padding-bottom: max(20px, env(safe-area-inset-bottom));
  }

  .checkin-content section {
    margin-bottom: 24px;
  }

  .checkin-content h2 {
    margin: 0 0 12px 0;
    font-size: 0.875rem;
    font-weight: 600;
    color: #374151;
  }

  /* Status options */
  .status-options {
    display: flex;
    gap: 12px;
  }

  .status-option {
    flex: 1;
    padding: 20px 12px;
    background: white;
    border: 2px solid #e5e7eb;
    border-radius: 12px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .status-option.selected {
    border-width: 3px;
  }

  .status-icon {
    font-size: 2rem;
  }

  .status-label {
    font-size: 0.875rem;
    font-weight: 500;
  }

  /* Location */
  .location-display {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    background: white;
    border-radius: 8px;
    font-size: 0.875rem;
  }

  .location-display.loading {
    color: #6b7280;
  }

  .location-display.error {
    color: #dc2626;
    background: #fee2e2;
  }

  .location-display.success {
    color: #16a34a;
    background: #dcfce7;
  }

  .retry-btn {
    margin-left: auto;
    padding: 4px 12px;
    background: white;
    border: 1px solid #dc2626;
    border-radius: 4px;
    color: #dc2626;
    font-size: 0.75rem;
    cursor: pointer;
  }

  /* Note input */
  .note-input {
    width: 100%;
    padding: 12px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 0.9375rem;
    resize: none;
    font-family: inherit;
  }

  .note-input:focus {
    outline: none;
    border-color: #3b82f6;
  }

  /* Submit button */
  .submit-btn {
    width: 100%;
    padding: 18px;
    border: none;
    border-radius: 12px;
    font-size: 1.125rem;
    font-weight: 600;
    color: white;
    cursor: pointer;
    transition: all 0.2s;
  }

  .submit-btn.safe {
    background: #22c55e;
  }

  .submit-btn.caution {
    background: #f59e0b;
  }

  .submit-btn.help {
    background: #dc2626;
  }

  .submit-btn:disabled {
    opacity: 0.7;
  }

  .submit-btn:active {
    transform: scale(0.98);
  }

  .offline-notice {
    text-align: center;
    margin-top: 12px;
    font-size: 0.875rem;
    color: #6b7280;
  }

  /* History */
  .history-section {
    margin-top: 32px;
    padding-top: 24px;
    border-top: 1px solid #e5e7eb;
  }

  .history-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .history-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px;
    background: white;
    border-radius: 8px;
  }

  .history-status {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-top: 4px;
  }

  .history-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .history-time {
    font-size: 0.875rem;
    color: #374151;
  }

  .history-note {
    font-size: 0.8125rem;
    color: #6b7280;
  }

  .history-pending {
    font-size: 0.75rem;
    color: #f59e0b;
  }

  /* Success screen */
  .success-screen {
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  }

  .success-content {
    text-align: center;
    color: white;
    padding: 40px;
  }

  .success-icon {
    width: 80px;
    height: 80px;
    background: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 3rem;
    color: #22c55e;
    margin: 0 auto 24px;
  }

  .success-title {
    margin: 0 0 12px 0;
    font-size: 1.5rem;
    font-weight: 600;
  }

  .success-message {
    margin: 0 0 24px 0;
    opacity: 0.9;
  }

  .done-btn {
    padding: 12px 32px;
    background: white;
    border: none;
    border-radius: 8px;
    color: #16a34a;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
  }
`;
