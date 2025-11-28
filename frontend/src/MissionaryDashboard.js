import React, { useState, useEffect, useCallback } from 'react';

function MissionaryDashboard() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    try {
      if (isOnline) {
        const response = await fetch('http://localhost:3001/api/rss');
        const data = await response.json();
        if (data.success) {
          const processedAlerts = data.data.map(item => ({
            ...item,
            severity: item.ai_threat_level || assessSeverity(item.title + ' ' + item.contentSnippet) // Use AI if available
          }));
          setAlerts(processedAlerts);
          localStorage.setItem('alerts', JSON.stringify(processedAlerts)); // Cache for offline
        } else {
          setError('Failed to fetch alerts');
        }
      } else {
        // Load from cache
        const cached = localStorage.getItem('alerts');
        if (cached) {
          setAlerts(JSON.parse(cached));
        } else {
          setError('No cached alerts available');
        }
      }
    } catch (err) {
      setError('Error fetching alerts: ' + err.message);
    } finally {
      setLoading(false);
    }
  }, [isOnline]);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    fetchAlerts();

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [fetchAlerts]);

  const assessSeverity = (text) => {
    const threatWords = ['crisis', 'attack', 'violence', 'emergency', 'threat', 'danger'];
    const lowerText = text.toLowerCase();
    const matches = threatWords.filter(word => lowerText.includes(word));
    return matches.length > 0 ? 'high' : 'low';
  };

  const sendSMS = () => {
    console.log('SMS alert sent to missionary contacts');
    // For MVP, just log. In production, integrate with SMS API
  };

  const checkIn = () => {
    console.log('Missionary checked in at', new Date().toLocaleString());
    // For MVP, just log. In production, send location or status to backend
  };

  const highAlerts = alerts.filter(alert => alert.severity === 'high');

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '600px', margin: '0 auto' }}>
      <h1>Good Shepherd - Missionary Alerts</h1>
      <p style={{ color: isOnline ? 'green' : 'red' }}>
        Status: {isOnline ? 'Online' : 'Offline'}
      </p>
      {loading && <p>Loading alerts...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {highAlerts.length > 0 && (
        <div>
          <h2>High Severity Alerts</h2>
          {highAlerts.map((alert, index) => (
            <div key={index} style={{ border: '1px solid #ccc', padding: '10px', margin: '10px 0', borderRadius: '5px' }}>
              <h3>{alert.title}</h3>
              <p>{alert.contentSnippet}</p>
              <p><strong>Source:</strong> {alert.source}</p>
              <p><strong>Published:</strong> {new Date(alert.pubDate).toLocaleString()}</p>
            </div>
          ))}
          <button onClick={sendSMS} style={{ backgroundColor: '#ff4444', color: 'white', padding: '10px', border: 'none', borderRadius: '5px', width: '100%', fontSize: '16px', marginBottom: '10px' }}>
            Send SMS Alert
          </button>
          <button onClick={checkIn} style={{ backgroundColor: '#4CAF50', color: 'white', padding: '10px', border: 'none', borderRadius: '5px', width: '100%', fontSize: '16px' }}>
            Check In
          </button>
        </div>
      )}
      {highAlerts.length === 0 && !loading && <p>No high severity alerts at this time.</p>}
    </div>
  );
}

export default MissionaryDashboard;
