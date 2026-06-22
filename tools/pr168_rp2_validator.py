#!/usr/bin/env python3
"""Validation for PR168-RP2-MAP2 generated artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from tools.pr168_rp2_config import (
    COMPUTABILITY_ROUTES,
    FAIL_PATH,
    GENERATED_ROOT,
    INTENT_POLICIES,
    ORDER_POLICIES,
    REPORT_ALIASES,
    ROW_SHARDS,
    report_path,
    shard_path,
)
from tools.pr168_rp2_reports import load_report, read_jsonl


FALSE_FLAG_KEYS = {
    "live_authority_created_flag",
    "profit_evidence_created_flag",
    "source_truth_acceptance_created_flag",
    "connector_semantic_binding_created_flag",
    "private_state_access_created_flag",
    "cash_access_created_flag",
    "order_authority_created_flag",
    "live_order_authority_flag",
    "quantum_backend_execution_flag",
    "quantum_advantage_claim_flag",
    "qtt_sha_or_atomicrows_hash_authority_flag",
    "champion_allowed_flag",
    "live_candidate_allowed_flag",
}


def rows(key: str) -> list[dict[str, Any]]:
    return read_jsonl(shard_path(key))


def records(report_id: str) -> Any:
    return load_report(report_id)["records"]


def final_summary() -> dict[str, Any]:
    return records("PR168_RP2_FinalSummary")


def assert_true(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise AssertionError(f"{code}: {message}")


def walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def validate_reports_exist() -> None:
    for report_id, physical in REPORT_ALIASES.items():
        path = report_path(report_id)
        assert_true(path.exists(), "PR168_RP2_REPORT_MISSING", f"{report_id} at {path}")
        payload = load_report(report_id)
        assert_true(payload.get("report_id") == report_id, "PR168_RP2_REPORT_ID_MISMATCH", report_id)
        assert_true(payload.get("physical_filename", "").endswith(physical), "PR168_RP2_PHYSICAL_ALIAS_MISMATCH", report_id)
        for key in (
            "logical_to_physical_alias_ref",
            "path_length_audit_ref",
            "upstream_input_refs",
            "downstream_consumers",
            "owning_agent",
            "validator_refs",
            "test_refs",
            "no_orphan_status",
            "authority_class",
        ):
            assert_true(key in payload, "PR168_RP2_REPORT_METADATA_MISSING", f"{report_id} missing {key}")
        assert_true(payload.get("records") or payload.get("terminal_by_nature_flag"), "PR168_RP2_REPORT_EMPTY", report_id)
    for key in ROW_SHARDS:
        path = shard_path(key)
        assert_true(path.exists(), "PR168_RP2_SHARD_MISSING", str(path))
        assert_true(path.with_suffix(".manifest.json").exists(), "PR168_RP2_SHARD_MANIFEST_MISSING", str(path))


def validate_final_summary() -> None:
    final = final_summary()
    assert_true(final["gfp2r_consumed_flag"] is True, "PR168_RP2_GFP2R_NOT_CONSUMED", str(final))
    assert_true(final["rp2_handoff_input_count"] == 36, "PR168_RP2_HANDOFF_COUNT", str(final["rp2_handoff_input_count"]))
    assert_true(final["map2_promotion_attempt_count"] == 36, "PR168_RP2_MAP2_ATTEMPT_COUNT", str(final["map2_promotion_attempt_count"]))
    assert_true(final["map2_exact_repaired_qku_formula_count"] >= 0, "PR168_RP2_EXACT_COUNT", str(final))
    assert_true(final["unique_economic_candidate_count"] == 36, "PR168_RP2_UNIQUE_ECON_COUNT", str(final["unique_economic_candidate_count"]))
    assert_true(final["order_intent_count"] == 36 * len(INTENT_POLICIES) * 3, "PR168_RP2_ORDER_INTENT_COUNT", str(final["order_intent_count"]))
    assert_true(final["rank2_evidence_handoff_count"] > 0, "PR168_RP2_RANK2_EMPTY", str(final))
    for key in (
        "real_positive_count",
        "real_negative_count",
        "champion_allowed_count",
        "live_candidate_allowed_count",
        "historical_full_book_assumption_violation_count",
        "market_implied_probability_as_alpha_violation_count",
        "quantum_backend_execution_count",
        "quantum_advantage_claim_count",
        "no_orphan_violation_count",
        "path_length_fail_count",
        "long_physical_filename_duplicate_count",
    ):
        assert_true(final.get(key) == 0, "PR168_RP2_FORBIDDEN_COUNT_NONZERO", f"{key}={final.get(key)}")
    for key in (
        "live_authority_created_flag",
        "profit_evidence_created_flag",
        "source_truth_acceptance_created_flag",
        "qtt_sha_or_atomicrows_hash_authority_flag",
    ):
        assert_true(final.get(key) is False, "PR168_RP2_FORBIDDEN_FLAG_TRUE", key)


def validate_map2() -> None:
    map2 = rows("map2_promote")
    assert_true(len(map2) == final_summary()["map2_promotion_attempt_count"], "PR168_RP2_MAP2_SHARD_COUNT", str(len(map2)))
    for row in map2:
        assert_true(row["original_gfp2r_compute_row_ref"], "PR168_RP2_MAP2_NO_GFP2R_REF", row["map2_row_id"])
        if row["promotion_state"] == "EXACT_REPAIRED_QKU_FORMULA_CANDIDATE_COMPUTE_READY":
            for key in ("canonical_qku_id", "canonical_formula_id", "formula_variant_id", "data_consumer_id"):
                assert_true(row.get(key), "PR168_RP2_EXACT_IDENTITY_INCOMPLETE", f"{row['map2_row_id']} {key}")
        else:
            assert_true(row.get("repair_route_if_not_promoted"), "PR168_RP2_PROVISIONAL_WITHOUT_REPAIR", row["map2_row_id"])
        assert_true(row["historical_full_book_assumption_allowed_flag"] is False, "PR168_RP2_FULL_BOOK_ASSUMED", row["map2_row_id"])


def validate_order_replay_paper() -> None:
    intents = rows("order_intents")
    replay = rows("replay_exec")
    paper = rows("paper_exec")
    assert_true(len(intents) == len(replay) == len(paper), "PR168_RP2_REPLAY_PAPER_COUNTS", f"{len(intents)} {len(replay)} {len(paper)}")
    assert_true({row["order_policy"] for row in intents}.issuperset(set(INTENT_POLICIES)), "PR168_RP2_POLICY_MISSING", "intent policies")
    for row in intents:
        assert_true(row["paper_only_flag"] is True, "PR168_RP2_INTENT_NOT_PAPER_ONLY", row["order_intent_id"])
        assert_true(row["live_order_authority_flag"] is False, "PR168_RP2_INTENT_LIVE_AUTHORITY", row["order_intent_id"])
    for row in replay:
        for key in (
            "replay_gross_pnl_candidate",
            "replay_tca_total_candidate",
            "replay_net_pnl_after_tca_candidate",
            "replay_fill_adjusted_expected_pnl_candidate",
            "replay_latency_adjusted_pnl_candidate",
            "replay_capacity_adjusted_pnl_candidate",
            "replay_no_trade_margin_candidate",
        ):
            assert_true(isinstance(row.get(key), (int, float)), "PR168_RP2_REPLAY_NUMERIC_MISSING", f"{row['replay_row_id']} {key}")
        assert_true(float(row["fill_probability_candidate"]) < 1.0, "PR168_RP2_FILL_DEFAULT_ONE", row["replay_row_id"])
    for row in paper:
        assert_true(row["private_cash_receipt_created_flag"] is False, "PR168_RP2_PRIVATE_CASH_RECEIPT", row["paper_ledger_row_id"])
        assert_true(row["live_order_receipt_created_flag"] is False, "PR168_RP2_LIVE_ORDER_RECEIPT", row["paper_ledger_row_id"])


def validate_tca_scenarios_rank2() -> None:
    tca = rows("tca")
    replay = rows("replay_exec")
    scenarios = rows("scenarios")
    rank2 = rows("rank2_rows")
    assert_true(len(tca) == len(replay), "PR168_RP2_TCA_COUNT", str(len(tca)))
    assert_true({row["scenario_family"] for row in scenarios}.issuperset(set([
        "BASE_OBSERVED",
        "NO_TRADE_BASELINE",
        "WIDE_SPREAD_PLUS_1C",
        "THIN_BOOK_50_PERCENT_DEPTH",
        "LATENCY_DELAY_LONG",
        "HISTORICAL_FULL_BOOK_MISSING",
        "SOURCE_ACCEPTANCE_PENDING",
        "FORMULA_INPUT_REPAIR_PENDING",
        "CAPACITY_DEPTH_LIMIT",
    ])), "PR168_RP2_SCENARIOS_MISSING", "scenario families")
    for row in tca:
        assert_true(row["explicit_fee_candidate"] != 0 or row["TCA_total_candidate"] == 0, "PR168_RP2_FAKE_ZERO_FEE", row["tca_row_id"])
        assert_true(row["TCA_missing_component_flags"], "PR168_RP2_TCA_NO_GAP_FLAGS", row["tca_row_id"])
    for row in rank2:
        assert_true(row["rank2_consumption_allowed_flag"] is True, "PR168_RP2_RANK2_NOT_ALLOWED", row["rank2_evidence_row_id"])
        assert_true(row["champion_allowed_flag"] is False, "PR168_RP2_CHAMPION_ALLOWED", row["rank2_evidence_row_id"])
        assert_true(row["live_candidate_allowed_flag"] is False, "PR168_RP2_LIVE_ALLOWED", row["rank2_evidence_row_id"])
        assert_true(row["candidate_only_flag"] is True, "PR168_RP2_RANK2_NOT_CANDIDATE_ONLY", row["rank2_evidence_row_id"])


def validate_formula_quantum_agent() -> None:
    contracts = rows("formula_contracts")
    routes = records("PR168_RP2_FormulaComputabilityRouteLedger")["sample_rows"]
    quantum = rows("q_stack")
    connector = rows("connector_routes")
    assert_true(contracts, "PR168_RP2_NO_FORMULA_CONTRACTS", "formula contracts")
    for row in contracts:
        for key in (
            "formula_plugin_id",
            "data_requirement_contract_ref",
            "unit_normalization_contract_ref",
            "execution_policy_grid_ref",
            "replay_paper_compute_receipt_schema_ref",
            "quantum_objective_mapping_contract_ref",
            "agent_route_contract_ref",
        ):
            assert_true(row.get(key), "PR168_RP2_FORMULA_CONTRACT_FIELD_MISSING", f"{row.get('formula_plugin_id')} {key}")
        assert_true(row["metadata_only_formula_pass_flag"] is False, "PR168_RP2_METADATA_ONLY_FORMULA", row["formula_plugin_id"])
    assert_true(routes, "PR168_RP2_NO_COMPUTABILITY_ROUTES", "routes")
    for row in routes:
        assert_true(row["computability_route_state"] in COMPUTABILITY_ROUTES, "PR168_RP2_BAD_ROUTE_STATE", row["row_id"])
    for row in quantum:
        assert_true(row["binary_variable_id"], "PR168_RP2_Q_NO_VARIABLE", row["quantum_stack_row_id"])
        assert_true(row["linear_coefficient_refs"], "PR168_RP2_Q_NO_LINEAR", row["quantum_stack_row_id"])
        assert_true(row["constraint_refs"], "PR168_RP2_Q_NO_CONSTRAINT", row["quantum_stack_row_id"])
        assert_true(row["classical_fallback_exists"] is True, "PR168_RP2_Q_NO_FALLBACK", row["quantum_stack_row_id"])
        assert_true(row["quantum_backend_execution_flag"] is False, "PR168_RP2_Q_BACKEND", row["quantum_stack_row_id"])
        assert_true(row["quantum_advantage_claim_flag"] is False, "PR168_RP2_Q_ADVANTAGE", row["quantum_stack_row_id"])
    for row in connector:
        assert_true(row["connector_semantic_binding_created_flag"] is False, "PR168_RP2_CONNECTOR_BINDING", row["connector_route_id"])
        assert_true(row["private_state_access_created_flag"] is False, "PR168_RP2_CONNECTOR_PRIVATE_STATE", row["connector_route_id"])
        assert_true(row["order_authority_created_flag"] is False, "PR168_RP2_CONNECTOR_ORDER", row["connector_route_id"])


def validate_aliases_paths() -> None:
    alias_records = records("PR168_RP2_FileAliasLedger")["rows"]
    path_records = records("PR168_RP2_PathLengthAudit")["rows"]
    by_logical = {}
    for row in alias_records:
        logical = row["logical_artifact_id"]
        assert_true(logical not in by_logical, "PR168_RP2_ALIAS_DUPLICATE_LOGICAL", logical)
        by_logical[logical] = row["short_physical_path"]
    for logical, physical in REPORT_ALIASES.items():
        assert_true(by_logical.get(logical) == f"docs/master_plan/generated/{physical}", "PR168_RP2_ALIAS_REPORT_MISSING", logical)
        long_copy = GENERATED_ROOT / f"{logical}.report.json"
        if long_copy.name != physical:
            assert_true(not long_copy.exists(), "PR168_RP2_LONG_DUPLICATE_REPORT", str(long_copy))
    for row in path_records:
        assert_true(row["path_length"] <= FAIL_PATH, "PR168_RP2_PATH_TOO_LONG", row["path"])
        if row["path"].startswith("tests/pr168_rp2/"):
            assert_true(len(Path(row["path"]).name) <= 96, "PR168_RP2_TEST_NAME_TOO_LONG", row["path"])
    assert_true((GENERATED_ROOT / "rp2p").name == "rp2p", "PR168_RP2_SHARD_DIR_NOT_SHORT", "rp2p")


def validate_no_forbidden_authority() -> None:
    for report_id in REPORT_ALIASES:
        payload = load_report(report_id)
        for item in walk(payload):
            for key in FALSE_FLAG_KEYS:
                if key in item:
                    assert_true(item[key] is False, "PR168_RP2_FORBIDDEN_AUTHORITY_FLAG", f"{report_id} {key}")
            state_values = [str(value) for value in item.values() if isinstance(value, str)]
            forbidden = {"REAL_POSITIVE", "REAL_NEGATIVE", "CHAMPION", "LIVE_CANDIDATE", "PROFIT_PROOF", "SOURCE_TRUTH_ACCEPTED_BY_RP2", "CONNECTOR_BOUND_BY_RP2", "ORDER_AUTHORITY_CREATED_BY_RP2", "QUANTUM_BACKEND_EXECUTED_BY_RP2", "QUANTUM_ADVANTAGE_PROVEN_BY_RP2"}
            assert_true(not forbidden.intersection(state_values), "PR168_RP2_FORBIDDEN_STATE", f"{report_id} {forbidden.intersection(state_values)}")


def validate_generated_reports() -> list[str]:
    checks = [
        validate_reports_exist,
        validate_final_summary,
        validate_map2,
        validate_order_replay_paper,
        validate_tca_scenarios_rank2,
        validate_formula_quantum_agent,
        validate_aliases_paths,
        validate_no_forbidden_authority,
    ]
    failures = []
    for check in checks:
        try:
            check()
        except AssertionError as exc:
            failures.append(str(exc))
    return failures


def run_validation(_name: str = "all") -> None:
    failures = validate_generated_reports()
    assert_true(not failures, "PR168_RP2_VALIDATION_FAILURES", "\n".join(failures))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", default="all")
    args = parser.parse_args()
    run_validation(args.check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
