// frontend/components/watchlist/AddCompanyForm.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { WATCHLIST_API } from "@/lib/constants/api";

const BUSINESS_ID = 1;

export default function AddCompanyForm() {
    const router = useRouter();
    const [bseCode, setBseCode] = useState("");
    const [companyName, setCompanyName] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function handleAdd() {
        const code = bseCode.trim().toUpperCase();
        const name = companyName.trim();
        if (!code) { setError("BSE code is required"); return; }

        setLoading(true);
        setError(null);

        try {
            const res = await fetch(WATCHLIST_API.add(), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    business_id: BUSINESS_ID,
                    company_bse_code: code,
                    company_name: name || code,
                }),
            });

            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data?.detail || `Error ${res.status}`);
            }

            setBseCode("");
            setCompanyName("");
            router.refresh();
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to add company");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div style={{
            background: "#ffffff",
            border: "1px solid #e2e8f0",
            borderRadius: "8px",
            padding: "20px 24px",
            marginBottom: "24px",
        }}>
            <p style={{ fontSize: "13px", fontWeight: 600, color: "#0f172a", marginBottom: "12px" }}>
                Add Company to Watchlist
            </p>

            <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", alignItems: "flex-end" }}>
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                    <label style={{ fontSize: "12px", color: "#64748b" }}>BSE Code *</label>
                    <input
                        value={bseCode}
                        onChange={e => setBseCode(e.target.value)}
                        placeholder="e.g. DHFL"
                        style={{
                            padding: "8px 12px",
                            border: "1px solid #e2e8f0",
                            borderRadius: "6px",
                            fontSize: "14px",
                            width: "140px",
                            outline: "none",
                        }}
                    />
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                    <label style={{ fontSize: "12px", color: "#64748b" }}>Company Name</label>
                    <input
                        value={companyName}
                        onChange={e => setCompanyName(e.target.value)}
                        placeholder="e.g. DHFL Ltd"
                        style={{
                            padding: "8px 12px",
                            border: "1px solid #e2e8f0",
                            borderRadius: "6px",
                            fontSize: "14px",
                            width: "200px",
                            outline: "none",
                        }}
                    />
                </div>

                <button
                    onClick={handleAdd}
                    disabled={loading}
                    style={{
                        padding: "8px 20px",
                        background: loading ? "#94a3b8" : "#0f172a",
                        color: "#ffffff",
                        border: "none",
                        borderRadius: "6px",
                        fontSize: "14px",
                        fontWeight: 600,
                        cursor: loading ? "not-allowed" : "pointer",
                    }}
                >
                    {loading ? "Adding…" : "Add"}
                </button>
            </div>

            {error && (
                <p style={{ marginTop: "8px", fontSize: "13px", color: "#b91c1c" }}>{error}</p>
            )}
        </div>
    );
}