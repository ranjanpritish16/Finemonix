export default function WatchlistPage() {
  const clients = [
    {
      name: "Alpha Logistics Pvt Ltd",
      tier: "B2S Tier 1 | Construction & Infra",
      risk: "CRITICAL RISK",
      riskColor: "#dc2626",
      riskBg: "#fee2e2",
      updated: "41 mins ago",
      currentRatio: { val: "0.82", note: "(2%)" },
      debtEquity: { val: "3.45", note: "(High)" },
      pledging: { val: "78.2%", note: "(Pledged)" },
      alert: {
        type: "RECENT ALERT",
        typeColor: "#dc2626",
        text: "Legal proceedings initiated by creditor consortium regarding payment defaults in Q3...",
      },
      actions: ["View Public Filings", "Review Exposure"],
    },
    {
      name: "Nexus Tech Systems",
      tier: "B2S Tier 2 | Software Services",
      risk: "ELEVATED RISK",
      riskColor: "#d97706",
      riskBg: "#fef3c7",
      updated: "12h ago",
      currentRatio: { val: "1.45", note: "(Stable)" },
      debtEquity: { val: "0.85", note: "(Low)" },
      pledging: { val: "12.0%", note: "(Stable)" },
      alert: {
        type: "ALERT",
        typeColor: "#d97706",
        text: "Sudden change in registered board members reported to MCA last week.",
      },
      actions: ["View Public Filings", "Audit Loan"],
    },
    {
      name: "GreenLeaf Agro Exports",
      tier: "B2S Tier 2 | Food Processing",
      risk: "HEALTHY",
      riskColor: "#16a34a",
      riskBg: "#dcfce7",
      updated: "5h ago",
      currentRatio: { val: "2.10", note: "(High)" },
      debtEquity: { val: "0.12", note: "(Optimal)" },
      pledging: { val: "0.0%", note: "(None)" },
      alert: {
        type: "COMPLIANCE CLEAR",
        typeColor: "#16a34a",
        text: "Annual compliance certificate filed successfully. Revenue growth projected at 18% YoY.",
      },
      actions: ["View Public Filings", "No Action Needed"],
    },
  ];

  const intel = [
    { ago: "10 MIN AGO", text: "Court records indicate winding up petition for Alpha Logistics." },
    { ago: "3H AGO", text: "SEBI updates promoter holding data for Nexus Tech." },
    { ago: "8H AGO", text: "GreenLeaf Agro expands B2B credit line by 20%." },
  ];

  const sectors = [
    { name: "1 Logistics", value: "-6.2%", color: "#dc2626" },
    { name: "Agro Tech", value: "+1.6%", color: "#16a34a" },
    { name: "Manufacturing", value: "Stable", color: "#94a3b8" },
  ];

  return (
    <div style={{ maxWidth: "1200px" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "28px" }}>
        <div>
          <h1 style={{ fontSize: "28px", fontWeight: "700", margin: "0 0 4px" }}>Client Surveillance Dashboard</h1>
          <p style={{ color: "#64748b", fontSize: "13px", margin: 0 }}>
            Real-time surveillance of B2B exposure. Derived from MCA filings, credit bureaus, and automated news sentiment analysis.
          </p>
        </div>
        <div style={{
          backgroundColor: "#dcfce7", border: "1px solid #86efac",
          borderRadius: "20px", padding: "6px 14px",
          fontSize: "12px", fontWeight: "600", color: "#16a34a",
        }}>✦ AI Insight: 2 high-risk alerts detected in the last 24h</div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: "24px" }}>
        {/* Client cards */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {clients.map((client) => (
            <div key={client.name} style={{ backgroundColor: "#fff", borderRadius: "12px", border: "1px solid #e2e8f0", padding: "20px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "14px" }}>
                <div>
                  <div style={{ fontWeight: "700", fontSize: "15px", marginBottom: "2px" }}>
                    {client.name} <span style={{ color: "#94a3b8", fontSize: "14px" }}>ⓘ</span>
                  </div>
                  <div style={{ fontSize: "12px", color: "#64748b" }}>{client.tier}</div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: "10px", fontWeight: "700", color: client.riskColor, backgroundColor: client.riskBg, padding: "3px 8px", borderRadius: "4px", marginBottom: "4px" }}>
                    {client.risk}
                  </div>
                  <div style={{ fontSize: "11px", color: "#94a3b8" }}>Updated {client.updated}</div>
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0", backgroundColor: "#f8fafc", borderRadius: "8px", overflow: "hidden", marginBottom: "14px" }}>
                {[
                  { label: "CURRENT RATIO", ...client.currentRatio },
                  { label: "DEBT/EQUITY", ...client.debtEquity },
                  { label: "PROMOTER PLEDGING", ...client.pledging },
                ].map((metric) => (
                  <div key={metric.label} style={{ padding: "12px 14px", borderRight: "1px solid #e2e8f0" }}>
                    <div style={{ fontSize: "9px", color: "#94a3b8", fontWeight: "600", marginBottom: "4px" }}>{metric.label}</div>
                    <div style={{ fontSize: "16px", fontWeight: "700", color: "#0f172a" }}>{metric.val}</div>
                    <div style={{ fontSize: "11px", color: "#94a3b8" }}>{metric.note}</div>
                  </div>
                ))}
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div style={{ flex: 1, paddingRight: "16px" }}>
                  <div style={{ fontSize: "10px", fontWeight: "700", color: client.alert.typeColor, marginBottom: "4px" }}>⚡ {client.alert.type}</div>
                  <div style={{ fontSize: "12px", color: "#64748b" }}>{client.alert.text}</div>
                </div>
                <div style={{ display: "flex", gap: "8px", flexShrink: 0 }}>
                  {client.actions.map((action, i) => (
                    <button key={action} style={{
                      padding: "7px 12px", fontSize: "11px", fontWeight: "600", cursor: "pointer",
                      borderRadius: "6px", border: "1px solid #e2e8f0",
                      backgroundColor: i === 0 ? "transparent" : "#0f172a",
                      color: i === 0 ? "#0f172a" : "white",
                    }}>{action}</button>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Right panel */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Portfolio exposure */}
          <div style={{ backgroundColor: "#0f172a", borderRadius: "10px", padding: "16px", color: "white" }}>
            <div style={{ fontSize: "11px", color: "#94a3b8", fontWeight: "600", marginBottom: "8px" }}>PORTFOLIO EXPOSURE</div>
            <div style={{ fontSize: "26px", fontWeight: "700", marginBottom: "4px" }}>$14.2M</div>
            <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "12px" }}>Total Monitored Credit</div>
            <div style={{ height: "6px", backgroundColor: "#1e293b", borderRadius: "3px", marginBottom: "6px" }}>
              <div style={{ height: "100%", width: "19%", backgroundColor: "#dc2626", borderRadius: "3px" }} />
            </div>
            <div style={{ display: "flex", gap: "16px", fontSize: "11px" }}>
              <span style={{ color: "#dc2626" }}>● 19% Critical</span>
              <span style={{ color: "#d97706" }}>● 20% Watchlist</span>
            </div>
          </div>

          {/* Sector heatmap */}
          <div style={{ backgroundColor: "#fff", borderRadius: "10px", border: "1px solid #e2e8f0", padding: "16px" }}>
            <div style={{ fontWeight: "600", fontSize: "14px", marginBottom: "12px" }}>Sector Heatmap</div>
            {sectors.map((s) => (
              <div key={s.name} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid #f8fafc", fontSize: "12px" }}>
                <span>{s.name}</span>
                <span style={{ fontWeight: "600", color: s.color }}>{s.value}</span>
              </div>
            ))}
          </div>

          {/* Intelligence Feed */}
          <div style={{ backgroundColor: "#fff", borderRadius: "10px", border: "1px solid #e2e8f0", padding: "16px" }}>
            <div style={{ fontWeight: "600", fontSize: "14px", marginBottom: "12px" }}>Intelligence Feed</div>
            {intel.map((item) => (
              <div key={item.ago} style={{ marginBottom: "10px", paddingBottom: "10px", borderBottom: "1px solid #f8fafc" }}>
                <div style={{ fontSize: "10px", color: "#94a3b8", fontWeight: "600", marginBottom: "4px" }}>{item.ago}</div>
                <div style={{ fontSize: "12px", color: "#334155" }}>{item.text}</div>
              </div>
            ))}
            <button style={{
              width: "100%", padding: "8px", backgroundColor: "transparent",
              border: "1px solid #e2e8f0", color: "#64748b",
              borderRadius: "6px", fontSize: "12px", fontWeight: "600", cursor: "pointer",
            }}>SEE ALL INTELLIGENCE</button>
          </div>
        </div>
      </div>
    </div>
  );
}
