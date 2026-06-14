// frontend/lib/constants/severity.ts

export type Severity = "low" | "medium" | "high" | "critical";

export const SEVERITY_LABELS: Record<Severity, string> = {
    low: "Low",
    medium: "Medium",
    high: "High",
    critical: "Critical",
};

export const SEVERITY_COLORS: Record<Severity, { bg: string; text: string; border: string }> = {
    low: { bg: "#f0fdf4", text: "#15803d", border: "#bbf7d0" },
    medium: { bg: "#fefce8", text: "#a16207", border: "#fef08a" },
    high: { bg: "#fff7ed", text: "#c2410c", border: "#fed7aa" },
    critical: { bg: "#fef2f2", text: "#b91c1c", border: "#fecaca" },
};

export const SEVERITY_ORDER: Severity[] = ["low", "medium", "high", "critical"];

export const DANGER_FLAG_LABELS: Record<string, string> = {
    revenue_growth: "Revenue contracting",
    expense_ratio: "Expenses exceed 85% of revenue",
    receivables_days: "Receivables over 90 days",
    payables_days: "Payables over 75 days",
    cash_to_debt: "Cash below 10% of total debt",
    promoter_pledge_pct: "Promoter pledge above 40%",
    interest_coverage: "Interest coverage below 1.5x",
};