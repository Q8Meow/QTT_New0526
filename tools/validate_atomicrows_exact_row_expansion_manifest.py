#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import copy
from dataclasses import dataclass
import json
import pathlib
import subprocess
import sys
from typing import Any, Iterable, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import validate_atomicrows_bundle_builder_deterministic_assembly_gate as pr99_gate  # noqa: E402
from tools import validate_atomicrows_bundle_row_family_source_files as pr98_gate  # noqa: E402
from tools import validate_atomicrows_bundle_sha_freeze_authority_gate as pr100_gate  # noqa: E402
from tools import validate_atomicrows_exact_row_authority_classifier_bridge as bridge_gate  # noqa: E402
from tools import validate_atomicrows_full_bundle_row_expansion_plan as pr97_gate  # noqa: E402
from tools import atomicrows_repair_pr_d_materialization_sentinel as post_d_sentinel  # noqa: E402
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)


DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_exact_row_expansion_manifest.schema.json"
)
DEFAULT_CONFIG = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsExactRowExpansionManifest.yaml"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsExactRowExpansionManifest.report.json"
)

REPORT_TYPE = "ATOMICROWS_EXACT_ROW_EXPANSION_MANIFEST_REPORT"
ARTIFACT_ID = "ATOMICROWS_EXACT_ROW_EXPANSION_MANIFEST"
ARTIFACT_VERSION = "v1"
REPAIR_SCOPE = "ATOMICROWS_4183_EXACT_ROW_EXPANSION_MANIFEST"
AUTHORITY_CLASS = "STATIC_REPAIR_MANIFEST_NOT_EXACT_ROWS_NOT_BUNDLE_NOT_SHA_NOT_FREEZE"
TARGET_TOTAL_ROW_COUNT = 4183
FAMILY_COUNT_TOTAL = 15
SUCCESS_MARKER = "QTT_ATOMICROWS_EXACT_ROW_EXPANSION_MANIFEST_OK"
FAILURE_MARKER = "QTT_ATOMICROWS_EXACT_ROW_EXPANSION_MANIFEST_FAILED"

EXACT_DISTRIBUTION_READY_STATE = "EXACT_DISTRIBUTION_READY_NO_ROWS_CREATED"
BLOCKED_STATE = "BLOCKED_PENDING_OWNER_EXACT_DISTRIBUTION"
PASS_EXACT_DISTRIBUTION_READY = "PASS_EXACT_DISTRIBUTION_READY"
PASS_OWNER_APPROVED_DISTRIBUTION_READY = "PASS_OWNER_APPROVED_DISTRIBUTION_READY"
PASS_BLOCKED_EXPECTED = "PASS_BLOCKED_EXPECTED"
DERIVED_COUNT_AUTHORITY = "DERIVED_FROM_PR97_EXPLICIT_DISTRIBUTION"
OWNER_APPROVED_COUNT_AUTHORITY = "OWNER_APPROVED_EXACT_15_FAMILY_COUNT_DISTRIBUTION"
OWNER_APPROVAL_REQUIRED_AUTHORITY = "OWNER_APPROVAL_REQUIRED"
OWNER_DISTRIBUTION_DECISION = "EXACT_15_FAMILY_ROW_COUNT_DISTRIBUTION"
NEXT_REQUIRED_REPAIR_PR = "ATOMICROWS_EXACT_ROW_GENERATOR_DRY_RUN"

PR97_PLAN = pr97_gate.DEFAULT_PRODUCTION_PLAN
PR97_REPORT = pr97_gate.DEFAULT_REPORT
PR97_SCHEMA = pr97_gate.DEFAULT_SCHEMA
PR98_CONFIG = pr98_gate.DEFAULT_SOURCE_FILE_SET
PR98_REPORT = pr98_gate.DEFAULT_REPORT
PR99_CONFIG = pr99_gate.DEFAULT_BUILDER_CONFIG
PR99_REPORT = pr99_gate.DEFAULT_REPORT
PR100_CONFIG = pr100_gate.DEFAULT_CONFIG
PR100_REPORT = pr100_gate.DEFAULT_REPORT
BRIDGE_CONFIG = bridge_gate.DEFAULT_CONFIG
BRIDGE_REPORT = bridge_gate.DEFAULT_REPORT
OWNER_APPROVED_DISTRIBUTION_CONFIG = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsOwnerApprovedExact15FamilyCountDistribution.yaml"
)

MASTER_PLAN_CURRENT = pr97_gate.MASTER_PLAN_CURRENT
CANONICAL_BUNDLE_JSONL = pr97_gate.CANONICAL_BUNDLE_JSONL
CANONICAL_BUNDLE_SHA256 = pr97_gate.CANONICAL_BUNDLE_SHA256
EXACT_ROW_SOURCES_DIR = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "exact_row_sources"
)
PR98_SOURCE_DIR = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "pr98_row_family_sources"
)

REQUIRED_FAMILY_SLUGS = (
    "001_signal_features",
    "002_scoring_ranking",
    "003_normalization_calibration",
    "004_risk_control",
    "005_execution_connector_boundary",
    "006_capital_sizing_cash",
    "007_latency_routing",
    "008_error_guard_fail_closed",
    "009_lifecycle_agent_binding",
    "010_source_evidence_connector_semantic",
    "011_replay_paper_validation",
    "012_quantum_advisory_optimization",
    "013_quantum_qubo_ising_metadata",
    "014_quantum_qaoa_vqe_annealing_metadata",
    "015_quantum_portfolio_hybrid_comparator",
)
REQUIRED_FAMILY_IDS = tuple(
    "AR_FAMILY_" + slug.upper() for slug in REQUIRED_FAMILY_SLUGS
)
REQUIRED_SOURCE_BLUEPRINT_FILES = tuple(
    f"docs/master_plan/atomic_rows/pr98_row_family_sources/{slug}.source.jsonl"
    for slug in REQUIRED_FAMILY_SLUGS
)
REQUIRED_EXACT_ROW_SOURCE_FILES = tuple(
    f"docs/master_plan/atomic_rows/exact_row_sources/{slug}.exact_rows.jsonl"
    for slug in REQUIRED_FAMILY_SLUGS
)
ALLOWED_SUBFAMILY_CLASSES = (
    "PARAMETER_DEFINITION",
    "ALGORITHM_DEFINITION",
    "AGENT_ACCESS_POLICY",
    "FAMILY_ACCESS_POLICY",
    "SCORING_INPUT",
    "RANKING_INPUT",
    "OPTIMIZER_INPUT",
    "RISK_CONTROL",
    "EXECUTION_BOUNDARY",
    "CAPITAL_CONTROL",
    "LATENCY_CONTROL",
    "ERROR_GUARD",
    "SOURCE_EVIDENCE_REQUIREMENT",
    "REPLAY_PAPER_REQUIREMENT",
    "QUANTUM_METADATA",
    "QUANTUM_BACKEND_REQUIREMENT",
    "OWNER_APPROVAL_REQUIREMENT",
)
FUTURE_EXACT_ROW_REQUIRED_FIELDS = (
    "family_slug",
    "subfamily_class",
    "row_class",
    "row_kind",
    "parameter_or_algorithm_scope",
    "agent_access_scope",
    "authority_class",
    "activation_state",
)
REQUIRED_POLICY_ROW_KINDS = (
    "AGENT_ROW_ACCESS_POLICY",
    "AGENT_FAMILY_ACCESS_POLICY",
    "AGENT_PARAMETER_ACCESS_POLICY",
    "AGENT_ALGORITHM_ACCESS_POLICY",
    "AGENT_QUANTUM_ROW_ACCESS_POLICY",
    "AGENT_LIVE_MODE_ACCESS_POLICY",
)
NO_CREATION_FALSE_FIELDS = (
    "may_create_exact_rows_now",
    "may_create_bundle_now",
    "may_create_sha_now",
    "may_create_freeze_now",
    "may_create_final_readiness_now",
)
QUANTUM_FALSE_FIELDS = (
    "may_execute_quantum_backend_now",
    "may_execute_qubo_solving_now",
    "may_execute_ising_solving_now",
    "may_execute_qaoa_now",
    "may_execute_vqe_now",
    "may_execute_annealing_now",
    "may_execute_quantum_portfolio_optimization_now",
    "may_claim_quantum_advantage_now",
)
AGENT_DENY_FALSE_FIELDS = (
    "may_grant_agent_access_now",
    "row_existence_grants_access",
    "family_membership_grants_access",
    "quantum_applicability_grants_access",
    "owner_quantum_priority_grants_access",
    "replay_paper_eligibility_grants_live_access",
    "static_selection_eligibility_grants_order_authority",
    "direct_order_authority_allowed_default",
    "direct_quantum_order_authority_allowed_default",
)
NO_AUTHORITY_FALSE_FIELDS = (
    "runtime_live_order_authority_created",
    "source_fact_authority_created",
    "connector_semantic_authority_created",
    "profit_evidence_created",
    "latency_evidence_created",
    "execution_superiority_evidence_created",
    "optimizer_execution_created",
    "quantum_backend_authority_created",
    "quantum_advantage_evidence_created",
    "specific_agent_family_assignments_created",
    "specific_agent_row_assignments_created",
)
PR97_EXPLICIT_COUNT_KEYS = (
    "target_row_count",
    "exact_row_count",
    "row_count",
    "allocated_row_count",
    "planned_row_count",
)

FAMILY_REQUIRED_SUBFAMILIES = {
    "002_scoring_ranking": ("OPTIMIZER_INPUT", "SCORING_INPUT", "RANKING_INPUT"),
    "004_risk_control": ("RISK_CONTROL",),
    "005_execution_connector_boundary": ("EXECUTION_BOUNDARY",),
    "006_capital_sizing_cash": ("CAPITAL_CONTROL",),
    "007_latency_routing": ("LATENCY_CONTROL",),
    "008_error_guard_fail_closed": ("ERROR_GUARD",),
    "009_lifecycle_agent_binding": ("AGENT_ACCESS_POLICY", "FAMILY_ACCESS_POLICY"),
    "012_quantum_advisory_optimization": (
        "QUANTUM_METADATA",
        "OPTIMIZER_INPUT",
        "SCORING_INPUT",
        "RANKING_INPUT",
    ),
    "013_quantum_qubo_ising_metadata": (
        "QUANTUM_METADATA",
        "QUANTUM_BACKEND_REQUIREMENT",
        "OPTIMIZER_INPUT",
        "SCORING_INPUT",
        "RANKING_INPUT",
    ),
    "014_quantum_qaoa_vqe_annealing_metadata": (
        "QUANTUM_METADATA",
        "QUANTUM_BACKEND_REQUIREMENT",
        "OPTIMIZER_INPUT",
        "SCORING_INPUT",
        "RANKING_INPUT",
    ),
    "015_quantum_portfolio_hybrid_comparator": (
        "QUANTUM_METADATA",
        "QUANTUM_BACKEND_REQUIREMENT",
        "OPTIMIZER_INPUT",
        "SCORING_INPUT",
        "RANKING_INPUT",
    ),
}
QUANTUM_RELEVANCE_BY_FAMILY = {
    "012_quantum_advisory_optimization": "QUANTUM_ADVISORY_STATIC_METADATA",
    "013_quantum_qubo_ising_metadata": "QUBO_ISING_COMPATIBLE_STATIC_METADATA",
    "014_quantum_qaoa_vqe_annealing_metadata": (
        "QAOA_VQE_ANNEALING_COMPATIBLE_STATIC_METADATA"
    ),
    "015_quantum_portfolio_hybrid_comparator": (
        "QUANTUM_PORTFOLIO_HYBRID_COMPARATOR_STATIC_METADATA"
    ),
}
FORBIDDEN_STATIC_IMPORTS = (
    "ccxt",
    "requests",
    "httpx",
    "aiohttp",
    "urllib",
    "qiskit",
    "dwave",
    "braket",
    "cirq",
    "pennylane",
)
FORBIDDEN_STATIC_CALLS = (
    "sha256",
    "run_replay",
    "run_paper",
    "execute_optimizer",
    "execute_quantum",
    "submit_order",
    "fetch_balance",
    "fetch_order",
    "create_order",
)


@dataclass(frozen=True)
class DistributionDerivation:
    state: str
    validation_result: str
    source: str
    source_pointer: str | None
    owner_required_decision: str | None
    counts: dict[str, int] | None
    ranges: dict[str, tuple[int, int]] | None
    family_counts_sum: int | None
    row_ranges_contiguous: bool | None
    final_row_index: int | None
    explicit_distribution_found: bool
    failures: tuple[str, ...] = ()


@dataclass(frozen=True)
class UpstreamState:
    pr97_expansion_plan_present: bool
    pr98_blueprints_are_not_exact_rows: bool
    pr99_path_b_remains_current_blocked_state: bool
    pr100_sha_freeze_gate_remains_blocked: bool
    repair_pr_a_bridge_present: bool
    repair_pr_a_bridge_preserved: bool
    forbidden_artifacts_absent: dict[str, bool]
    master_plan_unchanged: bool


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
    value = pr97_gate.load_yaml(path)
    if not isinstance(value, dict):
        raise ValueError(f"YAML root must be an object: {path}")
    return value


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_json_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def _load_json_checked(
    path: pathlib.Path, label: str
) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        return load_json(path), []
    except FileNotFoundError:
        return None, [f"{label} missing: {path.as_posix()}"]
    except (json.JSONDecodeError, ValueError) as exc:
        return None, [f"{label} invalid JSON: {path.as_posix()}: {exc}"]


def _load_yaml_checked(
    path: pathlib.Path, label: str
) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        return load_yaml(path), []
    except FileNotFoundError:
        return None, [f"{label} missing: {path.as_posix()}"]
    except Exception as exc:
        return None, [f"{label} invalid YAML: {path.as_posix()}: {exc}"]


def schema_subset_failures(
    payload: dict[str, Any], schema: dict[str, Any], label: str
) -> list[str]:
    return [f"{label} {failure}" for failure in validate_json_schema_subset(payload, schema)]


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _walk(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, f"{path}[{index}]")


def _slug_from_value(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().replace("\\", "/")
    if normalized in REQUIRED_FAMILY_SLUGS:
        return normalized
    if normalized.startswith("AR_FAMILY_"):
        suffix = normalized.removeprefix("AR_FAMILY_").lower()
        if suffix in REQUIRED_FAMILY_SLUGS:
            return suffix
    name = pathlib.PurePosixPath(normalized).name
    for suffix in (".exact_rows.jsonl", ".source.jsonl"):
        if name.endswith(suffix):
            slug = name[: -len(suffix)]
            if slug in REQUIRED_FAMILY_SLUGS:
                return slug
    return None


def _slug_from_mapping(entry: dict[str, Any]) -> str | None:
    for key in (
        "family_slug",
        "row_family_slug",
        "family",
        "family_id",
        "row_family_id",
        "planned_downstream_source_file_path",
        "source_file_path",
        "future_exact_row_source_file",
    ):
        slug = _slug_from_value(entry.get(key))
        if slug:
            return slug
    return None


def _entry_count(entry: dict[str, Any]) -> int | None:
    for key in PR97_EXPLICIT_COUNT_KEYS:
        value = entry.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return None


def _build_ranges(counts: dict[str, int]) -> dict[str, tuple[int, int]]:
    ranges: dict[str, tuple[int, int]] = {}
    start = 1
    for slug in REQUIRED_FAMILY_SLUGS:
        end = start + counts[slug] - 1
        ranges[slug] = (start, end)
        start = end + 1
    return ranges


def _validate_count_candidate(
    *,
    counts: dict[str, int],
    source_pointer: str,
    source: str = DERIVED_COUNT_AUTHORITY,
    validation_result: str = PASS_EXACT_DISTRIBUTION_READY,
) -> DistributionDerivation:
    failures: list[str] = []
    if tuple(counts) != REQUIRED_FAMILY_SLUGS:
        failures.append(f"{source_pointer}: exact distribution must use canonical family order")
    missing = sorted(set(REQUIRED_FAMILY_SLUGS) - set(counts))
    unexpected = sorted(set(counts) - set(REQUIRED_FAMILY_SLUGS))
    if missing:
        failures.append(f"{source_pointer}: missing families {', '.join(missing)}")
    if unexpected:
        failures.append(f"{source_pointer}: unexpected families {', '.join(unexpected)}")
    for slug, count in counts.items():
        if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
            failures.append(f"{source_pointer}.{slug}: count must be a positive integer")
    total = sum(count for count in counts.values() if isinstance(count, int))
    if total != TARGET_TOTAL_ROW_COUNT:
        failures.append(
            f"{source_pointer}: count sum must be {TARGET_TOTAL_ROW_COUNT}, got {total}"
        )

    ranges: dict[str, tuple[int, int]] | None = None
    final_row_index: int | None = None
    if not failures:
        ranges = _build_ranges(counts)
        final_row_index = ranges[REQUIRED_FAMILY_SLUGS[-1]][1]
        if final_row_index != TARGET_TOTAL_ROW_COUNT:
            failures.append(
                f"{source_pointer}: final row index must be {TARGET_TOTAL_ROW_COUNT}"
            )

    if failures:
        return DistributionDerivation(
            state="FAIL",
            validation_result="FAIL",
            source=source,
            source_pointer=source_pointer,
            owner_required_decision=None,
            counts=counts,
            ranges=ranges,
            family_counts_sum=total,
            row_ranges_contiguous=False,
            final_row_index=final_row_index,
            explicit_distribution_found=True,
            failures=tuple(failures),
        )

    return DistributionDerivation(
        state=EXACT_DISTRIBUTION_READY_STATE,
        validation_result=validation_result,
        source=source,
        source_pointer=source_pointer,
        owner_required_decision=None,
        counts=counts,
        ranges=ranges,
        family_counts_sum=TARGET_TOTAL_ROW_COUNT,
        row_ranges_contiguous=True,
        final_row_index=TARGET_TOTAL_ROW_COUNT,
        explicit_distribution_found=True,
    )


def _candidate_from_mapping(
    mapping: dict[str, Any], source_pointer: str
) -> DistributionDerivation | None:
    if all(slug in mapping for slug in REQUIRED_FAMILY_SLUGS):
        counts: dict[str, int] = {}
        for slug in REQUIRED_FAMILY_SLUGS:
            value = mapping.get(slug)
            if isinstance(value, int) and not isinstance(value, bool):
                counts[slug] = value
            else:
                return _validate_count_candidate(
                    counts={slug: value for slug, value in mapping.items() if slug in REQUIRED_FAMILY_SLUGS},
                    source_pointer=source_pointer,
                )
        return _validate_count_candidate(counts=counts, source_pointer=source_pointer)
    return None


def _candidate_from_list(
    entries: list[Any], source_pointer: str
) -> DistributionDerivation | None:
    if len(entries) != FAMILY_COUNT_TOTAL:
        return None
    counts: dict[str, int] = {}
    duplicate_slugs: set[str] = set()
    seen_slugs: set[str] = set()
    found_count_field = False
    for entry in entries:
        if not isinstance(entry, dict):
            return None
        slug = _slug_from_mapping(entry)
        count = _entry_count(entry)
        if slug is None:
            return None
        if count is None:
            return None
        found_count_field = True
        if slug in seen_slugs:
            duplicate_slugs.add(slug)
        seen_slugs.add(slug)
        counts[slug] = count
    if not found_count_field:
        return None
    candidate = _validate_count_candidate(counts=counts, source_pointer=source_pointer)
    if duplicate_slugs:
        failures = list(candidate.failures)
        failures.append(f"{source_pointer}: duplicate families {', '.join(sorted(duplicate_slugs))}")
        return DistributionDerivation(
            state="FAIL",
            validation_result="FAIL",
            source=candidate.source,
            source_pointer=candidate.source_pointer,
            owner_required_decision=None,
            counts=candidate.counts,
            ranges=candidate.ranges,
            family_counts_sum=candidate.family_counts_sum,
            row_ranges_contiguous=False,
            final_row_index=candidate.final_row_index,
            explicit_distribution_found=True,
            failures=tuple(failures),
        )
    return candidate


def derive_pr97_explicit_distribution(
    pr97_plan: dict[str, Any],
    pr97_report: dict[str, Any],
    pr97_schema: dict[str, Any] | None = None,
) -> DistributionDerivation:
    sources: list[tuple[str, dict[str, Any]]] = [
        (_as_posix(PR97_PLAN), pr97_plan),
        (_as_posix(PR97_REPORT), pr97_report),
    ]
    if pr97_schema is not None:
        sources.append((_as_posix(PR97_SCHEMA), pr97_schema))

    invalid_candidates: list[DistributionDerivation] = []
    for source_path, payload in sources:
        for path, value in _walk(payload):
            pointer = f"{source_path}:{path}"
            candidate: DistributionDerivation | None = None
            if isinstance(value, dict):
                candidate = _candidate_from_mapping(value, pointer)
            elif isinstance(value, list):
                candidate = _candidate_from_list(value, pointer)
            if candidate is None:
                continue
            if candidate.failures:
                invalid_candidates.append(candidate)
                continue
            return candidate

    if invalid_candidates:
        first = invalid_candidates[0]
        combined = []
        for candidate in invalid_candidates:
            combined.extend(candidate.failures)
        return DistributionDerivation(
            state="FAIL",
            validation_result="FAIL",
            source=DERIVED_COUNT_AUTHORITY,
            source_pointer=first.source_pointer,
            owner_required_decision=None,
            counts=first.counts,
            ranges=first.ranges,
            family_counts_sum=first.family_counts_sum,
            row_ranges_contiguous=False,
            final_row_index=first.final_row_index,
            explicit_distribution_found=True,
            failures=tuple(combined),
        )

    return DistributionDerivation(
        state=BLOCKED_STATE,
        validation_result=PASS_BLOCKED_EXPECTED,
        source=OWNER_APPROVAL_REQUIRED_AUTHORITY,
        source_pointer=None,
        owner_required_decision=OWNER_DISTRIBUTION_DECISION,
        counts=None,
        ranges=None,
        family_counts_sum=None,
        row_ranges_contiguous=None,
        final_row_index=None,
        explicit_distribution_found=False,
    )


def derive_owner_approved_distribution(repo_root: pathlib.Path) -> DistributionDerivation:
    config_path = repo_root / OWNER_APPROVED_DISTRIBUTION_CONFIG
    config, config_failures = _load_yaml_checked(
        config_path, "Owner-approved exact 15-family count distribution"
    )
    source_pointer = _as_posix(OWNER_APPROVED_DISTRIBUTION_CONFIG)
    if config is None:
        return DistributionDerivation(
            state=BLOCKED_STATE,
            validation_result=PASS_BLOCKED_EXPECTED,
            source=OWNER_APPROVAL_REQUIRED_AUTHORITY,
            source_pointer=None,
            owner_required_decision=OWNER_DISTRIBUTION_DECISION,
            counts=None,
            ranges=None,
            family_counts_sum=None,
            row_ranges_contiguous=None,
            final_row_index=None,
            explicit_distribution_found=False,
            failures=tuple(config_failures),
        )

    failures: list[str] = []
    if config.get("artifact_id") != "ATOMICROWS_OWNER_APPROVED_EXACT_15_FAMILY_COUNT_DISTRIBUTION":
        failures.append("owner distribution artifact_id is wrong")
    if config.get("approval_state") != "OWNER_APPROVED":
        failures.append("owner distribution approval_state must be OWNER_APPROVED")
    if config.get("owner_approval_scope") != "EXACT_15_FAMILY_ROW_COUNT_DISTRIBUTION_ONLY":
        failures.append("owner distribution approval scope is wrong")
    if config.get("target_total_row_count") != TARGET_TOTAL_ROW_COUNT:
        failures.append("owner distribution target_total_row_count must be 4183")
    if config.get("family_count_total") != FAMILY_COUNT_TOTAL:
        failures.append("owner distribution family_count_total must be 15")
    if config.get("owner_distribution_approval_created_by_this_pr") is not True:
        failures.append("owner distribution must record C0 owner approval")

    no_authority = config.get("not_authorized_by_this_approval")
    if not isinstance(no_authority, dict):
        failures.append("owner distribution not_authorized_by_this_approval must be an object")
        no_authority = {}
    for field in (
        "exact_rows_created",
        "exact_row_source_directory_created",
        "bundle_created",
        "sha_created",
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
        "agent_trading_authority_created",
        "agent_live_order_authority_created",
        "agent_quantum_backend_authority_created",
    ):
        if no_authority.get(field) is not False:
            failures.append(f"owner distribution {field} must be false")

    distribution = config.get("distribution")
    counts: dict[str, int] = {}
    if not isinstance(distribution, list):
        failures.append("owner distribution must include a distribution list")
    else:
        if len(distribution) != FAMILY_COUNT_TOTAL:
            failures.append("owner distribution must contain 15 entries")
        slugs: list[str] = []
        for index, entry in enumerate(distribution):
            if not isinstance(entry, dict):
                failures.append(f"owner distribution[{index}] must be an object")
                continue
            slug = entry.get("family_slug")
            count = entry.get("target_row_count")
            number = entry.get("family_number")
            expected_slug = REQUIRED_FAMILY_SLUGS[index] if index < FAMILY_COUNT_TOTAL else None
            if slug != expected_slug:
                failures.append(f"owner distribution[{index}] must use canonical slug order")
            if number != index + 1:
                failures.append(f"owner distribution[{index}].family_number must be {index + 1}")
            if isinstance(slug, str):
                slugs.append(slug)
            if isinstance(slug, str) and isinstance(count, int) and not isinstance(count, bool):
                counts[slug] = count
        if len(slugs) != len(set(slugs)):
            failures.append("owner distribution must not contain duplicate family slugs")
    if failures:
        return DistributionDerivation(
            state="FAIL",
            validation_result="FAIL",
            source=OWNER_APPROVED_COUNT_AUTHORITY,
            source_pointer=source_pointer,
            owner_required_decision=None,
            counts=counts or None,
            ranges=None,
            family_counts_sum=sum(counts.values()) if counts else None,
            row_ranges_contiguous=False,
            final_row_index=None,
            explicit_distribution_found=True,
            failures=tuple(failures),
        )

    candidate = _validate_count_candidate(
        counts=counts,
        source_pointer=source_pointer,
        source=OWNER_APPROVED_COUNT_AUTHORITY,
        validation_result=PASS_OWNER_APPROVED_DISTRIBUTION_READY,
    )
    if candidate.failures:
        return candidate

    if config.get("counts_sum") != candidate.family_counts_sum:
        failures.append("owner distribution counts_sum must match computed sum")
    quantum = config.get("quantum_forward_distribution")
    if not isinstance(quantum, dict) or quantum.get("quantum_family_total_rows") != 1103:
        failures.append("owner distribution quantum family total must be 1103")
    agent = config.get("agent_governance_distribution")
    if not isinstance(agent, dict) or agent.get("primary_agent_governance_family_rows") != 270:
        failures.append("owner distribution family 009 count must be 270")
    if failures:
        return DistributionDerivation(
            state="FAIL",
            validation_result="FAIL",
            source=OWNER_APPROVED_COUNT_AUTHORITY,
            source_pointer=source_pointer,
            owner_required_decision=None,
            counts=candidate.counts,
            ranges=candidate.ranges,
            family_counts_sum=candidate.family_counts_sum,
            row_ranges_contiguous=False,
            final_row_index=candidate.final_row_index,
            explicit_distribution_found=True,
            failures=tuple(failures),
        )
    return candidate


def derive_current_distribution(
    repo_root: pathlib.Path,
    pr97_plan: dict[str, Any],
    pr97_report: dict[str, Any],
    pr97_schema: dict[str, Any] | None = None,
) -> DistributionDerivation:
    pr97_derivation = derive_pr97_explicit_distribution(
        pr97_plan, pr97_report, pr97_schema
    )
    if pr97_derivation.failures or pr97_derivation.explicit_distribution_found:
        return pr97_derivation
    return derive_owner_approved_distribution(repo_root)


def _require_exact_list(
    failures: list[str], *, label: str, actual: Any, expected: Sequence[str]
) -> None:
    if actual != list(expected):
        failures.append(f"{label} must exactly match canonical order")


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


def validate_config_payload(
    config: dict[str, Any],
    schema: dict[str, Any],
    derivation: DistributionDerivation | None = None,
) -> list[str]:
    failures: list[str] = []
    failures.extend(schema_subset_failures(config, schema, "CONFIG"))

    _require_exact_list(
        failures,
        label="upstream_dependencies",
        actual=config.get("upstream_dependencies"),
        expected=(
            "AtomicRowsFullBundleRowExpansionPlan",
            "AtomicRowsBundleRowFamilySourceFiles",
            "AtomicRowsBundleBuilderDeterministicAssemblyGate",
            "AtomicRowsBundleShaFreezeAuthorityGate",
            "AtomicRowsExactRowAuthorityClassifierBridge",
        ),
    )
    _require_exact_list(
        failures,
        label="allowed_subfamily_classes",
        actual=config.get("allowed_subfamily_classes"),
        expected=ALLOWED_SUBFAMILY_CLASSES,
    )
    _require_exact_list(
        failures,
        label="future_exact_row_required_fields",
        actual=config.get("future_exact_row_required_fields"),
        expected=FUTURE_EXACT_ROW_REQUIRED_FIELDS,
    )
    _require_exact_list(
        failures,
        label="forbidden_current_outputs",
        actual=config.get("forbidden_current_outputs"),
        expected=(
            "docs/master_plan/atomic_rows/exact_row_sources/",
            "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
            "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256",
        ),
    )

    owner_process = config.get("owner_process_approval")
    if not isinstance(owner_process, dict):
        failures.append("owner_process_approval must be an object")
        owner_process = {}
    current_source = derivation.source if derivation is not None else None
    owner_approved_ready = current_source == OWNER_APPROVED_COUNT_AUTHORITY
    pr97_ready = current_source == DERIVED_COUNT_AUTHORITY
    blocked_for_owner = current_source == OWNER_APPROVAL_REQUIRED_AUTHORITY

    if owner_process.get("owner_approves_exact_counts_now") is not owner_approved_ready:
        failures.append(
            "owner_process_approval.owner_approves_exact_counts_now must match current owner-approved distribution state"
        )
    if owner_process.get("codex_may_use_owner_approved_c0_distribution") is not owner_approved_ready:
        failures.append(
            "owner_process_approval.codex_may_use_owner_approved_c0_distribution must match current owner-approved distribution state"
        )
    for field in (
        "codex_may_invent_counts",
        "codex_may_estimate_counts",
        "codex_may_balance_counts",
        "codex_may_optimize_counts",
        "codex_may_infer_counts_from_family_names",
    ):
        if owner_process.get(field) is not False:
            failures.append(f"owner_process_approval.{field} must be false")
    if owner_process.get("codex_may_use_pr97_explicit_counts_only") is not pr97_ready:
        failures.append(
            "owner_process_approval.codex_may_use_pr97_explicit_counts_only must match PR97-derived distribution state"
        )
    if owner_process.get("historical_owner_distribution_required_before_c0") is not True:
        failures.append(
            "owner_process_approval.historical_owner_distribution_required_before_c0 must be true"
        )
    if owner_process.get("c0_owner_distribution_approval_applied") is not owner_approved_ready:
        failures.append(
            "owner_process_approval.c0_owner_distribution_approval_applied must match owner-approved distribution state"
        )
    if owner_process.get("if_pr97_counts_absent_block_for_owner_decision") is not blocked_for_owner:
        failures.append(
            "owner_process_approval.if_pr97_counts_absent_block_for_owner_decision must be true only while blocked"
        )
    expected_required_if_absent = (
        OWNER_DISTRIBUTION_DECISION if blocked_for_owner else None
    )
    if owner_process.get("required_owner_decision_if_absent") != expected_required_if_absent:
        failures.append(
            "owner_process_approval.required_owner_decision_if_absent must reflect current distribution state"
        )

    distribution = config.get("distribution_authority")
    if not isinstance(distribution, dict):
        failures.append("distribution_authority must be an object")
        distribution = {}
    if distribution.get("no_guesswork") is not True:
        failures.append("distribution_authority.no_guesswork must be true")
    for field in (
        "codex_may_invent_counts",
        "codex_may_estimate_counts",
        "codex_may_balance_counts",
        "codex_may_optimize_counts",
        "codex_may_infer_counts_from_family_names",
    ):
        if distribution.get(field) is not False:
            failures.append(f"distribution_authority.{field} must be false")

    count_derivation = config.get("count_derivation")
    if not isinstance(count_derivation, dict):
        failures.append("count_derivation must be an object")
        count_derivation = {}
    if count_derivation.get("pr97_explicit_distribution_checked") is not True:
        failures.append("count_derivation.pr97_explicit_distribution_checked must be true")
    if count_derivation.get("pr97_explicit_distribution_found") is not False:
        failures.append("count_derivation must preserve PR97 missing exact-count finding")
    if count_derivation.get("historical_owner_distribution_required_before_c0") is not True:
        failures.append("count_derivation must preserve historical owner-distribution requirement")
    if count_derivation.get("historical_owner_required_decision_before_c0") != OWNER_DISTRIBUTION_DECISION:
        failures.append("count_derivation must preserve historical owner-required decision")
    if count_derivation.get("c0_owner_distribution_supplied") is not owner_approved_ready:
        failures.append("count_derivation.c0_owner_distribution_supplied must match current state")
    expected_c0_pointer = (
        _as_posix(OWNER_APPROVED_DISTRIBUTION_CONFIG) if owner_approved_ready else None
    )
    if count_derivation.get("c0_distribution_source_pointer") != expected_c0_pointer:
        failures.append("count_derivation.c0_distribution_source_pointer must match current state")

    no_authority = config.get("no_authority_created")
    if isinstance(no_authority, dict):
        _require_false_fields(
            failures,
            no_authority,
            NO_AUTHORITY_FALSE_FIELDS,
            prefix="no_authority_created",
        )
    else:
        failures.append("no_authority_created must be an object")

    families = config.get("families")
    if not isinstance(families, list):
        failures.append("families must be a list")
        families = []
    if len(families) != FAMILY_COUNT_TOTAL:
        failures.append("families must contain exactly 15 entries")
    slugs = [
        family.get("family_slug") for family in families if isinstance(family, dict)
    ]
    if tuple(slugs) != REQUIRED_FAMILY_SLUGS:
        failures.append("families must use the canonical 15-family order")
    if len(slugs) != len(set(slugs)):
        failures.append("families must not contain duplicate family_slug values")

    if config.get("family_count_total") != FAMILY_COUNT_TOTAL:
        failures.append("family_count_total must equal 15")
    if config.get("target_total_row_count") != TARGET_TOTAL_ROW_COUNT:
        failures.append("target_total_row_count must equal 4183")
    if config.get("families_are_top_level_buckets_not_parameters") is not True:
        failures.append("families must be marked as top-level buckets, not parameters")
    if config.get("subfamily_row_class_doctrine_required") is not True:
        failures.append("subfamily row-class doctrine must be required")

    for index, family in enumerate(families):
        if not isinstance(family, dict):
            failures.append(f"families[{index}] must be an object")
            continue
        slug = REQUIRED_FAMILY_SLUGS[index] if index < len(REQUIRED_FAMILY_SLUGS) else ""
        expected_file = (
            REQUIRED_EXACT_ROW_SOURCE_FILES[index]
            if index < len(REQUIRED_EXACT_ROW_SOURCE_FILES)
            else None
        )
        expected_blueprint = (
            REQUIRED_SOURCE_BLUEPRINT_FILES[index]
            if index < len(REQUIRED_SOURCE_BLUEPRINT_FILES)
            else None
        )
        if family.get("family_number") != index + 1:
            failures.append(f"families[{index}].family_number must be {index + 1}")
        if family.get("family_id") != REQUIRED_FAMILY_IDS[index]:
            failures.append(f"families[{index}].family_id must be {REQUIRED_FAMILY_IDS[index]}")
        if family.get("future_exact_row_source_file") != expected_file:
            failures.append(f"families[{index}].future_exact_row_source_file is wrong")
        if family.get("future_source_blueprint_file") != expected_blueprint:
            failures.append(f"families[{index}].future_source_blueprint_file is wrong")
        _require_false_fields(
            failures,
            family,
            NO_CREATION_FALSE_FIELDS,
            prefix=f"families[{index}]",
        )
        _require_false_fields(
            failures,
            family,
            QUANTUM_FALSE_FIELDS,
            prefix=f"families[{index}]",
        )
        if family.get("agent_eligibility_governance_required_for_future_rows") is not True:
            failures.append(
                f"families[{index}].agent_eligibility_governance_required_for_future_rows must be true"
            )
        if family.get("deny_by_default_agent_access_required") is not True:
            failures.append(
                f"families[{index}].deny_by_default_agent_access_required must be true"
            )
        subfamilies = family.get("subfamily_classes")
        if not isinstance(subfamilies, list) or not subfamilies:
            failures.append(f"families[{index}].subfamily_classes must be non-empty")
            subfamilies = []
        if len(subfamilies) != len(set(subfamilies)):
            failures.append(f"families[{index}].subfamily_classes must be unique")
        for subfamily in subfamilies:
            if subfamily not in ALLOWED_SUBFAMILY_CLASSES:
                failures.append(f"families[{index}].subfamily_classes has invalid {subfamily!r}")
        for required in FAMILY_REQUIRED_SUBFAMILIES.get(slug, ()):
            if required not in subfamilies:
                failures.append(f"families[{index}] {slug} must include {required}")
        if slug in QUANTUM_RELEVANCE_BY_FAMILY:
            if family.get("quantum_relevance_class") != QUANTUM_RELEVANCE_BY_FAMILY[slug]:
                failures.append(f"families[{index}] {slug} has wrong quantum relevance class")
        elif family.get("quantum_relevance_class") != "NOT_QUANTUM_SPECIFIC_STATIC_METADATA":
            failures.append(f"families[{index}] {slug} must be non-quantum-specific")
        if slug == "009_lifecycle_agent_binding":
            if family.get("agent_governance_relevance_class") != (
                "PRIMARY_AGENT_ROW_ACCESS_GOVERNANCE_FAMILY"
            ):
                failures.append("family 009 must be the primary agent governance family")
            _require_exact_list(
                failures,
                label="family 009 future_policy_row_kinds_allowed",
                actual=family.get("future_policy_row_kinds_allowed"),
                expected=REQUIRED_POLICY_ROW_KINDS,
            )
            if family.get("access_decision_default") != "DENY":
                failures.append("family 009 access_decision_default must be DENY")
            _require_false_fields(
                failures,
                family,
                AGENT_DENY_FALSE_FIELDS,
                prefix="family 009",
            )

    if derivation is None:
        return failures

    if derivation.failures:
        failures.extend(derivation.failures)
        return failures

    if derivation.explicit_distribution_found:
        expected_state = EXACT_DISTRIBUTION_READY_STATE
        if config.get("exact_distribution_ready") is not True:
            failures.append("exact_distribution_ready must be true when exact distribution exists")
        if config.get("owner_distribution_required") is not False:
            failures.append("owner_distribution_required must be false when exact distribution exists")
        if config.get("gate_mode") != expected_state or config.get("manifest_state") != expected_state:
            failures.append("gate_mode and manifest_state must be exact-ready")
        expected_validation_result = (
            PASS_OWNER_APPROVED_DISTRIBUTION_READY
            if derivation.source == OWNER_APPROVED_COUNT_AUTHORITY
            else PASS_EXACT_DISTRIBUTION_READY
        )
        if config.get("validation_result") != expected_validation_result:
            failures.append(f"validation_result must be {expected_validation_result}")
        if distribution.get("source") != derivation.source:
            failures.append("distribution_authority.source must match current exact distribution source")
        if distribution.get("source_pointer") != derivation.source_pointer:
            failures.append("distribution_authority.source_pointer must match current distribution source")
        if distribution.get("owner_required_decision") is not None:
            failures.append("owner_required_decision must be null when exact counts exist")
        for family in families:
            slug = family.get("family_slug")
            if not isinstance(slug, str) or derivation.counts is None or derivation.ranges is None:
                continue
            start, end = derivation.ranges[slug]
            if family.get("target_row_count") != derivation.counts[slug]:
                failures.append(f"{slug}.target_row_count must match PR97 distribution")
            if family.get("row_index_start") != start or family.get("row_index_end") != end:
                failures.append(f"{slug}.row_index range must be deterministic and contiguous")
            if family.get("count_authority") != derivation.source:
                failures.append(f"{slug}.count_authority must match current distribution authority")
            if family.get("distribution_state") != EXACT_DISTRIBUTION_READY_STATE:
                failures.append(f"{slug}.distribution_state must be exact-ready")
    else:
        if config.get("exact_distribution_ready") is not False:
            failures.append("exact_distribution_ready must be false while PR97 counts are absent")
        if config.get("owner_distribution_required") is not True:
            failures.append("owner_distribution_required must be true while PR97 counts are absent")
        if config.get("gate_mode") != BLOCKED_STATE or config.get("manifest_state") != BLOCKED_STATE:
            failures.append("gate_mode and manifest_state must be blocked pending owner distribution")
        if config.get("validation_result") != PASS_BLOCKED_EXPECTED:
            failures.append("validation_result must be PASS_BLOCKED_EXPECTED")
        if distribution.get("source") != OWNER_APPROVAL_REQUIRED_AUTHORITY:
            failures.append("distribution_authority.source must be OWNER_APPROVAL_REQUIRED")
        if distribution.get("source_pointer") is not None:
            failures.append("distribution_authority.source_pointer must be null while blocked")
        if distribution.get("owner_required_decision") != OWNER_DISTRIBUTION_DECISION:
            failures.append("owner_required_decision must request exact 15-family distribution")
        for family in families:
            slug = family.get("family_slug")
            if family.get("target_row_count") is not None:
                failures.append(f"{slug}.target_row_count must be null while blocked")
            if family.get("row_index_start") is not None or family.get("row_index_end") is not None:
                failures.append(f"{slug}.row ranges must be null while blocked")
            if family.get("count_authority") != OWNER_APPROVAL_REQUIRED_AUTHORITY:
                failures.append(f"{slug}.count_authority must be OWNER_APPROVAL_REQUIRED")
            if family.get("distribution_state") != BLOCKED_STATE:
                failures.append(f"{slug}.distribution_state must be blocked")
    return failures


def _read_jsonl(path: pathlib.Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    failures: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return records, [f"PR98 source file missing: {path.as_posix()}"]
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            failures.append(f"{path.as_posix()}:{line_number}: invalid JSONL: {exc}")
            continue
        if not isinstance(value, dict):
            failures.append(f"{path.as_posix()}:{line_number}: record must be an object")
            continue
        records.append(value)
    return records, failures


def validate_pr98_sources(repo_root: pathlib.Path) -> tuple[bool, list[str]]:
    failures: list[str] = []
    source_dir = repo_root / PR98_SOURCE_DIR
    files = sorted(source_dir.glob("*.source.jsonl"))
    if len(files) != FAMILY_COUNT_TOTAL:
        failures.append("PR98 source directory must contain exactly 15 source blueprint files")
    expected_paths = [repo_root / pathlib.Path(path) for path in REQUIRED_SOURCE_BLUEPRINT_FILES]
    if [path.resolve() for path in files] != [path.resolve() for path in expected_paths]:
        failures.append("PR98 source files must match canonical 15-family blueprint order")

    for index, path in enumerate(expected_paths):
        records, record_failures = _read_jsonl(path)
        failures.extend(record_failures)
        if len(records) != 1:
            failures.append(f"{path.as_posix()} must contain exactly one source blueprint record")
            continue
        record = records[0]
        if record.get("source_file_mode") != "SOURCE_REQUIRED":
            failures.append(f"{path.as_posix()} must remain a SOURCE_REQUIRED blueprint")
        if record.get("declared_source_blueprint_count") != 1:
            failures.append(f"{path.as_posix()} must declare one source blueprint")
        if record.get("declared_source_record_count") != 0:
            failures.append(f"{path.as_posix()} must declare zero exact source records")
        if record.get("exact_row_count_created_by_pr98_flag") is not False:
            failures.append(f"{path.as_posix()} must not create exact row counts")
        if record.get("final_bundle_row_file_flag") is not False:
            failures.append(f"{path.as_posix()} must not be a final bundle row file")
        nested = record.get("source_records_or_blueprints")
        if not isinstance(nested, list) or len(nested) != 1 or not isinstance(nested[0], dict):
            failures.append(f"{path.as_posix()} must contain one nested blueprint")
            continue
        blueprint = nested[0]
        if blueprint.get("record_class") != "SOURCE_ROW_BLUEPRINT_NOT_EXACT_FINAL_ROW":
            failures.append(f"{path.as_posix()} nested record must remain a blueprint")
        for field in (
            "exact_final_row_created_flag",
            "exact_row_created_flag",
            "final_bundle_membership_created_flag",
            "runtime_live_order_authority_created_flag",
            "source_evidence_created_flag",
            "connector_semantic_created_flag",
            "profit_evidence_created_flag",
            "quantum_backend_execution_created_flag",
        ):
            if blueprint.get(field) is not False:
                failures.append(f"{path.as_posix()} nested {field} must be false")
        if index < len(REQUIRED_FAMILY_IDS) and record.get("row_family_id") != REQUIRED_FAMILY_IDS[index]:
            failures.append(f"{path.as_posix()} row_family_id is out of order")
    return not failures, failures


def validate_no_forbidden_artifacts(repo_root: pathlib.Path) -> tuple[list[str], dict[str, bool]]:
    post_d_state = post_d_sentinel.check_post_d_materialization_state(repo_root)
    exact_dir_present = (repo_root / EXACT_ROW_SOURCES_DIR).exists()
    exact_row_sources_allowed_by_d = exact_dir_present and post_d_state.allowed
    checks = {
        "exact_row_sources": (not exact_dir_present) or exact_row_sources_allowed_by_d,
        "AtomicRows.bundle.jsonl": not (repo_root / CANONICAL_BUNDLE_JSONL).exists(),
        "AtomicRows.bundle.sha256": not (repo_root / CANONICAL_BUNDLE_SHA256).exists(),
    }
    failures = [
        f"forbidden artifact exists: {name}" for name, absent in checks.items() if not absent
    ]
    return failures, checks


def validate_master_plan_not_modified(repo_root: pathlib.Path) -> tuple[bool, list[str]]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", "--", _as_posix(MASTER_PLAN_CURRENT)],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return False, [f"could not verify master plan git diff: {completed.stderr.strip()}"]
    modified = bool(completed.stdout.strip())
    if modified:
        return False, ["docs/master_plan/QTT_MasterPlan_Current.md must remain unchanged"]
    return True, []


def validate_static_surface(path: pathlib.Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    failures: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FORBIDDEN_STATIC_IMPORTS:
                    failures.append(f"forbidden import in validator: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in FORBIDDEN_STATIC_IMPORTS:
                failures.append(f"forbidden import in validator: {node.module}")
        elif isinstance(node, ast.Call):
            func = node.func
            name = ""
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name in FORBIDDEN_STATIC_CALLS:
                failures.append(f"forbidden call in validator: {name}")
    return failures


def validate_upstream_state(repo_root: pathlib.Path) -> tuple[list[str], UpstreamState | None]:
    failures: list[str] = []

    pr97_plan, pr97_plan_failures = _load_yaml_checked(repo_root / PR97_PLAN, "PR97 plan")
    pr97_report, pr97_report_failures = _load_json_checked(repo_root / PR97_REPORT, "PR97 report")
    pr98_config, pr98_config_failures = _load_yaml_checked(repo_root / PR98_CONFIG, "PR98 config")
    pr98_report, pr98_report_failures = _load_json_checked(repo_root / PR98_REPORT, "PR98 report")
    pr99_config, pr99_config_failures = _load_yaml_checked(repo_root / PR99_CONFIG, "PR99 config")
    pr99_report, pr99_report_failures = _load_json_checked(repo_root / PR99_REPORT, "PR99 report")
    pr100_config, pr100_config_failures = _load_yaml_checked(repo_root / PR100_CONFIG, "PR100 config")
    pr100_report, pr100_report_failures = _load_json_checked(repo_root / PR100_REPORT, "PR100 report")
    bridge_config, bridge_config_failures = _load_yaml_checked(repo_root / BRIDGE_CONFIG, "Repair PR A bridge config")
    bridge_report, bridge_report_failures = _load_json_checked(repo_root / BRIDGE_REPORT, "Repair PR A bridge report")

    failures.extend(pr97_plan_failures)
    failures.extend(pr97_report_failures)
    failures.extend(pr98_config_failures)
    failures.extend(pr98_report_failures)
    failures.extend(pr99_config_failures)
    failures.extend(pr99_report_failures)
    failures.extend(pr100_config_failures)
    failures.extend(pr100_report_failures)
    failures.extend(bridge_config_failures)
    failures.extend(bridge_report_failures)

    pr97_present = pr97_plan is not None and pr97_report is not None
    if pr97_plan is not None:
        if pr97_plan.get("target_total_row_count") != TARGET_TOTAL_ROW_COUNT:
            failures.append("PR97 target_total_row_count must remain 4183")
        row_families = (
            pr97_plan.get("row_family_split_plan", {}).get("row_families", [])
            if isinstance(pr97_plan.get("row_family_split_plan"), dict)
            else []
        )
        ids = [
            item.get("row_family_id") for item in row_families if isinstance(item, dict)
        ]
        if tuple(ids) != REQUIRED_FAMILY_IDS:
            failures.append("PR97 row families must remain the canonical 15 families")
        for item in row_families:
            if not isinstance(item, dict):
                continue
            if item.get("exact_row_count_created_by_pr97_flag") is not False:
                failures.append("PR97 must not claim exact row counts were created")
            if item.get("planned_count_policy") != "OWNER_REVIEW_REQUIRED":
                failures.append("PR97 planned count policy must remain owner-review required")
    if pr97_report is not None:
        if pr97_report.get("target_total_row_count") != TARGET_TOTAL_ROW_COUNT:
            failures.append("PR97 report target_total_row_count must remain 4183")

    pr98_blueprints_ok, source_failures = validate_pr98_sources(repo_root)
    failures.extend(source_failures)
    if pr98_config is not None:
        if pr98_config.get("target_total_row_count_planning_authority_only_flag") is not True:
            failures.append("PR98 target total must remain planning-only authority")
        if pr98_config.get("final_bundle_created_flag") is not False:
            failures.append("PR98 must not create final bundle")
    if pr98_report is not None:
        if pr98_report.get("source_file_count") != FAMILY_COUNT_TOTAL:
            failures.append("PR98 report source_file_count must be 15")
        summaries = pr98_report.get("source_files")
        if not isinstance(summaries, list) or len(summaries) != FAMILY_COUNT_TOTAL:
            failures.append("PR98 report must summarize 15 source blueprint files")
        else:
            for summary in summaries:
                if not isinstance(summary, dict):
                    failures.append("PR98 report source_file_summaries entries must be objects")
                    continue
                if summary.get("exact_row_count_created_by_pr98_flag") is not False:
                    failures.append("PR98 report must not claim exact row counts were created")

    pr99_ok = False
    if pr99_config is not None:
        if pr99_config.get("build_path_decision") != (
            "PATH_B_BUILDER_FRAMEWORK_AND_BLOCKED_ASSEMBLY_GATE"
        ):
            failures.append("PR99 config must remain Path B blocked")
    if pr99_report is not None:
        pr99_ok = (
            pr99_report.get("build_path_decision")
            == "PATH_B_BUILDER_FRAMEWORK_AND_BLOCKED_ASSEMBLY_GATE"
            and pr99_report.get("build_allowed_flag") is False
            and pr99_report.get("build_blocked_flag") is True
            and pr99_report.get("exact_source_rows_found_count") == 0
            and pr99_report.get("source_blueprints_found_count") == FAMILY_COUNT_TOTAL
            and pr99_report.get("bundle_file_created_flag") is False
            and pr99_report.get("bundle_sha_created_flag") is False
            and pr99_report.get("final_readiness_created_flag") is False
        )
        if not pr99_ok:
            failures.append("PR99 report must preserve Path B blocked assembly state")

    pr100_ok = False
    if pr100_config is not None:
        if pr100_config.get("gate_mode") != "BLOCKED":
            failures.append("PR100 config gate_mode must remain BLOCKED")
    if pr100_report is not None:
        pr100_ok = (
            pr100_report.get("gate_mode") == "BLOCKED"
            and pr100_report.get("validation_result") == "PASS_BLOCKED_EXPECTED"
            and pr100_report.get("sha_computed") is False
            and pr100_report.get("sha_file_created") is False
            and pr100_report.get("freeze_authority_created") is False
            and pr100_report.get("final_readiness_created") is False
        )
        if not pr100_ok:
            failures.append("PR100 report must preserve blocked SHA/freeze state")

    bridge_present = bridge_config is not None and bridge_report is not None
    bridge_preserved = False
    if bridge_report is not None:
        bridge_preserved = all(
            bridge_report.get(field) is expected
            for field, expected in {
                "bridge_created": True,
                "exact_rows_created": False,
                "atomicrows_bundle_jsonl_created": False,
                "atomicrows_bundle_sha256_created": False,
                "sha_computed": False,
                "freeze_authority_created": False,
                "final_readiness_created": False,
                "canonical_row_fill_architecture_defined": True,
                "future_row_file_strategy_defined": True,
                "future_row_id_law_defined": True,
                "agent_eligibility_governance_required": True,
                "deny_by_default_agent_access_policy_required": True,
            }.items()
        )
        if not bridge_preserved:
            failures.append("Repair PR A bridge report is missing required preserved facts")
    if bridge_config is not None:
        if bridge_config.get("gate_mode") != "BRIDGE_READY_EXACT_ROWS_NOT_CREATED":
            failures.append("Repair PR A bridge config gate_mode must remain ready/no-rows")

    forbidden_failures, forbidden_absent = validate_no_forbidden_artifacts(repo_root)
    failures.extend(forbidden_failures)
    master_plan_unchanged, master_plan_failures = validate_master_plan_not_modified(repo_root)
    failures.extend(master_plan_failures)

    state = UpstreamState(
        pr97_expansion_plan_present=pr97_present,
        pr98_blueprints_are_not_exact_rows=pr98_blueprints_ok,
        pr99_path_b_remains_current_blocked_state=pr99_ok,
        pr100_sha_freeze_gate_remains_blocked=pr100_ok,
        repair_pr_a_bridge_present=bridge_present,
        repair_pr_a_bridge_preserved=bridge_preserved,
        forbidden_artifacts_absent=forbidden_absent,
        master_plan_unchanged=master_plan_unchanged,
    )
    return failures, state


def build_report(
    *,
    config: dict[str, Any],
    derivation: DistributionDerivation,
    upstream: UpstreamState,
    schema_path: pathlib.Path,
    config_path: pathlib.Path,
    report_path: pathlib.Path,
) -> dict[str, Any]:
    families = []
    for family in config["families"]:
        families.append(
            {
                "family_number": family["family_number"],
                "family_slug": family["family_slug"],
                "family_id": family["family_id"],
                "future_exact_row_source_file": family["future_exact_row_source_file"],
                "future_source_blueprint_file": family["future_source_blueprint_file"],
                "subfamily_classes": family["subfamily_classes"],
                "target_row_count": family["target_row_count"],
                "row_index_start": family["row_index_start"],
                "row_index_end": family["row_index_end"],
                "count_authority": family["count_authority"],
                "distribution_state": family["distribution_state"],
            }
        )

    report = {
        "report_type": REPORT_TYPE,
        "artifact_id": ARTIFACT_ID,
        "artifact_version": ARTIFACT_VERSION,
        "repair_scope": REPAIR_SCOPE,
        "authority_class": AUTHORITY_CLASS,
        "generated_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "schema_path": _as_posix(schema_path),
        "config_path": _as_posix(config_path),
        "report_path": _as_posix(report_path),
        "validation_result": derivation.validation_result,
        "validator_stdout_marker": SUCCESS_MARKER,
        "manifest_created": True,
        "manifest_state": derivation.state,
        "exact_distribution_ready": derivation.explicit_distribution_found,
        "owner_distribution_required": not derivation.explicit_distribution_found,
        "owner_process_approval_preserved": True,
        "owner_approves_exact_counts_now": derivation.source == OWNER_APPROVED_COUNT_AUTHORITY,
        "codex_may_use_pr97_explicit_counts_only": derivation.source == DERIVED_COUNT_AUTHORITY,
        "codex_may_use_owner_approved_c0_distribution": (
            derivation.source == OWNER_APPROVED_COUNT_AUTHORITY
        ),
        "codex_may_invent_counts": False,
        "codex_may_estimate_counts": False,
        "codex_may_balance_counts": False,
        "codex_may_optimize_counts": False,
        "codex_may_infer_counts_from_family_names": False,
        "pr97_explicit_distribution_found": (
            config.get("count_derivation", {}).get("pr97_explicit_distribution_found")
        ),
        "pr97_missing_count_finding_preserved": (
            config.get("count_derivation", {}).get("pr97_explicit_distribution_found") is False
        ),
        "historical_owner_distribution_required_before_c0": (
            config.get("count_derivation", {}).get("historical_owner_distribution_required_before_c0")
        ),
        "c0_owner_distribution_supplied": (
            config.get("count_derivation", {}).get("c0_owner_distribution_supplied")
        ),
        "target_total_row_count": TARGET_TOTAL_ROW_COUNT,
        "family_count_total": FAMILY_COUNT_TOTAL,
        "families_are_top_level_buckets_not_parameters": True,
        "subfamily_row_class_doctrine_required": True,
        "allowed_subfamily_classes": list(ALLOWED_SUBFAMILY_CLASSES),
        "future_exact_row_required_fields": list(FUTURE_EXACT_ROW_REQUIRED_FIELDS),
        "family_counts_sum": derivation.family_counts_sum,
        "row_ranges_contiguous": derivation.row_ranges_contiguous,
        "final_row_index": derivation.final_row_index,
        "families": families,
        "exact_rows_created": False,
        "exact_row_source_directory_created": False,
        "atomicrows_bundle_jsonl_created": False,
        "atomicrows_bundle_sha256_created": False,
        "sha_computed": False,
        "freeze_authority_created": False,
        "final_readiness_created": False,
        "runtime_live_order_authority_created": False,
        "source_fact_authority_created": False,
        "connector_semantic_authority_created": False,
        "profit_evidence_created": False,
        "latency_evidence_created": False,
        "execution_superiority_evidence_created": False,
        "optimizer_execution_created": False,
        "quantum_backend_authority_created": False,
        "quantum_advantage_evidence_created": False,
        "specific_agent_family_assignments_created": False,
        "specific_agent_row_assignments_created": False,
        "agent_family_assignment_matrix_future_required": True,
        "distribution_counts_grant_agent_access": False,
        "distribution_counts_grant_trading_authority": False,
        "distribution_counts_grant_live_authority": False,
        "distribution_counts_grant_order_authority": False,
        "distribution_counts_grant_quantum_backend_authority": False,
        "pr97_expansion_plan_present": upstream.pr97_expansion_plan_present,
        "pr98_blueprints_are_not_exact_rows": upstream.pr98_blueprints_are_not_exact_rows,
        "pr99_path_b_remains_current_blocked_state": (
            upstream.pr99_path_b_remains_current_blocked_state
        ),
        "pr100_sha_freeze_gate_remains_blocked": (
            upstream.pr100_sha_freeze_gate_remains_blocked
        ),
        "repair_pr_a_bridge_present": upstream.repair_pr_a_bridge_present,
        "repair_pr_a_bridge_preserved": upstream.repair_pr_a_bridge_preserved,
        "repair_pr_a_authority_classifier_preserved": upstream.repair_pr_a_bridge_preserved,
        "repair_pr_a_agent_eligibility_governance_preserved": (
            upstream.repair_pr_a_bridge_preserved
        ),
        "distribution_authority": derivation.source,
        "distribution_source_pointer": derivation.source_pointer,
        "owner_required_decision": derivation.owner_required_decision,
        "quantum_forward_families_preserved": True,
        "agent_governance_family_preserved": True,
        "deny_by_default_agent_access_preserved": True,
        "forbidden_artifacts_absent": upstream.forbidden_artifacts_absent,
        "master_plan_unchanged": upstream.master_plan_unchanged,
        "next_required_repair_pr": NEXT_REQUIRED_REPAIR_PR,
    }
    return report


def validate_report(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if report.get("report_type") != REPORT_TYPE:
        failures.append("report_type is wrong")
    if report.get("artifact_id") != ARTIFACT_ID:
        failures.append("artifact_id is wrong")
    if report.get("validator_stdout_marker") != SUCCESS_MARKER:
        failures.append("validator marker is wrong")
    if report.get("target_total_row_count") != TARGET_TOTAL_ROW_COUNT:
        failures.append("report target_total_row_count must be 4183")
    if report.get("family_count_total") != FAMILY_COUNT_TOTAL:
        failures.append("report family_count_total must be 15")
    if report.get("exact_rows_created") is not False:
        failures.append("report must not claim exact rows were created")
    if report.get("sha_computed") is not False:
        failures.append("report must not claim SHA was computed")
    for field in (
        "freeze_authority_created",
        "final_readiness_created",
        "runtime_live_order_authority_created",
        "profit_evidence_created",
        "latency_evidence_created",
        "execution_superiority_evidence_created",
        "quantum_advantage_evidence_created",
        "specific_agent_family_assignments_created",
        "specific_agent_row_assignments_created",
        "distribution_counts_grant_agent_access",
        "distribution_counts_grant_trading_authority",
        "distribution_counts_grant_live_authority",
        "distribution_counts_grant_order_authority",
        "distribution_counts_grant_quantum_backend_authority",
    ):
        if report.get(field) is not False:
            failures.append(f"report {field} must be false")
    if report.get("distribution_authority") not in (
        DERIVED_COUNT_AUTHORITY,
        OWNER_APPROVED_COUNT_AUTHORITY,
        OWNER_APPROVAL_REQUIRED_AUTHORITY,
    ):
        failures.append("report distribution_authority is invalid")
    if report.get("distribution_authority") in (
        DERIVED_COUNT_AUTHORITY,
        OWNER_APPROVED_COUNT_AUTHORITY,
    ):
        if report.get("family_counts_sum") != TARGET_TOTAL_ROW_COUNT:
            failures.append("report family_counts_sum must be 4183 when exact-ready")
        if report.get("row_ranges_contiguous") is not True:
            failures.append("report row ranges must be contiguous when exact-ready")
        if report.get("final_row_index") != TARGET_TOTAL_ROW_COUNT:
            failures.append("report final_row_index must be 4183 when exact-ready")
        if report.get("owner_required_decision") is not None:
            failures.append("exact-ready report owner_required_decision must be null")
        if report.get("distribution_authority") == OWNER_APPROVED_COUNT_AUTHORITY:
            if report.get("validation_result") != PASS_OWNER_APPROVED_DISTRIBUTION_READY:
                failures.append("owner-approved report validation_result is wrong")
    else:
        if report.get("owner_required_decision") != OWNER_DISTRIBUTION_DECISION:
            failures.append("blocked report must record owner_required_decision")
        if report.get("family_counts_sum") is not None:
            failures.append("blocked report must not fabricate family_counts_sum")
        if report.get("final_row_index") is not None:
            failures.append("blocked report must not fabricate final_row_index")
    if report != json.loads(serialize_report(report)):
        failures.append("report must be JSON deterministic")
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
    schema, schema_failures = _load_json_checked(schema_abs, "SCHEMA")
    config, config_failures = _load_yaml_checked(config_abs, "CONFIG")
    pr97_plan, pr97_plan_failures = _load_yaml_checked(repo_root / PR97_PLAN, "PR97 plan")
    pr97_report, pr97_report_failures = _load_json_checked(repo_root / PR97_REPORT, "PR97 report")
    pr97_schema, pr97_schema_failures = _load_json_checked(repo_root / PR97_SCHEMA, "PR97 schema")

    failures.extend(schema_failures)
    failures.extend(config_failures)
    failures.extend(pr97_plan_failures)
    failures.extend(pr97_report_failures)
    failures.extend(pr97_schema_failures)
    if schema is None or config is None or pr97_plan is None or pr97_report is None:
        return ValidationResult(False, tuple(failures), None)

    derivation = derive_current_distribution(repo_root, pr97_plan, pr97_report, pr97_schema)
    upstream_failures, upstream = validate_upstream_state(repo_root)
    failures.extend(upstream_failures)
    failures.extend(validate_static_surface(repo_root / "tools" / pathlib.Path(__file__).name))
    failures.extend(validate_config_payload(config, schema, derivation))

    if upstream is None:
        return ValidationResult(False, tuple(failures), None)

    report = build_report(
        config=config,
        derivation=derivation,
        upstream=upstream,
        schema_path=schema_path,
        config_path=config_path,
        report_path=output_path,
    )
    second_report = build_report(
        config=copy.deepcopy(config),
        derivation=copy.deepcopy(derivation),
        upstream=copy.deepcopy(upstream),
        schema_path=schema_path,
        config_path=config_path,
        report_path=output_path,
    )
    if report != second_report:
        failures.append("generated report is not deterministic across builds")
    failures.extend(validate_report(report))

    if failures:
        return ValidationResult(False, tuple(failures), report)

    write_json_report(report, output_abs)
    return ValidationResult(True, tuple(), report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate AtomicRows exact-row expansion manifest."
    )
    parser.add_argument("--repo-root", type=pathlib.Path, default=pathlib.Path("."))
    parser.add_argument("--schema", type=pathlib.Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--config", type=pathlib.Path, default=DEFAULT_CONFIG)
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
