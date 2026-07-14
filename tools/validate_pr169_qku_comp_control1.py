#!/usr/bin/env python3
"""Independent validator for PR169-QKU-COMP-CONTROL1.

The validator deliberately does not read ``acceptance.report.json``.  It
reconstructs conclusions from the logical registry, the RP5C source cohort,
the public facade, and private *mechanism* helpers exposed by ``control.py``.
Those helpers return records, snapshots, indexes, and deltas; their PASS/FAIL
labels, if any, are ignored.

Only a single JSON document is written, to stdout.  Temporary registries used
for storage, scale, and concurrency probes are created outside the repository.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import dataclasses
import importlib
import inspect
import io
import json
import math
import re
import subprocess
import sys
import tempfile
import threading
import time
from collections import Counter, defaultdict, deque
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence

# Validation must not create repository-local bytecode artifacts even when a
# caller forgets the repository's conventional ``python -B`` flag.
sys.dont_write_bytecode = True

DEFAULT_ARTIFACT_DIR = Path("docs/master_plan/generated/pr169_qku_comp_control1")
RP5C_DEDUPE = Path("docs/master_plan/generated/rp5c/identity_deduplication_ledger.jsonl")
RP5C_LINEAGE = Path("docs/master_plan/generated/rp5c/qku_formula_identity_lineage.jsonl")
RP5C_CANONICAL_LIBRARY = Path(
    "docs/master_plan/generated/rp5c/immutable_qku_formula_library.jsonl"
)
RP5C_LIBRARIES = (
    Path("docs/master_plan/generated/rp5c/immutable_qku_library.jsonl"),
    Path("docs/master_plan/generated/rp5c/immutable_formula_library.jsonl"),
    Path("docs/master_plan/generated/rp5c/immutable_qku_formula_library.jsonl"),
)
RP5C_GROUP_CUSTODY_KEY_VERSION = "RP5C_SOURCE_GROUP_CUSTODY_KEY_V1"
RP5C_GROUP_KEY_FIELDS = (
    "identity_type",
    "qku_id",
    "formula_id",
    "formula_variant_id",
    "formula_expression_ref",
    "plugin_ref",
)
EXPECTED_RP5C_CANONICAL = 10_189
EXPECTED_OWNER_REQUIREMENTS = 213
EXPECTED_IMPLEMENTATIONS = {"FORMULA": 61, "ALGORITHM": 30, "QUANTUM_CALLABLE_FAMILY": 9}
EXPECTED_AGENTS = {
    "research_agent",
    "parameter_selector_agent",
    "risk_manager_agent",
    "quantum_optimizer_agent",
    "commander_agent",
    "governance_agent",
    "dashboard_agent",
    "connector_venue_readiness_future_consumer",
}

TOP_LEVEL_REQUIRED = {
    "canonical_component_id",
    "semantic_version",
    "record_state",
    "origin_cohorts",
    "definition",
    "uses",
    "bindings",
    "provenance",
    "relations",
    "governance",
}
DEFINITION_REQUIRED = {
    "display_name",
    "description",
    "component_kind",
    "family_template_ref_or_null",
    "complete_mathematical_or_procedural_definition",
    "objective_sense_or_null",
    "assumptions",
    "hard_constraints",
    "soft_preferences",
    "domain_and_boundary_behavior",
    "state_and_time_semantics",
    "input_schema",
    "output_schema",
    "units_and_bases",
    "output_accounting_class",
    "missing_stale_nonfinite_behavior",
    "precision_and_rounding",
    "parameter_schema_and_default_provenance",
    "requirements",
    "latency_class",
    "risk_materiality",
    "failure_domain_tags",
    "classical_fallback",
    "quantum",
    "implementation_versions",
    "oracle_and_test_refs",
    "equivalence_proof_refs",
}
USES_REQUIRED = {
    "decision_roles",
    "decision_outputs",
    "market_family_tags",
    "qku_role_bindings",
    "consumer_class_tags",
}
BINDING_REQUIRED = {
    "binding_id",
    "market",
    "venue",
    "context_selector",
    "qku_binding_selector_or_null",
    "supported_modes",
    "mode_state",
    "as_of_policy",
    "selected_implementation_version",
    "binding_version",
    "selected_parameter_policy",
    "input_source_bindings",
    "venue_semantic_version",
    "portfolio_state_requirement",
    "cash_state_requirement",
    "freshness_and_TTL",
    "point_in_time_policy",
    "requirement_context_policy",
    "selected_requirement_alternatives",
    "readiness",
    "derived_state",
    "exact_resolution_action_or_null",
    "evidence_summary",
    "agent_access_policy",
    "fallback_policy",
    "runtime_snapshot_ref_or_null",
    "activation_state",
    "rollback_target_or_null",
    "upstream_value_lineage",
    "downstream_consumer_classes",
    "producer_owner",
    "validator_refs",
    "terminal_disposition_or_null",
}
READINESS_REQUIRED = {
    "specification",
    "implementation",
    "inputs",
    "requirements",
    "oracle",
    "context",
    "evidence",
    "authorization",
}
PROVENANCE_REQUIRED = {
    "source_artifact_ref",
    "source_row_ref",
    "source_local_identity_or_name",
    "source_fields_consumed",
    "source_relation",
    "canonical_target_ref",
    "proof_refs",
}
GOVERNANCE_REQUIRED = {
    "producer_owner",
    "validator_refs",
    "reviewer_or_challenger_owner",
    "change_authority",
}
REQUIREMENT_REQUIRED = {
    "required_component_id_or_source_selector",
    "required_semantic_version_constraint",
    "requirement_role",
    "required_or_optional",
    "producer_output_name",
    "consumer_input_name",
    "unit_or_basis_conversion",
    "timing_and_freshness_constraint",
    "activation_condition",
    "fallback_component_id_or_null",
    "failure_behavior",
}
RECORD_STATES = {
    "PROVISIONAL",
    "UNDER_REVIEW",
    "CANONICAL_ACCEPTED",
    "SUPERSEDED",
    "DORMANT_PRESERVED",
    "REJECTED_INVALID",
    "INAPPLICABLE_WITH_PROOF",
}
ACCEPTED_STATES = {"CANONICAL_ACCEPTED", "SUPERSEDED", "DORMANT_PRESERVED"}
RUNTIME_ACTIVE_RECORD_STATES = {"CANONICAL_ACCEPTED", "PROVISIONAL", "UNDER_REVIEW"}
DERIVED_STATES = {
    "SPECIFIED",
    "VERIFIED",
    "CONTEXT_READY",
    "STACK_READY",
    "EVIDENCED",
    "AUTHORIZED",
    "RETIRED",
    "INVALID",
}
SPEC_STATES = {"PASS", "REQUIRED", "INVALID"}
EVIDENCE_STATES = {"NONE", "FIXTURE", "REPLAY", "PAPER", "SHADOW", "DRYRUN", "CANARY", "LIVE"}
AUTH_STATES = {"NOT_ELIGIBLE", "ELIGIBLE", "ALLOW_PENDING", "AUTHORIZED"}
RELATION_TYPES = {
    "ALIAS_OF",
    "FAMILY_BINDING_OF",
    "SUCCESSOR_OF",
    "ENCODES_OR_MAPS",
    "DISTINCT_FROM",
    "SUPERSEDES",
}
ALGORITHM_KINDS = {
    "STATISTICAL_ESTIMATOR",
    "STATISTICAL_TEST",
    "OPTIMIZATION_PROGRAM",
    "ALLOCATION_OR_SIZING_POLICY",
    "NUMERICAL_ALGORITHM",
    "SOLVER_PROCEDURE",
    "EXECUTION_POLICY",
    "EXIT_POLICY",
    "QKU_SELECTION_POLICY",
    "COMPUTATION_STACK",
}
PLACEHOLDERS = {"TBD", "SCOPED_GAP", "FUTURE CONSUMER", "METADATA ONLY", "SOLVER COMPATIBLE", "ROUTE LATER", "PLACEHOLDER"}
BULK_KEY_TOKENS = {
    "order_book",
    "raw_fills",
    "fill_ledger",
    "replay_history",
    "replay_rows",
    "trial_rows",
    "bootstrap_samples",
    "qpu_samples",
    "time_series",
    "timeseries",
    "source_document",
    "tca_ledger",
    "campaign_ledger",
}
FORBIDDEN_CALL_TOKENS = {
    "eval",
    "exec",
    "__import__",
    "importlib",
    "pickle",
    "marshal",
    "subprocess",
    "os.system",
    "powershell",
    "cmd.exe",
}
FORBIDDEN_AGENT_OPERATIONS = {
    "compile",
    "write_registry",
    "mutate_registry",
    "activate",
    "authorize",
    "release_order",
    "submit_order",
    "read_private_state",
    "qpu_execute",
    "live_execute",
}
ALLOWED_QUANTUM_CEILINGS = {
    "NONE",
    "SPECIFIED",
    "MAPPED",
    "LOCAL_EXACT_PARITY",
    "CLASSICAL_COMPARATOR_READY",
}
RP5C_ID_RE = re.compile(r"^RP5C_IDENTITY_\d{8}$")
SEMVER_RE = re.compile(r"^\d+\.\d+(?:\.\d+)?(?:[-+][A-Za-z0-9._-]+)?$")
CALLABLE_RE = re.compile(r"^(?:src\.)?qtt\.[A-Za-z_][A-Za-z0-9_.]*(?::|\.)[A-Za-z_][A-Za-z0-9_]*$")


class InvariantError(RuntimeError):
    """A named independent invariant failure."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


class Deadline:
    def __init__(self, timeout_ms: int) -> None:
        self.started = time.perf_counter()
        self.limit = self.started + max(1, timeout_ms) / 1000.0

    def check(self, where: str) -> None:
        if time.perf_counter() > self.limit:
            raise InvariantError("VALIDATION_TIMEOUT", where)

    @property
    def elapsed_ms(self) -> int:
        return int((time.perf_counter() - self.started) * 1000)


class Audit:
    def __init__(self, deadline: Deadline) -> None:
        self.deadline = deadline
        self.checks: dict[str, Any] = {}
        self.metrics: dict[str, Any] = {}
        self.errors: list[dict[str, str]] = []
        self.error_count = 0

    def fail(self, code: str, detail: str) -> None:
        self.error_count += 1
        if len(self.errors) < 200:
            self.errors.append({"code": code, "detail": detail[:2000]})

    def require(self, name: str, condition: bool, detail: str) -> None:
        self.checks[name] = bool(condition)
        if not condition:
            self.fail(name, detail)

    def capture(self, name: str, function: Callable[[], Any]) -> Any:
        self.deadline.check(name)
        before = self.error_count
        try:
            value = function()
        except InvariantError as exc:
            self.fail(exc.code, exc.detail)
            value = None
        except Exception as exc:  # fail closed, while keeping stdout machine-readable
            self.fail(name, f"{type(exc).__name__}: {exc}")
            value = None
        self.checks[name] = self.error_count == before
        return value


def _plain(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return {field.name: _plain(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_plain(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _plain(value.to_dict())
    if hasattr(value, "__dict__") and not isinstance(value, type):
        return {str(key): _plain(item) for key, item in vars(value).items() if not key.startswith("__")}
    return value


def _canonical_json(value: Any, *, strip_volatile: bool = False) -> str:
    volatile = {
        "receipt_id",
        "start_time",
        "end_time",
        "started_at",
        "ended_at",
        "latency_ms",
        "generation",
        "snapshot_generation",
        "trace_id",
    }

    def clean(item: Any) -> Any:
        item = _plain(item)
        if isinstance(item, dict):
            return {
                key: clean(value)
                for key, value in sorted(item.items())
                if not (strip_volatile and key.lower() in volatile)
            }
        if isinstance(item, list):
            return [clean(value) for value in item]
        return item

    return json.dumps(clean(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _rp5c_group_custody_key(row: Mapping[str, Any]) -> dict[str, str]:
    return {
        "key_version": RP5C_GROUP_CUSTODY_KEY_VERSION,
        **{field: str(row.get(field) or "") for field in RP5C_GROUP_KEY_FIELDS},
    }


def _rp5c_group_custody_tuple(
    value: Mapping[str, Any], *, code: str = "RP5C_SOURCE_GROUP_KEY_INVALID"
) -> tuple[str, ...]:
    expected = {"key_version", *RP5C_GROUP_KEY_FIELDS}
    if (
        set(value) != expected
        or value.get("key_version") != RP5C_GROUP_CUSTODY_KEY_VERSION
        or any(not isinstance(value.get(field), str) for field in RP5C_GROUP_KEY_FIELDS)
    ):
        raise InvariantError(code, repr(value))
    return tuple(str(value[field]) for field in RP5C_GROUP_KEY_FIELDS)


def _walk(value: Any, path: tuple[str, ...] = ()) -> Iterator[tuple[tuple[str, ...], Any]]:
    yield path, value
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk(child, path + (str(key),))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from _walk(child, path + (str(index),))


def _strings(value: Any) -> Iterator[str]:
    for _, item in _walk(value):
        if isinstance(item, str):
            yield item


def _nonempty(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def _require_keys(value: Any, required: set[str], code: str, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise InvariantError(code, f"{label} must be an object")
    missing = sorted(required - set(value))
    if missing:
        raise InvariantError(code, f"{label} missing {missing}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise InvariantError("REGISTRY_JSON_INVALID", f"{path}:{line_number}: {exc}") from exc
            if not isinstance(row, dict):
                raise InvariantError("REGISTRY_ROW_NOT_OBJECT", f"{path}:{line_number}")
            rows.append(row)
    return rows


def _manifest_files(manifest: Mapping[str, Any]) -> list[str]:
    candidates = manifest.get("shards") or manifest.get("partitions") or manifest.get("files")
    if not isinstance(candidates, list):
        raise InvariantError("SHARD_MANIFEST_INVALID", "manifest has no shards/partitions list")
    names: list[str] = []
    for item in candidates:
        if isinstance(item, str):
            name = item
        elif isinstance(item, Mapping):
            name = next(
                (
                    str(item[key])
                    for key in ("file_name", "filename", "file", "path", "shard_file")
                    if _nonempty(item.get(key))
                ),
                "",
            )
        else:
            name = ""
        if not name:
            raise InvariantError("SHARD_MANIFEST_INVALID", f"invalid shard entry {item!r}")
        names.append(name)
    if len(names) != len(set(names)):
        raise InvariantError("SHARD_MANIFEST_DUPLICATE", "manifest repeats a shard")
    return names


def _detect_layout(artifact_dir: Path) -> tuple[str, list[Path], Mapping[str, Any] | None]:
    single = artifact_dir / "registry.jsonl"
    manifest_path = artifact_dir / "registry.manifest.json"
    shards = sorted(artifact_dir.glob("registry.part-*.jsonl"), key=lambda path: path.name)
    single_active = single.is_file()
    sharded_active = manifest_path.is_file() or bool(shards)
    if single_active == sharded_active:
        raise InvariantError(
            "ACTIVE_LAYOUT_COUNT",
            f"single={single_active}, manifest={manifest_path.is_file()}, shard_count={len(shards)}",
        )
    if single_active:
        return "SINGLE", [single], None
    if not manifest_path.is_file() or not shards:
        raise InvariantError("SHARDED_LAYOUT_INCOMPLETE", "manifest and at least one shard are both required")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise InvariantError("SHARD_MANIFEST_INVALID", "manifest root is not an object")
    for path, value in _walk(manifest):
        key = path[-1].lower() if path else ""
        if any(token in key for token in ("hash", "sha", "checksum", "digest")):
            raise InvariantError("QTT_DIGEST_AUTHORITY", f"manifest key {'.'.join(path)}")
        if isinstance(value, str) and ("sha256" in value.lower() or "checksum" in value.lower()):
            raise InvariantError("QTT_DIGEST_AUTHORITY", f"manifest value at {'.'.join(path)}")
    declared = _manifest_files(manifest)
    resolved: list[Path] = []
    for name in declared:
        candidate = (artifact_dir / name).resolve()
        try:
            candidate.relative_to(artifact_dir.resolve())
        except ValueError as exc:
            raise InvariantError("SHARD_PATH_ESCAPE", name) from exc
        if not candidate.is_file():
            raise InvariantError("SHARD_MISSING", name)
        resolved.append(candidate)
    actual = {path.resolve() for path in shards}
    if set(resolved) != actual:
        raise InvariantError(
            "SHARD_MANIFEST_MISMATCH",
            f"declared={sorted(path.name for path in resolved)}, actual={sorted(path.name for path in actual)}",
        )
    return "SHARDED", resolved, manifest


def _validate_canonical_artifact_surface(
    artifact_dir: Path, layout: str, registry_files: Sequence[Path]
) -> None:
    if not artifact_dir.is_dir():
        raise InvariantError("CANONICAL_ARTIFACT_SURFACE", f"missing directory: {artifact_dir}")
    children = list(artifact_dir.iterdir())
    directories = sorted(path.name for path in children if path.is_dir())
    if directories:
        raise InvariantError("CANONICAL_ARTIFACT_SURFACE", f"unexpected directories: {directories}")
    expected = {path.name for path in registry_files} | {"acceptance.report.json"}
    if layout == "SHARDED":
        expected.add("registry.manifest.json")
    actual = {path.name for path in children if path.is_file()}
    if actual != expected:
        raise InvariantError(
            "CANONICAL_ARTIFACT_SURFACE",
            f"layout={layout}, missing={sorted(expected-actual)}, unexpected={sorted(actual-expected)}",
        )


def _unwrap_records(value: Any) -> list[dict[str, Any]] | None:
    if isinstance(value, (list, tuple)) and all(isinstance(row, Mapping) for row in value):
        if not value or all("canonical_component_id" in row for row in value):
            return [row if isinstance(row, dict) else dict(row) for row in value]
    if isinstance(value, (list, tuple)):
        for item in value:
            rows = _unwrap_records(item)
            if rows is not None:
                return rows
    if isinstance(value, Mapping):
        for key in ("records", "rows", "registry_records"):
            if key in value:
                return _unwrap_records(value[key])
        if value and all(isinstance(row, Mapping) and "canonical_component_id" in row for row in value.values()):
            return [row if isinstance(row, dict) else dict(row) for row in value.values()]
    if dataclasses.is_dataclass(value) or (hasattr(value, "__dict__") and not isinstance(value, type)):
        return _unwrap_records(_plain(value))
    return None


def _call_with_path(function: Callable[..., Any], artifact_dir: Path) -> Any:
    signature = inspect.signature(function)
    parameters = signature.parameters
    for key in ("artifact_dir", "registry_root", "registry_dir", "path", "root"):
        if key in parameters:
            return function(**{key: artifact_dir})
    return function(artifact_dir)


def _load_logical_records(control_module: Any, artifact_dir: Path) -> tuple[list[dict[str, Any]], str, int]:
    layout, files, manifest = _detect_layout(artifact_dir)
    _validate_canonical_artifact_surface(artifact_dir, layout, files)
    for name in (
        "_load_logical_registry",
        "_read_logical_registry",
        "_load_registry_records",
        "_load_registry_layout",
    ):
        function = getattr(control_module, name, None)
        if callable(function):
            try:
                rows = _unwrap_records(_call_with_path(function, artifact_dir))
            except Exception:
                rows = None
            if rows is not None:
                return rows, layout, len(files)
    rows: list[dict[str, Any]] = []
    for path in files:
        rows.extend(_read_jsonl(path))
    if manifest is not None:
        declared_count = manifest.get("row_count") or manifest.get("total_row_count")
        if declared_count is not None and int(declared_count) != len(rows):
            raise InvariantError("SHARD_ROW_COUNT_MISMATCH", f"manifest={declared_count}, observed={len(rows)}")
    return rows, layout, len(files)


def _accepted_git_base_ref(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "merge-base", "HEAD", "origin/main"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=120,
            text=True,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise InvariantError("ACCEPTED_BASE_REF", str(exc)) from exc
    base_ref = result.stdout.strip()
    if result.returncode != 0 or not re.fullmatch(r"[0-9a-fA-F]{40}", base_ref):
        raise InvariantError("ACCEPTED_BASE_REF", result.stderr.strip())
    return base_ref


def _git_base_tree_paths(repo_root: Path, base_ref: str, prefix: Path) -> set[str]:
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo_root),
                "ls-tree",
                "-r",
                "-z",
                "--name-only",
                base_ref,
                "--",
                f"{prefix.as_posix()}/",
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise InvariantError("ACCEPTED_BASE_READ", str(exc)) from exc
    if result.returncode != 0:
        raise InvariantError(
            "ACCEPTED_BASE_READ",
            result.stderr.decode("utf-8", errors="replace").strip(),
        )
    try:
        return {
            value.decode("utf-8", errors="strict")
            for value in result.stdout.split(b"\0")
            if value
        }
    except UnicodeDecodeError as exc:
        raise InvariantError("ACCEPTED_BASE_READ", str(exc)) from exc


def _materialize_git_base_blob(
    repo_root: Path,
    base_ref: str,
    relative_path: Path,
    destination: Path,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("wb") as handle:
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo_root),
                    "show",
                    f"{base_ref}:{relative_path.as_posix()}",
                ],
                stdin=subprocess.DEVNULL,
                stdout=handle,
                stderr=subprocess.PIPE,
                check=False,
                timeout=120,
            )
    except (OSError, subprocess.TimeoutExpired) as exc:
        destination.unlink(missing_ok=True)
        raise InvariantError("ACCEPTED_BASE_READ", str(exc)) from exc
    if result.returncode != 0:
        destination.unlink(missing_ok=True)
        raise InvariantError(
            "ACCEPTED_BASE_READ",
            result.stderr.decode("utf-8", errors="replace").strip(),
        )


def _load_accepted_base_records(
    control_module: Any, repo_root: Path, deadline: Deadline
) -> list[dict[str, Any]]:
    base_ref = _accepted_git_base_ref(repo_root)
    single_rel = DEFAULT_ARTIFACT_DIR / "registry.jsonl"
    manifest_rel = DEFAULT_ARTIFACT_DIR / "registry.manifest.json"
    tree_paths = _git_base_tree_paths(repo_root, base_ref, DEFAULT_ARTIFACT_DIR)
    if not tree_paths:
        return []
    prefix_text = f"{DEFAULT_ARTIFACT_DIR.as_posix()}/"
    relative_names: set[str] = set()
    for path_text in tree_paths:
        if not path_text.startswith(prefix_text):
            raise InvariantError("ACCEPTED_BASE_LAYOUT", path_text)
        relative = path_text.removeprefix(prefix_text)
        if not relative or Path(relative).name != relative:
            raise InvariantError("ACCEPTED_BASE_LAYOUT", path_text)
        relative_names.add(relative)
    has_single = single_rel.name in relative_names
    has_manifest = manifest_rel.name in relative_names
    shard_names = {
        name
        for name in relative_names
        if name.startswith("registry.part-") and name.endswith(".jsonl")
    }
    allowed_names = {"acceptance.report.json", *shard_names}
    if has_single:
        allowed_names.add(single_rel.name)
    if has_manifest:
        allowed_names.add(manifest_rel.name)
    unexpected = sorted(relative_names - allowed_names)
    if unexpected:
        raise InvariantError("ACCEPTED_BASE_LAYOUT", f"unexpected={unexpected}")
    if "acceptance.report.json" not in relative_names:
        raise InvariantError("ACCEPTED_BASE_LAYOUT", "missing acceptance report")
    if has_single and (has_manifest or shard_names):
        raise InvariantError("ACCEPTED_BASE_LAYOUT", "two physical layouts")
    if has_manifest != bool(shard_names):
        raise InvariantError(
            "ACCEPTED_BASE_LAYOUT",
            f"manifest={has_manifest}, shards={sorted(shard_names)!r}",
        )
    if not has_single and not has_manifest:
        raise InvariantError("ACCEPTED_BASE_LAYOUT", "no registry layout")
    with tempfile.TemporaryDirectory(prefix="qtt-control1-validator-base-") as temporary:
        artifact_dir = Path(temporary)
        (artifact_dir / "acceptance.report.json").write_text("{}\n", encoding="utf-8")
        if has_single:
            _materialize_git_base_blob(
                repo_root, base_ref, single_rel, artifact_dir / single_rel.name
            )
        else:
            manifest_path = artifact_dir / manifest_rel.name
            _materialize_git_base_blob(
                repo_root, base_ref, manifest_rel, manifest_path
            )
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                names = _manifest_files(manifest)
            except (OSError, json.JSONDecodeError, InvariantError) as exc:
                if isinstance(exc, InvariantError):
                    raise
                raise InvariantError("ACCEPTED_BASE_MANIFEST", str(exc)) from exc
            for name in names:
                if (
                    not name.startswith("registry.part-")
                    or not name.endswith(".jsonl")
                    or Path(name).name != name
                ):
                    raise InvariantError("ACCEPTED_BASE_MANIFEST", name)
                relative = DEFAULT_ARTIFACT_DIR / name
                _materialize_git_base_blob(
                    repo_root, base_ref, relative, artifact_dir / name
                )
                deadline.check("accepted merge-base registry materialization")
            if set(names) != shard_names:
                raise InvariantError(
                    "ACCEPTED_BASE_MANIFEST",
                    f"declared={sorted(set(names))!r}, tree={sorted(shard_names)!r}",
                )
        records, _, _ = _load_logical_records(control_module, artifact_dir)
        return records


def _import_control(repo_root: Path) -> tuple[Any, Any, type[Any]]:
    root_text = str(repo_root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    capture = io.StringIO()
    with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
        package = importlib.import_module("src.qtt.computation_control")
        control = importlib.import_module("src.qtt.computation_control.control")
    exported = list(getattr(package, "__all__", []))
    if exported != ["QKUComputationControlPlaneV1"]:
        raise InvariantError("PUBLIC_EXPORT_SURFACE", f"__all__={exported!r}")
    facade_class = getattr(package, "QKUComputationControlPlaneV1", None)
    if not inspect.isclass(facade_class):
        raise InvariantError("PUBLIC_FACADE_MISSING", "QKUComputationControlPlaneV1 is not a class")
    for operation in ("resolve", "compute", "status", "explain"):
        if not callable(getattr(facade_class, operation, None)):
            raise InvariantError("PUBLIC_OPERATION_MISSING", operation)
    forbidden = [
        name
        for name in ("compile", "register", "registry", "executor", "compiler", "apply_update")
        if callable(getattr(facade_class, name, None))
    ]
    if forbidden:
        raise InvariantError("PUBLIC_INTERNAL_LAYER_EXPOSED", repr(forbidden))
    return package, control, facade_class


def _construct_facade(facade_class: type[Any], artifact_dir: Path) -> Any:
    attempts: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    signature = inspect.signature(facade_class)
    parameters = signature.parameters
    for key in ("artifact_dir", "registry_root", "registry_dir", "registry_path", "path"):
        if key in parameters:
            value = artifact_dir / "registry.jsonl" if key == "registry_path" and (artifact_dir / "registry.jsonl").is_file() else artifact_dir
            attempts.append(((), {key: value}))
    attempts.extend([((artifact_dir,), {}), ((), {})])
    failures: list[str] = []
    for args, kwargs in attempts:
        try:
            capture = io.StringIO()
            with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
                return facade_class(*args, **kwargs)
        except Exception as exc:
            failures.append(f"{args!r}/{kwargs!r}: {type(exc).__name__}: {exc}")
    raise InvariantError("FACADE_INITIALIZATION", " | ".join(failures[:5]))


def _operation(facade: Any, name: str, selector: Any, inputs: Any = None, context: Any = None) -> Any:
    function = getattr(facade, name)
    context = {} if context is None else context
    if name == "compute":
        attempts = [
            ((), {"selector": selector, "inputs": inputs or {}, "context": context}),
            ((selector, inputs or {}, context), {}),
            ((selector, inputs or {}), {"context": context}),
        ]
    else:
        attempts = [
            ((), {"selector": selector, "context": context}),
            ((selector, context), {}),
            ((selector,), {"context": context}),
        ]
    failures: list[str] = []
    for args, kwargs in attempts:
        try:
            capture = io.StringIO()
            with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
                return function(*args, **kwargs)
        except TypeError as exc:
            failures.append(str(exc))
            continue
    raise InvariantError("FACADE_CALL_SIGNATURE", f"{name}: {failures[:3]}")


def _binding_context(binding: Mapping[str, Any]) -> dict[str, Any]:
    selector = binding.get("context_selector")
    context = (
        {
            str(key): value
            for key, value in selector.items()
            if str(key) not in {"component_id", "canonical_component_id", "binding_id"}
        }
        if isinstance(selector, Mapping)
        else {"context_selector": selector}
    )
    context.setdefault("market", binding.get("market"))
    context.setdefault("venue", binding.get("venue"))
    modes = binding.get("supported_modes")
    if isinstance(modes, list) and modes:
        context.setdefault("mode", modes[0])
    return {key: value for key, value in context.items() if value is not None}


def _validate_callable_ref(reference: Any) -> None:
    if not isinstance(reference, str) or not reference:
        raise InvariantError("CALLABLE_REF_MISSING", repr(reference))
    lowered = reference.lower()
    if any(token in lowered for token in FORBIDDEN_CALL_TOKENS) or "__" in reference:
        raise InvariantError("UNSAFE_CALLABLE_REF", reference)
    if not CALLABLE_RE.fullmatch(reference):
        raise InvariantError("UNSAFE_CALLABLE_REF", reference)


def _validate_compact_value(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise InvariantError("NONFINITE_VALUE", ".".join(path))
    if isinstance(value, Decimal) and not value.is_finite():
        raise InvariantError("NONFINITE_VALUE", ".".join(path))
    if isinstance(value, Mapping):
        for key, child in value.items():
            lowered = str(key).lower()
            in_evidence = "evidence_summary" in path or str(key) == "evidence_summary"
            if in_evidence and any(token in lowered for token in BULK_KEY_TOKENS):
                if isinstance(child, (list, dict)) and len(child) > 4:
                    raise InvariantError("BULK_EVIDENCE_PAYLOAD", ".".join(path + (str(key),)))
            _validate_compact_value(child, path + (str(key),))
        return
    if isinstance(value, (list, tuple)):
        if "evidence_summary" in path and len(value) > 64:
            raise InvariantError("BULK_EVIDENCE_PAYLOAD", f"{'.'.join(path)} length={len(value)}")
        for index, child in enumerate(value):
            _validate_compact_value(child, path + (str(index),))


def _validate_evidence_compact(
    value: Any,
    path: tuple[str, ...],
    *,
    depth: int = 0,
    node_budget: list[int] | None = None,
) -> None:
    """Reject bulk payloads even when their keys avoid known evidence names."""

    if node_budget is None:
        node_budget = [0]
        try:
            serialized_bytes = len(_canonical_json(value).encode("utf-8"))
        except (TypeError, ValueError) as exc:
            raise InvariantError("BULK_EVIDENCE_PAYLOAD", ".".join(path)) from exc
        if serialized_bytes > 65_536:
            raise InvariantError(
                "BULK_EVIDENCE_PAYLOAD",
                f"{'.'.join(path)} serialized_bytes={serialized_bytes}",
            )
    node_budget[0] += 1
    if node_budget[0] > 512:
        raise InvariantError(
            "BULK_EVIDENCE_PAYLOAD",
            f"{'.'.join(path)} nodes={node_budget[0]}",
        )
    if depth > 8:
        raise InvariantError(
            "BULK_EVIDENCE_PAYLOAD",
            f"{'.'.join(path)} depth={depth}",
        )
    if isinstance(value, Mapping):
        if len(value) > 64:
            raise InvariantError(
                "BULK_EVIDENCE_PAYLOAD",
                f"{'.'.join(path)} keys={len(value)}",
            )
        for key, child in value.items():
            lowered = str(key).lower()
            if any(token in lowered for token in BULK_KEY_TOKENS):
                if isinstance(child, (Mapping, list, tuple)) and len(child) > 0:
                    raise InvariantError(
                        "BULK_EVIDENCE_PAYLOAD", ".".join(path + (str(key),))
                    )
            _validate_evidence_compact(
                child,
                path + (str(key),),
                depth=depth + 1,
                node_budget=node_budget,
            )
        return
    if isinstance(value, (list, tuple)):
        if len(value) > 64:
            raise InvariantError(
                "BULK_EVIDENCE_PAYLOAD",
                f"{'.'.join(path)} entries={len(value)}",
            )
        for index, child in enumerate(value):
            _validate_evidence_compact(
                child,
                path + (str(index),),
                depth=depth + 1,
                node_budget=node_budget,
            )
        return
    if isinstance(value, str) and len(value.encode("utf-8")) > 4_096:
        raise InvariantError(
            "BULK_EVIDENCE_PAYLOAD",
            f"{'.'.join(path)} scalar_bytes={len(value.encode('utf-8'))}",
        )


def _is_selector_wildcard(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value in {"ANY", "ALL", "*"})


def _selector_values_compatible(left: Any, right: Any) -> bool:
    return (
        _is_selector_wildcard(left)
        or _is_selector_wildcard(right)
        or _canonical_json(left) == _canonical_json(right)
    )


def _ambiguous_binding_selector_overlap(
    left: Mapping[str, Any], right: Mapping[str, Any]
) -> bool:
    left_modes = {str(value) for value in left.get("supported_modes", ())}
    right_modes = {str(value) for value in right.get("supported_modes", ())}
    if not (left_modes & right_modes):
        return False
    if not all(
        _selector_values_compatible(left.get(field), right.get(field))
        for field in ("market", "venue", "qku_binding_selector_or_null")
    ):
        return False
    left_selector = left.get("context_selector", {})
    right_selector = right.get("context_selector", {})
    if not isinstance(left_selector, Mapping) or not isinstance(right_selector, Mapping):
        return _canonical_json(left_selector) == _canonical_json(right_selector)
    for key in set(left_selector) & set(right_selector):
        if not _selector_values_compatible(left_selector[key], right_selector[key]):
            return False

    def specificity(binding: Mapping[str, Any], selector: Mapping[str, Any]) -> int:
        score = sum(
            4 for field in ("market", "venue") if not _is_selector_wildcard(binding.get(field))
        )
        score += sum(1 for item in selector.values() if not _is_selector_wildcard(item))
        return score

    return specificity(left, left_selector) == specificity(right, right_selector)


def _validate_no_digest_authority(value: Any) -> None:
    for path, item in _walk(value):
        key = path[-1].lower() if path else ""
        key_tokens = {token for token in re.split(r"[^a-z0-9]+", key) if token}
        if key_tokens & {"hash", "sha", "sha1", "sha256", "checksum", "digest", "freeze"}:
            raise InvariantError("QTT_DIGEST_AUTHORITY", ".".join(path))
        if isinstance(item, str):
            lowered = item.lower()
            if "atomicrows" in lowered and re.search(r"\b(?:sha\d*|hash|digest|checksum)\b", lowered):
                raise InvariantError("ATOMICROWS_DIGEST_REFERENCE", ".".join(path))


def _relation_type(relation: Mapping[str, Any]) -> str:
    return str(relation.get("relation_type") or relation.get("type") or relation.get("relation") or "")


def _validate_record(record: Mapping[str, Any]) -> None:
    component_id = str(record.get("canonical_component_id", "<missing>"))
    _require_keys(record, TOP_LEVEL_REQUIRED, "RECORD_SHAPE", component_id)
    if not component_id or component_id.startswith(("SOURCE::", "LOCAL::")):
        raise InvariantError("CANONICAL_ID_INVALID", component_id)
    id_tokens = {token for token in re.split(r"[^A-Za-z0-9]+", component_id.upper()) if token}
    if (
        {"PR169", "CONTROL1"} & id_tokens
        or re.search(r"(?:19|20)\d{2}[-_.]\d{2}[-_.]\d{2}", component_id)
        or {"SHA", "HASH", "DIGEST", "CHECKSUM"} & id_tokens
        or any(re.fullmatch(r"[0-9A-F]{12,64}", token) for token in id_tokens)
    ):
        raise InvariantError("CANONICAL_ID_UNSTABLE", component_id)
    semantic_version = record["semantic_version"]
    if not isinstance(semantic_version, str) or not SEMVER_RE.fullmatch(semantic_version):
        raise InvariantError("SEMANTIC_VERSION_INVALID", f"{component_id}@{semantic_version!r}")
    if record["record_state"] not in RECORD_STATES:
        raise InvariantError("RECORD_STATE_INVALID", f"{component_id}: {record['record_state']!r}")
    if not isinstance(record["origin_cohorts"], list) or not record["origin_cohorts"]:
        raise InvariantError("ORIGIN_COHORT_INVALID", component_id)

    definition = _require_keys(record["definition"], DEFINITION_REQUIRED, "DEFINITION_SHAPE", component_id)
    if not _nonempty(definition["complete_mathematical_or_procedural_definition"]):
        raise InvariantError("DEFINITION_EMPTY", component_id)
    for key in ("input_schema", "output_schema", "units_and_bases"):
        if not isinstance(definition[key], (dict, list)):
            raise InvariantError("UNIT_SCHEMA_MISSING" if key == "units_and_bases" else "DEFINITION_SHAPE", f"{component_id}.{key}")
    if (record["record_state"] == "CANONICAL_ACCEPTED" or definition["implementation_versions"]) and (
        not definition["input_schema"] or not definition["output_schema"] or not definition["units_and_bases"]
    ):
        raise InvariantError("UNIT_SCHEMA_MISSING", component_id)
    for key in ("requirements", "implementation_versions", "oracle_and_test_refs", "equivalence_proof_refs"):
        if not isinstance(definition[key], list):
            raise InvariantError("DEFINITION_SHAPE", f"{component_id}.{key} must be a list")
    for index, implementation in enumerate(definition["implementation_versions"]):
        if not isinstance(implementation, Mapping):
            raise InvariantError("IMPLEMENTATION_SHAPE", f"{component_id}[{index}]")
        embedded_fixture_keys = {
            "fixture_inputs",
            "fixture_outputs",
            "fixture_vectors",
            "test_inputs",
            "test_outputs",
            "test_vectors",
            "golden_vector",
            "golden_vectors",
        } & set(implementation)
        if embedded_fixture_keys:
            raise InvariantError(
                "CANONICAL_FIXTURE_PAYLOAD",
                f"{component_id}[{index}]: {sorted(embedded_fixture_keys)}",
            )
    for index, requirement in enumerate(definition["requirements"]):
        requirement = _require_keys(requirement, REQUIREMENT_REQUIRED, "REQUIREMENT_SHAPE", f"{component_id}[{index}]")
        target = requirement["required_component_id_or_source_selector"]
        if not isinstance(target, str) or not target or target.startswith(("SOURCE::", "LOCAL::", "UNRESOLVED::")):
            raise InvariantError("SOURCE_LOCAL_REQUIREMENT", f"{component_id}: {target!r}")
        if not _nonempty(requirement["producer_output_name"]) or not _nonempty(requirement["consumer_input_name"]):
            raise InvariantError("REQUIREMENT_PORT_MISSING", component_id)
        if "unit_or_basis_conversion" not in requirement:
            raise InvariantError("REQUIREMENT_UNIT_MISSING", component_id)

    uses = _require_keys(record["uses"], USES_REQUIRED, "USES_SHAPE", component_id)
    for key in USES_REQUIRED:
        if not isinstance(uses[key], list):
            raise InvariantError("USES_SHAPE", f"{component_id}.{key} must be a list")
    if record["record_state"] == "CANONICAL_ACCEPTED" and not uses["decision_roles"]:
        raise InvariantError("DECISION_ROLE_MISSING", component_id)

    if not isinstance(record["bindings"], list):
        raise InvariantError("BINDING_SHAPE", component_id)
    if record["record_state"] in {"CANONICAL_ACCEPTED", "PROVISIONAL", "UNDER_REVIEW"} and not record["bindings"]:
        raise InvariantError("ACTIVE_RECORD_WITHOUT_BINDING", component_id)
    binding_ids: set[str] = set()
    selectors: set[str] = set()
    validated_bindings: list[Mapping[str, Any]] = []
    for binding in record["bindings"]:
        binding = _require_keys(binding, BINDING_REQUIRED, "BINDING_SHAPE", component_id)
        binding_id = binding["binding_id"]
        if not isinstance(binding_id, str) or not binding_id:
            raise InvariantError("BINDING_ID_INVALID", component_id)
        if binding_id in binding_ids:
            raise InvariantError("AMBIGUOUS_BINDING", f"duplicate {binding_id}")
        binding_ids.add(binding_id)
        selector_key = _canonical_json(
            {
                "market": binding["market"],
                "venue": binding["venue"],
                "context": binding["context_selector"],
                "qku": binding["qku_binding_selector_or_null"],
                "modes": sorted(binding["supported_modes"]) if isinstance(binding["supported_modes"], list) else binding["supported_modes"],
            }
        )
        if selector_key in selectors:
            raise InvariantError("AMBIGUOUS_BINDING", f"{component_id}: overlapping exact selector")
        selectors.add(selector_key)
        supported_modes = binding["supported_modes"]
        mode_state = binding["mode_state"]
        if not isinstance(supported_modes, list) or len(supported_modes) != len(
            {str(value) for value in supported_modes}
        ):
            raise InvariantError("SUPPORTED_MODES_INVALID", binding_id)
        if not isinstance(mode_state, Mapping):
            raise InvariantError("MODE_STATE_INVALID", binding_id)
        missing_mode_state = sorted(
            str(mode) for mode in supported_modes if str(mode) not in mode_state
        )
        if missing_mode_state:
            raise InvariantError(
                "MODE_STATE_MISSING",
                f"{binding_id}: {missing_mode_state}",
            )
        extra_mode_state = sorted(
            str(mode) for mode in mode_state if str(mode) not in {str(value) for value in supported_modes}
        )
        if extra_mode_state:
            raise InvariantError(
                "MODE_STATE_WITHOUT_SUPPORTED_MODE",
                f"{binding_id}: {extra_mode_state}",
            )
        for mode in supported_modes:
            state = mode_state[str(mode)]
            if not isinstance(state, Mapping):
                raise InvariantError("MODE_STATE_INVALID", f"{binding_id}.{mode}")
            if state.get("evidence") not in EVIDENCE_STATES:
                raise InvariantError("MODE_STATE_INVALID", f"{binding_id}.{mode}.evidence")
            if state.get("authorization") not in AUTH_STATES:
                raise InvariantError(
                    "MODE_STATE_INVALID", f"{binding_id}.{mode}.authorization"
                )
        readiness = _require_keys(binding["readiness"], READINESS_REQUIRED, "READINESS_SHAPE", binding_id)
        for key in ("specification", "implementation", "inputs", "requirements", "oracle", "context"):
            if readiness[key] not in SPEC_STATES:
                raise InvariantError("READINESS_STATE_INVALID", f"{binding_id}.{key}={readiness[key]!r}")
        if readiness["evidence"] not in EVIDENCE_STATES or readiness["authorization"] not in AUTH_STATES:
            raise InvariantError("READINESS_STATE_INVALID", binding_id)
        if binding["derived_state"] not in DERIVED_STATES:
            raise InvariantError("DERIVED_STATE_INVALID", f"{binding_id}: {binding['derived_state']!r}")
        unresolved = any(readiness[key] != "PASS" for key in ("specification", "implementation", "inputs", "requirements", "oracle", "context"))
        if unresolved:
            action = binding["exact_resolution_action_or_null"]
            if not isinstance(action, str) or not action or action.upper() in PLACEHOLDERS:
                raise InvariantError("EXACT_ACTION_MISSING", binding_id)
        if readiness["authorization"] == "AUTHORIZED" or binding["derived_state"] == "AUTHORIZED":
            raise InvariantError("LIVE_AUTHORITY_CLAIM", binding_id)
        if readiness["evidence"] in {"REPLAY", "PAPER", "SHADOW", "DRYRUN", "CANARY", "LIVE"}:
            raise InvariantError("EMPIRICAL_EXECUTION_CLAIM", f"{binding_id}: {readiness['evidence']}")
        _validate_compact_value(binding["evidence_summary"], (component_id, binding_id, "evidence_summary"))
        _validate_evidence_compact(
            binding["evidence_summary"],
            (component_id, binding_id, "evidence_summary"),
        )
        validated_bindings.append(binding)

    for left_index, left in enumerate(validated_bindings):
        for right in validated_bindings[left_index + 1 :]:
            if _ambiguous_binding_selector_overlap(left, right):
                raise InvariantError(
                    "OVERLAPPING_BINDING_SELECTORS",
                    f"{component_id}: {left['binding_id']} / {right['binding_id']}",
                )

    if not isinstance(record["provenance"], list) or not record["provenance"]:
        raise InvariantError("PROVENANCE_SHAPE", component_id)
    for provenance in record["provenance"]:
        _require_keys(provenance, PROVENANCE_REQUIRED, "PROVENANCE_SHAPE", component_id)
    if not isinstance(record["relations"], list):
        raise InvariantError("RELATIONS_SHAPE", component_id)
    for relation in record["relations"]:
        if not isinstance(relation, Mapping) or not _relation_type(relation):
            raise InvariantError("RELATION_INVALID", f"{component_id}: {relation!r}")
    _require_keys(record["governance"], GOVERNANCE_REQUIRED, "GOVERNANCE_SHAPE", component_id)
    _validate_compact_value(record)
    _validate_no_digest_authority(record)


def _requirement_target(requirement: Mapping[str, Any]) -> str:
    return str(requirement.get("required_component_id_or_source_selector", ""))


def _graph(records: Sequence[Mapping[str, Any]]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    active_ids = {
        str(record["canonical_component_id"])
        for record in records
        if record.get("record_state") in ACCEPTED_STATES
    }
    graph: dict[str, set[str]] = {component_id: set() for component_id in active_ids}
    reverse: dict[str, set[str]] = {component_id: set() for component_id in active_ids}
    for record in records:
        component_id = str(record.get("canonical_component_id", ""))
        if component_id not in graph:
            continue
        for requirement in record.get("definition", {}).get("requirements", []):
            target = _requirement_target(requirement)
            if target not in active_ids:
                raise InvariantError("UNRESOLVED_REQUIREMENT", f"{component_id} -> {target}")
            graph[component_id].add(target)
            reverse[target].add(component_id)
    return graph, reverse


def _topological(graph: Mapping[str, set[str]]) -> list[str]:
    indegree = {node: len(requirements) for node, requirements in graph.items()}
    reverse: dict[str, set[str]] = {node: set() for node in graph}
    for node, requirements in graph.items():
        for requirement in requirements:
            reverse.setdefault(requirement, set()).add(node)
    queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
    order: list[str] = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for dependent in sorted(reverse.get(node, ())):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                queue.append(dependent)
    if len(order) != len(graph):
        cycle_nodes = sorted(node for node, degree in indegree.items() if degree > 0)[:20]
        raise InvariantError("DAG_CYCLE", repr(cycle_nodes))
    return order


def _validate_qku_unambiguity(records: Sequence[Mapping[str, Any]]) -> int:
    roots: dict[tuple[str, str, str, str], set[str]] = defaultdict(set)
    selection_policy: dict[tuple[str, str, str, str], bool] = defaultdict(bool)
    for record in records:
        if record.get("record_state") not in RUNTIME_ACTIVE_RECORD_STATES:
            continue
        component_id = str(record["canonical_component_id"])
        kind = str(record["definition"]["component_kind"])
        binding_contexts = [
            _canonical_json(binding.get("context_selector")) for binding in record.get("bindings", [])
        ] or ["null"]
        for qku in record["uses"]["qku_role_bindings"]:
            if not isinstance(qku, Mapping):
                raise InvariantError("QKU_BINDING_SHAPE", component_id)
            qku_id = str(qku.get("qku_id", ""))
            role = str(qku.get("role_or_decision_stage", ""))
            market = str(qku.get("market_family", ""))
            explicit_context = qku.get("context_selector")
            contexts = [_canonical_json(explicit_context)] if explicit_context is not None else binding_contexts
            target = str(qku.get("stack_root_or_direct_component") or component_id)
            if not qku_id or not role or not market or not target:
                raise InvariantError("QKU_BINDING_SHAPE", f"{component_id}: {qku!r}")
            for context in contexts:
                key = (qku_id, role, market, context)
                roots[key].add(target)
                if kind == "QKU_SELECTION_POLICY" or qku.get("selection_rule_if_container"):
                    selection_policy[key] = True
    ambiguous = [key for key, values in roots.items() if len(values) > 1 and not selection_policy[key]]
    if ambiguous:
        raise InvariantError("AMBIGUOUS_QKU_ROOT", repr(ambiguous[:10]))
    return len(roots)


def _rp5c_source(
    repo_root: Path, deadline: Deadline
) -> tuple[dict[str, dict[str, Any]], int]:
    path = repo_root / RP5C_DEDUPE
    groups: dict[str, dict[str, Any]] = {}
    duplicate_group_ids: set[str] = set()
    member_owner: dict[str, str] = {}
    member_count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line_number % 1000 == 0:
                deadline.check("rp5c_source")
            row = json.loads(line)
            canonical = row.get("canonical_identity_row_id")
            members = row.get("duplicate_member_identity_row_ids")
            group_id = row.get("duplicate_group_id")
            if not isinstance(canonical, str) or not RP5C_ID_RE.fullmatch(canonical):
                raise InvariantError("RP5C_SOURCE_INVALID", f"line {line_number}: canonical")
            if not isinstance(group_id, str) or not group_id or group_id in duplicate_group_ids:
                raise InvariantError("RP5C_SOURCE_INVALID", f"line {line_number}: duplicate group")
            duplicate_group_ids.add(group_id)
            if not isinstance(members, list) or len(members) != row.get("duplicate_member_count"):
                raise InvariantError("RP5C_SOURCE_INVALID", f"line {line_number}: members")
            member_set = set(members)
            if len(member_set) != len(members) or canonical not in member_set:
                raise InvariantError("RP5C_SOURCE_INVALID", f"line {line_number}: member uniqueness")
            if canonical in groups:
                raise InvariantError("RP5C_SOURCE_INVALID", f"line {line_number}: duplicate canonical")
            for member in members:
                if not isinstance(member, str) or not RP5C_ID_RE.fullmatch(member):
                    raise InvariantError("RP5C_SOURCE_INVALID", f"line {line_number}: member identity")
                if member in member_owner:
                    raise InvariantError("RP5C_SOURCE_INVALID", f"line {line_number}: repeated member")
                member_owner[member] = canonical
            groups[canonical] = {
                "duplicate_group_id": group_id,
                "dedupe_status": row.get("dedupe_status"),
                "members": member_set,
                "source_artifact_row_ids": set(),
                "provenance_tiers": set(),
                "custody_route_refs": set(),
            }
            member_count += len(members)
    if len(groups) != EXPECTED_RP5C_CANONICAL or member_count < len(groups):
        raise InvariantError("RP5C_SOURCE_COUNT", f"groups={len(groups)}, members={member_count}")

    custody_key_owners: dict[tuple[str, ...], str] = {}
    canonical_library_rows: set[str] = set()
    for relative_path in RP5C_LIBRARIES:
        with (repo_root / relative_path).open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if line_number % 1000 == 0:
                    deadline.check("rp5c_library_source")
                row = json.loads(line)
                canonical = row.get("canonical_identity_row_id")
                if canonical not in groups:
                    raise InvariantError(
                        "RP5C_LIBRARY_INVALID",
                        f"{relative_path.as_posix()} line {line_number}: canonical",
                    )
                if relative_path == RP5C_CANONICAL_LIBRARY:
                    if canonical in canonical_library_rows:
                        raise InvariantError(
                            "RP5C_SOURCE_GROUP_KEY_COLLISION",
                            f"repeated canonical library row: {canonical}",
                        )
                    canonical_library_rows.add(str(canonical))
                    source_group = groups[str(canonical)]
                    if row.get("duplicate_group_id") != source_group["duplicate_group_id"]:
                        raise InvariantError(
                            "RP5C_SOURCE_GROUP_KEY_INVALID",
                            f"{canonical}: canonical-library/ledger group mismatch",
                        )
                    key_payload = _rp5c_group_custody_key(row)
                    key = _rp5c_group_custody_tuple(key_payload)
                    prior = custody_key_owners.get(key)
                    if prior is not None:
                        raise InvariantError(
                            "RP5C_SOURCE_GROUP_KEY_COLLISION",
                            f"{prior} <> {canonical}",
                        )
                    custody_key_owners[key] = str(canonical)
                    source_group["source_group_custody_key"] = key_payload
                    source_group["source_group_custody_tuple"] = key
                source_artifact_row_id = row.get("source_artifact_row_id")
                if source_artifact_row_id:
                    groups[canonical]["source_artifact_row_ids"].add(
                        str(source_artifact_row_id)
                    )
    if canonical_library_rows != set(groups) or len(custody_key_owners) != len(groups):
        missing = sorted(set(groups) - canonical_library_rows)[:10]
        extra = sorted(canonical_library_rows - set(groups))[:10]
        raise InvariantError(
            "RP5C_SOURCE_GROUP_KEY_CLOSURE",
            f"keys={len(custody_key_owners)}, groups={len(groups)}, missing={missing}, extra={extra}",
        )

    lineage_members: set[str] = set()
    with (repo_root / RP5C_LINEAGE).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line_number % 1000 == 0:
                deadline.check("rp5c_lineage_source")
            row = json.loads(line)
            canonical = row.get("canonical_identity_row_id")
            member = row.get("identity_row_id")
            if (
                not isinstance(canonical, str)
                or canonical not in groups
                or not isinstance(member, str)
                or member not in groups[canonical]["members"]
            ):
                raise InvariantError("RP5C_LINEAGE_INVALID", f"line {line_number}: canonical/member")
            if member in lineage_members:
                raise InvariantError("RP5C_LINEAGE_INVALID", f"line {line_number}: repeated member")
            lineage_members.add(member)
            source_artifact_row_id = row.get("source_artifact_row_id")
            if source_artifact_row_id:
                groups[canonical]["source_artifact_row_ids"].add(
                    str(source_artifact_row_id)
                )
            provenance_tier = row.get("provenance_tier")
            if provenance_tier:
                groups[canonical]["provenance_tiers"].add(str(provenance_tier))
            groups[canonical]["custody_route_refs"].update(
                str(value) for value in row.get("custody_route_refs", ())
            )
    expected_members = set(member_owner)
    if lineage_members != expected_members:
        missing = sorted(expected_members - lineage_members)[:10]
        extra = sorted(lineage_members - expected_members)[:10]
        raise InvariantError(
            "RP5C_LINEAGE_CLOSURE",
            f"lineage={len(lineage_members)}, dedupe_members={member_count}, missing={missing}, extra={extra}",
        )
    return groups, member_count


def _registry_rp5c_group_map(
    records: Sequence[Mapping[str, Any]],
) -> dict[tuple[str, ...], str]:
    key_to_component: dict[tuple[str, ...], str] = {}
    baseline_components: set[str] = set()
    for record in records:
        if "RP5C_BASELINE" not in {str(value) for value in record.get("origin_cohorts", ())}:
            continue
        component_id = str(record.get("canonical_component_id") or "")
        baseline_components.add(component_id)
        key_payloads = [
            relation.get("source_group_custody_key")
            for relation in record.get("relations", ())
            if isinstance(relation, Mapping)
            and _relation_type(relation)
            == "RP5C_BASELINE_GROUPING_NOT_CONTROL1_EQUIVALENCE_PROOF"
        ]
        if len(key_payloads) != 1 or not isinstance(key_payloads[0], Mapping):
            raise InvariantError("RP5C_STABLE_GROUP_KEY", component_id)
        key = _rp5c_group_custody_tuple(
            key_payloads[0], code="RP5C_STABLE_GROUP_KEY"
        )
        prior = key_to_component.get(key)
        if prior is not None and prior != component_id:
            raise InvariantError(
                "RP5C_STABLE_GROUP_COLLISION", f"{key!r}: {prior} <> {component_id}"
            )
        key_to_component[key] = component_id
    if (
        len(baseline_components) != EXPECTED_RP5C_CANONICAL
        or len(key_to_component) != EXPECTED_RP5C_CANONICAL
    ):
        raise InvariantError(
            "RP5C_STABLE_GROUP_COUNT",
            f"records={len(baseline_components)}, groups={len(key_to_component)}",
        )
    return key_to_component


def _validate_rp5c_nonruntime_qku_roles(record: Mapping[str, Any]) -> int:
    component_id = str(record.get("canonical_component_id") or "")
    roles = record.get("uses", {}).get("qku_role_bindings", ())
    if not roles:
        return 0
    exact_action = f"MISSING_SEMANTIC_SPECIFICATION: {component_id}"
    if record.get("record_state") != "DORMANT_PRESERVED":
        raise InvariantError("RP5C_QKU_ROLE_RUNTIME_ACTIVATION", component_id)
    for role in roles:
        if (
            not isinstance(role, Mapping)
            or role.get("stack_root_or_direct_component") is not None
            or role.get("selection_rule_if_container") is not None
            or role.get("runtime_root_eligibility")
            != "INELIGIBLE_UNTIL_COMPLETE_SEMANTICS_AND_DIRECT_ROOT_PROOF"
            or role.get("exact_resolution_action") != exact_action
        ):
            raise InvariantError("RP5C_QKU_ROLE_RUNTIME_ROOT", component_id)
    ineligibility = [
        relation
        for relation in record.get("relations", ())
        if isinstance(relation, Mapping)
        and _relation_type(relation) == "RP5C_RUNTIME_ROOT_INELIGIBILITY"
    ]
    if len(ineligibility) != 1:
        raise InvariantError("RP5C_QKU_ROLE_INELIGIBILITY_PROOF", component_id)
    proof = ineligibility[0]
    if (
        proof.get("runtime_root_eligible") is not False
        or proof.get("selector_or_root_invented") is not False
        or proof.get("qku_roles_erased") is not False
        or proof.get("preserved_qku_role_count") != len(roles)
        or proof.get("exact_resolution_action") != exact_action
    ):
        raise InvariantError("RP5C_QKU_ROLE_INELIGIBILITY_PROOF", component_id)
    if any(
        _relation_type(relation) == "ALIAS_OF"
        for relation in record.get("relations", ())
        if isinstance(relation, Mapping)
    ):
        raise InvariantError("RP5C_CUSTODY_KEY_FALSE_EQUIVALENCE", component_id)
    bindings = record.get("bindings", ())
    if not bindings or any(
        not isinstance(binding, Mapping)
        or binding.get("activation_state") != "DORMANT_PRESERVED"
        or bool(binding.get("supported_modes"))
        or binding.get("selected_implementation_version") is not None
        or binding.get("readiness", {}).get("authorization") != "NOT_ELIGIBLE"
        for binding in bindings
    ):
        raise InvariantError("RP5C_QKU_ROLE_RUNTIME_BINDING", component_id)
    return len(roles)


def _validate_rp5c_import(
    records: Sequence[Mapping[str, Any]],
    groups: Mapping[str, Mapping[str, Any]],
    deadline: Deadline,
    accepted_group_map: Mapping[tuple[str, ...], str] | None = None,
) -> tuple[int, int]:
    expected_member_count = sum(len(group["members"]) for group in groups.values())
    by_group_id = {
        str(group["duplicate_group_id"]): (canonical, group)
        for canonical, group in groups.items()
    }
    by_custody_key = {
        tuple(group["source_group_custody_tuple"]): (canonical, group)
        for canonical, group in groups.items()
    }
    if len(by_custody_key) != len(groups):
        raise InvariantError("RP5C_SOURCE_GROUP_KEY_COLLISION", "source key map")
    exact_group_records: dict[str, set[str]] = defaultdict(set)
    exact_lineage_records: dict[str, set[str]] = defaultdict(set)
    current_group_ids = set(by_group_id)
    for index, record in enumerate(records):
        if index % 1000 == 0:
            deadline.check("rp5c_registry_scan")
        origins = {str(value) for value in record.get("origin_cohorts", [])}
        if "RP5C_BASELINE" not in origins:
            continue
        component_id = str(record["canonical_component_id"])
        _validate_rp5c_nonruntime_qku_roles(record)
        for relation in record.get("relations", ()):
            if not isinstance(relation, Mapping):
                continue
            relation_type = _relation_type(relation)
            if relation_type == "RP5C_BASELINE_GROUPING_NOT_CONTROL1_EQUIVALENCE_PROOF":
                group_id = str(relation.get("source_duplicate_group_id") or "")
                if group_id not in current_group_ids:
                    raise InvariantError(
                        "RP5C_REGISTRY_UNKNOWN_GROUP", f"{component_id}: {group_id}"
                    )
                _, source_group = by_group_id[group_id]
                key_payload = relation.get("source_group_custody_key")
                if (
                    isinstance(key_payload, Mapping)
                    and _rp5c_group_custody_tuple(
                        key_payload, code="RP5C_REGISTRY_GROUP_KEY_INVALID"
                    )
                    == tuple(source_group["source_group_custody_tuple"])
                    and
                    set(relation.get("member_identity_row_ids", ()))
                    == set(source_group["members"])
                    and relation.get("source_dedupe_status")
                    == source_group["dedupe_status"]
                    and relation.get("direct_semantic_equivalence_proven") is False
                ):
                    exact_group_records[group_id].add(component_id)
            elif relation_type == "RP5C_SOURCE_LINEAGE_SUMMARY":
                canonical = str(relation.get("source_canonical_identity_row_id") or "")
                source_group = groups.get(canonical)
                if source_group is None:
                    continue
                if (
                    relation.get("source_occurrence_count")
                    == len(source_group["members"])
                    and set(relation.get("identity_row_ids", ()))
                    == set(source_group["members"])
                    and set(relation.get("source_artifact_row_ids", ()))
                    == set(source_group["source_artifact_row_ids"])
                    and set(relation.get("provenance_tiers", ()))
                    == set(source_group["provenance_tiers"])
                    and set(relation.get("custody_route_refs", ()))
                    == set(source_group["custody_route_refs"])
                    and relation.get("immutable_original_preserved") is True
                ):
                    exact_lineage_records[canonical].add(component_id)

    missing_groups = [group_id for group_id in current_group_ids if not exact_group_records[group_id]]
    ambiguous_groups = [
        group_id for group_id in current_group_ids if len(exact_group_records[group_id]) != 1
    ]
    missing_lineage = [canonical for canonical in groups if not exact_lineage_records[canonical]]
    ambiguous_lineage = [
        canonical for canonical in groups if len(exact_lineage_records[canonical]) != 1
    ]
    if missing_groups or ambiguous_groups or missing_lineage or ambiguous_lineage:
        raise InvariantError(
            "RP5C_CANONICAL_IMPORT",
            "missing_groups="
            f"{missing_groups[:10]}, ambiguous_groups={ambiguous_groups[:10]}, "
            f"missing_lineage={missing_lineage[:10]}, ambiguous_lineage={ambiguous_lineage[:10]}",
        )

    covered = 0
    stable_mismatches: list[str] = []
    for index, (canonical, source_group) in enumerate(groups.items()):
        if index % 1000 == 0:
            deadline.check("rp5c_member_coverage")
        group_id = str(source_group["duplicate_group_id"])
        custody_key = tuple(source_group["source_group_custody_tuple"])
        target = next(iter(exact_group_records[group_id]))
        if exact_lineage_records[canonical] != {target}:
            stable_mismatches.append(f"{group_id}: grouping/lineage target mismatch")
        if accepted_group_map is not None and accepted_group_map.get(custody_key) != target:
            stable_mismatches.append(
                f"{custody_key!r}: {accepted_group_map.get(custody_key)!r} -> {target!r}"
            )
        covered += len(source_group["members"])
    if stable_mismatches or covered != expected_member_count:
        raise InvariantError(
            "RP5C_DUPLICATE_MEMBER_COVERAGE",
            f"covered={covered}/{expected_member_count}, stable_mismatches={stable_mismatches[:10]}",
        )
    return len(groups), covered


def _owner_requirement_coverage(records: Sequence[Mapping[str, Any]]) -> int:
    mapping: dict[str, set[str]] = defaultdict(set)
    for record in records:
        component_id = str(record["canonical_component_id"])
        for path, value in _walk(record):
            if not path:
                continue
            key = path[-1]
            if key == "owner_requirement_id" and isinstance(value, str) and value:
                mapping[value].add(component_id)
            elif key == "owner_requirement_ids" and isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and item:
                        mapping[item].add(component_id)
    ambiguous = {key: sorted(values) for key, values in mapping.items() if len(values) != 1}
    if len(mapping) != EXPECTED_OWNER_REQUIREMENTS or ambiguous:
        raise InvariantError(
            "OWNER_REQUIREMENT_COVERAGE",
            f"unique={len(mapping)}, ambiguous={dict(list(ambiguous.items())[:10])}",
        )
    return len(mapping)


def _implementation_ref(entry: Mapping[str, Any]) -> str:
    return str(
        entry.get("callable_or_solver_ref")
        or entry.get("callable_ref")
        or entry.get("implementation_ref")
        or ""
    )


def _implementation_class(record: Mapping[str, Any]) -> str:
    definition = record["definition"]
    explicit = str(
        definition.get("implementation_inventory_class")
        or definition.get("implementation_class")
        or ""
    ).upper()
    if explicit in EXPECTED_IMPLEMENTATIONS:
        return explicit
    for entry in definition.get("implementation_versions", []):
        if isinstance(entry, Mapping):
            explicit = str(entry.get("implementation_inventory_class") or entry.get("inventory_class") or "").upper()
            if explicit in EXPECTED_IMPLEMENTATIONS:
                return explicit
    kind = str(definition.get("component_kind", ""))
    origins = " ".join(str(value) for value in record.get("origin_cohorts", [])).upper()
    if kind == "QUANTUM_FORMULATION" or "QUANTUM_CALLABLE" in origins:
        return "QUANTUM_CALLABLE_FAMILY"
    if kind in ALGORITHM_KINDS or "ALGORITHM_IMPLEMENTATION" in origins:
        return "ALGORITHM"
    return "FORMULA"


def _validate_implementation_inventory(
    records: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, int], list[Mapping[str, Any]]]:
    counts: Counter[str] = Counter()
    implementation_records: list[Mapping[str, Any]] = []
    callable_refs: set[str] = set()
    for record in records:
        implementations = record["definition"].get("implementation_versions", [])
        if not implementations:
            continue
        inventory_class = _implementation_class(record)
        counts[inventory_class] += 1
        implementation_records.append(record)
        for entry in implementations:
            if not isinstance(entry, Mapping):
                raise InvariantError("IMPLEMENTATION_SHAPE", str(record["canonical_component_id"]))
            reference = _implementation_ref(entry)
            _validate_callable_ref(reference)
            callable_refs.add(reference)
            for key in ("implementation_version", "determinism_or_seed_policy", "memoizable_flag"):
                if key not in entry:
                    aliases = {
                        "determinism_or_seed_policy": ("determinism_seed_policy", "determinism_policy"),
                        "memoizable_flag": ("memoizable",),
                        "implementation_version": ("version",),
                    }[key]
                    if not any(alias in entry for alias in aliases):
                        raise InvariantError("IMPLEMENTATION_SHAPE", f"{reference}: missing {key}")
        if inventory_class == "QUANTUM_CALLABLE_FAMILY":
            quantum = record["definition"].get("quantum", {})
            ceiling = str(quantum.get("maturity_ceiling", "")) if isinstance(quantum, Mapping) else ""
            if ceiling not in ALLOWED_QUANTUM_CEILINGS:
                raise InvariantError("QUANTUM_MATURITY_CEILING", f"{record['canonical_component_id']}: {ceiling!r}")
            for binding in record.get("bindings", []):
                if binding.get("readiness", {}).get("authorization") not in {"NOT_ELIGIBLE", "ELIGIBLE"}:
                    raise InvariantError("QUANTUM_AUTHORITY_CLAIM", str(record["canonical_component_id"]))
    if dict(counts) != EXPECTED_IMPLEMENTATIONS:
        raise InvariantError("IMPLEMENTATION_INVENTORY_COUNT", f"observed={dict(counts)}, expected={EXPECTED_IMPLEMENTATIONS}")
    if len(implementation_records) != sum(EXPECTED_IMPLEMENTATIONS.values()):
        raise InvariantError("IMPLEMENTATION_INVENTORY_COUNT", f"records={len(implementation_records)}")
    return dict(counts), implementation_records


def _policy_entries(policy: Any) -> Iterator[tuple[str, Mapping[str, Any]]]:
    if isinstance(policy, Mapping):
        if isinstance(policy.get("agent_id"), str):
            yield str(policy["agent_id"]), policy
            return
        for key, value in policy.items():
            if key in EXPECTED_AGENTS and isinstance(value, Mapping):
                yield key, value
    elif isinstance(policy, list):
        for entry in policy:
            yield from _policy_entries(entry)


def _validate_agent_policies(records: Sequence[Mapping[str, Any]]) -> int:
    policies: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        for binding in record.get("bindings", []):
            for agent_id, policy in _policy_entries(binding.get("agent_access_policy")):
                policies[agent_id].append(policy)
    observed = set(policies)
    if observed != EXPECTED_AGENTS:
        raise InvariantError("PR165_D2_AGENT_SET", f"missing={sorted(EXPECTED_AGENTS-observed)}, extra={sorted(observed-EXPECTED_AGENTS)}")
    expected_compute = {
        "parameter_selector_agent",
        "risk_manager_agent",
        "quantum_optimizer_agent",
        "commander_agent",
    }
    operation_union: dict[str, set[str]] = defaultdict(set)
    for agent_id, entries in policies.items():
        for entry in entries:
            operations = entry.get("control_plane_operations") or entry.get("allowed_operations") or []
            if not isinstance(operations, list):
                raise InvariantError("AGENT_POLICY_SHAPE", agent_id)
            operation_set = {str(value) for value in operations}
            if not operation_set <= {"resolve", "compute", "status", "explain"}:
                raise InvariantError("AGENT_ACCESS_ESCALATION", f"{agent_id}: {sorted(operation_set)}")
            if operation_set & FORBIDDEN_AGENT_OPERATIONS:
                raise InvariantError("AGENT_ACCESS_ESCALATION", agent_id)
            if not {"status", "explain"} <= operation_set:
                raise InvariantError("AGENT_POLICY_INCOMPLETE", agent_id)
            if "compute" in operation_set and "resolve" not in operation_set:
                raise InvariantError("AGENT_POLICY_INCOMPLETE", f"{agent_id}: compute without resolve")
            if agent_id in {"dashboard_agent", "connector_venue_readiness_future_consumer", "research_agent"} and "compute" in operation_set:
                raise InvariantError("AGENT_ACCESS_ESCALATION", agent_id)
            operation_union[agent_id].update(operation_set)
            for path, value in _walk(entry):
                key = path[-1].lower() if path else ""
                if any(token in key for token in ("live", "order", "private", "qpu", "activate", "authorize")) and value not in (
                    False,
                    None,
                    0,
                    "NONE",
                    "NOT_ALLOWED",
                    "FORBIDDEN",
                    "NONLIVE_ONLY",
                    "HANDOFF_ONLY",
                ):
                    raise InvariantError("AGENT_ACCESS_ESCALATION", f"{agent_id}.{'.'.join(path)}={value!r}")
    for agent_id in expected_compute:
        if not {"resolve", "compute"} <= operation_union[agent_id]:
            raise InvariantError("AGENT_POLICY_INCOMPLETE", f"{agent_id}: no eligible compute binding")
    return len(observed)


def _validate_authority_absence(records: Sequence[Mapping[str, Any]]) -> None:
    protected_terms = ("qpu", "replay", "paper", "shadow", "live", "order_release", "private_state")
    positive_keys = ("executed", "execution_created", "call_count", "claim_created", "authority_created", "authorized")
    for record in records:
        component_id = str(record["canonical_component_id"])
        for path, value in _walk(record):
            key = path[-1].lower() if path else ""
            if any(term in key for term in protected_terms) and any(token in key for token in positive_keys):
                if value not in (False, None, 0, "0", "NONE", "NOT_EXECUTED", "NOT_AUTHORIZED", "FORBIDDEN"):
                    raise InvariantError("FORBIDDEN_AUTHORITY_CLAIM", f"{component_id}.{'.'.join(path)}={value!r}")


def _fixture_catalog(control_module: Any) -> Any:
    for name in (
        "_IMPLEMENTATION_FIXTURES",
        "IMPLEMENTATION_FIXTURES",
        "_VALIDATION_FIXTURES",
        "_fixture_catalog",
    ):
        value = getattr(control_module, name, None)
        if isinstance(value, Mapping):
            return value
        if callable(value):
            try:
                result = value()
            except TypeError:
                continue
            if isinstance(result, Mapping):
                return result
    return {}


def _source_fixture_catalog() -> dict[str, dict[str, Any]]:
    """Reconstruct bounded fixtures from fixed, reviewed PR162D source modules."""

    base = "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations"
    modules = {
        "formula": importlib.import_module(f"{base}.formula_seed_library"),
        "algorithm": importlib.import_module(f"{base}.algorithm_seed_library"),
        "quantum": importlib.import_module(f"{base}.quantum_seed_library"),
    }
    result: dict[str, dict[str, Any]] = {}
    closed_decimal_fixtures: dict[str, dict[str, Any]] = {
        "IMPLIED_PROBABILITY": {"price": "0.43", "payout": "1"},
        "PROBABILITY_EDGE": {"p_model": "0.58", "price": "0.43", "payout": "1"},
        "MID_PRICE": {"best_bid": "0.42", "best_ask": "0.46"},
        "SPREAD": {"best_bid": "0.42", "best_ask": "0.46"},
        "RELATIVE_SPREAD": {"best_bid": "0.42", "best_ask": "0.46"},
    }
    for spec in modules["formula"].formula_specs():
        fixture = {
            "inputs": copy.deepcopy(closed_decimal_fixtures.get(spec.formula_id, spec.test_inputs)),
            "context": {},
        }
        result[f"QTT.COMP.FORMULA.{spec.formula_id}"] = fixture
        result[str(spec.callable_ref)] = fixture
    for spec in modules["algorithm"].algorithm_specs():
        fixture = {"inputs": copy.deepcopy(spec.test_inputs), "context": {}}
        result[f"QTT.COMP.ALGORITHM.{spec.algorithm_id}"] = fixture
        result[str(spec.callable_ref)] = fixture
    quantum_groups: dict[str, list[Any]] = defaultdict(list)
    for spec in modules["quantum"].quantum_specs():
        quantum_groups[str(spec.callable_ref)].append(spec)
    for reference, specs in quantum_groups.items():
        representative = sorted(specs, key=lambda value: value.quantum_formulation_id)[0]
        family = representative.build_shape.__name__.removeprefix("build_").upper()
        fixture = {"inputs": copy.deepcopy(representative.test_inputs), "context": {}}
        result[f"QTT.COMP.QUANTUM.{family}"] = fixture
        result[reference] = fixture
    return result


def _fixture_for(record: Mapping[str, Any], catalog: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    component_id = str(record["canonical_component_id"])
    references = [_implementation_ref(entry) for entry in record["definition"]["implementation_versions"]]
    candidate: Any = catalog.get(component_id)
    if candidate is None:
        for reference in references:
            if reference in catalog:
                candidate = catalog[reference]
                break
    if isinstance(candidate, list):
        candidate = candidate[0] if candidate else None
    if isinstance(candidate, Mapping):
        inputs = candidate.get("inputs", candidate.get("fixture_inputs", {}))
        context = candidate.get("context", {})
        if isinstance(inputs, Mapping) and isinstance(context, Mapping):
            return dict(inputs), dict(context)
    raise InvariantError("IMPLEMENTATION_FIXTURE_MISSING", component_id)


def _schema_specs(schema: Any) -> dict[str, Mapping[str, Any]]:
    if isinstance(schema, Mapping):
        return {
            str(name): spec if isinstance(spec, Mapping) else {"type": spec}
            for name, spec in schema.items()
        }
    if isinstance(schema, list):
        result: dict[str, Mapping[str, Any]] = {}
        for entry in schema:
            if not isinstance(entry, Mapping):
                continue
            name = entry.get("name") or entry.get("field") or entry.get("input_name")
            if name:
                result[str(name)] = entry
        return result
    return {}


def _typed_fixture_inputs(record: Mapping[str, Any], inputs: Mapping[str, Any]) -> dict[str, Any]:
    specs = _schema_specs(record["definition"].get("input_schema", {}))
    typed: dict[str, Any] = {}
    for name, value in inputs.items():
        spec = specs.get(str(name), {})
        declared_type = str(spec.get("type", "")).upper()
        safe_source_value = copy.deepcopy(value)
        if (
            isinstance(value, str)
            and any(
                token in declared_type
                for token in ("NUMBER", "NUMERIC", "DECIMAL", "FLOAT", "PROBABILITY")
            )
        ):
            try:
                numeric_value = Decimal(value)
            except InvalidOperation:
                numeric_value = None
            if numeric_value is not None and numeric_value.is_finite():
                safe_source_value = numeric_value
        unit = str(
            spec.get("unit")
            or spec.get("units")
            or spec.get("basis")
            or spec.get("unit_or_basis")
            or ""
        )
        unresolved_unit = (
            not unit
            or unit in {"ANY", "UNSPECIFIED"}
            or any(token in unit for token in ("EXACT_", "SOURCE_DECLARED", "REQUIRED"))
        )
        if unresolved_unit:
            typed[str(name)] = safe_source_value
            continue
        boundary_tokens = {token for token in re.split(r"[^A-Z0-9]+", unit.upper()) if token}
        safe_value = safe_source_value
        if boundary_tokens & {"MONEY", "CURRENCY", "CASH", "PRICE", "FEE", "USD", "CENTS"}:
            if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
                safe_value = format(Decimal(str(value)), "f")
        typed[str(name)] = {
            "value": safe_value,
            "unit": unit,
            "lineage": "PR162D_FIXED_SOURCE_TEST_INPUT",
        }
    return typed


def _closed_fixture_inputs(
    record: Mapping[str, Any],
    records_by_id: Mapping[str, Mapping[str, Any]],
    catalog: Mapping[str, Any],
    stack: tuple[str, ...] = (),
) -> tuple[dict[str, Any], dict[str, Any]]:
    component_id = str(record["canonical_component_id"])
    if component_id in stack:
        raise InvariantError("FIXTURE_REQUIREMENT_CYCLE", " -> ".join((*stack, component_id)))
    inputs, context = _fixture_for(record, catalog)
    merged = dict(inputs)
    for requirement in record["definition"].get("requirements", []):
        if requirement.get("required_or_optional") == "OPTIONAL":
            continue
        target_id = _requirement_target(requirement)
        producer = records_by_id.get(target_id)
        if producer is None:
            raise InvariantError("FIXTURE_REQUIREMENT_MISSING", f"{component_id} -> {target_id}")
        producer_inputs, producer_context = _closed_fixture_inputs(
            producer, records_by_id, catalog, (*stack, component_id)
        )
        merged.pop(str(requirement["consumer_input_name"]), None)
        for name, value in producer_inputs.items():
            def normalized_fixture_lock(candidate: Any) -> Any:
                if (
                    isinstance(candidate, Mapping)
                    and "value" in candidate
                    and any(
                        key in candidate
                        for key in ("unit", "lineage", "as_of", "source")
                    )
                ):
                    candidate = candidate["value"]
                if isinstance(candidate, str):
                    try:
                        numeric = Decimal(candidate)
                    except InvalidOperation:
                        return _canonical_json(candidate)
                    if numeric.is_finite():
                        return ("FINITE_DECIMAL", numeric.normalize())
                if isinstance(candidate, (int, float, Decimal)) and not isinstance(
                    candidate, bool
                ):
                    try:
                        numeric = Decimal(str(candidate))
                    except InvalidOperation:
                        return _canonical_json(candidate)
                    if numeric.is_finite():
                        return ("FINITE_DECIMAL", numeric.normalize())
                return _canonical_json(candidate)

            if (
                name in merged
                and normalized_fixture_lock(merged[name])
                != normalized_fixture_lock(value)
            ):
                raise InvariantError("FIXTURE_INPUT_CONFLICT", f"{component_id}.{name}")
            merged[name] = value
        for name, value in producer_context.items():
            context.setdefault(name, value)
    return _typed_fixture_inputs(record, merged), context


def _assert_finite(value: Any, label: str) -> None:
    plain = _plain(value)
    for path, item in _walk(plain):
        if isinstance(item, bool):
            continue
        if isinstance(item, (int, float, Decimal)):
            numeric = float(item)
            if not math.isfinite(numeric):
                raise InvariantError("NONFINITE_COMPUTE_OUTPUT", f"{label}.{'.'.join(path)}")
    text = _canonical_json(value).lower()
    if any(token in text for token in ('"error":true', '"status":"error"', '"status":"failed"')):
        raise InvariantError("FIXTURE_COMPUTE_ERROR", label)
    output = plain
    if isinstance(plain, Mapping):
        output = plain.get("output_values", plain.get("outputs", plain.get("result", plain)))
    if output in (None, {}, []):
        raise InvariantError("FIXTURE_OUTPUT_EMPTY", label)


def _invoke_implementation_fixtures(
    facade: Any,
    control_module: Any,
    records: Sequence[Mapping[str, Any]],
    deadline: Deadline,
) -> tuple[int, int, int, list[tuple[Mapping[str, Any], Any, Any]]]:
    """Exercise every registered implementation without weakening runtime readiness.

    The five independently closed arithmetic records must execute through the public
    facade.  The remaining source implementations deliberately retain an exact
    oracle/parity blocker: their fixed fixtures exercise the facade-owned allowlist
    entry, while public ``compute`` must fail closed with ``PLAN_NOT_READY``.  This
    keeps source-produced fixture vectors from being relabelled as independent
    oracles merely to make a validation count green.
    """
    catalog = _source_fixture_catalog()
    catalog.update(_fixture_catalog(control_module))
    facade_cases = getattr(facade, "_implementation_fixture_cases", None)
    if callable(facade_cases):
        for case in facade_cases():
            plain_case = _plain(case)
            if not isinstance(plain_case, Mapping):
                continue
            component_id = str(plain_case.get("canonical_component_id", ""))
            reference = str(plain_case.get("callable_or_solver_ref", ""))
            fixture = {
                "inputs": plain_case.get("inputs", {}),
                "context": plain_case.get("context", {}),
            }
            if component_id:
                catalog.setdefault(component_id, fixture)
            if reference:
                catalog.setdefault(reference, fixture)
    facade_allowlist = getattr(facade, "_implementation_allowlist", None)
    if not isinstance(facade_allowlist, Mapping):
        raise InvariantError(
            "FACADE_ALLOWLIST_UNAVAILABLE",
            "registered fixture dispatch cannot be reconstructed",
        )
    invoked: list[tuple[Mapping[str, Any], Any, Any]] = []
    registered_fixture_count = 0
    blocked_public_compute_count = 0
    records_by_id = {str(record["canonical_component_id"]): record for record in records}
    for record in records:
        for requirement in record["definition"].get("requirements", []):
            target = _requirement_target(requirement)
            if target not in records_by_id:
                # Requirement producers may be implementation records outside a
                # caller-provided subset; recover them from the facade snapshot.
                snapshot = getattr(getattr(facade, "_registry", None), "pin", lambda: None)()
                if snapshot is not None:
                    for candidate in snapshot.records:
                        records_by_id.setdefault(str(candidate["canonical_component_id"]), candidate)
                break
    for index, record in enumerate(records):
        if index % 10 == 0:
            deadline.check("implementation_fixtures")
        inputs, supplied_context = _closed_fixture_inputs(record, records_by_id, catalog)
        binding = record["bindings"][0]
        context = _binding_context(binding)
        context.update(supplied_context)
        plan = _operation(facade, "resolve", record["canonical_component_id"], context=context)
        try:
            receipt = _operation(
                facade,
                "compute",
                record["canonical_component_id"],
                inputs=inputs,
                context=context,
            )
        except Exception as exc:
            code = str(getattr(exc, "code", "") or str(exc).split(":", 1)[0])
            readiness = binding.get("readiness", {})
            exact_action = str(binding.get("exact_resolution_action_or_null") or "")
            if (
                code != "PLAN_NOT_READY"
                or readiness.get("oracle") == "PASS"
                or not exact_action
                or exact_action in {"TBD", "SCOPED_GAP"}
            ):
                raise
            selected_version = str(binding.get("selected_implementation_version", ""))
            selected_entry = next(
                (
                    entry
                    for entry in record["definition"].get("implementation_versions", [])
                    if str(entry.get("implementation_version", "")) == selected_version
                ),
                None,
            )
            if not isinstance(selected_entry, Mapping):
                raise InvariantError(
                    "SELECTED_IMPLEMENTATION_MISSING",
                    f"{record['canonical_component_id']}@{selected_version}",
                )
            reference = _implementation_ref(selected_entry)
            implementation = facade_allowlist.get(reference)
            if not callable(implementation):
                raise InvariantError(
                    "REGISTERED_IMPLEMENTATION_NOT_ALLOWLISTED",
                    f"{record['canonical_component_id']}: {reference}",
                )
            raw_inputs = {
                key: value.get("value")
                if isinstance(value, Mapping) and "value" in value
                else value
                for key, value in inputs.items()
            }
            output = implementation(copy.deepcopy(raw_inputs))
            _assert_finite(output, str(record["canonical_component_id"]))
            registered_fixture_count += 1
            blocked_public_compute_count += 1
            continue
        readiness = binding.get("readiness", {})
        if (
            record.get("record_state") != "CANONICAL_ACCEPTED"
            or readiness.get("oracle") != "PASS"
            or any(
                readiness.get(dimension) != "PASS"
                for dimension in (
                    "specification",
                    "implementation",
                    "inputs",
                    "requirements",
                    "context",
                )
            )
        ):
            raise InvariantError(
                "UNVERIFIED_PUBLIC_COMPUTE_EXECUTED",
                str(record["canonical_component_id"]),
            )
        _assert_finite(receipt, str(record["canonical_component_id"]))
        registered_fixture_count += 1
        invoked.append((record, plan, receipt))
    if registered_fixture_count != len(records):
        raise InvariantError(
            "REGISTERED_FIXTURE_INVOCATION_COVERAGE",
            f"{registered_fixture_count}/{len(records)}",
        )
    expected_facade_count = sum(
        record.get("record_state") == "CANONICAL_ACCEPTED"
        and record["bindings"][0].get("readiness", {}).get("oracle") == "PASS"
        and all(
            record["bindings"][0].get("readiness", {}).get(dimension) == "PASS"
            for dimension in (
                "specification",
                "implementation",
                "inputs",
                "requirements",
                "context",
            )
        )
        for record in records
    )
    if len(invoked) != expected_facade_count:
        raise InvariantError(
            "VERIFIED_FACADE_FIXTURE_COVERAGE",
            f"{len(invoked)}/{expected_facade_count}",
        )
    return (
        registered_fixture_count,
        len(invoked),
        blocked_public_compute_count,
        invoked,
    )


def _diagnostic_mapping(facade: Any) -> Mapping[str, Any]:
    merged: dict[str, Any] = {}
    for name in ("_diagnostics", "_counters", "_metrics", "_debug_counters", "_instrumentation"):
        value = getattr(facade, name, None)
        if callable(value):
            try:
                value = value()
            except TypeError:
                continue
        plain = _plain(value)
        if isinstance(plain, Mapping):
            merged.update(plain)
    snapshot = getattr(facade, "_snapshot", None)
    if snapshot is not None:
        plain = _plain(snapshot)
        if isinstance(plain, Mapping):
            for key in ("diagnostics", "counters", "metrics"):
                if isinstance(plain.get(key), Mapping):
                    merged.update(plain[key])
    return merged


def _counter(mapping: Mapping[str, Any], names: Iterable[str]) -> int | None:
    lowered = {str(key).lower(): value for key, value in mapping.items()}
    for name in names:
        if name.lower() in lowered:
            try:
                return int(lowered[name.lower()])
            except (TypeError, ValueError):
                return None
    return None


def _validate_runtime_counters(facade: Any) -> tuple[int, int, int]:
    diagnostics = _diagnostic_mapping(facade)
    reads = _counter(
        diagnostics,
        (
            "runtime_registry_file_reads_after_initialization",
            "registry_file_reads_after_initialization",
            "post_init_registry_file_reads",
            "runtime_registry_file_reads",
        ),
    )
    scans = _counter(
        diagnostics,
        ("per_request_full_registry_iterations", "full_registry_scans", "runtime_full_registry_scans"),
    )
    unrelated = _counter(
        diagnostics,
        ("unrelated_component_executions", "unrelated_computation_executions"),
    )
    if reads is None or scans is None or unrelated is None:
        raise InvariantError("RUNTIME_COUNTERS_MISSING", f"keys={sorted(diagnostics)[:50]}")
    if reads or scans or unrelated:
        raise InvariantError("RUNTIME_COMPLEXITY_VIOLATION", f"reads={reads}, scans={scans}, unrelated={unrelated}")
    return reads, scans, unrelated


def _closure(graph: Mapping[str, set[str]], root: str) -> set[str]:
    result: set[str] = set()
    stack = [root]
    while stack:
        node = stack.pop()
        if node in result:
            continue
        result.add(node)
        stack.extend(graph.get(node, ()))
    return result


def _plan_component_ids(plan: Any) -> list[str]:
    plain = _plain(plan)
    values: list[str] = []
    for path, value in _walk(plain):
        key = path[-1].lower() if path else ""
        if key in {"canonical_component_id", "component_id"} and isinstance(value, str):
            values.append(value)
        elif key in {"topological_execution_order", "execution_order", "component_ids"} and isinstance(value, list):
            values.extend(str(item) for item in value if isinstance(item, str))
    return list(dict.fromkeys(values))


def _validate_selected_subgraph(
    invoked: Sequence[tuple[Mapping[str, Any], Any, Any]], graph: Mapping[str, set[str]], registry_size: int
) -> tuple[int, int]:
    candidates = [item for item in invoked if graph.get(str(item[0]["canonical_component_id"]))]
    if not candidates:
        raise InvariantError("CLOSED_STACK_FIXTURE_MISSING", "no implementation fixture has requirements")
    record, plan, receipt = max(candidates, key=lambda item: len(_closure(graph, str(item[0]["canonical_component_id"]))))
    root = str(record["canonical_component_id"])
    expected = _closure(graph, root)
    observed = set(_plan_component_ids(plan))
    if not expected <= observed or observed - expected:
        raise InvariantError("SELECTED_SUBGRAPH_MISMATCH", f"expected={sorted(expected)}, observed={sorted(observed)}")
    if len(observed) >= registry_size:
        raise InvariantError("FULL_REGISTRY_EXECUTION", f"selected={len(observed)}, registry={registry_size}")
    receipt_text = _canonical_json(receipt)
    for component_id in expected:
        if component_id not in receipt_text:
            raise InvariantError("RECEIPT_GRAPH_INCOMPLETE", component_id)
    return len(observed), sum(len(graph[node]) for node in expected)


def _runtime_error_code(function: Callable[[], Any]) -> str:
    try:
        function()
    except Exception as exc:
        code = getattr(exc, "code", None)
        if code:
            return str(code)
        text = str(exc)
        return text.split(":", 1)[0]
    raise InvariantError("RUNTIME_DEFECT_NOT_REJECTED", "operation returned normally")


def _common_subgraph_probe(facade_class: type[Any], template: Mapping[str, Any]) -> dict[str, Any]:
    counters: Counter[str] = Counter()

    def implementation(name: str, output_name: str, input_names: Sequence[str]) -> Callable[[dict[str, Any]], dict[str, Any]]:
        def run(inputs: dict[str, Any]) -> dict[str, Any]:
            counters[name] += 1
            values = [Decimal(str(inputs[input_name])) for input_name in input_names]
            if name == "shared":
                result = values[0]
            elif name == "left":
                result = values[0] + Decimal("1")
            elif name == "right":
                result = values[0] + Decimal("2")
            elif name == "root":
                result = sum(values, Decimal("0"))
            else:
                result = Decimal("999")
            return {output_name: result}

        return run

    refs = {
        "shared": "qtt.computation_control.validation:shared",
        "left": "qtt.computation_control.validation:left",
        "right": "qtt.computation_control.validation:right",
        "root": "qtt.computation_control.validation:root",
        "unrelated": "qtt.computation_control.validation:unrelated",
        "fallback_primary": "qtt.computation_control.validation:fallback_primary",
        "fallback_alternative": "qtt.computation_control.validation:fallback_alternative",
        "fallback_root": "qtt.computation_control.validation:fallback_root",
    }

    def failing_primary(inputs: dict[str, Any]) -> dict[str, Any]:
        del inputs
        counters["fallback_primary"] += 1
        raise RuntimeError("VALIDATOR_INJECTED_PRIMARY_FAILURE")

    def working_fallback(inputs: dict[str, Any]) -> dict[str, Any]:
        counters["fallback_alternative"] += 1
        return {"upstream_value": Decimal(str(inputs["base_value"])) + Decimal("6")}

    def fallback_root(inputs: dict[str, Any]) -> dict[str, Any]:
        counters["fallback_root"] += 1
        return {"result": Decimal(str(inputs["upstream_value"]))}

    allowlist = {
        refs["shared"]: implementation("shared", "shared_value", ("base_value",)),
        refs["left"]: implementation("left", "left_value", ("shared_value",)),
        refs["right"]: implementation("right", "right_value", ("shared_value",)),
        refs["root"]: implementation("root", "result", ("left_value", "right_value")),
        refs["unrelated"]: implementation("unrelated", "unused", ()),
        refs["fallback_primary"]: failing_primary,
        refs["fallback_alternative"]: working_fallback,
        refs["fallback_root"]: fallback_root,
    }

    def requirement(target: str, producer: str, consumer: str) -> dict[str, Any]:
        return {
            "required_component_id_or_source_selector": target,
            "required_semantic_version_constraint": "1.0",
            "requirement_role": f"{target}::{producer}->{consumer}",
            "required_or_optional": "REQUIRED",
            "producer_output_name": producer,
            "consumer_input_name": consumer,
            "unit_or_basis_conversion": "IDENTITY",
            "timing_and_freshness_constraint": "SAME_REQUEST",
            "activation_condition": "ALWAYS",
            "fallback_component_id_or_null": None,
            "failure_behavior": "FAIL_CLOSED",
        }

    def record(
        token: str,
        inputs: Sequence[str],
        output: str,
        requirements: Sequence[Mapping[str, Any]],
        *,
        memoizable: bool = True,
    ) -> dict[str, Any]:
        value = copy.deepcopy(template)
        component_id = f"QTT.COMP.VALIDATION.MEMO.{token.upper()}"
        value["canonical_component_id"] = component_id
        value["semantic_version"] = "1.0"
        value["record_state"] = "CANONICAL_ACCEPTED"
        value["origin_cohorts"] = ["VALIDATOR_SYNTHETIC_MEMOIZATION"]
        definition = value["definition"]
        definition["display_name"] = f"Memoization {token}"
        definition["description"] = "Independent selected-subgraph and invocation-key probe."
        definition["component_kind"] = "DETERMINISTIC_TRANSFORM"
        definition["complete_mathematical_or_procedural_definition"] = f"VALIDATOR::{token}"
        definition["input_schema"] = [
            {"name": name, "type": "decimal", "unit": "DIMENSIONLESS", "required": True}
            for name in inputs
        ]
        definition["output_schema"] = [
            {"name": output, "type": "decimal", "unit": "DIMENSIONLESS", "required": True}
        ]
        definition["units_and_bases"] = {
            "inputs": {name: "DIMENSIONLESS" for name in inputs},
            "outputs": {output: "DIMENSIONLESS"},
        }
        definition["requirements"] = [dict(item) for item in requirements]
        definition["implementation_versions"] = [
            {
                "implementation_version": "1.0",
                "callable_or_solver_ref": refs[token],
                "code_owner": "CONTROL1_INDEPENDENT_VALIDATOR",
                "supported_platforms": ["WINDOWS", "LINUX"],
                "pinned_dependencies": ["PYTHON_STDLIB_DECIMAL"],
                "determinism_seed_policy": "DETERMINISTIC_NO_SEED",
                "precision": "DECIMAL",
                "latency_class": "PRETRADE_BOUNDED",
                "security_state": "LOCAL_ALLOWLIST_ONLY",
                "memoizable_flag": memoizable,
                "memoizable_proof_basis": "PURE_SIDE_EFFECT_FREE_VALIDATOR_CLOSURE",
                "fallback": "FAIL_CLOSED",
                "implementation_inventory_class": "FORMULA",
            }
        ]
        definition["oracle_and_test_refs"] = ["tools/validate_pr169_qku_comp_control1.py"]
        definition["equivalence_proof_refs"] = []
        value["uses"] = {
            "decision_roles": ["INTERNAL_SUPPORT"],
            "decision_outputs": [output],
            "market_family_tags": ["VALIDATOR_SYNTHETIC"],
            "qku_role_bindings": [],
            "consumer_class_tags": ["CONTROL1_INDEPENDENT_VALIDATOR"],
        }
        binding = copy.deepcopy(value["bindings"][0])
        binding["binding_id"] = f"BINDING.VALIDATION.MEMO.{token.upper()}"
        binding["market"] = "VALIDATOR_SYNTHETIC"
        binding["venue"] = "LOCAL_FIXTURE"
        binding["context_selector"] = {"context_family": "VALIDATOR_MEMOIZATION"}
        binding["supported_modes"] = ["TEST_VECTOR"]
        binding["mode_state"] = {
            "TEST_VECTOR": {
                "evidence": "FIXTURE",
                "authorization": "NOT_ELIGIBLE",
                "activation_state": "INACTIVE_NONLIVE",
            }
        }
        binding["selected_implementation_version"] = "1.0"
        binding["input_source_bindings"] = [
            {"input_name": name, "source": "TYPED_VALIDATOR_INPUT_OR_REQUIREMENT"} for name in inputs
        ]
        binding["readiness"] = {
            "specification": "PASS",
            "implementation": "PASS",
            "inputs": "PASS",
            "requirements": "PASS",
            "oracle": "PASS",
            "context": "PASS",
            "evidence": "FIXTURE",
            "authorization": "NOT_ELIGIBLE",
        }
        binding["derived_state"] = "STACK_READY"
        binding["exact_resolution_action_or_null"] = None
        binding["evidence_summary"] = {
            "evidence_ceiling": "FIXTURE",
            "empirical_market_evidence": False,
            "limitations": ["VALIDATOR_SYNTHETIC_ONLY"],
        }
        binding["activation_state"] = "INACTIVE_NONLIVE"
        value["bindings"] = [binding]
        value["provenance"] = [
            {
                "source_artifact_ref": "tools/validate_pr169_qku_comp_control1.py",
                "source_row_ref": token,
                "source_local_identity_or_name": token,
                "source_fields_consumed": ["synthetic_probe"],
                "source_relation": "VALIDATION_ONLY",
                "canonical_target_ref": component_id,
                "proof_refs": ["tools/validate_pr169_qku_comp_control1.py"],
            }
        ]
        value["relations"] = []
        return value

    shared_id = "QTT.COMP.VALIDATION.MEMO.SHARED"
    left_id = "QTT.COMP.VALIDATION.MEMO.LEFT"
    right_id = "QTT.COMP.VALIDATION.MEMO.RIGHT"
    records = [
        record("shared", ("base_value",), "shared_value", ()),
        record("left", ("shared_value",), "left_value", (requirement(shared_id, "shared_value", "shared_value"),)),
        record("right", ("shared_value",), "right_value", (requirement(shared_id, "shared_value", "shared_value"),)),
        record(
            "root",
            ("left_value", "right_value"),
            "result",
            (
                requirement(left_id, "left_value", "left_value"),
                requirement(right_id, "right_value", "right_value"),
            ),
        ),
        record("unrelated", (), "unused", ()),
    ]
    trusted_memoizable_refs = {refs["shared"]}
    facade = facade_class(
        records=records,
        implementation_allowlist=allowlist,
        trusted_memoizable_refs=trusted_memoizable_refs,
    )
    context = {
        "market": "VALIDATOR_SYNTHETIC",
        "venue": "LOCAL_FIXTURE",
        "context_family": "VALIDATOR_MEMOIZATION",
    }
    typed_one = {"base_value": {"value": "1", "unit": "DIMENSIONLESS", "lineage": "VALIDATOR_INPUT_1"}}
    first = _plain(facade.compute("QTT.COMP.VALIDATION.MEMO.ROOT", typed_one, context, mode="TEST_VECTOR"))
    if counters != Counter({"shared": 1, "left": 1, "right": 1, "root": 1}):
        raise InvariantError("COMMON_SUBGRAPH_MEMOIZATION", repr(counters))
    if first.get("shared_invocations_reused") != 1 or first.get("nodes_executed") != 4:
        raise InvariantError("COMMON_SUBGRAPH_MEMOIZATION", repr(first))
    if counters["unrelated"]:
        raise InvariantError("UNRELATED_COMPONENT_EXECUTION", repr(counters))

    typed_two = {"base_value": {"value": "2", "unit": "DIMENSIONLESS", "lineage": "VALIDATOR_INPUT_2"}}
    second = _plain(facade.compute("QTT.COMP.VALIDATION.MEMO.ROOT", typed_two, context, mode="TEST_VECTOR"))
    if counters["shared"] != 2 or first.get("outputs") == second.get("outputs"):
        raise InvariantError("DIFFERENT_INPUT_UNSAFE_REUSE", repr(counters))

    nonmemo_records = copy.deepcopy(records)
    nonmemo_records[0]["definition"]["implementation_versions"][0]["memoizable_flag"] = False
    counters.clear()
    nonmemo = facade_class(
        records=nonmemo_records,
        implementation_allowlist=allowlist,
        trusted_memoizable_refs=trusted_memoizable_refs,
    )
    nonmemo_receipt = _plain(
        nonmemo.compute("QTT.COMP.VALIDATION.MEMO.ROOT", typed_one, context, mode="TEST_VECTOR")
    )
    if counters["shared"] != 2 or nonmemo_receipt.get("shared_invocations_reused") != 0:
        raise InvariantError("NONMEMOIZABLE_NODE_REUSED", repr(counters))

    missing_unit = _runtime_error_code(
        lambda: facade.compute(
            "QTT.COMP.VALIDATION.MEMO.ROOT",
            {"base_value": "1"},
            context,
            mode="TEST_VECTOR",
        )
    )
    if missing_unit != "MISSING_UNIT":
        raise InvariantError("RUNTIME_DEFECT_WRONG_REASON", f"missing unit -> {missing_unit}")
    stale = _runtime_error_code(
        lambda: facade.compute(
            "QTT.COMP.VALIDATION.MEMO.ROOT",
            {
                "base_value": {
                    "value": "1",
                    "unit": "DIMENSIONLESS",
                    "lineage": "VALIDATOR_STALE",
                    "as_of": "2000-01-01T00:00:00Z",
                }
            },
            {
                **context,
                "request_time": "2000-01-01T00:00:10Z",
                "freshness_ttl_seconds": 1,
            },
            mode="TEST_VECTOR",
        )
    )
    if stale != "STALE_INPUT":
        raise InvariantError("RUNTIME_DEFECT_WRONG_REASON", f"stale input -> {stale}")
    nonfinite = _runtime_error_code(
        lambda: facade.compute(
            "QTT.COMP.VALIDATION.MEMO.ROOT",
            {"base_value": {"value": float("inf"), "unit": "DIMENSIONLESS", "lineage": "VALIDATOR_NONFINITE"}},
            context,
            mode="TEST_VECTOR",
        )
    )
    if nonfinite != "NONFINITE_VALUE":
        raise InvariantError("RUNTIME_DEFECT_WRONG_REASON", f"nonfinite input -> {nonfinite}")

    ambiguous_records = copy.deepcopy(records)
    extra_binding = copy.deepcopy(ambiguous_records[-1]["bindings"][0])
    extra_binding["binding_id"] = "BINDING.VALIDATION.MEMO.UNRELATED.ALTERNATE"
    ambiguous_records[-1]["bindings"].append(extra_binding)
    ambiguous_code = _runtime_error_code(
        lambda: facade_class(
            records=ambiguous_records, implementation_allowlist=allowlist
        ).resolve("QTT.COMP.VALIDATION.MEMO.UNRELATED", context)
    )
    if ambiguous_code not in {
        "AMBIGUOUS_CONTEXT_BINDING",
        "OVERLAPPING_BINDING_SELECTORS",
        "AMBIGUOUS_BINDING_SELECTOR",
    }:
        raise InvariantError("RUNTIME_DEFECT_WRONG_REASON", f"ambiguous binding -> {ambiguous_code}")

    overlap_records = copy.deepcopy(records)
    overlap_binding = overlap_records[-1]["bindings"][0]
    overlap_binding["context_selector"] = {
        "context_family": "VALIDATOR_MEMOIZATION",
        "left_wildcard": "ANY",
    }
    alternate_overlap = copy.deepcopy(overlap_binding)
    alternate_overlap["binding_id"] = "BINDING.VALIDATION.MEMO.UNRELATED.OVERLAP"
    alternate_overlap["context_selector"] = {
        "context_family": "VALIDATOR_MEMOIZATION",
        "right_wildcard": "ANY",
    }
    overlap_records[-1]["bindings"].append(alternate_overlap)
    overlap_load_code = _runtime_error_code(
        lambda: facade_class(records=overlap_records, implementation_allowlist=allowlist)
    )
    if overlap_load_code not in {
        "OVERLAPPING_BINDING_SELECTORS",
        "AMBIGUOUS_BINDING_SELECTOR",
    }:
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"overlapping selector load -> {overlap_load_code}",
        )

    missing_mode_records = copy.deepcopy(records)
    missing_mode_records[-1]["bindings"][0]["mode_state"] = {}
    missing_mode_code = _runtime_error_code(
        lambda: facade_class(
            records=missing_mode_records, implementation_allowlist=allowlist
        )
    )
    if missing_mode_code not in {
        "MODE_STATE_MISSING",
        "MODE_STATE_COVERAGE_MISSING",
        "SUPPORTED_MODE_STATE_MISSING",
    }:
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"missing mode_state load -> {missing_mode_code}",
        )

    bulky_evidence_records = copy.deepcopy(records)
    bulky_evidence_records[-1]["bindings"][0]["evidence_summary"] = {
        "observations": {
            f"row_{index:05d}": {"value": index} for index in range(5_000)
        }
    }
    bulky_evidence_code = _runtime_error_code(
        lambda: facade_class(
            records=bulky_evidence_records, implementation_allowlist=allowlist
        )
    )
    if bulky_evidence_code not in {
        "EMBEDDED_BULK_EVIDENCE",
        "BULK_EVIDENCE_PAYLOAD",
    }:
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"generic bulk evidence load -> {bulky_evidence_code}",
        )

    paper_record = copy.deepcopy(records[-1])
    paper_binding = paper_record["bindings"][0]
    paper_binding["supported_modes"] = ["PAPER"]
    paper_binding["mode_state"] = {
        "PAPER": {
            "evidence": "NONE",
            "authorization": "NOT_ELIGIBLE",
            "activation_state": "INACTIVE_NONLIVE",
        }
    }
    paper_binding["readiness"]["evidence"] = "NONE"
    paper_binding["readiness"]["authorization"] = "NOT_ELIGIBLE"
    paper_binding["activation_state"] = "INACTIVE_NONLIVE"
    paper_binding["exact_resolution_action_or_null"] = (
        "MISSING_PAPER_AUTHORIZATION: validator synthetic binding"
    )
    paper_facade = facade_class(records=[paper_record], implementation_allowlist=allowlist)
    paper_context = _binding_context(paper_binding)
    paper_status = _plain(
        paper_facade.status(
            paper_record["canonical_component_id"],
            paper_context,
        )
    )
    paper_blockers = {str(value) for value in paper_status.get("blockers", ())}
    if (
        paper_status.get("authorization") != "NOT_ELIGIBLE"
        or paper_status.get("mode_state", {}).get("PAPER", {}).get("authorization")
        != "NOT_ELIGIBLE"
        or paper_status.get("derived_state") == "AUTHORIZED"
        or not any(value.startswith("MODE_NOT_AUTHORIZED: PAPER") for value in paper_blockers)
    ):
        raise InvariantError(
            "NOT_ELIGIBLE_STATUS_UNTRUTHFUL", repr(paper_status)
        )

    primary_id = "QTT.COMP.VALIDATION.MEMO.FALLBACK_PRIMARY"
    fallback_id = "QTT.COMP.VALIDATION.MEMO.FALLBACK_ALTERNATIVE"
    fallback_requirement = requirement(
        primary_id, "upstream_value", "upstream_value"
    )
    fallback_requirement["fallback_component_id_or_null"] = fallback_id
    fallback_requirement["failure_behavior"] = "USE_FALLBACK_FAIL_CLOSED"
    fallback_records = [
        record(
            "fallback_primary",
            ("base_value",),
            "upstream_value",
            (),
            memoizable=False,
        ),
        record(
            "fallback_alternative",
            ("base_value",),
            "upstream_value",
            (),
            memoizable=False,
        ),
        record(
            "fallback_root",
            ("base_value", "upstream_value"),
            "result",
            (fallback_requirement,),
            memoizable=False,
        ),
    ]
    counters.clear()
    fallback_facade = facade_class(
        records=fallback_records, implementation_allowlist=allowlist
    )
    fallback_receipt = _plain(
        fallback_facade.compute(
            "QTT.COMP.VALIDATION.MEMO.FALLBACK_ROOT",
            {
                "base_value": {
                    "value": "1",
                    "unit": "DIMENSIONLESS",
                    "lineage": "VALIDATOR_FALLBACK_INPUT",
                }
            },
            context,
            mode="TEST_VECTOR",
        )
    )
    if (
        fallback_receipt.get("fallback_used") is not True
        or fallback_receipt.get("outputs", {}).get("result") not in {"7", 7, Decimal("7")}
        or counters["fallback_primary"] != 1
        or counters["fallback_alternative"] != 1
        or counters["fallback_root"] != 1
    ):
        raise InvariantError(
            "RUNTIME_REQUIREMENT_FALLBACK",
            f"receipt={fallback_receipt}, counters={dict(counters)}",
        )
    receipt_generation = fallback_receipt.get("generation")
    fallback_generations = {
        entry.get("receipt_generation")
        for entry in fallback_receipt.get("requirement_receipts", ())
        if isinstance(entry, Mapping)
    }
    if not fallback_generations or fallback_generations != {receipt_generation}:
        raise InvariantError(
            "MIXED_FALLBACK_SNAPSHOT_GENERATION",
            f"root={receipt_generation!r}, requirements={sorted(fallback_generations, key=repr)!r}",
        )
    fallback_entries = [
        entry
        for entry in fallback_receipt.get("requirement_receipts", ())
        if isinstance(entry, Mapping)
        and entry.get("component_id") == fallback_id
    ]
    if len(fallback_entries) != 1:
        raise InvariantError(
            "FALLBACK_INPUT_PROJECTION_RECEIPT_MISSING", repr(fallback_receipt)
        )
    return {
        "memoizable_shared_calls": 1,
        "memoizable_reuse_count": 1,
        "different_request_shared_calls": 2,
        "nonmemoizable_shared_calls": 2,
        "unrelated_calls": 0,
        "runtime_defects": {
            "missing_unit": missing_unit,
            "stale": stale,
            "nonfinite": nonfinite,
            "ambiguous_binding": ambiguous_code,
            "overlapping_selector_load": overlap_load_code,
            "missing_mode_state_load": missing_mode_code,
            "bulk_evidence_load": bulky_evidence_code,
            "not_eligible_status": "TRUTHFUL",
            "runtime_requirement_fallback": "PASS",
            "fallback_input_projection": "PASS",
            "fallback_snapshot_generation": receipt_generation,
        },
    }


def _find_function(module: Any, names: Sequence[str]) -> Callable[..., Any] | None:
    for name in names:
        function = getattr(module, name, None)
        if callable(function):
            return function
    return None


def _invoke_records_function(function: Callable[..., Any], records: Sequence[Mapping[str, Any]]) -> Any:
    signature = inspect.signature(function)
    for key in ("records", "registry_records", "rows"):
        if key in signature.parameters:
            return function(**{key: records})
    return function(records)


def _derive_delta(control_module: Any, before: Sequence[Mapping[str, Any]], after: Sequence[Mapping[str, Any]]) -> Any:
    function = _find_function(
        control_module,
        ("_derive_registry_update", "_derive_registry_update_v1", "_build_registry_update", "_diff_registry"),
    )
    if function is None:
        raise InvariantError("DELTA_HELPER_MISSING", "control.py must expose a private mechanism helper")
    signature = inspect.signature(function)
    kwargs: dict[str, Any] = {}
    for key in signature.parameters:
        if key in {"before", "base", "old_records", "accepted_records", "base_records"}:
            kwargs[key] = before
        elif key in {"after", "candidate", "new_records", "candidate_records"}:
            kwargs[key] = after
    if len(kwargs) >= 2:
        return function(**kwargs)
    return function(before, after)


def _delta_field(delta: Any, name: str) -> set[str]:
    plain = _plain(delta)
    if not isinstance(plain, Mapping):
        return set()
    value = plain.get(name, [])
    return {str(item) for item in value} if isinstance(value, list) else set()


def _validate_delta(
    control_module: Any,
    records: Sequence[Mapping[str, Any]],
    reverse: Mapping[str, set[str]],
) -> tuple[Any, list[Mapping[str, Any]], str]:
    target_index = next(
        (
            index
            for index, record in enumerate(records)
            if record.get("bindings") and record.get("record_state") == "CANONICAL_ACCEPTED"
        ),
        None,
    )
    if target_index is None:
        raise InvariantError("DELTA_FIXTURE_MISSING", "no accepted bound record")
    candidate = list(records)
    target = copy.deepcopy(records[target_index])
    candidate[target_index] = target
    component_id = str(target["canonical_component_id"])
    binding = target["bindings"][0]
    policy = binding["selected_parameter_policy"]
    if isinstance(policy, Mapping):
        policy = dict(policy)
        policy["validation_probe_revision"] = int(policy.get("validation_probe_revision", 0)) + 1
        binding["selected_parameter_policy"] = policy
    else:
        binding["selected_parameter_policy"] = {"policy_ref": policy, "validation_probe_revision": 1}
    delta = _derive_delta(control_module, records, candidate)
    changed = _delta_field(delta, "changed_component_ids")
    added = _delta_field(delta, "added_component_ids")
    retired = _delta_field(delta, "retired_component_ids")
    changed_bindings = _delta_field(delta, "changed_binding_ids")
    dependents = _delta_field(delta, "affected_dependent_ids")
    expected_dependents: set[str] = set()
    queue = deque(reverse.get(component_id, ()))
    while queue:
        node = queue.popleft()
        if node in expected_dependents:
            continue
        expected_dependents.add(node)
        queue.extend(reverse.get(node, ()))
    if changed != {component_id} or added or retired:
        raise InvariantError("DELTA_EXACTNESS", f"changed={changed}, added={added}, retired={retired}")
    expected_binding_labels = {
        str(binding["binding_id"]),
        f"{component_id}::{binding['binding_id']}",
    }
    if not (changed_bindings & expected_binding_labels) or dependents != expected_dependents:
        raise InvariantError(
            "DELTA_EXACTNESS",
            f"changed_bindings={changed_bindings}, dependents={dependents}, expected={expected_dependents}",
        )
    return delta, candidate, component_id


def _build_indexes(control_module: Any, records: Sequence[Mapping[str, Any]]) -> Any:
    function = _find_function(
        control_module,
        ("_build_registry_snapshot", "_build_snapshot", "_build_index_set", "_build_indexes"),
    )
    if function is None:
        raise InvariantError("INDEX_HELPER_MISSING", "control.py must expose private snapshot/index construction")
    signature = inspect.signature(function)
    kwargs: dict[str, Any] = {}
    for key in signature.parameters:
        if key in {"records", "registry_records", "rows"}:
            kwargs[key] = records
        elif key == "generation":
            kwargs[key] = 1
        elif key == "layout":
            kwargs[key] = "IN_MEMORY_VALIDATION"
        elif key in {"shard_count", "registry_file_reads"}:
            kwargs[key] = 0
    return function(**kwargs) if kwargs else function(records)


def _refresh_indexes(
    control_module: Any,
    base: Any,
    records: Sequence[Mapping[str, Any]],
    delta: Any,
    *,
    verify_full_rebuild: bool = False,
) -> Any:
    function = _find_function(
        control_module,
        (
            "_refresh_index_set",
            "_refresh_indexes",
            "_incremental_snapshot",
            "_apply_registry_update_to_snapshot",
            "_apply_registry_update",
        ),
    )
    if function is None:
        raise InvariantError("INCREMENTAL_INDEX_HELPER_MISSING", "control.py must expose private incremental refresh")
    signature = inspect.signature(function)
    kwargs: dict[str, Any] = {}
    for key in signature.parameters:
        if key in {"base", "snapshot", "indexes", "old_snapshot"}:
            kwargs[key] = base
        elif key in {"records", "candidate_records", "new_records"}:
            kwargs[key] = records
        elif key in {"delta", "update", "registry_update"}:
            kwargs[key] = delta
        elif key == "verify_full_rebuild":
            kwargs[key] = verify_full_rebuild
    if len(kwargs) >= 2:
        result = function(**kwargs)
    else:
        result = function(base, records, delta)
    if isinstance(result, tuple) and result and hasattr(result[0], "indexes"):
        if verify_full_rebuild:
            stats = _plain(result[1]) if len(result) > 1 else None
            if not isinstance(stats, Mapping) or stats.get("full_rebuild_parity") is not True:
                raise InvariantError(
                    "INCREMENTAL_INDEX_FULL_REBUILD_PROOF_MISSING", repr(stats)
                )
        return result[0]
    if verify_full_rebuild and "verify_full_rebuild" not in signature.parameters:
        raise InvariantError(
            "INCREMENTAL_INDEX_FULL_REBUILD_PROOF_MISSING",
            f"{function.__name__} has no verify_full_rebuild mechanism",
        )
    return result


def _index_projection(value: Any) -> Any:
    plain = _plain(value)
    if isinstance(plain, Mapping):
        ignored = {
            "generation",
            "created_at",
            "built_at_monotonic",
            "diagnostics",
            "metrics",
            "counters",
        }
        return {
            key: _index_projection(child)
            for key, child in sorted(plain.items())
            if key.lower() not in ignored
        }
    if isinstance(plain, list):
        converted = [_index_projection(child) for child in plain]
        try:
            return sorted(converted, key=_canonical_json)
        except TypeError:
            return converted
    return plain


def _validate_index_parity(control_module: Any, records: Sequence[Mapping[str, Any]], candidate: Sequence[Mapping[str, Any]], delta: Any) -> None:
    if len(records) > 1_000:
        template = next(record for record in records if record.get("bindings"))
        records = _synthetic_records(template, 256)
        candidate = list(records)
        changed = copy.deepcopy(records[127])
        changed["bindings"][0]["selected_parameter_policy"] = {
            **dict(changed["bindings"][0]["selected_parameter_policy"]),
            "validation_probe_revision": 1,
        }
        candidate[127] = changed
        delta = _derive_delta(control_module, records, candidate)
    base = _build_indexes(control_module, records)
    incremental = _refresh_indexes(
        control_module,
        base,
        candidate,
        delta,
        verify_full_rebuild=True,
    )
    full = _build_indexes(control_module, candidate)
    if _canonical_json(_index_projection(incremental)) != _canonical_json(_index_projection(full)):
        raise InvariantError("INCREMENTAL_INDEX_PARITY", "incremental refresh differs from full rebuild")
    repeated = _refresh_indexes(
        control_module,
        base,
        candidate,
        delta,
        verify_full_rebuild=True,
    )
    if _canonical_json(_index_projection(repeated)) != _canonical_json(_index_projection(incremental)):
        raise InvariantError("DELTA_IDEMPOTENCE", "reapplying RegistryUpdateV1 changes indexes")


def _write_jsonl(path: Path, records: Sequence[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in sorted(records, key=lambda row: (str(row["canonical_component_id"]), str(row["semantic_version"]))):
            handle.write(_canonical_json(record))
            handle.write("\n")


def _write_layout_fallback(directory: Path, records: Sequence[Mapping[str, Any]], sharded: bool) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    ordered = sorted(records, key=lambda row: (str(row["canonical_component_id"]), str(row["semantic_version"])))
    if not sharded:
        _write_jsonl(directory / "registry.jsonl", ordered)
        return
    partitions: list[dict[str, Any]] = []
    width = max(1, min(500, math.ceil(len(ordered) / 4)))
    for index, start in enumerate(range(0, len(ordered), width)):
        subset = ordered[start : start + width]
        name = f"registry.part-{index:04d}.jsonl"
        _write_jsonl(directory / name, subset)
        partitions.append(
            {
                "file_name": name,
                "canonical_id_start": subset[0]["canonical_component_id"],
                "canonical_id_end": subset[-1]["canonical_component_id"],
                "row_count": len(subset),
            }
        )
    manifest = {
        "registry_schema_version": "1.0",
        "layout": "DETERMINISTIC_SHARDED_JSONL",
        "partition_policy": {"kind": "STABLE_CANONICAL_ID_PREFIX_AND_RANGE"},
        "row_count": len(ordered),
        "partitions": [
            {
                "file": row["file_name"],
                "range_start": row["canonical_id_start"],
                "range_end": row["canonical_id_end"],
                "row_count": row["row_count"],
            }
            for row in partitions
        ],
    }
    (directory / "registry.manifest.json").write_text(_canonical_json(manifest) + "\n", encoding="utf-8", newline="\n")


def _write_layout(control_module: Any, directory: Path, records: Sequence[Mapping[str, Any]], sharded: bool) -> None:
    function = _find_function(
        control_module,
        ("_write_logical_registry", "_write_registry_layout", "_write_registry_records"),
    )
    if function is None:
        _write_layout_fallback(directory, records, sharded)
        return
    signature = inspect.signature(function)
    kwargs: dict[str, Any] = {}
    for key in signature.parameters:
        if key in {"records", "rows", "registry_records"}:
            kwargs[key] = records
        elif key in {"artifact_dir", "registry_root", "directory", "out_dir", "path"}:
            kwargs[key] = directory
        elif key in {"force_sharded", "sharded"}:
            kwargs[key] = sharded
        elif key in {"force_layout", "layout"}:
            kwargs[key] = "sharded" if sharded else "single"
    try:
        function(**kwargs)
    except TypeError:
        _write_layout_fallback(directory, records, sharded)


def _synthetic_records(template: Mapping[str, Any], count: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    base_definition = copy.deepcopy(template["definition"])
    base_definition["implementation_versions"] = []
    base_definition["oracle_and_test_refs"] = ["tests/pr169_qku_comp_control1/test_control1.py"]
    base_definition["equivalence_proof_refs"] = []
    base_definition["component_kind"] = "DETERMINISTIC_TRANSFORM"
    base_definition["input_schema"] = {"value": {"type": "integer", "unit": "dimensionless"}}
    base_definition["output_schema"] = {"value": {"type": "integer", "unit": "dimensionless"}}
    base_definition["units_and_bases"] = {"input": "dimensionless", "output": "dimensionless"}
    for index in range(count):
        component_id = f"QTT.COMP.SCALE.NODE_{index:08d}"
        definition = copy.deepcopy(base_definition)
        definition["display_name"] = f"Scale node {index}"
        definition["description"] = "Bounded deterministic synthetic index/resolve probe."
        definition["complete_mathematical_or_procedural_definition"] = "output.value = input.value"
        requirements: list[dict[str, Any]] = []
        if index % 64 and index > 0:
            requirements.append(
                {
                    "required_component_id_or_source_selector": f"QTT.COMP.SCALE.NODE_{index-1:08d}",
                    "required_semantic_version_constraint": "1.0",
                    "requirement_role": "SCALE_PREDECESSOR",
                    "required_or_optional": "REQUIRED",
                    "producer_output_name": "value",
                    "consumer_input_name": "value",
                    "unit_or_basis_conversion": "IDENTITY",
                    "timing_and_freshness_constraint": "SAME_REQUEST",
                    "activation_condition": "ALWAYS",
                    "fallback_component_id_or_null": None,
                    "failure_behavior": "FAIL_CLOSED",
                }
            )
        definition["requirements"] = requirements
        binding = copy.deepcopy(template["bindings"][0])
        binding["binding_id"] = f"BINDING.SCALE.NODE.{index:08d}"
        binding["market"] = "SYNTHETIC_SCALE"
        binding["venue"] = "LOCAL_FIXTURE"
        binding["context_selector"] = {"context_family": "VALIDATOR_SCALE"}
        binding["qku_binding_selector_or_null"] = None
        binding["supported_modes"] = ["TEST_VECTOR"]
        binding["mode_state"] = {
            "TEST_VECTOR": {
                "evidence": "NONE",
                "authorization": "NOT_ELIGIBLE",
                "activation_state": "INACTIVE_NONLIVE",
            }
        }
        binding["selected_implementation_version"] = None
        binding["input_source_bindings"] = {"value": "CALLER_TYPED_INPUT"}
        binding["readiness"] = {
            "specification": "PASS",
            "implementation": "REQUIRED",
            "inputs": "PASS",
            "requirements": "PASS",
            "oracle": "REQUIRED",
            "context": "PASS",
            "evidence": "NONE",
            "authorization": "NOT_ELIGIBLE",
        }
        binding["derived_state"] = "SPECIFIED"
        binding["exact_resolution_action_or_null"] = "MISSING_IMPLEMENTATION: synthetic_scale_probe"
        binding["evidence_summary"] = {"state": "SYNTHETIC_SCALE_ONLY"}
        binding["runtime_snapshot_ref_or_null"] = None
        row = {
            "canonical_component_id": component_id,
            "semantic_version": "1.0",
            "record_state": "CANONICAL_ACCEPTED",
            "origin_cohorts": ["VALIDATOR_SYNTHETIC_SCALE"],
            "definition": definition,
            "uses": {
                "decision_roles": ["INTERNAL_SUPPORT"],
                "decision_outputs": ["value"],
                "market_family_tags": ["SYNTHETIC_SCALE"],
                "qku_role_bindings": [
                    {
                        "qku_id": f"QKU-SCALE-{index:08d}",
                        "role_or_decision_stage": "INTERNAL_SUPPORT",
                        "market_family": "SYNTHETIC_SCALE",
                        "stack_root_or_direct_component": component_id,
                        "selection_rule_if_container": None,
                        "agent_policy_tags": ["VALIDATOR_ONLY"],
                        "source_refs": ["VALIDATOR_SYNTHETIC_SCALE"],
                    }
                ],
                "consumer_class_tags": ["VALIDATOR_ONLY"],
            },
            "bindings": [binding],
            "provenance": [
                {
                    "source_artifact_ref": "VALIDATOR_SYNTHETIC_SCALE",
                    "source_row_ref": f"row[{index}]",
                    "source_local_identity_or_name": component_id,
                    "source_fields_consumed": ["synthetic_index"],
                    "source_relation": "VALIDATION_ONLY",
                    "canonical_target_ref": component_id,
                    "proof_refs": ["tools/validate_pr169_qku_comp_control1.py"],
                }
            ],
            "relations": [],
            "governance": copy.deepcopy(template["governance"]),
        }
        rows.append(row)
    return rows


def _scale_probe(
    control_module: Any,
    facade_class: type[Any],
    template: Mapping[str, Any],
    count: int,
    parity: bool,
    deadline: Deadline,
) -> dict[str, Any]:
    if count <= 0:
        return {"records": 0, "skipped": True}
    started = time.perf_counter()
    records = _synthetic_records(template, count)
    build_ms = int((time.perf_counter() - started) * 1000)
    with tempfile.TemporaryDirectory(prefix="qtt-control1-scale-") as temporary:
        root = Path(temporary)
        single_dir = root / "single"
        write_started = time.perf_counter()
        _write_layout(control_module, single_dir, records, False)
        single = _construct_facade(facade_class, single_dir)
        load_ms = int((time.perf_counter() - write_started) * 1000)
        selected_records = [records[0], records[count // 2], records[-1]]
        selectors = [record["canonical_component_id"] for record in selected_records]
        contexts = [_binding_context(record["bindings"][0]) for record in selected_records]
        single_results: list[str] = []
        resolve_started = time.perf_counter()
        for selector, context in zip(selectors, contexts, strict=True):
            deadline.check("scale_probe_resolve")
            plan = _operation(single, "resolve", selector, context=context)
            single_results.append(_canonical_json(plan, strip_volatile=True))
        resolve_ms = int((time.perf_counter() - resolve_started) * 1000)
        parity_result = True
        if parity:
            shard_dir = root / "sharded"
            _write_layout(control_module, shard_dir, records, True)
            sharded = _construct_facade(facade_class, shard_dir)
            sharded_results = [
                _canonical_json(
                    _operation(sharded, "resolve", selector, context=context),
                    strip_volatile=True,
                )
                for selector, context in zip(selectors, contexts, strict=True)
            ]
            parity_result = single_results == sharded_results
            if not parity_result:
                raise InvariantError("SINGLE_SHARD_PARITY", "resolved plans differ")
    return {
        "records": count,
        "synthetic_build_ms": build_ms,
        "single_write_load_index_ms": load_ms,
        "representative_resolve_ms": resolve_ms,
        "single_shard_parity": parity_result,
    }


def _validate_semantic_reuse(records: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    relation_counts: Counter[str] = Counter()
    accepted_ids = {
        str(record["canonical_component_id"])
        for record in records
        if record.get("record_state") == "CANONICAL_ACCEPTED"
    }
    for record in records:
        component_id = str(record["canonical_component_id"])
        proofs = record["definition"].get("equivalence_proof_refs", [])
        for relation in record.get("relations", []):
            kind = _relation_type(relation)
            relation_counts[kind] += 1
            target = str(
                relation.get("canonical_target_ref")
                or relation.get("target_component_id")
                or relation.get("target_ref")
                or ""
            )
            if kind in {"ALIAS_OF", "FAMILY_BINDING_OF"}:
                if not proofs and not relation.get("proof_refs"):
                    raise InvariantError("SEMANTIC_REUSE_WITHOUT_PROOF", f"{component_id}: {kind}")
                if target and target not in accepted_ids:
                    raise InvariantError("SEMANTIC_REUSE_TARGET", f"{component_id}: {target}")
            if kind == "ENCODES_OR_MAPS" and target == component_id:
                raise InvariantError("QUANTUM_ORIGINAL_ALIAS", component_id)
    provenance_relations = Counter(
        str(entry.get("source_relation", ""))
        for record in records
        for entry in record.get("provenance", [])
    )
    if not any(
        token in key
        for key in provenance_relations
        for token in ("DUPLICATE", "REUSE", "GROUPING_NOT_SEMANTIC_PROOF")
    ):
        raise InvariantError("SEMANTIC_REUSE_CASE_COVERAGE", "no dedupe/reuse source disposition")
    result = dict(relation_counts)
    result["SOURCE_DISPOSITION_KINDS"] = len(provenance_relations)
    return result


def _expect_defect(code: str, function: Callable[[], Any]) -> None:
    try:
        function()
    except InvariantError as exc:
        if exc.code != code:
            raise InvariantError("DEFECT_WRONG_REASON", f"expected={code}, observed={exc.code}: {exc.detail}") from exc
        return
    raise InvariantError("DEFECT_NOT_REJECTED", code)


def _defect_injection(template: Mapping[str, Any]) -> int:
    probes = 0

    bulk = copy.deepcopy(template)
    bulk["bindings"][0]["evidence_summary"] = {"replay_history": list(range(100))}
    _expect_defect("BULK_EVIDENCE_PAYLOAD", lambda: _validate_record(bulk))
    probes += 1

    neutral_bulk = copy.deepcopy(template)
    neutral_bulk["bindings"][0]["evidence_summary"] = {
        "observations": {f"row_{index:05d}": {"value": index} for index in range(5_000)}
    }
    _expect_defect("BULK_EVIDENCE_PAYLOAD", lambda: _validate_record(neutral_bulk))
    probes += 1

    deeply_nested = copy.deepcopy(template)
    nested: dict[str, Any] = {"terminal": "reference"}
    for index in range(12):
        nested = {f"level_{index:02d}": nested}
    deeply_nested["bindings"][0]["evidence_summary"] = nested
    _expect_defect("BULK_EVIDENCE_PAYLOAD", lambda: _validate_record(deeply_nested))
    probes += 1

    unit = copy.deepcopy(template)
    del unit["definition"]["units_and_bases"]
    _expect_defect("DEFINITION_SHAPE", lambda: _validate_record(unit))
    probes += 1

    stale = copy.deepcopy(template)
    del stale["bindings"][0]["freshness_and_TTL"]
    _expect_defect("BINDING_SHAPE", lambda: _validate_record(stale))
    probes += 1

    nonfinite = copy.deepcopy(template)
    nonfinite["bindings"][0]["evidence_summary"] = {"metric": float("inf")}
    _expect_defect("NONFINITE_VALUE", lambda: _validate_record(nonfinite))
    probes += 1

    fixture = copy.deepcopy(template)
    fixture["definition"]["implementation_versions"][0]["fixture_inputs"] = {"value": "1"}
    _expect_defect("CANONICAL_FIXTURE_PAYLOAD", lambda: _validate_record(fixture))
    probes += 1

    ambiguous = copy.deepcopy(template)
    duplicate = copy.deepcopy(ambiguous["bindings"][0])
    duplicate["binding_id"] += "-other"
    ambiguous["bindings"].append(duplicate)
    _expect_defect("AMBIGUOUS_BINDING", lambda: _validate_record(ambiguous))
    probes += 1

    overlapping = copy.deepcopy(template)
    original = overlapping["bindings"][0]
    original["supported_modes"] = ["TEST_VECTOR"]
    original["mode_state"] = {
        "TEST_VECTOR": {"evidence": "FIXTURE", "authorization": "NOT_ELIGIBLE"}
    }
    original["context_selector"] = {
        "context_family": "VALIDATOR_OVERLAP",
        "left_wildcard": "ANY",
    }
    overlap = copy.deepcopy(original)
    overlap["binding_id"] += ".OVERLAP"
    overlap["context_selector"] = {
        "context_family": "VALIDATOR_OVERLAP",
        "right_wildcard": "ANY",
    }
    overlapping["bindings"].append(overlap)
    _expect_defect(
        "OVERLAPPING_BINDING_SELECTORS", lambda: _validate_record(overlapping)
    )
    probes += 1

    missing_mode = copy.deepcopy(template)
    missing_mode["bindings"][0]["supported_modes"] = ["TEST_VECTOR"]
    missing_mode["bindings"][0]["mode_state"] = {}
    _expect_defect("MODE_STATE_MISSING", lambda: _validate_record(missing_mode))
    probes += 1

    extra_mode = copy.deepcopy(template)
    extra_mode["bindings"][0]["supported_modes"] = ["TEST_VECTOR"]
    extra_mode["bindings"][0]["mode_state"] = {
        "TEST_VECTOR": {"evidence": "FIXTURE", "authorization": "NOT_ELIGIBLE"},
        "PAPER": {"evidence": "NONE", "authorization": "NOT_ELIGIBLE"},
    }
    _expect_defect(
        "MODE_STATE_WITHOUT_SUPPORTED_MODE", lambda: _validate_record(extra_mode)
    )
    probes += 1

    unsafe = copy.deepcopy(template)
    unsafe["definition"]["implementation_versions"] = [
        {
            "implementation_version": "1",
            "callable_or_solver_ref": "os.system",
            "determinism_or_seed_policy": "DETERMINISTIC",
            "memoizable_flag": False,
        }
    ]
    _expect_defect(
        "UNSAFE_CALLABLE_REF",
        lambda: _validate_callable_ref(_implementation_ref(unsafe["definition"]["implementation_versions"][0])),
    )
    probes += 1

    first_id = str(template["canonical_component_id"])
    cycle_a = copy.deepcopy(template)
    cycle_b = copy.deepcopy(template)
    cycle_b["canonical_component_id"] = first_id + ".CYCLE_B"
    req = {
        "required_component_id_or_source_selector": cycle_b["canonical_component_id"],
        "required_semantic_version_constraint": "1.0",
        "requirement_role": "DEFECT",
        "required_or_optional": "REQUIRED",
        "producer_output_name": "value",
        "consumer_input_name": "value",
        "unit_or_basis_conversion": "IDENTITY",
        "timing_and_freshness_constraint": "SAME_REQUEST",
        "activation_condition": "ALWAYS",
        "fallback_component_id_or_null": None,
        "failure_behavior": "FAIL_CLOSED",
    }
    cycle_a["definition"]["requirements"] = [req]
    reverse_req = dict(req)
    reverse_req["required_component_id_or_source_selector"] = first_id
    cycle_b["definition"]["requirements"] = [reverse_req]
    _expect_defect("DAG_CYCLE", lambda: _topological(_graph([cycle_a, cycle_b])[0]))
    probes += 1
    return probes


def _snapshot_replace_probe(control_module: Any, facade: Any, candidate: Sequence[Mapping[str, Any]], delta: Any, selector: str, context: Mapping[str, Any]) -> int:
    replace = None
    for name in ("_replace_snapshot", "_apply_validated_registry_update", "_swap_snapshot"):
        method = getattr(facade, name, None)
        if callable(method):
            replace = method
            break
    if replace is None:
        raise InvariantError("SNAPSHOT_SWAP_HELPER_MISSING", "facade needs a private validation-only snapshot swap mechanism")
    observed: list[str] = []
    failures: list[str] = []
    stop = threading.Event()
    first_observation = threading.Event()

    def reader() -> None:
        while not stop.is_set() and len(observed) < 200:
            try:
                observed.append(_canonical_json(_operation(facade, "status", selector, context=context), strip_volatile=True))
                first_observation.set()
            except Exception as exc:  # pragma: no cover - reported deterministically below
                failures.append(f"{type(exc).__name__}: {exc}")
                break

    thread = threading.Thread(target=reader, name="control1-snapshot-reader", daemon=True)
    thread.start()
    if not first_observation.wait(timeout=5):
        stop.set()
        thread.join(timeout=5)
        raise InvariantError("SNAPSHOT_SWAP_CONCURRENCY", "reader did not pin the old generation")
    signature = inspect.signature(replace)
    kwargs: dict[str, Any] = {}
    for key in signature.parameters:
        if key in {"records", "candidate_records", "new_records"}:
            kwargs[key] = candidate
        elif key in {"delta", "registry_update", "update"}:
            kwargs[key] = delta
    try:
        if kwargs:
            replace(**kwargs)
        else:
            replace(candidate, delta)
        wait_until = time.perf_counter() + 1.0
        while time.perf_counter() < wait_until and len(set(observed)) < 2 and not failures:
            time.sleep(0.001)
    finally:
        stop.set()
        thread.join(timeout=10)
    if thread.is_alive() or failures or not observed:
        raise InvariantError("SNAPSHOT_SWAP_CONCURRENCY", f"alive={thread.is_alive()}, failures={failures}, observations={len(observed)}")
    if len(set(observed)) != 2:
        raise InvariantError("MIXED_SNAPSHOT_GENERATION", f"expected old/new payloads, observed={len(set(observed))}")
    return len(observed)


def _bounded_snapshot_concurrency_probe(
    control_module: Any,
    facade_class: type[Any],
    template: Mapping[str, Any],
) -> int:
    base = _synthetic_records(template, 128)
    candidate = list(base)
    changed = copy.deepcopy(base[63])
    changed["bindings"][0]["selected_parameter_policy"] = {
        **dict(changed["bindings"][0]["selected_parameter_policy"]),
        "validation_probe_revision": 1,
    }
    candidate[63] = changed
    delta = _derive_delta(control_module, base, candidate)
    facade = facade_class(records=base)
    selector = str(changed["canonical_component_id"])
    context = _binding_context(changed["bindings"][0])
    return _snapshot_replace_probe(control_module, facade, candidate, delta, selector, context)


def _compiler_mechanism_probe(control_module: Any, records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    function = _find_function(
        control_module,
        ("_compile_expansion_batch_for_validation", "_compile_expansion_batch", "_compile_candidate_batch"),
    )
    if function is None:
        raise InvariantError("COMPILER_PROBE_HELPER_MISSING", "private compiler mechanism is required")
    source_template = next(
        (
            copy.deepcopy(record)
            for record in records
            if record.get("record_state") == "CANONICAL_ACCEPTED"
            and record.get("bindings")
            and record.get("definition", {}).get("implementation_versions")
        ),
        None,
    )
    if source_template is None:
        raise InvariantError("COMPILER_PROBE_FIXTURE_MISSING", "no accepted implementation record")
    if len(records) > 1_000:
        bounded = _synthetic_records(source_template, 64)
        selected_version = str(
            source_template["definition"]["implementation_versions"][0]["implementation_version"]
        )
        bounded[0]["definition"]["implementation_versions"] = copy.deepcopy(
            source_template["definition"]["implementation_versions"]
        )
        bounded[0]["definition"]["implementation_inventory_class"] = "FORMULA"
        bounded[0]["bindings"][0]["selected_implementation_version"] = selected_version
        bounded[0]["bindings"][0]["readiness"]["implementation"] = "PASS"
        records = bounded
    base_projection = _canonical_json(records)
    template = next(
        copy.deepcopy(record)
        for record in records
        if record.get("definition", {}).get("implementation_versions")
    )
    base_id = str(template["canonical_component_id"])

    def provenance(case: str, target: str) -> dict[str, Any]:
        return {
            "source_artifact_ref": "VALIDATOR_SYNTHETIC_EXPANSION",
            "source_row_ref": case,
            "source_local_identity_or_name": f"VALIDATOR::{case}",
            "source_fields_consumed": ["case", "record"],
            "source_relation": case,
            "canonical_target_ref": target,
            "proof_refs": ["tools/validate_pr169_qku_comp_control1.py"],
        }

    def clone(case: str, *, same_semantics: bool = False) -> dict[str, Any]:
        value = copy.deepcopy(template)
        component_id = f"QTT.COMP.VALIDATION.{case}"
        value["canonical_component_id"] = component_id
        value["origin_cohorts"] = ["VALIDATOR_SYNTHETIC_EXPANSION"]
        value["record_state"] = "PROVISIONAL"
        if not same_semantics:
            value["definition"]["display_name"] = f"Validation {case}"
            value["definition"]["description"] = f"Independent compiler probe for {case}."
            value["definition"]["complete_mathematical_or_procedural_definition"] = (
                f"VALIDATION_PROCEDURE::{case}"
            )
        if not same_semantics:
            value["definition"]["requirements"] = []
        value["provenance"] = [provenance(case, component_id)]
        value["relations"] = []
        for index, binding in enumerate(value["bindings"]):
            binding["binding_id"] = f"BINDING.VALIDATION.{case}.{index:02d}"
            binding["context_selector"] = {"context_family": "VALIDATOR_SYNTHETIC", "case": case}
            binding["exact_resolution_action_or_null"] = f"MISSING_INDEPENDENT_PROMOTION: {component_id}"
            binding["readiness"] = {
                "specification": "PASS",
                "implementation": "REQUIRED",
                "inputs": "REQUIRED",
                "requirements": "REQUIRED",
                "oracle": "REQUIRED",
                "context": "REQUIRED",
                "evidence": "NONE",
                "authorization": "NOT_ELIGIBLE",
            }
            binding["derived_state"] = "SPECIFIED"
        value["uses"]["qku_role_bindings"] = []
        return value

    exact_duplicate = copy.deepcopy(template)
    exact_duplicate["origin_cohorts"] = sorted(set(exact_duplicate["origin_cohorts"]) | {"VALIDATOR_SYNTHETIC_EXPANSION"})
    exact_duplicate["provenance"] = [*exact_duplicate["provenance"], provenance("EXACT_DUPLICATE", base_id)]

    provenance_only = copy.deepcopy(template)
    provenance_only["provenance"] = [*provenance_only["provenance"], provenance("PROVENANCE_ONLY", base_id)]

    qku_addition = copy.deepcopy(template)
    qku_addition["provenance"] = [
        *qku_addition["provenance"],
        provenance("QKU_ROLE_ADDITION", base_id),
    ]
    qku_addition["uses"]["qku_role_bindings"] = [
        *qku_addition["uses"].get("qku_role_bindings", []),
        {
            "qku_id": "QKU-VALIDATOR-SEMANTIC-REUSE",
            "role_or_decision_stage": "INTERNAL_SUPPORT",
            "market_family": "VALIDATOR_SYNTHETIC",
            "stack_root_or_direct_component": base_id,
            "selection_rule_if_container": None,
            "agent_policy_tags": ["VALIDATOR_ONLY"],
            "source_refs": ["VALIDATOR_SYNTHETIC_EXPANSION"],
        },
    ]

    binding_addition = copy.deepcopy(template)
    binding_addition["provenance"] = [
        *binding_addition["provenance"],
        provenance("NEW_BINDING", base_id),
    ]
    new_binding = copy.deepcopy(binding_addition["bindings"][0])
    new_binding["binding_id"] = "BINDING.VALIDATION.NEW_BINDING.00"
    new_binding["context_selector"] = {"context_family": "VALIDATOR_SYNTHETIC", "case": "NEW_BINDING"}
    new_binding["readiness"] = {
        "specification": "PASS",
        "implementation": "REQUIRED",
        "inputs": "REQUIRED",
        "requirements": "REQUIRED",
        "oracle": "REQUIRED",
        "context": "REQUIRED",
        "evidence": "NONE",
        "authorization": "NOT_ELIGIBLE",
    }
    new_binding["derived_state"] = "SPECIFIED"
    new_binding["exact_resolution_action_or_null"] = (
        f"MISSING_INDEPENDENT_PROMOTION: {base_id}"
    )
    binding_addition["bindings"].append(new_binding)

    parameter_update = copy.deepcopy(template)
    parameter_update["provenance"] = [
        *parameter_update["provenance"],
        provenance("NEW_PARAMETER_POLICY", base_id),
    ]
    parameter_update["bindings"][0]["selected_parameter_policy"] = {
        **dict(parameter_update["bindings"][0]["selected_parameter_policy"]),
        "validation_probe_revision": 1,
    }

    implementation_update = copy.deepcopy(template)
    implementation_update["provenance"] = [
        *implementation_update["provenance"],
        provenance("NEW_IMPLEMENTATION", base_id),
    ]
    added_implementation = copy.deepcopy(implementation_update["definition"]["implementation_versions"][0])
    added_implementation["implementation_version"] = "validation-probe"
    implementation_update["definition"]["implementation_versions"].append(added_implementation)

    alias = clone("NAME_ALIAS", same_semantics=True)
    # A family binding preserves the complete generic definition.  Only its
    # contextual binding/use/provenance metadata may differ.
    family = clone("COMPATIBLE_FAMILY_MEMBER", same_semantics=True)
    family["relations"] = [
        {
            "relation_type": "FAMILY_BINDING_OF",
            "canonical_target_ref": base_id,
            "proof_refs": ["VALIDATOR_FAMILY_COMPATIBILITY_PROOF"],
        }
    ]
    distinct = clone("SIMILAR_BUT_DISTINCT")
    distinct["relations"] = [
        {
            "relation_type": "DISTINCT_FROM",
            "canonical_target_ref": base_id,
            "proof_refs": ["VALIDATOR_DISTINCTION_PROOF"],
        }
    ]
    true_new = clone("TRUE_NEW")
    encoding = clone("QUANTUM_ENCODING_RELATION")
    encoding["definition"]["component_kind"] = "QUANTUM_FORMULATION"
    encoding["definition"]["quantum"].update(
        {
            "applicability_state": "MAPPED_SYNTHETIC_VALIDATION_ONLY",
            "original_economic_problem_ref": base_id,
            "problem_family": "VALIDATOR_BINARY_SELECTION",
            "formulation_candidates": ["VALIDATOR_QUBO_ENCODING"],
            "selected_formulation_or_none": "VALIDATOR_QUBO_ENCODING",
            "variable_encoding": {"x": "BINARY"},
            "objective_map": "minimize negative validated utility over x",
            "constraint_map": ["x in {0,1}"],
            "penalty_policy": "BOUNDED_SYNTHETIC_PENALTY",
            "coefficient_scaling": "IDENTITY_SYNTHETIC_SCALE",
            "precision_and_quantization": "EXACT_SMALL_INSTANCE",
            "decomposition_or_embedding": "NOT_REQUIRED_SMALL_INSTANCE",
            "warm_start": "DETERMINISTIC_ZERO_STATE",
            "optimizer_and_version": "LOCAL_EXACT_ENUMERATION_V1",
            "shots_reads_or_sampling_policy": "NO_QPU_OR_SAMPLING",
            "inverse_map": "x maps directly to the selected binary decision",
            "original_model_feasibility_check": "EXACT_BINARY_DOMAIN_CHECK",
            "same_formulation_classical_comparator": base_id,
            "local_exact_or_small_instance_parity": "STRUCTURAL_FIXTURE_ONLY",
            "fallback": base_id,
            "maturity_ceiling": "SPECIFIED",
        }
    )
    encoding["relations"] = [
        {
            "relation_type": "ENCODES_OR_MAPS",
            "canonical_target_ref": base_id,
            "proof_refs": ["VALIDATOR_STRUCTURAL_MAPPING_ONLY"],
        }
    ]

    marker_items = [
        {"record": exact_duplicate, "case": "EXACT_DUPLICATE"},
        {
            "record": alias,
            "case": "NAME_ALIAS",
            "equivalence_decision": "YES",
            "candidate_alias": "VALIDATOR_NAME_ALIAS",
        },
        {"record": provenance_only, "case": "PROVENANCE_ONLY"},
        {"record": binding_addition, "case": "NEW_BINDING"},
        {"record": parameter_update, "case": "NEW_PARAMETER_POLICY"},
        {
            "record": family,
            "case": "COMPATIBLE_FAMILY_MEMBER",
            "equivalence_decision": "NO",
            "nonidentical_relation": "FAMILY_COMPATIBLE",
        },
        {
            "record": distinct,
            "case": "SIMILAR_BUT_DISTINCT",
            "equivalence_decision": "NO",
            "nonidentical_relation": "DISTINCT",
        },
        {
            "record": true_new,
            "case": "TRUE_NEW",
            "equivalence_decision": "NO",
            "nonidentical_relation": "DISTINCT",
        },
        {
            "record": encoding,
            "case": "QUANTUM_ENCODING_RELATION",
            "equivalence_decision": "NO",
            "nonidentical_relation": "DISTINCT",
        },
    ]
    signature = inspect.signature(function)

    def invoke(base: Sequence[Mapping[str, Any]], items: Sequence[Mapping[str, Any]], source_order: str, inject_failure: bool) -> Any:
        intended_contexts: dict[str, dict[str, Any]] = {}
        for item in items:
            record = item.get("record", {})
            for binding in record.get("bindings", ()):
                for mode in binding.get("supported_modes", ()):
                    context = {
                        "market": copy.deepcopy(binding.get("market", "ANY")),
                        "venue": copy.deepcopy(binding.get("venue", "ANY")),
                        "mode": str(mode),
                    }
                    intended_contexts[_canonical_json(context)] = context
        batch = {
            "batch_id": f"VALIDATOR_SYNTHETIC_{source_order}",
            "batch_origin": "VALIDATOR_SYNTHETIC_EXPANSION",
            "submitted_by": "CONTROL1_CENTRAL_BUILDER",
            "submission_time": "2000-01-01T00:00:00Z",
            "source_refs": ["tools/validate_pr169_qku_comp_control1.py"],
            "source_classification": "OWNER_SUBMITTED",
            "intended_market_venue_modes": [
                intended_contexts[key] for key in sorted(intended_contexts)
            ],
            "items": list(items),
            "requested_evidence_modes": ["FIXTURE"],
            "requested_promotion_ceiling": "SPECIFIED",
        }
        if inject_failure:
            invalid = copy.deepcopy(template)
            invalid["definition"]["complete_mathematical_or_procedural_definition"] = (
                "MATERIAL_MUTATION_UNDER_EXISTING_ID"
            )
            batch["items"] = [{"record": invalid, "case": "INJECTED_FAILURE"}]
        kwargs: dict[str, Any] = {}
        for key in signature.parameters:
            if key in {"base", "base_records", "accepted_records", "records"}:
                kwargs[key] = base
            elif key in {"batch", "expansion_batch"}:
                kwargs[key] = batch
            elif key in {"items", "batch_items", "synthetic_items"}:
                kwargs[key] = batch["items"]
            elif key in {"source_order", "order_tag"}:
                kwargs[key] = source_order
            elif key in {"inject_failure", "fail_after_stage", "force_failure"}:
                kwargs[key] = inject_failure
        return function(**kwargs) if kwargs else function(base, batch)

    qku_role_rejection = _runtime_error_code(
        lambda: invoke(
            records,
            [{"record": qku_addition, "case": "QKU_ROLE_ADDITION"}],
            "QKU_ROLE_REJECTION",
            False,
        )
    )
    if qku_role_rejection != "NEW_REUSED_QKU_ROLE_REQUIRES_BUILD_OWNED_VERIFIER":
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"unverified QKU role -> {qku_role_rejection}",
        )
    implementation_rejection = _runtime_error_code(
        lambda: invoke(
            records,
            [{"record": implementation_update, "case": "NEW_IMPLEMENTATION"}],
            "IMPLEMENTATION_REJECTION",
            False,
        )
    )
    if (
        implementation_rejection
        != "NEW_REUSED_IMPLEMENTATION_REQUIRES_BUILD_OWNED_VERIFIER"
    ):
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"unverified implementation -> {implementation_rejection}",
        )

    forward = _unwrap_records(invoke(records, marker_items, "FORWARD", False))
    reverse = _unwrap_records(invoke(records, list(reversed(marker_items)), "REVERSE", False))
    if forward is None or reverse is None:
        raise InvariantError("COMPILER_PROBE_RESULT", "compiler helper did not return records")
    forward_projection = sorted(forward, key=lambda row: (str(row["canonical_component_id"]), str(row["semantic_version"])))
    reverse_projection = sorted(reverse, key=lambda row: (str(row["canonical_component_id"]), str(row["semantic_version"])))
    if _canonical_json(forward_projection) != _canonical_json(reverse_projection):
        raise InvariantError("SOURCE_ORDER_ID_STABILITY", "forward and reverse batch allocation differ")
    failed = False
    try:
        invoke(records, marker_items, "FORWARD", True)
    except Exception:
        failed = True
    if not failed:
        raise InvariantError("FAILED_COMPILE_NOT_REJECTED", "failure injection returned normally")
    forged_alias = copy.deepcopy(marker_items[1])
    forged_alias["record"]["definition"][
        "complete_mathematical_or_procedural_definition"
    ] = "FORGED_CALLER_ASSERTED_SEMANTIC_EQUALITY"
    forged_alias["equivalence_proof_refs"] = [
        "CONTROL1_DIRECT_PROOF::FORGED_CALLER_PASS"
    ]
    forged_alias["trusted_proof_result_id"] = "FORGED.CALLER.PASS"
    forged_proof_code = _runtime_error_code(
        lambda: invoke(records, [forged_alias], "FORGED_CALLER_PROOF", False)
    )
    if forged_proof_code not in {
        "UNPROVEN_EQUIVALENCE",
        "BUILD_OWNED_EQUIVALENCE_PROOF_FAILED",
    }:
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"forged caller equivalence proof -> {forged_proof_code}",
        )
    if _canonical_json(records) != base_projection:
        raise InvariantError("FAILED_COMPILE_ROLLBACK", "base records changed after injected failure")
    return {
        "synthetic_cases": len(marker_items) + 2,
        "forward_records": len(forward),
        "source_order_stable": True,
        "rollback": True,
        "forged_caller_proof_rejected": forged_proof_code,
        "unverified_qku_role_rejected": qku_role_rejection,
        "unverified_implementation_rejected": implementation_rejection,
        "build_owned_submitter": "CONTROL1_CENTRAL_BUILDER",
    }


def _hardened_contract_probe(
    control_module: Any, records: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Independently exercise the hardened compiler/storage/runtime boundaries."""

    template = next(
        (
            copy.deepcopy(record)
            for record in records
            if record.get("record_state") == "CANONICAL_ACCEPTED"
            and record.get("bindings")
            and not record.get("definition", {}).get("requirements")
            and _schema_specs(record.get("definition", {}).get("input_schema"))
            and _schema_specs(record.get("definition", {}).get("output_schema"))
        ),
        None,
    )
    if template is None:
        raise InvariantError(
            "HARDENED_CONTRACT_TEMPLATE_MISSING",
            "accepted bound record with direct inputs/outputs is required",
        )

    base = copy.deepcopy(template)
    base["relations"] = []
    base["uses"]["qku_role_bindings"] = []
    base["definition"]["requirements"] = []
    base["record_state"] = "CANONICAL_ACCEPTED"
    binding = base["bindings"][0]
    binding["readiness"]["authorization"] = "NOT_ELIGIBLE"
    binding["activation_state"] = "INACTIVE_NONLIVE"
    binding["rollback_target_or_null"] = None
    binding["terminal_disposition_or_null"] = None
    binding["fallback_policy"] = {"state": "FAIL_CLOSED"}
    binding["selected_requirement_alternatives"] = []

    validate_shape = getattr(control_module, "_validate_record_shape")
    build_snapshot = getattr(control_module, "_build_snapshot")
    derive_delta = getattr(control_module, "_derive_registry_update")
    apply_update = getattr(control_module, "_apply_registry_update")
    compile_batch = getattr(control_module, "_compile_expansion_batch")
    derive_context = getattr(control_module, "_derive_requirement_context")
    write_layout = getattr(control_module, "_write_registry_layout")
    load_layout = getattr(control_module, "_load_logical_registry")
    registry_partitions = getattr(control_module, "_registry_partitions")
    choose_layout = getattr(control_module, "_choose_layout")

    validate_shape(base)
    snapshot = build_snapshot([base], generation=11)

    def update_error(candidate: Mapping[str, Any], batch_id: str) -> str:
        delta = derive_delta([base], [candidate], batch_id=batch_id)
        return _runtime_error_code(
            lambda: apply_update(snapshot, delta, [candidate])
        )

    demoted = copy.deepcopy(base)
    demoted["record_state"] = "PROVISIONAL"
    demotion_code = update_error(demoted, "VALIDATOR.ACCEPTED.DEMOTION")
    if demotion_code != "ACCEPTED_RECORD_STATE_DEMOTION_FORBIDDEN":
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"accepted demotion -> {demotion_code}",
        )

    authority = copy.deepcopy(base)
    authority["bindings"][0]["readiness"]["authorization"] = "AUTHORIZED"
    authority["bindings"][0]["activation_state"] = "ACTIVE"
    authority_code = update_error(authority, "VALIDATOR.AUTHORITY.GRANT")
    if authority_code not in {
        "BINDING_AUTHORITY_CHANGE_FORBIDDEN",
        "BINDING_AUTHORITY_GRANT_FORBIDDEN",
    }:
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"accepted authority grant -> {authority_code}",
        )

    source_ref = "tools/validate_pr169_qku_comp_control1.py"

    def provenance(case: str, target: str) -> dict[str, Any]:
        return {
            "source_artifact_ref": source_ref,
            "source_row_ref": case,
            "source_local_identity_or_name": case,
            "source_fields_consumed": ["independent_hardened_contract_probe"],
            "source_relation": "VALIDATION_ONLY",
            "canonical_target_ref": target,
            "proof_refs": [source_ref],
        }

    def batch(
        items: Sequence[Mapping[str, Any]],
        case: str,
        *,
        ceiling: str = "SPECIFIED",
        evidence_modes: Sequence[str] = ("FIXTURE",),
    ) -> dict[str, Any]:
        return {
            "batch_id": f"VALIDATOR.HARDENED.{case}",
            "batch_origin": "VALIDATOR_SYNTHETIC_EXPANSION",
            "submitted_by": "CONTROL1_CENTRAL_BUILDER",
            "submission_time": "2000-01-01T00:00:00Z",
            "source_refs": [source_ref],
            "source_classification": "OWNER_SUBMITTED",
            "intended_market_venue_modes": [],
            "items": list(items),
            "requested_evidence_modes": list(evidence_modes),
            "requested_promotion_ceiling": ceiling,
        }

    apply_envelope = getattr(control_module, "_apply_expansion_envelope_to_candidate")
    validate_envelope = getattr(control_module, "_validate_expansion_envelope")
    batch_type = getattr(control_module, "ExpansionBatchV1")

    def promotion_candidate(state: str, case: str) -> dict[str, Any]:
        candidate = copy.deepcopy(base)
        candidate_id = f"QTT.COMP.VALIDATION.PROMOTION.{case}"
        candidate["canonical_component_id"] = candidate_id
        candidate["origin_cohorts"] = ["VALIDATOR_SYNTHETIC_EXPANSION"]
        candidate["provenance"] = [provenance(case, candidate_id)]
        candidate["uses"]["qku_role_bindings"] = []
        candidate_binding = candidate["bindings"][0]
        candidate_binding["binding_id"] = f"BINDING.VALIDATION.PROMOTION.{case}"
        candidate_binding["readiness"] = {
            "specification": "PASS",
            "implementation": "PASS",
            "inputs": "REQUIRED",
            "requirements": "REQUIRED",
            "oracle": "PASS",
            "context": "REQUIRED",
            "evidence": "NONE",
            "authorization": "NOT_ELIGIBLE",
        }
        candidate_binding["activation_state"] = "INACTIVE_NONLIVE"
        if state in {"STACK_READY", "EVIDENCED", "AUTHORIZED"}:
            for dimension in ("inputs", "requirements", "context"):
                candidate_binding["readiness"][dimension] = "PASS"
        if state in {"EVIDENCED", "AUTHORIZED"}:
            candidate_binding["readiness"]["evidence"] = "PAPER"
        if state == "AUTHORIZED":
            candidate_binding["readiness"]["authorization"] = "AUTHORIZED"
            candidate_binding["activation_state"] = "ACTIVE"
        return candidate

    promotion_cases = {
        "NOT_ELIGIBLE": "VERIFIED",
        "SPECIFIED": "VERIFIED",
        "VERIFIED": "STACK_READY",
        "CONTEXT_READY": "STACK_READY",
        "STACK_READY": "EVIDENCED",
        "EVIDENCED": "AUTHORIZED",
    }
    promotion_codes: dict[str, str] = {}
    for ceiling, attempted_state in promotion_cases.items():
        candidate = promotion_candidate(attempted_state, ceiling)
        envelope = batch(
            [],
            f"PROMOTION.{ceiling}",
            ceiling=ceiling,
            evidence_modes=("FIXTURE", "PAPER"),
        )
        envelope_value = batch_type.from_mapping(envelope)
        validate_envelope(envelope_value)
        code = _runtime_error_code(
            lambda candidate=candidate, envelope_value=envelope_value: apply_envelope(
                candidate, batch=envelope_value, existing=None
            )
        )
        if code not in {
            "EXPANSION_STATE_EXCEEDS_CEILING",
            "EXPANSION_AUTHORIZATION_EXCEEDS_CEILING",
            "EXPANSION_MODE_AUTHORIZATION_EXCEEDS_CEILING",
        }:
            raise InvariantError(
                "RUNTIME_DEFECT_WRONG_REASON",
                f"promotion {attempted_state} under {ceiling} -> {code}",
            )
        promotion_codes[ceiling] = code
    authorized = promotion_candidate("AUTHORIZED", "AUTHORIZED")
    authorized_envelope = batch_type.from_mapping(
        batch(
            [],
            "PROMOTION.AUTHORIZED",
            ceiling="AUTHORIZED",
            evidence_modes=("FIXTURE", "PAPER"),
        )
    )
    validate_envelope(authorized_envelope)
    apply_envelope(authorized, batch=authorized_envelope, existing=None)
    promotion_codes["AUTHORIZED"] = "ALLOWED_AT_DECLARED_CEILING"

    raw_item = {
        "candidate_identity": "VALIDATOR_RAW_MATERIALIZATION",
        "component_kind": "DETERMINISTIC_TRANSFORM",
        "complete_mathematical_or_procedural_definition": "y = x + 1",
        "input_schema": [
            {"name": "x", "type": "DECIMAL", "unit": "UNITLESS", "required": True}
        ],
        "output_schema": [
            {"name": "y", "type": "DECIMAL", "unit": "UNITLESS", "required": True}
        ],
        "units_and_bases": {"x": "UNITLESS", "y": "UNITLESS"},
        "domain_and_boundary_behavior": {"domain": "finite decimal", "invalid": "FAIL_CLOSED"},
        "state_and_time_semantics": {"state": "STATELESS", "time": "SAME_REQUEST"},
        "decision_roles": ["INTERNAL_SUPPORT"],
        "decision_outputs": ["y"],
        "equivalence_decision": "NO",
        "nonidentical_relation": "DISTINCT",
    }
    raw_result = _unwrap_records(
        compile_batch([], batch([raw_item], "RAW.MATERIALIZATION", evidence_modes=()))
    )
    if raw_result is None or len(raw_result) != 1:
        raise InvariantError("RAW_MATERIALIZATION_RESULT", repr(raw_result))
    raw_record = raw_result[0]
    if (
        raw_record.get("canonical_component_id")
        != "QTT.COMP.EXPANSION.VALIDATOR_RAW_MATERIALIZATION"
        or raw_record.get("record_state") != "PROVISIONAL"
        or raw_record.get("definition", {}).get(
            "complete_mathematical_or_procedural_definition"
        )
        != "y = x + 1"
    ):
        raise InvariantError("RAW_MATERIALIZATION_RESULT", repr(raw_record))
    incomplete_raw = copy.deepcopy(raw_item)
    incomplete_raw.pop("domain_and_boundary_behavior")
    incomplete_raw_code = _runtime_error_code(
        lambda: compile_batch(
            [], batch([incomplete_raw], "RAW.INCOMPLETE", evidence_modes=())
        )
    )
    if incomplete_raw_code != "INCOMPLETE_RAW_EXPANSION_ITEM":
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"incomplete raw materialization -> {incomplete_raw_code}",
        )

    def candidate_record(case: str) -> dict[str, Any]:
        candidate = copy.deepcopy(base)
        candidate_id = f"QTT.COMP.VALIDATION.SELECTOR.{case}"
        candidate["canonical_component_id"] = candidate_id
        candidate["record_state"] = "PROVISIONAL"
        candidate["origin_cohorts"] = ["VALIDATOR_SYNTHETIC_EXPANSION"]
        candidate["definition"]["display_name"] = f"Selector {case}"
        candidate["definition"]["description"] = f"Selector probe {case}"
        candidate["definition"][
            "complete_mathematical_or_procedural_definition"
        ] = f"VALIDATOR_SELECTOR_PROCEDURE::{case}"
        candidate["definition"]["requirements"] = []
        candidate["bindings"] = []
        candidate["exact_resolution_action"] = (
            f"MISSING_CONTEXTUAL_BINDING: {candidate_id}"
        )
        candidate["provenance"] = [provenance(case, candidate_id)]
        candidate["relations"] = []
        candidate["uses"]["qku_role_bindings"] = []
        return candidate

    base_local = copy.deepcopy(base)
    local_selector = "VALIDATOR::BASE_LOCAL_SELECTOR"
    base_local["provenance"] = [
        {
            **provenance("BASE_LOCAL", str(base_local["canonical_component_id"])),
            "source_local_identity_or_name": local_selector,
        }
    ]
    dependent = candidate_record("BASE_DEPENDENT")
    producer_output, producer_spec = next(
        iter(_schema_specs(base_local["definition"]["output_schema"]).items())
    )
    producer_unit = str(
        producer_spec.get("unit", producer_spec.get("units", "UNSPECIFIED"))
    )
    dependent["definition"]["input_schema"] = [
        {
            "name": "upstream_value",
            "type": producer_spec.get("type", "ANY"),
            "unit": producer_unit,
            "required": True,
        }
    ]
    dependent["definition"]["units_and_bases"] = {
        "upstream_value": producer_unit,
        **{
            name: spec.get("unit", spec.get("units", "UNSPECIFIED"))
            for name, spec in _schema_specs(
                dependent["definition"]["output_schema"]
            ).items()
        },
    }
    dependent["definition"]["requirements"] = [
        {
            "required_component_id_or_source_selector": local_selector,
            "required_semantic_version_constraint": f"=={base_local['semantic_version']}",
            "requirement_role": "VALIDATOR_BASE_SEEDED_SELECTOR",
            "required_or_optional": "REQUIRED",
            "producer_output_name": producer_output,
            "consumer_input_name": "upstream_value",
            "unit_or_basis_conversion": "IDENTITY",
            "timing_and_freshness_constraint": "SAME_REQUEST",
            "activation_condition": "ALWAYS",
            "fallback_component_id_or_null": None,
            "failure_behavior": "FAIL_CLOSED",
        }
    ]
    seeded_result = _unwrap_records(
        compile_batch(
            [base_local],
            batch(
                [
                    {
                        "record": dependent,
                        "equivalence_decision": "NO",
                        "nonidentical_relation": "DISTINCT",
                    }
                ],
                "SELECTOR.BASE_SEEDED",
                evidence_modes=(),
            ),
        )
    )
    seeded_dependent = next(
        record
        for record in seeded_result or ()
        if record["canonical_component_id"] == dependent["canonical_component_id"]
    )
    seeded_target = seeded_dependent["definition"]["requirements"][0][
        "required_component_id_or_source_selector"
    ]
    if seeded_target != base_local["canonical_component_id"]:
        raise InvariantError(
            "BASE_SEEDED_SOURCE_SELECTOR", f"resolved={seeded_target!r}"
        )

    selector_a = candidate_record("COLLISION_A")
    selector_b = candidate_record("COLLISION_B")
    selector_dep = candidate_record("COLLISION_DEP")
    selector_dep["definition"]["requirements"] = copy.deepcopy(
        dependent["definition"]["requirements"]
    )
    selector_dep["definition"]["requirements"][0][
        "required_component_id_or_source_selector"
    ] = "VALIDATOR::COLLIDING_SELECTOR"
    selector_dep["definition"]["input_schema"] = copy.deepcopy(
        dependent["definition"]["input_schema"]
    )
    selector_dep["definition"]["units_and_bases"] = copy.deepcopy(
        dependent["definition"]["units_and_bases"]
    )
    collision_items = {
        "A": {
            "record": selector_a,
            "source_selector_aliases": ["VALIDATOR::COLLIDING_SELECTOR"],
            "equivalence_decision": "NO",
            "nonidentical_relation": "DISTINCT",
        },
        "B": {
            "record": selector_b,
            "source_selector_aliases": ["VALIDATOR::COLLIDING_SELECTOR"],
            "equivalence_decision": "NO",
            "nonidentical_relation": "DISTINCT",
        },
    }
    collision_codes: list[str] = []
    for order in (("A", "B"), ("B", "A")):
        items = [collision_items[name] for name in order]
        items.append(
            {
                "record": selector_dep,
                "equivalence_decision": "NO",
                "nonidentical_relation": "DISTINCT",
            }
        )
        code = _runtime_error_code(
            lambda items=items, order=order: compile_batch(
                [],
                batch(
                    items,
                    f"SELECTOR.COLLISION.{''.join(order)}",
                    evidence_modes=(),
                ),
            )
        )
        if code != "AMBIGUOUS_SOURCE_SELECTOR":
            raise InvariantError(
                "RUNTIME_DEFECT_WRONG_REASON",
                f"selector collision {order} -> {code}",
            )
        collision_codes.append(code)

    nested_parameter = copy.deepcopy(base)
    nested_parameter["definition"][
        "parameter_schema_and_default_provenance"
    ] = {
        "parameters": [
            {
                "name": "validator_alpha",
                "type": "INTEGER",
                "unit": "UNITLESS",
                "minimum": 0,
                "maximum": 1,
                "default": 1,
                "default_provenance": "CONTROL1_INDEPENDENT_VALIDATOR",
            }
        ],
        "default_provenance": "CONTROL1_INDEPENDENT_VALIDATOR",
    }
    nested_parameter["bindings"][0]["selected_parameter_policy"] = {
        "policy_id": "PARAM.VALIDATOR.NESTED",
        "version": "1.0",
        "defaults": {"validator_alpha": 1},
        "default_provenance": "CONTROL1_INDEPENDENT_VALIDATOR",
    }
    validate_shape(nested_parameter)
    invalid_parameter = copy.deepcopy(nested_parameter)
    invalid_parameter["bindings"][0]["selected_parameter_policy"]["defaults"][
        "validator_alpha"
    ] = 2
    nested_parameter_code = _runtime_error_code(
        lambda: validate_shape(invalid_parameter)
    )
    if nested_parameter_code != "ABOVE_MAXIMUM":
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"nested parameter default -> {nested_parameter_code}",
        )

    context_binding = copy.deepcopy(base["bindings"][0])
    context_binding["requirement_context_policy"] = {
        "inherit_root_context": True,
        "include_fields": ["market", "venue", "mode", "request_time"],
        "overrides": {"context_family": "VALIDATOR_PINNED_REQUIREMENT"},
    }
    context_requirement = copy.deepcopy(dependent["definition"]["requirements"][0])
    context_requirement["timing_and_freshness_constraint"] = (
        "SAME_REQUEST_IMMUTABLE_INPUT_LOCK"
    )
    pinned_context = derive_context(
        {
            "market": "VALIDATOR",
            "venue": "LOCAL",
            "mode": "TEST_VECTOR",
            "request_time": "2000-01-01T00:00:00Z",
            "binding_id": "CALLER_MUST_NOT_PIN",
        },
        consumer_binding=context_binding,
        requirement=context_requirement,
        target_component_id=str(base["canonical_component_id"]),
    )
    if (
        pinned_context.get("canonical_component_id") != base["canonical_component_id"]
        or pinned_context.get("request_scope") != "SAME_REQUEST"
        or pinned_context.get("requirement_timing_policy")
        != "SAME_REQUEST_IMMUTABLE_INPUT_LOCK"
        or pinned_context.get("input_lock_policy") != "IMMUTABLE"
        or pinned_context.get("binding_id") is not None
        or pinned_context.get("context_family")
        != "VALIDATOR_PINNED_REQUIREMENT"
    ):
        raise InvariantError("REQUIREMENT_CONTEXT_NOT_PINNED", repr(pinned_context))
    invalid_timing = copy.deepcopy(context_requirement)
    invalid_timing["timing_and_freshness_constraint"] = "CALLER_SELECTED_LATEST"
    invalid_timing_code = _runtime_error_code(
        lambda: derive_context(
            {},
            consumer_binding=context_binding,
            requirement=invalid_timing,
            target_component_id=str(base["canonical_component_id"]),
        )
    )
    if invalid_timing_code != "UNSUPPORTED_REQUIREMENT_TIMING_POLICY":
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"requirement timing -> {invalid_timing_code}",
        )

    quantum = copy.deepcopy(base)
    quantum["canonical_component_id"] = "QTT.COMP.QUANTUM.VALIDATOR_SELF_ASSERTED"
    quantum["definition"]["component_kind"] = "QUANTUM_FORMULATION"
    quantum["definition"]["quantum"].update(
        {
            "applicability_state": "APPLICABLE",
            "original_economic_problem_ref": "SELF_ASSERTED_ORIGINAL",
            "problem_family": "QUBO",
            "formulation_candidates": ["QUBO"],
            "selected_formulation_or_none": "QUBO",
            "variable_encoding": {"x": "BINARY"},
            "objective_map": "SELF_ASSERTED_OBJECTIVE",
            "constraint_map": ["SELF_ASSERTED_CONSTRAINT"],
            "inverse_map": "SELF_ASSERTED_INVERSE",
            "same_formulation_classical_comparator": "SELF_ASSERTED_COMPARATOR",
            "local_exact_or_small_instance_parity": {
                "result": "PASS",
                "authority": "CALLER",
            },
            "fallback": "SELF_ASSERTED_FALLBACK",
            "maturity_ceiling": "LOCAL_EXACT_PARITY",
        }
    )
    quantum_code = _runtime_error_code(lambda: validate_shape(quantum))
    if quantum_code != "QUANTUM_MATURITY_REQUIRES_INDEPENDENT_PROMOTION_AUTHORITY":
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"self-asserted quantum parity -> {quantum_code}",
        )

    with tempfile.TemporaryDirectory(prefix="qtt-control1-manifest-") as temporary:
        registry_root = Path(temporary) / "registry"
        write_layout([base], registry_root, force_layout="sharded")
        manifest_path = registry_root / "registry.manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["partitions"][0]["range_start"] = "ZZZ.INVALID.START"
        manifest["partitions"][0]["range_end"] = "AAA.INVALID.END"
        manifest_path.write_text(
            json.dumps(manifest, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
            newline="\n",
        )
        manifest_code = _runtime_error_code(lambda: load_layout(registry_root))
    if manifest_code != "REGISTRY_MANIFEST_PARTITION_DERIVATION_MISMATCH":
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"manifest range tamper -> {manifest_code}",
        )

    original_policy = control_module.STORAGE_POLICY
    try:
        split_policy = dict(original_policy)
        split_policy["rp5c_rows_per_stable_partition"] = 2
        split_policy["diff_size_budget_bytes"] = 1_000_000_000
        control_module.STORAGE_POLICY = MappingProxyType(split_policy)
        compact_records = [
            {
                "canonical_component_id": f"QTT.COMP.FORMULA.{suffix}",
                "semantic_version": "1.0",
            }
            for suffix in ("ALPHA", "BETA", "GAMMA")
        ]
        partitions = registry_partitions(compact_records)
        reverse_partitions = registry_partitions(list(reversed(compact_records)))
        partition_projection = [partition.manifest_row() for partition in partitions]
        reverse_projection = [
            partition.manifest_row() for partition in reverse_partitions
        ]
        if len(partitions) <= 1 or partition_projection != reverse_projection:
            raise InvariantError(
                "STABLE_OVERFLOW_PARTITIONING",
                f"forward={partition_projection!r}, reverse={reverse_projection!r}",
            )
        with_unrelated = registry_partitions(
            [
                *compact_records,
                {
                    "canonical_component_id": "QTT.COMP.ALGORITHM.UNRELATED",
                    "semantic_version": "1.0",
                },
            ]
        )
        formula_before = [
            partition.manifest_row()
            for partition in partitions
            if partition.token.startswith("formula")
        ]
        formula_after = [
            partition.manifest_row()
            for partition in with_unrelated
            if partition.token.startswith("formula")
        ]
        if formula_before != formula_after:
            raise InvariantError(
                "UNRELATED_SHARD_CHURN",
                f"before={formula_before!r}, after={formula_after!r}",
            )
    finally:
        control_module.STORAGE_POLICY = original_policy

    measurement_to_policy = {
        "row_count": "single_file_max_rows",
        "serialized_bytes": "single_file_max_serialized_bytes",
        "maximum_record_serialized_bytes": "max_record_serialized_bytes",
        "load_ms": "single_file_max_load_ms",
        "index_build_ms": "single_file_max_index_build_ms",
        "validation_ms": "single_file_max_validation_ms",
        "diff_candidate_bytes": "diff_size_budget_bytes",
    }
    baseline_measurements = {name: 0 for name in measurement_to_policy}
    if choose_layout([], measurements=baseline_measurements) != "single":
        raise InvariantError(
            "CENTRAL_MEASURED_STORAGE_POLICY", "zero measurements did not select single"
        )
    measured_dimensions: list[str] = []
    for measurement_name, policy_name in measurement_to_policy.items():
        measurements = dict(baseline_measurements)
        measurements[measurement_name] = float(original_policy[policy_name]) + 1
        if choose_layout([], measurements=measurements) != "sharded":
            raise InvariantError(
                "CENTRAL_MEASURED_STORAGE_POLICY",
                f"ignored {measurement_name}/{policy_name}",
            )
        measured_dimensions.append(measurement_name)

    return {
        "accepted_state_demotion": demotion_code,
        "accepted_authority_grant": authority_code,
        "promotion_ceiling_cases": promotion_codes,
        "raw_materialization": raw_record["canonical_component_id"],
        "incomplete_raw_rejected": incomplete_raw_code,
        "base_seeded_selector_target": seeded_target,
        "collision_order_independent_rejection": collision_codes,
        "nested_parameter_schema": nested_parameter_code,
        "requirement_context_timing": invalid_timing_code,
        "quantum_self_assertion": quantum_code,
        "manifest_range_tamper": manifest_code,
        "stable_overflow_shards": len(partitions),
        "central_measured_storage_dimensions": measured_dimensions,
    }


class _JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = _JsonArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--timeout-ms", type=int, default=3_600_000)
    parser.add_argument("--scale-probe-records", type=int, default=10_000)
    args = parser.parse_args(argv)
    if args.timeout_ms <= 0:
        parser.error("--timeout-ms must be positive")
    if args.scale_probe_records < 0:
        parser.error("--scale-probe-records must be zero or positive")
    return args


def validate(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = args.repo_root.resolve()
    artifact_dir = args.artifact_dir
    if not artifact_dir.is_absolute():
        artifact_dir = (repo_root / artifact_dir).resolve()
    deadline = Deadline(args.timeout_ms)
    audit = Audit(deadline)

    imported = audit.capture("public_facade_architecture", lambda: _import_control(repo_root))
    if imported is None:
        return _result(audit)
    _, control_module, facade_class = imported

    loaded = audit.capture("logical_registry_layout_and_load", lambda: _load_logical_records(control_module, artifact_dir))
    if loaded is None:
        return _result(audit)
    records, layout, physical_count = loaded
    audit.metrics.update(
        {
            "logical_registry_rows": len(records),
            "active_physical_layout": layout,
            "active_registry_data_file_count": physical_count,
            "serialized_registry_bytes": sum(path.stat().st_size for path in artifact_dir.glob("registry*.json*")),
        }
    )

    def shape_validation() -> None:
        seen: set[tuple[str, str]] = set()
        binding_ids: set[str] = set()
        for index, record in enumerate(records):
            if index % 500 == 0:
                deadline.check("record_shape")
            _validate_record(record)
            key = (str(record["canonical_component_id"]), str(record["semantic_version"]))
            if key in seen:
                raise InvariantError("CANONICAL_ID_VERSION_DUPLICATE", repr(key))
            seen.add(key)
            for binding in record["bindings"]:
                binding_id = str(binding["binding_id"])
                if binding_id in binding_ids:
                    raise InvariantError("BINDING_ID_DUPLICATE", binding_id)
                binding_ids.add(binding_id)

    audit.capture("record_schema_and_uniqueness", shape_validation)

    accepted_group_map: Mapping[tuple[str, ...], str] | None = None
    accepted_base_records = audit.capture(
        "accepted_merge_base_registry",
        lambda: _load_accepted_base_records(control_module, repo_root, deadline),
    )
    if accepted_base_records:
        accepted_group_map = audit.capture(
            "accepted_merge_base_rp5c_stable_group_map",
            lambda: _registry_rp5c_group_map(accepted_base_records),
        )
    canonical_artifact_dir = (repo_root / DEFAULT_ARTIFACT_DIR).resolve()
    if (
        accepted_group_map is None
        and artifact_dir != canonical_artifact_dir
        and canonical_artifact_dir.is_dir()
    ):
        accepted_loaded = audit.capture(
            "canonical_candidate_registry_for_layout_parity",
            lambda: _load_logical_records(control_module, canonical_artifact_dir),
        )
        if accepted_loaded is not None:
            accepted_group_map = audit.capture(
                "canonical_candidate_rp5c_stable_group_map",
                lambda: _registry_rp5c_group_map(accepted_loaded[0]),
            )

    graph_pair = audit.capture("requirements_canonical_and_acyclic", lambda: _graph(records))
    graph: dict[str, set[str]] = {}
    reverse: dict[str, set[str]] = {}
    if graph_pair is not None:
        graph, reverse = graph_pair
        order = audit.capture("requirements_topological_order", lambda: _topological(graph))
        if order is not None:
            audit.metrics["canonical_dag_nodes"] = len(order)
            audit.metrics["canonical_requirement_edges"] = sum(map(len, graph.values()))
    qku_keys = audit.capture("qku_context_root_unambiguity", lambda: _validate_qku_unambiguity(records))
    if qku_keys is not None:
        audit.metrics["active_qku_context_keys"] = qku_keys

    rp5c = audit.capture("rp5c_source_reconstruction", lambda: _rp5c_source(repo_root, deadline))
    if rp5c is not None:
        groups, _ = rp5c
        coverage = audit.capture(
            "rp5c_exact_import_and_member_coverage",
            lambda: _validate_rp5c_import(
                records, groups, deadline, accepted_group_map
            ),
        )
        if coverage is not None:
            audit.metrics["rp5c_canonical_imports"] = coverage[0]
            audit.metrics["rp5c_duplicate_members_covered"] = coverage[1]
    owner_count = audit.capture("owner_requirement_213_coverage", lambda: _owner_requirement_coverage(records))
    if owner_count is not None:
        audit.metrics["owner_requirement_ids"] = owner_count

    implementation = audit.capture("implementation_inventory_and_safe_dispatch", lambda: _validate_implementation_inventory(records))
    implementation_records: list[Mapping[str, Any]] = []
    if implementation is not None:
        counts, implementation_records = implementation
        audit.metrics["implementation_records"] = counts
    agent_count = audit.capture("pr165_d2_exact_agent_policies", lambda: _validate_agent_policies(records))
    if agent_count is not None:
        audit.metrics["pr165_d2_agent_ids"] = agent_count
    audit.capture("no_qpu_live_replay_paper_authority_claims", lambda: _validate_authority_absence(records))
    reuse = audit.capture("semantic_reuse_direct_proof_cases", lambda: _validate_semantic_reuse(records))
    if reuse is not None:
        audit.metrics["semantic_relation_counts"] = reuse

    template = next(
        (
            record
            for record in records
            if record.get("record_state") == "CANONICAL_ACCEPTED" and record.get("bindings")
        ),
        None,
    )
    if template is None:
        audit.fail("VALIDATION_TEMPLATE_MISSING", "no accepted bound record")
    else:
        defects = audit.capture("defect_injection_rejects_correct_reason", lambda: _defect_injection(template))
        if defects is not None:
            audit.metrics["defect_injections"] = defects
        memoization = audit.capture(
            "selected_subgraph_memoization_nonreuse_and_runtime_defects",
            lambda: _common_subgraph_probe(facade_class, template),
        )
        if memoization is not None:
            audit.metrics["common_subgraph_probe"] = memoization

    facade = audit.capture("public_facade_initialization", lambda: _construct_facade(facade_class, artifact_dir))
    invoked: list[tuple[Mapping[str, Any], Any, Any]] = []
    if facade is not None and implementation_records:
        fixture_result = audit.capture(
            "all_registered_implementation_fixtures_and_readiness",
            lambda: _invoke_implementation_fixtures(facade, control_module, implementation_records, deadline),
        )
        if fixture_result is not None:
            registered_count, facade_count, blocked_count, invoked = fixture_result
            audit.metrics.update(
                {
                    "registered_implementation_fixtures_invoked": registered_count,
                    "verified_facade_fixture_computations": facade_count,
                    "unverified_public_compute_fail_closed": blocked_count,
                }
            )
        if graph and invoked:
            subgraph = audit.capture(
                "closed_stack_selected_subgraph_compute",
                lambda: _validate_selected_subgraph(invoked, graph, len(records)),
            )
            if subgraph is not None:
                audit.metrics["representative_selected_subgraph_nodes"] = subgraph[0]
                audit.metrics["representative_selected_subgraph_requirements"] = subgraph[1]
        counters = audit.capture("zero_post_init_reads_scans_unrelated_execution", lambda: _validate_runtime_counters(facade))
        if counters is not None:
            audit.metrics.update(
                {
                    "runtime_registry_file_reads_after_initialization": counters[0],
                    "per_request_full_registry_iterations": counters[1],
                    "unrelated_component_executions": counters[2],
                }
            )

    delta = candidate = changed_id = None
    if reverse:
        delta_result = audit.capture("transient_delta_exactness", lambda: _validate_delta(control_module, records, reverse))
        if delta_result is not None:
            delta, candidate, changed_id = delta_result
            audit.metrics["delta_changed_component"] = changed_id
            audit.capture(
                "incremental_index_full_rebuild_parity_and_idempotence",
                lambda: _validate_index_parity(control_module, records, candidate, delta),
            )
    if template is not None:
        observations = audit.capture(
            "atomic_snapshot_replacement_concurrency",
            lambda: _bounded_snapshot_concurrency_probe(control_module, facade_class, template),
        )
        if observations is not None:
            audit.metrics["snapshot_concurrent_observations"] = observations

    compiler = audit.capture("compiler_source_order_and_failed_rollback", lambda: _compiler_mechanism_probe(control_module, records))
    if compiler is not None:
        audit.metrics["compiler_probe"] = compiler
    hardened = audit.capture(
        "hardened_compiler_storage_runtime_contract",
        lambda: _hardened_contract_probe(control_module, records),
    )
    if hardened is not None:
        audit.metrics["hardened_contract_probe"] = hardened

    if template is not None:
        mandatory_scale = audit.capture(
            "synthetic_2000_single_shard_scale_proof",
            lambda: _scale_probe(control_module, facade_class, template, 2_000, True, deadline),
        )
        if mandatory_scale is not None:
            audit.metrics["synthetic_2000_probe"] = mandatory_scale
        if args.scale_probe_records:
            larger = audit.capture(
                "larger_opt_in_scale_probe",
                lambda: _scale_probe(control_module, facade_class, template, args.scale_probe_records, False, deadline),
            )
            if larger is not None:
                audit.metrics["larger_scale_probe"] = larger
        else:
            audit.checks["larger_opt_in_scale_probe"] = True
            audit.metrics["larger_scale_probe"] = {"records": 0, "skipped": True}
    return _result(audit)


def _result(audit: Audit) -> dict[str, Any]:
    return {
        "validator": "PR169-QKU-COMP-CONTROL1",
        "validator_version": "5.1",
        "status": "PASS" if audit.error_count == 0 else "FAIL",
        "elapsed_ms": audit.deadline.elapsed_ms,
        "checks": audit.checks,
        "metrics": audit.metrics,
        "error_count": audit.error_count,
        "errors": audit.errors,
        "acceptance_report_trusted": False,
        "report_files_written": 0,
    }


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parse_args(argv)
        result = validate(args)
    except Exception as exc:  # last-resort JSON-only failure boundary
        result = {
            "validator": "PR169-QKU-COMP-CONTROL1",
            "validator_version": "5.1",
            "status": "FAIL",
            "error_count": 1,
            "errors": [{"code": "VALIDATOR_UNHANDLED", "detail": f"{type(exc).__name__}: {exc}"}],
            "acceptance_report_trusted": False,
            "report_files_written": 0,
        }
    sys.stdout.write(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False))
    sys.stdout.write("\n")
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
