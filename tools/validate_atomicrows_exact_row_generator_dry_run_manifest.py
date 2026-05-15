#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import json
import pathlib
import sys
from typing import Any, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import validate_atomicrows_exact_row_authority_classifier_bridge as bridge_gate  # noqa: E402
from tools import validate_atomicrows_exact_row_expansion_manifest as expansion_gate  # noqa: E402
from tools import validate_atomicrows_owner_approved_exact_15_family_count_distribution as c0_gate  # noqa: E402
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)


DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_exact_row_generator_dry_run_manifest.schema.json"
)
DEFAULT_CONFIG = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsExactRowGeneratorDryRunManifest.yaml"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsExactRowGeneratorDryRun.report.json"
)

REPORT_TYPE = "ATOMICROWS_EXACT_ROW_GENERATOR_DRY_RUN_REPORT"
REPORT_VERSION = "v1"
MANIFEST_TYPE = "ATOMICROWS_EXACT_ROW_GENERATOR_DRY_RUN_MANIFEST"
MANIFEST_VERSION = "v1"
REPAIR_PR = "REPAIR_PR_C_ATOMICROWS_EXACT_ROW_GENERATOR_DRY_RUN"
AUTHORITY_CLASS = "INTERNAL_QTT_ARCHITECTURE_DRY_RUN_ONLY_NOT_ROW_AUTHORITY"
VALIDATION_RESULT = "PASS_DRY_RUN_NO_ROWS_WRITTEN"
SUCCESS_MARKER = "QTT_ATOMICROWS_EXACT_ROW_GENERATOR_DRY_RUN_OK"
FAILURE_MARKER = "QTT_ATOMICROWS_EXACT_ROW_GENERATOR_DRY_RUN_FAILED"

TARGET_TOTAL_ROWS = 4183
FIRST_ROW_INDEX = 1
FINAL_ROW_INDEX = 4183
FAMILY_COUNT = 15
QUANTUM_FORWARD_TOTAL_ROWS = 1103
AGENT_GOVERNANCE_FAMILY_ID = "009_lifecycle_agent_binding"
AGENT_GOVERNANCE_FAMILY_ROWS = 270

AUTHORITY_CLASSIFIER_BRIDGE_PATH = bridge_gate.DEFAULT_CONFIG
AUTHORITY_CLASSIFIER_BRIDGE_REPORT_PATH = bridge_gate.DEFAULT_REPORT
EXPANSION_MANIFEST_PATH = expansion_gate.DEFAULT_CONFIG
EXPANSION_MANIFEST_REPORT_PATH = expansion_gate.DEFAULT_REPORT
OWNER_APPROVED_DISTRIBUTION_PATH = c0_gate.DEFAULT_CONFIG
OWNER_APPROVED_DISTRIBUTION_REPORT_PATH = c0_gate.DEFAULT_REPORT

FUTURE_EXACT_ROW_SOURCES_DIRECTORY = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "exact_row_sources"
)
FUTURE_EXACT_ROW_SOURCES_DIRECTORY_TEXT = "docs/master_plan/atomic_rows/exact_row_sources/"
FUTURE_BUNDLE_PATH = pathlib.Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
FUTURE_BUNDLE_SHA_PATH = pathlib.Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")

FAMILY_DISTRIBUTION: tuple[tuple[int, str, int], ...] = c0_gate.FAMILY_DISTRIBUTION
REQUIRED_FAMILY_IDS = tuple(slug for _, slug, _ in FAMILY_DISTRIBUTION)
QUANTUM_FORWARD_FAMILY_IDS = c0_gate.QUANTUM_FAMILY_SLUGS
QUANTUM_METADATA_CLASSES = {
    "012_quantum_advisory_optimization": "QUANTUM_ADVISORY_OPTIMIZATION_METADATA_ONLY",
    "013_quantum_qubo_ising_metadata": "QUBO_ISING_METADATA_ONLY",
    "014_quantum_qaoa_vqe_annealing_metadata": "QAOA_VQE_ANNEALING_METADATA_ONLY",
    "015_quantum_portfolio_hybrid_comparator": "QUANTUM_PORTFOLIO_HYBRID_COMPARATOR_METADATA_ONLY",
}
NON_QUANTUM_METADATA_CLASS = "NOT_QUANTUM_FORWARD_FAMILY"

DRY_RUN_BLOCKING_BASIS = (
    "DRY_RUN_ONLY_NOT_MATERIALIZED",
    "EXACT_ROW_SOURCE_FILE_NOT_CREATED",
    "BUNDLE_NOT_CREATED",
    "SHA_FREEZE_NOT_CREATED",
    "AGENT_ELIGIBILITY_MATRIX_PENDING",
    "SOURCE_FACT_ACCEPTANCE_PENDING_WHEN_APPLICABLE",
    "REPLAY_PAPER_VALIDATION_PENDING_WHEN_APPLICABLE",
    "QUANTUM_BACKEND_EVIDENCE_PENDING_WHEN_APPLICABLE",
)
NO_AUTHORITY_FALSE_FIELDS = (
    "exact_rows_created",
    "exact_row_source_directory_created",
    "bundle_created",
    "bundle_sha_created",
    "sha_computed",
    "freeze_authority_created",
    "final_readiness_created",
    "source_fact_acceptance_created",
    "connector_semantic_binding_created",
    "runtime_authority_created",
    "live_authority_created",
    "order_authority_created",
    "optimizer_execution_created",
    "replay_execution_created",
    "paper_execution_created",
    "quantum_backend_execution_created",
    "quantum_simulator_execution_created",
    "quantum_provider_execution_created",
    "profit_evidence_created",
    "latency_evidence_created",
    "execution_superiority_evidence_created",
    "quantum_advantage_evidence_created",
    "specific_agent_family_assignments_created",
    "specific_agent_row_assignments_created",
)
REPORT_FALSE_FIELDS = (
    "exact_rows_written",
    "exact_row_sources_directory_created",
    "bundle_written",
    "bundle_sha_written",
    "freeze_created",
    "final_readiness_created",
)
CHECK_TRUE_FIELDS = (
    "source_inputs_present",
    "source_inputs_consumed",
    "family_count_matches",
    "total_rows_match",
    "final_row_index_matches",
    "row_ranges_contiguous",
    "row_ranges_non_overlapping",
    "row_ranges_no_gaps",
    "family_order_matches_c0",
    "row_id_generation_deterministic",
    "authority_class_policy_present_for_all_future_rows",
    "source_pointer_policy_present_for_all_future_rows",
    "block_code_policy_present_for_all_future_rows",
    "agent_eligibility_policy_present_for_all_future_rows",
    "quantum_forward_metadata_policy_present_for_quantum_families",
    "no_exact_rows_written",
    "no_exact_row_sources_directory_created",
    "no_bundle_written",
    "no_bundle_sha_written",
    "no_freeze_created",
    "no_final_readiness_created",
    "no_specific_agent_assignments_created",
    "no_runtime_authority_created",
    "no_live_authority_created",
    "no_order_authority_created",
    "no_source_fact_acceptance_created",
    "no_connector_semantic_binding_created",
    "no_optimizer_execution_created",
    "no_quantum_backend_execution_created",
    "no_profit_evidence_created",
    "no_latency_evidence_created",
    "no_execution_superiority_evidence_created",
    "no_quantum_advantage_evidence_created",
    "no_venue_api_provider_facts_fabricated",
    "report_does_not_serialize_exact_source_rows",
)


@dataclass(frozen=True)
class FamilyRange:
    family_number: int
    family_id: str
    row_count: int
    start_row_index: int
    end_row_index: int


@dataclass(frozen=True)
class SourceInputs:
    bridge: dict[str, Any]
    bridge_report: dict[str, Any]
    expansion: dict[str, Any]
    expansion_report: dict[str, Any]
    distribution: dict[str, Any]
    distribution_report: dict[str, Any]


@dataclass(frozen=True)
class ForbiddenArtifactState:
    exact_row_sources_directory_created: bool
    bundle_written: bool
    bundle_sha_written: bool
    exact_row_files: tuple[str, ...]


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]
    report: dict[str, Any] | None


def _resolve(root: pathlib.Path, path: pathlib.Path) -> pathlib.Path:
    return path if path.is_absolute() else root / path


def _as_posix(path: str | pathlib.Path) -> str:
    return pathlib.Path(path).as_posix()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def load_yaml(path: pathlib.Path) -> dict[str, Any]:
    value = c0_gate.load_yaml(path)
    if not isinstance(value, dict):
        raise ValueError(f"YAML root must be an object: {path}")
    return value


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_json_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def schema_subset_failures(
    payload: dict[str, Any], schema: dict[str, Any], label: str
) -> list[str]:
    return [f"{label} {failure}" for failure in validate_json_schema_subset(payload, schema)]


def _family_label(family_id: str) -> str:
    return family_id.split("_", 1)[1].upper()


def generate_row_id_preview(family_id: str, family_local_index: int) -> str:
    if family_id not in REQUIRED_FAMILY_IDS:
        raise ValueError(f"unknown AtomicRows family id: {family_id}")
    if not isinstance(family_local_index, int) or isinstance(family_local_index, bool):
        raise ValueError("family_local_index must be an integer")
    row_count = dict((slug, count) for _, slug, count in FAMILY_DISTRIBUTION)[family_id]
    if family_local_index < 1 or family_local_index > row_count:
        raise ValueError(f"family_local_index out of range for {family_id}")
    family_number = int(family_id.split("_", 1)[0])
    return f"AR_EXACT_{family_number:03d}_{_family_label(family_id)}_{family_local_index:06d}"


def compute_family_ranges(
    distribution: Sequence[tuple[int, str, int]] = FAMILY_DISTRIBUTION,
) -> list[FamilyRange]:
    ranges: list[FamilyRange] = []
    start = FIRST_ROW_INDEX
    for family_number, family_id, row_count in distribution:
        end = start + row_count - 1
        ranges.append(
            FamilyRange(
                family_number=family_number,
                family_id=family_id,
                row_count=row_count,
                start_row_index=start,
                end_row_index=end,
            )
        )
        start = end + 1
    return ranges


def ranges_are_contiguous(ranges: Sequence[FamilyRange]) -> bool:
    if not ranges:
        return False
    if ranges[0].start_row_index != FIRST_ROW_INDEX:
        return False
    return all(
        previous.end_row_index + 1 == current.start_row_index
        for previous, current in zip(ranges, ranges[1:])
    )


def ranges_non_overlapping(ranges: Sequence[FamilyRange]) -> bool:
    return all(
        previous.end_row_index < current.start_row_index
        for previous, current in zip(ranges, ranges[1:])
    )


def ranges_have_no_gaps(ranges: Sequence[FamilyRange]) -> bool:
    return ranges_are_contiguous(ranges)


def _require_false_fields(
    failures: list[str],
    mapping: dict[str, Any],
    fields: Sequence[str],
    *,
    prefix: str,
) -> None:
    for field in fields:
        if mapping.get(field) is not False:
            failures.append(f"{prefix}.{field} must be false")


def _require_true_fields(
    failures: list[str],
    mapping: dict[str, Any],
    fields: Sequence[str],
    *,
    prefix: str,
) -> None:
    for field in fields:
        if mapping.get(field) is not True:
            failures.append(f"{prefix}.{field} must be true")


def _load_sources(repo_root: pathlib.Path) -> tuple[SourceInputs | None, list[str]]:
    failures: list[str] = []
    loaded: dict[str, dict[str, Any]] = {}
    paths = {
        "bridge": AUTHORITY_CLASSIFIER_BRIDGE_PATH,
        "bridge_report": AUTHORITY_CLASSIFIER_BRIDGE_REPORT_PATH,
        "expansion": EXPANSION_MANIFEST_PATH,
        "expansion_report": EXPANSION_MANIFEST_REPORT_PATH,
        "distribution": OWNER_APPROVED_DISTRIBUTION_PATH,
        "distribution_report": OWNER_APPROVED_DISTRIBUTION_REPORT_PATH,
    }
    for label, path in paths.items():
        path_abs = _resolve(repo_root, path)
        try:
            loaded[label] = load_json(path_abs) if path.suffix == ".json" else load_yaml(path_abs)
        except FileNotFoundError:
            failures.append(f"{label} missing: {path.as_posix()}")
        except Exception as exc:
            failures.append(f"{label} invalid: {path.as_posix()}: {exc}")
    if failures:
        return None, failures
    return (
        SourceInputs(
            bridge=loaded["bridge"],
            bridge_report=loaded["bridge_report"],
            expansion=loaded["expansion"],
            expansion_report=loaded["expansion_report"],
            distribution=loaded["distribution"],
            distribution_report=loaded["distribution_report"],
        ),
        [],
    )


def validate_source_inputs(sources: SourceInputs) -> list[str]:
    failures: list[str] = []

    bridge_row_id_law = sources.bridge.get("future_row_id_law")
    if not isinstance(bridge_row_id_law, dict):
        failures.append("Repair PR A bridge future_row_id_law must be present")
        bridge_row_id_law = {}
    if bridge_row_id_law.get("format") != "AR_EXACT_<family_number>_<family_slug>_<six_digit_family_index>":
        failures.append("Repair PR A row-ID law format must remain canonical")
    if bridge_row_id_law.get("deterministic") is not True:
        failures.append("Repair PR A row-ID law must remain deterministic")
    if bridge_row_id_law.get("row_order") != "FAMILY_ORDER_THEN_ROW_INDEX_WITHIN_FAMILY":
        failures.append("Repair PR A row-ID row order must remain family order then local row index")

    bridge_doctrine = sources.bridge.get("row_field_doctrine")
    if not isinstance(bridge_doctrine, dict):
        failures.append("Repair PR A row_field_doctrine must be present")
        bridge_doctrine = {}
    _require_true_fields(
        failures,
        bridge_doctrine,
        (
            "every_future_exact_row_field_requires_authority_class",
            "internally_sourced_fields_require_source_pointer",
            "blocked_fields_require_block_code",
            "every_future_exact_row_requires_agent_eligibility_block",
        ),
        prefix="bridge.row_field_doctrine",
    )
    _require_false_fields(
        failures,
        bridge_doctrine,
        (
            "unknown_authority_allowed",
            "non_null_external_fact_without_accepted_source_evidence_allowed",
            "runtime_private_account_order_fill_cash_without_receipt_allowed",
            "replay_paper_values_without_result_packets_allowed",
            "optimizer_quantum_backend_values_without_receipts_allowed",
            "profit_latency_execution_superiority_quantum_advantage_without_future_evidence_allowed",
        ),
        prefix="bridge.row_field_doctrine",
    )

    bridge_no_authority = sources.bridge.get("no_authority_created")
    if not isinstance(bridge_no_authority, dict):
        failures.append("Repair PR A no_authority_created must be present")
        bridge_no_authority = {}
    for field in (
        "exact_rows_created",
        "atomicrows_bundle_jsonl_created",
        "atomicrows_bundle_sha256_created",
        "sha_computed",
        "freeze_authority_created",
        "final_readiness_created",
        "runtime_live_order_authority_created",
        "source_fact_authority_created",
        "connector_semantic_authority_created",
        "profit_evidence_created",
        "latency_evidence_created",
        "execution_superiority_evidence_created",
        "quantum_backend_authority_created",
        "quantum_advantage_evidence_created",
    ):
        if bridge_no_authority.get(field) is not False:
            failures.append(f"bridge.no_authority_created.{field} must be false")

    if sources.bridge_report.get("validator_stdout_marker") != bridge_gate.SUCCESS_MARKER:
        failures.append("Repair PR A bridge report marker mismatch")
    if sources.expansion_report.get("validator_stdout_marker") != expansion_gate.SUCCESS_MARKER:
        failures.append("Repair PR B expansion report marker mismatch")
    if sources.distribution_report.get("validator_stdout_marker") != c0_gate.SUCCESS_MARKER:
        failures.append("Repair PR C0 distribution report marker mismatch")

    expansion_families = sources.expansion.get("families")
    if not isinstance(expansion_families, list):
        failures.append("Repair PR B expansion manifest families must be a list")
        expansion_families = []
    distribution_entries = sources.distribution.get("distribution")
    if not isinstance(distribution_entries, list):
        failures.append("Repair PR C0 distribution must be a list")
        distribution_entries = []

    expected_ranges = compute_family_ranges()
    if len(expansion_families) != FAMILY_COUNT:
        failures.append("Repair PR B expansion manifest must contain 15 families")
    if len(distribution_entries) != FAMILY_COUNT:
        failures.append("Repair PR C0 distribution must contain 15 families")

    for index, expected in enumerate(expected_ranges):
        if index < len(distribution_entries):
            c0_entry = distribution_entries[index]
            if c0_entry.get("family_number") != expected.family_number:
                failures.append(f"C0 distribution[{index}].family_number mismatch")
            if c0_entry.get("family_slug") != expected.family_id:
                failures.append(f"C0 distribution[{index}].family_slug mismatch")
            if c0_entry.get("target_row_count") != expected.row_count:
                failures.append(f"C0 distribution[{index}].target_row_count mismatch")
        if index < len(expansion_families):
            expansion_entry = expansion_families[index]
            if expansion_entry.get("family_number") != expected.family_number:
                failures.append(f"Expansion family[{index}].family_number mismatch")
            if expansion_entry.get("family_slug") != expected.family_id:
                failures.append(f"Expansion family[{index}].family_slug mismatch")
            if expansion_entry.get("target_row_count") != expected.row_count:
                failures.append(f"Expansion family[{index}].target_row_count mismatch")
            if expansion_entry.get("row_index_start") != expected.start_row_index:
                failures.append(f"Expansion family[{index}].row_index_start mismatch")
            if expansion_entry.get("row_index_end") != expected.end_row_index:
                failures.append(f"Expansion family[{index}].row_index_end mismatch")
            if expansion_entry.get("agent_eligibility_governance_required_for_future_rows") is not True:
                failures.append(f"Expansion family[{index}] must require agent eligibility")
            if expansion_entry.get("deny_by_default_agent_access_required") is not True:
                failures.append(f"Expansion family[{index}] must preserve deny-by-default access")

    if sources.distribution.get("counts_sum") != TARGET_TOTAL_ROWS:
        failures.append("Repair PR C0 counts_sum must be 4183")
    if sources.distribution_report.get("final_row_index") != FINAL_ROW_INDEX:
        failures.append("Repair PR C0 final_row_index must be 4183")
    if sources.expansion_report.get("final_row_index") != FINAL_ROW_INDEX:
        failures.append("Repair PR B final_row_index must be 4183")
    if sources.distribution_report.get("row_ranges_contiguous") is not True:
        failures.append("Repair PR C0 row ranges must be contiguous")
    if sources.expansion_report.get("row_ranges_contiguous") is not True:
        failures.append("Repair PR B row ranges must be contiguous")
    if sources.distribution_report.get("quantum_family_total_rows") != QUANTUM_FORWARD_TOTAL_ROWS:
        failures.append("Repair PR C0 quantum total must be 1103")
    if sources.distribution_report.get("agent_governance_family_rows") != AGENT_GOVERNANCE_FAMILY_ROWS:
        failures.append("Repair PR C0 agent governance family rows must be 270")

    c0_not_authorized = sources.distribution.get("not_authorized_by_this_approval")
    if not isinstance(c0_not_authorized, dict):
        failures.append("Repair PR C0 not_authorized_by_this_approval must be present")
        c0_not_authorized = {}
    for field in c0_gate.NOT_AUTHORIZED_FALSE_FIELDS:
        if c0_not_authorized.get(field) is not False:
            failures.append(f"C0 not_authorized_by_this_approval.{field} must be false")

    return failures


def validate_forbidden_artifacts(repo_root: pathlib.Path) -> tuple[list[str], ForbiddenArtifactState]:
    failures: list[str] = []
    exact_source_abs = _resolve(repo_root, FUTURE_EXACT_ROW_SOURCES_DIRECTORY)
    bundle_abs = _resolve(repo_root, FUTURE_BUNDLE_PATH)
    bundle_sha_abs = _resolve(repo_root, FUTURE_BUNDLE_SHA_PATH)
    exact_row_files: list[str] = []
    atomic_rows_root = repo_root / pathlib.Path("docs/master_plan/atomic_rows")
    if atomic_rows_root.exists():
        exact_row_files = sorted(
            path.relative_to(repo_root).as_posix()
            for path in atomic_rows_root.rglob("*.exact_rows.jsonl")
        )
    if exact_source_abs.exists():
        failures.append(f"forbidden exact row source directory exists: {FUTURE_EXACT_ROW_SOURCES_DIRECTORY_TEXT}")
    if bundle_abs.exists():
        failures.append(f"forbidden bundle exists: {FUTURE_BUNDLE_PATH.as_posix()}")
    if bundle_sha_abs.exists():
        failures.append(f"forbidden bundle SHA exists: {FUTURE_BUNDLE_SHA_PATH.as_posix()}")
    if exact_row_files:
        failures.append("forbidden exact row source files exist: " + ", ".join(exact_row_files))
    return failures, ForbiddenArtifactState(
        exact_row_sources_directory_created=exact_source_abs.exists(),
        bundle_written=bundle_abs.exists(),
        bundle_sha_written=bundle_sha_abs.exists(),
        exact_row_files=tuple(exact_row_files),
    )


def validate_manifest_payload(
    config: dict[str, Any],
    schema: dict[str, Any],
    forbidden_state: ForbiddenArtifactState,
) -> list[str]:
    failures: list[str] = []
    failures.extend(schema_subset_failures(config, schema, "CONFIG"))

    expected_identity = {
        "manifest_type": MANIFEST_TYPE,
        "manifest_version": MANIFEST_VERSION,
        "repair_pr": REPAIR_PR,
        "authority_class": AUTHORITY_CLASS,
        "row_write_mode": "DRY_RUN_ONLY",
        "dry_run_only": True,
        "exact_rows_written": False,
        "exact_row_sources_directory_created": False,
        "bundle_written": False,
        "bundle_sha_written": False,
        "freeze_created": False,
        "final_readiness_created": False,
    }
    for field, expected in expected_identity.items():
        if config.get(field) != expected:
            failures.append(f"config.{field} must be {expected!r}")

    source_inputs = config.get("source_inputs")
    if not isinstance(source_inputs, dict):
        failures.append("source_inputs must be an object")
        source_inputs = {}
    expected_source_inputs = {
        "authority_classifier_bridge_path": AUTHORITY_CLASSIFIER_BRIDGE_PATH.as_posix(),
        "authority_classifier_bridge_report_path": AUTHORITY_CLASSIFIER_BRIDGE_REPORT_PATH.as_posix(),
        "expansion_manifest_path": EXPANSION_MANIFEST_PATH.as_posix(),
        "expansion_manifest_report_path": EXPANSION_MANIFEST_REPORT_PATH.as_posix(),
        "owner_approved_distribution_path": OWNER_APPROVED_DISTRIBUTION_PATH.as_posix(),
        "owner_approved_distribution_report_path": OWNER_APPROVED_DISTRIBUTION_REPORT_PATH.as_posix(),
    }
    for field, expected in expected_source_inputs.items():
        if source_inputs.get(field) != expected:
            failures.append(f"source_inputs.{field} must be {expected}")

    future_outputs = config.get("future_planned_outputs")
    if not isinstance(future_outputs, dict):
        failures.append("future_planned_outputs must be an object")
        future_outputs = {}
    if future_outputs.get("future_exact_row_sources_directory") != FUTURE_EXACT_ROW_SOURCES_DIRECTORY_TEXT:
        failures.append("future exact row sources directory path mismatch")
    if future_outputs.get("future_bundle_path") != FUTURE_BUNDLE_PATH.as_posix():
        failures.append("future bundle path mismatch")
    if future_outputs.get("future_bundle_sha_path") != FUTURE_BUNDLE_SHA_PATH.as_posix():
        failures.append("future bundle SHA path mismatch")
    _require_true_fields(
        failures,
        future_outputs,
        (
            "future_exact_row_sources_directory_forbidden_to_create_in_repair_pr_c",
            "future_bundle_path_forbidden_to_create_in_repair_pr_c",
            "future_bundle_sha_path_forbidden_to_create_in_repair_pr_c",
        ),
        prefix="future_planned_outputs",
    )

    expected = config.get("expected")
    if not isinstance(expected, dict):
        failures.append("expected must be an object")
        expected = {}
    expected_fields = {
        "expected_total_rows": TARGET_TOTAL_ROWS,
        "expected_first_row_index": FIRST_ROW_INDEX,
        "expected_final_row_index": FINAL_ROW_INDEX,
        "expected_family_count": FAMILY_COUNT,
        "expected_quantum_forward_total_rows": QUANTUM_FORWARD_TOTAL_ROWS,
        "expected_agent_governance_family_id": AGENT_GOVERNANCE_FAMILY_ID,
        "expected_agent_governance_family_rows": AGENT_GOVERNANCE_FAMILY_ROWS,
    }
    for field, expected_value in expected_fields.items():
        if expected.get(field) != expected_value:
            failures.append(f"expected.{field} must be {expected_value!r}")

    row_index_policy = config.get("row_index_generation_policy")
    if not isinstance(row_index_policy, dict):
        failures.append("row_index_generation_policy must be an object")
        row_index_policy = {}
    _require_true_fields(
        failures,
        row_index_policy,
        (
            "row_ranges_must_be_contiguous",
            "row_ranges_must_not_overlap",
            "row_ranges_must_not_have_gaps",
            "family_order_must_follow_c0_exactly",
            "no_randomization",
            "no_timestamp_in_row_id",
            "no_environment_dependent_value_in_row_id",
            "no_filesystem_order_dependency",
        ),
        prefix="row_index_generation_policy",
    )

    row_id_policy = config.get("row_id_generation_policy")
    if not isinstance(row_id_policy, dict):
        failures.append("row_id_generation_policy must be an object")
        row_id_policy = {}
    expected_row_id_policy = {
        "row_id_law_source": "REPAIR_PR_A_FUTURE_ROW_ID_LAW",
        "row_id_preview_template": "AR_EXACT_<family_number>_<family_slug_upper>_<six_digit_family_index>",
        "row_id_preview_is_exact_row_materialization": False,
        "row_ids_encode_family_number_family_slug_and_family_local_index": True,
        "row_order": "FAMILY_ORDER_THEN_ROW_INDEX_WITHIN_FAMILY",
        "global_row_index_rule": "CUMULATIVE_PRIOR_FAMILY_ROW_COUNT_PLUS_ROW_INDEX_WITHIN_FAMILY",
        "deterministic": True,
        "no_randomization": True,
        "no_timestamp_in_row_id": True,
        "no_environment_dependent_value_in_row_id": True,
        "no_filesystem_order_dependency": True,
    }
    for field, expected_value in expected_row_id_policy.items():
        if row_id_policy.get(field) != expected_value:
            failures.append(f"row_id_generation_policy.{field} must be {expected_value!r}")

    authority_policy = config.get("authority_field_policy")
    if not isinstance(authority_policy, dict):
        failures.append("authority_field_policy must be an object")
        authority_policy = {}
    _require_true_fields(
        failures,
        authority_policy,
        (
            "every_future_row_requires_authority_class",
            "every_future_row_requires_source_pointer_policy",
            "every_future_row_requires_block_code_policy",
        ),
        prefix="authority_field_policy",
    )
    _require_false_fields(
        failures,
        authority_policy,
        ("unknown_authority_allowed", "non_null_external_fact_without_accepted_source_evidence_allowed"),
        prefix="authority_field_policy",
    )

    source_policy = config.get("source_pointer_policy")
    if not isinstance(source_policy, dict):
        failures.append("source_pointer_policy must be an object")
        source_policy = {}
    _require_false_fields(
        failures,
        source_policy,
        (
            "source_facts_retrieved_by_this_pr",
            "source_facts_accepted_by_this_pr",
            "connector_semantics_populated_by_this_pr",
            "external_fact_authority_created_by_this_pr",
        ),
        prefix="source_pointer_policy",
    )
    if source_policy.get("source_required_policy_for_missing_external_facts") != "SOURCE_EVIDENCE_REQUIRED":
        failures.append("source_pointer_policy must preserve SOURCE_EVIDENCE_REQUIRED sentinel")

    block_policy = config.get("block_code_policy")
    if not isinstance(block_policy, dict):
        failures.append("block_code_policy must be an object")
        block_policy = {}
    if tuple(block_policy.get("dry_run_blocking_basis", ())) != DRY_RUN_BLOCKING_BASIS:
        failures.append("block_code_policy.dry_run_blocking_basis must match canonical dry-run blockers")
    _require_true_fields(
        failures,
        block_policy,
        ("every_future_row_has_planned_block_code_policy",),
        prefix="block_code_policy",
    )

    agent_policy = config.get("agent_eligibility_policy")
    if not isinstance(agent_policy, dict):
        failures.append("agent_eligibility_policy must be an object")
        agent_policy = {}
    _require_true_fields(
        failures,
        agent_policy,
        ("agent_eligibility_required", "future_eligibility_matrix_required"),
        prefix="agent_eligibility_policy",
    )
    _require_false_fields(
        failures,
        agent_policy,
        (
            "specific_agent_family_assignments_created",
            "specific_agent_row_assignments_created",
            "live_order_agent_authority_created",
            "quantum_backend_agent_authority_created",
        ),
        prefix="agent_eligibility_policy",
    )

    subfamily_policy = config.get("subfamily_row_class_policy")
    if not isinstance(subfamily_policy, dict):
        failures.append("subfamily_row_class_policy must be an object")
        subfamily_policy = {}
    _require_true_fields(
        failures,
        subfamily_policy,
        (
            "subfamily_row_class_doctrine_required",
            "placeholder_policy_is_fail_closed_for_live_runtime_authority",
        ),
        prefix="subfamily_row_class_policy",
    )
    if subfamily_policy.get("subfamily_classification_state") != "PLANNED_REQUIRED_PENDING_REPAIR_PR_D_EXACT_ROW_CONTENT":
        failures.append("subfamily classification state must remain planned/pending")
    if subfamily_policy.get("row_classification_state") != "PLANNED_REQUIRED_PENDING_REPAIR_PR_D_EXACT_ROW_CONTENT":
        failures.append("row classification state must remain planned/pending")

    quantum_policy = config.get("quantum_forward_metadata_policy")
    if not isinstance(quantum_policy, dict):
        failures.append("quantum_forward_metadata_policy must be an object")
        quantum_policy = {}
    if tuple(quantum_policy.get("quantum_forward_family_ids", ())) != QUANTUM_FORWARD_FAMILY_IDS:
        failures.append("quantum_forward_metadata_policy family ids must match C0")
    _require_false_fields(
        failures,
        quantum_policy,
        (
            "quantum_backend_execution_created",
            "quantum_simulator_execution_created",
            "quantum_provider_execution_created",
            "quantum_advantage_claim_created",
            "quantum_latency_superiority_claim_created",
            "quantum_execution_superiority_claim_created",
            "quantum_profit_evidence_created",
        ),
        prefix="quantum_forward_metadata_policy",
    )

    no_authority = config.get("no_authority_created")
    if not isinstance(no_authority, dict):
        failures.append("no_authority_created must be an object")
        no_authority = {}
    _require_false_fields(failures, no_authority, NO_AUTHORITY_FALSE_FIELDS, prefix="no_authority_created")

    blocked = config.get("blocked_future_work")
    if not isinstance(blocked, dict):
        failures.append("blocked_future_work must be an object")
        blocked = {}
    _require_true_fields(
        failures,
        blocked,
        (
            "repair_pr_d_generate_exact_row_source_files_required",
            "repair_pr_d2_e0_agent_family_eligibility_matrix_required",
            "repair_pr_e_bundle_materialization_required",
            "repair_pr_f_sha_freeze_required",
            "roadmap_pr_101_final_readiness_delayed",
        ),
        prefix="blocked_future_work",
    )

    manifest_families = config.get("family_generation_plan")
    if not isinstance(manifest_families, list):
        failures.append("family_generation_plan must be a list")
        manifest_families = []
    expected_ranges = compute_family_ranges()
    if len(manifest_families) != FAMILY_COUNT:
        failures.append("family_generation_plan must contain 15 entries")
    if tuple(entry.get("family_id") for entry in manifest_families if isinstance(entry, dict)) != REQUIRED_FAMILY_IDS:
        failures.append("family_generation_plan family order must match C0 exactly")

    for index, expected_range in enumerate(expected_ranges):
        if index >= len(manifest_families) or not isinstance(manifest_families[index], dict):
            continue
        entry = manifest_families[index]
        expected_file = f"{FUTURE_EXACT_ROW_SOURCES_DIRECTORY_TEXT}{expected_range.family_id}.exact_rows.jsonl"
        expected_quantum = expected_range.family_id in QUANTUM_FORWARD_FAMILY_IDS
        expected_agent = expected_range.family_id == AGENT_GOVERNANCE_FAMILY_ID
        expected_metadata_class = QUANTUM_METADATA_CLASSES.get(expected_range.family_id, NON_QUANTUM_METADATA_CLASS)
        expected_metadata_authority = (
            "METADATA_ONLY_NOT_BACKEND_OUTPUT" if expected_quantum else NON_QUANTUM_METADATA_CLASS
        )
        expected_values = {
            "family_id": expected_range.family_id,
            "family_label": _family_label(expected_range.family_id),
            "row_count": expected_range.row_count,
            "start_row_index": expected_range.start_row_index,
            "end_row_index": expected_range.end_row_index,
            "quantum_forward_family_flag": expected_quantum,
            "agent_governance_family_flag": expected_agent,
            "future_exact_rows_file_path": expected_file,
            "row_id_generation_policy_ref": "REPAIR_PR_A_FUTURE_ROW_ID_LAW",
            "authority_field_policy_ref": "REPAIR_PR_A_AUTHORITY_CLASSIFIER_BRIDGE",
            "agent_eligibility_policy_ref": "REPAIR_PR_A_AGENT_ELIGIBILITY_GOVERNANCE",
            "subfamily_row_class_policy_ref": "REPAIR_PR_B_SUBFAMILY_ROW_CLASS_DOCTRINE",
            "quantum_metadata_authority": expected_metadata_authority,
            "quantum_metadata_class": expected_metadata_class,
            "dry_run_only_no_write_flag": True,
        }
        for field, expected_value in expected_values.items():
            if entry.get(field) != expected_value:
                failures.append(f"family_generation_plan[{index}].{field} must be {expected_value!r}")
        if expected_quantum:
            _require_false_fields(
                failures,
                entry,
                (
                    "quantum_backend_execution_created",
                    "quantum_simulator_execution_created",
                    "quantum_provider_execution_created",
                    "quantum_advantage_claim_created",
                    "quantum_latency_superiority_claim_created",
                    "quantum_execution_superiority_claim_created",
                    "quantum_profit_evidence_created",
                ),
                prefix=f"family_generation_plan[{index}]",
            )

    if forbidden_state.exact_row_sources_directory_created:
        failures.append("validator saw forbidden exact_row_sources directory before report build")
    if forbidden_state.bundle_written:
        failures.append("validator saw forbidden AtomicRows.bundle.jsonl before report build")
    if forbidden_state.bundle_sha_written:
        failures.append("validator saw forbidden AtomicRows.bundle.sha256 before report build")
    if forbidden_state.exact_row_files:
        failures.append("validator saw forbidden exact row files before report build")
    return failures


def build_family_generation_plan_summary(ranges: Sequence[FamilyRange]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for family_range in ranges:
        quantum_forward = family_range.family_id in QUANTUM_FORWARD_FAMILY_IDS
        agent_governance = family_range.family_id == AGENT_GOVERNANCE_FAMILY_ID
        summaries.append(
            {
                "family_number": family_range.family_number,
                "family_id": family_range.family_id,
                "family_label": _family_label(family_range.family_id),
                "row_count": family_range.row_count,
                "start_row_index": family_range.start_row_index,
                "end_row_index": family_range.end_row_index,
                "first_preview_row_id": generate_row_id_preview(family_range.family_id, 1),
                "last_preview_row_id": generate_row_id_preview(
                    family_range.family_id, family_range.row_count
                ),
                "future_exact_rows_file_path": (
                    f"{FUTURE_EXACT_ROW_SOURCES_DIRECTORY_TEXT}"
                    f"{family_range.family_id}.exact_rows.jsonl"
                ),
                "quantum_forward_family_flag": quantum_forward,
                "agent_governance_family_flag": agent_governance,
                "row_id_generation_policy_ref": "REPAIR_PR_A_FUTURE_ROW_ID_LAW",
                "authority_field_policy_ref": "REPAIR_PR_A_AUTHORITY_CLASSIFIER_BRIDGE",
                "agent_eligibility_policy_ref": "REPAIR_PR_A_AGENT_ELIGIBILITY_GOVERNANCE",
                "subfamily_row_class_policy_ref": "REPAIR_PR_B_SUBFAMILY_ROW_CLASS_DOCTRINE",
                "quantum_metadata_authority": (
                    "METADATA_ONLY_NOT_BACKEND_OUTPUT"
                    if quantum_forward
                    else NON_QUANTUM_METADATA_CLASS
                ),
                "quantum_metadata_class": QUANTUM_METADATA_CLASSES.get(
                    family_range.family_id, NON_QUANTUM_METADATA_CLASS
                ),
                "quantum_backend_execution_created": False,
                "quantum_simulator_execution_created": False,
                "quantum_provider_execution_created": False,
                "quantum_advantage_claim_created": False,
                "quantum_latency_superiority_claim_created": False,
                "quantum_execution_superiority_claim_created": False,
                "quantum_profit_evidence_created": False,
                "dry_run_only_no_write_flag": True,
            }
        )
    return summaries


def build_report(
    *,
    config: dict[str, Any],
    ranges: Sequence[FamilyRange],
    forbidden_state: ForbiddenArtifactState,
    schema_path: pathlib.Path,
    config_path: pathlib.Path,
    report_path: pathlib.Path,
) -> dict[str, Any]:
    total_rows = sum(family.row_count for family in ranges)
    quantum_total = sum(
        family.row_count for family in ranges if family.family_id in QUANTUM_FORWARD_FAMILY_IDS
    )
    agent_rows = sum(
        family.row_count for family in ranges if family.family_id == AGENT_GOVERNANCE_FAMILY_ID
    )
    no_authority = copy.deepcopy(config["no_authority_created"])
    return {
        "report_type": REPORT_TYPE,
        "report_version": REPORT_VERSION,
        "manifest_type": MANIFEST_TYPE,
        "manifest_version": MANIFEST_VERSION,
        "repair_pr": REPAIR_PR,
        "authority_class": AUTHORITY_CLASS,
        "generated_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "schema_path": schema_path.as_posix(),
        "config_path": config_path.as_posix(),
        "report_path": report_path.as_posix(),
        "validation_result": VALIDATION_RESULT,
        "validator_stdout_marker": SUCCESS_MARKER,
        "dry_run_only": True,
        "exact_rows_written": False,
        "exact_row_sources_directory_created": forbidden_state.exact_row_sources_directory_created,
        "bundle_written": forbidden_state.bundle_written,
        "bundle_sha_written": forbidden_state.bundle_sha_written,
        "freeze_created": False,
        "final_readiness_created": False,
        "source_inputs": copy.deepcopy(config["source_inputs"]),
        "expected": {
            "family_count": FAMILY_COUNT,
            "total_rows": TARGET_TOTAL_ROWS,
            "first_row_index": FIRST_ROW_INDEX,
            "final_row_index": FINAL_ROW_INDEX,
            "quantum_forward_total_rows": QUANTUM_FORWARD_TOTAL_ROWS,
            "agent_governance_family_rows": AGENT_GOVERNANCE_FAMILY_ROWS,
        },
        "actual_dry_run": {
            "family_count": len(ranges),
            "would_generate_total_rows": total_rows,
            "first_row_index": ranges[0].start_row_index if ranges else None,
            "final_row_index": ranges[-1].end_row_index if ranges else None,
            "quantum_forward_total_rows": quantum_total,
            "agent_governance_family_rows": agent_rows,
        },
        "checks": {
            "source_inputs_present": True,
            "source_inputs_consumed": True,
            "family_count_matches": len(ranges) == FAMILY_COUNT,
            "total_rows_match": total_rows == TARGET_TOTAL_ROWS,
            "final_row_index_matches": bool(ranges) and ranges[-1].end_row_index == FINAL_ROW_INDEX,
            "row_ranges_contiguous": ranges_are_contiguous(ranges),
            "row_ranges_non_overlapping": ranges_non_overlapping(ranges),
            "row_ranges_no_gaps": ranges_have_no_gaps(ranges),
            "family_order_matches_c0": tuple(family.family_id for family in ranges) == REQUIRED_FAMILY_IDS,
            "row_id_generation_deterministic": True,
            "authority_class_policy_present_for_all_future_rows": True,
            "source_pointer_policy_present_for_all_future_rows": True,
            "block_code_policy_present_for_all_future_rows": True,
            "agent_eligibility_policy_present_for_all_future_rows": True,
            "quantum_forward_metadata_policy_present_for_quantum_families": True,
            "no_exact_rows_written": True,
            "no_exact_row_sources_directory_created": not forbidden_state.exact_row_sources_directory_created,
            "no_bundle_written": not forbidden_state.bundle_written,
            "no_bundle_sha_written": not forbidden_state.bundle_sha_written,
            "no_freeze_created": True,
            "no_final_readiness_created": True,
            "no_specific_agent_assignments_created": True,
            "no_runtime_authority_created": True,
            "no_live_authority_created": True,
            "no_order_authority_created": True,
            "no_source_fact_acceptance_created": True,
            "no_connector_semantic_binding_created": True,
            "no_optimizer_execution_created": True,
            "no_quantum_backend_execution_created": True,
            "no_profit_evidence_created": True,
            "no_latency_evidence_created": True,
            "no_execution_superiority_evidence_created": True,
            "no_quantum_advantage_evidence_created": True,
            "no_venue_api_provider_facts_fabricated": True,
            "report_does_not_serialize_exact_source_rows": True,
        },
        "row_id_generation_policy": copy.deepcopy(config["row_id_generation_policy"]),
        "row_index_generation_policy": copy.deepcopy(config["row_index_generation_policy"]),
        "authority_field_policy": copy.deepcopy(config["authority_field_policy"]),
        "source_pointer_policy": copy.deepcopy(config["source_pointer_policy"]),
        "block_code_policy": copy.deepcopy(config["block_code_policy"]),
        "agent_eligibility_policy": copy.deepcopy(config["agent_eligibility_policy"]),
        "subfamily_row_class_policy": copy.deepcopy(config["subfamily_row_class_policy"]),
        "quantum_forward_metadata_policy": copy.deepcopy(config["quantum_forward_metadata_policy"]),
        "field_presence_plan": {
            "total_future_rows_checked_in_memory": total_rows,
            "planned_authority_class_present_count": total_rows,
            "planned_source_pointer_policy_present_count": total_rows,
            "planned_block_code_policy_present_count": total_rows,
            "planned_agent_eligibility_present_count": total_rows,
        },
        "family_generation_plan": build_family_generation_plan_summary(ranges),
        "forbidden_artifact_absence": {
            "exact_row_sources_directory_absent": not forbidden_state.exact_row_sources_directory_created,
            "AtomicRows.bundle.jsonl_absent": not forbidden_state.bundle_written,
            "AtomicRows.bundle.sha256_absent": not forbidden_state.bundle_sha_written,
            "exact_row_files_found": list(forbidden_state.exact_row_files),
        },
        "no_authority_created": no_authority,
        "blocked_future_work": copy.deepcopy(config["blocked_future_work"]),
    }


def _contains_large_exact_row_list(value: Any) -> bool:
    if isinstance(value, list):
        if len(value) >= TARGET_TOTAL_ROWS:
            return True
        return any(_contains_large_exact_row_list(item) for item in value)
    if isinstance(value, dict):
        if "exact_rows" in value or "source_rows" in value:
            return True
        return any(_contains_large_exact_row_list(item) for item in value.values())
    return False


def validate_report(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected = {
        "report_type": REPORT_TYPE,
        "report_version": REPORT_VERSION,
        "manifest_type": MANIFEST_TYPE,
        "manifest_version": MANIFEST_VERSION,
        "repair_pr": REPAIR_PR,
        "authority_class": AUTHORITY_CLASS,
        "validation_result": VALIDATION_RESULT,
        "validator_stdout_marker": SUCCESS_MARKER,
        "dry_run_only": True,
        "generated_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
    }
    for field, expected_value in expected.items():
        if report.get(field) != expected_value:
            failures.append(f"report.{field} must be {expected_value!r}")
    _require_false_fields(failures, report, REPORT_FALSE_FIELDS, prefix="report")
    expected_section = report.get("expected")
    if not isinstance(expected_section, dict):
        failures.append("report.expected must be an object")
        expected_section = {}
    if expected_section.get("total_rows") != TARGET_TOTAL_ROWS:
        failures.append("report.expected.total_rows must be 4183")
    actual = report.get("actual_dry_run")
    if not isinstance(actual, dict):
        failures.append("report.actual_dry_run must be an object")
        actual = {}
    actual_expected = {
        "family_count": FAMILY_COUNT,
        "would_generate_total_rows": TARGET_TOTAL_ROWS,
        "first_row_index": FIRST_ROW_INDEX,
        "final_row_index": FINAL_ROW_INDEX,
        "quantum_forward_total_rows": QUANTUM_FORWARD_TOTAL_ROWS,
        "agent_governance_family_rows": AGENT_GOVERNANCE_FAMILY_ROWS,
    }
    for field, expected_value in actual_expected.items():
        if actual.get(field) != expected_value:
            failures.append(f"report.actual_dry_run.{field} must be {expected_value!r}")
    checks = report.get("checks")
    if not isinstance(checks, dict):
        failures.append("report.checks must be an object")
        checks = {}
    _require_true_fields(failures, checks, CHECK_TRUE_FIELDS, prefix="report.checks")
    field_presence = report.get("field_presence_plan")
    if not isinstance(field_presence, dict):
        failures.append("report.field_presence_plan must be an object")
        field_presence = {}
    for field in (
        "total_future_rows_checked_in_memory",
        "planned_authority_class_present_count",
        "planned_source_pointer_policy_present_count",
        "planned_block_code_policy_present_count",
        "planned_agent_eligibility_present_count",
    ):
        if field_presence.get(field) != TARGET_TOTAL_ROWS:
            failures.append(f"report.field_presence_plan.{field} must be 4183")
    family_plan = report.get("family_generation_plan")
    if not isinstance(family_plan, list) or len(family_plan) != FAMILY_COUNT:
        failures.append("report.family_generation_plan must contain 15 summaries")
        family_plan = []
    if tuple(entry.get("family_id") for entry in family_plan if isinstance(entry, dict)) != REQUIRED_FAMILY_IDS:
        failures.append("report family order must match C0 exactly")
    if _contains_large_exact_row_list(report):
        failures.append("report must not serialize exact rows or 4183 source records")
    if report != json.loads(serialize_report(report)):
        failures.append("report serialization must be deterministic")
    return failures


def validate(
    *,
    repo_root: pathlib.Path = pathlib.Path("."),
    schema_path: pathlib.Path = DEFAULT_SCHEMA,
    config_path: pathlib.Path = DEFAULT_CONFIG,
    output_path: pathlib.Path = DEFAULT_REPORT,
) -> ValidationResult:
    repo_root = repo_root.resolve()
    schema_abs = _resolve(repo_root, schema_path)
    config_abs = _resolve(repo_root, config_path)
    output_abs = _resolve(repo_root, output_path)

    failures: list[str] = []
    try:
        schema = load_json(schema_abs)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        return ValidationResult(False, (f"schema load failed: {exc}",), None)
    try:
        config = load_yaml(config_abs)
    except Exception as exc:
        return ValidationResult(False, (f"config load failed: {exc}",), None)

    sources, source_failures = _load_sources(repo_root)
    failures.extend(source_failures)
    if sources is not None:
        failures.extend(validate_source_inputs(sources))

    forbidden_failures, forbidden_state = validate_forbidden_artifacts(repo_root)
    failures.extend(forbidden_failures)
    failures.extend(expansion_gate.validate_master_plan_not_modified(repo_root)[1])
    failures.extend(expansion_gate.validate_static_surface(repo_root / "tools" / pathlib.Path(__file__).name))
    failures.extend(validate_manifest_payload(config, schema, forbidden_state))

    ranges = compute_family_ranges()
    report = build_report(
        config=config,
        ranges=ranges,
        forbidden_state=forbidden_state,
        schema_path=schema_path,
        config_path=config_path,
        report_path=output_path,
    )
    second_report = build_report(
        config=copy.deepcopy(config),
        ranges=copy.deepcopy(ranges),
        forbidden_state=copy.deepcopy(forbidden_state),
        schema_path=schema_path,
        config_path=config_path,
        report_path=output_path,
    )
    if report != second_report:
        failures.append("generated dry-run report is not deterministic across builds")
    failures.extend(validate_report(report))

    if failures:
        return ValidationResult(False, tuple(failures), report)

    write_json_report(report, output_abs)
    return ValidationResult(True, tuple(), report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate AtomicRows exact-row generator dry-run manifest."
    )
    parser.add_argument("--repo-root", type=pathlib.Path, default=pathlib.Path("."))
    parser.add_argument("--schema", type=pathlib.Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--config", "--manifest", type=pathlib.Path, default=DEFAULT_CONFIG)
    parser.add_argument("--out", dest="output_path", type=pathlib.Path, default=DEFAULT_REPORT)
    parser.add_argument("--report-out", dest="output_path", type=pathlib.Path)
    args = parser.parse_args(argv)

    result = validate(
        repo_root=args.repo_root,
        schema_path=args.schema,
        config_path=args.config,
        output_path=args.output_path,
    )
    if result.ok:
        print(SUCCESS_MARKER)
        return 0

    print(FAILURE_MARKER, file=sys.stderr)
    for failure in result.failures:
        print(failure, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
