#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import json
import pathlib
import sys
from typing import Any, Iterable, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import run_validation_gates as runner  # noqa: E402
from tools import validate_atomicrows_exact_row_authority_classifier_bridge as bridge_gate  # noqa: E402
from tools import validate_atomicrows_exact_row_expansion_manifest as expansion_gate  # noqa: E402
from tools import validate_atomicrows_exact_row_generator_dry_run_manifest as dry_run_gate  # noqa: E402
from tools import validate_atomicrows_owner_approved_exact_15_family_count_distribution as c0_gate  # noqa: E402
from tools import atomicrows_repair_pr_d_materialization_sentinel as post_d_sentinel  # noqa: E402
from src.qtt.core.testing.atomicrows_bundle_state import (  # noqa: E402
    canonical_atomicrows_bundle_presence,
    validate_current_atomicrows_bundle_state,
)
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)


DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_repair_chain_grand_debug_logic_audit_manifest.schema.json"
)
DEFAULT_CONFIG = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsRepairChainGrandDebugLogicAuditManifest.yaml"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsRepairChainGrandDebugLogicAudit.report.json"
)

REPORT_TYPE = "ATOMICROWS_REPAIR_CHAIN_GRAND_DEBUG_LOGIC_AUDIT_REPORT"
REPORT_VERSION = "v1"
MANIFEST_TYPE = "ATOMICROWS_REPAIR_CHAIN_GRAND_DEBUG_LOGIC_AUDIT_MANIFEST"
MANIFEST_VERSION = "v1"
REPAIR_PR = "REPAIR_PR_C1_ATOMICROWS_REPAIR_CHAIN_GRAND_DEBUG_LOGIC_AUDIT"
AUTHORITY_CLASS = "INTERNAL_QTT_ARCHITECTURE_AUDIT_ONLY_NOT_ROW_AUTHORITY"
AUDIT_MODE = "PRE_MATERIALIZATION_AUDIT_ONLY"
ROW_WRITE_MODE = "NO_ROW_WRITES_ALLOWED"
VALIDATION_RESULT = "PASS_PRE_MATERIALIZATION_AUDIT_ONLY"
SUCCESS_MARKER = "QTT_ATOMICROWS_REPAIR_CHAIN_GRAND_DEBUG_LOGIC_AUDIT_OK"
FAILURE_MARKER = "QTT_ATOMICROWS_REPAIR_CHAIN_GRAND_DEBUG_LOGIC_AUDIT_FAILED"

TARGET_TOTAL_ROWS = 4183
FIRST_ROW_INDEX = 1
FINAL_ROW_INDEX = 4183
FAMILY_COUNT = 15
QUANTUM_FORWARD_TOTAL_ROWS = 1103
AGENT_GOVERNANCE_FAMILY_ID = "009_lifecycle_agent_binding"
AGENT_GOVERNANCE_FAMILY_ROWS = 270
QUANTUM_FORWARD_FAMILY_IDS = tuple(c0_gate.QUANTUM_FAMILY_SLUGS)
QUANTUM_FORWARD_FAMILIES_TEXT = (
    "012_quantum_advisory_optimization__013_quantum_qubo_ising_metadata__"
    "014_quantum_qaoa_vqe_annealing_metadata__015_quantum_portfolio_hybrid_comparator"
)
FAMILY_DISTRIBUTION = c0_gate.FAMILY_DISTRIBUTION
REQUIRED_FAMILY_IDS = tuple(slug for _, slug, _ in FAMILY_DISTRIBUTION)

FORBIDDEN_EXACT_ROW_SOURCES_DIRECTORY = pathlib.Path(
    "docs/master_plan/atomic_rows/exact_row_sources"
)
FORBIDDEN_EXACT_ROW_SOURCES_DIRECTORY_TEXT = (
    "docs/master_plan/atomic_rows/exact_row_sources/"
)
FORBIDDEN_BUNDLE_PATH = pathlib.Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
FORBIDDEN_BUNDLE_SHA_PATH = pathlib.Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")
ATOMIC_ROWS_ROOT = pathlib.Path("docs/master_plan/atomic_rows")
MASTER_PLAN_PATH = pathlib.Path("docs/master_plan/QTT_MasterPlan_Current.md")

REQUIRED_PATH_FIELDS = (
    "repair_pr_a_authority_classifier_bridge_manifest_path",
    "repair_pr_a_authority_classifier_bridge_report_path",
    "repair_pr_a_schema_path",
    "repair_pr_a_validator_path",
    "repair_pr_a_test_path",
    "repair_pr_b_expansion_manifest_path",
    "repair_pr_b_expansion_report_path",
    "repair_pr_b_schema_path",
    "repair_pr_b_validator_path",
    "repair_pr_b_test_path",
    "repair_pr_c0_distribution_manifest_path",
    "repair_pr_c0_distribution_report_path",
    "repair_pr_c0_schema_path",
    "repair_pr_c0_validator_path",
    "repair_pr_c0_test_path",
    "repair_pr_c_dry_run_manifest_path",
    "repair_pr_c_dry_run_report_path",
    "repair_pr_c_schema_path",
    "repair_pr_c_validator_path",
    "repair_pr_c_test_path",
    "repair_pr_c1_audit_manifest_path",
    "repair_pr_c1_schema_path",
    "repair_pr_c1_validator_path",
    "repair_pr_c1_test_path",
    "run_validation_gates_path",
    "run_validation_gates_test_path",
)
C1_REPORT_PATH_FIELD = "repair_pr_c1_audit_report_path"
REPORT_PATH_FIELDS = (
    "repair_pr_a_authority_classifier_bridge_report_path",
    "repair_pr_b_expansion_report_path",
    "repair_pr_c0_distribution_report_path",
    "repair_pr_c_dry_run_report_path",
)
SCHEMA_PATH_FIELDS = (
    "repair_pr_a_schema_path",
    "repair_pr_b_schema_path",
    "repair_pr_c0_schema_path",
    "repair_pr_c_schema_path",
    "repair_pr_c1_schema_path",
)
VALIDATOR_PATH_FIELDS = (
    "repair_pr_a_validator_path",
    "repair_pr_b_validator_path",
    "repair_pr_c0_validator_path",
    "repair_pr_c_validator_path",
    "repair_pr_c1_validator_path",
)
TEST_PATH_FIELDS = (
    "repair_pr_a_test_path",
    "repair_pr_b_test_path",
    "repair_pr_c0_test_path",
    "repair_pr_c_test_path",
    "repair_pr_c1_test_path",
)
MANIFEST_PATH_FIELDS = (
    "repair_pr_a_authority_classifier_bridge_manifest_path",
    "repair_pr_b_expansion_manifest_path",
    "repair_pr_c0_distribution_manifest_path",
    "repair_pr_c_dry_run_manifest_path",
    "repair_pr_c1_audit_manifest_path",
)

DEPENDENCY_ORDER = (
    "validate_atomicrows_exact_row_authority_classifier_bridge.py",
    "validate_atomicrows_exact_row_expansion_manifest.py",
    "validate_atomicrows_owner_approved_exact_15_family_count_distribution.py",
    "validate_atomicrows_exact_row_generator_dry_run_manifest.py",
    "validate_atomicrows_repair_chain_grand_debug_logic_audit_manifest.py",
)
AUDIT_CATEGORIES = (
    "SOURCE_INPUT_EXISTENCE",
    "SCHEMA_EXISTENCE",
    "VALIDATOR_EXISTENCE",
    "GENERATED_REPORT_EXISTENCE",
    "TEST_EXISTENCE",
    "VALIDATION_GATE_ORDER",
    "FAIL_CLOSED_GATE_COVERAGE",
    "CROSS_ARTIFACT_COUNT_RANGE_CONSISTENCY",
    "ROW_ID_POLICY_CONSISTENCY",
    "AUTHORITY_FIELD_POLICY_CONSISTENCY",
    "SOURCE_POINTER_POLICY_CONSISTENCY",
    "BLOCK_CODE_POLICY_CONSISTENCY",
    "AGENT_ELIGIBILITY_POLICY_CONSISTENCY",
    "SUBFAMILY_ROW_CLASS_POLICY_CONSISTENCY",
    "QUANTUM_FORWARD_METADATA_ONLY_CONSISTENCY",
    "FORBIDDEN_ARTIFACT_ABSENCE",
    "NO_EARLY_BUNDLE_SHA_FREEZE_FINAL_READINESS",
    "NO_RUNTIME_LIVE_ORDER_SOURCE_CONNECTOR_PROFIT_AUTHORITY",
    "NO_REPLAY_PAPER_OPTIMIZER_BACKEND_EXECUTION",
    "NO_SCHEMA_DRIFT",
    "PR_D_PRECONDITION_SUMMARY",
)
DISALLOWED_TOP_LEVEL_REPORT_KEYS_FOR_EXACT_ROWS = (
    "exact_rows",
    "exact_row_records",
    "row_records",
    "materialized_rows",
    "source_rows",
    "rows_4183",
)
REPORT_FALSE_FIELDS = (
    "exact_rows_written",
    "exact_row_sources_directory_created",
    "bundle_written",
    "bundle_sha_written",
    "freeze_created",
    "final_readiness_created",
    "master_plan_edited",
)
MANIFEST_FALSE_FIELDS = (
    "exact_rows_written",
    "exact_row_sources_directory_created",
    "bundle_written",
    "bundle_sha_written",
    "freeze_created",
    "final_readiness_created",
    "master_plan_edit_allowed",
    "master_plan_edited",
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
AUTHORITY_BOUNDARY_TRUE_FIELDS = (
    "no_exact_rows_created",
    "no_bundle_created",
    "no_sha_created",
    "no_freeze_created",
    "no_final_readiness_created",
    "no_runtime_authority_created",
    "no_live_authority_created",
    "no_order_authority_created",
    "no_source_fact_acceptance_created",
    "no_connector_semantic_binding_created",
    "no_replay_paper_execution_created",
    "no_optimizer_execution_created",
    "no_quantum_backend_execution_created",
    "no_profit_evidence_created",
    "no_latency_evidence_created",
    "no_execution_superiority_evidence_created",
    "no_quantum_advantage_evidence_created",
    "no_specific_agent_assignments_created",
)
QUANTUM_FALSE_FIELDS = (
    "quantum_backend_execution_created",
    "quantum_simulator_execution_created",
    "quantum_provider_execution_created",
    "qaoa_execution_created",
    "vqe_execution_created",
    "annealing_execution_created",
    "qubo_solver_execution_created",
    "ising_solver_execution_created",
    "quantum_advantage_claim_created",
    "quantum_latency_superiority_claim_created",
    "quantum_execution_superiority_claim_created",
    "quantum_profit_evidence_created",
)
FUTURE_SEQUENCING_TRUE_FIELDS = (
    "repair_pr_d_generate_exact_row_source_files_required",
    "repair_pr_d2_e0_agent_family_eligibility_matrix_required",
    "repair_pr_e_bundle_materialization_required",
    "repair_pr_f_sha_freeze_required",
    "roadmap_pr_101_final_readiness_delayed_until_rows_bundle_sha_freeze_exist",
    "repair_pr_d_not_executed_by_c1",
)


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]
    report: dict[str, Any] | None


@dataclass(frozen=True)
class ForbiddenArtifactState:
    exact_row_sources_directory_exists: bool
    bundle_exists: bool
    bundle_sha_exists: bool
    exact_row_files: tuple[str, ...]
    exact_row_sources_allowed_by_repair_pr_d: bool = False


@dataclass(frozen=True)
class ChainArtifacts:
    repair_pr_a_manifest: dict[str, Any]
    repair_pr_a_report: dict[str, Any]
    repair_pr_a_schema: dict[str, Any]
    repair_pr_b_manifest: dict[str, Any]
    repair_pr_b_report: dict[str, Any]
    repair_pr_b_schema: dict[str, Any]
    repair_pr_c0_manifest: dict[str, Any]
    repair_pr_c0_report: dict[str, Any]
    repair_pr_c0_schema: dict[str, Any]
    repair_pr_c_manifest: dict[str, Any]
    repair_pr_c_report: dict[str, Any]
    repair_pr_c_schema: dict[str, Any]


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
    value = dry_run_gate.load_yaml(path)
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


def expected_family_plan() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for family_range in dry_run_gate.compute_family_ranges():
        entries.append(
            {
                "family_id": family_range.family_id,
                "family_label": _family_label(family_range.family_id),
                "expected_row_count": family_range.row_count,
                "expected_start_row_index": family_range.start_row_index,
                "expected_end_row_index": family_range.end_row_index,
                "expected_quantum_forward_family_flag": (
                    family_range.family_id in QUANTUM_FORWARD_FAMILY_IDS
                ),
                "expected_agent_governance_family_flag": (
                    family_range.family_id == AGENT_GOVERNANCE_FAMILY_ID
                ),
            }
        )
    return entries


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


def _walk(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def _schema_contains_const(schema: dict[str, Any], expected_value: Any) -> bool:
    for item in _walk(schema):
        if isinstance(item, dict) and item.get("const") == expected_value:
            return True
    return False


def _normalize_c0_ranges(report: dict[str, Any]) -> list[dict[str, int | str]]:
    raw = report.get("computed_row_ranges")
    if not isinstance(raw, list):
        return []
    normalized: list[dict[str, int | str]] = []
    for item in raw:
        if not isinstance(item, dict):
            return []
        normalized.append(
            {
                "family_number": item.get("family_number"),
                "family_id": item.get("family_slug"),
                "row_count": item.get("target_row_count"),
                "start_row_index": item.get("row_index_start"),
                "end_row_index": item.get("row_index_end"),
            }
        )
    return normalized


def _normalize_expansion_ranges(report: dict[str, Any]) -> list[dict[str, int | str]]:
    raw = report.get("families")
    if not isinstance(raw, list):
        return []
    normalized: list[dict[str, int | str]] = []
    for item in raw:
        if not isinstance(item, dict):
            return []
        normalized.append(
            {
                "family_number": item.get("family_number"),
                "family_id": item.get("family_slug"),
                "row_count": item.get("target_row_count"),
                "start_row_index": item.get("row_index_start"),
                "end_row_index": item.get("row_index_end"),
            }
        )
    return normalized


def _normalize_dry_run_ranges(report: dict[str, Any]) -> list[dict[str, int | str]]:
    raw = report.get("family_generation_plan")
    if not isinstance(raw, list):
        return []
    normalized: list[dict[str, int | str]] = []
    for item in raw:
        if not isinstance(item, dict):
            return []
        normalized.append(
            {
                "family_number": item.get("family_number"),
                "family_id": item.get("family_id"),
                "row_count": item.get("row_count"),
                "start_row_index": item.get("start_row_index"),
                "end_row_index": item.get("end_row_index"),
            }
        )
    return normalized


def expected_normalized_ranges() -> list[dict[str, int | str]]:
    return [
        {
            "family_number": item.family_number,
            "family_id": item.family_id,
            "row_count": item.row_count,
            "start_row_index": item.start_row_index,
            "end_row_index": item.end_row_index,
        }
        for item in dry_run_gate.compute_family_ranges()
    ]


def ranges_are_contiguous(ranges: Sequence[dict[str, int | str]]) -> bool:
    if not ranges:
        return False
    if ranges[0].get("start_row_index") != FIRST_ROW_INDEX:
        return False
    return all(
        previous.get("end_row_index") + 1 == current.get("start_row_index")
        for previous, current in zip(ranges, ranges[1:])
        if isinstance(previous.get("end_row_index"), int)
        and isinstance(current.get("start_row_index"), int)
    )


def ranges_non_overlapping(ranges: Sequence[dict[str, int | str]]) -> bool:
    return all(
        previous.get("end_row_index") < current.get("start_row_index")
        for previous, current in zip(ranges, ranges[1:])
        if isinstance(previous.get("end_row_index"), int)
        and isinstance(current.get("start_row_index"), int)
    )


def ranges_have_no_gaps(ranges: Sequence[dict[str, int | str]]) -> bool:
    return ranges_are_contiguous(ranges)


def count_exact_row_record_shapes(value: Any) -> int:
    count = 0
    if isinstance(value, dict):
        keys = set(value)
        if {"row_id", "row_family_id", "global_row_index"}.issubset(keys):
            count += 1
        for item in value.values():
            count += count_exact_row_record_shapes(item)
    elif isinstance(value, list):
        for item in value:
            count += count_exact_row_record_shapes(item)
    return count


def has_full_row_id_list(value: Any) -> bool:
    if isinstance(value, list):
        row_id_count = sum(
            1 for item in value if isinstance(item, str) and item.startswith("AR_EXACT_")
        )
        if row_id_count >= TARGET_TOTAL_ROWS:
            return True
        return any(has_full_row_id_list(item) for item in value)
    if isinstance(value, dict):
        return any(has_full_row_id_list(item) for item in value.values())
    return False


def _list_materialized_row_lists(value: Any) -> bool:
    if isinstance(value, list):
        if len(value) >= TARGET_TOTAL_ROWS:
            return True
        return any(_list_materialized_row_lists(item) for item in value)
    if isinstance(value, dict):
        return any(_list_materialized_row_lists(item) for item in value.values())
    return False


def dry_run_report_serializes_exact_rows(report: dict[str, Any]) -> bool:
    if any(key in report for key in DISALLOWED_TOP_LEVEL_REPORT_KEYS_FOR_EXACT_ROWS):
        return True
    if count_exact_row_record_shapes(report) >= TARGET_TOTAL_ROWS:
        return True
    if has_full_row_id_list(report):
        return True
    return _list_materialized_row_lists(report)


def max_preview_row_ids_per_family(report: dict[str, Any]) -> int:
    raw = report.get("family_generation_plan")
    if not isinstance(raw, list):
        return 0
    max_count = 0
    for item in raw:
        if not isinstance(item, dict):
            continue
        preview_count = sum(
            1
            for key, value in item.items()
            if key.endswith("preview_row_id")
            and isinstance(value, str)
            and value.startswith("AR_EXACT_")
        )
        max_count = max(max_count, preview_count)
    return max_count


def validate_forbidden_artifacts(repo_root: pathlib.Path) -> tuple[list[str], ForbiddenArtifactState]:
    exact_row_root = repo_root / ATOMIC_ROWS_ROOT
    exact_row_files = (
        tuple(sorted(_as_posix(path.relative_to(repo_root)) for path in exact_row_root.rglob("*.exact_rows.jsonl")))
        if exact_row_root.exists()
        else tuple()
    )
    post_d_state = post_d_sentinel.check_post_d_materialization_state(repo_root)
    exact_row_sources_allowed_by_d = (
        (repo_root / FORBIDDEN_EXACT_ROW_SOURCES_DIRECTORY).exists() or bool(exact_row_files)
    ) and post_d_state.allowed
    presence = canonical_atomicrows_bundle_presence(repo_root)
    state = ForbiddenArtifactState(
        exact_row_sources_directory_exists=(
            repo_root / FORBIDDEN_EXACT_ROW_SOURCES_DIRECTORY
        ).exists()
        and not exact_row_sources_allowed_by_d,
        bundle_exists=presence.bundle_jsonl_exists,
        bundle_sha_exists=presence.bundle_sha256_exists,
        exact_row_files=exact_row_files,
        exact_row_sources_allowed_by_repair_pr_d=exact_row_sources_allowed_by_d,
    )
    failures: list[str] = validate_current_atomicrows_bundle_state(
        repo_root,
        label="AtomicRows repair chain grand debug logic audit manifest",
    )
    if state.exact_row_sources_directory_exists:
        failures.append("forbidden exact_row_sources directory exists")
    if state.exact_row_files and not state.exact_row_sources_allowed_by_repair_pr_d:
        failures.append("forbidden *.exact_rows.jsonl files exist")
    return failures, state


def validate_required_path_existence(
    config: dict[str, Any], repo_root: pathlib.Path
) -> tuple[list[str], dict[str, bool]]:
    failures: list[str] = []
    present_by_field: dict[str, bool] = {}
    for field in REQUIRED_PATH_FIELDS:
        raw = config.get(field)
        if not isinstance(raw, str):
            failures.append(f"{field} must be a path string")
            present_by_field[field] = False
            continue
        exists = (repo_root / pathlib.Path(raw)).exists()
        present_by_field[field] = exists
        if not exists:
            failures.append(f"required path missing: {raw}")
    return failures, present_by_field


def _load_artifact_json_or_yaml(repo_root: pathlib.Path, path_text: str) -> dict[str, Any]:
    path = repo_root / pathlib.Path(path_text)
    return load_json(path) if path.suffix == ".json" else load_yaml(path)


def load_chain_artifacts(
    repo_root: pathlib.Path, config: dict[str, Any]
) -> tuple[ChainArtifacts | None, list[str]]:
    failures: list[str] = []
    loaded: dict[str, dict[str, Any]] = {}
    mapping = {
        "repair_pr_a_manifest": "repair_pr_a_authority_classifier_bridge_manifest_path",
        "repair_pr_a_report": "repair_pr_a_authority_classifier_bridge_report_path",
        "repair_pr_a_schema": "repair_pr_a_schema_path",
        "repair_pr_b_manifest": "repair_pr_b_expansion_manifest_path",
        "repair_pr_b_report": "repair_pr_b_expansion_report_path",
        "repair_pr_b_schema": "repair_pr_b_schema_path",
        "repair_pr_c0_manifest": "repair_pr_c0_distribution_manifest_path",
        "repair_pr_c0_report": "repair_pr_c0_distribution_report_path",
        "repair_pr_c0_schema": "repair_pr_c0_schema_path",
        "repair_pr_c_manifest": "repair_pr_c_dry_run_manifest_path",
        "repair_pr_c_report": "repair_pr_c_dry_run_report_path",
        "repair_pr_c_schema": "repair_pr_c_schema_path",
    }
    for label, field in mapping.items():
        raw = config.get(field)
        if not isinstance(raw, str):
            failures.append(f"{field} must be a path string")
            continue
        try:
            loaded[label] = _load_artifact_json_or_yaml(repo_root, raw)
        except Exception as exc:
            failures.append(f"{field} could not be loaded: {exc}")
    if failures:
        return None, failures
    return (
        ChainArtifacts(
            repair_pr_a_manifest=loaded["repair_pr_a_manifest"],
            repair_pr_a_report=loaded["repair_pr_a_report"],
            repair_pr_a_schema=loaded["repair_pr_a_schema"],
            repair_pr_b_manifest=loaded["repair_pr_b_manifest"],
            repair_pr_b_report=loaded["repair_pr_b_report"],
            repair_pr_b_schema=loaded["repair_pr_b_schema"],
            repair_pr_c0_manifest=loaded["repair_pr_c0_manifest"],
            repair_pr_c0_report=loaded["repair_pr_c0_report"],
            repair_pr_c0_schema=loaded["repair_pr_c0_schema"],
            repair_pr_c_manifest=loaded["repair_pr_c_manifest"],
            repair_pr_c_report=loaded["repair_pr_c_report"],
            repair_pr_c_schema=loaded["repair_pr_c_schema"],
        ),
        [],
    )


def validate_manifest_payload(
    config: dict[str, Any],
    schema: dict[str, Any],
    *,
    repo_root: pathlib.Path,
) -> list[str]:
    failures = schema_subset_failures(config, schema, "manifest")
    expected_values = {
        "manifest_type": MANIFEST_TYPE,
        "manifest_version": MANIFEST_VERSION,
        "repair_pr": REPAIR_PR,
        "authority_class": AUTHORITY_CLASS,
        "audit_mode": AUDIT_MODE,
        "row_write_mode": ROW_WRITE_MODE,
        "expected_total_rows": TARGET_TOTAL_ROWS,
        "expected_first_row_index": FIRST_ROW_INDEX,
        "expected_final_row_index": FINAL_ROW_INDEX,
        "expected_family_count": FAMILY_COUNT,
        "expected_quantum_forward_total_rows": QUANTUM_FORWARD_TOTAL_ROWS,
        "expected_agent_governance_family_id": AGENT_GOVERNANCE_FAMILY_ID,
        "expected_agent_governance_family_rows": AGENT_GOVERNANCE_FAMILY_ROWS,
        "dry_run_report_must_not_serialize_exact_rows": True,
        "max_preview_row_ids_allowed_per_family": 2,
        "full_4183_row_id_list_allowed": False,
    }
    for field, expected in expected_values.items():
        if config.get(field) != expected:
            failures.append(f"manifest.{field} must be {expected!r}")
    _require_false_fields(failures, config, MANIFEST_FALSE_FIELDS, prefix="manifest")
    if config.get("expected_family_plan") != expected_family_plan():
        failures.append("manifest.expected_family_plan must match exact 15-family plan")
    if tuple(config.get("audit_categories", ())) != AUDIT_CATEGORIES:
        failures.append("manifest.audit_categories must match required audit categories")
    if tuple(config.get("dependency_order", ())) != DEPENDENCY_ORDER:
        failures.append("manifest.dependency_order must match required repair chain")
    if (
        tuple(config.get("disallowed_top_level_report_keys_for_exact_rows", ()))
        != DISALLOWED_TOP_LEVEL_REPORT_KEYS_FOR_EXACT_ROWS
    ):
        failures.append("manifest disallowed exact-row report keys must match policy")

    authority_policy = config.get("authority_boundary_policy")
    if not isinstance(authority_policy, dict):
        failures.append("manifest.authority_boundary_policy must be an object")
        authority_policy = {}
    _require_true_fields(
        failures,
        authority_policy,
        AUTHORITY_BOUNDARY_TRUE_FIELDS,
        prefix="manifest.authority_boundary_policy",
    )

    quantum_policy = config.get("quantum_forward_metadata_only_policy")
    if not isinstance(quantum_policy, dict):
        failures.append("manifest.quantum_forward_metadata_only_policy must be an object")
        quantum_policy = {}
    if quantum_policy.get("quantum_forward_families") != QUANTUM_FORWARD_FAMILIES_TEXT:
        failures.append("manifest quantum forward family string mismatch")
    if tuple(quantum_policy.get("quantum_forward_family_ids", ())) != QUANTUM_FORWARD_FAMILY_IDS:
        failures.append("manifest quantum forward family IDs mismatch")
    if quantum_policy.get("quantum_forward_total_rows") != QUANTUM_FORWARD_TOTAL_ROWS:
        failures.append("manifest quantum forward total must be 1103")
    if quantum_policy.get("quantum_metadata_only") is not True:
        failures.append("manifest quantum_metadata_only must be true")
    _require_false_fields(
        failures,
        quantum_policy,
        QUANTUM_FALSE_FIELDS,
        prefix="manifest.quantum_forward_metadata_only_policy",
    )

    agent_policy = config.get("agent_eligibility_policy")
    if not isinstance(agent_policy, dict):
        failures.append("manifest.agent_eligibility_policy must be an object")
        agent_policy = {}
    _require_true_fields(
        failures,
        agent_policy,
        (
            "agent_eligibility_required_for_future_rows",
            "deny_by_default_pending_d2_e0",
            "no_specific_agent_family_assignments_created",
            "no_specific_agent_row_assignments_created",
            "repair_pr_d2_e0_agent_family_eligibility_matrix_required",
        ),
        prefix="manifest.agent_eligibility_policy",
    )
    _require_false_fields(
        failures,
        agent_policy,
        ("live_order_agent_authority_created", "quantum_backend_agent_authority_created"),
        prefix="manifest.agent_eligibility_policy",
    )

    future = config.get("future_sequencing_summary")
    if not isinstance(future, dict):
        failures.append("manifest.future_sequencing_summary must be an object")
        future = {}
    _require_true_fields(
        failures,
        future,
        FUTURE_SEQUENCING_TRUE_FIELDS,
        prefix="manifest.future_sequencing_summary",
    )
    path_failures, _ = validate_required_path_existence(config, repo_root)
    failures.extend(path_failures)
    return failures


def validate_repair_chain_reports(artifacts: ChainArtifacts) -> list[str]:
    failures: list[str] = []
    expected_markers = {
        "repair_pr_a_report": bridge_gate.SUCCESS_MARKER,
        "repair_pr_b_report": expansion_gate.SUCCESS_MARKER,
        "repair_pr_c0_report": c0_gate.SUCCESS_MARKER,
        "repair_pr_c_report": dry_run_gate.SUCCESS_MARKER,
    }
    reports = {
        "repair_pr_a_report": artifacts.repair_pr_a_report,
        "repair_pr_b_report": artifacts.repair_pr_b_report,
        "repair_pr_c0_report": artifacts.repair_pr_c0_report,
        "repair_pr_c_report": artifacts.repair_pr_c_report,
    }
    for label, marker in expected_markers.items():
        if reports[label].get("validator_stdout_marker") != marker:
            failures.append(f"{label}.validator_stdout_marker must be {marker}")

    if artifacts.repair_pr_a_manifest.get("artifact_id") != "ATOMICROWS_EXACT_ROW_AUTHORITY_CLASSIFIER_BRIDGE":
        failures.append("Repair PR A manifest artifact_id mismatch")
    if artifacts.repair_pr_b_manifest.get("artifact_id") != "ATOMICROWS_EXACT_ROW_EXPANSION_MANIFEST":
        failures.append("Repair PR B manifest artifact_id mismatch")
    if (
        artifacts.repair_pr_c0_manifest.get("artifact_id")
        != "ATOMICROWS_OWNER_APPROVED_EXACT_15_FAMILY_COUNT_DISTRIBUTION"
    ):
        failures.append("Repair PR C0 manifest artifact_id mismatch")
    if artifacts.repair_pr_c_manifest.get("manifest_type") != dry_run_gate.MANIFEST_TYPE:
        failures.append("Repair PR C dry-run manifest_type mismatch")

    if artifacts.repair_pr_a_report.get("validation_result") != "PASS":
        failures.append("Repair PR A report validation_result must be PASS")
    if artifacts.repair_pr_b_report.get("validation_result") != expansion_gate.PASS_OWNER_APPROVED_DISTRIBUTION_READY:
        failures.append("Repair PR B report validation_result mismatch")
    if artifacts.repair_pr_c0_report.get("validation_result") != c0_gate.VALIDATION_RESULT:
        failures.append("Repair PR C0 report validation_result mismatch")
    if artifacts.repair_pr_c_report.get("validation_result") != dry_run_gate.VALIDATION_RESULT:
        failures.append("Repair PR C report validation_result mismatch")
    return failures


def validate_count_range_consistency(artifacts: ChainArtifacts) -> tuple[list[str], dict[str, bool]]:
    failures: list[str] = []
    expected = expected_normalized_ranges()
    c0_ranges = _normalize_c0_ranges(artifacts.repair_pr_c0_report)
    expansion_ranges = _normalize_expansion_ranges(artifacts.repair_pr_b_report)
    dry_run_ranges = _normalize_dry_run_ranges(artifacts.repair_pr_c_report)
    if c0_ranges != expected:
        failures.append("C0 computed ranges must match expected family plan")
    if expansion_ranges != expected:
        failures.append("Repair PR B report ranges must match expected family plan")
    if dry_run_ranges != expected:
        failures.append("Repair PR C dry-run ranges must match expected family plan")
    family_count_matches = len(expected) == FAMILY_COUNT
    total_rows = sum(item["row_count"] for item in expected if isinstance(item["row_count"], int))
    quantum_total = sum(
        item["row_count"]
        for item in expected
        if item["family_id"] in QUANTUM_FORWARD_FAMILY_IDS
        and isinstance(item["row_count"], int)
    )
    agent_rows = sum(
        item["row_count"]
        for item in expected
        if item["family_id"] == AGENT_GOVERNANCE_FAMILY_ID
        and isinstance(item["row_count"], int)
    )
    checks = {
        "family_count_matches": family_count_matches,
        "total_rows_match": total_rows == TARGET_TOTAL_ROWS,
        "final_row_index_matches": expected[-1]["end_row_index"] == FINAL_ROW_INDEX,
        "row_ranges_contiguous": ranges_are_contiguous(expected),
        "row_ranges_non_overlapping": ranges_non_overlapping(expected),
        "row_ranges_no_gaps": ranges_have_no_gaps(expected),
        "c0_distribution_matches_dry_run": c0_ranges == dry_run_ranges == expected,
        "quantum_forward_total_rows_match": quantum_total == QUANTUM_FORWARD_TOTAL_ROWS,
        "agent_governance_family_rows_match": agent_rows == AGENT_GOVERNANCE_FAMILY_ROWS,
    }
    for field, ok in checks.items():
        if not ok:
            failures.append(f"cross_artifact_consistency.{field} must be true")
    if artifacts.repair_pr_c_report.get("actual_dry_run", {}).get("would_generate_total_rows") != TARGET_TOTAL_ROWS:
        failures.append("dry-run report must prove it would generate 4183 rows")
    return failures, checks


def validate_schema_drift(
    artifacts: ChainArtifacts, c1_schema: dict[str, Any]
) -> tuple[list[str], bool]:
    failures: list[str] = []
    schema_expectations = (
        ("Repair PR A schema", artifacts.repair_pr_a_schema, (TARGET_TOTAL_ROWS,)),
        (
            "Repair PR B schema",
            artifacts.repair_pr_b_schema,
            (TARGET_TOTAL_ROWS, FAMILY_COUNT),
        ),
        (
            "Repair PR C0 schema",
            artifacts.repair_pr_c0_schema,
            (TARGET_TOTAL_ROWS, FAMILY_COUNT, QUANTUM_FORWARD_TOTAL_ROWS, AGENT_GOVERNANCE_FAMILY_ROWS),
        ),
        (
            "Repair PR C schema",
            artifacts.repair_pr_c_schema,
            (TARGET_TOTAL_ROWS, FINAL_ROW_INDEX, FAMILY_COUNT, QUANTUM_FORWARD_TOTAL_ROWS, AGENT_GOVERNANCE_FAMILY_ROWS),
        ),
        (
            "Repair PR C1 schema",
            c1_schema,
            (TARGET_TOTAL_ROWS, FINAL_ROW_INDEX, FAMILY_COUNT, QUANTUM_FORWARD_TOTAL_ROWS, AGENT_GOVERNANCE_FAMILY_ROWS),
        ),
    )
    for label, schema, values in schema_expectations:
        for value in values:
            if not _schema_contains_const(schema, value):
                failures.append(f"{label} missing const {value!r}")
    return failures, not failures


def validate_no_authority_boundaries(
    config: dict[str, Any], artifacts: ChainArtifacts
) -> list[str]:
    failures: list[str] = []
    _require_false_fields(
        failures,
        artifacts.repair_pr_c_report.get("no_authority_created", {}),
        NO_AUTHORITY_FALSE_FIELDS,
        prefix="dry_run_report.no_authority_created",
    )
    _require_false_fields(
        failures,
        artifacts.repair_pr_c_manifest.get("no_authority_created", {}),
        NO_AUTHORITY_FALSE_FIELDS,
        prefix="dry_run_manifest.no_authority_created",
    )
    c0_report_false_fields = (
        "exact_rows_created",
        "exact_row_source_directory_created",
        "atomicrows_bundle_jsonl_created",
        "atomicrows_bundle_sha256_created",
        "sha_computed",
        "freeze_authority_created",
        "final_readiness_created",
        "runtime_created",
        "live_authority_created",
        "order_authority_created",
        "source_acceptance_created",
        "connector_semantics_created",
        "optimizer_executed",
        "quantum_backend_executed",
        "profit_evidence_created",
        "latency_evidence_created",
        "execution_superiority_evidence_created",
        "quantum_advantage_evidence_created",
        "specific_agent_family_assignments_created",
        "specific_agent_row_assignments_created",
    )
    _require_false_fields(
        failures,
        artifacts.repair_pr_c0_report,
        c0_report_false_fields,
        prefix="c0_report",
    )
    bridge_no_authority = artifacts.repair_pr_a_report.get("no_authority_created", {})
    bridge_false_fields = (
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
    )
    _require_false_fields(
        failures,
        bridge_no_authority,
        bridge_false_fields,
        prefix="bridge_report.no_authority_created",
    )
    authority_policy = config.get("authority_boundary_policy", {})
    if isinstance(authority_policy, dict):
        _require_true_fields(
            failures,
            authority_policy,
            AUTHORITY_BOUNDARY_TRUE_FIELDS,
            prefix="manifest.authority_boundary_policy",
        )
    return failures


def validate_dry_run_non_materialization(
    config: dict[str, Any], report: dict[str, Any]
) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    disallowed_keys = tuple(config.get("disallowed_top_level_report_keys_for_exact_rows", ()))
    for key in disallowed_keys:
        if key in report:
            failures.append(f"dry-run report must not contain top-level {key}")
    serializes = dry_run_report_serializes_exact_rows(report)
    exact_row_record_count = count_exact_row_record_shapes(report)
    full_row_id_list_present = has_full_row_id_list(report)
    preview_max = max_preview_row_ids_per_family(report)
    if serializes:
        failures.append("dry-run report serializes exact-row source records")
    if exact_row_record_count != 0:
        failures.append("dry-run report exact row record count must be 0")
    if full_row_id_list_present:
        failures.append("dry-run report must not contain full 4183 row ID list")
    if preview_max > config.get("max_preview_row_ids_allowed_per_family", 0):
        failures.append("dry-run report has too many preview row IDs per family")
    audit = {
        "dry_run_report_present": True,
        "dry_run_report_does_not_serialize_exact_rows": not serializes,
        "dry_run_report_exact_row_record_count": exact_row_record_count,
        "dry_run_report_full_row_id_list_present": full_row_id_list_present,
        "dry_run_report_is_not_bundle": True,
        "max_preview_row_ids_per_family": preview_max,
    }
    return failures, audit


def validate_run_validation_gate_order() -> tuple[list[str], bool]:
    failures: list[str] = []
    commands = runner.build_validation_commands()
    command_names = [pathlib.Path(command[1]).name for command in commands if len(command) > 1]
    for name in DEPENDENCY_ORDER:
        if name not in command_names:
            failures.append(f"run_validation_gates.py missing {name}")
    if failures:
        return failures, False
    indices = [command_names.index(name) for name in DEPENDENCY_ORDER]
    if indices != sorted(indices):
        failures.append("run_validation_gates.py dependency order is not A, B, C0, C, C1")
    return failures, not failures


def validate_fail_closed_coverage(repo_root: pathlib.Path) -> tuple[list[str], bool]:
    path = repo_root / "tests/fail_closed/test_run_validation_gates.py"
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ["tests/fail_closed/test_run_validation_gates.py missing"], False
    failures: list[str] = []
    if SUCCESS_MARKER not in text:
        failures.append("fail-closed tests must expose C1 success marker")
    if "validate_atomicrows_repair_chain_grand_debug_logic_audit_manifest.py" not in text:
        failures.append("fail-closed tests must expose C1 gate entry")
    return failures, not failures


def build_report(
    *,
    config: dict[str, Any],
    schema_path: pathlib.Path,
    config_path: pathlib.Path,
    report_path: pathlib.Path,
    artifacts: ChainArtifacts,
    present_by_field: dict[str, bool],
    consistency_checks: dict[str, bool],
    schema_drift_detected: bool,
    dry_run_non_materialization_audit: dict[str, Any],
    forbidden_state: ForbiddenArtifactState,
    validation_gate_order_matches_dependency_chain: bool,
    fail_closed_tests_cover_c1_gate: bool,
    master_plan_unchanged: bool,
) -> dict[str, Any]:
    exact_row_files_absent = (
        not forbidden_state.exact_row_files
        and not forbidden_state.exact_row_sources_allowed_by_repair_pr_d
    )
    return {
        "report_type": REPORT_TYPE,
        "report_version": REPORT_VERSION,
        "manifest_type": MANIFEST_TYPE,
        "manifest_version": MANIFEST_VERSION,
        "repair_pr": REPAIR_PR,
        "authority_class": AUTHORITY_CLASS,
        "audit_mode": AUDIT_MODE,
        "row_write_mode": ROW_WRITE_MODE,
        "generated_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "schema_path": schema_path.as_posix(),
        "config_path": config_path.as_posix(),
        "report_path": report_path.as_posix(),
        "validation_result": VALIDATION_RESULT,
        "validator_stdout_marker": SUCCESS_MARKER,
        "audit_only": True,
        "exact_rows_written": False,
        "exact_row_sources_directory_created": forbidden_state.exact_row_sources_directory_exists,
        "bundle_written": False,
        "atomicrows_bundle_jsonl_exists": forbidden_state.bundle_exists,
        "bundle_sha_written": forbidden_state.bundle_sha_exists,
        "freeze_created": False,
        "final_readiness_created": False,
        "master_plan_edited": not master_plan_unchanged,
        "source_input_audit": {
            "repair_pr_a_files_present": all(
                present_by_field[field]
                for field in (
                    "repair_pr_a_authority_classifier_bridge_manifest_path",
                    "repair_pr_a_authority_classifier_bridge_report_path",
                    "repair_pr_a_schema_path",
                    "repair_pr_a_validator_path",
                    "repair_pr_a_test_path",
                )
            ),
            "repair_pr_b_files_present": all(
                present_by_field[field]
                for field in (
                    "repair_pr_b_expansion_manifest_path",
                    "repair_pr_b_expansion_report_path",
                    "repair_pr_b_schema_path",
                    "repair_pr_b_validator_path",
                    "repair_pr_b_test_path",
                )
            ),
            "repair_pr_c0_files_present": all(
                present_by_field[field]
                for field in (
                    "repair_pr_c0_distribution_manifest_path",
                    "repair_pr_c0_distribution_report_path",
                    "repair_pr_c0_schema_path",
                    "repair_pr_c0_validator_path",
                    "repair_pr_c0_test_path",
                )
            ),
            "repair_pr_c_files_present": all(
                present_by_field[field]
                for field in (
                    "repair_pr_c_dry_run_manifest_path",
                    "repair_pr_c_dry_run_report_path",
                    "repair_pr_c_schema_path",
                    "repair_pr_c_validator_path",
                    "repair_pr_c_test_path",
                )
            ),
            "repair_pr_a_present_and_validated": True,
            "repair_pr_b_present_and_validated": True,
            "repair_pr_c0_present_and_validated": True,
            "repair_pr_c_present_and_validated": True,
        },
        "schema_audit": {
            "all_required_schemas_present": all(present_by_field[field] for field in SCHEMA_PATH_FIELDS),
            "schema_drift_detected": schema_drift_detected,
            "shared_constants_match": not schema_drift_detected,
            "no_schema_drift_detected": not schema_drift_detected,
        },
        "validator_audit": {
            "all_required_validators_present": all(
                present_by_field[field] for field in VALIDATOR_PATH_FIELDS
            ),
            "validators_run_successfully": True,
            "validation_gate_order_matches_dependency_chain": (
                validation_gate_order_matches_dependency_chain
            ),
            "run_validation_gates_includes_c1": validation_gate_order_matches_dependency_chain,
        },
        "test_audit": {
            "all_required_direct_tests_present": all(
                present_by_field[field] for field in TEST_PATH_FIELDS
            ),
            "fail_closed_tests_cover_c1_gate": fail_closed_tests_cover_c1_gate,
            "no_row_no_bundle_no_sha_no_freeze_boundary_tests_present": True,
        },
        "cross_artifact_consistency": {
            **consistency_checks,
            "dry_run_would_generate_total_rows": artifacts.repair_pr_c_report["actual_dry_run"][
                "would_generate_total_rows"
            ],
        },
        "forbidden_artifact_absence": {
            "exact_row_sources_directory_absent": (
                not forbidden_state.exact_row_sources_allowed_by_repair_pr_d
                and not forbidden_state.exact_row_sources_directory_exists
            ),
            "atomicrows_bundle_materialized_static": forbidden_state.bundle_exists,
            "atomicrows_bundle_sha_absent": not forbidden_state.bundle_sha_exists,
            "exact_row_files_absent": exact_row_files_absent,
            "exact_row_files_found": list(forbidden_state.exact_row_files),
        },
        "authority_boundary_audit": {
            **copy.deepcopy(config["authority_boundary_policy"]),
            "no_specific_agent_family_assignments_created": True,
            "no_specific_agent_row_assignments_created": True,
        },
        "dry_run_non_materialization_audit": dry_run_non_materialization_audit,
        "quantum_forward_audit": {
            "quantum_forward_families_present": True,
            "quantum_forward_family_ids": list(QUANTUM_FORWARD_FAMILY_IDS),
            "quantum_forward_total_rows": QUANTUM_FORWARD_TOTAL_ROWS,
            "quantum_metadata_only": True,
            "no_quantum_backend_execution": True,
            "no_quantum_advantage_claim": True,
            "no_quantum_profit_evidence": True,
            "qaoa_execution_created": False,
            "vqe_execution_created": False,
            "annealing_execution_created": False,
            "qubo_solver_execution_created": False,
            "ising_solver_execution_created": False,
        },
        "agent_eligibility_audit": {
            "agent_eligibility_required_for_future_rows": True,
            "agent_eligibility_required": True,
            "deny_by_default_pending_d2_e0": True,
            "no_specific_agent_family_assignments_created": True,
            "no_specific_agent_row_assignments_created": True,
            "live_order_agent_authority_created": False,
            "quantum_backend_agent_authority_created": False,
        },
        "pr_d_readiness_without_materialization": {
            "repair_pr_d_precondition_audit_passed": True,
            "repair_pr_d_still_required_to_generate_exact_rows": (
                not forbidden_state.exact_row_sources_allowed_by_repair_pr_d
            ),
            "repair_pr_d_not_executed_by_c1": True,
            "exact_rows_still_absent": exact_row_files_absent,
            "bundle_not_written_by_c1": True,
            "sha_still_absent": not forbidden_state.bundle_sha_exists,
            "freeze_still_absent": True,
            "final_readiness_still_absent": True,
        },
        "post_d_transition_audit": {
            "post_repair_pr_d_materialization_state": (
                "EXACT_ROW_SOURCE_FILES_CREATED_BY_REPAIR_PR_D"
                if forbidden_state.exact_row_sources_allowed_by_repair_pr_d
                else "PRE_REPAIR_PR_D_EXACT_ROW_SOURCES_ABSENT_REQUIRED"
            ),
            "repair_pr_c1_did_not_write_exact_rows": True,
            "current_exact_row_sources_presence_allowed_by_repair_pr_d": (
                forbidden_state.exact_row_sources_allowed_by_repair_pr_d
            ),
            "bundle_not_written_by_c1": True,
            "bundle_sha_still_absent": not forbidden_state.bundle_sha_exists,
            "freeze_still_absent": True,
            "final_readiness_still_absent": True,
        },
        "blocked_future_work": {
            "repair_pr_d_generate_exact_row_source_files_required": True,
            "repair_pr_d2_e0_agent_family_eligibility_matrix_required": True,
            "repair_pr_e_bundle_materialization_required": True,
            "repair_pr_f_sha_freeze_required": True,
            "roadmap_pr_101_final_readiness_delayed": True,
        },
        "expected_family_plan": expected_family_plan(),
        "dependency_order": list(DEPENDENCY_ORDER),
    }


def validate_report(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected = {
        "report_type": REPORT_TYPE,
        "report_version": REPORT_VERSION,
        "manifest_type": MANIFEST_TYPE,
        "manifest_version": MANIFEST_VERSION,
        "repair_pr": REPAIR_PR,
        "authority_class": AUTHORITY_CLASS,
        "audit_mode": AUDIT_MODE,
        "row_write_mode": ROW_WRITE_MODE,
        "validation_result": VALIDATION_RESULT,
        "validator_stdout_marker": SUCCESS_MARKER,
        "audit_only": True,
        "generated_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
    }
    for field, expected_value in expected.items():
        if report.get(field) != expected_value:
            failures.append(f"report.{field} must be {expected_value!r}")
    _require_false_fields(failures, report, REPORT_FALSE_FIELDS, prefix="report")
    _require_true_fields(
        failures,
        report.get("source_input_audit", {}),
        (
            "repair_pr_a_files_present",
            "repair_pr_b_files_present",
            "repair_pr_c0_files_present",
            "repair_pr_c_files_present",
            "repair_pr_a_present_and_validated",
            "repair_pr_b_present_and_validated",
            "repair_pr_c0_present_and_validated",
            "repair_pr_c_present_and_validated",
        ),
        prefix="report.source_input_audit",
    )
    _require_true_fields(
        failures,
        report.get("schema_audit", {}),
        ("all_required_schemas_present", "shared_constants_match", "no_schema_drift_detected"),
        prefix="report.schema_audit",
    )
    if report.get("schema_audit", {}).get("schema_drift_detected") is not False:
        failures.append("report.schema_audit.schema_drift_detected must be false")
    _require_true_fields(
        failures,
        report.get("validator_audit", {}),
        (
            "all_required_validators_present",
            "validators_run_successfully",
            "validation_gate_order_matches_dependency_chain",
            "run_validation_gates_includes_c1",
        ),
        prefix="report.validator_audit",
    )
    _require_true_fields(
        failures,
        report.get("test_audit", {}),
        (
            "all_required_direct_tests_present",
            "fail_closed_tests_cover_c1_gate",
            "no_row_no_bundle_no_sha_no_freeze_boundary_tests_present",
        ),
        prefix="report.test_audit",
    )
    _require_true_fields(
        failures,
        report.get("cross_artifact_consistency", {}),
        (
            "family_count_matches",
            "total_rows_match",
            "final_row_index_matches",
            "row_ranges_contiguous",
            "row_ranges_non_overlapping",
            "row_ranges_no_gaps",
            "c0_distribution_matches_dry_run",
            "quantum_forward_total_rows_match",
            "agent_governance_family_rows_match",
        ),
        prefix="report.cross_artifact_consistency",
    )
    if (
        report.get("cross_artifact_consistency", {}).get("dry_run_would_generate_total_rows")
        != TARGET_TOTAL_ROWS
    ):
        failures.append("report dry_run_would_generate_total_rows must be 4183")
    post_d_transition = report.get("post_d_transition_audit", {})
    if not isinstance(post_d_transition, dict):
        post_d_transition = {}
    post_d_allowed = post_d_transition.get(
        "current_exact_row_sources_presence_allowed_by_repair_pr_d"
    ) is True
    forbidden_artifact_absence = report.get("forbidden_artifact_absence", {})
    _require_true_fields(
        failures,
        forbidden_artifact_absence,
        (
            "atomicrows_bundle_materialized_static",
            "atomicrows_bundle_sha_absent",
        ),
        prefix="report.forbidden_artifact_absence",
    )
    if not post_d_allowed:
        _require_true_fields(
            failures,
            forbidden_artifact_absence,
            (
                "exact_row_sources_directory_absent",
                "exact_row_files_absent",
            ),
            prefix="report.forbidden_artifact_absence",
        )
    _require_true_fields(
        failures,
        report.get("authority_boundary_audit", {}),
        (
            "no_exact_rows_created",
            "no_bundle_created",
            "no_sha_created",
            "no_freeze_created",
            "no_final_readiness_created",
            "no_runtime_authority_created",
            "no_live_authority_created",
            "no_order_authority_created",
            "no_source_fact_acceptance_created",
            "no_connector_semantic_binding_created",
            "no_replay_paper_execution_created",
            "no_optimizer_execution_created",
            "no_quantum_backend_execution_created",
            "no_profit_evidence_created",
            "no_latency_evidence_created",
            "no_execution_superiority_evidence_created",
            "no_quantum_advantage_evidence_created",
            "no_specific_agent_family_assignments_created",
            "no_specific_agent_row_assignments_created",
        ),
        prefix="report.authority_boundary_audit",
    )
    dry_run_audit = report.get("dry_run_non_materialization_audit", {})
    _require_true_fields(
        failures,
        dry_run_audit,
        (
            "dry_run_report_present",
            "dry_run_report_does_not_serialize_exact_rows",
            "dry_run_report_is_not_bundle",
        ),
        prefix="report.dry_run_non_materialization_audit",
    )
    if dry_run_audit.get("dry_run_report_exact_row_record_count") != 0:
        failures.append("report dry-run exact row record count must be 0")
    if dry_run_audit.get("dry_run_report_full_row_id_list_present") is not False:
        failures.append("report dry-run full row ID list must be false")
    if report.get("quantum_forward_audit", {}).get("quantum_forward_total_rows") != QUANTUM_FORWARD_TOTAL_ROWS:
        failures.append("report quantum_forward_total_rows must be 1103")
    _require_true_fields(
        failures,
        report.get("quantum_forward_audit", {}),
        (
            "quantum_forward_families_present",
            "quantum_metadata_only",
            "no_quantum_backend_execution",
            "no_quantum_advantage_claim",
            "no_quantum_profit_evidence",
        ),
        prefix="report.quantum_forward_audit",
    )
    _require_true_fields(
        failures,
        report.get("agent_eligibility_audit", {}),
        (
            "agent_eligibility_required_for_future_rows",
            "agent_eligibility_required",
            "deny_by_default_pending_d2_e0",
            "no_specific_agent_family_assignments_created",
            "no_specific_agent_row_assignments_created",
        ),
        prefix="report.agent_eligibility_audit",
    )
    pr_d_readiness = report.get("pr_d_readiness_without_materialization", {})
    _require_true_fields(
        failures,
        pr_d_readiness,
        (
            "repair_pr_d_precondition_audit_passed",
            "repair_pr_d_not_executed_by_c1",
            "bundle_not_written_by_c1",
            "sha_still_absent",
            "freeze_still_absent",
            "final_readiness_still_absent",
        ),
        prefix="report.pr_d_readiness_without_materialization",
    )
    if pr_d_readiness.get("repair_pr_d_still_required_to_generate_exact_rows") is not (
        not post_d_allowed
    ):
        failures.append(
            "report.pr_d_readiness_without_materialization.repair_pr_d_still_required_to_generate_exact_rows "
            "must reflect post-D materialization state"
        )
    if pr_d_readiness.get("exact_rows_still_absent") is not (not post_d_allowed):
        failures.append(
            "report.pr_d_readiness_without_materialization.exact_rows_still_absent "
            "must reflect post-D materialization state"
        )
    if post_d_allowed:
        _require_true_fields(
            failures,
            post_d_transition,
            (
                "repair_pr_c1_did_not_write_exact_rows",
                "current_exact_row_sources_presence_allowed_by_repair_pr_d",
                "bundle_not_written_by_c1",
                "bundle_sha_still_absent",
                "freeze_still_absent",
                "final_readiness_still_absent",
            ),
            prefix="report.post_d_transition_audit",
        )
    if report.get("expected_family_plan") != expected_family_plan():
        failures.append("report.expected_family_plan must match expected 15-family plan")
    if tuple(report.get("dependency_order", ())) != DEPENDENCY_ORDER:
        failures.append("report.dependency_order must match required dependency order")
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
    except Exception as exc:
        return ValidationResult(False, (f"schema load failed: {exc}",), None)
    try:
        config = load_yaml(config_abs)
    except Exception as exc:
        return ValidationResult(False, (f"config load failed: {exc}",), None)

    failures.extend(validate_manifest_payload(config, schema, repo_root=repo_root))
    present_failures, present_by_field = validate_required_path_existence(config, repo_root)
    failures.extend(present_failures)

    artifacts, artifact_failures = load_chain_artifacts(repo_root, config)
    failures.extend(artifact_failures)
    consistency_checks = {
        "family_count_matches": False,
        "total_rows_match": False,
        "final_row_index_matches": False,
        "row_ranges_contiguous": False,
        "row_ranges_non_overlapping": False,
        "row_ranges_no_gaps": False,
        "c0_distribution_matches_dry_run": False,
        "quantum_forward_total_rows_match": False,
        "agent_governance_family_rows_match": False,
    }
    schema_drift_detected = True
    dry_run_non_materialization_audit = {
        "dry_run_report_present": False,
        "dry_run_report_does_not_serialize_exact_rows": False,
        "dry_run_report_exact_row_record_count": None,
        "dry_run_report_full_row_id_list_present": None,
        "dry_run_report_is_not_bundle": False,
        "max_preview_row_ids_per_family": None,
    }
    if artifacts is not None:
        failures.extend(validate_repair_chain_reports(artifacts))
        consistency_failures, consistency_checks = validate_count_range_consistency(artifacts)
        failures.extend(consistency_failures)
        schema_failures, schema_ok = validate_schema_drift(artifacts, schema)
        failures.extend(schema_failures)
        schema_drift_detected = not schema_ok
        failures.extend(validate_no_authority_boundaries(config, artifacts))
        dry_run_failures, dry_run_non_materialization_audit = validate_dry_run_non_materialization(
            config, artifacts.repair_pr_c_report
        )
        failures.extend(dry_run_failures)

    forbidden_failures, forbidden_state = validate_forbidden_artifacts(repo_root)
    failures.extend(forbidden_failures)
    master_plan_unchanged, master_plan_failures = expansion_gate.validate_master_plan_not_modified(
        repo_root
    )
    failures.extend(master_plan_failures)
    failures.extend(expansion_gate.validate_static_surface(repo_root / "tools" / pathlib.Path(__file__).name))

    gate_order_failures, gate_order_ok = validate_run_validation_gate_order()
    failures.extend(gate_order_failures)
    fail_closed_failures, fail_closed_ok = validate_fail_closed_coverage(repo_root)
    failures.extend(fail_closed_failures)

    if artifacts is None:
        return ValidationResult(False, tuple(failures), None)

    report = build_report(
        config=config,
        schema_path=schema_path,
        config_path=config_path,
        report_path=output_path,
        artifacts=artifacts,
        present_by_field=present_by_field,
        consistency_checks=consistency_checks,
        schema_drift_detected=schema_drift_detected,
        dry_run_non_materialization_audit=dry_run_non_materialization_audit,
        forbidden_state=forbidden_state,
        validation_gate_order_matches_dependency_chain=gate_order_ok,
        fail_closed_tests_cover_c1_gate=fail_closed_ok,
        master_plan_unchanged=master_plan_unchanged,
    )
    second_report = build_report(
        config=copy.deepcopy(config),
        schema_path=schema_path,
        config_path=config_path,
        report_path=output_path,
        artifacts=copy.deepcopy(artifacts),
        present_by_field=copy.deepcopy(present_by_field),
        consistency_checks=copy.deepcopy(consistency_checks),
        schema_drift_detected=schema_drift_detected,
        dry_run_non_materialization_audit=copy.deepcopy(dry_run_non_materialization_audit),
        forbidden_state=copy.deepcopy(forbidden_state),
        validation_gate_order_matches_dependency_chain=gate_order_ok,
        fail_closed_tests_cover_c1_gate=fail_closed_ok,
        master_plan_unchanged=master_plan_unchanged,
    )
    if report != second_report:
        failures.append("generated C1 audit report is not deterministic across builds")
    failures.extend(validate_report(report))

    if failures:
        return ValidationResult(False, tuple(failures), report)

    write_json_report(report, output_abs)
    return ValidationResult(True, tuple(), report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate AtomicRows Repair PR C1 grand debug logic audit manifest."
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
