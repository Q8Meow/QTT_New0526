"""Validator for PR168-VS1 generated trading-intelligence artifacts."""

from __future__ import annotations

import argparse
from functools import lru_cache
from pathlib import Path
from typing import Any

from .models import (
    BLOCKER_POLICY_REF,
    EXECUTION_AUTHORITY_REF,
    GENERATED_DIR,
    JSONL_OUTPUTS,
    PLATFORM_IDS,
    REQUIRED_BLOCKER_CODES,
    REPORT_OUTPUTS,
    REPO_ROOT,
    RunConfig,
    dec,
    read_json,
    read_jsonl,
)


class VS1ValidationError(AssertionError):
    """Raised when the VS1 generated surface violates its contract."""


def _failures() -> list[str]:
    failures: list[str] = []
    if not GENERATED_DIR.is_dir():
        failures.append("MISSING_GENERATED_DIR")
        return failures
    for name in JSONL_OUTPUTS:
        path = GENERATED_DIR / name
        manifest = path.with_suffix(".manifest.json")
        if not path.is_file():
            failures.append(f"MISSING_JSONL:{name}")
            continue
        if not manifest.is_file():
            failures.append(f"MISSING_MANIFEST:{manifest.name}")
            continue
        rows = read_jsonl(path)
        payload = read_json(manifest)
        if payload.get("row_count") != len(rows):
            failures.append(f"MANIFEST_ROW_COUNT_MISMATCH:{name}")
        if not rows:
            failures.append(f"EMPTY_JSONL:{name}")
    for name in REPORT_OUTPUTS:
        if not (GENERATED_DIR / name).is_file():
            failures.append(f"MISSING_REPORT:{name}")
    if failures:
        return failures

    rows = {name: read_jsonl(GENERATED_DIR / name) for name in JSONL_OUTPUTS}
    reports = {name: read_json(GENERATED_DIR / name) for name in REPORT_OUTPUTS}
    authority = reports["vs1_execution_authority_receipt.report.json"]
    if authority.get("execution_authority_ref") != EXECUTION_AUTHORITY_REF:
        failures.append("EXECUTION_AUTHORITY_REF_MISMATCH")
    forbidden_authority_true = [
        key
        for key, value in authority.items()
        if key.endswith("_authorized") and key not in {"paper_submit_authorized", "live_submit_authorized"} and value is not False
    ]
    if authority.get("paper_submit_authorized") is not False or authority.get("live_submit_authorized") is not False:
        failures.append("SUBMIT_AUTHORITY_TRUE")
    if forbidden_authority_true:
        failures.append(f"FORBIDDEN_AUTHORITY_TRUE:{forbidden_authority_true}")

    blocker_codes = {row["blocker_code"] for row in rows["vs1_blocker_policy_registry.jsonl"]}
    if not set(REQUIRED_BLOCKER_CODES).issubset(blocker_codes):
        failures.append("BLOCKER_REGISTRY_MISSING_REQUIRED_CODES")
    policy_refs = {row["policy_parameter_ref"] for row in rows["vs1_policy_parameter_registry.jsonl"]}
    if len(policy_refs) < 50:
        failures.append("POLICY_PARAMETER_REGISTRY_TOO_SMALL")

    for filename, file_rows in rows.items():
        for index, row in enumerate(file_rows, start=1):
            if row.get("execution_authority_ref") != EXECUTION_AUTHORITY_REF:
                failures.append(f"ROW_AUTHORITY_REF_MISMATCH:{filename}:{index}")
            if row.get("blocker_policy_ref") != BLOCKER_POLICY_REF:
                failures.append(f"ROW_BLOCKER_REF_MISMATCH:{filename}:{index}")
            for code in row.get("blocker_codes", []):
                if code not in blocker_codes:
                    failures.append(f"UNDEFINED_BLOCKER_CODE:{filename}:{code}")
            if not row.get("producer_agent"):
                failures.append(f"ROW_MISSING_PRODUCER:{filename}:{index}")
            if not row.get("consumer_agent_refs"):
                failures.append(f"ROW_MISSING_CONSUMER:{filename}:{index}")
            if "no_live_submit_flag" in row or "paper_execution_submitted_flag" in row or "live_execution_submitted_flag" in row:
                failures.append(f"SCATTERED_SUBMIT_FLAG:{filename}:{index}")

    required_rp5c = [
        "docs/master_plan/generated/rp5c/immutable_qku_formula_library.jsonl",
        "docs/master_plan/generated/rp5c/agent_qku_access_policy_registry.jsonl",
        "docs/master_plan/generated/rp5c/stage_agent_qku_universe_resolver.jsonl",
    ]
    for ref in required_rp5c:
        if not (REPO_ROOT / ref).is_file():
            failures.append(f"MISSING_RP5C_REQUIRED:{ref}")
    reading_refs = {row["file_ref"] for row in rows["vs1_reading_receipts.jsonl"]}
    if "docs/master_plan/generated/rp5c/agent_qku_access_policy_registry.jsonl" not in reading_refs:
        failures.append("CORRECT_AGENT_QKU_ACCESS_POLICY_PATH_NOT_READ")
    if "docs/master_plan/generated/rp5c/agent_access_policy_registry.jsonl" in reading_refs:
        failures.append("INCORRECT_AGENT_ACCESS_POLICY_PATH_REQUIRED")

    duty_rows = rows["agent_duty_evidence_discovery_receipts.jsonl"]
    if not duty_rows or not duty_rows[0].get("discovery_status"):
        failures.append("PR165_D2_DISCOVERY_NOT_RECORDED")

    context_rows = rows["context_formula_selection_receipts.jsonl"]
    if not context_rows:
        failures.append("NO_CONTEXT_SELECTION_ROWS")
    for row in context_rows:
        count = int(row["selected_identity_count"])
        if count < 10 or count > 50:
            failures.append(f"SELECTED_IDENTITY_COUNT_OUT_OF_BOUNDS:{row['context_selection_id']}")
        if row["no_unknown_needs_review_flag"] is not True:
            failures.append("UNKNOWN_NEEDS_REVIEW_SELECTED")

    for row in rows["selected_computable_qku_formula_bindings.jsonl"]:
        if row["metadata_only_flag"] is not False:
            failures.append(f"METADATA_ONLY_BINDING:{row['computable_binding_id']}")
        if row["computable_for_vs1_fixture_flag"] is not True:
            failures.append(f"BINDING_NOT_COMPUTABLE:{row['computable_binding_id']}")
        if int(row["missing_input_count"]) != 0:
            failures.append(f"BINDING_MISSING_INPUT:{row['computable_binding_id']}")
        if not row["input_fields"] or not row["output_field"] or not row["computable_algorithm_ref"]:
            failures.append(f"BINDING_CONTRACT_INCOMPLETE:{row['computable_binding_id']}")

    for row in rows["temporary_stack_candidate_receipts.jsonl"]:
        if row["ephemeral_stack_flag"] is not True or row["bulk_grid_retained_flag"] is not False:
            failures.append(f"STACK_NOT_EPHEMERAL:{row['temporary_stack_id']}")
        if int(row["stack_size"]) > 3:
            failures.append(f"STACK_TOO_LARGE:{row['temporary_stack_id']}")

    for row in rows["trade_plan_variable_search_receipts.jsonl"]:
        for key in ("bounded_search_flag", "ex_ante_search_flag", "hindsight_free_flag"):
            if row[key] is not True:
                failures.append(f"SEARCH_FLAG_FALSE:{key}:{row['variable_search_ref']}")
        for key in ("outcome_backsolve_flag",):
            if row[key] is not False:
                failures.append(f"SEARCH_FORBIDDEN_FLAG_TRUE:{key}:{row['variable_search_ref']}")
        for key in ("gate_relaxation_attempt_count", "impossible_price_candidate_count", "impossible_fill_candidate_count"):
            if int(row[key]) != 0:
                failures.append(f"SEARCH_FORBIDDEN_COUNT_NONZERO:{key}:{row['variable_search_ref']}")

    search_refs = {row["variable_search_ref"] for row in rows["trade_plan_variable_search_receipts.jsonl"]}
    for row in rows["order_variable_candidate_receipts.jsonl"]:
        if row["variable_search_ref"] not in search_refs:
            failures.append(f"ORDER_WITHOUT_SEARCH:{row['order_variable_candidate_id']}")
        if row["ex_ante_candidate_flag"] is not True or row["feasible_price_flag"] is not True or row["feasible_fill_flag"] is not True:
            failures.append(f"ORDER_FEASIBILITY_FLAG_FALSE:{row['order_variable_candidate_id']}")

    tca_fields = {
        "fees_cash",
        "spread_cost_cash",
        "slippage_cash",
        "queue_fill_shortfall_cash",
        "cancel_replace_cost_cash",
        "latency_penalty_cash",
        "capital_lock_cost_cash",
        "capacity_cost_cash",
        "crowding_cost_cash",
        "tca_total_cash",
    }
    for row in rows["tca_breakdown_receipts.jsonl"]:
        if not tca_fields.issubset(row):
            failures.append(f"TCA_FIELDS_MISSING:{row.get('tca_breakdown_ref')}")
        total = sum(dec(row[field]) for field in tca_fields if field != "tca_total_cash")
        if abs(total - dec(row["tca_total_cash"])) > dec("0.0002"):
            failures.append(f"TCA_TOTAL_MISMATCH:{row['tca_breakdown_ref']}")

    objective_terms = {row["objective_term_ref"] for row in rows["objective_term_ledger.jsonl"]}
    constraint_refs = {row["constraint_penalty_ref"] for row in rows["constraint_penalty_policy_receipts.jsonl"]}
    required_terms = {
        "expected_edge",
        "fill_adjusted_edge",
        "fees",
        "spread",
        "slippage",
        "queue_fill_shortfall",
        "cancel_replace_cost",
        "latency_decay",
        "capital_lock",
        "capacity_cost",
        "crowding_cost",
        "uncertainty",
        "overfit_fdr",
        "scenario_tail",
        "portfolio_overlap",
        "marginal_utility",
        "diversification_bonus",
        "correlation_overlap_penalty",
        "no_trade_margin",
    }
    if not required_terms.issubset({row["term_name"] for row in rows["objective_term_ledger.jsonl"]}):
        failures.append("OBJECTIVE_TERM_FAMILY_MISSING")
    if len(constraint_refs) < 18:
        failures.append("CONSTRAINT_ROWS_MISSING")

    candidates = rows["trade_plan_candidates.jsonl"]
    if not candidates:
        failures.append("NO_TRADE_PLAN_CANDIDATES")
    for candidate in candidates:
        if candidate["ex_ante_candidate_flag"] is not True or candidate["hindsight_free_flag"] is not True:
            failures.append(f"CANDIDATE_NOT_EX_ANTE:{candidate['trade_plan_id']}")
        if int(candidate["gate_relaxation_count"]) != 0 or candidate["impossible_price_flag"] is not False or candidate["impossible_fill_flag"] is not False:
            failures.append(f"CANDIDATE_FORBIDDEN_FEASIBILITY:{candidate['trade_plan_id']}")
        if candidate["selection_status"] == "TOP_K_ELIGIBLE":
            if dec(candidate["candidate_minus_no_trade_cash"]) <= 0 or dec(candidate["lower_confidence_bound_pnl_cash"]) <= 0:
                failures.append(f"TOPK_WITHOUT_POSITIVE_NET_AND_LCB:{candidate['trade_plan_id']}")
        for ref in candidate["objective_term_refs"]:
            if ref not in objective_terms:
                failures.append(f"CANDIDATE_OBJECTIVE_REF_MISSING:{candidate['trade_plan_id']}:{ref}")
        for ref in candidate["constraint_penalty_refs"]:
            if ref not in constraint_refs:
                failures.append(f"CANDIDATE_CONSTRAINT_REF_MISSING:{candidate['trade_plan_id']}:{ref}")

    fixture_platforms = {row["platform_id"] for row in rows["trade_target_fixtures.jsonl"]}
    if fixture_platforms != set(PLATFORM_IDS):
        failures.append(f"PLATFORM_COVERAGE_MISMATCH:{fixture_platforms}")
    eligible_positive = [row for row in candidates if row["fixture_id"].startswith("VS1_FIXTURE_0001") and row["selection_status"] == "TOP_K_ELIGIBLE"]
    if not eligible_positive:
        failures.append("POSITIVE_FIXTURE_NO_TOPK_ELIGIBLE")
    negative_no_trade = [
        row for row in rows["no_trade_comparator_receipts.jsonl"] if row["fixture_id"].startswith("VS1_FIXTURE_0002") and row["no_trade_wins_flag"] is True
    ]
    if not negative_no_trade:
        failures.append("NEGATIVE_FIXTURE_NO_NO_TRADE")
    thin_bad = [
        row for row in candidates if row["fixture_id"].startswith("VS1_FIXTURE_0003") and row["selection_status"] == "TOP_K_ELIGIBLE"
    ]
    if thin_bad:
        failures.append("THIN_BOOK_FALSE_POSITIVE_ELIGIBLE")
    crowded_penalty = [
        row for row in rows["capacity_crowding_receipts.jsonl"] if row["fixture_id"].startswith("VS1_FIXTURE_0004") and dec(row["capacity_penalty_cash"]) > 0
    ]
    if not crowded_penalty:
        failures.append("CROWDED_FIXTURE_NO_CAPACITY_PENALTY")
    portfolio_penalty = [
        row for row in rows["portfolio_diversification_receipts.jsonl"] if row["fixture_id"].startswith("VS1_FIXTURE_0005") and dec(row["portfolio_penalty_cash"]) > 0
    ]
    if not portfolio_penalty:
        failures.append("PORTFOLIO_FIXTURE_NO_PENALTY")

    previews = rows["paper_intent_candidate_previews.jsonl"]
    if not previews:
        failures.append("NO_PAPER_INTENT_PREVIEWS")
    if any(row.get("paper_ready_preview_flag") is not True for row in previews):
        failures.append("PAPER_PREVIEW_NOT_READY")
    champions = rows["champion_challenger_selection_receipts.jsonl"]
    if not any(row["champion_trade_plan_id"] for row in champions):
        failures.append("NO_CHAMPION_SELECTED")

    for row in rows["trade_plan_quantum_encoding_receipts.jsonl"]:
        if row["quantum_backend_execution_flag"] is not False or row["quantum_advantage_claim_flag"] is not False:
            failures.append(f"QUANTUM_FORBIDDEN_FLAG:{row['quantum_encoding_ref']}")
        if not row["classical_fallback_optimizer_refs"]:
            failures.append(f"QUANTUM_NO_CLASSICAL_FALLBACK:{row['quantum_encoding_ref']}")
        for policy_field in ("anneal_time_policy", "num_reads_policy", "chain_strength_policy", "qaoa_reps_policy", "shots_policy"):
            if row[policy_field] != "NOT_SET_IN_VS1":
                failures.append(f"QUANTUM_BACKEND_PARAM_SET:{row['quantum_encoding_ref']}:{policy_field}")
    for row in rows["quantum_structural_readiness_receipts.jsonl"]:
        if row["quantum_backend_execution_flag"] is not False or row["quantum_advantage_claim_flag"] is not False:
            failures.append(f"QUANTUM_READY_FORBIDDEN_FLAG:{row['quantum_structural_readiness_ref']}")

    external_rows = rows["external_research_candidate_receipts.jsonl"]
    for row in external_rows:
        for key in (
            "accepted_source_fact_flag",
            "connector_semantic_binding_flag",
            "fixture_constant_binding_flag",
            "live_order_authority_flag",
            "runtime_dependency_flag",
            "external_code_cloned_flag",
            "external_code_executed_flag",
        ):
            if row[key] is not False:
                failures.append(f"EXTERNAL_RESEARCH_FORBIDDEN_FLAG:{key}")

    for row in rows["no_pnl_forcing_proof.jsonl"]:
        for key, value in row.items():
            if key.endswith("_count") and key not in {"trade_plan_ids_checked_count"} and isinstance(value, int) and value != 0:
                failures.append(f"NO_PNL_FORCING_COUNT_NONZERO:{key}:{row['fixture_id']}")
        required_zero = [
            "gate_relaxation_attempt_count",
            "formula_mutation_count",
            "qku_deletion_count",
            "formula_deletion_count",
            "global_qku_ban_count",
            "global_formula_ban_count",
            "impossible_price_candidate_count",
            "impossible_fill_candidate_count",
            "hindsight_backsolve_count",
            "post_hoc_exit_selection_count",
            "ignored_fee_count",
            "ignored_spread_count",
            "ignored_slippage_count",
            "ignored_fill_risk_count",
            "ignored_latency_risk_count",
            "ignored_capacity_risk_count",
            "ignored_portfolio_risk_count",
            "ignored_scenario_risk_count",
            "ignored_overfit_fdr_count",
            "raw_edge_promoted_without_tca_count",
            "no_trade_overridden_count",
        ]
        for key in required_zero:
            if int(row[key]) != 0:
                failures.append(f"NO_PNL_FORCING_REQUIRED_ZERO_NONZERO:{key}")

    for row in rows["no_orphan_qku_formula_proof.jsonl"]:
        if row["orphan_identity_flag"] or row["orphan_formula_flag"] or row["orphan_qku_flag"]:
            failures.append(f"ORPHAN_SELECTED_IDENTITY:{row['identity_ref']}")
        if not row["downstream_trade_plan_refs"]:
            failures.append(f"SELECTED_IDENTITY_WITHOUT_TRADE_PLAN:{row['identity_ref']}")
    for row in rows["vs1_no_orphan_artifact_ledger.jsonl"]:
        if row["orphan_artifact_flag"] is not False:
            failures.append(f"ORPHAN_ARTIFACT:{row['artifact_ref']}")

    run_report = reports["vs1_run_receipt.report.json"]
    hard_zero_fields = [
        "metadata_only_selected_count",
        "orphan_artifact_count",
        "orphan_selected_qku_count",
        "orphan_selected_formula_count",
        "undefined_blocker_code_count",
        "scattered_no_live_flag_count",
        "gate_relaxation_attempt_count",
        "hindsight_backsolve_count",
        "impossible_price_candidate_count",
        "impossible_fill_candidate_count",
        "global_formula_ban_count",
        "global_qku_ban_count",
        "formula_mutation_count",
        "qku_deletion_count",
        "paper_submit_count",
        "live_submit_count",
        "connector_runtime_count",
        "private_state_fetch_count",
        "cash_runtime_count",
        "venue_api_call_count",
        "source_fact_acceptance_count",
        "fixture_constant_from_external_source_count",
        "quantum_backend_execution_count",
        "quantum_advantage_claim_count",
        "qtt_sha_authority_count",
        "qtt_generated_sha_file_count",
        "atomicrows_bundle_sha_reference_count",
    ]
    for field in hard_zero_fields:
        if int(run_report.get(field, -1)) != 0:
            failures.append(f"RUN_REPORT_HARD_ZERO_NONZERO:{field}:{run_report.get(field)}")
    if run_report.get("positive_fixture_topk_count", 0) < 1:
        failures.append("RUN_REPORT_POSITIVE_TOPK_ZERO")
    if run_report.get("negative_fixture_no_trade_count", 0) < 1:
        failures.append("RUN_REPORT_NEGATIVE_NOTRADE_ZERO")
    if run_report.get("validation_status") != "PASS_GENERATED_OFFLINE":
        failures.append("RUN_REPORT_VALIDATION_STATUS_BAD")

    generated_text = "\n".join(path.read_text(encoding="utf-8") for path in GENERATED_DIR.glob("*") if path.is_file())
    atomicrows_bundle_sha_marker = "AtomicRows.bundle" + ".sha256"
    if atomicrows_bundle_sha_marker in generated_text:
        failures.append("ATOMICROWS_BUNDLE_SHA_REFERENCE_FOUND")
    forbidden_generated_files = [path.name for path in GENERATED_DIR.glob("*.sha256")]
    if forbidden_generated_files:
        failures.append(f"QTT_GENERATED_SHA_FILE_FOUND:{forbidden_generated_files}")
    return failures


def _generated_file_texts() -> dict[str, str]:
    return {path.name: path.read_text(encoding="utf-8") for path in sorted(GENERATED_DIR.glob("*"), key=lambda p: p.name) if path.is_file()}


def _assert_deterministic() -> None:
    from .runner import run_slice

    before = _generated_file_texts()
    run_slice(RunConfig())
    middle = _generated_file_texts()
    run_slice(RunConfig())
    after = _generated_file_texts()
    if before != middle or middle != after:
        raise VS1ValidationError("VS1 generated outputs are not deterministic across repeated runs")


@lru_cache(maxsize=1)
def _validation_result() -> dict[str, Any]:
    failures = _failures()
    if failures:
        raise VS1ValidationError("; ".join(failures[:50]))
    _assert_deterministic()
    failures_after = _failures()
    if failures_after:
        raise VS1ValidationError("; ".join(failures_after[:50]))
    run_report = read_json(GENERATED_DIR / "vs1_run_receipt.report.json")
    return {
        "artifact_dir": str(GENERATED_DIR.relative_to(REPO_ROOT)).replace("\\", "/"),
        "champion_count": run_report["champion_count"],
        "orphan_artifact_count": run_report["orphan_artifact_count"],
        "selected_identity_count": run_report["selected_identity_count"],
        "trade_plan_candidate_count": run_report["trade_plan_candidate_count"],
        "validation": "PR168_VS1_TRADING_INTELLIGENCE_SLICE_OK",
    }


def run_validation(_section: str | None = None) -> dict[str, Any]:
    return dict(_validation_result())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate PR168-VS1 trading-intelligence artifacts.")
    parser.add_argument("section", nargs="?", default=None)
    args = parser.parse_args(argv)
    result = run_validation(args.section)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
