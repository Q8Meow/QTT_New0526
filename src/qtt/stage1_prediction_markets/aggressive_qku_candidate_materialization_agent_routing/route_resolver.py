"""Canonical PR162D agent route resolver."""

from __future__ import annotations

from typing import Any

from . import constants as c
from .candidate_status_model import route_status_for_progress
from .deterministic_id import deterministic_id


def route_for_qku(progress: dict[str, Any], *, quantum: bool = False) -> dict[str, Any]:
    status = route_status_for_progress(str(progress["pr162d_progress_status"]))
    routes = [
        "QKU_DATA_ACQUISITION_AGENT",
        "QKU_FORMULA_COMPUTE_ENGINE",
        "FORMULA_ALGORITHM_RUNTIME_CANDIDATE_MODE",
        "FEATURE_BUILDER",
        "REPLAY_PAPER_CANDIDATE_ROUTER",
        "REPLAY_ENGINE_INPUT_PREP",
        "PAPER_ENGINE_INPUT_PREP",
        "REPLAY_PAPER_RESULT_ANALYZER_INPUT_PREP",
        "OWNER_REVIEW_OPTIONAL",
    ]
    if quantum:
        routes.extend(
            [
                "QUANTUM_ADVISORY_AGENT",
                "QUANTUM_EXECUTION_HARNESS",
                "QUANTUM_CLASSICAL_HYBRID_COMPARATOR",
            ]
        )
        status = "AGENT_ROUTED_QUANTUM_CANDIDATE"
    if "RISK" in str(progress["qku_id"]).upper() or len(routes) % 2 == 1:
        routes.extend(["RISK_MANAGER_CANDIDATE_REVIEW", "CAPITAL_SIZING_CANDIDATE_REVIEW"])
    return {
        "route_id": deterministic_id("PR162D-AGENT-ROUTE", progress["qku_id"]),
        "qku_id": progress["qku_id"],
        "reinterpretation_ref": progress["reinterpretation_id"],
        "route_status": status,
        "agent_path_refs": sorted(set(routes), key=lambda item: c.AGENT_PATHS.index(item)),
        "replay_paper_candidate_route_flag": True,
        "candidate_trade_intent_only_flag": True,
        "execution_router_non_authority_preview_flag": True,
        "live_order_authority": False,
        "order_submission_allowed_flag": False,
        "profit_evidence_claim_flag": False,
        "created_by_pr": c.PR_ID,
    }


def route_records(progress_records: list[dict[str, Any]], quantum_qku_refs: set[str] | None = None) -> list[dict[str, Any]]:
    quantum_qku_refs = quantum_qku_refs or set()
    return [
        route_for_qku(record, quantum=record["qku_id"] in quantum_qku_refs)
        for record in progress_records
    ]


def filter_routes_for_agent(routes: list[dict[str, Any]], agent_path: str) -> list[dict[str, Any]]:
    return [record for record in routes if agent_path in record.get("agent_path_refs", [])]
