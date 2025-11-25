/**
 * Stream View - Main timeline of intelligence events.
 */
import { useState } from 'react';
import { useEvents } from '../hooks/useEvents';
import EventCard from '../components/EventCard';
import EventFilters from '../components/EventFilters';
import EmptyState, { EmptyIcons } from '../components/EmptyState';
import { EventFilters as EventFiltersType } from '../types';

export default function StreamView() {
  const [filters, setFilters] = useState<EventFiltersType>({
    page: 1,
    page_size: 20,
  });

  const { events, total, isLoading, error } = useEvents(filters);

  const handleFilterChange = (newFilters: EventFiltersType) => {
    setFilters(newFilters);
  };

  const handleLoadMore = () => {
    setFilters({
      ...filters,
      page: (filters.page || 1) + 1,
    });
  };

  const totalPages = Math.ceil(total / (filters.page_size || 20));
  const hasMore = (filters.page || 1) < totalPages;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Event Stream
        </h1>
        <p className="text-gray-600">
          Real-time intelligence events from across Europe
        </p>
      </div>

      <EventFilters filters={filters} onChange={handleFilterChange} />

      {/* Loading state */}
      {isLoading && events.length === 0 && (
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

      {/* Events list */}
      {!isLoading && events.length === 0 && !error && (
        <EmptyState
          icon={EmptyIcons.Events}
          title="No events found"
          description="Try adjusting your filters or check back later for new events. The RSS worker ingests events continuously from configured feeds."
        />
      )}

      {events.length > 0 && (
        <>
          {/* Results summary */}
          <div className="mb-4 text-sm text-gray-600">
            Showing {events.length} of {total} events
            {filters.page && filters.page > 1 && (
              <> (Page {filters.page} of {totalPages})</>
            )}
          </div>

          {/* Event cards */}
          <div className="space-y-4 mb-6">
            {events.map((event) => (
              <EventCard key={event.event_id} event={event} />
            ))}
          </div>

          {/* Load more button */}
          {hasMore && (
            <div className="flex justify-center">
              <button
                onClick={handleLoadMore}
                disabled={isLoading}
                className="px-6 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Loading...' : 'Load More'}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
