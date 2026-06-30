"""Validator for PR168-QOPT1 advisory batch optimization artifacts."""

from __future__ import annotations

import argparse
from functools import lru_cache
import json
from pathlib import Path
from typing import Any

from .models import (
    AUTHORITY_BOUNDARY_REF,
    BLOCKER_POLICY_REF,
    EXECUTION_AUTHORITY_REF,
    FALSE_AUTHORITY_FIELDS,
    FORBIDDEN_STATE_VALUES,
    GENERATED_DIR,
    JSONL_OUTPUTS,
    JSON_OUTPUTS,
    REPORT_OUTPUTS,
    PR_ID,
    all_artifact_filenames,
    manifest_name,
    read_json,
    read_jsonl,
)


class Qopt1ValidationError(AssertionError):
    """Raised when QOPT1 generated surfaces violate their contract."""


COMMON_FIELDS = (
    "schema_version",
    "row_id",
    "run_id",
    "producer_pr",
    "source_pr",
    "producer_tool",
    "created_at_utc",
    "source_artifact_refs",
    "upstream_refs",
    "downstream_refs",
    "owner_agent",
    "consumer_agents",
    "validation_refs",
    "authority_boundary_ref",
    "execution_authority_ref",
    "blocker_policy_ref",
    "connector_refs_or_future_connector_status",
    "provenance_tier",
    "orphan_flag",
)

OWNER_QUESTION_ONLY_FILENAMES = (
    "qopt_owner3q_proof.jsonl",
    "owner_q1_qopt_edge.jsonl",
    "owner_q2_qopt_route.jsonl",
    "owner_q3_qopt_auto_path.jsonl",
)


def _generated_file_texts(generated_dir: Path) -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(generated_dir.glob("*"), key=lambda p: p.name)
        if path.is_file()
    }


def _row_files(generated_dir: Path) -> dict[str, list[dict[str, Any]]]:
    return {name: read_jsonl(generated_dir / name) for name in JSONL_OUTPUTS}


def _report_files(generated_dir: Path) -> dict[str, dict[str, Any]]:
    return {name: read_json(generated_dir / name) for name in (*JSON_OUTPUTS, *REPORT_OUTPUTS)}


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


def _check_common_row(filename: str, index: int, row: dict[str, Any], failures: list[str]) -> None:
    for key in COMMON_FIELDS:
        if row.get(key) in (None, "", []):
            failures.append(f"ROW_MISSING_COMMON_FIELD:{filename}:{index}:{key}")
    if row.get("source_pr") != PR_ID or row.get("producer_pr") != PR_ID:
        failures.append(f"ROW_SOURCE_PR_BAD:{filename}:{index}:{row.get('source_pr')}:{row.get('producer_pr')}")
    if row.get("execution_authority_ref") != EXECUTION_AUTHORITY_REF:
        failures.append(f"ROW_EXEC_AUTH_MISMATCH:{filename}:{index}")
    if row.get("authority_boundary_ref") != AUTHORITY_BOUNDARY_REF:
        failures.append(f"ROW_AUTH_BOUNDARY_MISMATCH:{filename}:{index}")
    if row.get("blocker_policy_ref") != BLOCKER_POLICY_REF:
        failures.append(f"ROW_BLOCKER_REF_MISMATCH:{filename}:{index}")
    if row.get("advisory_only_flag") is not True:
        failures.append(f"ROW_NOT_ADVISORY_ONLY:{filename}:{index}")
    if row.get("optimized_batch_advisory_only_flag") is not True:
        failures.append(f"ROW_NOT_OPTIMIZED_BATCH_ADVISORY_ONLY:{filename}:{index}")
    for key in FALSE_AUTHORITY_FIELDS:
        if key == "optimized_batch_advisory_only_flag":
            continue
        if row.get(key) is not False:
            failures.append(f"ROW_FORBIDDEN_FLAG_TRUE:{filename}:{index}:{key}={row.get(key)!r}")


def _candidate_ids(rows: dict[str, list[dict[str, Any]]]) -> set[str]:
    return {
        str(row["candidate_id"])
        for row in rows["batch_universe.jsonl"]
        if row.get("candidate_id")
    }


def _check_specific(rows: dict[str, list[dict[str, Any]]], reports: dict[str, dict[str, Any]], generated_dir: Path, failures: list[str]) -> None:
    if reports["missing_req.report.json"].get("fail_closed_flag") is not False:
        failures.append("MISSING_REQUIRED_INPUTS_PRESENT")
    if reports["run_receipt.report.json"].get("RANK4_outputs_consumed") is not True:
        failures.append("RANK4_OUTPUTS_NOT_CONSUMED")
    if reports["run_receipt.report.json"].get("RP5G_refs_preserved") is not True:
        failures.append("RP5G_REFS_NOT_PRESERVED")

    candidates = _candidate_ids(rows)
    if not candidates:
        failures.append("NO_QOPT1_ACTIVE_SET_CANDIDATES")
        return

    for row in rows["batch_universe.jsonl"]:
        refs = row.get("upstream_refs", []) + row.get("source_artifact_refs", [])
        if row.get("candidate_id") and not any("pr168_rank4" in str(ref) for ref in refs):
            failures.append(f"CANDIDATE_WITHOUT_RANK4_REF:{row.get('row_id')}")
        if row.get("candidate_id") and not any("pr168_rp5g" in str(ref) for ref in refs):
            failures.append(f"CANDIDATE_WITHOUT_RP5G_REF:{row.get('row_id')}")
        for key in ("net_expected_pnl_cash", "lower_confidence_bound_pnl_cash", "candidate_minus_no_trade_cash", "TCA_total_cash", "fill_probability", "objective_value"):
            if row.get("candidate_id") and row.get(key) in (None, ""):
                failures.append(f"CANDIDATE_MISSING_NUMERIC:{row.get('candidate_id')}:{key}")

    for filename in ("obj_terms.jsonl", "obj_decomp.jsonl", "constraints.jsonl", "constraint_check.jsonl", "var_map.jsonl"):
        if not rows[filename]:
            failures.append(f"REQUIRED_OPTIMIZATION_ROWS_EMPTY:{filename}")

    if not any(row.get("batch_class") == "PRIMARY_ADVISORY" and row.get("constraint_pass_flag") is True for row in rows["batch_select.jsonl"]):
        failures.append("NO_PRIMARY_ADVISORY_FEASIBLE_BATCH")
    for row in rows["batch_select.jsonl"]:
        if row.get("paper_order_intent_created_flag") is not False or row.get("live_authority_created_flag") is not False:
            failures.append(f"BATCH_AUTHORITY_CREATED:{row.get('row_id')}")
        if row.get("batch_class") == "PRIMARY_ADVISORY" and not row.get("classical_solver_result_ref"):
            failures.append(f"PRIMARY_BATCH_WITHOUT_CLASSICAL_SOLVER:{row.get('row_id')}")
        if row.get("batch_class") == "PRIMARY_ADVISORY" and not row.get("interpret_back_map_ref"):
            failures.append(f"PRIMARY_BATCH_WITHOUT_INTERPRET_BACK:{row.get('row_id')}")

    notrade_rows = rows["notrade_reopt.jsonl"] + rows["notrade_not_terminal.jsonl"] + rows["notrade_batch.jsonl"]
    for row in notrade_rows:
        if row.get("terminal_dead_end_flag") is not False and "terminal_dead_end_flag" in row:
            failures.append(f"NOTRADE_TERMINAL_DEAD_END:{row.get('row_id')}")
        if row.get("formula_global_ban_flag") is not False and "formula_global_ban_flag" in row:
            failures.append(f"NOTRADE_FORMULA_GLOBAL_BAN:{row.get('row_id')}")
        if row.get("qku_global_ban_flag") is not False and "qku_global_ban_flag" in row:
            failures.append(f"NOTRADE_QKU_GLOBAL_BAN:{row.get('row_id')}")
    if not rows["var_tune_frontier.jsonl"] or not rows["next_target_rotate.jsonl"] or not rows["agent_work_queue.jsonl"]:
        failures.append("NOTRADE_NEXT_ACTION_LADDER_INCOMPLETE")

    pos_rows = rows["pos_edge_search.jsonl"]
    if not pos_rows or not any(row.get("positive_edge_found_flag") is True or row.get("closest_to_positive_batch_id_if_none") for row in pos_rows):
        failures.append("POSITIVE_EDGE_SEARCH_NO_RESULT")
    for filename in ("profit_gap_close.jsonl", "scenario_trade_frontier.jsonl", "latency_profit_frontier.jsonl", "cand_ablation.jsonl"):
        if not rows[filename]:
            failures.append(f"POSITIVE_EDGE_SUPPORT_ROWS_EMPTY:{filename}")

    for filename in ("greedy_baseline.jsonl", "beam_result.jsonl", "local_search_result.jsonl", "milp_result.jsonl", "classic_best.jsonl", "classic_compare.jsonl", "solver_cascade.jsonl", "solver_arb.jsonl"):
        if not rows[filename]:
            failures.append(f"CLASSICAL_SOLVER_ROWS_EMPTY:{filename}")
    if not any(row.get("optimality_claim_scope") in {"BOUNDED_GLOBAL", "HEURISTIC_LOCAL", "STRUCTURAL_ONLY"} for row in rows["classic_best.jsonl"]):
        failures.append("CLASSIC_BEST_SCOPE_MISSING")

    quantum_required = ("qproblem.jsonl", "qubo.jsonl", "bqm.jsonl", "cqm.jsonl", "quad_prog.jsonl", "ising_map.jsonl")
    for filename in quantum_required:
        for row in rows[filename]:
            for key in (
                "variable_domain_map",
                "linear_coefficients",
                "quadratic_coefficients",
                "constraint_terms",
                "penalty_weight_numeric_values",
                "coefficient_scale_policy_ref",
                "feasibility_check_receipt",
                "interpret_back_map_ref",
                "classical_fallback_solver_ref",
            ):
                if row.get(key) in (None, "", [], {}):
                    failures.append(f"QSTRUCT_MISSING_FIELD:{filename}:{row.get('row_id')}:{key}")
            if row.get("true_quantum_backend_execution_flag") is not False or row.get("quantum_advantage_claim_flag") is not False:
                failures.append(f"QSTRUCT_AUTHORITY_CREATED:{filename}:{row.get('row_id')}")
    for filename in ("qobj_coeff.jsonl", "qconstraints.jsonl", "qcoef_scale.jsonl", "qfeas_check.jsonl", "qinterp.jsonl", "qclassic_fb.jsonl", "qencoding_diag.jsonl", "qresource_est.jsonl", "qpenalty_audit.jsonl", "qbackend_hint.jsonl", "penalty_dom_audit.jsonl", "feas_energy_gap.jsonl", "class_dom_base.jsonl"):
        if not rows[filename]:
            failures.append(f"QUANTUM_DIAG_ROWS_EMPTY:{filename}")
    for row in rows["qubo_matrix.jsonl"]:
        if row.get("upper_triangle_canonical_flag") is not True:
            failures.append(f"QUBO_NOT_CANONICAL:{row.get('row_id')}")
        if row.get("symmetric_duplicate_edge_flag") is not False:
            failures.append(f"QUBO_DUPLICATE_EDGE:{row.get('row_id')}")
    if not rows["qubo_symmetry.jsonl"] or rows["qubo_symmetry.jsonl"][0].get("duplicate_edge_count") != 0:
        failures.append("QUBO_SYMMETRY_RECEIPT_BAD")

    for filename in ("vs2_handoff.jsonl", "mem1_handoff.jsonl", "paper_handoff.jsonl", "live_dry_handoff.jsonl", "shadow_handoff.jsonl"):
        for row in rows[filename]:
            if row.get("paper_order_intent_created_flag") is not False:
                failures.append(f"HANDOFF_PAPER_INTENT_CREATED:{filename}:{row.get('row_id')}")
            if row.get("live_authority_created_flag") is not False:
                failures.append(f"HANDOFF_LIVE_AUTH_CREATED:{filename}:{row.get('row_id')}")
            if row.get("durable_MEM1_storage_created_flag") is not False:
                failures.append(f"HANDOFF_MEM1_STORAGE_CREATED:{filename}:{row.get('row_id')}")
    for row in rows["mem1_handoff.jsonl"]:
        if row.get("future_MEM1_storage_required_flag") is not True:
            failures.append(f"MEM1_FUTURE_STORAGE_FLAG_MISSING:{row.get('row_id')}")

    for row in rows["research_rec.jsonl"] + rows["source_coverage.jsonl"] + rows["source_intake.jsonl"] + rows["source_value_cand.jsonl"] + rows["institutional_default_cand.jsonl"]:
        if row.get("candidate_only_flag") is not True:
            failures.append(f"RESEARCH_NOT_CANDIDATE_ONLY:{row.get('row_id')}")
        if row.get("accepted_source_fact_flag") is not False:
            failures.append(f"SOURCE_FACT_ACCEPTED:{row.get('row_id')}")
        if row.get("replay_paper_verification_required") is not True:
            failures.append(f"RESEARCH_REPLAY_PAPER_VERIFICATION_MISSING:{row.get('row_id')}")

    for filename in OWNER_QUESTION_ONLY_FILENAMES:
        if (generated_dir / filename).exists():
            failures.append(f"OWNER_QUESTION_ONLY_ARTIFACT_PRESENT:{filename}")

    expected_files = set(all_artifact_filenames())
    artifact_io_paths = {Path(row["file_path"]).name for row in rows["artifact_io.jsonl"] if row.get("file_path")}
    if artifact_io_paths != expected_files:
        failures.append("ARTIFACT_IO_DOES_NOT_COVER_ALL_FILES")
    value_paths = {Path(row["artifact_or_value_ref"]).name for row in rows["value_route.jsonl"] if row.get("artifact_or_value_ref")}
    if value_paths != expected_files:
        failures.append("VALUE_ROUTE_DOES_NOT_COVER_ALL_FILES")
    if reports["no_orphan.report.json"].get("orphan_artifact_count") != 0 or reports["no_orphan.report.json"].get("orphan_value_count") != 0:
        failures.append("NO_ORPHAN_REPORT_NONZERO")
    if reports["authority_boundary.report.json"].get("authority_boundary_pass_flag") is not True:
        failures.append("AUTHORITY_BOUNDARY_REPORT_FAIL")
    if reports["run_receipt.report.json"].get("owner_question_only_artifact_count") != 0:
        failures.append("OWNER_QUESTION_ONLY_COUNT_NONZERO")


def _failures(generated_dir: Path) -> list[str]:
    failures: list[str] = []
    if not generated_dir.is_dir():
        return ["MISSING_QOPT1_GENERATED_DIR"]
    expected_files = set(all_artifact_filenames())
    actual_files = {path.name for path in generated_dir.iterdir() if path.is_file()}
    for name in sorted(expected_files - actual_files):
        failures.append(f"MISSING_GENERATED_FILE:{name}")
    for name in sorted(set(OWNER_QUESTION_ONLY_FILENAMES) & actual_files):
        failures.append(f"OWNER_QUESTION_ONLY_ARTIFACT_PRESENT:{name}")
    for name in expected_files:
        if len(name) > 64:
            failures.append(f"FILENAME_TOO_LONG:{name}")
        if " " in name or any(ch in name for ch in '&;|`"'):
            failures.append(f"UNSAFE_FILENAME:{name}")
    if failures:
        return failures
    for name in JSONL_OUTPUTS:
        path = generated_dir / name
        manifest = generated_dir / manifest_name(name)
        if not path.is_file() or not manifest.is_file():
            failures.append(f"MISSING_JSONL_OR_MANIFEST:{name}")
            continue
        rows = read_jsonl(path)
        payload = read_json(manifest)
        if payload.get("row_count") != len(rows):
            failures.append(f"MANIFEST_ROW_COUNT_MISMATCH:{name}")
        if not rows:
            failures.append(f"REQUIRED_ROW_FILE_EMPTY:{name}")
    if failures:
        return failures

    rows = _row_files(generated_dir)
    reports = _report_files(generated_dir)
    art_reg = reports["art_reg.json"]
    registry_names = {entry["artifact_filename"] for entry in art_reg.get("entries", [])}
    if registry_names != expected_files:
        failures.append("ARTIFACT_REGISTRY_DOES_NOT_COVER_ALL_GENERATED_FILES")

    for filename, file_rows in rows.items():
        for index, row in enumerate(file_rows, start=1):
            _check_common_row(filename, index, row, failures)
    for filename in (*JSON_OUTPUTS, *REPORT_OUTPUTS):
        _check_common_row(filename, 1, reports[filename], failures)
    _check_specific(rows, reports, generated_dir, failures)

    generated_text = "\n".join(path.read_text(encoding="utf-8") for path in generated_dir.glob("*") if path.is_file())
    if "AtomicRows.bundle" + ".sha256" in generated_text:
        failures.append("ATOMICROWS_BUNDLE_SHA_REFERENCE_FOUND")
    if list(generated_dir.glob("*.sha256")):
        failures.append("QTT_GENERATED_SHA_FILE_FOUND")
    for value in _walk_values(json.loads(json.dumps({name: reports[name] for name in (*JSON_OUTPUTS, *REPORT_OUTPUTS)}))):
        if isinstance(value, str) and value in FORBIDDEN_STATE_VALUES:
            failures.append(f"FORBIDDEN_STATE_VALUE_FOUND:{value}")
    for filename, file_rows in rows.items():
        for row in file_rows:
            for value in _walk_values(row):
                if isinstance(value, str) and value in FORBIDDEN_STATE_VALUES:
                    failures.append(f"FORBIDDEN_STATE_VALUE_FOUND:{filename}:{row.get('row_id')}:{value}")
    return failures


def _assert_deterministic(generated_dir: Path) -> None:
    from .builder import run_layer

    before = _generated_file_texts(generated_dir)
    run_layer(out_dir=generated_dir)
    middle = _generated_file_texts(generated_dir)
    run_layer(out_dir=generated_dir)
    after = _generated_file_texts(generated_dir)
    if before != middle or middle != after:
        raise Qopt1ValidationError("QOPT1 generated outputs are not deterministic across repeated runs")


@lru_cache(maxsize=8)
def _validation_result(generated_dir_key: str) -> dict[str, Any]:
    generated_dir = Path(generated_dir_key)
    failures = _failures(generated_dir)
    if failures:
        raise Qopt1ValidationError("; ".join(failures[:200]))
    _assert_deterministic(generated_dir)
    failures_after = _failures(generated_dir)
    if failures_after:
        raise Qopt1ValidationError("; ".join(failures_after[:200]))
    run_report = read_json(generated_dir / "run_receipt.report.json")
    return {
        "artifact_dir": str(generated_dir),
        "candidate_count": run_report["candidate_count"],
        "primary_batch_id": run_report["primary_batch_id"],
        "validation": "PR168_QOPT1_BATCH_OPTIMIZATION_OK",
    }


def run_validation(_section: str | None = None, generated_dir: Path | None = None) -> dict[str, Any]:
    requested = generated_dir or GENERATED_DIR
    if not requested.is_absolute():
        requested = Path.cwd() / requested
    return dict(_validation_result(str(requested.resolve())))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate PR168-QOPT1 advisory batch optimization artifacts.")
    parser.add_argument("--repo-root", default=str(Path.cwd()))
    parser.add_argument("--artifact-dir", "--generated", dest="artifact_dir", default=str(GENERATED_DIR))
    parser.add_argument("--timeout-ms", type=int, default=3600000)
    parser.add_argument("section", nargs="?", default=None)
    args = parser.parse_args(argv)
    requested = Path(args.artifact_dir)
    if not requested.is_absolute():
        requested = Path(args.repo_root) / requested
    result = run_validation(args.section, requested)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
