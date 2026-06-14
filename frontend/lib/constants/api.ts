// frontend/lib/constants/api.ts

export const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const WATCHLIST_API = {
    companies: (businessId: number) =>
        `${API_BASE_URL}/api/watchlist/companies?business_id=${businessId}`,
    add: () => `${API_BASE_URL}/api/watchlist/add`,
    remove: (entryId: number) =>
        `${API_BASE_URL}/api/watchlist/remove/${entryId}`,
    runAnomaly: () => `${API_BASE_URL}/api/watchlist/anomaly/run`,
    timeline: (bseCode: string) =>
        `${API_BASE_URL}/api/watchlist/anomaly/timeline/${bseCode}`,
};