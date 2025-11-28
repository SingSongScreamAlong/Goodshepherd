// Mock for offlineStorage service
export const initDatabase = jest.fn(() => Promise.resolve(true));
export const saveEvents = jest.fn(() => Promise.resolve(true));
export const getEvents = jest.fn(() => Promise.resolve([]));
export const saveReports = jest.fn(() => Promise.resolve(true));
export const getReports = jest.fn(() => Promise.resolve([]));
export const saveAlert = jest.fn(() => Promise.resolve(true));
export const getUnacknowledgedAlerts = jest.fn(() => Promise.resolve([]));
export const queueAction = jest.fn(() => Promise.resolve(true));
export const getPendingSyncActions = jest.fn(() => Promise.resolve([]));
export const removeSyncAction = jest.fn(() => Promise.resolve(true));
export const isOnline = jest.fn(() => true);
export const getStorageStats = jest.fn(() => Promise.resolve({ events: 0, reports: 0 }));
