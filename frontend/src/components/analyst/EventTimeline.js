/**
 * Event Timeline Visualization Component
 * Displays events on an interactive timeline with filtering and drill-down
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { getTimelineEvents } from '../../services/analyticsService';

// Threat level colors
const THREAT_COLORS = {
  critical: '#dc2626',
  high: '#ea580c',
  medium: '#ca8a04',
  low: '#16a34a',
  minimal: '#6b7280',
};

// Category icons (using emoji for simplicity)
const CATEGORY_ICONS = {
  conflict: '⚔️',
  terrorism: '💣',
  disaster: '🌊',
  health: '🏥',
  political: '🏛️',
  humanitarian: '🆘',
  unknown: '❓',
};

/**
 * Format date for display
 */
function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Timeline event item component
 */
function TimelineEvent({ event, isSelected, onClick }) {
  const threatColor = THREAT_COLORS[event.threat_level] || THREAT_COLORS.minimal;
  const icon = CATEGORY_ICONS[event.category] || CATEGORY_ICONS.unknown;

  return (
    <div
      className={`timeline-event ${isSelected ? 'selected' : ''}`}
      onClick={() => onClick(event)}
      style={{
        borderLeftColor: threatColor,
        backgroundColor: isSelected ? '#f0f9ff' : 'white',
      }}
    >
      <div className="event-header">
        <span className="event-icon">{icon}</span>
        <span className="event-time">{formatDate(event.published_at || event.fetched_at)}</span>
        <span
          className="threat-badge"
          style={{ backgroundColor: threatColor }}
        >
          {event.threat_level}
        </span>
      </div>
      <h4 className="event-title">{event.title}</h4>
      <p className="event-summary">
        {event.summary?.substring(0, 150)}
        {event.summary?.length > 150 ? '...' : ''}
      </p>
      <div className="event-meta">
        <span className="event-region">📍 {event.region || 'Unknown'}</span>
        <span className="event-source">🔗 {event.source_url?.split('/')[2] || 'Unknown'}</span>
      </div>
    </div>
  );
}

/**
 * Timeline day group component
 */
function TimelineDay({ date, events, selectedEvent, onEventClick }) {
  const dayDate = new Date(date);
  const isToday = new Date().toDateString() === dayDate.toDateString();

  return (
    <div className="timeline-day">
      <div className={`day-header ${isToday ? 'today' : ''}`}>
        <span className="day-date">
          {dayDate.toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
          })}
        </span>
        <span className="day-count">{events.length} events</span>
      </div>
      <div className="day-events">
        {events.map((event) => (
          <TimelineEvent
            key={event.id}
            event={event}
            isSelected={selectedEvent?.id === event.id}
            onClick={onEventClick}
          />
        ))}
      </div>
    </div>
  );
}

/**
 * Event detail panel component
 */
function EventDetailPanel({ event, onClose, onValidate }) {
  if (!event) return null;

  const threatColor = THREAT_COLORS[event.threat_level] || THREAT_COLORS.minimal;

  return (
    <div className="event-detail-panel">
      <div className="panel-header">
        <h3>Event Details</h3>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>
      
      <div className="panel-content">
        <div className="detail-section">
          <span
            className="threat-indicator"
            style={{ backgroundColor: threatColor }}
          >
            {event.threat_level?.toUpperCase()}
          </span>
          <span className="category-badge">
            {CATEGORY_ICONS[event.category]} {event.category}
          </span>
        </div>

        <h2 className="detail-title">{event.title}</h2>
        
        <div className="detail-meta">
          <div className="meta-item">
            <strong>Region:</strong> {event.region || 'Unknown'}
          </div>
          <div className="meta-item">
            <strong>Published:</strong> {formatDate(event.published_at || event.fetched_at)}
          </div>
          <div className="meta-item">
            <strong>Source:</strong>{' '}
            <a href={event.link} target="_blank" rel="noopener noreferrer">
              {event.source_url?.split('/')[2] || 'View Source'}
            </a>
          </div>
          <div className="meta-item">
            <strong>Credibility:</strong>{' '}
            <span className={`credibility-score ${event.credibility_score > 0.7 ? 'high' : event.credibility_score > 0.4 ? 'medium' : 'low'}`}>
              {Math.round((event.credibility_score || 0.5) * 100)}%
            </span>
          </div>
        </div>

        <div className="detail-summary">
          <h4>Summary</h4>
          <p>{event.summary}</p>
        </div>

        {event.geocode && (
          <div className="detail-location">
            <h4>Location</h4>
            <p>
              Lat: {event.geocode.lat?.toFixed(4)}, Lon: {event.geocode.lon?.toFixed(4)}
            </p>
          </div>
        )}

        <div className="detail-actions">
          <button
            className="action-btn validate"
            onClick={() => onValidate(event, 'verified')}
          >
            ✓ Verify
          </button>
          <button
            className="action-btn flag"
            onClick={() => onValidate(event, 'flagged')}
          >
            ⚠ Flag for Review
          </button>
          <button
            className="action-btn dismiss"
            onClick={() => onValidate(event, 'dismissed')}
          >
            ✗ Dismiss
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Main Event Timeline Component
 */
export default function EventTimeline({
  initialStartDate = null,
  initialEndDate = null,
  initialCategory = null,
  initialRegion = null,
}) {
  // Calculate default date range (last 7 days)
  const defaultEndDate = new Date().toISOString().split('T')[0];
  const defaultStartDate = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
    .toISOString()
    .split('T')[0];

  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);
  
  // Filters
  const [startDate, setStartDate] = useState(initialStartDate || defaultStartDate);
  const [endDate, setEndDate] = useState(initialEndDate || defaultEndDate);
  const [category, setCategory] = useState(initialCategory || '');
  const [region, setRegion] = useState(initialRegion || '');
  const [threatFilter, setThreatFilter] = useState('');

  // Fetch events
  const fetchEvents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getTimelineEvents({
        startDate,
        endDate,
        category: category || null,
        region: region || null,
      });
      setEvents(data.events || []);
    } catch (err) {
      setError(err.message);
      // Use mock data for demo
      setEvents(generateMockEvents());
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, category, region]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  // Group events by day
  const eventsByDay = useMemo(() => {
    const filtered = events.filter((event) => {
      if (threatFilter && event.threat_level !== threatFilter) return false;
      return true;
    });

    const grouped = {};
    filtered.forEach((event) => {
      const date = new Date(event.published_at || event.fetched_at)
        .toISOString()
        .split('T')[0];
      if (!grouped[date]) {
        grouped[date] = [];
      }
      grouped[date].push(event);
    });

    // Sort days descending, events by time descending
    const sortedDays = Object.keys(grouped).sort((a, b) => b.localeCompare(a));
    sortedDays.forEach((day) => {
      grouped[day].sort((a, b) => 
        new Date(b.published_at || b.fetched_at) - new Date(a.published_at || a.fetched_at)
      );
    });

    return { days: sortedDays, events: grouped };
  }, [events, threatFilter]);

  // Stats
  const stats = useMemo(() => {
    const threatCounts = {};
    const categoryCounts = {};
    events.forEach((event) => {
      threatCounts[event.threat_level] = (threatCounts[event.threat_level] || 0) + 1;
      categoryCounts[event.category] = (categoryCounts[event.category] || 0) + 1;
    });
    return { threatCounts, categoryCounts, total: events.length };
  }, [events]);

  const handleValidate = async (event, status) => {
    // TODO: Call API to validate event
    console.log('Validating event:', event.id, 'as', status);
    setSelectedEvent(null);
  };

  return (
    <div className="event-timeline-container">
      <style>{`
        .event-timeline-container {
          display: flex;
          flex-direction: column;
          height: 100%;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .timeline-header {
          padding: 16px;
          background: white;
          border-bottom: 1px solid #e5e7eb;
        }

        .timeline-title {
          margin: 0 0 16px 0;
          font-size: 1.5rem;
          font-weight: 600;
        }

        .timeline-filters {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
          align-items: center;
        }

        .filter-group {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .filter-group label {
          font-size: 0.75rem;
          color: #6b7280;
          font-weight: 500;
        }

        .filter-group input,
        .filter-group select {
          padding: 8px 12px;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          font-size: 0.875rem;
        }

        .timeline-stats {
          display: flex;
          gap: 16px;
          padding: 12px 16px;
          background: #f9fafb;
          border-bottom: 1px solid #e5e7eb;
        }

        .stat-item {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .stat-count {
          font-weight: 600;
          font-size: 1.25rem;
        }

        .stat-label {
          color: #6b7280;
          font-size: 0.875rem;
        }

        .threat-pills {
          display: flex;
          gap: 8px;
          margin-left: auto;
        }

        .threat-pill {
          padding: 4px 12px;
          border-radius: 16px;
          font-size: 0.75rem;
          font-weight: 500;
          color: white;
          cursor: pointer;
          opacity: 0.7;
          transition: opacity 0.2s;
        }

        .threat-pill:hover,
        .threat-pill.active {
          opacity: 1;
        }

        .timeline-content {
          display: flex;
          flex: 1;
          overflow: hidden;
        }

        .timeline-scroll {
          flex: 1;
          overflow-y: auto;
          padding: 16px;
        }

        .timeline-day {
          margin-bottom: 24px;
        }

        .day-header {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 8px 0;
          border-bottom: 2px solid #e5e7eb;
          margin-bottom: 12px;
        }

        .day-header.today {
          border-bottom-color: #3b82f6;
        }

        .day-date {
          font-weight: 600;
          font-size: 1rem;
        }

        .day-count {
          color: #6b7280;
          font-size: 0.875rem;
        }

        .day-events {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .timeline-event {
          padding: 12px 16px;
          background: white;
          border-radius: 8px;
          border-left: 4px solid #6b7280;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
          cursor: pointer;
          transition: all 0.2s;
        }

        .timeline-event:hover {
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
          transform: translateX(4px);
        }

        .timeline-event.selected {
          border-left-width: 6px;
        }

        .event-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }

        .event-icon {
          font-size: 1.25rem;
        }

        .event-time {
          color: #6b7280;
          font-size: 0.75rem;
        }

        .threat-badge {
          margin-left: auto;
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 0.625rem;
          font-weight: 600;
          color: white;
          text-transform: uppercase;
        }

        .event-title {
          margin: 0 0 8px 0;
          font-size: 0.9375rem;
          font-weight: 500;
          line-height: 1.4;
        }

        .event-summary {
          margin: 0 0 8px 0;
          color: #4b5563;
          font-size: 0.8125rem;
          line-height: 1.5;
        }

        .event-meta {
          display: flex;
          gap: 16px;
          font-size: 0.75rem;
          color: #6b7280;
        }

        .event-detail-panel {
          width: 400px;
          background: white;
          border-left: 1px solid #e5e7eb;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px;
          border-bottom: 1px solid #e5e7eb;
        }

        .panel-header h3 {
          margin: 0;
          font-size: 1rem;
        }

        .close-btn {
          background: none;
          border: none;
          font-size: 1.5rem;
          cursor: pointer;
          color: #6b7280;
        }

        .panel-content {
          flex: 1;
          overflow-y: auto;
          padding: 16px;
        }

        .detail-section {
          display: flex;
          gap: 8px;
          margin-bottom: 16px;
        }

        .threat-indicator {
          padding: 4px 12px;
          border-radius: 4px;
          font-size: 0.75rem;
          font-weight: 600;
          color: white;
        }

        .category-badge {
          padding: 4px 12px;
          background: #f3f4f6;
          border-radius: 4px;
          font-size: 0.75rem;
        }

        .detail-title {
          margin: 0 0 16px 0;
          font-size: 1.125rem;
          line-height: 1.4;
        }

        .detail-meta {
          display: grid;
          gap: 8px;
          margin-bottom: 16px;
          font-size: 0.875rem;
        }

        .meta-item strong {
          color: #6b7280;
        }

        .credibility-score {
          padding: 2px 8px;
          border-radius: 4px;
          font-weight: 500;
        }

        .credibility-score.high {
          background: #dcfce7;
          color: #166534;
        }

        .credibility-score.medium {
          background: #fef3c7;
          color: #92400e;
        }

        .credibility-score.low {
          background: #fee2e2;
          color: #991b1b;
        }

        .detail-summary {
          margin-bottom: 16px;
        }

        .detail-summary h4,
        .detail-location h4 {
          margin: 0 0 8px 0;
          font-size: 0.875rem;
          color: #6b7280;
        }

        .detail-summary p {
          margin: 0;
          line-height: 1.6;
          font-size: 0.875rem;
        }

        .detail-actions {
          display: flex;
          gap: 8px;
          margin-top: 24px;
          padding-top: 16px;
          border-top: 1px solid #e5e7eb;
        }

        .action-btn {
          flex: 1;
          padding: 10px;
          border: none;
          border-radius: 6px;
          font-size: 0.875rem;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.2s;
        }

        .action-btn.validate {
          background: #dcfce7;
          color: #166534;
        }

        .action-btn.validate:hover {
          background: #bbf7d0;
        }

        .action-btn.flag {
          background: #fef3c7;
          color: #92400e;
        }

        .action-btn.flag:hover {
          background: #fde68a;
        }

        .action-btn.dismiss {
          background: #fee2e2;
          color: #991b1b;
        }

        .action-btn.dismiss:hover {
          background: #fecaca;
        }

        .loading-state,
        .error-state {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 200px;
          color: #6b7280;
        }

        .error-state {
          color: #dc2626;
        }
      `}</style>

      <div className="timeline-header">
        <h2 className="timeline-title">📅 Event Timeline</h2>
        <div className="timeline-filters">
          <div className="filter-group">
            <label>Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>
          <div className="filter-group">
            <label>End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>
          <div className="filter-group">
            <label>Category</label>
            <select value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="">All Categories</option>
              <option value="conflict">⚔️ Conflict</option>
              <option value="terrorism">💣 Terrorism</option>
              <option value="disaster">🌊 Disaster</option>
              <option value="health">🏥 Health</option>
              <option value="political">🏛️ Political</option>
              <option value="humanitarian">🆘 Humanitarian</option>
            </select>
          </div>
          <div className="filter-group">
            <label>Region</label>
            <input
              type="text"
              placeholder="Filter by region..."
              value={region}
              onChange={(e) => setRegion(e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="timeline-stats">
        <div className="stat-item">
          <span className="stat-count">{stats.total}</span>
          <span className="stat-label">Total Events</span>
        </div>
        <div className="threat-pills">
          {Object.entries(THREAT_COLORS).map(([level, color]) => (
            <span
              key={level}
              className={`threat-pill ${threatFilter === level ? 'active' : ''}`}
              style={{ backgroundColor: color }}
              onClick={() => setThreatFilter(threatFilter === level ? '' : level)}
            >
              {stats.threatCounts[level] || 0} {level}
            </span>
          ))}
        </div>
      </div>

      <div className="timeline-content">
        <div className="timeline-scroll">
          {loading && <div className="loading-state">Loading events...</div>}
          {error && <div className="error-state">⚠️ {error}</div>}
          {!loading && !error && eventsByDay.days.length === 0 && (
            <div className="loading-state">No events found for this period</div>
          )}
          {!loading &&
            eventsByDay.days.map((day) => (
              <TimelineDay
                key={day}
                date={day}
                events={eventsByDay.events[day]}
                selectedEvent={selectedEvent}
                onEventClick={setSelectedEvent}
              />
            ))}
        </div>

        {selectedEvent && (
          <EventDetailPanel
            event={selectedEvent}
            onClose={() => setSelectedEvent(null)}
            onValidate={handleValidate}
          />
        )}
      </div>
    </div>
  );
}

/**
 * Generate mock events for demo
 */
function generateMockEvents() {
  const categories = ['conflict', 'terrorism', 'disaster', 'health', 'political', 'humanitarian'];
  const threatLevels = ['critical', 'high', 'medium', 'low', 'minimal'];
  const regions = ['Middle East', 'Sub-Saharan Africa', 'South Asia', 'Eastern Europe', 'Latin America'];
  
  const mockTitles = [
    'Armed clashes reported near border region',
    'Earthquake strikes coastal area',
    'Disease outbreak confirmed in rural district',
    'Political protests escalate in capital',
    'Humanitarian crisis deepens amid conflict',
    'Terrorist threat warning issued',
    'Flooding displaces thousands',
    'Military offensive launched',
    'Health emergency declared',
    'Civil unrest spreads to new regions',
  ];

  const events = [];
  for (let i = 0; i < 30; i++) {
    const daysAgo = Math.floor(Math.random() * 7);
    const hoursAgo = Math.floor(Math.random() * 24);
    const date = new Date(Date.now() - daysAgo * 24 * 60 * 60 * 1000 - hoursAgo * 60 * 60 * 1000);
    
    events.push({
      id: `mock-${i}`,
      title: mockTitles[Math.floor(Math.random() * mockTitles.length)],
      summary: 'This is a mock event summary for demonstration purposes. In production, this would contain actual event details from the data sources.',
      category: categories[Math.floor(Math.random() * categories.length)],
      threat_level: threatLevels[Math.floor(Math.random() * threatLevels.length)],
      region: regions[Math.floor(Math.random() * regions.length)],
      published_at: date.toISOString(),
      fetched_at: date.toISOString(),
      source_url: 'https://example.com/news',
      link: 'https://example.com/news/article',
      credibility_score: 0.5 + Math.random() * 0.5,
    });
  }

  return events;
}
