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
