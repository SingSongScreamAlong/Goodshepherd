import React, { useState, useEffect, useCallback } from 'react';
import {
  Bell,
  BellOff,
  Check,
  AlertTriangle,
  Shield,
  Clock,
  MapPin,
  ExternalLink,
  Loader2,
  RefreshCw,
  Filter,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import {
  getUnacknowledgedAlerts,
  acknowledgeAlert,
} from '../../services/notificationService';

const PRIORITY_COLORS = {
  critical: 'bg-red-100 border-red-300 text-red-800',
  high: 'bg-orange-100 border-orange-300 text-orange-800',
  medium: 'bg-yellow-100 border-yellow-300 text-yellow-800',
  low: 'bg-green-100 border-green-300 text-green-800',
};

const PRIORITY_ICONS = {
  critical: AlertTriangle,
  high: Shield,
  medium: Bell,
  low: Check,
};

/**
 * Single alert card component
 */
function AlertCard({ alert, onAcknowledge, acknowledging }) {
  const [expanded, setExpanded] = useState(false);
  const [notes, setNotes] = useState('');

  const event = alert.event;
  const priority = event.threat_level || 'medium';
  const PriorityIcon = PRIORITY_ICONS[priority] || Bell;
  const colorClass = PRIORITY_COLORS[priority] || PRIORITY_COLORS.medium;

  const handleAcknowledge = async () => {
    await onAcknowledge(alert.event_id, notes || null);
  };

  return (
    <div className={`rounded-lg border-2 ${colorClass} overflow-hidden transition-all`}>
      {/* Header */}
      <div
        className="p-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <PriorityIcon className="w-5 h-5 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="font-semibold text-gray-900 line-clamp-2">
                {event.title}
              </h4>
              <div className="flex items-center gap-3 mt-1 text-sm text-gray-600">
                {event.region && (
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3 h-3" />
                    {event.region}
                  </span>
                )}
                {alert.sent_at && (
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(alert.sent_at).toLocaleString()}
                  </span>
                )}
              </div>
            </div>
          </div>
          <button className="p-1 hover:bg-white/50 rounded">
            {expanded ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-current/10">
          {event.summary && (
            <p className="text-sm text-gray-700 mt-3">{event.summary}</p>
          )}

          <div className="flex flex-wrap gap-2 text-xs">
            {event.category && (
              <span className="px-2 py-1 bg-white/50 rounded-full">
                {event.category}
              </span>
            )}
            <span className="px-2 py-1 bg-white/50 rounded-full">
              via {alert.channel}
            </span>
          </div>

          {event.link && (
            <a
              href={event.link}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm text-blue-700 hover:underline"
            >
              View source <ExternalLink className="w-3 h-3" />
            </a>
          )}

          {/* Acknowledge form */}
          <div className="pt-3 border-t border-current/10 space-y-2">
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add notes (optional)"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 resize-none"
              rows={2}
            />
            <button
              onClick={handleAcknowledge}
              disabled={acknowledging}
              className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 transition-colors text-sm"
            >
              {acknowledging ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Check className="w-4 h-4" />
              )}
              Acknowledge Alert
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Alerts Panel Component
 */
export default function AlertsPanel() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [acknowledging, setAcknowledging] = useState(null);
  const [filter, setFilter] = useState('all');

  // Load alerts
  const loadAlerts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getUnacknowledgedAlerts();
      setAlerts(data);
    } catch (err) {
      setError('Failed to load alerts');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAlerts();
  }, [loadAlerts]);

  // Acknowledge an alert
  const handleAcknowledge = async (eventId, notes) => {
    setAcknowledging(eventId);
    try {
      await acknowledgeAlert(eventId, notes);
      setAlerts((prev) => prev.filter((a) => a.event_id !== eventId));
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    } finally {
      setAcknowledging(null);
    }
  };

  // Filter alerts
  const filteredAlerts = alerts.filter((alert) => {
    if (filter === 'all') return true;
    return alert.event.threat_level === filter;
  });

  // Count by priority
  const counts = alerts.reduce((acc, alert) => {
    const level = alert.event.threat_level || 'medium';
    acc[level] = (acc[level] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Bell className="w-6 h-6 text-gray-700" />
          <div>
            <h2 className="text-lg font-bold text-gray-900">
              Pending Alerts
              {alerts.length > 0 && (
                <span className="ml-2 px-2 py-0.5 text-sm bg-red-100 text-red-700 rounded-full">
                  {alerts.length}
                </span>
              )}
            </h2>
            <p className="text-sm text-gray-500">
              Alerts requiring your acknowledgment
            </p>
          </div>
        </div>
        <button
          onClick={loadAlerts}
          disabled={loading}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          title="Refresh"
        >
          <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        <button
          onClick={() => setFilter('all')}
          className={`px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
            filter === 'all'
              ? 'bg-gray-900 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          All ({alerts.length})
        </button>
        {['critical', 'high', 'medium', 'low'].map((level) => (
          <button
            key={level}
            onClick={() => setFilter(level)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
              filter === level
                ? 'bg-gray-900 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {level.charAt(0).toUpperCase() + level.slice(1)} ({counts[level] || 0})
          </button>
        ))}
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          {error}
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      )}

      {/* Empty state */}
      {!loading && filteredAlerts.length === 0 && (
        <div className="text-center py-12">
          <BellOff className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">
            {alerts.length === 0
              ? 'No pending alerts'
              : 'No alerts match the selected filter'}
          </p>
        </div>
      )}

      {/* Alert list */}
      {!loading && filteredAlerts.length > 0 && (
        <div className="space-y-3">
          {filteredAlerts.map((alert) => (
            <AlertCard
              key={alert.notification_id}
              alert={alert}
              onAcknowledge={handleAcknowledge}
              acknowledging={acknowledging === alert.event_id}
            />
          ))}
        </div>
      )}
    </div>
  );
}
