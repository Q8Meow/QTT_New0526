#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import copy
from dataclasses import dataclass
import json
import pathlib
import re
import sys
from typing import Any, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import build_atomicrows_bundle as builder  # noqa: E402
from tools import validate_atomicrows_bundle_builder_deterministic_assembly_gate as pr99_gate  # noqa: E402
from tools import validate_atomicrows_bundle_row_family_source_files as pr98_gate  # noqa: E402
from tools import validate_atomicrows_full_bundle_row_expansion_plan as pr97_gate  # noqa: E402
from src.qtt.core.testing.atomicrows_bundle_state import (  # noqa: E402
    canonical_atomicrows_bundle_presence,
)
from src.qtt.core.testing import atomicrows_sha_system_dormancy_state as sha_dormancy  # noqa: E402
from src.qtt.core.testing import qtt_final_readiness_dependency_policy as readiness_policy  # noqa: E402
from src.qtt.core.testing.atomicrows_sha_freeze_final_readiness_state import (  # noqa: E402
    validate_current_atomicrows_sha_freeze_final_readiness_state,
)
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)


DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_bundle_sha_freeze_authority_gate.schema.json"
)
DEFAULT_CONFIG = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsBundleShaFreezeAuthorityGate.yaml"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsBundleShaFreezeAuthorityGate.report.json"
)

ROADMAP_INDEX = pr98_gate.ROADMAP_INDEX
BLUEPRINT_INDEX = pr98_gate.BLUEPRINT_INDEX
MASTER_PLAN_CURRENT = pr97_gate.MASTER_PLAN_CURRENT
CANONICAL_BUNDLE_JSONL = builder.CANONICAL_BUNDLE_JSONL
CANONICAL_BUNDLE_SHA256 = builder.CANONICAL_BUNDLE_SHA256

REPORT_TYPE = "ATOMICROWS_BUNDLE_SHA_FREEZE_AUTHORITY_GATE_REPORT"
ARTIFACT_ID = "ATOMICROWS_BUNDLE_SHA_FREEZE_AUTHORITY_GATE"
ARTIFACT_VERSION = "v1"
ROADMAP_PR = "PR_100"
ROADMAP_DELIVERY_LABEL = "PR #100"
GITHUB_PR_NUMBER_POLICY = "may differ"
SEMANTIC_TASK_ID = "ROADMAP_ATOMICROWS_BUNDLE_SHA_FREEZE"
BLUEPRINT_SEMANTIC_TASK_ID = "ROADMAP-ATOMICROWS-BUNDLE-SHA-FREEZE-AUTHORITY"
AUTHORITY_CLASS = "STATIC_FAIL_CLOSED_SHA_FREEZE_GATE_NOT_SHA_AUTHORITY"
GATE_MODE = "BLOCKED"
TARGET_BRANCH = "pr100-atomicrows-bundle-sha-freeze-authority"
ROADMAP_SHORT_BRANCH_LABEL = TARGET_BRANCH
ROADMAP_GUIDANCE_MARKER = "QTT_ATOMICROWS_BUNDLE_SHA_FREEZE_AUTHORITY_OK"
EXPECTED_BASELINE_ANCESTOR = "89b89b3"
SUCCESS_MARKER = "QTT_ATOMICROWS_BUNDLE_SHA_FREEZE_AUTHORITY_GATE_BLOCKED_OK"
FAILURE_MARKER = "QTT_ATOMICROWS_BUNDLE_SHA_FREEZE_AUTHORITY_GATE_FAILED"

CI_DETACHED_HEAD_MODE_MARKER = pr97_gate.CI_DETACHED_HEAD_MODE_MARKER
CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER = pr97_gate.CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER
DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER = (
    pr97_gate.DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER
)
BRANCH_CONTEXT_ENV_CANDIDATES = pr97_gate.BRANCH_CONTEXT_ENV_CANDIDATES

BLOCKED_REASON_CODES = (
    "ATOMICROWS_SHA_FREEZE_BLOCKED_SHA_SYSTEM_DORMANT_NON_PARTICIPATING_OWNER_CONTROLLED",
    "ATOMICROWS_SHA_FREEZE_BLOCKED_SHA_GENERATION_DISABLED_BY_DORMANCY_POLICY",
    "ATOMICROWS_SHA_FREEZE_BLOCKED_SHA_FREEZE_AUTHORITY_DISABLED_BY_DORMANCY_POLICY",
    "ATOMICROWS_SHA_FREEZE_BLOCKED_SHA_REACTIVATION_REQUIRES_FUTURE_OWNER_APPROVED_PR",
    "ATOMICROWS_SHA_FREEZE_BLOCKED_FINAL_READINESS_POLICY_ACTIVE_NON_SHA_GATES_ONLY",
    "ATOMICROWS_SHA_FREEZE_BLOCKED_PR99_PATH_B",
    "ATOMICROWS_SHA_FREEZE_BLOCKED_EXACT_SOURCE_ROWS_NOT_AUTHORIZED",
    "ATOMICROWS_SHA_FREEZE_BLOCKED_SOURCE_BLUEPRINTS_ONLY",
    "ATOMICROWS_SHA_FREEZE_BLOCKED_FINAL_READINESS_NOT_CREATED_BY_THIS_PR",
)
UPSTREAM_ARTIFACT_DEPENDENCIES = (
    "AtomicRowsFullBundleRowExpansionPlan",
    "AtomicRowsBundleRowFamilySourceFiles",
    "AtomicRowsBundleBuilderDeterministicAssemblyGate",
)
DOWNSTREAM_BLOCKED_UNTIL = ("ACTIVE_NON_SHA_DAY1_FINAL_READINESS_GATES",)
NO_CLAIM_FALSE_FIELDS = (
    "bundle_created",
    "bundle_sha256_created",
    "sha_computed",
    "freeze_authority_created",
    "final_readiness_created",
    "runtime_created",
    "live_authority_created",
    "order_authority_created",
    "source_acceptance_created",
    "connector_semantics_created",
    "replay_or_paper_executed",
    "optimizer_executed",
    "quantum_backend_executed",
    "profit_evidence_created",
    "latency_evidence_created",
    "quantum_advantage_claimed",
    "external_facts_retrieved",
    "accepted_source_packets_created",
    "runtime_cash_receipts_created",
    "account_order_fill_receipts_created",
    "backend_outputs_created",
    "execution_superiority_evidence_created",
    "quantum_simulator_executed",
    "quantum_provider_called",
)
QUANTUM_TRUE_FIELDS = (
    "preserves_quantum_advisory_rows",
    "preserves_qubo_ising_metadata_rows",
    "preserves_qaoa_vqe_annealing_metadata_rows",
    "preserves_quantum_portfolio_hybrid_comparator_rows",
)
QUANTUM_FALSE_FIELDS = (
    "quantum_execution_allowed",
    "quantum_advantage_claim_allowed",
    "qubo_solving_allowed",
    "ising_solving_allowed",
    "qaoa_execution_allowed",
    "vqe_execution_allowed",
    "annealing_execution_allowed",
    "quantum_simulator_allowed",
    "quantum_provider_call_allowed",
    "optimizer_execution_allowed",
)
FORBIDDEN_EXECUTION_EFFECTS = (
    "QAOA_EXECUTION",
    "VQE_EXECUTION",
    "ANNEALING_EXECUTION",
    "QUBO_SOLVING",
    "ISING_SOLVING",
    "QUANTUM_INSPIRED_OPTIMIZER_EXECUTION",
    "TRUE_QUANTUM_BACKEND_EXECUTION",
    "QUANTUM_SIMULATOR_EXECUTION",
    "QUANTUM_PROVIDER_CALL",
    "QUANTUM_ADVANTAGE_VALIDATION",
    "QUANTUM_DIRECT_ORDER_AUTHORITY",
)
OWNER_APPROVAL_CANNOT_FABRICATE = (
    "EXTERNAL_FACTS",
    "ACCEPTED_SOURCE_PACKETS",
    "RUNTIME_CASH_RECEIPTS",
    "ACCOUNT_ORDER_FILL_RECEIPTS",
    "REPLAY_RESULTS",
    "PAPER_RESULTS",
    "BUNDLE_ROWS",
    "SHA_FREEZE_AUTHORITY",
    "BACKEND_OUTPUTS",
    "PROFIT_EVIDENCE",
    "LATENCY_EVIDENCE",
    "EXECUTION_SUPERIORITY_EVIDENCE",
    "QUANTUM_ADVANTAGE_EVIDENCE",
)
ADDITIONAL_FORBIDDEN_ARTIFACT_PATHS = (
    (
        pathlib.Path("tools") / "build_atomicrows_full_bundle.py",
        "forbidden full bundle materializer exists",
    ),
    (
        pathlib.Path("tools") / "validate_atomicrows_full_bundle_final_readiness_gate.py",
        "forbidden final readiness validator exists",
    ),
    (
        pathlib.Path("docs")
        / "master_plan"
        / "atomic_rows"
        / "AtomicRowsBundleFreezeAuthority.yaml",
        "forbidden SHA/freeze authority artifact exists",
    ),
    (
        pathlib.Path("docs")
        / "master_plan"
        / "generated"
        / "AtomicRowsFullBundleFinalReadinessGate.report.json",
        "forbidden final readiness artifact exists",
    ),
)
SIMULATED_BUNDLE_FORBIDDEN_ARTIFACTS = (
    (CANONICAL_BUNDLE_SHA256, "forbidden AtomicRows bundle hash exists"),
)
FORBIDDEN_STATIC_SURFACE_IMPORT_ROOTS = (
    "hashlib",
    "requests",
    "qiskit",
    "dwave",
    "cirq",
    "pennylane",
    "dimod",
    "neal",
)
FORBIDDEN_CALL_NAMES = (
    "builder.main",
    "builder.materialize_bundle_if_allowed",
    "materialize_bundle_if_allowed",
)
DIGEST_VALUE_KEYS = {
    "actual_sha256_value",
    "digest_value",
    "sha256_digest_value",
    "bundle_sha256_value",
    "bundle_digest_value",
    "deterministic_order_hash_or_digest",
}
SHA256_HEX_RE = re.compile(r"\b[0-9a-fA-F]{64}\b")


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]
    report: dict[str, Any] | None
    info_lines: tuple[str, ...] = ()


def _resolve(root: pathlib.Path, path: pathlib.Path) -> pathlib.Path:
    return path if path.is_absolute() else root / path


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return pr99_gate.load_json(path)


def load_yaml(path: pathlib.Path) -> dict[str, Any]:
    return pr99_gate.load_yaml(path)


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_json_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def _load_json_checked(path: pathlib.Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        return load_json(path), []
    except FileNotFoundError:
        return None, [f"{label} missing: {path.as_posix()}"]
    except (json.JSONDecodeError, ValueError) as exc:
        return None, [f"{label} invalid JSON: {path.as_posix()}: {exc}"]


def _load_yaml_checked(path: pathlib.Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        return load_yaml(path), []
    except FileNotFoundError:
        return None, [f"{label} missing: {path.as_posix()}"]
    except ValueError as exc:
        return None, [f"{label} invalid YAML/JSON: {path.as_posix()}: {exc}"]


def schema_subset_failures(payload: dict[str, Any], schema: dict[str, Any], label: str) -> list[str]:
    return [f"{label} {failure}" for failure in validate_json_schema_subset(payload, schema)]


def _downstream_validation_branch_allowed(branch: str) -> bool:
    match = re.match(r"pr(?P<number>[0-9]+)[a-z]*-", branch)
    if not match:
        return False
    return int(match.group("number")) > 100


def _main_cumulative_branch_allowed(branch: str) -> bool:
    return branch == "main" or branch.startswith("repair/main-cumulative-")


def _downstream_or_main_validation_branch_allowed(branch: str) -> bool:
    return _main_cumulative_branch_allowed(branch) or _downstream_validation_branch_allowed(
        branch
    )


def _should_skip_default_report_write(
    *,
    repo_root: pathlib.Path,
    output_abs: pathlib.Path,
    metadata: dict[str, Any],
) -> bool:
    if output_abs != _resolve(repo_root, DEFAULT_REPORT):
        return False
    branch = str(metadata.get("branch") or "")
    return branch not in {TARGET_BRANCH, "main"}


def validate_roadmap_metadata(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    info_lines: list[str] = []
    roadmap = load_json(_resolve(repo_root, ROADMAP_INDEX))
    blueprint = load_json(_resolve(repo_root, BLUEPRINT_INDEX))
    roadmap_entry = next(
        (
            item
            for item in _list_of_mappings(roadmap.get("pr_entries"))
            if item.get("number") == 100
        ),
        None,
    )
    blueprint_entry = next(
        (
            item
            for item in _list_of_mappings(blueprint.get("entries"))
            if item.get("number") == 100
        ),
        None,
    )
    if roadmap_entry is None:
        failures.append("PR100 roadmap index entry missing")
        roadmap_entry = {}
    if blueprint_entry is None:
        failures.append("PR100 blueprint index entry missing")
        blueprint_entry = {}

    checks = (
        ("roadmap.delivery_label", roadmap_entry.get("delivery_label"), ROADMAP_DELIVERY_LABEL),
        ("roadmap.title", roadmap_entry.get("title"), "AtomicRows bundle SHA/freeze authority"),
        ("roadmap.branch", roadmap_entry.get("branch"), ROADMAP_SHORT_BRANCH_LABEL),
        ("roadmap.marker", roadmap_entry.get("marker"), ROADMAP_GUIDANCE_MARKER),
        ("blueprint.delivery_label", blueprint_entry.get("delivery_label"), ROADMAP_DELIVERY_LABEL),
        ("blueprint.title", blueprint_entry.get("title"), "AtomicRows bundle SHA/freeze authority"),
        ("blueprint.branch", blueprint_entry.get("branch"), ROADMAP_SHORT_BRANCH_LABEL),
        ("blueprint.validator_marker", blueprint_entry.get("validator_marker"), ROADMAP_GUIDANCE_MARKER),
        ("blueprint.semantic_task_id", blueprint_entry.get("semantic_task_id"), BLUEPRINT_SEMANTIC_TASK_ID),
        ("blueprint.category", blueprint_entry.get("category"), "STATIC"),
        ("blueprint.stage", blueprint_entry.get("stage"), "AtomicRows bundle preparation"),
        ("blueprint.priority", blueprint_entry.get("priority"), "S1 launch-essential static"),
    )
    for label, actual, expected in checks:
        if actual != expected:
            failures.append(f"{label} must be {expected}, got {actual}")

    branch_context = pr98_gate._current_branch_context(repo_root)
    branch = branch_context.branch
    if not branch:
        if pr98_gate._github_actions_active():
            info_lines.append(CI_DETACHED_HEAD_MODE_MARKER)
        else:
            branch_err = branch_context.git_error or "unable to determine current branch"
            failures.append(f"git branch check failed: {branch_err}")
    elif branch != TARGET_BRANCH:
        if _main_cumulative_branch_allowed(branch):
            pass
        elif _downstream_validation_branch_allowed(branch):
            info_lines.append(DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER)

    head_rc, head, head_err = pr98_gate._git_stdout(repo_root, ["rev-parse", "--short", "HEAD"])
    if head_rc != 0:
        failures.append(f"git HEAD check failed: {head_err}")
        head = ""
    baseline_rc, _, baseline_err = pr98_gate._git_stdout(
        repo_root, ["cat-file", "-e", f"{EXPECTED_BASELINE_ANCESTOR}^{{commit}}"]
    )
    if pr98_gate._github_actions_active() and baseline_rc != 0:
        info_lines.append(CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER)
    elif baseline_rc != 0:
        failures.append(f"baseline commit missing: {EXPECTED_BASELINE_ANCESTOR}: {baseline_err}")
    else:
        ancestor_rc, _, ancestor_err = pr98_gate._git_stdout(
            repo_root, ["merge-base", "--is-ancestor", EXPECTED_BASELINE_ANCESTOR, "HEAD"]
        )
        if ancestor_rc != 0:
            failures.append(f"HEAD must descend from {EXPECTED_BASELINE_ANCESTOR}: {ancestor_err}")

    return failures, {
        "roadmap_pr": ROADMAP_PR,
        "roadmap_delivery_label": ROADMAP_DELIVERY_LABEL,
        "github_pr_number_policy": GITHUB_PR_NUMBER_POLICY,
        "branch": branch,
        "branch_context_source": branch_context.source,
        "base_head": head,
        "expected_baseline_ancestor": EXPECTED_BASELINE_ANCESTOR,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "blueprint_semantic_task_id": blueprint_entry.get("semantic_task_id"),
        "blueprint_semantic_task_id_source": "roadmap blueprint guidance",
        "owner_selected_branch": TARGET_BRANCH,
        "roadmap_short_branch_label": ROADMAP_SHORT_BRANCH_LABEL,
        "branch_name_policy": "OWNER_SELECTED_BRANCH_MATCHES_ROADMAP_SHORT_LABEL",
        "roadmap_guidance_marker": ROADMAP_GUIDANCE_MARKER,
        "current_blocked_stdout_marker": SUCCESS_MARKER,
        "marker_policy": "OWNER_PROMPT_BLOCKED_GATE_MARKER_CONTROLS_CURRENT_PR100_VALIDATOR",
        "ci_info_lines": tuple(info_lines),
    }


def validate_no_digest_values(payload: Any, label: str = "PAYLOAD") -> list[str]:
    failures: list[str] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                if key in DIGEST_VALUE_KEYS and child is not None:
                    failures.append(f"{label}.{child_path} must be null in blocked mode")
                walk(child, child_path)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{path}[{index}]")
        elif isinstance(value, str) and SHA256_HEX_RE.search(value):
            failures.append(f"{label}.{path} contains a forbidden SHA-256 digest-looking value")

    walk(payload, "")
    return failures


def validate_config_payload(config: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    failures.extend(schema_subset_failures(config, schema, "CONFIG"))

    expected = _mapping(config.get("expected_current_state"))
    canonical_paths = _mapping(config.get("canonical_paths"))
    no_claims = _mapping(config.get("no_claims"))
    quantum = _mapping(config.get("quantum_forward_static_metadata"))
    owner_boundary = _mapping(config.get("owner_authority_boundary"))
    planning_target = _mapping(config.get("planning_target"))

    checks = (
        ("artifact_id", config.get("artifact_id"), ARTIFACT_ID),
        ("artifact_version", config.get("artifact_version"), ARTIFACT_VERSION),
        ("roadmap_pr", config.get("roadmap_pr"), ROADMAP_PR),
        ("roadmap_delivery_label", config.get("roadmap_delivery_label"), ROADMAP_DELIVERY_LABEL),
        ("semantic_task_id", config.get("semantic_task_id"), SEMANTIC_TASK_ID),
        ("authority_class", config.get("authority_class"), AUTHORITY_CLASS),
        ("gate_mode", config.get("gate_mode"), GATE_MODE),
        (
            "canonical_paths.atomicrows_bundle_path",
            canonical_paths.get("atomicrows_bundle_path"),
            CANONICAL_BUNDLE_JSONL.as_posix(),
        ),
        (
            "canonical_paths.atomicrows_bundle_sha256_path",
            canonical_paths.get("atomicrows_bundle_sha256_path"),
            CANONICAL_BUNDLE_SHA256.as_posix(),
        ),
        ("actual_sha256_value", config.get("actual_sha256_value"), None),
        ("digest_value", config.get("digest_value"), None),
        ("planning_target.target_total_row_count", planning_target.get("target_total_row_count"), 4183),
        (
            "planning_target.target_total_row_count_planning_authority_only",
            planning_target.get("target_total_row_count_planning_authority_only"),
            True,
        ),
        (
            "planning_target.materialized_row_count_claimed",
            planning_target.get("materialized_row_count_claimed"),
            False,
        ),
    )
    for label, actual, expected_value in checks:
        if actual != expected_value:
            failures.append(f"config.{label} must be {expected_value!r}, got {actual!r}")

    expected_checks = (
        ("atomicrows_bundle_jsonl_exists", True),
        ("atomicrows_bundle_sha256_exists", False),
        (
            "sha_system_dormancy_state",
            "SHA_SYSTEM_DORMANT_NON_PARTICIPATING_OWNER_CONTROLLED",
        ),
        ("sha_system_non_participating_for_final_readiness", True),
        (
            "final_readiness_dependency_policy_state",
            "FINAL_READINESS_DEPENDENCY_POLICY_ACTIVE_NON_SHA_GATES_ONLY",
        ),
        ("sha_required_for_final_readiness", False),
        ("sha_dormancy_is_final_readiness_blocker", False),
        ("sha_absence_is_final_readiness_blocker", False),
        ("sha_presence_is_final_readiness_evidence", False),
        ("exact_source_rows_authorized", False),
        ("pr99_assembly_path", "PATH_B_BLOCKED"),
        ("pr98_source_files_are_blueprints_only", True),
        ("sha_materialization_allowed", False),
        ("sha_generation_allowed", False),
        ("sha_freeze_authority_allowed", False),
        ("freeze_authority_created", False),
        ("final_readiness_created", False),
    )
    for field, expected_value in expected_checks:
        if expected.get(field) != expected_value:
            failures.append(f"expected_current_state.{field} must be {expected_value!r}")

    if expected.get("atomicrows_bundle_jsonl_exists") is not True:
        failures.append("PR113 materialized bundle state must be explicit")
    if expected.get("exact_source_rows_authorized") is False and expected.get("sha_materialization_allowed") is not False:
        failures.append("unauthorized exact rows must force sha_materialization_allowed=false")
    if expected.get("pr99_assembly_path") == "PATH_B_BLOCKED" and config.get("gate_mode") != GATE_MODE:
        failures.append("PR99 Path B must force gate_mode=BLOCKED")

    if config.get("blocked_reason_codes") != list(BLOCKED_REASON_CODES):
        failures.append("blocked_reason_codes must exactly match PR100 blocked SHA/freeze reasons")
    if config.get("upstream_artifact_dependencies") != list(UPSTREAM_ARTIFACT_DEPENDENCIES):
        failures.append("upstream_artifact_dependencies must exactly match PR97-PR99 dependencies")
    if config.get("downstream_blocked_until") != list(DOWNSTREAM_BLOCKED_UNTIL):
        failures.append("downstream_blocked_until must keep PR101 final readiness blocked")
    if config.get("outputs_created_by_this_pr") != []:
        failures.append("outputs_created_by_this_pr must be empty")
    if CANONICAL_BUNDLE_SHA256.as_posix() in set(config.get("outputs_created_by_this_pr") or []):
        failures.append("AtomicRows.bundle.sha256 must not be an output created by PR100")

    for field in NO_CLAIM_FALSE_FIELDS:
        if no_claims.get(field) is not False:
            failures.append(f"no_claims.{field} must be false")
    for field in QUANTUM_TRUE_FIELDS:
        if quantum.get(field) is not True:
            failures.append(f"quantum_forward_static_metadata.{field} must be true")
    for field in QUANTUM_FALSE_FIELDS:
        if quantum.get(field) is not False:
            failures.append(f"quantum_forward_static_metadata.{field} must be false")
    for effect in FORBIDDEN_EXECUTION_EFFECTS:
        if effect not in set(config.get("forbidden_execution_effects") or []):
            failures.append(f"forbidden_execution_effects missing {effect}")
    for fabricated in OWNER_APPROVAL_CANNOT_FABRICATE:
        if fabricated not in set(owner_boundary.get("owner_approval_cannot_fabricate") or []):
            failures.append(f"owner_authority_boundary missing non-fabrication item {fabricated}")
    for field in (
        "owner_global_internal_workflow_authority_preserved",
        "owner_approval_may_approve_future_internal_workflow_movement",
        "owner_approval_does_not_create_sha_freeze_truth",
    ):
        if owner_boundary.get(field) is not True:
            failures.append(f"owner_authority_boundary.{field} must be true")

    failures.extend(validate_no_digest_values(config, "CONFIG"))
    return failures


def validate_upstream_state(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    pr97_report, pr97_failures = _load_json_checked(
        _resolve(repo_root, pr98_gate.PR97_REPORT_PATH), "PR97_REPORT"
    )
    pr98_report, pr98_failures = _load_json_checked(
        _resolve(repo_root, builder.PR98_REPORT_PATH), "PR98_REPORT"
    )
    pr99_config, pr99_config_failures = _load_yaml_checked(
        _resolve(repo_root, pr99_gate.DEFAULT_BUILDER_CONFIG), "PR99_CONFIG"
    )
    pr99_report, pr99_report_failures = _load_json_checked(
        _resolve(repo_root, pr99_gate.DEFAULT_REPORT), "PR99_REPORT"
    )
    failures.extend(pr97_failures)
    failures.extend(pr98_failures)
    failures.extend(pr99_config_failures)
    failures.extend(pr99_report_failures)

    inputs, input_failures = builder.load_bundle_inputs(
        repo_root=repo_root,
        builder_config_path=pr99_gate.DEFAULT_BUILDER_CONFIG,
    )
    failures.extend(input_failures)

    if pr97_report and pr97_report.get("validation_marker") != pr97_gate.SUCCESS_MARKER:
        failures.append("PR97 report validation marker mismatch")
    if pr98_report and pr98_report.get("validation_marker") != pr98_gate.SUCCESS_MARKER:
        failures.append("PR98 report validation marker mismatch")
    if pr99_report and pr99_report.get("validation_marker") != pr99_gate.SUCCESS_MARKER:
        failures.append("PR99 report validation marker mismatch")

    pr99_path = "PATH_B_BLOCKED"
    if pr99_config and pr99_config.get("build_path_decision") != builder.PATH_DECISION:
        failures.append("PR99 config build_path_decision must preserve Path B blocked assembly")
    if pr99_report and pr99_report.get("build_path_decision") != builder.PATH_DECISION:
        failures.append("PR99 report build_path_decision must preserve Path B blocked assembly")

    source_file_count_found = 0
    source_blueprints_found_count = 0
    exact_source_rows_found_count = 0
    source_file_entries: list[dict[str, Any]] = []
    quantum_metadata_refs: list[str] = []
    if inputs is not None:
        summary = inputs.source_summary
        source_file_count_found = len(summary.source_files)
        source_blueprints_found_count = len(summary.blueprints)
        exact_source_rows_found_count = len(summary.exact_rows)
        quantum_metadata_refs = list(summary.quantum_metadata_refs_found)
        source_file_entries = builder.source_file_report_entries(inputs)
        if source_file_count_found != 15:
            failures.append(f"PR98 source file count must be 15, got {source_file_count_found}")
        if source_blueprints_found_count != 15:
            failures.append(
                f"PR98 source blueprint count must be 15, got {source_blueprints_found_count}"
            )
        if exact_source_rows_found_count != 0:
            failures.append(
                f"exact source rows must remain absent, got {exact_source_rows_found_count}"
            )
        if summary.missing_source_files:
            failures.append("PR98 source files missing: " + ", ".join(summary.missing_source_files))
        if summary.unknown_source_files:
            failures.append("unknown PR98 source files found: " + ", ".join(summary.unknown_source_files))
        if builder.build_allowed(inputs):
            failures.append("PR99 builder inputs must remain blocked and non-materializable")
        block_reasons = set(builder.build_block_reason_codes(inputs))
        for reason in pr99_gate.BLOCKED_REASON_CODES:
            if reason not in block_reasons:
                failures.append(f"PR99 Path B reason missing from live source summary: {reason}")

    return failures, {
        "pr97_report_marker": (pr97_report or {}).get("validation_marker"),
        "pr98_report_marker": (pr98_report or {}).get("validation_marker"),
        "pr99_report_marker": (pr99_report or {}).get("validation_marker"),
        "pr99_assembly_path": pr99_path,
        "pr99_build_path_decision": (pr99_report or {}).get("build_path_decision"),
        "pr99_build_allowed_flag": (pr99_report or {}).get("build_allowed_flag"),
        "pr99_build_blocked_flag": (pr99_report or {}).get("build_blocked_flag"),
        "source_file_count_found": source_file_count_found,
        "source_blueprints_found_count": source_blueprints_found_count,
        "exact_source_rows_found_count": exact_source_rows_found_count,
        "source_file_entries": source_file_entries,
        "quantum_metadata_refs": quantum_metadata_refs,
    }


def validate_no_forbidden_artifacts(
    repo_root: pathlib.Path,
    *,
    extra_existing_paths: Sequence[pathlib.Path] = (),
) -> list[str]:
    failures: list[str] = validate_current_atomicrows_sha_freeze_final_readiness_state(
        repo_root,
        label="AtomicRows bundle SHA/freeze authority gate",
    )
    extra_set = {path.as_posix() for path in extra_existing_paths}
    for relative_path, message in SIMULATED_BUNDLE_FORBIDDEN_ARTIFACTS:
        if relative_path.as_posix() in extra_set:
            failures.append(f"{message}: {relative_path.as_posix()}")
    for relative_path, message in ADDITIONAL_FORBIDDEN_ARTIFACT_PATHS:
        exists = _resolve(repo_root, relative_path).exists() or relative_path.as_posix() in extra_set
        if exists:
            failures.append(f"{message}: {relative_path.as_posix()}")
    for directory in (
        pathlib.Path("docs") / "master_plan" / "atomic_rows",
        pathlib.Path("docs") / "master_plan" / "atomicrows",
    ):
        directory_abs = _resolve(repo_root, directory)
        if directory_abs.exists():
            for path in directory_abs.rglob("*.sha256"):
                rel = path.relative_to(repo_root).as_posix()
                if rel == CANONICAL_BUNDLE_SHA256.as_posix():
                    continue
                failures.append(f"forbidden AtomicRows hash file exists: {rel}")
    return failures


def validate_master_plan_not_modified(repo_root: pathlib.Path) -> list[str]:
    return pr98_gate.validate_master_plan_not_modified(repo_root)


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def validate_static_surface(path: pathlib.Path) -> list[str]:
    failures: list[str] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return [f"{path.as_posix()} is not valid Python: {exc}"]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FORBIDDEN_STATIC_SURFACE_IMPORT_ROOTS:
                    failures.append(f"{path.name} imports forbidden runtime/quantum module {root}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".")[0]
            if root in FORBIDDEN_STATIC_SURFACE_IMPORT_ROOTS:
                failures.append(f"{path.name} imports forbidden runtime/quantum module {root}")
        elif isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name in FORBIDDEN_CALL_NAMES:
                failures.append(f"{path.name} calls forbidden materializing function {call_name}")
    return failures


def build_report(
    *,
    config: dict[str, Any],
    upstream: dict[str, Any],
    metadata: dict[str, Any],
    repo_root: pathlib.Path,
    schema_path: pathlib.Path,
    config_path: pathlib.Path,
    report_path: pathlib.Path,
) -> dict[str, Any]:
    presence = canonical_atomicrows_bundle_presence(repo_root)
    bundle_exists = presence.bundle_jsonl_exists
    sha_exists = presence.bundle_sha256_exists
    no_claims = copy.deepcopy(_mapping(config.get("no_claims")))
    quantum = copy.deepcopy(_mapping(config.get("quantum_forward_static_metadata")))
    return {
        "report_type": REPORT_TYPE,
        "artifact_id": ARTIFACT_ID,
        "artifact_version": ARTIFACT_VERSION,
        "roadmap_pr": ROADMAP_PR,
        "roadmap_delivery_label": ROADMAP_DELIVERY_LABEL,
        "github_pr_number_policy": GITHUB_PR_NUMBER_POLICY,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "blueprint_semantic_task_id": metadata.get("blueprint_semantic_task_id"),
        "authority_class": AUTHORITY_CLASS,
        "gate_mode": GATE_MODE,
        "validation_result": "PASS_BLOCKED_EXPECTED",
        "generated_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "validation_marker": SUCCESS_MARKER,
        "validator_stdout_marker": SUCCESS_MARKER,
        "roadmap_guidance_marker": metadata.get("roadmap_guidance_marker"),
        "marker_policy": metadata.get("marker_policy"),
        "branch": metadata.get("branch"),
        "branch_context_source": metadata.get("branch_context_source"),
        "base_head": metadata.get("base_head"),
        "expected_baseline_ancestor": metadata.get("expected_baseline_ancestor"),
        "owner_selected_branch": metadata.get("owner_selected_branch"),
        "roadmap_short_branch_label": metadata.get("roadmap_short_branch_label"),
        "branch_name_policy": metadata.get("branch_name_policy"),
        "schema_path": schema_path.as_posix(),
        "config_path": config_path.as_posix(),
        "report_path": report_path.as_posix(),
        "canonical_paths": copy.deepcopy(config.get("canonical_paths")),
        "atomicrows_bundle_jsonl_exists": bundle_exists,
        "atomicrows_bundle_sha256_exists": sha_exists,
        "sha_system_dormancy_state": sha_dormancy.get_atomicrows_sha_system_dormancy_state(),
        "sha_system_non_participating_for_final_readiness": (
            sha_dormancy.is_sha_system_non_participating_for_final_readiness()
        ),
        "final_readiness_dependency_policy_state": (
            readiness_policy.get_qtt_final_readiness_dependency_policy_state()
        ),
        "sha_required_for_final_readiness": (
            readiness_policy.is_sha_required_for_final_readiness()
        ),
        "sha_dormancy_is_final_readiness_blocker": (
            readiness_policy.is_sha_dormancy_a_final_readiness_blocker()
        ),
        "sha_absence_is_final_readiness_blocker": False,
        "sha_presence_is_final_readiness_evidence": False,
        "sha_materialization_allowed": False,
        "sha_generation_allowed": sha_dormancy.is_sha_generation_allowed(),
        "sha_freeze_authority_allowed": sha_dormancy.is_sha_freeze_authority_allowed(),
        "sha_file_created": False,
        "sha_computation_attempted": False,
        "sha_computed": False,
        "missing_bundle_digest_computation_blocked": not bundle_exists,
        "actual_sha256_value": None,
        "digest_value": None,
        "freeze_authority_created": False,
        "final_readiness_created": False,
        "outputs_created_by_this_pr": [],
        "blocked_reason_codes": list(BLOCKED_REASON_CODES),
        "forbidden_artifacts_absent": {
            "AtomicRows.bundle.jsonl": not bundle_exists,
            "AtomicRows.bundle.sha256": not sha_exists,
        },
        "no_claims_confirmed": no_claims,
        "quantum_static_metadata_confirmed": quantum,
        "forbidden_execution_effects": list(FORBIDDEN_EXECUTION_EFFECTS),
        "owner_authority_boundary": copy.deepcopy(config.get("owner_authority_boundary")),
        "planning_target": copy.deepcopy(config.get("planning_target")),
        "upstream_artifact_dependencies": list(UPSTREAM_ARTIFACT_DEPENDENCIES),
        "downstream_blocked_until": list(DOWNSTREAM_BLOCKED_UNTIL),
        "upstream_status": {
            "pr97_report_marker": upstream.get("pr97_report_marker"),
            "pr98_report_marker": upstream.get("pr98_report_marker"),
            "pr99_report_marker": upstream.get("pr99_report_marker"),
            "pr99_assembly_path": upstream.get("pr99_assembly_path"),
            "pr99_build_path_decision": upstream.get("pr99_build_path_decision"),
            "pr99_build_allowed_flag": upstream.get("pr99_build_allowed_flag"),
            "pr99_build_blocked_flag": upstream.get("pr99_build_blocked_flag"),
            "pr98_source_files_are_blueprints_only": True,
            "source_file_count_found": upstream.get("source_file_count_found"),
            "source_blueprints_found_count": upstream.get("source_blueprints_found_count"),
            "exact_source_rows_found_count": upstream.get("exact_source_rows_found_count"),
            "source_file_entries": upstream.get("source_file_entries"),
            "quantum_metadata_refs": upstream.get("quantum_metadata_refs"),
        },
        "downstream_status": {
            "roadmap_pr101_final_readiness_gate": (
                "NOT_CREATED_BY_THIS_PR_ACTIVE_NON_SHA_GATES_CONTROL_DAY1_FINAL_READINESS"
            )
        },
        "future_consumer_notes": config.get("future_consumer_notes"),
    }


def validate_report_is_deterministic(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    first = serialize_report(report)
    second = serialize_report(copy.deepcopy(report))
    if first != second:
        failures.append("generated report serialization is not byte-stable")
    if report.get("generated_at_utc") != "STATIC_DETERMINISTIC_NO_WALL_CLOCK":
        failures.append("generated report must use deterministic generated_at_utc sentinel")
    forbidden_patterns = (
        re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),
        re.compile(r"\b20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"),
        re.compile(r"[A-Za-z]:\\\\"),
        re.compile(r"\\\\"),
    )
    for pattern in forbidden_patterns:
        if pattern.search(first):
            failures.append("generated report contains nondeterministic or platform-specific content")
            break
    return failures


def validate_report(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    checks = (
        ("report_type", report.get("report_type"), REPORT_TYPE),
        ("artifact_id", report.get("artifact_id"), ARTIFACT_ID),
        ("roadmap_pr", report.get("roadmap_pr"), ROADMAP_PR),
        ("semantic_task_id", report.get("semantic_task_id"), SEMANTIC_TASK_ID),
        ("gate_mode", report.get("gate_mode"), GATE_MODE),
        ("validation_result", report.get("validation_result"), "PASS_BLOCKED_EXPECTED"),
        (
            "sha_system_dormancy_state",
            report.get("sha_system_dormancy_state"),
            "SHA_SYSTEM_DORMANT_NON_PARTICIPATING_OWNER_CONTROLLED",
        ),
        (
            "sha_system_non_participating_for_final_readiness",
            report.get("sha_system_non_participating_for_final_readiness"),
            True,
        ),
        (
            "final_readiness_dependency_policy_state",
            report.get("final_readiness_dependency_policy_state"),
            "FINAL_READINESS_DEPENDENCY_POLICY_ACTIVE_NON_SHA_GATES_ONLY",
        ),
        (
            "sha_required_for_final_readiness",
            report.get("sha_required_for_final_readiness"),
            False,
        ),
        (
            "sha_dormancy_is_final_readiness_blocker",
            report.get("sha_dormancy_is_final_readiness_blocker"),
            False,
        ),
        (
            "sha_absence_is_final_readiness_blocker",
            report.get("sha_absence_is_final_readiness_blocker"),
            False,
        ),
        (
            "sha_presence_is_final_readiness_evidence",
            report.get("sha_presence_is_final_readiness_evidence"),
            False,
        ),
        ("sha_materialization_allowed", report.get("sha_materialization_allowed"), False),
        ("sha_generation_allowed", report.get("sha_generation_allowed"), False),
        (
            "sha_freeze_authority_allowed",
            report.get("sha_freeze_authority_allowed"),
            False,
        ),
        ("sha_file_created", report.get("sha_file_created"), False),
        ("sha_computation_attempted", report.get("sha_computation_attempted"), False),
        ("sha_computed", report.get("sha_computed"), False),
        (
            "missing_bundle_digest_computation_blocked",
            report.get("missing_bundle_digest_computation_blocked"),
            False,
        ),
        ("actual_sha256_value", report.get("actual_sha256_value"), None),
        ("digest_value", report.get("digest_value"), None),
        ("freeze_authority_created", report.get("freeze_authority_created"), False),
        ("final_readiness_created", report.get("final_readiness_created"), False),
        ("validator_stdout_marker", report.get("validator_stdout_marker"), SUCCESS_MARKER),
    )
    for label, actual, expected_value in checks:
        if actual != expected_value:
            failures.append(f"report.{label} must be {expected_value!r}, got {actual!r}")

    if report.get("blocked_reason_codes") != list(BLOCKED_REASON_CODES):
        failures.append("report.blocked_reason_codes must exactly match PR100 blocked reasons")
    if report.get("outputs_created_by_this_pr") != []:
        failures.append("report.outputs_created_by_this_pr must be empty")
    forbidden_absent = _mapping(report.get("forbidden_artifacts_absent"))
    if forbidden_absent.get("AtomicRows.bundle.jsonl") not in {True, False}:
        failures.append("report must record AtomicRows.bundle.jsonl presence as boolean")
    if forbidden_absent.get("AtomicRows.bundle.sha256") is not True:
        failures.append("report must confirm AtomicRows.bundle.sha256 is absent")
    no_claims = _mapping(report.get("no_claims_confirmed"))
    for field in NO_CLAIM_FALSE_FIELDS:
        if no_claims.get(field) is not False:
            failures.append(f"report.no_claims_confirmed.{field} must be false")
    quantum = _mapping(report.get("quantum_static_metadata_confirmed"))
    for field in QUANTUM_TRUE_FIELDS:
        if quantum.get(field) is not True:
            failures.append(f"report.quantum_static_metadata_confirmed.{field} must be true")
    for field in QUANTUM_FALSE_FIELDS:
        if quantum.get(field) is not False:
            failures.append(f"report.quantum_static_metadata_confirmed.{field} must be false")
    upstream = _mapping(report.get("upstream_status"))
    if upstream.get("pr99_assembly_path") != "PATH_B_BLOCKED":
        failures.append("report.upstream_status.pr99_assembly_path must preserve PATH_B_BLOCKED")
    if upstream.get("exact_source_rows_found_count") != 0:
        failures.append("report must preserve zero exact source rows")
    if upstream.get("source_blueprints_found_count") != 15:
        failures.append("report must preserve 15 PR98 source blueprints")
    if _mapping(report.get("downstream_status")).get("roadmap_pr101_final_readiness_gate") != (
        "NOT_CREATED_BY_THIS_PR_ACTIVE_NON_SHA_GATES_CONTROL_DAY1_FINAL_READINESS"
    ):
        failures.append("report must defer Day-1 final readiness to active non-SHA gates")
    failures.extend(validate_no_digest_values(report, "REPORT"))
    failures.extend(validate_report_is_deterministic(report))
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
    failures.extend(schema_failures)
    failures.extend(config_failures)
    if schema is None or config is None:
        return ValidationResult(False, tuple(failures), None)

    metadata_failures, metadata = validate_roadmap_metadata(repo_root)
    info_lines = tuple(metadata.get("ci_info_lines", ()))
    failures.extend(metadata_failures)
    upstream_failures, upstream = validate_upstream_state(repo_root)
    failures.extend(upstream_failures)
    failures.extend(validate_config_payload(config, schema))
    if not sha_dormancy.is_sha_system_dormant():
        failures.append("central SHA system must remain dormant")
    if not sha_dormancy.is_sha_system_non_participating_for_final_readiness():
        failures.append("central SHA system must remain non-participating for final readiness")
    if sha_dormancy.is_sha_generation_allowed():
        failures.append("central SHA generation must remain disabled")
    if sha_dormancy.is_sha_freeze_authority_allowed():
        failures.append("central SHA/freeze authority must remain disabled")
    if readiness_policy.is_sha_required_for_final_readiness():
        failures.append("central final-readiness policy must not require SHA")
    if readiness_policy.is_sha_dormancy_a_final_readiness_blocker():
        failures.append("central final-readiness policy must not block on SHA dormancy")
    failures.extend(validate_no_forbidden_artifacts(repo_root))
    failures.extend(validate_master_plan_not_modified(repo_root))
    failures.extend(
        validate_static_surface(
            repo_root / pathlib.Path(__file__).relative_to(_REPO_ROOT)
        )
    )

    report = build_report(
        config=config,
        upstream=upstream,
        metadata=metadata,
        repo_root=repo_root,
        schema_path=schema_path,
        config_path=config_path,
        report_path=output_path,
    )
    expected_report = copy.deepcopy(report)
    failures.extend(validate_report(report))
    if report != expected_report:
        failures.append("PR100 report mutation check failed")

    if failures:
        return ValidationResult(False, tuple(failures), report, info_lines)

    if not _should_skip_default_report_write(
        repo_root=repo_root,
        output_abs=output_abs,
        metadata=metadata,
    ):
        write_json_report(report, output_abs)
    return ValidationResult(True, tuple(), report, info_lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate PR100 AtomicRows blocked bundle SHA/freeze authority gate."
    )
    parser.add_argument("--repo-root", type=pathlib.Path, default=pathlib.Path("."))
    parser.add_argument("--schema", type=pathlib.Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--config", type=pathlib.Path, default=DEFAULT_CONFIG)
    parser.add_argument("--out", dest="output_path", type=pathlib.Path, default=None)
    parser.add_argument("--report-out", dest="output_path", type=pathlib.Path)
    args = parser.parse_args(argv)

    result = validate(
        repo_root=args.repo_root,
        schema_path=args.schema,
        config_path=args.config,
        output_path=args.output_path or DEFAULT_REPORT,
    )
    if result.ok:
        print(SUCCESS_MARKER)
        for line in result.info_lines:
            print(line)
        return 0
    print(FAILURE_MARKER, file=sys.stderr)
    for line in result.info_lines:
        print(line, file=sys.stderr)
    for failure in result.failures:
        print(failure, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
