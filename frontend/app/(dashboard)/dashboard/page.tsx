"use client";

import React, { useEffect, useRef, useState } from "react";
import { Chart, registerables } from "chart.js";

Chart.register(...registerables);

type DashboardData = {
  business: {
    name: string;
    quality_score: number;
    data_sources_connected: string[];
  };
  cash_summary: {
    current_balance_inr: number;
    monthly_revenue_inr: number;
    monthly_expenses_inr: number;
    next_danger_zone_days: number | null;
    forecast_accuracy_pct: number;
  };
  loan_summary: {
    best_approval_probability: number;
    best_lender_type: string;
    top_blocking_factor: string;
  };
  watchlist_summary: {
    total_watched: number;
    high_alert_count: number;
    latest_alert: { company_code: string; alert_type: string; severity: string | null } | null;
  };
  client_risk_summary: {
    high_concentration_clients: number;
    top_clients: Array<{
      id: number;
      client_name: string;
      revenue_share_pct: number;
      avg_payment_delay_days: number;
      bse_code: string | null;
    }>;
  };
  recent_transactions: Array<{
    id: number;
    date: string;
    counterparty: string;
    direction: "in" | "out";
    amount: number;
    source: string;
    category: string;
  }>;
};

const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const cardBase: React.CSSProperties = {
  background: "white",
  border: "0.5px solid #e2e8f0",
  borderRadius: "12px",
  padding: "18px",
  transition: "border-color 0.2s, transform 0.15s",
  cursor: "default",
};

const labelBase: React.CSSProperties = {
  fontSize: "10px",
  fontWeight: "700",
  letterSpacing: "0.1em",
  color: "#94a3b8",
  marginBottom: "6px",
};

const statVal: React.CSSProperties = {
  fontSize: "22px",
  fontWeight: "700",
  color: "#0f172a",
  margin: "6px 0 4px",
};

const btn: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: "6px",
  border: "none",
  borderRadius: "6px",
  padding: "7px 14px",
  fontSize: "12px",
  fontWeight: "700",
  cursor: "pointer",
  letterSpacing: "0.04em",
  transition: "opacity 0.15s, transform 0.1s",
};

function formatInr(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value || 0);
}

export default function DashboardPage() {
  const chartRef = useRef<HTMLCanvasElement | null>(null);
  const chartInstance = useRef<Chart | null>(null);
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function loadDashboard() {
      try {
        const res = await fetch(`${backendUrl}/api/dashboard/1`, { cache: "no-store" });
        if (!res.ok) throw new Error("Dashboard API failed");
        const payload = (await res.json()) as DashboardData;
        if (mounted) setData(payload);
      } catch {
        if (mounted) setError("Dashboard data is unavailable. Start the backend and try again.");
      } finally {
        if (mounted) setLoading(false);
      }
    }

    loadDashboard();
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!chartRef.current || !data) return;
    chartInstance.current?.destroy();

    chartInstance.current = new Chart(chartRef.current, {
      type: "bar",
      data: {
        labels: ["This month"],
        datasets: [
          {
            label: "Revenue",
            data: [data.cash_summary.monthly_revenue_inr],
            backgroundColor: "#3b82f6",
            borderRadius: 4,
            barPercentage: 0.55,
          },
          {
            label: "Expenses",
            data: [data.cash_summary.monthly_expenses_inr],
            backgroundColor: "rgba(148,163,184,0.35)",
            borderRadius: 4,
            barPercentage: 0.55,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
            labels: { font: { size: 11 }, color: "#64748b", boxWidth: 10, padding: 12 },
          },
          tooltip: {
            callbacks: { label: (ctx) => ` ${formatInr(Number(ctx.parsed.y))}` },
          },
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { font: { size: 11 }, color: "#94a3b8" },
          },
          y: {
            grid: { color: "rgba(148,163,184,0.15)" },
            ticks: {
              font: { size: 11 },
              color: "#94a3b8",
              callback: (value: string | number) => formatInr(Number(value)),
            },
            border: { display: false },
          },
        },
      },
    });

    return () => {
      chartInstance.current?.destroy();
    };
  }, [data]);

  if (loading) {
    return <div style={{ padding: "24px", color: "#64748b" }}>Loading dashboard...</div>;
  }

  if (error || !data) {
    return <div style={{ padding: "24px", color: "#dc2626" }}>{error || "Dashboard data unavailable."}</div>;
  }

  const dangerCopy =
    data.cash_summary.next_danger_zone_days === null
      ? "No danger zone found in saved forecasts."
      : `Low cash expected in ${data.cash_summary.next_danger_zone_days} days.`;

  const topClient = data.client_risk_summary.top_clients[0];

  return (
    <div style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "16px", fontFamily: "sans-serif" }}>
      <div>
        <p style={{ ...labelBase, color: "#16a34a" }}>PORTFOLIO OVERVIEW</p>
        <h1 style={{ fontSize: "26px", fontWeight: "700", color: "#0f172a", marginBottom: "6px" }}>
          {data.business.name} is <span style={{ color: "#16a34a" }}>connected</span>
        </h1>
        <p style={{ fontSize: "13px", color: "#64748b", maxWidth: "620px" }}>
          Live summary from your Finemonix backend. Upload more data from the integrations page to improve these signals.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: "14px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "14px" }}>
          <HoverCard style={{ ...cardBase, borderLeft: "3px solid #16a34a", borderRadius: "0 12px 12px 0" }}>
            <p style={labelBase}>CASH ON HAND</p>
            <p style={statVal}>{formatInr(data.cash_summary.current_balance_inr)}</p>
            <p style={{ fontSize: "11px", color: "#16a34a" }}>{data.business.quality_score}% data quality</p>
          </HoverCard>

          <HoverCard style={{ ...cardBase, borderLeft: "3px solid #ee0d0dff", borderRadius: "0 12px 12px 0" }}>
            <p style={labelBase}>MONTHLY EXPENSES</p>
            <p style={statVal}>{formatInr(data.cash_summary.monthly_expenses_inr)}</p>
            <p style={{ fontSize: "11px", color: "#64748b" }}>{dangerCopy}</p>
          </HoverCard>

          <HoverCard style={{ ...cardBase, borderLeft: "3px solid #1d4ed8", borderRadius: "0 12px 12px 0" }}>
            <p style={labelBase}>WATCHLIST ALERTS</p>
            <p style={statVal}>{data.watchlist_summary.high_alert_count}</p>
            <p style={{ fontSize: "11px", color: "#64748b" }}>{data.watchlist_summary.total_watched} companies watched</p>
          </HoverCard>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <HoverCard style={{ background: "#fef2f2", border: "0.5px solid #fecaca", borderRadius: "12px", padding: "18px", flex: 1 }}>
            <p style={{ ...labelBase, color: "#dc2626" }}>PRIORITY ALERT</p>
            <p style={{ fontSize: "13px", fontWeight: "700", color: "#dc2626", marginBottom: "5px" }}>
              {dangerCopy}
            </p>
            <p style={{ fontSize: "12px", color: "#64748b", marginBottom: "12px" }}>
              Forecasting will become richer after the cash flow model endpoint is implemented.
            </p>
            <button style={{ ...btn, background: "#dc2626", color: "#fff" }}>Adjust Cash Flow</button>
          </HoverCard>

          <HoverCard style={{ background: "#eff6ff", border: "0.5px solid #bfdbfe", borderRadius: "12px", padding: "18px", flex: 1 }}>
            <p style={{ ...labelBase, color: "#1d4ed8" }}>CLIENT MONITORING</p>
            <p style={{ fontSize: "13px", fontWeight: "700", color: "#1e3a8a", marginBottom: "5px" }}>
              {topClient ? topClient.client_name : "No client risk yet"}
            </p>
            <p style={{ fontSize: "12px", color: "#64748b" }}>
              {topClient
                ? `${topClient.revenue_share_pct}% revenue share, ${topClient.avg_payment_delay_days} average delay days.`
                : "Upload Tally, GST, or bank data to populate client risk."}
            </p>
          </HoverCard>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 440px 300px", gap: "14px" }}>
        <div style={{ background: "white", border: "0.5px solid #e2e8f0", borderRadius: "12px", padding: "18px" }}>
          <p style={{ fontSize: "13px", fontWeight: "700", color: "#0f172a", marginBottom: "14px" }}>Revenue vs. Expenses</p>
          <div style={{ height: "180px", position: "relative" }}>
            <canvas ref={chartRef} />
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <DarkCard color="#1e3a8a" label="SYNC DATA" labelColor="#93c5fd" title="Upload Ledger" sub="Use integrations to process new files" />
          <DarkCard color="#2563eb" label="CREDIT" labelColor="#bfdbfe" title="Run Loan Check" sub={data.loan_summary.top_blocking_factor} />
        </div>

        <div style={{ background: "#0f2218", borderRadius: "12px", padding: "20px", display: "flex", flexDirection: "column", gap: "10px" }}>
          <p style={{ fontSize: "13px", fontWeight: "700", color: "#fff" }}>Quick Insights</p>
          <InsightItem tag="DATA SOURCES" text={`${data.business.data_sources_connected.length} connected source(s).`} />
          <InsightItem tag="CLIENT RISK" text={`${data.client_risk_summary.high_concentration_clients} high concentration client(s).`} />
          <button style={{ ...btn, background: "#0d9488", color: "#fff", marginTop: "auto", width: "100%", justifyContent: "center" }}>
            EXPLORE STRATEGY
          </button>
        </div>
      </div>

      <div style={{ background: "white", border: "0.5px solid #e2e8f0", borderRadius: "12px", overflow: "hidden" }}>
        <div style={{ padding: "16px 22px", borderBottom: "0.5px solid #e2e8f0", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <p style={{ fontSize: "14px", fontWeight: "700", color: "#0f172a" }}>Recent Activity</p>
        </div>

        <div style={{ background: "#f8fafc", display: "grid", gridTemplateColumns: "1.2fr 1.8fr 1fr 1fr", padding: "10px 22px", fontSize: "10px", fontWeight: "700", color: "#94a3b8", letterSpacing: "0.1em" }}>
          <div>TRANSACTION ID</div>
          <div>COUNTERPARTY</div>
          <div>SOURCE</div>
          <div style={{ textAlign: "right" }}>AMOUNT</div>
        </div>

        {data.recent_transactions.length === 0 ? (
          <div style={{ padding: "18px 22px", fontSize: "13px", color: "#64748b" }}>No uploaded transactions yet.</div>
        ) : (
          data.recent_transactions.map((transaction, index) => (
            <TxRow
              key={transaction.id}
              id={`#TRX-${transaction.id}`}
              name={transaction.counterparty}
              badge={transaction.source.toUpperCase()}
              amount={`${transaction.direction === "in" ? "+" : "-"}${formatInr(transaction.amount)}`}
              amountColor={transaction.direction === "in" ? "#2563eb" : "#0f172a"}
              last={index === data.recent_transactions.length - 1}
            />
          ))
        )}
      </div>
    </div>
  );
}

function HoverCard({ style, children }: { style: React.CSSProperties; children: React.ReactNode }) {
  return (
    <div
      style={style}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = "translateY(-1px)";
        e.currentTarget.style.borderColor = "#cbd5e1";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "";
        e.currentTarget.style.borderColor = "";
      }}
    >
      {children}
    </div>
  );
}

function DarkCard({
  color,
  label,
  labelColor,
  title,
  sub,
}: {
  color: string;
  label: string;
  labelColor: string;
  title: string;
  sub: string;
}) {
  return (
    <div style={{ background: color, borderRadius: "12px", padding: "20px", display: "flex", flexDirection: "column", flex: 1 }}>
      <p style={{ fontSize: "10px", fontWeight: "700", color: labelColor, letterSpacing: "0.1em", marginBottom: "auto" }}>{label}</p>
      <div style={{ marginTop: "16px" }}>
        <p style={{ fontSize: "15px", fontWeight: "700", color: "#fff", marginBottom: "3px" }}>{title}</p>
        <p style={{ fontSize: "11px", color: labelColor }}>{sub}</p>
      </div>
    </div>
  );
}

function InsightItem({ tag, text }: { tag: string; text: React.ReactNode }) {
  return (
    <div style={{ background: "rgba(255,255,255,0.07)", borderRadius: "8px", padding: "12px" }}>
      <p style={{ fontSize: "9px", fontWeight: "700", color: "#0d9488", letterSpacing: "0.1em", marginBottom: "5px" }}>{tag}</p>
      <p style={{ fontSize: "11px", color: "#cbd5e1" }}>{text}</p>
    </div>
  );
}

function TxRow({
  id,
  name,
  badge,
  amount,
  amountColor,
  last = false,
}: {
  id: string;
  name: string;
  badge: string;
  amount: string;
  amountColor: string;
  last?: boolean;
}) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1.8fr 1fr 1fr", padding: "16px 22px", alignItems: "center", borderBottom: last ? "none" : "0.5px solid #f1f5f9" }}>
      <div style={{ fontSize: "13px", fontWeight: "700", color: "#0f172a" }}>{id}</div>
      <div style={{ fontSize: "13px", color: "#0f172a", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{name}</div>
      <div>
        <span style={{ display: "inline-block", padding: "4px 12px", borderRadius: "999px", fontSize: "11px", fontWeight: "700", background: "#dbeafe", color: "#1d4ed8" }}>
          {badge}
        </span>
      </div>
      <div style={{ textAlign: "right", fontSize: "13px", fontWeight: "700", color: amountColor }}>{amount}</div>
    </div>
  );
}
