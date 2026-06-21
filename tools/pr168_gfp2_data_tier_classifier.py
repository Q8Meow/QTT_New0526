#!/usr/bin/env python3
"""Evidence tier classification for PR168-GFP2."""

from __future__ import annotations

from typing import Any

from tools.pr168_gfp2_input_loader import GFP2Inputs, rp_gap_by_key, rp_negative_by_key


def data_tier_rows(inputs: GFP2Inputs) -> list[dict[str, Any]]:
    negatives = rp_negative_by_key(inputs)
    gaps = rp_gap_by_key(inputs)
    rows: list[dict[str, Any]] = []
    for assignment in inputs.assignments:
        key = str(assignment.get("canonical_row_key"))
        if key in negatives:
            tier = "REPO_LOCAL_GENERATED_EVIDENCE"
            reason = "PR168_RP_REPLAY_PAPER_COMPUTED_WITHOUT_PRODUCTION_ACCEPTED_SOURCE_EVIDENCE"
        elif key in gaps:
            tier = "GAP_ROUTED"
            reason = "FORMULA_INPUT_OR_MARKET_DATA_GAP_ROUTED"
        else:
            tier = "UNKNOWN_OR_UNVERIFIED"
            reason = "NO_ACCEPTED_REAL_DATA_PROOF_COMPONENTS_FOUND"
        rows.append(
            {
                "canonical_row_key": key,
                "qku_id": _qku_id(assignment),
                "formula_id": assignment.get("formula_id"),
                "input_data_tier": tier,
                "accepted_real_data_available_flag": False,
                "accepted_real_data_refs": [],
                "accepted_source_evidence_refs": [],
                "source_truth_accepted_flag": False,
                "synthetic_proxy_candidate_component_present_flag": tier != "GAP_ROUTED",
                "repo_local_generated_flag": tier == "REPO_LOCAL_GENERATED_EVIDENCE",
                "gap_reason_codes": [reason],
                "classification_after_gfp2": _classification_for_tier(tier),
                "downstream_repair_route": "PR168-RP2",
                "agent_owner": assignment.get("owning_agent") or "Formula Materialization Agent",
                "agent_consumers": ["Replay Paper Recompute Agent", "Ranking Agent"],
                "downstream_pr_refs": ["PR168-RP2", "PR168-RANK2"],
                "validator_refs": ["tools/pr168_gfp2_validator.py"],
                "test_refs": ["tests/pr168_gfp2"],
                "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
                "authority_class": "DATA_TIER_CLASSIFICATION_NOT_SOURCE_TRUTH",
            }
        )
    return rows


def accepted_real_data_discovery_rows(inputs: GFP2Inputs) -> list[dict[str, Any]]:
    if inputs.accepted_source_rows:
        return [
            {
                "accepted_ledger_record_id": row.get("accepted_ledger_record_id"),
                "source_class": row.get("source_class"),
                "source_authority_class": row.get("source_authority_class"),
                "production_external_fact_authority": bool(row.get("production_external_fact_authority")),
                "runtime_live_use_allowed_flag": bool(row.get("runtime_live_use_allowed_flag")),
                "profit_evidence_allowed_flag": bool(row.get("profit_evidence_allowed_flag")),
                "accepted_real_market_data_usable_for_pr168_gfp2_flag": False,
                "discovery_status": "TEST_FIXTURE_OR_NON_PRODUCTION_SOURCE_EVIDENCE_NOT_REAL_MARKET_PROOF",
                "downstream_pr_refs": ["PR168-RP2"],
                "agent_owner": "Source Evidence Agent",
                "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
            }
            for row in inputs.accepted_source_rows
        ]
    return [
        {
            "accepted_ledger_record_id": "NO_ACCEPTED_SOURCE_EVIDENCE_LEDGER_ROWS",
            "accepted_real_market_data_usable_for_pr168_gfp2_flag": False,
            "discovery_status": "NO_ACCEPTED_REAL_MARKET_DATA_FOUND",
            "downstream_pr_refs": ["PR168-RP2"],
            "agent_owner": "Source Evidence Agent",
            "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
        }
    ]


def _classification_for_tier(tier: str) -> str:
    if tier == "REPO_LOCAL_GENERATED_EVIDENCE":
        return "TRUE_NEGATIVE_UNDER_CURRENT_INTERNAL_EVIDENCE_ONLY"
    if tier == "GAP_ROUTED":
        return "GAP_ROUTED"
    return "UNKNOWN_OR_UNVERIFIED"


def _qku_id(row: dict[str, Any]) -> str:
    key = str(row.get("canonical_row_key") or "")
    if key.startswith("QKU::"):
        return key.removeprefix("QKU::")
    return key or "UNKNOWN_QKU_ID"
