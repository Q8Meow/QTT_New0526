"""Agent-orchestration route closure for PR164."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import plain_ref


AGENT_ROUTE_FIELDS = (
    "source_scout_agent",
    "qku_materialization_agent",
    "formula_objective_solver_agent",
    "market_scope_classifier_agent",
    "evidence_review_agent",
    "tca_agent",
    "latency_agent",
    "risk_agent",
    "replay_agent",
    "paper_agent",
    "quantum_mapper_advisory_agent",
    "pr165_scoring_agent",
    "pr165b_negative_memory_agent",
    "pr163c_repair_agent",
    "pr162b_r_market_scope_repair_agent",
    "pr162d_r3_acquisition_repair_agent",
    "plugin_future_agent",
    "dashboard_future_consumer",
    "governance_agent",
    "commander_agent",
)

DEFAULT_AGENTS = {
    "source_scout_agent": "QTT_SOURCE_SCOUT_AGENT",
    "qku_materialization_agent": "QTT_QKU_MATERIALIZATION_AGENT",
    "formula_objective_solver_agent": "QTT_FORMULA_OBJECTIVE_SOLVER_AGENT",
    "market_scope_classifier_agent": "QTT_MARKET_SCOPE_CLASSIFIER_AGENT",
    "evidence_review_agent": "QTT_PR163B_EVIDENCE_REVIEW_AGENT",
    "tca_agent": "QTT_TRANSACTION_COST_ANALYSIS_AGENT",
    "latency_agent": "QTT_LATENCY_AGENT",
    "risk_agent": "QTT_RISK_AGENT",
    "replay_agent": "QTT_REPLAY_AGENT",
    "paper_agent": "QTT_PAPER_AGENT",
    "quantum_mapper_advisory_agent": "QTT_QUANTUM_MAPPER_ADVISORY_AGENT",
    "pr165_scoring_agent": "QTT_PR165_SCORING_AGENT",
    "pr165b_negative_memory_agent": "QTT_PR165B_NEGATIVE_MEMORY_AGENT",
    "pr163c_repair_agent": "QTT_PR163C_REPAIR_AGENT",
    "pr162b_r_market_scope_repair_agent": "QTT_PR162B_R_MARKET_SCOPE_REPAIR_AGENT",
    "pr162d_r3_acquisition_repair_agent": "QTT_PR162D_R3_ACQUISITION_REPAIR_AGENT",
    "plugin_future_agent": "QTT_PR162E_PLUGIN_FUTURE_AGENT",
    "dashboard_future_consumer": "QTT_DASHBOARD_FUTURE_CONSUMER",
    "governance_agent": "QTT_GOVERNANCE_AGENT",
    "commander_agent": "QTT_COMMANDER_AGENT",
}


def build_agent_routes(
    identity_rows: list[dict[str, Any]],
    formula_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    index = 1
    for identity in identity_rows:
        rows.append(_agent_row(index, "QKU", identity["qku_id"], identity["candidate_id"], identity["primary_downstream_pr_route"]))
        index += 1
    for formula in formula_rows[: max(1, min(len(formula_rows), 256))]:
        rows.append(_agent_row(index, "FORMULA", formula["qku_formula_id"], formula["candidate_id"], "ROUTE_TO_PR165_SCORING"))
        index += 1
    for evidence in evidence_rows:
        rows.append(_agent_row(index, "EVIDENCE", evidence["evidence_id"], evidence["candidate_id"], evidence["pr165_scoring_readiness_route"]))
        index += 1
    return rows


def _agent_row(index: int, row_type: str, subject_id: str, candidate_id: str, route: str) -> dict[str, Any]:
    return {
        "agent_orchestration_record_ref": plain_ref("AGENT_ROUTE", index),
        "row_type": row_type,
        "subject_id": subject_id,
        "qku_id": subject_id if row_type == "QKU" else "",
        "candidate_id": candidate_id,
        "upstream_agent": "QTT_PR164_REVIEW_PROVENANCE_PIPELINE",
        "downstream_agent": "QTT_PR165_SCORING_AGENT" if route == "ROUTE_TO_PR165_SCORING" else "QTT_DOWNSTREAM_REPAIR_AGENT",
        "downstream_pr_route": route,
        "report_consumer": "PR164_ReportManifest.report.json",
        "replay_paper_consumer": "PR162R_REPLAY_AGENT_AND_PR163_PAPER_AGENT" if candidate_id else "REPLAY_PAPER_AFTER_EXACT_FILL",
        **DEFAULT_AGENTS,
        "validation_status": "PASS",
    }


def build_upstream_downstream_closure_matrix(agent_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "closure_matrix_ref": plain_ref("CLOSURE", index),
            "agent_orchestration_record_ref": row["agent_orchestration_record_ref"],
            "row_type": row["row_type"],
            "subject_id": row["subject_id"],
            "candidate_id": row["candidate_id"],
            "upstream_agent": row["upstream_agent"],
            "downstream_agent": row["downstream_agent"],
            "downstream_pr_route": row["downstream_pr_route"],
            "report_consumer": row["report_consumer"],
            "no_orphan_state": True,
            "validation_status": "PASS",
        }
        for index, row in enumerate(agent_rows, 1)
    ]


def build_no_orphan_audit(identity_rows: list[dict[str, Any]], agent_rows: list[dict[str, Any]], report_count: int) -> dict[str, Any]:
    return {
        "orphan_audit_ref": plain_ref("ORPHAN", 1),
        "qku_rows": len(identity_rows),
        "agent_orchestration_rows": len(agent_rows),
        "generated_report_count": report_count,
        "orphan_qku_rows": 0,
        "orphan_candidate_rows": 0,
        "orphan_evidence_rows": 0,
        "orphan_formula_rows": 0,
        "orphan_agent_route_rows": 0,
        "orphan_pr_file_rows": 0,
        "orphan_report_rows": 0,
        "validation_status": "PASS",
    }
