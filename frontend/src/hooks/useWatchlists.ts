/**
 * Hook for managing watchlists.
 */
import { useState, useEffect } from 'react';
import { apiClient } from '../utils/api';
import { Watchlist, WatchlistWithDossiers, WatchlistCreate } from '../types';

export function useWatchlists() {
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchWatchlists = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<Watchlist[]>('/watchlists');
      setWatchlists(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch watchlists');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchWatchlists();
  }, []);

  const createWatchlist = async (data: WatchlistCreate): Promise<Watchlist> => {
    const response = await apiClient.post<Watchlist>('/watchlists', data);
    await fetchWatchlists(); // Refresh list
    return response;
  };

  const getWatchlist = async (id: string): Promise<WatchlistWithDossiers> => {
    return await apiClient.get<WatchlistWithDossiers>(`/watchlists/${id}`);
  };

  const updateWatchlist = async (
    id: string,
    data: Partial<WatchlistCreate>
  ): Promise<Watchlist> => {
    const response = await apiClient.patch<Watchlist>(`/watchlists/${id}`, data);
    await fetchWatchlists(); // Refresh list
    return response;
  };

  const deleteWatchlist = async (id: string): Promise<void> => {
    await apiClient.delete(`/watchlists/${id}`);
    await fetchWatchlists(); // Refresh list
  };

  return {
    watchlists,
    isLoading,
    error,
    createWatchlist,
    getWatchlist,
    updateWatchlist,
    deleteWatchlist,
    refetch: fetchWatchlists,
  };
}
