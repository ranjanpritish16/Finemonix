"use client";

import React, { useEffect, useRef } from "react";
import { Chart, registerables } from "chart.js";

Chart.register(...registerables);

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

export default function DashboardPage() {
  const chartRef = useRef<HTMLCanvasElement | null>(null);
  const chartInstance = useRef<Chart | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;
    chartInstance.current?.destroy();

    chartInstance.current = new Chart(chartRef.current, {
      type: "bar",
      data: {
        labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
        datasets: [
          {
            label: "Revenue",
            data: [210, 245, 230, 280, 265, 310, 295],
            backgroundColor: "#3b82f6",
            borderRadius: 4,
            barPercentage: 0.55,
          },
          {
            label: "Expenses",
            data: [160, 175, 190, 200, 185, 220, 210],
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
            callbacks: { label: (ctx) => ` $${ctx.parsed.y}k` },
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
              callback: (v: string | number) => `$${v}k`,
            },
            border: { display: false },
          },
        },
      },
    });

    return () => { chartInstance.current?.destroy(); };
  }, []);

  return (
    <div style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "16px", fontFamily: "sans-serif" }}>

      {/* ── Heading ── */}
      <div>
        <p style={{ ...labelBase, color: "#16a34a" }}>PORTFOLIO OVERVIEW</p>
        <h1 style={{ fontSize: "26px", fontWeight: "700", color: "#0f172a", marginBottom: "6px" }}>
          Your cash position is <span style={{ color: "#16a34a" }}>Steady</span>
        </h1>
        <p style={{ fontSize: "13px", color: "#64748b", maxWidth: "580px" }}>
          Financial liquidity remains within optimal thresholds for Q3 expansion plans. Predictive modelling suggests
          attention on upcoming receivables.
        </p>
      </div>

      {/* ── ROW 1: Stat Cards + Alerts ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: "14px" }}>

        {/* Stat cards */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "14px" }}>
          <HoverCard style={{ ...cardBase, borderLeft: "3px solid #16a34a", borderRadius: "0 12px 12px 0" }}>
            <p style={labelBase}>CASH ON HAND</p>
            <p style={statVal}>$428,950</p>
            <p style={{ fontSize: "11px", color: "#16a34a" }}>↗ 4.2% vs last month</p>
          </HoverCard>

          <HoverCard style={{ ...cardBase, borderLeft: "3px solid #ee0d0dff", borderRadius: "0 12px 12px 0" }}>
            <p style={labelBase}>PROJECTED BURN</p>
            <p style={statVal}>$82,400</p>
            <p style={{ fontSize: "11px", color: "#64748b" }}>⊙ 32 days coverage</p>
          </HoverCard>

          <HoverCard style={{ ...cardBase, borderLeft: "3px solid #1d4ed8", borderRadius: "0 12px 12px 0" }}>
            <p style={labelBase}>TOTAL DEBT</p>
            <p style={statVal}>$1.2M</p>
            <p style={{ fontSize: "11px", color: "#64748b" }}>⊙ 2.1% Avg APR</p>
            <div style={{ height: "4px", background: "rgba(148,163,184,0.25)", borderRadius: "2px", marginTop: "8px", overflow: "hidden" }}>
              <div style={{ height: "100%", width: "48%", background: "#60a5fa", borderRadius: "2px", transition: "width 1s ease" }} />
            </div>
          </HoverCard>
        </div>

        {/* Alert + Monitor */}
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <HoverCard style={{ background: "#fef2f2", border: "0.5px solid #fecaca", borderRadius: "12px", padding: "18px", flex: 1 }}>
            <p style={{ ...labelBase, color: "#dc2626" }}>⚡ PRIORITY ALERT</p>
            <p style={{ fontSize: "13px", fontWeight: "700", color: "#dc2626", marginBottom: "5px" }}>
              Low cash expected in 15 days
            </p>
            <p style={{ fontSize: "12px", color: "#64748b", marginBottom: "12px" }}>
              Upcoming vendor payments total $145k against a predicted balance of $110k.
            </p>
            <button style={{ ...btn, background: "#dc2626", color: "#fff" }}>Adjust Cash Flow →</button>
          </HoverCard>

          <HoverCard style={{ background: "#eff6ff", border: "0.5px solid #bfdbfe", borderRadius: "12px", padding: "18px", flex: 1 }}>
            <p style={{ ...labelBase, color: "#1d4ed8" }}>⊙ CLIENT MONITORING</p>
            <p style={{ fontSize: "13px", fontWeight: "700", color: "#1e3a8a", marginBottom: "5px" }}>
              Major client ABC at risk
            </p>
            <p style={{ fontSize: "12px", color: "#64748b" }}>
              Delayed payment detected over 3 consecutive cycles. Credit score dropped 12 pts.
            </p>
          </HoverCard>
        </div>
      </div>

      {/* ── ROW 2: Chart + Dark Cards + Insights ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 440px 300px", gap: "14px" }}>

        {/* Chart */}
        <div style={{ background: "white", border: "0.5px solid #e2e8f0", borderRadius: "12px", padding: "18px" }}>
          <p style={{ fontSize: "13px", fontWeight: "700", color: "#0f172a", marginBottom: "14px" }}>Revenue vs. Expenses</p>
          <div style={{ height: "180px", position: "relative" }}>
            <canvas ref={chartRef} />
          </div>
        </div>

        {/* Upload Ledger + Run Loan Check */}
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <DarkCard
            color="#1e3a8a"
            label="SYNC DATA"
            labelColor="#93c5fd"
            title="Upload Ledger"
            sub="Sync your latest bank statements →"
          />
          <DarkCard
            color="#2563eb"
            label="CREDIT"
            labelColor="#bfdbfe"
            title="Run Loan Check"
            sub="Instant eligibility score →"
          />
        </div>

        {/* Quick Insights */}
        <div style={{ background: "#0f2218", borderRadius: "12px", padding: "20px", display: "flex", flexDirection: "column", gap: "10px" }}>
          <p style={{ fontSize: "13px", fontWeight: "700", color: "#fff" }}>⚡ Quick Insights</p>
          <InsightItem
            tag="COST OPTIMIZATION"
            text={<>Subscriptions for "SaaS Tool Alpha" up 40%. Save <strong style={{ color: "#2dd4bf" }}>$1,200/yr</strong> by consolidating licenses.</>}
          />
          <InsightItem
            tag="GROWTH OPPORTUNITY"
            text="Cash reserve is 2.1× above benchmark. Allocate $90k to a high-yield sweep account."
          />
          <button style={{ ...btn, background: "#0d9488", color: "#fff", marginTop: "auto", width: "100%", justifyContent: "center" }}>
            EXPLORE STRATEGY →
          </button>
        </div>
      </div>

      {/* ── ROW 3: Transaction Table ── */}
      <div style={{ background: "white", border: "0.5px solid #e2e8f0", borderRadius: "12px", overflow: "hidden" }}>
        <div style={{ padding: "16px 22px", borderBottom: "0.5px solid #e2e8f0", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <p style={{ fontSize: "14px", fontWeight: "700", color: "#0f172a" }}>Recent Institutional Activity</p>
          <button style={{ ...btn, background: "#2563eb", color: "#fff", fontSize: "11px", padding: "5px 12px" }}>View All →</button>
        </div>

        <div style={{
          background: "#f8fafc",
          display: "grid",
          gridTemplateColumns: "1.2fr 1.8fr 1fr 1fr",
          padding: "10px 22px",
          fontSize: "10px",
          fontWeight: "700",
          color: "#94a3b8",
          letterSpacing: "0.1em",
        }}>
          <div>TRANSACTION ID</div>
          <div>COUNTERPARTY</div>
          <div>STATUS</div>
          <div style={{ textAlign: "right" }}>AMOUNT</div>
        </div>

        <TxRow
          id="#TRX-99201"
          initials="CC"
          avatarBg="#e2e8f0"
          avatarColor="#475569"
          name="Cloud Core Systems"
          badge="Cleared"
          badgeBg="#d1fae5"
          badgeColor="#065f46"
          amount="-$12,450.00"
          amountColor="#0f172a"
        />
        <TxRow
          id="#TRX-99185"
          initials="LM"
          avatarBg="#dbeafe"
          avatarColor="#2563eb"
          name="Lunar Media Group"
          badge="Pending"
          badgeBg="#dbeafe"
          badgeColor="#1d4ed8"
          amount="+$45,000.00"
          amountColor="#2563eb"
          last
        />
      </div>

    </div>
  );
}

/* ── Sub-components ── */

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
  color, label, labelColor, title, sub,
}: {
  color: string; label: string; labelColor: string; title: string; sub: string;
}) {
  return (
    <div
      style={{
        background: color,
        borderRadius: "12px",
        padding: "20px",
        display: "flex",
        flexDirection: "column",
        flex: 1,
        cursor: "pointer",
        transition: "transform 0.15s, opacity 0.15s",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = "translateY(-2px)";
        e.currentTarget.style.opacity = "0.92";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "";
        e.currentTarget.style.opacity = "";
      }}
    >
      <p style={{ fontSize: "10px", fontWeight: "700", color: labelColor, letterSpacing: "0.1em", marginBottom: "auto" }}>
        {label}
      </p>
      <div style={{ marginTop: "16px" }}>
        <p style={{ fontSize: "15px", fontWeight: "700", color: "#fff", marginBottom: "3px" }}>{title}</p>
        <p style={{ fontSize: "11px", color: labelColor }}>{sub}</p>
      </div>
    </div>
  );
}

function InsightItem({ tag, text }: { tag: string; text: React.ReactNode }) {
  return (
    <div
      style={{ background: "rgba(255,255,255,0.07)", borderRadius: "8px", padding: "12px", transition: "background 0.15s", cursor: "default" }}
      onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(255,255,255,0.12)"; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = "rgba(255,255,255,0.07)"; }}
    >
      <p style={{ fontSize: "9px", fontWeight: "700", color: "#0d9488", letterSpacing: "0.1em", marginBottom: "5px" }}>{tag}</p>
      <p style={{ fontSize: "11px", color: "#cbd5e1" }}>{text}</p>
    </div>
  );
}

function TxRow({
  id, initials, avatarBg, avatarColor, name, badge, badgeBg, badgeColor, amount, amountColor, last = false,
}: {
  id: string; initials: string; avatarBg: string; avatarColor: string;
  name: string; badge: string; badgeBg: string; badgeColor: string;
  amount: string; amountColor: string; last?: boolean;
}) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1.2fr 1.8fr 1fr 1fr",
        padding: "16px 22px",
        alignItems: "center",
        borderBottom: last ? "none" : "0.5px solid #f1f5f9",
        cursor: "pointer",
        transition: "background 0.15s",
      }}
      onMouseEnter={(e) => { e.currentTarget.style.background = "#f8fafc"; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = ""; }}
    >
      <div style={{ fontSize: "13px", fontWeight: "700", color: "#0f172a" }}>{id}</div>
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <div style={{
          width: "32px", height: "32px", borderRadius: "50%",
          background: avatarBg, color: avatarColor,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: "11px", fontWeight: "700", flexShrink: 0,
        }}>
          {initials}
        </div>
        <span style={{ fontSize: "13px", color: "#0f172a" }}>{name}</span>
      </div>
      <div>
        <span style={{ display: "inline-block", padding: "4px 12px", borderRadius: "999px", fontSize: "11px", fontWeight: "700", background: badgeBg, color: badgeColor }}>
          {badge}
        </span>
      </div>
      <div style={{ textAlign: "right", fontSize: "13px", fontWeight: "700", color: amountColor }}>{amount}</div>
    </div>
  );
}