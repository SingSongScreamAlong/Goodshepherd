/**
 * Event Map Page - Geospatial visualization of intelligence events.
 */
import { useState } from 'react';
import { useEvents } from '../hooks/useEvents';
import MapView from '../components/MapView';
import EventFilters from '../components/EventFilters';
import EmptyState, { EmptyIcons } from '../components/EmptyState';
import { EventFilters as EventFiltersType } from '../types';

export default function EventMap() {
  const [filters, setFilters] = useState<EventFiltersType>({
    page: 1,
    page_size: 1000, // Load more events for map view
  });

  const { events, total, isLoading, error } = useEvents(filters);

  const handleFilterChange = (newFilters: EventFiltersType) => {
    setFilters({
      ...newFilters,
      page_size: 1000, // Maintain larger page size for map
    });
  };

  // Count events with valid geolocation
  const mappableEvents = events.filter(
    (event) => event.location_lat !== null && event.location_lon !== null
  );
  const unmappableCount = events.length - mappableEvents.length;

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Event Map</h1>
        <p className="text-gray-600">
          Geospatial visualization of intelligence events across Europe
        </p>
      </div>

      <EventFilters filters={filters} onChange={handleFilterChange} />

      {/* Statistics */}
      <div className="mb-4 flex items-center justify-between">
        <div className="text-sm text-gray-600">
          Showing {mappableEvents.length} of {total} events
          {unmappableCount > 0 && (
            <span className="ml-2 text-gray-500">
              ({unmappableCount} without location data)
            </span>
          )}
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-600"></div>
            <span className="text-xs text-gray-600">Crime</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-orange-600"></div>
            <span className="text-xs text-gray-600">Protest</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-purple-600"></div>
            <span className="text-xs text-gray-600">Religious Freedom</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-600"></div>
            <span className="text-xs text-gray-600">Political</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-teal-600"></div>
            <span className="text-xs text-gray-600">Migration</span>
          </div>
        </div>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <svg
              className="w-5 h-5 text-red-600 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Map */}
      {!isLoading && !error && (
        <div className="mb-6">
          {mappableEvents.length > 0 ? (
            <MapView events={mappableEvents} />
          ) : (
            <EmptyState
              icon={EmptyIcons.Map}
              title="No events to display"
              description={
                events.length > 0
                  ? 'None of the filtered events have location data available. Try adjusting your filters or wait for more events with geocoded locations.'
                  : 'Try adjusting your filters to see events on the map, or wait for the RSS worker to ingest geolocated events.'
              }
            />
          )}
        </div>
      )}

      {/* Map usage tip */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg
              className="h-5 w-5 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Map Tips</h3>
            <div className="mt-2 text-sm text-blue-700">
              <ul className="list-disc list-inside space-y-1">
                <li>Click on markers to see detailed event information</li>
                <li>Use filters above to focus on specific event types or locations</li>
                <li>Markers with a white center indicate multi-source clustered events</li>
                <li>Zoom and pan to explore different regions</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
