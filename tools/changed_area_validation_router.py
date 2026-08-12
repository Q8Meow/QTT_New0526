#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.repo_path_refs import normalize_repo_ref
from tools.validation_scope_registry import (
    ST12A_ALLOWED_EXACT_PATHS,
    ST12B_ALLOWED_EXACT_PATHS,
    ST12C_ALLOWED_EXACT_PATHS,
    ST12D_ALLOWED_EXACT_PATHS,
    ST12E_ALLOWED_EXACT_PATHS,
    ST12F_ALLOWED_EXACT_PATHS,
    ST12G_ALLOWED_EXACT_PATHS,
)
from tools.validation_inventory import (
    FAST_UNIVERSAL_PREFLIGHT,
    GENERATED_REPORT_GLOBS,
    PR152_TRACKED_GLOBS,
    ST12C_QKU_VALIDATOR_IDS,
    ST12D_QKU_VALIDATOR_IDS,
    ST12E_QKU_VALIDATOR_IDS,
    ST12F_QKU_VALIDATOR_IDS,
    ST12G_QKU_VALIDATOR_IDS,
    ST12G_REQUIRED_VALIDATOR_IDS,
    VALIDATION_INFRASTRUCTURE_GLOBS,
    ValidatorInventoryEntry,
    entries_matching_path,
    inventory_by_id,
    phase_job_id,
    phase_job_ids_for_validators,
    validation_inventory,
)
from tools import run_validation_gates as runner

ROUTING_POLICY_VERSION = 1
FORCE_FULL_FLAG_NAME = "QTT_FORCE_FULL_VALIDATION"
ST12G_INDEPENDENT_VALIDATOR_SCRIPT = (
    "tools/independent_validate_qku_computation_control_plane_g.py"
)
QKU_VALIDATOR_IDS = frozenset(
    {
        "independent_validate_qku_computation_control_plane",
        "independent_validate_qku_computation_control_plane_latency",
        "independent_validate_qku_computation_control_plane_model_risk",
        "validate_qku_computation_control_plane_architecture",
        "validate_qku_computation_control_plane_operations",
        "validate_qku_computation_control_plane_quantum",
        "validate_qku_computation_control_plane_security",
        "validate_qku_computation_control_plane_source",
        *ST12C_QKU_VALIDATOR_IDS,
        *ST12D_QKU_VALIDATOR_IDS,
        *ST12E_QKU_VALIDATOR_IDS,
        *ST12F_QKU_VALIDATOR_IDS,
        *ST12G_QKU_VALIDATOR_IDS,
    }
)
QKU_ALLOWED_EXACT_PATHS = frozenset(
    (
        *ST12A_ALLOWED_EXACT_PATHS,
        *ST12B_ALLOWED_EXACT_PATHS,
        *ST12C_ALLOWED_EXACT_PATHS,
        *ST12D_ALLOWED_EXACT_PATHS,
        *ST12E_ALLOWED_EXACT_PATHS,
        *ST12F_ALLOWED_EXACT_PATHS,
        *ST12G_ALLOWED_EXACT_PATHS,
    )
)


@dataclass(frozen=True)
class RouterInput:
    repo_root: Path
    base_ref: str | None = None
    head_ref: str | None = None
    changed_files: tuple[str, ...] = ()
    workflow_event_name: str = ""
    github_ref: str = ""
    github_base_ref: str = ""
    github_head_ref: str = ""
    force_full_flag: bool = False
    manual_mode: str = ""
    current_branch: str = ""
    is_main_push: bool = False
    is_pull_request: bool = False
    is_schedule: bool = False
    is_workflow_dispatch: bool = False


@dataclass(frozen=True)
class RouterResult:
    required_validators: tuple[str, ...]
    skipped_validators: tuple[str, ...]
    skip_reasons: dict[str, str]
    changed_files: tuple[str, ...]
    classified_files: dict[str, tuple[str, ...]]
    unknown_files: tuple[str, ...]
    touched_domains: tuple[str, ...]
    touched_generated_reports: tuple[str, ...]
    touched_validator_tools: tuple[str, ...]
    touched_workflows: tuple[str, ...]
    touched_tests: tuple[str, ...]
    full_validation_required: bool
    full_validation_reason: str
    pr152_currentization_required: bool
    pr152_currentization_reason: str
    cross_platform_path_scan_required: bool
    branch_context_required: bool
    fail_closed_reasons: tuple[str, ...]
    required_jobs: tuple[str, ...]
    routing_policy_version: int = ROUTING_POLICY_VERSION

    def to_json_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["skip_reasons"] = dict(sorted(self.skip_reasons.items()))
        return payload


def _git_stdout(repo_root: Path, args: Sequence[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout, completed.stderr


def _matches_any(path: str, globs: Sequence[str]) -> bool:
    from fnmatch import fnmatchcase

    normalized = normalize_repo_ref(path)
    return any(fnmatchcase(normalized, glob) for glob in globs)


def _normalize_changed_files(paths: Sequence[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    for path in paths:
        stripped = str(path).strip()
        if not stripped:
            continue
        normalized.append(normalize_repo_ref(stripped))
    return tuple(sorted(dict.fromkeys(normalized)))


def _current_branch(repo_root: Path) -> str:
    rc, stdout, _stderr = _git_stdout(repo_root, ["branch", "--show-current"])
    if rc == 0 and stdout.strip():
        return stdout.strip()
    rc, stdout, _stderr = _git_stdout(repo_root, ["rev-parse", "--abbrev-ref", "HEAD"])
    if rc == 0:
        return stdout.strip()
    return ""


def _diff_name_only(
    repo_root: Path,
    base_ref: str,
    head_ref: str,
) -> tuple[str, ...]:
    rc, stdout, _stderr = _git_stdout(
        repo_root,
        ["diff", "--name-only", "--diff-filter=ACMRTUXB", f"{base_ref}...{head_ref}"],
    )
    if rc == 0:
        return _normalize_changed_files(stdout.splitlines())
    return ()


def changed_files_from_git(
    repo_root: str | Path,
    *,
    base_ref: str | None = None,
    head_ref: str | None = None,
) -> tuple[str, ...]:
    root = Path(repo_root)
    head = head_ref or "HEAD"
    bases: list[str] = []
    if base_ref:
        bases.extend([base_ref, f"origin/{base_ref}", f"refs/remotes/origin/{base_ref}"])
    bases.extend(["origin/main", "main"])
    cumulative: list[str] = []
    for base in dict.fromkeys(bases):
        rc, stdout, _stderr = _git_stdout(
            root,
            [
                "diff",
                "--name-only",
                "--diff-filter=ACMRTUXB",
                f"{base}...{head}",
            ],
        )
        if rc == 0:
            cumulative.extend(stdout.splitlines())
            break
    for args in (
        ["diff", "--name-only", "--diff-filter=ACMRTUXB", "HEAD"],
        ["diff", "--cached", "--name-only", "--diff-filter=ACMRTUXB"],
        ["ls-files", "--others", "--exclude-standard"],
    ):
        rc, stdout, _stderr = _git_stdout(root, args)
        if rc == 0:
            cumulative.extend(stdout.splitlines())
    return _normalize_changed_files(cumulative)


def router_input_from_environment(
    repo_root: str | Path,
    *,
    changed_files: Sequence[str] = (),
    base_ref: str | None = None,
    head_ref: str | None = None,
    force_full_flag: bool = False,
    manual_mode: str = "",
) -> RouterInput:
    root = Path(repo_root)
    event_name = os.getenv("GITHUB_EVENT_NAME", "")
    github_ref = os.getenv("GITHUB_REF", "")
    github_base_ref = os.getenv("GITHUB_BASE_REF", "")
    github_head_ref = os.getenv("GITHUB_HEAD_REF", "")
    env_force = os.getenv(FORCE_FULL_FLAG_NAME, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "full",
    }
    resolved_changed = _normalize_changed_files(changed_files)
    if not resolved_changed:
        resolved_changed = changed_files_from_git(
            root,
            base_ref=base_ref or github_base_ref or None,
            head_ref=head_ref or "HEAD",
        )
    return RouterInput(
        repo_root=root,
        base_ref=base_ref or github_base_ref or None,
        head_ref=head_ref or "HEAD",
        changed_files=resolved_changed,
        workflow_event_name=event_name,
        github_ref=github_ref,
        github_base_ref=github_base_ref,
        github_head_ref=github_head_ref,
        force_full_flag=force_full_flag or env_force,
        manual_mode=manual_mode,
        current_branch=_current_branch(root),
        is_main_push=(
            event_name == "push" and github_ref == "refs/heads/main"
        ),
        is_pull_request=event_name == "pull_request",
        is_schedule=event_name == "schedule",
        is_workflow_dispatch=event_name == "workflow_dispatch",
    )


def _is_generated_report(path: str) -> bool:
    return _matches_any(path, tuple(GENERATED_REPORT_GLOBS))


def _is_validation_infra(path: str) -> bool:
    return _matches_any(path, tuple(VALIDATION_INFRASTRUCTURE_GLOBS))


def _is_pr152_tracked(path: str) -> bool:
    return _matches_any(path, tuple(PR152_TRACKED_GLOBS)) or (
        path.startswith("docs/master_plan/generated/PR")
        and path.endswith(".report.json")
    )


def _is_qku_control_plane_path(path: str) -> bool:
    return normalize_repo_ref(path) in QKU_ALLOWED_EXACT_PATHS


def _current_pr152_inventory_counts(repo_root: Path) -> dict[str, int]:
    generated_root = repo_root / "docs/master_plan/generated"
    tests_root = repo_root / "tests"
    tools_root = repo_root / "tools"

    return {
        "generated_report_count": sum(1 for path in generated_root.rglob("*") if path.is_file())
        if generated_root.exists()
        else 0,
        "test_file_count": sum(
            1 for path in tests_root.rglob("*.py") if path.is_file()
        )
        if tests_root.exists()
        else 0,
        "validator_tool_count": sum(
            1 for path in tools_root.glob("validate_*.py") if path.is_file()
        )
        if tools_root.exists()
        else 0,
    }


def _pr152_currentization_report_matches_filesystem(repo_root: Path) -> bool:
    report_path = (
        repo_root
        / "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
    )
    if not report_path.exists():
        return False
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    current = _current_pr152_inventory_counts(repo_root)
    generated = report.get("generated_report_consistency_audit", {})
    tests = report.get("schema_fixture_test_consistency_audit", {})
    validators = report.get("validator_tool_registry_audit", {})
    return (
        generated.get("generated_report_count") == current["generated_report_count"]
        and tests.get("test_file_count") == current["test_file_count"]
        and validators.get("validator_tool_count") == current["validator_tool_count"]
    )


def _classify_changed_files(
    changed_files: Sequence[str],
) -> tuple[
    dict[str, tuple[str, ...]],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
]:
    classified: dict[str, tuple[str, ...]] = {}
    unknown: list[str] = []
    generated: list[str] = []
    tools: list[str] = []
    workflows: list[str] = []
    tests: list[str] = []
    domains: set[str] = set()
    fail_closed: list[str] = []
    entries = validation_inventory()
    qku_entries = {
        entry.validator_id: entry
        for entry in entries
        if entry.validator_id in QKU_VALIDATOR_IDS
    }
    st12g_entries = {
        entry.validator_id: entry
        for entry in entries
        if entry.validator_id in ST12G_REQUIRED_VALIDATOR_IDS
    }

    for path in changed_files:
        matches_by_id = {
            entry.validator_id: entry
            for entry in entries_matching_path(path, entries)
        }
        if _is_qku_control_plane_path(path):
            matches_by_id.update(qku_entries)
        if normalize_repo_ref(path) in ST12G_ALLOWED_EXACT_PATHS:
            matches_by_id.update(st12g_entries)
        matches = tuple(
            matches_by_id[validator_id]
            for validator_id in sorted(matches_by_id)
        )
        if matches:
            validator_ids = tuple(sorted(entry.validator_id for entry in matches))
            classified[path] = validator_ids
            domains.update(entry.owner_domain for entry in matches)
        else:
            unknown.append(path)
            if _is_generated_report(path):
                fail_closed.append(f"GENERATED_REPORT_OWNER_MISSING: {path}")
            elif path.startswith("tools/") and path.endswith(".py"):
                fail_closed.append(f"VALIDATOR_TOOL_OWNER_MISSING: {path}")

        if _is_generated_report(path):
            generated.append(path)
        if path.startswith("tools/") and path.endswith(".py"):
            tools.append(path)
        if path.startswith(".github/workflows/"):
            workflows.append(path)
        if path.startswith("tests/"):
            tests.append(path)

    return (
        dict(sorted(classified.items())),
        tuple(sorted(unknown)),
        tuple(sorted(generated)),
        tuple(sorted(tools)),
        tuple(sorted(workflows)),
        tuple(sorted(tests)),
        tuple(sorted(domains)),
        tuple(sorted(fail_closed)),
    )


def _full_validation_reason(
    router_input: RouterInput,
    changed_files: Sequence[str],
    classified_files: Mapping[str, Sequence[str]],
    entries_by_id: Mapping[str, ValidatorInventoryEntry],
) -> str:
    manual_full = router_input.manual_mode.lower() in {"full", "true", "1", "yes"}
    if router_input.force_full_flag:
        return f"{FORCE_FULL_FLAG_NAME}=1"
    if router_input.is_main_push:
        return "main push runs full validation"
    if router_input.is_schedule:
        return "scheduled validation runs full validation"
    if router_input.is_workflow_dispatch and (manual_full or not router_input.manual_mode):
        return "workflow_dispatch defaults to full validation"
    for path in changed_files:
        if _is_validation_infra(path):
            return f"validation infrastructure changed: {path}"
        for validator_id in classified_files.get(path, ()):
            entry = entries_by_id[validator_id]
            if entry.full_validation_required_when_changed:
                return f"full validation required by {validator_id}: {path}"
    return ""


def build_router_result(router_input: RouterInput) -> RouterResult:
    changed_files = _normalize_changed_files(router_input.changed_files)
    entries = validation_inventory()
    by_id = {entry.validator_id: entry for entry in entries}
    all_ids = tuple(sorted(by_id))
    (
        classified_files,
        unknown_files,
        touched_generated_reports,
        touched_validator_tools,
        touched_workflows,
        touched_tests,
        touched_domains,
        fail_closed_reasons,
    ) = _classify_changed_files(changed_files)
    routing_failures = set(fail_closed_reasons)
    for path in changed_files:
        if _is_qku_control_plane_path(path):
            routed = set(classified_files.get(path, ()))
            missing = sorted(QKU_VALIDATOR_IDS - routed)
            if missing:
                routing_failures.add(
                    f"QKU_VALIDATION_ROUTE_INCOMPLETE: {path}: {missing}"
                )
        if normalize_repo_ref(path) in ST12G_ALLOWED_EXACT_PATHS:
            routed = set(classified_files.get(path, ()))
            missing = sorted(ST12G_REQUIRED_VALIDATOR_IDS - routed)
            if missing:
                routing_failures.add(
                    f"ST12G_VALIDATION_ROUTE_INCOMPLETE: {path}: {missing}"
                )
    fail_closed_reasons = tuple(sorted(routing_failures))

    full_reason = _full_validation_reason(
        router_input,
        changed_files,
        classified_files,
        by_id,
    )
    if unknown_files and not fail_closed_reasons and not full_reason:
        full_reason = "unknown changed files force full validation"
    full_validation_required = bool(full_reason)

    required_ids: set[str]
    if full_validation_required:
        required_ids = set(all_ids)
    else:
        required_ids = {
            entry.validator_id
            for entry in entries
            if entry.runs_on_pull_request_default
            or FAST_UNIVERSAL_PREFLIGHT in entry.validator_class
        }
        for validator_ids in classified_files.values():
            required_ids.update(validator_ids)

    if touched_generated_reports:
        path_validator_ids = {
            validator_id
            for path in touched_generated_reports
            for validator_id in classified_files.get(path, ())
        }
        required_ids.update(path_validator_ids)

    required = tuple(sorted(required_ids))
    skipped = tuple(sorted(set(all_ids) - set(required)))
    skip_reasons = {
        validator_id: "unaffected by changed-area router; still runs on main/nightly/manual full"
        for validator_id in skipped
    }
    pr152_tracked_changed = any(_is_pr152_tracked(path) for path in changed_files)
    pr152_clean = _pr152_currentization_report_matches_filesystem(router_input.repo_root)
    pr152_required = pr152_tracked_changed and not pr152_clean
    if pr152_required:
        pr152_reason = "PR152-tracked generated report/tool inventory changed"
    elif pr152_tracked_changed:
        pr152_reason = "PR152-tracked inventory changed and currentization report matches filesystem counts"
    else:
        pr152_reason = "No PR152-tracked file, generated report count, or currentization tool changed"
    cross_platform_required = bool(
        touched_generated_reports
        or any(by_id[validator_id].cross_platform_sensitive for validator_id in required)
    )
    branch_context_required = (
        router_input.is_pull_request
        or router_input.is_main_push
        or router_input.is_workflow_dispatch
        or bool(os.getenv("GITHUB_ACTIONS"))
    )
    return RouterResult(
        required_validators=required,
        skipped_validators=skipped,
        skip_reasons=skip_reasons,
        changed_files=changed_files,
        classified_files=classified_files,
        unknown_files=unknown_files,
        touched_domains=touched_domains,
        touched_generated_reports=touched_generated_reports,
        touched_validator_tools=touched_validator_tools,
        touched_workflows=touched_workflows,
        touched_tests=touched_tests,
        full_validation_required=full_validation_required,
        full_validation_reason=full_reason,
        pr152_currentization_required=pr152_required,
        pr152_currentization_reason=pr152_reason,
        cross_platform_path_scan_required=cross_platform_required,
        branch_context_required=branch_context_required,
        fail_closed_reasons=fail_closed_reasons,
        required_jobs=phase_job_ids_for_validators(required, by_id),
    )


def build_routing_policy_report() -> dict[str, object]:
    full_validation_jobs = sorted(
        {phase_job_id(phase) for phase in runner.ORDERED_PHASES}
    )
    return {
        "routing_policy_version": ROUTING_POLICY_VERSION,
        "pull_request_default_mode": (
            "fast universal preflight plus validators matched by changed files"
        ),
        "main_push_mode": "full validation",
        "schedule_mode": "full validation",
        "workflow_dispatch_mode": "full validation by default",
        "force_full_flag_name": FORCE_FULL_FLAG_NAME,
        "unknown_file_policy": "force full validation unless generated/tool ownership is missing",
        "generated_report_without_owner_policy": "fail closed",
        "validation_infra_changed_policy": "force full validation",
        "workflow_changed_policy": "force full validation and workflow sanity",
        "pr152_currentization_policy": (
            "decision required when PR152-tracked reports, counts, or tools change"
        ),
        "cross_platform_path_scan_policy": (
            "scan touched generated JSON/report/manifest/shard refs"
        ),
        "branch_context_policy": "required on pull_request, main, and workflow_dispatch",
        "required_jobs_for_reduced_pr_mode": full_validation_jobs,
        "required_jobs_for_full_mode": full_validation_jobs,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--base-ref")
    parser.add_argument("--head-ref")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--force-full", action="store_true")
    parser.add_argument("--manual-mode", default="")
    parser.add_argument("--report-out", type=Path)
    args = parser.parse_args(argv)

    router_input = router_input_from_environment(
        args.repo_root,
        changed_files=args.changed_file,
        base_ref=args.base_ref,
        head_ref=args.head_ref,
        force_full_flag=args.force_full,
        manual_mode=args.manual_mode,
    )
    result = build_router_result(router_input)
    payload = result.to_json_dict()
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.report_out:
        report_out = args.report_out
        if not report_out.is_absolute():
            report_out = args.repo_root / report_out
        report_out.parent.mkdir(parents=True, exist_ok=True)
        report_out.write_text(text, encoding="utf-8")
    print(text, end="")
    if result.fail_closed_reasons:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
