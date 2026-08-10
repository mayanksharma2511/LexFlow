import { useEffect, useState } from "react";
import {
  Activity,
  ArrowLeft,
  BriefcaseBusiness,
  Clock3,
  FileText,
  Plus,
  Scale,
  Sparkles,
  UserPlus,
  UserRound,
  FileDiff,
  Search,
  Loader2,
  Network,
  CheckCircle2,
} from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import apiClient from "../api/client";
import { UploadDocumentModal } from "../components/UploadDocumentModal";
import { CompareDocumentsModal } from "../components/CompareDocumentsModal";
import { KnowledgeGraphView } from "../components/KnowledgeGraphView";

interface CaseDetailsData {
  id: string;
  title: string;
  case_number?: string | null;
  client_name?: string | null;
  opposing_party?: string | null;
  court?: string | null;
  description?: string | null;
  status?: string | null;
  priority?: string | null;
  documents: {
    id: string;
    file_name: string;
    document_type: string;
    version?: number;
    uploaded_at: string;
    analysis_count: number;
  }[];
  document_count: number;
}

interface CaseMember {
  id: string;
  user_id: string;
  role_in_case: string;
  full_name?: string | null;
  email?: string | null;
  created_at: string;
}

interface AuditLog {
  id: string;
  action: string;
  entity_type: string;
  details?: string | null;
  created_at: string;
}

interface CaseAISynthesis {
  overall_risk_score: number;
  overall_risk_level: string;
  executive_summary: string;
  key_issues: (string | Record<string, unknown>)[];
  recommended_actions: (string | Record<string, unknown>)[];
}

interface SemanticSearchResult {
  chunk_id: string;
  document_id: string;
  file_name: string;
  text_snippet: string;
  relevance_score: number;
  chunk_index: number;
}

function formatItemText(item: unknown): string {
  if (typeof item === "string") return item;
  if (typeof item === "number" || typeof item === "boolean") return String(item);
  if (typeof item === "object" && item !== null) {
    const obj = item as Record<string, unknown>;
    if (obj.issue) return `${obj.issue}${obj.exposure ? ` (${obj.exposure})` : ""}`;
    if (obj.title) return `${obj.title}${obj.description ? `: ${obj.description}` : ""}`;
    if (obj.action) return String(obj.action);
    return Object.values(obj).filter(Boolean).map(String).join(" - ");
  }
  return String(item ?? "");
}

function CaseDetails() {
  const { caseId } = useParams();
  const navigate = useNavigate();

  const [caseData, setCaseData] = useState<CaseDetailsData | null>(null);
  const [members, setMembers] = useState<CaseMember[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [aiSynthesis, setAiSynthesis] = useState<CaseAISynthesis | null>(null);
  const [loadingSynthesis, setLoadingSynthesis] = useState(false);
  const [synthesisError, setSynthesisError] = useState("");
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isCompareOpen, setIsCompareOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // RAG Semantic Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<SemanticSearchResult[] | null>(null);
  const [searchError, setSearchError] = useState("");

  // Tab State
  const [activeTab, setActiveTab] = useState<"overview" | "graph">("overview");

  const loadDetails = () => {
    if (!caseId) return;

    apiClient.get<CaseDetailsData>(`/cases/${caseId}/dashboard`)
      .then((response) => {
        setCaseData(response.data);
      })
      .catch(() => {
        setError("Unable to load this case.");
      })
      .finally(() => {
        setLoading(false);
      });

    apiClient.get<CaseMember[]>(`/cases/${caseId}/members`)
      .then((memRes) => {
        setMembers(memRes.data);
      })
      .catch(() => {
        setMembers([]);
      });

    apiClient.get<AuditLog[]>(`/audit-logs/cases/${caseId}`)
      .then((logRes) => {
        setAuditLogs(logRes.data);
      })
      .catch(() => {
        setAuditLogs([]);
      });
  };

  useEffect(() => {
    loadDetails();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseId]);

  const handleSynthesizeAI = async () => {
    if (!caseId) return;
    setLoadingSynthesis(true);
    setSynthesisError("");
    try {
      const res = await apiClient.post<CaseAISynthesis>(`/ai/cases/${caseId}/synthesis`);
      setAiSynthesis(res.data);
    } catch (err: unknown) {
      console.error("Failed to run case synthesis", err);
      const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string };
      setSynthesisError(axiosErr.response?.data?.detail || axiosErr.message || "Failed to generate AI synthesis.");
    } finally {
      setLoadingSynthesis(false);
    }
  };

  const handleSemanticSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!caseId || !searchQuery.trim()) return;

    setSearching(true);
    setSearchError("");
    try {
      const res = await apiClient.get<SemanticSearchResult[]>(
        `/cases/${caseId}/semantic-search`,
        { params: { query: searchQuery.trim(), top_k: 5 } }
      );
      setSearchResults(res.data);
    } catch {
      setSearchError("Failed to execute RAG vector search.");
    } finally {
      setSearching(false);
    }
  };

  if (loading) {
    return <div className="case-details-state">Loading case details...</div>;
  }

  if (error || !caseData) {
    return (
      <div className="case-details-state">
        <p>{error || "Case not found."}</p>
        <button className="secondary-button" onClick={() => navigate("/cases")}>
          Back to cases
        </button>
      </div>
    );
  }

  return (
    <div className="case-details-page">
      <UploadDocumentModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        caseId={caseData.id}
        onSuccess={loadDetails}
      />

      <CompareDocumentsModal
        isOpen={isCompareOpen}
        onClose={() => setIsCompareOpen(false)}
        caseId={caseData.id}
        documents={caseData.documents}
      />

      <button className="back-button" onClick={() => navigate("/cases")}>
        <ArrowLeft size={16} />
        Back to cases
      </button>

      <div className="case-details-header">
        <div>
          <div className="eyebrow">Legal Matter</div>
          <h1>{caseData.title}</h1>
          {caseData.case_number && (
            <p className="case-details-number">Case No. {caseData.case_number}</p>
          )}
        </div>

        <div className="case-status-row" style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
          {caseData.status && <span className="status-pill">{caseData.status}</span>}
          {caseData.priority && <span className="priority-pill">{caseData.priority}</span>}
          <button className="primary-button" onClick={() => setIsUploadOpen(true)}>
            <Plus size={16} /> Upload File
          </button>
          <button
            className="secondary-button"
            onClick={() => setIsCompareOpen(true)}
            disabled={caseData.documents.length < 2}
            style={{ display: "flex", alignItems: "center", gap: "6px" }}
          >
            <FileDiff size={16} color="#c9a96e" />
            Compare Docs
          </button>
          <button
            className="secondary-button"
            onClick={handleSynthesizeAI}
            disabled={loadingSynthesis}
            style={{ display: "flex", alignItems: "center", gap: "6px" }}
          >
            <Sparkles size={16} color="#60a5fa" />
            {loadingSynthesis ? "Synthesizing..." : "Synthesize AI"}
          </button>
        </div>
      </div>

      {/* CASE OVERVIEW CARDS */}
      <div className="case-overview-grid">
        <div className="overview-card">
          <UserRound size={18} />
          <div>
            <span>Client</span>
            <strong>{caseData.client_name || "Not specified"}</strong>
          </div>
        </div>

        <div className="overview-card">
          <Scale size={18} />
          <div>
            <span>Opposing Party</span>
            <strong>{caseData.opposing_party || "Not specified"}</strong>
          </div>
        </div>

        <div className="overview-card">
          <BriefcaseBusiness size={18} />
          <div>
            <span>Court</span>
            <strong>{caseData.court || "Not specified"}</strong>
          </div>
        </div>

        <div className="overview-card">
          <FileText size={18} />
          <div>
            <span>Documents</span>
            <strong>{caseData.document_count}</strong>
          </div>
        </div>
      </div>

      {/* VIEW TABS: OVERVIEW VS KNOWLEDGE GRAPH */}
      <div style={{ display: "flex", gap: "12px", margin: "20px 0 0 0", borderBottom: "1px solid rgba(255, 255, 255, 0.1)" }}>
        <button
          onClick={() => setActiveTab("overview")}
          style={{
            padding: "10px 16px",
            backgroundColor: "transparent",
            border: "none",
            borderBottom: activeTab === "overview" ? "2px solid #c9a96e" : "2px solid transparent",
            color: activeTab === "overview" ? "#c9a96e" : "#94a3b8",
            fontWeight: 600,
            fontSize: "14px",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <FileText size={16} /> Matter Workspace & Intelligence
        </button>
        <button
          onClick={() => setActiveTab("graph")}
          style={{
            padding: "10px 16px",
            backgroundColor: "transparent",
            border: "none",
            borderBottom: activeTab === "graph" ? "2px solid #c9a96e" : "2px solid transparent",
            color: activeTab === "graph" ? "#c9a96e" : "#94a3b8",
            fontWeight: 600,
            fontSize: "14px",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <Network size={16} /> Knowledge Graph & Entities
        </button>
      </div>

      {activeTab === "graph" ? (
        <KnowledgeGraphView caseId={caseData.id} />
      ) : (
        <>
          {/* RAG VECTOR SEMANTIC SEARCH BAR */}
          <section className="case-section" style={{ marginTop: "24px" }}>
            <div className="section-heading">
              <div>
                <div className="eyebrow">Vector RAG Intelligence</div>
                <h2>Semantic Matter Search</h2>
              </div>
            </div>

            <form onSubmit={handleSemanticSearch} style={{ display: "flex", gap: "12px", marginBottom: "16px" }}>
              <div style={{ position: "relative", flex: 1 }}>
                <Search size={18} style={{ position: "absolute", left: "14px", top: "12px", color: "#64748b" }} />
                <input
                  type="text"
                  placeholder="Search matter context (e.g. 'rent amount', 'highway acquisition compensation')..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px 14px 10px 42px",
                    backgroundColor: "#13161c",
                    border: "1px solid rgba(255, 255, 255, 0.16)",
                    borderRadius: "8px",
                    color: "#ffffff",
                    fontSize: "14px",
                  }}
                />
              </div>
              <button
                type="submit"
                disabled={searching || !searchQuery.trim()}
                style={{
                  padding: "10px 20px",
                  backgroundColor: "#c9a96e",
                  color: "#000000",
                  border: "none",
                  borderRadius: "8px",
                  fontWeight: 600,
                  fontSize: "14px",
                  cursor: searching || !searchQuery.trim() ? "not-allowed" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                {searching ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
                <span>RAG Search</span>
              </button>
            </form>

            {searchError && (
              <div style={{ padding: "12px", backgroundColor: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.3)", borderRadius: "6px", color: "#ef4444", fontSize: "13px" }}>
                {searchError}
              </div>
            )}

            {searchResults && (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "12px" }}>
                <div style={{ fontSize: "12px", color: "#94a3b8" }}>
                  Found {searchResults.length} ranked semantic match{searchResults.length === 1 ? "" : "es"}
                </div>
                {searchResults.length === 0 ? (
                  <div style={{ padding: "16px", backgroundColor: "#13161c", border: "1px solid rgba(255, 255, 255, 0.1)", borderRadius: "8px", color: "#94a3b8", fontSize: "13px" }}>
                    No matching semantic chunks found for "{searchQuery}".
                  </div>
                ) : (
                  searchResults.map((hit) => {
                    const pctScore = Math.round((hit.relevance_score || 0) * 100);
                    return (
                      <div
                        key={hit.chunk_id}
                        style={{
                          padding: "14px",
                          backgroundColor: "#13161c",
                          border: "1px solid rgba(255, 255, 255, 0.14)",
                          borderRadius: "8px",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "6px" }}>
                          <button
                            onClick={() => navigate(`/documents/${hit.document_id}`)}
                            style={{ background: "none", border: "none", color: "#60a5fa", fontWeight: 600, fontSize: "13px", cursor: "pointer", display: "flex", alignItems: "center", gap: "6px", padding: 0 }}
                          >
                            <FileText size={14} />
                            {hit.file_name} (Chunk #{hit.chunk_index + 1})
                          </button>
                          <span
                            style={{
                              padding: "2px 8px",
                              backgroundColor: "rgba(16, 185, 129, 0.15)",
                              color: "#10b981",
                              borderRadius: "4px",
                              fontSize: "11px",
                              fontWeight: 600,
                              display: "flex",
                              alignItems: "center",
                              gap: "4px",
                            }}
                          >
                            <CheckCircle2 size={12} />
                            {pctScore}% Match
                          </span>
                        </div>
                        <p style={{ margin: 0, fontSize: "13px", color: "#cbd5e1", lineHeight: 1.5, fontStyle: "italic" }}>
                          "{hit.text_snippet}"
                        </p>
                      </div>
                    );
                  })
                )}
              </div>
            )}
          </section>

          {loadingSynthesis && (
            <div style={{ marginTop: "24px", padding: "16px", backgroundColor: "rgba(37, 99, 235, 0.1)", border: "1px solid rgba(37, 99, 235, 0.3)", borderRadius: "10px", color: "#60a5fa", display: "flex", alignItems: "center", gap: "10px" }}>
              <Sparkles size={18} className="animate-spin" />
              <span>Synthesizing legal documents and assessing case risk profile...</span>
            </div>
          )}

          {synthesisError && (
            <div style={{ marginTop: "24px", padding: "16px", backgroundColor: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.3)", borderRadius: "10px", color: "#ef4444" }}>
              {synthesisError}
            </div>
          )}

          {aiSynthesis && (
            <section className="case-section" style={{ marginTop: "24px" }}>
              <div className="section-heading">
                <div>
                  <div className="eyebrow">Legal Intelligence</div>
                  <h2>Multi-Document Case AI Synthesis</h2>
                </div>
                <span
                  style={{
                    padding: "4px 10px",
                    backgroundColor: (aiSynthesis.overall_risk_level || "").toLowerCase() === "high" ? "rgba(239, 68, 68, 0.2)" : "rgba(34, 197, 94, 0.2)",
                    color: (aiSynthesis.overall_risk_level || "").toLowerCase() === "high" ? "#ef4444" : "#4ade80",
                    borderRadius: "6px",
                    fontSize: "12px",
                    fontWeight: 600,
                  }}
                >
                  Risk Level: {aiSynthesis.overall_risk_level || "Medium"} ({aiSynthesis.overall_risk_score ?? 50}/100)
                </span>
              </div>

              <div className="description-card" style={{ display: "grid", gap: "16px" }}>
                <div>
                  <h4 style={{ margin: "0 0 6px", fontSize: "14px", color: "#f8fafc" }}>Executive Matter Summary</h4>
                  <p style={{ margin: 0, color: "#cbd5e1", lineHeight: 1.5 }}>{aiSynthesis.executive_summary || "Matter synthesis completed."}</p>
                </div>

                {Array.isArray(aiSynthesis.key_issues) && aiSynthesis.key_issues.length > 0 && (
                  <div>
                    <h4 style={{ margin: "0 0 6px", fontSize: "14px", color: "#f8fafc" }}>Key Legal Issues & Risk Exposure</h4>
                    <ul style={{ margin: 0, paddingLeft: "20px", color: "#cbd5e1", fontSize: "13px" }}>
                      {aiSynthesis.key_issues.map((issue, idx) => (
                        <li key={idx} style={{ marginBottom: "4px" }}>{formatItemText(issue)}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {Array.isArray(aiSynthesis.recommended_actions) && aiSynthesis.recommended_actions.length > 0 && (
                  <div>
                    <h4 style={{ margin: "0 0 6px", fontSize: "14px", color: "#60a5fa" }}>Recommended Strategic Actions</h4>
                    <ul style={{ margin: 0, paddingLeft: "20px", color: "#cbd5e1", fontSize: "13px" }}>
                      {aiSynthesis.recommended_actions.map((act, idx) => (
                        <li key={idx} style={{ marginBottom: "4px" }}>{formatItemText(act)}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </section>
          )}

          {caseData.description && (
            <section className="case-section" style={{ marginTop: "24px" }}>
              <div className="section-heading">
                <div>
                  <div className="eyebrow">Matter Overview</div>
                  <h2>Description</h2>
                </div>
              </div>
              <div className="description-card">{caseData.description}</div>
            </section>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "24px", marginTop: "24px" }}>
            <section className="case-section">
              <div className="section-heading">
                <div>
                  <div className="eyebrow">Case Files</div>
                  <h2>Documents</h2>
                </div>
                <span className="section-count">{caseData.document_count}</span>
              </div>

              {caseData.documents.length === 0 ? (
                <div className="documents-empty">
                  <FileText size={22} />
                  <div>
                    <strong>No documents yet</strong>
                    <p>Upload documents to begin AI analysis.</p>
                  </div>
                </div>
              ) : (
                <div className="documents-list">
                  {caseData.documents.map((document) => (
                    <button
                      key={document.id}
                      className="document-row"
                      onClick={() => navigate(`/documents/${document.id}`)}
                    >
                      <div className="document-icon">
                        <FileText size={18} />
                      </div>

                      <div className="document-main">
                        <strong>{document.file_name}</strong>
                        <span>{document.document_type} · v{document.version || 1}.0</span>
                      </div>

                      <div className="document-analysis">
                        <Sparkles size={14} />
                        {document.analysis_count} analyses
                      </div>

                      <div className="document-date">
                        <Clock3 size={14} />
                        {new Date(document.uploaded_at).toLocaleDateString()}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </section>

            <div>
              <section className="case-section" style={{ marginBottom: "24px" }}>
                <div className="section-heading">
                  <div>
                    <div className="eyebrow">Case Team</div>
                    <h2>Members</h2>
                  </div>
                  <UserPlus size={16} style={{ cursor: "pointer", color: "#60a5fa" }} />
                </div>

                <div className="description-card" style={{ display: "grid", gap: "12px", padding: "16px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <div style={{ width: "32px", height: "32px", borderRadius: "50%", backgroundColor: "#2563eb", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 600, color: "#fff" }}>
                      M
                    </div>
                    <div>
                      <div style={{ fontSize: "13px", fontWeight: 600, color: "#f8fafc" }}>Mayank Sharma (You)</div>
                      <div style={{ fontSize: "11px", color: "#60a5fa" }}>Lead Counsel</div>
                    </div>
                  </div>

                  {members.map((m) => (
                    <div key={m.id} style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <div style={{ width: "32px", height: "32px", borderRadius: "50%", backgroundColor: "#334155", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 600, color: "#fff" }}>
                        {(m.full_name || m.email || "U")[0].toUpperCase()}
                      </div>
                      <div>
                        <div style={{ fontSize: "13px", fontWeight: 600, color: "#f8fafc" }}>{m.full_name || m.email}</div>
                        <div style={{ fontSize: "11px", color: "#94a3b8" }}>{m.role_in_case}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              <section className="case-section">
                <div className="section-heading">
                  <div>
                    <div className="eyebrow">Audit Trail</div>
                    <h2>Case Timeline</h2>
                  </div>
                  <Activity size={16} />
                </div>

                <div className="description-card" style={{ display: "grid", gap: "12px", padding: "16px" }}>
                  {auditLogs.length === 0 ? (
                    <div style={{ fontSize: "12px", color: "#94a3b8" }}>No timeline events recorded yet.</div>
                  ) : (
                    auditLogs.map((log) => (
                      <div key={log.id} style={{ borderLeft: "2px solid #2563eb", paddingLeft: "10px" }}>
                        <div style={{ fontSize: "12px", fontWeight: 600, color: "#f8fafc" }}>{log.action}</div>
                        <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "2px" }}>{log.details || log.entity_type}</div>
                        <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>{new Date(log.created_at).toLocaleString()}</div>
                      </div>
                    ))
                  )}
                </div>
              </section>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default CaseDetails;