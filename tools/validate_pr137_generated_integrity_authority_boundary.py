#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.stage1_prediction_markets.launch_readiness import (  # noqa: E402
    pr137_launch_readiness_dependency_policy as policy,
)


SUCCESS_MARKER = policy.GENERATED_INTEGRITY_VALIDATION_MARKER

FORBIDDEN_GENERATED_INTEGRITY_AUTHORITY_TERMS = (
    "AtomicRows.bundle.sha256",
    "atomicrows_bundle_sha_path",
    "ATOMICROWS_BUNDLE_SHA_PATH",
    "coverage_report_digest_sha256",
    "file_digests_or_sizes",
    "sha256_file",
    "hashlib",
    "sha256",
)

ALLOWED_ASSERTION_FILES = {
    "tools/validate_pr137_generated_integrity_authority_boundary.py",
    "tests/roadmap/test_pr137_launch_readiness_dependency_controller.py",
}

LEGACY_ATOMICROWS_INTEGRITY_ARTIFACT_PATH = (
    "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256"
)


def _json_key_failures(value: Any, rel_path: str, path: str = "$") -> list[str]:
    failures: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            current = f"{path}.{key}"
            if key == "sha256":
                failures.append(f"{rel_path}:{current}")
            failures.extend(_json_key_failures(item, rel_path, current))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            failures.extend(_json_key_failures(item, rel_path, f"{path}[{index}]"))
    return failures


def _scan_paths(repo_root: Path) -> list[str]:
    paths = [
        *policy.report_paths(),
        *policy.receipt_paths(),
        *policy.schema_paths(),
        policy.ROADMAP_DOC_PATH,
        "src/qtt/stage1_prediction_markets/launch_readiness/pr137_launch_readiness_dependency_controller.py",
        "src/qtt/stage1_prediction_markets/launch_readiness/pr137_launch_readiness_dependency_policy.py",
        "tools/validate_pr137_launch_readiness_dependency_controller.py",
        "tools/validate_pr137_generated_integrity_authority_boundary.py",
        "tests/roadmap/test_pr137_launch_readiness_dependency_controller.py",
    ]
    return sorted(dict.fromkeys(paths))


def validate_boundary(repo_root: Path = _REPO_ROOT) -> list[str]:
    repo_root = repo_root.resolve()
    failures: list[str] = []
    for rel_path in _scan_paths(repo_root):
        path = repo_root / rel_path
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        hits = [
            term
            for term in FORBIDDEN_GENERATED_INTEGRITY_AUTHORITY_TERMS
            if term in text
        ]
        if hits and rel_path not in ALLOWED_ASSERTION_FILES:
            failures.append(f"forbidden generated-integrity authority text in {rel_path}")
        if path.suffix == ".json":
            try:
                payload = json.loads(text)
            except json.JSONDecodeError as exc:
                failures.append(f"invalid JSON while scanning {rel_path}: {exc}")
                continue
            failures.extend(_json_key_failures(payload, rel_path))
    return failures


def protected_integrity_diff_failures(repo_root: Path = _REPO_ROOT) -> list[str]:
    repo_root = repo_root.resolve()
    failures: list[str] = []
    for rel_path in (*policy.PROTECTED_FILE_PATHS, LEGACY_ATOMICROWS_INTEGRITY_ARTIFACT_PATH):
        completed = subprocess.run(
            ["git", "diff", "--", rel_path],
            cwd=repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            failures.append(f"protected diff check failed for {rel_path}")
        elif completed.stdout.strip():
            failures.append(f"protected artifact has diff: {rel_path}")
    return failures


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    args = parser.parse_args(argv)
    failures = validate_boundary(args.repo_root)
    failures.extend(protected_integrity_diff_failures(args.repo_root))
    if failures:
        for failure in failures:
            print(failure)
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
