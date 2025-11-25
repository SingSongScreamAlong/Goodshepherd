/**
 * Utility functions for dossier-related formatting.
 */
import { DossierType, WatchlistPriority } from '../types';

export function getDossierTypeLabel(type: DossierType): string {
  const labels: Record<DossierType, string> = {
    location: 'Location',
    organization: 'Organization',
    group: 'Group',
    topic: 'Topic',
    person: 'Person',
  };
  return labels[type] || type;
}

export function getDossierTypeColor(type: DossierType): string {
  const colors: Record<DossierType, string> = {
    location: 'bg-blue-100 text-blue-800',
    organization: 'bg-purple-100 text-purple-800',
    group: 'bg-green-100 text-green-800',
    topic: 'bg-yellow-100 text-yellow-800',
    person: 'bg-pink-100 text-pink-800',
  };
  return colors[type] || 'bg-gray-100 text-gray-800';
}

export function getWatchlistPriorityLabel(priority: WatchlistPriority): string {
  const labels: Record<WatchlistPriority, string> = {
    low: 'Low',
    medium: 'Medium',
    high: 'High',
    critical: 'Critical',
  };
  return labels[priority] || priority;
}

export function getWatchlistPriorityColor(priority: WatchlistPriority): string {
  const colors: Record<WatchlistPriority, string> = {
    low: 'bg-gray-100 text-gray-700',
    medium: 'bg-blue-100 text-blue-700',
    high: 'bg-orange-100 text-orange-700',
    critical: 'bg-red-100 text-red-700',
  };
  return colors[priority] || 'bg-gray-100 text-gray-700';
}
