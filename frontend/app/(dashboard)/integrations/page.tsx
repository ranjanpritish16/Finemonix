export default function IntegrationsPage() {
  const connectedSources = [
    { name: "HDFC Bank ++ 4902", sub: "Last sync: 15 mins ago", status: "LIVE SYNC", statusColor: "#16a34a", icon: "🏦", iconBg: "#dbeafe" },
    { name: "Zoho Books Integration", sub: "Last sync: Today, 08:30 AM", status: "LIVE SYNC", statusColor: "#16a34a", icon: "Z", iconBg: "#fef3c7" },
    { name: "Razorpay X", sub: "Token expired: 2 days ago", status: "RE-AUTH REQUIRED", statusColor: "#dc2626", icon: "R", iconBg: "#f1f5f9" },
  ];

  const recentActivity = [
    { type: "XML", name: "Tally_Export_Q3.xml", size: "4.2MB", status: "Processing Ledger for links", progress: 55 },
    { type: "PDF", name: "HDFC_Current_Oct23.pdf", size: "1.8MB", status: "Completed: 2 mins ago", progress: 100 },
  ];

  return (
    <div style={{ maxWidth: "1200px" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "28px" }}>
        <div>
          <h1 style={{ fontSize: "28px", fontWeight: "700", margin: "0 0 6px" }}>Data Hub</h1>
          <p style={{ color: "#64748b", fontSize: "14px", margin: 0 }}>
            Centralize your business intelligence by integrating bank statements,
            <br />ERP records, and accounting software.
          </p>
        </div>
        <div style={{
          display: "flex", alignItems: "center", gap: "8px",
          backgroundColor: "#d1fae5", border: "1px solid #6ee7b7",
          borderRadius: "20px", padding: "7px 14px", fontSize: "12px", fontWeight: "600", color: "#065f46",
        }}>
          ✦ AI Processing Active
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: "24px" }}>
        {/* Left */}
        <div>
          {/* Upload zone */}
          <div style={{
            backgroundColor: "#fff", border: "2px dashed #cbd5e1",
            borderRadius: "12px", padding: "40px 24px", textAlign: "center", marginBottom: "24px",
          }}>
            <div style={{ fontSize: "48px", marginBottom: "12px" }}>☁</div>
            <div style={{ fontWeight: "600", fontSize: "18px", marginBottom: "8px" }}>Upload Financial Files</div>
            <div style={{ color: "#64748b", fontSize: "13px", marginBottom: "20px", maxWidth: "360px", margin: "0 auto 20px" }}>
              Drag and drop Tally XML, GST JSON, Bank CSV, or PDF files here. We'll automatically extract and categorize the data.
            </div>
            <div style={{ display: "flex", gap: "10px", justifyContent: "center" }}>
              <button style={{
                backgroundColor: "#0f172a", color: "white", border: "none",
                borderRadius: "6px", padding: "9px 18px", fontSize: "13px", fontWeight: "600", cursor: "pointer",
              }}>📎 Browse Files</button>
              <button style={{
                backgroundColor: "#eff6ff", color: "#1d4ed8", border: "1px solid #bfdbfe",
                borderRadius: "6px", padding: "9px 18px", fontSize: "13px", fontWeight: "600", cursor: "pointer",
              }}>✦ Direct API</button>
            </div>
            <div style={{ display: "flex", gap: "20px", justifyContent: "center", marginTop: "14px", color: "#94a3b8", fontSize: "12px" }}>
              <span>○ TALLY PRIME</span>
              <span>○ GST PORTAL</span>
              <span>○ BANK FEEDS</span>
            </div>
          </div>

          {/* Recent activity */}
          <div style={{ backgroundColor: "#fff", borderRadius: "10px", border: "1px solid #e2e8f0", padding: "20px" }}>
            <div style={{ fontWeight: "600", fontSize: "13px", letterSpacing: "0.05em", color: "#64748b", marginBottom: "14px" }}>RECENT ACTIVITY</div>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {recentActivity.map((file) => (
                <div key={file.name} style={{ display: "flex", alignItems: "center", gap: "14px", padding: "12px", border: "1px solid #f1f5f9", borderRadius: "8px" }}>
                  <div style={{
                    width: "36px", height: "36px", borderRadius: "6px",
                    backgroundColor: file.type === "XML" ? "#dcfce7" : "#fee2e2",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: "10px", fontWeight: "700", color: file.type === "XML" ? "#16a34a" : "#dc2626",
                  }}>{file.type}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: "600", fontSize: "13px" }}>{file.name}</div>
                    <div style={{ fontSize: "12px", color: "#64748b" }}>{file.size} • {file.status}</div>
                    <div style={{ marginTop: "6px", height: "4px", backgroundColor: "#f1f5f9", borderRadius: "2px" }}>
                      <div style={{ height: "100%", width: `${file.progress}%`, backgroundColor: file.progress === 100 ? "#16a34a" : "#1d4ed8", borderRadius: "2px" }} />
                    </div>
                  </div>
                  {file.progress === 100 && <span style={{ color: "#16a34a", fontSize: "18px" }}>✓</span>}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ backgroundColor: "#fff", borderRadius: "10px", border: "1px solid #e2e8f0", padding: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
              <div style={{ fontWeight: "600", fontSize: "14px" }}>Connected Sources</div>
              <div style={{ fontSize: "12px", color: "#1d4ed8", cursor: "pointer", fontWeight: "600" }}>Manage All</div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {connectedSources.map((src) => (
                <div key={src.name} style={{ display: "flex", alignItems: "center", gap: "10px", padding: "10px", backgroundColor: "#f8fafc", borderRadius: "8px" }}>
                  <div style={{ width: "32px", height: "32px", borderRadius: "6px", backgroundColor: src.iconBg, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "14px" }}>{src.icon}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: "12px", fontWeight: "600" }}>{src.name}</div>
                    <div style={{ fontSize: "11px", color: "#94a3b8" }}>{src.sub}</div>
                  </div>
                  <div style={{ fontSize: "10px", fontWeight: "700", color: src.statusColor, backgroundColor: src.statusColor === "#16a34a" ? "#dcfce7" : "#fee2e2", padding: "2px 6px", borderRadius: "4px" }}>{src.status}</div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ backgroundColor: "#0f172a", borderRadius: "10px", padding: "20px", color: "white" }}>
            <div style={{ fontWeight: "600", fontSize: "14px", marginBottom: "8px" }}>Add Accounting Software</div>
            <div style={{ fontSize: "12px", color: "#94a3b8", marginBottom: "16px" }}>
              Directly sync with Tally Cloud, QuickBooks, or Zoho for real-time risk monitoring.
            </div>
            <button style={{
              width: "100%", padding: "9px", backgroundColor: "transparent",
              border: "1px solid #334155", color: "white", borderRadius: "6px",
              fontSize: "13px", fontWeight: "600", cursor: "pointer",
            }}>Configure API</button>
          </div>
        </div>
      </div>
    </div>
  );
}
