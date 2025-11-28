/**
 * Notification preferences service for API communication
 */

import { getAccessToken } from './authService';

const API_BASE = process.env.REACT_APP_API_BASE ?? '';

/**
 * Get authorization headers
 */
function getAuthHeaders() {
  const token = getAccessToken();
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

/**
 * Get user's notification preferences
 */
export async function getNotificationPreferences() {
  const response = await fetch(`${API_BASE}/api/notifications/preferences`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch notification preferences');
  }

  return response.json();
}

/**
 * Update user's notification preferences
 */
export async function updateNotificationPreferences(preferences) {
  const response = await fetch(`${API_BASE}/api/notifications/preferences`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(preferences),
  });

  if (!response.ok) {
    throw new Error('Failed to update notification preferences');
  }

  return response.json();
}

/**
 * Get unacknowledged alerts
 */
export async function getUnacknowledgedAlerts(limit = 50) {
  const response = await fetch(
    `${API_BASE}/api/alerts/unacknowledged?limit=${limit}`,
    { headers: getAuthHeaders() }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch unacknowledged alerts');
  }

  return response.json();
}

/**
 * Acknowledge an alert
 */
export async function acknowledgeAlert(eventId, notes = null) {
  const response = await fetch(`${API_BASE}/api/alerts/acknowledge`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ event_id: eventId, notes }),
  });

  if (!response.ok) {
    throw new Error('Failed to acknowledge alert');
  }

  return response.json();
}

/**
 * Get data sources status
 */
export async function getDataSourcesStatus() {
  const response = await fetch(`${API_BASE}/api/sources/status`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch data sources status');
  }

  return response.json();
}

/**
 * Get alert rules
 */
export async function getAlertRules() {
  const response = await fetch(`${API_BASE}/api/alert-rules`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch alert rules');
  }

  return response.json();
}

/**
 * Create alert rule
 */
export async function createAlertRule(rule) {
  const response = await fetch(`${API_BASE}/api/alert-rules`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(rule),
  });

  if (!response.ok) {
    throw new Error('Failed to create alert rule');
  }

  return response.json();
}

/**
 * Update alert rule
 */
export async function updateAlertRule(ruleId, rule) {
  const response = await fetch(`${API_BASE}/api/alert-rules/${ruleId}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(rule),
  });

  if (!response.ok) {
    throw new Error('Failed to update alert rule');
  }

  return response.json();
}

/**
 * Delete alert rule
 */
export async function deleteAlertRule(ruleId) {
  const response = await fetch(`${API_BASE}/api/alert-rules/${ruleId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to delete alert rule');
  }

  return true;
}
