import React, { useCallback, useEffect, useState } from 'react';
import {
  AlertTriangle,
  Shield,
  MapPin,
  Phone,
  CheckCircle,
  Bell,
  RefreshCw,
  ChevronRight,
  Wifi,
  WifiOff,
  Clock,
  Users,
  Navigation,
} from 'lucide-react';
import { useWebSocket, ConnectionState } from '../hooks/useWebSocket';
import { useOfflineFirst } from '../hooks/useOfflineFirst';
import { AlertToastContainer } from './AlertToast';
import EventMap from './EventMap';

// Threat level configurations
const THREAT_CONFIG = {
  critical: {
    color: 'bg-red-500',
    textColor: 'text-red-700',
    bgLight: 'bg-red-50',
    border: 'border-red-200',
    icon: AlertTriangle,
    label: 'CRITICAL',
  },
  high: {
    color: 'bg-orange-500',
    textColor: 'text-orange-700',
    bgLight: 'bg-orange-50',
    border: 'border-orange-200',
    icon: Shield,
    label: 'HIGH',
  },
  medium: {
    color: 'bg-yellow-500',
    textColor: 'text-yellow-700',
    bgLight: 'bg-yellow-50',
    border: 'border-yellow-200',
    icon: Bell,
    label: 'MEDIUM',
  },
  low: {
    color: 'bg-green-500',
    textColor: 'text-green-700',
    bgLight: 'bg-green-50',
    border: 'border-green-200',
    icon: CheckCircle,
    label: 'LOW',
  },
};

/**
 * Mobile-optimized dashboard for field missionaries
 */
export default function MissionaryDashboard() {
  const [events, setEvents] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRegion, setSelectedRegion] = useState(null);
  const [showMap, setShowMap] = useState(false);
  const [checkInStatus, setCheckInStatus] = useState(null);

  // Offline-first data management
  const {
    online,
    syncing,
    lastSync,
    pendingActions,
    fetchEvents,
    handleRealtimeEvent,
    handleRealtimeAlert,
    queueOfflineAction,
  } = useOfflineFirst();

  // WebSocket for real-time updates
  const {
    connectionState,
    connect,
    isConnected,
  } = useWebSocket({
    onEvent: (event) => {
      handleRealtimeEvent(event);
      setEvents(prev => [event, ...prev.slice(0, 49)]);
    },
    onAlert: (alert) => {
      handleRealtimeAlert(alert);
      setAlerts(prev => [{ ...alert, id: Date.now() }, ...prev]);
      // Vibrate on mobile if supported
      if (navigator.vibrate) {
        navigator.vibrate([200, 100, 200]);
      }
    },
  });

  // Load initial data
  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const { events: fetchedEvents } = await fetchEvents('', { limit: 20 });
      setEvents(fetchedEvents);
      setLoading(false);
    }
    loadData();
  }, [fetchEvents]);

  // Dismiss alert
  const dismissAlert = useCallback((alertId) => {
    setAlerts(prev => prev.filter(a => a.id !== alertId));
  }, []);

  // Handle check-in
  const handleCheckIn = useCallback(async () => {
    const checkInData = {
      timestamp: new Date().toISOString(),
      location: null,
    };

    // Try to get location
    if (navigator.geolocation) {
      try {
        const position = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, {
            timeout: 10000,
            enableHighAccuracy: false,
          });
        });
        checkInData.location = {
          lat: position.coords.latitude,
          lon: position.coords.longitude,
          accuracy: position.coords.accuracy,
        };
      } catch (err) {
        console.warn('Could not get location:', err);
      }
    }

    if (online) {
      // Send immediately
      try {
        // API call would go here
        setCheckInStatus('success');
      } catch (err) {
        setCheckInStatus('error');
      }
    } else {
      // Queue for later
      await queueOfflineAction('check_in', checkInData);
      setCheckInStatus('queued');
    }

    // Reset status after 3 seconds
    setTimeout(() => setCheckInStatus(null), 3000);
  }, [online, queueOfflineAction]);

  // Calculate threat summary
  const threatSummary = events.reduce((acc, event) => {
    const level = event.threat_level?.toLowerCase() || 'unknown';
    acc[level] = (acc[level] || 0) + 1;
    return acc;
  }, {});

  // Get highest threat level
  const highestThreat = ['critical', 'high', 'medium', 'low'].find(
    level => threatSummary[level] > 0
  ) || 'low';

  const threatConfig = THREAT_CONFIG[highestThreat];

  return (
    <div className="min-h-screen bg-gray-100 pb-20">
      {/* Alert Toasts */}
      <AlertToastContainer alerts={alerts} onDismiss={dismissAlert} />

      {/* Header */}
      <header className={`${threatConfig.color} text-white px-4 py-3 sticky top-0 z-40`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield size={28} />
            <div>
              <h1 className="font-bold text-lg">Good Shepherd</h1>
              <p className="text-xs opacity-90">Field Safety Monitor</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {online ? (
              <Wifi size={20} className="text-white/80" />
            ) : (
              <WifiOff size={20} className="text-white/80" />
            )}
            {syncing && <RefreshCw size={16} className="animate-spin" />}
          </div>
        </div>
      </header>

      {/* Threat Status Banner */}
      <div className={`${threatConfig.bgLight} ${threatConfig.border} border-b px-4 py-3`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`${threatConfig.color} p-2 rounded-full`}>
              <threatConfig.icon size={24} className="text-white" />
            </div>
            <div>
              <p className={`font-bold ${threatConfig.textColor}`}>
                Threat Level: {threatConfig.label}
              </p>
              <p className="text-sm text-gray-600">
                {events.length} active events in your area
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowMap(!showMap)}
            className="p-2 rounded-full bg-white shadow-sm"
          >
            <MapPin size={20} className="text-gray-600" />
          </button>
        </div>
      </div>

      {/* Map (collapsible) */}
      {showMap && (
        <div className="border-b border-gray-200">
          <EventMap events={events} height={300} />
        </div>
      )}

      {/* Quick Actions */}
      <div className="px-4 py-4 grid grid-cols-2 gap-3">
        {/* Check In Button */}
        <button
          onClick={handleCheckIn}
          disabled={checkInStatus === 'success'}
          className={`
            flex flex-col items-center justify-center p-4 rounded-xl shadow-sm
            transition-all active:scale-95
            ${checkInStatus === 'success' 
              ? 'bg-green-500 text-white' 
              : checkInStatus === 'queued'
              ? 'bg-yellow-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-50'
            }
          `}
        >
          {checkInStatus === 'success' ? (
            <CheckCircle size={32} />
          ) : checkInStatus === 'queued' ? (
            <Clock size={32} />
          ) : (
            <CheckCircle size={32} className="text-green-500" />
          )}
          <span className="mt-2 font-medium text-sm">
            {checkInStatus === 'success' 
              ? "Checked In!" 
              : checkInStatus === 'queued'
              ? "Queued"
              : "I'm Safe"
            }
          </span>
        </button>

        {/* Emergency Contact */}
        <a
          href="tel:+1234567890"
          className="flex flex-col items-center justify-center p-4 rounded-xl bg-red-500 text-white shadow-sm active:scale-95"
        >
          <Phone size={32} />
          <span className="mt-2 font-medium text-sm">Emergency</span>
        </a>

        {/* Team Status */}
        <button className="flex flex-col items-center justify-center p-4 rounded-xl bg-white text-gray-700 shadow-sm active:scale-95">
          <Users size={32} className="text-blue-500" />
          <span className="mt-2 font-medium text-sm">Team Status</span>
        </button>

        {/* Navigate */}
        <button className="flex flex-col items-center justify-center p-4 rounded-xl bg-white text-gray-700 shadow-sm active:scale-95">
          <Navigation size={32} className="text-purple-500" />
          <span className="mt-2 font-medium text-sm">Safe Routes</span>
        </button>
      </div>

      {/* Recent Alerts */}
      <section className="px-4 mb-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-bold text-gray-900">Recent Alerts</h2>
          <span className="text-xs text-gray-500">
            {lastSync ? `Updated ${formatTimeAgo(lastSync)}` : 'Not synced'}
          </span>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="animate-spin text-gray-400" size={24} />
          </div>
        ) : events.length === 0 ? (
          <div className="bg-white rounded-xl p-6 text-center">
            <CheckCircle size={48} className="mx-auto text-green-500 mb-2" />
            <p className="text-gray-600">No active alerts in your area</p>
          </div>
        ) : (
          <div className="space-y-3">
            {events.slice(0, 5).map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        )}

        {events.length > 5 && (
          <button className="w-full mt-3 py-3 text-center text-blue-600 font-medium bg-white rounded-xl shadow-sm">
            View All ({events.length}) Events
          </button>
        )}
      </section>

      {/* Connection Status Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-4 py-2 flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${
            isConnected ? 'bg-green-500' : online ? 'bg-yellow-500' : 'bg-red-500'
          }`} />
          <span className="text-gray-600">
            {isConnected ? 'Live' : online ? 'Connecting...' : 'Offline'}
          </span>
        </div>
        {pendingActions > 0 && (
          <span className="text-yellow-600">
            {pendingActions} pending sync{pendingActions > 1 ? 's' : ''}
          </span>
        )}
        {!isConnected && online && (
          <button onClick={connect} className="text-blue-600 font-medium">
            Reconnect
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Event card component for the list
 */
function EventCard({ event }) {
  const threatLevel = event.threat_level?.toLowerCase() || 'low';
  const config = THREAT_CONFIG[threatLevel] || THREAT_CONFIG.low;
  const Icon = config.icon;

  return (
    <div className={`bg-white rounded-xl shadow-sm overflow-hidden border-l-4 ${config.border.replace('border-', 'border-l-')}`}>
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className={`${config.bgLight} p-2 rounded-lg flex-shrink-0`}>
            <Icon size={20} className={config.textColor} />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 text-sm line-clamp-2">
              {event.title || 'Untitled Event'}
            </h3>
            {event.region && (
              <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                <MapPin size={12} />
                {event.region}
              </p>
            )}
            <p className="text-xs text-gray-400 mt-1">
              {formatTimeAgo(new Date(event.fetched_at || event.published_at))}
            </p>
          </div>
          <ChevronRight size={20} className="text-gray-300 flex-shrink-0" />
        </div>
      </div>
    </div>
  );
}

/**
 * Format time ago string
 */
function formatTimeAgo(date) {
  if (!date) return '';
  const now = new Date();
  const diff = Math.floor((now - new Date(date)) / 1000);

  if (diff < 60) return 'Just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}
