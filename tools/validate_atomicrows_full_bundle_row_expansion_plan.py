#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import json
import os
import pathlib
import re
import subprocess
import sys
from typing import Any, Iterable, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.build_master_plan_section_coverage_report import (  # noqa: E402
    RegistryParseError,
    load_yaml_subset,
)
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
    / "atomicrows_full_bundle_row_expansion_plan.schema.json"
)
DEFAULT_PRODUCTION_PLAN = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsFullBundleRowExpansionPlan.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "atomicrows"
    / "synthetic_atomicrows_full_bundle_row_expansion_plan.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsFullBundleRowExpansionPlan.report.json"
)

ROADMAP_INDEX = pathlib.Path("docs") / "roadmap" / "QTT_PRs_Roadmap_Index_v1_0.json"
BLUEPRINT_INDEX = (
    pathlib.Path("docs")
    / "roadmap"
    / "QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json"
)
MASTER_PLAN_CURRENT = pathlib.Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"
CANONICAL_BUNDLE_JSONL = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA256 = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.sha256"
)

REPORT_ID = "ATOMICROWS_FULL_BUNDLE_ROW_EXPANSION_PLAN_REPORT"
REPORT_VERSION = "v1"
ROADMAP_PR_LABEL = "PR #97"
GITHUB_PR_NUMBER_POLICY = "may differ"
SEMANTIC_TASK_ID = "ROADMAP-ATOMICROWS-BUNDLE-PLAN"
BLUEPRINT_SEMANTIC_TASK_ID = "ROADMAP-ATOMICROWS-FULL-BUNDLE-ROW-EXPANSION-PLAN"
TARGET_BRANCH = "pr97-atomicrows-full-bundle-row-expansion-plan"
EXPECTED_BASELINE_ANCESTOR = "1352bb9"
SUCCESS_MARKER = "QTT_ATOMICROWS_FULL_BUNDLE_ROW_EXPANSION_PLAN_OK"
FAILURE_MARKER = "QTT_ATOMICROWS_FULL_BUNDLE_ROW_EXPANSION_PLAN_FAILED"
AUTHORITY_CLASS = (
    "STATIC_ATOMICROWS_FULL_BUNDLE_ROW_EXPANSION_PLAN_ONLY_NOT_BUNDLE_NOT_HASH_"
    "NOT_FREEZE_NOT_RUNTIME_AUTHORITY"
)
TARGET_TOTAL_ROW_COUNT_AUTHORITY = (
    "MASTER_PLAN_0X_5F_LAUNCH_BASELINE_AND_COVERAGE_LEDGER"
)

CI_DETACHED_HEAD_MODE_MARKER = "CI_DETACHED_HEAD_BRANCH_CONTEXT_USED"
CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER = "CI_SHALLOW_FETCH_ANCESTRY_CHECK_SKIPPED"
DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER = (
    "DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE"
)
BRANCH_CONTEXT_ENV_CANDIDATES = (
    "GITHUB_HEAD_REF",
    "GITHUB_REF_NAME",
    "GITHUB_REF",
    "BRANCH_NAME",
    "CI_COMMIT_REF_NAME",
)

REQUIRED_PLAN_CONCEPTS = (
    "ATOMICROWS_FULL_BUNDLE_EXPANSION_PLAN",
    "ATOMICROWS_ROW_FAMILY_SPLIT_PLAN",
    "ATOMICROWS_GENERATION_SEQUENCE_PLAN",
    "ATOMICROWS_VALIDATION_MATRIX_PLAN",
    "ATOMICROWS_OWNER_APPROVAL_SEQUENCE_PLAN",
    "ATOMICROWS_QUANTUM_FORWARD_ROW_FAMILY_PLAN",
    "ATOMICROWS_FORBIDDEN_ARTIFACT_BOUNDARY_PLAN",
)
ROW_FAMILY_IDS = (
    "AR_FAMILY_001_SIGNAL_FEATURES",
    "AR_FAMILY_002_SCORING_RANKING",
    "AR_FAMILY_003_NORMALIZATION_CALIBRATION",
    "AR_FAMILY_004_RISK_CONTROL",
    "AR_FAMILY_005_EXECUTION_CONNECTOR_BOUNDARY",
    "AR_FAMILY_006_CAPITAL_SIZING_CASH",
    "AR_FAMILY_007_LATENCY_ROUTING",
    "AR_FAMILY_008_ERROR_GUARD_FAIL_CLOSED",
    "AR_FAMILY_009_LIFECYCLE_AGENT_BINDING",
    "AR_FAMILY_010_SOURCE_EVIDENCE_CONNECTOR_SEMANTIC",
    "AR_FAMILY_011_REPLAY_PAPER_VALIDATION",
    "AR_FAMILY_012_QUANTUM_ADVISORY_OPTIMIZATION",
    "AR_FAMILY_013_QUANTUM_QUBO_ISING_METADATA",
    "AR_FAMILY_014_QUANTUM_QAOA_VQE_ANNEALING_METADATA",
    "AR_FAMILY_015_QUANTUM_PORTFOLIO_HYBRID_COMPARATOR",
)
ROW_FAMILY_CLASSES = (
    "SIGNAL_FEATURE_FAMILY",
    "SCORING_RANKING_FAMILY",
    "NORMALIZATION_CALIBRATION_FAMILY",
    "RISK_CONTROL_FAMILY",
    "EXECUTION_CONNECTOR_BOUNDARY_FAMILY",
    "CAPITAL_SIZING_CASH_FAMILY",
    "LATENCY_ROUTING_FAMILY",
    "ERROR_GUARD_FAIL_CLOSED_FAMILY",
    "LIFECYCLE_AGENT_BINDING_FAMILY",
    "SOURCE_EVIDENCE_CONNECTOR_SEMANTIC_FAMILY",
    "REPLAY_PAPER_VALIDATION_FAMILY",
    "QUANTUM_ADVISORY_OPTIMIZATION_FAMILY",
    "QUANTUM_QUBO_ISING_METADATA_FAMILY",
    "QUANTUM_QAOA_VQE_ANNEALING_METADATA_FAMILY",
    "QUANTUM_PORTFOLIO_HYBRID_COMPARATOR_FAMILY",
)
VALIDATION_CLASSES = (
    "SCHEMA_COMPLIANCE",
    "ROW_FAMILY_COMPLETENESS",
    "ROW_ID_UNIQUENESS",
    "NO_DUPLICATE_ROW_IDS",
    "FAMILY_MEMBERSHIP_VALIDITY",
    "AGENT_BINDING_COMPATIBILITY",
    "LIFECYCLE_STATE_VALIDITY",
    "PARAMETER_STACK_ROLE_COVERAGE",
    "SELECTION_UNIVERSE_COVERAGE",
    "SCORING_RANKING_COMPATIBILITY",
    "REPLAY_PAPER_READINESS_GATING",
    "OWNER_OVERRIDE_OWNER_APPROVAL_GATING",
    "SOURCE_EVIDENCE_BOUNDARY_GATING",
    "CONNECTOR_SEMANTIC_BOUNDARY_GATING",
    "RUNTIME_LIVE_ORDER_BOUNDARY_GATING",
    "QUANTUM_METADATA_BOUNDARY_GATING",
    "BUNDLE_HASH_FREEZE_BOUNDARY_GATING",
)
GENERATION_SEQUENCE = (
    ("PR #98", "PR98_ROW_FAMILY_SOURCE_FILES"),
    ("PR #99", "PR99_BUNDLE_BUILDER"),
    ("PR #100", "PR100_SHA_FREEZE_AUTHORITY"),
    ("PR #101", "PR101_FINAL_READINESS"),
)
QUANTUM_METADATA_ENTRIES = (
    "QUANTUM_ADVISORY_ROW_FAMILIES",
    "QUANTUM_APPLICABILITY_METADATA",
    "QUBO_COMPATIBLE_METADATA",
    "ISING_COMPATIBLE_METADATA",
    "QAOA_COMPATIBLE_METADATA",
    "VQE_COMPATIBLE_METADATA",
    "ANNEALING_COMPATIBLE_METADATA",
    "QUANTUM_PORTFOLIO_OPTIMIZATION_METADATA",
    "HYBRID_CLASSICAL_QUANTUM_COMPARISON_METADATA",
    "OWNER_QUANTUM_PRIORITY_POLICY_REFERENCE",
)
FORBIDDEN_QUANTUM_EFFECTS = (
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

TRUE_FIELDS = (
    "static_only_flag",
    "planning_only_flag",
    "handoff_only_flag",
    "consumes_existing_atomicrows_schema_flag",
    "consumes_existing_lifecycle_gate_flag",
    "consumes_existing_agent_binding_gate_flag",
    "consumes_existing_parameter_stack_taxonomy_flag",
    "consumes_existing_selection_universe_gate_flag",
    "consumes_existing_quantum_applicability_registry_flag",
)
FALSE_FIELDS = (
    "target_total_row_count_created_by_pr97_flag",
    "bundle_file_created_flag",
    "bundle_sha_created_flag",
    "sha_authority_created_flag",
    "freeze_authority_created_flag",
    "row_family_source_files_created_flag",
    "row_records_created_flag",
    "bundle_builder_created_flag",
    "bundle_builder_executed_flag",
    "final_readiness_created_flag",
    "creates_runtime_live_authority_flag",
    "creates_order_authority_flag",
    "creates_source_fact_flag",
    "creates_connector_semantic_flag",
    "creates_runtime_cash_receipt_flag",
    "creates_replay_paper_result_flag",
    "creates_optimizer_execution_flag",
    "creates_quantum_backend_execution_flag",
    "creates_profit_evidence_flag",
    "creates_latency_evidence_flag",
    "creates_quantum_advantage_evidence_flag",
)
FAMILY_FALSE_FIELDS = (
    "source_file_created_by_pr97_flag",
    "row_records_created_by_pr97_flag",
    "exact_row_count_created_by_pr97_flag",
)
FORBIDDEN_EXACT_COUNT_FIELDS = (
    "exact_row_count",
    "planned_row_count",
    "target_row_count",
    "row_count",
    "allocated_row_count",
)
ALWAYS_FORBIDDEN_ARTIFACT_PATHS = (
    CANONICAL_BUNDLE_JSONL,
    CANONICAL_BUNDLE_SHA256,
    pathlib.Path("tools") / "build_atomicrows_full_bundle.py",
    pathlib.Path("tools") / "validate_atomicrows_full_bundle_final_readiness_gate.py",
    (
        pathlib.Path("docs")
        / "master_plan"
        / "generated"
        / "AtomicRowsFullBundleFinalReadinessGate.report.json"
    ),
    (
        pathlib.Path("docs")
        / "master_plan"
        / "atomic_rows"
        / "AtomicRowsBundleFreezeAuthority.yaml"
    ),
)
PR99_STATIC_BUILDER_ARTIFACT_PATHS = (
    pathlib.Path("tools") / "build_atomicrows_bundle.py",
)
MASTER_PLAN_TARGET_COUNT_ANCHORS = (
    "current_launch_baseline_atomic_row_count = 4183",
    "atomicrows_expected_row_count = 4183",
    "required_launch_baseline_jsonl_row_records = 4183",
)
REQUIRED_FIXTURE_CASE_IDS = (
    "FULL_BUNDLE_EXPANSION_PLAN_VALID_STATIC_ONLY",
    "BLOCK_MISSING_REQUIRED_PLAN_CONCEPT",
    "BLOCK_DUPLICATE_ROW_FAMILY_ID",
    "BLOCK_DUPLICATE_VALIDATION_ID",
    "BLOCK_UNSTABLE_ROW_FAMILY_ORDER",
    "BLOCK_UNSTABLE_VALIDATION_ORDER",
    "BLOCK_FABRICATED_EXACT_FAMILY_COUNT",
    "BLOCK_BUNDLE_JSONL_CREATION_FLAG",
    "BLOCK_BUNDLE_SHA_CREATION_FLAG",
    "BLOCK_ROW_FAMILY_SOURCE_FILE_CREATION_FLAG",
    "BLOCK_BUNDLE_BUILDER_CREATION_FLAG",
    "BLOCK_SHA_FREEZE_AUTHORITY_FLAG",
    "BLOCK_FINAL_READINESS_CLAIM",
    "BLOCK_RUNTIME_LIVE_ORDER_SOURCE_CONNECTOR_PROFIT_EFFECTS",
    "BLOCK_QUANTUM_EXECUTION_OR_ADVANTAGE_CLAIM",
)


@dataclass(frozen=True)
class BranchContext:
    branch: str
    source: str
    git_error: str = ""


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]
    report: dict[str, Any] | None
    info_lines: tuple[str, ...] = ()


def repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[1]


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
    value = load_yaml_subset(path)
    if not isinstance(value, dict):
        raise ValueError(f"YAML root must be an object: {path}")
    return value


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_json_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _duplicate_values(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _git_stdout(repo_root: pathlib.Path, args: Sequence[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _github_actions_active() -> bool:
    return os.getenv("GITHUB_ACTIONS") == "true"


def _normalize_branch_context(value: str) -> str:
    branch = value.strip()
    if not branch or branch == "HEAD":
        return ""
    for prefix in ("refs/heads/", "refs/remotes/origin/", "origin/"):
        if branch.startswith(prefix):
            return branch[len(prefix) :]
    return branch


def _current_branch_context(repo_root: pathlib.Path) -> BranchContext:
    for env_name in BRANCH_CONTEXT_ENV_CANDIDATES:
        branch = _normalize_branch_context(os.getenv(env_name, ""))
        if branch:
            return BranchContext(branch=branch, source=env_name)

    git_errors: list[str] = []
    for args in (["branch", "--show-current"], ["rev-parse", "--abbrev-ref", "HEAD"]):
        branch_rc, branch_stdout, branch_err = _git_stdout(repo_root, args)
        if branch_rc != 0:
            git_errors.append(branch_err or f"git {' '.join(args)} failed")
            continue
        branch = _normalize_branch_context(branch_stdout)
        if branch:
            return BranchContext(branch=branch, source=f"git {' '.join(args)}")

    return BranchContext(branch="", source="", git_error="; ".join(git_errors))


def _downstream_validation_branch_allowed(branch: str) -> bool:
    match = re.match(r"pr(?P<number>[0-9]+)[a-z]*-", branch)
    if not match:
        return False
    return int(match.group("number")) > 97


def _main_cumulative_branch_allowed(branch: str) -> bool:
    return branch == "main" or branch.startswith("repair/main-cumulative-")


def _downstream_or_main_validation_branch_allowed(branch: str) -> bool:
    return _main_cumulative_branch_allowed(branch) or _downstream_validation_branch_allowed(
        branch
    )


def _pr99_static_builder_branch_allowed(branch: str) -> bool:
    if _main_cumulative_branch_allowed(branch):
        return True
    match = re.match(r"pr(?P<number>[0-9]+)[a-z]*-", branch)
    if not match:
        return False
    return int(match.group("number")) >= 99


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


def schema_subset_failures(payload: dict[str, Any], schema: dict[str, Any], label: str) -> list[str]:
    return [f"{label} {failure}" for failure in validate_json_schema_subset(payload, schema)]


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
    except (RegistryParseError, ValueError) as exc:
        return None, [f"{label} invalid YAML: {path.as_posix()}: {exc}"]


def validate_roadmap_metadata(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    info_lines: list[str] = []
    github_actions = _github_actions_active()
    roadmap = load_json(_resolve(repo_root, ROADMAP_INDEX))
    blueprint = load_json(_resolve(repo_root, BLUEPRINT_INDEX))
    roadmap_entries = _list_of_mappings(roadmap.get("pr_entries"))
    blueprint_entries = _list_of_mappings(blueprint.get("entries"))
    roadmap_entry = next((item for item in roadmap_entries if item.get("number") == 97), None)
    blueprint_entry = next((item for item in blueprint_entries if item.get("number") == 97), None)
    if roadmap_entry is None:
        failures.append("PR97 roadmap index entry missing")
        roadmap_entry = {}
    if blueprint_entry is None:
        failures.append("PR97 blueprint index entry missing")
        blueprint_entry = {}

    checks = (
        ("roadmap.delivery_label", roadmap_entry.get("delivery_label"), ROADMAP_PR_LABEL),
        ("roadmap.title", roadmap_entry.get("title"), "AtomicRows full bundle row expansion plan"),
        ("roadmap.branch", roadmap_entry.get("branch"), TARGET_BRANCH),
        ("roadmap.marker", roadmap_entry.get("marker"), SUCCESS_MARKER),
        ("blueprint.delivery_label", blueprint_entry.get("delivery_label"), ROADMAP_PR_LABEL),
        ("blueprint.title", blueprint_entry.get("title"), "AtomicRows full bundle row expansion plan"),
        ("blueprint.branch", blueprint_entry.get("branch"), TARGET_BRANCH),
        ("blueprint.validator_marker", blueprint_entry.get("validator_marker"), SUCCESS_MARKER),
        ("blueprint.semantic_task_id", blueprint_entry.get("semantic_task_id"), BLUEPRINT_SEMANTIC_TASK_ID),
        ("blueprint.category", blueprint_entry.get("category"), "STATIC"),
        ("blueprint.stage", blueprint_entry.get("stage"), "AtomicRows bundle preparation"),
        ("blueprint.priority", blueprint_entry.get("priority"), "S1 launch-essential static"),
    )
    for label, actual, expected in checks:
        if actual != expected:
            failures.append(f"{label} must be {expected}, got {actual}")

    branch_context = _current_branch_context(repo_root)
    branch = branch_context.branch
    if not branch:
        if github_actions:
            info_lines.append(CI_DETACHED_HEAD_MODE_MARKER)
        else:
            branch_err = branch_context.git_error or "unable to determine current branch"
            failures.append(f"git branch check failed: {branch_err}")
    elif branch != TARGET_BRANCH:
        if _main_cumulative_branch_allowed(branch):
            pass
        elif _downstream_validation_branch_allowed(branch):
            if github_actions:
                info_lines.append(CI_DETACHED_HEAD_MODE_MARKER)
            info_lines.append(DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER)
        elif github_actions:
            info_lines.append(CI_DETACHED_HEAD_MODE_MARKER)

    head_rc, head, head_err = _git_stdout(repo_root, ["rev-parse", "--short", "HEAD"])
    if head_rc != 0:
        failures.append(f"git HEAD check failed: {head_err}")
    baseline_rc, _, baseline_err = _git_stdout(
        repo_root, ["cat-file", "-e", f"{EXPECTED_BASELINE_ANCESTOR}^{{commit}}"]
    )
    if github_actions and baseline_rc != 0:
        info_lines.append(CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER)
    elif baseline_rc != 0:
        failures.append(f"baseline commit missing: {EXPECTED_BASELINE_ANCESTOR}: {baseline_err}")
    else:
        ancestor_rc, _, ancestor_err = _git_stdout(
            repo_root,
            ["merge-base", "--is-ancestor", EXPECTED_BASELINE_ANCESTOR, "HEAD"],
        )
        if ancestor_rc != 0:
            failures.append(
                f"HEAD must descend from {EXPECTED_BASELINE_ANCESTOR}: {ancestor_err}"
            )

    return failures, {
        "roadmap_pr_label": ROADMAP_PR_LABEL,
        "github_pr_number_policy": GITHUB_PR_NUMBER_POLICY,
        "branch": branch,
        "branch_context_source": branch_context.source,
        "base_head": head,
        "expected_baseline_ancestor": EXPECTED_BASELINE_ANCESTOR,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "semantic_task_id_source": "owner prompt semantic task controls",
        "blueprint_semantic_task_id": blueprint_entry.get("semantic_task_id"),
        "blueprint_semantic_task_id_source": BLUEPRINT_INDEX.as_posix(),
        "validator_marker": SUCCESS_MARKER,
        "ci_info_lines": tuple(info_lines),
    }


def validate_master_plan_target_count_authority(repo_root: pathlib.Path) -> list[str]:
    try:
        text = _resolve(repo_root, MASTER_PLAN_CURRENT).read_text(encoding="utf-8")
    except OSError as exc:
        return [f"master plan target count authority unreadable: {exc}"]
    missing = [anchor for anchor in MASTER_PLAN_TARGET_COUNT_ANCHORS if anchor not in text]
    if missing:
        return [
            "target_total_row_count 4183 is not traceable to required master-plan anchors: "
            + ", ".join(missing)
        ]
    return []


def validate_plan_identity(plan: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected = {
        "plan_id": "ATOMICROWS_FULL_BUNDLE_EXPANSION_PLAN",
        "plan_version": "v1",
        "semantic_task_id": SEMANTIC_TASK_ID,
        "roadmap_pr_label": ROADMAP_PR_LABEL,
        "authority_class": AUTHORITY_CLASS,
        "target_total_row_count": 4183,
        "target_total_row_count_authority": TARGET_TOTAL_ROW_COUNT_AUTHORITY,
        "canonical_future_bundle_path": CANONICAL_BUNDLE_JSONL.as_posix(),
        "canonical_future_bundle_sha_path": CANONICAL_BUNDLE_SHA256.as_posix(),
    }
    for field, value in expected.items():
        if plan.get(field) != value:
            failures.append(f"{field} must be {value!r}")
    for field in TRUE_FIELDS:
        if plan.get(field) is not True:
            failures.append(f"{field} must be true")
    for field in FALSE_FIELDS:
        if plan.get(field) is not False:
            failures.append(f"{field} must be false")
    return failures


def validate_required_plan_concepts(plan: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    concepts = tuple(plan.get("required_plan_concepts") or ())
    if concepts != REQUIRED_PLAN_CONCEPTS:
        failures.append("required_plan_concepts must match the canonical PR97 concept order")
    if len(concepts) != len(set(concepts)):
        failures.append("duplicate plan concept id")
    nested_ids = (
        plan.get("plan_id"),
        _mapping(plan.get("row_family_split_plan")).get("plan_id"),
        _mapping(plan.get("generation_sequence_plan")).get("plan_id"),
        _mapping(plan.get("validation_matrix_plan")).get("plan_id"),
        _mapping(plan.get("owner_approval_sequence_plan")).get("plan_id"),
        _mapping(plan.get("quantum_forward_row_family_plan")).get("plan_id"),
        _mapping(plan.get("forbidden_artifact_boundary_plan")).get("plan_id"),
    )
    if nested_ids != REQUIRED_PLAN_CONCEPTS:
        failures.append("nested plan IDs must prove every required PR97 concept")
    return failures


def _row_families(plan: dict[str, Any]) -> list[dict[str, Any]]:
    return _list_of_mappings(_mapping(plan.get("row_family_split_plan")).get("row_families"))


def _validations(plan: dict[str, Any]) -> list[dict[str, Any]]:
    return _list_of_mappings(_mapping(plan.get("validation_matrix_plan")).get("validations"))


def validate_row_family_split_plan(plan: dict[str, Any], repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    branch_context = _current_branch_context(repo_root)
    pr98_source_files_allowed = _downstream_or_main_validation_branch_allowed(
        branch_context.branch
    )
    split = _mapping(plan.get("row_family_split_plan"))
    if split.get("stable_ordering_policy") != "CANONICAL_ORDER_ASCENDING":
        failures.append("row_family_split_plan.stable_ordering_policy must be canonical ascending")
    families = _row_families(plan)
    ids = tuple(str(item.get("row_family_id")) for item in families)
    if ids != ROW_FAMILY_IDS:
        failures.append("row_family_id values must match canonical PR97 order")
    duplicates = _duplicate_values(ids)
    if duplicates:
        failures.append(f"duplicate row_family_id values: {', '.join(duplicates)}")
    for index, family in enumerate(families, start=1):
        label = str(family.get("row_family_id") or f"row_family[{index}]")
        if family.get("canonical_order") != index:
            failures.append(f"{label}.canonical_order must be {index}")
        if family.get("row_family_class") not in ROW_FAMILY_CLASSES:
            failures.append(f"{label}.row_family_class is unknown")
        if (
            index <= len(ROW_FAMILY_CLASSES)
            and family.get("row_family_class") != ROW_FAMILY_CLASSES[index - 1]
        ):
            failures.append(f"{label}.row_family_class must match canonical order")
        for field in FAMILY_FALSE_FIELDS:
            if family.get(field) is not False:
                failures.append(f"{label}.{field} must be false")
        for field in FORBIDDEN_EXACT_COUNT_FIELDS:
            if field in family:
                failures.append(f"{label}.{field} is forbidden because PR97 cannot fabricate exact family counts")
        if family.get("planned_count_policy") != "OWNER_REVIEW_REQUIRED":
            failures.append(f"{label}.planned_count_policy must be OWNER_REVIEW_REQUIRED")
        if family.get("planned_count_authority") != "FUTURE_PR98_OR_OWNER_APPROVED_SOURCE":
            failures.append(f"{label}.planned_count_authority must be FUTURE_PR98_OR_OWNER_APPROVED_SOURCE")
        planned_path = pathlib.Path(str(family.get("planned_downstream_source_file_path") or ""))
        planned_text = planned_path.as_posix()
        if not planned_text.startswith("docs/master_plan/atomic_rows/pr98_row_family_sources/"):
            failures.append(f"{label}.planned_downstream_source_file_path must stay in PR98 path intent directory")
        if _resolve(repo_root, planned_path).exists() and not pr98_source_files_allowed:
            failures.append(f"{label}.planned_downstream_source_file_path exists but PR97 must not create it")
        if not _list_of_mappings([{"v": v} for v in family.get("required_validators", [])]):
            failures.append(f"{label}.required_validators must be non-empty")
        if family.get("required_owner_approval_stage") != "PR98_OWNER_APPROVAL_BEFORE_SOURCE_CREATION":
            failures.append(f"{label}.required_owner_approval_stage must require PR98 owner approval")
    return failures


def validate_generation_sequence_plan(plan: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    sequence = _mapping(plan.get("generation_sequence_plan"))
    if sequence.get("sequence_created_by_pr97_flag") is not True:
        failures.append("generation_sequence_plan.sequence_created_by_pr97_flag must be true")
    stages = _list_of_mappings(sequence.get("downstream_stages"))
    pairs = tuple((stage.get("roadmap_pr_label"), stage.get("downstream_pr_stage")) for stage in stages)
    if pairs != GENERATION_SEQUENCE:
        failures.append("generation_sequence_plan downstream stages must be PR98 PR99 PR100 PR101 in order")
    for index, stage in enumerate(stages, start=1):
        if stage.get("stage_order") != index:
            failures.append(f"generation stage {index} has unstable stage_order")
        if stage.get("creates_artifact_by_pr97_flag") is not False:
            failures.append(f"{stage.get('roadmap_pr_label')}.creates_artifact_by_pr97_flag must be false")
        if stage.get("owner_approval_required_before_stage_flag") is not True:
            failures.append(f"{stage.get('roadmap_pr_label')} must require owner approval")
    return failures


def validate_validation_matrix_plan(plan: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    matrix = _mapping(plan.get("validation_matrix_plan"))
    if matrix.get("stable_ordering_policy") != "CANONICAL_ORDER_ASCENDING":
        failures.append("validation_matrix_plan.stable_ordering_policy must be canonical ascending")
    validations = _validations(plan)
    ids = tuple(str(item.get("validation_id")) for item in validations)
    duplicates = _duplicate_values(ids)
    if duplicates:
        failures.append(f"duplicate validation_id values: {', '.join(duplicates)}")
    classes = tuple(str(item.get("validation_class")) for item in validations)
    if classes != VALIDATION_CLASSES:
        failures.append("validation_class values must match canonical PR97 validation order")
    for index, validation in enumerate(validations, start=1):
        label = str(validation.get("validation_id") or f"validation[{index}]")
        if validation.get("canonical_order") != index:
            failures.append(f"{label}.canonical_order must be {index}")
        if validation.get("validation_class") not in VALIDATION_CLASSES:
            failures.append(f"{label}.validation_class is unknown")
        if validation.get("blocks_live_or_runtime_use_flag") is not True:
            failures.append(f"{label}.blocks_live_or_runtime_use_flag must be true")
        if not validation.get("fail_closed_reason_code"):
            failures.append(f"{label}.fail_closed_reason_code must be non-empty")
    return failures


def validate_owner_approval_sequence_plan(plan: dict[str, Any]) -> list[str]:
    approval = _mapping(plan.get("owner_approval_sequence_plan"))
    failures: list[str] = []
    true_fields = (
        "owner_final_authority_flag",
        "owner_review_required_before_pr98_source_creation",
        "owner_review_required_before_pr99_builder_execution",
        "owner_review_required_before_pr100_sha_freeze",
        "owner_review_required_before_pr101_final_readiness_claim",
        "owner_override_satisfies_internal_workflow_only_flag",
    )
    for field in true_fields:
        if approval.get(field) is not True:
            failures.append(f"owner_approval_sequence_plan.{field} must be true")
    required_nonfabrication = {
        "ROW_RECORDS",
        "SOURCE_FACTS",
        "ACCEPTED_SOURCE_PACKETS",
        "CONNECTOR_SEMANTICS",
        "RUNTIME_CASH_RECEIPTS",
        "ORDER_OR_FILL_RECEIPTS",
        "REPLAY_OR_PAPER_RESULTS",
        "BUNDLE_HASH",
        "PROFIT_EVIDENCE",
        "LATENCY_EVIDENCE",
        "QUANTUM_ADVANTAGE_EVIDENCE",
    }
    actual = set(approval.get("owner_override_cannot_fabricate") or [])
    missing = sorted(required_nonfabrication - actual)
    if missing:
        failures.append("owner override nonfabrication list missing: " + ", ".join(missing))
    return failures


def validate_quantum_forward_row_family_plan(plan: dict[str, Any]) -> list[str]:
    quantum = _mapping(plan.get("quantum_forward_row_family_plan"))
    failures: list[str] = []
    if quantum.get("metadata_only_flag") is not True:
        failures.append("quantum_forward_row_family_plan.metadata_only_flag must be true")
    if quantum.get("quantum_execution_created_flag") is not False:
        failures.append("quantum_forward_row_family_plan.quantum_execution_created_flag must be false")
    if quantum.get("quantum_advantage_evidence_created_flag") is not False:
        failures.append("quantum_forward_row_family_plan.quantum_advantage_evidence_created_flag must be false")
    entries = tuple(quantum.get("quantum_metadata_planning_entries") or ())
    if entries != QUANTUM_METADATA_ENTRIES:
        failures.append("quantum metadata planning entries must match canonical PR97 order")
    effects = tuple(quantum.get("forbidden_quantum_execution_effects") or ())
    missing_effects = [effect for effect in FORBIDDEN_QUANTUM_EFFECTS if effect not in effects]
    if missing_effects:
        failures.append("forbidden quantum execution effects missing: " + ", ".join(missing_effects))
    never_overrides = set(quantum.get("quantum_output_never_overrides_gates") or [])
    for gate in (
        "SOURCE_EVIDENCE_GATE",
        "CONNECTOR_SEMANTIC_GATE",
        "RUNTIME_CASH_GATE",
        "REPLAY_PAPER_GATE",
        "RISK_GATE",
        "OWNER_APPROVAL_GATE",
        "ATOMICROWS_BUNDLE_HASH_GATE",
        "EXECUTION_ROUTER_GATE",
    ):
        if gate not in never_overrides:
            failures.append(f"quantum output override boundary missing {gate}")
    return failures


def validate_forbidden_artifact_boundary_plan(plan: dict[str, Any]) -> list[str]:
    boundary = _mapping(plan.get("forbidden_artifact_boundary_plan"))
    failures: list[str] = []
    if boundary.get("all_blocked_effects_active_in_pr97_flag") is not True:
        failures.append("forbidden_artifact_boundary_plan.all_blocked_effects_active_in_pr97_flag must be true")
    blocked_artifacts = set(boundary.get("blocked_artifacts") or [])
    for required in (
        CANONICAL_BUNDLE_JSONL.as_posix(),
        CANONICAL_BUNDLE_SHA256.as_posix(),
        "PR98_ROW_FAMILY_SOURCE_FILES",
        "PR99_BUNDLE_BUILDER",
        "PR100_SHA_FREEZE_AUTHORITY",
        "PR101_FINAL_READINESS_GATE",
    ):
        if required not in blocked_artifacts:
            failures.append(f"forbidden artifact boundary missing {required}")
    blocked_runtime = set(boundary.get("blocked_runtime_effects") or [])
    for required in (
        "SOURCE_RETRIEVAL",
        "SOURCE_ACCEPTANCE",
        "ACCEPTED_SOURCE_PACKETS",
        "CONNECTOR_SEMANTIC_BINDING",
        "PRIVATE_STATE_FETCH",
        "RUNTIME_CASH_RECEIPT",
        "REPLAY_EXECUTION",
        "PAPER_EXECUTION",
        "OPTIMIZER_EXECUTION",
        "QUANTUM_BACKEND_OR_SIMULATOR_EXECUTION",
        "LIVE_ROUTING",
        "ORDER_SUBMISSION_CANCELLATION_REDUCTION_OR_CLOSE",
    ):
        if required not in blocked_runtime:
            failures.append(f"forbidden runtime boundary missing {required}")
    blocked_claims = set(boundary.get("blocked_claims") or [])
    for required in (
        "BUNDLE_READINESS",
        "FINAL_READINESS",
        "LIVE_READINESS",
        "PROFIT_IMPROVEMENT",
        "LATENCY_IMPROVEMENT",
        "QUANTUM_ADVANTAGE",
    ):
        if required not in blocked_claims:
            failures.append(f"forbidden claim boundary missing {required}")
    return failures


def validate_downstream_pr_handoff_plan(plan: dict[str, Any]) -> list[str]:
    handoff = _mapping(plan.get("downstream_pr_handoff_plan"))
    failures: list[str] = []
    for field in (
        "pr98_handoff_intent_only",
        "pr99_handoff_intent_only",
        "pr100_handoff_intent_only",
        "pr101_handoff_intent_only",
    ):
        if handoff.get(field) is not True:
            failures.append(f"downstream_pr_handoff_plan.{field} must be true")
    if handoff.get("runtime_live_handoff_created_flag") is not False:
        failures.append("downstream_pr_handoff_plan.runtime_live_handoff_created_flag must be false")
    return failures


def planned_pr98_source_paths(plan: dict[str, Any]) -> tuple[pathlib.Path, ...]:
    return tuple(
        pathlib.Path(str(family.get("planned_downstream_source_file_path")))
        for family in _row_families(plan)
    )


def validate_no_forbidden_artifacts(repo_root: pathlib.Path, plan: dict[str, Any]) -> list[str]:
    failures: list[str] = validate_current_atomicrows_bundle_state(
        repo_root,
        label="AtomicRows full bundle row expansion plan",
    )
    for path in ALWAYS_FORBIDDEN_ARTIFACT_PATHS:
        if path in {CANONICAL_BUNDLE_JSONL, CANONICAL_BUNDLE_SHA256}:
            continue
        if _resolve(repo_root, path).exists():
            failures.append(f"forbidden downstream artifact exists: {path.as_posix()}")
    branch_context = _current_branch_context(repo_root)
    pr98_source_files_allowed = _downstream_or_main_validation_branch_allowed(
        branch_context.branch
    )
    pr99_static_builder_allowed = _pr99_static_builder_branch_allowed(branch_context.branch)
    for path in PR99_STATIC_BUILDER_ARTIFACT_PATHS:
        if _resolve(repo_root, path).exists() and not pr99_static_builder_allowed:
            failures.append(f"forbidden downstream artifact exists: {path.as_posix()}")
    for path in planned_pr98_source_paths(plan):
        if _resolve(repo_root, path).exists():
            if pr98_source_files_allowed:
                continue
            failures.append(f"PR98 row-family source file exists during PR97: {path.as_posix()}")
    return failures


def validate_master_plan_not_modified(repo_root: pathlib.Path) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--quiet", "--", MASTER_PLAN_CURRENT.as_posix()],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0:
        return []
    if completed.returncode == 1:
        return [
            "ATOMICROWS_PR97_BLOCKED_MASTER_PLAN_EDIT: "
            f"{MASTER_PLAN_CURRENT.as_posix()} has local diff"
        ]
    return [f"git diff check failed for {MASTER_PLAN_CURRENT.as_posix()}: {completed.stderr.strip()}"]


def validate_plan_payload(
    plan: dict[str, Any],
    schema: dict[str, Any],
    repo_root: pathlib.Path,
    *,
    label: str = "PLAN",
) -> list[str]:
    failures: list[str] = []
    failures.extend(schema_subset_failures(plan, schema, label))
    failures.extend(validate_plan_identity(plan))
    failures.extend(validate_required_plan_concepts(plan))
    failures.extend(validate_row_family_split_plan(plan, repo_root))
    failures.extend(validate_generation_sequence_plan(plan))
    failures.extend(validate_validation_matrix_plan(plan))
    failures.extend(validate_owner_approval_sequence_plan(plan))
    failures.extend(validate_quantum_forward_row_family_plan(plan))
    failures.extend(validate_forbidden_artifact_boundary_plan(plan))
    failures.extend(validate_downstream_pr_handoff_plan(plan))
    return failures


def _deep_update(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)
        else:
            base[key] = value
    return base


def _case_plan_from_fixture(base_plan: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    plan = copy.deepcopy(base_plan)
    concept = case.get("remove_required_plan_concept")
    if concept:
        plan["required_plan_concepts"] = [
            item for item in plan.get("required_plan_concepts", []) if item != concept
        ]
    duplicate_family_id = case.get("duplicate_row_family_id")
    if duplicate_family_id:
        families = plan["row_family_split_plan"]["row_families"]
        duplicate = copy.deepcopy(next(item for item in families if item["row_family_id"] == duplicate_family_id))
        families.append(duplicate)
    duplicate_validation_id = case.get("duplicate_validation_id")
    if duplicate_validation_id:
        validations = plan["validation_matrix_plan"]["validations"]
        duplicate = copy.deepcopy(next(item for item in validations if item["validation_id"] == duplicate_validation_id))
        validations.append(duplicate)
    if case.get("swap_row_family_order"):
        families = plan["row_family_split_plan"]["row_families"]
        families[0], families[1] = families[1], families[0]
    if case.get("swap_validation_order"):
        validations = plan["validation_matrix_plan"]["validations"]
        validations[0], validations[1] = validations[1], validations[0]
    if "inject_exact_row_count" in case:
        plan["row_family_split_plan"]["row_families"][0]["exact_row_count"] = case[
            "inject_exact_row_count"
        ]
    overrides = case.get("plan_overrides")
    if isinstance(overrides, dict):
        _deep_update(plan, copy.deepcopy(overrides))
    return plan


def validate_fixture_cases(
    fixture: dict[str, Any],
    plan: dict[str, Any],
    schema: dict[str, Any],
    repo_root: pathlib.Path,
) -> list[str]:
    failures: list[str] = []
    if fixture.get("fixture_id") != "SYNTHETIC_ATOMICROWS_FULL_BUNDLE_ROW_EXPANSION_PLAN_FIXTURE":
        failures.append("fixture_id mismatch")
    if fixture.get("positive_plan_ref") != DEFAULT_PRODUCTION_PLAN.as_posix():
        failures.append("positive_plan_ref must point to the production PR97 plan")
    case_ids = tuple(case.get("case_id") for case in _list_of_mappings(fixture.get("fixture_cases")))
    if case_ids != REQUIRED_FIXTURE_CASE_IDS:
        failures.append("fixture cases must match canonical PR97 negative coverage order")
    positive_flags = _mapping(fixture.get("positive_plan_static_only_flags"))
    for field, expected in positive_flags.items():
        if plan.get(field) != expected:
            failures.append(f"fixture positive flag {field} does not match production plan")
    for case in _list_of_mappings(fixture.get("fixture_cases")):
        case_id = str(case.get("case_id"))
        mutated_plan = _case_plan_from_fixture(plan, case)
        case_failures = validate_plan_payload(mutated_plan, schema, repo_root, label=case_id)
        expected_valid = case.get("expected_schema_valid")
        if expected_valid is True and case_failures:
            failures.append(f"{case_id} expected valid but failed: {case_failures[0]}")
        if expected_valid is False and not case_failures:
            failures.append(f"{case_id} expected fail-closed validation failure")
    return failures


def build_report(
    *,
    plan: dict[str, Any],
    metadata: dict[str, Any],
    schema_path: pathlib.Path,
    production_plan_path: pathlib.Path,
    fixture_path: pathlib.Path,
    repo_root: pathlib.Path,
) -> dict[str, Any]:
    families = _row_families(plan)
    validations = _validations(plan)
    blocked_boundary = _mapping(plan.get("forbidden_artifact_boundary_plan"))
    presence = canonical_atomicrows_bundle_presence(repo_root)
    report: dict[str, Any] = {
        "report_id": REPORT_ID,
        "report_version": REPORT_VERSION,
        "generated_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "validation_marker": SUCCESS_MARKER,
        "validator": pathlib.Path(__file__).name,
        "roadmap_pr_label": ROADMAP_PR_LABEL,
        "github_pr_number_policy": GITHUB_PR_NUMBER_POLICY,
        "branch": metadata.get("branch"),
        "branch_context_source": metadata.get("branch_context_source"),
        "base_head": metadata.get("base_head"),
        "expected_baseline_ancestor": EXPECTED_BASELINE_ANCESTOR,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "semantic_task_id_source": metadata.get("semantic_task_id_source"),
        "blueprint_semantic_task_id": metadata.get("blueprint_semantic_task_id"),
        "schema_path": schema_path.as_posix(),
        "production_plan_path": production_plan_path.as_posix(),
        "fixture_path": fixture_path.as_posix(),
        "authority_class": AUTHORITY_CLASS,
        "static_only_flag": plan.get("static_only_flag"),
        "planning_only_flag": plan.get("planning_only_flag"),
        "handoff_only_flag": plan.get("handoff_only_flag"),
        "target_total_row_count": plan.get("target_total_row_count"),
        "target_total_row_count_authority": plan.get("target_total_row_count_authority"),
        "target_total_row_count_created_by_pr97_flag": plan.get(
            "target_total_row_count_created_by_pr97_flag"
        ),
        "canonical_future_bundle_path": plan.get("canonical_future_bundle_path"),
        "canonical_future_bundle_sha_path": plan.get("canonical_future_bundle_sha_path"),
        "required_plan_concepts": list(plan.get("required_plan_concepts") or []),
        "row_family_count": len(families),
        "row_family_ids": [family.get("row_family_id") for family in families],
        "row_family_classes": [family.get("row_family_class") for family in families],
        "planned_pr98_source_file_paths": [
            family.get("planned_downstream_source_file_path") for family in families
        ],
        "validation_entry_count": len(validations),
        "validation_ids": [entry.get("validation_id") for entry in validations],
        "validation_classes": [entry.get("validation_class") for entry in validations],
        "generation_sequence": [
            [stage.get("roadmap_pr_label"), stage.get("downstream_pr_stage")]
            for stage in _list_of_mappings(
                _mapping(plan.get("generation_sequence_plan")).get("downstream_stages")
            )
        ],
        "owner_review_required_before_pr98_source_creation": _mapping(
            plan.get("owner_approval_sequence_plan")
        ).get("owner_review_required_before_pr98_source_creation"),
        "owner_review_required_before_pr99_builder_execution": _mapping(
            plan.get("owner_approval_sequence_plan")
        ).get("owner_review_required_before_pr99_builder_execution"),
        "owner_review_required_before_pr100_sha_freeze": _mapping(
            plan.get("owner_approval_sequence_plan")
        ).get("owner_review_required_before_pr100_sha_freeze"),
        "owner_review_required_before_pr101_final_readiness_claim": _mapping(
            plan.get("owner_approval_sequence_plan")
        ).get("owner_review_required_before_pr101_final_readiness_claim"),
        "quantum_metadata_planning_entries": list(
            _mapping(plan.get("quantum_forward_row_family_plan")).get(
                "quantum_metadata_planning_entries",
                [],
            )
        ),
        "quantum_metadata_only_flag": _mapping(
            plan.get("quantum_forward_row_family_plan")
        ).get("metadata_only_flag"),
        "blocked_artifacts": list(blocked_boundary.get("blocked_artifacts") or []),
        "blocked_runtime_effects": list(blocked_boundary.get("blocked_runtime_effects") or []),
        "blocked_claims": list(blocked_boundary.get("blocked_claims") or []),
        "atomicrows_bundle_jsonl_exists": presence.bundle_jsonl_exists,
        "atomicrows_bundle_sha256_exists": presence.bundle_sha256_exists,
        "pr98_row_family_source_files_created": False,
        "pr99_bundle_builder_created": False,
        "pr100_sha_freeze_authority_created": False,
        "pr101_final_readiness_created": False,
        "runtime_live_order_source_connector_profit_quantum_backend_effect_created": False,
        "remaining_boundary": (
            "PR97 creates no bundle hash freeze row records source files builder final "
            "readiness runtime live trading profit latency or quantum advantage readiness."
        ),
    }
    for field in FALSE_FIELDS:
        report[field] = plan.get(field)
    return report


def validate_report_is_deterministic(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if report != json.loads(serialize_report(report)):
        failures.append("generated report serialization is not deterministic sorted JSON")
    if report.get("generated_at_utc") != "STATIC_DETERMINISTIC_NO_WALL_CLOCK":
        failures.append("generated report must use deterministic generated_at_utc sentinel")
    forbidden_patterns = (
        re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),
        re.compile(r"\b20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"),
        re.compile(r"[A-Za-z]:\\\\"),
        re.compile(r"\\\\"),
    )
    text = serialize_report(report)
    for pattern in forbidden_patterns:
        if pattern.search(text):
            failures.append("generated report contains nondeterministic or platform-specific content")
            break
    expected_false = (
        "bundle_file_created_flag",
        "bundle_sha_created_flag",
        "sha_authority_created_flag",
        "freeze_authority_created_flag",
        "row_family_source_files_created_flag",
        "row_records_created_flag",
        "bundle_builder_created_flag",
        "bundle_builder_executed_flag",
        "final_readiness_created_flag",
        "creates_runtime_live_authority_flag",
        "creates_order_authority_flag",
        "creates_source_fact_flag",
        "creates_connector_semantic_flag",
        "creates_runtime_cash_receipt_flag",
        "creates_replay_paper_result_flag",
        "creates_optimizer_execution_flag",
        "creates_quantum_backend_execution_flag",
        "creates_profit_evidence_flag",
        "creates_latency_evidence_flag",
        "creates_quantum_advantage_evidence_flag",
        "atomicrows_bundle_sha256_exists",
        "pr98_row_family_source_files_created",
        "pr99_bundle_builder_created",
        "pr100_sha_freeze_authority_created",
        "pr101_final_readiness_created",
        "runtime_live_order_source_connector_profit_quantum_backend_effect_created",
    )
    for field in expected_false:
        if report.get(field) is not False:
            failures.append(f"report.{field} must be false")
    return failures


def validate(
    *,
    repo_root: pathlib.Path = pathlib.Path("."),
    schema_path: pathlib.Path = DEFAULT_SCHEMA,
    production_plan_path: pathlib.Path = DEFAULT_PRODUCTION_PLAN,
    fixture_path: pathlib.Path = DEFAULT_FIXTURE,
    output_path: pathlib.Path = DEFAULT_REPORT,
) -> ValidationResult:
    repo_root = repo_root.resolve()
    schema_abs = _resolve(repo_root, schema_path)
    production_plan_abs = _resolve(repo_root, production_plan_path)
    fixture_abs = _resolve(repo_root, fixture_path)
    output_abs = _resolve(repo_root, output_path)

    failures: list[str] = []
    schema, schema_failures = _load_json_checked(schema_abs, "SCHEMA")
    plan, plan_failures = _load_yaml_checked(production_plan_abs, "PLAN")
    fixture, fixture_failures = _load_json_checked(fixture_abs, "FIXTURE")
    failures.extend(schema_failures)
    failures.extend(plan_failures)
    failures.extend(fixture_failures)
    if schema is None or plan is None or fixture is None:
        return ValidationResult(False, tuple(failures), None)

    metadata_failures, metadata = validate_roadmap_metadata(repo_root)
    info_lines = tuple(metadata.get("ci_info_lines", ()))
    failures.extend(metadata_failures)
    failures.extend(validate_master_plan_target_count_authority(repo_root))
    failures.extend(validate_plan_payload(plan, schema, repo_root))
    failures.extend(validate_fixture_cases(fixture, plan, schema, repo_root))
    failures.extend(validate_no_forbidden_artifacts(repo_root, plan))
    failures.extend(validate_master_plan_not_modified(repo_root))

    report = build_report(
        plan=plan,
        metadata=metadata,
        schema_path=schema_path,
        production_plan_path=production_plan_path,
        fixture_path=fixture_path,
        repo_root=repo_root,
    )
    second_report = build_report(
        plan=copy.deepcopy(plan),
        metadata=copy.deepcopy(metadata),
        schema_path=schema_path,
        production_plan_path=production_plan_path,
        fixture_path=fixture_path,
        repo_root=repo_root,
    )
    if report != second_report:
        failures.append("generated report is not deterministic across builds")
    failures.extend(validate_report_is_deterministic(report))

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--production-plan", default=str(DEFAULT_PRODUCTION_PLAN))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    args = parser.parse_args(argv)

    result = validate(
        repo_root=pathlib.Path(args.repo_root),
        schema_path=pathlib.Path(args.schema),
        production_plan_path=pathlib.Path(args.production_plan),
        fixture_path=pathlib.Path(args.fixture),
        output_path=pathlib.Path(args.out),
    )
    if result.ok:
        print(SUCCESS_MARKER)
        for line in result.info_lines:
            print(line)
        return 0

    print(FAILURE_MARKER)
    for line in result.info_lines:
        print(line)
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
