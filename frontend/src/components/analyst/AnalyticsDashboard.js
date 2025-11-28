/**
 * Analytics Dashboard Component
 * Overview of threat trends, regional breakdown, and key metrics
 */

import React, { useState, useEffect, useCallback } from 'react';
import { getAnalyticsSummary, getThreatTrends, getRegionalBreakdown } from '../../services/analyticsService';

// Threat level colors
const THREAT_COLORS = {
  critical: '#dc2626',
  high: '#ea580c',
  medium: '#ca8a04',
  low: '#16a34a',
  minimal: '#6b7280',
};

// Category colors
const CATEGORY_COLORS = {
  conflict: '#ef4444',
  terrorism: '#f97316',
  disaster: '#3b82f6',
  health: '#22c55e',
  political: '#8b5cf6',
  humanitarian: '#ec4899',
};

/**
 * Metric card component
 */
function MetricCard({ title, value, change, icon, color }) {
  const isPositive = change > 0;
  const changeColor = title.includes('Threat') || title.includes('Critical')
    ? (isPositive ? '#dc2626' : '#16a34a')
    : (isPositive ? '#16a34a' : '#dc2626');

  return (
    <div className="metric-card" style={{ borderTopColor: color }}>
      <div className="metric-icon">{icon}</div>
      <div className="metric-content">
        <span className="metric-title">{title}</span>
        <span className="metric-value">{value}</span>
        {change !== undefined && (
          <span className="metric-change" style={{ color: changeColor }}>
            {isPositive ? '↑' : '↓'} {Math.abs(change)}% vs last period
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * Simple bar chart component
 */
function BarChart({ data, title, colorMap }) {
  const maxValue = Math.max(...data.map((d) => d.value), 1);

  return (
    <div className="chart-container">
      <h3 className="chart-title">{title}</h3>
      <div className="bar-chart">
        {data.map((item) => (
          <div key={item.label} className="bar-row">
            <span className="bar-label">{item.label}</span>
            <div className="bar-track">
              <div
                className="bar-fill"
                style={{
                  width: `${(item.value / maxValue) * 100}%`,
                  backgroundColor: colorMap?.[item.label] || '#3b82f6',
                }}
              />
            </div>
            <span className="bar-value">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Trend line chart component (simplified)
 */
function TrendChart({ data, title }) {
  if (!data || data.length === 0) return null;

  const maxValue = Math.max(...data.map((d) => d.total), 1);
  const points = data.map((d, i) => ({
    x: (i / (data.length - 1)) * 100,
    y: 100 - (d.total / maxValue) * 80,
  }));

  const pathD = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`)
    .join(' ');

  return (
    <div className="chart-container trend-chart">
      <h3 className="chart-title">{title}</h3>
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="trend-svg">
        {/* Grid lines */}
        <line x1="0" y1="20" x2="100" y2="20" stroke="#e5e7eb" strokeWidth="0.5" />
        <line x1="0" y1="50" x2="100" y2="50" stroke="#e5e7eb" strokeWidth="0.5" />
        <line x1="0" y1="80" x2="100" y2="80" stroke="#e5e7eb" strokeWidth="0.5" />
        
        {/* Trend line */}
        <path d={pathD} fill="none" stroke="#3b82f6" strokeWidth="2" />
        
        {/* Data points */}
        {points.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r="2" fill="#3b82f6" />
        ))}
      </svg>
      <div className="trend-labels">
        {data.filter((_, i) => i % Math.ceil(data.length / 5) === 0).map((d, i) => (
          <span key={i} className="trend-label">{d.date}</span>
        ))}
      </div>
    </div>
  );
}

/**
 * Regional map placeholder (would use actual map library in production)
 */
function RegionalMap({ data }) {
  return (
    <div className="chart-container regional-map">
      <h3 className="chart-title">🗺️ Regional Threat Distribution</h3>
      <div className="region-grid">
        {data.map((region) => (
          <div key={region.name} className="region-card">
            <div className="region-header">
              <span className="region-name">{region.name}</span>
              <span
                className="region-threat"
                style={{ backgroundColor: THREAT_COLORS[region.dominant_threat] }}
              >
                {region.dominant_threat}
              </span>
            </div>
            <div className="region-stats">
              <span className="region-count">{region.event_count} events</span>
              <span className="region-trend">
                {region.trend > 0 ? '↑' : region.trend < 0 ? '↓' : '→'}
                {Math.abs(region.trend)}%
              </span>
            </div>
            <div className="region-bar">
              <div
                className="region-bar-fill"
                style={{
                  width: `${Math.min(100, region.event_count / 2)}%`,
                  backgroundColor: THREAT_COLORS[region.dominant_threat],
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Recent activity feed
 */
function ActivityFeed({ activities }) {
  return (
    <div className="chart-container activity-feed">
      <h3 className="chart-title">📡 Recent Activity</h3>
      <div className="activity-list">
        {activities.map((activity, i) => (
          <div key={i} className="activity-item">
            <span className="activity-icon">{activity.icon}</span>
            <div className="activity-content">
              <span className="activity-text">{activity.text}</span>
              <span className="activity-time">{activity.time}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Main Analytics Dashboard Component
 */
export default function AnalyticsDashboard() {
  const [period, setPeriod] = useState('7d');
  const [summary, setSummary] = useState(null);
  const [trends, setTrends] = useState([]);
  const [regions, setRegions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryData, trendsData, regionsData] = await Promise.all([
        getAnalyticsSummary({ period }),
        getThreatTrends({
          startDate: getStartDate(period),
          endDate: new Date().toISOString().split('T')[0],
          granularity: period === '24h' ? 'hour' : 'day',
        }),
        getRegionalBreakdown({ period }),
      ]);
      setSummary(summaryData);
      setTrends(trendsData.trends || []);
      setRegions(regionsData.regions || []);
    } catch (err) {
      setError(err.message);
      // Use mock data for demo
      setSummary(generateMockSummary());
      setTrends(generateMockTrends(period));
      setRegions(generateMockRegions());
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const threatByLevel = summary?.by_threat_level || [];
  const byCategory = summary?.by_category || [];
  const recentActivities = summary?.recent_activities || generateMockActivities();

  return (
    <div className="analytics-dashboard">
      <style>{`
        .analytics-dashboard {
          padding: 20px;
          background: #f9fafb;
          min-height: 100%;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
        }

        .dashboard-title {
          margin: 0;
          font-size: 1.5rem;
          font-weight: 600;
        }

        .period-selector {
          display: flex;
          gap: 8px;
        }

        .period-btn {
          padding: 8px 16px;
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 6px;
          font-size: 0.875rem;
          cursor: pointer;
          transition: all 0.2s;
        }

        .period-btn:hover,
        .period-btn.active {
          background: #3b82f6;
          color: white;
          border-color: #3b82f6;
        }

        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
          margin-bottom: 24px;
        }

        .metric-card {
          background: white;
          border-radius: 12px;
          padding: 16px;
          border-top: 4px solid #3b82f6;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .metric-icon {
          font-size: 1.5rem;
          margin-bottom: 8px;
        }

        .metric-content {
          display: flex;
          flex-direction: column;
        }

        .metric-title {
          font-size: 0.75rem;
          color: #6b7280;
          margin-bottom: 4px;
        }

        .metric-value {
          font-size: 1.75rem;
          font-weight: 600;
        }

        .metric-change {
          font-size: 0.75rem;
          margin-top: 4px;
        }

        .charts-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 20px;
          margin-bottom: 24px;
        }

        @media (max-width: 1024px) {
          .charts-grid {
            grid-template-columns: 1fr;
          }
        }

        .chart-container {
          background: white;
          border-radius: 12px;
          padding: 20px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .chart-title {
          margin: 0 0 16px 0;
          font-size: 1rem;
          font-weight: 600;
        }

        .bar-chart {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .bar-row {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .bar-label {
          width: 80px;
          font-size: 0.75rem;
          text-transform: capitalize;
        }

        .bar-track {
          flex: 1;
          height: 24px;
          background: #f3f4f6;
          border-radius: 4px;
          overflow: hidden;
        }

        .bar-fill {
          height: 100%;
          border-radius: 4px;
          transition: width 0.3s;
        }

        .bar-value {
          width: 40px;
          font-size: 0.875rem;
          font-weight: 500;
          text-align: right;
        }

        .trend-chart {
          height: 300px;
        }

        .trend-svg {
          width: 100%;
          height: 200px;
        }

        .trend-labels {
          display: flex;
          justify-content: space-between;
          margin-top: 8px;
        }

        .trend-label {
          font-size: 0.625rem;
          color: #6b7280;
        }

        .region-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
          gap: 12px;
        }

        .region-card {
          padding: 12px;
          background: #f9fafb;
          border-radius: 8px;
        }

        .region-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .region-name {
          font-weight: 500;
          font-size: 0.875rem;
        }

        .region-threat {
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 0.625rem;
          font-weight: 600;
          color: white;
          text-transform: uppercase;
        }

        .region-stats {
          display: flex;
          justify-content: space-between;
          font-size: 0.75rem;
          color: #6b7280;
          margin-bottom: 8px;
        }

        .region-bar {
          height: 4px;
          background: #e5e7eb;
          border-radius: 2px;
          overflow: hidden;
        }

        .region-bar-fill {
          height: 100%;
          border-radius: 2px;
        }

        .activity-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
          max-height: 300px;
          overflow-y: auto;
        }

        .activity-item {
          display: flex;
          gap: 12px;
          padding: 8px;
          background: #f9fafb;
          border-radius: 8px;
        }

        .activity-icon {
          font-size: 1.25rem;
        }

        .activity-content {
          display: flex;
          flex-direction: column;
          flex: 1;
        }

        .activity-text {
          font-size: 0.875rem;
        }

        .activity-time {
          font-size: 0.75rem;
          color: #6b7280;
        }

        .loading-state {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 400px;
          color: #6b7280;
        }
      `}</style>

      <div className="dashboard-header">
        <h2 className="dashboard-title">📊 Analytics Dashboard</h2>
        <div className="period-selector">
          {['24h', '7d', '30d', '90d'].map((p) => (
            <button
              key={p}
              className={`period-btn ${period === p ? 'active' : ''}`}
              onClick={() => setPeriod(p)}
            >
              {p === '24h' ? '24 Hours' : p === '7d' ? '7 Days' : p === '30d' ? '30 Days' : '90 Days'}
            </button>
          ))}
        </div>
      </div>

      {loading && <div className="loading-state">Loading analytics...</div>}

      {!loading && (
        <>
          <div className="metrics-grid">
            <MetricCard
              title="Total Events"
              value={summary?.total_events || 0}
              change={summary?.events_change}
              icon="📈"
              color="#3b82f6"
            />
            <MetricCard
              title="Critical Threats"
              value={summary?.critical_count || 0}
              change={summary?.critical_change}
              icon="🔴"
              color="#dc2626"
            />
            <MetricCard
              title="Verified Events"
              value={summary?.verified_count || 0}
              change={summary?.verified_change}
              icon="✓"
              color="#16a34a"
            />
            <MetricCard
              title="Pending Review"
              value={summary?.pending_count || 0}
              change={summary?.pending_change}
              icon="⏳"
              color="#ca8a04"
            />
            <MetricCard
              title="Active Regions"
              value={summary?.active_regions || 0}
              icon="🌍"
              color="#8b5cf6"
            />
            <MetricCard
              title="Data Sources"
              value={summary?.active_sources || 0}
              icon="📡"
              color="#06b6d4"
            />
          </div>

          <div className="charts-grid">
            <BarChart
              data={threatByLevel}
              title="📊 Events by Threat Level"
              colorMap={THREAT_COLORS}
            />
            <BarChart
              data={byCategory}
              title="📁 Events by Category"
              colorMap={CATEGORY_COLORS}
            />
          </div>

          <div className="charts-grid">
            <TrendChart data={trends} title="📈 Event Trend" />
            <RegionalMap data={regions} />
          </div>

          <ActivityFeed activities={recentActivities} />
        </>
      )}
    </div>
  );
}

/**
 * Helper to get start date from period
 */
function getStartDate(period) {
  const now = new Date();
  switch (period) {
    case '24h':
      return new Date(now - 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    case '7d':
      return new Date(now - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    case '30d':
      return new Date(now - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    case '90d':
      return new Date(now - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    default:
      return new Date(now - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  }
}

/**
 * Generate mock summary data
 */
function generateMockSummary() {
  return {
    total_events: 1247,
    events_change: 12,
    critical_count: 23,
    critical_change: -5,
    verified_count: 892,
    verified_change: 8,
    pending_count: 47,
    pending_change: -15,
    active_regions: 34,
    active_sources: 6,
    by_threat_level: [
      { label: 'critical', value: 23 },
      { label: 'high', value: 89 },
      { label: 'medium', value: 234 },
      { label: 'low', value: 456 },
      { label: 'minimal', value: 445 },
    ],
    by_category: [
      { label: 'conflict', value: 312 },
      { label: 'disaster', value: 245 },
      { label: 'political', value: 198 },
      { label: 'health', value: 176 },
      { label: 'humanitarian', value: 167 },
      { label: 'terrorism', value: 149 },
    ],
  };
}

/**
 * Generate mock trends data
 */
function generateMockTrends(period) {
  const days = period === '24h' ? 24 : period === '7d' ? 7 : period === '30d' ? 30 : 90;
  const trends = [];
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(Date.now() - i * (period === '24h' ? 60 * 60 * 1000 : 24 * 60 * 60 * 1000));
    trends.push({
      date: period === '24h' 
        ? date.toLocaleTimeString('en-US', { hour: '2-digit' })
        : date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      total: Math.floor(50 + Math.random() * 100),
    });
  }
  
  return trends;
}

/**
 * Generate mock regions data
 */
function generateMockRegions() {
  return [
    { name: 'Middle East', event_count: 187, dominant_threat: 'high', trend: 12 },
    { name: 'Sub-Saharan Africa', event_count: 156, dominant_threat: 'critical', trend: 8 },
    { name: 'South Asia', event_count: 134, dominant_threat: 'medium', trend: -3 },
    { name: 'Eastern Europe', event_count: 98, dominant_threat: 'high', trend: 25 },
    { name: 'Latin America', event_count: 87, dominant_threat: 'medium', trend: -8 },
    { name: 'Southeast Asia', event_count: 76, dominant_threat: 'low', trend: 2 },
  ];
}

/**
 * Generate mock activities
 */
function generateMockActivities() {
  return [
    { icon: '🔴', text: 'Critical threat detected in Middle East region', time: '2 min ago' },
    { icon: '✓', text: 'Analyst verified 5 events in Sub-Saharan Africa', time: '15 min ago' },
    { icon: '📡', text: 'New data source connected: WHO Outbreak Feed', time: '1 hour ago' },
    { icon: '⚠️', text: 'Potential disinformation flagged for review', time: '2 hours ago' },
    { icon: '📊', text: 'Weekly threat report generated', time: '3 hours ago' },
    { icon: '🌍', text: 'New region added to monitoring: Central Asia', time: '5 hours ago' },
  ];
}
