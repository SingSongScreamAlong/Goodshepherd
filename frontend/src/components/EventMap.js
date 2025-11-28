import React, { useCallback, useMemo, useRef, useState } from 'react';
import Map, { Marker, Popup, NavigationControl, ScaleControl } from 'react-map-gl/maplibre';
import { AlertTriangle, MapPin, Shield, Info } from 'lucide-react';
import 'maplibre-gl/dist/maplibre-gl.css';

// Threat level colors matching Tailwind config
const THREAT_COLORS = {
  low: '#22c55e',      // green-500
  medium: '#eab308',   // yellow-500
  high: '#f97316',     // orange-500
  critical: '#ef4444', // red-500
  unknown: '#6b7280',  // gray-500
};

// Default map center (Europe)
const DEFAULT_CENTER = {
  longitude: 10.0,
  latitude: 50.0,
};

const DEFAULT_ZOOM = 4;

/**
 * Get marker icon based on threat level
 */
function ThreatMarker({ threatLevel, size = 24 }) {
  const color = THREAT_COLORS[threatLevel?.toLowerCase()] || THREAT_COLORS.unknown;
  
  if (threatLevel === 'critical') {
    return <AlertTriangle size={size} color={color} fill={color} fillOpacity={0.3} />;
  }
  if (threatLevel === 'high') {
    return <Shield size={size} color={color} fill={color} fillOpacity={0.3} />;
  }
  return <MapPin size={size} color={color} fill={color} fillOpacity={0.3} />;
}

/**
 * Format date for display
 */
function formatDate(dateString) {
  if (!dateString) return 'Unknown';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Extract coordinates from event geocode data
 */
function getEventCoordinates(event) {
  if (!event.geocode) return null;
  
  const { lat, lon, latitude, longitude } = event.geocode;
  const parsedLat = parseFloat(lat ?? latitude);
  const parsedLon = parseFloat(lon ?? longitude);
  
  if (isNaN(parsedLat) || isNaN(parsedLon)) return null;
  
  return { latitude: parsedLat, longitude: parsedLon };
}

/**
 * Event popup component
 */
function EventPopup({ event, onClose }) {
  const threatLevel = event.threat_level?.toLowerCase() || 'unknown';
  const threatColor = THREAT_COLORS[threatLevel];
  
  return (
    <div className="max-w-xs">
      <div className="flex items-start gap-2 mb-2">
        <ThreatMarker threatLevel={threatLevel} size={20} />
        <h3 className="font-semibold text-sm text-gray-900 leading-tight">
          {event.title || 'Untitled Event'}
        </h3>
      </div>
      
      <div className="space-y-1 text-xs text-gray-600">
        {event.region && (
          <p><span className="font-medium">Region:</span> {event.region}</p>
        )}
        {event.category && (
          <p><span className="font-medium">Category:</span> {event.category}</p>
        )}
        <p>
          <span className="font-medium">Threat:</span>{' '}
          <span style={{ color: threatColor }} className="font-semibold capitalize">
            {threatLevel}
          </span>
        </p>
        {event.credibility_score !== undefined && (
          <p>
            <span className="font-medium">Credibility:</span>{' '}
            {(event.credibility_score * 100).toFixed(0)}%
          </p>
        )}
        <p>
          <span className="font-medium">Time:</span> {formatDate(event.published_at || event.fetched_at)}
        </p>
      </div>
      
      {event.summary && (
        <p className="mt-2 text-xs text-gray-700 line-clamp-3">
          {event.summary}
        </p>
      )}
      
      {event.link && (
        <a
          href={event.link}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
        >
          <Info size={12} />
          View Source
        </a>
      )}
    </div>
  );
}

/**
 * Main EventMap component
 */
export default function EventMap({ 
  events = [], 
  onEventSelect,
  height = 400,
  className = '',
}) {
  const mapRef = useRef(null);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [viewState, setViewState] = useState({
    longitude: DEFAULT_CENTER.longitude,
    latitude: DEFAULT_CENTER.latitude,
    zoom: DEFAULT_ZOOM,
  });

  // Filter events with valid coordinates
  const mappableEvents = useMemo(() => {
    return events
      .map(event => ({
        ...event,
        coordinates: getEventCoordinates(event),
      }))
      .filter(event => event.coordinates !== null);
  }, [events]);

  // Handle marker click
  const handleMarkerClick = useCallback((event) => {
    setSelectedEvent(event);
    if (onEventSelect) {
      onEventSelect(event);
    }
  }, [onEventSelect]);

  // Close popup
  const handlePopupClose = useCallback(() => {
    setSelectedEvent(null);
  }, []);

  // Fit map to events
  const fitToEvents = useCallback(() => {
    if (mappableEvents.length === 0 || !mapRef.current) return;

    const lngs = mappableEvents.map(e => e.coordinates.longitude);
    const lats = mappableEvents.map(e => e.coordinates.latitude);

    const bounds = [
      [Math.min(...lngs), Math.min(...lats)],
      [Math.max(...lngs), Math.max(...lats)],
    ];

    mapRef.current.fitBounds(bounds, {
      padding: 50,
      maxZoom: 10,
      duration: 1000,
    });
  }, [mappableEvents]);

  return (
    <div className={`relative ${className}`} style={{ height }}>
      <Map
        ref={mapRef}
        {...viewState}
        onMove={evt => setViewState(evt.viewState)}
        style={{ width: '100%', height: '100%' }}
        mapStyle="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
        attributionControl={false}
      >
        <NavigationControl position="top-right" />
        <ScaleControl position="bottom-left" />

        {/* Event markers */}
        {mappableEvents.map((event) => (
          <Marker
            key={event.id}
            longitude={event.coordinates.longitude}
            latitude={event.coordinates.latitude}
            anchor="center"
            onClick={(e) => {
              e.originalEvent.stopPropagation();
              handleMarkerClick(event);
            }}
            style={{ cursor: 'pointer' }}
          >
            <ThreatMarker threatLevel={event.threat_level} size={28} />
          </Marker>
        ))}

        {/* Selected event popup */}
        {selectedEvent && selectedEvent.coordinates && (
          <Popup
            longitude={selectedEvent.coordinates.longitude}
            latitude={selectedEvent.coordinates.latitude}
            anchor="bottom"
            onClose={handlePopupClose}
            closeButton={true}
            closeOnClick={false}
            className="event-popup"
          >
            <EventPopup event={selectedEvent} onClose={handlePopupClose} />
          </Popup>
        )}
      </Map>

      {/* Map controls overlay */}
      <div className="absolute top-2 left-2 flex gap-2">
        <button
          onClick={fitToEvents}
          disabled={mappableEvents.length === 0}
          className="px-3 py-1.5 bg-white rounded-md shadow-sm border border-gray-200 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Fit to Events
        </button>
        <div className="px-3 py-1.5 bg-white rounded-md shadow-sm border border-gray-200 text-xs text-gray-600">
          {mappableEvents.length} / {events.length} events mapped
        </div>
      </div>

      {/* Legend */}
      <div className="absolute bottom-8 right-2 bg-white rounded-md shadow-sm border border-gray-200 p-2">
        <div className="text-xs font-medium text-gray-700 mb-1">Threat Level</div>
        <div className="space-y-1">
          {Object.entries(THREAT_COLORS).filter(([k]) => k !== 'unknown').map(([level, color]) => (
            <div key={level} className="flex items-center gap-2 text-xs">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
              <span className="capitalize">{level}</span>
            </div>
          ))}
        </div>
      </div>

      {/* No events message */}
      {events.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100/80">
          <div className="text-center text-gray-500">
            <MapPin size={48} className="mx-auto mb-2 opacity-50" />
            <p className="font-medium">No events to display</p>
            <p className="text-sm">Events with location data will appear here</p>
          </div>
        </div>
      )}
    </div>
  );
}
