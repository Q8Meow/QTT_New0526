"""Validator for PR168-RP5D-R1 executable-now unlock overlays."""

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
    FORBIDDEN_TEXT_PARTS,
    GENERATED_DIR,
    JSON_OUTPUTS,
    JSONL_OUTPUTS,
    REPORT_OUTPUTS,
    REPO_ROOT,
    all_artifact_filenames,
    manifest_name,
    read_json,
    read_jsonl,
)
from .path_safety import path_safety_failures


class RP5DR1ValidationError(AssertionError):
    """Raised when RP5D-R1 generated overlays violate their contract."""


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
        "provenance_tier",
    )
    for key in required:
        if key not in row:
            failures.append(f"ROW_MISSING_COMMON_FIELD:{filename}:{index}:{key}")
    if row.get("source_pr") != "PR168-RP5D-R1":
        failures.append(f"ROW_SOURCE_PR_BAD:{filename}:{index}:{row.get('source_pr')}")
    if row.get("execution_authority_ref") != EXECUTION_AUTHORITY_REF:
        failures.append(f"ROW_EXEC_AUTH_MISMATCH:{filename}:{index}")
    if row.get("blocker_policy_ref") != BLOCKER_POLICY_REF:
        failures.append(f"ROW_BLOCKER_REF_MISMATCH:{filename}:{index}")
    for key in FALSE_FLAG_FIELDS:
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
        return ["MISSING_RP5D_R1_GENERATED_DIR"]
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
        if filename != "miss_opt.jsonl" and not file_rows:
            failures.append(f"REQUIRED_ROW_FILE_EMPTY:{filename}")
        for index, row in enumerate(file_rows, start=1):
            _check_common_row(filename, index, row, failures)

    for report_name in REPORT_OUTPUTS:
        report = reports[report_name]
        _check_common_row(report_name, 1, report, failures)

    missing_report = reports["missing_req.report.json"]
    if missing_report.get("fail_closed_flag") is not False or missing_report.get("missing_required_refs"):
        failures.append("MISSING_REQUIRED_INPUTS_PRESENT")

    authority = reports["exec_auth.report.json"]
    for key, value in authority.items():
        if key.endswith("_authorized") and key not in {"contract_completion_authorized", "fixture_smoke_authorized", "tier_overlay_authorized"} and value is not False:
            failures.append(f"FORBIDDEN_AUTHORIZED_TRUE:{key}")

    mode_values = {row["runtime_mode"]: row for row in rows["mode_bound.jsonl"]}
    required_modes = {"REPLAY_MODE", "PAPER_MODE", "LIVE_DRY_RUN", "SHADOW_MODE", "LIMITED_LIVE_CANARY", "LIVE_MODE"}
    if required_modes - set(mode_values):
        failures.append(f"MODE_BOUNDARY_MISSING:{sorted(required_modes - set(mode_values))}")
    for mode, row in mode_values.items():
        for key in ("order_authority_flag", "connector_write_flag", "private_state_fetch_flag", "cash_account_read_flag"):
            if row.get(key) is not False:
                failures.append(f"MODE_AUTHORITY_FLAG_TRUE:{mode}:{key}")
    if mode_values.get("SHADOW_MODE", {}).get("post_live_validation_only_flag") is not True:
        failures.append("SHADOW_POST_LIVE_BOUNDARY_BAD")
    if mode_values.get("LIVE_DRY_RUN", {}).get("submit_disabled_flag") is not True:
        failures.append("LIVE_DRY_RUN_SUBMIT_BOUNDARY_BAD")

    promote = rows["promote.jsonl"]
    promoted_ids = {row["unlock_candidate_id"] for row in promote}
    if not 5 <= len(promote) <= 15:
        failures.append(f"PROMOTION_COUNT_OUT_OF_RANGE:{len(promote)}")
    if int(run.get("rows_promoted", -1)) != len(promote):
        failures.append("RUN_PROMOTED_COUNT_MISMATCH")
    if int(run.get("new_replay_paper_executable_now_count", -1)) != int(run.get("prior_replay_paper_executable_now_rows", -1)) + len(promote):
        failures.append("RUN_NEW_COUNT_FORMULA_BAD")

    proof_by_candidate = {row["unlock_candidate_id"]: row for row in rows["exec_now_proof.jsonl"]}
    tier_by_candidate = {row["unlock_candidate_id"]: row for row in rows["proof_tier.jsonl"]}
    matrix_by_candidate = {row["unlock_candidate_id"]: row for row in rows["contract_matrix.jsonl"]}
    audit_by_candidate = {row["unlock_candidate_id"]: row for row in rows["promote_audit.jsonl"]}
    overlay_by_candidate = {row["unlock_candidate_id"]: row for row in rows["tier_overlay.jsonl"]}
    smoke_by_candidate = {row["unlock_candidate_id"]: row for row in rows["calc_smoke.jsonl"]}
    for candidate_id in promoted_ids:
        if candidate_id not in proof_by_candidate:
            failures.append(f"PROMOTED_WITHOUT_EXEC_NOW_PROOF:{candidate_id}")
        if tier_by_candidate.get(candidate_id, {}).get("executable_proof_provenance_tier") != "EXEC_NOW_PROOF_FIXTURE_ONLY":
            failures.append(f"PROMOTED_BAD_PROOF_TIER:{candidate_id}")
        if matrix_by_candidate.get(candidate_id, {}).get("all_required_contracts_complete_flag") is not True:
            failures.append(f"PROMOTED_MATRIX_INCOMPLETE:{candidate_id}")
        if audit_by_candidate.get(candidate_id, {}).get("promotion_approved_flag") is not True:
            failures.append(f"PROMOTED_AUDIT_NOT_APPROVED:{candidate_id}")
        if overlay_by_candidate.get(candidate_id, {}).get("upstream_mutation_flag") is not False:
            failures.append(f"PROMOTED_OVERLAY_MUTATION_FLAG_BAD:{candidate_id}")
        smoke = smoke_by_candidate.get(candidate_id, {})
        if smoke.get("deterministic_reproducible_flag") is not True or smoke.get("numeric_output_present_flag") is not True:
            failures.append(f"PROMOTED_SMOKE_BAD:{candidate_id}")
        if smoke.get("profit_proof_flag") is not False or smoke.get("real_market_evidence_flag") is not False:
            failures.append(f"PROMOTED_SMOKE_PROOF_FLAG_BAD:{candidate_id}")

    count = rows["count_integrity.jsonl"][0]
    if count.get("upstream_files_mutated_flag") is not False or count.get("fake_label_promotion_detected_flag") is not False:
        failures.append("COUNT_INTEGRITY_MUTATION_OR_FAKE_LABEL")
    if count.get("new_overlay_count") != int(count.get("prior_executable_now_count", -1)) + int(count.get("promoted_count", -1)):
        failures.append("COUNT_INTEGRITY_FORMULA_BAD")
    if count.get("target_met_flag") is not True:
        failures.append("COUNT_INTEGRITY_TARGET_NOT_MET")

    if len(rows["rp5e_unlock_in.jsonl"]) != 52:
        failures.append("RP5E_UNLOCK_INPUT_COUNT_NOT_52")
    if len(rows["edge_profit_map.jsonl"]) != 52:
        failures.append("EDGE_PROFIT_MAP_NOT_ONE_PER_UNLOCK_CANDIDATE")
    for row in rows["edge_profit_map.jsonl"]:
        if row.get("rp5d_r1_profit_proof_flag") is not False or row.get("rp5d_r1_order_authority_flag") is not False:
            failures.append(f"EDGE_PROFIT_FORBIDDEN_FLAG_TRUE:{row.get('unlock_candidate_id')}")

    nonpromoted = rows["nonpromote.jsonl"]
    if len(nonpromoted) + len(promote) != 52:
        failures.append("PROMOTE_NONPROMOTE_TOTAL_NOT_52")
    for row in nonpromoted:
        if not row.get("exact_blocker_codes"):
            failures.append(f"NONPROMOTE_WITHOUT_EXACT_BLOCKER:{row.get('unlock_candidate_id')}")
        if row.get("global_ban_flag") is not False:
            failures.append(f"NONPROMOTE_GLOBAL_BAN:{row.get('unlock_candidate_id')}")

    if not rows["source_req.jsonl"]:
        failures.append("SOURCE_REQ_EMPTY")
    if not rows["research_rec.jsonl"]:
        failures.append("RESEARCH_RECEIPTS_EMPTY")
    for row in rows["research_rec.jsonl"]:
        if row.get("candidate_only_flag") is not True:
            failures.append(f"RESEARCH_NOT_CANDIDATE_ONLY:{row.get('row_id')}")
        for key in ("accepted_source_fact_flag", "connector_semantic_binding_flag", "live_default_flag", "proprietary_claim_flag"):
            if row.get(key) is not False:
                failures.append(f"RESEARCH_FORBIDDEN_FLAG_TRUE:{row.get('row_id')}:{key}")

    if rows["promo_diverse.jsonl"][0].get("hard_blocker_flag") is not False:
        failures.append("PROMOTION_DIVERSITY_HARD_BLOCKER_TRUE")
    for filename in ("q_struct_carry.jsonl", "q_solver_carry.jsonl", "q_interp_carry.jsonl", "classic_exec.jsonl"):
        if not rows[filename]:
            failures.append(f"QUANTUM_CLASSICAL_CARRY_EMPTY:{filename}")
    for row in rows["q_struct_carry.jsonl"]:
        for key in ("objective_terms", "linear_coefficients", "quadratic_coefficients", "variable_domains", "constraints", "penalty_weights", "normalization_bounds", "interpret_back_map_ref", "classical_fallback"):
            if key not in row:
                failures.append(f"Q_STRUCT_FIELD_MISSING:{row.get('unlock_candidate_id')}:{key}")
        if row.get("qopt_execution_flag") is not False or row.get("quantum_backend_execution_flag") is not False or row.get("quantum_advantage_claim_flag") is not False:
            failures.append(f"Q_STRUCT_EXEC_FLAG_TRUE:{row.get('unlock_candidate_id')}")

    for report_name in ("to_paper.report.json", "to_live_dry.report.json", "to_shadow.report.json"):
        report = reports[report_name]
        if report.get("non_authority_handoff_flag") is not True:
            failures.append(f"HANDOFF_NOT_NON_AUTHORITY:{report_name}")
        for key in ("paper_authority_flag", "shadow_authority_flag", "live_authority_flag", "order_authority_flag", "connector_write_flag", "private_state_fetch_flag", "cash_account_read_flag"):
            if report.get(key) is not False:
                failures.append(f"HANDOFF_AUTHORITY_FLAG_TRUE:{report_name}:{key}")

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
        "order_variable_optimization_count",
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
        "full_stack_universe_count",
        "full_adapter_queue_completion_attempt_count",
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

    generated_text = _all_generated_text()
    for state in FORBIDDEN_STATE_VALUES:
        if f'"{state}"' in generated_text:
            failures.append(f"FORBIDDEN_STATE_VALUE_FOUND:{state}")
    for left, right in FORBIDDEN_TEXT_PARTS:
        token = f"{left}{right}"
        if token in generated_text:
            failures.append(f"FORBIDDEN_EXECUTION_CONTRACT_TERMINOLOGY_FOUND:{token}")
    if "AtomicRows.bundle" + ".sha256" in generated_text:
        failures.append("ATOMICROWS_BUNDLE_SHA_REFERENCE_FOUND")
    if list(GENERATED_DIR.glob("*.sha256")):
        failures.append("QTT_GENERATED_SHA_FILE_FOUND")

    return failures


def _assert_deterministic() -> None:
    from .runner import run_layer

    before = _generated_file_texts()
    run_layer(offline=True, fixture="sample", target_min=5, target_max=15)
    middle = _generated_file_texts()
    run_layer(offline=True, fixture="sample", target_min=5, target_max=15)
    after = _generated_file_texts()
    if before != middle or middle != after:
        raise RP5DR1ValidationError("RP5D-R1 generated outputs are not deterministic across repeated runs")


@lru_cache(maxsize=1)
def _validation_result() -> dict[str, Any]:
    failures = _failures()
    if failures:
        raise RP5DR1ValidationError("; ".join(failures[:120]))
    _assert_deterministic()
    failures_after = _failures()
    if failures_after:
        raise RP5DR1ValidationError("; ".join(failures_after[:120]))
    run_report = read_json(GENERATED_DIR / "run_receipt.report.json")
    return {
        "artifact_dir": str(GENERATED_DIR.relative_to(REPO_ROOT)).replace("\\", "/"),
        "rows_attempted": run_report["rows_attempted"],
        "rows_promoted": run_report["rows_promoted"],
        "new_replay_paper_executable_now_count": run_report["new_replay_paper_executable_now_count"],
        "validation": "PR168_RP5D_R1_EXEC_NOW_UNLOCK_OK",
    }


def run_validation(_section: str | None = None) -> dict[str, Any]:
    return dict(_validation_result())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate PR168-RP5D-R1 executable-now unlock overlays.")
    parser.add_argument("section", nargs="?", default=None)
    args = parser.parse_args(argv)
    result = run_validation(args.section)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
