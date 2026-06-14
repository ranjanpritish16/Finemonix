// frontend/app/(dashboard)/watchlist/page.tsx

import Link from "next/link";
import AddCompanyForm from "@/components/watchlist/AddCompanyForm";
import { WATCHLIST_API } from "@/lib/constants/api";
import { SEVERITY_COLORS, SEVERITY_LABELS, DANGER_FLAG_LABELS, type Severity } from "@/lib/constants/severity";
import RunAnalysisButton from "@/components/watchlist/RunAnalysisButton";

const BUSINESS_ID = 1;

interface WatchlistEntry {
  id: number;
  company_bse_code: string;
  company_name: string;
}

interface AnomalyScore {
  quarter: string;
  score_financial: number;
  severity: Severity;
  contributing_features: {
    top_deviations: Record<string, number>;
    danger_flags: string[];
  };
}

interface CompanyWithRisk extends WatchlistEntry {
  latest_severity: Severity | null;
  latest_quarter: string | null;
  top_flag: string | null;
  all_flags: string[];
  score: number | null;
  quarters_analysed: number;
  severity_counts: Record<Severity, number>;
}

async function getWatchlist(): Promise<WatchlistEntry[]> {
  try {
    const res = await fetch(WATCHLIST_API.companies(BUSINESS_ID), { cache: "no-store" });
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : (data.companies ?? []);
  } catch { return []; }
}

async function getTimeline(bseCode: string): Promise<AnomalyScore[]> {
  try {
    const res = await fetch(WATCHLIST_API.timeline(bseCode), { cache: "no-store" });
    if (!res.ok) return [];
    const data = await res.json();
    return data.scores ?? [];
  } catch { return []; }
}

async function enrichCompanies(companies: WatchlistEntry[]): Promise<CompanyWithRisk[]> {
  return Promise.all(companies.map(async (c) => {
    const scores = await getTimeline(c.company_bse_code);
    if (scores.length === 0) {
      return { ...c, latest_severity: null, latest_quarter: null, top_flag: null, all_flags: [], score: null, quarters_analysed: 0, severity_counts: { low: 0, medium: 0, high: 0, critical: 0 } };
    }
    const latest = scores[scores.length - 1];
    const flags = latest.contributing_features?.danger_flags ?? [];
    const counts = { low: 0, medium: 0, high: 0, critical: 0 } as Record<Severity, number>;
    scores.forEach(s => { counts[s.severity] = (counts[s.severity] ?? 0) + 1; });
    return {
      ...c,
      latest_severity: latest.severity,
      latest_quarter: latest.quarter,
      top_flag: flags[0] ?? null,
      all_flags: flags,
      score: latest.score_financial,
      quarters_analysed: scores.length,
      severity_counts: counts,
    };
  }));
}

const SEVERITY_RANK: Record<Severity, number> = { critical: 0, high: 1, medium: 2, low: 3 };

function SeverityBar({ counts, total }: { counts: Record<Severity, number>; total: number }) {
  if (total === 0) return null;
  const sevs: Severity[] = ["critical", "high", "medium", "low"];
  return (
    <div style={{ display: "flex", height: "5px", borderRadius: "3px", overflow: "hidden", gap: "1px", marginTop: "8px" }}>
      {sevs.map(sev => {
        const pct = (counts[sev] / total) * 100;
        if (pct === 0) return null;
        return <div key={sev} style={{ width: `${pct}%`, background: SEVERITY_COLORS[sev].text, opacity: 0.75 }} />;
      })}
    </div>
  );
}

export default async function WatchlistPage() {
  const companies = await getWatchlist();
  const enriched = await enrichCompanies(companies);
  const sorted = [...enriched].sort((a, b) => {
    const ra = a.latest_severity ? SEVERITY_RANK[a.latest_severity] : 4;
    const rb = b.latest_severity ? SEVERITY_RANK[b.latest_severity] : 4;
    return ra - rb;
  });

  const analysed = enriched.filter(c => c.latest_severity);
  const counts = { critical: 0, high: 0, medium: 0, low: 0 } as Record<Severity, number>;
  analysed.forEach(c => { if (c.latest_severity) counts[c.latest_severity]++; });

  // Intelligence feed: collect recent flags from high/critical companies
  const feedItems: { company: string; flag: string; severity: Severity }[] = [];
  sorted.forEach(c => {
    if (c.latest_severity && (c.latest_severity === "critical" || c.latest_severity === "high")) {
      c.all_flags.slice(0, 2).forEach(f => {
        feedItems.push({ company: c.company_bse_code, flag: f, severity: c.latest_severity! });
      });
    }
  });

  return (
    <div style={{ padding: "32px", maxWidth: "100%", paddingRight: "32px" }}>
      {/* Header */}
      <div style={{ marginBottom: "20px" }}>
        <h1 style={{ fontSize: "22px", fontWeight: 700, color: "#0f172a", margin: 0 }}>Risk Monitor</h1>
        <p style={{ fontSize: "14px", color: "#64748b", marginTop: "4px" }}>
          Real-time anomaly surveillance across your MSME borrower portfolio.
        </p>
      </div>

      {/* Portfolio strip — light */}
      {companies.length > 0 && (
        <div style={{
          background: "linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)",
          border: "1px solid #bae6fd",
          borderRadius: "12px",
          padding: "20px 24px",
          marginBottom: "24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "16px",
        }}>
          <div>
            <p style={{ fontSize: "11px", color: "#0369a1", margin: 0, letterSpacing: "0.06em", textTransform: "uppercase", fontWeight: 600 }}>
              Portfolio Exposure
            </p>
            <p style={{ fontSize: "26px", fontWeight: 700, color: "#0c4a6e", margin: "4px 0 0" }}>
              {companies.length}{" "}
              <span style={{ fontSize: "14px", fontWeight: 400, color: "#0369a1" }}>companies monitored</span>
            </p>
          </div>
          <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
            {(["critical", "high", "medium", "low"] as Severity[]).map(sev => {
              const colors = SEVERITY_COLORS[sev];
              return (
                <div key={sev} style={{
                  textAlign: "center",
                  background: counts[sev] > 0 ? colors.bg : "#f8fafc",
                  border: `1px solid ${counts[sev] > 0 ? colors.border : "#e2e8f0"}`,
                  borderRadius: "8px",
                  padding: "10px 18px",
                  minWidth: "64px",
                }}>
                  <div style={{ fontSize: "22px", fontWeight: 700, color: counts[sev] > 0 ? colors.text : "#94a3b8" }}>
                    {counts[sev]}
                  </div>
                  <div style={{ fontSize: "11px", color: counts[sev] > 0 ? colors.text : "#94a3b8", marginTop: "2px", fontWeight: 500 }}>
                    {SEVERITY_LABELS[sev]}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Main layout: cards + right panel */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: "20px", alignItems: "start" }}>

        {/* LEFT: Add form + company cards */}
        <div>
          <AddCompanyForm />

          {sorted.length === 0 ? (
            <div style={{
              textAlign: "center", padding: "48px 24px",
              border: "1px dashed #e2e8f0", borderRadius: "8px",
              color: "#64748b", fontSize: "14px",
            }}>
              No companies on your watchlist yet. Add one above.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {sorted.map(c => {
                const sev = c.latest_severity;
                const colors = sev ? SEVERITY_COLORS[sev] : null;
                const isAlert = sev === "critical" || sev === "high";

                return (
                  <div key={c.id} style={{
                    background: "#ffffff",
                    border: "1px solid #e2e8f0",
                    borderLeft: `4px solid ${colors?.text ?? "#e2e8f0"}`,
                    borderRadius: "8px",
                    padding: "16px 20px",
                  }}>
                    <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "12px", flexWrap: "wrap" }}>
                      {/* Left: name + bar + flags */}
                      <div style={{ flex: "1 1 200px", minWidth: 0 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "2px" }}>
                          <span style={{ fontSize: "15px", fontWeight: 700, color: "#0f172a" }}>{c.company_name}</span>
                          <span style={{ fontSize: "11px", color: "#94a3b8", fontFamily: "monospace", background: "#f1f5f9", padding: "1px 6px", borderRadius: "4px" }}>
                            {c.company_bse_code}
                          </span>
                          {sev && colors && (
                            <span style={{
                              padding: "2px 10px", borderRadius: "9999px", fontSize: "11px", fontWeight: 700,
                              background: colors.bg, color: colors.text, border: `1px solid ${colors.border}`,
                            }}>
                              {isAlert ? "⚠ " : ""}{SEVERITY_LABELS[sev]}
                            </span>
                          )}
                        </div>

                        {c.quarters_analysed > 0 && (
                          <SeverityBar counts={c.severity_counts} total={c.quarters_analysed} />
                        )}

                        {/* Danger flags inline */}
                        {c.all_flags.length > 0 && (
                          <div style={{ display: "flex", flexWrap: "wrap", gap: "4px", marginTop: "8px" }}>
                            {c.all_flags.slice(0, 3).map(f => (
                              <span key={f} style={{
                                fontSize: "11px", color: "#b91c1c", background: "#fef2f2",
                                border: "1px solid #fecaca", borderRadius: "4px", padding: "2px 7px",
                              }}>
                                ⚠ {DANGER_FLAG_LABELS[f] ?? f}
                              </span>
                            ))}
                            {c.all_flags.length > 3 && (
                              <span style={{ fontSize: "11px", color: "#94a3b8", padding: "2px 4px" }}>
                                +{c.all_flags.length - 3} more
                              </span>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Right: stats + CTA */}
                      <div style={{ display: "flex", alignItems: "center", gap: "20px", flexShrink: 0 }}>
                        <div style={{ textAlign: "center" }}>
                          <p style={{ fontSize: "10px", color: "#94a3b8", margin: "0 0 2px", textTransform: "uppercase", letterSpacing: "0.05em" }}>Quarter</p>
                          <p style={{ fontSize: "13px", fontWeight: 600, color: "#0f172a", margin: 0, fontFamily: "monospace" }}>
                            {c.latest_quarter ?? "—"}
                          </p>
                        </div>
                        <div style={{ textAlign: "center" }}>
                          <p style={{ fontSize: "10px", color: "#94a3b8", margin: "0 0 2px", textTransform: "uppercase", letterSpacing: "0.05em" }}>Score</p>
                          <p style={{ fontSize: "13px", fontWeight: 600, color: "#0f172a", margin: 0, fontFamily: "monospace" }}>
                            {c.score !== null ? c.score.toFixed(3) : "—"}
                          </p>
                        </div>
                        <div style={{ textAlign: "center" }}>
                          <p style={{ fontSize: "10px", color: "#94a3b8", margin: "0 0 2px", textTransform: "uppercase", letterSpacing: "0.05em" }}>Qtrs</p>
                          <p style={{ fontSize: "13px", fontWeight: 600, color: "#0f172a", margin: 0 }}>
                            {c.quarters_analysed || "—"}
                          </p>
                        </div>

                        {/* Run analysis button */}
                        <div style={{ textAlign: "center" }}>
                          <RunAnalysisButton bseCode={c.company_bse_code} />
                        </div>

                        <Link href={`/company/${c.company_bse_code}`} style={{
                          padding: "7px 14px",
                          background: "#0f172a",
                          color: "#ffffff",
                          borderRadius: "6px",
                          fontSize: "12px",
                          fontWeight: 600,
                          textDecoration: "none",
                          whiteSpace: "nowrap",
                        }}>
                          View →
                        </Link>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* RIGHT PANEL */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>

          {/* Risk breakdown */}
          <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "16px 20px" }}>
            <p style={{ fontSize: "12px", fontWeight: 700, color: "#0f172a", margin: "0 0 12px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Risk Breakdown
            </p>
            {(["critical", "high", "medium", "low"] as Severity[]).map(sev => {
              const colors = SEVERITY_COLORS[sev];
              const total = analysed.length || 1;
              const pct = Math.round((counts[sev] / total) * 100);
              return (
                <div key={sev} style={{ marginBottom: "10px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "3px" }}>
                    <span style={{ fontSize: "12px", color: colors.text, fontWeight: 600 }}>{SEVERITY_LABELS[sev]}</span>
                    <span style={{ fontSize: "12px", color: "#64748b" }}>{counts[sev]} co.</span>
                  </div>
                  <div style={{ background: "#f1f5f9", borderRadius: "3px", height: "6px", overflow: "hidden" }}>
                    <div style={{ width: `${pct}%`, height: "100%", background: colors.text, opacity: 0.8, borderRadius: "3px", transition: "width 0.3s" }} />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Intelligence feed */}
          <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "16px 20px" }}>
            <p style={{ fontSize: "12px", fontWeight: 700, color: "#0f172a", margin: "0 0 12px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Intelligence Feed
            </p>
            {feedItems.length === 0 ? (
              <p style={{ fontSize: "13px", color: "#94a3b8", margin: 0 }}>No active alerts.</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {feedItems.slice(0, 6).map((item, i) => {
                  const colors = SEVERITY_COLORS[item.severity];
                  return (
                    <div key={i} style={{ borderLeft: `3px solid ${colors.text}`, paddingLeft: "10px" }}>
                      <p style={{ fontSize: "11px", fontWeight: 700, color: colors.text, margin: "0 0 2px" }}>
                        {item.company}
                      </p>
                      <p style={{ fontSize: "12px", color: "#374151", margin: 0 }}>
                        {DANGER_FLAG_LABELS[item.flag] ?? item.flag}
                      </p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Quick stats */}
          <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "16px 20px" }}>
            <p style={{ fontSize: "12px", fontWeight: 700, color: "#0f172a", margin: "0 0 12px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Portfolio Stats
            </p>
            {[
              { label: "Total Monitored", value: companies.length },
              { label: "Analysed", value: analysed.length },
              { label: "Pending Analysis", value: companies.length - analysed.length },
              { label: "Active Alerts", value: (counts.critical + counts.high) },
            ].map(({ label, value }) => (
              <div key={label} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid #f1f5f9" }}>
                <span style={{ fontSize: "12px", color: "#64748b" }}>{label}</span>
                <span style={{ fontSize: "13px", fontWeight: 700, color: "#0f172a" }}>{value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}