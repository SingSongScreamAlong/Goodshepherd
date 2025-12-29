/**
 * Verification Queue Widget - Shows pending incidents requiring review.
 */
import { useVerificationQueue, confirmIncident, debunkIncident } from '../hooks/useWorldAwareness';
import { getSeverityColor, getIncidentStatusColor } from '../types/worldAwareness';
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

    if (isLoading) {
        return (
            <div className="bg-white rounded-lg shadow p-6">
                <div className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
                    <div className="space-y-3">
                        <div className="h-16 bg-gray-200 rounded"></div>
                        <div className="h-16 bg-gray-200 rounded"></div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Verification Queue</h2>
                {stats && (
                    <div className="flex items-center space-x-3 text-sm">
                        <span className="text-gray-600">
                            {stats.total_pending} pending
                        </span>
                        {stats.critical > 0 && (
                            <span className="bg-red-100 text-red-800 px-2 py-0.5 rounded-full text-xs font-medium">
                                {stats.critical} critical
                            </span>
                        )}
                    </div>
                )}
            </div>

            {queue.length === 0 ? (
                <div className="text-center py-6">
                    <span className="text-4xl mb-2 block">✅</span>
                    <p className="text-sm text-gray-600">No incidents pending verification</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {queue.map((incident) => (
                        <div
                            key={incident.id}
                            className="border rounded-lg p-3 hover:bg-gray-50 transition-colors"
                        >
                            <div className="flex items-start justify-between mb-2">
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center space-x-2 mb-1">
                                        <span className={`px-2 py-0.5 text-xs font-medium rounded ${getSeverityColor(incident.severity)}`}>
                                            {incident.severity.toUpperCase()}
                                        </span>
                                        <span className={`px-2 py-0.5 text-xs rounded ${getIncidentStatusColor(incident.status)}`}>
                                            {incident.status}
                                        </span>
                                        {incident.confidence_score && (
                                            <span className="text-xs text-gray-500">
                                                {Math.round(incident.confidence_score * 100)}% conf
                                            </span>
                                        )}
                                    </div>
                                    <p className="text-sm font-medium text-gray-900 truncate">
                                        {incident.title || incident.summary}
                                    </p>
                                    <p className="text-xs text-gray-500 mt-1">
                                        {incident.location_name || 'Unknown location'} • {incident.category}
                                    </p>
                                </div>
                            </div>

                            <div className="flex items-center justify-end space-x-2 pt-2 border-t">
                                <button
                                    onClick={() => handleDebunk(incident.id)}
                                    disabled={actionInProgress === incident.id}
                                    className="px-3 py-1 text-xs font-medium text-red-700 bg-red-50 rounded hover:bg-red-100 disabled:opacity-50"
                                >
                                    Debunk
                                </button>
                                <button
                                    onClick={() => handleConfirm(incident.id)}
                                    disabled={actionInProgress === incident.id}
                                    className="px-3 py-1 text-xs font-medium text-green-700 bg-green-50 rounded hover:bg-green-100 disabled:opacity-50"
                                >
                                    Confirm
                                </button>
                            </div>
                        </div>
                    ))}

                    {stats && stats.total_pending > 10 && (
                        <a
                            href="/admin/verification"
                            className="block text-center text-sm text-primary-600 hover:text-primary-800 py-2"
                        >
                            View all {stats.total_pending} pending →
                        </a>
                    )}
                </div>
            )}
        </div>
    );
}
