#!/usr/bin/env python3
"""Validation rules for PR168-GFP2R generated artifacts."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_gfp2r_config import (
    AUTHORITY_FALSE_FLAGS,
    FORBIDDEN_OUTPUT_CLASSIFICATIONS,
    REQUIRED_REPORT_IDS,
    ROW_SHARDS,
    VALID_MAPPING_CLASSES,
    generated_ref,
    manifest_path,
    report_path,
)


def _load(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _records(report_id: str) -> Any:
    return _load(report_path(report_id)).get("records")


def _fail(condition: bool, code: str, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(f"{code}: {message}")


def _walk(value: Any, failures: list[str], path: str = "root") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in AUTHORITY_FALSE_FLAGS:
                _fail(item is False, "PR168_GFP2R_AUTHORITY_FLAG_TRUE", f"{path}.{key}={item}", failures)
            lowered = key.lower()
            if lowered in {
                "real_positive_allowed_flag",
                "real_negative_allowed_flag",
                "real_positive_negative_allowed_flag",
                "forced_positive_flag",
                "quantum_backend_execution_flag",
                "quantum_advantage_claim_flag",
            }:
                _fail(item is False, "PR168_GFP2R_FORBIDDEN_FLAG_TRUE", f"{path}.{key}={item}", failures)
            if lowered == "qtt_sha_or_atomicrows_hash_authority_flag":
                _fail(item is False, "PR168_GFP2R_HASH_AUTHORITY_TRUE", f"{path}.{key}={item}", failures)
            if key == "candidate_output_classification":
                _fail(item not in FORBIDDEN_OUTPUT_CLASSIFICATIONS, "PR168_GFP2R_FORBIDDEN_CLASSIFICATION", f"{path}.{key}={item}", failures)
            _walk(item, failures, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk(item, failures, f"{path}[{index}]")


def _validate_required_global_fields(report_id: str, payload: dict[str, Any], failures: list[str]) -> None:
    required = [
        "report_id",
        "report_version",
        "created_by_tool",
        "created_at_utc",
        "records",
        "upstream_input_refs",
        "DATA1_refs",
        "DATA1A_refs",
        "formula_refs",
        "formula_variant_refs_if_available",
        "row_shard_refs_if_any",
        "numeric_evidence_refs",
        "data_provenance_refs",
        "computed_from_refs",
        "owning_agent",
        "consumer_agents",
        "downstream_consumers",
        "downstream_pr_refs",
        "validator_refs",
        "test_refs",
        "no_orphan_status",
        "terminal_by_nature_flag",
        "authority_class",
        *AUTHORITY_FALSE_FLAGS.keys(),
    ]
    for key in required:
        _fail(key in payload, "PR168_GFP2R_GLOBAL_FIELD_MISSING", f"{report_id} missing {key}", failures)
    _fail(payload.get("report_id") == report_id, "PR168_GFP2R_REPORT_ID_MISMATCH", report_id, failures)
    _fail(payload.get("no_orphan_status") == "NO_ORPHAN_ROUTED", "PR168_GFP2R_ORPHAN_REPORT", report_id, failures)
    _fail(bool(payload.get("records")) or payload.get("terminal_by_nature_flag"), "PR168_GFP2R_EMPTY_REPORT_RECORDS", report_id, failures)


def _validate_shards(failures: list[str]) -> dict[str, list[dict[str, Any]]]:
    rows_by_key: dict[str, list[dict[str, Any]]] = {}
    for shard_name, path in ROW_SHARDS.items():
        manifest = manifest_path(path)
        _fail(path.exists(), "PR168_GFP2R_SHARD_MISSING", generated_ref(path), failures)
        _fail(manifest.exists(), "PR168_GFP2R_SHARD_MANIFEST_MISSING", generated_ref(manifest), failures)
        if not path.exists() or not manifest.exists():
            continue
        rows: list[dict[str, Any]] = []
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                failures.append(f"PR168_GFP2R_JSONL_PARSE:{shard_name}:{index}:{exc}")
                continue
            rows.append(row)
            for key in ("owning_agent", "consumer_agents", "downstream_pr_refs", "validator_refs", "test_refs", "no_orphan_status"):
                _fail(key in row, "PR168_GFP2R_ROW_ROUTE_FIELD_MISSING", f"{shard_name}:{index}:{key}", failures)
            _fail(row.get("no_orphan_status") == "NO_ORPHAN_ROUTED", "PR168_GFP2R_ROW_ORPHAN", f"{shard_name}:{index}", failures)
            _walk(row, failures, f"{shard_name}:{index}")
        payload = _load(manifest)
        _fail(payload.get("row_count") == len(rows), "PR168_GFP2R_SHARD_ROW_COUNT_MISMATCH", shard_name, failures)
        _walk(payload, failures, f"manifest:{shard_name}")
        rows_by_key[shard_name] = rows
    return rows_by_key


def _validate_final_summary(failures: list[str]) -> None:
    final = _records("PR168_GFP2R_FinalSummary")
    expected_zero = [
        "exact_qku_formula_candidate_compute_ready_count",
        "exact_repaired_qku_formula_candidate_compute_ready_count",
        "real_positive_count",
        "real_negative_count",
        "real_positive_negative_allowed_count",
        "historical_full_book_assumption_violation_count",
        "market_implied_probability_as_alpha_violation_count",
        "quantum_backend_execution_count",
        "quantum_advantage_claim_count",
        "no_orphan_violation_count",
    ]
    for key in expected_zero:
        _fail(final.get(key) == 0, "PR168_GFP2R_EXPECTED_ZERO_MISMATCH", f"{key}={final.get(key)}", failures)
    for key in (
        "data1a_consumed_flag",
        "live_authority_created_flag",
        "profit_evidence_created_flag",
        "source_truth_acceptance_created_flag",
        "qtt_sha_or_atomicrows_hash_authority_flag",
    ):
        if key == "data1a_consumed_flag":
            _fail(final.get(key) is True, "PR168_GFP2R_DATA1A_NOT_CONSUMED", str(final), failures)
        else:
            _fail(final.get(key) is False, "PR168_GFP2R_FORBIDDEN_FINAL_FLAG", f"{key}={final.get(key)}", failures)
    minimum_positive = [
        "provisional_data_consumer_compute_ready_count",
        "formula_variant_generated_count",
        "formula_variant_executed_count",
        "formula_variant_duplicate_suppressed_count",
        "formula_variant_unit_invalid_count",
        "formula_equivalence_cluster_count",
        "candidate_formula_execution_count",
        "provisional_formula_execution_count",
        "break_even_threshold_computed_count",
        "required_edge_threshold_computed_count",
        "rp2_candidate_handoff_count",
        "rank2_candidate_handoff_count",
        "negative_recovery_repair_route_count",
        "recovery_variant_generated_count",
        "execution_adjusted_seed_count",
        "tca_fill_latency_capacity_seed_count",
        "fdr_trial_family_seed_count",
        "portfolio_marginal_utility_seed_count",
        "regime_conditioned_seed_count",
        "quantum_structural_candidate_count",
        "quantum_formula_variant_coverage_count",
    ]
    for key in minimum_positive:
        _fail(int(final.get(key, 0) or 0) > 0, "PR168_GFP2R_EXPECTED_POSITIVE_COUNT", f"{key}={final.get(key)}", failures)


def _validate_specific_rows(rows_by_key: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    mapping_rows = rows_by_key.get("mapping_repair", [])
    variant_rows = rows_by_key.get("formula_variant", [])
    execution_rows = rows_by_key.get("formula_execution", [])
    provisional_rows = rows_by_key.get("provisional_compute", [])
    threshold_rows = rows_by_key.get("break_even_threshold", [])
    recovery_rows = rows_by_key.get("recovery_variant", [])
    rp2_rows = rows_by_key.get("rp2_handoff", [])
    rank2_rows = rows_by_key.get("rank2_handoff", [])
    quantum_rows = rows_by_key.get("quantum_candidate_stack", [])

    _fail(mapping_rows, "PR168_GFP2R_MAPPING_ROWS_EMPTY", "mapping rows required", failures)
    _fail(
        all(row.get("mapping_class") in VALID_MAPPING_CLASSES for row in mapping_rows + variant_rows),
        "PR168_GFP2R_INVALID_MAPPING_CLASS",
        "mapping/variant mapping_class must be registered",
        failures,
    )
    _fail(
        not any(row.get("exact_candidate_compute_eligible_flag") for row in variant_rows),
        "PR168_GFP2R_FAKE_EXACT_COMPUTE_ELIGIBLE",
        "DATA1A exact_QKU_formula_unblocked_count=0",
        failures,
    )
    _fail(
        all(row.get("trial_family_id") and row.get("parameter_family_id") for row in variant_rows),
        "PR168_GFP2R_VARIANT_TRIAL_FAMILY_MISSING",
        "variant rows need trial/parameter families",
        failures,
    )
    _fail(
        any(row.get("duplicate_suppressed_flag") for row in variant_rows),
        "PR168_GFP2R_NO_DUPLICATE_SUPPRESSED",
        "dedupe receipt required",
        failures,
    )
    _fail(
        any(row.get("formula_units_valid_flag") is False for row in variant_rows),
        "PR168_GFP2R_NO_UNIT_INVALID_RECEIPT",
        "unit invalid receipt required",
        failures,
    )
    _fail(
        all(row.get("compute_lane") != "EXACT_QKU_FORMULA" for row in execution_rows),
        "PR168_GFP2R_EXACT_EXECUTION_WITHOUT_DATA1A_PROOF",
        "exact lane must be empty",
        failures,
    )
    _fail(
        all(row.get("proof_authority_class") == "PROVISIONAL_DATA_CONSUMER_NON_PROOF" for row in provisional_rows),
        "PR168_GFP2R_PROVISIONAL_PROOF_AUTHORITY_BAD",
        "provisional rows are non-proof only",
        failures,
    )
    _fail(
        all(row.get("market_implied_probability_as_alpha_proof_flag") is False for row in threshold_rows),
        "PR168_GFP2R_MARKET_IMPLIED_ALPHA_VIOLATION",
        "market implied probability may not be alpha proof",
        failures,
    )
    _fail(
        all(row.get("forced_positive_flag") is False for row in recovery_rows),
        "PR168_GFP2R_RECOVERY_FORCED_POSITIVE",
        "recovery variants cannot force positives",
        failures,
    )
    _fail(
        all(row.get("real_positive_negative_allowed_flag") is False for row in rp2_rows),
        "PR168_GFP2R_RP2_REAL_AUTHORITY",
        "RP2 handoff remains candidate/provisional",
        failures,
    )
    _fail(
        all(row.get("candidate_only_flag") is True and row.get("champion_allowed_flag") is False and row.get("live_candidate_allowed_flag") is False for row in rank2_rows),
        "PR168_GFP2R_RANK2_AUTHORITY_BAD",
        "RANK2 handoff must be candidate-only and no champion/live",
        failures,
    )
    _fail(
        all(
            row.get("binary_variable_id")
            and row.get("linear_coefficient_refs")
            and row.get("quadratic_coefficient_refs")
            and row.get("constraint_refs")
            and row.get("classical_fallback_exists")
            and row.get("classical_comparator_exists")
            for row in quantum_rows
        ),
        "PR168_GFP2R_QUANTUM_STRUCTURE_INCOMPLETE",
        "quantum rows require variables, coefficients, constraints, fallback, comparator",
        failures,
    )
    _fail(
        all(row.get("quantum_backend_execution_flag") is False and row.get("quantum_advantage_claim_flag") is False for row in quantum_rows),
        "PR168_GFP2R_QUANTUM_AUTHORITY_CREATED",
        "no backend execution or advantage claim",
        failures,
    )


def _validate_no_forbidden_text(failures: list[str]) -> None:
    forbidden = [
        "AtomicRows.bundle.sha256",
        "REAL_POSITIVE\": true",
        "REAL_NEGATIVE\": true",
        "CHAMPION\": true",
        "LIVE_CANDIDATE\": true",
        "quantum_advantage_claim_flag\": true",
        "quantum_backend_execution_flag\": true",
        "live_authority_created_flag\": true",
        "profit_evidence_created_flag\": true",
        "source_truth_acceptance_created_flag\": true",
        "qtt_sha_or_atomicrows_hash_authority_flag\": true",
    ]
    paths = [*(report_path(report_id) for report_id in REQUIRED_REPORT_IDS), *ROW_SHARDS.values()]
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            _fail(token not in text, "PR168_GFP2R_FORBIDDEN_TEXT", f"{generated_ref(path)} contains {token}", failures)


def validate_generated_reports() -> list[str]:
    failures: list[str] = []
    for report_id in REQUIRED_REPORT_IDS:
        path = report_path(report_id)
        _fail(path.exists(), "PR168_GFP2R_REQUIRED_REPORT_MISSING", generated_ref(path), failures)
        if not path.exists():
            continue
        payload = _load(path)
        _validate_required_global_fields(report_id, payload, failures)
        _walk(payload, failures, report_id)
    rows_by_key = _validate_shards(failures)
    if not failures:
        _validate_final_summary(failures)
        _validate_specific_rows(rows_by_key, failures)
        _validate_no_forbidden_text(failures)
    return failures


def main() -> int:
    failures = validate_generated_reports()
    if failures:
        print("\n".join(failures))
        return 1
    print("PR168_GFP2R_VALIDATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
