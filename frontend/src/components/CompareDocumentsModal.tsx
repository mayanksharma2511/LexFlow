import { useState } from "react";
import {
  FileDiff,
  X,
  Loader2,
  AlertCircle,
  CheckCircle2,
  ArrowRight,
  PlusCircle,
  MinusCircle,
  RefreshCw,
} from "lucide-react";
import apiClient from "../api/client";

interface DocumentOption {
  id: string;
  file_name: string;
  document_type: string;
}

interface CompareDocumentsModalProps {
  isOpen: boolean;
  onClose: () => void;
  caseId: string;
  documents: DocumentOption[];
  initialDocId?: string;
}

interface ComparisonChange {
  old: string;
  new: string;
}

interface ComparisonResult {
  summary: string;
  added?: ComparisonChange[] | string[];
  removed?: ComparisonChange[] | string[];
  modified?: ComparisonChange[] | string[];
}

export function CompareDocumentsModal({
  isOpen,
  onClose,
  documents,
  initialDocId,
}: CompareDocumentsModalProps) {
  const [doc1Id, setDoc1Id] = useState<string>(initialDocId || (documents[0]?.id || ""));
  const [doc2Id, setDoc2Id] = useState<string>(
    documents.find((d) => d.id !== (initialDocId || documents[0]?.id))?.id || ""
  );

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<ComparisonResult | null>(null);

  if (!isOpen) return null;

  async function handleCompare() {
    if (!doc1Id || !doc2Id) {
      setError("Please select two documents to compare.");
      return;
    }

    if (doc1Id === doc2Id) {
      setError("Please select two different documents for comparison.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setResult(null);

      const response = await apiClient.post<ComparisonResult>(
        `/ai/documents/${doc1Id}/compare/${doc2Id}`
      );

      setResult(response.data);
    } catch {
      setError("Failed to execute document comparison. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  function formatChangeList(items?: ComparisonChange[] | string[]) {
    if (!items || items.length === 0) return null;
    return items.map((item, idx) => {
      if (typeof item === "string") {
        return <div key={idx} style={{ marginBottom: "6px" }}>• {item}</div>;
      }
      return (
        <div key={idx} style={{ marginBottom: "8px", fontSize: "13px", lineHeight: "1.4" }}>
          {item.old && <div style={{ color: "#ef4444", textDecoration: "line-through" }}>- {item.old}</div>}
          {item.new && <div style={{ color: "#10b981", fontWeight: 500 }}>+ {item.new}</div>}
        </div>
      );
    });
  }

  const doc1Obj = documents.find((d) => d.id === doc1Id);
  const doc2Obj = documents.find((d) => d.id === doc2Id);

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        padding: "20px",
      }}
    >
      <div
        style={{
          backgroundColor: "#13161c",
          border: "1px solid rgba(255, 255, 255, 0.16)",
          borderRadius: "12px",
          width: "100%",
          maxWidth: "800px",
          maxHeight: "90vh",
          overflowY: "auto",
          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.5)",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* MODAL HEADER */}
        <div
          style={{
            padding: "20px 24px",
            borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "8px",
                backgroundColor: "rgba(201, 169, 110, 0.15)",
                color: "#c9a96e",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <FileDiff size={20} />
            </div>
            <div>
              <h2 style={{ margin: 0, fontSize: "18px", color: "#ffffff", fontWeight: 600 }}>
                Document Comparison Analysis
              </h2>
              <p style={{ margin: "2px 0 0 0", fontSize: "12px", color: "#94a3b8" }}>
                Select two documents from this legal matter to compare contractual differences
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              color: "#94a3b8",
              cursor: "pointer",
              padding: "4px",
              borderRadius: "4px",
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* MODAL BODY */}
        <div style={{ padding: "24px", flex: 1 }}>
          {/* SELECTORS */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 40px 1fr",
              gap: "12px",
              alignItems: "center",
              marginBottom: "20px",
            }}
          >
            <div>
              <label style={{ display: "block", fontSize: "12px", color: "#94a3b8", marginBottom: "6px" }}>
                Original Document (Base)
              </label>
              <select
                value={doc1Id}
                onChange={(e) => setDoc1Id(e.target.value)}
                style={{
                  width: "100%",
                  padding: "10px 12px",
                  backgroundColor: "#1e293b",
                  border: "1px solid rgba(255, 255, 255, 0.16)",
                  borderRadius: "6px",
                  color: "#ffffff",
                  fontSize: "13px",
                }}
              >
                {documents.map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    {doc.file_name} ({doc.document_type})
                  </option>
                ))}
              </select>
            </div>

            <div style={{ textAlign: "center", color: "#c9a96e", marginTop: "18px" }}>
              <ArrowRight size={20} />
            </div>

            <div>
              <label style={{ display: "block", fontSize: "12px", color: "#94a3b8", marginBottom: "6px" }}>
                Compared Document (New / Amendment)
              </label>
              <select
                value={doc2Id}
                onChange={(e) => setDoc2Id(e.target.value)}
                style={{
                  width: "100%",
                  padding: "10px 12px",
                  backgroundColor: "#1e293b",
                  border: "1px solid rgba(255, 255, 255, 0.16)",
                  borderRadius: "6px",
                  color: "#ffffff",
                  fontSize: "13px",
                }}
              >
                {documents.map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    {doc.file_name} ({doc.document_type})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {error && (
            <div
              style={{
                marginBottom: "20px",
                padding: "12px",
                backgroundColor: "rgba(239, 68, 68, 0.1)",
                border: "1px solid rgba(239, 68, 68, 0.3)",
                borderRadius: "6px",
                color: "#ef4444",
                fontSize: "13px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <button
            onClick={handleCompare}
            disabled={loading || documents.length < 2}
            style={{
              width: "100%",
              padding: "12px",
              backgroundColor: "#c9a96e",
              color: "#000000",
              border: "none",
              borderRadius: "6px",
              fontWeight: 600,
              fontSize: "14px",
              cursor: loading || documents.length < 2 ? "not-allowed" : "pointer",
              opacity: loading || documents.length < 2 ? 0.6 : 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              marginBottom: "24px",
            }}
          >
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                <span>Running AI Comparison Analysis...</span>
              </>
            ) : (
              <>
                <FileDiff size={18} />
                <span>Execute Document Comparison</span>
              </>
            )}
          </button>

          {/* RESULTS VIEW */}
          {result && (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {/* SUMMARY CARD */}
              <div
                style={{
                  padding: "16px",
                  backgroundColor: "#1e293b",
                  border: "1px solid rgba(255, 255, 255, 0.12)",
                  borderRadius: "8px",
                }}
              >
                <h3 style={{ margin: "0 0 8px 0", fontSize: "14px", color: "#c9a96e", display: "flex", alignItems: "center", gap: "6px" }}>
                  <CheckCircle2 size={16} />
                  Executive Comparison Summary
                </h3>
                <p style={{ margin: 0, fontSize: "13px", color: "#e2e8f0", lineHeight: "1.5" }}>
                  {result.summary}
                </p>
                <div style={{ marginTop: "10px", fontSize: "11px", color: "#94a3b8" }}>
                  Comparing <strong>{doc1Obj?.file_name}</strong> vs <strong>{doc2Obj?.file_name}</strong>
                </div>
              </div>

              {/* DIFF COLUMNS */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                {/* ADDED PROVISIONS */}
                <div
                  style={{
                    padding: "14px",
                    backgroundColor: "rgba(16, 185, 129, 0.05)",
                    border: "1px solid rgba(16, 185, 129, 0.2)",
                    borderRadius: "8px",
                  }}
                >
                  <h4 style={{ margin: "0 0 10px 0", fontSize: "13px", color: "#10b981", display: "flex", alignItems: "center", gap: "6px" }}>
                    <PlusCircle size={15} />
                    Added Provisions
                  </h4>
                  {formatChangeList(result.added) || (
                    <span style={{ fontSize: "12px", color: "#64748b" }}>No added terms detected</span>
                  )}
                </div>

                {/* REMOVED PROVISIONS */}
                <div
                  style={{
                    padding: "14px",
                    backgroundColor: "rgba(239, 68, 68, 0.05)",
                    border: "1px solid rgba(239, 68, 68, 0.2)",
                    borderRadius: "8px",
                  }}
                >
                  <h4 style={{ margin: "0 0 10px 0", fontSize: "13px", color: "#ef4444", display: "flex", alignItems: "center", gap: "6px" }}>
                    <MinusCircle size={15} />
                    Removed Provisions
                  </h4>
                  {formatChangeList(result.removed) || (
                    <span style={{ fontSize: "12px", color: "#64748b" }}>No removed terms detected</span>
                  )}
                </div>
              </div>

              {/* MODIFIED PROVISIONS */}
              {result.modified && result.modified.length > 0 && (
                <div
                  style={{
                    padding: "14px",
                    backgroundColor: "rgba(201, 169, 110, 0.05)",
                    border: "1px solid rgba(201, 169, 110, 0.2)",
                    borderRadius: "8px",
                  }}
                >
                  <h4 style={{ margin: "0 0 10px 0", fontSize: "13px", color: "#c9a96e", display: "flex", alignItems: "center", gap: "6px" }}>
                    <RefreshCw size={15} />
                    Modified Provisions & Obligations
                  </h4>
                  {formatChangeList(result.modified)}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
