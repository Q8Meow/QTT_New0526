"""Mandatory PR161C QKU orchestration graph builder."""

from __future__ import annotations

from typing import Any

from .qku_id_builder import graph_node_id
from .qku_orchestration_edge_model import make_edge


def build_edges_for_record(record: dict[str, Any]) -> list[dict[str, Any]]:
    qku_id = str(record["qku_id"])
    source_path = str(record.get("qku_source_artifact_path") or "docs/master_plan/generated/PR161C_QKUFinalAssimilationSummary.report.json")
    upstream_type = str(record.get("_upstream_edge_type") or "UPSTREAM_QTT_DEFAULT_POLICY")
    upstream_id = str(record.get("_upstream_object_id") or "PR161C_OWNER_DEFAULT_POLICY")
    agents = list(record.get("qku_downstream_qtt_agents") or ["QTT_AGENT_RETRIEVAL_INDEX"])
    primary_agent = str(agents[0])
    edges = [
        make_edge(
            source_qku_id=qku_id,
            edge_direction="UPSTREAM",
            edge_type=upstream_type,
            serial=1,
            linked_object_type="ARTIFACT_PATH",
            linked_object_id=upstream_id,
            linked_object_path=source_path,
            linked_object_name=source_path.rsplit("/", 1)[-1],
            linkage_basis="PR161C_SOURCE_MEMBERSHIP_OR_FALLBACK_POLICY",
        ),
        make_edge(
            source_qku_id=qku_id,
            edge_direction="DOWNSTREAM",
            edge_type="DOWNSTREAM_QTT_AGENT",
            serial=1,
            linked_object_type="AGENT_ROLE",
            linked_object_id=primary_agent,
            linked_agent_role=primary_agent,
            linked_workflow_stage="QKU_AGENT_RETRIEVAL",
            linked_process_name="QKU_AGENT_CONSUMPTION",
            linkage_basis="PR161C_AGENT_WORKFLOW_ROUTER",
        ),
        make_edge(
            source_qku_id=qku_id,
            edge_direction="DOWNSTREAM",
            edge_type="DOWNSTREAM_REPLAY_PAPER_ROUTE",
            serial=2,
            linked_object_type="FUTURE_ROUTE_ENUM",
            linked_object_id=str(record.get("qku_replay_paper_route_ids", ["DOWNSTREAM_REPLAY_PAPER_QUEUE"])[0]),
            linked_workflow_stage="REPLAY_PAPER_PREP",
            linked_process_name="QKU_REPLAY_PAPER_ROUTING",
            linkage_basis="PR161C_REPLAY_PAPER_ROUTER",
        ),
        make_edge(
            source_qku_id=qku_id,
            edge_direction="DOWNSTREAM",
            edge_type="DOWNSTREAM_REPORT",
            serial=3,
            linked_object_type="ARTIFACT_PATH",
            linked_object_id="PR161C_QKUAgentRetrievalIndex.report.json",
            linked_object_path="docs/master_plan/generated/PR161C_QKUAgentRetrievalIndex.report.json",
            linked_object_name="PR161C_QKUAgentRetrievalIndex.report.json",
            linked_workflow_stage="QKU_AGENT_RETRIEVAL",
            linked_process_name="QKU_REPORT_INDEXING",
            linkage_basis="PR161C_AGENT_RETRIEVAL_REPORT_BRIDGE",
        ),
        make_edge(
            source_qku_id=qku_id,
            edge_direction="DOWNSTREAM",
            edge_type="DOWNSTREAM_VALIDATOR",
            serial=4,
            linked_object_type="VALIDATOR_PATH",
            linked_object_id="validate_pr161c_qku_residual_candidate_assimilation",
            linked_object_path="tools/validate_pr161c_qku_residual_candidate_assimilation.py",
            linked_object_name="validate_pr161c_qku_residual_candidate_assimilation.py",
            linked_workflow_stage="VALIDATION",
            linked_process_name="QKU_SEMANTIC_INTEGRITY_VALIDATION",
            linkage_basis="PR161C_VALIDATOR_BRIDGE",
        ),
    ]
    if record.get("qku_quantum_applicability") == "QUANTUM_APPLICABLE":
        edges.extend(
            [
                make_edge(
                    source_qku_id=qku_id,
                    edge_direction="DOWNSTREAM",
                    edge_type="DOWNSTREAM_QUANTUM_ADVISORY",
                    serial=5,
                    linked_object_type="AGENT_ROLE",
                    linked_object_id="QTT_QUANTUM_ADVISORY_AGENT",
                    linked_agent_role="QTT_QUANTUM_ADVISORY_AGENT",
                    linked_workflow_stage="QUANTUM_FORWARD_ADVISORY",
                    linked_process_name="QKU_QUANTUM_CANDIDATE_ROUTING",
                    linkage_basis="PR161B_QUANTUM_RESIDUAL_TRACE_OR_PR161A_QUANTUM_READY_FLAG",
                ),
                make_edge(
                    source_qku_id=qku_id,
                    edge_direction="DOWNSTREAM",
                    edge_type="DOWNSTREAM_CLASSICAL_BASELINE",
                    serial=6,
                    linked_object_type="FUTURE_ROUTE_ENUM",
                    linked_object_id="CLASSICAL_BASELINE_REQUIRED_ROUTE",
                    linked_workflow_stage="CLASSICAL_BASELINE_PREP",
                    linked_process_name="QKU_CLASSICAL_BASELINE_ROUTING",
                    linkage_basis="PR161C_QUANTUM_CLASSICAL_BASELINE_REQUIREMENT",
                ),
                make_edge(
                    source_qku_id=qku_id,
                    edge_direction="DOWNSTREAM",
                    edge_type="DOWNSTREAM_HYBRID_ARBITRATION",
                    serial=7,
                    linked_object_type="FUTURE_ROUTE_ENUM",
                    linked_object_id="HYBRID_ARBITRATION_REQUIRED_ROUTE",
                    linked_workflow_stage="HYBRID_ARBITRATION_PREP",
                    linked_process_name="QKU_HYBRID_ARBITRATION_ROUTING",
                    linkage_basis="PR161C_QUANTUM_HYBRID_ARBITRATION_REQUIREMENT",
                ),
            ]
        )
    return edges


def build_graph_nodes(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for record in records:
        nodes.append(
            {
                "qku_graph_node_id": graph_node_id(str(record["qku_id"])),
                "qku_id": record["qku_id"],
                "qku_type": record["qku_type"],
                "qku_name": record["qku_name"],
                "qku_graph_node_type": "PRIMARY_QKU_NODE",
                "qku_graph_materialized_flag": True,
                "qku_graph_isolated_flag": False,
            }
        )
    return nodes


def attach_graph(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    graph_records: list[dict[str, Any]] = []
    all_edges: list[dict[str, Any]] = []
    for record in records:
        clean = {key: value for key, value in record.items() if not key.startswith("_")}
        edges = build_edges_for_record(record)
        all_edges.extend(edges)
        upstream_count = sum(1 for edge in edges if edge["edge_direction"] == "UPSTREAM")
        downstream_count = sum(1 for edge in edges if edge["edge_direction"] == "DOWNSTREAM")
        clean.update(
            {
                "qku_graph_node_id": graph_node_id(str(record["qku_id"])),
                "qku_graph_edges": edges,
                "qku_graph_upstream_edge_count": upstream_count,
                "qku_graph_downstream_edge_count": downstream_count,
                "qku_graph_total_edge_count": len(edges),
                "qku_graph_isolated_flag": False,
                "qku_graph_isolated_reason_if_any": None,
                "qku_graph_materialized_flag": True,
            }
        )
        graph_records.append(clean)
    return graph_records, build_graph_nodes(graph_records), all_edges
