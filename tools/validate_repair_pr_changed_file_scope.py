#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import ci_branch_context as context  # noqa: E402


SUCCESS_MARKER = "REPAIR_PR_CHANGED_FILE_SCOPE_OK"

TRANSIENT_RUNTIME_ARTIFACT_PATH_PREFIXES = (
    ".tmp/qtt-validation-router/",
    ".tmp/qtt-validation-timing/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    "htmlcov/",
)
TRANSIENT_RUNTIME_ARTIFACT_EXACT_PATHS = frozenset(
    {
        ".coverage",
        "coverage.xml",
    }
)
FORBIDDEN_REPAIR_SCOPE_PATHS = (
    "docs/master_plan/generated/PR163_C_FinalSummary.report.json",
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
    "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256",
    "docs/master_plan/source_evidence/accepted_source_packet.json",
    "src/qtt/source_evidence/connector_binding.py",
    "src/qtt/stage1_prediction_markets/private_state/account_snapshot.py",
    "src/qtt/stage1_prediction_markets/runtime_cash/cash_state.py",
    "src/qtt/stage1_prediction_markets/order_live/live_order_router.py",
    "src/qtt/stage1_prediction_markets/quantum_backend/backend_runtime.py",
    "src/qtt/stage1_prediction_markets/llm_runtime/model_client.py",
    "src/qtt/stage1_prediction_markets/freeze_checksum/qku_digest.py",
    "src/qtt/stage1_prediction_markets/profit_claims/profit_summary.py",
)


@dataclass(frozen=True)
class _ChangedPath:
    path: str
    source: str
    status: str = ""

    @property
    def is_untracked_worktree_path(self) -> bool:
        return self.source == "worktree" and self.status == "??"


def _git(
    repo_root: Path,
    args: Sequence[str],
) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout.rstrip(), completed.stderr.rstrip()


def _normalize_repo_path(path: str) -> str | None:
    normalized = path.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized if normalized else None


def _porcelain_status(line: str) -> str:
    return line[:2] if len(line) >= 2 else line


def _normalize_status_path(line: str) -> str | None:
    if len(line) < 3:
        return None
    if len(line) >= 3 and line[2] == " ":
        path = line[3:].strip()
    elif len(line) >= 2 and line[1] == " ":
        path = line[2:].strip()
    else:
        path = line[3:].strip()
    if " -> " in path:
        path = path.rsplit(" -> ", 1)[1]
    return _normalize_repo_path(path)


def _is_transient_runtime_artifact_path(path: str) -> bool:
    normalized = _normalize_repo_path(path)
    if not normalized:
        return False
    return (
        normalized in TRANSIENT_RUNTIME_ARTIFACT_EXACT_PATHS
        or any(
            normalized.startswith(prefix)
            for prefix in TRANSIENT_RUNTIME_ARTIFACT_PATH_PREFIXES
        )
        or normalized.startswith("__pycache__/")
        or "/__pycache__/" in normalized
    )


def _explicit_repair_branches_with_scope() -> frozenset[str]:
    branches: set[str] = set()
    for policy in context.BRANCH_CONTEXT_GATE_POLICIES.values():
        branches.update(
            branch for branch in policy.allowed_branches if context.is_repair_branch(branch)
        )
        branches.update(policy.local_repair_branches_requiring_ancestry)
        branches.update(policy.detached_head_ref_branches)
    branches.update(
        branch
        for branch in context.EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_CHANGED_PATHS
        if context.is_repair_branch(branch)
    )
    return frozenset(branches)


def _changed_worktree_entries_from_git(repo_root: Path) -> tuple[_ChangedPath, ...]:
    rc, stdout, _stderr = _git(
        repo_root,
        ("status", "--porcelain", "--untracked-files=all"),
    )
    if rc != 0 or not stdout.strip():
        return ()
    entries = {
        _ChangedPath(
            path=path,
            source="worktree",
            status=_porcelain_status(line),
        )
        for line in stdout.splitlines()
        for path in (_normalize_status_path(line),)
        if path
    }
    return tuple(sorted(entries, key=lambda entry: (entry.path, entry.status)))


def _changed_worktree_files_from_git(repo_root: Path) -> tuple[str, ...]:
    return tuple(entry.path for entry in _changed_worktree_entries_from_git(repo_root))


def _changed_file_entries_from_git(repo_root: Path) -> tuple[_ChangedPath, ...]:
    worktree_entries = _changed_worktree_entries_from_git(repo_root)
    if worktree_entries:
        return worktree_entries

    diff_commands = (
        ("diff", "--name-only", "HEAD^1", "HEAD"),
        ("diff", "--name-only", "origin/main...HEAD"),
        ("diff", "--name-only", "main...HEAD"),
    )
    for args in diff_commands:
        rc, stdout, _stderr = _git(repo_root, args)
        if rc == 0 and stdout.strip():
            return tuple(
                _ChangedPath(path=path, source="diff", status="committed")
                for line in stdout.splitlines()
                for path in (_normalize_repo_path(line),)
                if path
            )
    return ()


def _changed_files_from_git(repo_root: Path) -> tuple[str, ...]:
    return tuple(entry.path for entry in _changed_file_entries_from_git(repo_root))


def _changed_files_for_repair_scope_from_git(
    repo_root: Path,
    failures: list[str],
) -> tuple[str, ...]:
    scope_paths: list[str] = []
    for entry in _changed_file_entries_from_git(repo_root):
        if not _is_transient_runtime_artifact_path(entry.path):
            scope_paths.append(entry.path)
            continue
        if entry.is_untracked_worktree_path:
            continue
        failures.append(
            "git hygiene failure: transient runtime artifact is tracked or staged: "
            f"{entry.path}"
        )
    return tuple(scope_paths)


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)


def _check_static_scope_matrix(failures: list[str]) -> None:
    allowed_cases = (
        (
            context.PR160_MAIN_ANCESTRY_REPAIR_BRANCH,
            "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        ),
        (
            context.PR159R_DETACHED_HEAD_REPAIR_BRANCH,
            "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        ),
        (
            context.PR159S_BRANCH_CONTEXT_REPAIR_BRANCH,
            "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        ),
        (
            context.PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "tools/ci_branch_context.py",
        ),
    )
    for branch, path in allowed_cases:
        _expect(
            context.changed_path_allowed_for_explicit_repair_branch(branch, path),
            failures,
            f"expected repair path should be allowed: {branch}:{path}",
        )

    outside_cases = (
        (
            context.PR160_MAIN_ANCESTRY_REPAIR_BRANCH,
            "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        ),
        (
            context.PR159S_BRANCH_CONTEXT_REPAIR_BRANCH,
            "docs/master_plan/generated/PR159R_ExactSourceLocatorValueUnitCapture.report.json",
        ),
        (
            "repair/pr160-unlisted-context",
            "tools/ci_branch_context.py",
        ),
    )
    for branch, path in outside_cases:
        _expect(
            not context.changed_path_allowed_for_explicit_repair_branch(branch, path),
            failures,
            f"outside repair path should fail closed: {branch}:{path}",
        )

    for path in FORBIDDEN_REPAIR_SCOPE_PATHS:
        _expect(
            not context.changed_path_allowed_for_explicit_repair_branch(
                context.PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
                path,
            ),
            failures,
            f"forbidden repair path was silently allowed: {path}",
        )


def _check_current_repair_branch_scope(repo_root: Path, failures: list[str]) -> None:
    branch = context.current_branch_context(repo_root).branch
    normalized = context.normalize_branch_context(branch)
    if not context.is_repair_branch(normalized):
        return

    known_repairs = _explicit_repair_branches_with_scope()
    _expect(
        normalized in known_repairs,
        failures,
        f"repair branch has no explicit central scope: {normalized}",
    )
    if normalized not in known_repairs:
        return

    changed_files = _changed_files_for_repair_scope_from_git(repo_root, failures)
    for path in changed_files:
        if context.changed_path_allowed_for_explicit_repair_branch(normalized, path):
            continue
        failures.append(f"repair branch changed path outside explicit scope: {path}")


def validate(repo_root: Path) -> tuple[str, ...]:
    failures: list[str] = []
    _check_static_scope_matrix(failures)
    _check_current_repair_branch_scope(repo_root, failures)
    return tuple(failures)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)

    failures = validate(args.repo_root.resolve())
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
