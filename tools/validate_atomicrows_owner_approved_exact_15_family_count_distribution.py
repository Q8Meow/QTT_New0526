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
from tools import validate_atomicrows_exact_row_expansion_manifest as manifest_gate  # noqa: E402
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)


DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_owner_approved_exact_15_family_count_distribution.schema.json"
)
DEFAULT_CONFIG = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsOwnerApprovedExact15FamilyCountDistribution.yaml"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsOwnerApprovedExact15FamilyCountDistribution.report.json"
)

REPORT_TYPE = "ATOMICROWS_OWNER_APPROVED_EXACT_15_FAMILY_COUNT_DISTRIBUTION_REPORT"
ARTIFACT_ID = "ATOMICROWS_OWNER_APPROVED_EXACT_15_FAMILY_COUNT_DISTRIBUTION"
ARTIFACT_VERSION = "v1"
REPAIR_SCOPE = "OWNER_APPROVED_ATOMICROWS_EXACT_15_FAMILY_COUNT_DISTRIBUTION"
AUTHORITY_CLASS = (
    "OWNER_INTERNAL_ARCHITECTURE_DECISION_NOT_EXTERNAL_FACT_NOT_ROWS_NOT_BUNDLE_NOT_SHA_NOT_FREEZE"
)
APPROVAL_SCOPE = "EXACT_15_FAMILY_ROW_COUNT_DISTRIBUTION_ONLY"
DISTRIBUTION_AUTHORITY = "OWNER_APPROVED_EXACT_15_FAMILY_COUNT_DISTRIBUTION"
DISTRIBUTION_AUTHORITY_CLASS = "OWNER_INTERNAL_ARCHITECTURE_DECISION_NOT_EXTERNAL_FACT"
VALIDATION_RESULT = "PASS_OWNER_APPROVED_DISTRIBUTION_READY"
SUCCESS_MARKER = "QTT_ATOMICROWS_OWNER_APPROVED_EXACT_15_FAMILY_COUNT_DISTRIBUTION_OK"
FAILURE_MARKER = "QTT_ATOMICROWS_OWNER_APPROVED_EXACT_15_FAMILY_COUNT_DISTRIBUTION_FAILED"
TARGET_TOTAL_ROW_COUNT = 4183
FAMILY_COUNT_TOTAL = 15
QUANTUM_FAMILY_TOTAL_ROWS = 1103
AGENT_GOVERNANCE_FAMILY_ROWS = 270
NEXT_REQUIRED_REPAIR_PR = "ATOMICROWS_EXACT_ROW_GENERATOR_DRY_RUN"

FAMILY_DISTRIBUTION: tuple[tuple[int, str, int], ...] = (
    (1, "001_signal_features", 390),
    (2, "002_scoring_ranking", 330),
    (3, "003_normalization_calibration", 220),
    (4, "004_risk_control", 315),
    (5, "005_execution_connector_boundary", 280),
    (6, "006_capital_sizing_cash", 220),
    (7, "007_latency_routing", 250),
    (8, "008_error_guard_fail_closed", 220),
    (9, "009_lifecycle_agent_binding", 270),
    (10, "010_source_evidence_connector_semantic", 315),
    (11, "011_replay_paper_validation", 270),
    (12, "012_quantum_advisory_optimization", 290),
    (13, "013_quantum_qubo_ising_metadata", 265),
    (14, "014_quantum_qaoa_vqe_annealing_metadata", 265),
    (15, "015_quantum_portfolio_hybrid_comparator", 283),
)
REQUIRED_FAMILY_SLUGS = tuple(slug for _, slug, _ in FAMILY_DISTRIBUTION)
REQUIRED_COUNTS = {slug: count for _, slug, count in FAMILY_DISTRIBUTION}
QUANTUM_FAMILY_SLUGS = (
    "012_quantum_advisory_optimization",
    "013_quantum_qubo_ising_metadata",
    "014_quantum_qaoa_vqe_annealing_metadata",
    "015_quantum_portfolio_hybrid_comparator",
)
FORBIDDEN_CURRENT_OUTPUTS = (
    "docs/master_plan/atomic_rows/exact_row_sources/",
    "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
    "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256",
)
NOT_AUTHORIZED_FALSE_FIELDS = (
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
)
REPORT_FALSE_FIELDS = (
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
    "distribution_counts_grant_agent_access",
    "distribution_counts_grant_trading_authority",
    "distribution_counts_grant_live_authority",
    "distribution_counts_grant_order_authority",
    "distribution_counts_grant_quantum_backend_authority",
)
AGENT_GOVERNANCE_FALSE_FIELDS = (
    "row_existence_grants_access",
    "family_membership_grants_access",
    "quantum_applicability_grants_access",
    "owner_quantum_priority_grants_access",
    "replay_paper_eligibility_grants_live_access",
    "static_selection_eligibility_grants_order_authority",
    "agent_access_granted_by_distribution",
    "specific_agent_family_assignments_created",
    "specific_agent_row_assignments_created",
    "distribution_counts_grant_agent_access",
    "distribution_counts_grant_trading_authority",
    "distribution_counts_grant_live_authority",
    "distribution_counts_grant_order_authority",
    "distribution_counts_grant_quantum_backend_authority",
)
QUANTUM_FALSE_FIELDS = (
    "quantum_execution_created",
    "quantum_backend_executed",
    "quantum_simulator_executed",
    "quantum_provider_called",
    "qubo_solving_executed",
    "ising_solving_executed",
    "qaoa_executed",
    "vqe_executed",
    "annealing_executed",
    "quantum_portfolio_optimization_executed",
    "quantum_advantage_claim_created",
)
FUTURE_MATRIX_FORBIDDEN_PATHS = (
    pathlib.Path("docs/master_plan/atomicrows/AtomicRowsExactRowAgentFamilyEligibilityMatrix.yaml"),
    pathlib.Path("docs/master_plan/generated/AtomicRowsExactRowAgentFamilyEligibilityMatrix.report.json"),
    pathlib.Path("schemas/atomicrows/atomicrows_exact_row_agent_family_eligibility_matrix.schema.json"),
    pathlib.Path("tools/validate_atomicrows_exact_row_agent_family_eligibility_matrix.py"),
    pathlib.Path("tests/atomicrows/test_atomicrows_exact_row_agent_family_eligibility_matrix.py"),
)


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
    value = manifest_gate.load_yaml(path)
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


def compute_row_ranges(
    distribution: Sequence[tuple[int, str, int]] = FAMILY_DISTRIBUTION,
) -> list[dict[str, int | str]]:
    ranges: list[dict[str, int | str]] = []
    start = 1
    for family_number, family_slug, target_row_count in distribution:
        end = start + target_row_count - 1
        ranges.append(
            {
                "family_number": family_number,
                "family_slug": family_slug,
                "target_row_count": target_row_count,
                "row_index_start": start,
                "row_index_end": end,
            }
        )
        start = end + 1
    return ranges


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


def _require_true(failures: list[str], mapping: dict[str, Any], field: str, prefix: str) -> None:
    if mapping.get(field) is not True:
        failures.append(f"{prefix}.{field} must be true")


def validate_distribution_payload(config: dict[str, Any], schema: dict[str, Any]) -> tuple[list[str], list[dict[str, int | str]]]:
    failures: list[str] = []
    failures.extend(schema_subset_failures(config, schema, "CONFIG"))

    expected_identity = {
        "artifact_id": ARTIFACT_ID,
        "artifact_version": ARTIFACT_VERSION,
        "repair_scope": REPAIR_SCOPE,
        "authority_class": AUTHORITY_CLASS,
        "approval_state": "OWNER_APPROVED",
        "owner_approval_scope": APPROVAL_SCOPE,
        "target_total_row_count": TARGET_TOTAL_ROW_COUNT,
        "family_count_total": FAMILY_COUNT_TOTAL,
        "counts_sum_must_equal_target": True,
        "counts_sum": TARGET_TOTAL_ROW_COUNT,
        "owner_distribution_approval_created_by_this_pr": True,
        "distribution_authority": DISTRIBUTION_AUTHORITY,
        "distribution_rationale_class": DISTRIBUTION_AUTHORITY_CLASS,
        "external_source_evidence_required_for_distribution": False,
        "next_required_repair_pr": NEXT_REQUIRED_REPAIR_PR,
    }
    for field, expected in expected_identity.items():
        if config.get(field) != expected:
            failures.append(f"config.{field} must be {expected!r}")

    rationale = config.get("count_rationale")
    if not isinstance(rationale, dict):
        failures.append("count_rationale must be an object")
        rationale = {}
    for field in (
        "signal_rich_for_prediction_market_microstructure_and_edge_detection",
        "scoring_ranking_rich_for_deterministic_stack_selection",
        "risk_execution_source_latency_governance_rich_for_fail_closed_controls",
        "quantum_forward_metadata_preserved",
        "avoids_single_family_overfit",
        "non_executable_and_non_live",
    ):
        _require_true(failures, rationale, field, "count_rationale")

    not_authorized = config.get("not_authorized_by_this_approval")
    if not isinstance(not_authorized, dict):
        failures.append("not_authorized_by_this_approval must be an object")
        not_authorized = {}
    _require_false_fields(
        failures,
        not_authorized,
        NOT_AUTHORIZED_FALSE_FIELDS,
        prefix="not_authorized_by_this_approval",
    )

    distribution = config.get("distribution")
    if not isinstance(distribution, list):
        failures.append("distribution must be a list")
        distribution = []
    if len(distribution) != FAMILY_COUNT_TOTAL:
        failures.append("distribution must contain exactly 15 families")
    slugs: list[str] = []
    counts: dict[str, int] = {}
    observed_distribution: list[tuple[int, str, int]] = []
    for index, entry in enumerate(distribution):
        if not isinstance(entry, dict):
            failures.append(f"distribution[{index}] must be an object")
            continue
        family_number = entry.get("family_number")
        family_slug = entry.get("family_slug")
        target_row_count = entry.get("target_row_count")
        if isinstance(family_slug, str):
            slugs.append(family_slug)
        if (
            isinstance(family_number, int)
            and not isinstance(family_number, bool)
            and isinstance(family_slug, str)
            and isinstance(target_row_count, int)
            and not isinstance(target_row_count, bool)
        ):
            observed_distribution.append((family_number, family_slug, target_row_count))
            counts[family_slug] = target_row_count
        if index < len(FAMILY_DISTRIBUTION):
            expected_number, expected_slug, expected_count = FAMILY_DISTRIBUTION[index]
            if family_number != expected_number:
                failures.append(f"distribution[{index}].family_number must be {expected_number}")
            if family_slug != expected_slug:
                failures.append(f"distribution[{index}].family_slug must be {expected_slug}")
            if target_row_count != expected_count:
                failures.append(f"distribution[{index}].target_row_count must be {expected_count}")
    if tuple(slugs) != REQUIRED_FAMILY_SLUGS:
        failures.append("distribution family slugs must be canonical and deterministic")
    if len(slugs) != len(set(slugs)):
        failures.append("distribution must reject duplicate family slugs")
    count_sum = sum(counts.values())
    if count_sum != TARGET_TOTAL_ROW_COUNT:
        failures.append(f"distribution counts must sum to {TARGET_TOTAL_ROW_COUNT}, got {count_sum}")
    if config.get("counts_sum") != count_sum:
        failures.append("config.counts_sum must match computed distribution sum")

    row_ranges = compute_row_ranges()
    if row_ranges[0]["row_index_start"] != 1:
        failures.append("computed first row index must be 1")
    if row_ranges[-1]["row_index_end"] != TARGET_TOTAL_ROW_COUNT:
        failures.append("computed final row index must be 4183")
    for previous, current in zip(row_ranges, row_ranges[1:]):
        if int(previous["row_index_end"]) + 1 != current["row_index_start"]:
            failures.append("computed row ranges must be contiguous")

    quantum = config.get("quantum_forward_distribution")
    if not isinstance(quantum, dict):
        failures.append("quantum_forward_distribution must be an object")
        quantum = {}
    if tuple(quantum.get("quantum_family_slugs", ())) != QUANTUM_FAMILY_SLUGS:
        failures.append("quantum family slugs must be deterministic")
    quantum_total = sum(REQUIRED_COUNTS[slug] for slug in QUANTUM_FAMILY_SLUGS)
    if quantum_total != QUANTUM_FAMILY_TOTAL_ROWS:
        failures.append("computed quantum family total must be 1103")
    if quantum.get("quantum_family_total_rows") != quantum_total:
        failures.append("quantum_family_total_rows must match computed quantum total")
    _require_true(
        failures,
        quantum,
        "quantum_family_total_is_internal_architecture_allocation_only",
        "quantum_forward_distribution",
    )
    _require_true(
        failures,
        quantum,
        "quantum_metadata_future_scope_only",
        "quantum_forward_distribution",
    )
    _require_false_fields(
        failures,
        quantum,
        QUANTUM_FALSE_FIELDS,
        prefix="quantum_forward_distribution",
    )

    agent = config.get("agent_governance_distribution")
    if not isinstance(agent, dict):
        failures.append("agent_governance_distribution must be an object")
        agent = {}
    if agent.get("primary_agent_governance_family") != "009_lifecycle_agent_binding":
        failures.append("family 009 must remain the primary agent governance family")
    if agent.get("primary_agent_governance_family_rows") != AGENT_GOVERNANCE_FAMILY_ROWS:
        failures.append("family 009 row count must be 270")
    _require_true(
        failures,
        agent,
        "deny_by_default_agent_access_preserved",
        "agent_governance_distribution",
    )
    _require_true(
        failures,
        agent,
        "future_agent_governance_row_kinds_preserved",
        "agent_governance_distribution",
    )
    _require_true(
        failures,
        agent,
        "agent_family_assignment_matrix_future_required",
        "agent_governance_distribution",
    )
    if agent.get("future_agent_family_eligibility_matrix_artifact_concept") != (
        "AtomicRowsExactRowAgentFamilyEligibilityMatrix"
    ):
        failures.append("future eligibility matrix concept must remain canonical")
    _require_false_fields(
        failures,
        agent,
        AGENT_GOVERNANCE_FALSE_FIELDS,
        prefix="agent_governance_distribution",
    )

    range_policy = config.get("future_row_range_policy")
    if not isinstance(range_policy, dict):
        failures.append("future_row_range_policy must be an object")
        range_policy = {}
    if range_policy.get("row_index_start_first_family") != 1:
        failures.append("future row range policy must start at 1")
    if range_policy.get("row_index_end_last_family") != TARGET_TOTAL_ROW_COUNT:
        failures.append("future row range policy must end at 4183")
    _require_true(failures, range_policy, "ranges_must_be_contiguous", "future_row_range_policy")
    _require_true(
        failures,
        range_policy,
        "ranges_are_future_planning_ranges_not_created_rows",
        "future_row_range_policy",
    )

    if tuple(config.get("forbidden_current_outputs", ())) != FORBIDDEN_CURRENT_OUTPUTS:
        failures.append("forbidden_current_outputs must match canonical forbidden outputs")

    return failures, row_ranges


def validate_forbidden_artifacts(repo_root: pathlib.Path) -> tuple[list[str], dict[str, bool]]:
    failures, absent = manifest_gate.validate_no_forbidden_artifacts(repo_root)
    atomic_rows_dir = repo_root / pathlib.Path("docs/master_plan/atomic_rows")
    exact_row_files: list[str] = []
    if atomic_rows_dir.exists():
        exact_row_files = sorted(
            path.relative_to(repo_root).as_posix()
            for path in atomic_rows_dir.rglob("*.exact_rows.jsonl")
        )
    if exact_row_files:
        failures.append("forbidden exact row files exist: " + ", ".join(exact_row_files))
    future_matrix_absent = True
    for path in FUTURE_MATRIX_FORBIDDEN_PATHS:
        if (repo_root / path).exists():
            future_matrix_absent = False
            failures.append(f"future agent-family eligibility matrix artifact must remain absent: {path.as_posix()}")
    absent = dict(absent)
    absent["specific_agent_family_assignment_artifact"] = future_matrix_absent
    absent["specific_agent_row_assignment_artifact"] = future_matrix_absent
    return failures, absent


def validate_repair_pr_a(repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    bridge_result = bridge_gate.validate(repo_root=repo_root)
    if not bridge_result.ok:
        failures.extend(f"Repair PR A bridge invalid: {failure}" for failure in bridge_result.failures)
    bridge_report = load_json(repo_root / bridge_gate.DEFAULT_REPORT)
    expected = {
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
    }
    for field, expected_value in expected.items():
        if bridge_report.get(field) is not expected_value:
            failures.append(f"Repair PR A report {field} must be {expected_value!r}")
    return failures


def validate_repair_pr_b_currentized(repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    manifest_config = load_yaml(repo_root / manifest_gate.DEFAULT_CONFIG)
    manifest_report = load_json(repo_root / manifest_gate.DEFAULT_REPORT)
    expected_source_pointer = _as_posix(DEFAULT_CONFIG)
    expected_manifest_fields = {
        "manifest_state": manifest_gate.EXACT_DISTRIBUTION_READY_STATE,
        "validation_result": manifest_gate.PASS_OWNER_APPROVED_DISTRIBUTION_READY,
        "exact_distribution_ready": True,
        "owner_distribution_required": False,
        "target_total_row_count": TARGET_TOTAL_ROW_COUNT,
        "family_count_total": FAMILY_COUNT_TOTAL,
    }
    for field, expected in expected_manifest_fields.items():
        if manifest_config.get(field) != expected:
            failures.append(f"Repair PR B manifest {field} must be {expected!r}")
        if manifest_report.get(field) != expected:
            failures.append(f"Repair PR B report {field} must be {expected!r}")

    authority = manifest_config.get("distribution_authority")
    if not isinstance(authority, dict):
        failures.append("Repair PR B distribution_authority must be an object")
        authority = {}
    if authority.get("source") != DISTRIBUTION_AUTHORITY:
        failures.append("Repair PR B must consume C0 distribution authority")
    if authority.get("source_pointer") != expected_source_pointer:
        failures.append("Repair PR B source pointer must target C0 distribution config")
    if authority.get("owner_required_decision") is not None:
        failures.append("Repair PR B owner_required_decision must be null after C0")

    derivation = manifest_config.get("count_derivation")
    if not isinstance(derivation, dict):
        failures.append("Repair PR B count_derivation must be an object")
        derivation = {}
    if derivation.get("pr97_explicit_distribution_checked") is not True:
        failures.append("Repair PR B must preserve PR97 distribution check")
    if derivation.get("pr97_explicit_distribution_found") is not False:
        failures.append("Repair PR B must preserve PR97 missing-count finding")
    if derivation.get("historical_owner_distribution_required_before_c0") is not True:
        failures.append("Repair PR B must preserve historical owner-distribution requirement")
    if derivation.get("c0_owner_distribution_supplied") is not True:
        failures.append("Repair PR B must record that C0 supplies the missing distribution")

    if manifest_report.get("distribution_authority") != DISTRIBUTION_AUTHORITY:
        failures.append("Repair PR B report distribution_authority must consume C0")
    if manifest_report.get("distribution_source_pointer") != expected_source_pointer:
        failures.append("Repair PR B report source pointer must target C0 distribution config")
    if manifest_report.get("family_counts_sum") != TARGET_TOTAL_ROW_COUNT:
        failures.append("Repair PR B report family_counts_sum must be 4183")
    if manifest_report.get("row_ranges_contiguous") is not True:
        failures.append("Repair PR B report row ranges must be contiguous")
    if manifest_report.get("final_row_index") != TARGET_TOTAL_ROW_COUNT:
        failures.append("Repair PR B report final_row_index must be 4183")
    for field in (
        "exact_rows_created",
        "exact_row_source_directory_created",
        "atomicrows_bundle_jsonl_created",
        "atomicrows_bundle_sha256_created",
        "sha_computed",
        "freeze_authority_created",
        "final_readiness_created",
        "specific_agent_family_assignments_created",
        "specific_agent_row_assignments_created",
    ):
        if manifest_report.get(field) is not False:
            failures.append(f"Repair PR B report {field} must be false")
    return failures


def validate_upstream_chain(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    upstream_failures, upstream = manifest_gate.validate_upstream_state(repo_root)
    failures.extend(upstream_failures)
    if upstream is None:
        return failures, {}

    pr98_ok, pr98_failures = manifest_gate.validate_pr98_sources(repo_root)
    failures.extend(pr98_failures)
    if not pr98_ok:
        failures.append("PR98 source files must remain blueprints only")
    master_plan_unchanged, master_plan_failures = manifest_gate.validate_master_plan_not_modified(repo_root)
    failures.extend(master_plan_failures)

    return failures, {
        "repair_pr_a_bridge_preserved": upstream.repair_pr_a_bridge_preserved,
        "repair_pr_b_manifest_currentized": True,
        "pr98_blueprints_remain_not_exact_rows": pr98_ok,
        "pr99_path_b_remains_historical_until_exact_rows_generated": (
            upstream.pr99_path_b_remains_current_blocked_state
        ),
        "pr100_sha_freeze_gate_remains_blocked_until_bundle_exists": (
            upstream.pr100_sha_freeze_gate_remains_blocked
        ),
        "master_plan_unchanged": master_plan_unchanged,
    }


def build_report(
    *,
    config: dict[str, Any],
    row_ranges: list[dict[str, int | str]],
    forbidden_artifacts_absent: dict[str, bool],
    upstream_facts: dict[str, Any],
    schema_path: pathlib.Path,
    config_path: pathlib.Path,
    report_path: pathlib.Path,
) -> dict[str, Any]:
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
        "validation_result": VALIDATION_RESULT,
        "validator_stdout_marker": SUCCESS_MARKER,
        "owner_distribution_approval_created": True,
        "owner_approval_scope": APPROVAL_SCOPE,
        "distribution_authority": DISTRIBUTION_AUTHORITY,
        "distribution_authority_class": DISTRIBUTION_AUTHORITY_CLASS,
        "target_total_row_count": TARGET_TOTAL_ROW_COUNT,
        "family_count_total": FAMILY_COUNT_TOTAL,
        "counts_sum": TARGET_TOTAL_ROW_COUNT,
        "row_ranges_contiguous": True,
        "final_row_index": TARGET_TOTAL_ROW_COUNT,
        "quantum_family_total_rows": QUANTUM_FAMILY_TOTAL_ROWS,
        "agent_governance_family_rows": AGENT_GOVERNANCE_FAMILY_ROWS,
        "computed_row_ranges": copy.deepcopy(row_ranges),
        "distribution": copy.deepcopy(config.get("distribution")),
        "exact_rows_created": False,
        "exact_row_source_directory_created": False,
        "atomicrows_bundle_jsonl_created": False,
        "atomicrows_bundle_sha256_created": False,
        "sha_computed": False,
        "freeze_authority_created": False,
        "final_readiness_created": False,
        "runtime_created": False,
        "live_authority_created": False,
        "order_authority_created": False,
        "source_acceptance_created": False,
        "connector_semantics_created": False,
        "optimizer_executed": False,
        "quantum_backend_executed": False,
        "profit_evidence_created": False,
        "latency_evidence_created": False,
        "execution_superiority_evidence_created": False,
        "quantum_advantage_evidence_created": False,
        "specific_agent_family_assignments_created": False,
        "specific_agent_row_assignments_created": False,
        "agent_family_assignment_matrix_future_required": True,
        "distribution_counts_grant_agent_access": False,
        "distribution_counts_grant_trading_authority": False,
        "distribution_counts_grant_live_authority": False,
        "distribution_counts_grant_order_authority": False,
        "distribution_counts_grant_quantum_backend_authority": False,
        "repair_pr_a_bridge_preserved": upstream_facts.get("repair_pr_a_bridge_preserved"),
        "repair_pr_b_manifest_currentized": upstream_facts.get("repair_pr_b_manifest_currentized"),
        "pr98_blueprints_remain_not_exact_rows": upstream_facts.get(
            "pr98_blueprints_remain_not_exact_rows"
        ),
        "pr99_path_b_remains_historical_until_exact_rows_generated": upstream_facts.get(
            "pr99_path_b_remains_historical_until_exact_rows_generated"
        ),
        "pr100_sha_freeze_gate_remains_blocked_until_bundle_exists": upstream_facts.get(
            "pr100_sha_freeze_gate_remains_blocked_until_bundle_exists"
        ),
        "master_plan_unchanged": upstream_facts.get("master_plan_unchanged"),
        "forbidden_artifacts_absent": {
            "exact_row_sources": forbidden_artifacts_absent.get("exact_row_sources"),
            "AtomicRows.bundle.jsonl": forbidden_artifacts_absent.get("AtomicRows.bundle.jsonl"),
            "AtomicRows.bundle.sha256": forbidden_artifacts_absent.get("AtomicRows.bundle.sha256"),
            "specific_agent_family_assignment_artifact": forbidden_artifacts_absent.get(
                "specific_agent_family_assignment_artifact"
            ),
            "specific_agent_row_assignment_artifact": forbidden_artifacts_absent.get(
                "specific_agent_row_assignment_artifact"
            ),
        },
        "quantum_forward_family_metadata_preserved": True,
        "quantum_metadata_future_requirement_scope_only": True,
        "quantum_execution_created": False,
        "quantum_advantage_claim_created": False,
        "deny_by_default_agent_governance_preserved": True,
        "future_agent_family_eligibility_matrix_artifact_concept": (
            "AtomicRowsExactRowAgentFamilyEligibilityMatrix"
        ),
        "next_required_repair_pr": NEXT_REQUIRED_REPAIR_PR,
    }
    return report


def validate_report(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected = {
        "report_type": REPORT_TYPE,
        "artifact_id": ARTIFACT_ID,
        "validation_result": VALIDATION_RESULT,
        "validator_stdout_marker": SUCCESS_MARKER,
        "owner_distribution_approval_created": True,
        "owner_approval_scope": APPROVAL_SCOPE,
        "distribution_authority": DISTRIBUTION_AUTHORITY,
        "distribution_authority_class": DISTRIBUTION_AUTHORITY_CLASS,
        "target_total_row_count": TARGET_TOTAL_ROW_COUNT,
        "family_count_total": FAMILY_COUNT_TOTAL,
        "counts_sum": TARGET_TOTAL_ROW_COUNT,
        "row_ranges_contiguous": True,
        "final_row_index": TARGET_TOTAL_ROW_COUNT,
        "quantum_family_total_rows": QUANTUM_FAMILY_TOTAL_ROWS,
        "agent_governance_family_rows": AGENT_GOVERNANCE_FAMILY_ROWS,
        "agent_family_assignment_matrix_future_required": True,
        "repair_pr_a_bridge_preserved": True,
        "repair_pr_b_manifest_currentized": True,
        "pr98_blueprints_remain_not_exact_rows": True,
        "pr99_path_b_remains_historical_until_exact_rows_generated": True,
        "pr100_sha_freeze_gate_remains_blocked_until_bundle_exists": True,
        "master_plan_unchanged": True,
        "next_required_repair_pr": NEXT_REQUIRED_REPAIR_PR,
    }
    for field, expected_value in expected.items():
        if report.get(field) != expected_value:
            failures.append(f"report.{field} must be {expected_value!r}")
    _require_false_fields(failures, report, REPORT_FALSE_FIELDS, prefix="report")
    forbidden = report.get("forbidden_artifacts_absent")
    if not isinstance(forbidden, dict):
        failures.append("report.forbidden_artifacts_absent must be an object")
        forbidden = {}
    for field in (
        "exact_row_sources",
        "AtomicRows.bundle.jsonl",
        "AtomicRows.bundle.sha256",
        "specific_agent_family_assignment_artifact",
        "specific_agent_row_assignment_artifact",
    ):
        if forbidden.get(field) is not True:
            failures.append(f"report.forbidden_artifacts_absent.{field} must be true")
    if report.get("computed_row_ranges") != compute_row_ranges():
        failures.append("report computed row ranges must be deterministic")
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

    payload_failures, row_ranges = validate_distribution_payload(config, schema)
    failures.extend(payload_failures)
    forbidden_failures, forbidden_artifacts_absent = validate_forbidden_artifacts(repo_root)
    failures.extend(forbidden_failures)
    failures.extend(validate_repair_pr_a(repo_root))
    failures.extend(validate_repair_pr_b_currentized(repo_root))
    upstream_failures, upstream_facts = validate_upstream_chain(repo_root)
    failures.extend(upstream_failures)
    failures.extend(manifest_gate.validate_static_surface(repo_root / "tools" / pathlib.Path(__file__).name))

    report = build_report(
        config=config,
        row_ranges=row_ranges,
        forbidden_artifacts_absent=forbidden_artifacts_absent,
        upstream_facts=upstream_facts,
        schema_path=schema_path,
        config_path=config_path,
        report_path=output_path,
    )
    second_report = build_report(
        config=copy.deepcopy(config),
        row_ranges=copy.deepcopy(row_ranges),
        forbidden_artifacts_absent=copy.deepcopy(forbidden_artifacts_absent),
        upstream_facts=copy.deepcopy(upstream_facts),
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
        description="Validate AtomicRows owner-approved exact 15-family count distribution."
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
