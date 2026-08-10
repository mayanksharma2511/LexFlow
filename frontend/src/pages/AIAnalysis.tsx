import { useEffect, useState } from "react";
import {
  ArrowRight,
  FileText,
  Sparkles,
  ShieldAlert,
  Scale,
  ListChecks,
  Loader2,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import apiClient from "../api/client";
import "./AIAnalysis.css";

interface Document {
  id: string;
  file_name: string;
  document_type: string;
  case_id?: string;
}

function AIAnalysis() {
  const navigate = useNavigate();

  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDocuments() {
      try {
        setLoading(true);

        const response =
          await apiClient.get<Document[]>("/documents");

        setDocuments(response.data);
      } catch {
        setDocuments([]);
      } finally {
        setLoading(false);
      }
    }

    loadDocuments();
  }, []);

  return (
    <div className="ai-page">
      {/* =====================================================
          PAGE HEADER
      ===================================================== */}

      <header className="ai-page-header">
        <div>
          <div className="eyebrow">
            Artificial Intelligence
          </div>

          <h1>AI Analysis</h1>

          <p>
            Transform your legal documents into actionable
            intelligence with LexFlow AI.
          </p>
        </div>

        <div className="ai-header-badge">
          <Sparkles size={14} />
          <span>AI Powered</span>
        </div>
      </header>

      {/* =====================================================
          INTRO CARD
      ===================================================== */}

      <section className="ai-intro-card">
        <div className="ai-intro-glow" />

        <div className="ai-intro-icon">
          <Sparkles size={25} />
        </div>

        <div className="ai-intro-content">
          <div className="ai-intro-eyebrow">
            Legal Intelligence Workspace
          </div>

          <h2>
            Understand your documents faster.
          </h2>

          <p>
            Select a document below to generate an
            executive summary, classify the document,
            extract important clauses, or identify
            potential legal risks.
          </p>
        </div>

        <div className="ai-intro-mark">
          AI
        </div>
      </section>

      {/* =====================================================
          DOCUMENTS
      ===================================================== */}

      <section className="ai-documents-section">
        <div className="section-heading">
          <div>
            <div className="eyebrow">
              Your Documents
            </div>

            <h2>Select a document</h2>
          </div>

          <span className="section-count">
            {documents.length}
          </span>
        </div>

        {loading ? (
          <div className="ai-state">
            <Loader2
              size={16}
              className="ai-loading-spinner"
            />

            <span>Loading documents...</span>
          </div>
        ) : documents.length === 0 ? (
          <div className="ai-empty">
            <div className="ai-empty-icon">
              <FileText size={22} />
            </div>

            <h3>No documents available</h3>

            <p>
              Upload a legal document to start using
              LexFlow AI analysis.
            </p>
          </div>
        ) : (
          <div className="ai-document-grid">
            {documents.map((document) => (
              <article
                key={document.id}
                className="ai-document-card"
                onClick={() =>
                  navigate(
                    `/documents/${document.id}`,
                  )
                }
                role="button"
                tabIndex={0}
                onKeyDown={(event) => {
                  if (
                    event.key === "Enter" ||
                    event.key === " "
                  ) {
                    navigate(
                      `/documents/${document.id}`,
                    );
                  }
                }}
              >
                <div className="ai-document-icon">
                  <FileText size={20} />
                </div>

                <div className="ai-document-info">
                  <h3>{document.file_name}</h3>

                  <div className="ai-document-meta">
                    <span>
                      {document.document_type ||
                        "Legal Document"}
                    </span>

                    {document.case_id && (
                      <>
                        <span className="ai-meta-dot">
                          •
                        </span>

                        <span>
                          Case{" "}
                          {document.case_id.length > 18
                            ? `${document.case_id.slice(
                                0,
                                18,
                              )}...`
                            : document.case_id}
                        </span>
                      </>
                    )}
                  </div>
                </div>

                <div className="ai-document-arrow">
                  <ArrowRight size={16} />
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      {/* =====================================================
          CAPABILITIES
      ===================================================== */}

      <section className="ai-capabilities">
        <div className="section-heading">
          <div>
            <div className="eyebrow">
              Capabilities
            </div>

            <h2>What LexFlow AI can do</h2>
          </div>
        </div>

        <div className="ai-capability-grid">
          {/* SUMMARIZATION */}

          <div className="ai-capability-card">
            <div className="ai-capability-icon">
              <Sparkles size={19} />
            </div>

            <div className="ai-capability-content">
              <h3>Summarization</h3>

              <p>
                Generate concise summaries of lengthy
                legal documents.
              </p>
            </div>

            <div className="ai-capability-line" />
          </div>

          {/* CLASSIFICATION */}

          <div className="ai-capability-card">
            <div className="ai-capability-icon">
              <Scale size={19} />
            </div>

            <div className="ai-capability-content">
              <h3>Classification</h3>

              <p>
                Identify the type and category of a
                legal document.
              </p>
            </div>

            <div className="ai-capability-line" />
          </div>

          {/* CLAUSE EXTRACTION */}

          <div className="ai-capability-card">
            <div className="ai-capability-icon">
              <ListChecks size={19} />
            </div>

            <div className="ai-capability-content">
              <h3>Clause Extraction</h3>

              <p>
                Extract important contractual
                provisions and obligations.
              </p>
            </div>

            <div className="ai-capability-line" />
          </div>

          {/* RISK ANALYSIS */}

          <div className="ai-capability-card ai-capability-danger">
            <div className="ai-capability-icon">
              <ShieldAlert size={19} />
            </div>

            <div className="ai-capability-content">
              <h3>Risk Analysis</h3>

              <p>
                Identify potential legal risks and
                important contract concerns.
              </p>
            </div>

            <div className="ai-capability-line" />
          </div>
        </div>
      </section>
    </div>
  );
}

export default AIAnalysis;