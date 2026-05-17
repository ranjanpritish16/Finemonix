"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/dashboard",     label: "Dashboard",     icon: "⊞" },
  { href: "/integrations",  label: "Integrations",  icon: "⇄" },
  { href: "/cashflow",      label: "Cash Flow",     icon: "↗" },
  { href: "/loan",          label: "Loan Analyzer", icon: "⬡" },
  { href: "/watchlist",     label: "Risk Monitor",  icon: "⚑" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside style={{
      width: "220px",
      minHeight: "100vh",
      backgroundColor: "var(--sidebar-bg)",
      display: "flex",
      flexDirection: "column",
      flexShrink: 0,
    }}>
      {/* Logo */}
      <div style={{ padding: "20px 16px 16px", borderBottom: "1px solid #1e293b" }}>
        <div style={{
          backgroundColor: "#1d4ed8",
          borderRadius: "8px",
          padding: "6px 10px",
          display: "inline-flex",
          alignItems: "center",
          gap: "8px",
          marginBottom: "4px",
        }}>
          <span style={{ color: "white", fontWeight: "700", fontSize: "15px" }}>NeevFinance</span>
        </div>
        <div style={{ color: "#475569", fontSize: "11px", marginTop: "4px" }}>BUSINESS INTELLIGENCE</div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: "12px 8px" }}>
        {navItems.map(({ href, label, icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link key={href} href={href} style={{ textDecoration: "none" }}>
              <div style={{
                display: "flex",
                alignItems: "center",
                gap: "10px",
                padding: "9px 12px",
                borderRadius: "6px",
                marginBottom: "2px",
                backgroundColor: active ? "#1e3a8a" : "transparent",
                color: active ? "#ffffff" : "var(--sidebar-text)",
                fontSize: "13.5px",
                fontWeight: active ? "600" : "400",
                cursor: "pointer",
                transition: "background 0.15s",
              }}>
                <span style={{ fontSize: "15px", lineHeight: 1 }}>{icon}</span>
                {label}
              </div>
            </Link>
          );
        })}
      </nav>

      {/* Bottom */}
      <div style={{ padding: "12px 8px", borderTop: "1px solid #1e293b" }}>
        <div style={{ color: "var(--sidebar-text)", fontSize: "13px", padding: "8px 12px", cursor: "pointer" }}>
          ⓘ Support
        </div>
        <div style={{ color: "var(--sidebar-text)", fontSize: "13px", padding: "8px 12px", cursor: "pointer" }}>
          → Sign Out
        </div>
        <button style={{
          width: "100%",
          marginTop: "8px",
          padding: "10px",
          backgroundColor: "#1d4ed8",
          color: "white",
          border: "none",
          borderRadius: "6px",
          fontSize: "13px",
          fontWeight: "600",
          cursor: "pointer",
        }}>
          Connect Data
        </button>
      </div>
    </aside>
  );
}
