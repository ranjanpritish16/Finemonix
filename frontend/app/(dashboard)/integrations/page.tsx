"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";

type SourceStatus = {
  type: "tally" | "gst" | "bank";
  label: string;
  status: "connected" | "not_connected";
  records: number;
  last_sync: string | null;
};

type IntegrationsSummary = {
  business_id: number;
  quality_score: number;
  connected_sources: SourceStatus[];
  supported_uploads: Array<{ type: "tally" | "gst" | "bank"; label: string; accept: string }>;
};

type UploadStatus = {
  task_id: string;
  state: string;
  percent: number;
  status: string;
  error: string | null;
  result: unknown;
};

const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const businessId = 1;

export default function IntegrationsPage() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [summary, setSummary] = useState<IntegrationsSummary | null>(null);
  const [selectedType, setSelectedType] = useState<"tally" | "gst" | "bank">("tally");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedUpload = useMemo(
    () => summary?.supported_uploads.find((upload) => upload.type === selectedType),
    [selectedType, summary],
  );

  async function loadSummary() {
    try {
      const res = await fetch(`${backendUrl}/api/data/integrations/${businessId}`, { cache: "no-store" });
      if (!res.ok) throw new Error("Could not load integrations");
      setSummary((await res.json()) as IntegrationsSummary);
    } catch {
      setError("Integration data is unavailable. Start the backend and try again.");
    }
  }

  useEffect(() => {
    loadSummary();
  }, []);

  useEffect(() => {
    if (!uploadStatus?.task_id) return;
    if (["SUCCESS", "FAILURE"].includes(uploadStatus.state)) return;

    const timer = window.setInterval(async () => {
      try {
        const res = await fetch(`${backendUrl}/api/data/status/${uploadStatus.task_id}`, { cache: "no-store" });
        if (!res.ok) return;
        const nextStatus = (await res.json()) as UploadStatus;
        setUploadStatus(nextStatus);
        if (nextStatus.state === "SUCCESS") {
          setUploading(false);
          loadSummary();
        }
        if (nextStatus.state === "FAILURE") {
          setUploading(false);
          setError(nextStatus.error || "Upload processing failed.");
        }
      } catch {
        setError("Could not refresh upload status.");
      }
    }, 2000);

    return () => window.clearInterval(timer);
  }, [uploadStatus?.task_id, uploadStatus?.state]);

  async function uploadFile() {
    if (!selectedFile) {
      setError("Choose a file before uploading.");
      return;
    }

    setError(null);
    setUploading(true);
    setUploadStatus(null);

    const formData = new FormData();
    formData.append("business_id", String(businessId));
    formData.append("file_type", selectedType);
    formData.append("file", selectedFile);

    try {
      const res = await fetch(`${backendUrl}/api/data/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const payload = await res.json().catch(() => null);
        throw new Error(payload?.detail || "Upload failed");
      }

      const payload = (await res.json()) as { task_id: string };
      setUploadStatus({
        task_id: payload.task_id,
        state: "PENDING",
        percent: 0,
        status: "Queued in background",
        error: null,
        result: null,
      });
    } catch (err) {
      setUploading(false);
      setError(err instanceof Error ? err.message : "Upload failed.");
    }
  }

  const sources = summary?.connected_sources || [];

  return (
    <div style={{ fontFamily: "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif", padding: "24px", display: "flex", flexDirection: "column", gap: "18px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1 style={{ margin: "0 0 6px", fontSize: "26px", fontWeight: 700, color: "#111827", lineHeight: 1.3 }}>
            Data <span style={{ color: "#16a34a" }}>Hub</span>
          </h1>
          <p style={{ margin: 0, fontSize: "13px", color: "#6b7280", lineHeight: 1.5, maxWidth: "680px" }}>
            Upload Tally XML, GST JSON, and bank CSV files into the backend processing pipeline.
          </p>
        </div>

        <div style={{ backgroundColor: "#e8f9f4", color: "#047857", border: "1px solid #b2edd8", borderRadius: "8px", padding: "10px 16px", fontSize: "13px", fontWeight: 600 }}>
          Data quality {summary?.quality_score ?? 0}%
        </div>
      </div>

      {error && (
        <div style={{ background: "#fef2f2", border: "1px solid #fecaca", color: "#b91c1c", borderRadius: "8px", padding: "12px 14px", fontSize: "13px" }}>
          {error}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1.3fr) minmax(320px, 0.7fr)", gap: "16px" }}>
        <div style={{ padding: "24px", backgroundColor: "white", borderRadius: "12px", border: "1px solid #e5e7eb" }}>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "16px", textAlign: "center", minHeight: "300px" }}>
            <div style={{ width: "60px", height: "60px", borderRadius: "50%", backgroundColor: "#e8f4fd", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#5aabf7" strokeWidth="1.8">
                <polyline points="16 16 12 12 8 16" />
                <line x1="12" y1="12" x2="12" y2="21" />
                <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
              </svg>
            </div>

            <div>
              <h3 style={{ margin: "0 0 6px", fontSize: "14px", fontWeight: 600, color: "#111827" }}>Upload Financial Files</h3>
              <p style={{ margin: 0, fontSize: "12px", color: "#6b7280", maxWidth: "420px", lineHeight: 1.5 }}>
                Files are sent to FastAPI and processed by Celery. Keep the worker running to complete parsing.
              </p>
            </div>

            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", justifyContent: "center" }}>
              {(["tally", "gst", "bank"] as const).map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => {
                    setSelectedType(type);
                    setSelectedFile(null);
                    if (inputRef.current) inputRef.current.value = "";
                  }}
                  style={{
                    border: selectedType === type ? "1px solid #00c48c" : "1px solid #d1d5db",
                    background: selectedType === type ? "#e8f9f4" : "#fff",
                    color: selectedType === type ? "#047857" : "#374151",
                    borderRadius: "8px",
                    padding: "8px 12px",
                    fontSize: "12px",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  {type.toUpperCase()}
                </button>
              ))}
            </div>

            <input
              ref={inputRef}
              type="file"
              accept={selectedUpload?.accept}
              onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
              style={{ display: "none" }}
            />

            <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap", justifyContent: "center" }}>
              <button
                type="button"
                onClick={() => inputRef.current?.click()}
                style={{ backgroundColor: "#1e2a4a", color: "#fff", border: "none", borderRadius: "8px", padding: "10px 20px", fontSize: "13px", fontWeight: 600, cursor: "pointer" }}
              >
                Browse {selectedUpload?.label || "File"}
              </button>

              <button
                type="button"
                onClick={uploadFile}
                disabled={uploading || !selectedFile}
                style={{
                  backgroundColor: uploading || !selectedFile ? "#d1d5db" : "#00c48c",
                  color: "#fff",
                  border: "none",
                  borderRadius: "8px",
                  padding: "10px 20px",
                  fontSize: "13px",
                  fontWeight: 600,
                  cursor: uploading || !selectedFile ? "not-allowed" : "pointer",
                }}
              >
                {uploading ? "Processing..." : "Upload"}
              </button>
            </div>

            {selectedFile && <p style={{ margin: 0, fontSize: "12px", color: "#6b7280" }}>{selectedFile.name}</p>}

            {uploadStatus && (
              <div style={{ width: "100%", maxWidth: "420px", textAlign: "left" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "#6b7280", marginBottom: "6px" }}>
                  <span>{uploadStatus.status}</span>
                  <span>{uploadStatus.percent}%</span>
                </div>
                <div style={{ height: "6px", backgroundColor: "#e5e7eb", borderRadius: "999px", overflow: "hidden" }}>
                  <div style={{ width: `${uploadStatus.percent}%`, height: "100%", backgroundColor: uploadStatus.state === "FAILURE" ? "#ef4444" : "#1e2a4a" }} />
                </div>
              </div>
            )}
          </div>
        </div>

        <div style={{ backgroundColor: "#d6e8f5", borderRadius: "12px", padding: "20px", display: "flex", flexDirection: "column", gap: "12px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <p style={{ margin: 0, fontSize: "13px", fontWeight: 700, color: "#111827" }}>Connected Sources</p>
            <span style={{ fontSize: "12px", color: "#6b7280" }}>{sources.filter((source) => source.status === "connected").length}/3 live</span>
          </div>

          {sources.length === 0 ? (
            <div style={{ color: "#6b7280", fontSize: "13px" }}>Loading sources...</div>
          ) : (
            sources.map((source) => (
              <SourceRow key={source.type} source={source} />
            ))
          )}

          <div style={{ marginTop: "auto", backgroundColor: "#1e2a4a", borderRadius: "12px", padding: "20px" }}>
            <p style={{ margin: "0 0 6px", fontSize: "14px", fontWeight: 600, color: "#fff" }}>API Status</p>
            <p style={{ margin: "0 0 16px", fontSize: "12px", color: "#94a3b8", lineHeight: 1.5 }}>
              Upload endpoint: `/api/data/upload`. Status polling: `/api/data/status/:taskId`.
            </p>
            <button
              type="button"
              onClick={loadSummary}
              style={{ backgroundColor: "#00c48c", color: "#fff", border: "none", borderRadius: "8px", padding: "8px 16px", fontSize: "13px", fontWeight: 600, cursor: "pointer" }}
            >
              Refresh
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function SourceRow({ source }: { source: SourceStatus }) {
  const connected = source.status === "connected";

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "12px", borderRadius: "8px", backgroundColor: "#fff" }}>
      <div style={{ width: "38px", height: "38px", borderRadius: "8px", backgroundColor: connected ? "#e6faf3" : "#f3f4f6", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "12px", fontWeight: 800, color: connected ? "#047857" : "#6b7280", flexShrink: 0 }}>
        {source.type.toUpperCase()}
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <p style={{ margin: "0 0 3px", fontSize: "13px", fontWeight: 600, color: "#111827" }}>{source.label}</p>
        <p style={{ margin: 0, fontSize: "11px", color: "#9ca3af" }}>
          {source.records} records{source.last_sync ? `, last sync ${source.last_sync}` : ""}
        </p>
      </div>

      <span style={{ fontSize: "10px", fontWeight: 700, color: connected ? "#00c48c" : "#6b7280", backgroundColor: connected ? "#e6faf3" : "#f3f4f6", padding: "3px 8px", borderRadius: "20px", whiteSpace: "nowrap" }}>
        {connected ? "CONNECTED" : "NO DATA"}
      </span>
    </div>
  );
}
