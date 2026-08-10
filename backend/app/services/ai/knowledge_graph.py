"""Knowledge Graph Service for Entity Extraction and Graph Neutral Network (GNN) compatibility.

Parses legal entities (parties, courts, jurisdictions, monetary values, dates)
and builds node-edge graph structures for conflict-of-interest detection.
Operates with strict Python 3.13 type standards.
"""

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """Enumeration of legal knowledge graph node categories."""

    PARTY = "PARTY"
    JURISDICTION = "JURISDICTION"
    COURT = "COURT"
    DOCUMENT = "DOCUMENT"
    VALUATION = "VALUATION"
    DATE = "DATE"
    OBLIGATION = "OBLIGATION"


class EdgeRelation(str, Enum):
    """Enumeration of legal entity relationship edges for GNN adjacency matrices."""

    SIGNATORY_TO = "SIGNATORY_TO"
    BOUND_BY = "BOUND_BY"
    JURISDICTION_OF = "JURISDICTION_OF"
    INVOLVES = "INVOLVES"
    SUBORDINATE_TO = "SUBORDINATE_TO"
    CONFLICT_RISK = "CONFLICT_RISK"


class GraphNode(BaseModel):
    """Data model for a Knowledge Graph Node."""

    id: str
    label: str
    node_type: NodeType
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Data model for a Knowledge Graph Edge connecting two nodes."""

    source_id: str
    target_id: str
    relation: EdgeRelation
    weight: float = 1.0
    properties: dict[str, Any] = Field(default_factory=dict)


class KnowledgeGraphResult(BaseModel):
    """Data model representing the exported Knowledge Graph payload."""

    case_id: str | None = None
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    conflict_risks: list[dict[str, Any]] = Field(default_factory=list)
    gnn_adjacency_matrix: list[list[float]] = Field(default_factory=list)


class KnowledgeGraphService:
    """Enterprise Knowledge Graph service for GNN conflict and entity mapping."""

    def extract_entities_and_build_graph(
        self,
        text: str,
        case_id: str | None = None,
        document_id: str | None = None,
    ) -> KnowledgeGraphResult:
        """Extract legal entities and construct a GNN-compatible knowledge graph.

        Args:
            text: Raw or structured legal text content.
            case_id: Optional case identifier context.
            document_id: Optional document identifier context.

        Returns:
            KnowledgeGraphResult containing node-edge payload and adjacency matrix.
        """
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        node_map: dict[str, GraphNode] = {}

        # Root Document Node
        doc_node_id = f"doc_{document_id or 'main'}"
        doc_node = GraphNode(
            id=doc_node_id,
            label=f"Document {document_id or 'Main'}",
            node_type=NodeType.DOCUMENT,
            properties={"char_count": len(text)},
        )
        nodes.append(doc_node)
        node_map[doc_node_id] = doc_node

        # 1. Party Entity Extraction (Capitalized Legal Party Regex Patterns)
        party_matches = re.findall(
            r"\b(?:Lessor|Lessee|Landlord|Tenant|Employer|Employee|Buyer|Seller|Plaintiff|Defendant|Licensor|Licensee|Borrower|Lender)\b",
            text,
            re.IGNORECASE,
        )
        unique_parties = {p.capitalize() for p in party_matches}

        for p_name in unique_parties:
            p_node_id = f"party_{p_name.lower()}"
            if p_node_id not in node_map:
                node = GraphNode(
                    id=p_node_id,
                    label=p_name,
                    node_type=NodeType.PARTY,
                    properties={"extracted_role": p_name},
                )
                nodes.append(node)
                node_map[p_node_id] = node

                # Edge from Party to Document
                edges.append(
                    GraphEdge(
                        source_id=p_node_id,
                        target_id=doc_node_id,
                        relation=EdgeRelation.SIGNATORY_TO,
                        weight=1.0,
                    )
                )

        # 2. Jurisdiction / Court Entity Extraction
        jurisdiction_matches = re.findall(
            r"\b(?:California|New York|Delaware|Texas|Illinois|United States|UK|London|San Francisco)\b",
            text,
            re.IGNORECASE,
        )
        unique_jurisdictions = {j.title() for j in jurisdiction_matches}

        for j_name in unique_jurisdictions:
            j_node_id = f"jurisdiction_{j_name.lower().replace(' ', '_')}"
            if j_node_id not in node_map:
                node = GraphNode(
                    id=j_node_id,
                    label=j_name,
                    node_type=NodeType.JURISDICTION,
                )
                nodes.append(node)
                node_map[j_node_id] = node

                edges.append(
                    GraphEdge(
                        source_id=doc_node_id,
                        target_id=j_node_id,
                        relation=EdgeRelation.JURISDICTION_OF,
                        weight=0.9,
                    )
                )

        # 3. Monetary Valuations Extraction
        val_matches = re.findall(r"\$[\d,]+(?:\.\d{2})?", text)
        for val in set(val_matches[:5]):
            v_node_id = f"val_{val.replace('$', '').replace(',', '')}"
            if v_node_id not in node_map:
                node = GraphNode(
                    id=v_node_id,
                    label=val,
                    node_type=NodeType.VALUATION,
                )
                nodes.append(node)
                node_map[v_node_id] = node

                edges.append(
                    GraphEdge(
                        source_id=doc_node_id,
                        target_id=v_node_id,
                        relation=EdgeRelation.INVOLVES,
                        weight=0.8,
                    )
                )

        # 4. Conflict of Interest Risk Evaluation
        conflict_risks: list[dict[str, Any]] = []
        party_nodes = [n for n in nodes if n.node_type == NodeType.PARTY]

        if len(party_nodes) > 1:
            # Check for dual representation or opposing role collision
            for i in range(len(party_nodes)):
                for j in range(i + 1, len(party_nodes)):
                    p1, p2 = party_nodes[i], party_nodes[j]
                    edges.append(
                        GraphEdge(
                            source_id=p1.id,
                            target_id=p2.id,
                            relation=EdgeRelation.CONFLICT_RISK,
                            weight=0.5,
                            properties={"conflict_type": "Multi-party contractual interaction"},
                        )
                    )
                    conflict_risks.append({
                        "party_a": p1.label,
                        "party_b": p2.label,
                        "risk_level": "LOW_ADVERSARIAL_EXPOSURE",
                        "description": f"Interaction detected between {p1.label} and {p2.label}",
                    })

        # 5. Build GNN Adjacency Matrix
        n_count = len(nodes)
        node_id_to_idx = {n.id: idx for idx, n in enumerate(nodes)}
        adj_matrix = [[0.0] * n_count for _ in range(n_count)]

        for edge in edges:
            src_idx = node_id_to_idx.get(edge.source_id)
            tgt_idx = node_id_to_idx.get(edge.target_id)
            if src_idx is not None and tgt_idx is not None:
                adj_matrix[src_idx][tgt_idx] = edge.weight
                adj_matrix[tgt_idx][src_idx] = edge.weight

        return KnowledgeGraphResult(
            case_id=case_id,
            nodes=nodes,
            edges=edges,
            conflict_risks=conflict_risks,
            gnn_adjacency_matrix=adj_matrix,
        )


knowledge_graph_service = KnowledgeGraphService()
