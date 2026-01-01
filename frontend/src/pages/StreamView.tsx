/**
 * Stream View - Main timeline of intelligence events.
 * Dark theme with glass-morphism cards.
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
    <div className="max-w-4xl mx-auto animate-fade-in">
      <div className="page-header">
        <h1 className="text-3xl font-bold text-white mb-2">
          Event Stream
        </h1>
        <p className="text-gray-400">
          Real-time intelligence events from across Europe
        </p>
      </div>

      <EventFilters filters={filters} onChange={handleFilterChange} />

      {/* Loading state */}
      {isLoading && events.length === 0 && (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-2 border-primary-500 border-t-transparent"></div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="glass-card border-red-500/30 p-4 mb-6">
          <div className="flex items-center">
            <svg
              className="w-5 h-5 text-red-400 mr-2"
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
            <p className="text-sm text-red-400">{error}</p>
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
          <div className="mb-4 text-sm text-gray-400">
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
                className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
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
