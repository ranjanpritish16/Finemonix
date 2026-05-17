export default function DashboardPage() {
  return (
    <div style={{ maxWidth: "1200px" }}>
      {/* Header */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ fontSize: "11px", color: "#64748b", fontWeight: "600", letterSpacing: "0.08em", marginBottom: "6px" }}>
          PORTFOLIO OVERVIEW
        </div>
        <h1 style={{ fontSize: "32px", fontWeight: "700", color: "#0f172a", margin: 0 }}>
          Your cash position is <span style={{ color: "#0d9488" }}>Steady.</span>
        </h1>
        <p style={{ color: "#64748b", fontSize: "14px", marginTop: "8px", maxWidth: "480px" }}>
          Financial liquidity remains within optimal thresholds for Q3 expansion plans. However,
          predictive modeling suggests attention is needed on upcoming receivables.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: "24px" }}>
        {/* Left column */}
        <div>
          {/* KPI Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1px", backgroundColor: "#e2e8f0", borderRadius: "10px", overflow: "hidden", marginBottom: "24px" }}>
            {[
              { label: "CASH ON HAND", value: "$428,950.00", sub: "▲ 4.9% vs last month", subColor: "#16a34a" },
              { label: "PROJECTED BURN", value: "$82,400.00", sub: "⊘ 30 days coverage", subColor: "#64748b" },
              { label: "TOTAL DEBT", value: "$1.2M", sub: "⊘ 7.1% Avg APR", subColor: "#64748b" },
            ].map((kpi) => (
              <div key={kpi.label} style={{ backgroundColor: "#fff", padding: "20px 24px" }}>
                <div style={{ fontSize: "10px", color: "#94a3b8", fontWeight: "600", letterSpacing: "0.08em", marginBottom: "8px" }}>{kpi.label}</div>
                <div style={{ fontSize: "24px", fontWeight: "700", color: "#0f172a", marginBottom: "6px" }}>{kpi.value}</div>
                <div style={{ fontSize: "12px", color: kpi.subColor }}>{kpi.sub}</div>
              </div>
            ))}
          </div>

          {/* Chart placeholder */}
          <div style={{ backgroundColor: "#fff", borderRadius: "10px", padding: "20px", marginBottom: "24px", border: "1px solid #e2e8f0" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div style={{ fontWeight: "600", fontSize: "14px" }}>Revenue vs. Expenses</div>
              <span style={{ color: "#94a3b8", fontSize: "18px", cursor: "pointer" }}>⌄</span>
            </div>
            {/* Simple bar chart approximation */}
            <div style={{ display: "flex", alignItems: "flex-end", gap: "16px", height: "140px", paddingBottom: "8px" }}>
              {[
                { month: "MAR", rev: 70, exp: 45 },
                { month: "APR", rev: 85, exp: 60 },
                { month: "MAY", rev: 90, exp: 55 },
                { month: "JUN", rev: 100, exp: 70 },
                { month: "JUL", rev: 60, exp: 80 },
              ].map((d) => (
                <div key={d.month} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "4px", flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "flex-end", gap: "4px", width: "100%", justifyContent: "center" }}>
                    <div style={{ width: "20px", height: `${d.rev}px`, backgroundColor: "#1e3a8a", borderRadius: "3px 3px 0 0" }} />
                    <div style={{ width: "20px", height: `${d.exp}px`, backgroundColor: "#93c5fd", borderRadius: "3px 3px 0 0" }} />
                  </div>
                  <div style={{ fontSize: "10px", color: "#94a3b8" }}>{d.month}</div>
                </div>
              ))}
            </div>
            <div style={{ display: "flex", gap: "16px", marginTop: "8px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", color: "#64748b" }}>
                <div style={{ width: "10px", height: "10px", backgroundColor: "#1e3a8a", borderRadius: "2px" }} /> Revenue
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", color: "#64748b" }}>
                <div style={{ width: "10px", height: "10px", backgroundColor: "#93c5fd", borderRadius: "2px" }} /> Expenses
              </div>
            </div>
          </div>

          {/* Quick action cards */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            {[
              { title: "Upload Ledger", sub: "Sync your latest bank statements", icon: "📄", bg: "#1e3a8a" },
              { title: "Run Loan Check", sub: "Check eligibility for lines of credit", icon: "📋", bg: "#1e3a8a" },
            ].map((card) => (
              <div key={card.title} style={{
                backgroundColor: card.bg,
                borderRadius: "10px",
                padding: "20px",
                color: "white",
                cursor: "pointer",
                display: "flex",
                flexDirection: "column",
                gap: "8px",
              }}>
                <span style={{ fontSize: "24px" }}>{card.icon}</span>
                <div style={{ fontWeight: "600", fontSize: "15px" }}>{card.title}</div>
                <div style={{ fontSize: "12px", color: "#93c5fd" }}>{card.sub}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Right column */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Priority Alert */}
          <div style={{ backgroundColor: "#fef2f2", border: "1px solid #fecaca", borderRadius: "10px", padding: "16px" }}>
            <div style={{ fontSize: "10px", color: "#dc2626", fontWeight: "600", letterSpacing: "0.08em", marginBottom: "8px" }}>⚡ PRIORITY ALERT</div>
            <div style={{ fontWeight: "700", color: "#dc2626", fontSize: "14px", marginBottom: "6px" }}>Low cash expected in 15 days</div>
            <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "12px" }}>
              Upcoming vendor payments total $145k expense, a predicted balance of $110k.
            </div>
            <button style={{
              backgroundColor: "#dc2626", color: "white", border: "none",
              borderRadius: "6px", padding: "7px 14px", fontSize: "12px", fontWeight: "600", cursor: "pointer",
            }}>Adjust Cash Flow</button>
          </div>

          {/* Client monitoring */}
          <div style={{ backgroundColor: "#fff", border: "1px solid #e2e8f0", borderRadius: "10px", padding: "16px" }}>
            <div style={{ fontSize: "10px", color: "#94a3b8", fontWeight: "600", letterSpacing: "0.08em", marginBottom: "8px" }}>⊙ CLIENT MONITORING</div>
            <div style={{ fontWeight: "600", fontSize: "14px", marginBottom: "6px" }}>Major client ABC at risk</div>
            <div style={{ fontSize: "12px", color: "#64748b" }}>
              Delayed payment behavior detected over 3 consecutive cycles. Credit score dropped 12 pts.
            </div>
          </div>

          {/* Quick Insights */}
          <div style={{ backgroundColor: "#0f172a", borderRadius: "10px", padding: "16px", color: "white", flex: 1 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
              <div style={{ fontWeight: "600", fontSize: "14px" }}>⚡ Quick Insights</div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div style={{ backgroundColor: "#1e293b", borderRadius: "8px", padding: "12px" }}>
                <div style={{ fontSize: "10px", color: "#0d9488", fontWeight: "600", marginBottom: "6px" }}>COST OPTIMIZATION</div>
                <div style={{ fontSize: "12px", color: "#cbd5e1" }}>
                  Subscriptions for "SaaS Tool Alpha" have increased 40% this quarter. You could save <span style={{ color: "#0d9488" }}>$1,200/yr</span> by consolidating licenses.
                </div>
              </div>
              <div style={{ backgroundColor: "#1e293b", borderRadius: "8px", padding: "12px" }}>
                <div style={{ fontSize: "10px", color: "#0d9488", fontWeight: "600", marginBottom: "6px" }}>GROWTH OPPORTUNITY</div>
                <div style={{ fontSize: "12px", color: "#cbd5e1" }}>
                  Cash reserve is 2.1x above benchmark. Recommended action: Allocate $90k to high-yield sweep account or marketing R&D.
                </div>
              </div>
            </div>
            <button style={{
              width: "100%", marginTop: "14px",
              backgroundColor: "#0d9488", color: "white", border: "none",
              borderRadius: "6px", padding: "10px", fontSize: "13px", fontWeight: "600", cursor: "pointer",
            }}>EXPLORE STRATEGY</button>
          </div>
        </div>
      </div>
    </div>
  );
}
