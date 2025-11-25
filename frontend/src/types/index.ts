/**
 * TypeScript type definitions for The Good Shepherd.
 */

export type EventCategory =
  | 'protest'
  | 'crime'
  | 'religious_freedom'
  | 'cultural_tension'
  | 'political'
  | 'infrastructure'
  | 'health'
  | 'migration'
  | 'economic'
  | 'weather'
  | 'community_event'
  | 'other';

export type Sentiment = 'positive' | 'neutral' | 'negative';

export type StabilityTrend = 'increasing' | 'decreasing' | 'neutral';

export interface Event {
  event_id: string;
  timestamp: string;
  summary: string;
  full_text?: string;
  location_lat?: number;
  location_lon?: number;
  location_name?: string;
  category: EventCategory;
  sub_category?: string;
  sentiment?: Sentiment;
  relevance_score?: number;
  confidence_score?: number;
  stability_trend?: StabilityTrend;
  source_list?: Array<{
    name: string;
    url: string;
    fetched_at: string;
  }>;
  entity_list?: {
    locations: string[];
    organizations: string[];
    groups: string[];
    topics: string[];
    keywords: string[];
  };
  cluster_id?: string;
  created_at: string;
  updated_at: string;
}

export interface EventListResponse {
  events: Event[];
  total: number;
  page: number;
  page_size: number;
}

export interface User {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  last_login?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface EventFilters {
  category?: EventCategory;
  sentiment?: Sentiment;
  location_name?: string;
  start_date?: string;
  end_date?: string;
  min_relevance?: number;
  page?: number;
  page_size?: number;
}

// Dossier and Watchlist Types

export type DossierType = 'location' | 'organization' | 'group' | 'topic' | 'person';

export type WatchlistPriority = 'low' | 'medium' | 'high' | 'critical';

export interface Dossier {
  id: string;
  organization_id: string;
  name: string;
  dossier_type: DossierType;
  description?: string;
  aliases?: string[];
  location_lat?: string;
  location_lon?: string;
  location_name?: string;
  tags?: string[];
  notes?: string;
  event_count: number;
  last_event_timestamp?: string;
  first_event_timestamp?: string;
  created_at: string;
  updated_at: string;
}

export interface DossierStats {
  dossier_id: string;
  name: string;
  dossier_type: DossierType;
  event_count: number;
  recent_event_count_7d: number;
  recent_event_count_30d: number;
  last_event_timestamp?: string;
  categories: Record<string, number>;
  sentiment_distribution: Record<string, number>;
}

export interface DossierCreate {
  name: string;
  dossier_type: DossierType;
  description?: string;
  aliases?: string[];
  location_lat?: string;
  location_lon?: string;
  location_name?: string;
  tags?: string[];
  notes?: string;
}

export interface Watchlist {
  id: string;
  organization_id: string;
  user_id: string;
  name: string;
  description?: string;
  priority: WatchlistPriority;
  is_active: boolean;
  notification_enabled: boolean;
  created_at: string;
  updated_at: string;
  dossier_count: number;
}

export interface WatchlistWithDossiers extends Watchlist {
  dossiers: Dossier[];
}

export interface WatchlistCreate {
  name: string;
  description?: string;
  priority?: WatchlistPriority;
  is_active?: boolean;
  notification_enabled?: boolean;
  dossier_ids?: string[];
}

// Dashboard Types

export interface DashboardSummary {
  timestamp: string;
  total_events: number;
  events_today: number;
  events_week: number;
  events_month: number;
  high_relevance_today: number;
  category_distribution: Record<string, number>;
  sentiment_distribution: Record<string, number>;
  top_locations: Array<{ location: string; count: number }>;
  total_dossiers: number;
  active_dossiers: number;
  recent_highlights: Array<{
    event_id: string;
    summary: string;
    category: string | null;
    relevance_score: number;
    timestamp: string;
  }>;
}

export interface TrendsData {
  period_days: number;
  start_date: string;
  end_date: string;
  daily_counts: Array<{ date: string; count: number }>;
  category_trends: Record<string, Array<{ date: string; count: number }>>;
  sentiment_trends: Record<string, Array<{ date: string; count: number }>>;
}
