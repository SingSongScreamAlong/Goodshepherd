/**
 * Advanced Search Component
 * Full-text search with filters, facets, and result highlighting
 */

import React, { useState, useCallback, useEffect } from 'react';
import { searchEvents } from '../../services/analyticsService';

// Threat level colors
const THREAT_COLORS = {
  critical: '#dc2626',
  high: '#ea580c',
  medium: '#ca8a04',
  low: '#16a34a',
  minimal: '#6b7280',
};

/**
 * Search result item component
 */
function SearchResultItem({ result, onSelect }) {
  const threatColor = THREAT_COLORS[result.threat_level] || THREAT_COLORS.minimal;

  return (
    <div className="search-result-item" onClick={() => onSelect(result)}>
      <div className="result-header">
        <span
          className="threat-indicator"
          style={{ backgroundColor: threatColor }}
        >
          {result.threat_level}
        </span>
        <span className="result-category">{result.category}</span>
        <span className="result-date">
          {new Date(result.published_at || result.fetched_at).toLocaleDateString()}
        </span>
      </div>
      <h3 className="result-title">{result.title}</h3>
      <p className="result-summary">
        {result.summary?.substring(0, 200)}
        {result.summary?.length > 200 ? '...' : ''}
      </p>
      <div className="result-meta">
        <span className="meta-region">📍 {result.region || 'Unknown'}</span>
        <span className="meta-credibility">
          Credibility: {Math.round((result.credibility_score || 0.5) * 100)}%
        </span>
        <span className="meta-source">
          {result.source_url?.split('/')[2] || 'Unknown source'}
        </span>
      </div>
    </div>
  );
}

/**
 * Filter panel component
 */
function FilterPanel({ filters, onChange, facets }) {
  return (
    <div className="filter-panel">
      <h3>Filters</h3>

      <div className="filter-section">
        <label>Category</label>
        <select
          value={filters.category || ''}
          onChange={(e) => onChange({ ...filters, category: e.target.value || null })}
        >
          <option value="">All Categories</option>
          <option value="conflict">⚔️ Conflict</option>
          <option value="terrorism">💣 Terrorism</option>
          <option value="disaster">🌊 Disaster</option>
          <option value="health">🏥 Health</option>
          <option value="political">🏛️ Political</option>
          <option value="humanitarian">🆘 Humanitarian</option>
        </select>
      </div>

      <div className="filter-section">
        <label>Threat Level</label>
        <select
          value={filters.threatLevel || ''}
          onChange={(e) => onChange({ ...filters, threatLevel: e.target.value || null })}
        >
          <option value="">All Levels</option>
          <option value="critical">🔴 Critical</option>
          <option value="high">🟠 High</option>
          <option value="medium">🟡 Medium</option>
          <option value="low">🟢 Low</option>
          <option value="minimal">⚪ Minimal</option>
        </select>
      </div>

      <div className="filter-section">
        <label>Region</label>
        <input
          type="text"
          placeholder="Enter region..."
          value={filters.region || ''}
          onChange={(e) => onChange({ ...filters, region: e.target.value || null })}
        />
      </div>

      <div className="filter-section">
        <label>Verification Status</label>
        <select
          value={filters.verificationStatus || ''}
          onChange={(e) => onChange({ ...filters, verificationStatus: e.target.value || null })}
        >
          <option value="">All Status</option>
          <option value="verified">✓ Verified</option>
          <option value="unverified">? Unverified</option>
          <option value="pending">⏳ Pending Review</option>
          <option value="flagged">⚠ Flagged</option>
        </select>
      </div>

      <div className="filter-section">
        <label>Date Range</label>
        <div className="date-range">
          <input
            type="date"
            value={filters.startDate || ''}
            onChange={(e) => onChange({ ...filters, startDate: e.target.value || null })}
          />
          <span>to</span>
          <input
            type="date"
            value={filters.endDate || ''}
            onChange={(e) => onChange({ ...filters, endDate: e.target.value || null })}
          />
        </div>
      </div>

      {facets && (
        <div className="filter-section facets">
          <label>Quick Filters</label>
          <div className="facet-list">
            {facets.categories?.map((cat) => (
              <button
                key={cat.value}
                className={`facet-btn ${filters.category === cat.value ? 'active' : ''}`}
                onClick={() => onChange({
                  ...filters,
                  category: filters.category === cat.value ? null : cat.value,
                })}
              >
                {cat.value} ({cat.count})
              </button>
            ))}
          </div>
        </div>
      )}

      <button
        className="clear-filters-btn"
        onClick={() => onChange({
          category: null,
          threatLevel: null,
          region: null,
          verificationStatus: null,
          startDate: null,
          endDate: null,
        })}
      >
        Clear All Filters
      </button>
    </div>
  );
}

/**
 * Event detail modal component
 */
function EventDetailModal({ event, onClose }) {
  if (!event) return null;

  const threatColor = THREAT_COLORS[event.threat_level] || THREAT_COLORS.minimal;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <span
            className="threat-badge"
            style={{ backgroundColor: threatColor }}
          >
            {event.threat_level?.toUpperCase()}
          </span>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <h2 className="modal-title">{event.title}</h2>

        <div className="modal-meta">
          <div className="meta-row">
            <strong>Category:</strong> {event.category}
          </div>
          <div className="meta-row">
            <strong>Region:</strong> {event.region || 'Unknown'}
          </div>
          <div className="meta-row">
            <strong>Published:</strong>{' '}
            {new Date(event.published_at || event.fetched_at).toLocaleString()}
          </div>
          <div className="meta-row">
            <strong>Credibility:</strong> {Math.round((event.credibility_score || 0.5) * 100)}%
          </div>
          <div className="meta-row">
            <strong>Verification:</strong> {event.verification_status || 'Unverified'}
          </div>
        </div>

        <div className="modal-summary">
          <h4>Summary</h4>
          <p>{event.summary}</p>
        </div>

        {event.link && (
          <a
            href={event.link}
            target="_blank"
            rel="noopener noreferrer"
            className="source-link"
          >
            View Original Source →
          </a>
        )}

        <div className="modal-actions">
          <button className="action-btn primary">Add to Report</button>
          <button className="action-btn secondary">Flag for Review</button>
          <button className="action-btn secondary">Share</button>
        </div>
      </div>
    </div>
  );
}

/**
 * Main Advanced Search Component
 */
export default function AdvancedSearch() {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState({
    category: null,
    threatLevel: null,
    region: null,
    verificationStatus: null,
    startDate: null,
    endDate: null,
  });
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [totalResults, setTotalResults] = useState(0);
  const [page, setPage] = useState(0);
  const [facets, setFacets] = useState(null);

  const pageSize = 20;

  const performSearch = useCallback(async (resetPage = true) => {
    setLoading(true);
    setError(null);
    
    const currentPage = resetPage ? 0 : page;
    if (resetPage) setPage(0);

    try {
      const data = await searchEvents({
        query,
        ...filters,
        limit: pageSize,
        offset: currentPage * pageSize,
      });
      setResults(data.events || data.results || []);
      setTotalResults(data.total || data.events?.length || 0);
      setFacets(data.facets || null);
    } catch (err) {
      setError(err.message);
      // Use mock data for demo
      const mockResults = generateMockResults(query, filters);
      setResults(mockResults);
      setTotalResults(mockResults.length);
    } finally {
      setLoading(false);
    }
  }, [query, filters, page]);

  // Search on filter change
  useEffect(() => {
    const timer = setTimeout(() => {
      if (query || Object.values(filters).some(Boolean)) {
        performSearch(true);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [query, filters]);

  const handleSearch = (e) => {
    e.preventDefault();
    performSearch(true);
  };

  const loadMore = () => {
    setPage((p) => p + 1);
    performSearch(false);
  };

  return (
    <div className="advanced-search-container">
      <style>{`
        .advanced-search-container {
          display: flex;
          flex-direction: column;
          height: 100%;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          background: #f9fafb;
        }

        .search-header {
          padding: 20px;
          background: white;
          border-bottom: 1px solid #e5e7eb;
        }

        .search-title {
          margin: 0 0 16px 0;
          font-size: 1.5rem;
          font-weight: 600;
        }

        .search-form {
          display: flex;
          gap: 12px;
        }

        .search-input-wrapper {
          flex: 1;
          position: relative;
        }

        .search-input {
          width: 100%;
          padding: 12px 16px 12px 44px;
          border: 2px solid #e5e7eb;
          border-radius: 8px;
          font-size: 1rem;
          transition: border-color 0.2s;
        }

        .search-input:focus {
          outline: none;
          border-color: #3b82f6;
        }

        .search-icon {
          position: absolute;
          left: 16px;
          top: 50%;
          transform: translateY(-50%);
          color: #9ca3af;
        }

        .search-btn {
          padding: 12px 24px;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 1rem;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.2s;
        }

        .search-btn:hover {
          background: #2563eb;
        }

        .search-content {
          display: flex;
          flex: 1;
          overflow: hidden;
        }

        .filter-panel {
          width: 280px;
          padding: 20px;
          background: white;
          border-right: 1px solid #e5e7eb;
          overflow-y: auto;
        }

        .filter-panel h3 {
          margin: 0 0 16px 0;
          font-size: 1rem;
          font-weight: 600;
        }

        .filter-section {
          margin-bottom: 20px;
        }

        .filter-section label {
          display: block;
          margin-bottom: 8px;
          font-size: 0.875rem;
          font-weight: 500;
          color: #374151;
        }

        .filter-section select,
        .filter-section input {
          width: 100%;
          padding: 8px 12px;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          font-size: 0.875rem;
        }

        .date-range {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .date-range input {
          flex: 1;
        }

        .date-range span {
          color: #6b7280;
        }

        .facet-list {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }

        .facet-btn {
          padding: 4px 10px;
          background: #f3f4f6;
          border: 1px solid #e5e7eb;
          border-radius: 16px;
          font-size: 0.75rem;
          cursor: pointer;
          transition: all 0.2s;
        }

        .facet-btn:hover,
        .facet-btn.active {
          background: #3b82f6;
          color: white;
          border-color: #3b82f6;
        }

        .clear-filters-btn {
          width: 100%;
          padding: 10px;
          background: #fee2e2;
          color: #991b1b;
          border: none;
          border-radius: 6px;
          font-size: 0.875rem;
          cursor: pointer;
          transition: background 0.2s;
        }

        .clear-filters-btn:hover {
          background: #fecaca;
        }

        .results-panel {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
        }

        .results-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .results-count {
          font-size: 0.875rem;
          color: #6b7280;
        }

        .results-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .search-result-item {
          padding: 16px;
          background: white;
          border-radius: 8px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
          cursor: pointer;
          transition: all 0.2s;
        }

        .search-result-item:hover {
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
          transform: translateY(-2px);
        }

        .result-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }

        .threat-indicator {
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 0.625rem;
          font-weight: 600;
          color: white;
          text-transform: uppercase;
        }

        .result-category {
          padding: 2px 8px;
          background: #f3f4f6;
          border-radius: 4px;
          font-size: 0.75rem;
        }

        .result-date {
          margin-left: auto;
          font-size: 0.75rem;
          color: #6b7280;
        }

        .result-title {
          margin: 0 0 8px 0;
          font-size: 1rem;
          font-weight: 500;
          line-height: 1.4;
        }

        .result-summary {
          margin: 0 0 12px 0;
          font-size: 0.875rem;
          color: #4b5563;
          line-height: 1.5;
        }

        .result-meta {
          display: flex;
          gap: 16px;
          font-size: 0.75rem;
          color: #6b7280;
        }

        .load-more-btn {
          display: block;
          width: 100%;
          padding: 12px;
          margin-top: 16px;
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          font-size: 0.875rem;
          cursor: pointer;
          transition: background 0.2s;
        }

        .load-more-btn:hover {
          background: #f9fafb;
        }

        .loading-state,
        .error-state,
        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 40px;
          color: #6b7280;
        }

        .error-state {
          color: #dc2626;
        }

        .empty-state-icon {
          font-size: 3rem;
          margin-bottom: 16px;
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

        .modal-content {
          width: 90%;
          max-width: 600px;
          max-height: 90vh;
          overflow-y: auto;
          background: white;
          border-radius: 12px;
          padding: 24px;
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .threat-badge {
          padding: 4px 12px;
          border-radius: 4px;
          font-size: 0.75rem;
          font-weight: 600;
          color: white;
        }

        .modal-close {
          background: none;
          border: none;
          font-size: 1.5rem;
          cursor: pointer;
          color: #6b7280;
        }

        .modal-title {
          margin: 0 0 16px 0;
          font-size: 1.25rem;
          line-height: 1.4;
        }

        .modal-meta {
          display: grid;
          gap: 8px;
          margin-bottom: 16px;
          font-size: 0.875rem;
        }

        .meta-row strong {
          color: #6b7280;
        }

        .modal-summary h4 {
          margin: 0 0 8px 0;
          font-size: 0.875rem;
          color: #6b7280;
        }

        .modal-summary p {
          margin: 0;
          line-height: 1.6;
        }

        .source-link {
          display: inline-block;
          margin-top: 16px;
          color: #3b82f6;
          text-decoration: none;
        }

        .source-link:hover {
          text-decoration: underline;
        }

        .modal-actions {
          display: flex;
          gap: 8px;
          margin-top: 24px;
          padding-top: 16px;
          border-top: 1px solid #e5e7eb;
        }

        .action-btn {
          padding: 10px 16px;
          border-radius: 6px;
          font-size: 0.875rem;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.2s;
        }

        .action-btn.primary {
          background: #3b82f6;
          color: white;
          border: none;
        }

        .action-btn.primary:hover {
          background: #2563eb;
        }

        .action-btn.secondary {
          background: white;
          color: #374151;
          border: 1px solid #d1d5db;
        }

        .action-btn.secondary:hover {
          background: #f9fafb;
        }
      `}</style>

      <div className="search-header">
        <h2 className="search-title">🔍 Advanced Search</h2>
        <form className="search-form" onSubmit={handleSearch}>
          <div className="search-input-wrapper">
            <span className="search-icon">🔎</span>
            <input
              type="text"
              className="search-input"
              placeholder="Search events, regions, keywords..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <button type="submit" className="search-btn">
            Search
          </button>
        </form>
      </div>

      <div className="search-content">
        <FilterPanel
          filters={filters}
          onChange={setFilters}
          facets={facets}
        />

        <div className="results-panel">
          {loading && (
            <div className="loading-state">
              <div className="empty-state-icon">⏳</div>
              <p>Searching...</p>
            </div>
          )}

          {error && (
            <div className="error-state">
              <div className="empty-state-icon">⚠️</div>
              <p>{error}</p>
            </div>
          )}

          {!loading && !error && results.length === 0 && (
            <div className="empty-state">
              <div className="empty-state-icon">🔍</div>
              <p>No results found. Try adjusting your search or filters.</p>
            </div>
          )}

          {!loading && results.length > 0 && (
            <>
              <div className="results-header">
                <span className="results-count">
                  Showing {results.length} of {totalResults} results
                </span>
              </div>

              <div className="results-list">
                {results.map((result) => (
                  <SearchResultItem
                    key={result.id}
                    result={result}
                    onSelect={setSelectedEvent}
                  />
                ))}
              </div>

              {results.length < totalResults && (
                <button className="load-more-btn" onClick={loadMore}>
                  Load More Results
                </button>
              )}
            </>
          )}
        </div>
      </div>

      <EventDetailModal
        event={selectedEvent}
        onClose={() => setSelectedEvent(null)}
      />
    </div>
  );
}

/**
 * Generate mock results for demo
 */
function generateMockResults(query, filters) {
  const categories = ['conflict', 'terrorism', 'disaster', 'health', 'political', 'humanitarian'];
  const threatLevels = ['critical', 'high', 'medium', 'low', 'minimal'];
  const regions = ['Middle East', 'Sub-Saharan Africa', 'South Asia', 'Eastern Europe', 'Latin America'];

  const results = [];
  const count = Math.floor(Math.random() * 15) + 5;

  for (let i = 0; i < count; i++) {
    const category = filters.category || categories[Math.floor(Math.random() * categories.length)];
    const threatLevel = filters.threatLevel || threatLevels[Math.floor(Math.random() * threatLevels.length)];
    const region = filters.region || regions[Math.floor(Math.random() * regions.length)];

    results.push({
      id: `mock-${i}`,
      title: `${query ? `Results for "${query}": ` : ''}Event ${i + 1} - ${category} incident in ${region}`,
      summary: `This is a mock search result demonstrating the advanced search functionality. The event involves ${category} activity in the ${region} region with ${threatLevel} threat level.`,
      category,
      threat_level: threatLevel,
      region,
      published_at: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
      credibility_score: 0.5 + Math.random() * 0.5,
      verification_status: ['verified', 'unverified', 'pending'][Math.floor(Math.random() * 3)],
      source_url: 'https://example.com',
      link: 'https://example.com/article',
    });
  }

  return results;
}
