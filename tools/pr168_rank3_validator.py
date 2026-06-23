#!/usr/bin/env python3
"""Strict validator for PR168-RANK3 generated ranking artifacts."""

from __future__ import annotations

import math
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_rank3_config import (
    AUTHORITY_FALSE_FLAGS,
    EXPECTED_RP3_CANONICAL_FORMULA_COUNT,
    EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT,
    EXPECTED_RP3_DATA_REPAIR_COUNT,
    EXPECTED_RP3_EXPRESSION_REPAIR_COUNT,
    EXPECTED_RP3_ROW_SHARD_FAMILY_COUNT,
    EXPECTED_RP3_SOURCE_REVIEW_COUNT,
    EXPECTED_RP3_TARGETED_TEST_COUNT,
    EXPECTED_RP3_TOP_LEVEL_REPORT_COUNT,
    FORBIDDEN_STATE_VALUES,
    REPORT_ALIASES,
    ROW_SHARDS,
    report_path,
    shard_path,
)
from tools.pr168_rank3_report_writer import read_json, read_jsonl


class RANK3ValidationError(AssertionError):
    """Raised when PR168-RANK3 evidence violates the RANK3 contract."""


def _fail(message: str) -> None:
    raise RANK3ValidationError(message)


def _require(condition: bool, message: str) -> None:
    if not condition:
        _fail(message)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def run_validation() -> dict[str, Any]:
    reports = _load_reports()
    rows = _load_rows()
    for key, shard_rows in rows.items():
        for index, row in enumerate(shard_rows, start=1):
            _assert_route_fields(row, f"{key}[{index}]")

    final = reports["PR168_RANK3_FinalSummary"]["records"]
    _assert_final_summary(final)
    _assert_item_accounting(rows)
    _assert_inventory(rows)
    _assert_pre_rank_repair(rows)
    _assert_source_provenance(rows)
    _assert_ranking(rows)
    _assert_no_trade(rows)
    _assert_diagnostics(rows)
    _assert_quantum(rows)
    _assert_handoffs(rows)
    _assert_online(rows)
    _assert_path_alias(reports)
    return {
        "status": "passed",
        "reports": len(reports),
        "shards": len(rows),
        "rankable_stack_count": final["rankable_stack_count"],
        "no_trade_competitor_count": final["no_trade_competitor_count"],
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
    _require(len(seen_physical) == len(REPORT_ALIASES), "duplicate RANK3 physical report filename")
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
    _assert_no_authority(row, label)


def _assert_final_summary(final: Mapping[str, Any]) -> None:
    expected = {
        "pr238_merged_preflight_passed_flag": True,
        "rp3_computable_map3_formula_tested_count_observed": EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT,
        "rp3_canonical_formula_id_universe_observed": EXPECTED_RP3_CANONICAL_FORMULA_COUNT,
        "rp3_expression_repair_formula_count_observed": EXPECTED_RP3_EXPRESSION_REPAIR_COUNT,
        "rp3_source_review_formula_count_observed": EXPECTED_RP3_SOURCE_REVIEW_COUNT,
        "rp3_formula_data_repair_count_observed": EXPECTED_RP3_DATA_REPAIR_COUNT,
        "rp3_top_level_report_count_observed": EXPECTED_RP3_TOP_LEVEL_REPORT_COUNT,
        "rp3_row_shard_family_count_observed": EXPECTED_RP3_ROW_SHARD_FAMILY_COUNT,
        "rp3_targeted_test_count_observed": EXPECTED_RP3_TARGETED_TEST_COUNT,
        "expression_repair_attempt_count": EXPECTED_RP3_EXPRESSION_REPAIR_COUNT,
        "source_provenance_attempt_count": EXPECTED_RP3_SOURCE_REVIEW_COUNT,
        "rankable_stack_count": EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT,
        "no_trade_competitor_count": EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT,
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
        "rp3_evidence_rows_consumed_count": 1,
        "feature_matrix_row_count": EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT,
        "normalized_score_row_count": EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT,
        "component_score_row_count": EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT,
        "rank_score_lineage_row_count": EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT,
        "execution_adjusted_rank_row_count": EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT,
        "hurdle_gate_fail_count": EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT,
        "pairwise_dominance_row_count": EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT,
        "pareto_frontier_row_count": EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT,
        "tournament_rank_row_count": EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT,
        "robust_minimax_row_count": EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT,
        "evidence_shrinkage_row_count": EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT,
        "quantum_rank_objective_row_count": EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT,
        "online_verify_source_count": 16,
    }
    for field, minimum in minimums.items():
        _require(int(final.get(field, 0)) >= minimum, f"FinalSummary {field} below {minimum}: {final.get(field)!r}")


def _assert_item_accounting(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    accounting = rows["rp3_item_accounting"][0]
    _require(accounting["count_match_state"] == "COUNTS_MATCH_EXPECTED_RP3_COMPLETION_ITEMS", "RP3 item accounting mismatch")
    inventory = rows["rp3_report_inventory"]
    shards = rows["rp3_shard_family"]
    history = rows["upstream_validation_history"][0]
    _require(len(inventory) == EXPECTED_RP3_TOP_LEVEL_REPORT_COUNT, "RP3 report inventory count mismatch")
    _require(all(row["consumed_flag"] for row in inventory), "RP3 report silently ignored")
    _require(len(shards) == EXPECTED_RP3_ROW_SHARD_FAMILY_COUNT, "RP3 shard family count mismatch")
    _require(history["targeted_test_count_observed"] == EXPECTED_RP3_TARGETED_TEST_COUNT, "RP3 targeted test count mismatch")


def _assert_inventory(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    evidence = rows["evidence_universe"]
    _require(evidence, "evidence universe empty")
    _require(all(row.get("source_row_ref") for row in evidence), "evidence universe row without RP3 source ref")
    consumption = rows["rp3_consumption"]
    _require(len(consumption) == EXPECTED_RP3_CANONICAL_FORMULA_COUNT, "formula universe crosswalk count mismatch")
    rankable = [row for row in consumption if row["rank3_rankable_flag"]]
    _require(len(rankable) == EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT, "rankable formula count mismatch")


def _assert_pre_rank_repair(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    attempts = rows["expression_repair_attempt"]
    resolutions = rows["expression_repair_resolution"]
    rankability = rows["repaired_formula_rank_eligibility"]
    _require(len(attempts) == EXPECTED_RP3_EXPRESSION_REPAIR_COUNT, "expression repair attempt count mismatch")
    _require(len(resolutions) == EXPECTED_RP3_EXPRESSION_REPAIR_COUNT, "expression repair resolution count mismatch")
    for row in attempts:
        _require(row["repair_attempted_flag"] is True, "expression repair not attempted")
        _require(row["unsafe_eval_executed_flag"] is False, "unsafe expression eval executed")
        _require(row["safe_parser_rules"], "expression repair missing parser rules")
    for row in resolutions:
        _require(row["formula_to_pnl_map_ref"], "expression repair resolution missing FormulaToPnL ref")
        _require(row["rankable_after_expression_repair_flag"] is False, "unexpected expression formula rankable without mini evidence")
    _require(all(not row["rankable_flag"] for row in rankability), "repaired formulas should remain non-rankable without mini evidence")


def _assert_source_provenance(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    attempts = rows["source_provenance_attempt"]
    resolutions = rows["source_provenance_resolution"]
    uses = rows["source_candidate_use"]
    penalties = rows["source_provenance_penalty"]
    _require(len(attempts) == EXPECTED_RP3_SOURCE_REVIEW_COUNT, "source provenance attempt count mismatch")
    _require(len(resolutions) == EXPECTED_RP3_SOURCE_REVIEW_COUNT, "source provenance resolution count mismatch")
    _require(len(uses) == EXPECTED_RP3_SOURCE_REVIEW_COUNT, "source candidate use count mismatch")
    _require(len(penalties) == EXPECTED_RP3_SOURCE_REVIEW_COUNT, "source penalty count mismatch")
    for row in attempts:
        _require(row["official_source_required_flag"] is False, "official-source blocker remains")
        _require(row["candidate_only_flag"] is True, "source attempt not candidate-only")
        _require(row["accepted_truth_flag"] is False, "source attempt accepted truth")
    for row in uses:
        for field in ("source_url_or_owner_ref", "source_title_or_owner_label", "source_tier", "formula_input_mapping", "evidence_tier", "reliability_penalty_or_gap"):
            _require(row.get(field) not in (None, "", []), f"source candidate use missing {field}")
        _require(row["candidate_only_flag"] is True, "source candidate use not candidate-only")
        _require(row["accepted_truth_flag"] is False, "source candidate use accepted truth")
    _require(
        any(row["source_tier"] == "NON_OFFICIAL_SOURCE_CANDIDATE" for row in rows["online_verify"]),
        "non-official sources not represented as candidate usable rows",
    )


def _assert_ranking(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    feature = rows["feature_matrix"]
    normalized = rows["normalized_score"]
    components = rows["component_score"]
    lineage = rows["rank_score_lineage"]
    execution = rows["execution_adjusted_rank"]
    _require(len(feature) == EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT, "feature row count mismatch")
    _require(len(normalized) == len(feature), "normalized row count mismatch")
    _require(len(components) == len(feature), "component row count mismatch")
    _require(len(lineage) == len(feature), "score lineage row count mismatch")
    _require(len(execution) == len(feature), "execution rank row count mismatch")
    required = (
        "net_expected_pnl_candidate",
        "fill_adjusted_expected_pnl",
        "execution_adjusted_edge",
        "lower_confidence_bound_edge_or_gap",
        "TCA_total_candidate",
        "scenario_robustness_score",
        "portfolio_marginal_utility",
        "source_reliability_penalty_or_gap",
        "no_trade_margin_candidate",
        "no_orphan_state",
    )
    for row in feature:
        for field in required:
            _require(field in row, f"feature row missing {field}")
        _require(row["unit_normalization_group"], "feature row missing unit normalization group")
    for row in normalized:
        _require(row["normalization_state"] == "VENUE_UNIT_PRICE_SCALE_NORMALIZED", "normalization state mismatch")
        _require(row["normalized_lcb_edge_or_conservative_gap"] < 0, "LCB gap not conservatively penalized")
    for row in lineage:
        _require(row["raw_component_refs"], "score lineage missing raw refs")
        _require(row["normalized_component_refs"], "score lineage missing normalized refs")
        _require(row["no_trade_refs"], "score lineage missing no-trade refs")


def _assert_no_trade(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    no_trade = rows["no_trade_competition"]
    _require(len(no_trade) == EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT, "no-trade competitor count mismatch")
    for row in no_trade:
        _require(row["no_trade_wins_flag_non_proof"] is True, "expected no-trade to win weak candidate comparison")
        _require(row["candidate_beats_no_trade_flag_non_proof"] is False, "candidate incorrectly beats no-trade")
        _require(row["candidate_formula_refs"], "no-trade row missing formula refs")


def _assert_diagnostics(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    for key in ("lcb_rank", "tca_rank", "fill_latency_capacity_rank", "fdr_model_risk", "hurdle_gate", "rank_stability_stress", "pairwise_dominance", "pareto_frontier", "tournament_rank", "robust_minimax", "evidence_shrinkage", "scenario_rank", "portfolio_rank", "marginal_utility", "candidate_batch", "rank_tier", "repair_route", "repair_priority"):
        _require(rows[key], f"{key} rows missing")
    for row in rows["hurdle_gate"]:
        _require(row["hurdle_gate_pass_flag"] is False, "hurdle gate unexpectedly passed no-trade dominated candidate")
        _require("NO_TRADE_BEATEN_NON_PROOF" in row["block_reasons"], "hurdle gate missing no-trade block reason")
    for row in rows["candidate_batch"]:
        _require(row["raw_top_n_selection_blocked_flag"] is True, "candidate batch allowed raw top-N")
    for row in rows["repair_priority"]:
        _require(_is_number(row["repair_priority_non_proof"]), "repair priority not numeric")
        _require(row["downstream_unblock_score"] > 0, "repair priority missing downstream unblock score")


def _assert_quantum(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    qrows = rows["q_rank"]
    _require(len(qrows) == EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT, "q-rank row count mismatch")
    for row in qrows:
        for field in ("binary_variable_id", "linear_coefficient_refs", "quadratic_coefficient_refs", "constraint_refs"):
            _require(row.get(field) not in (None, "", []), f"q-rank missing {field}")
        _require(row["interpret_back_map_exists"] is True, "q-rank missing interpret-back")
        _require(row["classical_greedy_fallback_exists"] is True, "q-rank missing classical fallback")
        _require(row["quantum_backend_execution_flag"] is False, "q-rank executed backend")
        _require(row["quantum_advantage_claim_flag"] is False, "q-rank claimed advantage")


def _assert_handoffs(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    handoffs = rows["downstream_handoff"]
    families = {row["handoff_family"] for row in handoffs}
    for expected in {"RANK4", "RP4", "PR165B", "PR162EQ", "DATA1B", "SOURCE_PROVENANCE", "DASHBOARD"}:
        _require(expected in families, f"missing downstream handoff {expected}")
    _require(rows["agent_memory"], "agent memory rows missing")
    _require(rows["every_value"], "every-value DAG rows missing")
    for row in rows["agent_memory"]:
        _require(row.get("regime_condition_id"), "PR165-B memory row missing regime condition")


def _assert_online(rows: Mapping[str, list[dict[str, Any]]]) -> None:
    online = rows["online_verify"]
    urls = {row.get("source_url_or_owner_ref") for row in online if row.get("source_url_or_owner_ref")}
    families = {row.get("query_family") for row in online if row.get("query_family")}
    _require(len(online) >= 16, "online source-use row count below coverage minimum")
    _require(len(urls) >= 16, "distinct source URL count below coverage minimum")
    _require(len(families) >= 8, "query family count below coverage minimum")
    for row in online:
        _require(row["candidate_only_flag"] is True, "online source row not candidate-only")
        _require(row["accepted_truth_flag"] is False, "online source row accepted truth")
        _require(row.get("source_url_or_owner_ref"), "online source row missing URL")


def _assert_path_alias(reports: Mapping[str, dict[str, Any]]) -> None:
    aliases = reports["PR168_RANK3_FileAliases"]["records"]["rows"]
    paths = reports["PR168_RANK3_PathAudit"]["records"]["rows"]
    _require(len(aliases) >= len(REPORT_ALIASES), "file alias rows too small")
    _require(all(row["path_audit_status"] != "FAIL_HARD_PATH_TOO_LONG" for row in paths), "path audit hard failure")


if __name__ == "__main__":
    import json

    print(json.dumps(run_validation(), sort_keys=True))
