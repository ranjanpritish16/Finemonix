export default function CashFlowPage() {
  const scenarios = [
    { label: "Delay Client X Payment", sub: "Postpone ₹1.5L inflow by 10 days", enabled: false },
    { label: "New 10L Business Loan", sub: "12% APR, 5-year tenure", enabled: true, impact: "Impact: +₹8.1L Cash" },
    { label: "Early Vendor Settlement", sub: "2% discount on ₹7.4L payable", enabled: false },
  ];

  const inflows = [
    { name: "Global Tech Corp", date: "Due 17th", amount: "₹12.5L" },
    { name: "Reliance Retail", date: "Due 23rd", amount: "₹8.2L" },
    { name: "Tata Ventures", date: "Due 28th", amount: "₹5.6L" },
  ];

  const outflows = [
    { name: "Payroll Aug 2024", date: "Due 1st", amount: "₹8.2L" },
    { name: "Office Rent", date: "Due 5th", amount: "₹2.4L" },
    { name: "GST Payment", date: "Due 20th", amount: "₹3.1L" },
  ];

  return (
    <div style={{ maxWidth: "1200px" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "28px" }}>
        <div>
          <h1 style={{ fontSize: "28px", fontWeight: "700", margin: "0 0 6px" }}>90-Day Cash Flow Forecast</h1>
          <p style={{ color: "#64748b", fontSize: "14px", margin: 0 }}>
            Intelligence-led projection of your liquidity through Nov 2024.{" "}
            <span style={{ color: "#1d4ed8", cursor: "pointer" }}>Plan with precision, not guesswork.</span>
          </p>
        </div>
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: "10px", color: "#94a3b8", fontWeight: "600" }}>CURRENT BALANCE</div>
            <div style={{ fontSize: "20px", fontWeight: "700" }}>₹ 42,10,250</div>
          </div>
          <div style={{
            backgroundColor: "#0d9488", color: "white", borderRadius: "8px",
            padding: "10px 16px", textAlign: "center",
          }}>
            <div style={{ fontSize: "10px", fontWeight: "600" }}>FORECAST HEALTH</div>
            <div style={{ fontSize: "16px", fontWeight: "700" }}>Optimized</div>
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: "24px" }}>
        {/* Left */}
        <div>
          {/* Chart */}
          <div style={{ backgroundColor: "#fff", borderRadius: "12px", border: "1px solid #e2e8f0", padding: "24px", marginBottom: "20px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
              <div>
                <div style={{ fontWeight: "600", fontSize: "15px" }}>Liquidity Projection</div>
                <div style={{ fontSize: "12px", color: "#94a3b8" }}>Projected closing balance per day</div>
              </div>
              <div style={{ display: "flex", gap: "6px" }}>
                {["Daily", "Weekly"].map((v) => (
                  <button key={v} style={{
                    padding: "4px 10px", fontSize: "12px", borderRadius: "4px", cursor: "pointer",
                    border: v === "Daily" ? "none" : "1px solid #e2e8f0",
                    backgroundColor: v === "Daily" ? "#0f172a" : "transparent",
                    color: v === "Daily" ? "white" : "#64748b",
                  }}>{v}</button>
                ))}
              </div>
            </div>

            {/* SVG line chart simulation */}
            <div style={{ position: "relative", height: "200px", backgroundColor: "#f8fafc", borderRadius: "8px", overflow: "hidden" }}>
              <svg viewBox="0 0 600 200" style={{ width: "100%", height: "100%" }}>
                {/* Confidence band */}
                <path d="M0,140 C100,130 150,160 200,150 C250,140 280,170 300,175 C350,180 400,120 450,80 C500,50 550,40 600,35"
                  fill="none" stroke="#1e3a8a" strokeWidth="2.5" />
                {/* Danger zone dot */}
                <circle cx="300" cy="175" r="5" fill="#dc2626" />
                {/* Tooltip */}
                <rect x="180" y="155" width="130" height="38" fill="#0f172a" rx="6" />
                <text x="245" y="170" textAnchor="middle" fill="#94a3b8" fontSize="9">AUG 24, 2024</text>
                <text x="245" y="185" textAnchor="middle" fill="#0d9488" fontSize="11" fontWeight="bold">Projected: ₹68,40,000</text>
                {/* Cash flow label */}
                <text x="300" y="198" textAnchor="middle" fill="#dc2626" fontSize="9">CASH FLOW SEP 18</text>
              </svg>
            </div>

            {/* KPIs */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0", marginTop: "16px", borderTop: "1px solid #f1f5f9", paddingTop: "16px" }}>
              {[
                { label: "RUNWAY", value: "14.2 Months" },
                { label: "NET CASH CHANGE", value: "+₹12,45,000", color: "#16a34a" },
                { label: "BURN RATE", value: "₹3.2L / mo" },
              ].map((k) => (
                <div key={k.label} style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "10px", color: "#94a3b8", fontWeight: "600" }}>{k.label}</div>
                  <div style={{ fontSize: "15px", fontWeight: "700", color: k.color || "#0f172a", marginTop: "4px" }}>{k.value}</div>
                </div>
              ))}
            </div>
            <div style={{ textAlign: "right", marginTop: "8px" }}>
              <span style={{ fontSize: "12px", color: "#1d4ed8", cursor: "pointer" }}>View Detailed Ledgers →</span>
            </div>
          </div>

          {/* Inflows / Outflows */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            {[
              { title: "CRITICAL INFLOWS", items: inflows, color: "#16a34a", icon: "↓" },
              { title: "PLANNED OUTFLOWS", items: outflows, color: "#dc2626", icon: "↑" },
            ].map((section) => (
              <div key={section.title} style={{ backgroundColor: "#fff", borderRadius: "10px", border: "1px solid #e2e8f0", padding: "16px" }}>
                <div style={{ fontSize: "10px", color: "#94a3b8", fontWeight: "600", letterSpacing: "0.08em", marginBottom: "12px" }}>{section.title}</div>
                {section.items.map((item) => (
                  <div key={item.name} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 0", borderBottom: "1px solid #f8fafc" }}>
                    <div>
                      <div style={{ fontSize: "12px", fontWeight: "600" }}>{item.name}</div>
                      <div style={{ fontSize: "11px", color: "#94a3b8" }}>{item.date}</div>
                    </div>
                    <div style={{ fontSize: "13px", fontWeight: "700", color: section.color }}>{item.amount}</div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* Right — Scenario Simulator */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ backgroundColor: "#fff", borderRadius: "10px", border: "1px solid #e2e8f0", padding: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
              <div style={{ fontWeight: "600", fontSize: "14px" }}>SCENARIO SIMULATOR</div>
              <span style={{ color: "#94a3b8", fontSize: "16px" }}>⊞</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {scenarios.map((s) => (
                <div key={s.label} style={{ backgroundColor: "#f8fafc", borderRadius: "8px", padding: "12px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: "13px", fontWeight: "600" }}>{s.label}</div>
                      <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "2px" }}>{s.sub}</div>
                      {s.impact && <div style={{ fontSize: "11px", color: "#0d9488", marginTop: "4px", backgroundColor: "#d1fae5", padding: "2px 6px", borderRadius: "4px", display: "inline-block" }}>{s.impact}</div>}
                    </div>
                    {/* Toggle */}
                    <div style={{
                      width: "36px", height: "20px", borderRadius: "10px", flexShrink: 0, marginLeft: "10px",
                      backgroundColor: s.enabled ? "#0f172a" : "#e2e8f0", position: "relative", cursor: "pointer",
                    }}>
                      <div style={{
                        position: "absolute", top: "2px",
                        left: s.enabled ? "18px" : "2px",
                        width: "16px", height: "16px",
                        borderRadius: "50%", backgroundColor: "white",
                        transition: "left 0.2s",
                      }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <button style={{
              width: "100%", marginTop: "12px",
              backgroundColor: "#0f172a", color: "white", border: "none",
              borderRadius: "6px", padding: "10px", fontSize: "13px", fontWeight: "600", cursor: "pointer",
            }}>⊕ Add New Variable</button>
          </div>

          {/* AI Risk Alert */}
          <div style={{ backgroundColor: "#0f172a", borderRadius: "10px", padding: "16px", color: "white" }}>
            <div style={{ fontSize: "11px", color: "#0d9488", fontWeight: "600", marginBottom: "8px" }}>⚡ AI RISK ALERT</div>
            <div style={{ fontSize: "12px", color: "#cbd5e1", marginBottom: "12px" }}>
              You have a potential cash deficit on{" "}
              <span style={{ color: "#fbbf24" }}>September 18th</span>{" "}
              due to seasonal payroll spikes. Consider invoice discounting for invoice #8841.
            </div>
            <button style={{
              padding: "7px 14px", backgroundColor: "transparent",
              border: "1px solid #0d9488", color: "#0d9488",
              borderRadius: "6px", fontSize: "12px", fontWeight: "600", cursor: "pointer",
            }}>OPTIMIZE NOW →</button>
          </div>

          {/* Predictive Accuracy */}
          <div style={{ backgroundColor: "#fff", borderRadius: "10px", border: "1px solid #e2e8f0", padding: "16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontSize: "10px", color: "#94a3b8", fontWeight: "600" }}>PREDICTIVE ACCURACY</div>
              <div style={{ fontSize: "28px", fontWeight: "700", color: "#0f172a", marginTop: "4px" }}>98.4%</div>
            </div>
            <div style={{ fontSize: "20px", color: "#94a3b8" }}>+</div>
          </div>
        </div>
      </div>
    </div>
  );
}
