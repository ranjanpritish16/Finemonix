export default function IntegrationsPage() {
  return (
    <div style={{ fontFamily: "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif" }}>
    <div style={{ display: "flex", padding: "24px", flexDirection: "row", gap: "16px" }}>
      <div style={{ width: "200px", height: "100px" }}></div>
      <div style={{ width: "70%", padding: "16px" }}>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <h1 style={{ margin: "0 0 6px", fontSize: "26px", fontWeight: 700, color: "#111827", lineHeight: 1.3, letterSpacing: "-0.01em" }}>Data <span style={{color: "#16a34a"}}>Hub</span></h1>
            <p style={{ margin: 0, fontSize: "13px", fontWeight: 400, color: "#6b7280", lineHeight: 1.5 }}>Centralize your business intelligence by integrating bank statements, ERP records, and accounting software.</p>
          </div>

          <button style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            backgroundColor: "#00c48c",
            color: "#fff",
            border: "none",
            borderRadius: "8px",
            padding: "10px 16px",
            fontSize: "13px",
            fontWeight: 500,
            cursor: "pointer",
            whiteSpace: "nowrap",
            flexShrink: 0,
          }}>
            ✦ AI Processing Active
          </button>
        </div>

      </div>
    </div>
    <div style={{ display: "flex", padding: "24px", flexDirection: "row", gap: "16px" }}>
      <div style={{ width: "250px", height: "100px" }}></div>
      <div style={{display:"flex",padding:"12px",flexDirection:"column",gap:"16px"}}>
        <div style={{padding: "16px", backgroundColor:"white",borderRadius:"20px" }}>
          <div style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: "24px",
            gap: "16px",
            textAlign: "center",
          }}>

            {/* Cloud upload icon */}
            <div style={{
              width: "60px", height: "60px",
              borderRadius: "50%",
              backgroundColor: "#e8f4fd",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#5aabf7" strokeWidth="1.8">
                <polyline points="16 16 12 12 8 16" />
                <line x1="12" y1="12" x2="12" y2="21" />
                <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
              </svg>
            </div>

            {/* Title + description */}
            <div>
              <h3 style={{ margin: "0 0 6px", fontSize: "14px", fontWeight: 600, color: "#111827", letterSpacing: "-0.01em" }}>
                Upload Financial Files
              </h3>
              <p style={{ margin: 0, fontSize: "12px", fontWeight: 400, color: "#6b7280", maxWidth: "380px", lineHeight: 1.5 }}>
                Drag and drop Tally XML, GST JSON, Bank CSV, or PDF files here. We'll automatically extract and categorize the data.
              </p>
            </div>

            {/* Buttons */}
            <div style={{ display: "flex", gap: "12px" }}>
              <button style={{
                display: "flex", alignItems: "center", gap: "7px",
                backgroundColor: "#1e2a4a", color: "#fff",
                border: "none", borderRadius: "8px",
                padding: "10px 20px", fontSize: "13px", fontWeight: 500, cursor: "pointer",
              }}>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                Browse Files
              </button>

              <button style={{
                display: "flex", alignItems: "center", gap: "7px",
                backgroundColor: "#e8f9f4", color: "#00c48c",
                border: "1px solid #b2edd8", borderRadius: "8px",
                padding: "10px 20px", fontSize: "13px", fontWeight: 500, cursor: "pointer",
              }}>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/>
                </svg>
                Direct API
              </button>
            </div>

            {/* Supported sources */}
            <div style={{ display: "flex", gap: "20px", marginTop: "4px" }}>
              {["Tally Prime", "GST Portal", "Bank Feeds"].map(label => (
                <span key={label} style={{
                  display: "flex", alignItems: "center", gap: "5px",
                  fontSize: "11px", fontWeight: 500, color: "#9ca3af", letterSpacing: "0.03em",
                }}>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" strokeWidth="2.5">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  {label}
                </span>
              ))}
            </div>

          </div>
        </div>
        <div style={{height:"300px"}}>
          {/* Recent Activity Card */}
          <div style={{
            backgroundColor: "#e3eef7",
            borderRadius: "12px",
            padding: "20px",
            marginTop: "16px",
          }}>

            {/* Header */}
            <p style={{ margin: "0 0 16px", fontSize: "11px", fontWeight: 600, letterSpacing: "0.07em", textTransform: "uppercase" }}>
              Recent Activity
            </p>

            {[
              {
                type: "XML",
                typeColor: "#00c48c",
                typeBg: "#e6faf3",
                name: "Tally_Export_Q3.xml",
                meta: "4.2 MB • Processing Ledger Entries",
                status: "progress",
              },
              {
                type: "PDF",
                typeColor: "#6b7280",
                typeBg: "#f3f4f6",
                name: "HDFC_Current_Oct23.pdf",
                meta: "1.1 MB • Completed 2 mins ago",
                status: "done",
              },
            ].map((file, i) => (
              <div key={i} style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                padding: "12px",
                borderRadius: "8px",
                backgroundColor: "#f9fafb",
                marginBottom: i === 0 ? "8px" : "0",
              }}>

                <div style={{
                  width: "40px", height: "40px",
                  borderRadius: "8px",
                  backgroundColor: file.typeBg,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "10px", fontWeight: 700,
                  color: file.typeColor,
                  flexShrink: 0,
                }}>
                  {file.type}
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ margin: "0 0 3px", fontSize: "13px", fontWeight: 500, color: "#111827" }}>
                    {file.name}
                  </p>
                  <p style={{ margin: 0, fontSize: "12px", fontWeight: 400, color: "#9ca3af" }}>
                    {file.meta}
                  </p>
                </div>

                {file.status === "progress" ? (
                  <div style={{ width: "80px", height: "4px", backgroundColor: "#e5e7eb", borderRadius: "2px", flexShrink: 0 }}>
                    <div style={{ width: "55%", height: "100%", backgroundColor: "#1e2a4a", borderRadius: "2px" }} />
                  </div>
                ) : (
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" style={{flexShrink:"0"}}>
                    <circle cx="12" cy="12" r="10" fill="#e6faf3"/>
                    <polyline points="8 12 11 15 16 9" stroke="#00c48c" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                )}

              </div>
            ))}

          </div>
        </div>
      </div>
      <div style={{}}>
        {/* Right Column — Connected Sources Card */}
        <div style={{
          backgroundColor: "#d6e8f5",
          borderRadius: "12px",
          padding: "20px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
        }}>

          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <p style={{ margin: 0, fontSize: "13px", fontWeight: 600, color: "#111827", letterSpacing: "-0.01em" }}>
                Connected Sources
              </p>
              <span style={{ fontSize: "12px", fontWeight: 400, color: "#6b7280", cursor: "pointer" }}>Manage All</span>
            </div>

            {[
              {
                icon: "🏦",
                iconBg: "#e8f0fe",
                name: "HDFC Bank • • 4902",
                meta: "Last sync: 15 mins ago",
                status: "LIVE SYNC",
                statusColor: "#00c48c",
                statusBg: "#e6faf3",
              },
              {
                icon: "📚",
                iconBg: "#fff0e6",
                name: "Zoho Books Integration",
                meta: "Last sync: Today, 08:30 AM",
                status: "LIVE SYNC",
                statusColor: "#00c48c",
                statusBg: "#e6faf3",
              },
              {
                icon: "💳",
                iconBg: "#f3f4f6",
                name: "Razorpay X",
                meta: "Token expired 2 days ago",
                status: "RE-AUTH REQUIRED",
                statusColor: "#ef4444",
                statusBg: "#fef2f2",
              },
            ].map((source, i, arr) => (
              <div key={i} style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                padding: "12px",
                borderRadius: "8px",
                backgroundColor: "#fff",
                marginBottom: i < arr.length - 1 ? "8px" : "0",
              }}>

                <div style={{
                  width: "38px", height: "38px",
                  borderRadius: "8px",
                  backgroundColor: source.iconBg,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "18px",
                  flexShrink: 0,
                }}>
                  {source.icon}
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ margin: "0 0 3px", fontSize: "13px", fontWeight: 500, color: "#111827" }}>
                    {source.name}
                  </p>
                  <p style={{ margin: 0, fontSize: "11px", fontWeight: 400, color: "#9ca3af" }}>
                    {source.meta}
                  </p>
                </div>

                <span style={{
                  fontSize: "10px",
                  fontWeight: 600,
                  color: source.statusColor,
                  backgroundColor: source.statusBg,
                  padding: "3px 8px",
                  borderRadius: "20px",
                  whiteSpace: "nowrap",
                  flexShrink: 0,
                  letterSpacing: "0.04em",
                }}>
                  {source.status}
                </span>

              </div>
            ))}
          </div>

          {/* Bottom — Add Accounting Software */}
          <div style={{
            marginTop: "16px",
            backgroundColor: "#1e2a4a",
            borderRadius: "12px",
            padding: "20px",
            position: "relative",
            overflow: "hidden",
          }}>

            <div style={{
              position: "absolute", right: "-20px", top: "-20px",
              width: "100px", height: "100px",
              borderRadius: "50%",
              backgroundColor: "rgba(255,255,255,0.04)",
            }} />
            <div style={{
              position: "absolute", right: "20px", bottom: "-30px",
              width: "80px", height: "80px",
              borderRadius: "50%",
              backgroundColor: "rgba(255,255,255,0.04)",
            }} />

            <p style={{ margin: "0 0 6px", fontSize: "14px", fontWeight: 600, color: "#fff", letterSpacing: "-0.01em" }}>
              Add Accounting Software
            </p>
            <p style={{ margin: "0 0 16px", fontSize: "12px", fontWeight: 400, color: "#94a3b8", lineHeight: 1.5 }}>
              Directly sync with Tally Cloud, QuickBooks, or Zoho for real-time risk monitoring.
            </p>

            <button style={{
              backgroundColor: "#00c48c",
              color: "#fff",
              border: "none",
              borderRadius: "8px",
              padding: "8px 16px",
              fontSize: "13px",
              fontWeight: 500,
              cursor: "pointer",
            }}>
              Configure API
            </button>

          </div>

        </div>
        </div>
      </div>
    </div>
  );
}