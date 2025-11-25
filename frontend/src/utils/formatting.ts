/**
 * Utility functions for formatting data in the Good Shepherd OSINT platform.
 *
 * This module provides helpers for displaying dates, event categories, sentiments,
 * and scoring metrics in a user-friendly way throughout the application.
 */
import { formatDistanceToNow, format } from 'date-fns';
import { EventCategory, Sentiment } from '../types';

/**
 * Format a date string into a human-readable long format.
 *
 * @param dateString - ISO 8601 date string (e.g., "2025-11-25T10:30:00Z")
 * @returns Formatted date string (e.g., "Nov 25, 2025, 10:30:00 AM")
 *
 * @example
 * formatDate("2025-11-25T10:30:00Z") // "Nov 25, 2025, 10:30:00 AM"
 */
export function formatDate(dateString: string): string {
  return format(new Date(dateString), 'PPpp');
}

/**
 * Format a date string as relative time from now.
 *
 * @param dateString - ISO 8601 date string
 * @returns Relative time string (e.g., "2 hours ago", "3 days ago")
 *
 * @example
 * formatRelativeTime("2025-11-25T08:00:00Z") // "2 hours ago"
 */
export function formatRelativeTime(dateString: string): string {
  return formatDistanceToNow(new Date(dateString), { addSuffix: true });
}

/**
 * Get Tailwind CSS classes for styling an event category badge.
 *
 * Returns background and text color classes for displaying category badges
 * with semantic colors. High-priority safety categories (crime, protest,
 * religious_freedom) use attention-grabbing colors.
 *
 * @param category - Event category from the EventCategory enum
 * @returns Tailwind CSS classes for background and text color
 *
 * @example
 * getCategoryColor('crime') // "bg-red-100 text-red-800"
 * getCategoryColor('protest') // "bg-orange-100 text-orange-800"
 */
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

/**
 * Get human-readable label for an event category.
 *
 * Converts internal category enum values (snake_case) to user-friendly
 * display labels (Title Case).
 *
 * @param category - Event category from the EventCategory enum
 * @returns Human-readable category label
 *
 * @example
 * getCategoryLabel('religious_freedom') // "Religious Freedom"
 * getCategoryLabel('community_event') // "Community Event"
 */
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

/**
 * Get Tailwind CSS classes for styling a sentiment badge.
 *
 * Returns semantic color classes for sentiment indicators:
 * - Positive: green (favorable/constructive events)
 * - Neutral: gray (informational/balanced events)
 * - Negative: red (concerning/adverse events)
 * - Unknown: gray (no sentiment analysis available)
 *
 * Sentiment is derived from LLM analysis of event text.
 *
 * @param sentiment - Event sentiment from the Sentiment enum (optional)
 * @returns Tailwind CSS classes for background and text color
 *
 * @example
 * getSentimentColor('positive') // "bg-green-100 text-green-700"
 * getSentimentColor('negative') // "bg-red-100 text-red-700"
 * getSentimentColor(undefined) // "bg-gray-100 text-gray-600"
 */
export function getSentimentColor(sentiment?: Sentiment): string {
  if (!sentiment) return 'bg-gray-100 text-gray-600';

  const colors: Record<Sentiment, string> = {
    positive: 'bg-green-100 text-green-700',
    neutral: 'bg-gray-100 text-gray-700',
    negative: 'bg-red-100 text-red-700',
  };
  return colors[sentiment];
}

/**
 * Get human-readable label for event sentiment.
 *
 * Converts sentiment enum values to capitalized display labels.
 * Returns "Unknown" for missing sentiment data.
 *
 * @param sentiment - Event sentiment from the Sentiment enum (optional)
 * @returns Human-readable sentiment label
 *
 * @example
 * getSentimentLabel('positive') // "Positive"
 * getSentimentLabel(undefined) // "Unknown"
 */
export function getSentimentLabel(sentiment?: Sentiment): string {
  if (!sentiment) return 'Unknown';

  const labels: Record<Sentiment, string> = {
    positive: 'Positive',
    neutral: 'Neutral',
    negative: 'Negative',
  };
  return labels[sentiment];
}

/**
 * Convert relevance score (0-1) to a human-readable label.
 *
 * Relevance indicates how important an event is to missionary safety and operations:
 * - High (≥0.8): Critical safety concerns (crime, protest, religious freedom)
 * - Medium (≥0.5): Noteworthy but less urgent
 * - Low (<0.5): General awareness, minimal direct impact
 *
 * Scoring is weighted higher for safety-related categories.
 *
 * @param score - Relevance score from 0 to 1 (optional)
 * @returns "High", "Medium", "Low", or "Unknown"
 *
 * @example
 * getRelevanceLabel(0.85) // "High"
 * getRelevanceLabel(0.6) // "Medium"
 * getRelevanceLabel(0.3) // "Low"
 * getRelevanceLabel(undefined) // "Unknown"
 */
export function getRelevanceLabel(score?: number): string {
  if (score === undefined || score === null) return 'Unknown';

  if (score >= 0.8) return 'High';
  if (score >= 0.5) return 'Medium';
  return 'Low';
}

/**
 * Convert confidence score (0-1) to a human-readable label.
 *
 * Confidence indicates the reliability of the event data and LLM enrichment:
 * - High (≥0.8): Strong source credibility, clear classification
 * - Medium (≥0.5): Reasonable confidence, some ambiguity
 * - Low (<0.5): Uncertain source or unclear event details
 *
 * Used to help analysts prioritize well-verified intelligence.
 *
 * @param score - Confidence score from 0 to 1 (optional)
 * @returns "High", "Medium", "Low", or "Unknown"
 *
 * @example
 * getConfidenceLabel(0.9) // "High"
 * getConfidenceLabel(0.65) // "Medium"
 * getConfidenceLabel(0.4) // "Low"
 * getConfidenceLabel(null) // "Unknown"
 */
export function getConfidenceLabel(score?: number): string {
  if (score === undefined || score === null) return 'Unknown';

  if (score >= 0.8) return 'High';
  if (score >= 0.5) return 'Medium';
  return 'Low';
}
