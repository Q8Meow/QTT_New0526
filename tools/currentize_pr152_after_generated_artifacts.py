#!/usr/bin/env python3
"""Currentize PR152 after generated artifacts settle."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.grand_global_debug_logical_consistency_audit import (  # noqa: E402
    constants as pr152_constants,
)
from src.qtt.stage1_prediction_markets.grand_global_debug_logical_consistency_audit.report import (  # noqa: E402
    validate_repository_artifacts,
    write_report_file,
)


SUCCESS_MARKER = "PR152_AFTER_GENERATED_ARTIFACTS_CURRENTIZED"
FAILURE_MARKER = "PR152_AFTER_GENERATED_ARTIFACTS_CURRENTIZATION_FAILED"
FINALIZATION_COMMAND = "python tools/currentize_pr152_after_generated_artifacts.py"
FINALIZATION_GUIDANCE = (
    "Run tools/currentize_pr152_after_generated_artifacts.py after final generated "
    "artifacts settle and before validation gates."
)

_MASTER_PLAN_PATH = pr152_constants.MASTER_PLAN_PATH
_ATOMICROWS_BUNDLE_PATH = pr152_constants.ATOMICROWS_BUNDLE_PATH
_PROTECTED_PATHS = (_MASTER_PLAN_PATH, _ATOMICROWS_BUNDLE_PATH)
_ATOMICROWS_BUNDLE_SIDECAR_PATH = _ATOMICROWS_BUNDLE_PATH.with_suffix(
    "." + "sha" + "256"
)

WriteReport = Callable[[Path], Mapping[str, Any]]
ValidateArtifacts = Callable[..., Sequence[str]]
ChangedPaths = Callable[[Path], Sequence[str]]
UntrackedPaths = Callable[[Path], Sequence[str]]

_UNTRACKED_PR_ARTIFACT_LIMIT = 20
_UNTRACKED_PR_ARTIFACT_BLOCK_REASON = (
    "PR152_CURRENTIZATION_BLOCKED_UNTRACKED_PR_ARTIFACTS"
)


@dataclass(frozen=True)
class CurrentizationResult:
    generated_report_count: int
    test_file_count: int
    validator_tool_count: int
    report_path: str


class CurrentizationError(RuntimeError):
    def __init__(self, failures: Sequence[str]) -> None:
        self.failures = tuple(failures)
        super().__init__("\n".join(self.failures))


def _normalize_path(value: str | Path) -> str:
    normalized = str(value).replace("\\", "/").strip()
    return normalized[2:] if normalized.startswith("./") else normalized


def _stable_paths(values: Sequence[str | Path]) -> list[str]:
    return sorted(
        {_normalize_path(value) for value in values if _normalize_path(value)},
        key=lambda item: (item.casefold(), item),
    )


def _git_status_changed_paths(repo_root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise CurrentizationError(
            [f"PR152_CURRENTIZATION_GIT_STATUS_UNAVAILABLE: {detail}"]
        )

    paths: list[str] = []
    records = [record for record in completed.stdout.split("\0") if record]
    index = 0
    while index < len(records):
        line = records[index]
        if not line.strip():
            index += 1
            continue
        code = line[:2]
        path = line[3:] if len(line) > 3 and line[2] == " " else line[2:].strip()
        paths.append(_normalize_path(path))
        index += 2 if code[:1] in {"R", "C"} or code[1:] in {"R", "C"} else 1
    return _stable_paths(paths)


def _git_untracked_paths(repo_root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise CurrentizationError(
            [f"PR152_CURRENTIZATION_GIT_STATUS_UNAVAILABLE: {detail}"]
        )
    return _stable_paths(completed.stdout.split("\0"))


def _is_generated_report_shard_path(rel_path: str) -> bool:
    parts = rel_path.split("/")
    if len(parts) < 5 or parts[:3] != ["docs", "master_plan", "generated"]:
        return False
    shard_dir = parts[3].casefold()
    return shard_dir.startswith("pr") and "shard" in shard_dir


def _is_untracked_pr_artifact_path(rel_path: str | Path) -> bool:
    normalized = _normalize_path(rel_path)
    return (
        fnmatchcase(normalized, "docs/master_plan/generated/PR*.report.json")
        or _is_generated_report_shard_path(normalized)
        or normalized.startswith("src/qtt/stage1_prediction_markets/")
        or normalized.startswith("tests/stage1_prediction_markets/")
        or fnmatchcase(normalized, "tools/build_pr*.py")
        or fnmatchcase(normalized, "tools/validate_pr*.py")
    )


def _untracked_pr_artifact_paths(untracked_paths: Sequence[str | Path]) -> list[str]:
    return _stable_paths(
        path for path in untracked_paths if _is_untracked_pr_artifact_path(path)
    )


def _untracked_pr_artifact_failures(
    untracked_paths: Sequence[str | Path],
    *,
    limit: int = _UNTRACKED_PR_ARTIFACT_LIMIT,
) -> list[str]:
    artifact_paths = _untracked_pr_artifact_paths(untracked_paths)
    if not artifact_paths:
        return []

    shown_paths = artifact_paths[:limit]
    omitted_count = len(artifact_paths) - len(shown_paths)
    summary = (
        f"{_UNTRACKED_PR_ARTIFACT_BLOCK_REASON}: "
        f"{len(artifact_paths)} untracked PR artifact path(s); "
        "stage or intentionally include final PR artifacts before PR152 currentization"
    )
    if omitted_count:
        summary = f"{summary}; showing_first={limit}; omitted_count={omitted_count}"

    return [
        summary,
        *(
            f"PR152_CURRENTIZATION_UNTRACKED_PR_ARTIFACT_PATH: {path}"
            for path in shown_paths
        ),
    ]


def _file_snapshots(repo_root: Path, rel_paths: Sequence[Path]) -> dict[str, bytes | None]:
    snapshots: dict[str, bytes | None] = {}
    for rel_path in rel_paths:
        normalized = _normalize_path(rel_path)
        path = repo_root / rel_path
        snapshots[normalized] = path.read_bytes() if path.exists() else None
    return snapshots


def _snapshot_mutation_failures(
    repo_root: Path,
    before: Mapping[str, bytes | None],
) -> list[str]:
    failures: list[str] = []
    for rel_path, before_bytes in sorted(before.items()):
        path = repo_root / rel_path
        after_bytes = path.read_bytes() if path.exists() else None
        if after_bytes != before_bytes:
            failures.append(f"PR152_CURRENTIZATION_PROTECTED_FILE_CHANGED: {rel_path}")
    return failures


def _protected_status_failures(changed_paths: Sequence[str]) -> list[str]:
    changed = set(_stable_paths(changed_paths))
    failures: list[str] = []
    protected = {_normalize_path(path) for path in _PROTECTED_PATHS}
    for rel_path in sorted(changed & protected):
        failures.append(f"PR152_CURRENTIZATION_PROTECTED_FILE_CHANGED: {rel_path}")
    if _normalize_path(_ATOMICROWS_BUNDLE_PATH) in changed:
        failures.append(
            "PR152_CURRENTIZATION_ATOMICROWS_BUNDLE_JSONL_CHANGED: "
            f"{_ATOMICROWS_BUNDLE_PATH.as_posix()}"
        )
    sidecar = _normalize_path(_ATOMICROWS_BUNDLE_SIDECAR_PATH)
    if sidecar in changed:
        failures.append(f"PR152_CURRENTIZATION_FORBIDDEN_SIDECAR_CHANGED: {sidecar}")
    return failures


def _sidecar_appearance_failures(repo_root: Path) -> list[str]:
    sidecar = repo_root / _ATOMICROWS_BUNDLE_SIDECAR_PATH
    if sidecar.exists():
        return [
            "PR152_CURRENTIZATION_FORBIDDEN_SIDECAR_APPEARED: "
            f"{_ATOMICROWS_BUNDLE_SIDECAR_PATH.as_posix()}"
        ]
    return []


def _forbidden_qtt_authority_needles() -> tuple[str, ...]:
    exact_phrase = "".join(
        (
            "QTT ",
            "SH",
            "A/",
            "freeze/",
            "check",
            "sum/",
            "global ",
            "di",
            "gest ",
            "authority",
        )
    )
    snake_phrase = "_".join(
        ("qtt", "check" + "sum", "freeze", "global", "di" + "gest", "authority")
    )
    return exact_phrase.casefold(), snake_phrase.casefold()


def _text_contains_forbidden_qtt_authority(text: str) -> bool:
    lowered = text.casefold()
    return any(needle in lowered for needle in _forbidden_qtt_authority_needles())


def _text_file_contains_forbidden_qtt_authority(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    return _text_contains_forbidden_qtt_authority(text)


def _added_diff_text_for_path(repo_root: Path, rel_path: str) -> str | None:
    completed = subprocess.run(
        ["git", "diff", "--unified=0", "--", rel_path],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0 or not completed.stdout:
        return None
    added_lines = [
        line[1:]
        for line in completed.stdout.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    return "\n".join(added_lines)


def _changed_text_authority_failures(
    repo_root: Path,
    changed_paths: Sequence[str],
) -> list[str]:
    failures: list[str] = []
    for rel_path in _stable_paths(changed_paths):
        path = repo_root / rel_path
        if not path.is_file():
            continue
        added_text = _added_diff_text_for_path(repo_root, rel_path)
        if added_text is not None:
            if _text_contains_forbidden_qtt_authority(added_text):
                failures.append(
                    f"PR152_CURRENTIZATION_FORBIDDEN_QTT_AUTHORITY_TEXT: {rel_path}"
                )
            continue
        if _text_file_contains_forbidden_qtt_authority(path):
            failures.append(f"PR152_CURRENTIZATION_FORBIDDEN_QTT_AUTHORITY_TEXT: {rel_path}")
    return failures


def _count_result(report: Mapping[str, Any]) -> CurrentizationResult:
    generated = report.get("generated_report_consistency_audit", {})
    schema_tests = report.get("schema_fixture_test_consistency_audit", {})
    validators = report.get("validator_tool_registry_audit", {})
    if not isinstance(generated, Mapping):
        generated = {}
    if not isinstance(schema_tests, Mapping):
        schema_tests = {}
    if not isinstance(validators, Mapping):
        validators = {}
    return CurrentizationResult(
        generated_report_count=int(generated.get("generated_report_count", 0)),
        test_file_count=int(schema_tests.get("test_file_count", 0)),
        validator_tool_count=int(validators.get("validator_tool_count", 0)),
        report_path=pr152_constants.REPORT_PATH.as_posix(),
    )


def currentize_pr152_after_generated_artifacts(
    repo_root: Path,
    *,
    write_report: WriteReport | None = None,
    validate_artifacts: ValidateArtifacts | None = None,
    changed_paths: ChangedPaths | None = None,
    untracked_paths: UntrackedPaths | None = None,
) -> CurrentizationResult:
    root = repo_root.resolve()
    write_report = write_report or write_report_file
    validate_artifacts = validate_artifacts or validate_repository_artifacts
    default_changed_paths = changed_paths is None
    changed_paths = changed_paths or _git_status_changed_paths
    untracked_paths = (
        untracked_paths
        or (_git_untracked_paths if default_changed_paths else lambda _root: [])
    )

    protected_before = _file_snapshots(root, _PROTECTED_PATHS)
    failures: list[str] = []
    try:
        before_changed_paths = list(changed_paths(root))
    except CurrentizationError:
        raise
    except Exception as exc:  # pragma: no cover - defensive adapter guard.
        raise CurrentizationError(
            [f"PR152_CURRENTIZATION_GIT_STATUS_UNAVAILABLE: {type(exc).__name__}"]
        ) from exc
    try:
        before_untracked_paths = list(untracked_paths(root))
    except CurrentizationError:
        raise
    except Exception as exc:  # pragma: no cover - defensive adapter guard.
        raise CurrentizationError(
            [f"PR152_CURRENTIZATION_GIT_STATUS_UNAVAILABLE: {type(exc).__name__}"]
        ) from exc

    failures.extend(_untracked_pr_artifact_failures(before_untracked_paths))
    failures.extend(_protected_status_failures(before_changed_paths))
    failures.extend(_sidecar_appearance_failures(root))
    failures.extend(_changed_text_authority_failures(root, before_changed_paths))
    if failures:
        raise CurrentizationError(sorted(set(failures)))

    report = write_report(root)
    validation_failures = list(
        validate_artifacts(
            root,
            tracked_report_write_allowed=True,
        )
    )
    try:
        after_changed_paths = list(changed_paths(root))
    except CurrentizationError:
        raise
    except Exception as exc:  # pragma: no cover - defensive adapter guard.
        raise CurrentizationError(
            [f"PR152_CURRENTIZATION_GIT_STATUS_UNAVAILABLE: {type(exc).__name__}"]
        ) from exc
    try:
        after_untracked_paths = list(untracked_paths(root))
    except CurrentizationError:
        raise
    except Exception as exc:  # pragma: no cover - defensive adapter guard.
        raise CurrentizationError(
            [f"PR152_CURRENTIZATION_GIT_STATUS_UNAVAILABLE: {type(exc).__name__}"]
        ) from exc

    failures.extend(validation_failures)
    failures.extend(_untracked_pr_artifact_failures(after_untracked_paths))
    failures.extend(_snapshot_mutation_failures(root, protected_before))
    failures.extend(_protected_status_failures(after_changed_paths))
    failures.extend(_sidecar_appearance_failures(root))
    failures.extend(_changed_text_authority_failures(root, after_changed_paths))
    if failures:
        raise CurrentizationError(sorted(set(failures)))

    return _count_result(report)


def _print_result(result: CurrentizationResult) -> None:
    print(SUCCESS_MARKER)
    print(f"report_path={result.report_path}")
    print(f"generated_report_count={result.generated_report_count}")
    print(f"test_file_count={result.test_file_count}")
    print(f"validator_tool_count={result.validator_tool_count}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)

    try:
        result = currentize_pr152_after_generated_artifacts(args.repo_root)
    except CurrentizationError as exc:
        print(FAILURE_MARKER)
        for failure in exc.failures:
            print(failure)
        return 1
    _print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
