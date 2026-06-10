#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.changed_area_validation_router import (
    build_router_result,
    router_input_from_environment,
)
from tools.repo_path_refs import normalize_repo_ref, resolve_repo_ref, to_repo_posix


PATH_KEY_MARKERS = (
    "path",
    "paths",
    "ref",
    "refs",
    "file",
    "files",
    "glob",
    "globs",
    "schema",
    "manifest",
    "report",
    "shard",
    "input",
    "output",
)


@dataclass(frozen=True)
class PathInvariantFailure:
    source_path: str
    json_pointer: str
    reason: str
    value: str

    def format(self) -> str:
        return (
            "CROSS_PLATFORM_PATH_INVARIANT_FAILURE: "
            f"{self.source_path} {self.json_pointer} {self.reason}: {self.value}"
        )


def _looks_like_path_ref(value: str, key_path: Sequence[str]) -> bool:
    key_text = "/".join(str(part).lower() for part in key_path)
    if any(marker in key_text for marker in PATH_KEY_MARKERS):
        return True
    return (
        "/" in value
        or "\\" in value
        or value.endswith((".json", ".jsonl", ".py", ".md", ".yml", ".yaml"))
    )


def _json_pointer(path: Sequence[str]) -> str:
    if not path:
        return "/"
    return "/" + "/".join(str(part).replace("~", "~0").replace("/", "~1") for part in path)


def _path_ref_failures_in_value(
    value: object,
    *,
    source_path: str,
    key_path: tuple[str, ...] = (),
) -> tuple[PathInvariantFailure, ...]:
    failures: list[PathInvariantFailure] = []
    if isinstance(value, dict):
        for key, child in value.items():
            failures.extend(
                _path_ref_failures_in_value(
                    child,
                    source_path=source_path,
                    key_path=(*key_path, str(key)),
                )
            )
    elif isinstance(value, list):
        for index, child in enumerate(value):
            failures.extend(
                _path_ref_failures_in_value(
                    child,
                    source_path=source_path,
                    key_path=(*key_path, str(index)),
                )
            )
    elif isinstance(value, str) and _looks_like_path_ref(value, key_path):
        if value == ".":
            return ()
        pointer = _json_pointer(key_path)
        if "\\" in value:
            failures.append(
                PathInvariantFailure(
                    source_path,
                    pointer,
                    "backslash in serialized path ref",
                    value,
                )
            )
        try:
            normalize_repo_ref(value)
        except ValueError as exc:
            failures.append(
                PathInvariantFailure(source_path, pointer, str(exc), value)
            )
    return tuple(failures)


def path_ref_failures_for_json_file(repo_root: str | Path, rel_path: str | Path) -> tuple[PathInvariantFailure, ...]:
    root = Path(repo_root)
    normalized = normalize_repo_ref(rel_path)
    path = resolve_repo_ref(root, normalized)
    if not path.exists():
        return (
            PathInvariantFailure(
                normalized,
                "/",
                "changed generated JSON path is missing",
                normalized,
            ),
        )
    if path.suffix == ".jsonl":
        failures: list[PathInvariantFailure] = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            failures.extend(
                _path_ref_failures_in_value(
                    json.loads(line),
                    source_path=normalized,
                    key_path=(str(line_number),),
                )
            )
        return tuple(failures)
    payload = json.loads(path.read_text(encoding="utf-8"))
    return _path_ref_failures_in_value(payload, source_path=normalized)


def pr208_generated_reports(repo_root: str | Path) -> tuple[str, ...]:
    root = Path(repo_root)
    generated = root / "docs" / "master_plan" / "generated"
    if not generated.is_dir():
        return ()
    return tuple(
        sorted(
            to_repo_posix(path, root)
            for path in generated.glob("PR208_*.report.json")
            if path.is_file()
        )
    )


def changed_generated_reports_to_scan(
    repo_root: str | Path,
    *,
    changed_files: Sequence[str] = (),
    base_ref: str | None = None,
    head_ref: str | None = None,
) -> tuple[str, ...]:
    router_input = router_input_from_environment(
        repo_root,
        changed_files=changed_files,
        base_ref=base_ref,
        head_ref=head_ref,
    )
    result = build_router_result(router_input)
    return tuple(
        sorted(
            {
                *result.touched_generated_reports,
                *pr208_generated_reports(repo_root),
            }
        )
    )


def path_invariant_failures(
    repo_root: str | Path,
    paths: Iterable[str | Path],
) -> tuple[PathInvariantFailure, ...]:
    failures: list[PathInvariantFailure] = []
    for path in sorted({normalize_repo_ref(item) for item in paths}):
        if path.endswith((".json", ".jsonl")):
            failures.extend(path_ref_failures_for_json_file(repo_root, path))
    return tuple(failures)


def invariant_report_payload() -> dict[str, object]:
    return {
        "serialized_repo_paths_must_be_posix": True,
        "backslash_serialized_paths_allowed": False,
        "absolute_serialized_paths_allowed": False,
        "parent_traversal_allowed": False,
        "pathlib_resolution_required": True,
        "linux_ci_required": True,
        "windows_dev_supported": True,
        "future_linux_cluster_supported": True,
        "touched_generated_json_scan_supported": True,
        "shared_helper_path": "tools/repo_path_refs.py",
        "test_refs": [
            "tests/tools/test_cross_platform_path_invariant.py",
            "tests/tools/test_changed_area_validation_router.py",
            "tests/tools/test_validation_inventory.py",
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--base-ref")
    parser.add_argument("--head-ref")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--report-out", type=Path)
    args = parser.parse_args(argv)

    paths = tuple(args.path) or changed_generated_reports_to_scan(
        args.repo_root,
        changed_files=args.changed_file,
        base_ref=args.base_ref,
        head_ref=args.head_ref,
    )
    failures = path_invariant_failures(args.repo_root, paths)
    if args.report_out:
        report_out = args.report_out
        if not report_out.is_absolute():
            report_out = args.repo_root / report_out
        report_out.parent.mkdir(parents=True, exist_ok=True)
        payload = invariant_report_payload()
        payload["scanned_paths"] = sorted(normalize_repo_ref(path) for path in paths)
        payload["failures"] = [failure.format() for failure in failures]
        report_out.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    for failure in failures:
        print(failure.format())
    if failures:
        return 1
    print("CROSS_PLATFORM_PATH_INVARIANT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
