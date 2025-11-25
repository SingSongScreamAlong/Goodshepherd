/**
 * Dashboard page - "Today's Picture" with analytics and trends.
 */
import { useDashboard } from '../hooks/useDashboard';
import StatCard from '../components/StatCard';
import InfoTooltip from '../components/InfoTooltip';
import EmptyState, { EmptyIcons } from '../components/EmptyState';
import { getCategoryLabel, getCategoryColor } from '../utils/formatting';
import { formatRelativeTime } from '../utils/formatting';

export default function Dashboard() {
  const { summary, isLoading, error } = useDashboard();

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      </div>
    );
  }

  if (!summary) {
    return null;
  }

  // Calculate trend (comparing today vs week average)
  const weekAverage = summary.events_week / 7;
  const todayVsAverage = weekAverage > 0
    ? ((summary.events_today - weekAverage) / weekAverage) * 100
    : 0;

  // Check if we have any data at all
  const hasAnyData = summary.total_events > 0;

  if (!hasAnyData) {
    return (
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
          <p className="text-gray-600">Today's intelligence picture and recent trends</p>
        </div>
        <EmptyState
          icon={EmptyIcons.Dashboard}
          title="No intelligence data yet"
          description="Once the RSS worker starts ingesting events, your dashboard will populate with metrics, trends, and high-priority events. Configure your RSS feeds and start the worker to begin."
        />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
        <p className="text-gray-600">Today's intelligence picture and recent trends</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <StatCard
          label={
            <span className="flex items-center space-x-1">
              <span>Events Today</span>
              <InfoTooltip content="Total intelligence events from the last 24 hours. Events are GLOBAL (shared across all organizations)." />
            </span>
          }
          value={summary.events_today}
          color="blue"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          }
          trend={{
            value: Math.abs(Math.round(todayVsAverage)),
            direction: todayVsAverage > 0 ? 'up' : todayVsAverage < 0 ? 'down' : 'neutral',
          }}
        />

        <StatCard
          label={
            <span className="flex items-center space-x-1">
              <span>High Relevance Today</span>
              <InfoTooltip content="Events with relevance score ≥ 0.7. Relevance is higher for safety-related categories (crime, protest, health, religious freedom)." />
            </span>
          }
          value={summary.high_relevance_today}
          color="red"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          }
        />

        <StatCard
          label={
            <span className="flex items-center space-x-1">
              <span>Events This Week</span>
              <InfoTooltip content="Total events from the last 7 days. Trend shows comparison to previous week average." />
            </span>
          }
          value={summary.events_week}
          color="green"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          }
        />

        <StatCard
          label={
            <span className="flex items-center space-x-1">
              <span>Active Dossiers</span>
              <InfoTooltip content="Dossiers with events in the last 7 days vs total dossiers. Dossiers are organization-specific." />
            </span>
          }
          value={`${summary.active_dossiers}/${summary.total_dossiers}`}
          color="purple"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          }
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Category Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center space-x-2 mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Category Distribution (7 Days)
            </h2>
            <InfoTooltip content="Breakdown of events by category over the last week. Categories include protest, crime, religious freedom, migration, and more." />
          </div>
          {Object.keys(summary.category_distribution).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(summary.category_distribution)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 6)
                .map(([category, count]) => (
                  <div key={category} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 text-xs font-medium rounded ${getCategoryColor(category as any)}`}>
                        {getCategoryLabel(category as any)}
                      </span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-primary-600 h-2 rounded-full"
                          style={{
                            width: `${(count / summary.events_week) * 100}%`,
                          }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium text-gray-900 w-8 text-right">
                        {count}
                      </span>
                    </div>
                  </div>
                ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 text-center py-8">No events in the last 7 days</p>
          )}
        </div>

        {/* Sentiment Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center space-x-2 mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Sentiment Distribution (7 Days)
            </h2>
            <InfoTooltip content="Sentiment analysis classifies events as positive, neutral, or negative based on LLM analysis of event text." />
          </div>
          {Object.keys(summary.sentiment_distribution).length > 0 ? (
            <div className="space-y-4">
              {Object.entries(summary.sentiment_distribution).map(([sentiment, count]) => {
                const total = Object.values(summary.sentiment_distribution).reduce((a, b) => a + b, 0);
                const percentage = ((count / total) * 100).toFixed(1);
                const colors = {
                  positive: 'bg-green-500',
                  neutral: 'bg-gray-500',
                  negative: 'bg-red-500',
                };

                return (
                  <div key={sentiment}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700 capitalize">
                        {sentiment}
                      </span>
                      <span className="text-sm text-gray-600">
                        {count} ({percentage}%)
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${colors[sentiment as keyof typeof colors]}`}
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-gray-500 text-center py-8">No sentiment data available</p>
          )}
        </div>
      </div>

      {/* Top Locations */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-center space-x-2 mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Most Active Locations (7 Days)
          </h2>
          <InfoTooltip content="Geographic locations with the most event activity in the last week." />
        </div>
        {summary.top_locations.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {summary.top_locations.map((loc, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <svg className="w-5 h-5 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span className="text-sm font-medium text-gray-900">{loc.location}</span>
                </div>
                <span className="text-sm text-gray-600 font-semibold">{loc.count}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500 text-center py-8">No location data available</p>
        )}
      </div>

      {/* Recent Highlights */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Today's High-Priority Events
          </h2>
          <InfoTooltip content="Events from today with high relevance scores (≥0.7). These require immediate attention." />
        </div>
        {summary.recent_highlights.length > 0 ? (
          <div className="space-y-3">
            {summary.recent_highlights.map((event) => (
              <div key={event.event_id} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div className="flex-shrink-0">
                  <div className="w-2 h-2 mt-2 bg-red-500 rounded-full"></div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    {event.category && (
                      <span className={`px-2 py-0.5 text-xs font-medium rounded ${getCategoryColor(event.category as any)}`}>
                        {getCategoryLabel(event.category as any)}
                      </span>
                    )}
                    <span className="text-xs text-gray-500">
                      {formatRelativeTime(event.timestamp)}
                    </span>
                    {event.relevance_score && (
                      <span className="text-xs text-gray-500">
                        Relevance: {(event.relevance_score * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-900">{event.summary}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500 text-center py-8">
            No high-priority events today. Check back later or adjust your relevance threshold.
          </p>
        )}
      </div>
    </div>
  );
}
