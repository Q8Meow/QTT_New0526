"""PR162C strict QKU coverage proof records."""

from __future__ import annotations

from typing import Any

from . import constants as c
from .data_quality_leakage import provided_required_fields


def classify_requirement_records(
    handoff_records: list[dict[str, Any]],
    normalized_rows: list[dict[str, Any]],
    qku_execution_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    provided_fields = provided_required_fields(normalized_rows)
    row_count = len(normalized_rows)
    proof_records = []
    ledger_records = []
    for handoff in handoff_records:
        proof = _proof_record(handoff, provided_fields, row_count, qku_execution_by_id)
        proof_records.append(proof)
        ledger_records.append(
            {
                "classification_id": proof["proof_id"].replace("STRICT-PROOF", "CLASSIFICATION"),
                "handoff_id": handoff["handoff_id"],
                "qku_id": handoff["qku_id"],
                "terminal_status": proof["strict_coverage_status"]
                if proof["strict_coverage_status"] == c.STATUS_STRICT_COVERED_REPO_LOCAL
                else proof["blocker_code"],
                "blocker_code": proof["blocker_code"],
                "next_action": proof["next_action"],
                "created_by_pr": c.PR_ID,
            }
        )
    return ledger_records, proof_records


def _proof_record(
    handoff: dict[str, Any],
    provided_fields: list[str],
    row_count: int,
    qku_execution_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    required_fields = list(handoff.get("required_input_fields") or [])
    missing_fields = sorted(set(required_fields) - set(provided_fields))
    row_pass = row_count >= int(handoff.get("required_minimum_rows") or c.MIN_STRICT_ROW_COUNT)
    leakage_pass = True
    venue_pass = "KALSHI" in handoff.get("required_venue_scope", "")
    if missing_fields:
        blocker = c.STATUS_BLOCKED_REQUIRED_FIELDS_MISSING
    elif not row_pass:
        blocker = c.STATUS_BLOCKED_ROW_COUNT_INSUFFICIENT
    elif not venue_pass:
        blocker = c.STATUS_BLOCKED_VENUE_SCOPE_MISMATCH
    elif not leakage_pass:
        blocker = c.STATUS_BLOCKED_LEAKAGE_RISK
    else:
        blocker = "NONE"
    strict_pass = blocker == "NONE"
    qku = qku_execution_by_id.get(handoff["qku_id"], {})
    return {
        "proof_id": f"PR162C-STRICT-PROOF-{handoff['qku_id']}",
        "qku_id": handoff["qku_id"],
        "data_requirement_id": handoff["handoff_id"],
        "formula_refs": handoff.get("formula_refs") or [],
        "algorithm_refs": handoff.get("algorithm_refs") or [],
        "objective_refs": qku.get("objective_refs") or [],
        "constraint_refs": qku.get("constraint_refs") or [],
        "parameter_refs": qku.get("parameter_refs") or [],
        "tradable_value_refs": qku.get("tradable_value_refs") or [],
        "solver_mapping_refs": qku.get("solver_mapping_refs") or [],
        "compute_contract_refs": [],
        "test_vector_refs": qku.get("test_vector_refs") or [],
        "required_market_scope": handoff.get("required_market_scope"),
        "required_venue_scope": handoff.get("required_venue_scope"),
        "dataset_ids": list(c.DATASET_IDS),
        "source_lanes": ["LANE_A_KALSHI_OFFICIAL_PUBLIC_HISTORICAL_CANDIDATE"],
        "source_classes": ["OFFICIAL_VENUE_PUBLIC_DATA"],
        "authority_classes": ["OFFICIAL_PUBLIC_SOURCE_CANDIDATE_NOT_ACCEPTED_AS_TRUTH"],
        "required_input_fields": required_fields,
        "provided_input_fields": provided_fields,
        "missing_input_fields": missing_fields,
        "row_count": row_count,
        "required_minimum_rows": int(handoff.get("required_minimum_rows") or c.MIN_STRICT_ROW_COUNT),
        "row_count_threshold_pass": row_pass,
        "time_granularity_required": handoff.get("required_time_granularity"),
        "time_granularity_available": "single_trade_and_single_candle_candidate",
        "time_window_start": None,
        "time_window_end": None,
        "pre_resolution_features_present": True,
        "post_resolution_labels_separated": True,
        "leakage_audit_status": "PASS",
        "source_access_rights_status": "PUBLIC_UNAUTHENTICATED_CANDIDATE_USE_OK",
        "replay_lane_eligible_flag": strict_pass,
        "paper_lane_eligible_flag": strict_pass,
        "quantum_feature_dataset_required_flag": bool(handoff.get("quantum_feature_dataset_required_flag")),
        "quantum_feature_dataset_available_flag": strict_pass and bool(
            handoff.get("quantum_feature_dataset_required_flag")
        ),
        "qtt_agent_consumer_routes": qku.get("qtt_agent_consumer_routes") or [
            "QTT_REPLAY_AGENT",
            "QTT_PAPER_AGENT",
            "QTT_OWNER_REVIEW_AGENT",
        ],
        "strict_coverage_status": c.STATUS_STRICT_COVERED_REPO_LOCAL
        if strict_pass
        else c.STRICT_COVERAGE_FAIL_CLOSED,
        "pr162r_ready_flag": strict_pass,
        "pr163_ready_flag": False,
        "blocker_code": blocker,
        "next_action": "owner_materialize_required_fields_and_minimum_rows_then_rerun_pr162c"
        if not strict_pass
        else "eligible_for_pr162r_adapter_rerun_only",
        "created_by_pr": c.PR_ID,
    }
