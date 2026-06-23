'use client';

import { useEffect, useState, useCallback } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL ?? '';
const BUSINESS_ID = 1;

// ─── Types ────────────────────────────────────────────────────────────────────

interface LenderScore {
  probability: number;
  probability_pct: number;
  verdict: 'approved' | 'rejected';
  display_name: string;
}

interface ShapAttribution {
  feature_name: string;
  display_name: string;
  value: number;
  shap_value: number;
  impact: 'positive' | 'negative';
}

interface ImprovementAction {
  feature: string;
  display_name: string;
  action: string;
  current_value: number;
  target_value: number;
  direction: string;
  projected_improvement_pct: number;
}

interface EligibilityResponse {
  lender_scores: Record<string, LenderScore>;
  shap_attributions: ShapAttribution[];
  top_actions: ImprovementAction[];
  best_lender: string;
  best_lender_display: string;
  best_probability_pct: number;
  extracted_features: Record<string, number>;
  data_quality: Record<string, unknown>;
}

interface PrefillResponse {
  features: Record<string, number>;
  data_freshness_days: number | null;
  missing_fields: string[];
  total_transactions: number;
  total_invoices: number;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function fmtInr(v: number) {
  if (v >= 1_00_00_000) return `₹${(v / 1_00_00_000).toFixed(1)}Cr`;
  if (v >= 1_00_000) return `₹${(v / 1_00_000).toFixed(1)}L`;
  if (v >= 1_000) return `₹${(v / 1_000).toFixed(0)}K`;
  return `₹${v.toFixed(0)}`;
}

function fmtFeature(key: string, val: number): string {
  if (key === 'monthly_revenue_inr' || key === 'outstanding_loans_inr') return fmtInr(val);
  if (key === 'cibil_score') return val.toFixed(0);
  if (key === 'client_concentration_pct' || key === 'gst_compliance_score') return `${val.toFixed(1)}%`;
  return val.toFixed(2);
}

const LENDER_META: Record<string, { icon: string; type: string; rate: string; amount: string; color: string }> = {
  psu:     { icon: '🏛', type: 'PSU Bank Term Loan',        rate: '8.5% – 11.5%', amount: '₹50L – ₹5Cr',  color: '#1d4ed8' },
  private: { icon: '🏦', type: 'Private Bank Credit Line', rate: '11% – 15%',    amount: '₹25L – ₹2Cr',  color: '#7c3aed' },
  nbfc:    { icon: '💼', type: 'NBFC Working Capital',      rate: '15% – 24%',    amount: '₹5L – ₹50L',   color: '#0891b2' },
  mfi:     { icon: '🤝', type: 'Microfinance (MFI)',         rate: '18% – 26%',    amount: '₹50K – ₹10L',  color: '#059669' },
};

const FEATURE_META: Record<string, { label: string; unit: string; min: number; max: number; step: number }> = {
  cibil_score:              { label: 'CIBIL Score',         unit: '',   min: 300, max: 900, step: 5 },
  debt_to_income_ratio:     { label: 'Debt-to-Income',      unit: 'x',  min: 0,   max: 3,   step: 0.05 },
  client_concentration_pct: { label: 'Client Concentration',unit: '%',  min: 0,   max: 100, step: 1 },
  revenue_stability:        { label: 'Revenue Stability CV', unit: '',  min: 0,   max: 2,   step: 0.05 },
  cash_flow_coverage:       { label: 'Cash Flow Coverage',  unit: 'x',  min: 0,   max: 5,   step: 0.1 },
  gst_compliance_score:     { label: 'GST Compliance',      unit: '%',  min: 0,   max: 100, step: 1 },
};

// ─── Donut Chart ─────────────────────────────────────────────────────────────

function ProbabilityDonut({ pct, color }: { pct: number; color: string }) {
  const r = 56;
  const circ = 2 * Math.PI * r;
  const dash = circ * (pct / 100);
  const grade = pct >= 75 ? 'HIGH' : pct >= 50 ? 'MODERATE' : 'LOW';
  const gradeColor = pct >= 75 ? '#16a34a' : pct >= 50 ? '#d97706' : '#dc2626';

  return (
    <div style={{ position: 'relative', width: 144, height: 144 }}>
      <svg width="144" height="144" viewBox="0 0 144 144">
        <circle cx="72" cy="72" r={r} fill="none" stroke="rgba(0,0,0,0.06)" strokeWidth="10" />
        <circle
          cx="72" cy="72" r={r}
          fill="none" stroke={color} strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circ}`}
          strokeDashoffset={circ * 0.25}
          style={{ transition: 'stroke-dasharray 0.8s ease' }}
        />
      </svg>
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{ fontSize: 26, fontWeight: 800, color: '#0f172a' }}>{pct.toFixed(0)}%</span>
        <span style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.08em', color: gradeColor }}>{grade} RELIABILITY</span>
      </div>
    </div>
  );
}

// ─── Bar for SHAP ─────────────────────────────────────────────────────────────

function ShapBar({ attribution }: { attribution: ShapAttribution }) {
  const pct = Math.min(100, Math.abs(attribution.shap_value) * 400);
  const positive = attribution.impact === 'positive';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0', borderBottom: '0.5px solid #f1f5f9' }}>
      <div style={{ width: 120, fontSize: 11, color: '#64748b', flexShrink: 0 }}>{attribution.display_name}</div>
      <div style={{ flex: 1, height: 6, background: '#f1f5f9', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{
          height: '100%',
          width: `${pct}%`,
          background: positive ? '#16a34a' : '#dc2626',
          borderRadius: 3,
          transition: 'width 0.6s ease',
        }} />
      </div>
      <div style={{ width: 60, fontSize: 11, textAlign: 'right', fontWeight: 700, color: positive ? '#16a34a' : '#dc2626' }}>
        {positive ? '+' : ''}{(attribution.shap_value * 100).toFixed(1)}pp
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function LoanAnalyzerPage() {
  const [result, setResult]           = useState<EligibilityResponse | null>(null);
  const [prefill, setPrefill]         = useState<PrefillResponse | null>(null);
  const [loading, setLoading]         = useState(true);
  const [analyzing, setAnalyzing]     = useState(false);
  const [error, setError]             = useState<string | null>(null);
  const [whatifDeltas, setWhatifDeltas] = useState<Record<string, number>>({});
  const [sliderValues, setSliderValues] = useState<Record<string, number>>({});
  const [activeTab, setActiveTab]     = useState<'overview' | 'factors' | 'actions' | 'whatif'>('overview');

  // Load prefill on mount
  useEffect(() => {
    async function loadPrefill() {
      try {
        const res = await fetch(`${API}/api/loan/prefill/${BUSINESS_ID}`);
        if (res.ok) {
          const data: PrefillResponse = await res.json();
          setPrefill(data);
          // Init sliders from prefill values
          const sliders: Record<string, number> = {};
          for (const key of Object.keys(FEATURE_META)) {
            if (data.features[key] !== undefined) sliders[key] = data.features[key];
          }
          setSliderValues(sliders);
        }
      } catch { /* ignore */ }
    }
    loadPrefill();
  }, []);

  const runAnalysis = useCallback(async () => {
    setAnalyzing(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/loan/eligibility`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ business_id: BUSINESS_ID }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || `API error ${res.status}`);
      }
      const data: EligibilityResponse = await res.json();
      setResult(data);
      setWhatifDeltas({});
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Analysis failed.');
    } finally {
      setAnalyzing(false);
      setLoading(false);
    }
  }, []);

  useEffect(() => { runAnalysis(); }, [runAnalysis]);

  const handleSlider = useCallback(async (feature: string, value: number) => {
    setSliderValues(prev => ({ ...prev, [feature]: value }));
    if (!result) return;
    try {
      const res = await fetch(`${API}/api/loan/whatif`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ business_id: BUSINESS_ID, changed_feature: feature, new_value: value }),
      });
      if (res.ok) {
        const data = await res.json();
        setWhatifDeltas(data.delta || {});
      }
    } catch { /* ignore */ }
  }, [result]);

  const bestScore = result ? result.lender_scores[result.best_lender] : null;
  const bestColor = bestScore
    ? bestScore.probability_pct >= 75 ? '#16a34a' : bestScore.probability_pct >= 50 ? '#d97706' : '#dc2626'
    : '#2563eb';

  // ── Render States ─────────────────────────────────────────────────────────
  if (loading || analyzing) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', gap: 16 }}>
        <div style={{
          width: 48, height: 48, borderRadius: '50%',
          border: '3px solid #e2e8f0', borderTopColor: '#2563eb',
          animation: 'spin 0.9s linear infinite',
        }} />
        <p style={{ color: '#64748b', fontSize: 14 }}>Running AI credit analysis across 4 lender models...</p>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <div style={{ background: '#fef2f2', border: '0.5px solid #fecaca', borderRadius: 14, padding: 24, maxWidth: 520 }}>
          <p style={{ fontWeight: 700, color: '#dc2626', marginBottom: 6 }}>⚠ Credit Analysis Failed</p>
          <p style={{ color: '#64748b', fontSize: 13, marginBottom: 16 }}>{error}</p>
          <button
            onClick={() => { setLoading(true); runAnalysis(); }}
            style={{ padding: '9px 20px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, cursor: 'pointer', fontSize: 13 }}
          >
            Retry Analysis
          </button>
        </div>
      </div>
    );
  }

  if (!result) return null;

  const tabs: { id: typeof activeTab; label: string }[] = [
    { id: 'overview', label: '📊 Overview' },
    { id: 'factors',  label: '🔬 SHAP Factors' },
    { id: 'actions',  label: '⚡ Actions' },
    { id: 'whatif',   label: '🎛 What-If Simulator' },
  ];

  return (
    <div style={{ padding: '20px 24px', fontFamily: 'system-ui, sans-serif', maxWidth: 1100 }}>

      {/* ── Header ── */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: '#0f172a', margin: 0 }}>Loan Eligibility Analyzer</h1>
          <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', background: '#eff6ff', color: '#2563eb', padding: '3px 8px', borderRadius: 20 }}>
            ✦ AI ENGINE ACTIVE
          </span>
        </div>
        <p style={{ fontSize: 13, color: '#64748b', margin: 0 }}>
          Real-time creditworthiness projection based on AI modelling · {prefill?.total_transactions ?? 0} transactions analysed
        </p>
      </div>

      {/* ── Tabs ── */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20, background: '#f8fafc', padding: 4, borderRadius: 10, width: 'fit-content' }}>
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            style={{
              padding: '7px 14px', fontSize: 12, fontWeight: 600, border: 'none', borderRadius: 7, cursor: 'pointer',
              background: activeTab === t.id ? '#fff' : 'transparent',
              color: activeTab === t.id ? '#0f172a' : '#64748b',
              boxShadow: activeTab === t.id ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
              transition: 'all 0.15s',
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ══ OVERVIEW TAB ══ */}
      {activeTab === 'overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: 16 }}>

          {/* Credit Probability Card */}
          <div style={{ background: '#fff', border: '0.5px solid #e2e8f0', borderRadius: 16, padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
              <div>
                <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.1em', color: '#94a3b8', marginBottom: 4 }}>CREDIT PROBABILITY</p>
                <p style={{ fontSize: 13, color: '#64748b' }}>Best lender: <strong style={{ color: '#0f172a' }}>{result.best_lender_display}</strong></p>
              </div>
              <span style={{ fontSize: 10, color: '#94a3b8' }}>UPDATED JUST NOW</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 20 }}>
              <ProbabilityDonut pct={result.best_probability_pct} color={bestColor} />
            </div>
            <p style={{ fontSize: 12, color: '#64748b', textAlign: 'center', lineHeight: 1.6 }}>
              {result.best_probability_pct >= 75
                ? 'Your business shows strong revenue resilience. You are currently in the Top 12% of applicants in your sector.'
                : result.best_probability_pct >= 50
                ? 'Your business shows moderate creditworthiness. Improve key factors to unlock better loan terms.'
                : 'Your business needs improvement in critical credit factors before applying.'}
            </p>
            <button
              onClick={() => { setLoading(true); runAnalysis(); }}
              style={{
                width: '100%', marginTop: 16, padding: '9px', background: '#2563eb', color: '#fff',
                border: 'none', borderRadius: 8, fontWeight: 700, cursor: 'pointer', fontSize: 13,
                transition: 'opacity 0.15s',
              }}
            >
              Refresh Analysis
            </button>
          </div>

          {/* Right Column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* Lender Scores Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              {Object.entries(result.lender_scores).map(([key, score]) => {
                const meta = LENDER_META[key];
                const approved = score.verdict === 'approved';
                return (
                  <div key={key} style={{
                    background: '#fff', border: `0.5px solid ${approved ? '#bbf7d0' : '#e2e8f0'}`,
                    borderRadius: 12, padding: 16,
                    borderLeft: `3px solid ${approved ? '#16a34a' : '#e2e8f0'}`,
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                      <div>
                        <span style={{ fontSize: 18 }}>{meta.icon}</span>
                        <p style={{ fontSize: 12, fontWeight: 700, color: '#0f172a', marginTop: 4 }}>{score.display_name}</p>
                        <p style={{ fontSize: 10, color: '#94a3b8' }}>{meta.type}</p>
                      </div>
                      <span style={{
                        fontSize: 10, fontWeight: 700, padding: '3px 8px', borderRadius: 20,
                        background: approved ? '#dcfce7' : '#f1f5f9',
                        color: approved ? '#16a34a' : '#94a3b8',
                      }}>
                        {approved ? '✓ APPROVED' : '✗ DECLINED'}
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ flex: 1, height: 4, background: '#f1f5f9', borderRadius: 2, overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${score.probability_pct}%`, background: meta.color, borderRadius: 2, transition: 'width 0.8s' }} />
                      </div>
                      <span style={{ fontSize: 13, fontWeight: 800, color: meta.color }}>{score.probability_pct.toFixed(0)}%</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
                      <span style={{ fontSize: 10, color: '#64748b' }}>Rate: <strong>{meta.rate}</strong></span>
                      <span style={{ fontSize: 10, color: '#64748b' }}>{meta.amount}</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Top 3 SHAP Factors */}
            <div style={{ background: '#fff', border: '0.5px solid #e2e8f0', borderRadius: 14, padding: 18 }}>
              <p style={{ fontSize: 12, fontWeight: 700, color: '#0f172a', marginBottom: 14 }}>Top Influence Factors</p>
              {result.shap_attributions.slice(0, 3).map(attr => (
                <div key={attr.feature_name} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '10px 12px', borderRadius: 10, marginBottom: 8,
                  background: attr.impact === 'positive' ? '#f0fdf4' : '#fef2f2',
                  border: `0.5px solid ${attr.impact === 'positive' ? '#bbf7d0' : '#fecaca'}`,
                }}>
                  <div>
                    <p style={{ fontSize: 12, fontWeight: 700, color: '#0f172a', marginBottom: 2 }}>{attr.display_name}</p>
                    <p style={{ fontSize: 10, color: '#64748b' }}>Value: {fmtFeature(attr.feature_name, attr.value)}</p>
                  </div>
                  <span style={{
                    fontSize: 10, fontWeight: 700, padding: '3px 8px', borderRadius: 20,
                    background: attr.impact === 'positive' ? '#dcfce7' : '#fee2e2',
                    color: attr.impact === 'positive' ? '#16a34a' : '#dc2626',
                  }}>
                    {attr.impact === 'positive' ? 'PASS' : 'NEEDS IMPROVEMENT'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ══ SHAP FACTORS TAB ══ */}
      {activeTab === 'factors' && (
        <div style={{ background: '#fff', border: '0.5px solid #e2e8f0', borderRadius: 16, padding: 24 }}>
          <div style={{ marginBottom: 20 }}>
            <p style={{ fontSize: 15, fontWeight: 700, color: '#0f172a', marginBottom: 4 }}>SHAP Feature Attribution</p>
            <p style={{ fontSize: 12, color: '#64748b' }}>
              Each bar shows how much a feature pushed your approval probability up (+) or down (–) for the best lender ({result.best_lender_display}).
            </p>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 40px' }}>
            <div>
              <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', color: '#16a34a', marginBottom: 8 }}>POSITIVE CONTRIBUTORS</p>
              {result.shap_attributions.filter(a => a.impact === 'positive').map(attr => (
                <ShapBar key={attr.feature_name} attribution={attr} />
              ))}
            </div>
            <div>
              <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', color: '#dc2626', marginBottom: 8 }}>NEGATIVE CONTRIBUTORS</p>
              {result.shap_attributions.filter(a => a.impact === 'negative').map(attr => (
                <ShapBar key={attr.feature_name} attribution={attr} />
              ))}
            </div>
          </div>
          <div style={{ marginTop: 24, borderTop: '0.5px solid #f1f5f9', paddingTop: 16 }}>
            <p style={{ fontSize: 11, fontWeight: 700, color: '#0f172a', marginBottom: 10 }}>Extracted Financial Features</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
              {Object.entries(result.extracted_features).map(([key, val]) => (
                <div key={key} style={{ background: '#f8fafc', borderRadius: 8, padding: '10px 12px' }}>
                  <p style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.07em', color: '#94a3b8', marginBottom: 3 }}>
                    {key.replace(/_/g, ' ').toUpperCase()}
                  </p>
                  <p style={{ fontSize: 14, fontWeight: 700, color: '#0f172a' }}>{fmtFeature(key, val)}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ══ ACTIONS TAB ══ */}
      {activeTab === 'actions' && (
        <div>
          <div style={{ background: '#fff', border: '0.5px solid #e2e8f0', borderRadius: 16, padding: 24, marginBottom: 16 }}>
            <p style={{ fontSize: 15, fontWeight: 700, color: '#0f172a', marginBottom: 4 }}>Top Improvement Actions</p>
            <p style={{ fontSize: 12, color: '#64748b', marginBottom: 20 }}>
              These specific changes will have the highest impact on your loan approval probability.
            </p>
            {result.top_actions.length === 0 ? (
              <div style={{ background: '#f0fdf4', border: '0.5px solid #bbf7d0', borderRadius: 12, padding: 20, textAlign: 'center' }}>
                <p style={{ fontSize: 24, marginBottom: 8 }}>🎉</p>
                <p style={{ fontWeight: 700, color: '#16a34a' }}>Excellent Profile!</p>
                <p style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>No critical improvement actions needed. Your financial profile is strong across all factors.</p>
              </div>
            ) : (
              result.top_actions.map((action, i) => (
                <div key={action.feature} style={{
                  display: 'flex', gap: 16, padding: '16px 20px', borderRadius: 12, marginBottom: 12,
                  background: i === 0 ? '#fefce8' : '#fff',
                  border: `0.5px solid ${i === 0 ? '#fde68a' : '#e2e8f0'}`,
                }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
                    background: i === 0 ? '#fbbf24' : '#e2e8f0',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 14, fontWeight: 800, color: '#fff',
                  }}>{i + 1}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
                      <p style={{ fontSize: 13, fontWeight: 700, color: '#0f172a' }}>{action.display_name}</p>
                      {action.projected_improvement_pct > 0 && (
                        <span style={{ fontSize: 11, fontWeight: 700, background: '#dcfce7', color: '#16a34a', padding: '2px 8px', borderRadius: 20 }}>
                          +{action.projected_improvement_pct.toFixed(1)}pp boost
                        </span>
                      )}
                    </div>
                    <p style={{ fontSize: 12, color: '#64748b', lineHeight: 1.6, marginBottom: 10 }}>{action.action}</p>
                    <div style={{ display: 'flex', gap: 16 }}>
                      <div style={{ background: '#f8fafc', borderRadius: 6, padding: '5px 10px' }}>
                        <p style={{ fontSize: 9, color: '#94a3b8', fontWeight: 700 }}>CURRENT</p>
                        <p style={{ fontSize: 12, fontWeight: 700, color: '#dc2626' }}>{fmtFeature(action.feature, action.current_value)}</p>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', color: '#94a3b8' }}>→</div>
                      <div style={{ background: '#f0fdf4', borderRadius: 6, padding: '5px 10px' }}>
                        <p style={{ fontSize: 9, color: '#94a3b8', fontWeight: 700 }}>TARGET</p>
                        <p style={{ fontSize: 12, fontWeight: 700, color: '#16a34a' }}>{fmtFeature(action.feature, action.target_value)}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* ══ WHAT-IF SIMULATOR TAB ══ */}
      {activeTab === 'whatif' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16 }}>
          <div style={{ background: '#fff', border: '0.5px solid #e2e8f0', borderRadius: 16, padding: 24 }}>
            <p style={{ fontSize: 15, fontWeight: 700, color: '#0f172a', marginBottom: 4 }}>What-If Scenario Simulator</p>
            <p style={{ fontSize: 12, color: '#64748b', marginBottom: 20 }}>
              Drag the sliders to see how improving each factor would change your approval probability in real time.
            </p>
            {Object.entries(FEATURE_META).map(([key, meta]) => {
              const val = sliderValues[key] ?? result.extracted_features[key] ?? meta.min;
              return (
                <div key={key} style={{ marginBottom: 20 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <span style={{ fontSize: 12, fontWeight: 600, color: '#0f172a' }}>{meta.label}</span>
                    <span style={{ fontSize: 12, fontWeight: 700, color: '#2563eb' }}>{val.toFixed(meta.step < 1 ? 2 : 0)}{meta.unit}</span>
                  </div>
                  <input
                    type="range"
                    min={meta.min} max={meta.max} step={meta.step}
                    value={val}
                    onChange={e => handleSlider(key, parseFloat(e.target.value))}
                    style={{ width: '100%', accentColor: '#2563eb' }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9, color: '#94a3b8', marginTop: 2 }}>
                    <span>{meta.min}{meta.unit}</span>
                    <span>{meta.max}{meta.unit}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Live Impact Panel */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ background: '#fff', border: '0.5px solid #e2e8f0', borderRadius: 14, padding: 20 }}>
              <p style={{ fontSize: 12, fontWeight: 700, color: '#0f172a', marginBottom: 14 }}>Live Probability Impact</p>
              {Object.entries(result.lender_scores).map(([key, score]) => {
                const delta = whatifDeltas[key] ?? 0;
                const newPct = Math.min(100, Math.max(0, score.probability_pct + delta));
                const meta = LENDER_META[key];
                return (
                  <div key={key} style={{ marginBottom: 14 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 11, color: '#64748b' }}>{score.display_name}</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ fontSize: 12, fontWeight: 700, color: '#0f172a' }}>{newPct.toFixed(1)}%</span>
                        {delta !== 0 && (
                          <span style={{ fontSize: 10, fontWeight: 700, color: delta > 0 ? '#16a34a' : '#dc2626' }}>
                            {delta > 0 ? '+' : ''}{delta.toFixed(1)}pp
                          </span>
                        )}
                      </div>
                    </div>
                    <div style={{ height: 5, background: '#f1f5f9', borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${newPct}%`, background: meta.color, borderRadius: 3, transition: 'width 0.3s' }} />
                    </div>
                  </div>
                );
              })}
            </div>

            <div style={{ background: '#1e1b4b', borderRadius: 14, padding: 20 }}>
              <p style={{ fontSize: 11, fontWeight: 700, color: '#a5b4fc', letterSpacing: '0.08em', marginBottom: 12 }}>BEST CASE SCENARIO</p>
              <p style={{ fontSize: 28, fontWeight: 800, color: '#fff', marginBottom: 4 }}>
                {(result.best_probability_pct + (whatifDeltas[result.best_lender] ?? 0)).toFixed(0)}%
              </p>
              <p style={{ fontSize: 12, color: '#a5b4fc' }}>{result.best_lender_display}</p>
              {(whatifDeltas[result.best_lender] ?? 0) !== 0 && (
                <div style={{ marginTop: 12, background: 'rgba(255,255,255,0.1)', borderRadius: 8, padding: '8px 12px' }}>
                  <p style={{ fontSize: 11, color: '#a5b4fc' }}>
                    With your changes: <strong style={{ color: '#fff' }}>
                      {(whatifDeltas[result.best_lender] ?? 0) > 0 ? '+' : ''}
                      {(whatifDeltas[result.best_lender] ?? 0).toFixed(1)}pp
                    </strong>
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
