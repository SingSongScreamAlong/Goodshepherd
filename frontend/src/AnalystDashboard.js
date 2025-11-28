import React, { useState, useEffect } from 'react';

function AnalystDashboard() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterLevel, setFilterLevel] = useState('all');
  const [actions, setActions] = useState({}); // {id: 'confirmed' | 'escalated' | 'dismissed'}

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      const response = await fetch('http://localhost:3001/api/rss');
      const data = await response.json();
      if (data.success) {
        setAlerts(data.data);
      } else {
        setError('Failed to fetch alerts');
      }
    } catch (err) {
      setError('Error fetching alerts: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = (id, action) => {
    setActions(prev => ({ ...prev, [id]: action }));
  };

  const filteredAlerts = alerts
    .filter(alert => alert.title.toLowerCase().includes(searchTerm.toLowerCase()))
    .filter(alert => filterLevel === 'all' || alert.ai_threat_level === filterLevel)
    .sort((a, b) => new Date(b.pubDate) - new Date(a.pubDate));

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Good Shepherd - Analyst Dashboard</h1>
      {loading && <p>Loading alerts...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <div style={{ marginBottom: '20px' }}>
        <input
          type="text"
          placeholder="Search alerts..."
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          style={{ padding: '10px', width: '200px', marginRight: '10px' }}
        />
        <select value={filterLevel} onChange={e => setFilterLevel(e.target.value)} style={{ padding: '10px' }}>
          <option value="all">All Levels</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
          <option value="unknown">Unknown</option>
        </select>
      </div>
      <div style={{ border: '1px solid #ccc', padding: '10px', marginBottom: '20px' }}>
        <h3>Incident Map Placeholder</h3>
        <p>Map visualization would go here (e.g., using Leaflet or Google Maps)</p>
      </div>
      <h2>Alert Timeline</h2>
      {filteredAlerts.map((alert, index) => (
        <div key={index} style={{ border: '1px solid #ddd', padding: '15px', margin: '10px 0', borderRadius: '5px' }}>
          <h3>{alert.title}</h3>
          <p><strong>Source:</strong> {alert.source}</p>
          <p><strong>Date:</strong> {new Date(alert.pubDate).toLocaleString()}</p>
          <p><strong>Threat Level:</strong> {alert.ai_threat_level} (Confidence: {alert.ai_confidence})</p>
          <p>{alert.contentSnippet}</p>
          <a href={alert.link} target="_blank" rel="noopener noreferrer">Read More</a>
          <div style={{ marginTop: '10px' }}>
            <button onClick={() => handleAction(alert.title, 'confirmed')} style={{ marginRight: '10px', padding: '5px 10px' }}>Confirm</button>
            <button onClick={() => handleAction(alert.title, 'escalated')} style={{ marginRight: '10px', padding: '5px 10px' }}>Escalate</button>
            <button onClick={() => handleAction(alert.title, 'dismissed')} style={{ padding: '5px 10px' }}>Dismiss</button>
            {actions[alert.title] && <span style={{ marginLeft: '10px', fontWeight: 'bold' }}>Action: {actions[alert.title]}</span>}
          </div>
        </div>
      ))}
    </div>
  );
}

export default AnalystDashboard;
