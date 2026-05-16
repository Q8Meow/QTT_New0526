from __future__ import annotations

import json
import os
import pathlib
from typing import Any, Iterable

from .atomicrows_bundle_state import (
    CANONICAL_ATOMICROWS_BUNDLE,
    CANONICAL_ATOMICROWS_BUNDLE_SHA,
    AtomicRowsBundleState,
    atomicrows_bundle_state_report,
    canonical_atomicrows_bundle_paths,
    canonical_atomicrows_bundle_presence,
    expected_atomicrows_bundle_state_from_contract,
    validate_atomicrows_bundle_state,
    validate_current_atomicrows_bundle_state,
)

DETERMINISTIC_GENERATED_AT_UTC = "STATIC_DETERMINISTIC_NO_WALL_CLOCK"
STATIC_REPORT_AUTHORITY_CLASS = "STATIC_REPORT_ONLY_NOT_TRADING_AUTHORITY"

STATIC_AUTHORITY_FLAGS = {
    "creates_source_fact_acceptance": False,
    "creates_connector_semantics": False,
    "creates_runtime_resolver_snapshot": False,
    "executes_replay_or_paper": False,
    "creates_live_reachability": False,
    "creates_runtime_cash_or_usable_cash": False,
    "creates_atomicrows_bundle_or_4183_rows": False,
    "reduces_blockers": False,
    "creates_profit_evidence": False,
}

SKIP_DIR_PARTS = {
    ".git",
    ".pytest_cache",
    ".tmp",
    ".uv-cache",
    ".venv",
    "__pycache__",
}


def static_metadata(generated_by: str) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "generated_by": generated_by,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT_UTC,
        "authority_class": STATIC_REPORT_AUTHORITY_CLASS,
    }
    metadata.update(STATIC_AUTHORITY_FLAGS)
    return metadata


def canonical_path(root: pathlib.Path, rel_path: pathlib.PurePosixPath) -> pathlib.Path:
    return root.resolve() / pathlib.Path(*rel_path.parts)


def canonical_atomicrows_presence(repo_root: pathlib.Path) -> tuple[bool, bool]:
    presence = canonical_atomicrows_bundle_presence(repo_root)
    return presence.bundle_jsonl_exists, presence.bundle_sha256_exists


def canonical_atomicrows_absence_failures(
    repo_root: pathlib.Path,
    label: str,
) -> list[str]:
    return validate_atomicrows_bundle_state(
        repo_root,
        AtomicRowsBundleState.PRE_MATERIALIZATION,
        label,
    )


def canonical_atomicrows_post_pr_e_boundary_failures(
    repo_root: pathlib.Path,
    label: str,
) -> list[str]:
    return validate_atomicrows_bundle_state(
        repo_root,
        AtomicRowsBundleState.POST_MATERIALIZATION_PRE_SHA,
        label,
    )


def load_json_object(path: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"JSON file is missing: {path}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"JSON file is not valid JSON: {path}: {exc}"]
    if not isinstance(value, dict):
        return None, [f"JSON file must contain an object: {path}"]
    return value, []


def write_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def require_exact_fields(
    value: dict[str, Any],
    fields: Iterable[str],
    label: str,
) -> list[str]:
    expected = set(fields)
    failures: list[str] = []
    missing = sorted(expected - set(value))
    unexpected = sorted(set(value) - expected)
    if missing:
        failures.append(f"{label} missing required fields: {', '.join(missing)}")
    if unexpected:
        failures.append(f"{label} has unexpected fields: {', '.join(unexpected)}")
    return failures


def require_bool_map(
    value: Any,
    expected: dict[str, bool],
    label: str,
) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    failures = require_exact_fields(value, expected, label)
    for field, expected_value in sorted(expected.items()):
        if value.get(field) is not expected_value:
            failures.append(f"{label}.{field} must be {expected_value}")
    return failures


def walk(value: Any, path: str = "value"):
    if isinstance(value, dict):
        for key, item in value.items():
            current = f"{path}.{key}"
            yield current, key, item
            yield from walk(item, current)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            current = f"{path}[{index}]"
            yield current, f"[{index}]", item
            yield from walk(item, current)


def true_claim_failures(
    value: Any,
    *,
    forbidden_true_fields: Iterable[str],
    label: str,
) -> list[str]:
    forbidden = set(forbidden_true_fields)
    failures: list[str] = []
    for path, key, item in walk(value, label):
        if key in forbidden and item is True:
            failures.append(f"{path} must remain false")
    return failures


def hidden_zip_paths(repo_root: pathlib.Path) -> list[pathlib.PurePosixPath]:
    root = repo_root.resolve()
    paths: list[pathlib.PurePosixPath] = []
    if not root.exists():
        return paths
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIR_PARTS]
        current_dir = pathlib.Path(dirpath)
        for filename in filenames:
            path = current_dir / filename
            if path.suffix.lower() == ".zip":
                paths.append(pathlib.PurePosixPath(path.relative_to(root).as_posix()))
    return sorted(paths, key=str)
