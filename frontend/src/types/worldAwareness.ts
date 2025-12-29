/**
 * World Awareness types for the Good Shepherd frontend.
 */

// Region types
export type RegionStatus = 'green' | 'yellow' | 'red';
export type RegionType = 'global' | 'continent' | 'country' | 'admin1' | 'admin2' | 'city' | 'custom';

export interface RegionScores {
    physical: number | null;
    migration: number | null;
    security: number | null;
    socioeconomic: number | null;
    information_reliability: number | null;
}

export interface Region {
    id: string;
    name: string;
    iso_code?: string;
    region_type: RegionType;
    status: RegionStatus;
    status_reason?: string;
    status_updated_at?: string;
    center_lat?: number;
    center_lon?: number;
    scores: RegionScores;
    composite_risk: number;
    incident_count?: number;
    indicator_count?: number;
}

export interface RegionSummary {
    id: string;
    name: string;
    iso_code?: string;
    region_type: string;
    status: string;
    composite_risk: number;
}

export interface RegionListResponse {
    regions: RegionSummary[];
    total: number;
    by_status: {
        green: number;
        yellow: number;
        red: number;
    };
}

// Indicator types
export type IndicatorDomain = 'geopolitical' | 'migration' | 'security' | 'economic' | 'infrastructure' | 'health' | 'environmental';

export interface Indicator {
    id: string;
    region_id: string;
    name: string;
    domain: IndicatorDomain;
    description?: string;
    value: number;
    delta_24h?: number;
    delta_7d?: number;
    confidence: number;
    trend: 'increasing' | 'stable' | 'decreasing';
    is_concerning: boolean;
    measured_at: string;
}

export interface IndicatorListResponse {
    indicators: Indicator[];
    total: number;
    concerning_count: number;
}

// Incident types (enhanced Event)
export type IncidentStatus = 'unverified' | 'developing' | 'corroborated' | 'confirmed' | 'debunked';
export type IncidentSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface Incident {
    id: string;
    title?: string;
    summary: string;
    category: string;
    status: IncidentStatus;
    severity: IncidentSeverity;
    confidence_score?: number;
    location_name?: string;
    location_lat?: number;
    location_lon?: number;
    occurred_at?: string;
    timestamp: string;
    tags?: string[];
    source_count?: number;
    evidence_count?: number;
}

export interface IncidentListResponse {
    incidents: Incident[];
    total: number;
    page: number;
    page_size: number;
}

export interface VerificationQueueResponse {
    queue: Incident[];
    total: number;
    stats: {
        total_pending: number;
        critical: number;
        high: number;
        by_status: {
            unverified: number;
            developing: number;
        };
    };
}

// Report types
export type ReportType = 'daily' | 'weekly' | 'ad_hoc';
export type ReportStatus = 'draft' | 'pending' | 'published' | 'archived';

export interface ReportSummary {
    id: string;
    report_type: ReportType;
    title: string;
    status: ReportStatus;
    created_at: string;
    published_at?: string;
    incident_count: number;
}

export interface Report extends ReportSummary {
    executive_summary?: string;
    narrative_markdown?: string;
    key_developments?: Array<{
        id: string;
        title: string;
        category: string;
        severity: string;
        location?: string;
    }>;
    areas_to_watch?: Array<{
        location: string;
        incident_count: number;
        reason: string;
    }>;
    forward_outlook?: string;
    confidence_notes?: string;
    period_start?: string;
    period_end?: string;
}

// Admin stats
export interface AdminStats {
    incidents_by_status: Record<string, number>;
    total_pending: number;
    high_priority_pending: number;
    recent_actions: Array<{
        incident_id: string;
        action_at: string;
        new_status: string;
    }>;
}

// World Awareness Dashboard
export interface WorldAwarenessSummary {
    regions_by_status: {
        green: number;
        yellow: number;
        red: number;
    };
    critical_regions: RegionSummary[];
    elevated_regions: RegionSummary[];
    concerning_indicators: Indicator[];
    verification_queue_count: number;
    recent_status_changes: Array<{
        region_name: string;
        from_status: string;
        to_status: string;
        changed_at: string;
    }>;
}

// Helper functions for status colors
export function getStatusColor(status: RegionStatus): string {
    switch (status) {
        case 'green':
            return 'bg-green-100 text-green-800 border-green-300';
        case 'yellow':
            return 'bg-yellow-100 text-yellow-800 border-yellow-300';
        case 'red':
            return 'bg-red-100 text-red-800 border-red-300';
        default:
            return 'bg-gray-100 text-gray-800 border-gray-300';
    }
}

export function getSeverityColor(severity: IncidentSeverity): string {
    switch (severity) {
        case 'critical':
            return 'bg-red-600 text-white';
        case 'high':
            return 'bg-orange-500 text-white';
        case 'medium':
            return 'bg-yellow-500 text-white';
        case 'low':
            return 'bg-green-500 text-white';
        default:
            return 'bg-gray-500 text-white';
    }
}

export function getIncidentStatusColor(status: IncidentStatus): string {
    switch (status) {
        case 'confirmed':
            return 'bg-green-100 text-green-800';
        case 'corroborated':
            return 'bg-blue-100 text-blue-800';
        case 'developing':
            return 'bg-yellow-100 text-yellow-800';
        case 'unverified':
            return 'bg-gray-100 text-gray-800';
        case 'debunked':
            return 'bg-red-100 text-red-800 line-through';
        default:
            return 'bg-gray-100 text-gray-800';
    }
}

export function getConfidenceColor(confidence: number): string {
    if (confidence >= 0.75) return 'border-blue-500';
    if (confidence >= 0.40) return 'border-yellow-500';
    return 'border-gray-300';
}
