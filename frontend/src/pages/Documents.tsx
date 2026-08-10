import { useEffect, useState } from "react";
import {
  FileText,
  Search,
  ChevronRight,
  Clock3,
  Sparkles,
  Filter,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import apiClient from "../api/client";

interface Document {
  id: string;
  file_name: string;
  document_type: string;
  version?: number;
  case_id?: string;
  uploaded_at?: string;
}

function Documents() {
  const navigate = useNavigate();

  const [documents, setDocuments] = useState<Document[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedType, setSelectedType] = useState<string>("ALL");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDocuments() {
      try {
        setLoading(true);
        setError("");

        const response = await apiClient.get<Document[]>("/documents");
        setDocuments(response.data);
      } catch {
        setError("Unable to load workspace documents.");
        setDocuments([]);
      } finally {
        setLoading(false);
      }
    }

    loadDocuments();
  }, []);

  const types = [
    "ALL",
    ...Array.from(
      new Set(
        documents
          .map((d) => d.document_type)
          .filter(Boolean)
      )
    ),
  ];

  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch =
      doc.file_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.document_type.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesType =
      selectedType === "ALL" || doc.document_type === selectedType;

    return matchesSearch && matchesType;
  });

  return (
    <div className="cases-page">
      <div className="page-header">
        <div>
          <div className="eyebrow">Workspace</div>
          <h1>Documents</h1>
          <p>
            Browse, search, and analyze all legal documents across your matters.
          </p>
        </div>

        <button
          className="primary-button"
          onClick={() => navigate("/cases")}
        >
          <FileText size={17} />
          Go to Cases
        </button>
      </div>

      <div className="cases-toolbar">
        <div className="cases-search">
          <Search size={16} />
          <input
            type="text"
            placeholder="Search documents by name or type..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {types.length > 1 && (
          <div className="filter-group" style={{ display: "flex", gap: "8px", alignItems: "center" }}>
            <Filter size={15} style={{ opacity: 0.7 }} />
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="type-select"
              style={{
                background: "rgba(255, 255, 255, 0.05)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                color: "var(--text-primary, #fff)",
                padding: "8px 12px",
                borderRadius: "8px",
                fontSize: "14px",
                cursor: "pointer",
              }}
            >
              {types.map((type) => (
                <option key={type} value={type} style={{ background: "#18181b", color: "#fff" }}>
                  {type === "ALL" ? "All Document Types" : type}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="case-count">
          {filteredDocuments.length}{" "}
          {filteredDocuments.length === 1 ? "document" : "documents"}
        </div>
      </div>

      {loading && <div className="cases-state">Loading documents...</div>}

      {!loading && error && (
        <div className="cases-state cases-error">{error}</div>
      )}

      {!loading && !error && filteredDocuments.length === 0 && (
        <div className="cases-empty">
          <div className="cases-empty-icon">
            <FileText size={23} />
          </div>
          <h2>No documents found</h2>
          <p>
            {searchQuery
              ? "No documents match your search query."
              : "Upload documents inside a case to view and analyze them here."}
          </p>
        </div>
      )}

      {!loading && !error && filteredDocuments.length > 0 && (
        <div className="cases-grid">
          {filteredDocuments.map((doc) => (
            <button
              key={doc.id}
              className="case-card"
              onClick={() => navigate(`/documents/${doc.id}`)}
            >
              <div className="case-card-top">
                <div className="case-icon">
                  <FileText size={18} />
                </div>
                <ChevronRight size={17} />
              </div>

              <div className="case-card-title">{doc.file_name}</div>

              <div className="case-card-details">
                <span>Type: {doc.document_type || "Legal Document"} · v{doc.version || 1}.0</span>
                {doc.case_id && (
                  <span>
                    Case:{" "}
                    {doc.case_id.length > 12
                      ? `${doc.case_id.slice(0, 12)}...`
                      : doc.case_id}
                  </span>
                )}
              </div>

              <div className="case-card-footer">
                <span style={{ display: "flex", alignItems: "center", gap: "5px" }}>
                  <Clock3 size={13} />
                  {doc.uploaded_at
                    ? new Date(doc.uploaded_at).toLocaleDateString()
                    : "Recently added"}
                </span>

                <span className="case-priority" style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                  <Sparkles size={12} />
                  Analyze
                </span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default Documents;
