import { useEffect, useState } from "react";
import {
  ArrowUpRight,
  BriefcaseBusiness,
  Clock3,
  FileCheck2,
  FileText,
  MoreHorizontal,
  Plus,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import apiClient from "../api/client";
import { useCurrentUser } from "../api/currentUser";
import { NewCaseModal } from "../components/NewCaseModal";

interface Stats {
  active_cases: number;
  total_documents: number;
  total_ai_analyses: number;
  pending_review: number;
}

interface AuditEntry {
  id: string;
  action: string;
  details: string | null;
  created_at: string;
}

const AI_ACTION_LABELS: Record<string, string> = {
  AI_SUMMARY: "Summary generated",
  AI_CLASSIFICATION: "Document classified",
  AI_CLAUSE_EXTRACTION: "Clauses extracted",
  AI_RISK_ANALYSIS: "Risk analysis run",
  AI_DOCUMENT_COMPARISON: "Documents compared",
  AI_CASE_SYNTHESIS: "Case synthesis run",
};

function timeAgo(iso: string): string {
  // The API stores times in UTC without a timezone marker; read them as UTC.
  const utc = /[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`;
  const minutes = Math.max(0, Math.round((Date.now() - new Date(utc).getTime()) / 60000));
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h`;
  return `${Math.round(hours / 24)}d`;
}

function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

interface CaseItem {
  id: string;
  title: string;
  case_number: string;
  client_name: string;
  status: string;
  priority: string;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<Stats>({
    active_cases: 0,
    total_documents: 0,
    total_ai_analyses: 0,
    pending_review: 0,
  });
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [isNewCaseOpen, setIsNewCaseOpen] = useState(false);
  const [recentAI, setRecentAI] = useState<AuditEntry[]>([]);
  const currentUser = useCurrentUser();
  const firstName = currentUser?.full_name.split(" ")[0] || "";

  const loadData = () => {
    apiClient
      .get<Stats>("/cases/stats/summary")
      .then((res) => setStats(res.data))
      .catch(() => {});

    apiClient
      .get<CaseItem[]>("/cases")
      .then((res) => setCases(res.data.slice(0, 4)))
      .catch(() => {});

    apiClient
      .get<AuditEntry[]>("/audit-logs")
      .then((res) =>
        setRecentAI(
          res.data
            .filter((e) => e.action in AI_ACTION_LABELS)
            .sort((a, b) => b.created_at.localeCompare(a.created_at))
            .slice(0, 3),
        ),
      )
      .catch(() => {});


  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="dashboard">
      <NewCaseModal
        isOpen={isNewCaseOpen}
        onClose={() => setIsNewCaseOpen(false)}
        onSuccess={loadData}
      />

      <div className="dashboard-heading">
        <div>
          <div className="eyebrow">LEGAL WORKSPACE</div>
          <h1>{greeting()}{firstName ? `, ${firstName}` : ""}.</h1>
          <p>Here&apos;s what&apos;s happening across your legal workspace.</p>
        </div>

        <button className="primary-button" onClick={() => setIsNewCaseOpen(true)}>
          <Plus size={17} />
          New Case
        </button>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">
            <BriefcaseBusiness size={19} />
          </div>

          <div className="stat-content">
            <span>Active Cases</span>
            <strong>{stats.active_cases}</strong>
            <small>
              <TrendingUp size={13} />
              Live Workspace Data
            </small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <FileText size={19} />
          </div>

          <div className="stat-content">
            <span>Documents</span>
            <strong>{stats.total_documents}</strong>
            <small>
              <ArrowUpRight size={13} />
              Processed Files
            </small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon ai">
            <Sparkles size={19} />
          </div>

          <div className="stat-content">
            <span>AI Analyses</span>
            <strong>{stats.total_ai_analyses}</strong>
            <small>
              <Sparkles size={13} />
              Generated Insights
            </small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <Clock3 size={19} />
          </div>

          <div className="stat-content">
            <span>Pending Review</span>
            <strong>{stats.pending_review}</strong>
            <small className="warning-text">Requires attention</small>
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        <section className="panel cases-panel">
          <div className="panel-header">
            <div>
              <h2>Active Cases</h2>
              <p>Your most recently accessed matters</p>
            </div>

            <button className="text-button" onClick={() => navigate("/cases")}>
              View all
              <ArrowUpRight size={15} />
            </button>
          </div>

          <div className="case-list">
            {cases.length === 0 ? (
              <div style={{ padding: "24px 0", color: "#94a3b8", textAlign: "center" }}>
                No active cases found. Click &quot;New Case&quot; to initialize your first matter.
              </div>
            ) : (
              cases.map((item) => (
                <div
                  className="case-row"
                  key={item.id}
                  onClick={() => navigate(`/cases/${item.id}`)}
                  style={{ cursor: "pointer" }}
                >
                  <div className="case-symbol">
                    <BriefcaseBusiness size={18} />
                  </div>

                  <div className="case-info">
                    <strong>{item.title}</strong>
                    <span>
                      {item.case_number} · {item.client_name}
                    </span>
                  </div>

                  <div className="case-meta">
                    <span className={`status ${item.status.toLowerCase()}`}>
                      {item.status}
                    </span>

                    <span className={`priority ${item.priority.toLowerCase()}`}>
                      {item.priority}
                    </span>
                  </div>

                  <button className="more-button" onClick={(e) => { e.stopPropagation(); navigate(`/cases/${item.id}`); }}>
                    <MoreHorizontal size={18} />
                  </button>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="panel ai-panel">
          <div className="panel-header">
            <div>
              <h2>AI Intelligence</h2>
              <p>Your most recent AI analyses</p>
            </div>

            <div className="ai-badge">
              <Sparkles size={13} />
              AI Engine
            </div>
          </div>

          <div style={{ display: "grid", gap: "10px", padding: "16px 20px 20px" }}>
            {recentAI.length === 0 ? (
              <p style={{ color: "#94a3b8", fontSize: "14px" }}>No AI analyses yet. Open a document to run one.</p>
            ) : (
              recentAI.map((entry) => (
                <div
                  key={entry.id}
                  style={{ display: "flex", alignItems: "center", gap: "12px", padding: "10px 12px", border: "1px solid #2a2f3a", borderRadius: "8px" }}
                >
                  {entry.action === "AI_CLAUSE_EXTRACTION" ? <FileCheck2 size={15} color="#c9a96e" /> : <Sparkles size={15} color="#c9a96e" />}
                  <span style={{ flex: 1, fontSize: "14px", color: "#f8fafc" }}>{AI_ACTION_LABELS[entry.action]}</span>
                  <small style={{ color: "#94a3b8" }}>{timeAgo(entry.created_at)} ago</small>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
}