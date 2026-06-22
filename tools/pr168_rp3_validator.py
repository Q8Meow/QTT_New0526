#!/usr/bin/env python3
"""Strict validator for PR168-RP3 generated evidence."""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_rp3_config import (
    AUTHORITY_FALSE_FLAGS,
    EXPECTED_COMPUTABLE_FORMULA_COUNT,
    EXPECTED_DATA_REPAIR_COUNT,
    EXPECTED_EXPRESSION_REPAIR_COUNT,
    EXPECTED_SOURCE_REVIEW_COUNT,
    EXPECTED_TOTAL_FORMULA_COUNT,
    FORBIDDEN_STATE_VALUES,
    GENERATED_ROOT,
    REPORT_ALIASES,
    ROW_SHARDS,
    SCENARIO_FAMILIES,
    report_path,
    shard_path,
)
from tools.pr168_rp3_report_writer import read_json, read_jsonl


class RP3ValidationError(AssertionError):
    """Raised when PR168-RP3 evidence violates the RP3 contract."""


def _fail(message: str) -> None:
    raise RP3ValidationError(message)


def _require(condition: bool, message: str) -> None:
    if not condition:
        _fail(message)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _load_reports() -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    seen_physical: set[str] = set()
    for report_id, physical in REPORT_ALIASES.items():
        path = report_path(report_id)
        _require(path.exists(), f"missing report {physical}")
        payload = read_json(path)
        _require(payload.get("logical_report_id") == report_id, f"{physical} has wrong logical_report_id")
        _require(payload.get("physical_filename") == physical, f"{physical} has wrong physical_filename")
        _require(payload.get("manual_edit_allowed_flag") is False, f"{physical} allows manual edit")
        _require(payload.get("no_orphan_status") == "NO_ORPHAN", f"{physical} is orphaned")
        _assert_no_authority(payload, f"report:{physical}")
        reports[report_id] = payload
        seen_physical.add(physical)
    _require(len(seen_physical) == len(REPORT_ALIASES), "duplicate physical report filename")
    return reports


def _load_rows() -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {}
    for key, filename in ROW_SHARDS.items():
        path = shard_path(key)
        manifest_path = path.with_suffix(".manifest.json")
        _require(path.exists(), f"missing shard {filename}")
        _require(manifest_path.exists(), f"missing shard manifest {filename}")
        materialized = read_jsonl(path)
        manifest = read_json(manifest_path)
        _require(manifest.get("row_count") == len(materialized), f"{filename} manifest row_count mismatch")
        _assert_no_authority(manifest, f"manifest:{filename}")
        rows[key] = materialized
    return rows


def _assert_no_authority(row: Mapping[str, Any], label: str) -> None:
    for flag, expected in AUTHORITY_FALSE_FLAGS.items():
        if flag in row:
            _require(row.get(flag) is expected, f"{label} authority flag {flag} is {row.get(flag)!r}")
    for key, value in row.items():
        if isinstance(value, str):
            _require(value not in FORBIDDEN_STATE_VALUES, f"{label} contains forbidden state {value}")
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    _require(item not in FORBIDDEN_STATE_VALUES, f"{label} contains forbidden state {item}")


def _assert_route_fields(row: Mapping[str, Any], label: str) -> None:
    _require(row.get("no_orphan_status") == "NO_ORPHAN", f"{label} missing no-orphan status")
    _require(bool(row.get("upstream_refs")), f"{label} missing upstream refs")
    _require(bool(row.get("downstream_consumers")), f"{label} missing downstream consumers")
    _require(bool(row.get("downstream_pr_refs")), f"{label} missing downstream PR refs")
    _require(bool(row.get("owning_agent")), f"{label} missing owning agent")
    _require(bool(row.get("validator_refs")), f"{label} missing validator refs")
    _require(bool(row.get("test_refs")), f"{label} missing test refs")
    _require(bool(row.get("authority_class")), f"{label} missing authority class")
    _assert_no_authority(row, label)


def _rows_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, Mapping[str, Any]]:
    return {str(row.get(key)): row for row in rows if row.get(key)}


def _assert_numeric_fields(row: Mapping[str, Any], fields: Iterable[str], label: str) -> None:
    for field in fields:
        _require(field in row, f"{label} missing numeric field {field}")
        _require(_is_number(row[field]), f"{label} {field} is not finite numeric: {row.get(field)!r}")


def run_validation() -> dict[str, Any]:
    reports = _load_reports()
    rows = _load_rows()
    for key, shard_rows in rows.items():
        for index, row in enumerate(shard_rows, start=1):
            _assert_route_fields(row, f"{key}[{index}]")

    final = reports["PR168_RP3_FinalSummary"]["records"]
    _assert_final_summary(final)
    _assert_formula_universe(rows)
    _assert_market_instantiation(rows)
    _assert_formula_execution(rows)
    _assert_replay_paper(rows)
    _assert_tca_fill_cost(rows)
    _assert_scenarios_guards_and_norms(rows)
    _assert_rank2_stack_and_quantum(rows)
    _assert_repairs_quality_success(rows)
    _assert_numeric_evidence(rows)
    return {
        "status": "passed",
        "reports": len(reports),
        "shards": len(rows),
        "formula_count": final["map3_formula_universe_count"],
        "rank2_rows": final["rank2_evidence_handoff_count"],
    }


def _assert_final_summary(final: Mapping[str, Any]) -> None:
    expected = {
        "pr237_merged_preflight_passed_flag": True,
        "map3_formula_universe_count": EXPECTED_TOTAL_FORMULA_COUNT,
        "map3_replay_paper_computable_formula_count": EXPECTED_COMPUTABLE_FORMULA_COUNT,
        "map3_expression_repair_formula_count": EXPECTED_EXPRESSION_REPAIR_COUNT,
        "map3_source_evidence_review_formula_count": EXPECTED_SOURCE_REVIEW_COUNT,
        "map3_data_repair_formula_count": EXPECTED_DATA_REPAIR_COUNT,
        "pr236_best_formula_rows_treated_as_formula_definitions_flag": False,
        "real_positive_count": 0,
        "real_negative_count": 0,
        "champion_allowed_count": 0,
        "live_candidate_allowed_count": 0,
        "source_truth_acceptance_created_count": 0,
        "connector_binding_created_count": 0,
        "private_state_or_cash_access_created_count": 0,
        "order_authority_created_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "qtt_sha_or_atomicrows_hash_authority_count": 0,
        "no_orphan_violation_count": 0,
        "path_audit_failure_count": 0,
    }
    for field, value in expected.items():
        _require(final.get(field) == value, f"FinalSummary {field}={final.get(field)!r}, expected {value!r}")
    minimums = {
        "formula_exec_receipt_count": EXPECTED_COMPUTABLE_FORMULA_COUNT * 2,
        "formula_to_pnl_map_count": EXPECTED_TOTAL_FORMULA_COUNT,
        "market_instantiation_row_count": EXPECTED_COMPUTABLE_FORMULA_COUNT,
        "formula_contribution_row_count": EXPECTED_COMPUTABLE_FORMULA_COUNT,
        "formula_stack_builder_row_count": EXPECTED_COMPUTABLE_FORMULA_COUNT,
        "formula_quality_row_count": EXPECTED_TOTAL_FORMULA_COUNT,
        "success_metrics_row_count": 1,
        "rank2_evidence_handoff_count": EXPECTED_COMPUTABLE_FORMULA_COUNT,
        "no_trade_comparison_count": EXPECTED_COMPUTABLE_FORMULA_COUNT,
        "online_verification_query_family_count": 8,
        "online_verification_distinct_source_url_count": 16,
    }
    for field, minimum in minimums.items():
        _require(int(final.get(field, 0)) >= minimum, f"FinalSummary {field} below {minimum}: {final.get(field)!r}")


def _assert_formula_universe(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    universe = rows["formula_universe"]
    eligibility = rows["formula_eligibility"]
    repairs = rows["formula_repair"]
    _require(len(universe) == EXPECTED_TOTAL_FORMULA_COUNT, "formula universe count mismatch")
    _require(len(eligibility) == EXPECTED_TOTAL_FORMULA_COUNT, "formula eligibility count mismatch")
    _require(
        sum(row["eligibility_state"] == "RP3_REPLAY_PAPER_COMPUTABLE_NOW" for row in eligibility)
        == EXPECTED_COMPUTABLE_FORMULA_COUNT,
        "computable eligibility count mismatch",
    )
    _require(
        sum(row["eligibility_state"] == "RP3_EXPRESSION_REPAIR_REQUIRED" for row in eligibility)
        == EXPECTED_EXPRESSION_REPAIR_COUNT,
        "expression repair eligibility count mismatch",
    )
    _require(
        sum(row["eligibility_state"] == "RP3_SOURCE_EVIDENCE_REVIEW_REQUIRED" for row in eligibility)
        == EXPECTED_SOURCE_REVIEW_COUNT,
        "source review eligibility count mismatch",
    )
    _require(len(repairs) == EXPECTED_EXPRESSION_REPAIR_COUNT + EXPECTED_SOURCE_REVIEW_COUNT, "repair row count mismatch")
    _require(all(row.get("PR236_best_formula_rows_are_formula_definitions") is False for row in universe), "PR236 rows counted as definitions")


def _assert_market_instantiation(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    markets = rows["market_instantiation"]
    _require(len(markets) == EXPECTED_COMPUTABLE_FORMULA_COUNT, "market instantiation count mismatch")
    required = (
        "market_instantiation_id",
        "formula_id",
        "formula_variant_id",
        "market_id_or_token_id",
        "venue",
        "side",
        "entry_price",
        "exit_price_or_resolution_price",
        "payout_value",
        "order_policy",
        "size_bucket",
        "decision_time_utc",
        "data_asof_utc",
    )
    for row in markets:
        for field in required:
            _require(row.get(field) not in (None, ""), f"market instantiation missing {field}")
        _require(row.get("resolution_used_for_decision_flag") is False, "market instantiation uses resolution for decision")
        _require(row.get("accepted_truth_flag") is False, "market instantiation accepted truth")
        _require(row.get("candidate_only_flag") is True, "market instantiation not candidate-only")


def _assert_formula_execution(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    locks = rows["input_locks"]
    exec_plan = rows["formula_execution"]
    receipts = rows["formula_exec_receipt"]
    pnl_maps = rows["formula_to_pnl_map"]
    _require(len(locks) == EXPECTED_COMPUTABLE_FORMULA_COUNT, "input lock count mismatch")
    _require(len(exec_plan) == EXPECTED_COMPUTABLE_FORMULA_COUNT, "formula execution plan count mismatch")
    _require(len(receipts) >= EXPECTED_COMPUTABLE_FORMULA_COUNT * 2, "formula exec receipt count too low")
    _require(len(pnl_maps) == EXPECTED_TOTAL_FORMULA_COUNT, "formula-to-PnL map count mismatch")
    _require(all(row.get("market_instantiation_id") for row in locks), "input lock missing market_instantiation_id")
    _require(all(row.get("market_instantiation_id") for row in exec_plan), "exec plan missing market_instantiation_id")
    for receipt in receipts:
        _require(receipt.get("formula_to_pnl_map_ref"), "formula receipt missing formula-to-PnL ref")
        _require(receipt.get("candidate_only_flag") is True, "formula receipt not candidate-only")
        _require(receipt.get("accepted_truth_flag") is False, "formula receipt accepted truth")


def _assert_replay_paper(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    replay = rows["replay"]
    paper = rows["paper"]
    _require(len(replay) == EXPECTED_COMPUTABLE_FORMULA_COUNT, "replay row count mismatch")
    _require(len(paper) == EXPECTED_COMPUTABLE_FORMULA_COUNT, "paper row count mismatch")
    replay_fields = (
        "replay_gross_pnl_candidate",
        "replay_tca_total_candidate",
        "replay_net_expected_pnl_candidate",
        "replay_fill_adjusted_expected_pnl",
        "replay_execution_adjusted_edge",
        "replay_latency_adjusted_pnl_candidate",
        "replay_capacity_adjusted_pnl_candidate",
        "replay_no_trade_margin_candidate",
    )
    paper_fields = (
        "paper_gross_pnl_candidate",
        "paper_tca_total_candidate",
        "paper_net_expected_pnl_candidate",
        "paper_fill_adjusted_expected_pnl",
        "paper_execution_adjusted_edge",
        "paper_latency_adjusted_pnl_candidate",
        "paper_capacity_adjusted_pnl_candidate",
        "paper_no_trade_margin_candidate",
    )
    for row in replay:
        _assert_numeric_fields(row, replay_fields, row["replay_row_id"])
        _require(row.get("market_instantiation_id"), f"{row['replay_row_id']} missing market_instantiation_id")
        _require(str(row.get("replay_result_classification_non_proof", "")).startswith("REPLAY_"), "bad replay classification")
        _require(row.get("lookahead_leakage_flag") is False, "replay lookahead leakage")
        _require(row.get("outcome_used_for_decision_flag") is False, "replay uses outcome for decision")
        if "resolution_used_for_decision_flag" in row:
            _require(row.get("resolution_used_for_decision_flag") is False, "replay uses resolution for decision")
    for row in paper:
        _assert_numeric_fields(row, paper_fields, row["paper_row_id"])
        _require(row.get("market_instantiation_id"), f"{row['paper_row_id']} missing market_instantiation_id")
        _require(str(row.get("paper_result_classification_non_proof", "")).startswith("PAPER_"), "bad paper classification")
        _require(row.get("private_cash_receipt_created_flag") is False, "paper created cash receipt")
        _require(row.get("live_order_receipt_created_flag") is False, "paper created live order receipt")
        _require(row.get("order_authority_created_flag") is False, "paper created order authority")


def _assert_tca_fill_cost(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    components = (
        "implementation_shortfall_candidate",
        "explicit_fee_candidate",
        "spread_cross_cost",
        "slippage_depth_cost",
        "adverse_selection_proxy",
        "latency_decay_penalty",
        "missed_fill_opportunity_cost",
        "capacity_depth_penalty",
        "market_impact_proxy",
        "settlement_or_carry_gap",
        "TCA_total_candidate",
    )
    for row in rows["tca"]:
        _assert_numeric_fields(row, components, row["tca_row_id"])
        _require(row.get("TCA_repair_route"), f"{row['tca_row_id']} missing TCA repair route")
    for row in rows["fill"]:
        _require(_is_number(row.get("fill_probability_candidate")), f"{row['fill_row_id']} missing fill probability")
        _require(0.0 <= float(row["fill_probability_candidate"]) < 1.0, f"{row['fill_row_id']} fill defaults to 1")
        _require(row.get("fill_probability_defaulted_to_one_flag") is False, "fill defaulted to one")
    for row in rows["cost_audit"]:
        _require(row.get("cost_components_defaulted_to_zero_flag") is False, "cost component defaulted to zero")
        _require(row.get("repair_route_if_gap"), "cost audit missing repair route")
    for row in rows["fill_audit"]:
        _require(row.get("fill_probability_defaulted_to_one_flag") is False, "fill audit defaulted to one")
        _require(row.get("direct_fill_evidence_state") != "DEFAULT_FULL_FILL", "fill audit defaulted full fill")
    for row in rows["probability_model_audit"]:
        _require(row.get("independent_alpha_proof_flag") is False, "probability audit claims independent alpha proof")
        _require(row.get("not_independent_alpha_proof_flag") is True, "probability audit missing proof blocker")


def _assert_scenarios_guards_and_norms(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    scenario_families = {row["scenario_family"] for row in rows["scenario"]}
    for family in SCENARIO_FAMILIES:
        _require(family in scenario_families, f"missing scenario family {family}")
    for key in ("asof_barrier", "no_lookahead"):
        for row in rows[key]:
            _require(row.get("lookahead_leakage_flag") is False, f"{key} leakage flag")
            _require(row.get("leakage_guard_state") in {"PASSED", "GAP_ROUTED"}, f"{key} bad guard state")
            _require(row.get("outcome_used_for_decision_flag") is False, f"{key} uses outcome for decision")
    for row in rows["expected_realized"]:
        _require(row.get("resolution_used_for_decision_flag") is False, "expected/realized uses resolution for decision")
        _assert_numeric_fields(row, ("expected_pnl_before_resolution_candidate", "mark_to_market_paper_pnl_candidate"), row["expected_realized_row_id"])
    for row in rows["venue_norm"]:
        _assert_numeric_fields(row, ("normalized_price_probability_0_to_1", "normalized_price_cents_0_to_100", "normalized_payout_value", "normalized_contract_size", "normalized_tick_size"), row["venue_norm_row_id"])
        _require(row.get("yes_no_parity_check_state") == "PASSED_OR_NOT_APPLICABLE", "binary parity not checked")


def _assert_rank2_stack_and_quantum(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    rank2 = rows["rank2_handoff"]
    stacks = rows["formula_stack"]
    no_trade = _rows_by(rows["no_trade"], "no_trade_row_id")
    _require(len(rank2) == EXPECTED_COMPUTABLE_FORMULA_COUNT, "rank2 count mismatch")
    _require(len(stacks) == EXPECTED_COMPUTABLE_FORMULA_COUNT, "stack count mismatch")
    for row in rank2:
        for field in (
            "replay_row_refs",
            "paper_row_refs",
            "TCA_refs",
            "fill_refs",
            "latency_refs",
            "capacity_refs",
            "calibration_lcb_refs",
            "FDR_refs",
            "portfolio_refs",
            "regime_refs",
            "scenario_refs",
            "no_trade_refs",
        ):
            _require(bool(row.get(field)), f"{row['rank2_evidence_row_id']} missing {field}")
        _assert_numeric_fields(row, ("replay_net_expected_pnl_candidate", "paper_net_expected_pnl_candidate", "fill_adjusted_expected_pnl", "execution_adjusted_edge", "TCA_total_candidate", "no_trade_margin_candidate"), row["rank2_evidence_row_id"])
        _require(row.get("rank2_consumption_allowed_flag") is True, "rank2 row not consumable")
        _require(row.get("champion_allowed_flag") is False, "rank2 row allows champion")
        _require(row.get("live_candidate_allowed_flag") is False, "rank2 row allows live")
        _require(row["no_trade_refs"][0] in no_trade, f"{row['rank2_evidence_row_id']} missing no-trade row")
    for stack in stacks:
        _assert_numeric_fields(stack, ("combined_edge", "combined_pnl", "combined_tca", "combined_fill", "combined_latency", "combined_capacity", "combined_no_trade_margin"), stack["stack_id"])
        _require(stack.get("market_instantiation_id"), "stack missing market instantiation")
        _require(stack.get("formula_stack_dedup_key"), "stack missing dedup key")
        _require(stack.get("champion_allowed_flag") is False, "stack allows champion")
        _require(stack.get("live_candidate_allowed_flag") is False, "stack allows live")
    for row in rows["quantum_stack"]:
        _require(row.get("binary_variable_id"), "quantum row missing binary variable")
        _require(bool(row.get("linear_coefficient_refs")), "quantum row missing linear refs")
        _require(bool(row.get("constraint_refs")), "quantum row missing constraint refs")
        _require(row.get("interpret_back_map_exists") is True, "quantum interpret-back missing")
        _require(row.get("classical_fallback_exists") is True, "quantum fallback missing")
        _require(row.get("quantum_backend_execution_flag") is False, "quantum backend executed")
        _require(row.get("quantum_advantage_claim_flag") is False, "quantum advantage claimed")
    for row in rows["q_stack_select"]:
        _require(row.get("binary_variable_id"), "quantum selection row missing binary variable")
        _require(row.get("classical_greedy_fallback_rank"), "quantum selection row missing fallback rank")
        _require(row.get("quantum_backend_execution_flag") is False, "quantum selection backend executed")
        _require(row.get("quantum_advantage_claim_flag") is False, "quantum selection advantage claimed")


def _assert_repairs_quality_success(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    _require(len(rows["formula_contribution"]) >= EXPECTED_COMPUTABLE_FORMULA_COUNT, "formula contribution count too low")
    for row in rows["formula_contribution"]:
        _assert_numeric_fields(row, ("edge_contribution", "tca_contribution", "fill_contribution", "latency_contribution", "capacity_contribution", "portfolio_contribution", "scenario_contribution", "no_trade_contribution", "net_effect"), row["formula_contribution_id"])
    _require(len(rows["negative_recovery"]) > 0, "negative recovery ledger empty")
    for row in rows["negative_recovery"]:
        _assert_numeric_fields(row, ("before_pnl", "after_pnl", "before_no_trade_margin", "after_no_trade_margin", "before_TCA", "after_TCA", "before_fill_probability_or_fillability", "after_fill_probability_or_fillability"), row["negative_recovery_id"])
        _require(row.get("not_profit_proof_flag") is True, "negative recovery claims proof")
        _require(row.get("do_not_overwrite_original_evidence_flag") is True, "negative recovery overwrites original evidence")
    _require(len(rows["formula_quality"]) == EXPECTED_TOTAL_FORMULA_COUNT, "formula quality count mismatch")
    for row in rows["formula_quality"]:
        _assert_numeric_fields(row, ("computability_score", "input_coverage_score", "data_coverage_score", "calibration_readiness_score", "stability_score", "FDR_control_score", "repair_burden_score", "portfolio_utility_score", "scenario_robustness_score", "no_trade_relevance_score", "quantum_structural_usability_score", "overall_formula_quality_score_non_proof"), row["formula_quality_id"])
    _require(len(rows["success_metrics"]) == 1, "success metrics row count mismatch")
    success = rows["success_metrics"][0]
    _require(success["formula_count_tested"] == EXPECTED_TOTAL_FORMULA_COUNT, "success metrics formula_count_tested mismatch")
    _require(success["formula_count_computed"] == EXPECTED_COMPUTABLE_FORMULA_COUNT, "success metrics formula_count_computed mismatch")
    _require(success["formula_count_gap_routed"] == EXPECTED_EXPRESSION_REPAIR_COUNT + EXPECTED_SOURCE_REVIEW_COUNT, "success metrics gap route mismatch")
    _require(success["no_orphan_violation_count"] == 0, "success metrics no orphan violations")
    _require(success["forbidden_authority_count"] == 0, "success metrics forbidden authorities")


def _assert_numeric_evidence(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    evidence = rows["evidence_tier"]
    _require(len(evidence) > EXPECTED_COMPUTABLE_FORMULA_COUNT * 10, "numeric evidence coverage too low")
    for row in evidence:
        _require(row.get("numeric_value_id"), "numeric row missing id")
        _require(row.get("numeric_field_name"), "numeric row missing field name")
        _require("numeric_value_or_null" in row, "numeric row missing value field")
        _require(row.get("evidence_tier"), "numeric row missing evidence tier")
        _require(bool(row.get("source_refs")), "numeric row missing source refs")
        _require(bool(row.get("computed_from_refs")), "numeric row missing computed-from refs")
        _require(bool(row.get("formula_refs")), "numeric row missing formula refs")
        _require(row.get("accepted_truth_flag") is False, "numeric row accepted truth")
        _require(row.get("candidate_only_flag") is True, "numeric row not candidate-only")
        _require(row.get("real_positive_eligible_flag") is False, "numeric row real positive eligible")
        _require(row.get("real_negative_eligible_flag") is False, "numeric row real negative eligible")
    coverage = rows["numeric_coverage"][0]
    _require(coverage["formula_count_expected"] == EXPECTED_COMPUTABLE_FORMULA_COUNT, "numeric coverage expected count mismatch")
    _require(coverage["real_proof_blocked_count"] >= EXPECTED_COMPUTABLE_FORMULA_COUNT, "real proof blockers too low")
    online = rows["online_verify"]
    _require(len({row["query_family"] for row in online}) >= 8, "online query family coverage below 8")
    _require(len({row["source_url"] for row in online}) >= 16, "online source URL coverage below 16")


def main() -> int:
    result = run_validation()
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
