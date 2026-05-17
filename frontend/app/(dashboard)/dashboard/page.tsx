export default function DashboardPage() {
  return (
    <div style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "20px" }}>

      {/* ── ROW 1: Heading + Priority Alert & Client Monitoring ── */}
      <div style={{ display: "flex", gap: "16px", height: "300px" }}>

        {/* Heading area */}
        <div style={{ flex: 1 }}>
          <p style={{ color: "#16a34a", margin: "0 0 6px 0", fontSize: "10px", fontWeight: "bold", letterSpacing: "0.08em" }}>PORTFOLIO OVERVIEW</p>
          <h1 style={{ margin: "0 0 10px 0", fontSize: "28px", fontWeight: "bold" }}>Your cash position is Steady</h1>
          <p style={{ margin: "0", fontSize: "13px", color: "#64748b" }}>Financial liquidity remains within optimal thresholds for Q3 expansion plans. However, predictive modelling suggests attention is needed on upcoming receivables.</p>
          <div style={{ display: "flex", gap: "16px" }}>
            <div style={{ backgroundColor: "white", height: "150px", flex: 1, marginTop: "30px", borderRadius: "12px", padding: "16px", border: "1px solid #e2e8f0" }}>
              <p style={{ margin: "0 0 8px 0", fontSize: "10px", fontWeight: "600", color: "#94a3b8", letterSpacing: "0.08em" }}>CASH ON HAND</p>
              <p style={{ margin: "0 0 8px 0", fontSize: "22px", fontWeight: "700", color: "#0f172a" }}>$428,950.00</p>
              <p style={{ margin: "0", fontSize: "11px", color: "#16a34a" }}>↗ 4.2% vs last month</p>
            </div>
            <div style={{ backgroundColor: "white", height: "150px", flex: 1, marginTop: "30px", borderRadius: "12px", padding: "16px", border: "1px solid #e2e8f0" }}>
              <p style={{ margin: "0 0 8px 0", fontSize: "10px", fontWeight: "600", color: "#94a3b8", letterSpacing: "0.08em" }}>PROJECTED BURN</p>
              <p style={{ margin: "0 0 8px 0", fontSize: "22px", fontWeight: "700", color: "#0f172a" }}>$82,400.00</p>
              <p style={{ margin: "0", fontSize: "11px", color: "#64748b" }}>⊙ 32 days coverage</p>
            </div>
            <div style={{ backgroundColor: "white", height: "150px", flex: 1, marginTop: "30px", borderRadius: "12px", padding: "16px", border: "1px solid #e2e8f0", borderLeft: "3px solid #1d4ed8" }}>
              <p style={{ margin: "0 0 8px 0", fontSize: "10px", fontWeight: "600", color: "#94a3b8", letterSpacing: "0.08em" }}>TOTAL DEBT</p>
              <p style={{ margin: "0 0 8px 0", fontSize: "22px", fontWeight: "700", color: "#0f172a" }}>$1.2M</p>
              <p style={{ margin: "0", fontSize: "11px", color: "#64748b" }}>⊙ 2.1% Avg APR</p>
            </div>
          </div>
        </div>

        {/* Right column — Priority Alert + Client Monitoring */}
        <div style={{ display: "flex", flexDirection: "column", gap: "12px", width: "375px" }}>

          {/* Priority Alert */}
          <div style={{ backgroundColor: "#fef2f2", border: "1px solid #fecaca", borderRadius: "12px", padding: "16px", height: "125px" }}>
            <p style={{ margin: "0 0 4px 0", fontSize: "10px", fontWeight: "bold", color: "#dc2626", letterSpacing: "0.08em" }}>⚡ PRIORITY ALERT</p>
            <p style={{ margin: "0 0 6px 0", fontSize: "13px", fontWeight: "bold", color: "#dc2626" }}>Low cash expected in 15 days</p>
            <p style={{ margin: "0 0 12px 0", fontSize: "12px", color: "#64748b" }}>Upcoming vendor payments total $145k against a predicted balance of $110k.</p>
            <button style={{ backgroundColor: "#dc2626", color: "white", border: "none", borderRadius: "6px", padding: "6px 14px", fontSize: "12px", fontWeight: "600", cursor: "pointer" }}>Adjust Cash Flow</button>
          </div>

          {/* Client Monitoring */}
          <div style={{ backgroundColor: "#bfd5f1ff", border: "1px solid #bfdbfe", borderRadius: "12px", padding: "16px", height: "125px" }}>
            <p style={{ margin: "0 0 4px 0", fontSize: "10px", fontWeight: "bold", color: "#1d4ed8", letterSpacing: "0.08em" }}>⊙ CLIENT MONITORING</p>
            <p style={{ margin: "0 0 6px 0", fontSize: "13px", fontWeight: "bold", color: "#1e293b" }}>Major client ABC at risk</p>
            <p style={{ margin: "0", fontSize: "12px", color: "#64748b" }}>Delayed payment behavior detected over 3 consecutive cycles. Credit score dropped 12 pts.</p>
          </div>

        </div>
      </div>

      {/* ── ROW 2: Chart + Upload/Loan cards + Quick Insights ── */}
      <div style={{ display: "flex", gap: "16px" }}>

        {/* Chart placeholder */}
        <div style={{ flex: 1, backgroundColor: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "12px", padding: "20px", minHeight: "350px" }}>
          <p style={{ margin: "0 0 16px 0", fontWeight: "600", fontSize: "14px" }}>Revenue vs. Expenses</p>
          <p style={{ color: "#94a3b8", fontSize: "12px" }}>Chart will go here</p>
        </div>

        {/* Upload Ledger + Run Loan Check */}
        <div style={{ display: "flex", flexDirection: "column", gap: "12px", width: "500px" }}>

          {/* Upload Ledger */}
          <div style={{ backgroundColor: "#1e3a8a", borderRadius: "12px", padding: "20px", color: "white", height: "175px", display: "flex", flexDirection: "column", justifyContent: "flex-end" }}>
            <p style={{ margin: "0 0 4px 0", fontSize: "14px", fontWeight: "700" }}>Upload Ledger</p>
            <p style={{ margin: "0", fontSize: "11px", color: "#93c5fd" }}>Sync your latest bank statements</p>
          </div>

          {/* Run Loan Check */}
          <div style={{ backgroundColor: "#2563eb", borderRadius: "12px", padding: "20px", color: "white", height: "175px", display: "flex", flexDirection: "column", justifyContent: "flex-end" }}>
            <p style={{ margin: "0 0 4px 0", fontSize: "14px", fontWeight: "700" }}>Run Loan Check</p>
            <p style={{ margin: "0", fontSize: "11px", color: "#bfdbfe" }}>Instant eligibility score for lines of credit</p>
          </div>

        </div>

        {/* Quick Insights */}
        <div style={{ backgroundColor: "#0f2218", borderRadius: "12px", padding: "20px", width: "350px", color: "white", display: "flex", flexDirection: "column", gap: "12px" }}>
          <p style={{ margin: "0", fontWeight: "700", fontSize: "14px" }}>⚡ Quick Insights</p>

          <div style={{ backgroundColor: "#1a3326", borderRadius: "8px", padding: "12px" }}>
            <p style={{ margin: "0 0 4px 0", fontSize: "9px", fontWeight: "700", color: "#0d9488", letterSpacing: "0.08em" }}>COST OPTIMIZATION</p>
            <p style={{ margin: "0", fontSize: "11px", color: "#cbd5e1" }}>Subscriptions for "SaaS Tool Alpha" increased 40%. Save <span style={{ color: "#0d9488" }}>$1,200/yr</span> by consolidating licenses.</p>
          </div>

          <div style={{ backgroundColor: "#1a3326", borderRadius: "8px", padding: "12px" }}>
            <p style={{ margin: "0 0 4px 0", fontSize: "9px", fontWeight: "700", color: "#0d9488", letterSpacing: "0.08em" }}>GROWTH OPPORTUNITY</p>
            <p style={{ margin: "0", fontSize: "11px", color: "#cbd5e1" }}>Cash reserve is 2.1x above benchmark. Allocate $90k to high-yield sweep account.</p>
          </div>

          <button style={{ marginTop: "auto", backgroundColor: "#0d9488", color: "white", border: "none", borderRadius: "6px", padding: "10px", fontSize: "12px", fontWeight: "700", cursor: "pointer", letterSpacing: "0.05em" }}>EXPLORE STRATEGY</button>
        </div>

      </div>
      <div style={{ display: "flex", gap: "16px" }}>
        <div style={{ backgroundColor: "white", border: "1px solid #e2e8f0", borderRadius: "12px", width: "100%", overflow: "hidden", }}>
          {/* Header */}
          <div style={{ padding: "20px 24px", borderBottom: "1px solid #e2e8f0", display: "flex", justifyContent: "space-between", alignItems: "center", }}>
            <p style={{ margin: "0", fontSize: "16px", fontWeight: "700", color: "#0f172a", }}>
              Recent Institutional Activity
            </p>

            <p style={{ margin: "0", fontSize: "12px", fontWeight: "600", color: "#2563eb", cursor: "pointer", }}>
              View All →
            </p>
          </div>

          {/* Table Header */}
          <div style={{ backgroundColor: "#f1f5f9", display: "grid", gridTemplateColumns: "1.2fr 1.8fr 1fr 1fr", padding: "14px 24px", fontSize: "10px", fontWeight: "700", color: "#64748b", letterSpacing: "0.12em", }}>
            <div>TRANSACTION ID</div>
            <div>COUNTERPARTY</div>
            <div>STATUS</div>
            <div style={{ textAlign: "right" }}>AMOUNT</div>
          </div>

          {/* Row 1 */}
          <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1.8fr 1fr 1fr", padding: "18px 24px", alignItems: "center", borderBottom: "1px solid #f1f5f9", }}>
            <div style={{ fontSize: "14px", fontWeight: "700", color: "#0f172a", }}>
              #TRX-99201
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "12px", }}>
              <div style={{ width: "30px", height: "30px", borderRadius: "50%", backgroundColor: "#e2e8f0", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "11px", fontWeight: "700", color: "#475569", }}>
                CC
              </div>
              <p style={{ margin: "0", fontSize: "14px", color: "#0f172a", }}>Cloud Core Systems</p>
            </div>

            <div>
              <span style={{ backgroundColor: "#99f6e4", color: "#065f46", padding: "6px 12px", borderRadius: "999px", fontSize: "11px", fontWeight: "600", }}>
                Cleared
              </span>
            </div>

            <div style={{ textAlign: "right", fontSize: "14px", fontWeight: "700", color: "#0f172a", }}>
              -$12,450.00
            </div>
          </div>

          {/* Row 2 */}
          <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1.8fr 1fr 1fr", padding: "18px 24px", alignItems: "center", }}>
            <div style={{ fontSize: "14px", fontWeight: "700", color: "#0f172a", }}>#TRX-99185</div>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", }}>
              <div style={{ width: "30px", height: "30px", borderRadius: "50%", backgroundColor: "#dbeafe", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "11px", fontWeight: "700", color: "#2563eb", }}>
                LM
              </div>

              <p style={{ margin: "0", fontSize: "14px", color: "#0f172a", }}>
                Lunar Media Group
              </p>
            </div>

            <div>
              <span style={{ backgroundColor: "#dbeafe", color: "#1d4ed8", padding: "6px 12px", borderRadius: "999px", fontSize: "11px", fontWeight: "600", }}>
                Pending
              </span>
            </div>

            <div style={{ textAlign: "right", fontSize: "14px", fontWeight: "700", color: "#2563eb", }}>
              +$45,000.00
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
