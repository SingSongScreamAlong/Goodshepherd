/**
 * Custom hook for fetching and managing events.
 */
import { useState, useEffect } from 'react';
import { apiClient } from '../utils/api';
import { Event, EventListResponse, EventFilters } from '../types';

export function useEvents(filters: EventFilters = {}) {
  const [events, setEvents] = useState<Event[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchEvents();
  }, [JSON.stringify(filters)]);

  const fetchEvents = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Build query string
      const params = new URLSearchParams();

      if (filters.category) params.append('category', filters.category);
      if (filters.sentiment) params.append('sentiment', filters.sentiment);
      if (filters.location_name) params.append('location_name', filters.location_name);
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      if (filters.min_relevance !== undefined) params.append('min_relevance', filters.min_relevance.toString());
      if (filters.page) params.append('page', filters.page.toString());
      if (filters.page_size) params.append('page_size', filters.page_size.toString());

      const queryString = params.toString();
      const url = `/events${queryString ? `?${queryString}` : ''}`;

      const response = await apiClient.get<EventListResponse>(url);

      setEvents(response.events);
      setTotal(response.total);
    } catch (err: any) {
      console.error('Failed to fetch events:', err);
      setError(err.message || 'Failed to fetch events');
    } finally {
      setIsLoading(false);
    }
  };

  const refetch = () => {
    fetchEvents();
  };

  return {
    events,
    total,
    isLoading,
    error,
    refetch,
  };
}
