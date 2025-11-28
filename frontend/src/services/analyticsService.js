/**
 * Analytics and search service for analyst dashboard
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
 * Search events with advanced filters
 */
export async function searchEvents({
  query = '',
  category = null,
  region = null,
  threatLevel = null,
  startDate = null,
  endDate = null,
  verificationStatus = null,
  limit = 50,
  offset = 0,
}) {
  const params = new URLSearchParams();
  if (query) params.append('q', query);
  if (category) params.append('category', category);
  if (region) params.append('region', region);
  if (threatLevel) params.append('threat_level', threatLevel);
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  if (verificationStatus) params.append('verification_status', verificationStatus);
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());

  const response = await fetch(`${API_BASE}/api/events/search?${params}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to search events');
  }

  return response.json();
}

/**
 * Get events for timeline view
 */
export async function getTimelineEvents({
  startDate,
  endDate,
  category = null,
  region = null,
  limit = 200,
}) {
  const params = new URLSearchParams();
  params.append('start_date', startDate);
  params.append('end_date', endDate);
  if (category) params.append('category', category);
  if (region) params.append('region', region);
  params.append('limit', limit.toString());

  const response = await fetch(`${API_BASE}/api/events/timeline?${params}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch timeline events');
  }

  return response.json();
}

/**
 * Get event clusters for visualization
 */
export async function getEventClusters({
  startDate = null,
  endDate = null,
  minClusterSize = 3,
}) {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  params.append('min_cluster_size', minClusterSize.toString());

  const response = await fetch(`${API_BASE}/api/events/clusters?${params}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch event clusters');
  }

  return response.json();
}

/**
 * Get review queue for analysts
 */
export async function getReviewQueue({
  status = 'pending',
  priority = null,
  limit = 50,
}) {
  const params = new URLSearchParams();
  params.append('status', status);
  if (priority) params.append('priority', priority);
  params.append('limit', limit.toString());

  const response = await fetch(`${API_BASE}/api/analyst/review-queue?${params}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch review queue');
  }

  return response.json();
}

/**
 * Submit event validation (human-in-loop)
 */
export async function submitEventValidation(eventId, validation) {
  const response = await fetch(`${API_BASE}/api/analyst/validate/${eventId}`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(validation),
  });

  if (!response.ok) {
    throw new Error('Failed to submit validation');
  }

  return response.json();
}

/**
 * Submit ML feedback for model improvement
 */
export async function submitMLFeedback(eventId, feedback) {
  const response = await fetch(`${API_BASE}/api/ml/feedback`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      event_id: eventId,
      ...feedback,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to submit ML feedback');
  }

  return response.json();
}

/**
 * Get analytics summary
 */
export async function getAnalyticsSummary({ period = '7d' }) {
  const response = await fetch(`${API_BASE}/api/analytics/summary?period=${period}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch analytics summary');
  }

  return response.json();
}

/**
 * Get threat trends over time
 */
export async function getThreatTrends({
  startDate,
  endDate,
  granularity = 'day',
}) {
  const params = new URLSearchParams();
  params.append('start_date', startDate);
  params.append('end_date', endDate);
  params.append('granularity', granularity);

  const response = await fetch(`${API_BASE}/api/analytics/trends?${params}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch threat trends');
  }

  return response.json();
}

/**
 * Get regional breakdown
 */
export async function getRegionalBreakdown({ period = '7d' }) {
  const response = await fetch(`${API_BASE}/api/analytics/regions?period=${period}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch regional breakdown');
  }

  return response.json();
}
