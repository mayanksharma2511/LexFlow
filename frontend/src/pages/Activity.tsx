import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import {
  Activity as ActivityIcon,
  ArrowLeft,
  Bot,
  FileText,
  Gavel,
  RefreshCw,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import apiClient from "../api/client";

interface AuditLog {
  id: string;
  user_id: string;
  action: string;
  entity_type: string;
  entity_id: string;
  details: string | null;
  created_at: string;
}

function Activity() {
  const navigate = useNavigate();

  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadActivity = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const token = localStorage.getItem("access_token");

      if (!token) {
        setError("You are not signed in.");
        return;
      }

      const response = await apiClient.get<AuditLog[]>(
        "/audit-logs",
      );

      setLogs(response.data);
    } catch (err: unknown) {
      console.error("Failed to load activity:", err);

      const status = (err as { response?: { status?: number } })?.response?.status;
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;

      if (status === 401) {
        setError(
          "Your session is no longer valid. Please sign in again.",
        );
      } else {
        setError(
          detail || "Unable to load activity.",
        );
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let ignore = false;

    async function initActivity() {
      try {
        setError("");

        const token = localStorage.getItem("access_token");

        if (!token) {
          if (!ignore) setError("You are not signed in.");
          return;
        }

        const response = await apiClient.get<AuditLog[]>(
          "/audit-logs",
        );

        if (!ignore) setLogs(response.data);
      } catch (err: unknown) {
        if (!ignore) {
          console.error("Failed to load activity:", err);
          const status = (err as { response?: { status?: number } })?.response?.status;
          const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;

          if (status === 401) {
            setError(
              "Your session is no longer valid. Please sign in again.",
            );
          } else {
            setError(
              detail || "Unable to load activity.",
            );
          }
        }
      } finally {
        if (!ignore) setLoading(false);
      }
    }

    initActivity();

    return () => {
      ignore = true;
    };
  }, []);

  function getActionLabel(action: string): string {
    const labels: Record<string, string> = {
      AI_SUMMARY: "AI summary generated",
      AI_CLASSIFICATION: "Document classified",
      AI_CLAUSE_EXTRACTION: "Clauses extracted",
      AI_RISK_ANALYSIS: "Risk analysis completed",
      AI_DOCUMENT_COMPARISON: "Documents compared",

      DOCUMENT_UPLOAD: "Document uploaded",
      DOCUMENT_DELETE: "Document deleted",

      CASE_CREATE: "Case created",
      CASE_UPDATE: "Case updated",
      CASE_DELETE: "Case deleted",

      LOGIN: "User signed in",
    };

    return (
      labels[action] ||
      action.replaceAll("_", " ").toLowerCase()
    );
  }

  function getActionIcon(log: AuditLog): ReactNode {
    if (log.action.startsWith("AI_")) {
      return <Bot size={17} />;
    }

    if (
      log.entity_type.toLowerCase() === "document"
    ) {
      return <FileText size={17} />;
    }

    if (log.entity_type.toLowerCase() === "case") {
      return <Gavel size={17} />;
    }

    if (log.action === "LOGIN") {
      return <UserRound size={17} />;
    }

    return <ActivityIcon size={17} />;
  }

  function formatDate(date: string) {
    return new Date(date).toLocaleDateString(
      undefined,
      {
        day: "2-digit",
        month: "short",
        year: "numeric",
      },
    );
  }

  function formatTime(date: string) {
    return new Date(date).toLocaleTimeString(
      undefined,
      {
        hour: "2-digit",
        minute: "2-digit",
      },
    );
  }

  if (loading) {
    return (
      <div className="activity-state">
        <RefreshCw
          size={18}
          className="activity-spinner"
        />
        <span>Loading activity...</span>
      </div>
    );
  }

  return (
    <div className="activity-page">
      <button
        className="back-button"
        onClick={() => navigate(-1)}
      >
        <ArrowLeft size={16} />
        Back
      </button>

      <div className="activity-header">
        <div>
          <div className="eyebrow">
            Security & Audit
          </div>

          <h1>Activity</h1>

          <p>
            A complete record of actions performed
            across your LexFlow workspace.
          </p>
        </div>

        <div className="audit-status">
          <ShieldCheck size={18} />

          <div>
            <strong>
              Audit logging active
            </strong>

            <span>
              Workspace activity is recorded.
            </span>
          </div>
        </div>
      </div>

      {error && (
        <div className="analysis-error">
          <span>{error}</span>

          <button
            type="button"
            onClick={loadActivity}
            className="activity-retry"
          >
            <RefreshCw size={14} />
            Retry
          </button>
        </div>
      )}

      <section className="activity-section">
        <div className="section-heading">
          <div>
            <div className="eyebrow">
              Workspace History
            </div>

            <h2>Recent Activity</h2>
          </div>

          <div className="section-heading-right">
            <span className="section-count">
              {logs.length}
            </span>

            <button
              type="button"
              className="activity-refresh"
              onClick={loadActivity}
              title="Refresh activity"
            >
              <RefreshCw size={15} />
            </button>
          </div>
        </div>

        {logs.length === 0 ? (
          <div className="activity-empty">
            <ActivityIcon size={24} />

            <h3>No activity yet</h3>

            <p>
              Actions performed in LexFlow will
              appear here.
            </p>
          </div>
        ) : (
          <div className="activity-list">
            {logs.map((log) => (
              <article
                className="activity-row"
                key={log.id}
              >
                <div className="activity-icon">
                  {getActionIcon(log)}
                </div>

                <div className="activity-main">
                  <strong>
                    {getActionLabel(log.action)}
                  </strong>

                  <span>
                    {log.details ||
                      `${log.entity_type} • ${log.entity_id}`}
                  </span>
                </div>

                <div className="activity-meta">
                  <span>
                    {formatDate(log.created_at)}
                  </span>

                  <span>
                    {formatTime(log.created_at)}
                  </span>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default Activity;