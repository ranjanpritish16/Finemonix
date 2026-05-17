export default function Loading() {
  return (
    <div style={{
      display: "flex", alignItems: "center", justifyContent: "center",
      height: "60vh", flexDirection: "column", gap: "16px",
    }}>
      <div style={{
        width: "36px", height: "36px",
        border: "3px solid #e2e8f0", borderTop: "3px solid #1d4ed8",
        borderRadius: "50%", animation: "spin 0.8s linear infinite",
      }} />
      <div style={{ color: "#94a3b8", fontSize: "13px" }}>Loading...</div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
