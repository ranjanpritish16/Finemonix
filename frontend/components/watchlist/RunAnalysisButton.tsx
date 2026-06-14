"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { WATCHLIST_API } from "@/lib/constants/api";

export default function RunAnalysisButton({ bseCode }: { bseCode: string }) {
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [done, setDone] = useState(false);
    const [error, setError] = useState(false);

    async function handleRun() {
        setLoading(true);
        setError(false);
        setDone(false);
        try {
            const res = await fetch(WATCHLIST_API.runAnomaly(), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ company_bse_code: bseCode, use_demo_data: true }),
            });
            if (!res.ok) throw new Error();
            setDone(true);
            router.refresh();
        } catch {
            setError(true);
        } finally {
            setLoading(false);
        }
    }

    return (
        <button
            onClick={handleRun}
            disabled={loading}
            title="Run anomaly analysis"
            style={{
                padding: "7px 14px",
                background: done ? "#f0fdf4" : error ? "#fef2f2" : "#f8fafc",
                color: done ? "#15803d" : error ? "#b91c1c" : "#475569",
                border: `1px solid ${done ? "#bbf7d0" : error ? "#fecaca" : "#e2e8f0"}`,
                borderRadius: "6px",
                fontSize: "12px",
                fontWeight: 600,
                cursor: loading ? "not-allowed" : "pointer",
                whiteSpace: "nowrap",
            }}
        >
            {loading ? "Running…" : done ? "✓ Done" : error ? "Failed" : "Run Analysis"}
        </button>
    );
}