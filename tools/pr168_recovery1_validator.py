#!/usr/bin/env python3
"""Strict validator for PR168-RECOVERY1 generated artifacts."""

from __future__ import annotations

import math
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_recovery1_config import (
    AUTHORITY_FALSE_FLAGS,
    FORBIDDEN_STATE_VALUES,
    REPORT_ALIASES,
    ROW_SHARDS,
    report_path,
    shard_path,
)
from tools.pr168_recovery1_report_writer import read_json, read_jsonl


class Recovery1ValidationError(AssertionError):
    """Raised when PR168-RECOVERY1 artifacts violate the Recovery1 contract."""


def _fail(message: str) -> None:
    raise Recovery1ValidationError(message)


def _require(condition: bool, message: str) -> None:
    if not condition:
        _fail(message)


def run_validation() -> dict[str, Any]:
    reports = _load_reports()
    rows = _load_rows()
    for key, shard_rows in rows.items():
        for index, row in enumerate(shard_rows, start=1):
            _assert_route_fields(row, f"{key}[{index}]")
    final = reports["PR168_RECOVERY1_FinalSummary"]["records"]
    _assert_final_summary(final, rows)
    _assert_work_items(rows)
    _assert_absorption(rows)
    _assert_repair_universe(rows)
    _assert_data_precision(rows)
    _assert_expression_source(rows)
    _assert_retest(rows)
    _assert_probability(rows)
    _assert_quantum(rows)
    _assert_handoff_memory(rows)
    _assert_online(reports, rows)
    _assert_validation_runtime(reports, rows)
    _assert_path_alias(reports)
    return {
        "status": "passed",
        "reports": len(reports),
        "shards": len(rows),
        "work_item_count": final["work_item_count"],
        "retest_before_after_count": final["retest_before_after_count"],
        "online_verify_source_count": final["online_verify_source_count"],
    }


def _load_reports() -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    seen_physical: set[str] = set()
    for report_id, physical in REPORT_ALIASES.items():
        path = report_path(report_id)
        _require(path.exists(), f"missing report {physical}")
        payload = read_json(path)
        _require(payload.get("logical_report_id") == report_id, f"{physical} wrong logical_report_id")
        _require(payload.get("physical_filename") == physical, f"{physical} wrong physical_filename")
        _require(payload.get("manual_edit_allowed_flag") is False, f"{physical} allows manual edit")
        _require(payload.get("no_orphan_status") == "NO_ORPHAN", f"{physical} missing no-orphan")
        _assert_no_authority(payload, f"report:{physical}")
        reports[report_id] = payload
        seen_physical.add(physical)
    _require(len(seen_physical) == len(REPORT_ALIASES), "duplicate Recovery1 physical report filename")
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
            _require(row.get(flag) is expected, f"{label} authority flag {flag}={row.get(flag)!r}")
    for value in _walk(row):
        if isinstance(value, str):
            _require(value not in FORBIDDEN_STATE_VALUES, f"{label} contains forbidden state {value}")


def _walk(value: Any) -> Iterable[Any]:
    if isinstance(value, Mapping):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)
    else:
        yield value


def _assert_route_fields(row: Mapping[str, Any], label: str) -> None:
    _require(row.get("no_orphan_status") == "NO_ORPHAN", f"{label} missing no-orphan")
    _require(bool(row.get("upstream_refs")), f"{label} missing upstream refs")
    _require(bool(row.get("downstream_consumers")), f"{label} missing downstream consumers")
    _require(bool(row.get("downstream_pr_refs")), f"{label} missing downstream PR refs")
    _require(bool(row.get("owning_agent")), f"{label} missing owning agent")
    _require(bool(row.get("validator_refs")), f"{label} missing validators")
    _require(bool(row.get("test_refs")), f"{label} missing tests")
    _require(bool(row.get("authority_class")), f"{label} missing authority class")
    _require(bool(row.get("work_item_ref")) or row.get("work_item_id"), f"{label} missing work item ref")
    _assert_no_authority(row, label)


def _assert_final_summary(final: Mapping[str, Any], rows: Mapping[str, list[dict[str, Any]]]) -> None:
    expected_zero = (
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
        "no_orphan_violation_count",
        "path_audit_failure_count",
        "no_lookahead_violation_count",
        "retest_quality_gate_fail_count",
    )
    for field in expected_zero:
        _require(final.get(field) == 0, f"FinalSummary {field}={final.get(field)!r}, expected 0")
    expected_positive = (
        "work_item_count",
        "candidate_input_confidence_row_count",
        "assumption_delta_audit_row_count",
        "repair_portfolio_selection_row_count",
        "old_roadmap_absorbed_task_count",
        "rank3_repair_queue_rows_consumed",
        "triage_priority_row_count",
        "repair_expected_value_row_count",
        "retest_sample_plan_row_count",
        "rank3_weak_negative_rows_consumed",
        "rank3_no_trade_dominated_rows_consumed",
        "rank3_expression_repair_rows_consumed",
        "rank3_source_provenance_rows_consumed",
        "data_precision_repair_attempt_count",
        "expression_repair_attempt_count",
        "source_provenance_attempt_count",
        "stack_repair_attempt_count",
        "retest_before_after_count",
        "replay_retest_count",
        "paper_retest_count",
        "tca_fill_capacity_retest_count",
        "no_trade_retest_count",
        "scenario_retest_count",
        "retest_improved_count",
        "quantum_repair_row_count",
        "operator_action_count",
        "asof_barrier_row_count",
        "retest_quality_gate_pass_count",
        "online_verify_source_count",
        "distinct_source_url_count",
        "source_rows_mapped_to_inputs_or_repairs_count",
    )
    for field in expected_positive:
        _require(int(final.get(field, 0)) > 0, f"FinalSummary {field} not positive: {final.get(field)!r}")
    _require(final.get("pr239_merged_preflight_passed_flag") is True, "PR239 preflight not passed")
    _require(final["work_item_count"] == len(rows["work_item"]), "work item count mismatch")
    _require(final["retest_before_after_count"] == len(rows["retest_before_after"]), "retest count mismatch")


def _assert_work_items(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    work_items = {row["work_item_id"] for row in rows["work_item"]}
    _require(work_items, "work item shard empty")
    required_fields = {
        "work_item_id",
        "work_item_family",
        "origin_pr_refs",
        "origin_report_refs",
        "origin_row_refs",
        "repair_hypothesis",
        "launch_criticality",
        "expected_repair_value_non_proof",
        "candidate_only_flag",
        "accepted_truth_flag",
        "current_state",
        "next_state",
        "state_transition_reason",
        "owning_agent",
        "consumer_agents",
    }
    for row in rows["work_item"]:
        missing = [field for field in required_fields if field not in row]
        _require(not missing, f"work item missing fields {missing}")
        _require(row["candidate_only_flag"] is True, "work item not candidate-only")
        _require(row["accepted_truth_flag"] is False, "work item accepted truth")
    for family, shard_rows in rows.items():
        if family == "work_item":
            continue
        for row in shard_rows:
            ref = row.get("work_item_ref")
            _require(ref in work_items, f"{family} row has unknown work_item_ref {ref!r}")


def _assert_absorption(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    absorbed = {row["absorbed_old_pr_ref"] for row in rows["old_roadmap_absorption"]}
    for required in ("PR162D-R3", "MAP4", "SRC1", "RP4", "PR166-SF/S2"):
        _require(required in absorbed, f"old roadmap absorption missing {required}")


def _assert_repair_universe(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    families = {row["repair_family"] for row in rows["repair_universe"]}
    for required in ("STACK_REPAIR", "EXPRESSION_FORMULA", "SOURCE_PROVENANCE"):
        _require(required in families, f"repair universe missing {required}")
    _require(
        all(row.get("expected_repair_value_non_proof", row.get("repair_expected_value_non_proof", -1)) >= 0 for row in rows["repair_expected_value"]),
        "negative EVR row",
    )
    _require(all(row["apply_repair_now_flag"] or row["defer_with_reason_flag"] for row in rows["triage_priority"]), "triage row without decision")
    _require(all(row["FDR_trial_expansion_count"] >= 1 for row in rows["triage_priority"]), "triage row missing FDR exposure")
    _require(all(row["suppressed_duplicate_count"] == 0 for row in rows["repair_dedupe"]), "unexpected duplicate suppression count")


def _assert_data_precision(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    for row in rows["data_precision"]:
        _require(row["candidate_only_flag"] is True, "data precision not candidate-only")
        _require(row["accepted_truth_flag"] is False, "data precision accepted truth")
        _require(row["target_field"] == "TCA_total_candidate", "unexpected data precision target")
        _require(_is_number(row["before_value_or_gap"]), "data precision before not numeric")
        _require(_is_number(row["after_value_or_gap"]), "data precision after not numeric")
    for row in rows["missing_value_repair"]:
        _require(row["fill_defaulted_to_one_flag"] is False, "missing value repair defaulted fill to one")
        _require(row["cost_defaulted_to_zero_flag"] is False, "missing value repair defaulted cost to zero")
        _require(row["historical_full_book_assumed_flag"] is False, "historical full book assumed")
    for row in rows["candidate_input_confidence"]:
        _require(row["input_confidence_class"] in {"OBSERVED_PUBLIC_DATA_CANDIDATE", "DERIVED_FROM_PUBLIC_DATA_CANDIDATE", "OWNER_SUBMITTED_CANDIDATE", "RESEARCH_OR_OPEN_SOURCE_CANDIDATE", "NON_OFFICIAL_SOURCE_CANDIDATE", "PROXY_REPAIR_REQUIRED", "SYNTHETIC_SHAPE_ONLY_NON_PROOF", "UNKNOWN_UNAVAILABLE", "UNSAFE_OR_UNMAPPABLE"}, "invalid input confidence class")
    for row in rows["assumption_delta"]:
        _require(row["silent_assumption_weakening_flag"] is False, "silent assumption weakening")


def _assert_expression_source(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    _require(len(rows["expression_repair"]) == 7, "expected 7 expression repair rows")
    _require(len(rows["source_provenance"]) == 5, "expected 5 source provenance rows")
    for row in rows["expression_repair"]:
        _require(row["unsafe_eval_used_flag"] is False, "unsafe eval used")
        _require(row["safe_parser_state"], "missing safe parser state")
        _require(row["FormulaToPnLMap"], "missing FormulaToPnL map")
    for row in rows["source_provenance"]:
        _require(row["candidate_only_flag"] is True, "source row not candidate-only")
        _require(row["accepted_truth_flag"] is False, "source row accepted truth")
        _require(row["source_truth_accepted_flag"] is False, "source truth accepted")
        _require(row["formula_input_mapping"], "source row missing mapping")
    for row in rows["source_to_retest"]:
        _require(row["source_to_retest_mapping_status"] in {"FORMULA_INPUT_CANDIDATE_MAPPED", "DATA_PRECISION_CANDIDATE_MAPPED", "THRESHOLD_CANDIDATE_MAPPED", "TCA_FILL_LATENCY_CAPACITY_CANDIDATE_MAPPED", "CALIBRATION_OR_FDR_NOTE_MAPPED", "QUANTUM_STRUCTURE_REPAIR_MAPPED", "RETEST_REPAIR_IDEA_MAPPED", "RELIABILITY_PENALTY_ONLY_MAPPED", "REJECTED_WITH_REASON"}, "invalid source-to-retest mapping")


def _assert_retest(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    for row in rows["retest_before_after"]:
        for field in (
            "before_net_expected_pnl_candidate",
            "after_net_expected_pnl_candidate",
            "before_fill_adjusted_expected_pnl",
            "after_fill_adjusted_expected_pnl",
            "before_execution_adjusted_edge",
            "after_execution_adjusted_edge",
            "before_TCA_total_candidate",
            "after_TCA_total_candidate",
            "before_no_trade_margin_candidate",
            "after_no_trade_margin_candidate",
            "repair_delta_net_expected_pnl_candidate",
            "repair_delta_no_trade_margin_candidate",
        ):
            _require(_is_number(row[field]), f"retest row missing numeric {field}")
        _require(row["outcome_used_for_decision_flag"] is False, "outcome used for repair decision")
        _require(row["lookahead_leakage_flag"] is False, "lookahead leakage flagged")
        _require(row["leakage_guard_state"] == "PASSED", "leakage guard not passed")
        _require(row["no_trade_competitor"], "retest row missing no-trade competitor")
        _require(row["changed_input_refs"], "retest row missing changed inputs")
        _require(row["unchanged_input_refs"], "retest row missing unchanged inputs")
        expected_delta = round(row["after_net_expected_pnl_candidate"] - row["before_net_expected_pnl_candidate"], 8)
        _require(abs(expected_delta - row["repair_delta_net_expected_pnl_candidate"]) < 1e-8, "net delta mismatch")
    for row in rows["tca_fill_capacity_retest"]:
        _require(row["fill_defaulted_to_one_flag"] is False, "fill defaulted to one in retest")
        _require(row["cost_defaulted_to_zero_flag"] is False, "cost defaulted to zero in retest")
    for row in rows["no_trade_retest"]:
        _require(row["no_trade_is_permanent_competitor_flag"] is True, "no-trade not permanent competitor")
    for row in rows["valid_vs_artificial"]:
        _require(row["candidate_only_flag"] is True, "valid/artificial row not candidate-only")
        _require(row["not_real_profit_proof_flag"] is True, "valid/artificial row claims proof")
    for row in rows["negative_to_recovery"]:
        _require(row["changed_input_refs"], "negative loop missing changed inputs")
        _require(row["unchanged_input_refs"], "negative loop missing unchanged inputs")


def _assert_probability(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    for row in rows["probability_source"]:
        _require(row["probability_role_state"] in {"INDEPENDENT_PROBABILITY_CANDIDATE", "MARKET_IMPLIED_PROBABILITY_ONLY", "OWNER_SUBMITTED_PROBABILITY_CANDIDATE", "MODEL_DERIVED_PROBABILITY_CANDIDATE", "BREAK_EVEN_THRESHOLD_ONLY", "REQUIRED_EDGE_THRESHOLD_ONLY", "PROBABILITY_MISSING_REPAIR_REQUIRED"}, "invalid probability role")
        _require(row["independent_alpha_proof_flag"] is False, "probability row claims independent alpha proof")
        _require(row["market_implied_probability_can_only_compute_threshold_flag"] is True, "market implied probability misused")


def _assert_quantum(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    for row in rows["quantum_repair"]:
        _require("linear_coefficient_refs" in row, "quantum row missing linear coefficients")
        _require("quadratic_coefficient_refs" in row, "quantum row missing quadratic coefficients")
        _require("constraint_refs" in row, "quantum row missing constraints")
        _require("interpret_back_map_exists" in row, "quantum row missing interpret-back")
        _require("classical_fallback_exists" in row, "quantum row missing classical fallback")
        _require(row["quantum_backend_execution_flag"] is False, "quantum backend execution claimed")
        _require(row["quantum_advantage_claim_flag"] is False, "quantum advantage claimed")
    for row in rows["q_classical_compare"]:
        _require(row["comparable_classical_fallback_ref"], "q/classical compare missing fallback")
        _require(row["quantum_backend_execution_flag"] is False, "q/classical compare backend execution")
        _require(row["quantum_advantage_claim_flag"] is False, "q/classical compare advantage claim")


def _assert_handoff_memory(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    handoff_families = {row["handoff_family"] for row in rows["downstream_handoff"]}
    for required in ("RP5_RANK4_QOPT1", "DATA1B", "MAP4", "SOURCE_PROVENANCE", "PR165B", "PR162E_Q", "PAPER_LOOP"):
        _require(required in handoff_families, f"missing handoff {required}")
    for row in rows["learning_memory"]:
        _require(row["condition_id"], "memory row missing condition")
        _require(row["repair_action_refs"], "memory row missing repair refs")
        _require(row["before_after_refs"], "memory row missing before/after refs")
    for row in rows["operator_action"]:
        _require(row["operator_action_type"], "operator row missing action")


def _assert_online(reports: Mapping[str, dict[str, Any]], rows: Mapping[str, list[dict[str, Any]]]) -> None:
    coverage = reports["PR168_RECOVERY1_OnlineVerifyCoverage"]["records"]
    _require(coverage["distinct_source_url_count"] >= 16, "online coverage has too few distinct committed sources")
    _require(coverage["source_rows_mapped_to_inputs_or_repairs_count"] >= 12, "source rows not materialized to inputs/repairs")
    deep = reports["PR168_RECOVERY1_DeepOnlineSearchCoverage"]["records"]
    if deep.get("live_deep_search_triggered_flag"):
        _require(deep["distinct_source_url_count"] >= 30 or deep.get("coverage_gap_if_any"), "deep search triggered without threshold or exact gap")
    for row in rows["online_verify"]:
        _require(row["candidate_only_flag"] is True, "online row not candidate-only")
        _require(row["accepted_truth_flag"] is False, "online row accepted truth")
        _require(row["source_to_retest_mapping_status"], "online row missing source-to-retest mapping")


def _assert_validation_runtime(reports: Mapping[str, dict[str, Any]], rows: Mapping[str, list[dict[str, Any]]]) -> None:
    runtime = rows["validation_runtime"][0]
    _require(runtime["new_validation_scope_added_flag"] is True, "Recovery1 validation scope addition not recorded")
    _require(runtime["currentization_required_flag"] is True, "Recovery1 currentization requirement not recorded")
    _require(runtime["github_full_validation_required_flag"] is True, "GitHub full validation not required")
    currentization = reports["PR168_RECOVERY1_CurrentizationNeedAudit"]["records"]
    _require(currentization["status"] == "required_and_currentized", "currentization audit not marked required_and_currentized")
    _require(
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
        in currentization["allowed_shared_currentization_files"],
        "currentization audit missing PR152 report",
    )
    side_effect = reports["PR168_RECOVERY1_SideEffectCleanupAudit"]["records"]
    _require(side_effect["forbidden_prefix_changed_count"] == 0, "forbidden side-effect prefix changed")


def _assert_path_alias(reports: Mapping[str, dict[str, Any]]) -> None:
    aliases = reports["PR168_RECOVERY1_FileAliases"]["records"]["aliases"]
    path_rows = reports["PR168_RECOVERY1_PathAudit"]["records"]["rows"]
    _require(len(aliases) == len(REPORT_ALIASES), "file alias count mismatch")
    _require(len(path_rows) == len(REPORT_ALIASES), "path audit count mismatch")
    _require(all(row["path_audit_state"] != "HARD_FAIL" for row in path_rows), "path audit hard failure")


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))
