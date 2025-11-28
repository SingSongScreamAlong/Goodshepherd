/**
 * IndexedDB-based offline storage for Good Shepherd
 * Provides offline-first caching for events, reports, and user data
 */

const DB_NAME = 'GoodShepherdDB';
const DB_VERSION = 1;

// Store names
const STORES = {
  EVENTS: 'events',
  REPORTS: 'reports',
  ALERTS: 'alerts',
  SYNC_QUEUE: 'syncQueue',
  USER_SETTINGS: 'userSettings',
  CACHED_REGIONS: 'cachedRegions',
};

let dbInstance = null;

/**
 * Initialize the IndexedDB database
 */
export async function initDatabase() {
  if (dbInstance) return dbInstance;

  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => {
      console.error('Failed to open IndexedDB:', request.error);
      reject(request.error);
    };

    request.onsuccess = () => {
      dbInstance = request.result;
      resolve(dbInstance);
    };

    request.onupgradeneeded = (event) => {
      const db = event.target.result;

      // Events store with indexes
      if (!db.objectStoreNames.contains(STORES.EVENTS)) {
        const eventsStore = db.createObjectStore(STORES.EVENTS, { keyPath: 'id' });
        eventsStore.createIndex('region', 'region', { unique: false });
        eventsStore.createIndex('threat_level', 'threat_level', { unique: false });
        eventsStore.createIndex('fetched_at', 'fetched_at', { unique: false });
        eventsStore.createIndex('category', 'category', { unique: false });
      }

      // Reports store
      if (!db.objectStoreNames.contains(STORES.REPORTS)) {
        const reportsStore = db.createObjectStore(STORES.REPORTS, { keyPath: 'id' });
        reportsStore.createIndex('generated_at', 'generated_at', { unique: false });
        reportsStore.createIndex('region', 'region', { unique: false });
      }

      // Alerts store for received alerts
      if (!db.objectStoreNames.contains(STORES.ALERTS)) {
        const alertsStore = db.createObjectStore(STORES.ALERTS, { keyPath: 'id', autoIncrement: true });
        alertsStore.createIndex('timestamp', 'timestamp', { unique: false });
        alertsStore.createIndex('acknowledged', 'acknowledged', { unique: false });
      }

      // Sync queue for offline actions
      if (!db.objectStoreNames.contains(STORES.SYNC_QUEUE)) {
        const syncStore = db.createObjectStore(STORES.SYNC_QUEUE, { keyPath: 'id', autoIncrement: true });
        syncStore.createIndex('timestamp', 'timestamp', { unique: false });
        syncStore.createIndex('type', 'type', { unique: false });
      }

      // User settings
      if (!db.objectStoreNames.contains(STORES.USER_SETTINGS)) {
        db.createObjectStore(STORES.USER_SETTINGS, { keyPath: 'key' });
      }

      // Cached regions for offline map
      if (!db.objectStoreNames.contains(STORES.CACHED_REGIONS)) {
        db.createObjectStore(STORES.CACHED_REGIONS, { keyPath: 'regionId' });
      }
    };
  });
}

/**
 * Get the database instance
 */
async function getDB() {
  if (!dbInstance) {
    await initDatabase();
  }
  return dbInstance;
}

// =============================================================================
// Events Storage
// =============================================================================

/**
 * Save events to IndexedDB
 */
export async function saveEvents(events) {
  const db = await getDB();
  const tx = db.transaction(STORES.EVENTS, 'readwrite');
  const store = tx.objectStore(STORES.EVENTS);

  const promises = events.map(event => {
    return new Promise((resolve, reject) => {
      const request = store.put({
        ...event,
        _cachedAt: new Date().toISOString(),
      });
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  });

  await Promise.all(promises);
  await tx.complete;
}

/**
 * Get all cached events
 */
export async function getEvents(options = {}) {
  const db = await getDB();
  const tx = db.transaction(STORES.EVENTS, 'readonly');
  const store = tx.objectStore(STORES.EVENTS);

  return new Promise((resolve, reject) => {
    const request = store.getAll();
    request.onsuccess = () => {
      let events = request.result;

      // Apply filters
      if (options.region) {
        events = events.filter(e => 
          e.region?.toLowerCase().includes(options.region.toLowerCase())
        );
      }
      if (options.threatLevel) {
        events = events.filter(e => e.threat_level === options.threatLevel);
      }
      if (options.category) {
        events = events.filter(e => e.category === options.category);
      }

      // Sort by fetched_at descending
      events.sort((a, b) => new Date(b.fetched_at) - new Date(a.fetched_at));

      // Apply limit
      if (options.limit) {
        events = events.slice(0, options.limit);
      }

      resolve(events);
    };
    request.onerror = () => reject(request.error);
  });
}

/**
 * Get a single event by ID
 */
export async function getEventById(eventId) {
  const db = await getDB();
  const tx = db.transaction(STORES.EVENTS, 'readonly');
  const store = tx.objectStore(STORES.EVENTS);

  return new Promise((resolve, reject) => {
    const request = store.get(eventId);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

/**
 * Delete old events (cleanup)
 */
export async function cleanupOldEvents(maxAgeDays = 7) {
  const db = await getDB();
  const tx = db.transaction(STORES.EVENTS, 'readwrite');
  const store = tx.objectStore(STORES.EVENTS);
  const index = store.index('fetched_at');

  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - maxAgeDays);

  return new Promise((resolve, reject) => {
    const range = IDBKeyRange.upperBound(cutoffDate.toISOString());
    const request = index.openCursor(range);
    let deletedCount = 0;

    request.onsuccess = (event) => {
      const cursor = event.target.result;
      if (cursor) {
        cursor.delete();
        deletedCount++;
        cursor.continue();
      } else {
        resolve(deletedCount);
      }
    };
    request.onerror = () => reject(request.error);
  });
}

// =============================================================================
// Reports Storage
// =============================================================================

/**
 * Save reports to IndexedDB
 */
export async function saveReports(reports) {
  const db = await getDB();
  const tx = db.transaction(STORES.REPORTS, 'readwrite');
  const store = tx.objectStore(STORES.REPORTS);

  const promises = reports.map(report => {
    return new Promise((resolve, reject) => {
      const request = store.put({
        ...report,
        _cachedAt: new Date().toISOString(),
      });
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  });

  await Promise.all(promises);
}

/**
 * Get all cached reports
 */
export async function getReports(limit = 20) {
  const db = await getDB();
  const tx = db.transaction(STORES.REPORTS, 'readonly');
  const store = tx.objectStore(STORES.REPORTS);

  return new Promise((resolve, reject) => {
    const request = store.getAll();
    request.onsuccess = () => {
      let reports = request.result;
      reports.sort((a, b) => new Date(b.generated_at) - new Date(a.generated_at));
      resolve(reports.slice(0, limit));
    };
    request.onerror = () => reject(request.error);
  });
}

// =============================================================================
// Alerts Storage
// =============================================================================

/**
 * Save an alert
 */
export async function saveAlert(alert) {
  const db = await getDB();
  const tx = db.transaction(STORES.ALERTS, 'readwrite');
  const store = tx.objectStore(STORES.ALERTS);

  return new Promise((resolve, reject) => {
    const request = store.add({
      ...alert,
      timestamp: new Date().toISOString(),
      acknowledged: false,
    });
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

/**
 * Get unacknowledged alerts
 */
export async function getUnacknowledgedAlerts() {
  const db = await getDB();
  const tx = db.transaction(STORES.ALERTS, 'readonly');
  const store = tx.objectStore(STORES.ALERTS);
  const index = store.index('acknowledged');

  return new Promise((resolve, reject) => {
    const request = index.getAll(IDBKeyRange.only(false));
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

/**
 * Acknowledge an alert
 */
export async function acknowledgeAlert(alertId) {
  const db = await getDB();
  const tx = db.transaction(STORES.ALERTS, 'readwrite');
  const store = tx.objectStore(STORES.ALERTS);

  return new Promise((resolve, reject) => {
    const getRequest = store.get(alertId);
    getRequest.onsuccess = () => {
      const alert = getRequest.result;
      if (alert) {
        alert.acknowledged = true;
        alert.acknowledgedAt = new Date().toISOString();
        const putRequest = store.put(alert);
        putRequest.onsuccess = () => resolve();
        putRequest.onerror = () => reject(putRequest.error);
      } else {
        resolve();
      }
    };
    getRequest.onerror = () => reject(getRequest.error);
  });
}

// =============================================================================
// Sync Queue (for offline actions)
// =============================================================================

/**
 * Add an action to the sync queue
 */
export async function queueAction(action) {
  const db = await getDB();
  const tx = db.transaction(STORES.SYNC_QUEUE, 'readwrite');
  const store = tx.objectStore(STORES.SYNC_QUEUE);

  return new Promise((resolve, reject) => {
    const request = store.add({
      ...action,
      timestamp: new Date().toISOString(),
      retries: 0,
    });
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

/**
 * Get all pending sync actions
 */
export async function getPendingSyncActions() {
  const db = await getDB();
  const tx = db.transaction(STORES.SYNC_QUEUE, 'readonly');
  const store = tx.objectStore(STORES.SYNC_QUEUE);

  return new Promise((resolve, reject) => {
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

/**
 * Remove a completed sync action
 */
export async function removeSyncAction(actionId) {
  const db = await getDB();
  const tx = db.transaction(STORES.SYNC_QUEUE, 'readwrite');
  const store = tx.objectStore(STORES.SYNC_QUEUE);

  return new Promise((resolve, reject) => {
    const request = store.delete(actionId);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

// =============================================================================
// User Settings
// =============================================================================

/**
 * Save a user setting
 */
export async function saveSetting(key, value) {
  const db = await getDB();
  const tx = db.transaction(STORES.USER_SETTINGS, 'readwrite');
  const store = tx.objectStore(STORES.USER_SETTINGS);

  return new Promise((resolve, reject) => {
    const request = store.put({ key, value, updatedAt: new Date().toISOString() });
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

/**
 * Get a user setting
 */
export async function getSetting(key, defaultValue = null) {
  const db = await getDB();
  const tx = db.transaction(STORES.USER_SETTINGS, 'readonly');
  const store = tx.objectStore(STORES.USER_SETTINGS);

  return new Promise((resolve, reject) => {
    const request = store.get(key);
    request.onsuccess = () => {
      resolve(request.result?.value ?? defaultValue);
    };
    request.onerror = () => reject(request.error);
  });
}

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Check if we're online
 */
export function isOnline() {
  return navigator.onLine;
}

/**
 * Get storage usage statistics
 */
export async function getStorageStats() {
  const db = await getDB();
  const stats = {};

  for (const storeName of Object.values(STORES)) {
    const tx = db.transaction(storeName, 'readonly');
    const store = tx.objectStore(storeName);
    
    stats[storeName] = await new Promise((resolve) => {
      const request = store.count();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => resolve(0);
    });
  }

  return stats;
}

/**
 * Clear all cached data
 */
export async function clearAllData() {
  const db = await getDB();
  
  for (const storeName of Object.values(STORES)) {
    const tx = db.transaction(storeName, 'readwrite');
    const store = tx.objectStore(storeName);
    await new Promise((resolve, reject) => {
      const request = store.clear();
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }
}

export default {
  initDatabase,
  saveEvents,
  getEvents,
  getEventById,
  cleanupOldEvents,
  saveReports,
  getReports,
  saveAlert,
  getUnacknowledgedAlerts,
  acknowledgeAlert,
  queueAction,
  getPendingSyncActions,
  removeSyncAction,
  saveSetting,
  getSetting,
  isOnline,
  getStorageStats,
  clearAllData,
};
