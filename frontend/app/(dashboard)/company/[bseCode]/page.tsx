// frontend/app/(dashboard)/company/[bseCode]/page.tsx
"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  Cell, PieChart, Pie, Legend,
} from "recharts";
import { WATCHLIST_API } from "@/lib/constants/api";
import {
  SEVERITY_COLORS, SEVERITY_LABELS, DANGER_FLAG_LABELS, type Severity,
} from "@/lib/constants/severity";

interface AnomalyScore {
  quarter: string;
  score_financial: number;
  severity: Severity;
  contributing_features: {
    top_deviations: Record<string, number>;
    danger_flags: string[];
  };
}

interface TimelineResponse {
  company_bse_code: string;
  scores: AnomalyScore[];
}

export default function CompanyPage() {
  const { bseCode } = useParams<{ bseCode: string }>();
  const [data, setData] = useState<TimelineResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(WATCHLIST_API.timeline(bseCode), { cache: "no-store" })
      .then(r => r.ok ? r.json() : null)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [bseCode]);

  if (loading) return (
    <div style={{ padding: "48px 32px", color: "#64748b", fontSize: "14px" }}>Loading…</div>
  );

  const scores = data?.scores ?? [];

  // Pie data
  const sevCounts = { low: 0, medium: 0, high: 0, critical: 0 } as Record<Severity, number>;
  scores.forEach(s => { sevCounts[s.severity]++; });
  const pieData = (["critical", "high", "medium", "low"] as Severity[])
    .filter(s => sevCounts[s] > 0)
    .map(s => ({ name: SEVERITY_LABELS[s], value: sevCounts[s], color: SEVERITY_COLORS[s].text }));

  return (
    <div style={{ padding: "32px", maxWidth: "100%", paddingRight: "32px" }}>
      {/* Header */}
      <div style={{ marginBottom: "28px" }}>
        <Link href="/watchlist" style={{ fontSize: "13px", color: "#64748b", textDecoration: "none" }}>
          ← Risk Monitor
        </Link>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", margin: "8px 0 4px" }}>
          <h1 style={{ fontSize: "22px", fontWeight: 700, color: "#0f172a", margin: 0 }}>{bseCode}</h1>
          {scores.length > 0 && (() => {
            const latest = scores[scores.length - 1];
            const colors = SEVERITY_COLORS[latest.severity];
            return (
              <span style={{
                padding: "4px 12px", borderRadius: "9999px", fontSize: "12px", fontWeight: 700,
                background: colors.bg, color: colors.text, border: `1px solid ${colors.border}`,
              }}>
                {SEVERITY_LABELS[latest.severity]} Risk
              </span>
            );
          })()}
        </div>
        <p style={{ fontSize: "14px", color: "#64748b", margin: 0 }}>
          Anomaly detection · IsolationForest · z-score severity
        </p>
      </div>

      {scores.length === 0 ? (
        <div style={{
          padding: "48px 24px", border: "1px dashed #e2e8f0", borderRadius: "8px",
          textAlign: "center", color: "#64748b", fontSize: "14px",
        }}>
          No anomaly scores found for <strong>{bseCode}</strong>.<br />
          <span style={{ fontSize: "13px" }}>Run <code style={{ background: "#f1f5f9", padding: "1px 6px", borderRadius: "4px" }}>
            POST /api/watchlist/anomaly/run
          </code> with <code style={{ background: "#f1f5f9", padding: "1px 6px", borderRadius: "4px" }}>
              {`{"company_bse_code":"${bseCode}","use_demo_data":true}`}
            </code> first.</span>
        </div>
      ) : (
        <>
          {/* Summary cards */}
          <div style={{ display: "flex", gap: "12px", marginBottom: "24px", flexWrap: "wrap" }}>
            {(["low", "medium", "high", "critical"] as Severity[]).map(sev => {
              const colors = SEVERITY_COLORS[sev];
              return (
                <div key={sev} style={{
                  padding: "12px 20px", borderRadius: "8px", minWidth: "80px", textAlign: "center",
                  background: colors.bg, border: `1px solid ${colors.border}`,
                }}>
                  <div style={{ fontSize: "22px", fontWeight: 700, color: colors.text }}>{sevCounts[sev]}</div>
                  <div style={{ fontSize: "12px", color: colors.text, fontWeight: 500 }}>{SEVERITY_LABELS[sev]}</div>
                </div>
              );
            })}
            <div style={{
              padding: "12px 20px", borderRadius: "8px", minWidth: "80px", textAlign: "center",
              background: "#f8fafc", border: "1px solid #e2e8f0",
            }}>
              <div style={{ fontSize: "22px", fontWeight: 700, color: "#0f172a" }}>{scores.length}</div>
              <div style={{ fontSize: "12px", color: "#64748b", fontWeight: 500 }}>Quarters</div>
            </div>
          </div>

          {/* Charts row */}
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "16px", marginBottom: "24px" }}>

            {/* Bar chart — anomaly score over time */}
            <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "20px" }}>
              <p style={{ fontSize: "13px", fontWeight: 600, color: "#0f172a", margin: "0 0 16px" }}>
                Anomaly Score by Quarter
              </p>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={scores} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                  <XAxis
                    dataKey="quarter"
                    tick={{ fontSize: 10, fill: "#94a3b8" }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: "#94a3b8" }}
                    tickLine={false}
                    axisLine={false}
                    domain={["auto", "auto"]}
                  />
                  <Tooltip
                    contentStyle={{ fontSize: "12px", border: "1px solid #e2e8f0", borderRadius: "6px" }}
                    formatter={(val: any) => [Number(val).toFixed(4), "Score"]}
                  />
                  <Bar dataKey="score_financial" radius={[3, 3, 0, 0]}>
                    {scores.map((s, i) => (
                      <Cell key={i} fill={SEVERITY_COLORS[s.severity].text} fillOpacity={0.85} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <p style={{ fontSize: "11px", color: "#94a3b8", margin: "8px 0 0", textAlign: "center" }}>
                Lower score = more anomalous · Color = severity
              </p>
            </div>

            {/* Pie chart — severity distribution */}
            <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "20px" }}>
              <p style={{ fontSize: "13px", fontWeight: 600, color: "#0f172a", margin: "0 0 8px" }}>
                Severity Distribution
              </p>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    dataKey="value"
                    paddingAngle={2}
                  >
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} fillOpacity={0.85} />
                    ))}
                  </Pie>
                  <Legend
                    iconType="circle"
                    iconSize={8}
                    wrapperStyle={{ fontSize: "11px", color: "#64748b" }}
                  />
                  <Tooltip
                    contentStyle={{ fontSize: "12px", border: "1px solid #e2e8f0", borderRadius: "6px" }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Timeline table */}
          <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "8px", overflow: "hidden" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: "#f8fafc", borderBottom: "1px solid #e2e8f0" }}>
                  {["Quarter", "Score", "Severity", "Top Deviations", "Danger Flags"].map(h => (
                    <th key={h} style={{
                      padding: "10px 16px", textAlign: "left", fontSize: "12px",
                      fontWeight: 600, color: "#64748b", letterSpacing: "0.04em",
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {scores.map((row, i) => {
                  const colors = SEVERITY_COLORS[row.severity];
                  const deviations = row.contributing_features?.top_deviations ?? {};
                  const flags = row.contributing_features?.danger_flags ?? [];
                  return (
                    <tr key={row.quarter} style={{
                      borderBottom: i < scores.length - 1 ? "1px solid #f1f5f9" : "none",
                      background: row.severity === "critical" ? "#fef2f2"
                        : row.severity === "high" ? "#fff7ed" : "#ffffff",
                    }}>
                      <td style={{ padding: "12px 16px", fontSize: "14px", fontWeight: 600, color: "#0f172a", fontFamily: "monospace" }}>
                        {row.quarter}
                      </td>
                      <td style={{ padding: "12px 16px", fontSize: "13px", color: "#64748b", fontFamily: "monospace" }}>
                        {row.score_financial.toFixed(4)}
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <span style={{
                          display: "inline-block", padding: "3px 10px", borderRadius: "9999px",
                          fontSize: "12px", fontWeight: 600,
                          background: colors.bg, color: colors.text, border: `1px solid ${colors.border}`,
                        }}>
                          {SEVERITY_LABELS[row.severity]}
                        </span>
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                          {Object.entries(deviations).map(([feat, val]) => (
                            <span key={feat} style={{ fontSize: "12px", color: "#64748b" }}>
                              <span style={{ color: "#0f172a", fontWeight: 500 }}>{feat}</span>
                              {" "}
                              <span style={{ color: (val as number) > 0 ? "#c2410c" : "#15803d" }}>
                                {(val as number) > 0 ? "+" : ""}{val}
                              </span>
                            </span>
                          ))}
                        </div>
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        {flags.length === 0 ? (
                          <span style={{ fontSize: "12px", color: "#94a3b8" }}>—</span>
                        ) : (
                          <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
                            {flags.map(f => (
                              <span key={f} style={{
                                fontSize: "11px", color: "#b91c1c", background: "#fef2f2",
                                border: "1px solid #fecaca", borderRadius: "4px",
                                padding: "2px 6px", display: "inline-block",
                              }}>
                                ⚠ {DANGER_FLAG_LABELS[f] ?? f}
                              </span>
                            ))}
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}