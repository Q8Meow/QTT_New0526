"""Validator for PR168-RP5D generated executability artifacts."""

from __future__ import annotations

import argparse
from functools import lru_cache
from pathlib import Path
from typing import Any

from .models import (
    BLOCKER_CODES,
    BLOCKER_POLICY_REF,
    COMPUTABILITY_STATES,
    EXECUTABILITY_STATES,
    EXECUTION_AUTHORITY_REF,
    GENERATED_DIR,
    JSON_OUTPUTS,
    JSONL_OUTPUTS,
    OLD_LONG_ARTIFACT_NAMES,
    QUEUE_FILE_BY_BLOCKER,
    READINESS_FILES,
    REPORT_OUTPUTS,
    REPO_ROOT,
    RP5C_REQUIRED_FILES,
    VS1_REQUIRED_FILES,
    all_artifact_filenames,
    manifest_name,
    read_json,
    read_jsonl,
)
from .path_safety import path_safety_failures


class RP5DValidationError(AssertionError):
    """Raised when RP5D generated surfaces violate their contract."""


def _generated_file_texts() -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(GENERATED_DIR.glob("*"), key=lambda p: p.name)
        if path.is_file()
    }


def _restore_generated_file_texts(snapshot: dict[str, str]) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    for path in GENERATED_DIR.iterdir():
        if path.is_file() and path.name not in snapshot:
            path.unlink()
    for name, text in snapshot.items():
        (GENERATED_DIR / name).write_text(text, encoding="utf-8")


def _row_files() -> dict[str, list[dict[str, Any]]]:
    return {name: read_jsonl(GENERATED_DIR / name) for name in JSONL_OUTPUTS}


def _report_files() -> dict[str, dict[str, Any]]:
    return {name: read_json(GENERATED_DIR / name) for name in (*JSON_OUTPUTS, *REPORT_OUTPUTS)}


def _failures() -> list[str]:
    failures: list[str] = []
    if not GENERATED_DIR.is_dir():
        return ["MISSING_RP5D_GENERATED_DIR"]
    expected_files = set(all_artifact_filenames())
    actual_files = {path.name for path in GENERATED_DIR.iterdir() if path.is_file()}
    missing_files = sorted(expected_files - actual_files)
    extra_old = sorted(actual_files & set(OLD_LONG_ARTIFACT_NAMES))
    for name in missing_files:
        failures.append(f"MISSING_GENERATED_FILE:{name}")
    for name in extra_old:
        failures.append(f"OLD_LONG_ARTIFACT_GENERATED:{name}")
    for name in JSONL_OUTPUTS:
        manifest = GENERATED_DIR / manifest_name(name)
        path = GENERATED_DIR / name
        if path.is_file() and manifest.is_file():
            rows = read_jsonl(path)
            manifest_payload = read_json(manifest)
            if manifest_payload.get("row_count") != len(rows):
                failures.append(f"MANIFEST_ROW_COUNT_MISMATCH:{name}")
            if manifest_payload.get("execution_authority_ref") != EXECUTION_AUTHORITY_REF:
                failures.append(f"MANIFEST_AUTHORITY_REF_MISMATCH:{name}")
    if failures:
        return failures

    rows = _row_files()
    reports = _report_files()
    run_report = reports["rp5d_run_receipt.report.json"]

    for ref in RP5C_REQUIRED_FILES:
        if not (REPO_ROOT / ref).is_file():
            failures.append(f"MISSING_RP5C_REQUIRED:{ref}")
    for ref in VS1_REQUIRED_FILES:
        if not (REPO_ROOT / ref).is_file():
            failures.append(f"MISSING_VS1_REQUIRED:{ref}")
    reading_refs = {row["file_ref"] for row in rows["rp5d_reading_receipts.jsonl"]}
    if "docs/master_plan/generated/rp5c/agent_qku_access_policy_registry.jsonl" not in reading_refs:
        failures.append("CORRECT_AGENT_QKU_ACCESS_POLICY_PATH_NOT_READ")
    if "docs/master_plan/generated/rp5c/agent_access_policy_registry.jsonl" in reading_refs:
        failures.append("INCORRECT_AGENT_ACCESS_POLICY_PATH_REQUIRED")
    if not any(row["discovery_target"] == "PR165_D2_AGENT_DUTY_EVIDENCE" for row in rows["rp5d_crosswalk_discovery_receipts.jsonl"]):
        failures.append("PR165_D2_DISCOVERY_NOT_RECORDED")

    registry_entries = reports["rp5d_artifact_name_registry.json"].get("entries", [])
    registry_names = {row["artifact_filename"] for row in registry_entries}
    if registry_names != expected_files:
        failures.append("ARTIFACT_NAME_REGISTRY_DOES_NOT_COVER_ALL_FILES")
    if len(registry_entries) != run_report["artifact_name_registry_count"]:
        failures.append("ARTIFACT_NAME_REGISTRY_COUNT_MISMATCH")
    for failure in path_safety_failures(expected_files):
        failures.append(f"PATH_SAFETY:{failure}")
    for entry in registry_entries:
        if not entry.get("safe_filename_flag"):
            failures.append(f"UNSAFE_REGISTRY_ENTRY:{entry.get('artifact_filename')}")
        if not entry.get("abbreviation_explanation"):
            failures.append(f"ABBREVIATION_NOT_EXPLAINED:{entry.get('artifact_filename')}")

    authority = reports["rp5d_execution_authority.report.json"]
    if authority.get("execution_authority_ref") != EXECUTION_AUTHORITY_REF:
        failures.append("EXECUTION_AUTHORITY_REF_MISMATCH")
    for key, value in authority.items():
        if key.endswith("_authorized") and value is not False:
            failures.append(f"FORBIDDEN_AUTHORITY_TRUE:{key}")

    blocker_codes = {row["blocker_code"] for row in rows["rp5d_blocker_policy_registry.jsonl"]}
    if set(BLOCKER_CODES) - blocker_codes:
        failures.append(f"BLOCKER_CODES_MISSING:{sorted(set(BLOCKER_CODES) - blocker_codes)}")
    for row in rows["rp5d_blocker_policy_registry.jsonl"]:
        if row.get("productive_adapter_gate_flag") is not True:
            failures.append(f"NON_PRODUCTIVE_BLOCKER:{row.get('blocker_code')}")
        if row.get("global_ban_allowed_flag") is not False:
            failures.append(f"BLOCKER_GLOBAL_BAN_ALLOWED:{row.get('blocker_code')}")

    comp_states = {row["state_name"] for row in rows["rp5d_comp_state_registry.jsonl"]}
    exec_states = {row["executability_state"] for row in rows["rp5d_exec_state_registry.jsonl"]}
    if comp_states != set(COMPUTABILITY_STATES):
        failures.append("COMPUTABILITY_STATE_REGISTRY_INCOMPLETE")
    if exec_states != set(EXECUTABILITY_STATES):
        failures.append("EXEC_STATE_REGISTRY_INCOMPLETE")
    if not rows["rp5d_adapter_family_registry.jsonl"]:
        failures.append("ADAPTER_FAMILY_REGISTRY_EMPTY")
    for row in rows["rp5d_adapter_family_registry.jsonl"]:
        if not row.get("owner_agent_ref") or not row.get("consumer_agent_refs"):
            failures.append(f"ADAPTER_FAMILY_ROUTE_INCOMPLETE:{row.get('adapter_family_ref')}")
        if row.get("live_authority_created_flag") is not False:
            failures.append(f"ADAPTER_LIVE_AUTHORITY:{row.get('adapter_family_ref')}")

    rp5c_identities = read_jsonl(REPO_ROOT / "docs/master_plan/generated/rp5c/immutable_qku_formula_library.jsonl")
    stage1_seeds = read_jsonl(REPO_ROOT / "docs/master_plan/generated/rp5c/stage1_agent_computation_universe_seed.jsonl")
    rp5c_ids = {row["identity_row_id"] for row in rp5c_identities}
    stage1_ids = {row["identity_row_id"] for row in stage1_seeds}
    coverage_ids = {row["identity_ref"] for row in rows["rp5d_universal_coverage.jsonl"]}
    comp_ids = {row["identity_ref"] for row in rows["rp5d_comp_materialization.jsonl"]}
    bundle_ids = {row["identity_ref"] for row in rows["rp5d_contract_bundles.jsonl"]}
    tier_ids = {row["identity_ref"] for row in rows["rp5d_exec_tiers.jsonl"]}
    if coverage_ids != rp5c_ids:
        failures.append("UNIVERSAL_COVERAGE_DOES_NOT_MATCH_RP5C_IDENTITIES")
    if comp_ids != rp5c_ids:
        failures.append("COMPUTABILITY_DOES_NOT_MATCH_RP5C_IDENTITIES")
    if bundle_ids != rp5c_ids:
        failures.append("CONTRACT_BUNDLE_DOES_NOT_MATCH_RP5C_IDENTITIES")
    if tier_ids != stage1_ids:
        failures.append("STAGE1_TIER_DOES_NOT_MATCH_STAGE1_SEEDS")

    for row in rows["rp5d_comp_materialization.jsonl"]:
        state = row["computability_materialization_state"]
        if state in {"UNKNOWN", "TBD", "PLACEHOLDER"} or state not in comp_states:
            failures.append(f"BAD_COMPUTABILITY_STATE:{row['identity_ref']}:{state}")
        if row.get("metadata_only_flag") is not False or row.get("placeholder_flag") is not False:
            failures.append(f"METADATA_OR_PLACEHOLDER:{row['identity_ref']}")
        for code in row.get("missing_contract_codes", []):
            if code not in blocker_codes:
                failures.append(f"UNDEFINED_MISSING_CODE:{row['identity_ref']}:{code}")

    queue_by_code_identity = {
        (code, row["identity_ref"])
        for filename in QUEUE_FILE_BY_BLOCKER.values()
        for row in rows[filename]
        for code in row.get("missing_contract_codes", [])
    }
    for row in rows["rp5d_comp_materialization.jsonl"]:
        if row["identity_ref"] not in stage1_ids:
            continue
        for code in row.get("missing_contract_codes", []):
            if code in QUEUE_FILE_BY_BLOCKER and (code, row["identity_ref"]) not in queue_by_code_identity:
                failures.append(f"MISSING_QUEUE_FOR_CONTRACT:{row['identity_ref']}:{code}")
    for filename in QUEUE_FILE_BY_BLOCKER.values():
        for row in rows[filename]:
            if row.get("live_authority_created_flag") is not False:
                failures.append(f"QUEUE_LIVE_AUTHORITY:{filename}:{row.get('adapter_queue_ref')}")
            if row.get("source_fact_acceptance_created_flag") is not False:
                failures.append(f"QUEUE_SOURCE_FACT:{filename}:{row.get('adapter_queue_ref')}")
            if row.get("connector_binding_created_flag") is not False:
                failures.append(f"QUEUE_CONNECTOR_BINDING:{filename}:{row.get('adapter_queue_ref')}")
            if row.get("adapter_family_ref") not in {item["adapter_family_ref"] for item in rows["rp5d_adapter_family_registry.jsonl"]}:
                failures.append(f"QUEUE_UNKNOWN_ADAPTER:{filename}:{row.get('adapter_queue_ref')}")

    for row in rows["rp5d_exec_tiers.jsonl"]:
        if row["executability_state"] not in exec_states:
            failures.append(f"BAD_TIER_STATE:{row['tier_ref']}")
        if row["replay_paper_executable_now_flag"]:
            required_available = [
                row["input_contract_state"],
                row["unit_contract_state"],
                row["formula_to_pnl_state"],
                row["market_data_binding_state"],
                row["agent_route_state"],
            ]
            if any(state != "AVAILABLE" for state in required_available):
                failures.append(f"EXEC_NOW_MISSING_CORE_CONTRACT:{row['tier_ref']}")
        if row["schedulable_after_adapter_flag"] and not row.get("adapter_queue_refs"):
            failures.append(f"SCHEDULABLE_WITHOUT_QUEUE:{row['tier_ref']}")

    for row in rows["rp5d_rp5c_vs1_crosswalk.jsonl"]:
        if row["vs1_evidence_scope"] != "BOUNDED_FIXTURE_EVIDENCE_ONLY":
            failures.append(f"VS1_SCOPE_NOT_BOUNDED:{row['crosswalk_ref']}")
    for row in rows["rp5d_no_mutation_proof.jsonl"]:
        for key, value in row.items():
            if key.endswith("_flag") and key not in {"global_formula_ban_flag", "global_qku_ban_flag"} and value is True:
                failures.append(f"NO_MUTATION_FORBIDDEN_FLAG:{key}:{row['identity_ref']}")
        if row["global_formula_ban_flag"] or row["global_qku_ban_flag"]:
            failures.append(f"GLOBAL_BAN_FLAG:{row['identity_ref']}")

    for filename in READINESS_FILES.values():
        if not rows[filename]:
            failures.append(f"READINESS_LEDGER_EMPTY:{filename}")
        for row in rows[filename]:
            if row.get("no_live_authority_created_flag") is not True:
                failures.append(f"READINESS_LIVE_AUTHORITY:{filename}:{row.get('readiness_ref')}")
    for row in rows["rp5d_qobj_constraint_ledger.jsonl"]:
        if row["backend_execution_flag"] is not False or row["quantum_advantage_claim_flag"] is not False:
            failures.append(f"QUANTUM_FORBIDDEN_FLAG:{row['quantum_materialization_ref']}")
        if not row["classical_fallback_refs"]:
            failures.append(f"QUANTUM_NO_CLASSICAL_FALLBACK:{row['quantum_materialization_ref']}")
    for row in rows["rp5d_quantum_compat.jsonl"]:
        if row["backend_execution_flag"] is not False or row["quantum_advantage_claim_flag"] is not False:
            failures.append(f"QCOMPAT_FORBIDDEN_FLAG:{row['quantum_compatibility_ref']}")
        if not row["classical_fallback_refs"]:
            failures.append(f"QCOMPAT_NO_CLASSICAL_FALLBACK:{row['quantum_compatibility_ref']}")
    for row in rows["rp5d_optimizer_readiness.jsonl"]:
        if row["candidate_optimizer_family"] in {"QUBO", "BQM", "CQM", "DQM", "QuadraticProgram", "Ising", "QAOA_READY", "VQE_READY"} and row["classical_fallback_required_flag"] is not True:
            failures.append(f"OPTIMIZER_QUANTUM_WITHOUT_FALLBACK:{row['optimizer_readiness_ref']}")

    for row in rows["rp5d_agent_exec_resolver.jsonl"]:
        if row["agent_stage_universe_count"] >= len(rp5c_ids):
            failures.append(f"AGENT_RESOLVER_FULL_LIBRARY_COPY:{row['resolver_ref']}")
    for row in rows["rp5d_computable_universe.jsonl"]:
        if row["contains_canonical_formula_objects_flag"] or row["contains_canonical_qku_objects_flag"]:
            failures.append(f"COMPUTABLE_UNIVERSE_COPIES_CANONICAL_OBJECT:{row['computable_universe_ref']}")

    for filename in ("rp5d_external_candidates.jsonl", "rp5d_external_research.jsonl"):
        for row in rows[filename]:
            for key in (
                "accepted_source_fact_flag",
                "connector_semantic_binding_flag",
                "fixture_constant_binding_flag",
                "live_order_authority_flag",
                "runtime_dependency_flag",
                "external_code_cloned_flag",
                "external_code_executed_flag",
            ):
                if key in row and row[key] is not False:
                    failures.append(f"EXTERNAL_FORBIDDEN_FLAG:{filename}:{key}")

    for filename, file_rows in rows.items():
        for index, row in enumerate(file_rows, start=1):
            if row.get("execution_authority_ref") != EXECUTION_AUTHORITY_REF:
                failures.append(f"ROW_AUTHORITY_REF_MISMATCH:{filename}:{index}")
            if row.get("blocker_policy_ref") != BLOCKER_POLICY_REF:
                failures.append(f"ROW_BLOCKER_REF_MISMATCH:{filename}:{index}")
            if not row.get("producer_agent"):
                failures.append(f"ROW_MISSING_PRODUCER:{filename}:{index}")
            if not row.get("consumer_agent_refs"):
                failures.append(f"ROW_MISSING_CONSUMER:{filename}:{index}")
            if not row.get("upstream_artifact_refs") and filename not in {"rp5d_external_candidates.jsonl", "rp5d_external_research.jsonl"}:
                failures.append(f"ROW_MISSING_UPSTREAM:{filename}:{index}")
            if not row.get("downstream_artifact_refs"):
                failures.append(f"ROW_MISSING_DOWNSTREAM:{filename}:{index}")
            if not row.get("validation_refs"):
                failures.append(f"ROW_MISSING_VALIDATION:{filename}:{index}")
            for code in row.get("blocker_codes", []):
                if code not in blocker_codes:
                    failures.append(f"UNDEFINED_BLOCKER_CODE:{filename}:{index}:{code}")

    hard_zero_fields = [
        "long_filename_violation_count",
        "long_repo_relative_path_violation_count",
        "long_windows_absolute_path_violation_count",
        "case_collision_count",
        "unsafe_filename_count",
        "unregistered_abbreviation_count",
        "metadata_only_ready_count",
        "placeholder_state_count",
        "final_unknown_state_count",
        "orphan_artifact_count",
        "orphan_qku_count",
        "orphan_formula_count",
        "orphan_value_count",
        "undefined_blocker_code_count",
        "non_productive_blocker_count",
        "scattered_non_live_flag_count",
        "formula_mutation_count",
        "formula_deletion_count",
        "qku_deletion_count",
        "global_formula_ban_count",
        "global_qku_ban_count",
        "stack_generation_count",
        "trade_simulation_count",
        "ranking_count",
        "champion_selection_count",
        "order_variable_optimization_count",
        "paper_submit_count",
        "live_submit_count",
        "order_submit_count",
        "order_cancel_count",
        "order_replace_count",
        "order_close_count",
        "connector_runtime_count",
        "private_state_fetch_count",
        "cash_runtime_count",
        "venue_api_call_count",
        "source_fact_acceptance_count",
        "external_source_to_fact_promotion_count",
        "quantum_backend_execution_count",
        "quantum_advantage_claim_count",
        "qtt_sha_authority_count",
        "qtt_generated_sha_file_count",
        "atomicrows_bundle_sha_reference_count",
    ]
    for field in hard_zero_fields:
        if int(run_report.get(field, -1)) != 0:
            failures.append(f"RUN_REPORT_HARD_ZERO_NONZERO:{field}:{run_report.get(field)}")
    generated_text = "\n".join(path.read_text(encoding="utf-8") for path in GENERATED_DIR.glob("*") if path.is_file())
    if "AtomicRows.bundle" + ".sha256" in generated_text:
        failures.append("ATOMICROWS_BUNDLE_SHA_REFERENCE_FOUND")
    if list(GENERATED_DIR.glob("*.sha256")):
        failures.append("QTT_GENERATED_SHA_FILE_FOUND")
    return failures


def _assert_deterministic() -> None:
    from .runner import run_layer

    before = _generated_file_texts()
    try:
        run_layer(offline=True)
        middle = _generated_file_texts()
        run_layer(offline=True)
        after = _generated_file_texts()
    finally:
        _restore_generated_file_texts(before)
    if middle != after:
        raise RP5DValidationError("RP5D generated outputs are not deterministic across repeated runs")


@lru_cache(maxsize=1)
def _validation_result() -> dict[str, Any]:
    failures = _failures()
    if failures:
        raise RP5DValidationError("; ".join(failures[:80]))
    _assert_deterministic()
    failures_after = _failures()
    if failures_after:
        raise RP5DValidationError("; ".join(failures_after[:80]))
    run_report = read_json(GENERATED_DIR / "rp5d_run_receipt.report.json")
    return {
        "artifact_dir": str(GENERATED_DIR.relative_to(REPO_ROOT)).replace("\\", "/"),
        "rp5c_identity_count": run_report["rp5c_identity_count"],
        "stage1_seed_identity_count": run_report["stage1_seed_identity_count"],
        "adapter_queue_row_count": run_report["adapter_queue_row_count"],
        "replay_paper_executable_now_count": run_report["replay_paper_executable_now_count"],
        "validation": "PR168_RP5D_REPLAY_PAPER_EXECUTABILITY_OK",
    }


def run_validation(_section: str | None = None) -> dict[str, Any]:
    return dict(_validation_result())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate PR168-RP5D generated artifacts.")
    parser.add_argument("section", nargs="?", default=None)
    args = parser.parse_args(argv)
    result = run_validation(args.section)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
