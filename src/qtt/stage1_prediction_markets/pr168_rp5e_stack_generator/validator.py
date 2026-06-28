"""Validator for PR168-RP5E generated stack-preview artifacts."""

from __future__ import annotations

import argparse
from functools import lru_cache
from pathlib import Path
from typing import Any

from .models import (
    BLOCKER_POLICY_REF,
    EXECUTION_AUTHORITY_REF,
    FORBIDDEN_STATE_VALUES,
    GENERATED_DIR,
    JSON_OUTPUTS,
    JSONL_OUTPUTS,
    REPORT_OUTPUTS,
    REPO_ROOT,
    ROLE_NAMES,
    all_artifact_filenames,
    manifest_name,
    read_json,
    read_jsonl,
)
from .path_safety import path_safety_failures


class RP5EValidationError(AssertionError):
    """Raised when RP5E generated surfaces violate their contract."""


def _generated_file_texts() -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(GENERATED_DIR.glob("*"), key=lambda p: p.name)
        if path.is_file()
    }


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
        "provenance_tier",
    )
    for key in required:
        if key not in row:
            failures.append(f"ROW_MISSING_COMMON_FIELD:{filename}:{index}:{key}")
    if row.get("execution_authority_ref") != EXECUTION_AUTHORITY_REF:
        failures.append(f"ROW_EXEC_AUTH_MISMATCH:{filename}:{index}")
    if row.get("blocker_policy_ref") != BLOCKER_POLICY_REF:
        failures.append(f"ROW_BLOCKER_REF_MISMATCH:{filename}:{index}")
    for key in (
        "metadata_is_proof_flag",
        "accepted_source_fact_flag",
        "paper_authority_flag",
        "shadow_authority_flag",
        "live_authority_flag",
        "qopt_execution_flag",
        "quantum_backend_execution_flag",
        "quantum_advantage_claim_flag",
        "proprietary_claim_flag",
        "qtt_sha_authority_flag",
        "atomicrows_sha_ref_flag",
    ):
        if row.get(key) is not False:
            failures.append(f"ROW_FORBIDDEN_FLAG_TRUE:{filename}:{index}:{key}")
    if not row.get("upstream_refs"):
        failures.append(f"ROW_MISSING_UPSTREAM:{filename}:{index}")
    if not row.get("downstream_refs"):
        failures.append(f"ROW_MISSING_DOWNSTREAM:{filename}:{index}")
    if not row.get("owner_agent"):
        failures.append(f"ROW_MISSING_OWNER:{filename}:{index}")
    if not row.get("consumer_agents"):
        failures.append(f"ROW_MISSING_CONSUMERS:{filename}:{index}")
    if not row.get("validation_refs"):
        failures.append(f"ROW_MISSING_VALIDATION:{filename}:{index}")


def _failures() -> list[str]:
    failures: list[str] = []
    if not GENERATED_DIR.is_dir():
        return ["MISSING_RP5E_GENERATED_DIR"]
    expected_files = set(all_artifact_filenames())
    actual_files = {path.name for path in GENERATED_DIR.iterdir() if path.is_file()}
    for name in sorted(expected_files - actual_files):
        failures.append(f"MISSING_GENERATED_FILE:{name}")
    for failure in path_safety_failures(expected_files):
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
        if filename not in {"miss_opt.jsonl"} and not file_rows:
            failures.append(f"REQUIRED_ROW_FILE_EMPTY:{filename}")
        for index, row in enumerate(file_rows, start=1):
            _check_common_row(filename, index, row, failures)

    authority = reports["exec_auth.report.json"]
    if authority.get("execution_authority_ref") != EXECUTION_AUTHORITY_REF:
        failures.append("EXEC_AUTH_REF_MISMATCH")
    for key, value in authority.items():
        if key.endswith("_authorized") and key not in {"stack_preview_authorized", "feature_generation_authorized", "downstream_handoff_authorized"} and value is not False:
            failures.append(f"FORBIDDEN_AUTHORIZED_TRUE:{key}")
    if authority.get("self_audit_v4_boundary", {}).get("shadow_mode", "").lower().find("not paper") < 0:
        failures.append("SELF_AUDIT_SHADOW_BOUNDARY_MISSING")

    mode_states = {row["runtime_state"]: row for row in rows["mode_boundary.jsonl"]}
    required_modes = {
        "PAPER_MODE",
        "LIVE_DRYRUN_SUBMIT_DISABLED",
        "SHADOW_LIVE_CONCURRENT_COMPARISON",
        "LIMITED_LIVE_CANARY",
    }
    if required_modes - set(mode_states):
        failures.append(f"MODE_BOUNDARY_MISSING:{sorted(required_modes - set(mode_states))}")
    paper = mode_states.get("PAPER_MODE", {})
    if paper.get("simulated_orders") is not True or paper.get("real_exchange_order_state") is not False:
        failures.append("PAPER_MODE_BOUNDARY_BAD")
    live_dry = mode_states.get("LIVE_DRYRUN_SUBMIT_DISABLED", {})
    if live_dry.get("submit_disabled") is not True or live_dry.get("real_order_submission_allowed") is not False:
        failures.append("LIVE_DRYRUN_BOUNDARY_BAD")
    shadow = mode_states.get("SHADOW_LIVE_CONCURRENT_COMPARISON", {})
    if (
        shadow.get("requires_live_execution_surface_flag") is not True
        or shadow.get("requires_live_receipts_flag") is not True
        or shadow.get("pre_live_gate_role_allowed_flag") is not False
        or shadow.get("post_live_validation_role_flag") is not True
        or shadow.get("required_before_limited_live_canary") is not False
        or shadow.get("order_authority_source") != "UNDERLYING_APPROVED_CANARY_OR_LIVE_SURFACE_ONLY"
    ):
        failures.append("SHADOW_BOUNDARY_BAD")
    canary = mode_states.get("LIMITED_LIVE_CANARY", {})
    if canary.get("enabled_in_rp5e_flag") is not False or canary.get("requires_owner_approval_flag") is not True:
        failures.append("LIMITED_CANARY_BOUNDARY_BAD")
    for row in rows["mode_boundary.jsonl"]:
        for key in (
            "order_authority_allowed_in_rp5e_flag",
            "connector_write_allowed_in_rp5e_flag",
            "private_state_fetch_allowed_in_rp5e_flag",
            "runtime_cash_receipt_allowed_in_rp5e_flag",
            "may_replace_replay_or_paper_flag",
        ):
            if row.get(key) is not False:
                failures.append(f"MODE_FORBIDDEN_FLAG_TRUE:{row.get('runtime_state')}:{key}")

    role_names = {row["role_name"] for row in rows["roles.jsonl"]}
    if role_names != set(ROLE_NAMES):
        failures.append("ROLE_ONTOLOGY_INCOMPLETE")
    if any(row.get("full_cartesian_generation_flag") for row in rows["search_trace.jsonl"]):
        failures.append("FULL_CARTESIAN_GENERATION_FLAG_TRUE")
    if any(row.get("persistent_family_grid_flag") for row in rows["cand_fam.jsonl"]):
        failures.append("PERSISTENT_FAMILY_GRID_FLAG_TRUE")

    topk = rows["topk.jsonl"]
    if not topk:
        failures.append("TOPK_EMPTY")
    if any(row.get("retain_or_discard") != "RETAIN" for row in topk):
        failures.append("TOPK_NON_RETAIN_ROW")
    for row in rows["tmp_previews.jsonl"]:
        if row.get("final_trade_rank_flag") is not False or row.get("champion_selected_flag") is not False:
            failures.append(f"PREVIEW_PROMOTION_FLAG_TRUE:{row.get('stack_preview_id')}")
        for key in ("paper_authority_flag", "shadow_authority_flag", "live_authority_flag"):
            if row.get(key) is not False:
                failures.append(f"PREVIEW_AUTHORITY_FLAG_TRUE:{key}:{row.get('stack_preview_id')}")

    included_ids = {identity for row in topk for identity in row.get("identity_refs", [])}
    guard_ids = {row["identity_ref"] for row in rows["qku_guard.jsonl"]}
    if not included_ids <= guard_ids:
        failures.append("TOPK_SELECTED_IDENTITY_WITHOUT_QKU_GUARD")
    for row in rows["qku_guard.jsonl"]:
        if row["included_in_stack_flag"] and row["computability_class"] not in {"COMPUTABLE_READY", "COMPUTABLE_AFTER_ADAPTER", "REPAIR_NEEDED", "STRUCTURAL_READY_NOT_EXECUTABLE"}:
            failures.append(f"BAD_QKU_GUARD_CLASS:{row['identity_ref']}")
        if row.get("metadata_only_flag") is not False:
            failures.append(f"QKU_GUARD_METADATA_ONLY:{row['identity_ref']}")

    for row in rows["exec_prev.jsonl"]:
        if row.get("no_cash_pnl_computed_flag") is not True or row.get("net_expected_pnl_computed_flag") is not False:
            failures.append(f"EXEC_PREVIEW_PNL_BOUNDARY_BAD:{row.get('stack_preview_id')}")
    for row in rows["tca_ready.jsonl"]:
        for key in (
            "fee_model_presence",
            "spread_model_presence",
            "slippage_model_presence",
            "latency_model_presence",
            "market_impact_or_capacity_model_presence",
            "unit_conversion_readiness",
            "venue_tick_size_readiness",
            "min_order_size_readiness",
            "cashflow_semantics_readiness",
            "settlement_semantics_readiness",
        ):
            if key not in row:
                failures.append(f"TCA_COMPONENT_MISSING:{row.get('stack_preview_id')}:{key}")
    for row in rows["fdr_ctrl.jsonl"]:
        if row.get("false_discovery_control_method") != "BENJAMINI_HOCHBERG_READY":
            failures.append(f"FDR_METHOD_BAD:{row.get('fdr_control_id')}")
        if row.get("deflated_performance_claim_flag") is not False:
            failures.append(f"DEFLATED_PERFORMANCE_CLAIM:{row.get('fdr_control_id')}")
    for row in rows["capacity.jsonl"]:
        for key in ("depth_bucket", "spread_bucket", "liquidity_bucket", "volume_bucket", "time_to_close_bucket"):
            if key not in row:
                failures.append(f"CAPACITY_BUCKET_MISSING:{row.get('capacity_crowding_id')}:{key}")
    for row in rows["champ_prev.jsonl"]:
        if row.get("final_champion_selected_flag") is not False or row.get("champion_selection_authority") != "NONE_IN_RP5E":
            failures.append(f"CHAMPION_SELECTION_BAD:{row.get('champion_challenger_preview_id')}")
    for row in rows["regime_mem.jsonl"]:
        if row.get("global_ban_flag") is not False:
            failures.append(f"REGIME_MEMORY_GLOBAL_BAN:{row.get('regime_memory_hint_id')}")

    for filename in ("q_obj.jsonl", "q_coeffs.jsonl", "q_solver.jsonl"):
        for row in rows[filename]:
            for key in ("objective_terms", "linear_coefficients", "quadratic_coefficients", "variable_domains", "constraint_terms", "normalization_bounds", "coefficient_scale_min", "coefficient_scale_max", "variable_count", "constraint_count", "interpret_back_map_ref", "classical_fallback_ref"):
                if key not in row:
                    failures.append(f"QUANTUM_STRUCT_FIELD_MISSING:{filename}:{row.get('stack_preview_id')}:{key}")
            if row.get("qopt_execution_flag") is not False or row.get("quantum_backend_execution_flag") is not False or row.get("quantum_advantage_claim_flag") is not False:
                failures.append(f"QUANTUM_EXECUTION_FLAG_TRUE:{filename}:{row.get('stack_preview_id')}")
    for row in rows["classic.jsonl"]:
        if row.get("classical_fallback_required_flag") is not True:
            failures.append(f"CLASSICAL_FALLBACK_NOT_REQUIRED:{row.get('classical_fallback_id')}")

    if len(rows["triage52.jsonl"]) != int(run.get("schedulable_after_adapter_count", -1)):
        failures.append("TRIAGE52_COUNT_DOES_NOT_MATCH_BASELINE")
    for row in rows["unlock_pri.jsonl"]:
        if row.get("promotion_in_rp5e_flag") is not False:
            failures.append(f"UNLOCK_PROMOTION_TRUE:{row.get('unlock_candidate_id')}")
    if int(run.get("replay_paper_executable_now_promotion_count", -1)) != 0:
        failures.append("REPLAY_PAPER_EXECUTABLE_NOW_PROMOTION_NONZERO")

    for filename in ("research_rec.jsonl", "default_cand.jsonl", "policy_prov.jsonl"):
        for row in rows[filename]:
            for key in ("accepted_source_fact_flag", "live_authority_flag", "profit_proof_flag", "proprietary_claim_flag"):
                if row.get(key) is not False:
                    failures.append(f"CANDIDATE_POLICY_FORBIDDEN_FLAG:{filename}:{key}:{row.get('row_id')}")
    for row in rows["default_cand.jsonl"]:
        if row.get("clean_room_flag") is not True or row.get("nda_or_confidential_input_flag") is not False or row.get("improper_access_flag") is not False:
            failures.append(f"CLEAN_ROOM_DEFAULT_BAD:{row.get('candidate_default_id')}")
    for row in rows["params.jsonl"]:
        if not row.get("policy_provenance_ref"):
            failures.append(f"PARAM_WITHOUT_POLICY_PROVENANCE:{row.get('parameter_name')}")

    report_files = {"to_paper.report.json", "to_live_dry.report.json", "to_shadow.report.json"}
    for name in report_files:
        report = reports[name]
        if report.get("non_authority_handoff_flag") is not True:
            failures.append(f"HANDOFF_NOT_NON_AUTHORITY:{name}")
        for key in ("paper_authority_flag", "shadow_authority_flag", "live_authority_flag", "order_authority_flag", "connector_write_flag", "private_state_fetch_flag", "runtime_cash_receipt_flag"):
            if report.get(key) is not False:
                failures.append(f"HANDOFF_AUTHORITY_FLAG_TRUE:{name}:{key}")

    hard_zero_fields = [
        "forbidden_authority_count",
        "paper_authority_count",
        "shadow_authority_count",
        "live_authority_count",
        "order_authority_count",
        "connector_write_count",
        "private_state_fetch_count",
        "runtime_cash_receipt_count",
        "trade_plan_simulation_count",
        "final_trade_ranking_count",
        "champion_selection_count",
        "order_variable_optimization_count",
        "qopt_execution_count",
        "quantum_backend_execution_count",
        "quantum_advantage_claim_count",
        "source_fact_acceptance_count",
        "proprietary_default_claim_count",
        "confidential_input_count",
        "formula_mutation_count",
        "formula_deletion_count",
        "qku_mutation_count",
        "qku_deletion_count",
        "global_formula_ban_count",
        "global_qku_ban_count",
        "qtt_sha_authority_count",
        "qtt_generated_sha_file_count",
        "atomicrows_sha_ref_count",
        "persistent_full_cartesian_grid_count",
        "full_stack_universe_count",
        "metadata_only_proof_count",
        "orphan_artifact_count",
        "orphan_qku_count",
        "orphan_formula_count",
        "orphan_value_count",
        "path_safety_violation_count",
        "replay_paper_executable_now_promotion_count",
        "paper_executable_now_promotion_count",
        "shadow_executable_now_promotion_count",
        "live_executable_now_promotion_count",
    ]
    for field in hard_zero_fields:
        if int(run.get(field, -1)) != 0:
            failures.append(f"RUN_REPORT_HARD_ZERO_NONZERO:{field}:{run.get(field)}")

    generated_text = _all_generated_text()
    for state in FORBIDDEN_STATE_VALUES:
        if state in generated_text:
            failures.append(f"FORBIDDEN_STATE_VALUE_FOUND:{state}")
    if "AtomicRows.bundle" + ".sha256" in generated_text:
        failures.append("ATOMICROWS_BUNDLE_SHA_REFERENCE_FOUND")
    if list(GENERATED_DIR.glob("*.sha256")):
        failures.append("QTT_GENERATED_SHA_FILE_FOUND")

    return failures


def _assert_deterministic() -> None:
    from .runner import run_layer

    before = _generated_file_texts()
    run_layer(offline=True, fixture="sample", max_stacks=1000, dump_temp=True)
    middle = _generated_file_texts()
    run_layer(offline=True, fixture="sample", max_stacks=1000, dump_temp=True)
    after = _generated_file_texts()
    if before != middle or middle != after:
        raise RP5EValidationError("RP5E generated outputs are not deterministic across repeated runs")


@lru_cache(maxsize=1)
def _validation_result() -> dict[str, Any]:
    failures = _failures()
    if failures:
        raise RP5EValidationError("; ".join(failures[:100]))
    _assert_deterministic()
    failures_after = _failures()
    if failures_after:
        raise RP5EValidationError("; ".join(failures_after[:100]))
    run_report = read_json(GENERATED_DIR / "run_receipt.report.json")
    return {
        "artifact_dir": str(GENERATED_DIR.relative_to(REPO_ROOT)).replace("\\", "/"),
        "runtime_stack_preview_rows": run_report["runtime_stack_preview_rows"],
        "retained_topk_preview_rows": run_report["retained_topk_preview_rows"],
        "schedulable_after_adapter_count": run_report["schedulable_after_adapter_count"],
        "adapter_queue_row_count": run_report["adapter_queue_row_count"],
        "validation": "PR168_RP5E_STACK_GENERATOR_OK",
    }


def run_validation(_section: str | None = None) -> dict[str, Any]:
    return dict(_validation_result())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate PR168-RP5E stack generator artifacts.")
    parser.add_argument("section", nargs="?", default=None)
    args = parser.parse_args(argv)
    result = run_validation(args.section)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
