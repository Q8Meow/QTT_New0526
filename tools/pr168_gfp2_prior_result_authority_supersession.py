#!/usr/bin/env python3
"""Prior-result authority supersession for PR168-GFP2."""

from __future__ import annotations

from itertools import count
from typing import Any

from tools.pr168_gfp2_constants import DOWNGRADED_AUTHORITY_CLASS
from tools.pr168_gfp2_input_loader import GFP2Inputs


def prior_result_correction_rows(inputs: GFP2Inputs) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    sequence = count(1)
    for row in inputs.rp_positive_rows:
        rows.append(
            _prior_row(
                next(sequence),
                previous_pr_ref="PR168-RP",
                previous_report_ref="PR168_RP_ComputedPositiveEdgeCandidates.report.json",
                source=row,
                old_classification="COMPUTED_POSITIVE_EDGE",
                new_classification="PRIOR_FAKE_POSITIVE_CORRECTION_REQUIRED",
                result_family="positive",
                downgrade_reason="POSITIVE_RESULT_LACKS_ACCEPTED_REAL_MARKET_DATA_PROOF",
            )
        )
    for row in inputs.rp_negative_rows:
        rows.append(
            _prior_row(
                next(sequence),
                previous_pr_ref="PR168-RP",
                previous_report_ref="PR168_RP_ComputedNegativeEdgeCandidates.report.json",
                source=row,
                old_classification="COMPUTED_NEGATIVE_EDGE",
                new_classification="PRIOR_FAKE_NEGATIVE_REOPEN_REQUIRED",
                result_family="negative",
                downgrade_reason="NEGATIVE_RESULT_LACKS_ACCEPTED_REAL_MARKET_DATA_PROOF",
            )
        )
    for row in inputs.rp_neutral_rows:
        rows.append(
            _prior_row(
                next(sequence),
                previous_pr_ref="PR168-RP",
                previous_report_ref="PR168_RP_ComputedNeutralOrZeroEdgeCandidates.report.json",
                source=row,
                old_classification="COMPUTED_NEUTRAL_OR_ZERO_EDGE",
                new_classification="PRIOR_FAKE_NEUTRAL_OR_ZERO_UNPROVEN",
                result_family="neutral_zero",
                downgrade_reason="NEUTRAL_ZERO_RESULT_LACKS_ACCEPTED_REAL_DATA_NO_TRADE_PROOF",
            )
        )
    for row in inputs.rp_true_negative_rows:
        rows.append(
            _prior_row(
                next(sequence),
                previous_pr_ref="PR168-RP",
                previous_report_ref="PR168_RP_TrueNegativeAfterRecoveryExhaustion.report.json",
                source=row,
                old_classification="NEGATIVE_RECOVERY_EXHAUSTED_TRUE_NEGATIVE",
                new_classification="PRIOR_FAKE_NEGATIVE_REOPEN_REQUIRED",
                result_family="true_negative",
                downgrade_reason="TRUE_NEGATIVE_RESULT_LACKS_ACCEPTED_REAL_DATA_RECOVERY_EXHAUSTION_PROOF",
            )
        )
    for row in inputs.rank_no_trade_rows:
        rows.append(
            _prior_row(
                next(sequence),
                previous_pr_ref="PR168-RANK",
                previous_report_ref="PR168_RANK_NoTradeDominanceResults.report.json",
                source=row,
                old_classification="NO_TRADE_DOMINANT",
                new_classification="PRIOR_NO_TRADE_DOMINANCE_UNPROVEN",
                result_family="no_trade_dominance",
                downgrade_reason="NO_TRADE_DOMINANCE_LACKS_ACCEPTED_REAL_DATA_AND_FORMULA_PROOF",
            )
        )
    return rows


def fake_positive_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row["new_classification"] in {"PRIOR_FAKE_POSITIVE_CORRECTION_REQUIRED", "PRIOR_CHAMPION_AUTHORITY_REVOKED_PENDING_REAL_DATA"}]


def fake_negative_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row["new_classification"] == "PRIOR_FAKE_NEGATIVE_REOPEN_REQUIRED"]


def fake_neutral_zero_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row["new_classification"] in {"PRIOR_FAKE_NEUTRAL_OR_ZERO_UNPROVEN", "PRIOR_NO_TRADE_DOMINANCE_UNPROVEN"}]


def champion_strip_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stripped = []
    for row in rows:
        if row["previous_result_family"] in {"positive", "no_trade_dominance"} or row.get("champion_wording_only_flag"):
            copy = dict(row)
            copy["new_classification"] = "PRIOR_CHAMPION_AUTHORITY_REVOKED_PENDING_REAL_DATA"
            copy["champion_eligible"] = False
            copy["live_candidate_worthy"] = False
            stripped.append(copy)
    return stripped


def _prior_row(
    sequence: int,
    *,
    previous_pr_ref: str,
    previous_report_ref: str,
    source: dict[str, Any],
    old_classification: str,
    new_classification: str,
    result_family: str,
    downgrade_reason: str,
) -> dict[str, Any]:
    qku_id = source.get("qku_id") or str(source.get("candidate_id") or source.get("canonical_row_key") or "UNKNOWN")
    old_authority = "INTERNAL_COMPUTED_OR_RANKED_AUTHORITY"
    old_tier = source.get("evidence_tier") or "REPO_LOCAL_GENERATED_EVIDENCE"
    is_negative = result_family in {"negative", "true_negative"}
    is_positive = result_family == "positive"
    is_neutral = result_family in {"neutral_zero", "no_trade_dominance"}
    return {
        "previous_pr_ref": previous_pr_ref,
        "previous_report_ref": previous_report_ref,
        "previous_row_id": source.get("result_ref") or source.get("candidate_id") or source.get("negative_recovery_ref") or f"PR168_GFP2_PRIOR::{sequence:06d}",
        "previous_artifact_path": f"docs/master_plan/generated/{previous_report_ref}",
        "previous_result_family": result_family,
        "qku_id": qku_id,
        "formula_id": source.get("formula_id"),
        "candidate_id": source.get("candidate_id"),
        "algorithm_id": source.get("algorithm_id"),
        "quantum_mapping_id_if_any": source.get("quantum_candidate_id"),
        "old_classification": old_classification,
        "new_classification": new_classification,
        "old_authority_class": old_authority,
        "new_authority_class": DOWNGRADED_AUTHORITY_CLASS,
        "old_evidence_tier": old_tier,
        "new_evidence_tier": "PROVENANCE_DOWNGRADED_PRIOR_RESULT",
        "real_market_data_used_flag": False,
        "formula_executed_flag": result_family in {"positive", "negative"},
        "accepted_source_truth_flag": False,
        "synthetic_or_proxy_flag": False,
        "repo_local_generated_flag": True,
        "gap_filled_assumption_flag": True,
        "unverified_external_source_flag": False,
        "metadata_label_only_flag": False,
        "champion_wording_only_flag": result_family == "no_trade_dominance",
        "future_consumer_note_only_flag": False,
        "formula_plugin_ready_label_only_flag": False,
        "solver_or_quantum_compatible_label_only_flag": False,
        "gap_reason_codes": [
            "ACCEPTED_REAL_MARKET_DATA_ABSENT",
            "PRODUCTION_ACCEPTED_SOURCE_EVIDENCE_ABSENT",
            "PRIOR_RESULT_AUTHORITY_SUPERSEDED",
        ],
        "downgrade_reason": downgrade_reason,
        "supersedes_previous_authority_flag": True,
        "historical_record_preserved_flag": True,
        "requires_real_market_recompute_flag": True,
        "real_positive_claim_allowed_flag": False,
        "real_negative_claim_allowed_flag": False,
        "champion_eligible": False,
        "live_candidate_worthy": False,
        "profit_evidence_created_flag": False,
        "prior_fake_positive_flag": is_positive,
        "prior_fake_negative_flag": is_negative,
        "prior_fake_neutral_zero_flag": is_neutral,
        "downstream_repair_route": "PR168-RP2",
        "downstream_agent_owner": "Replay Paper Recompute Agent",
        "downstream_pr_refs": ["PR168-RP2", "PR168-RANK2"],
        "validator_refs": ["tools/pr168_gfp2_validator.py"],
        "test_refs": ["tests/pr168_gfp2"],
        "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
        "authority_class": DOWNGRADED_AUTHORITY_CLASS,
    }
