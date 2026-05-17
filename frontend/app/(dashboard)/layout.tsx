import Sidebar from "@/components/shared/layout/Sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", minHeight: "100vh", backgroundColor: "#ffffff" }}>
      <Sidebar />
      <div style={{ flex: 1, display: "flex", flexDirection: "column", backgroundColor: "#f0f4f8" }}>
        <header style={{ height: "52px", borderBottom: "1px solid #e2e8f0", display: "flex", alignItems: "center", padding: "0 24px", backgroundColor: "#ffffff" }}>
          <input
            type="text"
            placeholder="Search insights..."
            style={{ width: "240px", padding: "6px 14px", backgroundColor: "#f1f5f9", border: "1px solid #e2e8f0", borderRadius: "20px", fontSize: "13px", outline: "none" }}
          />
        </header>
        <main style={{ flex: 1, backgroundColor: "#f0f4f8" }}>{children}</main>
      </div>
    </div>
  );
}
