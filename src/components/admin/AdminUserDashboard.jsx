import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { config } from '../../config';
import {
  labelForPrimaryGoal,
  labelForReferralSource,
} from '../../constants/onboardingSurveyOptions';
import './AdminUserDashboard.css';

const TRADING_STYLE_LABELS = {
  day: 'Day trading',
  swing: 'Swing trading',
  both: 'Day & swing',
  unsure: 'Not sure yet',
};

const EXPERIENCE_LABELS = {
  beginner: 'Beginner',
  intermediate: 'Intermediate',
  advanced: 'Advanced',
};

const formatDate = (iso) => {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return iso.slice(0, 10);
  }
};

const labelTradingStyle = (k) => TRADING_STYLE_LABELS[k] || k?.replace(/_/g, ' ') || '—';
const labelExperience = (k) => EXPERIENCE_LABELS[k] || k || '—';
const labelGoal = (k) => labelForPrimaryGoal(k);
const labelReferral = (k) => labelForReferralSource(k);

const StatCard = ({ value, label, sub }) => (
  <div className="admin-dash-stat">
    <div className="admin-dash-stat-value">{value}</div>
    <div className="admin-dash-stat-label">{label}</div>
    {sub && <div className="admin-dash-stat-sub">{sub}</div>}
  </div>
);

const StatusTag = ({ status }) => (
  <span className={`admin-dash-tag ${status || 'unknown'}`}>{status || 'unknown'}</span>
);

const MiniUserTable = ({ rows, columns, emptyText }) => (
  <div className="admin-dash-mini-table-wrap">
    {rows?.length ? (
      <table className="admin-dash-mini-table">
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={row.uid || row.email || i}>
              {columns.map((c) => (
                <td key={c.key} title={typeof row[c.key] === 'string' ? row[c.key] : undefined}>
                  {c.render ? c.render(row) : row[c.key] ?? '—'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    ) : (
      <p className="admin-dash-empty">{emptyText}</p>
    )}
  </div>
);

const BreakdownList = ({ items, labelFn }) => (
  <ul className="admin-dash-breakdown">
    {(items || []).map((item) => (
      <li key={item.key}>
        <span className="admin-dash-breakdown-label">{labelFn(item.key)}</span>
        <span className="admin-dash-breakdown-bar-wrap">
          <span className="admin-dash-breakdown-bar" style={{ width: `${item.pct}%` }} />
        </span>
        <span className="admin-dash-breakdown-meta">
          {item.count} <span>({item.pct}%)</span>
        </span>
      </li>
    ))}
    {!items?.length && <li className="admin-dash-empty">No survey data yet</li>}
  </ul>
);

const AdminUserDashboard = () => {
  const { currentUser } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState('overview');
  const [search, setSearch] = useState('');
  const [filterOnboarding, setFilterOnboarding] = useState('all');
  const [filterSubscription, setFilterSubscription] = useState('all');
  const [filterActivity, setFilterActivity] = useState('all');
  const [hideExcluded, setHideExcluded] = useState(true);

  const fetchData = useCallback(async (force = false) => {
    if (!currentUser) return;
    setError(null);
    if (force) setRefreshing(true);
    else setLoading(true);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    try {
      const token = await currentUser.getIdToken();
      const qs = force ? '?refresh=true' : '';
      const res = await fetch(`${config.API_BASE_URL}/api/admin/user-dashboard/users${qs}`, {
        headers: { Authorization: `Bearer ${token}` },
        signal: controller.signal,
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(json.error || json.message || `Request failed (${res.status})`);
      }
      setData(json);
    } catch (err) {
      if (err.name === 'AbortError') {
        setError('Request timed out. Restart backend on port 5001 and click Refresh.');
      } else if (err.message === 'Failed to fetch' || err.message?.includes('NetworkError')) {
        setError(`Cannot reach backend at ${config.API_BASE_URL}. Start the backend and try again.`);
      } else {
        setError(err.message || 'Failed to load dashboard');
      }
    } finally {
      clearTimeout(timeoutId);
      setLoading(false);
      setRefreshing(false);
    }
  }, [currentUser]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const filteredUsers = useMemo(() => {
    const users = data?.users || [];
    const q = search.trim().toLowerCase();
    return users.filter((u) => {
      if (hideExcluded && u.is_excluded) return false;
      if (q) {
        const hay = `${u.email} ${u.display_name} ${u.uid}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      if (filterOnboarding !== 'all' && u.onboarding_status !== filterOnboarding) return false;
      if (filterSubscription !== 'all' && u.subscription_status !== filterSubscription) return false;
      if (filterActivity === 'active_7d' && (u.days_since_active ?? 999) > 7) return false;
      if (filterActivity === 'active_30d' && (u.days_since_active ?? 999) > 30) return false;
      if (filterActivity === 'ai_users' && !(u.total_ai_analyses > 0)) return false;
      if (filterActivity === 'telegram' && !u.receives_alert_delivery) return false;
      if (filterActivity === 'never_activated' && !u.never_activated) return false;
      if (filterActivity === 'inactive_30d' && (u.days_since_active ?? 0) <= 30) return false;
      return true;
    });
  }, [data, search, filterOnboarding, filterSubscription, filterActivity, hideExcluded]);

  const exportCsv = () => {
    const users = filteredUsers.length ? filteredUsers : data?.users || [];
    if (!users.length) return;
    const cols = [
      'email', 'display_name', 'uid', 'provider_label', 'email_verified', 'created_at',
      'last_sign_in', 'onboarding_status', 'subscription_status', 'total_ai_analyses',
      'referral_source', 'experience_level', 'primary_goal', 'trading_style',
      'receives_alert_delivery', 'telegram_chat_id', 'never_activated', 'is_excluded', 'marketing_opt_in',
    ];
    const escape = (v) => {
      const s = String(v ?? '');
      return s.includes(',') || s.includes('"') ? `"${s.replace(/"/g, '""')}"` : s;
    };
    const lines = [cols.join(','), ...users.map((u) => cols.map((c) => escape(u[c])).join(','))];
    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `fxsentinel_users_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const summary = data?.summary;
  const insights = data?.insights;
  const meta = data?.meta;
  const onboarding = insights?.onboarding;
  const visibleUserCount = hideExcluded
    ? (meta?.analytics_user_count ?? (data?.users || []).filter((u) => !u.is_excluded).length)
    : (data?.users?.length || 0);

  const exportMarketingCsv = () => {
    const users = insights?.marketing_opt_in_users || [];
    if (!users.length) return;
    const cols = ['email', 'display_name', 'referral_source', 'created_at'];
    const escape = (v) => {
      const s = String(v ?? '');
      return s.includes(',') || s.includes('"') ? `"${s.replace(/"/g, '""')}"` : s;
    };
    const lines = [
      cols.join(','),
      ...users.map((u) => cols.map((c) => escape(c === 'referral_source' ? labelReferral(u[c]) : u[c])).join(',')),
    ];
    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `fxsentinel_marketing_opt_in_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  if (loading && !data) {
    return (
      <div className="admin-dash-loading">
        <div className="admin-dash-spinner" />
        <p>Loading your user base…</p>
        <p className="admin-dash-loading-sub">Auth + Firestore + Telegram delivery (~15 sec)</p>
      </div>
    );
  }

  const emailCol = {
    key: 'email',
    label: 'User',
    render: (r) => (
      <span>
        <strong>{r.email || '—'}</strong>
        {r.display_name && r.display_name !== r.email && (
          <span className="admin-dash-subline">{r.display_name}</span>
        )}
      </span>
    ),
  };

  return (
    <div className="admin-dash">
      <header className="admin-dash-header">
        <div>
          <h1>Your users at a glance</h1>
          <p>
            {summary?.total_users ?? 0} real users
            {(meta?.excluded_count ?? summary?.excluded_count) > 0 && (
              <> · {(meta?.excluded_count ?? summary?.excluded_count)} internal/test excluded</>
            )}
            {summary?.generated_at && <> · updated {formatDate(summary.generated_at)}</>}
          </p>
        </div>
        <div className="admin-dash-header-actions">
          <Link to="/dashboard" className="admin-dash-btn admin-dash-btn-secondary">Main app</Link>
          <button type="button" className="admin-dash-btn admin-dash-btn-secondary" disabled={!data?.users?.length} onClick={exportCsv}>
            Export CSV
          </button>
          <button
            type="button"
            className="admin-dash-btn admin-dash-btn-secondary"
            disabled={!insights?.marketing_opt_in_users?.length}
            onClick={exportMarketingCsv}
            title="Users who completed onboarding and opted in to product emails"
          >
            Export marketing list ({meta?.marketing_opt_in_count ?? insights?.marketing_opt_in_users?.length ?? 0})
          </button>
          <button type="button" className="admin-dash-btn" disabled={refreshing} onClick={() => fetchData(true)}>
            {refreshing ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>
      </header>

      {error && <div className="admin-dash-error">{error}</div>}

      {insights?.headlines?.length > 0 && (
        <div className="admin-dash-headlines">
          <h2>What you need to know</h2>
          <ul>
            {insights.headlines.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>
      )}

      {summary && (
        <div className="admin-dash-stats admin-dash-stats-compact">
          <StatCard value={summary.total_users} label="Signups" />
          <StatCard value={`${summary.active_30d_pct}%`} label="Active 30d" sub={`${summary.active_last_30_days} users`} />
          <StatCard value={`${summary.ai_users_pct}%`} label="Used AI" sub={`${summary.total_ai_analyses} analyses`} />
          <StatCard value={summary.alert_delivery_users} label="Alert delivery" sub="Telegram linked" />
          <StatCard value={`${summary.onboarding_completion_rate_pct}%`} label="Survey done" sub={`${summary.onboarding_completed} completed`} />
          <StatCard
            value={`${summary.never_activated_pct ?? 0}%`}
            label="Never activated"
            sub={`${summary.never_activated ?? 0} signed up only`}
          />
          <StatCard value={summary.subscription_premium} label="Premium" sub={`${summary.subscription_free} free`} />
        </div>
      )}

      <div className="admin-dash-tabs">
        <button type="button" className={tab === 'overview' ? 'active' : ''} onClick={() => setTab('overview')}>
          Overview
        </button>
        <button type="button" className={tab === 'all' ? 'active' : ''} onClick={() => setTab('all')}>
          All users ({visibleUserCount})
        </button>
      </div>

      {tab === 'overview' && insights && (
        <>
          <div className="admin-dash-grid-3">
            <div className="admin-dash-panel">
              <h2>Top AI users</h2>
              <p className="admin-dash-panel-desc">Who uses analysis most — your power users.</p>
              <MiniUserTable
                rows={insights.top_ai_users}
                emptyText="Nobody has run AI analysis yet."
                columns={[
                  emailCol,
                  { key: 'total_ai_analyses', label: 'Runs' },
                  {
                    key: 'last_ai_usage',
                    label: 'Last used',
                    render: (r) => formatDate(r.last_ai_usage),
                  },
                ]}
              />
            </div>

            <div className="admin-dash-panel">
              <h2>Alert delivery</h2>
              <p className="admin-dash-panel-desc">Who actually receives Telegram alerts.</p>
              <MiniUserTable
                rows={insights.alert_delivery}
                emptyText="No Telegram chat IDs linked yet."
                columns={[
                  emailCol,
                  { key: 'telegram_chat_id', label: 'Chat ID' },
                ]}
              />
            </div>

            <div className="admin-dash-panel">
              <h2>Recently active</h2>
              <p className="admin-dash-panel-desc">Last sign-in — who is still coming back.</p>
              <MiniUserTable
                rows={insights.recently_active}
                emptyText="No recent activity recorded."
                columns={[
                  emailCol,
                  {
                    key: 'days_since_active',
                    label: 'Last seen',
                    render: (r) => (r.days_since_active === 0 ? 'Today' : `${r.days_since_active}d ago`),
                  },
                ]}
              />
            </div>
          </div>

          <div className="admin-dash-grid-2">
            <div className="admin-dash-panel">
              <h2>Never activated</h2>
              <p className="admin-dash-panel-desc">
                Signed up but never used AI, alerts, or completed onboarding — re-engagement targets.
              </p>
              <MiniUserTable
                rows={insights.never_activated}
                emptyText="Everyone has tried at least one core feature."
                columns={[
                  emailCol,
                  {
                    key: 'created_at',
                    label: 'Signed up',
                    render: (r) => formatDate(r.created_at),
                  },
                  {
                    key: 'onboarding_status',
                    label: 'Status',
                    render: (r) => <StatusTag status={r.onboarding_status} />,
                  },
                ]}
              />
            </div>

            <div className="admin-dash-panel">
              <h2>Marketing opt-in</h2>
              <p className="admin-dash-panel-desc">
                Completed onboarding and agreed to product emails — safe for campaigns.
              </p>
              <MiniUserTable
                rows={insights.marketing_opt_in_users?.slice(0, 20)}
                emptyText="No marketing opt-ins yet."
                columns={[
                  emailCol,
                  {
                    key: 'referral_source',
                    label: 'Referral',
                    render: (r) => labelReferral(r.referral_source),
                  },
                ]}
              />
              {(insights.marketing_opt_in_users?.length ?? 0) > 20 && (
                <p className="admin-dash-meta-note">
                  Showing 20 of {insights.marketing_opt_in_users.length} — use Export marketing list for the full CSV.
                </p>
              )}
            </div>
          </div>

          {onboarding && (
            <div className="admin-dash-panel admin-dash-onboarding">
              <h2>Onboarding survey — {onboarding.survey_responses} responses</h2>
              <p className="admin-dash-panel-desc">
                {onboarding.completion_rate_pct}% of all signups completed the survey.
                {onboarding.skipped > 0 && ` ${onboarding.skipped} skipped.`}
                {onboarding.marketing_opt_in > 0 && (
                  <> {onboarding.marketing_opt_in} ({onboarding.marketing_opt_in_pct}%) opted in to product emails.</>
                )}
              </p>
              <div className="admin-dash-grid-2">
                <div>
                  <h3>How they found you</h3>
                  <BreakdownList items={onboarding.referral_sources} labelFn={labelReferral} />
                </div>
                <div>
                  <h3>Experience level</h3>
                  <BreakdownList items={onboarding.experience_levels} labelFn={labelExperience} />
                </div>
                <div>
                  <h3>Primary goal</h3>
                  <BreakdownList items={onboarding.primary_goals} labelFn={labelGoal} />
                </div>
                <div>
                  <h3>Trading style</h3>
                  <BreakdownList items={onboarding.trading_styles} labelFn={labelTradingStyle} />
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {tab === 'all' && (
        <>
          <div className="admin-dash-filters">
            <input type="search" placeholder="Search email, name…" value={search} onChange={(e) => setSearch(e.target.value)} />
            <select value={filterOnboarding} onChange={(e) => setFilterOnboarding(e.target.value)}>
              <option value="all">All onboarding</option>
              <option value="completed">Completed</option>
              <option value="skipped">Skipped</option>
              <option value="pending">Pending</option>
            </select>
            <select value={filterActivity} onChange={(e) => setFilterActivity(e.target.value)}>
              <option value="all">All activity</option>
              <option value="active_7d">Active 7d</option>
              <option value="active_30d">Active 30d</option>
              <option value="ai_users">Used AI</option>
              <option value="telegram">Alert delivery</option>
              <option value="never_activated">Never activated</option>
            </select>
            <label className="admin-dash-filter-check">
              <input
                type="checkbox"
                checked={hideExcluded}
                onChange={(e) => setHideExcluded(e.target.checked)}
              />
              Hide internal/test accounts
            </label>
          </div>
          <p className="admin-dash-count-note">
            Showing {filteredUsers.length} of {visibleUserCount}
            {hideExcluded && (meta?.excluded_count ?? 0) > 0 && (
              <> ({meta.excluded_count} excluded from list)</>
            )}
          </p>
          <div className="admin-dash-table-wrap">
            <table className="admin-dash-table">
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Signed up</th>
                  <th>Last active</th>
                  <th>AI runs</th>
                  <th>Alerts</th>
                  <th>Onboarding</th>
                  <th>Referral</th>
                  <th>Experience</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((u) => (
                  <tr key={u.uid} className={u.is_excluded ? 'admin-dash-row-excluded' : u.never_activated ? 'admin-dash-row-never' : ''}>
                    <td className="admin-dash-email" title={u.email}>
                      {u.email || '—'}
                      {u.display_name && <span className="admin-dash-subline">{u.display_name}</span>}
                      {u.is_excluded && <span className="admin-dash-tag excluded">excluded</span>}
                      {u.never_activated && !u.is_excluded && <span className="admin-dash-tag never">never activated</span>}
                    </td>
                    <td>{formatDate(u.created_at)}</td>
                    <td>{u.days_since_active != null ? `${u.days_since_active}d ago` : '—'}</td>
                    <td>{u.total_ai_analyses || '—'}</td>
                    <td>{u.receives_alert_delivery ? '✓ Telegram' : '—'}</td>
                    <td><StatusTag status={u.onboarding_status} /></td>
                    <td>{labelReferral(u.referral_source)}</td>
                    <td>{labelExperience(u.experience_level)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
};

export default AdminUserDashboard;
