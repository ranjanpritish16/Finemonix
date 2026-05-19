export default function IntegrationsPage() {
  return (
    <>
    <div style={{ display: "flex", padding: "24px", flexDirection: "row", gap: "16px" }}>
      <div style={{ width: "100px", height: "100px" }}></div>
      <div style={{ width: "70%", padding: "16px" }}>

        {/* Add this wrapper around the title block */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <h1>Data Hub</h1>
            <p>Centralize your business intelligence by integrating bank statements, ERP records, and accounting software.</p>
          </div>

          {/* The button */}
          <button style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            backgroundColor: "#00c48c",
            color: "#fff",
            border: "none",
            borderRadius: "8px",
            padding: "10px 16px",
            fontSize: "14px",
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
    <div style={{ display: "flex", padding: "24px", flexDirection: "row", gap: "16px", height:"60%" }}>
      <div style={{ width: "100px", height: "100px" }}></div>
      <div style={{ width: "70%", padding: "16px", backgroundColor:"white" }}></div>
    </div>
    </>
  );
}