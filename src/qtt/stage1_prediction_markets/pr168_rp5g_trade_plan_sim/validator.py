"""Validator for PR168-RP5G replay/paper simulation artifacts."""

from __future__ import annotations

import argparse
from functools import lru_cache
import json
from pathlib import Path
from typing import Any

from .models import (
    BLOCKER_POLICY_REF,
    EXECUTION_AUTHORITY_REF,
    FALSE_FLAG_FIELDS,
    FORBIDDEN_STATE_VALUES,
    GENERATED_DIR,
    JSONL_OUTPUTS,
    JSON_OUTPUTS,
    MARKDOWN_OUTPUTS,
    PR_ID,
    REPORT_OUTPUTS,
    all_artifact_filenames,
    manifest_name,
    read_json,
    read_jsonl,
)
from .path_safety import path_safety_failures


class RP5GValidationError(AssertionError):
    """Raised when RP5G generated surfaces violate their contract."""


COMMON_FIELDS = (
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


def _generated_file_texts() -> dict[str, str]:
    return {path.name: path.read_text(encoding="utf-8") for path in sorted(GENERATED_DIR.glob("*"), key=lambda p: p.name) if path.is_file()}


def _row_files() -> dict[str, list[dict[str, Any]]]:
    return {name: read_jsonl(GENERATED_DIR / name) for name in JSONL_OUTPUTS}


def _report_files() -> dict[str, dict[str, Any]]:
    return {name: read_json(GENERATED_DIR / name) for name in (*JSON_OUTPUTS, *REPORT_OUTPUTS)}


def _all_generated_text() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in GENERATED_DIR.glob("*") if path.is_file())


def _check_common_row(filename: str, index: int, row: dict[str, Any], failures: list[str]) -> None:
    for key in COMMON_FIELDS:
        if row.get(key) in (None, "", []):
            failures.append(f"ROW_MISSING_COMMON_FIELD:{filename}:{index}:{key}")
    if row.get("source_pr") != PR_ID:
        failures.append(f"ROW_SOURCE_PR_BAD:{filename}:{index}:{row.get('source_pr')}")
    if row.get("execution_authority_ref") != EXECUTION_AUTHORITY_REF:
        failures.append(f"ROW_EXEC_AUTH_MISMATCH:{filename}:{index}")
    if row.get("blocker_policy_ref") != BLOCKER_POLICY_REF:
        failures.append(f"ROW_BLOCKER_REF_MISMATCH:{filename}:{index}")
    for key in FALSE_FLAG_FIELDS:
        if row.get(key) is not False:
            failures.append(f"ROW_FORBIDDEN_FLAG_TRUE:{filename}:{index}:{key}")


def _walk_values(payload: Any) -> list[Any]:
    if isinstance(payload, dict):
        out: list[Any] = []
        for value in payload.values():
            out.extend(_walk_values(value))
        return out
    if isinstance(payload, list):
        out = []
        for value in payload:
            out.extend(_walk_values(value))
        return out
    return [payload]


def _specific_failures(rows: dict[str, list[dict[str, Any]]], reports: dict[str, dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    if reports["missing_req.report.json"].get("fail_closed_flag") is not False:
        failures.append("MISSING_REQUIRED_INPUTS_PRESENT")
    for filename in ("owner_q1_edge.jsonl", "owner_q2_route.jsonl", "owner_q3_auto_path.jsonl"):
        if not rows[filename]:
            failures.append(f"OWNER_QUESTION_LEDGER_EMPTY:{filename}")
    candidates = rows["trade_candidate.jsonl"]
    if not candidates:
        failures.append("TRADE_CANDIDATES_EMPTY")
    candidate_ids = {row["trade_plan_candidate_id"] for row in candidates}
    for row in candidates:
        for key in ("trade_seed_id", "target_id", "grid_id", "snapshot_id", "asof_timestamp_utc", "freshness_policy_ref", "ttl_policy_ref", "stale_invalidation_ref", "pre_submit_revalidation_ref", "qku_refs", "formula_refs"):
            if row.get(key) in (None, "", []):
                failures.append(f"CANDIDATE_MISSING_FIELD:{row.get('trade_plan_candidate_id')}:{key}")
        if row.get("candidate_status") != "SIMULATION_CANDIDATE":
            failures.append(f"CANDIDATE_BAD_STATUS:{row.get('trade_plan_candidate_id')}")
    formula_candidate_ids = {row.get("candidate_id") for row in rows["formula_comp.jsonl"] if row.get("compute_status") == "COMPUTED"}
    qku_candidate_ids = {row.get("candidate_id") for row in rows["qku_comp.jsonl"] if row.get("compute_status") == "COMPUTED"}
    if not candidate_ids <= formula_candidate_ids:
        failures.append("MISSING_FORMULA_COMPUTE_RECEIPT_FOR_CANDIDATE")
    if not candidate_ids <= qku_candidate_ids:
        failures.append("MISSING_QKU_COMPUTE_RECEIPT_FOR_CANDIDATE")
    eval_candidate_ids = {row.get("candidate_id") for row in rows["var_eval.jsonl"] if row.get("accept_reject_status") == "ACCEPTED"}
    reject_candidate_ids = {row.get("candidate_id") for row in rows["var_reject.jsonl"] if str(row.get("accept_reject_status", "")).startswith("REJECTED")}
    if not candidate_ids <= eval_candidate_ids:
        failures.append("MISSING_VARIABLE_EVAL_RECEIPTS")
    if not candidate_ids <= reject_candidate_ids:
        failures.append("MISSING_VARIABLE_REJECT_RECEIPTS")
    for filename in ("exec_pnl.jsonl", "tca_decomp.jsonl", "fill_latency_cap.jsonl", "scenario_ladder.jsonl", "notrade_cmp.jsonl", "overfit_fdr.jsonl", "port_marg_util.jsonl", "edge_attr.jsonl", "obj_decomp.jsonl"):
        if not rows[filename]:
            failures.append(f"NUMERIC_EVIDENCE_EMPTY:{filename}")
    for row in rows["sim_result.jsonl"]:
        label = str(row.get("outcome_label", ""))
        if label.startswith("REAL_"):
            failures.append(f"REAL_LABEL_FORBIDDEN_IN_FIXTURE_RP5G:{row.get('row_id')}:{label}")
        if row.get("real_market_profit_proof_flag") is not False:
            failures.append(f"REAL_MARKET_PROFIT_PROOF_BAD:{row.get('row_id')}")
        if row.get("metadata_only_flag") is not False:
            failures.append(f"METADATA_ONLY_SIM_RESULT:{row.get('row_id')}")
    for row in rows["champ_chall_preview.jsonl"]:
        if row.get("champion_selection_authority") != "NONE_IN_RP5G":
            failures.append(f"CHAMP_AUTHORITY_BAD:{row.get('row_id')}")
        if row.get("final_champion_selected_flag") is not False:
            failures.append(f"FINAL_CHAMPION_SELECTED:{row.get('row_id')}")
    for row in rows["order_auto_path.jsonl"] + rows["live_shadow_handoff.jsonl"] + rows["auth_block.jsonl"] + rows["order_ready_prev.jsonl"]:
        for key in ("order_authority_created_flag", "paper_submit_authority_created_flag", "buy_sell_open_close_logic_created_flag", "connector_write_created_flag"):
            if row.get(key) is not False:
                failures.append(f"ORDER_AUTH_BOUNDARY_BAD:{row.get('row_id')}:{key}")
    for row in rows["qstruct_problem.jsonl"]:
        required = ("linear_coefficients", "quadratic_coefficients", "constraint_matrix_or_constraint_terms", "penalty_weight_numeric_values", "coefficient_scale_policy_ref", "interpret_back_map_ref", "classical_fallback_ref")
        for key in required:
            if row.get(key) in (None, "", [], {}):
                failures.append(f"QSTRUCT_MISSING:{row.get('row_id')}:{key}")
        for key in ("qopt_execution_flag", "quantum_backend_execution_flag", "quantum_advantage_claim_flag"):
            if row.get(key) is not False:
                failures.append(f"QSTRUCT_EXEC_FLAG_TRUE:{row.get('row_id')}:{key}")
    if not rows["q_quality.jsonl"] or not rows["q_penalty.jsonl"] or not rows["q_counterfactual.jsonl"]:
        failures.append("V3_QUANTUM_QUALITY_SURFACES_EMPTY")
    artifact_io_paths = {Path(row["file_path"]).name for row in rows["artifact_io.jsonl"] if row.get("file_path")}
    expected_files = set(all_artifact_filenames())
    if artifact_io_paths != expected_files:
        failures.append("ARTIFACT_IO_DOES_NOT_COVER_ALL_FILES")
    if len(rows["owner_q2_route.jsonl"]) < len(expected_files):
        failures.append("OWNER_Q2_ROUTE_DOES_NOT_COVER_FILES")
    if reports["no_orphan.report.json"].get("orphan_artifact_count") != 0 or reports["no_orphan.report.json"].get("orphan_value_count") != 0:
        failures.append("NO_ORPHAN_REPORT_NONZERO")
    run = reports["run_receipt.report.json"]
    hard_zero_fields = [key for key in run if key.endswith("_count") and any(token in key for token in ("authority", "orphan", "mutation", "ban", "backend", "advantage", "connector", "cash", "private", "metadata_only", "checksum"))]
    for field in hard_zero_fields:
        if int(run.get(field, 0)) != 0:
            failures.append(f"RUN_REPORT_HARD_ZERO_NONZERO:{field}:{run.get(field)}")
    if run.get("owner_q1_edge_rows_exist_and_validate") is not True:
        failures.append("RUN_OWNER_Q1_FLAG_BAD")
    if run.get("owner_q2_route_rows_exist_and_validate") is not True:
        failures.append("RUN_OWNER_Q2_FLAG_BAD")
    if run.get("owner_q3_auto_path_rows_exist_and_validate") is not True:
        failures.append("RUN_OWNER_Q3_FLAG_BAD")
    return failures


def _failures() -> list[str]:
    failures: list[str] = []
    if not GENERATED_DIR.is_dir():
        return ["MISSING_RP5G_GENERATED_DIR"]
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
            file_rows = read_jsonl(path)
            payload = read_json(manifest)
            if payload.get("row_count") != len(file_rows):
                failures.append(f"MANIFEST_ROW_COUNT_MISMATCH:{name}")
    if failures:
        return failures
    rows = _row_files()
    reports = _report_files()
    art_reg = reports["art_reg.json"]
    registry_names = {entry["artifact_filename"] for entry in art_reg.get("entries", [])}
    if registry_names != expected_files:
        failures.append("ARTIFACT_REGISTRY_DOES_NOT_COVER_ALL_GENERATED_FILES")
    for filename, file_rows in rows.items():
        if not file_rows:
            failures.append(f"REQUIRED_ROW_FILE_EMPTY:{filename}")
        for index, row in enumerate(file_rows, start=1):
            _check_common_row(filename, index, row, failures)
    for report_name in REPORT_OUTPUTS:
        _check_common_row(report_name, 1, reports[report_name], failures)
    failures.extend(_specific_failures(rows, reports))
    for value in _walk_values(json.loads(json.dumps({name: read_json(GENERATED_DIR / name) for name in JSON_OUTPUTS + REPORT_OUTPUTS}))):
        if isinstance(value, str) and value in FORBIDDEN_STATE_VALUES:
            failures.append(f"FORBIDDEN_STATE_VALUE_FOUND:{value}")
    generated_text = _all_generated_text()
    if "AtomicRows.bundle" + ".sha256" in generated_text:
        failures.append("ATOMICROWS_BUNDLE_SHA_REFERENCE_FOUND")
    if list(GENERATED_DIR.glob("*.sha256")):
        failures.append("QTT_GENERATED_SHA_FILE_FOUND")
    for state in FORBIDDEN_STATE_VALUES:
        if f'"{state}"' in generated_text:
            failures.append(f"FORBIDDEN_STATE_VALUE_FOUND:{state}")
    return failures


def _assert_deterministic() -> None:
    from .runner import run_layer

    before = _generated_file_texts()
    run_layer(offline=True, fixture="sample", max_candidates=10, timeout_ms=3600000)
    middle = _generated_file_texts()
    run_layer(offline=True, fixture="sample", max_candidates=10, timeout_ms=3600000)
    after = _generated_file_texts()
    if before != middle or middle != after:
        raise RP5GValidationError("RP5G generated outputs are not deterministic across repeated runs")


@lru_cache(maxsize=1)
def _validation_result() -> dict[str, Any]:
    failures = _failures()
    if failures:
        raise RP5GValidationError("; ".join(failures[:200]))
    _assert_deterministic()
    failures_after = _failures()
    if failures_after:
        raise RP5GValidationError("; ".join(failures_after[:200]))
    run_report = read_json(GENERATED_DIR / "run_receipt.report.json")
    return {
        "artifact_dir": str(GENERATED_DIR.relative_to(Path.cwd())).replace("\\", "/") if GENERATED_DIR.is_relative_to(Path.cwd()) else str(GENERATED_DIR),
        "trade_plan_candidate_count": run_report["trade_plan_candidate_count"],
        "simulation_result_count": run_report["simulation_result_count"],
        "validation": "PR168_RP5G_TRADE_PLAN_SIM_OK",
    }


def run_validation(_section: str | None = None) -> dict[str, Any]:
    return dict(_validation_result())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate PR168-RP5G replay/paper simulation artifacts.")
    parser.add_argument("--generated", default=str(GENERATED_DIR))
    parser.add_argument("--timeout-ms", type=int, default=3600000)
    parser.add_argument("section", nargs="?", default=None)
    args = parser.parse_args(argv)
    requested = Path(args.generated)
    if not requested.is_absolute():
        requested = Path.cwd() / requested
    if requested.resolve() != GENERATED_DIR.resolve():
        raise RP5GValidationError(f"RP5G generated directory must be {GENERATED_DIR}, got {requested}")
    result = run_validation(args.section)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

