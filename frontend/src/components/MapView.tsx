/**
 * MapView component - Displays events on an interactive map with clustering.
 */
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { Icon, LatLngExpression, latLngBounds, LatLngTuple } from 'leaflet';
import { useEffect } from 'react';
import { Event } from '../types';
import {
  formatRelativeTime,
  formatDate,
  getCategoryColor,
  getCategoryLabel,
  getSentimentLabel,
} from '../utils/formatting';
import 'leaflet/dist/leaflet.css';

interface MapViewProps {
  events: Event[];
  center?: LatLngExpression;
  zoom?: number;
}

// Fix for default marker icons in Leaflet with webpack
delete (Icon.Default.prototype as any)._getIconUrl;
Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Component to handle map bounds updates
function MapBounds({ events }: { events: Event[] }) {
  const map = useMap();

  useEffect(() => {
    if (events.length > 0) {
      const coords = events
        .filter((e) => e.location_lat && e.location_lon)
        .map((e) => [e.location_lat!, e.location_lon!] as LatLngTuple);

      if (coords.length > 0) {
        const bounds = latLngBounds(coords);
        map.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 });
      }
    }
  }, [events, map]);

  return null;
}

// Get marker color based on category and sentiment
function getMarkerColor(event: Event): string {
  // High priority categories get distinct colors
  const categoryColors: Record<string, string> = {
    crime: '#dc2626', // red
    protest: '#ea580c', // orange
    religious_freedom: '#7c3aed', // purple
    cultural_tension: '#eab308', // yellow
    health: '#ec4899', // pink
    infrastructure: '#6b7280', // gray
    political: '#3b82f6', // blue
    migration: '#14b8a6', // teal
    economic: '#10b981', // green
    weather: '#06b6d4', // cyan
    community_event: '#8b5cf6', // violet
    other: '#64748b', // slate
  };

  return categoryColors[event.category] || '#64748b';
}

// Create custom marker icon
function createCustomIcon(event: Event) {
  const color = getMarkerColor(event);
  const isCluster = !!event.cluster_id;

  const svgIcon = `
    <svg width="25" height="41" viewBox="0 0 25 41" xmlns="http://www.w3.org/2000/svg">
      <path fill="${color}" stroke="#fff" stroke-width="2" d="M12.5 0C5.6 0 0 5.6 0 12.5c0 8.7 12.5 28.5 12.5 28.5S25 21.2 25 12.5C25 5.6 19.4 0 12.5 0z"/>
      ${isCluster ? '<circle cx="12.5" cy="12.5" r="4" fill="#fff"/>' : '<circle cx="12.5" cy="12.5" r="3" fill="#fff"/>'}
    </svg>
  `;

  return new Icon({
    iconUrl: 'data:image/svg+xml;base64,' + btoa(svgIcon),
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
  });
}

export default function MapView({ events, center = [50.8503, 4.3517], zoom = 5 }: MapViewProps) {
  // Filter events that have valid coordinates
  const mappableEvents = events.filter(
    (event) => event.location_lat !== null && event.location_lon !== null
  );

  return (
    <div className="relative w-full h-full min-h-[500px] rounded-lg overflow-hidden shadow-lg">
      <MapContainer
        center={center}
        zoom={zoom}
        className="h-full w-full z-0"
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {mappableEvents.map((event) => (
          <Marker
            key={event.event_id}
            position={[event.location_lat!, event.location_lon!]}
            icon={createCustomIcon(event)}
          >
            <Popup maxWidth={400} className="custom-popup">
              <div className="p-2">
                {/* Category and sentiment badges */}
                <div className="flex items-center gap-2 mb-2">
                  <span
                    className={`px-2 py-1 text-xs font-medium rounded ${getCategoryColor(
                      event.category
                    )}`}
                  >
                    {getCategoryLabel(event.category)}
                  </span>
                  {event.sentiment && (
                    <span className="text-xs text-gray-600">
                      {getSentimentLabel(event.sentiment)}
                    </span>
                  )}
                </div>

                {/* Title/Summary */}
                <h3 className="font-semibold text-sm mb-2 text-gray-900">
                  {event.summary}
                </h3>

                {/* Location and time */}
                <div className="text-xs text-gray-600 mb-2">
                  <div className="flex items-center gap-1 mb-1">
                    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span>{event.location_name}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span title={formatDate(event.timestamp)}>
                      {formatRelativeTime(event.timestamp)}
                    </span>
                  </div>
                </div>

                {/* Entities */}
                {event.entity_list && (
                  <div className="mb-2">
                    {event.entity_list.locations && event.entity_list.locations.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-1">
                        {event.entity_list.locations.slice(0, 3).map((loc, idx) => (
                          <span
                            key={idx}
                            className="px-1.5 py-0.5 text-xs bg-blue-50 text-blue-700 rounded"
                          >
                            {loc}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Cluster indicator */}
                {event.cluster_id && (
                  <div className="mt-2 pt-2 border-t border-gray-200">
                    <p className="text-xs text-gray-500">
                      <span className="font-medium">Multi-source event</span>
                    </p>
                  </div>
                )}

                {/* Scores */}
                <div className="flex justify-between mt-2 pt-2 border-t border-gray-200 text-xs">
                  {event.relevance_score !== undefined && (
                    <span className="text-gray-600">
                      Relevance: <span className="font-medium">{(event.relevance_score * 100).toFixed(0)}%</span>
                    </span>
                  )}
                  {event.confidence_score !== undefined && (
                    <span className="text-gray-600">
                      Confidence: <span className="font-medium">{(event.confidence_score * 100).toFixed(0)}%</span>
                    </span>
                  )}
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

        <MapBounds events={mappableEvents} />
      </MapContainer>

      {/* Event count overlay */}
      <div className="absolute top-4 left-4 z-[1000] bg-white rounded-lg shadow-md px-3 py-2">
        <p className="text-sm font-medium text-gray-900">
          {mappableEvents.length} {mappableEvents.length === 1 ? 'event' : 'events'} on map
        </p>
      </div>
    </div>
  );
}
