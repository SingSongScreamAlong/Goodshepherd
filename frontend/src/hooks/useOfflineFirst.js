import { useCallback, useEffect, useState } from 'react';
import {
  initDatabase,
  saveEvents,
  getEvents,
  saveReports,
  getReports,
  saveAlert,
  getUnacknowledgedAlerts,
  queueAction,
  getPendingSyncActions,
  removeSyncAction,
  isOnline,
  getStorageStats,
} from '../services/offlineStorage';

const API_BASE = process.env.REACT_APP_API_BASE ?? '';

/**
 * Hook for offline-first data management
 * Fetches from network when online, falls back to IndexedDB when offline
 */
export function useOfflineFirst() {
  const [online, setOnline] = useState(navigator.onLine);
  const [syncing, setSyncing] = useState(false);
  const [lastSync, setLastSync] = useState(null);
  const [pendingActions, setPendingActions] = useState(0);
  const [dbReady, setDbReady] = useState(false);

  // Initialize database on mount
  useEffect(() => {
    initDatabase()
      .then(() => setDbReady(true))
      .catch(err => console.error('Failed to init IndexedDB:', err));
  }, []);

  // Track online/offline status
  useEffect(() => {
    const handleOnline = () => {
      setOnline(true);
      // Trigger sync when coming back online
      syncPendingActions();
    };
    
    const handleOffline = () => {
      setOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Check pending actions count
  useEffect(() => {
    if (dbReady) {
      getPendingSyncActions().then(actions => {
        setPendingActions(actions.length);
      });
    }
  }, [dbReady, lastSync]);

  /**
   * Fetch events with offline fallback
   */
  const fetchEvents = useCallback(async (query = 'europe', options = {}) => {
    // Try network first if online
    if (isOnline()) {
      try {
        const response = await fetch(
          `${API_BASE}/api/search?q=${encodeURIComponent(query)}&limit=${options.limit || 50}`
        );
        
        if (response.ok) {
          const data = await response.json();
          const events = data.results || [];
          
          // Cache to IndexedDB
          if (dbReady && events.length > 0) {
            await saveEvents(events);
          }
          
          setLastSync(new Date());
          return { events, source: 'network' };
        }
      } catch (err) {
        console.warn('Network fetch failed, falling back to cache:', err);
      }
    }

    // Fall back to IndexedDB
    if (dbReady) {
      const cachedEvents = await getEvents(options);
      return { events: cachedEvents, source: 'cache' };
    }

    return { events: [], source: 'none' };
  }, [dbReady]);

  /**
   * Fetch reports with offline fallback
   */
  const fetchReports = useCallback(async (limit = 10) => {
    if (isOnline()) {
      try {
        const response = await fetch(`${API_BASE}/api/reports?limit=${limit}`);
        
        if (response.ok) {
          const data = await response.json();
          const reports = data.results || [];
          
          if (dbReady && reports.length > 0) {
            await saveReports(reports);
          }
          
          return { reports, source: 'network' };
        }
      } catch (err) {
        console.warn('Network fetch failed for reports:', err);
      }
    }

    if (dbReady) {
      const cachedReports = await getReports(limit);
      return { reports: cachedReports, source: 'cache' };
    }

    return { reports: [], source: 'none' };
  }, [dbReady]);

  /**
   * Handle incoming real-time event
   */
  const handleRealtimeEvent = useCallback(async (event) => {
    if (dbReady) {
      await saveEvents([event]);
    }
  }, [dbReady]);

  /**
   * Handle incoming alert
   */
  const handleRealtimeAlert = useCallback(async (alert) => {
    if (dbReady) {
      await saveAlert(alert);
    }
  }, [dbReady]);

  /**
   * Queue an action for later sync (when offline)
   */
  const queueOfflineAction = useCallback(async (actionType, payload) => {
    if (dbReady) {
      await queueAction({ type: actionType, payload });
      setPendingActions(prev => prev + 1);
    }
  }, [dbReady]);

  /**
   * Sync pending actions when back online
   */
  const syncPendingActions = useCallback(async () => {
    if (!dbReady || !isOnline() || syncing) return;

    setSyncing(true);
    
    try {
      const actions = await getPendingSyncActions();
      
      for (const action of actions) {
        try {
          // Process based on action type
          switch (action.type) {
            case 'check_in':
              await fetch(`${API_BASE}/api/user/check-in`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(action.payload),
              });
              break;
              
            case 'acknowledge_alert':
              // Alert acknowledgment sync
              break;
              
            default:
              console.warn('Unknown action type:', action.type);
          }
          
          // Remove successful action
          await removeSyncAction(action.id);
          setPendingActions(prev => Math.max(0, prev - 1));
          
        } catch (err) {
          console.error('Failed to sync action:', action, err);
          // Keep in queue for retry
        }
      }
      
      setLastSync(new Date());
    } finally {
      setSyncing(false);
    }
  }, [dbReady, syncing]);

  /**
   * Get storage statistics
   */
  const getStats = useCallback(async () => {
    if (!dbReady) return null;
    return getStorageStats();
  }, [dbReady]);

  /**
   * Get unacknowledged alerts from cache
   */
  const getCachedAlerts = useCallback(async () => {
    if (!dbReady) return [];
    return getUnacknowledgedAlerts();
  }, [dbReady]);

  return {
    // State
    online,
    syncing,
    lastSync,
    pendingActions,
    dbReady,
    
    // Data fetching
    fetchEvents,
    fetchReports,
    
    // Real-time handlers
    handleRealtimeEvent,
    handleRealtimeAlert,
    
    // Offline queue
    queueOfflineAction,
    syncPendingActions,
    
    // Utilities
    getStats,
    getCachedAlerts,
  };
}

export default useOfflineFirst;
