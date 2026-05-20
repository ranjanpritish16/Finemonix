export default function CashFlowPage() {
  return (
    /* 1. This outer wrapper ensures that if the window is smaller than 1200px, 
         the browser will create a scrollbar instead of squeezing the content.
    */
    <div style={{ width: "100%", overflowX: "auto" }}>
      
      {/* 2. Set a hard minimum width on the page layout wrapper. 
           This locks the positions and sizes of everything inside it.
      */}
      <div style={{ minWidth: "1200px", padding: "24px" }}>
        
        {/* Header Row */}
        <div style={{ display: "flex", flexDirection: "row", alignItems: "flex-end" }}>
          
          {/* Strict absolute widths ensure text doesn't wrap awkwardly */}
          <div style={{ width: "700px" }}>
            <h1 style={{ fontFamily: "system-ui", fontSize: "35px", margin: "0 0 10px 0" }}>
              90-Day Cash Flow <span style={{ color: "#16a34a" }}>Forecast</span>
            </h1>
            <p style={{ fontSize: "15px", margin: 0 }}>
              Intelligence-led projection of your liquidity through Nov 2024. Plan with precision, not guesswork.
            </p>
          </div>   
          
          {/* Card 1: Current Balance */}
          <div style={{
            width:"130px",
            gap:"2.5px", 
            backgroundColor: "white", 
            marginLeft: "auto", 
            display: "flex", 
            flexDirection: "column", 
            justifyContent: "center", 
            alignItems: "center", 
            borderRadius: "20px", 
            height: "60px" 
          }}>
            <p style={{ margin: "0", fontSize: "8px", color: "#555", fontWeight: "bold", letterSpacing: "0.5px" }}>
              CURRENT BALANCE
            </p>
            <h1 style={{ margin: 0, fontSize: "16px", color: "#001a4d" }}>₹ 42,10,250</h1>
          </div>
          
          {/* Card 2: Forecast Health */}
          <div style={{
            width: "130px",
            gap:"2.5px", 
            backgroundColor: "cyan", 
            marginLeft: "24px", // Fixed spacing instead of auto to keep them side-by-side
            display: "flex", 
            flexDirection: "column", 
            justifyContent: "center", 
            alignItems: "center", 
            borderRadius: "20px", 
            height: "60px"
          }}>
            <p style={{ margin: "0", fontSize: "8px", color: "#555", fontWeight: "bold", letterSpacing: "0.5px" }}>
              FORECAST HEALTH
            </p>
            <h1 style={{ margin: 0, fontSize: "16px", color: "#001a4d" }}>Optimized</h1>
          </div> 
          
        </div>

        {/* Lower Dashboard Section */}
        <div style={{ display: "flex", flexDirection: "column", marginTop: "40px" }}>
           {/* Your charts will go here and will also respect the 1200px minimum width constraint */}
        </div>

      </div>
    </div>
  );
}