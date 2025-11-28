import React, { useCallback, useEffect, useMemo, useState } from 'react';
import './App.css';
import EventMap from './components/EventMap';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { AuthModal, UserMenu } from './components/auth';

const API_BASE = process.env.REACT_APP_API_BASE ?? '';
const DEFAULT_QUERY = 'europe';
const THREAT_OPTIONS = ['low', 'medium', 'high', 'critical'];
const PRIORITY_OPTIONS = ['low', 'medium', 'high', 'critical'];
const emptyRuleForm = {
  name: '',
  description: '',
  regions: '',
  categories: '',
  minimum_threat: 'medium',
  minimum_credibility: 0.6,
  lookback_minutes: 60,
  priority: 'high',
  auto_ack: false,
};

function AppContent() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [reports, setReports] = useState([]);
  const [reportError, setReportError] = useState(null);
  const [alertRules, setAlertRules] = useState([]);
  const [rulesLoading, setRulesLoading] = useState(false);
  const [rulesError, setRulesError] = useState(null);
  const [rulesStatus, setRulesStatus] = useState(null);
  const [ruleForm, setRuleForm] = useState(emptyRuleForm);
  const [adminKey, setAdminKey] = useState('');
  const [editingRuleId, setEditingRuleId] = useState(null);
  const [ruleSubmitting, setRuleSubmitting] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authModalView, setAuthModalView] = useState('login');
  const [authToken, setAuthToken] = useState(null);

  // Handle URL params for auth flows (password reset, email verification)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const resetToken = params.get('token');
    const action = params.get('action');
    
    if (resetToken && action === 'reset-password') {
      setAuthToken(resetToken);
      setAuthModalView('reset-password');
      setShowAuthModal(true);
      // Clean URL
      window.history.replaceState({}, '', window.location.pathname);
    } else if (resetToken && action === 'verify-email') {
      setAuthToken(resetToken);
      setAuthModalView('verify-email');
      setShowAuthModal(true);
      // Clean URL
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function fetchEvents() {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `${API_BASE}/api/search?q=${encodeURIComponent(DEFAULT_QUERY)}`,
          { signal: controller.signal }
        );

        if (!response.ok) {
          throw new Error(`API responded with ${response.status}`);
        }

        const payload = await response.json();
        setEvents(payload?.results ?? []);
      } catch (err) {
        if (err.name !== 'AbortError') {
          setError(err.message ?? 'Unknown error');
        }
      } finally {
        setLoading(false);
      }
    }

    async function fetchReports() {
      setReportError(null);

      try {
        const response = await fetch(`${API_BASE}/api/reports?limit=5`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Reports API responded with ${response.status}`);
        }

        const payload = await response.json();
        setReports(payload?.results ?? []);
      } catch (err) {
        if (err.name !== 'AbortError') {
          setReportError(err.message ?? 'Unable to load reports');
        }
      }
    }

    fetchEvents();
    fetchReports();

    return () => {
      controller.abort();
    };
  }, []);

  const loadAlertRules = useCallback(async () => {
    setRulesLoading(true);
    setRulesError(null);
    setRulesStatus(null);
    try {
      const response = await fetch(`${API_BASE}/api/alerts/rules`);
      if (!response.ok) {
        throw new Error(`Alert rules API responded with ${response.status}`);
      }
      const payload = await response.json();
      setAlertRules(Array.isArray(payload) ? payload : []);
    } catch (err) {
      setRulesError(err.message ?? 'Unable to load alert rules');
      setAlertRules([]);
    } finally {
      setRulesLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAlertRules();
  }, [loadAlertRules]);

  const handleRuleFieldChange = (event) => {
    const { name, value, type, checked } = event.target;
    setRuleForm((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const resetRuleForm = () => {
    setRuleForm(emptyRuleForm);
    setEditingRuleId(null);
  };

  const ensureAdminKey = () => {
    if (!adminKey) {
      setRulesError('Provide the admin API key to modify alert rules.');
      return false;
    }
    return true;
  };

  const buildPayloadFromForm = () => {
    const regions = ruleForm.regions
      .split(',')
      .map((entry) => entry.trim())
      .filter(Boolean);
    const categories = ruleForm.categories
      .split(',')
      .map((entry) => entry.trim())
      .filter(Boolean);

    return {
      name: ruleForm.name.trim(),
      description: ruleForm.description.trim() || null,
      regions: regions.length ? regions : null,
      categories: categories.length ? categories : null,
      minimum_threat: ruleForm.minimum_threat,
      minimum_credibility: Number(ruleForm.minimum_credibility),
      lookback_minutes: Number(ruleForm.lookback_minutes),
      priority: ruleForm.priority,
      auto_ack: Boolean(ruleForm.auto_ack),
    };
  };

  const handleRuleSubmit = async (event) => {
    event.preventDefault();
    setRulesError(null);
    setRulesStatus(null);

    if (!ensureAdminKey()) {
      return;
    }

    if (!ruleForm.name.trim()) {
      setRulesError('Rule name is required.');
      return;
    }

    const payload = buildPayloadFromForm();
    if (Number.isNaN(payload.minimum_credibility) || Number.isNaN(payload.lookback_minutes)) {
      setRulesError('Credibility and lookback must be numeric values.');
      return;
    }

    const method = editingRuleId ? 'PUT' : 'POST';
    const endpoint = editingRuleId
      ? `${API_BASE}/api/alerts/rules/${encodeURIComponent(editingRuleId)}`
      : `${API_BASE}/api/alerts/rules`;

    setRuleSubmitting(true);
    try {
      const response = await fetch(endpoint, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-API-Key': adminKey,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `Rule ${editingRuleId ? 'update' : 'creation'} failed`);
      }

      await loadAlertRules();
      setRulesStatus(`Rule ${editingRuleId ? 'updated' : 'created'} successfully.`);
      resetRuleForm();
    } catch (err) {
      setRulesError(err.message ?? 'Unable to save rule');
    } finally {
      setRuleSubmitting(false);
    }
  };

  const handleRuleEdit = (rule) => {
    setEditingRuleId(rule.id);
    setRuleForm({
      name: rule.name,
      description: rule.description ?? '',
      regions: (rule.regions ?? []).join(', '),
      categories: (rule.categories ?? []).join(', '),
      minimum_threat: rule.minimum_threat,
      minimum_credibility: rule.minimum_credibility,
      lookback_minutes: rule.lookback_minutes,
      priority: rule.priority,
      auto_ack: Boolean(rule.auto_ack),
    });
    setRulesStatus(null);
    setRulesError(null);
  };

  const handleRuleDelete = async (ruleId) => {
    setRulesError(null);
    setRulesStatus(null);
    if (!ensureAdminKey()) {
      return;
    }

    if (!window.confirm('Delete this alert rule?')) {
      return;
    }

    setRuleSubmitting(true);
    try {
      const response = await fetch(`${API_BASE}/api/alerts/rules/${encodeURIComponent(ruleId)}`, {
        method: 'DELETE',
        headers: {
          'X-Admin-API-Key': adminKey,
        },
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || 'Rule deletion failed');
      }

      await loadAlertRules();
      setRulesStatus('Rule deleted.');
      if (editingRuleId === ruleId) {
        resetRuleForm();
      }
    } catch (err) {
      setRulesError(err.message ?? 'Unable to delete rule');
    } finally {
      setRuleSubmitting(false);
    }
  };

  const summary = useMemo(() => {
    const categories = new Set();
    const statuses = new Map();
    events.forEach((event) => {
      if (event.category) {
        categories.add(event.category);
      }
      if (event.verification_status) {
        statuses.set(
          event.verification_status,
          (statuses.get(event.verification_status) ?? 0) + 1
        );
      }
    });

    return {
      total: events.length,
      categories: Array.from(categories).sort(),
      statuses: Array.from(statuses.entries()),
    };
  }, [events]);

  const openAuthModal = (view = 'login') => {
    setAuthModalView(view);
    setAuthToken(null);
    setShowAuthModal(true);
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="App-header-content">
          <div className="App-header-left">
            <h1>Good Shepherd Operational Picture</h1>
            <p className="App-subtitle">
              Live situational awareness prototype
            </p>
          </div>
          <div className="App-header-right">
            {isAuthenticated ? (
              <UserMenu />
            ) : (
              <button
                className="App-signin-button"
                onClick={() => openAuthModal('login')}
              >
                Sign In
              </button>
            )}
          </div>
        </div>
      </header>

      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        initialView={authModalView}
        token={authToken}
      />

      <main className="App-main">
        <section className="App-map">
          <EventMap events={events} height={500} />
        </section>

        <aside className="App-sidebar">
          <SummaryPanel summary={summary} loading={loading} />
          <EventList events={events} loading={loading} error={error} />
          <ReportList reports={reports} error={reportError} />
          <AlertRulePanel
            alertRules={alertRules}
            rulesLoading={rulesLoading}
            rulesError={rulesError}
            rulesStatus={rulesStatus}
            ruleForm={ruleForm}
            adminKey={adminKey}
            setAdminKey={setAdminKey}
            onFieldChange={handleRuleFieldChange}
            onSubmit={handleRuleSubmit}
            onReset={resetRuleForm}
            onEdit={handleRuleEdit}
            onDelete={handleRuleDelete}
            ruleSubmitting={ruleSubmitting}
            editingRuleId={editingRuleId}
          />
        </aside>
      </main>
    </div>
  );
}

function SummaryPanel({ summary, loading }) {
  return (
    <section className="SummaryPanel">
      <h2>Summary</h2>
      {loading ? (
        <p>Loading…</p>
      ) : (
        <>
          <p>
            <strong>{summary.total}</strong> active events
          </p>
          <p>
            Categories: {summary.categories.length ? summary.categories.join(', ') : 'pending enrichment'}
          </p>
          {summary.statuses?.length ? (
            <dl className="SummaryPanel-statuses">
              {summary.statuses.map(([status, count]) => (
                <div key={status}>
                  <dt>{status}</dt>
                  <dd>{count}</dd>
                </div>
              ))}
            </dl>
          ) : (
            <p>Verification pending.</p>
          )}
        </>
      )}
    </section>
  );
}

function EventList({ events, loading, error }) {
  return (
    <section className="EventList">
      <h2>Latest events</h2>
      {loading && <p>Fetching events…</p>}
      {error && <p className="EventList-error">{error}</p>}
      {!loading && !events.length && !error && <p>No events yet. Configure ingestion to populate the feed.</p>}

      <ul>
        {events.map((event) => (
          <li key={event.id ?? event.link}>
            <h3>{event.title ?? 'Untitled event'}</h3>
            {event.summary && <p>{event.summary}</p>}
            <dl>
              {event.category && (
                <div>
                  <dt>Category</dt>
                  <dd>{event.category}</dd>
                </div>
              )}
              {event.region && (
                <div>
                  <dt>Region</dt>
                  <dd>{event.region}</dd>
                </div>
              )}
              {event.link && (
                <div>
                  <dt>Source</dt>
                  <dd>
                    <a href={event.link} target="_blank" rel="noreferrer">
                      View advisory
                    </a>
                  </dd>
                </div>
              )}
              {event.verification_status && (
                <div>
                  <dt>Verification</dt>
                  <dd>{event.verification_status}</dd>
                </div>
              )}
              {typeof event.credibility_score === 'number' && (
                <div>
                  <dt>Credibility</dt>
                  <dd>{event.credibility_score.toFixed(2)}</dd>
                </div>
              )}
              {event.threat_level && (
                <div>
                  <dt>Threat</dt>
                  <dd className={`EventList-threat EventList-threat--${event.threat_level}`}>
                    {event.threat_level}
                  </dd>
                </div>
              )}
              {event.duplicate_of && (
                <div>
                  <dt>Duplicate of</dt>
                  <dd>{event.duplicate_of}</dd>
                </div>
              )}
            </dl>
          </li>
        ))}
      </ul>
    </section>
  );
}

function ReportList({ reports, error }) {
  return (
    <section className="ReportList">
      <h2>Latest reports</h2>
      {error && <p className="ReportList-error">{error}</p>}
      {!reports.length && !error ? (
        <p>No reports generated yet. Trigger one via the backend API.</p>
      ) : (
        <ul>
          {reports.map((report) => (
            <li key={report.id}>
              <h3>{report.title}</h3>
              <p>{report.summary ?? 'No summary available.'}</p>
              <dl>
                <div>
                  <dt>Generated</dt>
                  <dd>{new Date(report.generated_at).toLocaleString()}</dd>
                </div>
                <div>
                  <dt>Region</dt>
                  <dd>{report.region ?? 'All'}</dd>
                </div>
                <div>
                  <dt>Type</dt>
                  <dd>{report.report_type}</dd>
                </div>
                <div>
                  <dt>Sources</dt>
                  <dd>{report.source_event_ids?.length ?? 0}</dd>
                </div>
              </dl>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function App() {
  return <AppContent />;
}

function AlertRulePanel({
  alertRules,
  rulesLoading,
  rulesError,
  rulesStatus,
  ruleForm,
  adminKey,
  setAdminKey,
  onFieldChange,
  onSubmit,
  onReset,
  onEdit,
  onDelete,
  ruleSubmitting,
  editingRuleId,
}) {
  return (
    <section className="AlertRulePanel">
      <h2>Alert rules</h2>
      <p className="AlertRulePanel-hint">
        Manage automatic alert thresholds. Mutations require the admin API key.
      </p>

      <label className="AlertRulePanel-admin">
        <span>Admin API Key</span>
        <input
          type="password"
          placeholder="Enter admin key"
          value={adminKey}
          onChange={(event) => setAdminKey(event.target.value)}
        />
      </label>

      {rulesError && <p className="AlertRulePanel-error">{rulesError}</p>}
      {rulesStatus && <p className="AlertRulePanel-status">{rulesStatus}</p>}

      <div className="AlertRulePanel-list">
        {rulesLoading ? (
          <p>Loading alert rules…</p>
        ) : !alertRules.length ? (
          <p>No alert rules configured yet.</p>
        ) : (
          <ul>
            {alertRules.map((rule) => (
              <li key={rule.id} className="AlertRulePanel-item">
                <div className="AlertRulePanel-item-header">
                  <strong>{rule.name}</strong>
                  <div className="AlertRulePanel-actions">
                    <button type="button" onClick={() => onEdit(rule)} disabled={ruleSubmitting}>
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => onDelete(rule.id)}
                      disabled={ruleSubmitting}
                    >
                      Delete
                    </button>
                  </div>
                </div>
                {rule.description && <p>{rule.description}</p>}
                <dl>
                  <div>
                    <dt>Threat</dt>
                    <dd>{rule.minimum_threat}</dd>
                  </div>
                  <div>
                    <dt>Credibility</dt>
                    <dd>{rule.minimum_credibility}</dd>
                  </div>
                  <div>
                    <dt>Lookback (min)</dt>
                    <dd>{rule.lookback_minutes}</dd>
                  </div>
                  <div>
                    <dt>Priority</dt>
                    <dd>{rule.priority}</dd>
                  </div>
                  <div>
                    <dt>Auto-ack</dt>
                    <dd>{rule.auto_ack ? 'Yes' : 'No'}</dd>
                  </div>
                  <div>
                    <dt>Regions</dt>
                    <dd>{rule.regions?.length ? rule.regions.join(', ') : 'Any'}</dd>
                  </div>
                  <div>
                    <dt>Categories</dt>
                    <dd>{rule.categories?.length ? rule.categories.join(', ') : 'Any'}</dd>
                  </div>
                </dl>
              </li>
            ))}
          </ul>
        )}
      </div>

      <form className="AlertRulePanel-form" onSubmit={onSubmit}>
        <h3>{editingRuleId ? 'Edit alert rule' : 'Create alert rule'}</h3>
        <label>
          <span>Name*</span>
          <input
            name="name"
            value={ruleForm.name}
            onChange={onFieldChange}
            required
          />
        </label>
        <label>
          <span>Description</span>
          <textarea
            name="description"
            value={ruleForm.description}
            onChange={onFieldChange}
            rows={2}
          />
        </label>
        <label>
          <span>Regions (comma-separated)</span>
          <input name="regions" value={ruleForm.regions} onChange={onFieldChange} />
        </label>
        <label>
          <span>Categories (comma-separated)</span>
          <input name="categories" value={ruleForm.categories} onChange={onFieldChange} />
        </label>
        <label>
          <span>Minimum threat*</span>
          <select name="minimum_threat" value={ruleForm.minimum_threat} onChange={onFieldChange}>
            {THREAT_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>Minimum credibility (0-1)*</span>
          <input
            name="minimum_credibility"
            type="number"
            step="0.05"
            min="0"
            max="1"
            value={ruleForm.minimum_credibility}
            onChange={onFieldChange}
          />
        </label>
        <label>
          <span>Lookback minutes*</span>
          <input
            name="lookback_minutes"
            type="number"
            min="1"
            value={ruleForm.lookback_minutes}
            onChange={onFieldChange}
          />
        </label>
        <label>
          <span>Priority*</span>
          <select name="priority" value={ruleForm.priority} onChange={onFieldChange}>
            {PRIORITY_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
        <label className="AlertRulePanel-checkbox">
          <input
            name="auto_ack"
            type="checkbox"
            checked={ruleForm.auto_ack}
            onChange={onFieldChange}
          />
          <span>Auto-acknowledge after dispatch</span>
        </label>

        <div className="AlertRulePanel-formActions">
          <button type="submit" disabled={ruleSubmitting}>
            {ruleSubmitting ? 'Saving…' : editingRuleId ? 'Update rule' : 'Create rule'}
          </button>
          <button type="button" onClick={onReset} disabled={ruleSubmitting}>
            Clear
          </button>
        </div>
      </form>
    </section>
  );
}

export default App;
