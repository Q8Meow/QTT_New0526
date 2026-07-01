"""Validator for PR168-MEM1 condition-scoped memory artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .models import (
    AUTHORITY_BOUNDARY_REF,
    AUTHORITY_FALSE_FIELDS,
    FORBIDDEN_FILENAME_TOKENS,
    FORBIDDEN_MEM1_FILENAMES,
    GENERATED_DIR,
    JSONL_OUTPUTS,
    JSON_OUTPUTS,
    REPORT_OUTPUTS,
    PR_ID,
    all_artifact_filenames,
    read_json,
    read_jsonl,
)


class Mem1ValidationError(AssertionError):
    """Raised when MEM1 generated surfaces violate their contract."""


COMMON_FIELDS = (
    "schema_version",
    "row_id",
    "producer_pr",
    "producer_tool",
    "created_at_utc",
    "source_artifact_refs",
    "upstream_refs",
    "downstream_refs",
    "owner_role_target",
    "canonical_agent_name_if_resolved",
    "consumer_role_targets",
    "consumer_agents_if_resolved",
    "validation_refs",
    "authority_boundary_ref",
    "orphan_flag",
)


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


def _rows(generated_dir: Path) -> dict[str, list[dict[str, Any]]]:
    return {name: read_jsonl(generated_dir / name) for name in JSONL_OUTPUTS}


def _reports(generated_dir: Path) -> dict[str, dict[str, Any]]:
    return {name: read_json(generated_dir / name) for name in (*JSON_OUTPUTS, *REPORT_OUTPUTS)}


def _check_common(filename: str, index: int, row: dict[str, Any], failures: list[str]) -> None:
    for field in COMMON_FIELDS:
        if row.get(field) in (None, "", []):
            failures.append(f"ROW_MISSING_COMMON_FIELD:{filename}:{index}:{field}")
    if row.get("producer_pr") != PR_ID:
        failures.append(f"ROW_BAD_PR:{filename}:{index}")
    if row.get("authority_boundary_ref") != AUTHORITY_BOUNDARY_REF:
        failures.append(f"ROW_BAD_AUTHORITY_REF:{filename}:{index}")
    if row.get("memory_prior_only_flag") is not True:
        failures.append(f"ROW_NOT_MEMORY_PRIOR_ONLY:{filename}:{index}")
    if row.get("replay_paper_revalidation_required") is not True:
        failures.append(f"ROW_NO_REPLAY_PAPER_REVALIDATION:{filename}:{index}")
    if row.get("execution_router_required_before_real_orders_flag") is not True:
        failures.append(f"ROW_NO_EXEC_ROUTER_REQUIREMENT:{filename}:{index}")
    for field in AUTHORITY_FALSE_FIELDS:
        if row.get(field) is not False:
            failures.append(f"ROW_FORBIDDEN_AUTHORITY_TRUE:{filename}:{index}:{field}={row.get(field)!r}")


def _check_filenames(generated_dir: Path, failures: list[str]) -> None:
    actual = {path.name for path in generated_dir.iterdir() if path.is_file()}
    expected = set(all_artifact_filenames())
    for name in sorted(expected - actual):
        failures.append(f"MISSING_GENERATED_FILE:{name}")
    for name in sorted(actual & FORBIDDEN_MEM1_FILENAMES):
        failures.append(f"FORBIDDEN_MEM1_ARTIFACT_PRESENT:{name}")
    for path in generated_dir.iterdir():
        if not path.is_file():
            continue
        lower = path.name.lower()
        for token in FORBIDDEN_FILENAME_TOKENS:
            if token in lower:
                failures.append(f"FORBIDDEN_LIFECYCLE_TOKEN_IN_MEM1_FILENAME:{path.name}:{token}")
        if lower.endswith("_placeholder_suffix.jsonl"):
            failures.append(f"WEAK_PLACEHOLDER_SUFFIX_IN_MEM1_FILENAME:{path.name}")


def _check_specific(rows: dict[str, list[dict[str, Any]]], reports: dict[str, dict[str, Any]], generated_dir: Path, failures: list[str]) -> None:
    if reports["missing_req.report.json"].get("fail_closed_flag") is not False:
        failures.append("MISSING_REQUIRED_INPUTS_PRESENT")
    if not rows["winning_recipe.jsonl"]:
        failures.append("NO_WINNING_RECIPES")
    if not rows["failure_memory.jsonl"]:
        failures.append("NO_FAILURE_MEMORY")
    if not rows["notrade_context_memory.jsonl"]:
        failures.append("NO_NOTRADE_CONTEXT_MEMORY")
    if not rows["qmemory_registry.jsonl"]:
        failures.append("NO_QMEMORY_REGISTRY")
    if not rows["memory_query_contract.jsonl"]:
        failures.append("NO_MEMORY_QUERY_CONTRACT")

    required_methods = {
        "get_top_recipes_for_context",
        "get_recipe_prior",
        "record_replay_outcome",
        "record_paper_outcome",
        "record_live_canary_outcome",
        "mark_recipe_stale",
        "cooldown_recipe_for_context",
        "get_failure_memories_for_context",
        "get_quantum_structures_for_context",
    }
    methods = {row.get("method_name") for row in rows["memory_query_contract.jsonl"]}
    if not required_methods.issubset(methods):
        failures.append(f"MEMORY_QUERY_CONTRACT_MISSING_METHODS:{sorted(required_methods - methods)}")

    for recipe in rows["winning_recipe.jsonl"]:
        for field in ("recipe_id", "qku_refs", "formula_refs", "formula_stack_id", "source_trade_plan_candidate_id", "numeric_evidence_refs", "data_provenance_tier"):
            if recipe.get(field) in (None, "", []):
                failures.append(f"RECIPE_MISSING_FIELD:{recipe.get('row_id')}:{field}")
        if recipe.get("current_profit_proof_flag") is not False:
            failures.append(f"RECIPE_CURRENT_PROFIT_TRUE:{recipe.get('row_id')}")
        if recipe.get("memory_prior_only_flag") is not True:
            failures.append(f"RECIPE_NOT_PRIOR_ONLY:{recipe.get('row_id')}")
        if recipe.get("replay_paper_revalidation_required") is not True:
            failures.append(f"RECIPE_NO_REVALIDATION:{recipe.get('row_id')}")

    for failure in rows["failure_memory.jsonl"]:
        if failure.get("similar_context_only_flag") is not True:
            failures.append(f"FAILURE_NOT_CONTEXT_SCOPED:{failure.get('row_id')}")
        for field in ("global_formula_ban_flag", "global_qku_ban_flag", "formula_mutation_required_flag"):
            if failure.get(field) is not False:
                failures.append(f"FAILURE_FORBIDDEN_TRUE:{failure.get('row_id')}:{field}")

    for notrade in rows["notrade_context_memory.jsonl"] + rows["notrade_not_terminal.jsonl"]:
        if notrade.get("terminal_dead_end_flag") is not False:
            failures.append(f"NOTRADE_TERMINAL_TRUE:{notrade.get('row_id')}")
        for field in ("global_formula_ban_flag", "global_qku_ban_flag", "paper_or_live_authority_created_flag"):
            if notrade.get(field) is not False:
                failures.append(f"NOTRADE_FORBIDDEN_TRUE:{notrade.get('row_id')}:{field}")

    for score in rows["recipe_prior_score.jsonl"]:
        for field in (
            "shrinkage_adjusted_mean_net_pnl",
            "hierarchical_pool_key",
            "off_policy_evaluation_required_flag",
            "oos_lockbox_required_flag",
            "fdr_q_value_or_proxy",
            "one_big_win_concentration_penalty",
        ):
            if score.get(field) in (None, ""):
                failures.append(f"PRIOR_SCORE_MISSING_FIELD:{score.get('row_id')}:{field}")

    for sim in rows["context_similarity_score.jsonl"]:
        for field in (
            "venue_match_weight",
            "market_category_match_weight",
            "spread_depth_liquidity_similarity",
            "drift_penalty",
            "stale_memory_penalty",
            "capacity_mismatch_penalty",
            "provenance_penalty",
        ):
            if sim.get(field) in (None, ""):
                failures.append(f"SIMILARITY_MISSING_COMPONENT:{sim.get('row_id')}:{field}")

    for row in rows["cooldown_policy.jsonl"] + rows["cooldown_state.jsonl"] + rows["negative_context_cooldown.jsonl"]:
        if row.get("global_formula_ban_flag") is not False or row.get("global_qku_ban_flag") is not False:
            failures.append(f"COOLDOWN_GLOBAL_BAN:{row.get('row_id')}")
        if row.get("cooldown_scope_key") in (None, "") and row.get("cooldown_scope") in (None, ""):
            failures.append(f"COOLDOWN_MISSING_SCOPE:{row.get('row_id')}")

    for row in rows["qmemory_registry.jsonl"]:
        for field in ("qubo_ref", "bqm_ref", "cqm_ref", "quadratic_program_ref", "interpret_back_map_ref", "classical_fallback_result_ref"):
            if row.get(field) in (None, ""):
                failures.append(f"QMEMORY_MISSING_REF:{row.get('row_id')}:{field}")
        for field in ("backend_execution_created_flag", "quantum_advantage_claim_flag", "true_quantum_backend_ready_flag"):
            if row.get(field) is not False:
                failures.append(f"QMEMORY_FORBIDDEN_TRUE:{row.get('row_id')}:{field}")

    for filename in ("llm_memory_view_contract.jsonl", "llm_memory_critic_payload_contract.jsonl", "llm_agent_task_contract.jsonl"):
        for row in rows[filename]:
            for field in ("llm_runtime_created_flag", "llm_source_truth_authority_flag", "llm_order_authority_flag", "llm_risk_gate_override_flag"):
                if row.get(field) is not False:
                    failures.append(f"LLM_CONTRACT_AUTHORITY_TRUE:{filename}:{field}")
            if row.get("current_pr_consumer_runtime_enabled_flag") is not False:
                failures.append(f"LLM_CONTRACT_RUNTIME_ENABLED:{filename}")

    for row in rows["hotpath_memory_index.jsonl"]:
        if row.get("hot_path_not_allowed_use") != "skip current replay/paper validation or submit orders":
            failures.append(f"HOTPATH_BAD_FORBIDDEN_USE:{row.get('row_id')}")
        if row.get("paper_or_live_authority_created_flag") is not False:
            failures.append(f"HOTPATH_CREATED_EXECUTION_AUTHORITY:{row.get('row_id')}")

    for filename in ("research_rec.jsonl", "source_coverage.jsonl", "source_intake.jsonl", "source_value_cand.jsonl", "memory_default_cand.jsonl", "clean_room_default_cand.jsonl"):
        for row in rows[filename]:
            if row.get("candidate_only_flag") is not True:
                failures.append(f"SOURCE_NOT_CANDIDATE_ONLY:{filename}:{row.get('row_id')}")
            if row.get("accepted_source_fact_flag") is not False or row.get("connector_semantic_binding_flag") is not False:
                failures.append(f"SOURCE_CREATED_AUTHORITY:{filename}:{row.get('row_id')}")

    artifact_paths = {Path(row.get("file_path", "")).name for row in rows["artifact_io.jsonl"]}
    value_paths = {Path(row.get("artifact_or_value_ref", "")).name for row in rows["value_route.jsonl"]}
    expected_without_manifests = set(all_artifact_filenames(include_manifests=False))
    if artifact_paths != expected_without_manifests:
        failures.append("ARTIFACT_IO_DOES_NOT_COVER_ALL_FILES")
    if value_paths != expected_without_manifests:
        failures.append("VALUE_ROUTE_DOES_NOT_COVER_ALL_FILES")
    if reports["no_orphan.report.json"].get("no_orphan_pass_flag") is not True:
        failures.append("NO_ORPHAN_REPORT_FAIL")
    if reports["authority_boundary.report.json"].get("authority_boundary_pass_flag") is not True:
        failures.append("AUTHORITY_REPORT_FAIL")

    for value in _walk_values({"rows": rows, "reports": reports}):
        if isinstance(value, str) and "AtomicRows.bundle.sha256" in value:
            failures.append("ATOMICROWS_BUNDLE_SHA_REF_PRESENT")

    _check_filenames(generated_dir, failures)


def validate_mem1_artifacts(repo_root: str | Path, artifact_dir: str | Path | None = None) -> list[str]:
    root = Path(repo_root)
    generated_dir = Path(artifact_dir) if artifact_dir is not None else GENERATED_DIR
    if not generated_dir.is_absolute():
        generated_dir = root / generated_dir
    failures: list[str] = []
    if not generated_dir.is_dir():
        return [f"MISSING_MEM1_GENERATED_DIR:{generated_dir}"]
    rows = _rows(generated_dir)
    reports = _reports(generated_dir)
    for filename in JSONL_OUTPUTS:
        for index, row in enumerate(rows.get(filename, []), start=1):
            _check_common(filename, index, row, failures)
    _check_specific(rows, reports, generated_dir, failures)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--artifact-dir", default=str(GENERATED_DIR))
    parser.add_argument("--timeout-ms", type=int, default=3600000)
    args = parser.parse_args(argv)
    failures = validate_mem1_artifacts(args.repo_root, args.artifact_dir)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    print("PR168-MEM1 validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
