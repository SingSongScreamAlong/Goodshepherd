/**
 * AuditLog - Admin-only page for viewing organization audit logs.
 *
 * Displays comprehensive audit trail of all user actions within the organization
 * for accountability, compliance, and security monitoring.
 */
import { useState, useEffect } from 'react';
import { apiClient } from '../utils/api';
import { formatDate } from '../utils/formatting';
import Layout from '../components/Layout';

interface AuditLogEntry {
  id: string;
  user_id: string | null;
  user_email: string | null;
  organization_id: string;
  action_type: string;
  object_type: string;
  object_id: string | null;
  description: string | null;
  metadata: Record<string, any> | null;
  ip_address: string | null;
  timestamp: string;
}

interface AuditStats {
  total_actions: number;
  actions_by_type: Record<string, number>;
  objects_by_type: Record<string, number>;
  most_active_users: Array<{ user_email: string; action_count: number }>;
}

export default function AuditLog() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [stats, setStats] = useState<AuditStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [actionType, setActionType] = useState('');
  const [objectType, setObjectType] = useState('');
  const [days, setDays] = useState(30);
  const [page, setPage] = useState(1);
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null);

  const pageSize = 50;

  // Action types for filter
  const actionTypes = ['create', 'update', 'delete', 'view', 'export', 'login', 'logout'];
  const objectTypes = ['dossier', 'watchlist', 'event', 'settings', 'user', 'feedback'];

  useEffect(() => {
    fetchAuditLogs();
    fetchAuditStats();
  }, [actionType, objectType, days, page]);

  const fetchAuditLogs = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        days: days.toString(),
        page: page.toString(),
        page_size: pageSize.toString(),
      });

      if (actionType) params.append('action_type', actionType);
      if (objectType) params.append('object_type', objectType);

      const response = await apiClient.get(`/audit/logs?${params.toString()}`);
      setLogs(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load audit logs');
      console.error('Error fetching audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAuditStats = async () => {
    try {
      const response = await apiClient.get(`/audit/stats?days=${days}`);
      setStats(response.data);
    } catch (err) {
      console.error('Error fetching audit stats:', err);
    }
  };

  const handleClearFilters = () => {
    setActionType('');
    setObjectType('');
    setDays(30);
    setPage(1);
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'create':
        return 'bg-green-100 text-green-800';
      case 'update':
        return 'bg-blue-100 text-blue-800';
      case 'delete':
        return 'bg-red-100 text-red-800';
      case 'view':
        return 'bg-gray-100 text-gray-800';
      case 'export':
        return 'bg-purple-100 text-purple-800';
      case 'login':
        return 'bg-indigo-100 text-indigo-800';
      case 'logout':
        return 'bg-gray-100 text-gray-600';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Audit Log</h1>
          <p className="text-gray-600 mt-2">
            Monitor all user actions for accountability and compliance
          </p>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Total Actions</div>
              <div className="text-2xl font-bold text-gray-900">{stats.total_actions}</div>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Actions by Type</div>
              <div className="mt-2 space-y-1">
                {Object.entries(stats.actions_by_type).slice(0, 3).map(([action, count]) => (
                  <div key={action} className="flex justify-between text-xs">
                    <span className="capitalize">{action}</span>
                    <span className="font-medium">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Objects by Type</div>
              <div className="mt-2 space-y-1">
                {Object.entries(stats.objects_by_type).slice(0, 3).map(([obj, count]) => (
                  <div key={obj} className="flex justify-between text-xs">
                    <span className="capitalize">{obj}</span>
                    <span className="font-medium">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Most Active</div>
              <div className="mt-2 space-y-1">
                {stats.most_active_users.slice(0, 2).map((user, idx) => (
                  <div key={idx} className="text-xs truncate">
                    <span className="text-gray-700">{user.user_email}</span>
                    <span className="ml-1 text-gray-500">({user.action_count})</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Action Type
              </label>
              <select
                value={actionType}
                onChange={(e) => {
                  setActionType(e.target.value);
                  setPage(1);
                }}
                className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="">All Actions</option>
                {actionTypes.map((type) => (
                  <option key={type} value={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Object Type
              </label>
              <select
                value={objectType}
                onChange={(e) => {
                  setObjectType(e.target.value);
                  setPage(1);
                }}
                className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="">All Objects</option>
                {objectTypes.map((type) => (
                  <option key={type} value={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Time Period
              </label>
              <select
                value={days}
                onChange={(e) => {
                  setDays(Number(e.target.value));
                  setPage(1);
                }}
                className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value={7}>Last 7 days</option>
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
                <option value={365}>Last year</option>
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={handleClearFilters}
                className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
              >
                Clear Filters
              </button>
            </div>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md mb-6">
            {error}
          </div>
        )}

        {/* Audit Log Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {loading ? (
            <div className="p-8 text-center text-gray-500">Loading audit logs...</div>
          ) : logs.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              No audit logs found for the selected filters.
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Timestamp
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        User
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Action
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Object
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        IP Address
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Details
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {logs.map((log) => (
                      <tr key={log.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                          {formatDate(log.timestamp)}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700">
                          {log.user_email || 'System'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-medium rounded ${getActionColor(log.action_type)}`}>
                            {log.action_type}
                          </span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700">
                          <span className="capitalize">{log.object_type}</span>
                          {log.object_id && (
                            <span className="ml-1 text-gray-400 text-xs">
                              ({log.object_id.substring(0, 8)})
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 font-mono">
                          {log.ip_address || '-'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm">
                          <button
                            onClick={() => setSelectedLog(log)}
                            className="text-blue-600 hover:text-blue-800"
                          >
                            View
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="bg-gray-50 px-4 py-3 flex items-center justify-between border-t border-gray-200">
                <div className="flex-1 flex justify-between sm:hidden">
                  <button
                    onClick={() => setPage(page - 1)}
                    disabled={page === 1}
                    className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage(page + 1)}
                    disabled={logs.length < pageSize}
                    className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      Page <span className="font-medium">{page}</span> · Showing{' '}
                      <span className="font-medium">{logs.length}</span> results
                    </p>
                  </div>
                  <div>
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                      <button
                        onClick={() => setPage(page - 1)}
                        disabled={page === 1}
                        className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Previous
                      </button>
                      <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                        {page}
                      </span>
                      <button
                        onClick={() => setPage(page + 1)}
                        disabled={logs.length < pageSize}
                        className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Next
                      </button>
                    </nav>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Detail Modal */}
        {selectedLog && (
          <>
            <div
              className="fixed inset-0 bg-black bg-opacity-50 z-40"
              onClick={() => setSelectedLog(null)}
            />
            <div className="fixed inset-0 z-50 overflow-y-auto">
              <div className="flex items-center justify-center min-h-screen px-4">
                <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Audit Log Details</h3>
                    <button
                      onClick={() => setSelectedLog(null)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>

                  <dl className="space-y-3">
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Timestamp</dt>
                      <dd className="mt-1 text-sm text-gray-900">{formatDate(selectedLog.timestamp)}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">User</dt>
                      <dd className="mt-1 text-sm text-gray-900">{selectedLog.user_email || 'System'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Action</dt>
                      <dd className="mt-1">
                        <span className={`px-2 py-1 text-xs font-medium rounded ${getActionColor(selectedLog.action_type)}`}>
                          {selectedLog.action_type}
                        </span>
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Object Type</dt>
                      <dd className="mt-1 text-sm text-gray-900 capitalize">{selectedLog.object_type}</dd>
                    </div>
                    {selectedLog.object_id && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Object ID</dt>
                        <dd className="mt-1 text-sm text-gray-900 font-mono">{selectedLog.object_id}</dd>
                      </div>
                    )}
                    {selectedLog.description && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Description</dt>
                        <dd className="mt-1 text-sm text-gray-900">{selectedLog.description}</dd>
                      </div>
                    )}
                    <div>
                      <dt className="text-sm font-medium text-gray-500">IP Address</dt>
                      <dd className="mt-1 text-sm text-gray-900 font-mono">{selectedLog.ip_address || 'N/A'}</dd>
                    </div>
                    {selectedLog.metadata && Object.keys(selectedLog.metadata).length > 0 && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Metadata</dt>
                        <dd className="mt-1 text-sm text-gray-900">
                          <pre className="bg-gray-50 p-3 rounded border border-gray-200 overflow-x-auto text-xs">
                            {JSON.stringify(selectedLog.metadata, null, 2)}
                          </pre>
                        </dd>
                      </div>
                    )}
                  </dl>

                  <div className="mt-6 flex justify-end">
                    <button
                      onClick={() => setSelectedLog(null)}
                      className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
                    >
                      Close
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </Layout>
  );
}
