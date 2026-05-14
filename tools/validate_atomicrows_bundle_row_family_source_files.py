#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
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

from tools import validate_atomicrows_full_bundle_row_expansion_plan as pr97_gate  # noqa: E402
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)


DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_bundle_row_family_source_files.schema.json"
)
DEFAULT_SOURCE_FILE_SET = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsBundleRowFamilySourceFiles.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "atomicrows"
    / "synthetic_atomicrows_bundle_row_family_source_files.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsBundleRowFamilySourceFiles.report.json"
)

ROADMAP_INDEX = pathlib.Path("docs") / "roadmap" / "QTT_PRs_Roadmap_Index_v1_0.json"
BLUEPRINT_INDEX = (
    pathlib.Path("docs")
    / "roadmap"
    / "QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json"
)
PR97_PLAN_PATH = pr97_gate.DEFAULT_PRODUCTION_PLAN
PR97_REPORT_PATH = pr97_gate.DEFAULT_REPORT
MASTER_PLAN_CURRENT = pr97_gate.MASTER_PLAN_CURRENT
CANONICAL_BUNDLE_JSONL = pr97_gate.CANONICAL_BUNDLE_JSONL
CANONICAL_BUNDLE_SHA256 = pr97_gate.CANONICAL_BUNDLE_SHA256

REPORT_ID = "ATOMICROWS_BUNDLE_ROW_FAMILY_SOURCE_FILES_REPORT"
REPORT_VERSION = "v1"
ROADMAP_PR_LABEL = "PR_98"
ROADMAP_DELIVERY_LABEL = "PR #98"
GITHUB_PR_NUMBER_POLICY = "may differ"
SEMANTIC_TASK_ID = "ROADMAP-ATOMICROWS-ROW-FAMILY-SOURCES"
BLUEPRINT_SEMANTIC_TASK_ID = "ROADMAP-ATOMICROWS-BUNDLE-ROW-FAMILY-SOURCE-FILES"
TARGET_BRANCH = "pr98-atomicrows-bundle-row-family-source-files"
EXPECTED_BASELINE_ANCESTOR = "3d58b1d"
SUCCESS_MARKER = "QTT_ATOMICROWS_BUNDLE_ROW_FAMILY_SOURCE_FILES_OK"
FAILURE_MARKER = "QTT_ATOMICROWS_BUNDLE_ROW_FAMILY_SOURCE_FILES_FAILED"
AUTHORITY_CLASS = (
    "STATIC_ATOMICROWS_ROW_FAMILY_SOURCE_FILES_ONLY_NOT_BUNDLE_NOT_HASH_"
    "NOT_FREEZE_NOT_RUNTIME_AUTHORITY"
)

CI_DETACHED_HEAD_MODE_MARKER = pr97_gate.CI_DETACHED_HEAD_MODE_MARKER
CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER = pr97_gate.CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER
DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER = (
    pr97_gate.DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER
)
BRANCH_CONTEXT_ENV_CANDIDATES = pr97_gate.BRANCH_CONTEXT_ENV_CANDIDATES

REQUIRED_SOURCE_FILE_CONCEPTS = (
    "ATOMICROWS_BUNDLE_ROW_FAMILY_SOURCE_FILE_SET",
    "ATOMICROWS_ROW_FAMILY_SOURCE_MANIFEST",
    "ATOMICROWS_ROW_FAMILY_SOURCE_FILE",
    "ATOMICROWS_ROW_SOURCE_RECORD_OR_BLUEPRINT",
    "ATOMICROWS_ROW_FAMILY_SOURCE_VALIDATION_MATRIX",
    "ATOMICROWS_ROW_FAMILY_SOURCE_OWNER_APPROVAL_BOUNDARY",
    "ATOMICROWS_ROW_FAMILY_QUANTUM_METADATA_SOURCE_PLAN",
)
REQUIRED_VALIDATION_CLASSES = (
    "SOURCE_FILE_SCHEMA_COMPLIANCE",
    "PR97_ROW_FAMILY_COVERAGE",
    "PR97_SOURCE_FILE_PATH_ALIGNMENT",
    "SOURCE_FILE_ID_UNIQUENESS",
    "ROW_FAMILY_OWNERSHIP_UNIQUENESS",
    "ROW_SOURCE_BLUEPRINT_ID_UNIQUENESS",
    "STABLE_ORDERING",
    "NO_FABRICATED_EXACT_COUNTS",
    "BUNDLE_AND_HASH_ABSENCE",
    "BUILDER_FREEZE_FINAL_READINESS_ABSENCE",
    "NO_RUNTIME_LIVE_ORDER_SOURCE_CONNECTOR_PROFIT_AUTHORITY",
    "QUANTUM_METADATA_NON_EXECUTABLE",
)
REQUIRED_FIXTURE_CASE_IDS = (
    "PASS_PR98_STATIC_SOURCE_FILES_VALID",
    "BLOCK_MISSING_REQUIRED_SOURCE_FILE",
    "BLOCK_UNKNOWN_ROW_FAMILY",
    "BLOCK_DUPLICATE_SOURCE_FILE_ID",
    "BLOCK_DUPLICATE_ROW_FAMILY_OWNERSHIP",
    "BLOCK_DUPLICATE_BLUEPRINT_ID",
    "BLOCK_UNSTABLE_SOURCE_FILE_ORDER",
    "BLOCK_UNSTABLE_BLUEPRINT_ORDER",
    "BLOCK_FABRICATED_EXACT_COUNT",
    "BLOCK_BUNDLE_JSONL_PRESENT",
    "BLOCK_BUNDLE_SHA256_PRESENT",
    "BLOCK_BUNDLE_BUILDER_PRESENT",
    "BLOCK_SHA_FREEZE_AUTHORITY_PRESENT",
    "BLOCK_FINAL_READINESS_PRESENT",
    "BLOCK_RUNTIME_LIVE_ORDER_SOURCE_CONNECTOR_PROFIT_EFFECT",
    "BLOCK_QUANTUM_EXECUTION_METADATA",
)
QUANTUM_METADATA_REFS = (
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
FORBIDDEN_QUANTUM_EFFECTS = pr97_gate.FORBIDDEN_QUANTUM_EFFECTS
FORBIDDEN_EXACT_COUNT_FIELDS = (
    "exact_row_count",
    "planned_row_count",
    "target_row_count",
    "row_count",
    "allocated_row_count",
    "exact_count",
)
FALSE_AUTHORITY_FIELDS = (
    "final_bundle_created_flag",
    "bundle_jsonl_created_flag",
    "bundle_sha_created_flag",
    "hash_created_flag",
    "sha_authority_created_flag",
    "freeze_authority_created_flag",
    "bundle_builder_created_flag",
    "bundle_builder_executed_flag",
    "final_readiness_created_flag",
    "external_source_retrieval_created_flag",
    "source_acceptance_created_flag",
    "connector_semantic_created_flag",
    "runtime_live_authority_created_flag",
    "quantum_backend_execution_created_flag",
)
SOURCE_FILE_FALSE_FIELDS = (
    "external_source_retrieval_created_flag",
    "source_acceptance_created_flag",
    "final_bundle_row_file_flag",
    "final_bundle_row_flag",
    "bundle_hash_authority_flag",
    "runtime_live_authority_flag",
    "exact_row_count_created_by_pr98_flag",
    "builder_execution_allowed_by_pr98_flag",
)
BLUEPRINT_FALSE_FIELDS = (
    "exact_row_created_flag",
    "exact_final_row_created_flag",
    "final_bundle_membership_created_flag",
    "source_evidence_created_flag",
    "connector_semantic_created_flag",
    "runtime_live_order_authority_created_flag",
    "profit_evidence_created_flag",
    "quantum_backend_execution_created_flag",
)
ALWAYS_FORBIDDEN_ARTIFACT_PATHS = (
    (CANONICAL_BUNDLE_JSONL, "forbidden AtomicRows bundle exists"),
    (CANONICAL_BUNDLE_SHA256, "forbidden AtomicRows bundle hash exists"),
    (pathlib.Path("tools") / "build_atomicrows_full_bundle.py", "forbidden bundle builder artifact exists"),
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
PR99_STATIC_BUILDER_ARTIFACT_PATHS = (
    (pathlib.Path("tools") / "build_atomicrows_bundle.py", "forbidden bundle builder artifact exists"),
)
FORBIDDEN_STATIC_SURFACE_IMPORT_ROOTS = (
    "hashlib",
    "requests",
    "qiskit",
    "dwave",
    "cirq",
    "pennylane",
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


def _walk(value: Any, path: str = "$"):
    if isinstance(value, dict):
        for key, item in value.items():
            current = f"{path}.{key}"
            yield current, key, item
            yield from _walk(item, current)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            current = f"{path}[{index}]"
            yield current, f"[{index}]", item
            yield from _walk(item, current)


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
    match = re.match(r"pr(?P<number>[0-9]+)-", branch)
    if not match:
        return False
    return int(match.group("number")) > 98


def _should_skip_default_report_write(
    *,
    repo_root: pathlib.Path,
    output_abs: pathlib.Path,
    metadata: dict[str, Any],
) -> bool:
    if output_abs != _resolve(repo_root, DEFAULT_REPORT):
        return False
    branch = str(metadata.get("branch") or "")
    return branch not in {TARGET_BRANCH, "main"} and _downstream_validation_branch_allowed(branch)


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
    except Exception as exc:
        return None, [f"{label} invalid YAML/JSON: {path.as_posix()}: {exc}"]


def _source_file_id_for_family(family: dict[str, Any]) -> str:
    row_family_id = str(family.get("row_family_id"))
    suffix = row_family_id.removeprefix("AR_FAMILY_")
    return f"AR_PR98_SOURCE_FILE_{suffix}"


def _blueprint_id_for_family(family: dict[str, Any]) -> str:
    row_family_id = str(family.get("row_family_id"))
    suffix = row_family_id.removeprefix("AR_FAMILY_")
    return f"AR_PR98_BLUEPRINT_{suffix}_OWNER_REVIEW_REQUIRED"


def _row_families(pr97_plan: dict[str, Any]) -> list[dict[str, Any]]:
    return _list_of_mappings(
        _mapping(pr97_plan.get("row_family_split_plan")).get("row_families")
    )


def _manifest_entries(source_file_set: dict[str, Any]) -> list[dict[str, Any]]:
    return _list_of_mappings(
        _mapping(source_file_set.get("row_family_source_manifest")).get(
            "row_family_source_files"
        )
    )


def _source_file_paths_from_pr97(pr97_plan: dict[str, Any]) -> tuple[pathlib.Path, ...]:
    return tuple(
        pathlib.Path(str(family.get("planned_downstream_source_file_path")))
        for family in _row_families(pr97_plan)
    )


def load_source_jsonl(path: pathlib.Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"JSONL line {line_no} must be an object")
        rows.append(value)
    return rows


def load_source_files(repo_root: pathlib.Path, pr97_plan: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    failures: list[str] = []
    loaded: dict[str, dict[str, Any]] = {}
    for relative_path in _source_file_paths_from_pr97(pr97_plan):
        path_abs = _resolve(repo_root, relative_path)
        try:
            rows = load_source_jsonl(path_abs)
        except FileNotFoundError:
            failures.append(f"missing required source file: {relative_path.as_posix()}")
            continue
        except (json.JSONDecodeError, ValueError) as exc:
            failures.append(f"source file invalid JSONL: {relative_path.as_posix()}: {exc}")
            continue
        if len(rows) != 1:
            failures.append(
                f"source file must contain exactly one ATOMICROWS_ROW_FAMILY_SOURCE_FILE object: {relative_path.as_posix()}"
            )
            continue
        loaded[relative_path.as_posix()] = rows[0]
    return loaded, failures


def schema_subset_failures(payload: dict[str, Any], schema: dict[str, Any], label: str) -> list[str]:
    return [f"{label} {failure}" for failure in validate_json_schema_subset(payload, schema)]


def source_file_schema_failures(payload: dict[str, Any], schema: dict[str, Any], label: str) -> list[str]:
    return [
        f"{label} {failure}"
        for failure in validate_json_schema_subset(
            payload,
            {"$ref": "#/$defs/source_file"},
            root_schema=schema,
        )
    ]


def validate_roadmap_metadata(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    info_lines: list[str] = []
    github_actions = _github_actions_active()
    roadmap = load_json(_resolve(repo_root, ROADMAP_INDEX))
    blueprint = load_json(_resolve(repo_root, BLUEPRINT_INDEX))
    roadmap_entries = _list_of_mappings(roadmap.get("pr_entries"))
    blueprint_entries = _list_of_mappings(blueprint.get("entries"))
    roadmap_entry = next((item for item in roadmap_entries if item.get("number") == 98), None)
    blueprint_entry = next((item for item in blueprint_entries if item.get("number") == 98), None)
    if roadmap_entry is None:
        failures.append("PR98 roadmap index entry missing")
        roadmap_entry = {}
    if blueprint_entry is None:
        failures.append("PR98 blueprint index entry missing")
        blueprint_entry = {}

    checks = (
        ("roadmap.delivery_label", roadmap_entry.get("delivery_label"), ROADMAP_DELIVERY_LABEL),
        ("roadmap.title", roadmap_entry.get("title"), "AtomicRows bundle row-family source files"),
        ("roadmap.branch", roadmap_entry.get("branch"), TARGET_BRANCH),
        ("roadmap.marker", roadmap_entry.get("marker"), SUCCESS_MARKER),
        ("blueprint.delivery_label", blueprint_entry.get("delivery_label"), ROADMAP_DELIVERY_LABEL),
        ("blueprint.title", blueprint_entry.get("title"), "AtomicRows bundle row-family source files"),
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
        if github_actions:
            info_lines.append(CI_DETACHED_HEAD_MODE_MARKER)
            if _downstream_validation_branch_allowed(branch):
                info_lines.append(DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER)
        elif _downstream_validation_branch_allowed(branch):
            info_lines.append(DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER)
        else:
            failures.append(f"current branch must be {TARGET_BRANCH}, got {branch}")

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
        "roadmap_delivery_label": ROADMAP_DELIVERY_LABEL,
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


def validate_upstream_pr97(repo_root: pathlib.Path, pr97_plan: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    pr97_report_path = _resolve(repo_root, PR97_REPORT_PATH)
    try:
        pr97_report = load_json(pr97_report_path)
    except FileNotFoundError:
        pr97_report = {}
        failures.append(f"PR97 report missing: {PR97_REPORT_PATH.as_posix()}")
    except (json.JSONDecodeError, ValueError) as exc:
        pr97_report = {}
        failures.append(f"PR97 report invalid: {PR97_REPORT_PATH.as_posix()}: {exc}")
    if pr97_report and pr97_report.get("validation_marker") != pr97_gate.SUCCESS_MARKER:
        failures.append("PR97 report validation marker mismatch")
    if pr97_plan.get("target_total_row_count") != 4183:
        failures.append("PR97 target_total_row_count must remain 4183")
    if pr97_plan.get("target_total_row_count_created_by_pr97_flag") is not False:
        failures.append("PR97 target_total_row_count_created_by_pr97_flag must be false")
    if len(_row_families(pr97_plan)) != 15:
        failures.append("PR97 row_family_split_plan must contain 15 row families")
    return failures


def validate_source_file_set_payload(
    source_file_set: dict[str, Any],
    schema: dict[str, Any],
    pr97_plan: dict[str, Any],
    repo_root: pathlib.Path,
) -> list[str]:
    failures: list[str] = []
    failures.extend(schema_subset_failures(source_file_set, schema, "SOURCE_FILE_SET"))

    if source_file_set.get("required_source_file_concepts") != list(REQUIRED_SOURCE_FILE_CONCEPTS):
        failures.append("required_source_file_concepts must match canonical PR98 concept order")
    if source_file_set.get("semantic_task_id") != SEMANTIC_TASK_ID:
        failures.append(f"semantic_task_id must be {SEMANTIC_TASK_ID}")
    if source_file_set.get("authority_class") != AUTHORITY_CLASS:
        failures.append(f"authority_class must be {AUTHORITY_CLASS}")
    if source_file_set.get("target_total_row_count") != pr97_plan.get("target_total_row_count"):
        failures.append("target_total_row_count must remain traceable to PR97")
    if source_file_set.get("target_total_row_count_planning_authority_only_flag") is not True:
        failures.append("target_total_row_count_planning_authority_only_flag must be true")
    if source_file_set.get("source_files_created_flag") is not True:
        failures.append("source_files_created_flag must be true for PR98 row-family source files")
    for field in FALSE_AUTHORITY_FIELDS:
        if source_file_set.get(field) is not False:
            failures.append(f"{field} must be false")

    validations = _list_of_mappings(_mapping(source_file_set.get("validation_matrix")).get("validations"))
    validation_classes = [str(entry.get("validation_class")) for entry in validations]
    if validation_classes != list(REQUIRED_VALIDATION_CLASSES):
        failures.append("validation_matrix.validation_class values must match canonical PR98 order")
    if [entry.get("canonical_order") for entry in validations] != list(range(1, len(validations) + 1)):
        failures.append("validation_matrix canonical_order values must be deterministic ascending")
    if _duplicate_values(str(entry.get("validation_id")) for entry in validations):
        failures.append("validation_matrix validation_id values must be unique")

    owner_boundary = _mapping(source_file_set.get("owner_approval_boundary"))
    for field in (
        "owner_approval_required_before_builder_execution",
        "owner_approval_required_before_hash_freeze",
        "owner_approval_required_before_final_readiness",
        "owner_override_satisfies_internal_workflow_only_flag",
    ):
        if owner_boundary.get(field) is not True:
            failures.append(f"owner_approval_boundary.{field} must be true")
    cannot_fabricate = set(owner_boundary.get("owner_override_cannot_fabricate") or [])
    for required in (
        "SOURCE_FACTS",
        "ACCEPTED_SOURCE_PACKETS",
        "CONNECTOR_SEMANTICS",
        "RUNTIME_CASH_RECEIPTS",
        "ORDER_OR_FILL_RECEIPTS",
        "REPLAY_OR_PAPER_RESULTS",
        "FINAL_ATOMICROWS_ROWS",
        "BUNDLE_FILE",
        "BUNDLE_HASH",
        "PROFIT_EVIDENCE",
        "LATENCY_EVIDENCE",
        "QUANTUM_ADVANTAGE_EVIDENCE",
    ):
        if required not in cannot_fabricate:
            failures.append(f"owner approval boundary missing no-fabrication item {required}")

    quantum_plan = _mapping(source_file_set.get("quantum_metadata_source_plan"))
    if quantum_plan.get("metadata_only_flag") is not True:
        failures.append("quantum_metadata_source_plan.metadata_only_flag must be true")
    for field in ("quantum_backend_execution_created_flag", "quantum_advantage_evidence_created_flag"):
        if quantum_plan.get(field) is not False:
            failures.append(f"quantum_metadata_source_plan.{field} must be false")
    for item in QUANTUM_METADATA_REFS:
        if item not in set(quantum_plan.get("allowed_static_metadata_refs") or []):
            failures.append(f"quantum metadata plan missing {item}")
    for item in FORBIDDEN_QUANTUM_EFFECTS:
        if item not in set(quantum_plan.get("forbidden_quantum_execution_effects") or []):
            failures.append(f"quantum metadata plan missing forbidden effect {item}")

    failures.extend(validate_manifest_alignment(source_file_set, pr97_plan, repo_root))
    return failures


def validate_manifest_alignment(
    source_file_set: dict[str, Any],
    pr97_plan: dict[str, Any],
    repo_root: pathlib.Path,
) -> list[str]:
    failures: list[str] = []
    entries = _manifest_entries(source_file_set)
    families = _row_families(pr97_plan)
    if len(entries) != len(families):
        failures.append("manifest row_family_source_files count must match PR97 row families")
    if [entry.get("canonical_order") for entry in entries] != list(range(1, len(entries) + 1)):
        failures.append("manifest source file order must be canonical_order ascending")
    if _duplicate_values(str(entry.get("source_file_id")) for entry in entries):
        failures.append("duplicate source_file_id values in manifest")
    if _duplicate_values(str(entry.get("row_family_id")) for entry in entries):
        failures.append("duplicate row_family_id ownership in manifest")

    for family, entry in zip(families, entries):
        expected_path = str(family.get("planned_downstream_source_file_path"))
        expected_source_file_id = _source_file_id_for_family(family)
        checks = (
            ("row_family_id", entry.get("row_family_id"), family.get("row_family_id")),
            ("row_family_class", entry.get("row_family_class"), family.get("row_family_class")),
            ("canonical_order", entry.get("canonical_order"), family.get("canonical_order")),
            ("planned_downstream_source_file_path", entry.get("planned_downstream_source_file_path"), expected_path),
            ("actual_created_source_file_path", entry.get("actual_created_source_file_path"), expected_path),
            ("source_file_id", entry.get("source_file_id"), expected_source_file_id),
            ("row_count_policy", entry.get("row_count_policy"), family.get("planned_count_policy")),
            ("exact_row_count_authority", entry.get("exact_row_count_authority"), "EXACT_PER_FAMILY_COUNTS_NOT_AUTHORIZED_BY_PR97"),
            ("downstream_builder_readiness_state", entry.get("downstream_builder_readiness_state"), "NOT_READY_FOR_BUNDLE_BUILD"),
        )
        for label, actual, expected in checks:
            if actual != expected:
                failures.append(
                    f"manifest {family.get('row_family_id')} {label} must be {expected}, got {actual}"
                )
        if entry.get("source_file_exists_flag") is not True:
            failures.append(f"manifest {family.get('row_family_id')} source_file_exists_flag must be true")
        if not _resolve(repo_root, pathlib.Path(expected_path)).exists():
            failures.append(f"manifest source file does not exist: {expected_path}")
        for exact_count_field in FORBIDDEN_EXACT_COUNT_FIELDS:
            if exact_count_field in entry:
                failures.append(f"manifest must not contain fabricated count field {exact_count_field}")
    return failures


def validate_source_file_payloads(
    source_files: dict[str, dict[str, Any]],
    schema: dict[str, Any],
    pr97_plan: dict[str, Any],
) -> list[str]:
    failures: list[str] = []
    families = _row_families(pr97_plan)
    source_file_ids: list[str] = []
    row_family_ids: list[str] = []
    blueprint_ids: list[str] = []
    row_source_ids: list[str] = []

    if set(source_files) != {path.as_posix() for path in _source_file_paths_from_pr97(pr97_plan)}:
        missing = sorted({path.as_posix() for path in _source_file_paths_from_pr97(pr97_plan)} - set(source_files))
        extra = sorted(set(source_files) - {path.as_posix() for path in _source_file_paths_from_pr97(pr97_plan)})
        if missing:
            failures.append(f"missing required source files: {', '.join(missing)}")
        if extra:
            failures.append(f"unknown source files relative to PR97: {', '.join(extra)}")

    ordered_source_objects: list[dict[str, Any]] = []
    for family in families:
        expected_path = str(family.get("planned_downstream_source_file_path"))
        source_file = source_files.get(expected_path)
        if source_file is None:
            continue
        ordered_source_objects.append(source_file)
        failures.extend(source_file_schema_failures(source_file, schema, f"SOURCE_FILE {expected_path}"))
        failures.extend(validate_single_source_file(source_file, family))
        source_file_ids.append(str(source_file.get("source_file_id")))
        row_family_ids.append(str(source_file.get("row_family_id")))
        for blueprint in _list_of_mappings(source_file.get("source_records_or_blueprints")):
            blueprint_ids.append(str(blueprint.get("blueprint_id")))
            if "row_source_id" in blueprint:
                row_source_ids.append(str(blueprint.get("row_source_id")))

    if [item.get("canonical_order") for item in ordered_source_objects] != list(
        range(1, len(ordered_source_objects) + 1)
    ):
        failures.append("source file canonical_order values must be deterministic ascending")
    duplicate_source_file_ids = _duplicate_values(source_file_ids)
    if duplicate_source_file_ids:
        failures.append(f"duplicate source_file_id values: {', '.join(duplicate_source_file_ids)}")
    duplicate_family_ids = _duplicate_values(row_family_ids)
    if duplicate_family_ids:
        failures.append(f"duplicate row_family_id ownership: {', '.join(duplicate_family_ids)}")
    duplicate_blueprint_ids = _duplicate_values(blueprint_ids)
    if duplicate_blueprint_ids:
        failures.append(f"duplicate blueprint_id values: {', '.join(duplicate_blueprint_ids)}")
    duplicate_row_source_ids = _duplicate_values(row_source_ids)
    if duplicate_row_source_ids:
        failures.append(f"duplicate row_source_id values: {', '.join(duplicate_row_source_ids)}")
    return failures


def validate_single_source_file(source_file: dict[str, Any], family: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_path = str(family.get("planned_downstream_source_file_path"))
    expected_source_file_id = _source_file_id_for_family(family)
    checks = (
        ("record_type", source_file.get("record_type"), "ATOMICROWS_ROW_FAMILY_SOURCE_FILE"),
        ("source_file_id", source_file.get("source_file_id"), expected_source_file_id),
        ("semantic_task_id", source_file.get("semantic_task_id"), SEMANTIC_TASK_ID),
        ("roadmap_pr_label", source_file.get("roadmap_pr_label"), ROADMAP_PR_LABEL),
        ("row_family_id", source_file.get("row_family_id"), family.get("row_family_id")),
        ("row_family_class", source_file.get("row_family_class"), family.get("row_family_class")),
        ("display_label", source_file.get("display_label"), family.get("display_label")),
        ("canonical_order", source_file.get("canonical_order"), family.get("canonical_order")),
        ("source_file_path", source_file.get("source_file_path"), expected_path),
        ("planned_count_policy", source_file.get("planned_count_policy"), family.get("planned_count_policy")),
        ("planned_count_authority", source_file.get("planned_count_authority"), family.get("planned_count_authority")),
        ("quantum_relevance_class", source_file.get("quantum_relevance_class"), family.get("quantum_relevance_class")),
        ("source_evidence_requirement_class", source_file.get("source_evidence_requirement_class"), family.get("source_evidence_requirement_class")),
        ("connector_semantic_requirement_class", source_file.get("connector_semantic_requirement_class"), family.get("connector_semantic_requirement_class")),
        ("replay_paper_requirement_class", source_file.get("replay_paper_requirement_class"), family.get("replay_paper_requirement_class")),
        ("live_order_requirement_class", source_file.get("live_order_requirement_class"), family.get("live_order_requirement_class")),
    )
    for label, actual, expected in checks:
        if actual != expected:
            failures.append(
                f"{family.get('row_family_id')} {label} must be {expected}, got {actual}"
            )
    if source_file.get("source_file_mode") != "SOURCE_REQUIRED":
        failures.append(f"{family.get('row_family_id')} source_file_mode must be SOURCE_REQUIRED")
    if source_file.get("source_file_created_by_pr98_flag") is not True:
        failures.append(f"{family.get('row_family_id')} source_file_created_by_pr98_flag must be true")
    if source_file.get("repository_source_file_only_flag") is not True:
        failures.append(f"{family.get('row_family_id')} repository_source_file_only_flag must be true")
    for field in SOURCE_FILE_FALSE_FIELDS:
        if source_file.get(field) is not False:
            failures.append(f"{family.get('row_family_id')} {field} must be false")
    if source_file.get("declared_source_record_count") != 0:
        failures.append(f"{family.get('row_family_id')} declared_source_record_count must be 0")
    blueprints = _list_of_mappings(source_file.get("source_records_or_blueprints"))
    if source_file.get("declared_source_blueprint_count") != len(blueprints):
        failures.append(f"{family.get('row_family_id')} declared_source_blueprint_count must match blueprints")
    if source_file.get("exact_count_authority") != "EXACT_PER_FAMILY_COUNTS_NOT_AUTHORIZED_BY_PR97":
        failures.append(f"{family.get('row_family_id')} exact_count_authority must remain non-authoritative")
    if [blueprint.get("canonical_order") for blueprint in blueprints] != list(range(1, len(blueprints) + 1)):
        failures.append(f"{family.get('row_family_id')} blueprint canonical_order values must be stable")

    for path, key, _item in _walk(source_file, f"SOURCE_FILE {family.get('row_family_id')}"):
        if key in FORBIDDEN_EXACT_COUNT_FIELDS:
            failures.append(f"{path} must not fabricate exact per-family counts")
    for blueprint in blueprints:
        failures.extend(validate_blueprint(blueprint, family))
    return failures


def validate_blueprint(blueprint: dict[str, Any], family: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_blueprint_id = _blueprint_id_for_family(family)
    checks = (
        ("record_type", blueprint.get("record_type"), "ATOMICROWS_ROW_SOURCE_RECORD_OR_BLUEPRINT"),
        ("blueprint_id", blueprint.get("blueprint_id"), expected_blueprint_id),
        ("row_family_id", blueprint.get("row_family_id"), family.get("row_family_id")),
        ("record_class", blueprint.get("record_class"), "SOURCE_ROW_BLUEPRINT_NOT_EXACT_FINAL_ROW"),
        ("lifecycle_state", blueprint.get("lifecycle_state"), "OWNER_REVIEW_REQUIRED_BEFORE_ROW_MATERIALIZATION"),
        ("source_evidence_requirement_class", blueprint.get("source_evidence_requirement_class"), family.get("source_evidence_requirement_class")),
        ("connector_semantic_requirement_class", blueprint.get("connector_semantic_requirement_class"), family.get("connector_semantic_requirement_class")),
        ("replay_paper_requirement_class", blueprint.get("replay_paper_requirement_class"), family.get("replay_paper_requirement_class")),
        ("live_order_requirement_class", blueprint.get("live_order_requirement_class"), family.get("live_order_requirement_class")),
    )
    for label, actual, expected in checks:
        if actual != expected:
            failures.append(
                f"{family.get('row_family_id')} blueprint {label} must be {expected}, got {actual}"
            )
    if blueprint.get("owner_review_required_before_row_materialization") is not True:
        failures.append(f"{family.get('row_family_id')} blueprint owner review flag must be true")
    if blueprint.get("no_final_bundle_authority_flag") is not True:
        failures.append(f"{family.get('row_family_id')} blueprint no_final_bundle_authority_flag must be true")
    for field in BLUEPRINT_FALSE_FIELDS:
        if blueprint.get(field) is not False:
            failures.append(f"{family.get('row_family_id')} blueprint {field} must be false")
    if "row_source_id" in blueprint:
        failures.append(f"{family.get('row_family_id')} must not create exact row_source_id records in PR98")
    quantum_class = str(family.get("quantum_relevance_class"))
    quantum_refs = blueprint.get("quantum_metadata_refs") or []
    if quantum_class == "NOT_QUANTUM_SPECIFIC_STATIC_METADATA" and quantum_refs:
        failures.append(f"{family.get('row_family_id')} non-quantum family must not carry quantum refs")
    if quantum_class != "NOT_QUANTUM_SPECIFIC_STATIC_METADATA" and not quantum_refs:
        failures.append(f"{family.get('row_family_id')} quantum family must carry static quantum metadata refs")
    return failures


def validate_fixture_payload(fixture: dict[str, Any], source_file_set: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected = {
        "fixture_id": "SYNTHETIC_ATOMICROWS_BUNDLE_ROW_FAMILY_SOURCE_FILES_FIXTURE",
        "fixture_version": "v1",
        "mode": "SOURCE_REQUIRED",
        "execution": "DISABLED",
        "semantic_task_id": SEMANTIC_TASK_ID,
        "schema_ref": DEFAULT_SCHEMA.as_posix(),
        "positive_source_file_set_ref": DEFAULT_SOURCE_FILE_SET.as_posix(),
        "pr97_plan_ref": PR97_PLAN_PATH.as_posix(),
        "expected_source_file_mode": "SOURCE_REQUIRED",
        "expected_source_file_count": 15,
    }
    for field, expected_value in expected.items():
        if fixture.get(field) != expected_value:
            failures.append(f"fixture {field} must be {expected_value}")
    flags = _mapping(fixture.get("expected_no_authority_flags"))
    for field, expected in flags.items():
        if source_file_set.get(field) is not expected:
            failures.append(f"fixture expected_no_authority_flags.{field} does not match source file set")
    cases = _list_of_mappings(fixture.get("fixture_cases"))
    case_ids = [str(case.get("case_id")) for case in cases]
    if case_ids != list(REQUIRED_FIXTURE_CASE_IDS):
        failures.append("fixture_cases must match canonical PR98 negative coverage order")
    if _duplicate_values(case_ids):
        failures.append("fixture case ids must not contain duplicates")
    return failures


def validate_fixture_cases(
    fixture: dict[str, Any],
    source_file_set: dict[str, Any],
    source_files: dict[str, dict[str, Any]],
    schema: dict[str, Any],
    pr97_plan: dict[str, Any],
    repo_root: pathlib.Path,
) -> list[str]:
    failures: list[str] = []
    for case in _list_of_mappings(fixture.get("fixture_cases")):
        case_id = str(case.get("case_id"))
        mutated_set = copy.deepcopy(source_file_set)
        mutated_files = copy.deepcopy(source_files)
        extra_forbidden_paths: tuple[pathlib.Path, ...] = ()

        remove_index = case.get("remove_source_file_index")
        if isinstance(remove_index, int):
            paths = list(mutated_files)
            if 0 <= remove_index < len(paths):
                mutated_files.pop(paths[remove_index], None)

        if case.get("swap_manifest_order"):
            entries = _mapping(
                mutated_set.get("row_family_source_manifest")
            ).get("row_family_source_files")
            if len(entries) >= 2:
                entries[0], entries[1] = entries[1], entries[0]

        source_overrides = case.get("source_file_overrides")
        if isinstance(source_overrides, dict) and mutated_files:
            first_key = sorted(mutated_files)[0]
            mutated_files[first_key].update(copy.deepcopy(source_overrides))

        blueprint_overrides = case.get("blueprint_overrides")
        if isinstance(blueprint_overrides, dict) and mutated_files:
            first_key = sorted(mutated_files)[0]
            blueprints = _list_of_mappings(mutated_files[first_key].get("source_records_or_blueprints"))
            if blueprints:
                blueprints[0].update(copy.deepcopy(blueprint_overrides))

        duplicate_source_index = case.get("duplicate_source_file_id_from_index")
        if isinstance(duplicate_source_index, int):
            files = [mutated_files[key] for key in sorted(mutated_files)]
            if len(files) > 1 and duplicate_source_index < len(files):
                files[1]["source_file_id"] = files[duplicate_source_index]["source_file_id"]

        duplicate_family_index = case.get("duplicate_row_family_ownership_from_index")
        if isinstance(duplicate_family_index, int):
            files = [mutated_files[key] for key in sorted(mutated_files)]
            if len(files) > 1 and duplicate_family_index < len(files):
                files[1]["row_family_id"] = files[duplicate_family_index]["row_family_id"]

        duplicate_blueprint_index = case.get("duplicate_blueprint_id_from_index")
        if isinstance(duplicate_blueprint_index, int):
            files = [mutated_files[key] for key in sorted(mutated_files)]
            if len(files) > 1 and duplicate_blueprint_index < len(files):
                first_blueprints = _list_of_mappings(files[duplicate_blueprint_index].get("source_records_or_blueprints"))
                second_blueprints = _list_of_mappings(files[1].get("source_records_or_blueprints"))
                if first_blueprints and second_blueprints:
                    second_blueprints[0]["blueprint_id"] = first_blueprints[0]["blueprint_id"]

        blueprint_order = case.get("set_blueprint_canonical_order")
        if isinstance(blueprint_order, int) and mutated_files:
            first_key = sorted(mutated_files)[0]
            blueprints = _list_of_mappings(mutated_files[first_key].get("source_records_or_blueprints"))
            if blueprints:
                blueprints[0]["canonical_order"] = blueprint_order

        forbidden_path = case.get("create_forbidden_path")
        if isinstance(forbidden_path, str):
            extra_forbidden_paths = (pathlib.Path(forbidden_path),)

        case_failures: list[str] = []
        case_failures.extend(
            validate_source_file_set_payload(mutated_set, schema, pr97_plan, repo_root)
        )
        case_failures.extend(validate_source_file_payloads(mutated_files, schema, pr97_plan))
        case_failures.extend(
            validate_no_forbidden_artifacts(
                repo_root,
                extra_existing_paths=extra_forbidden_paths,
            )
        )
        expected_valid = case.get("expected_schema_valid")
        if (
            case_id == "BLOCK_BUNDLE_BUILDER_PRESENT"
            and _downstream_validation_branch_allowed(
                _current_branch_context(repo_root).branch
            )
        ):
            expected_valid = True
        if expected_valid is True and case_failures:
            failures.append(f"{case_id} expected valid but failed: {case_failures[0]}")
        if expected_valid is False and not case_failures:
            failures.append(f"{case_id} expected fail-closed validation failure")
    return failures


def validate_no_forbidden_artifacts(
    repo_root: pathlib.Path,
    *,
    extra_existing_paths: Sequence[pathlib.Path] = (),
) -> list[str]:
    failures: list[str] = []
    extra_set = {path.as_posix() for path in extra_existing_paths}
    for relative_path, message in ALWAYS_FORBIDDEN_ARTIFACT_PATHS:
        exists = _resolve(repo_root, relative_path).exists() or relative_path.as_posix() in extra_set
        if exists:
            failures.append(f"{message}: {relative_path.as_posix()}")
    branch_context = _current_branch_context(repo_root)
    pr99_static_builder_allowed = _downstream_validation_branch_allowed(branch_context.branch)
    for relative_path, message in PR99_STATIC_BUILDER_ARTIFACT_PATHS:
        exists = _resolve(repo_root, relative_path).exists() or relative_path.as_posix() in extra_set
        if exists and not pr99_static_builder_allowed:
            failures.append(f"{message}: {relative_path.as_posix()}")
    for directory in (
        pathlib.Path("docs") / "master_plan" / "atomic_rows",
        pathlib.Path("docs") / "master_plan" / "atomicrows",
    ):
        directory_abs = _resolve(repo_root, directory)
        if directory_abs.exists():
            for path in directory_abs.rglob("*.sha256"):
                rel = path.relative_to(repo_root).as_posix() if path.is_absolute() else path.as_posix()
                failures.append(f"forbidden AtomicRows hash file exists: {rel}")
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
            "ATOMICROWS_PR98_BLOCKED_MASTER_PLAN_EDIT: "
            f"{MASTER_PLAN_CURRENT.as_posix()} has local diff"
        ]
    return [f"git diff check failed for {MASTER_PLAN_CURRENT.as_posix()}: {completed.stderr.strip()}"]


def validate_validator_static_surface(validator_path: pathlib.Path) -> list[str]:
    failures: list[str] = []
    try:
        tree = ast.parse(validator_path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return [f"validator static surface parse failed: {exc}"]
    for node in ast.walk(tree):
        imported_roots: list[str] = []
        if isinstance(node, ast.Import):
            imported_roots = [alias.name.split(".", 1)[0].lower() for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots = [node.module.split(".", 1)[0].lower()]
        for root in imported_roots:
            if root in FORBIDDEN_STATIC_SURFACE_IMPORT_ROOTS:
                failures.append(
                    "validator must not import forbidden runtime/quantum surface: "
                    f"{root}"
                )
    return failures


def build_report(
    *,
    source_file_set: dict[str, Any],
    source_files: dict[str, dict[str, Any]],
    pr97_plan: dict[str, Any],
    metadata: dict[str, Any],
    schema_path: pathlib.Path,
    source_file_set_path: pathlib.Path,
    fixture_path: pathlib.Path,
    repo_root: pathlib.Path,
) -> dict[str, Any]:
    families = _row_families(pr97_plan)
    manifest_entries = _manifest_entries(source_file_set)
    source_file_list = [
        {
            "row_family_id": family.get("row_family_id"),
            "row_family_class": family.get("row_family_class"),
            "canonical_order": family.get("canonical_order"),
            "planned_path": family.get("planned_downstream_source_file_path"),
            "actual_path": family.get("planned_downstream_source_file_path"),
            "source_file_id": _source_file_id_for_family(family),
            "source_file_exists": str(family.get("planned_downstream_source_file_path")) in source_files,
            "source_file_mode": source_files.get(
                str(family.get("planned_downstream_source_file_path")), {}
            ).get("source_file_mode"),
            "declared_source_record_count": source_files.get(
                str(family.get("planned_downstream_source_file_path")), {}
            ).get("declared_source_record_count"),
            "declared_source_blueprint_count": source_files.get(
                str(family.get("planned_downstream_source_file_path")), {}
            ).get("declared_source_blueprint_count"),
            "exact_row_count_created_by_pr98_flag": source_files.get(
                str(family.get("planned_downstream_source_file_path")), {}
            ).get("exact_row_count_created_by_pr98_flag"),
            "quantum_relevance_class": family.get("quantum_relevance_class"),
        }
        for family in families
    ]
    report: dict[str, Any] = {
        "report_id": REPORT_ID,
        "report_version": REPORT_VERSION,
        "generated_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "validation_marker": SUCCESS_MARKER,
        "validator": pathlib.Path(__file__).name,
        "roadmap_pr_label": ROADMAP_PR_LABEL,
        "roadmap_delivery_label": ROADMAP_DELIVERY_LABEL,
        "github_pr_number_policy": GITHUB_PR_NUMBER_POLICY,
        "branch": metadata.get("branch"),
        "branch_context_source": metadata.get("branch_context_source"),
        "base_head": metadata.get("base_head"),
        "expected_baseline_ancestor": EXPECTED_BASELINE_ANCESTOR,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "semantic_task_id_source": metadata.get("semantic_task_id_source"),
        "blueprint_semantic_task_id": metadata.get("blueprint_semantic_task_id"),
        "schema_path": schema_path.as_posix(),
        "source_file_set_path": source_file_set_path.as_posix(),
        "fixture_path": fixture_path.as_posix(),
        "pr97_plan_path": PR97_PLAN_PATH.as_posix(),
        "pr97_plan_report_path": PR97_REPORT_PATH.as_posix(),
        "authority_class": AUTHORITY_CLASS,
        "static_only_flag": True,
        "repository_source_files_only_flag": True,
        "consumes_pr97_expansion_plan_flag": True,
        "target_total_row_count": pr97_plan.get("target_total_row_count"),
        "target_total_row_count_authority": pr97_plan.get("target_total_row_count_authority"),
        "target_total_row_count_planning_authority_only_flag": True,
        "source_file_count": len(source_file_list),
        "manifest_entry_count": len(manifest_entries),
        "row_family_ids": [family.get("row_family_id") for family in families],
        "source_files": source_file_list,
        "validation_classes": list(REQUIRED_VALIDATION_CLASSES),
        "required_source_file_concepts": list(REQUIRED_SOURCE_FILE_CONCEPTS),
        "quantum_metadata_refs": list(QUANTUM_METADATA_REFS),
        "quantum_metadata_only_flag": True,
        "quantum_backend_execution_created_flag": False,
        "quantum_advantage_evidence_created_flag": False,
        "atomicrows_bundle_jsonl_exists": _resolve(repo_root, CANONICAL_BUNDLE_JSONL).exists(),
        "atomicrows_bundle_sha256_exists": _resolve(repo_root, CANONICAL_BUNDLE_SHA256).exists(),
        "pr99_bundle_builder_created": False,
        "pr100_sha_freeze_authority_created": False,
        "pr101_final_readiness_created": False,
        "runtime_live_order_source_connector_profit_quantum_backend_effect_created": False,
        "remaining_boundary": (
            "PR98 creates static row-family source files and source-row blueprints only; "
            "it creates no bundle, hash, freeze, builder execution, final readiness, "
            "runtime, live trading, profit, latency, or quantum advantage readiness."
        ),
    }
    for field in FALSE_AUTHORITY_FIELDS:
        report[field] = False
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
        *FALSE_AUTHORITY_FIELDS,
        "quantum_backend_execution_created_flag",
        "quantum_advantage_evidence_created_flag",
        "atomicrows_bundle_jsonl_exists",
        "atomicrows_bundle_sha256_exists",
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
    source_file_set_path: pathlib.Path = DEFAULT_SOURCE_FILE_SET,
    fixture_path: pathlib.Path = DEFAULT_FIXTURE,
    output_path: pathlib.Path = DEFAULT_REPORT,
) -> ValidationResult:
    repo_root = repo_root.resolve()
    schema_abs = _resolve(repo_root, schema_path)
    source_file_set_abs = _resolve(repo_root, source_file_set_path)
    fixture_abs = _resolve(repo_root, fixture_path)
    pr97_plan_abs = _resolve(repo_root, PR97_PLAN_PATH)
    output_abs = _resolve(repo_root, output_path)

    failures: list[str] = []
    schema, schema_failures = _load_json_checked(schema_abs, "SCHEMA")
    source_file_set, source_set_failures = _load_yaml_checked(source_file_set_abs, "SOURCE_FILE_SET")
    fixture, fixture_failures = _load_json_checked(fixture_abs, "FIXTURE")
    pr97_plan, pr97_plan_failures = _load_yaml_checked(pr97_plan_abs, "PR97_PLAN")
    failures.extend(schema_failures)
    failures.extend(source_set_failures)
    failures.extend(fixture_failures)
    failures.extend(pr97_plan_failures)
    if schema is None or source_file_set is None or fixture is None or pr97_plan is None:
        return ValidationResult(False, tuple(failures), None)

    metadata_failures, metadata = validate_roadmap_metadata(repo_root)
    info_lines = tuple(metadata.get("ci_info_lines", ()))
    failures.extend(metadata_failures)
    failures.extend(validate_upstream_pr97(repo_root, pr97_plan))
    source_files, source_file_failures = load_source_files(repo_root, pr97_plan)
    failures.extend(source_file_failures)
    failures.extend(validate_source_file_set_payload(source_file_set, schema, pr97_plan, repo_root))
    failures.extend(validate_source_file_payloads(source_files, schema, pr97_plan))
    failures.extend(validate_fixture_payload(fixture, source_file_set))
    failures.extend(
        validate_fixture_cases(
            fixture,
            source_file_set,
            source_files,
            schema,
            pr97_plan,
            repo_root,
        )
    )
    failures.extend(validate_no_forbidden_artifacts(repo_root))
    failures.extend(validate_master_plan_not_modified(repo_root))
    failures.extend(
        validate_validator_static_surface(
            repo_root / pathlib.Path(__file__).relative_to(_REPO_ROOT)
        )
    )

    report = build_report(
        source_file_set=source_file_set,
        source_files=source_files,
        pr97_plan=pr97_plan,
        metadata=metadata,
        schema_path=schema_path,
        source_file_set_path=source_file_set_path,
        fixture_path=fixture_path,
        repo_root=repo_root,
    )
    second_report = build_report(
        source_file_set=copy.deepcopy(source_file_set),
        source_files=copy.deepcopy(source_files),
        pr97_plan=copy.deepcopy(pr97_plan),
        metadata=copy.deepcopy(metadata),
        schema_path=schema_path,
        source_file_set_path=source_file_set_path,
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
    parser.add_argument("--source-file-set", default=str(DEFAULT_SOURCE_FILE_SET))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    args = parser.parse_args(argv)

    result = validate(
        repo_root=pathlib.Path(args.repo_root),
        schema_path=pathlib.Path(args.schema),
        source_file_set_path=pathlib.Path(args.source_file_set),
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
