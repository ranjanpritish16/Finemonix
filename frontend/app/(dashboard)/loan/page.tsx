export default function LoanPage() {
  const influenceFactors = [
    { icon: "📊", label: "Revenue Stability", sub: "Consistency over last 12 months", status: "PASS", statusColor: "#16a34a", statusBg: "#dcfce7", value: "+14.2% YoY" },
    { icon: "🏛", label: "Debt-to-Income", sub: "Operational leverage ratio", status: "PASS", statusColor: "#16a34a", statusBg: "#dcfce7", value: "0.74 Ratio" },
    { icon: "⚠", label: "Client Concentration", sub: "Revenue dependency on top 3 clients", status: "NEEDS IMPROVEMENT", statusColor: "#dc2626", statusBg: "#fee2e2", value: "62% Exposure" },
  ];

  const lenders = [
    { name: "Apex Capital Corp", type: "Unsecured Term Loan", match: "95% MATCH", matchBg: "#1e3a8a", interestRate: "4.2% – 6.8%", maxAmount: "$2,500,000" },
    { name: "BlueStone Venture", type: "Revenue Based Finance", match: "92% MATCH", matchBg: "#1e3a8a", feeRate: "1.2% / Month", fundingSpeed: "48 Hours" },
    { name: "ScaleUp Credit", type: "SBA / A1 Preferred", match: "84% MATCH", matchBg: "#475569", interestRate: "Prime + 2.5%", collateral: "Not Required" },
  ];

  return (
    <div style={{ maxWidth: "1200px" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "28px" }}>
        <div>
          <h1 style={{ fontSize: "28px", fontWeight: "700", margin: "0 0 4px" }}>Loan Eligibility Analyzer</h1>
          <p style={{ color: "#64748b", fontSize: "13px", margin: 0 }}>Real-time creditworthiness projection based on AI modeling</p>
        </div>
        <div style={{
          display: "flex", alignItems: "center", gap: "6px",
          backgroundColor: "#dbeafe", borderRadius: "20px", padding: "6px 14px",
          fontSize: "12px", fontWeight: "600", color: "#1d4ed8",
        }}>✦ AI ENGINE ACTIVE</div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginBottom: "28px" }}>
        {/* Credit Probability Gauge */}
        <div style={{ backgroundColor: "#fff", borderRadius: "12px", border: "1px solid #e2e8f0", padding: "28px", textAlign: "center" }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "20px" }}>
            <div style={{ fontWeight: "600", fontSize: "15px" }}>Credit Probability</div>
            <div style={{ fontSize: "11px", color: "#94a3b8" }}>UPDATED 2M AGO</div>
          </div>

          {/* SVG Gauge */}
          <svg viewBox="0 0 200 120" style={{ width: "240px", height: "140px" }}>
            {/* Background arc */}
            <path d="M20,100 A80,80 0 0,1 180,100" fill="none" stroke="#f1f5f9" strokeWidth="16" strokeLinecap="round" />
            {/* Score arc — 84% of 180° = ~151° */}
            <path d="M20,100 A80,80 0 0,1 175,27" fill="none" stroke="#0f172a" strokeWidth="16" strokeLinecap="round" />
            {/* Score */}
            <text x="100" y="92" textAnchor="middle" fontSize="32" fontWeight="800" fill="#0f172a">84%</text>
            <rect x="55" y="97" width="90" height="18" rx="9" fill="#16a34a" />
            <text x="100" y="110" textAnchor="middle" fontSize="9" fontWeight="700" fill="white">HIGH RELIABILITY</text>
          </svg>

          <div style={{ fontSize: "13px", color: "#64748b", marginTop: "12px", lineHeight: 1.5 }}>
            Your business shows strong revenue resilience.
            <br />You are currently in the{" "}
            <span style={{ color: "#1d4ed8", fontWeight: "600" }}>Top 12% of applicants</span>{" "}in your sector.
          </div>
        </div>

        {/* Influence Factors */}
        <div style={{ backgroundColor: "#fff", borderRadius: "12px", border: "1px solid #e2e8f0", padding: "24px" }}>
          <div style={{ fontWeight: "600", fontSize: "15px", marginBottom: "16px" }}>Influence Factors</div>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {influenceFactors.map((f) => (
              <div key={f.label} style={{ border: "1px solid #f1f5f9", borderRadius: "10px", padding: "14px", display: "flex", alignItems: "center", gap: "14px" }}>
                <div style={{ fontSize: "22px" }}>{f.icon}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div>
                      <div style={{ fontWeight: "600", fontSize: "13px" }}>{f.label}</div>
                      <div style={{ fontSize: "11px", color: "#94a3b8" }}>{f.sub}</div>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      <div style={{ fontSize: "10px", fontWeight: "700", color: f.statusColor, backgroundColor: f.statusBg, padding: "2px 7px", borderRadius: "4px", marginBottom: "4px" }}>{f.status}</div>
                      <div style={{ fontSize: "12px", fontWeight: "600", color: "#0f172a" }}>{f.value}</div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recommended Lenders */}
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div style={{ fontWeight: "700", fontSize: "18px" }}>Recommended Lenders</div>
          <span style={{ fontSize: "13px", color: "#1d4ed8", cursor: "pointer", fontWeight: "600" }}>View Marketplace →</span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px" }}>
          {lenders.map((lender) => (
            <div key={lender.name} style={{ backgroundColor: "#fff", borderRadius: "10px", border: "1px solid #e2e8f0", padding: "20px" }}>
              <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "10px" }}>
                <div style={{ backgroundColor: lender.matchBg, color: "white", fontSize: "10px", fontWeight: "700", padding: "3px 8px", borderRadius: "4px" }}>{lender.match}</div>
              </div>
              <div style={{ width: "36px", height: "36px", backgroundColor: "#f1f5f9", borderRadius: "8px", marginBottom: "10px" }} />
              <div style={{ fontWeight: "700", fontSize: "15px", marginBottom: "2px" }}>{lender.name}</div>
              <div style={{ fontSize: "12px", color: "#1d4ed8", marginBottom: "14px" }}>{lender.type}</div>
              <div style={{ borderTop: "1px solid #f1f5f9", paddingTop: "12px", display: "flex", flexDirection: "column", gap: "6px" }}>
                {lender.interestRate && (
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px" }}>
                    <span style={{ color: "#94a3b8" }}>Interest Rate</span>
                    <span style={{ fontWeight: "600" }}>{lender.interestRate}</span>
                  </div>
                )}
                {lender.feeRate && (
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px" }}>
                    <span style={{ color: "#94a3b8" }}>Fee Rate</span>
                    <span style={{ fontWeight: "600" }}>{lender.feeRate}</span>
                  </div>
                )}
                {lender.maxAmount && (
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px" }}>
                    <span style={{ color: "#94a3b8" }}>Max Amount</span>
                    <span style={{ fontWeight: "600" }}>{lender.maxAmount}</span>
                  </div>
                )}
                {lender.fundingSpeed && (
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px" }}>
                    <span style={{ color: "#94a3b8" }}>Funding Speed</span>
                    <span style={{ fontWeight: "600" }}>{lender.fundingSpeed}</span>
                  </div>
                )}
                {lender.collateral && (
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px" }}>
                    <span style={{ color: "#94a3b8" }}>Collateral</span>
                    <span style={{ fontWeight: "600" }}>{lender.collateral}</span>
                  </div>
                )}
              </div>
              <button style={{
                width: "100%", marginTop: "14px", padding: "9px",
                backgroundColor: "#0f172a", color: "white", border: "none",
                borderRadius: "6px", fontSize: "13px", fontWeight: "600", cursor: "pointer",
              }}>Apply Now</button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
