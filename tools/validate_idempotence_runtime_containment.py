#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from fnmatch import fnmatchcase
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SUCCESS_MARKER = "QTT_IDEMPOTENCE_RUNTIME_CONTAINMENT_OK"
FAIL_PREFIX = "QTT_IDEMPOTENCE_RUNTIME_CONTAINMENT_FAIL"
INVENTORY_PATH = Path(
    "tests/tools/fixtures/idempotence_runtime_containment_inventory.json"
)
AUTHORITY_CLASS = "CI_RUNTIME_CONTAINMENT_STATIC_GUARD_FIXTURE_NOT_TRADING_AUTHORITY"
REQUIRED_TOP_LEVEL_FIELDS = (
    "schema_version",
    "authority_class",
    "default_ci_idempotence_policy",
    "runtime_budget_policy",
    "pytest_shards",
    "workflow_jobs",
    "idempotence_tests",
    "known_heavy_families",
    "runtime_artifact_policy",
    "checkout_fixture_requirements",
    "manual_nightly_exhaustive_paths",
    "forbidden_touch_patterns",
)
CLASSIFICATION_ENUMS = frozenset(
    {
        "BOUNDED_PR_CI_IDEMPOTENCE",
        "MANUAL_NIGHTLY_EXHAUSTIVE_IDEMPOTENCE",
        "LIGHTWEIGHT_SAFE_DEFAULT_CI",
        "NEEDS_BOUNDING_NOW",
        "DEFAULT_CI_FORBIDDEN_EXHAUSTIVE_IDEMPOTENCE",
        "RUNTIME_ARTIFACT_IGNORED_IF_UNTRACKED",
        "RUNTIME_ARTIFACT_FAILS_IF_TRACKED_OR_STAGED",
        "PYTEST_SHARD_DEFAULT_CI",
        "FULL_VALIDATION_ONLY",
        "MANUAL_NIGHTLY_ONLY",
        "CHECKOUT_FIXTURE_REQUIRED",
        "CHECKOUT_FIXTURE_CLASSIFIED_ONLY",
        "FULL_CHECKOUT_REQUIRED",
        "VALIDATION_INFRA_ONLY",
    }
)
REQUIRED_PYTEST_SHARDS = tuple(f"pytest-shard-{index}" for index in range(1, 9))
REQUIRED_WORKFLOW_JOB_IDS = (
    "fast_preflight",
    "deterministic_validators",
    "pytest_shard_1",
    "pytest_shard_2",
    "pytest_shard_3",
    "pytest_shard_4",
    "pytest_shard_5",
    "pytest_shard_6",
    "pytest_shard_7",
    "pytest_shard_8",
    "post_validation_checks",
    "validation",
)
RUNTIME_POLICY_CLASSES = frozenset(
    {
        "RUNTIME_ARTIFACT_IGNORED_IF_UNTRACKED",
        "RUNTIME_ARTIFACT_FAILS_IF_TRACKED_OR_STAGED",
    }
)
BROAD_TMP_PATTERNS = frozenset({".tmp", ".tmp/", ".tmp/*", ".tmp/**"})
SOURCE_PAYLOAD_PREFIXES = (
    "src/",
    "tests/",
    "docs/master_plan/generated/",
    "docs/master_plan/source_evidence/generated/",
    "docs/roadmap/generated/",
)
DEFAULT_BUDGET_SECONDS = 180


@dataclass(frozen=True)
class Failure:
    code: str
    details: tuple[tuple[str, str], ...] = ()

    def render(self) -> str:
        if not self.details:
            return f"{FAIL_PREFIX} code={self.code}"
        suffix = " ".join(f"{key}={value}" for key, value in self.details)
        return f"{FAIL_PREFIX} code={self.code} {suffix}"


@dataclass(frozen=True)
class DiscoveredIdempotence:
    path: str
    has_verify_idempotent: bool
    builder_twice: bool
    bounded_contract: bool


def _failure(code: str, **details: object) -> Failure:
    rendered = tuple((key, str(value)) for key, value in details.items())
    return Failure(code=code, details=rendered)


def normalize_path(path: object) -> str:
    value = str(path).strip().replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return value


def _matches(path: str, pattern: str) -> bool:
    return fnmatchcase(normalize_path(path), normalize_path(pattern))


def _has_glob(pattern: str) -> bool:
    return any(char in pattern for char in "*?[")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def load_inventory(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    return completed.returncode, completed.stdout, completed.stderr


def _git_lines(repo_root: Path, args: Sequence[str]) -> tuple[str, ...]:
    rc, stdout, _stderr = _git(repo_root, args)
    if rc != 0:
        return ()
    return tuple(normalize_path(line) for line in stdout.splitlines() if line.strip())


def _tracked_paths(repo_root: Path) -> tuple[str, ...]:
    return _git_lines(repo_root, ("ls-files",))


def _staged_paths(repo_root: Path) -> tuple[str, ...]:
    return _git_lines(repo_root, ("diff", "--cached", "--name-only"))


def _status_paths(repo_root: Path) -> tuple[str, ...]:
    rc, stdout, _stderr = _git(
        repo_root,
        ("status", "--porcelain", "--untracked-files=all"),
    )
    if rc != 0:
        return ()
    paths: list[str] = []
    for line in stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.rsplit(" -> ", 1)[1]
        paths.append(normalize_path(path))
    return tuple(sorted(dict.fromkeys(paths)))


def _changed_paths(repo_root: Path) -> tuple[str, ...]:
    candidates: list[str] = []
    for args in (
        ("diff", "--name-only", "main..HEAD"),
        ("diff", "--name-only", "origin/main...HEAD"),
        ("diff", "--name-only", "--cached"),
        ("diff", "--name-only"),
    ):
        candidates.extend(_git_lines(repo_root, args))
    candidates.extend(_status_paths(repo_root))
    return tuple(sorted(dict.fromkeys(path for path in candidates if path)))


def _current_branch(repo_root: Path) -> str:
    rc, stdout, _stderr = _git(repo_root, ("branch", "--show-current"))
    if rc == 0:
        return stdout.strip()
    return ""


def _workflow_text(repo_root: Path) -> str:
    return _read_text(repo_root / ".github" / "workflows" / "qtt_validation.yml")


def _job_blocks(workflow_text: str) -> dict[str, str]:
    if "\njobs:" in workflow_text:
        workflow_text = workflow_text.split("\njobs:", 1)[1]
    blocks: dict[str, list[str]] = {}
    current: str | None = None
    for line in workflow_text.splitlines():
        match = re.match(r"^  ([A-Za-z0-9_]+):\s*$", line)
        if match:
            current = match.group(1)
            blocks[current] = [line]
            continue
        if current is not None:
            if line.startswith("  ") or not line.strip():
                blocks[current].append(line)
            else:
                current = None
    return {job_id: "\n".join(lines) for job_id, lines in blocks.items()}


def parse_workflow_jobs(workflow_text: str) -> dict[str, str]:
    jobs: dict[str, str] = {}
    for job_id, block in _job_blocks(workflow_text).items():
        name_match = re.search(r"^\s+name:\s*(.+?)\s*$", block, flags=re.MULTILINE)
        jobs[job_id] = name_match.group(1) if name_match else job_id
    return jobs


def _parse_needs(block: str) -> tuple[str, ...]:
    needs_match = re.search(r"^\s+needs:\s*\n(?P<body>(?:\s{6}- .+\n?)+)", block, re.MULTILINE)
    if not needs_match:
        inline = re.search(r"^\s+needs:\s*\[(?P<body>[^\]]*)\]", block, re.MULTILINE)
        if not inline:
            return ()
        return tuple(
            normalize_path(part).replace("-", "_")
            for part in inline.group("body").split(",")
            if part.strip()
        )
    values = []
    for line in needs_match.group("body").splitlines():
        item = line.strip()
        if item.startswith("- "):
            values.append(item[2:].strip())
    return tuple(values)


def _builder_twice(text: str) -> bool:
    calls = re.findall(r"\bbuild_payloads(?:_with_shards)?\s*\(", text)
    first_second_contract = "first" in text and "second" in text
    return (len(calls) >= 2 and first_second_contract) or (
        "rebuild_once" in text and "rebuild_twice" in text
    )


def _active_verify_idempotent(text: str) -> bool:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "--verify-idempotent" in stripped:
            return True
    return False


def _bounded_contract(text: str) -> bool:
    return (
        "bounded_snapshot" in text
        and (
            "assert_bounded_idempotence_equal" in text
            or "bounded_idempotence_differences" in text
        )
    )


def discover_idempotence_tests(repo_root: Path) -> tuple[DiscoveredIdempotence, ...]:
    discovered: list[DiscoveredIdempotence] = []
    tests_root = repo_root / "tests"
    if not tests_root.exists():
        return ()
    for path in sorted(tests_root.rglob("test*.py")):
        rel = normalize_path(path.relative_to(repo_root))
        if rel == "tests/tools/test_validate_idempotence_runtime_containment.py":
            continue
        text = _read_text(path)
        has_verify = _active_verify_idempotent(text)
        builder_twice = _builder_twice(text)
        if "idempotence" not in path.name and not has_verify and not builder_twice:
            continue
        discovered.append(
            DiscoveredIdempotence(
                path=rel,
                has_verify_idempotent=has_verify,
                builder_twice=builder_twice,
                bounded_contract=_bounded_contract(text),
            )
        )
    return tuple(discovered)


def discover_manual_exhaustive_paths(repo_root: Path) -> tuple[str, ...]:
    paths: list[str] = []
    for path in sorted((repo_root / "tools").glob("build_*.py")):
        text = _read_text(path)
        if "--verify-idempotent" in text:
            paths.append(normalize_path(path.relative_to(repo_root)))
    return tuple(paths)


def _pytest_membership(repo_root: Path) -> dict[str, str]:
    try:
        from tools import run_validation_gates as runner

        return runner.pytest_shard_membership(repo_root)
    except Exception:
        return {}


def _runner_shards() -> tuple[str, ...]:
    try:
        from tools import run_validation_gates as runner

        return tuple(runner.PYTEST_SHARD_PHASES)
    except Exception:
        return REQUIRED_PYTEST_SHARDS


def _active_inventory_entries(entries: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [entry for entry in entries if not entry.get("removed_with_reason")]


def _validate_top_level(inventory: Mapping[str, Any]) -> list[Failure]:
    failures: list[Failure] = []
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in inventory:
            failures.append(_failure("MISSING_INVENTORY_FIELD", field=field))
    if inventory.get("schema_version") != 1:
        failures.append(_failure("BAD_SCHEMA_VERSION", value=inventory.get("schema_version")))
    if inventory.get("authority_class") != AUTHORITY_CLASS:
        failures.append(
            _failure("BAD_AUTHORITY_CLASS", value=inventory.get("authority_class"))
        )
    return failures


def _validate_classifications(inventory: Mapping[str, Any]) -> list[Failure]:
    failures: list[Failure] = []
    sections = (
        "pytest_shards",
        "workflow_jobs",
        "idempotence_tests",
        "known_heavy_families",
        "runtime_artifact_policy",
        "checkout_fixture_requirements",
        "manual_nightly_exhaustive_paths",
    )
    for section in sections:
        for entry in inventory.get(section, ()):
            for key, value in entry.items():
                if key.endswith("classification") or key == "classification":
                    if value not in CLASSIFICATION_ENUMS:
                        failures.append(
                            _failure(
                                "UNKNOWN_CLASSIFICATION",
                                section=section,
                                value=value,
                            )
                        )
    return failures


def _path_or_glob_exists(repo_root: Path, pattern: str) -> bool:
    normalized = normalize_path(pattern)
    if _has_glob(normalized):
        return any(repo_root.glob(normalized))
    return (repo_root / normalized).exists()


def _inventory_path_patterns(inventory: Mapping[str, Any]) -> Iterable[tuple[str, Mapping[str, Any]]]:
    for section in (
        "idempotence_tests",
        "known_heavy_families",
        "runtime_artifact_policy",
        "checkout_fixture_requirements",
        "manual_nightly_exhaustive_paths",
        "forbidden_touch_patterns",
    ):
        for entry in inventory.get(section, ()):
            for field in ("path", "path_pattern", "path_glob", "generated_shard_glob", "pattern"):
                value = entry.get(field)
                if isinstance(value, str):
                    yield value, entry


def _validate_inventory_paths(repo_root: Path, inventory: Mapping[str, Any]) -> list[Failure]:
    failures: list[Failure] = []
    for pattern, entry in _inventory_path_patterns(inventory):
        if entry.get("removed_with_reason"):
            continue
        if "path_pattern" in entry and entry.get("classification") in RUNTIME_POLICY_CLASSES:
            continue
        if pattern in BROAD_TMP_PATTERNS:
            continue
        if _has_glob(pattern):
            # Forbidden touch globs are policy predicates; other globs must match.
            if "code" in entry:
                continue
            if not _path_or_glob_exists(repo_root, pattern):
                failures.append(_failure("STALE_INVENTORY_ENTRY", path=pattern))
            continue
        if not _path_or_glob_exists(repo_root, pattern):
            failures.append(_failure("STALE_INVENTORY_ENTRY", path=pattern))
    return failures


def _validate_idempotence(
    repo_root: Path,
    inventory: Mapping[str, Any],
    discovered: Sequence[DiscoveredIdempotence],
    pytest_membership: Mapping[str, str],
) -> list[Failure]:
    failures: list[Failure] = []
    entries = {
        normalize_path(entry["path"]): entry
        for entry in _active_inventory_entries(inventory.get("idempotence_tests", ()))
        if "path" in entry
    }
    discovered_by_path = {item.path: item for item in discovered}
    for item in discovered:
        entry = entries.get(item.path)
        if entry is None:
            failures.append(_failure("UNCLASSIFIED_IDEMPOTENCE_TEST", path=item.path))
            continue
        default_ci = item.path in pytest_membership or bool(entry.get("pytest_shard"))
        classification = str(entry.get("default_ci_classification", ""))
        runtime_budget = int(entry.get("runtime_budget_seconds", 0) or 0)
        lightweight_budgeted = (
            classification == "LIGHTWEIGHT_SAFE_DEFAULT_CI"
            and runtime_budget > 0
            and runtime_budget <= DEFAULT_BUDGET_SECONDS
            and item.bounded_contract
        )
        if item.has_verify_idempotent and default_ci and not lightweight_budgeted:
            failures.append(
                _failure(
                    "DEFAULT_CI_EXHAUSTIVE_VERIFY_IDEMPOTENT",
                    path=item.path,
                )
            )
        if item.builder_twice and default_ci:
            if classification != "BOUNDED_PR_CI_IDEMPOTENCE" or not item.bounded_contract:
                failures.append(
                    _failure("BUILDER_TWICE_UNBOUNDED_DEFAULT_CI", path=item.path)
                )
        if classification == "BOUNDED_PR_CI_IDEMPOTENCE" and not item.bounded_contract:
            failures.append(_failure("BOUNDED_IDEMPOTENCE_CONTRACT_MISSING", path=item.path))
    for path, entry in entries.items():
        if path not in discovered_by_path:
            if not (repo_root / path).exists():
                failures.append(_failure("STALE_INVENTORY_ENTRY", path=path))
            else:
                failures.append(_failure("INVENTORY_IDEMPOTENCE_NOT_DISCOVERED", path=path))
        if entry.get("manual_exhaustive_path") and not (
            repo_root / normalize_path(entry["manual_exhaustive_path"])
        ).exists():
            failures.append(
                _failure("MISSING_MANUAL_EXHAUSTIVE_PATH", path=entry["manual_exhaustive_path"])
            )
    listed_manual = {
        normalize_path(entry["path"])
        for entry in _active_inventory_entries(
            inventory.get("manual_nightly_exhaustive_paths", ())
        )
        if "path" in entry
    }
    discovered_manual = set(discover_manual_exhaustive_paths(repo_root))
    for path in sorted(discovered_manual - listed_manual):
        failures.append(_failure("UNDOCUMENTED_EXHAUSTIVE_IDEMPOTENCE_PATH", path=path))
    for path in sorted(listed_manual - discovered_manual):
        if not (repo_root / path).exists():
            failures.append(_failure("MISSING_MANUAL_EXHAUSTIVE_PATH", path=path))
        else:
            failures.append(_failure("STALE_MANUAL_EXHAUSTIVE_PATH", path=path))
    return failures


def _validate_heavy_families(inventory: Mapping[str, Any]) -> list[Failure]:
    failures: list[Failure] = []
    for entry in _active_inventory_entries(inventory.get("known_heavy_families", ())):
        classification = entry.get("classification")
        if classification not in {
            "BOUNDED_PR_CI_IDEMPOTENCE",
            "MANUAL_NIGHTLY_EXHAUSTIVE_IDEMPOTENCE",
        }:
            failures.append(
                _failure(
                    "KNOWN_HEAVY_FAMILY_UNBOUNDED",
                    family=entry.get("family", ""),
                )
            )
    return failures


def _validate_pytest_shards(
    inventory: Mapping[str, Any],
    runner_shards: Sequence[str],
) -> list[Failure]:
    failures: list[Failure] = []
    entries = list(_active_inventory_entries(inventory.get("pytest_shards", ())))
    phases = [str(entry.get("phase", "")) for entry in entries]
    for shard in REQUIRED_PYTEST_SHARDS:
        if shard not in phases:
            failures.append(_failure("MISSING_PYTEST_SHARD", shard=shard))
    for shard in runner_shards:
        if shard not in phases:
            failures.append(_failure("MISSING_PYTEST_SHARD", shard=shard))
    duplicates = sorted({phase for phase in phases if phases.count(phase) > 1})
    for shard in duplicates:
        failures.append(_failure("DUPLICATE_PYTEST_SHARD", shard=shard))
    for phase in phases:
        if re.fullmatch(r"pytest-shard-\d+", phase) and phase not in REQUIRED_PYTEST_SHARDS:
            failures.append(_failure("UNKNOWN_DEFAULT_CI_SHARD", shard=phase))
    for entry in entries:
        if entry.get("classification") != "PYTEST_SHARD_DEFAULT_CI":
            failures.append(_failure("BAD_PYTEST_SHARD_CLASSIFICATION", shard=entry.get("phase", "")))
    return failures


def _validate_workflow(
    inventory: Mapping[str, Any],
    workflow_text: str,
) -> list[Failure]:
    failures: list[Failure] = []
    discovered_jobs = parse_workflow_jobs(workflow_text)
    inventory_jobs = {
        str(entry.get("job_id")): entry
        for entry in _active_inventory_entries(inventory.get("workflow_jobs", ()))
    }
    for job_id in REQUIRED_WORKFLOW_JOB_IDS:
        if job_id not in inventory_jobs:
            failures.append(_failure("UNCLASSIFIED_WORKFLOW_JOB", job=job_id))
    for job_id in discovered_jobs:
        if job_id not in inventory_jobs:
            failures.append(_failure("UNCLASSIFIED_WORKFLOW_JOB", job=job_id))
    blocks = _job_blocks(workflow_text)
    validation_block = blocks.get("validation", "")
    post_block = blocks.get("post_validation_checks", "")
    validation_needs = set(_parse_needs(validation_block))
    post_needs = set(_parse_needs(post_block))
    shard_jobs = {f"pytest_shard_{index}" for index in range(1, 9)}
    for shard_job in sorted(shard_jobs):
        if shard_job not in validation_needs:
            failures.append(_failure("SHARD_NOT_AGGREGATED", shard=shard_job))
        if shard_job not in post_needs:
            failures.append(_failure("SHARD_NOT_AGGREGATED", shard=shard_job))
    for job_id in (
        "fast_preflight",
        "deterministic_validators",
        "post_validation_checks",
    ):
        if job_id not in validation_needs:
            failures.append(_failure("WORKFLOW_JOB_NOT_AGGREGATED", job=job_id))
    if "if: ${{ always() }}" not in validation_block:
        failures.append(_failure("WORKFLOW_AGGREGATION_NOT_FAIL_CLOSED", job="validation"))
    if "toJSON(needs)" not in validation_block:
        failures.append(_failure("WORKFLOW_AGGREGATION_NOT_FAIL_CLOSED", job="validation"))
    if 'result != "success"' not in validation_block:
        failures.append(_failure("WORKFLOW_AGGREGATION_NOT_FAIL_CLOSED", job="validation"))
    if "cancelled()" in validation_block and 'result != "success"' not in validation_block:
        failures.append(_failure("WORKFLOW_AGGREGATION_NOT_FAIL_CLOSED", job="validation"))
    if "sparse-checkout" in workflow_text:
        failures.append(
            _failure("SPARSE_CHECKOUT_EXPERIMENT_BLOCKED", path=".github/workflows/qtt_validation.yml")
        )
    return failures


def _runtime_patterns(inventory: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    patterns: list[tuple[str, str]] = []
    for entry in _active_inventory_entries(inventory.get("runtime_artifact_policy", ())):
        pattern = normalize_path(entry.get("path_pattern", ""))
        classification = str(entry.get("classification", ""))
        patterns.append((pattern, classification))
    return tuple(patterns)


def is_runtime_artifact_path(path: str, inventory: Mapping[str, Any]) -> bool:
    normalized = normalize_path(path)
    return any(_matches(normalized, pattern) for pattern, _ in _runtime_patterns(inventory))


def _validate_runtime_artifacts(
    inventory: Mapping[str, Any],
    tracked_paths: Sequence[str],
    staged_paths: Sequence[str],
) -> list[Failure]:
    failures: list[Failure] = []
    patterns = _runtime_patterns(inventory)
    for pattern, classification in patterns:
        if classification not in RUNTIME_POLICY_CLASSES:
            failures.append(_failure("UNKNOWN_RUNTIME_ARTIFACT_POLICY", path=pattern))
        if pattern in BROAD_TMP_PATTERNS:
            failures.append(_failure("BROAD_TMP_RUNTIME_ARTIFACT_ALLOWLIST", path=pattern))
        if pattern.startswith(SOURCE_PAYLOAD_PREFIXES):
            failures.append(_failure("RUNTIME_ARTIFACT_OUT_OF_SCOPE", path=pattern))
    tracked_or_staged = {
        normalize_path(path): "tracked"
        for path in tracked_paths
    }
    tracked_or_staged.update({normalize_path(path): "staged" for path in staged_paths})
    for path, source in sorted(tracked_or_staged.items()):
        if any(_matches(path, pattern) for pattern, _ in patterns):
            failures.append(_failure("RUNTIME_ARTIFACT_TRACKED", path=path, source=source))
    return failures


def _validate_changed_files(
    inventory: Mapping[str, Any],
    changed_paths: Sequence[str],
    *,
    workflow_text: str,
    current_branch: str = "",
    auto_discovered_changed_paths: bool = False,
) -> list[Failure]:
    failures: list[Failure] = []
    forbidden = tuple(_active_inventory_entries(inventory.get("forbidden_touch_patterns", ())))
    for path in sorted(dict.fromkeys(normalize_path(path) for path in changed_paths)):
        if _allowed_explicit_roadmap_feature_touch(
            current_branch,
            path,
            auto_discovered_changed_paths=auto_discovered_changed_paths,
        ):
            continue
        for entry in forbidden:
            pattern = str(entry.get("pattern", ""))
            if _matches(path, pattern):
                failures.append(_failure(str(entry.get("code")), path=path))
    if "sparse-checkout" in workflow_text:
        failures.append(
            _failure("SPARSE_CHECKOUT_EXPERIMENT_BLOCKED", path=".github/workflows/qtt_validation.yml")
        )
    return failures


def _allowed_explicit_roadmap_feature_touch(
    branch: str,
    path: str,
    *,
    auto_discovered_changed_paths: bool,
) -> bool:
    if not auto_discovered_changed_paths:
        return False
    try:
        from tools.ci_branch_context import (
            PR166_Q_BRANCH,
            is_explicit_downstream_repair_changed_path,
        )
    except Exception:
        return False
    if branch != PR166_Q_BRANCH:
        return False
    return is_explicit_downstream_repair_changed_path(branch, path)


def _validate_checkout(inventory: Mapping[str, Any]) -> list[Failure]:
    failures: list[Failure] = []
    for entry in _active_inventory_entries(inventory.get("checkout_fixture_requirements", ())):
        classification = entry.get("classification")
        if classification not in {
            "CHECKOUT_FIXTURE_CLASSIFIED_ONLY",
            "CHECKOUT_FIXTURE_REQUIRED",
            "FULL_CHECKOUT_REQUIRED",
        }:
            failures.append(_failure("UNKNOWN_CHECKOUT_FIXTURE_CLASSIFICATION", path=entry.get("path_glob", "")))
        if classification == "FULL_CHECKOUT_REQUIRED" and entry.get("main_checkout_green") is True:
            failures.append(
                _failure(
                    "SPARSE_CHECKOUT_EXPERIMENT_BLOCKED",
                    path=entry.get("path_glob", ""),
                )
            )
    return failures


def validate(
    repo_root: Path,
    *,
    inventory: Mapping[str, Any] | None = None,
    inventory_path: Path | None = None,
    workflow_text: str | None = None,
    changed_paths: Sequence[str] | None = None,
    tracked_paths: Sequence[str] | None = None,
    staged_paths: Sequence[str] | None = None,
    discovered_idempotence: Sequence[DiscoveredIdempotence] | None = None,
    pytest_membership: Mapping[str, str] | None = None,
    runner_shards: Sequence[str] | None = None,
) -> tuple[Failure, ...]:
    root = repo_root.resolve()
    payload = dict(inventory) if inventory is not None else load_inventory(root / (inventory_path or INVENTORY_PATH))
    workflow = _workflow_text(root) if workflow_text is None else workflow_text
    auto_discovered_changed_paths = changed_paths is None
    branch = _current_branch(root)
    discovered = (
        discover_idempotence_tests(root)
        if discovered_idempotence is None
        else tuple(discovered_idempotence)
    )
    membership = _pytest_membership(root) if pytest_membership is None else pytest_membership
    failures: list[Failure] = []
    failures.extend(_validate_top_level(payload))
    failures.extend(_validate_classifications(payload))
    failures.extend(_validate_inventory_paths(root, payload))
    failures.extend(_validate_idempotence(root, payload, discovered, membership))
    failures.extend(_validate_heavy_families(payload))
    failures.extend(_validate_pytest_shards(payload, runner_shards or _runner_shards()))
    failures.extend(_validate_workflow(payload, workflow))
    failures.extend(
        _validate_runtime_artifacts(
            payload,
            _tracked_paths(root) if tracked_paths is None else tracked_paths,
            _staged_paths(root) if staged_paths is None else staged_paths,
        )
    )
    failures.extend(
        _validate_changed_files(
            payload,
            _changed_paths(root) if changed_paths is None else changed_paths,
            workflow_text=workflow,
            current_branch=branch,
            auto_discovered_changed_paths=auto_discovered_changed_paths,
        )
    )
    failures.extend(_validate_checkout(payload))
    return tuple(failures)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--inventory", type=Path, default=INVENTORY_PATH)
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    inventory_path = args.inventory
    if not inventory_path.is_absolute():
        inventory_path = repo_root / inventory_path
    failures = validate(repo_root, inventory_path=inventory_path)
    if failures:
        for failure in failures:
            print(failure.render())
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
