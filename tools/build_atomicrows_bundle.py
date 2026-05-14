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

from tools import validate_atomicrows_bundle_row_family_source_files as pr98_gate  # noqa: E402
from tools import validate_atomicrows_full_bundle_row_expansion_plan as pr97_gate  # noqa: E402


DEFAULT_BUILDER_CONFIG = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsBundleBuilderDeterministicAssemblyGate.yaml"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsBundleBuilderDeterministicAssemblyGate.report.json"
)

PR97_PLAN_PATH = pr97_gate.DEFAULT_PRODUCTION_PLAN
PR97_REPORT_PATH = pr97_gate.DEFAULT_REPORT
PR98_SOURCE_FILE_SET_PATH = pr98_gate.DEFAULT_SOURCE_FILE_SET
PR98_REPORT_PATH = pr98_gate.DEFAULT_REPORT
CANONICAL_BUNDLE_JSONL = pr97_gate.CANONICAL_BUNDLE_JSONL
CANONICAL_BUNDLE_SHA256 = pr97_gate.CANONICAL_BUNDLE_SHA256

REPORT_ID = "ATOMICROWS_BUNDLE_BUILDER_DRY_RUN_REPORT"
REPORT_VERSION = "v1"
BUILDER_ID = "ATOMICROWS_DETERMINISTIC_BUNDLE_BUILDER_CONFIG"
BUILDER_VERSION = "v1"
ASSEMBLY_GATE_ID = "ATOMICROWS_BUNDLE_ASSEMBLY_GATE"
ASSEMBLY_GATE_VERSION = "v1"
SEMANTIC_TASK_ID = "ROADMAP-ATOMICROWS-BUNDLE-BUILDER"
ROADMAP_PR_LABEL = "PR_99"
ROADMAP_DELIVERY_LABEL = "PR #99"
SUCCESS_MARKER = "QTT_ATOMICROWS_BUNDLE_BUILDER_OK"
BUILD_BLOCKED_REASON_EXACT_SOURCE_ROWS = (
    "ATOMICROWS_BUNDLE_BUILD_BLOCKED_EXACT_SOURCE_ROWS_NOT_AUTHORIZED"
)
BUILD_BLOCKED_REASON_BLUEPRINTS_ONLY = "ATOMICROWS_BUNDLE_BUILD_BLOCKED_SOURCE_BLUEPRINTS_ONLY"
BUILD_BLOCKED_REASON_OWNER_APPROVAL = "ATOMICROWS_BUNDLE_BUILD_BLOCKED_OWNER_APPROVAL_REQUIRED"
BUILD_BLOCKED_REASON_TARGET_NOT_FEASIBLE = (
    "ATOMICROWS_BUNDLE_BUILD_BLOCKED_TARGET_TOTAL_ROW_COUNT_NOT_FEASIBLE"
)
PATH_DECISION = "PATH_B_BUILDER_FRAMEWORK_AND_BLOCKED_ASSEMBLY_GATE"
AUTHORITY_CLASS = (
    "STATIC_ATOMICROWS_BUNDLE_BUILDER_FRAMEWORK_ONLY_NOT_BUNDLE_NOT_HASH_"
    "NOT_FREEZE_NOT_FINAL_READINESS_NOT_RUNTIME_AUTHORITY"
)

REQUIRED_CONCEPTS = (
    "ATOMICROWS_DETERMINISTIC_BUNDLE_BUILDER_CONFIG",
    "ATOMICROWS_ROW_FAMILY_SOURCE_FILE_CONSUMER_CONTRACT",
    "ATOMICROWS_BUNDLE_ASSEMBLY_GATE",
    "ATOMICROWS_BUNDLE_BUILDER_DRY_RUN_REPORT",
    "ATOMICROWS_BUNDLE_JSONL_OUTPUT_CONTRACT",
    "ATOMICROWS_BUNDLE_BUILDER_FORBIDDEN_ARTIFACT_BOUNDARY",
    "ATOMICROWS_BUNDLE_BUILDER_QUANTUM_METADATA_VALIDATION",
)
QUANTUM_METADATA_REFS = pr98_gate.QUANTUM_METADATA_REFS
FORBIDDEN_QUANTUM_EFFECTS = pr97_gate.FORBIDDEN_QUANTUM_EFFECTS
FORBIDDEN_EFFECTS = (
    "ATOMICROWS_BUNDLE_SHA256",
    "SHA_AUTHORITY",
    "FREEZE_AUTHORITY",
    "PR100_SHA_FREEZE_AUTHORITY",
    "PR101_FINAL_READINESS_GATE",
    "RUNTIME_DASHBOARD_SERVICE",
    "DASHBOARD_RUNTIME_UI",
    "TELEGRAM_RUNTIME",
    "OWNER_APPROVAL_DECISION_EXECUTION",
    "OWNER_APPROVAL_RECEIPT",
    "OWNER_OVERRIDE_RECEIPT",
    "LIVE_PROMOTION",
    "CANARY_ELIGIBILITY",
    "ORDER_AUTHORITY",
    "ORDER_SUBMISSION_CANCELLATION_REDUCTION_OR_CLOSE",
    "LIVE_ROUTING",
    "EXTERNAL_SOURCE_RETRIEVAL",
    "SOURCE_ACCEPTANCE",
    "ACCEPTED_SOURCE_PACKETS",
    "CONNECTOR_SEMANTIC_BINDING",
    "PRIVATE_STATE_FETCH",
    "RUNTIME_CASH_RECEIPT",
    "REPLAY_PAPER_EXECUTION",
    "OPTIMIZER_EXECUTION",
    "QUANTUM_BACKEND_OR_SIMULATOR_EXECUTION",
    "PROFIT_EVIDENCE",
    "LATENCY_EVIDENCE",
    "QUANTUM_ADVANTAGE_EVIDENCE",
)


@dataclass(frozen=True)
class SourceSummary:
    source_files: dict[str, dict[str, Any]]
    ordered_paths: tuple[str, ...]
    exact_rows: tuple[dict[str, Any], ...]
    blueprints: tuple[dict[str, Any], ...]
    duplicate_source_file_ids: tuple[str, ...]
    duplicate_row_family_ids: tuple[str, ...]
    duplicate_blueprint_ids: tuple[str, ...]
    duplicate_row_ids: tuple[str, ...]
    unknown_source_files: tuple[str, ...]
    missing_source_files: tuple[str, ...]
    nondeterministic_order_reasons: tuple[str, ...]
    quantum_metadata_refs_found: tuple[str, ...]


@dataclass(frozen=True)
class BundleInputs:
    builder_config: dict[str, Any]
    pr97_plan: dict[str, Any]
    pr98_source_file_set: dict[str, Any]
    pr98_report: dict[str, Any]
    source_summary: SourceSummary


def _resolve(root: pathlib.Path, path: pathlib.Path) -> pathlib.Path:
    return path if path.is_absolute() else root / path


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _duplicate_values(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return tuple(sorted(duplicates))


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def load_yaml(path: pathlib.Path) -> dict[str, Any]:
    value = pr97_gate.load_yaml(path)
    if not isinstance(value, dict):
        raise ValueError(f"YAML root must be an object: {path}")
    return value


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_json_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def expected_source_paths(pr97_plan: dict[str, Any]) -> tuple[str, ...]:
    return tuple(path.as_posix() for path in pr98_gate._source_file_paths_from_pr97(pr97_plan))


def discover_source_files(repo_root: pathlib.Path) -> tuple[str, ...]:
    source_dir = pathlib.Path("docs") / "master_plan" / "atomic_rows" / "pr98_row_family_sources"
    source_dir_abs = _resolve(repo_root, source_dir)
    if not source_dir_abs.exists():
        return ()
    return tuple(
        sorted(
            path.relative_to(repo_root).as_posix()
            for path in source_dir_abs.glob("*.source.jsonl")
        )
    )


def _record_identifier(record: dict[str, Any]) -> str:
    for key in ("row_id", "atomic_row_id", "atomic_parameter_row_id", "row_source_id"):
        value = record.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _is_exact_row_record(record: dict[str, Any]) -> bool:
    if record.get("record_class") == "SOURCE_ROW_BLUEPRINT_NOT_EXACT_FINAL_ROW":
        return False
    exact_flags = (
        "exact_row_created_flag",
        "exact_final_row_created_flag",
        "final_bundle_membership_created_flag",
    )
    return any(record.get(field) is True for field in exact_flags) or bool(
        _record_identifier(record)
    )


def summarize_source_files(
    *,
    repo_root: pathlib.Path,
    pr97_plan: dict[str, Any],
    source_files: dict[str, dict[str, Any]],
) -> SourceSummary:
    expected_paths = expected_source_paths(pr97_plan)
    discovered_paths = discover_source_files(repo_root)
    missing = tuple(path for path in expected_paths if path not in source_files)
    unknown = tuple(path for path in discovered_paths if path not in set(expected_paths))
    ordered_files = [source_files[path] for path in expected_paths if path in source_files]

    exact_rows: list[dict[str, Any]] = []
    blueprints: list[dict[str, Any]] = []
    source_file_ids: list[str] = []
    row_family_ids: list[str] = []
    blueprint_ids: list[str] = []
    row_ids: list[str] = []
    quantum_refs: set[str] = set()
    nondeterministic_order_reasons: list[str] = []

    source_orders = [item.get("canonical_order") for item in ordered_files]
    if source_orders != list(range(1, len(source_orders) + 1)):
        nondeterministic_order_reasons.append("SOURCE_FILE_ORDER_NOT_DETERMINISTIC")

    for source_file in ordered_files:
        source_file_ids.append(str(source_file.get("source_file_id")))
        row_family_ids.append(str(source_file.get("row_family_id")))
        records = _list_of_mappings(source_file.get("source_records_or_blueprints"))
        record_orders = [record.get("canonical_order") for record in records]
        if record_orders != list(range(1, len(record_orders) + 1)):
            nondeterministic_order_reasons.append(
                f"{source_file.get('row_family_id')}:RECORD_ORDER_NOT_DETERMINISTIC"
            )
        for record in records:
            for ref in record.get("quantum_metadata_refs") or []:
                if isinstance(ref, str):
                    quantum_refs.add(ref)
            if _is_exact_row_record(record):
                exact_rows.append(record)
                row_id = _record_identifier(record)
                if row_id:
                    row_ids.append(row_id)
            else:
                blueprints.append(record)
                blueprint_id = record.get("blueprint_id")
                if isinstance(blueprint_id, str):
                    blueprint_ids.append(blueprint_id)

    return SourceSummary(
        source_files=source_files,
        ordered_paths=expected_paths,
        exact_rows=tuple(exact_rows),
        blueprints=tuple(blueprints),
        duplicate_source_file_ids=_duplicate_values(source_file_ids),
        duplicate_row_family_ids=_duplicate_values(row_family_ids),
        duplicate_blueprint_ids=_duplicate_values(blueprint_ids),
        duplicate_row_ids=_duplicate_values(row_ids),
        unknown_source_files=unknown,
        missing_source_files=missing,
        nondeterministic_order_reasons=tuple(sorted(set(nondeterministic_order_reasons))),
        quantum_metadata_refs_found=tuple(sorted(quantum_refs)),
    )


def load_bundle_inputs(
    *,
    repo_root: pathlib.Path,
    builder_config_path: pathlib.Path = DEFAULT_BUILDER_CONFIG,
) -> tuple[BundleInputs | None, list[str]]:
    failures: list[str] = []
    try:
        builder_config = load_yaml(_resolve(repo_root, builder_config_path))
    except Exception as exc:
        return None, [f"builder config invalid: {builder_config_path.as_posix()}: {exc}"]
    try:
        pr97_plan = pr97_gate.load_yaml(_resolve(repo_root, PR97_PLAN_PATH))
    except Exception as exc:
        return None, [f"PR97 expansion plan invalid: {PR97_PLAN_PATH.as_posix()}: {exc}"]
    try:
        pr98_source_file_set = load_yaml(_resolve(repo_root, PR98_SOURCE_FILE_SET_PATH))
    except Exception as exc:
        return None, [f"PR98 source-file set invalid: {PR98_SOURCE_FILE_SET_PATH.as_posix()}: {exc}"]
    try:
        pr98_report = load_json(_resolve(repo_root, PR98_REPORT_PATH))
    except Exception as exc:
        return None, [f"PR98 generated report invalid: {PR98_REPORT_PATH.as_posix()}: {exc}"]

    source_files, source_failures = pr98_gate.load_source_files(repo_root, pr97_plan)
    failures.extend(source_failures)
    source_summary = summarize_source_files(
        repo_root=repo_root,
        pr97_plan=pr97_plan,
        source_files=source_files,
    )
    return (
        BundleInputs(
            builder_config=builder_config,
            pr97_plan=pr97_plan,
            pr98_source_file_set=pr98_source_file_set,
            pr98_report=pr98_report,
            source_summary=source_summary,
        ),
        failures,
    )


def build_block_reason_codes(inputs: BundleInputs) -> tuple[str, ...]:
    summary = inputs.source_summary
    target_total = int(inputs.pr97_plan.get("target_total_row_count") or 0)
    reasons: list[str] = []
    if len(summary.exact_rows) == 0:
        reasons.append(BUILD_BLOCKED_REASON_EXACT_SOURCE_ROWS)
    if len(summary.blueprints) > 0 and len(summary.exact_rows) == 0:
        reasons.append(BUILD_BLOCKED_REASON_BLUEPRINTS_ONLY)
    if inputs.builder_config.get("owner_approval_status") != "APPROVED_EXACT_SOURCE_ROWS_FOR_BUNDLE_MATERIALIZATION":
        reasons.append(BUILD_BLOCKED_REASON_OWNER_APPROVAL)
    if len(summary.exact_rows) != target_total:
        reasons.append(BUILD_BLOCKED_REASON_TARGET_NOT_FEASIBLE)
    if summary.missing_source_files:
        reasons.append("ATOMICROWS_BUNDLE_BUILD_BLOCKED_MISSING_SOURCE_FILES")
    if summary.unknown_source_files:
        reasons.append("ATOMICROWS_BUNDLE_BUILD_BLOCKED_UNKNOWN_SOURCE_FILES")
    if summary.duplicate_source_file_ids:
        reasons.append("ATOMICROWS_BUNDLE_BUILD_BLOCKED_DUPLICATE_SOURCE_FILE_IDS")
    if summary.duplicate_row_family_ids:
        reasons.append("ATOMICROWS_BUNDLE_BUILD_BLOCKED_DUPLICATE_ROW_FAMILY_OWNERSHIP")
    if summary.duplicate_blueprint_ids:
        reasons.append("ATOMICROWS_BUNDLE_BUILD_BLOCKED_DUPLICATE_BLUEPRINT_IDS")
    if summary.duplicate_row_ids:
        reasons.append("ATOMICROWS_BUNDLE_BUILD_BLOCKED_DUPLICATE_ROW_IDS")
    if summary.nondeterministic_order_reasons:
        reasons.append("ATOMICROWS_BUNDLE_BUILD_BLOCKED_NONDETERMINISTIC_ORDERING")
    return tuple(dict.fromkeys(reasons))


def build_allowed(inputs: BundleInputs) -> bool:
    return len(build_block_reason_codes(inputs)) == 0


def source_file_report_entries(inputs: BundleInputs) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in inputs.source_summary.ordered_paths:
        source_file = inputs.source_summary.source_files.get(path, {})
        entries.append(
            {
                "canonical_order": source_file.get("canonical_order"),
                "declared_source_blueprint_count": source_file.get(
                    "declared_source_blueprint_count"
                ),
                "declared_source_record_count": source_file.get(
                    "declared_source_record_count"
                ),
                "exact_row_count_created_by_pr98_flag": source_file.get(
                    "exact_row_count_created_by_pr98_flag"
                ),
                "planned_path": path,
                "quantum_relevance_class": source_file.get("quantum_relevance_class"),
                "row_family_id": source_file.get("row_family_id"),
                "source_file_exists": bool(source_file),
                "source_file_id": source_file.get("source_file_id"),
                "source_file_mode": source_file.get("source_file_mode"),
            }
        )
    return entries


def build_dry_run_report(
    *,
    inputs: BundleInputs,
    repo_root: pathlib.Path,
    report_path: pathlib.Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    summary = inputs.source_summary
    block_reasons = build_block_reason_codes(inputs)
    allowed = not block_reasons
    target_total = inputs.pr97_plan.get("target_total_row_count")
    source_file_count_expected = len(summary.ordered_paths)
    source_file_count_found = len(summary.source_files)
    source_file_coverage_complete = (
        source_file_count_expected == source_file_count_found
        and not summary.missing_source_files
        and not summary.unknown_source_files
    )

    assembly_gate = {
        "gate_id": ASSEMBLY_GATE_ID,
        "gate_version": ASSEMBLY_GATE_VERSION,
        "canonical_order": "SOURCE_FILE_CANONICAL_ORDER_THEN_ROW_CANONICAL_ORDER",
        "build_allowed_flag": allowed,
        "build_blocked_flag": not allowed,
        "build_block_reason_codes": list(block_reasons),
        "exact_source_rows_available_flag": len(summary.exact_rows) == int(target_total or 0),
        "blueprint_only_sources_detected_flag": (
            len(summary.blueprints) > 0 and len(summary.exact_rows) == 0
        ),
        "source_file_coverage_complete_flag": source_file_coverage_complete,
        "duplicate_source_file_ids_found_flag": bool(summary.duplicate_source_file_ids),
        "duplicate_row_family_ownership_found_flag": bool(summary.duplicate_row_family_ids),
        "duplicate_row_ids_found_flag": bool(summary.duplicate_row_ids),
        "deterministic_ordering_verified_flag": not summary.nondeterministic_order_reasons,
        "no_fabrication_verified_flag": len(summary.exact_rows) == 0,
        "bundle_file_created_flag": False,
        "no_bundle_sha_created_flag": True,
        "no_freeze_authority_created_flag": True,
        "no_final_readiness_created_flag": True,
        "no_runtime_live_order_authority_created_flag": True,
        "no_source_acceptance_created_flag": True,
        "no_connector_semantic_created_flag": True,
        "no_profit_or_latency_evidence_created_flag": True,
        "no_quantum_backend_execution_created_flag": True,
    }
    source_file_consumer_contract = {
        "contract_id": "ATOMICROWS_ROW_FAMILY_SOURCE_FILE_CONSUMER_CONTRACT",
        "expected_source_file_count": source_file_count_expected,
        "found_source_file_count": source_file_count_found,
        "all_expected_pr98_source_files_present_flag": not summary.missing_source_files,
        "no_unknown_row_family_source_files_flag": not summary.unknown_source_files,
        "duplicate_source_file_ids_found": list(summary.duplicate_source_file_ids),
        "duplicate_row_family_ownership_found": list(summary.duplicate_row_family_ids),
        "duplicate_blueprint_ids_found": list(summary.duplicate_blueprint_ids),
        "source_required_repository_convention_only_flag": True,
        "source_blueprints_remain_blueprints_flag": len(summary.exact_rows) == 0,
        "exact_source_rows_required_for_actual_bundle_output_flag": True,
        "source_files": source_file_report_entries(inputs),
    }
    output_contract = {
        "contract_id": "ATOMICROWS_BUNDLE_JSONL_OUTPUT_CONTRACT",
        "canonical_output_path": CANONICAL_BUNDLE_JSONL.as_posix(),
        "output_creation_allowed_only_if_assembly_gate_passes_flag": True,
        "current_output_creation_allowed_flag": allowed,
        "jsonl_line_ordering": "SOURCE_FILE_CANONICAL_ORDER_THEN_ROW_CANONICAL_ORDER",
        "row_id_ordering": "DETERMINISTIC_ASCENDING_WITHIN_SOURCE_FILE",
        "per_row_schema_validation_required_flag": True,
        "duplicate_id_blocking_flag": True,
        "source_row_blueprint_materialization_allowed_flag": False,
        "bundle_sha_creation_allowed_flag": False,
        "final_readiness_claim_allowed_flag": False,
    }
    quantum_metadata_validation = {
        "validation_id": "ATOMICROWS_BUNDLE_BUILDER_QUANTUM_METADATA_VALIDATION",
        "static_metadata_only_flag": True,
        "quantum_metadata_refs_found": list(summary.quantum_metadata_refs_found),
        "required_static_metadata_refs": list(QUANTUM_METADATA_REFS),
        "qubo_ising_metadata_remains_metadata_flag": True,
        "qaoa_vqe_annealing_metadata_remains_metadata_flag": True,
        "quantum_portfolio_hybrid_metadata_remains_metadata_flag": True,
        "quantum_execution_fields_true_flag": False,
        "quantum_advantage_claim_created_flag": False,
        "forbidden_quantum_execution_effects": list(FORBIDDEN_QUANTUM_EFFECTS),
    }
    forbidden_artifact_boundary = {
        "boundary_id": "ATOMICROWS_BUNDLE_BUILDER_FORBIDDEN_ARTIFACT_BOUNDARY",
        "bundle_jsonl_blocked_unless_path_a_gate_passes_flag": True,
        "atomicrows_bundle_jsonl_exists": _resolve(repo_root, CANONICAL_BUNDLE_JSONL).exists(),
        "atomicrows_bundle_sha256_exists": _resolve(repo_root, CANONICAL_BUNDLE_SHA256).exists(),
        "hash_files_created_flag": False,
        "sha_authority_created_flag": False,
        "freeze_authority_created_flag": False,
        "pr100_sha_freeze_authority_created_flag": False,
        "pr101_final_readiness_created_flag": False,
        "runtime_live_order_source_connector_profit_quantum_backend_effect_created_flag": False,
        "blocked_effects": list(FORBIDDEN_EFFECTS),
    }

    return {
        "report_id": REPORT_ID,
        "report_version": REPORT_VERSION,
        "generated_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "validation_marker": SUCCESS_MARKER,
        "builder_id": BUILDER_ID,
        "builder_version": BUILDER_VERSION,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "roadmap_pr_label": ROADMAP_PR_LABEL,
        "roadmap_delivery_label": ROADMAP_DELIVERY_LABEL,
        "authority_class": AUTHORITY_CLASS,
        "static_tooling_only_flag": True,
        "build_path_decision": PATH_DECISION,
        "deterministic_builder_framework_created_flag": True,
        "bundle_materialization_attempted_flag": False,
        "bundle_materialization_allowed_flag": allowed,
        "bundle_file_created_flag": False,
        "bundle_jsonl_path": CANONICAL_BUNDLE_JSONL.as_posix(),
        "bundle_sha_created_flag": False,
        "bundle_sha_path": CANONICAL_BUNDLE_SHA256.as_posix(),
        "sha_authority_created_flag": False,
        "freeze_authority_created_flag": False,
        "final_readiness_created_flag": False,
        "consumes_pr97_expansion_plan_flag": True,
        "consumes_pr98_source_files_flag": True,
        "pr97_plan_path": PR97_PLAN_PATH.as_posix(),
        "pr97_report_path": PR97_REPORT_PATH.as_posix(),
        "pr98_source_file_set_path": PR98_SOURCE_FILE_SET_PATH.as_posix(),
        "pr98_report_path": PR98_REPORT_PATH.as_posix(),
        "source_file_count_expected": source_file_count_expected,
        "source_file_count_found": source_file_count_found,
        "source_file_count": source_file_count_found,
        "source_blueprint_count": len(summary.blueprints),
        "exact_source_rows_required_flag": True,
        "exact_source_rows_available_flag": len(summary.exact_rows) == int(target_total or 0),
        "exact_source_rows_available_count": len(summary.exact_rows),
        "exact_source_rows_found_count": len(summary.exact_rows),
        "source_blueprints_found_count": len(summary.blueprints),
        "blueprint_only_source_files_detected_flag": (
            len(summary.blueprints) > 0 and len(summary.exact_rows) == 0
        ),
        "blueprint_materialization_allowed_flag": False,
        "target_total_row_count": target_total,
        "target_total_row_count_authority": inputs.pr97_plan.get(
            "target_total_row_count_authority"
        ),
        "target_total_row_count_planning_authority_only_flag": True,
        "owner_approval_required_before_bundle_materialization_flag": True,
        "owner_approval_status": inputs.builder_config.get("owner_approval_status"),
        "build_allowed_flag": allowed,
        "build_blocked_flag": not allowed,
        "blocked_reason_codes": list(block_reasons),
        "deterministic_order_hash_or_digest": None,
        "deterministic_order_hash_or_digest_authority": "NOT_USED_NO_HASH_NO_SHA_FREEZE_AUTHORITY",
        "future_pr100_sha_freeze_required_flag": True,
        "future_pr101_final_readiness_required_flag": True,
        "source_file_consumer_contract": source_file_consumer_contract,
        "assembly_gate": assembly_gate,
        "output_contract": output_contract,
        "quantum_metadata_validation": quantum_metadata_validation,
        "forbidden_artifact_boundary": forbidden_artifact_boundary,
        "blocked_effects": list(FORBIDDEN_EFFECTS),
        "future_consumer_notes": (
            "PR99 creates the deterministic builder framework and dry-run gate only. "
            "Because PR98 source files contain owner-review-required blueprints and zero exact "
            "source rows, bundle materialization remains blocked until owner-approved exact "
            "source-row records exist and a future gate authorizes assembly."
        ),
        "report_path": report_path.as_posix(),
    }


def validate_report_determinism(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if report != json.loads(serialize_report(report)):
        failures.append("dry-run report is not JSON serialization stable")
    second = json.loads(serialize_report(copy.deepcopy(report)))
    if report != second:
        failures.append("dry-run report is not deterministic across copies")
    return failures


def materialize_bundle_if_allowed(*, inputs: BundleInputs, repo_root: pathlib.Path) -> list[str]:
    if not build_allowed(inputs):
        return list(build_block_reason_codes(inputs))
    output = _resolve(repo_root, CANONICAL_BUNDLE_JSONL)
    rows = sorted(
        inputs.source_summary.exact_rows,
        key=lambda record: (
            str(record.get("row_family_id") or ""),
            int(record.get("canonical_order") or 0),
            _record_identifier(record),
        ),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )
    return []


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run deterministic AtomicRows bundle assembly gate."
    )
    parser.add_argument("--repo-root", type=pathlib.Path, default=pathlib.Path("."))
    parser.add_argument("--config", type=pathlib.Path, default=DEFAULT_BUILDER_CONFIG)
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_REPORT)
    parser.add_argument("--dry-run", action="store_true", help="Validate and write a dry-run report.")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate inputs and report determinism without bundle materialization.",
    )
    parser.add_argument(
        "--materialize",
        action="store_true",
        help="Attempt bundle materialization only if the assembly gate passes.",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    inputs, failures = load_bundle_inputs(repo_root=repo_root, builder_config_path=args.config)
    if inputs is None:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    report = build_dry_run_report(inputs=inputs, repo_root=repo_root, report_path=args.out)
    failures.extend(validate_report_determinism(report))

    if args.materialize:
        materialize_failures = materialize_bundle_if_allowed(inputs=inputs, repo_root=repo_root)
        failures.extend(materialize_failures)
        if materialize_failures:
            write_json_report(report, _resolve(repo_root, args.out))
            for failure in materialize_failures:
                print(failure, file=sys.stderr)
            return 1
    elif not args.validate_only:
        write_json_report(report, _resolve(repo_root, args.out))

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
