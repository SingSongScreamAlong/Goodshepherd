/**
 * Verification Queue Widget - Shows pending incidents requiring review.
 * Dark theme with glass-morphism cards.
 */
import { useVerificationQueue, confirmIncident, debunkIncident } from '../hooks/useWorldAwareness';
import { useState } from 'react';

export default function VerificationQueueWidget() {
    const { queue, stats, isLoading, refresh } = useVerificationQueue(10);
    const [actionInProgress, setActionInProgress] = useState<string | null>(null);

    const handleConfirm = async (incidentId: string) => {
        setActionInProgress(incidentId);
        try {
            await confirmIncident(incidentId, 'Confirmed via dashboard widget');
            await refresh();
        } finally {
            setActionInProgress(null);
        }
    };

    const handleDebunk = async (incidentId: string) => {
        const reason = prompt('Reason for debunking:');
        if (!reason) return;

        setActionInProgress(incidentId);
        try {
            await debunkIncident(incidentId, reason);
            await refresh();
        } finally {
            setActionInProgress(null);
        }
    };

    const getSeverityStyle = (severity: string) => {
        switch (severity?.toLowerCase()) {
            case 'critical': return 'status-badge status-critical';
            case 'high': return 'status-badge status-elevated';
            case 'medium': return 'status-badge status-warning';
            default: return 'status-badge status-stable';
        }
    };

    if (isLoading) {
        return (
            <div className="glass-card p-6">
                <div className="animate-pulse">
                    <div className="h-4 bg-slate-700 rounded w-1/3 mb-4"></div>
                    <div className="space-y-3">
                        <div className="h-16 bg-slate-700 rounded"></div>
                        <div className="h-16 bg-slate-700 rounded"></div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white flex items-center">
                    <svg className="w-5 h-5 mr-2 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Verification Queue
                </h2>
                {stats && (
                    <div className="flex items-center space-x-3 text-sm">
                        <span className="text-gray-400">
                            {stats.total_pending} pending
                        </span>
                        {stats.critical > 0 && (
                            <span className="status-badge status-critical text-xs">
                                {stats.critical} critical
                            </span>
                        )}
                    </div>
                )}
            </div>

            {queue.length === 0 ? (
                <div className="text-center py-8 bg-emerald-500/5 border border-emerald-500/20 rounded-lg">
                    <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto mb-3">
                        <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                    <p className="text-sm text-emerald-400 font-medium">Queue Clear</p>
                    <p className="text-xs text-gray-500 mt-1">No incidents pending verification</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {queue.map((incident) => (
                        <div
                            key={incident.id}
                            className="bg-slate-800/50 border border-white/5 rounded-lg p-3 hover:border-white/10 transition-all duration-200"
                        >
                            <div className="flex items-start justify-between mb-2">
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center space-x-2 mb-1">
                                        <span className={getSeverityStyle(incident.severity)}>
                                            {incident.severity?.toUpperCase() || 'UNKNOWN'}
                                        </span>
                                        <span className="px-2 py-0.5 text-xs rounded bg-slate-700 text-gray-300 border border-white/5">
                                            {incident.status}
                                        </span>
                                        {incident.confidence_score && (
                                            <span className="text-xs text-gray-500">
                                                {Math.round(incident.confidence_score * 100)}% conf
                                            </span>
                                        )}
                                    </div>
                                    <p className="text-sm font-medium text-white truncate">
                                        {incident.title || incident.summary}
                                    </p>
                                    <p className="text-xs text-gray-500 mt-1">
                                        {incident.location_name || 'Unknown location'} • {incident.category}
                                    </p>
                                </div>
                            </div>

                            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-white/5">
                                <button
                                    onClick={() => handleDebunk(incident.id)}
                                    disabled={actionInProgress === incident.id}
                                    className="px-3 py-1.5 text-xs font-medium text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg hover:bg-red-500/20 hover:border-red-500/30 transition-all disabled:opacity-50"
                                >
                                    Debunk
                                </button>
                                <button
                                    onClick={() => handleConfirm(incident.id)}
                                    disabled={actionInProgress === incident.id}
                                    className="px-3 py-1.5 text-xs font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-lg hover:bg-emerald-500/20 hover:border-emerald-500/30 transition-all disabled:opacity-50"
                                >
                                    Confirm
                                </button>
                            </div>
                        </div>
                    ))}

                    {stats && stats.total_pending > 10 && (
                        <a
                            href="/admin/verification"
                            className="block text-center text-sm text-primary-400 hover:text-primary-300 py-2 transition-colors"
                        >
                            View all {stats.total_pending} pending →
                        </a>
                    )}
                </div>
            )}
        </div>
    );
}
