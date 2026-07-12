#!/usr/bin/env python3
"""Fail-closed validation for the exact PR169-QKU-FORMULA-EXP1 rollback.

This validator is intentionally branch-specific. It does not grant general changed-path
or trading authority. It proves that the rollback restores the trusted pre-PR #272 tree,
except for this validator and the workflow routing needed to execute it.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROLLBACK_BRANCH = "pr169-qku-formula-exp1-rollback"
TRUSTED_BASELINE = "e90b2b31bbdbdf35d4e6aff8fe30392b31fc7bb6"
CURRENTIZATION_PATHS = frozenset(
    {
        ".github/workflows/qtt_validation.yml",
        "tools/validate_pr169_qku_formula_exp1_rollback.py",
    }
)


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _branch(repo_root: Path) -> str:
    for name in ("GITHUB_HEAD_REF", "BRANCH_NAME"):
        import os

        value = os.environ.get(name, "").strip()
        if value:
            return value
    result = _git(repo_root, "branch", "--show-current")
    return result.stdout.strip() if result.returncode == 0 else ""


def _changed_paths(repo_root: Path) -> set[str]:
    result = _git(repo_root, "diff", "--name-only", "origin/main...HEAD")
    if result.returncode != 0:
        raise AssertionError(result.stderr.strip() or "unable to enumerate rollback diff")
    return {line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}


def validate(repo_root: Path) -> None:
    branch = _branch(repo_root)
    if branch != ROLLBACK_BRANCH:
        raise AssertionError(f"unexpected branch: {branch!r}")

    changed = _changed_paths(repo_root)
    if not CURRENTIZATION_PATHS.issubset(changed):
        missing = sorted(CURRENTIZATION_PATHS - changed)
        raise AssertionError(f"missing rollback CI currentization paths: {missing}")

    unexpected_currentization = {
        path
        for path in changed
        if path not in CURRENTIZATION_PATHS
        and not (
            path == "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
            or path.startswith("docs/master_plan/generated/pr169_qku_formula_exp1/")
            or path.startswith("src/qtt/stage1_prediction_markets/pr169_qku_formula_exp1/")
            or path.startswith("tests/pr169_qku_formula_exp1/")
            or path in {
                "tests/fail_closed/test_run_validation_gates.py",
                "tests/pr168_rp5c/test_rp5c_input_integrity.py",
                "tests/tools/test_validation_scope_registry.py",
                "tools/build_pr169_qku_formula_exp1.py",
                "tools/pr168_rp5c_config.py",
                "tools/run_validation_gates.py",
                "tools/validate_pr169_qku_formula_exp1.py",
                "tools/validation_inventory.py",
                "tools/validation_scope_registry.py",
            }
        )
    }
    if unexpected_currentization:
        raise AssertionError(
            "unexpected rollback path(s): " + ", ".join(sorted(unexpected_currentization))
        )

    pathspec = ["."]
    for path in sorted(CURRENTIZATION_PATHS):
        pathspec.append(f":(exclude){path}")
    comparison = _git(
        repo_root,
        "diff",
        "--exit-code",
        TRUSTED_BASELINE,
        "HEAD",
        "--",
        *pathspec,
    )
    if comparison.returncode != 0:
        raise AssertionError(
            "rollback tree differs from trusted baseline outside CI currentization paths\n"
            + comparison.stdout
            + comparison.stderr
        )

    status = _git(repo_root, "status", "--porcelain", "--untracked-files=all")
    if status.returncode != 0 or status.stdout.strip():
        raise AssertionError("rollback checkout is not clean: " + status.stdout.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    try:
        validate(args.repo_root.resolve())
    except AssertionError as exc:
        print(f"QTT_PR169_QKU_FORMULA_EXP1_ROLLBACK_FAIL: {exc}", file=sys.stderr)
        return 1
    print("QTT_PR169_QKU_FORMULA_EXP1_ROLLBACK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
