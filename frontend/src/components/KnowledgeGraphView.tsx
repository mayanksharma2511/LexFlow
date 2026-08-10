import { useEffect, useState } from "react";
import {
  Network,
  Users,
  Scale,
  Landmark,
  FileText,
  CalendarDays,
  IndianRupee,
  ShieldAlert,
  Loader2,
  AlertCircle,
} from "lucide-react";
import apiClient from "../api/client";

interface GraphNode {
  id: string;
  label: string;
  node_type: string;
  properties?: Record<string, unknown>;
}

interface GraphEdge {
  source_id: string;
  target_id: string;
  relation: string;
  weight?: number;
}

interface ConflictRisk {
  source?: string;
  target?: string;
  risk_description?: string;
  severity?: string;
}

interface KnowledgeGraphData {
  case_id?: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  conflict_risks?: ConflictRisk[];
}

interface KnowledgeGraphViewProps {
  caseId: string;
}

export function KnowledgeGraphView({ caseId }: KnowledgeGraphViewProps) {
  const [graphData, setGraphData] = useState<KnowledgeGraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadKnowledgeGraph() {
      if (!caseId) return;
      try {
        setLoading(true);
        setError("");
        const res = await apiClient.get<KnowledgeGraphData>(
          `/cases/${caseId}/knowledge-graph`
        );
        setGraphData(res.data);
      } catch {
        setError("Failed to generate Knowledge Graph for this matter.");
      } finally {
        setLoading(false);
      }
    }
    loadKnowledgeGraph();
  }, [caseId]);

  if (loading) {
    return (
      <div
        style={{
          padding: "40px",
          textAlign: "center",
          backgroundColor: "#13161c",
          border: "1px solid rgba(255, 255, 255, 0.16)",
          borderRadius: "12px",
          color: "#94a3b8",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "12px",
        }}
      >
        <Loader2 size={24} className="animate-spin" style={{ color: "#c9a96e" }} />
        <span>Extracting legal entities and building Matter Knowledge Graph...</span>
      </div>
    );
  }

  if (error || !graphData) {
    return (
      <div
        style={{
          padding: "24px",
          backgroundColor: "rgba(239, 68, 68, 0.08)",
          border: "1px solid rgba(239, 68, 68, 0.25)",
          borderRadius: "8px",
          color: "#ef4444",
          fontSize: "13px",
          display: "flex",
          alignItems: "center",
          gap: "8px",
        }}
      >
        <AlertCircle size={18} />
        <span>{error || "Unable to load Knowledge Graph."}</span>
      </div>
    );
  }

  function getNodeIcon(type: string) {
    switch (type.toUpperCase()) {
      case "PARTY":
        return <Users size={15} style={{ color: "#60a5fa" }} />;
      case "COURT":
        return <Scale size={15} style={{ color: "#c9a96e" }} />;
      case "JURISDICTION":
        return <Landmark size={15} style={{ color: "#a855f7" }} />;
      case "DOCUMENT":
        return <FileText size={15} style={{ color: "#34d399" }} />;
      case "DATE":
        return <CalendarDays size={15} style={{ color: "#f59e0b" }} />;
      case "VALUATION":
      case "MONEY":
        return <IndianRupee size={15} style={{ color: "#10b981" }} />;
      default:
        return <Network size={15} style={{ color: "#94a3b8" }} />;
    }
  }

  return (
    <div
      style={{
        backgroundColor: "#13161c",
        border: "1px solid rgba(255, 255, 255, 0.16)",
        borderRadius: "12px",
        padding: "24px",
        marginTop: "20px",
      }}
    >
      {/* HEADER */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "20px",
          paddingBottom: "16px",
          borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
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
            <Network size={20} />
          </div>
          <div>
            <h3 style={{ margin: 0, fontSize: "16px", color: "#ffffff", fontWeight: 600 }}>
              Matter Entity Knowledge Graph
            </h3>
            <p style={{ margin: "2px 0 0 0", fontSize: "12px", color: "#94a3b8" }}>
              Automated entity relationships and conflict risk matrix
            </p>
          </div>
        </div>

        <div style={{ display: "flex", gap: "16px", fontSize: "12px", color: "#94a3b8" }}>
          <span>
            Nodes: <strong style={{ color: "#ffffff" }}>{graphData.nodes.length}</strong>
          </span>
          <span>
            Edges: <strong style={{ color: "#ffffff" }}>{graphData.edges.length}</strong>
          </span>
        </div>
      </div>

      {/* CONFLICT RISKS ALERT BANNER */}
      {graphData.conflict_risks && graphData.conflict_risks.length > 0 && (
        <div
          style={{
            marginBottom: "20px",
            padding: "14px",
            backgroundColor: "rgba(239, 68, 68, 0.08)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            borderRadius: "8px",
          }}
        >
          <h4
            style={{
              margin: "0 0 8px 0",
              fontSize: "13px",
              color: "#ef4444",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <ShieldAlert size={16} />
            Potential Conflict Risks Detected ({graphData.conflict_risks.length})
          </h4>
          {graphData.conflict_risks.map((risk, idx) => (
            <div key={idx} style={{ fontSize: "12px", color: "#fca5a5", marginTop: "4px" }}>
              • {risk.risk_description || `${risk.source} <-> ${risk.target}`}
            </div>
          ))}
        </div>
      )}

      {/* GRID CONTAINER */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
        {/* NODES LIST */}
        <div>
          <h4 style={{ margin: "0 0 12px 0", fontSize: "13px", color: "#c9a96e", fontWeight: 600 }}>
            Extracted Entities (Nodes)
          </h4>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px", maxHeight: "300px", overflowY: "auto" }}>
            {graphData.nodes.length === 0 ? (
              <span style={{ fontSize: "12px", color: "#64748b" }}>No nodes extracted yet</span>
            ) : (
              graphData.nodes.map((node) => (
                <div
                  key={node.id}
                  style={{
                    padding: "10px 12px",
                    backgroundColor: "#1e293b",
                    border: "1px solid rgba(255, 255, 255, 0.12)",
                    borderRadius: "6px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    {getNodeIcon(node.node_type)}
                    <span style={{ fontSize: "13px", color: "#ffffff", fontWeight: 500 }}>
                      {node.label}
                    </span>
                  </div>
                  <span
                    style={{
                      fontSize: "10px",
                      fontWeight: 600,
                      padding: "2px 6px",
                      borderRadius: "4px",
                      backgroundColor: "rgba(255, 255, 255, 0.08)",
                      color: "#94a3b8",
                      textTransform: "uppercase",
                    }}
                  >
                    {node.node_type}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* EDGES LIST */}
        <div>
          <h4 style={{ margin: "0 0 12px 0", fontSize: "13px", color: "#c9a96e", fontWeight: 600 }}>
            Legal Relationships (Edges)
          </h4>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px", maxHeight: "300px", overflowY: "auto" }}>
            {graphData.edges.length === 0 ? (
              <span style={{ fontSize: "12px", color: "#64748b" }}>No relation edges established</span>
            ) : (
              graphData.edges.map((edge, idx) => {
                const srcNode = graphData.nodes.find((n) => n.id === edge.source_id);
                const tgtNode = graphData.nodes.find((n) => n.id === edge.target_id);

                return (
                  <div
                    key={idx}
                    style={{
                      padding: "10px 12px",
                      backgroundColor: "#1e293b",
                      border: "1px solid rgba(255, 255, 255, 0.12)",
                      borderRadius: "6px",
                      fontSize: "12px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <span style={{ color: "#e2e8f0" }}>
                      {srcNode?.label || edge.source_id}
                    </span>

                    <span
                      style={{
                        padding: "2px 8px",
                        backgroundColor: "rgba(201, 169, 110, 0.15)",
                        color: "#c9a96e",
                        borderRadius: "4px",
                        fontWeight: 600,
                        fontSize: "10px",
                      }}
                    >
                      {edge.relation}
                    </span>

                    <span style={{ color: "#e2e8f0" }}>
                      {tgtNode?.label || edge.target_id}
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
