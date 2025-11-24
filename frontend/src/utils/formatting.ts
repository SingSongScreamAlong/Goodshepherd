/**
 * Utility functions for formatting data.
 */
import { formatDistanceToNow, format } from 'date-fns';
import { EventCategory, Sentiment } from '../types';

export function formatDate(dateString: string): string {
  return format(new Date(dateString), 'PPpp');
}

export function formatRelativeTime(dateString: string): string {
  return formatDistanceToNow(new Date(dateString), { addSuffix: true });
}

export function getCategoryColor(category: EventCategory): string {
  const colors: Record<EventCategory, string> = {
    protest: 'bg-orange-100 text-orange-800',
    crime: 'bg-red-100 text-red-800',
    religious_freedom: 'bg-purple-100 text-purple-800',
    cultural_tension: 'bg-yellow-100 text-yellow-800',
    political: 'bg-blue-100 text-blue-800',
    infrastructure: 'bg-gray-100 text-gray-800',
    health: 'bg-pink-100 text-pink-800',
    migration: 'bg-teal-100 text-teal-800',
    economic: 'bg-green-100 text-green-800',
    weather: 'bg-cyan-100 text-cyan-800',
    community_event: 'bg-indigo-100 text-indigo-800',
    other: 'bg-slate-100 text-slate-800',
  };
  return colors[category] || colors.other;
}

export function getCategoryLabel(category: EventCategory): string {
  const labels: Record<EventCategory, string> = {
    protest: 'Protest',
    crime: 'Crime',
    religious_freedom: 'Religious Freedom',
    cultural_tension: 'Cultural Tension',
    political: 'Political',
    infrastructure: 'Infrastructure',
    health: 'Health',
    migration: 'Migration',
    economic: 'Economic',
    weather: 'Weather',
    community_event: 'Community Event',
    other: 'Other',
  };
  return labels[category] || 'Other';
}

export function getSentimentColor(sentiment?: Sentiment): string {
  if (!sentiment) return 'bg-gray-100 text-gray-600';

  const colors: Record<Sentiment, string> = {
    positive: 'bg-green-100 text-green-700',
    neutral: 'bg-gray-100 text-gray-700',
    negative: 'bg-red-100 text-red-700',
  };
  return colors[sentiment];
}

export function getSentimentLabel(sentiment?: Sentiment): string {
  if (!sentiment) return 'Unknown';

  const labels: Record<Sentiment, string> = {
    positive: 'Positive',
    neutral: 'Neutral',
    negative: 'Negative',
  };
  return labels[sentiment];
}

export function getRelevanceLabel(score?: number): string {
  if (score === undefined || score === null) return 'Unknown';

  if (score >= 0.8) return 'High';
  if (score >= 0.5) return 'Medium';
  return 'Low';
}

export function getConfidenceLabel(score?: number): string {
  if (score === undefined || score === null) return 'Unknown';

  if (score >= 0.8) return 'High';
  if (score >= 0.5) return 'Medium';
  return 'Low';
}
