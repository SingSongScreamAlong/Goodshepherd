/**
 * OrganizationSettings - Admin page for configuring organization-wide preferences.
 *
 * Allows administrators to customize default filters, alert thresholds, feature toggles,
 * display preferences, data retention policies, and regional focus.
 */
import { useState, useEffect } from 'react';
import { apiClient } from '../utils/api';
import Layout from '../components/Layout';

interface OrgSettings {
  id: string;
  organization_id: string;
  // Default Filters
  default_categories: string[] | null;
  default_sentiment_filter: string | null;
  default_min_relevance: number;
  // Alert Thresholds
  high_priority_threshold: number;
  alert_categories: string[] | null;
  alert_sentiment_types: string[] | null;
  // Feature Toggles
  enable_email_alerts: boolean;
  enable_clustering: boolean;
  enable_feedback_collection: boolean;
  enable_audit_logging: boolean;
  // Display Preferences
  default_map_zoom: number;
  default_map_center_lat: number | null;
  default_map_center_lon: number | null;
  events_per_page: number;
  // Data Retention
  event_retention_days: number | null;
  audit_log_retention_days: number;
  // Regional Focus
  focus_regions: string[] | null;
  exclude_regions: string[] | null;
  // Custom Configuration
  custom_config: Record<string, any> | null;
}

export default function OrganizationSettings() {
  const [settings, setSettings] = useState<OrgSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Form state
  const [formData, setFormData] = useState<Partial<OrgSettings>>({});

  const eventCategories = [
    'protest',
    'crime',
    'religious_freedom',
    'cultural_tension',
    'political',
    'infrastructure',
    'health',
    'migration',
    'economic',
    'weather',
    'community_event',
    'other',
  ];

  const sentimentTypes = ['positive', 'neutral', 'negative'];

  const europeanRegions = [
    'Western Europe',
    'Eastern Europe',
    'Northern Europe',
    'Southern Europe',
    'Central Europe',
    'Balkans',
  ];

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get('/settings');
      setSettings(response.data);
      setFormData(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load settings');
      console.error('Error fetching settings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(false);

      await apiClient.put('/settings', formData);

      setSuccess(true);
      await fetchSettings();

      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save settings');
      console.error('Error saving settings:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleResetSettings = async () => {
    if (!confirm('Are you sure you want to reset all settings to defaults?')) {
      return;
    }

    try {
      setSaving(true);
      setError(null);

      await apiClient.post('/settings/reset');

      setSuccess(true);
      await fetchSettings();

      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reset settings');
      console.error('Error resetting settings:', err);
    } finally {
      setSaving(false);
    }
  };

  const toggleCategory = (category: string) => {
    const current = formData.default_categories || [];
    if (current.includes(category)) {
      setFormData({
        ...formData,
        default_categories: current.filter((c) => c !== category),
      });
    } else {
      setFormData({
        ...formData,
        default_categories: [...current, category],
      });
    }
  };

  const toggleAlertCategory = (category: string) => {
    const current = formData.alert_categories || [];
    if (current.includes(category)) {
      setFormData({
        ...formData,
        alert_categories: current.filter((c) => c !== category),
      });
    } else {
      setFormData({
        ...formData,
        alert_categories: [...current, category],
      });
    }
  };

  const toggleRegion = (region: string, field: 'focus_regions' | 'exclude_regions') => {
    const current = formData[field] || [];
    if (current.includes(region)) {
      setFormData({
        ...formData,
        [field]: current.filter((r) => r !== region),
      });
    } else {
      setFormData({
        ...formData,
        [field]: [...current, region],
      });
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-500">Loading settings...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Organization Settings</h1>
          <p className="text-gray-600 mt-2">
            Configure default filters, alerts, and platform behavior for your organization
          </p>
        </div>

        {/* Success Message */}
        {success && (
          <div className="mb-6 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md">
            Settings saved successfully!
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
            {error}
          </div>
        )}

        <div className="space-y-6">
          {/* Default Filters Section */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Default Filters</h2>
            <p className="text-sm text-gray-600 mb-4">
              Set default filter preferences that will be applied to stream and map views
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Default Categories
                </label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {eventCategories.map((category) => (
                    <label key={category} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={(formData.default_categories || []).includes(category)}
                        onChange={() => toggleCategory(category)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2"
                      />
                      <span className="text-sm capitalize">
                        {category.replace(/_/g, ' ')}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Default Sentiment Filter
                </label>
                <select
                  value={formData.default_sentiment_filter || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, default_sentiment_filter: e.target.value || null })
                  }
                  className="w-full md:w-64 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  <option value="">All Sentiments</option>
                  {sentimentTypes.map((sentiment) => (
                    <option key={sentiment} value={sentiment}>
                      {sentiment.charAt(0).toUpperCase() + sentiment.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Minimum Relevance Threshold: {formData.default_min_relevance?.toFixed(2) || '0.50'}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={formData.default_min_relevance || 0.5}
                  onChange={(e) =>
                    setFormData({ ...formData, default_min_relevance: parseFloat(e.target.value) })
                  }
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>0.00 (Show All)</span>
                  <span>1.00 (Only Highest Relevance)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Alert Thresholds Section */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Alert Thresholds</h2>
            <p className="text-sm text-gray-600 mb-4">
              Configure what triggers high-priority alerts for your organization
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  High-Priority Threshold: {formData.high_priority_threshold?.toFixed(2) || '0.80'}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={formData.high_priority_threshold || 0.8}
                  onChange={(e) =>
                    setFormData({ ...formData, high_priority_threshold: parseFloat(e.target.value) })
                  }
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>0.00 (Low Threshold)</span>
                  <span>1.00 (Very High Threshold)</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Alert Categories (which categories trigger alerts)
                </label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {eventCategories.map((category) => (
                    <label key={category} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={(formData.alert_categories || []).includes(category)}
                        onChange={() => toggleAlertCategory(category)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2"
                      />
                      <span className="text-sm capitalize">
                        {category.replace(/_/g, ' ')}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Feature Toggles Section */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Feature Toggles</h2>
            <p className="text-sm text-gray-600 mb-4">
              Enable or disable specific platform features
            </p>

            <div className="space-y-3">
              <label className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                <div>
                  <div className="text-sm font-medium text-gray-900">Email Alerts</div>
                  <div className="text-xs text-gray-500">
                    Send email notifications for high-priority events
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={formData.enable_email_alerts || false}
                  onChange={(e) =>
                    setFormData({ ...formData, enable_email_alerts: e.target.checked })
                  }
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </label>

              <label className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                <div>
                  <div className="text-sm font-medium text-gray-900">Event Clustering</div>
                  <div className="text-xs text-gray-500">
                    Automatically group similar events together
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={formData.enable_clustering ?? true}
                  onChange={(e) =>
                    setFormData({ ...formData, enable_clustering: e.target.checked })
                  }
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </label>

              <label className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                <div>
                  <div className="text-sm font-medium text-gray-900">Feedback Collection</div>
                  <div className="text-xs text-gray-500">
                    Allow users to provide feedback on events
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={formData.enable_feedback_collection ?? true}
                  onChange={(e) =>
                    setFormData({ ...formData, enable_feedback_collection: e.target.checked })
                  }
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </label>

              <label className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                <div>
                  <div className="text-sm font-medium text-gray-900">Audit Logging</div>
                  <div className="text-xs text-gray-500">
                    Track all user actions for accountability
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={formData.enable_audit_logging ?? true}
                  onChange={(e) =>
                    setFormData({ ...formData, enable_audit_logging: e.target.checked })
                  }
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </label>
            </div>
          </div>

          {/* Display Preferences Section */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Display Preferences</h2>
            <p className="text-sm text-gray-600 mb-4">
              Customize how information is displayed
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Events Per Page
                </label>
                <select
                  value={formData.events_per_page || 20}
                  onChange={(e) =>
                    setFormData({ ...formData, events_per_page: parseInt(e.target.value) })
                  }
                  className="w-full md:w-48 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  <option value={10}>10 events</option>
                  <option value={20}>20 events</option>
                  <option value={50}>50 events</option>
                  <option value={100}>100 events</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Default Map Zoom Level
                </label>
                <input
                  type="number"
                  min="1"
                  max="18"
                  value={formData.default_map_zoom || 5}
                  onChange={(e) =>
                    setFormData({ ...formData, default_map_zoom: parseInt(e.target.value) })
                  }
                  className="w-full md:w-32 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">1 = World view, 18 = Street level</p>
              </div>
            </div>
          </div>

          {/* Data Retention Section */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Data Retention</h2>
            <p className="text-sm text-gray-600 mb-4">
              Control how long data is stored in the system
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Event Retention (days)
                </label>
                <input
                  type="number"
                  min="1"
                  placeholder="Never delete (leave empty)"
                  value={formData.event_retention_days || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      event_retention_days: e.target.value ? parseInt(e.target.value) : null,
                    })
                  }
                  className="w-full md:w-64 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Leave empty to keep events indefinitely
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Audit Log Retention (days)
                </label>
                <input
                  type="number"
                  min="30"
                  value={formData.audit_log_retention_days || 365}
                  onChange={(e) =>
                    setFormData({ ...formData, audit_log_retention_days: parseInt(e.target.value) })
                  }
                  className="w-full md:w-64 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">Minimum 30 days for compliance</p>
              </div>
            </div>
          </div>

          {/* Regional Focus Section */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Regional Focus</h2>
            <p className="text-sm text-gray-600 mb-4">
              Prioritize or exclude specific geographic regions
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Focus Regions (prioritize these areas)
                </label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {europeanRegions.map((region) => (
                    <label key={region} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={(formData.focus_regions || []).includes(region)}
                        onChange={() => toggleRegion(region, 'focus_regions')}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2"
                      />
                      <span className="text-sm">{region}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Exclude Regions (filter out these areas)
                </label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {europeanRegions.map((region) => (
                    <label key={region} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={(formData.exclude_regions || []).includes(region)}
                        onChange={() => toggleRegion(region, 'exclude_regions')}
                        className="rounded border-gray-300 text-red-600 focus:ring-red-500 mr-2"
                      />
                      <span className="text-sm">{region}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-between items-center pt-4">
            <button
              onClick={handleResetSettings}
              disabled={saving}
              className="px-4 py-2 border border-red-300 text-red-700 rounded-md hover:bg-red-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Reset to Defaults
            </button>

            <button
              onClick={handleSaveSettings}
              disabled={saving}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </div>
      </div>
    </Layout>
  );
}
