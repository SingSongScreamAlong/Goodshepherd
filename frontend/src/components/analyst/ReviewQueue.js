/**
 * Analyst Review Queue Component
 * Human-in-the-loop validation interface for event verification
 */

import React, { useState, useEffect, useCallback } from 'react';
import { getReviewQueue, submitEventValidation, submitMLFeedback } from '../../services/analyticsService';

// Threat level colors
const THREAT_COLORS = {
  critical: '#dc2626',
  high: '#ea580c',
  medium: '#ca8a04',
  low: '#16a34a',
  minimal: '#6b7280',
};

// Priority colors
const PRIORITY_COLORS = {
  urgent: '#dc2626',
  high: '#ea580c',
  normal: '#3b82f6',
  low: '#6b7280',
};

/**
 * Review item card component
 */
function ReviewCard({ item, onValidate, onExpand }) {
  const threatColor = THREAT_COLORS[item.threat_level] || THREAT_COLORS.minimal;
  const priorityColor = PRIORITY_COLORS[item.priority] || PRIORITY_COLORS.normal;

  return (
    <div className="review-card">
      <div className="card-header">
        <div className="card-badges">
          <span
            className="priority-badge"
            style={{ backgroundColor: priorityColor }}
          >
            {item.priority || 'normal'}
          </span>
          <span
            className="threat-badge"
            style={{ backgroundColor: threatColor }}
          >
            {item.threat_level}
          </span>
          <span className="category-badge">{item.category}</span>
        </div>
        <span className="card-time">
          {new Date(item.fetched_at).toLocaleString()}
        </span>
      </div>

      <h3 className="card-title" onClick={() => onExpand(item)}>
        {item.title}
      </h3>

      <p className="card-summary">
        {item.summary?.substring(0, 200)}
        {item.summary?.length > 200 ? '...' : ''}
      </p>

      <div className="card-meta">
        <span className="meta-region">📍 {item.region || 'Unknown'}</span>
        <span className="meta-source">
          🔗 {item.source_url?.split('/')[2] || 'Unknown'}
        </span>
      </div>

      <div className="card-scores">
        <div className="score-item">
          <span className="score-label">Credibility</span>
          <div className="score-bar">
            <div
              className="score-fill credibility"
              style={{ width: `${(item.credibility_score || 0.5) * 100}%` }}
            />
          </div>
          <span className="score-value">
            {Math.round((item.credibility_score || 0.5) * 100)}%
          </span>
        </div>
        {item.ml_analysis?.disinfo && (
          <div className="score-item">
            <span className="score-label">Disinfo Risk</span>
            <div className="score-bar">
              <div
                className="score-fill disinfo"
                style={{ width: `${(item.ml_analysis.disinfo.risk_score || 0) * 100}%` }}
              />
            </div>
            <span className="score-value">
              {Math.round((item.ml_analysis.disinfo.risk_score || 0) * 100)}%
            </span>
          </div>
        )}
      </div>

      <div className="card-actions">
        <button
          className="action-btn verify"
          onClick={() => onValidate(item.id, 'verified', null)}
        >
          ✓ Verify
        </button>
        <button
          className="action-btn flag"
          onClick={() => onValidate(item.id, 'flagged', null)}
        >
          ⚠ Flag
        </button>
        <button
          className="action-btn dismiss"
          onClick={() => onValidate(item.id, 'dismissed', null)}
        >
          ✗ Dismiss
        </button>
        <button
          className="action-btn expand"
          onClick={() => onExpand(item)}
        >
          📋 Details
        </button>
      </div>
    </div>
  );
}

/**
 * Detailed review modal with ML feedback
 */
function ReviewDetailModal({ item, onClose, onValidate, onMLFeedback }) {
  const [notes, setNotes] = useState('');
  const [correctedCategory, setCorrectedCategory] = useState(item?.category || '');
  const [correctedThreatLevel, setCorrectedThreatLevel] = useState(item?.threat_level || '');
  const [isDisinfo, setIsDisinfo] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  if (!item) return null;

  const threatColor = THREAT_COLORS[item.threat_level] || THREAT_COLORS.minimal;

  const handleValidate = async (status) => {
    setSubmitting(true);
    await onValidate(item.id, status, notes);
    
    // Submit ML feedback if corrections were made
    if (correctedCategory !== item.category || 
        correctedThreatLevel !== item.threat_level ||
        isDisinfo) {
      await onMLFeedback(item.id, {
        corrected_category: correctedCategory !== item.category ? correctedCategory : null,
        corrected_threat_level: correctedThreatLevel !== item.threat_level ? correctedThreatLevel : null,
        is_disinformation: isDisinfo,
        analyst_notes: notes,
      });
    }
    
    setSubmitting(false);
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content review-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Review Event</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {/* Event Info */}
          <div className="event-info-section">
            <div className="info-badges">
              <span
                className="threat-badge"
                style={{ backgroundColor: threatColor }}
              >
                {item.threat_level?.toUpperCase()}
              </span>
              <span className="category-badge">{item.category}</span>
            </div>
            <h3>{item.title}</h3>
            <p className="event-summary">{item.summary}</p>
            
            <div className="event-meta-grid">
              <div className="meta-item">
                <strong>Region:</strong> {item.region || 'Unknown'}
              </div>
              <div className="meta-item">
                <strong>Source:</strong>{' '}
                <a href={item.link} target="_blank" rel="noopener noreferrer">
                  {item.source_url?.split('/')[2] || 'View'}
                </a>
              </div>
              <div className="meta-item">
                <strong>Fetched:</strong>{' '}
                {new Date(item.fetched_at).toLocaleString()}
              </div>
              <div className="meta-item">
                <strong>Credibility:</strong>{' '}
                {Math.round((item.credibility_score || 0.5) * 100)}%
              </div>
            </div>
          </div>

          {/* ML Analysis */}
          {item.ml_analysis && (
            <div className="ml-analysis-section">
              <h4>🤖 ML Analysis</h4>
              <div className="ml-grid">
                {item.ml_analysis.threat && (
                  <div className="ml-item">
                    <strong>Threat Classification:</strong>
                    <span>{item.ml_analysis.threat.category}</span>
                    <span>Score: {Math.round(item.ml_analysis.threat.threat_score * 100)}%</span>
                  </div>
                )}
                {item.ml_analysis.disinfo && (
                  <div className="ml-item">
                    <strong>Disinfo Analysis:</strong>
                    <span>Risk: {item.ml_analysis.disinfo.risk_level}</span>
                    <span>Score: {Math.round(item.ml_analysis.disinfo.risk_score * 100)}%</span>
                    {item.ml_analysis.disinfo.indicators?.length > 0 && (
                      <div className="indicators">
                        {item.ml_analysis.disinfo.indicators.map((ind, i) => (
                          <span key={i} className="indicator-tag">{ind}</span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                {item.ml_analysis.source_language && item.ml_analysis.source_language !== 'en' && (
                  <div className="ml-item">
                    <strong>Translation:</strong>
                    <span>Original language: {item.ml_analysis.source_language}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Corrections Section */}
          <div className="corrections-section">
            <h4>📝 Analyst Corrections</h4>
            <p className="section-desc">
              Correct any ML misclassifications to improve future accuracy
            </p>

            <div className="correction-row">
              <label>Correct Category:</label>
              <select
                value={correctedCategory}
                onChange={(e) => setCorrectedCategory(e.target.value)}
              >
                <option value="conflict">⚔️ Conflict</option>
                <option value="terrorism">💣 Terrorism</option>
                <option value="disaster">🌊 Disaster</option>
                <option value="health">🏥 Health</option>
                <option value="political">🏛️ Political</option>
                <option value="humanitarian">🆘 Humanitarian</option>
                <option value="unknown">❓ Unknown</option>
              </select>
              {correctedCategory !== item.category && (
                <span className="correction-indicator">Changed</span>
              )}
            </div>

            <div className="correction-row">
              <label>Correct Threat Level:</label>
              <select
                value={correctedThreatLevel}
                onChange={(e) => setCorrectedThreatLevel(e.target.value)}
              >
                <option value="critical">🔴 Critical</option>
                <option value="high">🟠 High</option>
                <option value="medium">🟡 Medium</option>
                <option value="low">🟢 Low</option>
                <option value="minimal">⚪ Minimal</option>
              </select>
              {correctedThreatLevel !== item.threat_level && (
                <span className="correction-indicator">Changed</span>
              )}
            </div>

            <div className="correction-row checkbox">
              <label>
                <input
                  type="checkbox"
                  checked={isDisinfo}
                  onChange={(e) => setIsDisinfo(e.target.checked)}
                />
                Mark as Disinformation/Misinformation
              </label>
            </div>

            <div className="notes-section">
              <label>Analyst Notes:</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add notes about this event, corrections, or concerns..."
                rows={4}
              />
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button
            className="action-btn verify large"
            onClick={() => handleValidate('verified')}
            disabled={submitting}
          >
            ✓ Verify & Save
          </button>
          <button
            className="action-btn flag large"
            onClick={() => handleValidate('flagged')}
            disabled={submitting}
          >
            ⚠ Flag for Further Review
          </button>
          <button
            className="action-btn dismiss large"
            onClick={() => handleValidate('dismissed')}
            disabled={submitting}
          >
            ✗ Dismiss as Invalid
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Queue stats component
 */
function QueueStats({ stats }) {
  return (
    <div className="queue-stats">
      <div className="stat-card">
        <span className="stat-value">{stats.pending || 0}</span>
        <span className="stat-label">Pending</span>
      </div>
      <div className="stat-card urgent">
        <span className="stat-value">{stats.urgent || 0}</span>
        <span className="stat-label">Urgent</span>
      </div>
      <div className="stat-card">
        <span className="stat-value">{stats.verified_today || 0}</span>
        <span className="stat-label">Verified Today</span>
      </div>
      <div className="stat-card">
        <span className="stat-value">{stats.flagged || 0}</span>
        <span className="stat-label">Flagged</span>
      </div>
    </div>
  );
}

/**
 * Main Review Queue Component
 */
export default function ReviewQueue() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [filter, setFilter] = useState('pending');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [stats, setStats] = useState({});

  const fetchQueue = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getReviewQueue({
        status: filter,
        priority: priorityFilter || null,
      });
      setItems(data.items || []);
      setStats(data.stats || {});
    } catch (err) {
      setError(err.message);
      // Use mock data for demo
      setItems(generateMockQueueItems());
      setStats({ pending: 24, urgent: 3, verified_today: 47, flagged: 5 });
    } finally {
      setLoading(false);
    }
  }, [filter, priorityFilter]);

  useEffect(() => {
    fetchQueue();
  }, [fetchQueue]);

  const handleValidate = async (itemId, status, notes) => {
    try {
      await submitEventValidation(itemId, { status, notes });
      // Remove from queue
      setItems((prev) => prev.filter((item) => item.id !== itemId));
      // Update stats
      setStats((prev) => ({
        ...prev,
        pending: Math.max(0, (prev.pending || 0) - 1),
        verified_today: status === 'verified' ? (prev.verified_today || 0) + 1 : prev.verified_today,
        flagged: status === 'flagged' ? (prev.flagged || 0) + 1 : prev.flagged,
      }));
    } catch (err) {
      console.error('Validation failed:', err);
      // Still remove for demo
      setItems((prev) => prev.filter((item) => item.id !== itemId));
    }
  };

  const handleMLFeedback = async (itemId, feedback) => {
    try {
      await submitMLFeedback(itemId, feedback);
    } catch (err) {
      console.error('ML feedback failed:', err);
    }
  };

  return (
    <div className="review-queue-container">
      <style>{`
        .review-queue-container {
          display: flex;
          flex-direction: column;
          height: 100%;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          background: #f9fafb;
        }

        .queue-header {
          padding: 20px;
          background: white;
          border-bottom: 1px solid #e5e7eb;
        }

        .queue-title {
          margin: 0 0 16px 0;
          font-size: 1.5rem;
          font-weight: 600;
        }

        .queue-stats {
          display: flex;
          gap: 16px;
          margin-bottom: 16px;
        }

        .stat-card {
          padding: 12px 20px;
          background: #f3f4f6;
          border-radius: 8px;
          text-align: center;
        }

        .stat-card.urgent {
          background: #fee2e2;
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

        .queue-filters {
          display: flex;
          gap: 12px;
        }

        .filter-btn {
          padding: 8px 16px;
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 6px;
          font-size: 0.875rem;
          cursor: pointer;
          transition: all 0.2s;
        }

        .filter-btn:hover,
        .filter-btn.active {
          background: #3b82f6;
          color: white;
          border-color: #3b82f6;
        }

        .queue-content {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
        }

        .queue-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
          gap: 16px;
        }

        .review-card {
          background: white;
          border-radius: 12px;
          padding: 16px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 12px;
        }

        .card-badges {
          display: flex;
          gap: 6px;
          flex-wrap: wrap;
        }

        .priority-badge,
        .threat-badge {
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 0.625rem;
          font-weight: 600;
          color: white;
          text-transform: uppercase;
        }

        .category-badge {
          padding: 2px 8px;
          background: #f3f4f6;
          border-radius: 4px;
          font-size: 0.75rem;
        }

        .card-time {
          font-size: 0.75rem;
          color: #6b7280;
        }

        .card-title {
          margin: 0 0 8px 0;
          font-size: 1rem;
          font-weight: 500;
          line-height: 1.4;
          cursor: pointer;
        }

        .card-title:hover {
          color: #3b82f6;
        }

        .card-summary {
          margin: 0 0 12px 0;
          font-size: 0.875rem;
          color: #4b5563;
          line-height: 1.5;
        }

        .card-meta {
          display: flex;
          gap: 16px;
          margin-bottom: 12px;
          font-size: 0.75rem;
          color: #6b7280;
        }

        .card-scores {
          margin-bottom: 16px;
        }

        .score-item {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }

        .score-label {
          width: 80px;
          font-size: 0.75rem;
          color: #6b7280;
        }

        .score-bar {
          flex: 1;
          height: 8px;
          background: #e5e7eb;
          border-radius: 4px;
          overflow: hidden;
        }

        .score-fill {
          height: 100%;
          border-radius: 4px;
          transition: width 0.3s;
        }

        .score-fill.credibility {
          background: #16a34a;
        }

        .score-fill.disinfo {
          background: #dc2626;
        }

        .score-value {
          width: 40px;
          font-size: 0.75rem;
          text-align: right;
        }

        .card-actions {
          display: flex;
          gap: 8px;
        }

        .action-btn {
          flex: 1;
          padding: 8px;
          border: none;
          border-radius: 6px;
          font-size: 0.75rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
        }

        .action-btn.verify {
          background: #dcfce7;
          color: #166534;
        }

        .action-btn.verify:hover {
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

        .action-btn.expand {
          background: #e0e7ff;
          color: #3730a3;
        }

        .action-btn.expand:hover {
          background: #c7d2fe;
        }

        .action-btn.large {
          padding: 12px 20px;
          font-size: 0.875rem;
        }

        /* Modal styles */
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .modal-content.review-modal {
          width: 90%;
          max-width: 800px;
          max-height: 90vh;
          background: white;
          border-radius: 12px;
          display: flex;
          flex-direction: column;
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 20px;
          border-bottom: 1px solid #e5e7eb;
        }

        .modal-header h2 {
          margin: 0;
          font-size: 1.25rem;
        }

        .modal-close {
          background: none;
          border: none;
          font-size: 1.5rem;
          cursor: pointer;
          color: #6b7280;
        }

        .modal-body {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
        }

        .event-info-section {
          margin-bottom: 24px;
        }

        .info-badges {
          display: flex;
          gap: 8px;
          margin-bottom: 12px;
        }

        .event-info-section h3 {
          margin: 0 0 12px 0;
          font-size: 1.125rem;
        }

        .event-summary {
          margin: 0 0 16px 0;
          line-height: 1.6;
          color: #374151;
        }

        .event-meta-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 8px;
          font-size: 0.875rem;
        }

        .ml-analysis-section,
        .corrections-section {
          padding: 16px;
          background: #f9fafb;
          border-radius: 8px;
          margin-bottom: 16px;
        }

        .ml-analysis-section h4,
        .corrections-section h4 {
          margin: 0 0 12px 0;
          font-size: 1rem;
        }

        .section-desc {
          margin: 0 0 16px 0;
          font-size: 0.875rem;
          color: #6b7280;
        }

        .ml-grid {
          display: grid;
          gap: 12px;
        }

        .ml-item {
          display: flex;
          flex-direction: column;
          gap: 4px;
          font-size: 0.875rem;
        }

        .indicators {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
          margin-top: 4px;
        }

        .indicator-tag {
          padding: 2px 8px;
          background: #fee2e2;
          color: #991b1b;
          border-radius: 4px;
          font-size: 0.75rem;
        }

        .correction-row {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 12px;
        }

        .correction-row label {
          width: 150px;
          font-size: 0.875rem;
        }

        .correction-row select {
          flex: 1;
          padding: 8px 12px;
          border: 1px solid #d1d5db;
          border-radius: 6px;
        }

        .correction-row.checkbox label {
          width: auto;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .correction-indicator {
          padding: 2px 8px;
          background: #fef3c7;
          color: #92400e;
          border-radius: 4px;
          font-size: 0.75rem;
        }

        .notes-section {
          margin-top: 16px;
        }

        .notes-section label {
          display: block;
          margin-bottom: 8px;
          font-size: 0.875rem;
        }

        .notes-section textarea {
          width: 100%;
          padding: 12px;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          font-size: 0.875rem;
          resize: vertical;
        }

        .modal-footer {
          display: flex;
          gap: 12px;
          padding: 16px 20px;
          border-top: 1px solid #e5e7eb;
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

      <div className="queue-header">
        <h2 className="queue-title">📋 Analyst Review Queue</h2>
        <QueueStats stats={stats} />
        <div className="queue-filters">
          <button
            className={`filter-btn ${filter === 'pending' ? 'active' : ''}`}
            onClick={() => setFilter('pending')}
          >
            Pending Review
          </button>
          <button
            className={`filter-btn ${filter === 'flagged' ? 'active' : ''}`}
            onClick={() => setFilter('flagged')}
          >
            Flagged
          </button>
          <button
            className={`filter-btn ${filter === 'verified' ? 'active' : ''}`}
            onClick={() => setFilter('verified')}
          >
            Recently Verified
          </button>
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="filter-btn"
          >
            <option value="">All Priorities</option>
            <option value="urgent">🔴 Urgent</option>
            <option value="high">🟠 High</option>
            <option value="normal">🔵 Normal</option>
            <option value="low">⚪ Low</option>
          </select>
        </div>
      </div>

      <div className="queue-content">
        {loading && <div className="loading-state">Loading queue...</div>}
        {error && <div className="error-state">⚠️ {error}</div>}
        
        {!loading && !error && items.length === 0 && (
          <div className="loading-state">
            🎉 No items in queue! Great job keeping up with reviews.
          </div>
        )}

        {!loading && items.length > 0 && (
          <div className="queue-grid">
            {items.map((item) => (
              <ReviewCard
                key={item.id}
                item={item}
                onValidate={handleValidate}
                onExpand={setSelectedItem}
              />
            ))}
          </div>
        )}
      </div>

      <ReviewDetailModal
        item={selectedItem}
        onClose={() => setSelectedItem(null)}
        onValidate={handleValidate}
        onMLFeedback={handleMLFeedback}
      />
    </div>
  );
}

/**
 * Generate mock queue items for demo
 */
function generateMockQueueItems() {
  const categories = ['conflict', 'terrorism', 'disaster', 'health', 'political', 'humanitarian'];
  const threatLevels = ['critical', 'high', 'medium', 'low', 'minimal'];
  const priorities = ['urgent', 'high', 'normal', 'low'];
  const regions = ['Middle East', 'Sub-Saharan Africa', 'South Asia', 'Eastern Europe', 'Latin America'];

  const items = [];
  for (let i = 0; i < 12; i++) {
    items.push({
      id: `queue-${i}`,
      title: `Event requiring review: ${categories[i % categories.length]} incident reported`,
      summary: 'This event requires analyst review to verify accuracy and assess threat level. The ML system has flagged potential concerns that need human validation.',
      category: categories[i % categories.length],
      threat_level: threatLevels[i % threatLevels.length],
      priority: priorities[i % priorities.length],
      region: regions[i % regions.length],
      fetched_at: new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000).toISOString(),
      source_url: 'https://example.com',
      link: 'https://example.com/article',
      credibility_score: 0.3 + Math.random() * 0.5,
      ml_analysis: {
        threat: {
          category: categories[i % categories.length],
          threat_score: Math.random(),
        },
        disinfo: {
          risk_level: ['minimal', 'low', 'medium', 'high'][Math.floor(Math.random() * 4)],
          risk_score: Math.random() * 0.6,
          indicators: Math.random() > 0.5 ? ['Sensational language', 'Unverified claims'] : [],
        },
        source_language: Math.random() > 0.7 ? 'ar' : 'en',
      },
    });
  }

  return items;
}
