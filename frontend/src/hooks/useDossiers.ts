/**
 * Hook for managing dossiers.
 */
import { useState, useEffect } from 'react';
import { apiClient } from '../utils/api';
import { Dossier, DossierCreate, DossierStats, DossierType } from '../types';

export function useDossiers(dossierType?: DossierType, search?: string) {
  const [dossiers, setDossiers] = useState<Dossier[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDossiers = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params: Record<string, any> = { limit: 100 };
      if (dossierType) params.dossier_type = dossierType;
      if (search) params.search = search;

      const response = await apiClient.get<Dossier[]>('/dossiers', { params });
      setDossiers(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch dossiers');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDossiers();
  }, [dossierType, search]);

  const createDossier = async (data: DossierCreate): Promise<Dossier> => {
    const response = await apiClient.post<Dossier>('/dossiers', data);
    await fetchDossiers(); // Refresh list
    return response;
  };

  const updateDossier = async (id: string, data: Partial<DossierCreate>): Promise<Dossier> => {
    const response = await apiClient.patch<Dossier>(`/dossiers/${id}`, data);
    await fetchDossiers(); // Refresh list
    return response;
  };

  const deleteDossier = async (id: string): Promise<void> => {
    await apiClient.delete(`/dossiers/${id}`);
    await fetchDossiers(); // Refresh list
  };

  const getDossierStats = async (id: string): Promise<DossierStats> => {
    return await apiClient.get<DossierStats>(`/dossiers/${id}/stats`);
  };

  const refreshDossierStats = async (id: string): Promise<Dossier> => {
    const response = await apiClient.post<Dossier>(`/dossiers/${id}/refresh`);
    await fetchDossiers(); // Refresh list
    return response;
  };

  return {
    dossiers,
    isLoading,
    error,
    createDossier,
    updateDossier,
    deleteDossier,
    getDossierStats,
    refreshDossierStats,
    refetch: fetchDossiers,
  };
}
