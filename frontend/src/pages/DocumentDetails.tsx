import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import {
  ArrowLeft,
  FileText,
  Sparkles,
  ShieldAlert,
  ListChecks,
  Scale,
  Clock3,
  CheckCircle2,
  Loader2,
  AlertTriangle,
  CalendarDays,
  Users,
  IndianRupee,
  Gavel,
  Download,
  Trash2,
} from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import apiClient from "../api/client";
import "./DocumentDetails.css";

interface Analysis {
  id?: string;
  document_id?: string;
  analysis_type: string;
  result: string;
  created_at: string;
}

interface DocumentData {
  id: string;
  file_name: string;
  file_path?: string;
  extracted_text?: string | null;
  document_type: string;
  status?: string | null;
  error_message?: string | null;
  version?: number;
  uploaded_at: string;
  case_id?: string;
}

type AnalysisType =
  | "summary"
  | "classification"
  | "clauses"
  | "risks";

interface RiskItem {
  title?: string;
  severity?: string;
  description?: string;
  recommendation?: string;
}

function DocumentDetails() {
  const { documentId } = useParams();
  const navigate = useNavigate();

  const [document, setDocument] =
    useState<DocumentData | null>(null);

  const [analyses, setAnalyses] = useState<Analysis[]>(
    [],
  );

  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [activeAnalysis, setActiveAnalysis] =
    useState<AnalysisType | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDocument() {
      if (!documentId) return;

      try {
        setLoading(true);
        setError("");

        const [documentResponse, analysesResponse] =
          await Promise.all([
            apiClient.get<DocumentData>(
              `/documents/${documentId}`,
            ),
            apiClient.get<Analysis[]>(
              `/ai/documents/${documentId}/analyses`,
            ),
          ]);

        setDocument(documentResponse.data);
        setAnalyses(analysesResponse.data);
      } catch {
        setError("Unable to load this document.");
      } finally {
        setLoading(false);
      }
    }

    loadDocument();
  }, [documentId]);

  async function runAnalysis(
    analysisType: AnalysisType,
  ) {
    if (!documentId) return;

    try {
      setAnalyzing(true);
      setActiveAnalysis(analysisType);
      setError("");

      let endpoint = "";

      switch (analysisType) {
        case "summary":
          endpoint =
            `/ai/documents/${documentId}/summary`;
          break;

        case "classification":
          endpoint =
            `/ai/documents/${documentId}/classify`;
          break;

        case "clauses":
          endpoint =
            `/ai/documents/${documentId}/extract-clauses`;
          break;

        case "risks":
          endpoint =
            `/ai/documents/${documentId}/risk-analysis`;
          break;
      }

      await apiClient.post(endpoint);

      const response =
        await apiClient.get<Analysis[]>(
          `/ai/documents/${documentId}/analyses`,
        );

      setAnalyses(response.data);
    } catch {
      setError("AI analysis could not be completed.");
    } finally {
      setAnalyzing(false);
      setActiveAnalysis(null);
    }
  }

  async function handleDownload() {
    if (!documentId || !document) return;
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`/api/v1/documents/${documentId}/download`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Download failed");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const link = window.document.createElement("a");
      link.href = url;
      link.download = document.file_name;
      window.document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      setError("Failed to download document.");
    }
  }

  async function handleDelete() {
    if (!documentId) return;
    if (!window.confirm("Are you sure you want to delete this document?")) return;
    try {
      await apiClient.delete(`/documents/${documentId}`);
      navigate(-1);
    } catch {
      setError("Failed to delete document.");
    }
  }

  if (loading) {
    return (
      <div className="document-details-state">
        <Loader2
          size={20}
          className="document-loading-spinner"
        />
        <span>Loading document...</span>
      </div>
    );
  }

  if (error && !document) {
    return (
      <div className="document-details-state">
        <p>{error}</p>

        <button
          className="secondary-button"
          onClick={() => navigate(-1)}
        >
          Go back
        </button>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="document-details-state">
        Document not found.
      </div>
    );
  }

  const summary = getLatestAnalysis(
    analyses,
    "summary",
  );

  const classification = getLatestAnalysis(
    analyses,
    "classification",
  );

  const clauses = getLatestAnalysis(
    analyses,
    "clause_extraction",
  );

  const risks = getLatestAnalysis(
    analyses,
    "risk_analysis",
  );

  return (
    <div className="document-details-page">
      {/* BACK */}
      <button
        className="back-button document-back-button"
        onClick={() => navigate(-1)}
      >
        <ArrowLeft size={16} />
        Back
      </button>

      {/* DOCUMENT HEADER */}
      <div className="document-header">
        <div className="document-title-block">
          <div className="document-large-icon">
            <FileText size={25} />
          </div>

          <div>
            <div className="eyebrow">Legal Document</div>
            <h1 className="document-filename">{document.file_name}</h1>
            <div className="document-meta">
              <span>{document.document_type}</span>
              <span className="document-meta-dot">•</span>
              <span style={{ padding: "2px 6px", backgroundColor: "rgba(37, 99, 235, 0.2)", color: "#60a5fa", borderRadius: "4px", fontSize: "11px", fontWeight: 600 }}>
                {document.status || "COMPLETED"}
              </span>
              <span className="document-meta-dot">•</span>
              <span className="document-date">
                <Clock3 size={13} />
                {formatDate(document.uploaded_at)}
              </span>
            </div>
          </div>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <button
            className="primary-button"
            onClick={handleDownload}
            style={{ display: "flex", alignItems: "center", gap: "6px" }}
          >
            <Download size={16} /> Download File
          </button>
          <button
            className="secondary-button"
            onClick={handleDelete}
            style={{ display: "flex", alignItems: "center", gap: "6px", color: "#ef4444", borderColor: "rgba(239, 68, 68, 0.4)" }}
          >
            <Trash2 size={16} /> Delete
          </button>
        </div>
      </div>

      {/* AI LEGAL DISCLAIMER BANNER */}
      <div style={{
        margin: "16px 0 24px 0",
        padding: "10px 14px",
        backgroundColor: "rgba(30, 41, 59, 0.7)",
        border: "1px solid #334155",
        borderRadius: "8px",
        fontSize: "12px",
        color: "#94a3b8",
        display: "flex",
        alignItems: "center",
        gap: "10px",
      }}>
        <Scale size={16} style={{ color: "#60a5fa", flexShrink: 0 }} />
        <span><strong>AI Legal Disclaimer:</strong> LexFlow AI analysis outputs are decision-support tools designed to assist legal workflows and do not constitute formal legal advice or substitute for professional attorney evaluation.</span>
      </div>

      {/* ERROR */}
      {error && (
        <div className="analysis-error">
          <ShieldAlert size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* AI ACTIONS */}
      <section className="analysis-section">
        <div className="section-heading">
          <div>
            <div className="eyebrow">
              Artificial Intelligence
            </div>

            <h2>Document Analysis</h2>
          </div>

          {analyzing && (
            <span className="analysis-running">
              <Loader2 size={14} />
              Analyzing...
            </span>
          )}
        </div>

        <div className="analysis-actions">
          <AnalysisAction
            icon={<Sparkles size={18} />}
            title="Summarize"
            description="Generate an executive summary"
            active={activeAnalysis === "summary"}
            disabled={analyzing}
            onClick={() =>
              runAnalysis("summary")
            }
          />

          <AnalysisAction
            icon={<Scale size={18} />}
            title="Classify"
            description="Identify document category"
            active={
              activeAnalysis === "classification"
            }
            disabled={analyzing}
            onClick={() =>
              runAnalysis("classification")
            }
          />

          <AnalysisAction
            icon={<ListChecks size={18} />}
            title="Extract clauses"
            description="Identify important provisions"
            active={activeAnalysis === "clauses"}
            disabled={analyzing}
            onClick={() =>
              runAnalysis("clauses")
            }
          />

          <AnalysisAction
            icon={<ShieldAlert size={18} />}
            title="Analyze risks"
            description="Detect potential legal risks"
            active={activeAnalysis === "risks"}
            disabled={analyzing}
            danger
            onClick={() =>
              runAnalysis("risks")
            }
          />
        </div>
      </section>

      {/* RESULTS */}
      <section className="analysis-results">
        <div className="section-heading">
          <div>
            <div className="eyebrow">
              Intelligence
            </div>

            <h2>Analysis Results</h2>
          </div>

          <span className="section-count">
            {analyses.length}
          </span>
        </div>

        {analyses.length === 0 ? (
          <div className="analysis-empty">
            <div className="analysis-empty-icon">
              <Sparkles size={23} />
            </div>

            <h3>No analysis yet</h3>

            <p>
              Choose an AI analysis above to generate
              insights for this document.
            </p>
          </div>
        ) : (
          <div className="analysis-grid">
            {summary && (
              <AnalysisCard
                icon={<Sparkles size={18} />}
                title="Summary"
                type="summary"
                analysis={summary}
              />
            )}

            {classification && (
              <AnalysisCard
                icon={<Scale size={18} />}
                title="Classification"
                type="classification"
                analysis={classification}
              />
            )}

            {clauses && (
              <AnalysisCard
                icon={<ListChecks size={18} />}
                title="Clause Extraction"
                type="clause_extraction"
                analysis={clauses}
              />
            )}

            {risks && (
              <AnalysisCard
                icon={<ShieldAlert size={18} />}
                title="Risk Analysis"
                type="risk_analysis"
                analysis={risks}
                danger
              />
            )}
          </div>
        )}
      </section>

      {/* EXTRACTED TEXT */}
      <section className="document-text-section">
        <div className="section-heading">
          <div>
            <div className="eyebrow">
              Source Material
            </div>

            <h2>Extracted Text</h2>
          </div>
        </div>

        <div className="document-text">
          {document.extracted_text ? (
            document.extracted_text
          ) : (
            <div className="document-text-empty">
              No extracted text available.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

/* =========================================================
   ANALYSIS ACTION
========================================================= */

interface AnalysisActionProps {
  icon: ReactNode;
  title: string;
  description: string;
  active: boolean;
  disabled: boolean;
  danger?: boolean;
  onClick: () => void;
}

function AnalysisAction({
  icon,
  title,
  description,
  active,
  disabled,
  danger = false,
  onClick,
}: AnalysisActionProps) {
  return (
    <button
      type="button"
      className={`analysis-action ${
        active ? "analysis-action-active" : ""
      } ${danger ? "analysis-action-danger" : ""}`}
      onClick={onClick}
      disabled={disabled}
    >
      <div className="analysis-action-icon">
        {active ? (
          <Loader2
            size={18}
            className="analysis-spinner"
          />
        ) : (
          icon
        )}
      </div>

      <span className="analysis-action-content">
        <strong>{title}</strong>
        <small>{description}</small>
      </span>

      <span className="analysis-action-arrow">
        →
      </span>
    </button>
  );
}

/* =========================================================
   ANALYSIS CARD
========================================================= */

interface AnalysisCardProps {
  icon: ReactNode;
  title: string;
  type: string;
  analysis: Analysis;
  danger?: boolean;
}

function AnalysisCard({
  icon,
  title,
  type,
  analysis,
  danger = false,
}: AnalysisCardProps) {
  return (
    <article
      className={`analysis-card ${
        danger ? "analysis-card-danger" : ""
      }`}
    >
      <div className="analysis-card-header">
        <div className="analysis-card-icon">
          {icon}
        </div>

        <div className="analysis-card-title">
          <div>
            <h3>{title}</h3>

            <span className="analysis-card-type">
              {formatAnalysisType(type)}
            </span>
          </div>

          <span className="analysis-card-date">
            {formatDateTime(analysis.created_at)}
          </span>
        </div>
      </div>

      <div className="analysis-card-divider" />

      <div className="analysis-result">
        {formatResult(analysis.result, type)}
      </div>

      <div className="analysis-card-footer">
        <CheckCircle2 size={14} />
        <span>Analysis completed</span>
      </div>
    </article>
  );
}

/* =========================================================
   RESULT FORMATTER
========================================================= */

function formatResult(
  result: string,
  type: string,
): ReactNode {
  if (type === "summary") {
    return (
      <div className="analysis-text analysis-summary">
        {formatTextResult(result)}
      </div>
    );
  }

  try {
    const parsed = JSON.parse(result);

    if (type === "classification") {
      return formatClassificationResult(parsed);
    }

    if (type === "clause_extraction") {
      return formatClauseResult(parsed);
    }

    if (type === "risk_analysis") {
      return formatRiskResult(parsed);
    }

    return formatGenericJson(parsed);
  } catch {
    return (
      <div
        className={`analysis-text analysis-text-${type}`}
      >
        {formatTextResult(result)}
      </div>
    );
  }
}

/* =========================================================
   CLASSIFICATION
========================================================= */

function formatClassificationResult(
  value: Record<string, unknown>,
): ReactNode {
  const documentType =
    String(value.document_type || "Unknown");

  const confidenceValue =
    value.confidence ?? 0;

  const confidence =
    getConfidencePercent(confidenceValue);

  return (
    <div className="classification-result">
      <div className="classification-primary">
        <span className="analysis-json-key">
          Document type
        </span>

        <strong>{documentType}</strong>
      </div>

      <div className="classification-confidence">
        <div className="confidence-heading">
          <span className="analysis-json-key">
            Confidence
          </span>

          <span className="confidence-number">
            {confidence}%
          </span>
        </div>

        <div className="confidence-track">
          <div
            className="confidence-fill"
            style={{
              width: `${confidence}%`,
            }}
          />
        </div>

        <div className="confidence-label">
          <CheckCircle2 size={14} />

          <span>
            {getConfidenceLabel(confidence)}
          </span>
        </div>
      </div>
    </div>
  );
}

/* =========================================================
   CLAUSE EXTRACTION
========================================================= */

function formatClauseResult(
  value: Record<string, unknown>,
): ReactNode {
  const data =
    value.data &&
    typeof value.data === "object" &&
    !Array.isArray(value.data)
      ? (value.data as Record<string, unknown>)
      : value;

  const entries = Object.entries(data).filter(
    ([key]) =>
      key !== "document_type" &&
      key !== "confidence",
  );

  return (
    <div className="clause-result">
      {entries.map(([key, item]) => (
        <ClauseField
          key={key}
          fieldKey={key}
          value={item}
        />
      ))}
    </div>
  );
}

function ClauseField({
  fieldKey,
  value,
}: {
  fieldKey: string;
  value: unknown;
}) {
  const label = formatKey(fieldKey);

  if (fieldKey === "parties" && Array.isArray(value)) {
    return (
      <div className="clause-field">
        <div className="clause-field-heading">
          <Users size={15} />
          <span>{label}</span>
        </div>

        <div className="party-list">
          {value.map((party, index) => {
            const text = String(party);
            const separatorIndex =
              text.indexOf(":");

            if (separatorIndex > -1) {
              const role = text
                .slice(0, separatorIndex)
                .trim();

              const name = text
                .slice(separatorIndex + 1)
                .trim();

              return (
                <div
                  className="party-item"
                  key={index}
                >
                  <span>{role}</span>
                  <strong>{name}</strong>
                </div>
              );
            }

            return (
              <div
                className="party-item"
                key={index}
              >
                <strong>{text}</strong>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  if (
    fieldKey === "effective_date" ||
    fieldKey === "lease_start_date" ||
    fieldKey === "lease_end_date"
  ) {
    return (
      <div className="clause-field">
        <div className="clause-field-heading">
          <CalendarDays size={15} />
          <span>{label}</span>
        </div>

        <div className="clause-field-value">
          {String(value)}
        </div>
      </div>
    );
  }

  if (
    fieldKey === "payment_terms" ||
    fieldKey === "rent" ||
    fieldKey === "security_deposit"
  ) {
    return (
      <div className="clause-field">
        <div className="clause-field-heading">
          <IndianRupee size={15} />
          <span>{label}</span>
        </div>

        <div className="clause-field-value">
          {String(value)}
        </div>
      </div>
    );
  }

  if (
    fieldKey === "governing_law" ||
    fieldKey === "jurisdiction"
  ) {
    return (
      <div className="clause-field">
        <div className="clause-field-heading">
          <Gavel size={15} />
          <span>{label}</span>
        </div>

        <div className="clause-field-value">
          {String(value)}
        </div>
      </div>
    );
  }

  return (
    <div className="clause-field">
      <div className="clause-field-heading">
        <span>{label}</span>
      </div>

      <div className="clause-field-value">
        {formatStructuredValue(value)}
      </div>
    </div>
  );
}

/* =========================================================
   RISK ANALYSIS
========================================================= */

function formatRiskResult(
  value: Record<string, unknown>,
): ReactNode {
  const riskScore = value.risk_score;
  const riskLevel =
    String(value.risk_level || "Unknown");

  const risks = Array.isArray(value.risks)
    ? value.risks
    : [];

  return (
    <div className="risk-result">
      <div className="risk-overview">
        <div className="risk-score-block">
          <span className="analysis-json-key">
            Risk score
          </span>

          <strong>
            {riskScore !== undefined
              ? String(riskScore)
              : "—"}
          </strong>

          <span className="risk-score-caption">
            out of 100
          </span>
        </div>

        <div className="risk-level-block">
          <span className="analysis-json-key">
            Overall risk
          </span>

          <span
            className={`risk-level-badge ${getSeverityClass(
              riskLevel,
            )}`}
          >
            <AlertTriangle size={13} />
            {riskLevel}
          </span>
        </div>
      </div>

      <div className="risk-list">
        <div className="risk-list-heading">
          Identified risks
        </div>

        {risks.length === 0 ? (
          <div className="risk-empty">
            No specific risks were identified.
          </div>
        ) : (
          risks.map((risk, index) => (
            <RiskItemCard
              key={index}
              risk={risk}
            />
          ))
        )}
      </div>
    </div>
  );
}

function RiskItemCard({
  risk,
}: {
  risk: unknown;
}) {
  if (
    typeof risk !== "object" ||
    risk === null
  ) {
    return (
      <div className="risk-item">
        <span>{String(risk)}</span>
      </div>
    );
  }

  const item = risk as RiskItem;

  const severity =
    item.severity || "Unknown";

  return (
    <div className="risk-item">
      <div className="risk-item-header">
        <span
          className={`risk-severity ${getSeverityClass(
            severity,
          )}`}
        >
          {severity}
        </span>

        <span className="risk-item-icon">
          <AlertTriangle size={14} />
        </span>
      </div>

      <h4>
        {item.title || "Potential risk"}
      </h4>

      {item.description && (
        <p>{item.description}</p>
      )}

      {item.recommendation && (
        <div className="risk-recommendation">
          <span>Recommended action</span>
          <p>{item.recommendation}</p>
        </div>
      )}
    </div>
  );
}

/* =========================================================
   GENERIC JSON
========================================================= */

function formatGenericJson(
  value: Record<string, unknown>,
): ReactNode {
  return (
    <div className="analysis-json">
      {Object.entries(value).map(
        ([key, item]) => (
          <div
            className="analysis-json-item"
            key={key}
          >
            <span className="analysis-json-key">
              {formatKey(key)}
            </span>

            <div className="analysis-json-value">
              {formatStructuredValue(item)}
            </div>
          </div>
        ),
      )}
    </div>
  );
}

/* =========================================================
   TEXT RESULT
========================================================= */

function formatTextResult(result: string) {
  return result
    .split("\n")
    .map((line, index) => {
      const trimmed = line.trim();

      if (!trimmed) {
        return (
          <div
            className="analysis-spacer"
            key={index}
          />
        );
      }

      /*
       * Remove Markdown horizontal rules such as:
       * ========
       * -------
       * ******
       */
      if (
        /^[-_=*]{3,}$/.test(trimmed)
      ) {
        return null;
      }

      if (trimmed.startsWith("###")) {
        return (
          <h4 key={index}>
            {cleanMarkdown(
              trimmed.replace(
                /^###\s*/,
                "",
              ),
            )}
          </h4>
        );
      }

      if (trimmed.startsWith("##")) {
        return (
          <h3 key={index}>
            {cleanMarkdown(
              trimmed.replace(
                /^##\s*/,
                "",
              ),
            )}
          </h3>
        );
      }

      if (trimmed.startsWith("#")) {
        return (
          <h3 key={index}>
            {cleanMarkdown(
              trimmed.replace(
                /^#\s*/,
                "",
              ),
            )}
          </h3>
        );
      }

      if (
        trimmed.startsWith("- ") ||
        trimmed.startsWith("* ")
      ) {
        return (
          <div
            className="analysis-bullet"
            key={index}
          >
            <span className="analysis-bullet-marker">
              •
            </span>

            <span>
              {cleanMarkdown(
                trimmed.slice(2),
              )}
            </span>
          </div>
        );
      }

      if (/^\d+\.\s/.test(trimmed)) {
        return (
          <div
            className="analysis-numbered"
            key={index}
          >
            {cleanMarkdown(trimmed)}
          </div>
        );
      }

      return (
        <p key={index}>
          {cleanMarkdown(trimmed)}
        </p>
      );
    });
}

/* =========================================================
   STRUCTURED VALUE
========================================================= */

function formatStructuredValue(
  value: unknown,
): ReactNode {
  if (Array.isArray(value)) {
    return (
      <div className="analysis-json-list">
        {value.map((item, index) => (
          <div
            className="analysis-json-list-item"
            key={index}
          >
            <span>•</span>

            <span>
              {typeof item === "object" &&
              item !== null
                ? JSON.stringify(
                    item,
                    null,
                    2,
                  )
                : String(item)}
            </span>
          </div>
        ))}
      </div>
    );
  }

  if (
    typeof value === "object" &&
    value !== null
  ) {
    return (
      <pre className="analysis-json-object">
        {JSON.stringify(
          value,
          null,
          2,
        )}
      </pre>
    );
  }

  return String(value);
}

/* =========================================================
   HELPERS
========================================================= */

function getLatestAnalysis(
  analyses: Analysis[],
  type: string,
): Analysis | undefined {
  return analyses
    .filter(
      (analysis) =>
        analysis.analysis_type === type,
    )
    .sort(
      (a, b) =>
        new Date(
          b.created_at,
        ).getTime() -
        new Date(
          a.created_at,
        ).getTime(),
    )[0];
}

function formatDate(
  date?: string | null,
) {
  if (!date) {
    return "Date unavailable";
  }

  const parsed = new Date(date);

  if (Number.isNaN(parsed.getTime())) {
    return "Date unavailable";
  }

  return parsed.toLocaleDateString(
    undefined,
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    },
  );
}

function formatDateTime(
  date?: string | null,
) {
  if (!date) {
    return "Date unavailable";
  }

  const parsed = new Date(date);

  if (Number.isNaN(parsed.getTime())) {
    return "Date unavailable";
  }

  return parsed.toLocaleString(
    undefined,
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    },
  );
}

function formatKey(key: string) {
  return key
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      (char) =>
        char.toUpperCase(),
    );
}

function formatAnalysisType(
  type: string,
) {
  const labels: Record<
    string,
    string
  > = {
    summary:
      "Executive summary",

    classification:
      "Document classification",

    clause_extraction:
      "Clause intelligence",

    risk_analysis:
      "Legal risk assessment",
  };

  return (
    labels[type] ||
    formatKey(type)
  );
}

function cleanMarkdown(
  value: string,
) {
  return value
    .replace(
      /\*\*(.*?)\*\*/g,
      "$1",
    )
    .replace(
      /__(.*?)__/g,
      "$1",
    )
    .replace(
      /`(.*?)`/g,
      "$1",
    )
    .replace(
      /^>\s?/,
      "",
    );
}

function getConfidencePercent(
  value: unknown,
): number {
  const number =
    Number(value);

  if (
    Number.isNaN(number)
  ) {
    return 0;
  }

  if (number <= 1) {
    return Math.round(
      number * 100,
    );
  }

  return Math.round(
    Math.min(number, 100),
  );
}

function getConfidenceLabel(
  confidence: number,
) {
  if (confidence >= 90) {
    return "High confidence";
  }

  if (confidence >= 70) {
    return "Good confidence";
  }

  if (confidence >= 50) {
    return "Moderate confidence";
  }

  return "Low confidence";
}

function getSeverityClass(
  severity: string,
) {
  const normalized =
    severity
      .toLowerCase()
      .trim();

  if (
    normalized === "high" ||
    normalized === "critical" ||
    normalized === "severe"
  ) {
    return "severity-high";
  }

  if (
    normalized === "medium" ||
    normalized === "moderate"
  ) {
    return "severity-medium";
  }

  if (
    normalized === "low"
  ) {
    return "severity-low";
  }

  return "severity-neutral";
}

export default DocumentDetails;