import React, { useState, useEffect, useCallback } from 'react';
import {
  Bell,
  Plus,
  Edit2,
  Trash2,
  Save,
  X,
  AlertTriangle,
  Shield,
  CheckCircle,
  Loader2,
  Filter,
  Globe,
  Tag,
  Clock,
  Percent,
} from 'lucide-react';
import {
  getAlertRules,
  createAlertRule,
  updateAlertRule,
  deleteAlertRule,
} from '../../services/notificationService';

const PRIORITY_OPTIONS = [
  { value: 'critical', label: 'Critical', color: 'bg-red-500' },
  { value: 'high', label: 'High', color: 'bg-orange-500' },
  { value: 'medium', label: 'Medium', color: 'bg-yellow-500' },
  { value: 'low', label: 'Low', color: 'bg-green-500' },
];

const THREAT_LEVELS = ['critical', 'high', 'medium', 'low'];

const REGIONS = [
  'Africa', 'Asia', 'Europe', 'Middle East', 'North America',
  'South America', 'Oceania', 'Central America', 'Caribbean',
];

const CATEGORIES = [
  'conflict', 'disaster', 'health', 'humanitarian', 'political',
  'terrorism', 'travel_advisory', 'economic', 'environmental',
];

/**
 * Rule editor form
 */
function RuleEditor({ rule, onSave, onCancel, saving }) {
  const [form, setForm] = useState({
    name: rule?.name || '',
    description: rule?.description || '',
    priority: rule?.priority || 'medium',
    regions: rule?.regions || [],
    categories: rule?.categories || [],
    minimum_threat: rule?.minimum_threat || 'medium',
    minimum_credibility: rule?.minimum_credibility || 0.5,
    lookback_minutes: rule?.lookback_minutes || 60,
    auto_ack: rule?.auto_ack || false,
  });

  const updateForm = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const toggleArrayItem = (field, item) => {
    const current = form[field];
    if (current.includes(item)) {
      updateForm(field, current.filter((i) => i !== item));
    } else {
      updateForm(field, [...current, item]);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(form);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Name */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Rule Name *
        </label>
        <input
          type="text"
          value={form.name}
          onChange={(e) => updateForm('name', e.target.value)}
          required
          placeholder="e.g., Critical Conflict Alerts"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <textarea
          value={form.description}
          onChange={(e) => updateForm('description', e.target.value)}
          placeholder="Describe what this rule monitors..."
          rows={2}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 resize-none"
        />
      </div>

      {/* Priority */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Alert Priority
        </label>
        <div className="flex gap-2">
          {PRIORITY_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => updateForm('priority', opt.value)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors ${
                form.priority === opt.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <span className={`w-3 h-3 rounded-full ${opt.color}`} />
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Minimum Threat Level */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <Filter className="w-4 h-4 inline mr-1" />
          Minimum Threat Level
        </label>
        <select
          value={form.minimum_threat}
          onChange={(e) => updateForm('minimum_threat', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          {THREAT_LEVELS.map((level) => (
            <option key={level} value={level}>
              {level.charAt(0).toUpperCase() + level.slice(1)} & above
            </option>
          ))}
        </select>
      </div>

      {/* Minimum Credibility */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <Percent className="w-4 h-4 inline mr-1" />
          Minimum Credibility: {Math.round(form.minimum_credibility * 100)}%
        </label>
        <input
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={form.minimum_credibility}
          onChange={(e) => updateForm('minimum_credibility', parseFloat(e.target.value))}
          className="w-full"
        />
        <div className="flex justify-between text-xs text-gray-500">
          <span>0%</span>
          <span>50%</span>
          <span>100%</span>
        </div>
      </div>

      {/* Regions */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <Globe className="w-4 h-4 inline mr-1" />
          Filter by Regions
        </label>
        <div className="flex flex-wrap gap-2">
          {REGIONS.map((region) => (
            <button
              key={region}
              type="button"
              onClick={() => toggleArrayItem('regions', region)}
              className={`px-3 py-1 rounded-full text-sm transition-colors ${
                form.regions.includes(region)
                  ? 'bg-blue-100 text-blue-700 border border-blue-300'
                  : 'bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200'
              }`}
            >
              {region}
            </button>
          ))}
        </div>
        {form.regions.length === 0 && (
          <p className="text-xs text-gray-500 mt-1">No filter - all regions included</p>
        )}
      </div>

      {/* Categories */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <Tag className="w-4 h-4 inline mr-1" />
          Filter by Categories
        </label>
        <div className="flex flex-wrap gap-2">
          {CATEGORIES.map((category) => (
            <button
              key={category}
              type="button"
              onClick={() => toggleArrayItem('categories', category)}
              className={`px-3 py-1 rounded-full text-sm transition-colors ${
                form.categories.includes(category)
                  ? 'bg-blue-100 text-blue-700 border border-blue-300'
                  : 'bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200'
              }`}
            >
              {category}
            </button>
          ))}
        </div>
        {form.categories.length === 0 && (
          <p className="text-xs text-gray-500 mt-1">No filter - all categories included</p>
        )}
      </div>

      {/* Lookback */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          <Clock className="w-4 h-4 inline mr-1" />
          Lookback Period (minutes)
        </label>
        <input
          type="number"
          min="5"
          max="1440"
          value={form.lookback_minutes}
          onChange={(e) => updateForm('lookback_minutes', parseInt(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        />
        <p className="text-xs text-gray-500 mt-1">
          Only evaluate events from the last {form.lookback_minutes} minutes
        </p>
      </div>

      {/* Auto-acknowledge */}
      <div className="flex items-center gap-3">
        <input
          type="checkbox"
          id="auto_ack"
          checked={form.auto_ack}
          onChange={(e) => updateForm('auto_ack', e.target.checked)}
          className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
        />
        <label htmlFor="auto_ack" className="text-sm text-gray-700">
          Auto-acknowledge alerts (no manual acknowledgment required)
        </label>
      </div>

      {/* Actions */}
      <div className="flex gap-3 pt-4 border-t">
        <button
          type="submit"
          disabled={saving || !form.name}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {saving ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          {rule ? 'Update Rule' : 'Create Rule'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

/**
 * Rule card component
 */
function RuleCard({ rule, onEdit, onDelete, deleting }) {
  const priorityColor = PRIORITY_OPTIONS.find((p) => p.value === rule.priority)?.color || 'bg-gray-500';

  return (
    <div className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <span className={`w-3 h-3 rounded-full ${priorityColor} mt-1.5`} />
          <div>
            <h4 className="font-semibold text-gray-900">{rule.name}</h4>
            {rule.description && (
              <p className="text-sm text-gray-500 mt-1">{rule.description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => onEdit(rule)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Edit"
          >
            <Edit2 className="w-4 h-4 text-gray-500" />
          </button>
          <button
            onClick={() => onDelete(rule.id)}
            disabled={deleting}
            className="p-2 hover:bg-red-50 rounded-lg transition-colors"
            title="Delete"
          >
            {deleting ? (
              <Loader2 className="w-4 h-4 animate-spin text-red-500" />
            ) : (
              <Trash2 className="w-4 h-4 text-red-500" />
            )}
          </button>
        </div>
      </div>

      {/* Rule details */}
      <div className="mt-3 flex flex-wrap gap-2 text-xs">
        <span className="px-2 py-1 bg-gray-100 rounded-full">
          {rule.priority} priority
        </span>
        <span className="px-2 py-1 bg-gray-100 rounded-full">
          ≥ {rule.minimum_threat} threat
        </span>
        <span className="px-2 py-1 bg-gray-100 rounded-full">
          ≥ {Math.round(rule.minimum_credibility * 100)}% credibility
        </span>
        {rule.regions?.length > 0 && (
          <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded-full">
            {rule.regions.length} region(s)
          </span>
        )}
        {rule.categories?.length > 0 && (
          <span className="px-2 py-1 bg-green-50 text-green-700 rounded-full">
            {rule.categories.length} category(ies)
          </span>
        )}
        {rule.auto_ack && (
          <span className="px-2 py-1 bg-amber-50 text-amber-700 rounded-full">
            auto-ack
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * Alert Rules Manager Component
 */
export default function AlertRulesManager() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editing, setEditing] = useState(null); // null, 'new', or rule object
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(null);

  // Load rules
  const loadRules = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAlertRules();
      setRules(data);
    } catch (err) {
      setError('Failed to load alert rules');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRules();
  }, [loadRules]);

  // Save rule
  const handleSave = async (form) => {
    setSaving(true);
    try {
      if (editing === 'new') {
        const newRule = await createAlertRule(form);
        setRules((prev) => [...prev, newRule]);
      } else {
        const updated = await updateAlertRule(editing.id, form);
        setRules((prev) =>
          prev.map((r) => (r.id === editing.id ? updated : r))
        );
      }
      setEditing(null);
    } catch (err) {
      console.error('Failed to save rule:', err);
    } finally {
      setSaving(false);
    }
  };

  // Delete rule
  const handleDelete = async (ruleId) => {
    if (!window.confirm('Are you sure you want to delete this rule?')) return;
    
    setDeleting(ruleId);
    try {
      await deleteAlertRule(ruleId);
      setRules((prev) => prev.filter((r) => r.id !== ruleId));
    } catch (err) {
      console.error('Failed to delete rule:', err);
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Bell className="w-6 h-6 text-gray-700" />
          <div>
            <h2 className="text-lg font-bold text-gray-900">Alert Rules</h2>
            <p className="text-sm text-gray-500">
              Configure when to receive notifications
            </p>
          </div>
        </div>
        {!editing && (
          <button
            onClick={() => setEditing('new')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Rule
          </button>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          {error}
        </div>
      )}

      {/* Editor */}
      {editing && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            {editing === 'new' ? 'Create New Rule' : 'Edit Rule'}
          </h3>
          <RuleEditor
            rule={editing === 'new' ? null : editing}
            onSave={handleSave}
            onCancel={() => setEditing(null)}
            saving={saving}
          />
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      )}

      {/* Empty state */}
      {!loading && !editing && rules.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-xl">
          <Bell className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 mb-4">No alert rules configured</p>
          <button
            onClick={() => setEditing('new')}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Create Your First Rule
          </button>
        </div>
      )}

      {/* Rules list */}
      {!loading && !editing && rules.length > 0 && (
        <div className="space-y-3">
          {rules.map((rule) => (
            <RuleCard
              key={rule.id}
              rule={rule}
              onEdit={setEditing}
              onDelete={handleDelete}
              deleting={deleting === rule.id}
            />
          ))}
        </div>
      )}
    </div>
  );
}
