'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import './CashFlowDashboard.css';

// ─── Types ────────────────────────────────────────────────────────────────────

interface ForecastPoint {
  date: string;
  predicted_balance: number;
  p10: number;
  p90: number;
}

interface DangerZone {
  start_date: string;
  end_date: string;
  min_balance: number;
  severity: 'critical' | 'high' | 'medium';
}

interface ForecastResponse {
  forecast: ForecastPoint[];
  danger_zones: DangerZone[];
  model_used: string;
  accuracy_pct: number;
  days_of_data: number;
  warning: string | null;
}

interface Transaction {
  id: number;
  date: string;
  counterparty: string;
  direction: 'in' | 'out';
  amount: number;
  source: string;
  category: string;
}

interface DashboardData {
  cash_summary: {
    current_balance_inr: number;
    monthly_revenue_inr: number;
    monthly_expenses_inr: number;
    next_danger_zone_days: number | null;
    forecast_accuracy_pct: number;
  };
  recent_transactions: Transaction[];
}

interface TrainingStatus {
  status: 'idle' | 'starting' | 'training' | 'done' | 'failed';
  pct?: number;
  epoch?: number;
  total_epochs?: number;
  loss?: number;
  error?: string;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const BUSINESS_ID = 1;

// ─── Helpers ──────────────────────────────────────────────────────────────────

function fmt(n: number) {
  if (n >= 1_00_00_000) return `₹${(n / 1_00_00_000).toFixed(1)}Cr`;
  if (n >= 1_00_000) return `₹${(n / 1_00_000).toFixed(1)}L`;
  if (n >= 1_000) return `₹${(n / 1_000).toFixed(1)}K`;
  return `₹${Math.round(n).toLocaleString('en-IN')}`;
}

function fmtDate(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}

function daysUntil(dateStr: string) {
  const diff = Math.ceil((new Date(dateStr).getTime() - Date.now()) / 86400000);
  if (diff === 0) return 'Today';
  if (diff === 1) return 'Tomorrow';
  if (diff < 0) return `${Math.abs(diff)}d ago`;
  return `Due in ${diff}d`;
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function CashFlowPage() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<unknown>(null);
  const [horizon, setHorizon] = useState<30 | 90 | 180>(90);
  const [activeTab, setActiveTab] = useState<'Daily' | 'Weekly'>('Daily');
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [chartReady, setChartReady] = useState(false);
  const [scenarioResult, setScenarioResult] = useState<string | null>(null);
  const [runningScenario, setRunningScenario] = useState(false);
  const [trainingStatus, setTrainingStatus] = useState<TrainingStatus | null>(null);
  const [displayPct, setDisplayPct] = useState(0);

  // ── 1. Load Chart.js once ────────────────────────────────────────────────
  useEffect(() => {
    if ((window as unknown as Record<string, unknown>).Chart) { setChartReady(true); return; }
    const s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js';
    s.onload = () => setChartReady(true);
    document.head.appendChild(s);
  }, []);

  // ── 2. Fetch forecast + dashboard ───────────────────────────────────────
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [fcRes, dbRes] = await Promise.all([
        fetch(`${API}/api/forecast/${BUSINESS_ID}?horizon_days=${horizon}`, { cache: 'no-store' }),
        fetch(`${API}/api/dashboard/${BUSINESS_ID}`, { cache: 'no-store' }),
      ]);
      if (!fcRes.ok) throw new Error(`Forecast API error: ${fcRes.status}`);
      const fcData: ForecastResponse = await fcRes.json();
      setForecast(fcData);
      if (dbRes.ok) {
        const dbData: DashboardData = await dbRes.json();
        setDashboard(dbData);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load forecast data.');
    } finally {
      setLoading(false);
    }
  }, [horizon]);

  useEffect(() => { fetchData(); }, [fetchData]);

  // ── 2b. Poll training status (so we can show live retrain progress) ─────
  useEffect(() => {
    let cancelled = false;

    const poll = async () => {
      try {
        const res = await fetch(`${API}/api/forecast/${BUSINESS_ID}/status`, { cache: 'no-store' });
        if (!res.ok || cancelled) return;
        const data: TrainingStatus = await res.json();
        setTrainingStatus(prev => {
          // When a retrain finishes, refresh the forecast/dashboard automatically
          if (data.status === 'done' && prev?.status === 'training') {
            fetchData();
          }
          return data;
        });
      } catch {
        /* ignore — don't disrupt the page over a polling hiccup */
      }
    };

    poll();
    // Faster polling so we have a better chance of catching real intermediate progress
    const interval = setInterval(poll, 350);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [fetchData]);

  // ── 2c. Creep the displayed percentage so the ring never looks frozen ───
  const isRetraining =
    trainingStatus?.status === 'starting' || trainingStatus?.status === 'training';
  const trainingFailed = trainingStatus?.status === 'failed';
  useEffect(() => {
    if (!isRetraining) {
      if (trainingStatus?.status === 'done') {
        setDisplayPct(100);
        // Reset shortly after so the next retrain starts from 0
        const t = setTimeout(() => setDisplayPct(0), 800);
        return () => clearTimeout(t);
      }
      if (trainingStatus?.status === 'failed') {
        setDisplayPct(0);
        return;
      }
      setDisplayPct(0);
      return;
    }

    const realPct = trainingStatus?.pct ?? 0;

    // If the real value jumped ahead, snap forward immediately
    setDisplayPct(prev => (realPct > prev ? realPct : prev));

    // Creep forward slowly between real updates so it never looks stuck at 0
    const creep = setInterval(() => {
      setDisplayPct(prev => {
        const ceiling = Math.max(realPct + 15, 8); // always allow some movement even at pct=0
        return Math.min(prev + 1, ceiling, 95);
      });
    }, 150);

    return () => clearInterval(creep);
  }, [trainingStatus, isRetraining]);

  // ── 3. Build / update chart ──────────────────────────────────────────────
  useEffect(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const Chart = (window as any).Chart;
    if (!chartReady || !Chart || !canvasRef.current || !forecast) return;

    const step = activeTab === 'Weekly' ? 7 : 1;
    const data = forecast.forecast.filter((_, i) => i % step === 0);
    const labels = data.map(p => fmtDate(p.date));

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    if (chartRef.current) (chartRef.current as any).destroy();

    const ctx = canvasRef.current.getContext('2d')!;
    const gradient = ctx.createLinearGradient(0, 0, 0, 220);
    gradient.addColorStop(0, 'rgba(37, 99, 235, 0.18)');
    gradient.addColorStop(1, 'rgba(37, 99, 235, 0.00)');

    chartRef.current = new Chart(canvasRef.current, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'P90 (Optimistic)',
            data: data.map(p => p.p90),
            borderColor: 'transparent',
            backgroundColor: 'rgba(37,99,235,0.05)',
            fill: '+1',
            tension: 0.45,
            pointRadius: 0,
          },
          {
            label: 'Projected Balance',
            data: data.map(p => p.predicted_balance),
            borderColor: '#2563eb',
            borderWidth: 2.5,
            backgroundColor: gradient,
            fill: true,
            tension: 0.45,
            pointRadius: 0,
            pointHoverRadius: 6,
            pointHoverBackgroundColor: '#2563eb',
            pointHoverBorderColor: '#ffffff',
            pointHoverBorderWidth: 2,
          },
          {
            label: 'P10 (Pessimistic)',
            data: data.map(p => p.p10),
            borderColor: forecast.danger_zones.length ? '#dc2626' : 'rgba(148,163,184,0.4)',
            borderWidth: 1.5,
            borderDash: [4, 4],
            backgroundColor: 'transparent',
            fill: false,
            tension: 0.45,
            pointRadius: 0,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#ffffff',
            borderColor: '#e2e8f0',
            borderWidth: 1,
            titleColor: '#94a3b8',
            bodyColor: '#0f172a',
            padding: 12,
            callbacks: {
              label: (ctx: { dataset: { label: string }; parsed: { y: number } }) =>
                ` ${ctx.dataset.label}: ${fmt(ctx.parsed.y)}`,
            },
          },
        },
        scales: {
          x: {
            grid: { color: 'rgba(148,163,184,0.12)' },
            ticks: { color: '#94a3b8', font: { size: 11 }, maxTicksLimit: 8, maxRotation: 0 },
          },
          y: {
            grid: { color: 'rgba(148,163,184,0.12)' },
            ticks: { color: '#94a3b8', font: { size: 11 }, callback: (v: number) => fmt(v) },
            border: { display: false },
          },
        },
      },
    });
  }, [chartReady, activeTab, forecast]);

  // ── 4. Scenario planner (POST /api/forecast/scenario) ───────────────────
  const runScenario = async () => {
    setRunningScenario(true);
    setScenarioResult(null);
    try {
      const res = await fetch(`${API}/api/forecast/scenario`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_id: BUSINESS_ID,
          client_id: 1,
          delay_days: 10,
        }),
      });
      if (!res.ok) throw new Error('Scenario API failed');
      const data = await res.json();
      const summary = data.scenario_summary;
      setScenarioResult(summary.recommended_action);
    } catch {
      setScenarioResult('Could not run scenario. Check backend connection.');
    } finally {
      setRunningScenario(false);
    }
  };

  // ── Derived metrics ──────────────────────────────────────────────────────
  const currentBalance = dashboard?.cash_summary.current_balance_inr ?? 0;
  const monthlyExpenses = dashboard?.cash_summary.monthly_expenses_inr ?? 0;
  const forecastPts = forecast?.forecast ?? [];
  const firstBalance = forecastPts[0]?.predicted_balance ?? 0;
  const lastBalance = forecastPts[forecastPts.length - 1]?.predicted_balance ?? 0;
  const netChange = lastBalance - firstBalance;
  const runway = monthlyExpenses > 0 ? Math.round((currentBalance / monthlyExpenses) * 10) / 10 : 0;
  const burnRate = monthlyExpenses;
  const accuracyPct = forecast?.accuracy_pct ?? 0;
  const firstDanger = forecast?.danger_zones?.[0];

  // ── Inflows/Outflows from recent transactions ────────────────────────────
  const recentTx = dashboard?.recent_transactions ?? [];
  const inflows = recentTx.filter(t => t.direction === 'in').slice(0, 4);
  const outflows = recentTx.filter(t => t.direction === 'out').slice(0, 4);

  // ─────────────────────────────────────────────────────────────────────────
  if (loading || isRetraining) {
    const showEpochs = trainingStatus?.status === 'training';

    return (
      <div className="cf-root" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <div style={{ textAlign: 'center' }}>
          {isRetraining ? (
            <div style={{ width: 180, height: 180, margin: '0 auto', position: 'relative' }}>
              <svg width="180" height="180" viewBox="0 0 180 180">
                <circle cx="90" cy="90" r="78" fill="none" stroke="#e2e8f0" strokeWidth="10" />
                <circle
                  cx="90" cy="90" r="78" fill="none" stroke="#2563eb" strokeWidth="10"
                  strokeLinecap="round"
                  strokeDasharray={`${2 * Math.PI * 78 * (displayPct / 100)} ${2 * Math.PI * 78}`}
                  transform="rotate(-90 90 90)"
                  style={{ transition: 'stroke-dasharray 0.25s linear' }}
                />
              </svg>
              <div style={{
                position: 'absolute', inset: 0,
                display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              }}>
                <span style={{ fontSize: 30, fontWeight: 800, color: '#0f172a' }}>{Math.round(displayPct)}%</span>
                {showEpochs && trainingStatus?.epoch != null && (
                  <span style={{ fontSize: 11, color: '#64748b', marginTop: 4 }}>
                    Epoch {trainingStatus?.epoch}/{trainingStatus?.total_epochs}
                  </span>
                )}
              </div>
            </div>
          ) : (
            <div className="cf-spinner" />
          )}
          <p style={{ color: '#64748b', marginTop: 16, fontSize: 14, fontWeight: isRetraining ? 600 : 400 }}>
            {isRetraining
              ? 'Retraining LSTM on your latest data...'
              : 'Loading AI forecast...'}
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="cf-root">
        <div style={{ background: '#fef2f2', border: '0.5px solid #fecaca', borderRadius: 16, padding: 24 }}>
          <p style={{ fontWeight: 700, color: '#dc2626', marginBottom: 6 }}>⚠ Could not load forecast</p>
          <p style={{ color: '#64748b', fontSize: 13 }}>{error}</p>
          <button
            onClick={fetchData}
            style={{ marginTop: 14, padding: '8px 18px', background: '#dc2626', color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer', fontWeight: 700 }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="cf-root">

      {/* ── Data Scarcity Warning ── */}
      {forecast?.warning && (
        <div className="cf-warning-banner">
          <span>⚠</span>
          <span>{forecast.warning}</span>
        </div>
      )}
      {/* ── Retrain Failure Notice ── */}
      {trainingFailed && (
        <div className="cf-warning-banner" style={{ background: '#fef2f2', borderColor: '#fecaca', color: '#dc2626' }}>
          <span>⚠</span>
          <span>Model retraining failed{trainingStatus?.error ? `: ${trainingStatus.error}` : '.'} Showing last available forecast.</span>
        </div>
      )}

      {/* ── Header ── */}
      <div className="cf-header">
        <div className="cf-header-left">
          <h1>{horizon}-Day Cash Flow Forecast</h1>
          <p>
            AI-powered liquidity projection through{' '}
            <span>{fmtDate(forecastPts[forecastPts.length - 1]?.date ?? '')}</span>.
            {' '}Model: <span>{forecast?.model_used?.toUpperCase() ?? 'LSTM'}</span> · {forecast?.days_of_data ?? 0} days of history.
          </p>
        </div>

        <div className="cf-header-right">
          {/* Horizon selector */}
          <div className="cf-toggle-group">
            {([30, 90, 180] as const).map(h => (
              <button
                key={h}
                className={`cf-toggle-btn ${horizon === h ? 'active' : ''}`}
                onClick={() => setHorizon(h)}
              >
                {h}d
              </button>
            ))}
          </div>

          <div className="cf-badge">
            <span className="cf-badge-label">Current Balance</span>
            <span className="cf-badge-value">{fmt(currentBalance || 4210250)}</span>
          </div>
          <div className="cf-badge cf-badge-health">
            <span className="cf-badge-label">Forecast Health</span>
            <span className="cf-badge-value">
              {firstDanger ? `⚠ ${firstDanger.severity}` : '✦ Optimized'}
            </span>
          </div>
        </div>
      </div>

      {/* ── Body ── */}
      <div className="cf-body">

        {/* ══ LEFT ══ */}
        <div>

          {/* Chart */}
          <div className="cf-card cf-chart-card">
            <div className="cf-chart-header">
              <div>
                <p className="cf-chart-title">
                  Liquidity Projection
                  <span style={{ marginLeft: 10, display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                    <span className="cf-live-dot" />
                    <span style={{ fontSize: 11, color: '#16a34a', fontWeight: 600 }}>Live</span>
                  </span>
                </p>
                <p className="cf-chart-subtitle">
                  Projected closing balance — P10/P90 confidence bands via Monte Carlo Dropout
                </p>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                {firstDanger && (
                  <span className="cf-danger-tag">
                    ⚠ Risk: {fmtDate(firstDanger.start_date)}
                  </span>
                )}
                <div className="cf-toggle-group">
                  {(['Daily', 'Weekly'] as const).map(t => (
                    <button
                      key={t}
                      className={`cf-toggle-btn ${activeTab === t ? 'active' : ''}`}
                      onClick={() => setActiveTab(t)}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <div className="cf-chart-wrap">
              <canvas ref={canvasRef} />
            </div>
            {/* Legend */}
            <div style={{ display: 'flex', gap: 20, marginTop: 12 }}>
              {[
                { color: '#2563eb', label: 'Projected Balance', dash: false },
                { color: '#94a3b8', label: 'P90 Optimistic', dash: true },
                { color: firstDanger ? '#dc2626' : '#94a3b8', label: 'P10 Pessimistic', dash: true },
              ].map(l => (
                <div key={l.label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <div style={{ width: 24, height: 2, background: l.dash ? 'transparent' : l.color, borderTop: l.dash ? `2px dashed ${l.color}` : 'none' }} />
                  <span style={{ fontSize: 11, color: '#94a3b8' }}>{l.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Metrics */}
          <div className="cf-metrics-row">
            <div className="cf-metric-card teal">
              <div className="cf-metric-icon teal">🕐</div>
              <p className="cf-metric-label">Runway</p>
              <p className="cf-metric-value">{runway > 0 ? `${runway} Mo` : '—'}</p>
              <p className="cf-metric-sub">At current burn rate</p>
            </div>
            <div className="cf-metric-card green">
              <div className="cf-metric-icon green">📈</div>
              <p className="cf-metric-label">Net Cash Change</p>
              <p className={`cf-metric-value ${netChange >= 0 ? 'positive' : 'orange'}`}>
                {netChange >= 0 ? '+' : ''}{fmt(netChange)}
              </p>
              <p className="cf-metric-sub">Over {horizon} days</p>
            </div>
            <div className="cf-metric-card orange">
              <div className="cf-metric-icon orange">🔥</div>
              <p className="cf-metric-label">Burn Rate</p>
              <p className="cf-metric-value orange">{burnRate > 0 ? fmt(burnRate) : '—'} / mo</p>
              <p className="cf-metric-sub">Avg. monthly outflow</p>
            </div>
          </div>

          {/* Flows */}
          <div className="cf-flows-row">
            <div className="cf-card">
              <p className="cf-card-title">⬇ Critical Inflows</p>
              {inflows.length === 0 ? (
                <p style={{ fontSize: 13, color: '#94a3b8', padding: '8px 0' }}>No recent inflows found.</p>
              ) : inflows.map((t) => (
                <div className="cf-flow-item" key={t.id}>
                  <span className="cf-flow-dot green" />
                  <div style={{ flex: 1 }}>
                    <div className="cf-flow-name">{t.counterparty || t.category}</div>
                    <div className="cf-flow-date">{fmtDate(t.date)}</div>
                  </div>
                  <span className="cf-flow-amount green">{fmt(t.amount)}</span>
                </div>
              ))}
              <div className="cf-flows-link" onClick={() => window.location.href = '/integrations'}>
                View Detailed Ledgers →
              </div>
            </div>

            <div className="cf-card">
              <p className="cf-card-title">⬆ Planned Outflows</p>
              {outflows.length === 0 ? (
                <p style={{ fontSize: 13, color: '#94a3b8', padding: '8px 0' }}>No recent outflows found.</p>
              ) : outflows.map((t) => (
                <div className="cf-flow-item" key={t.id}>
                  <span className="cf-flow-dot red" />
                  <div style={{ flex: 1 }}>
                    <div className="cf-flow-name">{t.counterparty || t.category}</div>
                    <div className="cf-flow-date">{fmtDate(t.date)}</div>
                  </div>
                  <span className="cf-flow-amount red">{fmt(t.amount)}</span>
                </div>
              ))}
              <div className="cf-flows-link" onClick={() => window.location.href = '/integrations'}>
                View All Expenses →
              </div>
            </div>
          </div>
        </div>

        {/* ══ RIGHT ══ */}
        <div className="cf-right">

          {/* Scenario Simulator */}
          <div className="cf-card">
            <div className="cf-scenario-header">
              <p className="cf-card-title">🔮 Scenario Simulator</p>
            </div>
            <div className="cf-scenario-item">
              <div className="cf-scenario-top">
                <span className="cf-scenario-name">Delay Client Payment</span>
              </div>
              <p className="cf-scenario-desc">Postpone inflow from Client #1 by 10 days</p>
            </div>
            {scenarioResult && (
              <div style={{
                background: scenarioResult.startsWith('Critical') ? '#fef2f2' : '#f0fdf4',
                border: `0.5px solid ${scenarioResult.startsWith('Critical') ? '#fecaca' : '#bbf7d0'}`,
                borderRadius: 10,
                padding: '10px 14px',
                fontSize: 12.5,
                color: scenarioResult.startsWith('Critical') ? '#dc2626' : '#16a34a',
                marginBottom: 12,
                lineHeight: 1.5,
              }}>
                {scenarioResult}
              </div>
            )}
            <button
              className="cf-add-btn"
              onClick={runScenario}
              disabled={runningScenario}
              style={{ opacity: runningScenario ? 0.6 : 1 }}
            >
              {runningScenario ? '⏳ Simulating...' : '▶ Run Scenario'}
            </button>
          </div>

          {/* AI Risk Alert */}
          {firstDanger ? (
            <div className="cf-alert-card">
              <div className="cf-alert-top">
                <span className="cf-alert-chip">⚡ AI Risk Alert</span>
              </div>
              <p className="cf-alert-text">
                Cash balance at P10 level may drop below operating threshold starting{' '}
                <strong>{fmtDate(firstDanger.start_date)}</strong>.{' '}
                Minimum projected balance: <strong>{fmt(firstDanger.min_balance)}</strong>.{' '}
                Severity: <strong>{firstDanger.severity}</strong>.
              </p>
              <button
                className="cf-alert-cta"
                onClick={() => window.location.href = '/loan'}
              >
                Explore Financing →
              </button>
            </div>
          ) : (
            <div className="cf-card" style={{ background: '#f0fdf4', border: '0.5px solid #bbf7d0' }}>
              <div className="cf-alert-top">
                <span className="cf-alert-chip" style={{ background: '#dcfce7', color: '#16a34a' }}>
                  ✓ All Clear
                </span>
              </div>
              <p className="cf-alert-text" style={{ color: '#64748b' }}>
                No cash danger zones detected in the next {horizon} days. Your liquidity looks healthy!
              </p>
            </div>
          )}

          {/* Predictive Accuracy */}
          <div className="cf-card cf-accuracy-card">
            <div className="cf-accuracy-ring">
              <svg width="80" height="80" viewBox="0 0 80 80">
                <circle cx="40" cy="40" r="32" fill="none" stroke="rgba(0,0,0,0.06)" strokeWidth="6" />
                <circle
                  cx="40" cy="40" r="32"
                  fill="none"
                  stroke="url(#acc-grad)"
                  strokeWidth="6"
                  strokeLinecap="round"
                  strokeDasharray={`${2 * Math.PI * 32 * (accuracyPct / 100)} ${2 * Math.PI * 32 * (1 - accuracyPct / 100)}`}
                />
                <defs>
                  <linearGradient id="acc-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#16a34a" />
                    <stop offset="100%" stopColor="#2563eb" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="cf-accuracy-ring-inner">{Math.round(accuracyPct)}%</div>
            </div>
            <div className="cf-accuracy-text">
              <h3>Predictive Accuracy</h3>
              <p>{accuracyPct.toFixed(1)}% on last 30-day back-test via Monte Carlo Dropout · {forecast?.days_of_data ?? 0} days trained.</p>
            </div>
          </div>

          {/* Quick nav to other pages */}
          <div className="cf-card" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <p className="cf-card-title">🔗 Quick Actions</p>
            {[
              { label: '📊 Main Dashboard', href: '/dashboard' },
              { label: '🔌 Upload Data', href: '/integrations' },
              { label: '💰 Loan Analyzer', href: '/loan' },
              { label: '👁 Risk Monitor', href: '/watchlist' },
            ].map(({ label, href }) => (
              <button
                key={href}
                onClick={() => window.location.href = href}
                style={{
                  background: '#f8fafc',
                  border: '0.5px solid #e2e8f0',
                  borderRadius: 10,
                  padding: '10px 14px',
                  textAlign: 'left',
                  fontSize: 13,
                  fontWeight: 600,
                  color: '#0f172a',
                  cursor: 'pointer',
                  fontFamily: 'inherit',
                  transition: 'background 0.2s',
                }}
                onMouseEnter={e => (e.currentTarget.style.background = '#eff6ff')}
                onMouseLeave={e => (e.currentTarget.style.background = '#f8fafc')}
              >
                {label}
              </button>
            ))}
          </div>

        </div>
      </div>
    </div>
  );
}