import { useEffect, useState } from "react";
import {
  ShieldAlert,
  FileText,
  Download,
  PieChart,
  BarChart3,
  ArrowLeft,
  Loader2,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import apiClient from "../api/client";
import "./AnalyticsDashboard.css";

interface AnalyticsData {
  total_cases: number;
  total_documents: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  classification_counts: Record<string, number>;
}

export function AnalyticsDashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAnalytics() {
      try {
        setLoading(true);
        const [casesRes, docsRes] = await Promise.all([
          apiClient.get<Array<{ priority?: string }>>("/cases"),
          apiClient.get<Array<{ document_type?: string }>>("/documents"),
        ]);

        const cases = casesRes.data || [];
        const docs = docsRes.data || [];

        let high = 0;
        let medium = 0;
        let low = 0;

        cases.forEach((c) => {
          const prio = (c.priority || "").toUpperCase();
          if (prio === "HIGH") high++;
          else if (prio === "MEDIUM") medium++;
          else low++;
        });

        const classCounts: Record<string, number> = {};
        docs.forEach((d) => {
          const type = d.document_type || "OTHER";
          classCounts[type] = (classCounts[type] || 0) + 1;
        });

        setData({
          total_cases: cases.length,
          total_documents: docs.length,
          high_risk_count: high,
          medium_risk_count: medium,
          low_risk_count: low,
          classification_counts: classCounts,
        });
      } catch {
        // Never show made-up numbers: show an error instead.
        setData(null);
        setLoadError("Could not load analytics. Please check that the server is running.");
      } finally {
        setLoading(false);
      }
    }

    loadAnalytics();
  }, []);

  const handleExportPDF = () => {
    setExporting(true);
    setTimeout(() => {
      const summaryText = `LEXFLOW WORKSPACE SUMMARY
Generated on: ${new Date().toLocaleString()}

===================================================================
1. MATTERS BY PRIORITY
-------------------------------------------------------------------
- Total matters: ${data?.total_cases ?? 0}
- High priority: ${data?.high_risk_count ?? 0}
- Medium priority: ${data?.medium_risk_count ?? 0}
- Low priority: ${data?.low_risk_count ?? 0}
(Priority is the level set by the user for each matter.)

2. DOCUMENTS BY TYPE
-------------------------------------------------------------------
- Total Managed Files: ${data?.total_documents ?? 0}
${Object.entries(data?.classification_counts || {})
  .map(([k, v]) => `- ${k}: ${v} document(s)`)
  .join("\n")}
===================================================================
`;

      const blob = new Blob([summaryText], { type: "text/plain;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "LexFlow_Workspace_Summary.txt";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setExporting(false);
    }, 600);
  };

  if (loading) {
    return (
      <div className="analytics-state">
        <Loader2 size={24} className="analytics-spinner" />
        <span>Loading analytics intelligence...</span>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="analytics-state">
        <span>{loadError}</span>
      </div>
    );
  }

  const totalRisks = (data?.high_risk_count || 0) + (data?.medium_risk_count || 0) + (data?.low_risk_count || 0);
  const highPct = totalRisks > 0 ? Math.round(((data?.high_risk_count || 0) / totalRisks) * 100) : 0;
  const medPct = totalRisks > 0 ? Math.round(((data?.medium_risk_count || 0) / totalRisks) * 100) : 0;
  const lowPct = totalRisks > 0 ? Math.round(((data?.low_risk_count || 0) / totalRisks) * 100) : 0;

  return (
    <div className="analytics-page">
      <button className="back-button" onClick={() => navigate(-1)}>
        <ArrowLeft size={16} /> Back
      </button>

      <div className="analytics-header">
        <div>
          <div className="eyebrow">Visual Analytics & Reporting</div>
          <h1>Matter Intelligence Analytics</h1>
          <p>Your matters by priority and your documents by type.</p>
        </div>

        <button className="primary-button" onClick={handleExportPDF} disabled={exporting}>
          {exporting ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
          <span>Export Summary</span>
        </button>
      </div>

      <div className="analytics-grid">
        {/* RISK HEATMAP CARD */}
        <section className="analytics-card">
          <div className="analytics-card-header">
            <div className="analytics-card-icon risk">
              <ShieldAlert size={20} />
            </div>
            <div>
              <h3>Matters by Priority</h3>
              <p>The priority set for each matter when it was created or edited</p>
            </div>
          </div>

          <div className="heatmap-container">
            <div className="heatmap-bar">
              <div className="heatmap-segment high" style={{ width: `${highPct}%` }} title={`High priority: ${highPct}%`} />
              <div className="heatmap-segment medium" style={{ width: `${medPct}%` }} title={`Medium priority: ${medPct}%`} />
              <div className="heatmap-segment low" style={{ width: `${lowPct}%` }} title={`Low priority: ${lowPct}%`} />
            </div>

            <div className="heatmap-legend">
              <div className="legend-item">
                <span className="dot high" />
                <span>High priority ({data?.high_risk_count || 0})</span>
              </div>
              <div className="legend-item">
                <span className="dot medium" />
                <span>Medium priority ({data?.medium_risk_count || 0})</span>
              </div>
              <div className="legend-item">
                <span className="dot low" />
                <span>Low priority ({data?.low_risk_count || 0})</span>
              </div>
            </div>
          </div>
        </section>

        {/* CLASSIFICATION BREAKDOWN */}
        <section className="analytics-card">
          <div className="analytics-card-header">
            <div className="analytics-card-icon docs">
              <BarChart3 size={20} />
            </div>
            <div>
              <h3>Documents by Type</h3>
              <p>The document type chosen when each file was uploaded</p>
            </div>
          </div>

          <div className="class-breakdown-list">
            {Object.entries(data?.classification_counts || {}).map(([type, count]) => {
              const pct = data?.total_documents ? Math.round((count / data.total_documents) * 100) : 0;
              return (
                <div className="class-breakdown-row" key={type}>
                  <div className="class-row-header">
                    <span>{type}</span>
                    <strong>{count} file(s) ({pct}%)</strong>
                  </div>
                  <div className="class-bar-track">
                    <div className="class-bar-fill" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>

      {/* METRIC HIGHLIGHTS */}
      <section className="analytics-summary-section">
        <div className="analytics-summary-card">
          <PieChart size={24} color="#60a5fa" />
          <div>
            <strong>{data?.total_cases || 0} Matters</strong>
            <span>Grouped above by the priority set for each matter</span>
          </div>
        </div>

        <div className="analytics-summary-card">
          <FileText size={24} color="#34d399" />
          <div>
            <strong>{data?.total_documents || 0} Documents</strong>
            <span>Grouped above by document type</span>
          </div>
        </div>
      </section>
    </div>
  );
}

export default AnalyticsDashboard;
