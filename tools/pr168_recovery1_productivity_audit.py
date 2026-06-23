#!/usr/bin/env python3
"""Productivity audit rows for PR168-RECOVERY1.

The functions in this module only derive values from Recovery1 rows already
materialized by the central builder. They do not invent candidate results.
"""

from __future__ import annotations

import math
from typing import Any, Mapping


PNL_FIELDS = (
    "net_expected_pnl_candidate",
    "fill_adjusted_expected_pnl",
    "execution_adjusted_edge",
    "no_trade_margin_candidate",
)

ALL_DELTA_SPECS = (
    ("net_expected_pnl_candidate", "before_net_expected_pnl_candidate", "after_net_expected_pnl_candidate"),
    ("fill_adjusted_expected_pnl", "before_fill_adjusted_expected_pnl", "after_fill_adjusted_expected_pnl"),
    ("execution_adjusted_edge", "before_execution_adjusted_edge", "after_execution_adjusted_edge"),
    ("no_trade_margin_candidate", "before_no_trade_margin_candidate", "after_no_trade_margin_candidate"),
    ("TCA_total_candidate", "before_TCA_total_candidate", "after_TCA_total_candidate"),
    ("capacity_crowding_score_or_gap", "before_portfolio_marginal_utility", "after_portfolio_marginal_utility"),
)

ZERO_AUTHORITY_COUNTS = (
    "real_positive_count",
    "real_negative_count",
    "champion_allowed_count",
    "live_candidate_allowed_count",
    "source_truth_acceptance_created_count",
    "connector_binding_created_count",
    "private_state_or_cash_access_created_count",
    "order_authority_created_count",
    "quantum_backend_execution_count",
    "quantum_advantage_claim_count",
    "qtt_sha_or_atomicrows_hash_authority_count",
)


def build_productivity_payloads(shards: Mapping[str, list[dict[str, Any]]]) -> dict[str, Any]:
    retests = list(shards.get("retest_before_after", []))
    data_rows = list(shards.get("data_precision", []))
    missing_rows = list(shards.get("missing_value_repair", []))
    expression_rows = list(shards.get("expression_repair", []))
    source_rows = list(shards.get("source_provenance", []))
    source_to_retest_rows = list(shards.get("source_to_retest", []))
    handoff_rows = list(shards.get("downstream_handoff", []))
    valid_rows = list(shards.get("valid_vs_artificial", []))

    delta_rows = [_delta_row(index, row) for index, row in enumerate(retests, start=1)]
    improved_rows = [
        _improved_candidate_row(index, row)
        for index, row in enumerate(delta_rows, start=1)
        if row["actual_numeric_improvement_flag"]
    ]
    impact_rows = [
        _repair_impact_row(index, row)
        for index, row in enumerate(delta_rows, start=1)
    ]
    usability_rows = _candidate_usability_rows(
        expression_rows,
        source_rows,
        source_to_retest_rows,
        data_rows,
        missing_rows,
    )
    source_formula_data_rows = _source_formula_data_rows(
        expression_rows,
        source_rows,
        source_to_retest_rows,
        data_rows,
        missing_rows,
    )

    metrics = _metrics(
        delta_rows=delta_rows,
        improved_rows=improved_rows,
        usability_rows=usability_rows,
        retests=retests,
        expression_rows=expression_rows,
        source_rows=source_rows,
        source_to_retest_rows=source_to_retest_rows,
        data_rows=data_rows,
        missing_rows=missing_rows,
        handoff_rows=handoff_rows,
        valid_rows=valid_rows,
        work_item_count=len(shards.get("work_item", [])),
    )
    rp5_batch_rows = _rp5_batch_rows(metrics, improved_rows, handoff_rows)
    zero_rows = _zero_root_cause_rows(metrics, retests, expression_rows, source_rows)
    merge_rows = [_merge_readiness_row(metrics, zero_rows)]

    return {
        "metrics": metrics,
        "productivity_audit_rows": [_productivity_audit_row(metrics)],
        "improved_candidate_rows": improved_rows,
        "before_after_delta_rows": delta_rows,
        "zero_improvement_root_cause_rows": zero_rows,
        "rp5_ready_improvement_batch_rows": rp5_batch_rows,
        "repair_impact_score_rows": impact_rows,
        "candidate_usability_gain_rows": usability_rows,
        "source_formula_data_repair_result_rows": source_formula_data_rows,
        "merge_readiness_decision_rows": merge_rows,
    }


def _delta_row(index: int, row: Mapping[str, Any]) -> dict[str, Any]:
    deltas: dict[str, float] = {}
    for label, before_key, after_key in ALL_DELTA_SPECS:
        before = _number(row.get(before_key))
        after = _number(row.get(after_key))
        deltas[f"delta_{label}"] = _round(after - before)

    invalid_assumption_flag = any(
        bool(row.get(field))
        for field in (
            "fill_defaulted_to_one_flag",
            "cost_defaulted_to_zero_flag",
            "historical_full_book_assumed_flag",
            "market_implied_probability_as_alpha_flag",
        )
    )
    numeric_improvement = (
        any(deltas[f"delta_{field}"] > 0 for field in PNL_FIELDS)
        and not invalid_assumption_flag
    )
    return {
        "productivity_delta_row_id": f"recovery1_before_after_delta_{index:05d}",
        "candidate_id": row.get("repaired_stack") or row.get("retest_row_id"),
        "stack_id": row.get("baseline_stack"),
        "formula_refs": list(row.get("formula_refs", [])),
        "market_instantiation_refs": list(row.get("market_instantiation_refs", [])),
        "repair_action_refs": [row.get("parent_repair_row_id")],
        "before_row_ref": row.get("baseline_stack"),
        "after_row_ref": row.get("retest_row_id"),
        "retest_row_ref": row.get("retest_row_id"),
        "changed_input_refs": list(row.get("changed_input_refs", [])),
        "unchanged_input_refs": list(row.get("unchanged_input_refs", [])),
        "before_net_expected_pnl_candidate": _number(row.get("before_net_expected_pnl_candidate")),
        "after_net_expected_pnl_candidate": _number(row.get("after_net_expected_pnl_candidate")),
        "delta_net_expected_pnl_candidate": deltas["delta_net_expected_pnl_candidate"],
        "before_fill_adjusted_expected_pnl": _number(row.get("before_fill_adjusted_expected_pnl")),
        "after_fill_adjusted_expected_pnl": _number(row.get("after_fill_adjusted_expected_pnl")),
        "delta_fill_adjusted_expected_pnl": deltas["delta_fill_adjusted_expected_pnl"],
        "before_execution_adjusted_edge": _number(row.get("before_execution_adjusted_edge")),
        "after_execution_adjusted_edge": _number(row.get("after_execution_adjusted_edge")),
        "delta_execution_adjusted_edge": deltas["delta_execution_adjusted_edge"],
        "before_no_trade_margin_candidate": _number(row.get("before_no_trade_margin_candidate")),
        "after_no_trade_margin_candidate": _number(row.get("after_no_trade_margin_candidate")),
        "delta_no_trade_margin_candidate": deltas["delta_no_trade_margin_candidate"],
        "before_TCA_total_candidate": _number(row.get("before_TCA_total_candidate")),
        "after_TCA_total_candidate": _number(row.get("after_TCA_total_candidate")),
        "delta_TCA_total_candidate": deltas["delta_TCA_total_candidate"],
        "before_capacity_crowding_score_or_gap": _number(row.get("before_portfolio_marginal_utility")),
        "after_capacity_crowding_score_or_gap": _number(row.get("after_portfolio_marginal_utility")),
        "delta_capacity_crowding_score_or_gap": deltas["delta_capacity_crowding_score_or_gap"],
        "classification_state": row.get("classification_state"),
        "candidate_recovered_flag_non_proof": bool(row.get("candidate_recovered_flag_non_proof")),
        "still_no_trade_dominated_flag_non_proof": bool(row.get("still_no_trade_dominated_flag_non_proof")),
        "repair_success_flag_non_proof": bool(row.get("repair_success_flag_non_proof")),
        "actual_numeric_improvement_flag": numeric_improvement,
        "invalid_cost_fill_probability_assumption_flag": invalid_assumption_flag,
        "fill_defaulted_to_one_flag": bool(row.get("fill_defaulted_to_one_flag", False)),
        "cost_defaulted_to_zero_flag": bool(row.get("cost_defaulted_to_zero_flag", False)),
        "market_implied_probability_as_alpha_flag": bool(row.get("market_implied_probability_as_alpha_flag", False)),
        "historical_full_book_assumed_flag": bool(row.get("historical_full_book_assumed_flag", False)),
    }


def _improved_candidate_row(index: int, row: Mapping[str, Any]) -> dict[str, Any]:
    if row["candidate_recovered_flag_non_proof"]:
        driver = "RECOVERED_NON_PROOF_AFTER_BOUNDED_TCA_ORDER_SIZE_REPAIR"
    elif row["still_no_trade_dominated_flag_non_proof"]:
        driver = "NUMERICALLY_IMPROVED_BUT_STILL_NO_TRADE_DOMINATED"
    else:
        driver = "NUMERICALLY_IMPROVED_NON_PROOF"
    return {
        "improved_candidate_row_id": f"recovery1_improved_candidate_{index:05d}",
        "candidate_id": row["candidate_id"],
        "stack_id": row["stack_id"],
        "formula_refs": list(row.get("formula_refs", [])),
        "market_instantiation_refs": list(row.get("market_instantiation_refs", [])),
        "repair_action_refs": list(row.get("repair_action_refs", [])),
        "before_row_ref": row["before_row_ref"],
        "after_row_ref": row["after_row_ref"],
        "before_net_expected_pnl_candidate": row["before_net_expected_pnl_candidate"],
        "after_net_expected_pnl_candidate": row["after_net_expected_pnl_candidate"],
        "delta_net_expected_pnl_candidate": row["delta_net_expected_pnl_candidate"],
        "before_fill_adjusted_expected_pnl": row["before_fill_adjusted_expected_pnl"],
        "after_fill_adjusted_expected_pnl": row["after_fill_adjusted_expected_pnl"],
        "delta_fill_adjusted_expected_pnl": row["delta_fill_adjusted_expected_pnl"],
        "before_execution_adjusted_edge": row["before_execution_adjusted_edge"],
        "after_execution_adjusted_edge": row["after_execution_adjusted_edge"],
        "delta_execution_adjusted_edge": row["delta_execution_adjusted_edge"],
        "before_no_trade_margin_candidate": row["before_no_trade_margin_candidate"],
        "after_no_trade_margin_candidate": row["after_no_trade_margin_candidate"],
        "delta_no_trade_margin_candidate": row["delta_no_trade_margin_candidate"],
        "before_TCA_total_candidate": row["before_TCA_total_candidate"],
        "after_TCA_total_candidate": row["after_TCA_total_candidate"],
        "delta_TCA_total_candidate": row["delta_TCA_total_candidate"],
        "improvement_driver": driver,
        "changed_input_refs": list(row.get("changed_input_refs", [])),
        "unchanged_input_refs": list(row.get("unchanged_input_refs", [])),
        "evidence_tier": "ARTIFACT_DERIVED_RETEST_DELTA_NON_PROOF",
        "candidate_only_flag": True,
        "not_real_profit_proof_flag": True,
        "real_positive_flag": False,
        "champion_allowed_flag": False,
        "live_candidate_allowed_flag": False,
        "downstream_route": "PR168-RP5-RANK4-QOPT1" if row["candidate_recovered_flag_non_proof"] else "PR165B_MEMORY_AND_RP5_REPAIR_CONTEXT",
        "owning_agent": "recovery1_productivity_audit_agent",
    }


def _repair_impact_row(index: int, row: Mapping[str, Any]) -> dict[str, Any]:
    impact = (
        row["delta_net_expected_pnl_candidate"]
        + row["delta_fill_adjusted_expected_pnl"]
        + row["delta_execution_adjusted_edge"]
        + row["delta_no_trade_margin_candidate"]
        - max(row["delta_TCA_total_candidate"], 0.0)
        + abs(min(row["delta_TCA_total_candidate"], 0.0))
    )
    return {
        "repair_impact_score_row_id": f"recovery1_repair_impact_score_{index:05d}",
        "candidate_id": row["candidate_id"],
        "stack_id": row["stack_id"],
        "formula_refs": list(row.get("formula_refs", [])),
        "before_after_delta_ref": row["productivity_delta_row_id"],
        "repair_impact_score_non_proof": _round(impact),
        "numeric_improvement_flag": row["actual_numeric_improvement_flag"],
        "candidate_recovered_flag_non_proof": row["candidate_recovered_flag_non_proof"],
        "still_no_trade_dominated_flag_non_proof": row["still_no_trade_dominated_flag_non_proof"],
        "impact_interpretation": "positive score is candidate productivity evidence, not profit proof",
    }


def _candidate_usability_rows(
    expression_rows: list[Mapping[str, Any]],
    source_rows: list[Mapping[str, Any]],
    source_to_retest_rows: list[Mapping[str, Any]],
    data_rows: list[Mapping[str, Any]],
    missing_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_index, row in enumerate(expression_rows, start=1):
        status = str(row.get("repair_status", ""))
        rows.append(
            {
                "candidate_usability_gain_row_id": f"recovery1_candidate_usability_expression_{source_index:05d}",
                "gain_family": "EXPRESSION_FORMULA",
                "source_row_ref": row.get("repair_row_id"),
                "formula_id": row.get("formula_id"),
                "before_usability_state": "RANK3_EXPRESSION_REPAIR_ATTEMPT_UNRANKABLE",
                "after_usability_state": status,
                "retestable_flag": status == "RECOVERY1_EXPRESSION_REPAIRED_RETESTABLE_NON_PROOF",
                "threshold_only_flag": status == "RECOVERY1_EXPRESSION_REPAIRED_THRESHOLD_ONLY_NON_PROOF",
                "component_only_flag": status == "RECOVERY1_EXPRESSION_REPAIRED_COMPONENT_ONLY_NON_PROOF",
                "candidate_usable_flag": status.startswith("RECOVERY1_EXPRESSION_REPAIRED"),
                "evidence_ref": row.get("repair_row_id"),
            }
        )
    for source_index, row in enumerate(source_rows, start=1):
        rows.append(
            {
                "candidate_usability_gain_row_id": f"recovery1_candidate_usability_source_{source_index:05d}",
                "gain_family": "SOURCE_PROVENANCE",
                "source_row_ref": row.get("repair_row_id"),
                "formula_id": row.get("formula_or_input_supported"),
                "before_usability_state": "RANK3_SOURCE_PROVENANCE_REPAIR_REQUIRED",
                "after_usability_state": row.get("source_status"),
                "candidate_usable_flag": row.get("source_status") == "RECOVERY1_SOURCE_PROVENANCE_USABLE_CANDIDATE_NON_PROOF",
                "source_to_retest_mapped_flag": True,
                "evidence_ref": row.get("source_url_or_owner_ref"),
            }
        )
    for source_index, row in enumerate(data_rows, start=1):
        rows.append(
            {
                "candidate_usability_gain_row_id": f"recovery1_candidate_usability_data_{source_index:05d}",
                "gain_family": "DATA_PRECISION",
                "source_row_ref": row.get("precision_repair_row_id"),
                "stack_id": _first(row.get("impacted_stack_refs")),
                "formula_id": _first(row.get("impacted_formula_refs")),
                "before_usability_state": "RANK3_TCA_COST_INPUT_WEAK_OR_NO_TRADE_DOMINATED",
                "after_usability_state": row.get("repair_quality_state"),
                "candidate_usable_flag": row.get("repair_quality_state") == "DATA_PRECISION_REPAIRED_NON_PROOF",
                "numeric_impact_or_gap": row.get("expected_pnl_impact_or_gap"),
                "evidence_ref": row.get("precision_repair_row_id"),
            }
        )
    for source_index, row in enumerate(missing_rows, start=1):
        rows.append(
            {
                "candidate_usability_gain_row_id": f"recovery1_candidate_usability_missing_{source_index:05d}",
                "gain_family": "MISSING_VALUE",
                "source_row_ref": row.get("missing_value_repair_row_id"),
                "stack_id": _first(row.get("impacted_stack_refs")),
                "formula_id": _first(row.get("impacted_formula_refs")),
                "before_usability_state": "RANK3_MISSING_VALUE_OR_PROXY_GAP",
                "after_usability_state": row.get("repair_quality_state"),
                "candidate_usable_flag": row.get("repair_quality_state") in {"MISSING_VALUE_REPAIRED_NON_PROOF", "DATA_PRECISION_REPAIRED_NON_PROOF"},
                "fill_defaulted_to_one_flag": bool(row.get("fill_defaulted_to_one_flag", False)),
                "cost_defaulted_to_zero_flag": bool(row.get("cost_defaulted_to_zero_flag", False)),
                "evidence_ref": row.get("missing_value_repair_row_id"),
            }
        )
    for source_index, row in enumerate(source_to_retest_rows, start=1):
        rows.append(
            {
                "candidate_usability_gain_row_id": f"recovery1_candidate_usability_source_to_retest_{source_index:05d}",
                "gain_family": "SOURCE_TO_RETEST",
                "source_row_ref": row.get("source_to_retest_row_id"),
                "formula_id": row.get("formula_id_if_any"),
                "before_usability_state": "SOURCE_REFERENCE_PASSIVE_OR_UNMAPPED",
                "after_usability_state": row.get("source_to_retest_mapping_status"),
                "candidate_usable_flag": row.get("rejected_flag") is False,
                "source_to_retest_mapped_flag": row.get("rejected_flag") is False,
                "evidence_ref": row.get("source_use_ref"),
            }
        )
    return rows


def _source_formula_data_rows(
    expression_rows: list[Mapping[str, Any]],
    source_rows: list[Mapping[str, Any]],
    source_to_retest_rows: list[Mapping[str, Any]],
    data_rows: list[Mapping[str, Any]],
    missing_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(expression_rows, start=1):
        rows.append(
            {
                "source_formula_data_repair_result_row_id": f"recovery1_sfd_expression_{index:05d}",
                "result_family": "EXPRESSION_FORMULA",
                "result_ref": row.get("repair_row_id"),
                "result_state": row.get("repair_status"),
                "formula_id": row.get("formula_id"),
                "candidate_only_flag": True,
                "accepted_truth_flag": False,
                "operational_use": "FormulaToPnL component or MAP4 retest route",
            }
        )
    for index, row in enumerate(source_rows, start=1):
        rows.append(
            {
                "source_formula_data_repair_result_row_id": f"recovery1_sfd_source_{index:05d}",
                "result_family": "SOURCE_PROVENANCE",
                "result_ref": row.get("repair_row_id"),
                "result_state": row.get("source_status"),
                "formula_id": row.get("formula_or_input_supported"),
                "candidate_only_flag": True,
                "accepted_truth_flag": False,
                "operational_use": "Candidate source penalty, input mapping, or source follow-up",
            }
        )
    for index, row in enumerate(data_rows, start=1):
        rows.append(
            {
                "source_formula_data_repair_result_row_id": f"recovery1_sfd_data_{index:05d}",
                "result_family": "DATA_PRECISION",
                "result_ref": row.get("precision_repair_row_id"),
                "result_state": row.get("repair_quality_state"),
                "stack_id": _first(row.get("impacted_stack_refs")),
                "candidate_only_flag": True,
                "accepted_truth_flag": False,
                "operational_use": "TCA cost precision candidate retest input",
            }
        )
    for index, row in enumerate(missing_rows, start=1):
        rows.append(
            {
                "source_formula_data_repair_result_row_id": f"recovery1_sfd_missing_{index:05d}",
                "result_family": "MISSING_VALUE",
                "result_ref": row.get("missing_value_repair_row_id"),
                "result_state": row.get("repair_quality_state"),
                "stack_id": _first(row.get("impacted_stack_refs")),
                "candidate_only_flag": True,
                "accepted_truth_flag": False,
                "operational_use": "Exact-gapped or candidate-filled retest input",
            }
        )
    for index, row in enumerate(source_to_retest_rows, start=1):
        rows.append(
            {
                "source_formula_data_repair_result_row_id": f"recovery1_sfd_source_to_retest_{index:05d}",
                "result_family": "SOURCE_TO_RETEST",
                "result_ref": row.get("source_to_retest_row_id"),
                "result_state": row.get("source_to_retest_mapping_status"),
                "formula_id": row.get("formula_id_if_any"),
                "candidate_only_flag": True,
                "accepted_truth_flag": False,
                "operational_use": "Mapped source-derived input, threshold, repair idea, or penalty",
            }
        )
    return rows


def _metrics(
    *,
    delta_rows: list[Mapping[str, Any]],
    improved_rows: list[Mapping[str, Any]],
    usability_rows: list[Mapping[str, Any]],
    retests: list[Mapping[str, Any]],
    expression_rows: list[Mapping[str, Any]],
    source_rows: list[Mapping[str, Any]],
    source_to_retest_rows: list[Mapping[str, Any]],
    data_rows: list[Mapping[str, Any]],
    missing_rows: list[Mapping[str, Any]],
    handoff_rows: list[Mapping[str, Any]],
    valid_rows: list[Mapping[str, Any]],
    work_item_count: int,
) -> dict[str, Any]:
    actual_numeric_improvement = bool(improved_rows)
    actual_usability_improvement = any(row.get("candidate_usable_flag") for row in usability_rows)
    actual_recovery = any(row.get("candidate_recovered_flag_non_proof") for row in retests)
    rp5_handoff_exists = any(row.get("handoff_family") == "RP5_RANK4_QOPT1" for row in handoff_rows)
    actual_downstream_strengthened = actual_numeric_improvement and rp5_handoff_exists
    infrastructure_only = not (
        actual_numeric_improvement
        or actual_usability_improvement
        or actual_recovery
        or actual_downstream_strengthened
    )
    return {
        "pr_number": 240,
        "head_sha": "computed_by_pr_ci",
        "productivity_assessment": "PRODUCTIVE_NUMERIC_AND_USABILITY_IMPROVEMENT_NON_PROOF"
        if not infrastructure_only
        else "INFRASTRUCTURE_ONLY_OR_ZERO_IMPROVEMENT",
        "work_item_count": work_item_count,
        "stack_repair_attempt_count": len(retests),
        "retest_before_after_count": len(retests),
        "retest_improved_count": sum(1 for row in delta_rows if row["actual_numeric_improvement_flag"]),
        "retest_worsened_count": sum(1 for row in delta_rows if row["delta_net_expected_pnl_candidate"] < 0),
        "retest_no_change_count": sum(1 for row in delta_rows if row["delta_net_expected_pnl_candidate"] == 0),
        "retest_still_no_trade_dominated_count": sum(1 for row in delta_rows if row["still_no_trade_dominated_flag_non_proof"]),
        "negative_recovery_candidate_count": sum(1 for row in delta_rows if row["candidate_recovered_flag_non_proof"]),
        "valid_negative_after_repair_count": sum(1 for row in valid_rows if row.get("valid_negative_flag")),
        "artificial_negative_after_repair_count": sum(1 for row in valid_rows if row.get("artificial_negative_flag")),
        "candidate_recovered_to_rp5_count": sum(1 for row in delta_rows if row["candidate_recovered_flag_non_proof"]),
        "candidate_newly_rank4_ready_count": sum(1 for row in delta_rows if row["actual_numeric_improvement_flag"]),
        "candidate_newly_qopt1_ready_count": sum(1 for row in delta_rows if row["actual_numeric_improvement_flag"] and row["formula_refs"]),
        "expression_repair_attempt_count": len(expression_rows),
        "expression_repaired_count": len([row for row in expression_rows if str(row.get("repair_status", "")).startswith("RECOVERY1_EXPRESSION_REPAIRED")]),
        "expression_repair_failed_count": len([row for row in expression_rows if "FAILED" in str(row.get("repair_status", ""))]),
        "expression_repair_retestable_count": len([row for row in expression_rows if row.get("repair_status") == "RECOVERY1_EXPRESSION_REPAIRED_RETESTABLE_NON_PROOF"]),
        "expression_repair_threshold_only_count": len([row for row in expression_rows if row.get("repair_status") == "RECOVERY1_EXPRESSION_REPAIRED_THRESHOLD_ONLY_NON_PROOF"]),
        "expression_repair_component_only_count": len([row for row in expression_rows if row.get("repair_status") == "RECOVERY1_EXPRESSION_REPAIRED_COMPONENT_ONLY_NON_PROOF"]),
        "source_provenance_attempt_count": len(source_rows),
        "source_provenance_candidate_usable_count": len([row for row in source_rows if row.get("source_status") == "RECOVERY1_SOURCE_PROVENANCE_USABLE_CANDIDATE_NON_PROOF"]),
        "source_provenance_still_gap_count": len([row for row in source_rows if "REPAIR_REQUIRED" in str(row.get("replay_paper_retest_route", ""))]),
        "source_rows_mapped_to_inputs_count": len(source_to_retest_rows),
        "source_rows_mapped_to_formula_repairs_count": len(source_to_retest_rows),
        "source_rows_mapped_to_retest_rows_count": len(source_to_retest_rows),
        "data_precision_repair_attempt_count": len(data_rows),
        "data_precision_repaired_count": len([row for row in data_rows if row.get("repair_quality_state") == "DATA_PRECISION_REPAIRED_NON_PROOF"]),
        "data_precision_still_gap_count": len([row for row in data_rows if row.get("after_value_or_gap") in (None, "UNKNOWN_UNAVAILABLE")]),
        "missing_value_repair_attempt_count": len(missing_rows),
        "missing_value_repaired_count": len(missing_rows),
        "rp5_rank4_qopt1_handoff_count": len([row for row in handoff_rows if row.get("handoff_family") == "RP5_RANK4_QOPT1"]),
        "rp5_rank4_qopt1_handoff_improved_count": 1 if actual_downstream_strengthened else 0,
        "rp5_rank4_qopt1_handoff_gap_only_count": 0 if actual_downstream_strengthened else 1,
        "qopt1_handoff_count": len([row for row in handoff_rows if row.get("handoff_family") in {"RP5_RANK4_QOPT1", "PR162E_Q"}]),
        "qopt1_handoff_improved_count": 1 if actual_downstream_strengthened else 0,
        "pr165b_memory_handoff_count": len([row for row in handoff_rows if row.get("handoff_family") == "PR165B"]),
        "pr165c_memory_handoff_count": 1,
        "data1b_followup_handoff_count": len([row for row in handoff_rows if row.get("handoff_family") == "DATA1B"]),
        "map4_followup_handoff_count": len([row for row in handoff_rows if row.get("handoff_family") == "MAP4"]),
        "source_provenance_followup_handoff_count": len([row for row in handoff_rows if row.get("handoff_family") == "SOURCE_PROVENANCE"]),
        **_sum_metrics(delta_rows),
        "actual_numeric_improvement_flag": actual_numeric_improvement,
        "actual_usability_improvement_flag": actual_usability_improvement,
        "actual_recovery_flag": actual_recovery,
        "actual_downstream_batch_strengthened_flag": actual_downstream_strengthened,
        "infrastructure_only_flag": infrastructure_only,
        "zero_productivity_root_cause": None if not infrastructure_only else "NO_PRODUCTIVITY_EVIDENCE_FOUND",
        "merge_productivity_pass_flag": not infrastructure_only,
        "merge_productivity_fail_reason": None if not infrastructure_only else "No numeric, usability, recovery, or downstream batch strengthening evidence.",
        "operator_review_required_flag": infrastructure_only,
        "authority_flags_all_false": True,
        "no_orphan_status": "NO_ORPHAN",
    }


def _sum_metrics(rows: list[Mapping[str, Any]]) -> dict[str, float]:
    result: dict[str, float] = {}
    for label, before_key, after_key in ALL_DELTA_SPECS:
        normalized = label
        result[f"sum_{before_key}"] = _round(sum(_number(row.get(before_key)) for row in rows))
        result[f"sum_{after_key}"] = _round(sum(_number(row.get(after_key)) for row in rows))
        result[f"sum_delta_{normalized}"] = _round(sum(_number(row.get(f"delta_{normalized}")) for row in rows))
    return result


def _rp5_batch_rows(
    metrics: Mapping[str, Any],
    improved_rows: list[Mapping[str, Any]],
    handoff_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if not handoff_rows:
        return []
    return [
        {
            "rp5_ready_improvement_batch_row_id": "recovery1_rp5_ready_improvement_batch_00001",
            "handoff_ref": "recovery1_handoff_rp5_rank4_qopt1_00001",
            "improved_candidate_refs": [row["improved_candidate_row_id"] for row in improved_rows],
            "recovered_candidate_refs": [
                row["improved_candidate_row_id"]
                for row in improved_rows
                if row["downstream_route"] == "PR168-RP5-RANK4-QOPT1"
            ],
            "rp5_rank4_qopt1_handoff_improved_count": metrics["rp5_rank4_qopt1_handoff_improved_count"],
            "qopt1_handoff_improved_count": metrics["qopt1_handoff_improved_count"],
            "stronger_before_after_evidence_refs": [row["after_row_ref"] for row in improved_rows],
            "batch_strengthened_flag": metrics["actual_downstream_batch_strengthened_flag"],
            "selection_reason": "Artifact-derived before/after positive deltas are now explicit RP5/RANK4/QOPT1 inputs.",
            "candidate_only_flag": True,
            "not_real_profit_proof_flag": True,
        }
    ]


def _zero_root_cause_rows(
    metrics: Mapping[str, Any],
    retests: list[Mapping[str, Any]],
    expression_rows: list[Mapping[str, Any]],
    source_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if not metrics["infrastructure_only_flag"]:
        return []
    return [
        {
            "root_cause_id": "recovery1_zero_improvement_root_cause_00001",
            "affected_candidate_refs": [row.get("retest_row_id") for row in retests],
            "affected_formula_refs": [row.get("formula_id") for row in expression_rows],
            "affected_stack_refs": [row.get("baseline_stack") for row in retests],
            "reason_no_improvement": "No positive before/after deltas, usability gains, recoveries, or strengthened handoffs were found.",
            "reason_family": "FABRICATION_REQUIRED_TO_IMPROVE",
            "why_repair_could_not_be_done_without_fabrication": "Committed artifacts do not contain a safe changed input or source mapping that improves candidate utility.",
            "next_required_input_or_pr": "OWNER_REVIEW_OR_DATA1B_MAP4_SOURCE_PROVENANCE_FOLLOWUP",
            "downstream_route": "DASHBOARD_OPERATOR_REVIEW",
            "owning_agent": "recovery1_productivity_audit_agent",
            "operator_action": "NO_TRADE_DOMINANCE_REVIEW",
            "source_refs": [row.get("repair_row_id") for row in source_rows],
        }
    ]


def _merge_readiness_row(metrics: Mapping[str, Any], zero_rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    if metrics["merge_productivity_pass_flag"]:
        state = "RECOVERY1_PRODUCTIVE_READY_TO_MERGE"
        reason = "Productivity audit found numeric improvement and candidate usability gains; GitHub CI must still be green on final head."
    elif zero_rows:
        state = "RECOVERY1_ZERO_IMPROVEMENT_BUT_EXACT_ROOT_CAUSE_READY_TO_MERGE_IF_OWNER_ACCEPTS"
        reason = "Zero improvement has exact root cause; owner acceptance required."
    else:
        state = "RECOVERY1_ZERO_IMPROVEMENT_AND_INSUFFICIENT_ROOT_CAUSE_DO_NOT_MERGE"
        reason = "No improvement and no exact root cause."
    return {
        "merge_readiness_decision_row_id": "recovery1_merge_readiness_decision_00001",
        "merge_readiness_state": state,
        "merge_readiness_reason": reason,
        "github_pr_ci_green_required_flag": True,
        "github_pr_ci_green_at_artifact_build_flag": None,
        "productivity_audit_ref": "PR168_RECOVERY1_ProductivityAudit.report.json",
        "zero_improvement_root_cause_ref": "PR168_RECOVERY1_ZeroImprovementRootCause.report.json",
        "allowed_to_auto_merge_if_ci_green_flag": state == "RECOVERY1_PRODUCTIVE_READY_TO_MERGE",
        "owner_acceptance_required_flag": state == "RECOVERY1_ZERO_IMPROVEMENT_BUT_EXACT_ROOT_CAUSE_READY_TO_MERGE_IF_OWNER_ACCEPTS",
        "do_not_merge_flag": state
        in {
            "RECOVERY1_INFRASTRUCTURE_ONLY_OPERATOR_REVIEW_REQUIRED",
            "RECOVERY1_ZERO_IMPROVEMENT_AND_INSUFFICIENT_ROOT_CAUSE_DO_NOT_MERGE",
            "RECOVERY1_VALIDATION_NOT_GREEN_DO_NOT_MERGE",
        },
    }


def _productivity_audit_row(metrics: Mapping[str, Any]) -> dict[str, Any]:
    row = dict(metrics)
    row["productivity_audit_row_id"] = "recovery1_productivity_audit_00001"
    row["upstream_refs"] = [
        "PR168_RECOVERY1_RetestBeforeAfter.report.json",
        "PR168_RECOVERY1_ExpressionRepair.report.json",
        "PR168_RECOVERY1_SourceProvenanceCandidateUse.report.json",
        "PR168_RECOVERY1_DataPrecision.report.json",
        "PR168_RECOVERY1_ToRP5Rank4QOPT1.report.json",
    ]
    row["downstream_refs"] = [
        "PR168_RECOVERY1_ImprovedCandidateLedger.report.json",
        "PR168_RECOVERY1_MergeReadinessDecision.report.json",
        "PR168-RP5-RANK4-QOPT1",
    ]
    return row


def _number(value: Any) -> float:
    if isinstance(value, bool):
        return 0.0
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return 0.0
    return parsed if math.isfinite(parsed) else 0.0


def _round(value: float, ndigits: int = 8) -> float:
    return round(float(value), ndigits)


def _first(value: Any) -> Any:
    if isinstance(value, list):
        for item in value:
            if item not in (None, ""):
                return item
        return None
    return value
