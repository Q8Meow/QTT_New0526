#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import copy
from dataclasses import dataclass
import json
import pathlib
import sys
from typing import Any, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import build_atomicrows_bundle as builder  # noqa: E402
from tools import validate_atomicrows_bundle_row_family_source_files as pr98_gate  # noqa: E402
from tools import validate_atomicrows_full_bundle_row_expansion_plan as pr97_gate  # noqa: E402
from src.qtt.core.testing.atomicrows_bundle_state import (  # noqa: E402
    validate_current_atomicrows_bundle_state,
)
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)


DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_bundle_builder_deterministic_assembly_gate.schema.json"
)
DEFAULT_BUILDER_CONFIG = builder.DEFAULT_BUILDER_CONFIG
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "atomicrows"
    / "synthetic_atomicrows_bundle_builder_deterministic_assembly_gate.v1.fixture.json"
)
DEFAULT_REPORT = builder.DEFAULT_REPORT

ROADMAP_INDEX = pr98_gate.ROADMAP_INDEX
BLUEPRINT_INDEX = pr98_gate.BLUEPRINT_INDEX
MASTER_PLAN_CURRENT = pr97_gate.MASTER_PLAN_CURRENT
CANONICAL_BUNDLE_JSONL = builder.CANONICAL_BUNDLE_JSONL
CANONICAL_BUNDLE_SHA256 = builder.CANONICAL_BUNDLE_SHA256

REPORT_ID = builder.REPORT_ID
REPORT_VERSION = builder.REPORT_VERSION
ROADMAP_PR_LABEL = "PR_99"
ROADMAP_DELIVERY_LABEL = "PR #99"
GITHUB_PR_NUMBER_POLICY = "may differ"
SEMANTIC_TASK_ID = "ROADMAP-ATOMICROWS-BUNDLE-BUILDER"
TARGET_BRANCH = "pr99-atomicrows-bundle-builder-deterministic-assembly-gate"
ROADMAP_SHORT_BRANCH_LABEL = "pr99-atomicrows-bundle-builder"
EXPECTED_BASELINE_ANCESTOR = "c67fead"
SUCCESS_MARKER = "QTT_ATOMICROWS_BUNDLE_BUILDER_OK"
FAILURE_MARKER = "QTT_ATOMICROWS_BUNDLE_BUILDER_FAILED"
AUTHORITY_CLASS = builder.AUTHORITY_CLASS

CI_DETACHED_HEAD_MODE_MARKER = pr97_gate.CI_DETACHED_HEAD_MODE_MARKER
CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER = pr97_gate.CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER
DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER = (
    pr97_gate.DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER
)
BRANCH_CONTEXT_ENV_CANDIDATES = pr97_gate.BRANCH_CONTEXT_ENV_CANDIDATES

REQUIRED_CONCEPTS = builder.REQUIRED_CONCEPTS
REQUIRED_FIXTURE_CASE_IDS = (
    "PASS_PR99_STATIC_BUILDER_DRY_RUN_BLOCKED_VALID",
    "BLOCK_BLUEPRINT_ONLY_BUNDLE_CREATION",
    "BLOCK_DUPLICATE_SOURCE_FILE_ID",
    "BLOCK_DUPLICATE_ROW_FAMILY_OWNERSHIP",
    "BLOCK_DUPLICATE_ROW_ID_IF_EXACT_ROWS_EXIST",
    "BLOCK_UNKNOWN_ROW_FAMILY_SOURCE_FILE",
    "BLOCK_NONDETERMINISTIC_SOURCE_ORDER",
    "BLOCK_ATOMICROWS_BUNDLE_SHA256",
    "BLOCK_PR101_FINAL_READINESS",
    "BLOCK_RUNTIME_LIVE_ORDER_SOURCE_CONNECTOR_PROFIT_QUANTUM_EFFECT",
)
BLOCKED_REASON_CODES = (
    builder.BUILD_BLOCKED_REASON_EXACT_SOURCE_ROWS,
    builder.BUILD_BLOCKED_REASON_BLUEPRINTS_ONLY,
    builder.BUILD_BLOCKED_REASON_OWNER_APPROVAL,
    builder.BUILD_BLOCKED_REASON_TARGET_NOT_FEASIBLE,
)
ADDITIONAL_FORBIDDEN_ARTIFACT_PATHS = (
    (
        pathlib.Path("tools") / "build_atomicrows_full_bundle.py",
        "forbidden full bundle builder artifact exists",
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
    (CANONICAL_BUNDLE_JSONL, "forbidden AtomicRows bundle exists"),
    (CANONICAL_BUNDLE_SHA256, "forbidden AtomicRows bundle hash exists"),
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
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]
    report: dict[str, Any] | None
    info_lines: tuple[str, ...] = ()


def _resolve(root: pathlib.Path, path: pathlib.Path) -> pathlib.Path:
    return path if path.is_absolute() else root / path


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return builder.load_json(path)


def load_yaml(path: pathlib.Path) -> dict[str, Any]:
    return builder.load_yaml(path)


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_json_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def _load_json_checked(path: pathlib.Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        return load_json(path), []
    except Exception as exc:
        return None, [f"{label} invalid JSON: {path.as_posix()}: {exc}"]


def _load_yaml_checked(path: pathlib.Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        return load_yaml(path), []
    except Exception as exc:
        return None, [f"{label} invalid YAML/JSON: {path.as_posix()}: {exc}"]


def _downstream_validation_branch_allowed(branch: str) -> bool:
    return pr98_gate._downstream_validation_branch_allowed(branch)


def _main_cumulative_branch_allowed(branch: str) -> bool:
    return pr98_gate._main_cumulative_branch_allowed(branch)


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
        (item for item in pr98_gate._list_of_mappings(roadmap.get("pr_entries")) if item.get("number") == 99),
        None,
    )
    blueprint_entry = next(
        (item for item in pr98_gate._list_of_mappings(blueprint.get("entries")) if item.get("number") == 99),
        None,
    )
    if roadmap_entry is None:
        failures.append("PR99 roadmap index entry missing")
        roadmap_entry = {}
    if blueprint_entry is None:
        failures.append("PR99 blueprint index entry missing")
        blueprint_entry = {}

    checks = (
        ("roadmap.delivery_label", roadmap_entry.get("delivery_label"), ROADMAP_DELIVERY_LABEL),
        ("roadmap.title", roadmap_entry.get("title"), "AtomicRows bundle builder"),
        ("roadmap.branch", roadmap_entry.get("branch"), ROADMAP_SHORT_BRANCH_LABEL),
        ("roadmap.marker", roadmap_entry.get("marker"), SUCCESS_MARKER),
        ("blueprint.delivery_label", blueprint_entry.get("delivery_label"), ROADMAP_DELIVERY_LABEL),
        ("blueprint.title", blueprint_entry.get("title"), "AtomicRows bundle builder"),
        ("blueprint.branch", blueprint_entry.get("branch"), ROADMAP_SHORT_BRANCH_LABEL),
        ("blueprint.validator_marker", blueprint_entry.get("validator_marker"), SUCCESS_MARKER),
        ("blueprint.semantic_task_id", blueprint_entry.get("semantic_task_id"), SEMANTIC_TASK_ID),
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
        "roadmap_pr_label": ROADMAP_PR_LABEL,
        "roadmap_delivery_label": ROADMAP_DELIVERY_LABEL,
        "github_pr_number_policy": GITHUB_PR_NUMBER_POLICY,
        "branch": branch,
        "branch_context_source": branch_context.source,
        "base_head": head,
        "expected_baseline_ancestor": EXPECTED_BASELINE_ANCESTOR,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "blueprint_semantic_task_id": blueprint_entry.get("semantic_task_id"),
        "owner_selected_branch": TARGET_BRANCH,
        "roadmap_short_branch_label": ROADMAP_SHORT_BRANCH_LABEL,
        "branch_name_policy": "OWNER_SELECTED_BRANCH_OVERRIDES_SHORT_ROADMAP_LABEL",
        "validator_marker": SUCCESS_MARKER,
        "ci_info_lines": tuple(info_lines),
    }


def validate_builder_config(config: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    failures = [
        f"BUILDER_CONFIG {failure}"
        for failure in validate_json_schema_subset(config, schema)
    ]
    if config.get("required_builder_concepts") != list(REQUIRED_CONCEPTS):
        failures.append("required_builder_concepts must match canonical PR99 concept order")
    if config.get("blocked_reason_codes") != list(BLOCKED_REASON_CODES):
        failures.append("blocked_reason_codes must match canonical Path B blocked reasons")
    if config.get("authority_class") != AUTHORITY_CLASS:
        failures.append(f"authority_class must be {AUTHORITY_CLASS}")
    return failures


def validate_fixture_payload(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("fixture.mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("fixture.execution must be DISABLED")
    case_ids = [case.get("case_id") for case in pr98_gate._list_of_mappings(fixture.get("fixture_cases"))]
    if case_ids != list(REQUIRED_FIXTURE_CASE_IDS):
        failures.append("fixture case order must match canonical PR99 fail-closed contract")
    expected_flags = fixture.get("expected_no_authority_flags")
    if not isinstance(expected_flags, dict):
        failures.append("fixture.expected_no_authority_flags must be an object")
    else:
        for field, expected in expected_flags.items():
            if expected is not False:
                failures.append(f"fixture expected no-authority flag {field} must be false")
    return failures


def validate_source_summary(inputs: builder.BundleInputs) -> list[str]:
    failures: list[str] = []
    summary = inputs.source_summary
    if len(summary.ordered_paths) != 15:
        failures.append("PR99 must consume all 15 PR98 source files")
    if len(summary.source_files) != 15:
        failures.append("PR99 source-file count found must be 15")
    if summary.missing_source_files:
        failures.append(f"missing PR98 source files: {', '.join(summary.missing_source_files)}")
    if summary.unknown_source_files:
        failures.append(f"unknown PR98 source files: {', '.join(summary.unknown_source_files)}")
    if summary.duplicate_source_file_ids:
        failures.append(f"duplicate source_file_id values: {', '.join(summary.duplicate_source_file_ids)}")
    if summary.duplicate_row_family_ids:
        failures.append(
            f"duplicate row_family_id ownership: {', '.join(summary.duplicate_row_family_ids)}"
        )
    if summary.duplicate_blueprint_ids:
        failures.append(f"duplicate blueprint_id values: {', '.join(summary.duplicate_blueprint_ids)}")
    if summary.duplicate_row_ids:
        failures.append(f"duplicate exact row ids: {', '.join(summary.duplicate_row_ids)}")
    if summary.nondeterministic_order_reasons:
        failures.append(
            "source/record ordering must be deterministic: "
            + ", ".join(summary.nondeterministic_order_reasons)
        )
    if len(summary.exact_rows) != 0:
        failures.append("current PR98 source files must not expose exact source rows")
    if len(summary.blueprints) != 15:
        failures.append("current PR98 source files must expose exactly 15 source-row blueprints")
    for required_ref in pr98_gate.QUANTUM_METADATA_REFS:
        if required_ref not in set(inputs.pr98_source_file_set["quantum_metadata_source_plan"]["allowed_static_metadata_refs"]):
            failures.append(f"PR98 quantum metadata source plan missing {required_ref}")
    return failures


def validate_report(
    report: dict[str, Any],
    inputs: builder.BundleInputs,
    *,
    repo_root: pathlib.Path,
    report_path: pathlib.Path,
) -> list[str]:
    failures: list[str] = []
    expected_core = builder.build_dry_run_report(
        inputs=copy.deepcopy(inputs),
        repo_root=repo_root,
        report_path=report_path,
    )
    for key, value in expected_core.items():
        if report.get(key) != value:
            failures.append(f"generated PR99 dry-run report core field {key} is not deterministic")
    failures.extend(builder.validate_report_determinism(report))
    if report.get("validation_marker") != SUCCESS_MARKER:
        failures.append(f"report.validation_marker must be {SUCCESS_MARKER}")
    for field in (
        "bundle_file_created_flag",
        "bundle_sha_created_flag",
        "sha_authority_created_flag",
        "freeze_authority_created_flag",
        "final_readiness_created_flag",
        "blueprint_materialization_allowed_flag",
    ):
        if report.get(field) is not False:
            failures.append(f"report.{field} must be false")
    if report.get("build_path_decision") != builder.PATH_DECISION:
        failures.append("report.build_path_decision must select Path B")
    if report.get("blocked_reason_codes") != list(BLOCKED_REASON_CODES):
        failures.append("report.blocked_reason_codes must match current Path B authority")
    assembly_gate = report.get("assembly_gate")
    if not isinstance(assembly_gate, dict):
        failures.append("report.assembly_gate must be an object")
    else:
        if assembly_gate.get("build_allowed_flag") is not False:
            failures.append("assembly_gate.build_allowed_flag must be false")
        if assembly_gate.get("build_blocked_flag") is not True:
            failures.append("assembly_gate.build_blocked_flag must be true")
        if assembly_gate.get("no_quantum_backend_execution_created_flag") is not True:
            failures.append("assembly_gate quantum backend boundary must be true")
    return failures


def validate_no_forbidden_artifacts(
    repo_root: pathlib.Path,
    *,
    extra_existing_paths: Sequence[pathlib.Path] = (),
) -> list[str]:
    failures: list[str] = validate_current_atomicrows_bundle_state(
        repo_root,
        label="AtomicRows bundle builder deterministic assembly gate",
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


def validate_static_surface(path: pathlib.Path) -> list[str]:
    failures: list[str] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return [f"{path.as_posix()} is not valid Python: {exc}"]
    for node in ast.walk(tree):
        root = ""
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FORBIDDEN_STATIC_SURFACE_IMPORT_ROOTS:
                    failures.append(f"{path.name} imports forbidden runtime/quantum module {root}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".")[0]
            if root in FORBIDDEN_STATIC_SURFACE_IMPORT_ROOTS:
                failures.append(f"{path.name} imports forbidden runtime/quantum module {root}")
    return failures


def validate(
    *,
    repo_root: pathlib.Path = pathlib.Path("."),
    schema_path: pathlib.Path = DEFAULT_SCHEMA,
    builder_config_path: pathlib.Path = DEFAULT_BUILDER_CONFIG,
    fixture_path: pathlib.Path = DEFAULT_FIXTURE,
    output_path: pathlib.Path = DEFAULT_REPORT,
) -> ValidationResult:
    repo_root = repo_root.resolve()
    schema, schema_failures = _load_json_checked(_resolve(repo_root, schema_path), "SCHEMA")
    config, config_failures = _load_yaml_checked(_resolve(repo_root, builder_config_path), "BUILDER_CONFIG")
    fixture, fixture_failures = _load_json_checked(_resolve(repo_root, fixture_path), "FIXTURE")
    failures = [*schema_failures, *config_failures, *fixture_failures]
    if schema is None or config is None or fixture is None:
        return ValidationResult(False, tuple(failures), None)

    metadata_failures, metadata = validate_roadmap_metadata(repo_root)
    info_lines = tuple(metadata.get("ci_info_lines", ()))
    failures.extend(metadata_failures)

    inputs, input_failures = builder.load_bundle_inputs(
        repo_root=repo_root,
        builder_config_path=builder_config_path,
    )
    failures.extend(input_failures)
    if inputs is None:
        return ValidationResult(False, tuple(failures), None, info_lines)

    failures.extend(validate_builder_config(config, schema))
    failures.extend(validate_fixture_payload(fixture))
    failures.extend(validate_source_summary(inputs))
    failures.extend(validate_no_forbidden_artifacts(repo_root))
    failures.extend(validate_master_plan_not_modified(repo_root))
    failures.extend(validate_static_surface(repo_root / "tools" / "build_atomicrows_bundle.py"))
    failures.extend(validate_static_surface(repo_root / "tools" / pathlib.Path(__file__).name))

    report = builder.build_dry_run_report(
        inputs=inputs,
        repo_root=repo_root,
        report_path=output_path,
    )
    report["validation_marker"] = SUCCESS_MARKER
    report["github_pr_number_policy"] = GITHUB_PR_NUMBER_POLICY
    report["branch"] = metadata.get("branch")
    report["branch_context_source"] = metadata.get("branch_context_source")
    report["base_head"] = metadata.get("base_head")
    report["expected_baseline_ancestor"] = metadata.get("expected_baseline_ancestor")
    report["owner_selected_branch"] = metadata.get("owner_selected_branch")
    report["roadmap_short_branch_label"] = metadata.get("roadmap_short_branch_label")
    report["branch_name_policy"] = metadata.get("branch_name_policy")
    report["schema_path"] = schema_path.as_posix()
    report["builder_config_path"] = builder_config_path.as_posix()
    report["fixture_path"] = fixture_path.as_posix()

    expected_report = copy.deepcopy(report)
    failures.extend(
        validate_report(
            report,
            inputs,
            repo_root=repo_root,
            report_path=output_path,
        )
    )
    if report != expected_report:
        failures.append("PR99 report mutation check failed")

    if not failures and not _should_skip_default_report_write(
        repo_root=repo_root,
        output_abs=_resolve(repo_root, output_path),
        metadata=metadata,
    ):
        write_json_report(report, _resolve(repo_root, output_path))
    return ValidationResult(not failures, tuple(failures), report, info_lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate PR99 AtomicRows bundle-builder deterministic assembly gate."
    )
    parser.add_argument("--repo-root", type=pathlib.Path, default=pathlib.Path("."))
    parser.add_argument("--schema", type=pathlib.Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--config", type=pathlib.Path, default=DEFAULT_BUILDER_CONFIG)
    parser.add_argument("--fixture", type=pathlib.Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)

    result = validate(
        repo_root=args.repo_root,
        schema_path=args.schema,
        builder_config_path=args.config,
        fixture_path=args.fixture,
        output_path=args.out,
    )
    if result.ok:
        print(SUCCESS_MARKER)
        for line in result.info_lines:
            print(line)
        return 0
    print(FAILURE_MARKER, file=sys.stderr)
    for failure in result.failures:
        print(failure, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
