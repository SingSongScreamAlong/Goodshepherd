import React, { useState, useEffect } from 'react';
import {
  Database,
  CheckCircle,
  XCircle,
  AlertCircle,
  Key,
  Globe,
  RefreshCw,
  Loader2,
  ExternalLink,
  Rss,
  MessageSquare,
  Activity,
} from 'lucide-react';
import { getDataSourcesStatus } from '../../services/notificationService';

const SOURCE_ICONS = {
  gdacs: Globe,
  reliefweb: Rss,
  who: Activity,
  acled: Database,
  social: MessageSquare,
};

/**
 * Data source card component
 */
function SourceCard({ id, source }) {
  const Icon = SOURCE_ICONS[id] || Database;
  
  return (
    <div
      className={`p-4 rounded-lg border-2 transition-colors ${
        source.enabled
          ? 'border-green-200 bg-green-50'
          : 'border-gray-200 bg-gray-50'
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div
            className={`p-2 rounded-lg ${
              source.enabled ? 'bg-green-100' : 'bg-gray-200'
            }`}
          >
            <Icon
              className={`w-5 h-5 ${
                source.enabled ? 'text-green-600' : 'text-gray-500'
              }`}
            />
          </div>
          <div>
            <h4 className="font-semibold text-gray-900">{source.name}</h4>
            <p className="text-sm text-gray-500">{source.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {source.enabled ? (
            <CheckCircle className="w-5 h-5 text-green-500" />
          ) : (
            <XCircle className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </div>

      {/* API key status */}
      {source.requires_api_key && (
        <div className="mt-3 pt-3 border-t border-current/10">
          <div className="flex items-center gap-2 text-sm">
            <Key className="w-4 h-4" />
            <span
              className={
                source.api_key_configured
                  ? 'text-green-600'
                  : 'text-amber-600'
              }
            >
              {source.api_key_configured
                ? 'API key configured'
                : 'API key required'}
            </span>
          </div>
        </div>
      )}

      {/* Source URL */}
      {source.url && (
        <a
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 inline-flex items-center gap-1 text-xs text-blue-600 hover:underline"
        >
          {source.url.replace('https://', '')}
          <ExternalLink className="w-3 h-3" />
        </a>
      )}
    </div>
  );
}

/**
 * Data Sources Status Component
 */
export default function DataSourcesStatus() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getDataSourcesStatus();
      setStatus(data);
    } catch (err) {
      setError('Failed to load data sources status');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 text-red-700 rounded-lg flex items-center gap-2">
        <AlertCircle className="w-5 h-5" />
        {error}
      </div>
    );
  }

  const { sources, total_enabled } = status;
  const totalSources = Object.keys(sources).length;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Database className="w-6 h-6 text-gray-700" />
          <div>
            <h2 className="text-lg font-bold text-gray-900">Data Sources</h2>
            <p className="text-sm text-gray-500">
              {total_enabled} of {totalSources} sources active
            </p>
          </div>
        </div>
        <button
          onClick={loadStatus}
          disabled={loading}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          title="Refresh"
        >
          <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Status bar */}
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-green-500 transition-all"
          style={{ width: `${(total_enabled / totalSources) * 100}%` }}
        />
      </div>

      {/* Source cards */}
      <div className="grid gap-4 sm:grid-cols-2">
        {Object.entries(sources).map(([id, source]) => (
          <SourceCard key={id} id={id} source={source} />
        ))}
      </div>

      {/* Configuration hint */}
      {total_enabled < totalSources && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5" />
            <div>
              <p className="font-medium text-amber-800">
                Some sources are disabled
              </p>
              <p className="text-sm text-amber-700 mt-1">
                Configure environment variables to enable additional data sources.
                Sources requiring API keys need valid credentials.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
