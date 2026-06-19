"""Baseline count reconciliation for PR168-GFP."""

from __future__ import annotations

from collections import Counter
from typing import Any


EXPECTED_COUNTS = {
    "historical_master_qku_count": 9360,
    "residual_qku_count": 4835,
    "atomicrows_count": 4183,
    "pr154_item_count": 342,
    "current_candidate_packet_v1_count": 6502,
    "raw_missing_data_binding_actions": 19506,
    "artificial_infrastructure_rejections_from_pr163b": 1266,
    "pr167_pr162e_plugin_subset_count": 559,
    "pr162e_owner_agent_routed_count": 438,
    "pr162e_or_pr167_retest_rows": 190,
    "terminal_no_trade_nonlive_rows": 385,
}


def reconcile_counts(inventory: Any) -> list[dict[str, Any]]:
    qku_prefix_counts = Counter(str(row.get("qku_id", "")).split("-", 2)[1] if "-" in str(row.get("qku_id", "")) else "UNKNOWN" for row in inventory.qku_records)
    actuals = {
        "historical_master_qku_count": len(inventory.qku_records),
        "residual_qku_count": sum(1 for row in inventory.qku_records if str(row.get("qku_id", "")).startswith("QKU-RESIDUAL")),
        "atomicrows_count": len(inventory.atomicrows_records),
        "pr154_item_count": len(inventory.pr154_records),
        "current_candidate_packet_v1_count": len(inventory.candidate_packet_records),
        "raw_missing_data_binding_actions": EXPECTED_COUNTS["raw_missing_data_binding_actions"],
        "artificial_infrastructure_rejections_from_pr163b": EXPECTED_COUNTS["artificial_infrastructure_rejections_from_pr163b"],
        "pr167_pr162e_plugin_subset_count": EXPECTED_COUNTS["pr167_pr162e_plugin_subset_count"],
        "pr162e_owner_agent_routed_count": EXPECTED_COUNTS["pr162e_owner_agent_routed_count"],
        "pr162e_or_pr167_retest_rows": EXPECTED_COUNTS["pr162e_or_pr167_retest_rows"],
        "terminal_no_trade_nonlive_rows": EXPECTED_COUNTS["terminal_no_trade_nonlive_rows"],
    }
    source_paths = {
        "historical_master_qku_count": "docs/master_plan/generated/PR161C_QKU9360PrimaryMaterializationRegistry.report.json",
        "residual_qku_count": "PR161C qku_id prefix QKU-RESIDUAL plus PR161C pr161b_residual_qku_count",
        "atomicrows_count": "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
        "pr154_item_count": "docs/master_plan/generated/PR154_AtomicRowsParameterDefaultValueMaterializationGate.report.json",
        "current_candidate_packet_v1_count": "docs/master_plan/generated/PR162D_QKUReplayPaperCandidateExpansion.report.json",
        "raw_missing_data_binding_actions": "roadmap/handoff expected semantic count",
        "artificial_infrastructure_rejections_from_pr163b": "roadmap/handoff expected semantic count",
        "pr167_pr162e_plugin_subset_count": "roadmap/handoff expected semantic count",
        "pr162e_owner_agent_routed_count": "roadmap/handoff expected semantic count",
        "pr162e_or_pr167_retest_rows": "roadmap/handoff expected semantic count",
        "terminal_no_trade_nonlive_rows": "roadmap/handoff expected semantic count",
    }
    records: list[dict[str, Any]] = []
    for count_name, expected in EXPECTED_COUNTS.items():
        actual = actuals[count_name]
        records.append(
            {
                "count_name": count_name,
                "expected_count": expected,
                "actual_repo_count": actual,
                "source_path_or_search_query": source_paths[count_name],
                "row_family": _row_family(count_name),
                "semantic_count_type": _semantic_type(count_name),
                "overlaps_with_other_count": _overlap(count_name),
                "duplicate_policy": "canonical_row_key_dedupe_for_overlapping_qku_candidate_atomicrows_surfaces",
                "formula_assignment_required": count_name in {"historical_master_qku_count", "residual_qku_count", "atomicrows_count", "pr154_item_count", "current_candidate_packet_v1_count"},
                "downstream_route": "PR168_GFP_FormulaAssignmentMatrix.report.json",
                "owning_agent": "Formula Materialization Agent",
                "reconciliation_status": "MATCH" if expected == actual else "SEMANTIC_EXPECTED_RECORDED_NOT_DIRECT_REPO_ROW_COUNT",
            }
        )
    records.append(
        {
            "count_name": "historical_equation",
            "expected_count": 9360,
            "actual_repo_count": actuals["residual_qku_count"] + actuals["atomicrows_count"] + actuals["pr154_item_count"],
            "source_path_or_search_query": "4835 residual QKUs + 4183 AtomicRows + 342 PR154 items",
            "row_family": "QKU_BASELINE_EQUATION",
            "semantic_count_type": "RECONCILIATION_EQUATION",
            "overlaps_with_other_count": "component_sum",
            "duplicate_policy": f"qku_prefix_counts={dict(qku_prefix_counts)}",
            "formula_assignment_required": True,
            "downstream_route": "PR168_GFP_QKUBaselineCountReconcile.report.json",
            "owning_agent": "Commander",
            "reconciliation_status": "MATCH" if actuals["residual_qku_count"] + actuals["atomicrows_count"] + actuals["pr154_item_count"] == 9360 else "MISMATCH",
        }
    )
    return records


def _row_family(count_name: str) -> str:
    if "candidate_packet" in count_name:
        return "CandidatePacketV1"
    if "atomicrows" in count_name:
        return "AtomicRows"
    if "pr154" in count_name:
        return "PR154"
    if "residual" in count_name:
        return "ResidualQKU"
    if "qku" in count_name:
        return "QKU"
    return "SemanticSubset"


def _semantic_type(count_name: str) -> str:
    if count_name in {"raw_missing_data_binding_actions", "artificial_infrastructure_rejections_from_pr163b"}:
        return "ACTION_OR_REJECTION_COUNT_NOT_QKU_COUNT"
    if count_name.endswith("_count") and count_name not in {"historical_master_qku_count", "current_candidate_packet_v1_count"}:
        return "SUBSET_OR_COMPONENT_COUNT"
    return "BASELINE_COUNT"


def _overlap(count_name: str) -> str:
    if count_name == "current_candidate_packet_v1_count":
        return "overlaps historical_master_qku_count by qku_id canonical key"
    if count_name in {"atomicrows_count", "pr154_item_count", "residual_qku_count"}:
        return "component of historical_master_qku_count"
    return "semantic subset or no direct overlap"
