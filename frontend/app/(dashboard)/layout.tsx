import Sidebar from "@/components/shared/layout/Sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar />
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {/* Topbar */}
        <header style={{
          height: "52px",
          backgroundColor: "#ffffff",
          borderBottom: "1px solid #e2e8f0",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 24px",
          flexShrink: 0,
        }}>
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            backgroundColor: "#f8fafc",
            border: "1px solid #e2e8f0",
            borderRadius: "6px",
            padding: "6px 12px",
            width: "240px",
          }}>
            <span style={{ color: "#94a3b8", fontSize: "13px" }}>🔍 Search insights...</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <span style={{ fontSize: "18px", cursor: "pointer" }}>🔔</span>
            <span style={{ fontSize: "18px", cursor: "pointer" }}>⚙</span>
            <div style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              fontSize: "13px",
              fontWeight: "500",
              color: "#1e293b",
            }}>
              <div style={{
                width: "32px", height: "32px",
                backgroundColor: "#1d4ed8",
                borderRadius: "50%",
                display: "flex", alignItems: "center", justifyContent: "center",
                color: "white", fontSize: "13px", fontWeight: "700",
              }}>A</div>
              Alex Sterling
            </div>
          </div>
        </header>
        {/* Page content */}
        <main style={{ flex: 1, overflowY: "auto", padding: "28px 28px" }}>
          {children}
        </main>
      </div>
    </div>
  );
}
