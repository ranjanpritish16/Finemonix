"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/dashboard",    label: "Dashboard" },
  { href: "/integrations", label: "Integrations" },
  { href: "/cashflow",     label: "Cash Flow" },
  { href: "/loan",         label: "Loan Analyzer" },
  { href: "/watchlist",    label: "Risk Monitor" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside style={{ width: "200px", minHeight: "100vh", borderRight: "1px solid #e2e8f0", backgroundColor: "#ffffff" }}>
      <nav style={{ padding: "16px 8px" }}>
        {navItems.map(({ href, label }) => (
          <Link key={href} href={href} style={{ textDecoration: "none" }}>
            <div style={{
              padding: "8px 12px",
              marginBottom: "2px",
              borderRadius: "6px",
              backgroundColor: pathname.startsWith(href) ? "#f1f5f9" : "transparent",
              color: pathname.startsWith(href) ? "#0f172a" : "#64748b",
              fontSize: "14px",
              fontWeight: pathname.startsWith(href) ? "600" : "400",
            }}>
              {label}
            </div>
          </Link>
        ))}
      </nav>
    </aside>
  );
}
