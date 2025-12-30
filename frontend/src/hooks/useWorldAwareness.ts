/**
 * API hooks for World Awareness features.
 */
import { useState, useEffect, useCallback } from 'react';
import {
    Region,
    RegionSummary,
    RegionListResponse,
    Indicator,
    IndicatorListResponse,
    Incident,
    VerificationQueueResponse,
    AdminStats,
} from '../types/worldAwareness';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Helper for API calls
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...(token && { Authorization: `Bearer ${token}` }),
            ...options?.headers,
        },
    });

    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }

    return response.json();
}

// Regions hooks
export function useRegions(status?: string) {
    const [regions, setRegions] = useState<RegionSummary[]>([]);
    const [byStatus, setByStatus] = useState<{ green: number; yellow: number; red: number }>({ green: 0, yellow: 0, red: 0 });
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const load = async () => {
            try {
                setIsLoading(true);
                const params = status ? `?status=${status}` : '';
                const data = await fetchApi<RegionListResponse>(`/regions${params}`);
                setRegions(data.regions);
                setByStatus(data.by_status);
            } catch (e) {
                setError(e instanceof Error ? e.message : 'Failed to load regions');
            } finally {
                setIsLoading(false);
            }
        };
        load();
    }, [status]);

    return { regions, byStatus, isLoading, error };
}

export function useCriticalRegions() {
    const [regions, setRegions] = useState<RegionSummary[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetchApi<RegionSummary[]>('/regions/critical')
            .then(setRegions)
            .finally(() => setIsLoading(false));
    }, []);

    return { regions, isLoading };
}

export function useElevatedRegions() {
    const [regions, setRegions] = useState<RegionSummary[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetchApi<RegionSummary[]>('/regions/elevated')
            .then(setRegions)
            .finally(() => setIsLoading(false));
    }, []);

    return { regions, isLoading };
}

export function useRegion(regionId: string) {
    const [region, setRegion] = useState<Region | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!regionId) return;

        fetchApi<Region>(`/regions/${regionId}`)
            .then(setRegion)
            .catch(e => setError(e.message))
            .finally(() => setIsLoading(false));
    }, [regionId]);

    return { region, isLoading, error };
}

// Indicators hooks
export function useIndicators(domain?: string, regionId?: string) {
    const [indicators, setIndicators] = useState<Indicator[]>([]);
    const [concerningCount, setConcerningCount] = useState(0);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const params = new URLSearchParams();
        if (domain) params.set('domain', domain);
        if (regionId) params.set('region_id', regionId);

        const queryString = params.toString();
        fetchApi<IndicatorListResponse>(`/indicators${queryString ? `?${queryString}` : ''}`)
            .then(data => {
                setIndicators(data.indicators);
                setConcerningCount(data.concerning_count);
            })
            .finally(() => setIsLoading(false));
    }, [domain, regionId]);

    return { indicators, concerningCount, isLoading };
}

export function useConcerningIndicators() {
    const [indicators, setIndicators] = useState<Indicator[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetchApi<Indicator[]>('/indicators/concerning')
            .then(setIndicators)
            .finally(() => setIsLoading(false));
    }, []);

    return { indicators, isLoading };
}

export function useTrendingIndicators(direction: 'increasing' | 'decreasing' = 'increasing') {
    const [indicators, setIndicators] = useState<Indicator[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetchApi<Indicator[]>(`/indicators/trending?direction=${direction}`)
            .then(setIndicators)
            .finally(() => setIsLoading(false));
    }, [direction]);

    return { indicators, isLoading };
}

// Incidents hooks
export function useIncidents(filters?: { status?: string; severity?: string; page?: number }) {
    const [incidents, setIncidents] = useState<Incident[]>([]);
    const [total, setTotal] = useState(0);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const params = new URLSearchParams();
        if (filters?.status) params.set('status', filters.status);
        if (filters?.severity) params.set('severity', filters.severity);
        if (filters?.page) params.set('page', String(filters.page));

        const queryString = params.toString();
        fetchApi<{ incidents: Incident[]; total: number }>(`/incidents${queryString ? `?${queryString}` : ''}`)
            .then(data => {
                setIncidents(data.incidents);
                setTotal(data.total);
            })
            .finally(() => setIsLoading(false));
    }, [filters?.status, filters?.severity, filters?.page]);

    return { incidents, total, isLoading };
}

export function useVerificationQueue(limit = 50) {
    const [queue, setQueue] = useState<Incident[]>([]);
    const [stats, setStats] = useState<VerificationQueueResponse['stats'] | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const refresh = useCallback(async () => {
        setIsLoading(true);
        try {
            const data = await fetchApi<VerificationQueueResponse>(`/admin/verification-queue?limit=${limit}`);
            setQueue(data.queue);
            setStats(data.stats);
        } finally {
            setIsLoading(false);
        }
    }, [limit]);

    useEffect(() => {
        refresh();
    }, [refresh]);

    return { queue, stats, isLoading, refresh };
}

// Admin hooks
export function useAdminStats() {
    const [stats, setStats] = useState<AdminStats | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetchApi<AdminStats>('/admin/stats')
            .then(setStats)
            .finally(() => setIsLoading(false));
    }, []);

    return { stats, isLoading };
}

// Actions
export async function confirmIncident(incidentId: string, notes?: string) {
    return fetchApi(`/incidents/${incidentId}/confirm`, {
        method: 'POST',
        body: JSON.stringify({ notes }),
    });
}

export async function debunkIncident(incidentId: string, reason: string) {
    return fetchApi(`/incidents/${incidentId}/debunk`, {
        method: 'POST',
        body: JSON.stringify({ reason }),
    });
}

export async function bulkAction(incidentIds: string[], action: 'confirm' | 'debunk' | 'downgrade', notes?: string) {
    return fetchApi('/admin/bulk-action', {
        method: 'POST',
        body: JSON.stringify({ incident_ids: incidentIds, action, notes }),
    });
}

export async function refreshRegion(regionId: string) {
    return fetchApi(`/regions/${regionId}/refresh`, { method: 'POST' });
}

export async function generateDailySitrep(title?: string, regionIds?: string[]) {
    return fetchApi('/reports/daily-sitrep', {
        method: 'POST',
        body: JSON.stringify({ title, region_ids: regionIds }),
    });
}

export async function generateWeeklyBrief(title?: string, regionIds?: string[]) {
    return fetchApi('/reports/weekly-brief', {
        method: 'POST',
        body: JSON.stringify({ title, region_ids: regionIds }),
    });
}
