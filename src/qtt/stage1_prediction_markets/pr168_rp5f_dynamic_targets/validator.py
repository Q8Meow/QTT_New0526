"""Validator for PR168-RP5F dynamic target/grid artifacts."""

from __future__ import annotations

import argparse
from functools import lru_cache
from pathlib import Path
from typing import Any

from .models import (
    BLOCKER_POLICY_REF,
    EXECUTION_AUTHORITY_REF,
    FALSE_FLAG_FIELDS,
    FORBIDDEN_STATE_VALUES,
    GENERATED_DIR,
    JSON_OUTPUTS,
    JSONL_OUTPUTS,
    REPORT_OUTPUTS,
    all_artifact_filenames,
    manifest_name,
    read_json,
    read_jsonl,
)
from .path_safety import path_safety_failures


class RP5FValidationError(AssertionError):
    """Raised when RP5F generated surfaces violate their contract."""


def _generated_file_texts() -> dict[str, str]:
    return {path.name: path.read_text(encoding="utf-8") for path in sorted(GENERATED_DIR.glob("*"), key=lambda p: p.name) if path.is_file()}


def _row_files() -> dict[str, list[dict[str, Any]]]:
    return {name: read_jsonl(GENERATED_DIR / name) for name in JSONL_OUTPUTS}


def _report_files() -> dict[str, dict[str, Any]]:
    return {name: read_json(GENERATED_DIR / name) for name in (*JSON_OUTPUTS, *REPORT_OUTPUTS)}


def _all_generated_text() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in GENERATED_DIR.glob("*") if path.is_file())


def _check_common_row(filename: str, index: int, row: dict[str, Any], failures: list[str]) -> None:
    required = (
        "schema_version",
        "row_id",
        "run_id",
        "created_at_utc",
        "source_pr",
        "upstream_refs",
        "downstream_refs",
        "owner_agent",
        "consumer_agents",
        "validation_refs",
        "execution_authority_ref",
        "blocker_policy_ref",
        "connector_refs_or_future_connector_status",
        "provenance_tier",
    )
    for key in required:
        if row.get(key) in (None, "", []):
            failures.append(f"ROW_MISSING_COMMON_FIELD:{filename}:{index}:{key}")
    if row.get("source_pr") != "PR168-RP5F":
        failures.append(f"ROW_SOURCE_PR_BAD:{filename}:{index}:{row.get('source_pr')}")
    if row.get("execution_authority_ref") != EXECUTION_AUTHORITY_REF:
        failures.append(f"ROW_EXEC_AUTH_MISMATCH:{filename}:{index}")
    if row.get("blocker_policy_ref") != BLOCKER_POLICY_REF:
        failures.append(f"ROW_BLOCKER_REF_MISMATCH:{filename}:{index}")
    for key in FALSE_FLAG_FIELDS:
        if row.get(key) is not False:
            failures.append(f"ROW_FORBIDDEN_FLAG_TRUE:{filename}:{index}:{key}")
    for key in ("fixed_trade_instruction_flag", "non_expiring_trade_plan_flag", "stale_candidate_authority_flag"):
        if row.get(key) is not False:
            failures.append(f"ROW_DYNAMIC_BOUNDARY_FLAG_TRUE:{filename}:{index}:{key}")


def _target_grid_seed_failures(rows: dict[str, list[dict[str, Any]]]) -> list[str]:
    failures: list[str] = []
    targets = rows["targets.jsonl"]
    grids = rows["var_grid.jsonl"]
    seeds = rows["trade_seed.jsonl"]
    if not targets:
        failures.append("TARGETS_EMPTY")
    if not grids:
        failures.append("VAR_GRIDS_EMPTY")
    if not seeds:
        failures.append("TRADE_SEEDS_EMPTY")
    target_ids = {row["target_id"] for row in targets}
    grid_ids = {row["grid_id"] for row in grids}
    seed_ids = {row["trade_seed_id"] for row in seeds}
    for target in targets:
        for key in ("target_id", "snapshot_id", "asof_timestamp_utc", "eligible_stack_preview_refs", "eligible_executable_now_refs", "rp5d_r1_promoted_overlay_refs"):
            if target.get(key) in (None, "", []):
                failures.append(f"TARGET_MISSING_DYNAMIC_FIELD:{target.get('target_id')}:{key}")
        if target.get("candidate_status") != "DYNAMIC_TRADE_TARGET_CANDIDATE":
            failures.append(f"TARGET_BAD_STATUS:{target.get('target_id')}")
    for grid in grids:
        for key in ("grid_id", "target_id", "snapshot_id", "asof_timestamp_utc", "side_values", "entry_price_values", "order_size_values", "grid_size", "use_and_dump_policy_ref"):
            if grid.get(key) in (None, "", []):
                failures.append(f"GRID_MISSING_DYNAMIC_FIELD:{grid.get('grid_id')}:{key}")
        if grid.get("target_id") not in target_ids:
            failures.append(f"GRID_TARGET_MISSING:{grid.get('grid_id')}")
        if grid.get("full_cartesian_persisted_flag") is not False or grid.get("bounded_grid_flag") is not True:
            failures.append(f"GRID_CARTESIAN_OR_UNBOUNDED:{grid.get('grid_id')}")
    for seed in seeds:
        for key in ("trade_seed_id", "target_id", "grid_id", "snapshot_id", "asof_timestamp_utc", "freshness_policy_ref", "ttl_policy_ref", "stale_invalidation_ref", "pre_submit_revalidation_ref"):
            if seed.get(key) in (None, "", []):
                failures.append(f"SEED_MISSING_DYNAMIC_FIELD:{seed.get('trade_seed_id')}:{key}")
        if seed.get("target_id") not in target_ids or seed.get("grid_id") not in grid_ids:
            failures.append(f"SEED_TARGET_OR_GRID_MISSING:{seed.get('trade_seed_id')}")
        if seed.get("rp5f_final_trade_plan_flag") is not False or seed.get("future_rp5g_required_flag") is not True:
            failures.append(f"SEED_TRADE_PLAN_BOUNDARY_BAD:{seed.get('trade_seed_id')}")
    stale_by_seed = {row["trade_seed_id"]: row for row in rows["stale_rules.jsonl"]}
    reval_by_seed = {row["trade_seed_id"]: row for row in rows["pre_submit_reval.jsonl"]}
    no_stale_by_seed = {row["trade_seed_id"]: row for row in rows["no_stale_candidate.jsonl"]}
    snapshot_reval_by_seed = {row["trade_seed_id"]: row for row in rows["snapshot_reval.jsonl"]}
    for seed_id in seed_ids:
        stale = stale_by_seed.get(seed_id, {})
        reval = reval_by_seed.get(seed_id, {})
        if not stale or stale.get("must_recompute_before_submit") is not True:
            failures.append(f"SEED_WITHOUT_STALE_RECOMPUTE:{seed_id}")
        for flag in (
            "required_before_paper_intent_flag",
            "required_before_live_dryrun_intent_flag",
            "required_before_shadow_input_flag",
            "required_before_limited_live_canary_flag",
            "required_before_live_order_flag",
            "latest_snapshot_required_flag",
            "risk_gate_required_flag",
            "source_freshness_required_flag",
            "market_data_truth_required_flag",
        ):
            if reval.get(flag) is not True:
                failures.append(f"SEED_REVALIDATION_FLAG_BAD:{seed_id}:{flag}")
        if no_stale_by_seed.get(seed_id, {}).get("stale_candidate_authority_flag") is not False:
            failures.append(f"NO_STALE_AUTHORITY_BAD:{seed_id}")
        if snapshot_reval_by_seed.get(seed_id, {}).get("pre_submit_revalidation_required_flag") is not True:
            failures.append(f"SNAPSHOT_REVAL_REQUIRED_BAD:{seed_id}")
    return failures


def _surface_failures(rows: dict[str, list[dict[str, Any]]], reports: dict[str, dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    if reports["missing_req.report.json"].get("fail_closed_flag") is not False or reports["missing_req.report.json"].get("missing_required_refs"):
        failures.append("MISSING_REQUIRED_INPUTS_PRESENT")
    if len(rows["owner_audit.jsonl"]) != 3:
        failures.append("OWNER_AUDIT_QUESTION_COUNT_BAD")
    for row in rows["owner_audit.jsonl"]:
        if row.get("profit_proof_created_flag") is not False or row.get("order_authority_created_flag") is not False:
            failures.append(f"OWNER_AUDIT_AUTHORITY_BAD:{row.get('owner_audit_id')}")
    if {row.get("platform") for row in rows["owner_enable.jsonl"]} != {"KALSHI", "POLYMARKET", "FORECASTEX_IBKR"}:
        failures.append("OWNER_ENABLE_PLATFORM_COVERAGE_BAD")
    for row in rows["owner_enable.jsonl"]:
        if row.get("rp5f_live_reachability_created_flag") is not False or row.get("most_restrictive_scope_wins_flag") is not True:
            failures.append(f"OWNER_ENABLE_AUTHORITY_BAD:{row.get('enablement_handoff_id')}")
    live_modes = {row.get("future_consumer") for row in rows["live_shadow_route.jsonl"]}
    if not {"LIVE_DRYRUN", "LIVE_PILOT", "TRIGGERED_SHADOW_COMPARISON", "LAUNCH_GATE"} <= live_modes:
        failures.append("LIVE_SHADOW_FUTURE_CONSUMER_COVERAGE_BAD")
    for row in rows["live_shadow_route.jsonl"]:
        if row.get("rp5f_authority_flag") is not False or row.get("pre_submit_revalidation_required_flag") is not True:
            failures.append(f"LIVE_SHADOW_AUTHORITY_BAD:{row.get('live_shadow_route_id')}")
    for filename in ("research_rec.jsonl", "source_intake.jsonl", "source_value_cand.jsonl", "source_coverage.jsonl"):
        for row in rows[filename]:
            if row.get("candidate_only_flag") is not True:
                failures.append(f"SOURCE_ROW_NOT_CANDIDATE_ONLY:{filename}:{row.get('row_id')}")
            for key in ("accepted_source_fact_flag", "connector_semantic_binding_flag", "live_default_flag", "proprietary_claim_flag", "profit_proof_flag"):
                if row.get(key) is not False:
                    failures.append(f"SOURCE_FORBIDDEN_FLAG_TRUE:{filename}:{row.get('row_id')}:{key}")
    if len(rows["pm_edge_hints.jsonl"]) < len(rows["targets.jsonl"]) * 8:
        failures.append("PM_EDGE_HINT_SURFACE_TOO_SMALL")
    required_edge_files = ("yes_no_parity.jsonl", "cross_venue_hints.jsonl", "orderbook_imbalance.jsonl", "liquidity_decay.jsonl", "event_news_hints.jsonl", "notrade_hints.jsonl", "edge_capture_map.jsonl")
    for filename in required_edge_files:
        if not rows[filename]:
            failures.append(f"EDGE_SURFACE_EMPTY:{filename}")
    for row in rows["edge_capture_map.jsonl"]:
        if row.get("rp5f_profit_proof_flag") is not False or row.get("rp5f_order_authority_flag") is not False:
            failures.append(f"EDGE_CAPTURE_AUTHORITY_BAD:{row.get('edge_capture_map_id')}")
    for filename in ("tca_inputs.jsonl", "fill_inputs.jsonl", "queue_fill_inputs.jsonl", "adverse_select.jsonl", "lat_inputs.jsonl", "capacity_inputs.jsonl", "cash_settle_inputs.jsonl"):
        if not rows[filename]:
            failures.append(f"EXECUTION_INPUT_SURFACE_EMPTY:{filename}")
    for row in rows["md_truth.jsonl"]:
        if row.get("executable_truth_allowed_flag") is not False or row.get("block_new_or_increased_exposure_flag") is not True:
            failures.append(f"MD_TRUTH_BOUNDARY_BAD:{row.get('snapshot_id')}")
    for row in rows["src_fresh.jsonl"]:
        if row.get("accepted_source_packet_required_flag") is not True or row.get("new_live_use_allowed_flag") is not False:
            failures.append(f"SOURCE_FRESH_BOUNDARY_BAD:{row.get('source_freshness_id')}")
    if not rows["qku_access.jsonl"] or not rows["library_query.jsonl"] or not rows["qku_compute_route.jsonl"] or not rows["qku_target_use.jsonl"]:
        failures.append("QKU_ROUTE_SURFACE_EMPTY")
    for row in rows["library_query.jsonl"]:
        if row.get("full_library_scan_flag") is not False or row.get("agent_direct_jsonl_scan_allowed_flag") is not False:
            failures.append(f"LIBRARY_QUERY_SCAN_BOUNDARY_BAD:{row.get('library_query_receipt_id')}")
    allowed_use = {
        "TARGET_ELIGIBLE_REPLAY_PAPER_EXEC_NOW",
        "TARGET_ELIGIBLE_AVAILABLE_ON_DEMAND",
        "TARGET_ELIGIBLE_SOURCE_REQUIRED",
        "TARGET_ELIGIBLE_EXECUTION_CONTRACT_INCOMPLETE",
        "NOT_STAGE1_APPLICABLE",
        "AGENT_DUTY_NOT_ALLOWED",
    }
    for row in rows["qku_compute_route.jsonl"]:
        if row.get("use_class") not in allowed_use:
            failures.append(f"QKU_BAD_USE_CLASS:{row.get('qku_compute_route_id')}")
        if row.get("full_library_scan_flag") is not False or row.get("metadata_only_flag") is not False:
            failures.append(f"QKU_ROUTE_SCAN_OR_META_BAD:{row.get('qku_compute_route_id')}")
    for filename in ("q_grid.jsonl", "q_constraints.jsonl", "q_interp.jsonl", "classic_fallback.jsonl"):
        if not rows[filename]:
            failures.append(f"QUANTUM_SURFACE_EMPTY:{filename}")
        for row in rows[filename]:
            for key in ("qopt_execution_flag", "quantum_backend_execution_flag", "quantum_advantage_claim_flag"):
                if row.get(key) is not False:
                    failures.append(f"QUANTUM_EXEC_FLAG_TRUE:{filename}:{row.get('row_id')}:{key}")
    for row in rows["q_grid.jsonl"]:
        for key in ("binary_side_variables", "entry_bucket_variables", "size_bucket_variables", "hold_duration_variables", "exit_rule_variables", "maker_taker_split_variables", "portfolio_exposure_variables", "capacity_constraints", "TCA_penalty_terms", "no_trade_comparator_constraint", "variable_count", "constraint_count", "classical_fallback_ref"):
            if row.get(key) in (None, "", []):
                failures.append(f"Q_GRID_FIELD_MISSING:{row.get('q_grid_id')}:{key}")
    for filename in ("completion_route.jsonl", "exec_now_delta_hint.jsonl", "learning_hooks.jsonl", "context_similarity_keys.jsonl", "target_failure_taxonomy.jsonl", "retest_policy_hints.jsonl"):
        if not rows[filename]:
            failures.append(f"SUPPORT_SURFACE_EMPTY:{filename}")
    for row in rows["completion_route.jsonl"]:
        if row.get("broad_global_blocker_flag") is not False:
            failures.append(f"COMPLETION_ROUTE_BROAD_BLOCKER:{row.get('completion_route_id')}")
    for report_name in ("to_paper.report.json", "to_live_dry.report.json", "to_shadow.report.json"):
        report = reports[report_name]
        if report.get("non_authority_handoff_flag") is not True or report.get("future_consumer_must_revalidate_flag") is not True:
            failures.append(f"HANDOFF_REVALIDATION_BOUNDARY_BAD:{report_name}")
        for key in ("paper_authority_flag", "shadow_authority_flag", "live_authority_flag", "order_authority_flag", "connector_write_flag", "private_state_fetch_flag", "cash_account_read_flag"):
            if report.get(key) is not False:
                failures.append(f"HANDOFF_AUTHORITY_FLAG_TRUE:{report_name}:{key}")
    return failures


def _failures() -> list[str]:
    failures: list[str] = []
    if not GENERATED_DIR.is_dir():
        return ["MISSING_RP5F_GENERATED_DIR"]
    expected_files = set(all_artifact_filenames())
    actual_files = {path.name for path in GENERATED_DIR.iterdir() if path.is_file()}
    for name in sorted(expected_files - actual_files):
        failures.append(f"MISSING_GENERATED_FILE:{name}")
    for failure in path_safety_failures(tuple(expected_files)):
        failures.append(f"PATH_SAFETY:{failure}")
    for name in JSONL_OUTPUTS:
        path = GENERATED_DIR / name
        manifest = GENERATED_DIR / manifest_name(name)
        if path.is_file() and manifest.is_file():
            rows = read_jsonl(path)
            payload = read_json(manifest)
            if payload.get("row_count") != len(rows):
                failures.append(f"MANIFEST_ROW_COUNT_MISMATCH:{name}")
    if failures:
        return failures

    rows = _row_files()
    reports = _report_files()
    run = reports["run_receipt.report.json"]
    art_reg = reports["art_reg.json"]

    registry_names = {entry["artifact_filename"] for entry in art_reg.get("entries", [])}
    if registry_names != expected_files:
        failures.append("ARTIFACT_REGISTRY_DOES_NOT_COVER_ALL_GENERATED_FILES")
    artifact_io_paths = {Path(row["file_path"]).name for row in rows["artifact_io.jsonl"]}
    file_route_paths = {Path(row["file_path"]).name for row in rows["file_route.jsonl"]}
    if artifact_io_paths != expected_files:
        failures.append("ARTIFACT_IO_DOES_NOT_COVER_ALL_FILES")
    if file_route_paths != expected_files:
        failures.append("FILE_ROUTE_DOES_NOT_COVER_ALL_FILES")

    for filename, file_rows in rows.items():
        if filename != "miss_opt.jsonl" and not file_rows:
            failures.append(f"REQUIRED_ROW_FILE_EMPTY:{filename}")
        for index, row in enumerate(file_rows, start=1):
            _check_common_row(filename, index, row, failures)
    for report_name in REPORT_OUTPUTS:
        _check_common_row(report_name, 1, reports[report_name], failures)

    failures.extend(_target_grid_seed_failures(rows))
    failures.extend(_surface_failures(rows, reports))

    hard_zero_fields = [
        "forbidden_authority_count",
        "paper_authority_count",
        "shadow_authority_count",
        "live_authority_count",
        "order_authority_count",
        "connector_write_count",
        "private_state_fetch_count",
        "cash_account_read_count",
        "trade_plan_simulation_count",
        "final_trade_ranking_count",
        "champion_selection_count",
        "profit_proof_count",
        "source_fact_acceptance_count",
        "proprietary_default_claim_count",
        "confidential_input_count",
        "formula_mutation_count",
        "formula_deletion_count",
        "qku_mutation_count",
        "qku_deletion_count",
        "global_formula_ban_count",
        "global_qku_ban_count",
        "qopt_execution_count",
        "quantum_backend_execution_count",
        "quantum_advantage_claim_count",
        "qtt_sha_authority_count",
        "qtt_generated_sha_file_count",
        "atomicrows_sha_ref_count",
        "fixed_trade_plan_count",
        "non_expiring_trade_plan_count",
        "stale_candidate_authority_count",
        "persistent_full_cartesian_grid_count",
        "metadata_only_proof_count",
        "orphan_artifact_count",
        "orphan_qku_count",
        "orphan_formula_count",
        "orphan_value_count",
        "path_safety_violation_count",
    ]
    for field in hard_zero_fields:
        if int(run.get(field, -1)) != 0:
            failures.append(f"RUN_REPORT_HARD_ZERO_NONZERO:{field}:{run.get(field)}")
    if run.get("dynamic_target_count") != len(rows["targets.jsonl"]):
        failures.append("RUN_TARGET_COUNT_MISMATCH")
    if run.get("order_variable_grid_count") != len(rows["var_grid.jsonl"]):
        failures.append("RUN_GRID_COUNT_MISMATCH")
    if run.get("trade_seed_count") != len(rows["trade_seed.jsonl"]):
        failures.append("RUN_SEED_COUNT_MISMATCH")

    generated_text = _all_generated_text()
    for state in FORBIDDEN_STATE_VALUES:
        if f'"{state}"' in generated_text:
            failures.append(f"FORBIDDEN_STATE_VALUE_FOUND:{state}")
    if "AtomicRows.bundle" + ".sha256" in generated_text:
        failures.append("ATOMICROWS_BUNDLE_SHA_REFERENCE_FOUND")
    if list(GENERATED_DIR.glob("*.sha256")):
        failures.append("QTT_GENERATED_SHA_FILE_FOUND")

    return failures


def _assert_deterministic() -> None:
    from .runner import run_layer

    before = _generated_file_texts()
    run_layer(offline=True, fixture="sample", max_targets=25, max_seeds=500, dump_temp=True)
    middle = _generated_file_texts()
    run_layer(offline=True, fixture="sample", max_targets=25, max_seeds=500, dump_temp=True)
    after = _generated_file_texts()
    if before != middle or middle != after:
        raise RP5FValidationError("RP5F generated outputs are not deterministic across repeated runs")


@lru_cache(maxsize=1)
def _validation_result() -> dict[str, Any]:
    failures = _failures()
    if failures:
        raise RP5FValidationError("; ".join(failures[:150]))
    _assert_deterministic()
    failures_after = _failures()
    if failures_after:
        raise RP5FValidationError("; ".join(failures_after[:150]))
    run_report = read_json(GENERATED_DIR / "run_receipt.report.json")
    return {
        "artifact_dir": str(GENERATED_DIR.relative_to(Path.cwd())).replace("\\", "/") if GENERATED_DIR.is_relative_to(Path.cwd()) else str(GENERATED_DIR),
        "dynamic_target_count": run_report["dynamic_target_count"],
        "order_variable_grid_count": run_report["order_variable_grid_count"],
        "trade_seed_count": run_report["trade_seed_count"],
        "validation": "PR168_RP5F_DYNAMIC_TARGETS_OK",
    }


def run_validation(_section: str | None = None) -> dict[str, Any]:
    return dict(_validation_result())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate PR168-RP5F dynamic target/grid artifacts.")
    parser.add_argument("section", nargs="?", default=None)
    args = parser.parse_args(argv)
    result = run_validation(args.section)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
