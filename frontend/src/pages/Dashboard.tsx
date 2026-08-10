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
import { NewCaseModal } from "../components/NewCaseModal";

interface Stats {
  active_cases: number;
  total_documents: number;
  total_ai_analyses: number;
  pending_review: number;
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

  const loadData = () => {
    apiClient
      .get<Stats>("/cases/stats/summary")
      .then((res) => setStats(res.data))
      .catch(() => {});

    apiClient
      .get<CaseItem[]>("/cases")
      .then((res) => setCases(res.data.slice(0, 4)))
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
          <h1>Good morning, Mayank.</h1>
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
              <p>Recent analysis activity</p>
            </div>

            <div className="ai-badge">
              <Sparkles size={13} />
              AI Engine
            </div>
          </div>

          <div className="ai-summary">
            <div className="ai-score">
              <span>Risk profile</span>
              <strong>Low</strong>
              <div className="risk-bar">
                <div />
              </div>
            </div>

            <p>Your latest document analysis found no critical contractual risks.</p>
          </div>

          <div className="analysis-items">
            <div className="analysis-item">
              <div className="analysis-icon">
                <Sparkles size={15} />
              </div>
              <div>
                <strong>Lease Agreement</strong>
                <span>Risk analysis completed</span>
              </div>
              <small>8m</small>
            </div>

            <div className="analysis-item">
              <div className="analysis-icon">
                <FileCheck2 size={15} />
              </div>
              <div>
                <strong>Employment Contract</strong>
                <span>Clause extraction completed</span>
              </div>
              <small>42m</small>
            </div>

            <div className="analysis-item">
              <div className="analysis-icon">
                <Sparkles size={15} />
              </div>
              <div>
                <strong>Vendor Agreement</strong>
                <span>Document classified</span>
              </div>
              <small>2h</small>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}