"""Validator for PR168-RANK4 advisory ranking artifacts."""

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
    MARKDOWN_OUTPUTS,
    PR_ID,
    REPORT_OUTPUTS,
    all_artifact_filenames,
    manifest_name,
    read_json,
    read_jsonl,
)


class Rank4ValidationError(AssertionError):
    """Raised when RANK4 generated surfaces violate their contract."""


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
    "rank_owner3q_proof.jsonl",
    "owner_q1_rank_edge.jsonl",
    "owner_q2_rank_route.jsonl",
    "owner_q3_rank_auto_path.jsonl",
)


def _generated_file_texts(generated_dir: Path) -> dict[str, str]:
    return {path.name: path.read_text(encoding="utf-8") for path in sorted(generated_dir.glob("*"), key=lambda p: p.name) if path.is_file()}


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
    for key in FALSE_AUTHORITY_FIELDS:
        if row.get(key) is not False:
            failures.append(f"ROW_FORBIDDEN_FLAG_TRUE:{filename}:{index}:{key}={row.get(key)!r}")


def _check_specific(rows: dict[str, list[dict[str, Any]]], reports: dict[str, dict[str, Any]], generated_dir: Path, failures: list[str]) -> None:
    if reports["missing_req.report.json"].get("fail_closed_flag") is not False:
        failures.append("MISSING_REQUIRED_INPUTS_PRESENT")
    candidates = {row["candidate_id"] for row in rows["rank_feat.jsonl"] if row.get("candidate_id")}
    if not candidates:
        failures.append("NO_RANK4_FEATURE_CANDIDATES")
        return
    for filename in ("rank_score.jsonl", "rank_order.jsonl", "elig_gate.jsonl", "notrade_rank.jsonl", "pareto_frontier.jsonl", "dominance.jsonl"):
        ids = {row.get("candidate_id") for row in rows[filename] if row.get("candidate_id")}
        if not candidates <= ids:
            failures.append(f"CANDIDATE_COVERAGE_MISSING:{filename}:{sorted(candidates - ids)}")
    for row in rows["rank_feat.jsonl"]:
        refs = row.get("upstream_refs", []) + row.get("source_artifact_refs", [])
        if not any("pr168_rp5g" in str(ref) for ref in refs):
            failures.append(f"FEATURE_WITHOUT_RP5G_REF:{row.get('row_id')}")
        numeric_keys = ("net_expected_pnl_cash", "lower_confidence_bound_pnl_cash", "candidate_minus_no_trade_cash", "TCA_total_cash", "fill_probability")
        for key in numeric_keys:
            if row.get(key) in (None, ""):
                failures.append(f"FEATURE_MISSING_NUMERIC:{row.get('candidate_id')}:{key}")
    components_by_candidate: dict[str, int] = {}
    for row in rows["score_comp.jsonl"]:
        components_by_candidate[row["candidate_id"]] = components_by_candidate.get(row["candidate_id"], 0) + 1
    for cid in candidates:
        if components_by_candidate.get(cid, 0) < 10:
            failures.append(f"SCORE_COMPONENT_ATTRIBUTION_INCOMPLETE:{cid}")
    for row in rows["rank_score.jsonl"]:
        if row.get("metadata_only_rank_flag") is not False:
            failures.append(f"METADATA_ONLY_RANK:{row.get('row_id')}")
        if not row.get("numeric_evidence_refs"):
            failures.append(f"RANK_SCORE_WITHOUT_NUMERIC_REFS:{row.get('row_id')}")
    if not any(row.get("advisory_champion_preview_flag") for row in rows["champ_prev.jsonl"]):
        failures.append("NO_ADVISORY_CHAMPION_PREVIEW_ROW")
    for row in rows["champ_prev.jsonl"]:
        if row.get("final_champion_selected_flag") is not False:
            failures.append(f"FINAL_CHAMPION_SELECTED:{row.get('row_id')}")
        if row.get("champion_selection_authority") != "NONE_IN_RANK4":
            failures.append(f"CHAMPION_AUTHORITY_BAD:{row.get('row_id')}")
    for row in rows["notrade_rank.jsonl"]:
        if row.get("formula_global_ban_flag") is not False or row.get("qku_global_ban_flag") is not False:
            failures.append(f"NOTRADE_GLOBAL_BAN:{row.get('row_id')}")
    for filename in ("qopt_batch.jsonl", "qopt_frontier.jsonl", "qrank_feat.jsonl", "qrank_score.jsonl"):
        for row in rows[filename]:
            for key in ("qopt_execution_flag", "quantum_backend_execution_flag", "quantum_advantage_claim_flag"):
                if row.get(key) is not False:
                    failures.append(f"QOPT_AUTHORITY_FLAG_TRUE:{filename}:{row.get('row_id')}:{key}")
            for key in ("objective_coefficients_missing", "constraints_missing_when_claimed", "interpret_back_map_missing", "classical_fallback_missing", "penalty_weights_missing", "coefficient_scale_missing"):
                if row.get(key) is not False:
                    failures.append(f"QOPT_STRUCTURAL_MISSING:{filename}:{row.get('row_id')}:{key}")
    for filename in ("rank_memory_recipe_handoff.jsonl", "rank_recipe_prior_score.jsonl", "rank_memory_candidate.jsonl"):
        for row in rows[filename]:
            if row.get("memory_prior_only_flag") is not True:
                failures.append(f"MEMORY_PRIOR_FLAG_MISSING:{filename}:{row.get('row_id')}")
            if row.get("current_profit_proof_flag") is not False:
                failures.append(f"MEMORY_PROFIT_PROOF_BAD:{filename}:{row.get('row_id')}")
            if row.get("durable_MEM1_storage_created_flag") is not False:
                failures.append(f"MEM1_STORAGE_CREATED:{filename}:{row.get('row_id')}")
    for row in rows["rank_mem1_contract_hint.jsonl"]:
        if row.get("future_MEM1_contract_hint_only_flag") is not True:
            failures.append(f"MEM1_CONTRACT_NOT_HINT_ONLY:{row.get('row_id')}")
    for filename in ("rank_ext_cand_intake.jsonl", "rank_source_rights.jsonl", "source_value_cand.jsonl"):
        for row in rows[filename]:
            if row.get("accepted_source_fact_flag") is not False:
                failures.append(f"SOURCE_FACT_ACCEPTED:{filename}:{row.get('row_id')}")
            if row.get("replay_paper_verification_required") is not True:
                failures.append(f"SOURCE_REPLAY_VERIFICATION_MISSING:{filename}:{row.get('row_id')}")
    for row in rows["rank_model_risk.jsonl"]:
        if row.get("combined_model_risk_score") in (None, "") or row.get("uncertainty_reserve_cash") in (None, ""):
            failures.append(f"MODEL_RISK_INCOMPLETE:{row.get('row_id')}")
    for row in rows["rank_oos_lockbox_hint.jsonl"]:
        if row.get("statistical_metric_fabricated_flag") is not False:
            failures.append(f"OOS_FABRICATED_METRIC:{row.get('row_id')}")
    for filename in ("rank_bandit_alloc_hint.jsonl", "rank_ope_hint.jsonl"):
        for row in rows[filename]:
            if row.get("bandit_runtime_policy_created_flag") is not False and filename == "rank_bandit_alloc_hint.jsonl":
                failures.append(f"BANDIT_RUNTIME_POLICY_CREATED:{row.get('row_id')}")
            if row.get("order_authority_created_flag") is not False:
                failures.append(f"BANDIT_OPE_ORDER_AUTH:{filename}:{row.get('row_id')}")
    for row in rows["rank_reward_decomp.jsonl"]:
        if row.get("causal_attribution_claim_flag") is not False:
            failures.append(f"CAUSAL_ATTRIBUTION_CLAIM:{row.get('row_id')}")
    for row in rows["rank_constraint_tightness.jsonl"]:
        for key in ("constraint_name", "threshold_value", "observed_value", "margin_to_threshold", "pass_flag", "barely_passed_flag"):
            if key not in row:
                failures.append(f"CONSTRAINT_TIGHTNESS_FIELD_MISSING:{row.get('row_id')}:{key}")
    if not any(row.get("barely_passed_flag") is True for row in rows["rank_constraint_tightness.jsonl"]):
        failures.append("NO_BARELY_PASSED_CONSTRAINT_DISCLOSED")
    for row in rows["rank_auto_trading_path.jsonl"]:
        if row.get("paper_order_intent_created_by_RANK4") is not False:
            failures.append(f"AUTO_PATH_PAPER_AUTH:{row.get('row_id')}")
        if row.get("live_order_authority_created_by_RANK4") is not False:
            failures.append(f"AUTO_PATH_LIVE_AUTH:{row.get('row_id')}")
        if row.get("buy_sell_open_close_logic_created_by_RANK4") is not False:
            failures.append(f"AUTO_PATH_ORDER_LOGIC:{row.get('row_id')}")
    for row in rows["rank_shadow_route.jsonl"]:
        if row.get("shadow_execution_authority_created_flag") is not False:
            failures.append(f"SHADOW_EXEC_AUTH:{row.get('row_id')}")
    for filename in OWNER_QUESTION_ONLY_FILENAMES:
        if (generated_dir / filename).exists():
            failures.append(f"OWNER_QUESTION_ONLY_ARTIFACT_PRESENT:{filename}")
    artifact_io_paths = {Path(row["file_path"]).name for row in rows["artifact_io.jsonl"] if row.get("file_path")}
    expected_files = set(all_artifact_filenames())
    if artifact_io_paths != expected_files:
        failures.append("ARTIFACT_IO_DOES_NOT_COVER_ALL_FILES")
    user_route_paths = {Path(row["artifact_or_value_ref"]).name for row in rows["rank_user_conn_route.jsonl"] if row.get("artifact_or_value_ref")}
    if user_route_paths != expected_files:
        failures.append("USER_CONNECTOR_ROUTE_DOES_NOT_COVER_ALL_FILES")
    if reports["no_orphan.report.json"].get("orphan_artifact_count") != 0 or reports["no_orphan.report.json"].get("orphan_value_count") != 0:
        failures.append("NO_ORPHAN_REPORT_NONZERO")
    if reports["authority_boundary.report.json"].get("authority_boundary_pass_flag") is not True:
        failures.append("AUTHORITY_BOUNDARY_REPORT_FAIL")
    if reports["run_receipt.report.json"].get("owner_question_only_artifact_count") != 0:
        failures.append("RUN_OWNER_QUESTION_ONLY_COUNT_NONZERO")


def _failures(generated_dir: Path) -> list[str]:
    failures: list[str] = []
    if not generated_dir.is_dir():
        return ["MISSING_RANK4_GENERATED_DIR"]
    expected_files = set(all_artifact_filenames())
    actual_files = {path.name for path in generated_dir.iterdir() if path.is_file()}
    for name in sorted(expected_files - actual_files):
        failures.append(f"MISSING_GENERATED_FILE:{name}")
    unexpected_owner_files = sorted(set(OWNER_QUESTION_ONLY_FILENAMES) & actual_files)
    for name in unexpected_owner_files:
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
        raise Rank4ValidationError("RANK4 generated outputs are not deterministic across repeated runs")


@lru_cache(maxsize=8)
def _validation_result(generated_dir_key: str) -> dict[str, Any]:
    generated_dir = Path(generated_dir_key)
    failures = _failures(generated_dir)
    if failures:
        raise Rank4ValidationError("; ".join(failures[:200]))
    _assert_deterministic(generated_dir)
    failures_after = _failures(generated_dir)
    if failures_after:
        raise Rank4ValidationError("; ".join(failures_after[:200]))
    run_report = read_json(generated_dir / "run_receipt.report.json")
    return {
        "artifact_dir": str(generated_dir),
        "trade_plan_candidate_count": run_report["trade_plan_candidate_count"],
        "advisory_rank_row_count": run_report["advisory_rank_row_count"],
        "validation": "PR168_RANK4_ADVISORY_RANKING_OK",
    }


def run_validation(_section: str | None = None, generated_dir: Path | None = None) -> dict[str, Any]:
    requested = generated_dir or GENERATED_DIR
    if not requested.is_absolute():
        requested = Path.cwd() / requested
    return dict(_validation_result(str(requested.resolve())))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate PR168-RANK4 advisory ranking artifacts.")
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

