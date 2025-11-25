/**
 * Hook for dashboard data.
 */
import { useState, useEffect } from 'react';
import { apiClient } from '../utils/api';
import { DashboardSummary, TrendsData } from '../types';

export function useDashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<DashboardSummary>('/dashboard/summary');
      setSummary(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch dashboard data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  return {
    summary,
    isLoading,
    error,
    refetch: fetchSummary,
  };
}

export function useTrends(days: number = 30) {
  const [trends, setTrends] = useState<TrendsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTrends = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<TrendsData>('/dashboard/trends', {
        params: { days },
      });
      setTrends(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch trends data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTrends();
  }, [days]);

  return {
    trends,
    isLoading,
    error,
    refetch: fetchTrends,
  };
}
