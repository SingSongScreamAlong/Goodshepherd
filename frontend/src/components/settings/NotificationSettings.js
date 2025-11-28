import React, { useState, useEffect, useCallback } from 'react';
import {
  Bell,
  Mail,
  MessageSquare,
  Smartphone,
  Webhook,
  Moon,
  Clock,
  Filter,
  Save,
  Loader2,
  CheckCircle,
  AlertCircle,
  Globe,
  Tag,
} from 'lucide-react';
import {
  getNotificationPreferences,
  updateNotificationPreferences,
} from '../../services/notificationService';

const PRIORITY_OPTIONS = [
  { value: 'low', label: 'Low & Above', description: 'All alerts' },
  { value: 'medium', label: 'Medium & Above', description: 'Medium, High, Critical' },
  { value: 'high', label: 'High & Above', description: 'High and Critical only' },
  { value: 'critical', label: 'Critical Only', description: 'Only critical alerts' },
];

const DIGEST_OPTIONS = [
  { value: 'realtime', label: 'Real-time', description: 'Immediate notifications' },
  { value: 'hourly', label: 'Hourly Digest', description: 'Summary every hour' },
  { value: 'daily', label: 'Daily Digest', description: 'Summary once per day' },
  { value: 'weekly', label: 'Weekly Digest', description: 'Summary once per week' },
];

const REGIONS = [
  'Africa', 'Asia', 'Europe', 'Middle East', 'North America',
  'South America', 'Oceania', 'Central America', 'Caribbean',
];

const CATEGORIES = [
  'conflict', 'disaster', 'health', 'humanitarian', 'political',
  'terrorism', 'travel_advisory', 'economic', 'environmental',
];

/**
 * Toggle switch component
 */
function Toggle({ enabled, onChange, label, description, icon: Icon }) {
  return (
    <div className="flex items-center justify-between py-3">
      <div className="flex items-center gap-3">
        {Icon && <Icon className="w-5 h-5 text-gray-500" />}
        <div>
          <p className="font-medium text-gray-900">{label}</p>
          {description && (
            <p className="text-sm text-gray-500">{description}</p>
          )}
        </div>
      </div>
      <button
        type="button"
        onClick={() => onChange(!enabled)}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
          enabled ? 'bg-blue-600' : 'bg-gray-200'
        }`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
            enabled ? 'translate-x-6' : 'translate-x-1'
          }`}
        />
      </button>
    </div>
  );
}

/**
 * Multi-select chip component
 */
function ChipSelect({ options, selected, onChange, label }) {
  const toggleOption = (option) => {
    if (selected.includes(option)) {
      onChange(selected.filter((s) => s !== option));
    } else {
      onChange([...selected, option]);
    }
  };

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">{label}</label>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <button
            key={option}
            type="button"
            onClick={() => toggleOption(option)}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              selected.includes(option)
                ? 'bg-blue-100 text-blue-700 border-blue-300 border'
                : 'bg-gray-100 text-gray-600 border-gray-200 border hover:bg-gray-200'
            }`}
          >
            {option}
          </button>
        ))}
      </div>
      {selected.length === 0 && (
        <p className="text-xs text-gray-500">No filter applied - all {label.toLowerCase()} included</p>
      )}
    </div>
  );
}

/**
 * Notification Settings Component
 */
export default function NotificationSettings() {
  const [preferences, setPreferences] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  // Load preferences
  useEffect(() => {
    async function loadPreferences() {
      try {
        const prefs = await getNotificationPreferences();
        setPreferences(prefs);
        setError(null);
      } catch (err) {
        setError('Failed to load notification preferences');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadPreferences();
  }, []);

  // Update a single preference field
  const updateField = useCallback((field, value) => {
    setPreferences((prev) => ({ ...prev, [field]: value }));
    setSuccess(false);
  }, []);

  // Save preferences
  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(false);

    try {
      const updated = await updateNotificationPreferences(preferences);
      setPreferences(updated);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError('Failed to save preferences');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!preferences) {
    return (
      <div className="p-4 bg-red-50 text-red-700 rounded-lg">
        <AlertCircle className="w-5 h-5 inline mr-2" />
        {error || 'Unable to load preferences'}
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Notification Settings</h2>
          <p className="text-sm text-gray-500">
            Configure how and when you receive alerts
          </p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {saving ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : success ? (
            <CheckCircle className="w-4 h-4" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          {saving ? 'Saving...' : success ? 'Saved!' : 'Save Changes'}
        </button>
      </div>

      {/* Status messages */}
      {error && (
        <div className="p-3 bg-red-50 text-red-700 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          {error}
        </div>
      )}

      {/* Notification Channels */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Bell className="w-5 h-5" />
          Notification Channels
        </h3>
        <div className="divide-y divide-gray-100">
          <Toggle
            enabled={preferences.email_enabled}
            onChange={(v) => updateField('email_enabled', v)}
            label="Email Notifications"
            description="Receive alerts via email"
            icon={Mail}
          />
          <Toggle
            enabled={preferences.sms_enabled}
            onChange={(v) => updateField('sms_enabled', v)}
            label="SMS Notifications"
            description="Receive alerts via text message"
            icon={MessageSquare}
          />
          <Toggle
            enabled={preferences.whatsapp_enabled}
            onChange={(v) => updateField('whatsapp_enabled', v)}
            label="WhatsApp Notifications"
            description="Receive alerts via WhatsApp"
            icon={Smartphone}
          />
          <Toggle
            enabled={preferences.push_enabled}
            onChange={(v) => updateField('push_enabled', v)}
            label="Push Notifications"
            description="Browser push notifications"
            icon={Bell}
          />
          <Toggle
            enabled={preferences.webhook_enabled}
            onChange={(v) => updateField('webhook_enabled', v)}
            label="Webhook Integration"
            description="Send alerts to external systems"
            icon={Webhook}
          />
        </div>

        {/* Phone number input */}
        {(preferences.sms_enabled || preferences.whatsapp_enabled) && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Phone Number
            </label>
            <input
              type="tel"
              value={preferences.phone_number || ''}
              onChange={(e) => updateField('phone_number', e.target.value)}
              placeholder="+1234567890"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Include country code (e.g., +1 for US)
            </p>
          </div>
        )}

        {/* Webhook URL input */}
        {preferences.webhook_enabled && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Webhook URL
            </label>
            <input
              type="url"
              value={preferences.webhook_url || ''}
              onChange={(e) => updateField('webhook_url', e.target.value)}
              placeholder="https://your-server.com/webhook"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        )}
      </div>

      {/* Digest Settings */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5" />
          Digest Frequency
        </h3>
        <div className="grid grid-cols-2 gap-3">
          {DIGEST_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => updateField('digest_frequency', option.value)}
              className={`p-3 rounded-lg border text-left transition-colors ${
                preferences.digest_frequency === option.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <p className="font-medium text-gray-900">{option.label}</p>
              <p className="text-xs text-gray-500">{option.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Priority Filter */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Filter className="w-5 h-5" />
          Minimum Priority
        </h3>
        <div className="space-y-2">
          {PRIORITY_OPTIONS.map((option) => (
            <label
              key={option.value}
              className={`flex items-center p-3 rounded-lg border cursor-pointer transition-colors ${
                preferences.min_priority === option.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <input
                type="radio"
                name="min_priority"
                value={option.value}
                checked={preferences.min_priority === option.value}
                onChange={(e) => updateField('min_priority', e.target.value)}
                className="sr-only"
              />
              <div>
                <p className="font-medium text-gray-900">{option.label}</p>
                <p className="text-xs text-gray-500">{option.description}</p>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Region & Category Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-6">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Globe className="w-5 h-5" />
          Content Filters
        </h3>
        
        <ChipSelect
          label="Watched Regions"
          options={REGIONS}
          selected={preferences.watched_regions || []}
          onChange={(v) => updateField('watched_regions', v)}
        />

        <ChipSelect
          label="Watched Categories"
          options={CATEGORIES}
          selected={preferences.watched_categories || []}
          onChange={(v) => updateField('watched_categories', v)}
        />
      </div>

      {/* Quiet Hours */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Moon className="w-5 h-5" />
          Quiet Hours
        </h3>
        
        <Toggle
          enabled={preferences.quiet_hours_enabled}
          onChange={(v) => updateField('quiet_hours_enabled', v)}
          label="Enable Quiet Hours"
          description="Pause non-critical notifications during specified hours"
        />

        {preferences.quiet_hours_enabled && (
          <div className="mt-4 pt-4 border-t border-gray-100 grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Time
              </label>
              <input
                type="time"
                value={preferences.quiet_hours_start || '22:00'}
                onChange={(e) => updateField('quiet_hours_start', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Time
              </label>
              <input
                type="time"
                value={preferences.quiet_hours_end || '07:00'}
                onChange={(e) => updateField('quiet_hours_end', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <p className="col-span-2 text-xs text-gray-500">
              Critical alerts will still be delivered during quiet hours
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
