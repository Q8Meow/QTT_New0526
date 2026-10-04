"""Shared validation path, process, receipt, and text-integrity support.

This module deliberately has no command-line entry point.  The central validation
runner remains the sole owner of command planning and aggregate acceptance.
"""

from __future__ import annotations

import ast
from contextlib import ExitStack, contextmanager
from dataclasses import asdict, dataclass, field, is_dataclass, replace
from contextvars import ContextVar
from types import MappingProxyType
import math
from datetime import UTC, datetime
import codecs
import errno
import io
import itertools
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from typing import BinaryIO, Callable, ContextManager, Iterable, Iterator, Mapping, Sequence


_COMMAND_PROJECTION_V1 = ContextVar("_COMMAND_PROJECTION_V1", default=None)


@contextmanager
def _command_projection_v1(projection):
    token = _COMMAND_PROJECTION_V1.set(projection)
    try:
        yield
    finally:
        _COMMAND_PROJECTION_V1.reset(token)


SCHEMA_VERSION = 1
DEFAULT_SCAN_CHUNK_BYTES = 1024 * 1024
PROCESS_ROOT_ENV = "QTT_VALIDATION_PROCESS_ROOT"
RUN_ID_ENV = "QTT_VALIDATION_RUN_ID"
EVIDENCE_ROOT_ENV = "QTT_VALIDATION_EVIDENCE_ROOT"
TERMINATION_GRACE_SECONDS = 5.0
OUTPUT_DRAIN_INITIAL_WAIT_SECONDS = 0.5
OUTPUT_DRAIN_COMPLETION_WAIT_SECONDS = 10.0
OUTPUT_POLL_INTERVAL_SECONDS = 0.01
FILESYSTEM_PROBE_BYTES = b"QTT_VALIDATION_FILESYSTEM_PROBE_V1\n"
VALIDATION_OUTPUT_DIR_NAME = "v"
PYTEST_BASETEMP_DIR_NAME = "p"
PYTEST_TMP_PATH_NAME_LIMIT = 30
STANDALONE_PYTEST_HELPER_PHASE = "standalone-pytest-helper"
_RUN_NAME_COUNTER = itertools.count()
_RUN_NAME_LOCK = threading.Lock()
# Process-local creation evidence, not a persisted authority marker. Only this
# allocating process may remove its own repository-local disposable run root.
_LOCAL_RUN_OWNERS: dict[str, tuple[int, int, int, str]] = {}
_LOCAL_RUN_NAME = re.compile(r"r\d{12}_\d+_\d+(?:_\d+)?\Z")
_LOCAL_LAYOUT_DIR = ".qtt"


MANAGED_TEXT_SUFFIXES = frozenset(
    {
        ".py",
        ".pyi",
        ".md",
        ".json",
        ".jsonl",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".txt",
        ".sh",
        ".ps1",
    }
)
MANAGED_TEXT_EXACT_FILES = frozenset({".gitattributes", ".gitignore"})

TERMINAL_NEWLINE_KINDS = frozenset({"NONE", "LF", "CRLF", "BARE_CR"})
CHANGE_CLASSES = frozenset(
    {
        "CLEAN_IDENTICAL",
        "NEW_CONTROLLED_TEXT_FILE",
        "DELETED_FILE",
        "RENAMED_FILE",
        "STAT_CACHE_ONLY_CHANGE",
        "EOL_REPRESENTATION_ONLY_CHANGE",
        "EOF_FINAL_NEWLINE_ONLY_CHANGE",
        "MIXED_LINE_ENDING_ERROR",
        "BARE_CR_ERROR",
        "REAL_WHITESPACE_ERROR",
        "SEMANTIC_TEXT_CHANGE",
        "BINARY_CHANGE",
        "ENCODING_OR_UNCLASSIFIED_CHANGE",
        "OUTSIDE_MANAGED_TEXT_POLICY_CHANGE",
        "LATENT_BASELINE_REPRESENTATION_DEBT",
        "PREEXISTING_BASELINE_TEXT_ANOMALY",
    }
)
SEMANTIC_CHANGE_CLASSES = frozenset(
    {
        "NEW_CONTROLLED_TEXT_FILE",
        "DELETED_FILE",
        "RENAMED_FILE",
        "REAL_WHITESPACE_ERROR",
        "SEMANTIC_TEXT_CHANGE",
    }
)
_PATH_STATES = frozenset({"NEW", "EXISTING", "DELETED", "RENAMED"})
_UTF8_DECODE_STATES = frozenset({"UTF8_VALID", "INVALID_UTF8", "NOT_TEXT_NUL"})


class ValidationReliabilityError(RuntimeError):
    """Typed fail-closed error raised by the shared reliability owner."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def _require_nonempty(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a nonempty string")


def _require_absolute(path: Path, field_name: str) -> None:
    if not path.is_absolute():
        raise ValueError(f"{field_name} must be absolute: {path}")


@dataclass(frozen=True, slots=True)
class FilesystemProbeReceiptV1:
    probe_root: Path
    created_directory: bool
    write_path: Path
    written_bytes: int
    readback_equal: bool
    renamed_path: Path
    rename_equal: bool
    unlink_success: bool
    directory_cleanup_success: bool
    failure_operation: str | None
    native_error_class: str | None

    def __post_init__(self) -> None:
        _require_absolute(self.probe_root, "probe_root")
        _require_absolute(self.write_path, "write_path")
        _require_absolute(self.renamed_path, "renamed_path")
        if self.written_bytes < 0:
            raise ValueError("written_bytes cannot be negative")
        if self.failure_operation is None and self.native_error_class is not None:
            raise ValueError("native_error_class requires failure_operation")
        if self.failure_operation is not None and not self.native_error_class:
            raise ValueError("a failed probe requires native_error_class")
        if not _path_is_relative_to(self.write_path, self.probe_root):
            raise ValueError("write_path must be inside probe_root")
        if not _path_is_relative_to(self.renamed_path, self.probe_root):
            raise ValueError("renamed_path must be inside probe_root")
        if self.failure_operation is None and not all(
            (
                self.created_directory,
                self.readback_equal,
                self.rename_equal,
                self.unlink_success,
                self.directory_cleanup_success,
            )
        ):
            raise ValueError("a passing filesystem probe requires every operation to pass")


@dataclass(frozen=True, slots=True)
class ValidationRunPathsV1:
    run_id: str
    process_child_name: str
    repo_root: Path
    process_root: Path
    validation_output_root: Path
    pytest_basetemp_root: Path
    evidence_root: Path
    process_root_is_external_to_repo: bool
    filesystem_probe_state: str
    deepest_projected_path: Path
    deepest_projected_path_text_length: int
    cleanup_target: Path

    def __post_init__(self) -> None:
        _require_nonempty(self.run_id, "run_id")
        _require_nonempty(self.process_child_name, "process_child_name")
        for field_name in (
            "repo_root",
            "process_root",
            "validation_output_root",
            "pytest_basetemp_root",
            "evidence_root",
            "deepest_projected_path",
            "cleanup_target",
        ):
            _require_absolute(getattr(self, field_name), field_name)
        local = (_lexically_inside_or_equal(self.process_root, self.repo_root)
                 or _path_is_relative_to(self.process_root.resolve(strict=False),
                                         self.repo_root.resolve(strict=False)))
        if type(self.process_root_is_external_to_repo) is not bool:
            raise ValueError("external-root observation must be an exact boolean")
        if self.process_root_is_external_to_repo is local:
            raise ValueError("process_root external observation differs from actual location")
        if local:
            _local_run_binding(self.repo_root, self.process_root,
                               self.evidence_root, self.run_id)
            if (self.validation_output_root != self.process_root / VALIDATION_OUTPUT_DIR_NAME
                    or self.pytest_basetemp_root != self.process_root / PYTEST_BASETEMP_DIR_NAME):
                raise ValueError("local validation/pytest roots must be the exact run slots")
        if self.process_root.name != self.process_child_name:
            raise ValueError("process_root must be the compact unique process child")
        if self.cleanup_target != self.process_root:
            raise ValueError("cleanup_target must equal the exact run-specific process_root")
        if self.deepest_projected_path_text_length != len(
            str(self.deepest_projected_path)
        ):
            raise ValueError("deepest projected path length is inconsistent")
        if not _path_is_relative_to(self.validation_output_root, self.process_root):
            raise ValueError("validation_output_root must be run-scoped")
        if not _path_is_relative_to(self.pytest_basetemp_root, self.process_root):
            raise ValueError("pytest_basetemp_root must be run-scoped")
        if not _path_is_relative_to(self.deepest_projected_path, self.process_root):
            raise ValueError("deepest_projected_path must be run-scoped")
        if _path_is_relative_to(self.evidence_root, self.process_root):
            raise ValueError("evidence_root must survive process-root cleanup")
        if self.filesystem_probe_state != "PASS":
            raise ValueError("constructed run paths require a passing filesystem probe")


@dataclass(frozen=True, slots=True)
class CommandExecutionReceiptV1:
    schema_version: int
    run_id: str
    phase: str
    command_index: int
    argv: tuple[str, ...]
    cwd: str
    pid: int | None
    platform: str
    start_time_utc: str
    end_time_utc: str
    elapsed_monotonic_seconds: float
    native_exit_code: int | None
    start_failure_class: str | None
    timeout_seconds_or_null: float | None
    timeout_state: str
    termination_state: str
    stdout_path: str
    stderr_path: str
    stdout_byte_count: int | None
    stderr_byte_count: int | None
    stdout_required_markers: tuple[str, ...]
    stdout_marker_state: str
    stderr_was_nonempty: bool | None
    failure_class: str | None

    registered_argv: tuple[str, ...] = field(default=(), kw_only=True)
    removed_environment_keys: tuple[str, ...] = field(default=(), kw_only=True)
    fixed_environment_controls: tuple[tuple[str, str], ...] = field(default=(), kw_only=True)
    output_observation: dict | None = field(default=None, kw_only=True)

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("unsupported command receipt schema_version")
        _require_nonempty(self.run_id, "run_id")
        _require_nonempty(self.phase, "phase")
        if self.command_index < 1:
            raise ValueError("command_index must be positive")
        if not self.argv or any(not isinstance(part, str) for part in self.argv):
            raise ValueError("argv must be a nonempty tuple of strings")
        if self.elapsed_monotonic_seconds < 0:
            raise ValueError("elapsed_monotonic_seconds cannot be negative")
        for stream in ("stdout", "stderr"):
            count = getattr(self, stream + "_byte_count")
            if count is None:
                if (self.failure_class is None or self.output_observation is None
                        or self.output_observation[stream]["retained_byte_count"] is not None
                        or self.output_observation[stream]["complete"]):
                    raise ValueError("unmeasured output requires failed incomplete bounded evidence")
            elif count < 0:
                raise ValueError("output byte counts cannot be negative")
        if self.stderr_was_nonempty != (None if self.stderr_byte_count is None else self.stderr_byte_count > 0):
            raise ValueError("stderr_was_nonempty is inconsistent")
        if self.start_failure_class is not None and self.pid is not None:
            raise ValueError("a start failure cannot claim a child PID")
        if self.pid is not None and self.pid < 1:
            raise ValueError("pid must be positive")
        if self.native_exit_code is not None and self.start_failure_class is not None:
            raise ValueError("a start failure cannot claim a native exit code")
        if self.start_failure_class is not None and self.failure_class != "ENGVR_PROCESS_START_FAILED":
            raise ValueError("a start failure requires ENGVR_PROCESS_START_FAILED")
        if self.timeout_seconds_or_null is not None and self.timeout_seconds_or_null <= 0:
            raise ValueError("timeout_seconds_or_null must be positive")
        if self.timeout_seconds_or_null is None and self.timeout_state != "NOT_CONFIGURED":
            raise ValueError("an unconfigured timeout requires NOT_CONFIGURED state")
        if self.timeout_seconds_or_null is not None and self.timeout_state not in {
            "NOT_TRIGGERED",
            "TRIGGERED",
        }:
            raise ValueError("configured timeout has an invalid state")
        for field_name in ("cwd", "platform", "start_time_utc", "end_time_utc"):
            _require_nonempty(getattr(self, field_name), field_name)
        _require_absolute(Path(self.cwd), "cwd")
        _require_absolute(Path(self.stdout_path), "stdout_path")
        _require_absolute(Path(self.stderr_path), "stderr_path")
        if self.failure_class is None and self.native_exit_code != 0:
            raise ValueError("a passing receipt requires native exit code zero")
        if self.failure_class is None and self.stdout_marker_state.startswith("MISSING:"):
            raise ValueError("a passing receipt cannot have missing required markers")


def _command_requires_process_retention_v1(receipt: object) -> bool:
    """Return an unresolved-process veto, never independent tree certification."""
    if type(receipt) is not CommandExecutionReceiptV1:
        return True
    if any(not hasattr(receipt, name) for name in CommandExecutionReceiptV1.__dataclass_fields__):
        return True
    for name in ("run_id", "phase", "cwd", "platform", "start_time_utc",
                 "end_time_utc", "stdout_path", "stderr_path", "stdout_marker_state",
                 "timeout_state", "termination_state"):
        value = getattr(receipt, name)
        if type(value) is not str or not value:
            return True
    if (type(receipt.schema_version) is not int or receipt.schema_version != SCHEMA_VERSION
            or type(receipt.command_index) is not int or receipt.command_index < 1):
        return True
    for name in ("argv", "registered_argv", "stdout_required_markers", "removed_environment_keys"):
        value = getattr(receipt, name)
        if type(value) is not tuple or any(type(part) is not str for part in value):
            return True
    if not receipt.argv or any(not part for part in receipt.argv):
        return True
    controls = receipt.fixed_environment_controls
    if (type(controls) is not tuple or any(type(pair) is not tuple or len(pair) != 2
            or any(type(part) is not str for part in pair) for pair in controls)):
        return True
    if (any(type(value) is not int or value < 0 for value in
            (receipt.stdout_byte_count, receipt.stderr_byte_count))
            or type(receipt.stderr_was_nonempty) is not bool
            or receipt.stderr_was_nonempty != (receipt.stderr_byte_count > 0)):
        return True
    elapsed = receipt.elapsed_monotonic_seconds
    timeout = receipt.timeout_seconds_or_null
    if (type(elapsed) not in (int, float)
            or (type(elapsed) is float and not math.isfinite(elapsed)) or elapsed < 0
            or (timeout is not None and (type(timeout) not in (int, float)
                or (type(timeout) is float and not math.isfinite(timeout)) or timeout <= 0))):
        return True
    if receipt.timeout_state not in (
            {"NOT_CONFIGURED"} if timeout is None else {"NOT_TRIGGERED", "TRIGGERED"}):
        return True
    for value in (receipt.start_failure_class, receipt.failure_class):
        if value is not None and (type(value) is not str or not value):
            return True
    state = receipt.termination_state
    if (receipt.failure_class == "ENGVR_PROCESS_TERMINATION_FAILED"
            or "UNPROVEN" in state):
        return True
    observation = receipt.output_observation
    if type(observation) is dict and 'windows_job' in observation:
        return _windows_job_projection_retains_v1(receipt, observation['windows_job'])
    if receipt.pid is None:
        return not (
            receipt.native_exit_code is None and receipt.start_failure_class is not None
            and receipt.failure_class == "ENGVR_PROCESS_START_FAILED"
            and state == "NOT_REQUIRED" and receipt.timeout_state != "TRIGGERED"
        )
    if (type(receipt.pid) is not int or receipt.pid <= 0
            or type(receipt.native_exit_code) is not int
            or receipt.start_failure_class is not None
            or receipt.failure_class == "ENGVR_PROCESS_START_FAILED"):
        return True
    if receipt.failure_class is None and receipt.native_exit_code != 0:
        return True
    if (receipt.failure_class == "ENGVR_PROCESS_TIMEOUT"
            and receipt.timeout_state != "TRIGGERED"):
        return True
    if state == "NOT_REQUIRED":
        return receipt.timeout_state == "TRIGGERED"
    # Only the original termination owner's ordered action grammar is terminal.
    # The final token is exact: PROVEN is also a substring of UNPROVEN.
    tokens = state.split(";")
    if tokens[-1] != "TERMINAL:PROVEN" or receipt.failure_class is None:
        return True
    actions = tokens[:-1]
    if receipt.platform == "nt":
        if len(actions) not in (1, 2):
            return True
        names = ("TASKKILL_T", "TASKKILL_T_F")
        if any(re.fullmatch(name + r":(?:0|-?[1-9][0-9]*)", action) is None
               for name, action in zip(names, actions)):
            return True
        return actions[-1].split(":", 1)[1] != "0"
    if receipt.platform == "posix":
        if len(actions) not in (1, 2):
            return True
        return any(re.fullmatch(name + r":(?:0|[A-Za-z_][A-Za-z0-9_]*)", action) is None
                   for name, action in zip(("SIGTERM", "SIGKILL"), actions))
    return True


@dataclass(frozen=True, slots=True)
class CommandEvidencePlanEntry:
    """Immutable in-memory command identity bound to one active run."""

    run_id: str
    phase: str
    command_index: int
    argv: tuple[str, ...]
    cwd: str

    def __post_init__(self) -> None:
        _require_nonempty(self.run_id, "run_id")
        _require_nonempty(self.phase, "phase")
        if self.command_index < 1:
            raise ValueError("command_index must be positive")
        if not self.argv or any(
            not isinstance(part, str) or not part
            for part in self.argv
        ):
            raise ValueError("planned argv must contain nonempty strings")
        _require_nonempty(self.cwd, "cwd")
        _require_absolute(Path(self.cwd), "cwd")


def build_command_evidence_plan(
    *,
    run_id: str,
    phase: str,
    commands: Sequence[Sequence[str]],
    cwd: Path,
) -> tuple[CommandEvidencePlanEntry, ...]:
    resolved_cwd = str(Path(cwd).resolve(strict=True))
    return tuple(
        CommandEvidencePlanEntry(
            run_id=run_id,
            phase=phase,
            command_index=index,
            argv=tuple(command),
            cwd=resolved_cwd,
        )
        for index, command in enumerate(commands, start=1)
    )


@dataclass(frozen=True, slots=True)
class ValidationCompletionReceiptV1:
    run_id: str
    phase: str
    command_count_planned: int
    command_count_started: int
    command_count_completed: int
    first_failed_command_index_or_null: int | None
    terminal_native_exit_code: int | None
    required_marker_state: str
    process_root_cleanup_state: str
    evidence_root_state: str
    text_integrity_preflight_state: str
    final_state: str

    def __post_init__(self) -> None:
        _require_nonempty(self.run_id, "run_id")
        _require_nonempty(self.phase, "phase")
        counts = (
            self.command_count_planned,
            self.command_count_started,
            self.command_count_completed,
        )
        if any(value < 0 for value in counts):
            raise ValueError("command counts cannot be negative")
        if not (
            self.command_count_completed
            <= self.command_count_started
            <= self.command_count_planned
        ):
            raise ValueError("command receipt counts are inconsistent")
        if self.first_failed_command_index_or_null is not None and not (
            1
            <= self.first_failed_command_index_or_null
            <= self.command_count_planned
        ):
            raise ValueError("first failed command index is outside the planned range")
        if (
            self.first_failed_command_index_or_null is not None
            and self.first_failed_command_index_or_null
            not in {
                self.command_count_started,
                self.command_count_started + 1,
            }
        ):
            raise ValueError(
                "a failed command must be the final started or next pre-start command"
            )
        if self.final_state not in {"PASS", "FAIL"}:
            raise ValueError("final_state must be PASS or FAIL")
        if self.evidence_root_state not in {"PRESENT", "MISSING"}:
            raise ValueError("evidence_root_state is invalid")
        if self.text_integrity_preflight_state not in {
            "PASS",
            "FAIL",
            "NOT_RUN",
            "NOT_APPLICABLE",
        }:
            raise ValueError("text_integrity_preflight_state is invalid")
        text_integrity_terminal = self.text_integrity_preflight_state == "PASS" or (
            self.phase == STANDALONE_PYTEST_HELPER_PHASE
            and self.text_integrity_preflight_state == "NOT_APPLICABLE"
        )
        if self.final_state == "PASS" and not (
            self.command_count_completed == self.command_count_planned
            and self.first_failed_command_index_or_null is None
            and self.terminal_native_exit_code == 0
            and self.required_marker_state == "PASS"
            and self.process_root_cleanup_state.startswith("PASS")
            and self.evidence_root_state == "PRESENT"
            and text_integrity_terminal
        ):
            raise ValueError("a passing completion receipt must prove every terminal invariant")


@dataclass(frozen=True, slots=True)
class TextByteProfileV1:
    byte_count: int
    contains_nul: bool
    utf8_decode_state: str
    standalone_lf_count: int
    crlf_count: int
    bare_cr_count: int
    total_line_break_count: int
    has_mixed_line_endings: bool
    terminal_newline_kind: str
    has_utf8_bom: bool
    scan_mode: str
    chunk_boundary_state_closed: bool

    def __post_init__(self) -> None:
        if self.byte_count < 0:
            raise ValueError("byte_count cannot be negative")
        for field_name in (
            "standalone_lf_count",
            "crlf_count",
            "bare_cr_count",
            "total_line_break_count",
        ):
            if getattr(self, field_name) < 0:
                raise ValueError(f"{field_name} cannot be negative")
        expected_total = (
            self.standalone_lf_count + self.crlf_count + self.bare_cr_count
        )
        if self.total_line_break_count != expected_total:
            raise ValueError("total_line_break_count is inconsistent")
        expected_mixed = sum(
            value > 0
            for value in (
                self.standalone_lf_count,
                self.crlf_count,
                self.bare_cr_count,
            )
        ) > 1
        if self.has_mixed_line_endings != expected_mixed:
            raise ValueError("has_mixed_line_endings is inconsistent")
        if self.terminal_newline_kind not in TERMINAL_NEWLINE_KINDS:
            raise ValueError("unknown terminal_newline_kind")
        if self.utf8_decode_state not in _UTF8_DECODE_STATES:
            raise ValueError("unknown utf8_decode_state")
        if self.scan_mode != "STREAMING_BOUNDED_MEMORY":
            raise ValueError("text scans must be streaming and bounded-memory")
        if not self.chunk_boundary_state_closed:
            raise ValueError("text scan ended with an open chunk-boundary state")
        if self.contains_nul and self.utf8_decode_state != "NOT_TEXT_NUL":
            raise ValueError("NUL-containing bytes cannot be classified as text")


@dataclass(frozen=True, slots=True)
class GitPathIntegrityV1:
    path: str
    path_state: str
    head_or_base_blob_state: str
    index_blob_state: str
    worktree_state: str
    git_status_state: str
    git_attribute_text: str
    git_attribute_eol: str
    managed_text_policy_state: str
    managed_text_policy_reason: str
    baseline_blob_ref: str
    baseline_profile: TextByteProfileV1 | None
    index_profile: TextByteProfileV1 | None
    worktree_profile: TextByteProfileV1 | None
    preexisting_baseline_representation_state: str
    representation_debt_resolution_state: str
    outside_policy_disposition: str
    change_class: str
    semantic_scope_member: bool
    publication_cleanliness_state: str
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_nonempty(self.path, "path")
        if self.path_state not in _PATH_STATES:
            raise ValueError(f"unsupported path_state: {self.path_state}")
        if self.change_class not in CHANGE_CLASSES:
            raise ValueError(f"unsupported change_class: {self.change_class}")
        if self.semantic_scope_member and self.change_class not in SEMANTIC_CHANGE_CLASSES:
            raise ValueError("representation-only classes cannot be semantic scope")


def _utc_now_text() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _path_is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
    except ValueError:
        return False
    return True


def normalize_repo_path(path: object) -> str:
    value = str(path).replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return str(PurePosixPath(value))


def is_managed_text_path(path: object) -> bool:
    normalized = normalize_repo_path(path)
    name = PurePosixPath(normalized).name
    return name in MANAGED_TEXT_EXACT_FILES or PurePosixPath(name).suffix.lower() in MANAGED_TEXT_SUFFIXES


@dataclass(frozen=True, slots=True)
class _TextStreamAnalysis:
    profile: TextByteProfileV1
    has_real_whitespace_error: bool


@dataclass(frozen=True, slots=True)
class _ReopenableByteSource:
    description: str
    opener: Callable[[], ContextManager[BinaryIO]]

    def open(self) -> ContextManager[BinaryIO]:
        return self.opener()


class _WorktreeSurfaceChanged(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class _WorktreeSurface:
    kind: str
    source: _ReopenableByteSource | None
    observed_stat: os.stat_result | None


def _stat_is_reparse_point(file_stat: os.stat_result) -> bool:
    attributes = int(getattr(file_stat, "st_file_attributes", 0))
    reparse_flag = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    return bool(attributes & reparse_flag)


def _same_observed_file(
    left: os.stat_result,
    right: os.stat_result,
) -> bool:
    stable_identity = (
        stat.S_IFMT(left.st_mode) == stat.S_IFMT(right.st_mode)
        and left.st_dev == right.st_dev
        and left.st_ino == right.st_ino
    )
    if not stable_identity:
        return False
    # Windows path-based lstat and handle-based fstat expose different ctime
    # semantics for the same file. Device/inode/type establish identity;
    # size and modification time retain the bounded content-race guard.
    return (
        left.st_size == right.st_size
        and left.st_mtime_ns == right.st_mtime_ns
    )


def _open_regular_worktree_descriptor(path: Path, *, nonblocking: bool = False) -> int:
    flags = os.O_RDONLY | int(getattr(os, "O_BINARY", 0))
    if os.name != "nt":
        flags |= int(getattr(os, "O_NOFOLLOW", 0))
        if nonblocking:
            flags |= int(getattr(os, "O_NONBLOCK", 0))
        return os.open(path, flags)

    # The Windows CRT has no O_NOFOLLOW.  Open the reparse point itself so a
    # link swap can be rejected from handle metadata without ever opening its
    # target, then transfer sole handle ownership to the returned CRT fd.
    import ctypes
    from ctypes import wintypes
    import msvcrt

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create_file.restype = wintypes.HANDLE
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = (wintypes.HANDLE,)
    close_handle.restype = wintypes.BOOL
    generic_read = 0x80000000
    share_read_write_delete = 0x00000001 | 0x00000002 | 0x00000004
    open_existing = 3
    open_reparse_point = 0x00200000
    sequential_scan = 0x08000000
    handle = create_file(
        str(path),
        generic_read,
        share_read_write_delete,
        None,
        open_existing,
        open_reparse_point | sequential_scan,
        None,
    )
    invalid_handle = ctypes.c_void_p(-1).value
    handle_value = int(handle) if handle is not None else 0
    if handle_value == invalid_handle:
        error_code = ctypes.get_last_error()
        raise OSError(error_code, ctypes.FormatError(error_code), str(path))
    try:
        return msvcrt.open_osfhandle(handle_value, flags)
    except BaseException:
        close_handle(handle)
        raise


def _regular_worktree_source(
    path: Path,
    observed: os.stat_result,
) -> _ReopenableByteSource:
    @contextmanager
    def open_regular() -> Iterator[BinaryIO]:
        try:
            current = os.lstat(path)
        except OSError as exc:
            raise _WorktreeSurfaceChanged(
                f"worktree regular file disappeared before open: {path}"
            ) from exc
        if (
            not stat.S_ISREG(current.st_mode)
            or _stat_is_reparse_point(current)
            or not _same_observed_file(observed, current)
        ):
            raise _WorktreeSurfaceChanged(
                f"worktree file type or identity changed before open: {path}"
            )
        try:
            descriptor = _open_regular_worktree_descriptor(path)
        except OSError as exc:
            raise _WorktreeSurfaceChanged(
                f"worktree no-follow open failed: {path}: {type(exc).__name__}"
            ) from exc
        try:
            opened = os.fstat(descriptor)
            if (
                not stat.S_ISREG(opened.st_mode)
                or _stat_is_reparse_point(opened)
                or not _same_observed_file(current, opened)
            ):
                raise _WorktreeSurfaceChanged(
                    f"worktree file changed between lstat and open: {path}"
                )
            with os.fdopen(descriptor, "rb", closefd=True) as stream:
                descriptor = -1
                yield stream
            try:
                final = os.lstat(path)
            except OSError as exc:
                raise _WorktreeSurfaceChanged(
                    f"worktree regular file disappeared after read: {path}"
                ) from exc
            if (
                not stat.S_ISREG(final.st_mode)
                or _stat_is_reparse_point(final)
                or not _same_observed_file(observed, final)
            ):
                raise _WorktreeSurfaceChanged(
                    f"worktree file changed during bounded read: {path}"
                )
        finally:
            if descriptor >= 0:
                os.close(descriptor)

    return _ReopenableByteSource(
        description=f"worktree-regular:{path}",
        opener=open_regular,
    )


def _symlink_worktree_source(
    path: Path,
    observed: os.stat_result,
) -> _ReopenableByteSource:
    @contextmanager
    def open_link_payload() -> Iterator[BinaryIO]:
        try:
            current = os.lstat(path)
            if (
                not stat.S_ISLNK(current.st_mode)
                or not _same_observed_file(observed, current)
            ):
                raise _WorktreeSurfaceChanged(
                    f"worktree symlink changed before payload inspection: {path}"
                )
            payload_text = os.readlink(path)
            payload = os.fsencode(payload_text)
        except _WorktreeSurfaceChanged:
            raise
        except OSError as exc:
            raise _WorktreeSurfaceChanged(
                f"worktree symlink payload inspection failed: {path}"
            ) from exc
        yield io.BytesIO(payload)
        try:
            final = os.lstat(path)
            final_payload = os.readlink(path)
        except OSError as exc:
            raise _WorktreeSurfaceChanged(
                f"worktree symlink changed after payload inspection: {path}"
            ) from exc
        if (
            not stat.S_ISLNK(final.st_mode)
            or not _same_observed_file(observed, final)
            or final_payload != payload_text
        ):
            raise _WorktreeSurfaceChanged(
                f"worktree symlink changed during payload inspection: {path}"
            )

    return _ReopenableByteSource(
        description=f"worktree-symlink-payload:{path}",
        opener=open_link_payload,
    )


def _resolve_no_follow_worktree_surface(path: Path) -> _WorktreeSurface:
    try:
        observed = os.lstat(path)
    except FileNotFoundError:
        return _WorktreeSurface("MISSING", None, None)
    except OSError as exc:
        raise ValidationReliabilityError(
            "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
            f"worktree lstat failed for {path}: {type(exc).__name__}: {exc}",
        ) from exc
    if stat.S_ISLNK(observed.st_mode):
        return _WorktreeSurface(
            "SYMLINK",
            _symlink_worktree_source(path, observed),
            observed,
        )
    if _stat_is_reparse_point(observed) or _path_is_junction(path):
        return _WorktreeSurface("REPARSE_POINT", None, observed)
    if stat.S_ISREG(observed.st_mode):
        return _WorktreeSurface(
            "REGULAR_FILE",
            _regular_worktree_source(path, observed),
            observed,
        )
    if stat.S_ISDIR(observed.st_mode):
        return _WorktreeSurface("DIRECTORY", None, observed)
    return _WorktreeSurface("SPECIAL_FILE", None, observed)


class _BoundedContentReader:
    """Reject unbounded content reads at the repository-classifier boundary."""

    def __init__(self, stream: BinaryIO, chunk_bound: int) -> None:
        if chunk_bound < 1:
            raise ValueError("chunk_bound must be positive")
        self._stream = stream
        self.chunk_bound = chunk_bound

    def read(self, size: int = -1) -> bytes:
        if size < 1 or size > self.chunk_bound:
            raise ValueError(
                "repository content reads must be positive and within the chunk bound"
            )
        data = self._stream.read(size)
        if not isinstance(data, bytes):
            raise TypeError("repository content streams must return bytes")
        return data


def _scan_text_stream_analysis(
    stream: BinaryIO,
    *,
    chunk_size: int,
) -> _TextStreamAnalysis:
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")
    byte_count = 0
    contains_nul = False
    standalone_lf_count = 0
    crlf_count = 0
    bare_cr_count = 0
    pending_cr = False
    initial = bytearray()
    tail = b""
    whitespace_tail = b""
    whitespace_error = False
    decoder = codecs.getincrementaldecoder("utf-8")("strict")
    decode_failed = False

    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        if not isinstance(chunk, bytes):
            raise TypeError("binary text scanner requires bytes")
        byte_count += len(chunk)
        contains_nul = contains_nul or b"\0" in chunk
        if len(initial) < 3:
            initial.extend(chunk[: 3 - len(initial)])
        tail = (tail + chunk)[-2:]
        whitespace_scan = whitespace_tail + chunk
        whitespace_error = whitespace_error or bool(
            re.search(br" +\t|[ \t](?:\r|\n)", whitespace_scan)
        )
        whitespace_tail = whitespace_scan[-1:]
        if not decode_failed:
            try:
                decoder.decode(chunk, final=False)
            except UnicodeDecodeError:
                decode_failed = True

        scan = (b"\r" if pending_cr else b"") + chunk
        pending_cr = scan.endswith(b"\r")
        if pending_cr:
            scan = scan[:-1]
        paired = scan.count(b"\r\n")
        crlf_count += paired
        bare_cr_count += scan.count(b"\r") - paired
        standalone_lf_count += scan.count(b"\n") - paired

    if pending_cr:
        bare_cr_count += 1
    if whitespace_tail in {b" ", b"\t"}:
        whitespace_error = True
    if not decode_failed:
        try:
            decoder.decode(b"", final=True)
        except UnicodeDecodeError:
            decode_failed = True

    if tail.endswith(b"\r\n"):
        terminal_kind = "CRLF"
    elif tail.endswith(b"\n"):
        terminal_kind = "LF"
    elif tail.endswith(b"\r"):
        terminal_kind = "BARE_CR"
    else:
        terminal_kind = "NONE"
    kinds = sum(
        value > 0
        for value in (standalone_lf_count, crlf_count, bare_cr_count)
    )
    decode_state = (
        "NOT_TEXT_NUL"
        if contains_nul
        else "INVALID_UTF8"
        if decode_failed
        else "UTF8_VALID"
    )
    profile = TextByteProfileV1(
        byte_count=byte_count,
        contains_nul=contains_nul,
        utf8_decode_state=decode_state,
        standalone_lf_count=standalone_lf_count,
        crlf_count=crlf_count,
        bare_cr_count=bare_cr_count,
        total_line_break_count=standalone_lf_count + crlf_count + bare_cr_count,
        has_mixed_line_endings=kinds > 1,
        terminal_newline_kind=terminal_kind,
        has_utf8_bom=bytes(initial) == codecs.BOM_UTF8,
        scan_mode="STREAMING_BOUNDED_MEMORY",
        chunk_boundary_state_closed=True,
    )
    return _TextStreamAnalysis(
        profile=profile,
        has_real_whitespace_error=whitespace_error,
    )


def scan_text_stream(
    stream: BinaryIO,
    *,
    chunk_size: int = DEFAULT_SCAN_CHUNK_BYTES,
) -> TextByteProfileV1:
    """Profile bytes without materializing the file and close CRLF boundaries."""

    return _scan_text_stream_analysis(stream, chunk_size=chunk_size).profile


def profile_bytes(data: bytes, *, chunk_size: int = DEFAULT_SCAN_CHUNK_BYTES) -> TextByteProfileV1:
    return scan_text_stream(io.BytesIO(data), chunk_size=chunk_size)


def profile_path(path: Path, *, chunk_size: int = DEFAULT_SCAN_CHUNK_BYTES) -> TextByteProfileV1:
    with path.open("rb") as stream:
        return scan_text_stream(stream, chunk_size=chunk_size)


def _bytes_source(data: bytes, *, description: str) -> _ReopenableByteSource:
    @contextmanager
    def open_bytes() -> Iterator[BinaryIO]:
        yield io.BytesIO(data)

    return _ReopenableByteSource(description=description, opener=open_bytes)


def _path_source(path: Path) -> _ReopenableByteSource:
    @contextmanager
    def open_path() -> Iterator[BinaryIO]:
        with path.open("rb") as stream:
            yield stream

    return _ReopenableByteSource(description=str(path), opener=open_path)


@contextmanager
def _open_bounded_source(
    source: _ReopenableByteSource,
    *,
    chunk_size: int,
) -> Iterator[_BoundedContentReader]:
    with source.open() as stream:
        yield _BoundedContentReader(stream, chunk_size)


def _analyze_source(
    source: _ReopenableByteSource,
    *,
    chunk_size: int,
) -> _TextStreamAnalysis:
    with _open_bounded_source(source, chunk_size=chunk_size) as stream:
        return _scan_text_stream_analysis(stream, chunk_size=chunk_size)


def _raw_chunks(
    stream: _BoundedContentReader,
    *,
    chunk_size: int,
) -> Iterator[bytes]:
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            return
        yield chunk


def _normalized_chunks(
    stream: _BoundedContentReader,
    *,
    chunk_size: int,
) -> Iterator[bytes]:
    pending_cr = False
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        normalized = bytearray()
        for value in chunk:
            if pending_cr:
                normalized.append(0x0A)
                pending_cr = False
                if value == 0x0A:
                    continue
            if value == 0x0D:
                pending_cr = True
            else:
                normalized.append(value)
        if normalized:
            yield bytes(normalized)
    if pending_cr:
        yield b"\n"


def _without_one_terminal_lf(chunks: Iterable[bytes]) -> Iterator[bytes]:
    pending: bytes | None = None
    for chunk in chunks:
        if not chunk:
            continue
        if pending is not None:
            yield pending
        pending = chunk
    if pending is None:
        return
    if pending.endswith(b"\n"):
        pending = pending[:-1]
    if pending:
        yield pending


def _chunk_sequences_equal(
    left_chunks: Iterable[bytes],
    right_chunks: Iterable[bytes],
) -> bool:
    left_iterator = iter(left_chunks)
    right_iterator = iter(right_chunks)
    left = b""
    right = b""
    left_offset = 0
    right_offset = 0
    left_done = False
    right_done = False
    equal = True
    while not (left_done and right_done):
        if left_offset == len(left) and not left_done:
            try:
                left = next(left_iterator)
                left_offset = 0
            except StopIteration:
                left = b""
                left_done = True
        if right_offset == len(right) and not right_done:
            try:
                right = next(right_iterator)
                right_offset = 0
            except StopIteration:
                right = b""
                right_done = True
        left_remaining = len(left) - left_offset
        right_remaining = len(right) - right_offset
        if left_done and right_done:
            break
        if left_done and right_remaining:
            equal = False
            right_offset = len(right)
            continue
        if right_done and left_remaining:
            equal = False
            left_offset = len(left)
            continue
        if not left_remaining or not right_remaining:
            continue
        compared = min(left_remaining, right_remaining)
        if left[left_offset : left_offset + compared] != right[
            right_offset : right_offset + compared
        ]:
            equal = False
        left_offset += compared
        right_offset += compared
    return equal


def _sources_equal(
    left: _ReopenableByteSource,
    right: _ReopenableByteSource,
    *,
    chunk_size: int,
) -> bool:
    with ExitStack() as stack:
        left_stream = stack.enter_context(
            _open_bounded_source(left, chunk_size=chunk_size)
        )
        right_stream = stack.enter_context(
            _open_bounded_source(right, chunk_size=chunk_size)
        )
        return _chunk_sequences_equal(
            _raw_chunks(left_stream, chunk_size=chunk_size),
            _raw_chunks(right_stream, chunk_size=chunk_size),
        )


def _optional_sources_equal(
    left: _ReopenableByteSource | None,
    right: _ReopenableByteSource | None,
    *,
    chunk_size: int,
) -> bool:
    if left is None or right is None:
        return left is right
    return _sources_equal(left, right, chunk_size=chunk_size)


def _normalized_sources_equal(
    left: _ReopenableByteSource,
    right: _ReopenableByteSource,
    *,
    chunk_size: int,
    strip_one_terminal_lf: bool = False,
) -> bool:
    with ExitStack() as stack:
        left_stream = stack.enter_context(
            _open_bounded_source(left, chunk_size=chunk_size)
        )
        right_stream = stack.enter_context(
            _open_bounded_source(right, chunk_size=chunk_size)
        )
        left_chunks: Iterable[bytes] = _normalized_chunks(
            left_stream,
            chunk_size=chunk_size,
        )
        right_chunks: Iterable[bytes] = _normalized_chunks(
            right_stream,
            chunk_size=chunk_size,
        )
        if strip_one_terminal_lf:
            left_chunks = _without_one_terminal_lf(left_chunks)
            right_chunks = _without_one_terminal_lf(right_chunks)
        return _chunk_sequences_equal(left_chunks, right_chunks)


def _sources_eof_only_difference(
    left: _ReopenableByteSource,
    right: _ReopenableByteSource,
    left_profile: TextByteProfileV1,
    right_profile: TextByteProfileV1,
    *,
    chunk_size: int,
) -> bool:
    if _terminal_present(left_profile) == _terminal_present(right_profile):
        return False
    return _normalized_sources_equal(
        left,
        right,
        chunk_size=chunk_size,
        strip_one_terminal_lf=True,
    )


def normalize_text_bytes_for_comparison(data: bytes) -> bytes:
    """Pure comparison-only EOL normalization; this function never writes."""

    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _has_real_whitespace_error(data: bytes) -> bool:
    normalized = normalize_text_bytes_for_comparison(data)
    for line in normalized.split(b"\n"):
        if line.endswith((b" ", b"\t")) or re.search(br" +\t", line):
            return True
    return False


def _terminal_present(profile: TextByteProfileV1) -> bool:
    return profile.terminal_newline_kind != "NONE"


def _eof_only_difference(left: bytes, right: bytes) -> bool:
    normalized_left = normalize_text_bytes_for_comparison(left)
    normalized_right = normalize_text_bytes_for_comparison(right)
    if normalized_left == normalized_right:
        return False
    left_without = normalized_left[:-1] if normalized_left.endswith(b"\n") else normalized_left
    right_without = normalized_right[:-1] if normalized_right.endswith(b"\n") else normalized_right
    return left_without == right_without and (
        normalized_left.endswith(b"\n") != normalized_right.endswith(b"\n")
    )


def _baseline_representation_state(profile: TextByteProfileV1 | None) -> str:
    if profile is None:
        return "NOT_APPLICABLE"
    if (
        profile.contains_nul
        or profile.utf8_decode_state != "UTF8_VALID"
        or profile.has_mixed_line_endings
        or profile.bare_cr_count
        or profile.has_utf8_bom
    ):
        return "HARD_BASELINE_ANOMALY"
    if profile.crlf_count and not profile.standalone_lf_count:
        return "LATENT_CONSISTENT_CRLF_DEBT"
    if profile.byte_count and profile.terminal_newline_kind == "NONE":
        return "LATENT_MISSING_TERMINAL_LF_DEBT"
    return "CANONICAL_ALREADY_LF"


def _controlled_target_failure(profile: TextByteProfileV1) -> str | None:
    if profile.has_mixed_line_endings:
        return "MIXED_LINE_ENDING_ERROR"
    if profile.bare_cr_count:
        return "BARE_CR_ERROR"
    if (
        profile.contains_nul
        or profile.utf8_decode_state != "UTF8_VALID"
        or profile.has_utf8_bom
    ):
        return "ENCODING_OR_UNCLASSIFIED_CHANGE"
    return None


def _attributes_declare_text_handling(text_value: str, eol_value: str) -> bool:
    return text_value in {"set", "auto"} or eol_value in {"lf", "crlf"}


def classify_byte_surfaces(
    *,
    path: str,
    baseline_bytes: bytes | None,
    index_bytes: bytes | None,
    worktree_bytes: bytes | None,
    path_state: str = "EXISTING",
    git_status_state: str = "DIRTY",
    git_attribute_text: str = "unspecified",
    git_attribute_eol: str = "unspecified",
    git_unstaged_diff_state: str = "UNKNOWN",
    git_staged_diff_state: str = "UNKNOWN",
    baseline_blob_ref: str = "",
    authorized: bool = False,
) -> GitPathIntegrityV1:
    """Pure small-fixture interface for the shared streaming classifier."""

    return _classify_stream_surfaces(
        path=path,
        baseline_source=(
            _bytes_source(baseline_bytes, description=f"{path}:baseline")
            if baseline_bytes is not None
            else None
        ),
        index_source=(
            _bytes_source(index_bytes, description=f"{path}:index")
            if index_bytes is not None
            else None
        ),
        worktree_source=(
            _bytes_source(worktree_bytes, description=f"{path}:worktree")
            if worktree_bytes is not None
            else None
        ),
        path_state=path_state,
        git_status_state=git_status_state,
        git_attribute_text=git_attribute_text,
        git_attribute_eol=git_attribute_eol,
        git_unstaged_diff_state=git_unstaged_diff_state,
        git_staged_diff_state=git_staged_diff_state,
        baseline_blob_ref=baseline_blob_ref,
        authorized=authorized,
        chunk_size=DEFAULT_SCAN_CHUNK_BYTES,
    )


def _classify_stream_surfaces(
    *,
    path: str,
    baseline_source: _ReopenableByteSource | None,
    index_source: _ReopenableByteSource | None,
    worktree_source: _ReopenableByteSource | None,
    path_state: str,
    git_status_state: str,
    git_attribute_text: str,
    git_attribute_eol: str,
    git_unstaged_diff_state: str,
    git_staged_diff_state: str,
    baseline_blob_ref: str,
    authorized: bool,
    chunk_size: int,
    worktree_state_override: str | None = None,
    forced_decision_reason: str | None = None,
) -> GitPathIntegrityV1:
    """Classify reopenable byte surfaces with fixed fail-closed precedence."""

    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")
    for state_name, state_value in (
        ("git_unstaged_diff_state", git_unstaged_diff_state),
        ("git_staged_diff_state", git_staged_diff_state),
    ):
        if state_value not in {"CLEAN", "DIRTY", "UNKNOWN"}:
            raise ValueError(f"unsupported {state_name}: {state_value}")
    normalized_path = normalize_repo_path(path)
    managed = is_managed_text_path(normalized_path)
    baseline_analysis = (
        _analyze_source(baseline_source, chunk_size=chunk_size)
        if baseline_source is not None
        else None
    )
    index_analysis = (
        _analyze_source(index_source, chunk_size=chunk_size)
        if index_source is not None
        else None
    )
    worktree_analysis = (
        _analyze_source(worktree_source, chunk_size=chunk_size)
        if worktree_source is not None
        else None
    )
    baseline_profile = baseline_analysis.profile if baseline_analysis else None
    index_profile = index_analysis.profile if index_analysis else None
    worktree_profile = worktree_analysis.profile if worktree_analysis else None
    baseline_state = _baseline_representation_state(baseline_profile)
    baseline_index_equal = _optional_sources_equal(
        baseline_source,
        index_source,
        chunk_size=chunk_size,
    )
    index_worktree_equal = _optional_sources_equal(
        index_source,
        worktree_source,
        chunk_size=chunk_size,
    )
    reason_codes: list[str] = []
    outside_disposition = "NOT_APPLICABLE"
    debt_state = "NOT_APPLICABLE"

    def result(
        change_class: str,
        *,
        semantic: bool = False,
        cleanliness: str = "PASS",
        reasons: Iterable[str] = (),
        debt: str = debt_state,
        outside: str = outside_disposition,
    ) -> GitPathIntegrityV1:
        return GitPathIntegrityV1(
            path=normalized_path,
            path_state=path_state,
            head_or_base_blob_state=(
                "PRESENT" if baseline_source is not None else "ABSENT"
            ),
            index_blob_state="PRESENT" if index_source is not None else "ABSENT",
            worktree_state=(
                worktree_state_override
                if worktree_state_override is not None
                else "PRESENT"
                if worktree_source is not None
                else "ABSENT"
            ),
            git_status_state=git_status_state,
            git_attribute_text=git_attribute_text,
            git_attribute_eol=git_attribute_eol,
            managed_text_policy_state=(
                "MANAGED" if managed else "OUTSIDE_MANAGED_POLICY"
            ),
            managed_text_policy_reason=(
                "EXACT_FILE"
                if PurePosixPath(normalized_path).name in MANAGED_TEXT_EXACT_FILES
                else "APPROVED_SUFFIX"
                if managed
                else "FIXED_POLICY_SET_EXCLUDES_PATH"
            ),
            baseline_blob_ref=baseline_blob_ref,
            baseline_profile=baseline_profile,
            index_profile=index_profile,
            worktree_profile=worktree_profile,
            preexisting_baseline_representation_state=baseline_state,
            representation_debt_resolution_state=debt,
            outside_policy_disposition=outside,
            change_class=change_class,
            semantic_scope_member=semantic and authorized,
            publication_cleanliness_state=cleanliness,
            reason_codes=tuple(dict.fromkeys((*reason_codes, *reasons))),
        )

    if managed and baseline_state == "HARD_BASELINE_ANOMALY":
        return result(
            "PREEXISTING_BASELINE_TEXT_ANOMALY",
            cleanliness="FAIL_DECISION_REQUIRED",
            reasons=("PREEXISTING_BASELINE_TEXT_ANOMALY",),
        )

    if forced_decision_reason is not None:
        return result(
            "ENCODING_OR_UNCLASSIFIED_CHANGE",
            cleanliness="FAIL_DECISION_REQUIRED",
            reasons=(forced_decision_reason,),
        )

    git_canonical_content_clean = (
        git_unstaged_diff_state == "CLEAN"
        and git_staged_diff_state == "CLEAN"
    )
    worktree_filter_equivalent = False
    if (
        path_state == "EXISTING"
        and baseline_source is not None
        and index_source is not None
        and worktree_source is not None
        and baseline_index_equal
        and not index_worktree_equal
        and git_canonical_content_clean
        and _attributes_declare_text_handling(
            git_attribute_text,
            git_attribute_eol,
        )
    ):
        profiles = (baseline_profile, index_profile, worktree_profile)
        if all(
            profile is not None and _controlled_target_failure(profile) is None
            for profile in profiles
        ):
            assert index_profile is not None and worktree_profile is not None
            worktree_filter_equivalent = (
                _terminal_present(index_profile) == _terminal_present(worktree_profile)
                and _normalized_sources_equal(
                    index_source,
                    worktree_source,
                    chunk_size=chunk_size,
                )
            )
    if worktree_filter_equivalent:
        if git_status_state == "CLEAN":
            if managed and baseline_state.startswith("LATENT_"):
                return result(
                    "LATENT_BASELINE_REPRESENTATION_DEBT",
                    cleanliness="CLEAN_PRESERVE_BYTES",
                    debt="PRESERVE_BYTES",
                    reasons=(baseline_state, "WORKTREE_FILTER_EQUIVALENT_CLEAN"),
                )
            return result(
                "CLEAN_IDENTICAL",
                cleanliness="CLEAN",
                reasons=("WORKTREE_FILTER_EQUIVALENT_CLEAN",),
                outside=(
                    outside_disposition
                    if managed
                    else "OUTSIDE_MANAGED_TEXT_POLICY_UNCHANGED"
                ),
            )
        return result(
            "STAT_CACHE_ONLY_CHANGE",
            cleanliness="DIRTY_MUST_BE_REFRESHED",
            reasons=(
                "GIT_CANONICAL_CONTENT_IDENTICAL",
                "WORKTREE_FILTER_EQUIVALENT_CLEAN",
            ),
            outside=(
                outside_disposition
                if managed
                else "OUTSIDE_MANAGED_TEXT_POLICY_UNCHANGED"
            ),
        )

    all_existing_surfaces_identical = (
        path_state == "EXISTING"
        and baseline_source is not None
        and index_source is not None
        and worktree_source is not None
        and baseline_index_equal
        and index_worktree_equal
    )
    if all_existing_surfaces_identical:
        if git_status_state == "CLEAN":
            if managed and baseline_state.startswith("LATENT_"):
                return result(
                    "LATENT_BASELINE_REPRESENTATION_DEBT",
                    cleanliness="CLEAN_PRESERVE_BYTES",
                    debt="PRESERVE_BYTES",
                    reasons=(baseline_state,),
                )
            return result(
                "CLEAN_IDENTICAL",
                cleanliness="CLEAN",
                outside=(
                    outside_disposition
                    if managed
                    else "OUTSIDE_MANAGED_TEXT_POLICY_UNCHANGED"
                ),
            )
        return result(
            "STAT_CACHE_ONLY_CHANGE",
            cleanliness="DIRTY_MUST_BE_REFRESHED",
            reasons=(
                "AUTHORITATIVE_BYTES_IDENTICAL",
                *(("GIT_CANONICAL_CONTENT_IDENTICAL",) if git_canonical_content_clean else ()),
            ),
            outside=(
                outside_disposition
                if managed
                else "OUTSIDE_MANAGED_TEXT_POLICY_UNCHANGED"
            ),
        )

    if not managed:
        profiles = tuple(
            item
            for item in (baseline_profile, index_profile, worktree_profile)
            if item is not None
        )
        if any(item.contains_nul for item in profiles):
            return result(
                "BINARY_CHANGE",
                cleanliness="FAIL_DECISION_REQUIRED",
                reasons=("OUTSIDE_POLICY_BINARY_OWNER_REQUIRED",),
                outside="NOT_TEXT_OR_BINARY_BY_CANONICAL_OWNER",
            )
        return result(
            "OUTSIDE_MANAGED_TEXT_POLICY_CHANGE",
            cleanliness="FAIL_DECISION_REQUIRED",
            reasons=("OUTSIDE_MANAGED_TEXT_POLICY_REQUIRES_OWNER_DECISION",),
            outside="OUTSIDE_MANAGED_TEXT_POLICY_REQUIRES_OWNER_DECISION",
        )

    for surface_name, surface_profile in (
        ("INDEX", index_profile),
        ("WORKTREE", worktree_profile),
    ):
        if surface_profile is None:
            continue
        target_failure = _controlled_target_failure(surface_profile)
        if target_failure is not None:
            return result(
                target_failure,
                cleanliness="FAIL",
                reasons=(target_failure, f"{surface_name}_SURFACE"),
            )

    target_source = index_source
    target_analysis = index_analysis
    if baseline_index_equal and not index_worktree_equal:
        target_source = worktree_source
        target_analysis = worktree_analysis
    target_profile = target_analysis.profile if target_analysis else None

    secondary_worktree_failure = False
    if (
        not baseline_index_equal
        and index_source is not None
        and worktree_source is not None
        and not index_worktree_equal
    ):
        assert index_profile is not None and worktree_profile is not None
        if _sources_eof_only_difference(
            index_source,
            worktree_source,
            index_profile,
            worktree_profile,
            chunk_size=chunk_size,
        ):
            reason_codes.append("WORKTREE_EOF_DIFFERS_FROM_INDEX")
            secondary_worktree_failure = True
        elif not _normalized_sources_equal(
            index_source,
            worktree_source,
            chunk_size=chunk_size,
        ):
            reason_codes.append("WORKTREE_SEMANTICALLY_DIFFERS_FROM_INDEX")
            secondary_worktree_failure = True
        else:
            reason_codes.append("WORKTREE_REPRESENTATION_DIFFERS_FROM_INDEX")

    if path_state == "DELETED" or (
        baseline_source is not None
        and index_source is None
        and worktree_source is None
    ):
        return result(
            "DELETED_FILE",
            semantic=True,
            cleanliness="PASS" if authorized else "FAIL",
            reasons=(() if authorized else ("SEMANTIC_PATH_OUTSIDE_ALLOWLIST",)),
        )

    if path_state == "RENAMED":
        if target_profile is None or target_analysis is None:
            return result(
                "ENCODING_OR_UNCLASSIFIED_CHANGE",
                cleanliness="FAIL",
                reasons=("RENAMED_PATH_HAS_NO_READABLE_BYTE_SURFACE",),
            )
        rename_reasons: list[str] = []
        rename_cleanliness = "PASS" if authorized else "FAIL"
        if target_profile.terminal_newline_kind != "LF":
            rename_reasons.append("CHANGED_CONTROLLED_TEXT_REQUIRES_CANONICAL_LF")
            rename_cleanliness = "FAIL"
        if secondary_worktree_failure:
            rename_cleanliness = "FAIL"
        if target_analysis.has_real_whitespace_error:
            return result(
                "REAL_WHITESPACE_ERROR",
                semantic=True,
                cleanliness="FAIL",
                reasons=("REAL_WHITESPACE_ERROR", *rename_reasons),
            )
        return result(
            "RENAMED_FILE",
            semantic=True,
            cleanliness=rename_cleanliness,
            reasons=(
                *rename_reasons,
                *(() if authorized else ("SEMANTIC_PATH_OUTSIDE_ALLOWLIST",)),
            ),
        )

    if path_state == "NEW" or baseline_source is None:
        if target_profile is None or target_analysis is None:
            return result(
                "ENCODING_OR_UNCLASSIFIED_CHANGE",
                cleanliness="FAIL",
                reasons=("NEW_PATH_HAS_NO_READABLE_BYTE_SURFACE",),
            )
        new_reasons: list[str] = []
        new_cleanliness = "PASS" if authorized else "FAIL"
        if target_profile.terminal_newline_kind != "LF":
            new_reasons.append("NEW_CONTROLLED_TEXT_REQUIRES_CANONICAL_LF")
            new_cleanliness = "FAIL"
        if target_analysis.has_real_whitespace_error:
            return result(
                "REAL_WHITESPACE_ERROR",
                semantic=True,
                cleanliness="FAIL",
                reasons=("REAL_WHITESPACE_ERROR", *new_reasons),
            )
        return result(
            "NEW_CONTROLLED_TEXT_FILE",
            semantic=True,
            cleanliness=new_cleanliness,
            reasons=(
                *new_reasons,
                *(() if authorized else ("SEMANTIC_PATH_OUTSIDE_ALLOWLIST",)),
            ),
        )

    if target_source is None or target_profile is None or target_analysis is None:
        return result(
            "ENCODING_OR_UNCLASSIFIED_CHANGE",
            cleanliness="FAIL",
            reasons=("MISSING_AUTHORITATIVE_TARGET_SURFACE",),
        )

    if baseline_index_equal and (
        worktree_source is None or index_worktree_equal
    ):
        if git_status_state == "CLEAN":
            if baseline_state.startswith("LATENT_"):
                return result(
                    "LATENT_BASELINE_REPRESENTATION_DEBT",
                    cleanliness="CLEAN_PRESERVE_BYTES",
                    debt="PRESERVE_BYTES",
                    reasons=(baseline_state,),
                )
            return result("CLEAN_IDENTICAL", cleanliness="CLEAN")
        return result(
            "STAT_CACHE_ONLY_CHANGE",
            cleanliness="DIRTY_MUST_BE_REFRESHED",
            reasons=("AUTHORITATIVE_BYTES_IDENTICAL",),
        )

    assert baseline_source is not None and baseline_profile is not None
    normalized_equal = _normalized_sources_equal(
        baseline_source,
        target_source,
        chunk_size=chunk_size,
    )
    if normalized_equal:
        if baseline_state.startswith("LATENT_"):
            return result(
                "LATENT_BASELINE_REPRESENTATION_DEBT",
                cleanliness="DIRTY_MUST_BE_RESOLVED",
                debt="UNAUTHORIZED_REPRESENTATION_ONLY_RESOLUTION",
                reasons=(baseline_state, "NO_INDEPENDENT_SEMANTIC_DIFF"),
            )
        if _terminal_present(baseline_profile) == _terminal_present(target_profile):
            return result(
                "EOL_REPRESENTATION_ONLY_CHANGE",
                cleanliness="DIRTY_MUST_BE_RESOLVED",
                reasons=("NORMALIZED_BYTES_IDENTICAL",),
            )

    if _sources_eof_only_difference(
        baseline_source,
        target_source,
        baseline_profile,
        target_profile,
        chunk_size=chunk_size,
    ):
        if baseline_state.startswith("LATENT_"):
            return result(
                "LATENT_BASELINE_REPRESENTATION_DEBT",
                cleanliness="DIRTY_MUST_BE_RESOLVED",
                debt="UNAUTHORIZED_REPRESENTATION_ONLY_RESOLUTION",
                reasons=(baseline_state, "NO_INDEPENDENT_SEMANTIC_DIFF"),
            )
        return result(
            "EOF_FINAL_NEWLINE_ONLY_CHANGE",
            cleanliness="DIRTY_MUST_BE_RESOLVED",
            reasons=("CONTENT_EQUAL_EXCEPT_TERMINAL_NEWLINE",),
        )

    if target_analysis.has_real_whitespace_error:
        whitespace_reasons = ["REAL_WHITESPACE_ERROR"]
        if target_profile.terminal_newline_kind != "LF":
            whitespace_reasons.append("CHANGED_CONTROLLED_TEXT_REQUIRES_CANONICAL_LF")
        if secondary_worktree_failure:
            whitespace_reasons.append("WORKTREE_PUBLICATION_SURFACE_DIRTY")
        return result(
            "REAL_WHITESPACE_ERROR",
            semantic=True,
            cleanliness="FAIL",
            reasons=whitespace_reasons,
            debt=(
                "RESOLVED_WITH_INDEPENDENT_SEMANTIC_EDIT"
                if baseline_state.startswith("LATENT_")
                and target_profile.terminal_newline_kind == "LF"
                and target_profile.crlf_count == 0
                else "UNRESOLVED_DURING_SEMANTIC_EDIT"
                if baseline_state.startswith("LATENT_")
                else "NOT_APPLICABLE"
            ),
        )

    semantic_reasons: list[str] = []
    semantic_cleanliness = "PASS" if authorized else "FAIL"
    if target_profile.terminal_newline_kind != "LF":
        semantic_reasons.append("CHANGED_CONTROLLED_TEXT_REQUIRES_CANONICAL_LF")
        semantic_cleanliness = "FAIL"
    if secondary_worktree_failure:
        semantic_reasons.append("WORKTREE_PUBLICATION_SURFACE_DIRTY")
        semantic_cleanliness = "FAIL"
    return result(
        "SEMANTIC_TEXT_CHANGE",
        semantic=True,
        cleanliness=semantic_cleanliness,
        reasons=(
            *semantic_reasons,
            *(() if authorized else ("SEMANTIC_PATH_OUTSIDE_ALLOWLIST",)),
        ),
        debt=(
            "RESOLVED_WITH_INDEPENDENT_SEMANTIC_EDIT"
            if baseline_state.startswith("LATENT_")
            and target_profile.terminal_newline_kind == "LF"
            and target_profile.crlf_count == 0
            else "UNRESOLVED_DURING_SEMANTIC_EDIT"
            if baseline_state.startswith("LATENT_")
            else "NOT_APPLICABLE"
        ),
    )


def _git_bytes(
    repo_root: Path,
    args: Sequence[str],
    *,
    check: bool = True,
    environment: Mapping[str, str] | None = None,
) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        env=None if environment is None else dict(environment),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and completed.returncode:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise ValidationReliabilityError(
            "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
            detail or f"git {' '.join(args)} failed with {completed.returncode}",
        )
    return completed.stdout if completed.returncode == 0 else b""


def observe_git_text_config(repo_root: Path) -> dict[str, dict[str, str]]:
    """Read text-related Git configuration without setting repository state."""

    observations: dict[str, dict[str, str]] = {}
    for key in ("core.autocrlf", "core.eol", "core.safecrlf"):
        completed = subprocess.run(
            ["git", "config", "--show-origin", "--get", key],
            cwd=repo_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if completed.returncode == 1:
            observations[key] = {
                "state": "ABSENT",
                "origin": "",
                "value": "",
            }
            continue
        if completed.returncode != 0:
            raise ValidationReliabilityError(
                "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
                f"git config observation failed for {key}: {completed.stderr.strip()}",
            )
        rendered = completed.stdout.rstrip("\r\n")
        origin, separator, value = rendered.partition("\t")
        if not separator:
            origin, separator, value = rendered.partition(" ")
        observations[key] = {
            "state": "PRESENT",
            "origin": origin,
            "value": value,
        }
    return observations


def resolve_verified_baseline(repo_root: Path) -> str:
    root = repo_root.resolve()
    remote_main = _git_bytes(
        root,
        ("rev-parse", "--verify", "refs/remotes/origin/main^{commit}"),
        check=False,
    ).strip()
    if remote_main:
        merge_base = _git_bytes(root, ("merge-base", "refs/remotes/origin/main", "HEAD")).strip()
        if merge_base:
            return merge_base.decode("ascii", "strict")
    local_main = _git_bytes(
        root,
        ("rev-parse", "--verify", "refs/heads/main^{commit}"),
        check=False,
    ).strip()
    if local_main and remote_main and local_main == remote_main:
        return local_main.decode("ascii", "strict")
    raise ValidationReliabilityError(
        "ENGVR_REMOTE_STATE_DRIFT",
        "verified origin/main merge-base is unavailable",
    )


def _git_blob_source(
    repo_root: Path,
    ref: str,
    path: str,
) -> _ReopenableByteSource | None:
    spec = f":{path}" if ref == "INDEX" else f"{ref}:{path}"
    exists = subprocess.run(
        ["git", "cat-file", "-e", spec],
        cwd=repo_root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if exists.returncode != 0:
        return None

    @contextmanager
    def open_blob() -> Iterator[BinaryIO]:
        try:
            process = subprocess.Popen(
                ("git", "cat-file", "blob", spec),
                cwd=repo_root,
                shell=False,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                **hidden_subprocess_kwargs(
                    platform_name=os.name,
                    new_process_group=False,
                ),
            )
        except OSError as exc:
            raise ValidationReliabilityError(
                "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
                f"Git blob stream start failed for {path}: {type(exc).__name__}: {exc}",
            ) from exc
        if process.stdout is None:
            process.kill()
            process.wait()
            raise ValidationReliabilityError(
                "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
                f"Git blob stream has no stdout for {path}",
            )
        try:
            yield process.stdout
        finally:
            process.stdout.close()
            native_exit = process.wait()
        if native_exit != 0:
            raise ValidationReliabilityError(
                "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
                f"Git blob stream failed for {path} with native exit {native_exit}",
            )

    return _ReopenableByteSource(
        description=f"git:{ref}:{path}",
        opener=open_blob,
    )


def _mode_from_nul_record(
    raw: bytes,
    *,
    path: str,
    surface: str,
) -> str | None:
    records = tuple(record for record in raw.split(b"\0") if record)
    if not records:
        return None
    if len(records) != 1:
        raise ValidationReliabilityError(
            "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
            f"{surface} mode lookup is not unique for {path}",
        )
    header, separator, raw_path = records[0].partition(b"\t")
    if not separator or normalize_repo_path(
        raw_path.decode("utf-8", "surrogateescape")
    ) != normalize_repo_path(path):
        raise ValidationReliabilityError(
            "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
            f"{surface} mode lookup returned a different path for {path}",
        )
    mode = header.split(b" ", 1)[0]
    try:
        rendered = mode.decode("ascii", "strict")
    except UnicodeDecodeError as exc:
        raise ValidationReliabilityError(
            "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
            f"{surface} mode is undecodable for {path}",
        ) from exc
    if not re.fullmatch(r"[0-7]{6}", rendered):
        raise ValidationReliabilityError(
            "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
            f"{surface} mode is invalid for {path}: {rendered}",
        )
    return rendered


def _git_exact_path_modes(
    repo_root: Path,
    baseline_ref: str,
    path: str,
) -> tuple[str | None, str | None]:
    """Return exact baseline/index modes through NUL-delimited Git output."""

    baseline_mode = _mode_from_nul_record(
        _git_bytes(repo_root, ("ls-tree", "-z", baseline_ref, "--", path)),
        path=path,
        surface="baseline",
    )
    index_mode = _mode_from_nul_record(
        _git_bytes(repo_root, ("ls-files", "--stage", "-z", "--", path)),
        path=path,
        surface="index",
    )
    return baseline_mode, index_mode


def _classify_tracked_symlink_surfaces(
    *,
    path: str,
    baseline_source: _ReopenableByteSource | None,
    index_source: _ReopenableByteSource | None,
    worktree_source: _ReopenableByteSource | None,
    path_state: str,
    git_status_state: str,
    git_attribute_text: str,
    git_attribute_eol: str,
    baseline_blob_ref: str,
    chunk_size: int,
) -> GitPathIntegrityV1:
    analyses = tuple(
        _analyze_source(source, chunk_size=chunk_size) if source is not None else None
        for source in (baseline_source, index_source, worktree_source)
    )
    baseline_profile, index_profile, worktree_profile = tuple(
        analysis.profile if analysis is not None else None for analysis in analyses
    )
    exact_equal = (
        path_state == "EXISTING"
        and baseline_source is not None
        and index_source is not None
        and worktree_source is not None
        and _sources_equal(baseline_source, index_source, chunk_size=chunk_size)
        and _sources_equal(index_source, worktree_source, chunk_size=chunk_size)
    )
    clean = exact_equal and git_status_state == "CLEAN"
    stat_only = exact_equal and git_status_state != "CLEAN"
    change_class = (
        "CLEAN_IDENTICAL"
        if clean
        else "STAT_CACHE_ONLY_CHANGE"
        if stat_only
        else "ENCODING_OR_UNCLASSIFIED_CHANGE"
    )
    managed = is_managed_text_path(path)
    return GitPathIntegrityV1(
        path=normalize_repo_path(path),
        path_state=path_state,
        head_or_base_blob_state=(
            "PRESENT" if baseline_source is not None else "ABSENT"
        ),
        index_blob_state="PRESENT" if index_source is not None else "ABSENT",
        worktree_state=(
            "PRESENT_SYMLINK" if worktree_source is not None else "ABSENT"
        ),
        git_status_state=git_status_state,
        git_attribute_text=git_attribute_text,
        git_attribute_eol=git_attribute_eol,
        managed_text_policy_state=(
            "MANAGED" if managed else "OUTSIDE_MANAGED_POLICY"
        ),
        managed_text_policy_reason="CANONICAL_TRACKED_SYMLINK",
        baseline_blob_ref=baseline_blob_ref,
        baseline_profile=baseline_profile,
        index_profile=index_profile,
        worktree_profile=worktree_profile,
        preexisting_baseline_representation_state="NOT_APPLICABLE",
        representation_debt_resolution_state="NOT_APPLICABLE",
        outside_policy_disposition=(
            "NOT_APPLICABLE"
            if managed
            else "OUTSIDE_MANAGED_TEXT_POLICY_UNCHANGED"
            if exact_equal
            else "OUTSIDE_MANAGED_TEXT_POLICY_REQUIRES_OWNER_DECISION"
        ),
        change_class=change_class,
        semantic_scope_member=False,
        publication_cleanliness_state=(
            "CLEAN"
            if clean
            else "DIRTY_MUST_BE_REFRESHED"
            if stat_only
            else "FAIL_DECISION_REQUIRED"
        ),
        reason_codes=(
            ("TRACKED_SYMLINK_PAYLOAD_IDENTICAL",)
            if clean
            else (
                "AUTHORITATIVE_BYTES_IDENTICAL",
                "TRACKED_SYMLINK_PAYLOAD_IDENTICAL",
            )
            if stat_only
            else ("TRACKED_SYMLINK_PAYLOAD_CHANGE",)
        ),
    )


def _worktree_index_stat_paths(repo_root: Path) -> tuple[str, ...]:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    raw = _git_bytes(
        repo_root,
        ("diff-files", "--name-only", "-z", "--"),
        environment=environment,
    )
    return tuple(
        dict.fromkeys(
            normalize_repo_path(path.decode("utf-8", "surrogateescape"))
            for path in raw.split(b"\0")
            if path
        )
    )


def parse_git_status_porcelain_v1_z(
    raw: bytes | str,
) -> tuple[tuple[str, str, str | None], ...]:
    """Decode complete porcelain-v1 -z records, preserving both rename paths.

    Records are (XY, destination, original_or_none), in stream order. No path
    normalization, unquoting, scope admission, or file operation is performed.
    An empty complete stream is clean; malformed/truncated streams raise.
    The caller must separately prove successful terminal capture/currentness.
    """
    if type(raw) is bytes:
        text = raw.decode("utf-8", "surrogateescape")
    elif type(raw) is str:
        text = raw
    else:
        raise ValueError("porcelain-v1 -z input must be bytes or str")
    if not text:
        return ()
    if not text.endswith("\0"):
        raise ValueError("porcelain-v1 -z stream is not NUL-terminated")
    fields = text[:-1].split("\0")
    records: list[tuple[str, str, str | None]] = []
    index = 0
    while index < len(fields):
        field = fields[index]
        if len(field) < 4 or field[2] != " ":
            raise ValueError("malformed porcelain-v1 status record")
        code, destination = field[:2], field[3:]
        if code not in {"??", "!!"} and (
            code == "  " or any(value not in " MTADRCU" for value in code)
        ):
            raise ValueError("unsupported porcelain-v1 status code")
        index += 1
        original: str | None = None
        if "R" in code or "C" in code:
            if index >= len(fields) or not fields[index]:
                raise ValueError("rename/copy original pathname is missing")
            original = fields[index]
            index += 1
        records.append((code, destination, original))
    return tuple(records)


def _status_paths(repo_root: Path) -> tuple[str, ...]:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    raw = _git_bytes(
        repo_root,
        ("status", "--porcelain=v1", "-z", "--untracked-files=all"),
        environment=environment,
    )
    try:
        records = parse_git_status_porcelain_v1_z(raw)
    except ValueError as exc:
        raise ValidationReliabilityError(
            "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
            f"invalid complete Git status stream: {exc}",
        ) from exc
    paths: list[str] = []
    for _code, destination, original in records:
        paths.append(normalize_repo_path(destination))
        if original is not None:
            paths.append(normalize_repo_path(original))
    return tuple(dict.fromkeys(paths))


def _diff_path_states(
    repo_root: Path,
    baseline_ref: str,
    *,
    status_paths: Iterable[str] = (),
) -> dict[str, str]:
    raw = _git_bytes(
        repo_root,
        ("diff", "--name-status", "-z", "--find-renames", baseline_ref, "--"),
    )
    fields = [field for field in raw.split(b"\0") if field]
    states: dict[str, str] = {}
    index = 0
    while index < len(fields):
        status = fields[index].decode("ascii", "replace")
        index += 1
        if status.startswith(("R", "C")) and index + 1 < len(fields):
            old_path = normalize_repo_path(fields[index].decode("utf-8", "surrogateescape"))
            new_path = normalize_repo_path(fields[index + 1].decode("utf-8", "surrogateescape"))
            states[old_path] = "DELETED"
            states[new_path] = "RENAMED"
            index += 2
            continue
        if index >= len(fields):
            break
        path = normalize_repo_path(fields[index].decode("utf-8", "surrogateescape"))
        index += 1
        states[path] = "DELETED" if status.startswith("D") else "NEW" if status.startswith("A") else "EXISTING"
    for path in status_paths:
        worktree_path = repo_root.joinpath(*PurePosixPath(path).parts)
        states.setdefault(
            path,
            "NEW" if not os.path.lexists(worktree_path) else "EXISTING",
        )
    return states


def _git_attributes(repo_root: Path, path: str) -> tuple[str, str]:
    raw = _git_bytes(repo_root, ("check-attr", "-z", "text", "eol", "--", path))
    fields = [field.decode("utf-8", "replace") for field in raw.split(b"\0") if field]
    values: dict[str, str] = {}
    for index in range(0, len(fields) - 2, 3):
        values[fields[index + 1]] = fields[index + 2]
    return values.get("text", "unspecified"), values.get("eol", "unspecified")


def _git_exact_path_status_state(repo_root: Path, path: str) -> str:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        completed = subprocess.run(
            (
                "git",
                "status",
                "--porcelain=v1",
                "-z",
                "--untracked-files=all",
                "--",
                path,
            ),
            cwd=repo_root,
            env=environment,
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise ValidationReliabilityError(
            "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
            f"exact-path Git status could not start for {path}: {type(exc).__name__}: {exc}",
        ) from exc
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise ValidationReliabilityError(
            "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
            detail or f"exact-path Git status failed for {path}",
        )
    return "DIRTY" if completed.stdout else "CLEAN"


def _git_exact_path_diff_state(
    repo_root: Path,
    path: str,
    *,
    baseline_ref: str,
    staged: bool,
) -> str:
    command = ["git", "diff", "--quiet"]
    if staged:
        command.extend(("--cached", baseline_ref))
    command.extend(("--", path))
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        completed = subprocess.run(
            command,
            cwd=repo_root,
            env=environment,
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        surface = "staged" if staged else "unstaged"
        raise ValidationReliabilityError(
            "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
            f"ordinary {surface} Git diff could not start for {path}: {type(exc).__name__}: {exc}",
        ) from exc
    if completed.returncode == 0:
        return "CLEAN"
    if completed.returncode == 1:
        return "DIRTY"
    detail = completed.stderr.decode("utf-8", "replace").strip()
    surface = "staged" if staged else "unstaged"
    raise ValidationReliabilityError(
        "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
        detail or f"ordinary {surface} Git diff failed for {path}",
    )


def classify_repository_changes(
    repo_root: Path,
    *,
    authorized_paths: Iterable[str] = (),
    baseline_ref: str | None = None,
    include_paths: Iterable[str] = (),
    chunk_size: int = DEFAULT_SCAN_CHUNK_BYTES,
) -> tuple[GitPathIntegrityV1, ...]:
    """Classify repository content through bounded, reopenable byte streams."""

    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")
    root = repo_root.resolve()
    baseline = baseline_ref or resolve_verified_baseline(root)
    authorized = {normalize_repo_path(path) for path in authorized_paths}
    stat_reported_paths = _worktree_index_stat_paths(root)
    status_paths = _status_paths(root)
    states = _diff_path_states(
        root,
        baseline,
        status_paths=status_paths,
    )
    for path in stat_reported_paths:
        states.setdefault(path, "EXISTING")
    for path in include_paths:
        states.setdefault(normalize_repo_path(path), "EXISTING")
    records: list[GitPathIntegrityV1] = []
    for path, path_state in sorted(states.items(), key=lambda item: (item[0].casefold(), item[0])):
        baseline_source = _git_blob_source(root, baseline, path)
        index_source = _git_blob_source(root, "INDEX", path)
        baseline_mode, index_mode = _git_exact_path_modes(root, baseline, path)
        worktree_path = root.joinpath(*PurePosixPath(path).parts)
        worktree_surface = _resolve_no_follow_worktree_surface(worktree_path)
        worktree_source = worktree_surface.source
        if path_state == "EXISTING" and baseline_source is None:
            path_state = "NEW"
        elif (
            path_state == "EXISTING"
            and baseline_source is not None
            and index_source is None
            and worktree_source is None
        ):
            path_state = "DELETED"
        attr_text, attr_eol = _git_attributes(root, path)
        exact_status_state = _git_exact_path_status_state(root, path)
        unstaged_diff_state = _git_exact_path_diff_state(
            root,
            path,
            baseline_ref=baseline,
            staged=False,
        )
        staged_diff_state = _git_exact_path_diff_state(
            root,
            path,
            baseline_ref=baseline,
            staged=True,
        )
        regular_modes = {"100644", "100755"}
        forced_reason: str | None = None
        canonical_symlink = (
            index_mode == "120000"
            and baseline_mode in {None, "120000"}
            and worktree_surface.kind == "SYMLINK"
        )
        if canonical_symlink:
            try:
                record = _classify_tracked_symlink_surfaces(
                    path=path,
                    baseline_source=baseline_source,
                    index_source=index_source,
                    worktree_source=worktree_source,
                    path_state=path_state,
                    git_status_state=exact_status_state,
                    git_attribute_text=attr_text,
                    git_attribute_eol=attr_eol,
                    baseline_blob_ref=baseline,
                    chunk_size=chunk_size,
                )
            except _WorktreeSurfaceChanged:
                forced_reason = "WORKTREE_FILE_TYPE_CHANGE_OR_LINK"
            else:
                records.append(record)
                continue
        elif baseline_mode == "120000" or index_mode == "120000":
            forced_reason = "WORKTREE_FILE_TYPE_CHANGE_OR_LINK"
        elif (
            baseline_mode is not None
            and baseline_mode not in regular_modes
        ) or (index_mode is not None and index_mode not in regular_modes):
            forced_reason = "WORKTREE_UNSUPPORTED_GIT_FILE_MODE"
        elif (
            baseline_mode in regular_modes
            and index_mode in regular_modes
            and baseline_mode != index_mode
        ):
            forced_reason = "GIT_FILE_MODE_CHANGE_REQUIRES_OWNER_DECISION"
        elif worktree_surface.kind in {
            "SYMLINK",
            "REPARSE_POINT",
            "DIRECTORY",
            "SPECIAL_FILE",
        }:
            forced_reason = "WORKTREE_FILE_TYPE_CHANGE_OR_LINK"

        selected_worktree_source = (
            None if forced_reason is not None else worktree_source
        )
        try:
            record = _classify_stream_surfaces(
                path=path,
                baseline_source=baseline_source,
                index_source=index_source,
                worktree_source=selected_worktree_source,
                path_state=path_state,
                git_status_state=exact_status_state,
                git_attribute_text=attr_text,
                git_attribute_eol=attr_eol,
                git_unstaged_diff_state=unstaged_diff_state,
                git_staged_diff_state=staged_diff_state,
                baseline_blob_ref=baseline,
                authorized=path in authorized,
                chunk_size=chunk_size,
                worktree_state_override=worktree_surface.kind,
                forced_decision_reason=forced_reason,
            )
        except _WorktreeSurfaceChanged:
            record = _classify_stream_surfaces(
                path=path,
                baseline_source=baseline_source,
                index_source=index_source,
                worktree_source=None,
                path_state=path_state,
                git_status_state=exact_status_state,
                git_attribute_text=attr_text,
                git_attribute_eol=attr_eol,
                git_unstaged_diff_state=unstaged_diff_state,
                git_staged_diff_state=staged_diff_state,
                baseline_blob_ref=baseline,
                authorized=path in authorized,
                chunk_size=chunk_size,
                worktree_state_override="FILE_TYPE_CHANGE_OR_LINK",
                forced_decision_reason="WORKTREE_FILE_TYPE_CHANGE_OR_LINK",
            )
        records.append(record)
    return tuple(records)


def semantic_changed_paths(records: Iterable[GitPathIntegrityV1]) -> tuple[str, ...]:
    return tuple(sorted(record.path for record in records if record.semantic_scope_member))


def semantic_candidate_paths(records: Iterable[GitPathIntegrityV1]) -> tuple[str, ...]:
    """Return substantive paths independently of their later scope authorization."""

    return tuple(
        sorted(
            record.path
            for record in records
            if record.change_class in SEMANTIC_CHANGE_CLASSES
        )
    )


def _status_record_map(repo_root: Path) -> dict[str, str]:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    raw = _git_bytes(
        repo_root,
        ("status", "--porcelain=v1", "-z", "--untracked-files=all"),
        environment=environment,
    )
    try:
        records = parse_git_status_porcelain_v1_z(raw)
    except ValueError as exc:
        raise ValidationReliabilityError(
            "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
            f"invalid complete Git status stream: {exc}",
        ) from exc
    result: dict[str, str] = {}
    for code, destination, original in records:
        result[normalize_repo_path(destination)] = code
        if original is not None:
            result[normalize_repo_path(original)] = code + ":SOURCE"
    return result


def _run_exact_stat_refresh(
    repo_root: Path,
    paths: Sequence[str],
    *,
    stronger: bool,
) -> int:
    option = "--really-refresh" if stronger else "--refresh"
    try:
        completed = subprocess.run(
            ("git", "update-index", option, "--", *paths),
            cwd=repo_root,
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise ValidationReliabilityError(
            "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
            f"exact stat-cache refresh could not start: {type(exc).__name__}: {exc}",
        ) from exc
    return int(completed.returncode)


def _copy_source_to_temporary(
    source: _ReopenableByteSource,
    destination: BinaryIO,
    *,
    chunk_size: int,
) -> None:
    with _open_bounded_source(source, chunk_size=chunk_size) as stream:
        for chunk in _raw_chunks(stream, chunk_size=chunk_size):
            destination.write(chunk)
    destination.flush()
    destination.seek(0)


def _temporary_matches_source(
    snapshot: BinaryIO,
    source: _ReopenableByteSource,
    *,
    chunk_size: int,
) -> bool:
    snapshot.seek(0)
    snapshot_reader = _BoundedContentReader(snapshot, chunk_size)
    with _open_bounded_source(source, chunk_size=chunk_size) as current:
        return _chunk_sequences_equal(
            _raw_chunks(snapshot_reader, chunk_size=chunk_size),
            _raw_chunks(current, chunk_size=chunk_size),
        )


def refresh_exact_stat_cache_paths(
    repo_root: Path,
    records: Iterable[GitPathIntegrityV1],
) -> tuple[GitPathIntegrityV1, ...]:
    """Refresh and reclassify only exact, byte-proven stat-cache paths."""

    root = repo_root.resolve()
    source_records = tuple(records)
    requested: list[str] = []
    for record in source_records:
        if record.change_class != "STAT_CACHE_ONLY_CHANGE":
            continue
        exact_raw_identity = (
            "AUTHORITATIVE_BYTES_IDENTICAL" in record.reason_codes
            and record.worktree_profile == record.index_profile
        )
        git_canonical_identity = (
            "GIT_CANONICAL_CONTENT_IDENTICAL" in record.reason_codes
            and "WORKTREE_FILTER_EQUIVALENT_CLEAN" in record.reason_codes
        )
        if not (
            record.path_state == "EXISTING"
            and record.baseline_profile is not None
            and record.index_profile == record.baseline_profile
            and record.worktree_profile is not None
            and (exact_raw_identity or git_canonical_identity)
        ):
            raise ValidationReliabilityError(
                "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
                f"stat-cache refresh lacks exact byte-identity proof: {record.path}",
            )
        normalized = normalize_repo_path(record.path)
        candidate = PurePosixPath(normalized)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValidationReliabilityError(
                "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
                f"stat-cache refresh path is not an exact repository path: {record.path}",
            )
        requested.append(normalized)
    exact_paths = tuple(dict.fromkeys(requested))
    if not exact_paths:
        return source_records

    baseline_refs = {
        record.baseline_blob_ref
        for record in source_records
        if record.baseline_blob_ref
    }
    if len(baseline_refs) != 1:
        raise ValidationReliabilityError(
            "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
            "stat-cache refresh requires one verified baseline reference",
        )
    baseline_ref = next(iter(baseline_refs))
    for path in exact_paths:
        if (
            _git_exact_path_diff_state(
                root,
                path,
                baseline_ref=baseline_ref,
                staged=False,
            )
            != "CLEAN"
            or _git_exact_path_diff_state(
                root,
                path,
                baseline_ref=baseline_ref,
                staged=True,
            )
            != "CLEAN"
        ):
            raise ValidationReliabilityError(
                "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
                f"stat-cache target has an ordinary Git content diff: {path}",
            )
    authorized_paths = tuple(
        record.path for record in source_records if record.semantic_scope_member
    )
    authoritative_before = classify_repository_changes(
        root,
        authorized_paths=authorized_paths,
        baseline_ref=baseline_ref,
        include_paths=exact_paths,
    )
    before_by_path = {record.path: record for record in authoritative_before}
    for path in exact_paths:
        record = before_by_path.get(path)
        if record is None or not (
            record.path_state == "EXISTING"
            and record.change_class
            in {
                "STAT_CACHE_ONLY_CHANGE",
                "CLEAN_IDENTICAL",
                "LATENT_BASELINE_REPRESENTATION_DEBT",
            }
        ):
            raise ValidationReliabilityError(
                "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
                f"stat-cache target lost exact byte-identity proof: {path}",
            )

    staged_before = _git_bytes(
        root,
        ("diff", "--cached", "--name-only", "-z", "--"),
    )
    controls_before = _git_bytes(root, ("ls-files", "-v", "-z", "--"))
    status_before = _status_record_map(root)
    target_set = set(exact_paths)

    final_records: tuple[GitPathIntegrityV1, ...]
    with ExitStack() as snapshots:
        index_snapshots: dict[str, BinaryIO] = {}
        worktree_snapshots: dict[str, BinaryIO] = {}
        for path in exact_paths:
            index_source = _git_blob_source(root, "INDEX", path)
            worktree_path = root.joinpath(*PurePosixPath(path).parts)
            worktree_surface = _resolve_no_follow_worktree_surface(worktree_path)
            if index_source is None or worktree_surface.source is None:
                raise ValidationReliabilityError(
                    "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
                    f"stat-cache target lacks index/worktree content: {path}",
                )
            index_snapshot = snapshots.enter_context(tempfile.TemporaryFile())
            worktree_snapshot = snapshots.enter_context(tempfile.TemporaryFile())
            _copy_source_to_temporary(
                index_source,
                index_snapshot,
                chunk_size=DEFAULT_SCAN_CHUNK_BYTES,
            )
            try:
                _copy_source_to_temporary(
                    worktree_surface.source,
                    worktree_snapshot,
                    chunk_size=DEFAULT_SCAN_CHUNK_BYTES,
                )
            except _WorktreeSurfaceChanged as exc:
                raise ValidationReliabilityError(
                    "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
                    f"stat-cache target worktree surface changed: {path}",
                ) from exc
            index_snapshots[path] = index_snapshot
            worktree_snapshots[path] = worktree_snapshot

        _run_exact_stat_refresh(root, exact_paths, stronger=False)
        after_ordinary = classify_repository_changes(
            root,
            authorized_paths=authorized_paths,
            baseline_ref=baseline_ref,
            include_paths=exact_paths,
        )
        after_ordinary_by_path = {
            record.path: record for record in after_ordinary
        }
        remaining = tuple(
            path
            for path in exact_paths
            if after_ordinary_by_path.get(path) is not None
            and after_ordinary_by_path[path].change_class
            == "STAT_CACHE_ONLY_CHANGE"
        )
        if remaining:
            _run_exact_stat_refresh(root, remaining, stronger=True)
            final_records = classify_repository_changes(
                root,
                authorized_paths=authorized_paths,
                baseline_ref=baseline_ref,
                include_paths=exact_paths,
            )
        else:
            final_records = after_ordinary

        final_by_path = {record.path: record for record in final_records}
        uncleared = tuple(
            path
            for path in exact_paths
            if final_by_path.get(path) is None
            or final_by_path[path].git_status_state != "CLEAN"
            or final_by_path[path].change_class == "STAT_CACHE_ONLY_CHANGE"
        )
        if uncleared:
            raise ValidationReliabilityError(
                "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
                "exact stat-cache paths remained dirty: " + ",".join(uncleared),
            )

        for path in exact_paths:
            if (
                _git_exact_path_status_state(root, path) != "CLEAN"
                or _git_exact_path_diff_state(
                    root,
                    path,
                    baseline_ref=baseline_ref,
                    staged=False,
                )
                != "CLEAN"
                or _git_exact_path_diff_state(
                    root,
                    path,
                    baseline_ref=baseline_ref,
                    staged=True,
                )
                != "CLEAN"
            ):
                raise ValidationReliabilityError(
                    "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
                    f"exact stat-cache path did not reach canonical clean state: {path}",
                )

        for path in exact_paths:
            current_index = _git_blob_source(root, "INDEX", path)
            current_worktree_path = root.joinpath(*PurePosixPath(path).parts)
            current_worktree_surface = _resolve_no_follow_worktree_surface(
                current_worktree_path
            )
            if current_index is None or current_worktree_surface.source is None:
                raise ValidationReliabilityError(
                    "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
                    f"stat-cache refresh removed content surface: {path}",
                )
            try:
                content_unchanged = _temporary_matches_source(
                    index_snapshots[path],
                    current_index,
                    chunk_size=DEFAULT_SCAN_CHUNK_BYTES,
                ) and _temporary_matches_source(
                    worktree_snapshots[path],
                    current_worktree_surface.source,
                    chunk_size=DEFAULT_SCAN_CHUNK_BYTES,
                )
            except _WorktreeSurfaceChanged as exc:
                raise ValidationReliabilityError(
                    "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
                    f"stat-cache worktree surface changed after refresh: {path}",
                ) from exc
            if not content_unchanged:
                raise ValidationReliabilityError(
                    "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
                    f"stat-cache refresh changed content: {path}",
                )

    staged_after = _git_bytes(
        root,
        ("diff", "--cached", "--name-only", "-z", "--"),
    )
    controls_after = _git_bytes(root, ("ls-files", "-v", "-z", "--"))
    status_after = _status_record_map(root)
    outside_before = {
        path: state for path, state in status_before.items() if path not in target_set
    }
    outside_after = {
        path: state for path, state in status_after.items() if path not in target_set
    }
    if staged_after != staged_before:
        raise ValidationReliabilityError(
            "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
            "exact stat-cache refresh changed the staged path set",
        )
    if controls_after != controls_before:
        raise ValidationReliabilityError(
            "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
            "exact stat-cache refresh changed index control states",
        )
    if outside_after != outside_before:
        raise ValidationReliabilityError(
            "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
            "exact stat-cache refresh changed a path outside its target set",
        )
    return final_records


def text_integrity_failure_codes(
    records: Iterable[GitPathIntegrityV1],
    *,
    include_authority_boundary: bool = True,
) -> tuple[str, ...]:
    failures: list[str] = []
    for record in records:
        if record.change_class == "OUTSIDE_MANAGED_TEXT_POLICY_CHANGE":
            failures.append("ENGVR_OUTSIDE_MANAGED_TEXT_POLICY_REQUIRES_OWNER_DECISION")
        elif record.change_class == "PREEXISTING_BASELINE_TEXT_ANOMALY":
            failures.append("ENGVR_PREEXISTING_BASELINE_TEXT_ANOMALY_REQUIRES_EXACT_PATH_DECISION")
        elif record.change_class == "MIXED_LINE_ENDING_ERROR":
            failures.append("ENGVR_MIXED_LINE_ENDING_ERROR")
        elif record.change_class == "BARE_CR_ERROR":
            failures.append("ENGVR_BARE_CR_ERROR")
        elif record.change_class == "EOF_FINAL_NEWLINE_ONLY_CHANGE":
            failures.append("ENGVR_EOF_POLICY_FAILURE")
        elif record.change_class == "LATENT_BASELINE_REPRESENTATION_DEBT":
            clean_preserved_debt = (
                record.git_status_state == "CLEAN"
                and record.publication_cleanliness_state == "CLEAN_PRESERVE_BYTES"
                and record.representation_debt_resolution_state == "PRESERVE_BYTES"
            )
            if not clean_preserved_debt:
                failures.append("ENGVR_UNRELATED_TEXT_REPRESENTATION_DRIFT")
        elif record.change_class in {
            "EOL_REPRESENTATION_ONLY_CHANGE",
            "STAT_CACHE_ONLY_CHANGE",
        }:
            failures.append("ENGVR_UNRELATED_TEXT_REPRESENTATION_DRIFT")
        elif record.change_class == "ENCODING_OR_UNCLASSIFIED_CHANGE":
            failures.append("ENGVR_TEXT_ENCODING_UNCLASSIFIED")
        elif record.change_class == "BINARY_CHANGE":
            failures.append("ENGVR_OUTSIDE_MANAGED_TEXT_POLICY_REQUIRES_OWNER_DECISION")
        elif (
            include_authority_boundary
            and record.change_class in SEMANTIC_CHANGE_CLASSES
            and not record.semantic_scope_member
        ):
            failures.append("ENGVR_AUTHORITY_BOUNDARY_VIOLATION")
        if record.change_class == "REAL_WHITESPACE_ERROR":
            failures.append("ENGVR_PREPUBLICATION_CUSTODY_FAILED")
        if "WORKTREE_EOF_DIFFERS_FROM_INDEX" in record.reason_codes:
            failures.append("ENGVR_EOF_POLICY_FAILURE")
        if any(
            reason in record.reason_codes
            for reason in (
                "WORKTREE_SEMANTICALLY_DIFFERS_FROM_INDEX",
                "WORKTREE_PUBLICATION_SURFACE_DIRTY",
            )
        ):
            failures.append("ENGVR_PREPUBLICATION_CUSTODY_FAILED")
        if any(
            reason in record.reason_codes
            for reason in (
                "NEW_CONTROLLED_TEXT_REQUIRES_CANONICAL_LF",
                "CHANGED_CONTROLLED_TEXT_REQUIRES_CANONICAL_LF",
            )
        ):
            profiles = tuple(
                profile
                for profile in (record.index_profile, record.worktree_profile)
                if profile is not None
            )
            failures.append(
                "ENGVR_EOF_POLICY_FAILURE"
                if any(profile.terminal_newline_kind == "NONE" for profile in profiles)
                else "ENGVR_PREPUBLICATION_CUSTODY_FAILED"
            )
    return tuple(dict.fromkeys(failures))


def _new_run_names(run_id: str | None = None) -> tuple[str, str]:
    moment = datetime.now(UTC)
    with _RUN_NAME_LOCK:
        counter = next(_RUN_NAME_COUNTER)
    selected_run_id = run_id or (
        f"run_{moment.strftime('%Y%m%dT%H%M%S%fZ')}_{os.getpid()}_{counter}"
    )
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", selected_run_id):
        raise ValueError("run_id must be one safe path component")
    process_child_name = (
        f"r{moment.strftime('%y%m%d%H%M%S')}_{os.getpid()}_{counter}"
    )
    return selected_run_id, process_child_name


def _candidate_parents(
    explicit_process_root: Path | str | None,
    *,
    environment: Mapping[str, str],
    platform_name: str,
) -> tuple[tuple[str, Path], ...]:
    candidates: list[tuple[str, Path]] = []
    if explicit_process_root is not None:
        candidates.append(("EXPLICIT", Path(explicit_process_root)))
    env_value = environment.get(PROCESS_ROOT_ENV, "").strip()
    if env_value:
        candidates.append(("ENVIRONMENT", Path(env_value)))
    if platform_name == "nt":
        system_drive = environment.get("SystemDrive", "").strip()
        if system_drive:
            candidates.append(("WINDOWS_SHORT_ROOT", Path(f"{system_drive}\\qttv")))
    candidates.append(("SYSTEM_TEMP", Path(tempfile.gettempdir()) / "qttv"))
    deduped: list[tuple[str, Path]] = []
    seen: set[str] = set()
    for source, candidate in candidates:
        key = os.path.normcase(os.path.abspath(str(candidate)))
        if key not in seen:
            deduped.append((source, candidate))
            seen.add(key)
    return tuple(deduped)


def _local_layout_git(repo: Path, *args: str) -> bytes:
    """Read Git custody with no index refresh, replacement objects or lazy fetch."""
    env = {key: value for key, value in os.environ.items()
           if not key.upper().startswith("GIT_")}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0",
               GIT_NO_REPLACE_OBJECTS="1", GIT_NO_LAZY_FETCH="1",
               GIT_ALLOW_PROTOCOL="")
    try:
        result = subprocess.run(
            ["git", "--no-optional-locks", "-c", "core.fsmonitor=false",
             "-c", "protocol.allow=never", "-C", str(repo), *args],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=env, check=False, timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValidationReliabilityError(
            "ENGVR_REPOSITORY_LOCAL_LAYOUT_REJECTED",
            f"read-only layout custody query failed: {type(exc).__name__}",
        ) from exc
    if result.returncode != 0:
        raise ValidationReliabilityError(
            "ENGVR_REPOSITORY_LOCAL_LAYOUT_REJECTED",
            "read-only layout custody query returned nonzero",
        )
    return result.stdout


def _local_unlinked_path(path: Path) -> None:
    """Check every existing ancestor, retaining lexical paths before resolution."""
    if not path.is_absolute() or ".." in path.parts:
        raise ValidationReliabilityError(
            "ENGVR_REPOSITORY_LOCAL_LAYOUT_REJECTED", "nonexact local path",
        )
    for part in (*reversed(path.parents), path):
        try:
            value = part.lstat()
        except FileNotFoundError:
            continue
        if (stat.S_ISLNK(value.st_mode) or _stat_is_reparse_point(value)
                or _path_is_junction(part) or not stat.S_ISDIR(value.st_mode)):
            raise ValidationReliabilityError(
                "ENGVR_REPOSITORY_LOCAL_LAYOUT_REJECTED",
                "local directory chain contains a link, reparse point or non-directory",
            )
    if _lexical_path_key(path) != _lexical_path_key(path.resolve(strict=False)):
        raise ValidationReliabilityError(
            "ENGVR_REPOSITORY_LOCAL_LAYOUT_REJECTED", "local canonical path differs",
        )


def _require_local_layout(repo_root: Path) -> Path:
    """Admit only an ignored, untracked .qtt area in this exact Git worktree.

    HEAD and index are checked separately: staging a deletion never makes a
    previously tracked .qtt file safe for recursive run cleanup.
    """
    root = _lexical_absolute_path(repo_root, field_name="local repository root")
    _local_unlinked_path(root)
    area = root / _LOCAL_LAYOUT_DIR
    for path in (area, area / "runs", area / "evidence"):
        _local_unlinked_path(path)
    observed = _local_layout_git(root, "rev-parse", "--show-toplevel").strip()
    if (not observed or _lexical_path_key(Path(os.fsdecode(observed)))
            != _lexical_path_key(root)):
        raise ValidationReliabilityError(
            "ENGVR_REPOSITORY_LOCAL_LAYOUT_REJECTED", "not the exact Git root",
        )
    for args in (("ls-files", "--cached", "-z", "--"),
                 ("ls-tree", "-r", "--name-only", "-z", "HEAD", "--")):
        names = _local_layout_git(root, *args).split(b"\0")
        if any(name.lower() == b".qtt" or name.lower().startswith(b".qtt/")
               for name in names if name):
            raise ValidationReliabilityError(
                "ENGVR_REPOSITORY_LOCAL_LAYOUT_REJECTED", "tracked .qtt path present",
            )
    # Ask about the area directory itself: excluding a test sentinel alone is
    # insufficient because it could leave another descendant unignored.
    ignored = _local_layout_git(root, "check-ignore", "--quiet", "--", ".qtt/")
    if ignored != b"":
        raise ValidationReliabilityError(
            "ENGVR_REPOSITORY_LOCAL_LAYOUT_REJECTED", ".qtt directory is not ignored",
        )
    return area


def _local_run_binding(repo: Path, process: Path, evidence: Path,
                       run_id: str | None = None) -> None:
    area = _require_local_layout(repo)
    if (_lexical_path_key(process.parent) != _lexical_path_key(area / "runs")
            or _LOCAL_RUN_NAME.fullmatch(process.name) is None
            or _lexical_path_key(evidence.parent) != _lexical_path_key(area / "evidence")
            or not evidence.name.endswith(".evidence")
            or (run_id is not None and evidence.name != f"{run_id}.evidence")):
        raise ValidationReliabilityError(
            "ENGVR_REPOSITORY_LOCAL_LAYOUT_REJECTED", "local run/evidence placement differs",
        )
    _local_unlinked_path(process)
    _local_unlinked_path(evidence)


def _local_cleanup_owner(repo: Path, process: Path, evidence: Path | None) -> None:
    if evidence is None:
        raise ValidationReliabilityError(
            "ENGVR_RUN_SCOPED_CLEANUP_FAILED", "local cleanup requires separate evidence root",
        )
    _local_run_binding(repo, process, evidence)
    key = _lexical_path_key(process)
    with _RUN_NAME_LOCK:
        owner = _LOCAL_RUN_OWNERS.get(key)
    if owner is None or owner[0] != os.getpid() or owner[3] != _lexical_path_key(evidence):
        raise ValidationReliabilityError(
            "ENGVR_RUN_SCOPED_CLEANUP_FAILED", "local root was not created by this allocator",
        )
    if not os.path.lexists(process):
        return
    value = process.lstat()
    if (value.st_dev, value.st_ino) != owner[1:3]:
        raise ValidationReliabilityError(
            "ENGVR_RUN_SCOPED_CLEANUP_FAILED", "local root identity changed since allocation",
        )
    # Reject preexisting links rather than traverse or chmod them. Concurrent
    # mutation by another writer is outside the quiescent-run cleanup contract.
    pending = [process]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                # Windows DirEntry.stat leaves device and link counts at zero.
                # Read full no-follow metadata for the existing custody checks.
                value = Path(entry.path).lstat()
                if (stat.S_ISLNK(value.st_mode) or _stat_is_reparse_point(value)
                        or _path_is_junction(Path(entry.path))
                        or value.st_dev != owner[1]):
                    raise ValidationReliabilityError(
                        "ENGVR_RUN_SCOPED_CLEANUP_FAILED", "linked or foreign-device local descendant",
                    )
                if stat.S_ISDIR(value.st_mode):
                    pending.append(Path(entry.path))
                elif not stat.S_ISREG(value.st_mode) or value.st_nlink != 1:
                    raise ValidationReliabilityError(
                        "ENGVR_RUN_SCOPED_CLEANUP_FAILED", "nonregular or multiply linked local file",
                    )
    final = process.lstat()
    if (final.st_dev, final.st_ino) != owner[1:3]:
        raise ValidationReliabilityError(
            "ENGVR_RUN_SCOPED_CLEANUP_FAILED", "local root moved during cleanup validation",
        )


def _require_active_local_run_cache(root: Path, cache_path: Path) -> None:
    """Accept cache writes only in an allocated run or an attested child run."""
    process = cache_path.parent.parent
    _local_unlinked_path(cache_path.parent)
    if not process.is_dir():
        raise ValidationReliabilityError(
            "ENGVR_REPOSITORY_LOCAL_LAYOUT_REJECTED", "local cache run does not exist",
        )
    with _RUN_NAME_LOCK:
        owner = _LOCAL_RUN_OWNERS.get(_lexical_path_key(process))
    if owner is not None and owner[0] == os.getpid():
        current = process.lstat()
        if (current.st_dev, current.st_ino) != owner[1:3]:
            raise ValidationReliabilityError(
                "ENGVR_REPOSITORY_LOCAL_LAYOUT_REJECTED", "cache run identity changed",
            )
        return
    inherited = attest_inherited_validation_run(
        root, inherited_run_id=os.environ.get(RUN_ID_ENV, ""),
        inherited_evidence_root=Path(os.environ.get(EVIDENCE_ROOT_ENV, "")),
        explicit_basetemp=process / PYTEST_BASETEMP_DIR_NAME,
    )
    if inherited.process_root != process:
        raise ValidationReliabilityError(
            "ENGVR_REPOSITORY_LOCAL_LAYOUT_REJECTED", "cache run differs from inherited run",
        )


def _validate_candidate_parent(candidate: Path, repo_root: Path) -> Path:
    if not candidate.is_absolute():
        raise ValidationReliabilityError(
            "ENGVR_SHORT_PROCESS_ROOT_UNAVAILABLE",
            f"candidate is not absolute: {candidate}",
        )
    if ".." in candidate.parts:
        raise ValidationReliabilityError(
            "ENGVR_SHORT_PROCESS_ROOT_UNAVAILABLE",
            f"candidate has traversal ambiguity: {candidate}",
        )
    resolved = candidate.resolve(strict=False)
    root = repo_root.resolve()
    if (_lexically_inside_or_equal(candidate, root)
            or resolved == root or _path_is_relative_to(resolved, root)):
        try:
            area = _require_local_layout(root)
            if _lexical_path_key(candidate) != _lexical_path_key(area / "runs"):
                raise ValueError("only exact .qtt/runs is admissible")
            _local_unlinked_path(candidate)
        except (OSError, ValueError, ValidationReliabilityError) as exc:
            raise ValidationReliabilityError(
                "ENGVR_SHORT_PROCESS_ROOT_UNAVAILABLE",
                f"repository-local candidate rejected: {exc}",
            ) from exc
    return resolved


def _safe_relative_projection(value: str) -> Path:
    safe = _safe_fixture_path_text(value)
    if safe is None:
        raise ValidationReliabilityError(
            "ENGVR_LONGEST_PATH_PROBE_FAILED",
            f"unsafe relative projection: {value!r}",
        )
    return Path(*safe.split("/"))


def _literal_string_values(
    node: ast.AST,
    string_values: Mapping[str, frozenset[str]],
) -> frozenset[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return frozenset({node.value})
    if isinstance(node, ast.Name):
        return string_values.get(node.id, frozenset())
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return frozenset(
            value
            for item in node.elts
            for value in _literal_string_values(item, string_values)
        )
    if isinstance(node, ast.Dict):
        return frozenset(
            value
            for item in (*node.keys, *node.values)
            if item is not None
            for value in _literal_string_values(item, string_values)
        )
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _literal_string_values(node.left, string_values)
        right = _literal_string_values(node.right, string_values)
        return frozenset(a + b for a in left for b in right)
    return frozenset()


def _safe_fixture_path_text(value: str) -> str | None:
    """Admit conservative literal relative paths without changing their names."""
    if not isinstance(value, str):
        return None
    text = value.replace("\\", "/")
    if not text or text.startswith(("/", "-")):
        return None
    parts = text.split("/")
    for part in parts:
        if (
            not part
            or part in {".", ".."}
            or part.startswith(" ")
            or part.endswith((" ", "."))
        ):
            return None
        for character in part:
            if ord(character) < 128:
                if not (character.isalnum() or character in "._- "):
                    return None
            elif not character.isprintable() or character.isspace():
                return None
        stem = part.split(".", 1)[0].rstrip(" ").upper()
        if stem in {"CON", "PRN", "AUX", "NUL"} or re.fullmatch(
            r"(?:COM|LPT)[1-9\u00b9\u00b2\u00b3]", stem
        ):
            return None
    return text


def _path_expression_values(
    node: ast.AST,
    *,
    string_values: Mapping[str, frozenset[str]],
    path_values: Mapping[str, frozenset[str]],
) -> frozenset[str]:
    if isinstance(node, ast.Name):
        if node.id == "tmp_path":
            return frozenset({""})
        return path_values.get(node.id, frozenset())
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        parents = _path_expression_values(
            node.left,
            string_values=string_values,
            path_values=path_values,
        )
        children = _literal_string_values(node.right, string_values)
        combined: set[str] = set()
        for parent in parents:
            for child in children:
                safe_child = _safe_fixture_path_text(child)
                if safe_child is None:
                    continue
                value = PurePosixPath(parent) / PurePosixPath(safe_child)
                combined.add(value.as_posix())
        return frozenset(combined)
    return frozenset()


def _function_tmp_path_projection(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[str | None, frozenset[str]]:
    arguments = {
        argument.arg
        for argument in (
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        )
    }
    if "tmp_path" not in arguments:
        return None, frozenset()

    string_values: dict[str, frozenset[str]] = {}
    for decorator in function.decorator_list:
        if not (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr == "parametrize"
            and len(decorator.args) >= 2
        ):
            continue
        names = _literal_string_values(decorator.args[0], string_values)
        values = _literal_string_values(decorator.args[1], string_values)
        for name_text in names:
            for name in (part.strip() for part in name_text.split(",")):
                if name:
                    string_values[name] = values

    assignment_nodes = tuple(
        node
        for node in ast.walk(function)
        if isinstance(node, (ast.Assign, ast.AnnAssign))
    )
    for _pass in range(len(assignment_nodes) + 1):
        changed = False
        for assignment in assignment_nodes:
            value_node = assignment.value
            targets = (
                assignment.targets
                if isinstance(assignment, ast.Assign)
                else (assignment.target,)
            )
            values = _literal_string_values(value_node, string_values)
            for target in targets:
                if isinstance(target, ast.Name) and values:
                    previous = string_values.get(target.id, frozenset())
                    merged = previous | values
                    if merged != previous:
                        string_values[target.id] = merged
                        changed = True
        for loop in (
            node for node in ast.walk(function) if isinstance(node, ast.For)
        ):
            if isinstance(loop.target, ast.Name):
                values = _literal_string_values(loop.iter, string_values)
                previous = string_values.get(loop.target.id, frozenset())
                merged = previous | values
                if merged != previous:
                    string_values[loop.target.id] = merged
                    changed = True
        if not changed:
            break

    path_values: dict[str, frozenset[str]] = {}
    for _pass in range(len(assignment_nodes) + 1):
        changed = False
        for assignment in assignment_nodes:
            targets = (
                assignment.targets
                if isinstance(assignment, ast.Assign)
                else (assignment.target,)
            )
            values = _path_expression_values(
                assignment.value,
                string_values=string_values,
                path_values=path_values,
            )
            for target in targets:
                if isinstance(target, ast.Name) and values:
                    previous = path_values.get(target.id, frozenset())
                    merged = previous | values
                    if merged != previous:
                        path_values[target.id] = merged
                        changed = True
        if not changed:
            break

    suffixes = frozenset(
        value
        for node in ast.walk(function)
        for value in _path_expression_values(
            node,
            string_values=string_values,
            path_values=path_values,
        )
        if value
    )
    test_component = None
    if function.name.startswith("test_"):
        pytest_name = re.sub(r"[\W]", "_", function.name)
        test_component = pytest_name[:PYTEST_TMP_PATH_NAME_LIMIT] + "0"
    return test_component, suffixes


def _selected_pytest_source_files(
    repo_root: Path,
    projected_relative_paths: Sequence[str],
) -> tuple[Path, ...]:
    tests_root = repo_root / "tests"
    if not tests_root.is_dir():
        return ()
    selected: set[Path] = set()
    for value in projected_relative_paths:
        safe = _safe_fixture_path_text(str(value))
        if safe is None or not (
            safe == "tests" or safe.startswith("tests/")
        ):
            continue
        candidate = (repo_root / Path(*PurePosixPath(safe).parts)).resolve(
            strict=False
        )
        if not _path_is_relative_to(candidate, tests_root):
            continue
        if candidate.is_file() and candidate.name.startswith("test_") and candidate.suffix == ".py":
            selected.add(candidate)
        elif candidate.is_dir():
            selected.update(
                path.resolve()
                for path in candidate.rglob("test_*.py")
                if path.is_file()
            )
    return tuple(sorted(selected, key=lambda path: normalize_repo_path(path)))


def _pytest_tmp_path_budget(
    repo_root: Path | None,
    projected_relative_paths: Sequence[str],
) -> tuple[str, tuple[str, ...]]:
    test_components: set[str] = set()
    fixture_suffixes: set[str] = set()
    source_selectors: set[str] = set()
    if repo_root is not None:
        source_root = repo_root.resolve()
        for source_path in _selected_pytest_source_files(
            repo_root,
            projected_relative_paths,
        ):
            source_selectors.add(source_path.relative_to(source_root).as_posix())
            try:
                tree = ast.parse(source_path.read_text(encoding="utf-8"))
            except (OSError, SyntaxError, UnicodeError) as exc:
                raise ValidationReliabilityError(
                    "ENGVR_LONGEST_PATH_PROBE_FAILED",
                    f"cannot derive pytest tmp_path layout from {source_path}: {type(exc).__name__}",
                ) from exc
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    component, suffixes = _function_tmp_path_projection(node)
                    if component is not None:
                        test_components.add(component)
                    fixture_suffixes.update(suffixes)

    for value in projected_relative_paths:
        safe = _safe_fixture_path_text(str(value))
        if safe is not None and safe not in source_selectors and not safe.startswith(
            ("validation-output/", "pytest-basetemp/", "command-")
        ):
            fixture_suffixes.add(safe)

    test_component = max(
        test_components or {"test_validation_path_budget0"},
        key=lambda item: (len(item.encode("utf-16-le")) // 2, len(item), item),
    )
    return test_component, tuple(
        sorted(fixture_suffixes or {"sentinel.bin"})
    )


def _deepest_projection(
    process_root: Path,
    projected_relative_paths: Sequence[str],
    *,
    repo_root: Path | None = None,
) -> Path:
    test_component, fixture_suffixes = _pytest_tmp_path_budget(
        repo_root,
        projected_relative_paths,
    )
    candidates = [
        process_root
        / VALIDATION_OUTPUT_DIR_NAME
        / "command-generated-output"
        / "sentinel.bin",
        process_root / "command-receipts" / "command-0000.stderr.bin",
    ]
    candidates.extend(
        process_root
        / PYTEST_BASETEMP_DIR_NAME
        / test_component
        / _safe_relative_projection(item)
        for item in fixture_suffixes
    )
    for value in projected_relative_paths:
        raw = str(value).replace("\\", "/")
        output_namespace = raw in {"validation-output", "pytest-basetemp"} or raw.startswith(
            ("validation-output/", "pytest-basetemp/")
        )
        safe = _safe_fixture_path_text(raw)
        if safe is None:
            if output_namespace:
                raise ValidationReliabilityError(
                    "ENGVR_LONGEST_PATH_PROBE_FAILED",
                    f"unsafe declared output projection: {value!r}",
                )
            continue
        if raw in {"validation-output", "pytest-basetemp"}:
            raise ValidationReliabilityError(
                "ENGVR_LONGEST_PATH_PROBE_FAILED",
                f"declared output has no file destination: {value!r}",
            )
        if safe.startswith("validation-output/"):
            candidates.append(
                process_root
                / VALIDATION_OUTPUT_DIR_NAME
                / _safe_relative_projection(safe.removeprefix("validation-output/"))
            )
        elif safe.startswith("pytest-basetemp/"):
            candidates.append(
                process_root
                / PYTEST_BASETEMP_DIR_NAME
                / _safe_relative_projection(safe.removeprefix("pytest-basetemp/"))
            )
    return max(
        candidates,
        key=lambda item: (
            len(str(item).encode("utf-16-le")) // 2,
            len(str(item)),
            str(item),
        ),
    )


def probe_run_filesystem(
    process_root: Path,
    *,
    deepest_projected_path: Path,
) -> FilesystemProbeReceiptV1:
    write_path = deepest_projected_path
    probe_root = write_path.parent
    replacement_first = "r" if write_path.name[:1] != "r" else "s"
    renamed_path = write_path.with_name(replacement_first + write_path.name[1:])
    created_directory = False
    unlink_success = False
    directory_cleanup_success = False
    failure_operation: str | None = None
    native_error_class: str | None = None
    written_bytes = 0
    readback_equal = False
    rename_equal = False
    try:
        failure_operation = "deepest_mkdir"
        probe_root.mkdir(parents=True, exist_ok=False)
        created_directory = True
        failure_operation = "deepest_write_fsync"
        with write_path.open("xb") as stream:
            written_bytes = stream.write(FILESYSTEM_PROBE_BYTES)
            stream.flush()
            os.fsync(stream.fileno())
        failure_operation = "deepest_readback"
        readback_equal = write_path.read_bytes() == FILESYSTEM_PROBE_BYTES
        if not readback_equal:
            raise OSError("probe readback differs")
        failure_operation = "deepest_replace"
        os.replace(write_path, renamed_path)
        rename_equal = renamed_path.read_bytes() == FILESYSTEM_PROBE_BYTES
        if not rename_equal:
            raise OSError("renamed probe readback differs")
        failure_operation = "deepest_unlink"
        renamed_path.unlink()
        unlink_success = not renamed_path.exists()
        current = probe_root
        failure_operation = "deepest_directory_cleanup"
        while current != process_root:
            current.rmdir()
            current = current.parent
        directory_cleanup_success = True
        failure_operation = None
    except OSError as exc:
        native_error_class = type(exc).__name__
    return FilesystemProbeReceiptV1(
        probe_root=probe_root,
        created_directory=created_directory,
        write_path=write_path,
        written_bytes=written_bytes,
        readback_equal=readback_equal,
        renamed_path=renamed_path,
        rename_equal=rename_equal,
        unlink_success=unlink_success,
        directory_cleanup_success=directory_cleanup_success,
        failure_operation=failure_operation,
        native_error_class=native_error_class,
    )


def resolve_validation_run_paths(
    repo_root: Path,
    *,
    explicit_process_root: Path | str | None = None,
    projected_relative_paths: Sequence[str] = (),
    environment: Mapping[str, str] | None = None,
    platform_name: str | None = None,
    run_id: str | None = None,
) -> tuple[ValidationRunPathsV1, FilesystemProbeReceiptV1]:
    root = repo_root.resolve()
    env = os.environ if environment is None else environment
    selected_platform = os.name if platform_name is None else platform_name
    selected_run_id, base_process_child_name = _new_run_names(run_id)
    errors: list[str] = []
    typed_probe_errors: list[ValidationReliabilityError] = []
    candidates = (
        (("EXPLICIT", Path(explicit_process_root)),)
        if explicit_process_root is not None
        else _candidate_parents(
            None, environment=env, platform_name=selected_platform,
        )
    )
    for source, raw_candidate in candidates:
        process_root: Path | None = None
        process_root_owned = False
        try:
            parent = _validate_candidate_parent(raw_candidate, root)
            local = _lexically_inside_or_equal(parent, root)
            evidence_parent = root / ".qtt" / "evidence" if local else parent
            parent.mkdir(parents=True, exist_ok=True)
            if local:
                evidence_parent.mkdir(parents=True, exist_ok=True)
                _require_local_layout(root)
            process_child_name = base_process_child_name
            for collision_counter in range(1000):
                process_child_name = (
                    base_process_child_name
                    if collision_counter == 0
                    else f"{base_process_child_name}_{collision_counter}"
                )
                process_root = parent / process_child_name
                try:
                    process_root.mkdir(parents=False, exist_ok=False)
                except FileExistsError:
                    continue
                process_root_owned = True
                if local:
                    _local_unlinked_path(process_root)
                    value = process_root.lstat()
                    with _RUN_NAME_LOCK:
                        _LOCAL_RUN_OWNERS[_lexical_path_key(process_root)] = (
                            os.getpid(), value.st_dev, value.st_ino,
                            _lexical_path_key(evidence_parent / f"{selected_run_id}.evidence"),
                        )
                break
            else:
                raise OSError("compact run-child collision budget exhausted")
            deepest = _deepest_projection(
                process_root,
                projected_relative_paths,
                repo_root=root,
            )
            receipt = probe_run_filesystem(
                process_root,
                deepest_projected_path=deepest,
            )
            if receipt.failure_operation is not None:
                code = (
                    "ENGVR_LONGEST_PATH_PROBE_FAILED"
                    if receipt.failure_operation.startswith("deepest_")
                    else "ENGVR_FILESYSTEM_PROBE_FAILED"
                )
                raise ValidationReliabilityError(
                    code,
                    f"{source} failed at {receipt.failure_operation}: {receipt.native_error_class}",
                )
            validation_root = process_root / VALIDATION_OUTPUT_DIR_NAME
            pytest_root = process_root / PYTEST_BASETEMP_DIR_NAME
            evidence_root = evidence_parent / f"{selected_run_id}.evidence"
            validation_root.mkdir(parents=True, exist_ok=False)
            pytest_root.mkdir(parents=True, exist_ok=False)
            evidence_root.mkdir(parents=True, exist_ok=False)
            paths = ValidationRunPathsV1(
                run_id=selected_run_id,
                process_child_name=process_child_name,
                repo_root=root,
                process_root=process_root,
                validation_output_root=validation_root,
                pytest_basetemp_root=pytest_root,
                evidence_root=evidence_root,
                process_root_is_external_to_repo=not local,
                filesystem_probe_state="PASS",
                deepest_projected_path=deepest,
                deepest_projected_path_text_length=len(str(deepest)),
                cleanup_target=process_root,
            )
            return paths, receipt
        except (OSError, ValidationReliabilityError, ValueError) as exc:
            errors.append(f"{source}:{type(exc).__name__}:{exc}")
            if isinstance(exc, ValidationReliabilityError) and exc.code in {
                "ENGVR_FILESYSTEM_PROBE_FAILED",
                "ENGVR_LONGEST_PATH_PROBE_FAILED",
            }:
                typed_probe_errors.append(exc)
            if (
                process_root_owned
                and process_root is not None
                and process_root.exists()
            ):
                candidate_evidence_root = evidence_parent / f"{selected_run_id}.evidence"
                try:
                    remove_exact_run_owned_process_tree(
                        process_root,
                        expected_run_root=process_root,
                        repo_root=root,
                        evidence_root=candidate_evidence_root,
                    )
                except (OSError, ValidationReliabilityError) as cleanup_exc:
                    raise ValidationReliabilityError(
                        "ENGVR_RUN_SCOPED_CLEANUP_FAILED",
                        "abandoned exact candidate root cleanup failed: "
                        f"{type(cleanup_exc).__name__}: {cleanup_exc}",
                    ) from cleanup_exc
            if explicit_process_root is not None and source == "EXPLICIT":
                break
            if source == "ENVIRONMENT" and (
                _lexically_inside_or_equal(raw_candidate, root)
                or _path_is_relative_to(raw_candidate.resolve(strict=False), root)
            ):
                break  # Never escape a failed explicitly configured local layout.
    if typed_probe_errors:
        raise typed_probe_errors[-1]
    raise ValidationReliabilityError(
        "ENGVR_SHORT_PROCESS_ROOT_UNAVAILABLE",
        "; ".join(errors) or "no process-root candidate was available",
    )


def _json_compatible(value: object) -> object:
    if is_dataclass(value):
        return _json_compatible(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _json_compatible(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_compatible(item) for item in value]
    return value


def _fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def atomic_write_json(path: Path, payload: object) -> None:
    """Atomically publish one immutable external JSON receipt."""
    encoded = (json.dumps(_json_compatible(payload), indent=2, sort_keys=True) + "\n").encode("utf-8")
    _atomic_write_bytes_v1(path,encoded)


def _atomic_write_bytes_v1(path, encoded, *, control_mode=None):
    _preflight_require_v1(type(encoded) is bytes and control_mode in (None,0o444),
        'exact immutable bytes and selected control publication mode required')

    destination = Path(os.path.abspath(os.path.normpath(str(path))))
    destination.parent.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(destination):
        raise ValidationReliabilityError(
            "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
            f"write-once evidence path already exists: {destination}",
        )
    temporary = destination.with_name(
        f".{destination.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp"
    )
    try:
        with temporary.open("xb") as stream:
            written = stream.write(encoded)
            if written != len(encoded):
                raise OSError(
                    "short atomic JSON write: "
                    f"expected={len(encoded)} written={written}"
                )
            stream.flush()
            if control_mode is not None:
                os.fchmod(stream.fileno(),control_mode)
            os.fsync(stream.fileno())
        os.link(temporary, destination)
        temporary.unlink()
        _fsync_directory(destination.parent)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise ValidationReliabilityError(
            "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
            f"{destination}: {type(exc).__name__}: {exc}",
        ) from exc


def _run_provenance_payload(
    paths: ValidationRunPathsV1,
    probe: FilesystemProbeReceiptV1,
    *,
    phase: str,
    command_count: int,
    text_integrity_preflight_state: str,
    rp5a_scan_profiles=None,
    rp5a_reader_profiles=None,
    rp5a_reader_bases=None,
    rp5a_launch_wire_versions=None,
    rp5a_payload_byte_limits=None,
    scan_read_limits=None,
    scan_deadline_ns=None,
    mapper_read_profiles=None,
) -> dict[str, object]:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": paths.run_id,
        "phase": phase,
        "command_count": command_count,
        "text_integrity_preflight_state": text_integrity_preflight_state,
        "paths": paths,
        "filesystem_probe": probe,
    }
    if rp5a_scan_profiles is not None:
        payload["rp5a_scan_profiles"] = _scan_profile_projection(rp5a_scan_profiles)
    if (rp5a_reader_profiles is None) != (rp5a_reader_bases is None):
        raise ValueError("reader provenance fields must appear together")
    if rp5a_reader_profiles is not None:
        readers = _scan_profile_projection(rp5a_reader_profiles)
        bases = _rp5a_basis_map_projection_v1(rp5a_reader_bases)
        if not readers or set(readers) != set(bases):
            raise ValueError("reader provenance coverage differs")
        payload.update(rp5a_reader_profiles=readers, rp5a_reader_bases=bases, rp5a_launch_wire_version=2)
    if (rp5a_launch_wire_versions is None) != (rp5a_payload_byte_limits is None):
        raise ValueError("streamed provenance tables must appear together")
    if rp5a_launch_wire_versions is not None:
        if rp5a_reader_profiles is None or rp5a_scan_profiles is None:
            raise ValueError("streamed provenance requires original reader and scanner profiles")
        versions, counts = _rp5a_wire_projection_v3(
            rp5a_launch_wire_versions, rp5a_payload_byte_limits,
            readers=readers, scanners=payload["rp5a_scan_profiles"], command_count=command_count)
        payload.update(rp5a_launch_wire_version=3, rp5a_launch_wire_versions=versions,
                       rp5a_payload_byte_limits=counts)
    if mapper_read_profiles is not None:
        payload["mapper_read_profiles"] = _mapper_profiles_projection_v1(
            mapper_read_profiles, run_id=paths.run_id, phase=phase,
            command_count=command_count, paths=paths)
    return payload


def write_run_provenance(
    paths: ValidationRunPathsV1,
    probe: FilesystemProbeReceiptV1,
    *,
    phase: str,
    command_count: int,
    text_integrity_preflight_state: str = "NOT_RUN",
    rp5a_scan_profiles=None,
    rp5a_reader_profiles=None,
    rp5a_reader_bases=None,
    rp5a_launch_wire_versions=None,
    rp5a_payload_byte_limits=None,
    scan_read_limits=None,
    scan_deadline_ns=None,
    mapper_read_profiles=None,
) -> None:
    if text_integrity_preflight_state not in {
        "PASS",
        "FAIL",
        "NOT_RUN",
        "NOT_APPLICABLE",
    }:
        raise ValueError("invalid text_integrity_preflight_state")
    atomic_write_json(
        paths.evidence_root / "run.json",
        _run_provenance_payload(
            paths,
            probe,
            phase=phase,
            command_count=command_count,
            text_integrity_preflight_state=text_integrity_preflight_state,
            rp5a_scan_profiles=rp5a_scan_profiles,
            rp5a_reader_profiles=rp5a_reader_profiles,
            rp5a_reader_bases=rp5a_reader_bases,
            rp5a_launch_wire_versions=rp5a_launch_wire_versions,
            rp5a_payload_byte_limits=rp5a_payload_byte_limits,
            mapper_read_profiles=mapper_read_profiles,
        ),
    )


def command_receipt_file_indexes(evidence_root: Path) -> tuple[int, ...]:
    indexes: list[int] = []
    for path in evidence_root.glob("command-*.json"):
        match = re.fullmatch(r"command-([1-9][0-9]*)\.json", path.name)
        if match is None:
            raise ValidationReliabilityError(
                "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
                f"unrecognized command receipt path: {path.name}",
            )
        indexes.append(int(match.group(1)))
    return tuple(sorted(indexes))


def command_attempt_accounting(
    receipts: Sequence[CommandExecutionReceiptV1],
) -> tuple[int, int, int | None, int | None]:
    """Return truthful started/completed/failure/terminal native custody counts."""

    started = tuple(receipt for receipt in receipts if receipt.pid is not None)
    completed = tuple(
        receipt for receipt in started if receipt.native_exit_code is not None
    )
    first_failed = next(
        (
            receipt.command_index
            for receipt in receipts
            if receipt.failure_class is not None
        ),
        None,
    )
    terminal_native_exit = receipts[-1].native_exit_code if receipts else None
    return len(started), len(completed), first_failed, terminal_native_exit


def _evidence_failure(detail: str) -> ValidationReliabilityError:
    return ValidationReliabilityError("ENGVR_ATOMIC_RECEIPT_WRITE_FAILED", detail)


def _evidence_path_key(path: Path | str) -> str:
    return os.path.normcase(os.path.abspath(os.path.normpath(str(path))))


def _require_direct_regular_evidence_file(
    evidence_root: Path,
    filename: str,
) -> tuple[Path, os.stat_result]:
    root = Path(os.path.abspath(os.path.normpath(str(evidence_root))))
    if not root.is_absolute() or not root.is_dir():
        raise _evidence_failure(f"evidence root is not a directory: {root}")
    if root.is_symlink() or _path_is_junction(root):
        raise _evidence_failure(f"evidence root cannot be linked: {root}")
    candidate = root / filename
    if candidate.parent != root or candidate.name != filename:
        raise _evidence_failure(f"evidence filename is not direct: {filename}")
    try:
        file_stat = candidate.stat(follow_symlinks=False)
    except OSError as exc:
        raise _evidence_failure(
            f"required evidence file is unavailable: {filename}: "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    if (
        candidate.is_symlink()
        or _path_is_junction(candidate)
        or _stat_is_reparse_point(file_stat)
        or not stat.S_ISREG(file_stat.st_mode)
        or file_stat.st_nlink != 1
    ):
        raise _evidence_failure(
            f"evidence path must be one direct nonlinked regular file: {filename}"
        )
    try:
        if candidate.resolve(strict=True).parent != root.resolve(strict=True):
            raise _evidence_failure(
                f"evidence path resolves outside the run evidence root: {filename}"
            )
    except OSError as exc:
        raise _evidence_failure(
            f"evidence path resolution failed: {filename}: "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    return candidate, file_stat


def _read_evidence_json(evidence_root: Path, filename: str) -> object:
    path, _file_stat = _require_direct_regular_evidence_file(
        evidence_root,
        filename,
    )
    try:
        with path.open("r", encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _evidence_failure(
            f"evidence JSON is invalid: {filename}: {type(exc).__name__}: {exc}"
        ) from exc


@dataclass(frozen=True, slots=True)
class InheritedRunAttestation:
    run_id: str
    evidence_root: Path
    process_root: Path
    pytest_basetemp_root: Path
    _scan_snapshot: object = field(default=None, kw_only=True, repr=False, compare=False)


def attest_inherited_validation_run(
    repo_root: Path,
    *,
    inherited_run_id: str,
    inherited_evidence_root: Path,
    explicit_basetemp: Path,
    scan_read_limits=None,
    scan_deadline_ns=None,
) -> InheritedRunAttestation:
    """Prove inherited helper values name one active, exactly placed outer run."""

    if not isinstance(inherited_run_id, str) or not inherited_run_id.strip():
        raise _evidence_failure("inherited run ID must be nonempty")
    repository = Path(os.path.abspath(os.path.normpath(str(repo_root))))
    evidence = Path(inherited_evidence_root)
    if not evidence.is_absolute() or ".." in evidence.parts:
        raise _evidence_failure("inherited evidence root must be absolute and exact")
    evidence = Path(os.path.abspath(os.path.normpath(str(evidence))))
    try:
        evidence_stat = os.lstat(evidence)
    except OSError as exc:
        raise _evidence_failure(
            f"inherited evidence root is unavailable: {type(exc).__name__}: {exc}"
        ) from exc
    if (
        not stat.S_ISDIR(evidence_stat.st_mode)
        or stat.S_ISLNK(evidence_stat.st_mode)
        or _stat_is_reparse_point(evidence_stat)
        or _path_is_junction(evidence)
    ):
        raise _evidence_failure(
            "inherited evidence root must be one nonlinked directory"
        )
    evidence_local = (_lexically_inside_or_equal(evidence, repository)
                      or _path_is_relative_to(evidence.resolve(strict=True),
                                              repository.resolve(strict=True)))
    if evidence_local:
        try:
            area = _require_local_layout(repository)
            _local_unlinked_path(evidence)
            if _lexical_path_key(evidence.parent) != _lexical_path_key(area / "evidence"):
                raise ValueError("unexpected local evidence parent")
        except (ValueError, OSError, ValidationReliabilityError) as exc:
            raise _evidence_failure(f"inherited local evidence rejected: {exc}") from exc

    if (scan_read_limits is None) != (scan_deadline_ns is None):
        raise ValueError("scan limits and deadline must be supplied together")
    snapshot = None if scan_read_limits is None else _read_scan_run_snapshot(
        evidence, limits=scan_read_limits, deadline_ns=scan_deadline_ns)
    payload = _read_evidence_json(evidence, "run.json") if snapshot is None else snapshot.value
    if not isinstance(payload, Mapping):
        raise _evidence_failure("inherited run.json must contain an object")
    path_payload = payload.get("paths")
    probe_payload = payload.get("filesystem_probe")
    if not isinstance(path_payload, Mapping) or not isinstance(probe_payload, Mapping):
        raise _evidence_failure("inherited run.json lacks path or probe custody")
    if payload.get("run_id") != inherited_run_id or path_payload.get(
        "run_id"
    ) != inherited_run_id:
        raise _evidence_failure("inherited run ID disagrees with run.json")

    def payload_path(field_name: str) -> Path:
        value = path_payload.get(field_name)
        if not isinstance(value, str):
            raise _evidence_failure(
                f"inherited run.json path is missing: {field_name}"
            )
        path = Path(value)
        if not path.is_absolute() or ".." in path.parts:
            raise _evidence_failure(
                f"inherited run.json path is not absolute and exact: {field_name}"
            )
        return Path(os.path.abspath(os.path.normpath(str(path))))

    declared_repo = payload_path("repo_root")
    declared_evidence = payload_path("evidence_root")
    process_root = payload_path("process_root")
    pytest_root = payload_path("pytest_basetemp_root")
    if _lexical_path_key(declared_repo) != _lexical_path_key(repository):
        raise _evidence_failure("inherited repository root disagrees with run.json")
    if _lexical_path_key(declared_evidence) != _lexical_path_key(evidence):
        raise _evidence_failure("inherited evidence root disagrees with run.json")
    process_local = (_lexically_inside_or_equal(process_root, repository)
                     or _path_is_relative_to(process_root.resolve(strict=False),
                                             repository.resolve(strict=True)))
    if process_local != evidence_local:
        raise _evidence_failure("inherited local/external path classes disagree")
    if process_local:
        try:
            _local_run_binding(repository, process_root, evidence, inherited_run_id)
            if not process_root.is_dir():
                raise ValueError("inherited local process root is absent")
            if (path_payload.get("process_child_name") != process_root.name
                    or payload_path("cleanup_target") != process_root
                    or payload_path("validation_output_root") != process_root / VALIDATION_OUTPUT_DIR_NAME
                    or pytest_root != process_root / PYTEST_BASETEMP_DIR_NAME):
                raise ValueError("inherited exact local run fields differ")
        except (ValueError, OSError, ValidationReliabilityError) as exc:
            raise _evidence_failure(f"inherited local run rejected: {exc}") from exc
    if not _lexically_inside_or_equal(pytest_root, process_root):
        raise _evidence_failure("inherited pytest basetemp root is not run-scoped")
    if (
        path_payload.get("process_root_is_external_to_repo") is not (not process_local)
        or path_payload.get("filesystem_probe_state") != "PASS"
        or probe_payload.get("failure_operation") is not None
    ):
        raise _evidence_failure("inherited filesystem probe did not pass")

    selected_basetemp = Path(explicit_basetemp)
    if not selected_basetemp.is_absolute() or ".." in selected_basetemp.parts:
        raise _evidence_failure("inherited basetemp must be absolute and exact")
    selected_basetemp = Path(
        os.path.abspath(os.path.normpath(str(selected_basetemp)))
    )
    if not _lexically_inside_or_equal(selected_basetemp, pytest_root) or not (
        _path_is_relative_to(
            selected_basetemp.resolve(strict=False),
            pytest_root.resolve(strict=False),
        )
        or selected_basetemp.resolve(strict=False)
        == pytest_root.resolve(strict=False)
    ):
        raise _evidence_failure(
            "inherited basetemp is outside the declared outer pytest root"
        )
    return InheritedRunAttestation(
        run_id=inherited_run_id,
        evidence_root=evidence,
        process_root=process_root,
        pytest_basetemp_root=pytest_root,
        _scan_snapshot=snapshot,
    )


# Nested evidence is observed through the existing reliability owner. It is
# not OS-level process containment, and it creates no resource or run authority.
def _mapper_nested_pytest_args_v1(argv, repo_root):
    """Recognize only the six source-fixed report-wrapper scopes."""
    if type(argv) is not tuple or not argv or any(type(x) is not str for x in argv):
        raise ValueError("exact command tuple required")
    offset = 1
    while offset < len(argv) and argv[offset] in ("-B", "-I", "-u"):
        offset += 1
    if offset >= len(argv):
        return None
    script = Path(argv[offset])
    if script not in (Path("tools/run_pytest_fresh_basetemp.py"),
                      Path(repo_root) / "tools/run_pytest_fresh_basetemp.py"):
        return None
    arguments = argv[offset + 1:]
    scopes = tuple(row[3] for row in _REPORT_READ_ROUTES_V1 if row[3] is not None)
    targets = {scope[0] for scope in scopes}
    selected = any(x.split("::", 1)[0].replace("\\", "/").rstrip("/") in targets
                   for x in arguments if not x.startswith("-"))
    if not selected:
        return None
    from tools.run_pytest_fresh_basetemp import _split_pytest_options_v1
    retained, literals, basetemp = _split_pytest_options_v1(arguments)
    if literals or tuple(retained) not in scopes or basetemp is None:
        raise ValueError("report wrapper differs from its exact admitted test scope")
    return arguments


# Same-host monotonic cutoffs only. These controls restrict execution; they do
# not grant source, process, resource, or trading authority.
_MAPPER_PARENT_DEADLINE_ENV = "QTT_VALIDATION_MAPPER_PARENT_DEADLINE_NS"
_MAPPER_CHILD_DEADLINE_ENV = "QTT_VALIDATION_MAPPER_CHILD_DEADLINE_NS"
_MAPPER_DEADLINE_ENV_KEYS = (_MAPPER_PARENT_DEADLINE_ENV, _MAPPER_CHILD_DEADLINE_ENV)


def _execution_remaining_seconds_v1(deadline_ns):
    """A relative observation of one immutable signed-64-bit monotonic cutoff."""
    if type(deadline_ns) is not int or not 0 < deadline_ns < 2 ** 63:
        raise ValueError("execution deadline must be an exact positive int64 nanosecond value")
    remaining = deadline_ns - time.monotonic_ns()
    if remaining <= 0:
        raise TimeoutError("original execution deadline expired; no budget reset")
    # This float is a compatibility receipt/wait projection, not the authoritative
    # cutoff. The native loop independently compares integer monotonic ns.
    return remaining / 1_000_000_000


def _mapper_deadline_controls_v1(limits):
    child = limits["child_execution_deadline_ns"]
    parent = limits["execution_deadline_ns"]
    custody = limits["deadline_ns"]
    if (any(type(value) is not int or not 0 < value < 2 ** 63
            for value in (child, parent, custody)) or not child < parent < custody):
        raise ValueError("child, parent and custody cutoffs must be strictly nested")
    _execution_remaining_seconds_v1(child)
    return ((_MAPPER_PARENT_DEADLINE_ENV, str(parent)),
            (_MAPPER_CHILD_DEADLINE_ENV, str(child)))


def _mapper_child_deadline_v1(environment):
    """Consume, never regenerate, the attested ordinary parent's one-hop controls."""
    values = {}
    for key, value in environment.items():
        if type(key) is not str:
            raise ValueError("deadline environment key is not text")
        canonical = key.upper()
        if canonical not in _MAPPER_DEADLINE_ENV_KEYS:
            continue
        if canonical in values or key != canonical:
            raise ValueError("duplicate or noncanonical mapper deadline control")
        if (type(value) is not str or not 1 <= len(value) <= 19
                or re.fullmatch(r"[1-9][0-9]*", value, flags=re.ASCII) is None):
            raise ValueError("noncanonical mapper deadline value")
        values[canonical] = int(value)
    if set(values) != set(_MAPPER_DEADLINE_ENV_KEYS):
        raise ValueError("both original mapper deadline controls are required")
    parent, child = (values[name] for name in _MAPPER_DEADLINE_ENV_KEYS)
    if not 0 < child < parent < 2 ** 63:
        raise ValueError("child deadline widens or loses the original parent")
    _execution_remaining_seconds_v1(child)
    return child


class _NestedPytestEvidenceV1:
    """Bounded one-hop evidence collection for source-fixed report-wrapper calls.

    The original candidate owner supplies exclusive custody and finite limits.
    Existing parent/child receipts are never rewritten. A failed observation is
    sticky: failure evidence cannot be repaired into success within this object.
    """
    _LIMITS = frozenset(("entry_limit", "file_byte_limit", "read_byte_limit",
                        "retained_byte_limit", "deadline_ns",
                        "execution_deadline_ns", "child_execution_deadline_ns"))

    def __init__(self, *, planned, run_paths, environment, limits, check_exclusive, mapper_read_binding=None):
        if (type(planned) is not CommandEvidencePlanEntry or type(limits) is not dict
                or set(limits) != self._LIMITS or not callable(check_exclusive)
                or any(type(v) is not int or v <= 0 for v in limits.values())):
            raise ValueError("original nested evidence plan and finite limits required")
        if planned.run_id != run_paths.run_id:
            raise ValueError("nested evidence lost the original run")
        self.planned, self.paths = planned, run_paths
        self.root = Path(run_paths.evidence_root)
        self.owner_pid, self.owner_thread = os.getpid(), threading.get_ident()
        self.limits = MappingProxyType(dict(limits))
        self.remaining = limits["read_byte_limit"]
        self.retained = 0
        self.check_exclusive = check_exclusive
        self.armed_ns = time.monotonic_ns()
        self.state, self.failure, self.receipt = "PREPARING", None, None
        self.inconsistent = False
        self.saved = {}
        self.child_directory = None
        self._check()
        _local_unlinked_path(self.root)
        if not self.root.is_dir():
            raise ValueError("original evidence root is unavailable")
        self.root_identity = self._directory_identity(self.root.lstat())
        args = _mapper_nested_pytest_args_v1(planned.argv, Path(planned.cwd))
        if args is None or not Path(planned.argv[0]).is_absolute():
            raise ValueError("exact mapper wrapper and interpreter required")
        if (type(environment) is not dict or environment.get(RUN_ID_ENV) != planned.run_id
                or environment.get(EVIDENCE_ROOT_ENV) != str(self.root)):
            raise ValueError("nested parent environment differs from its original run")
        from tools.run_pytest_fresh_basetemp import _bind_canonical_pytest_invocation_v1
        # Windows os.environ uppercases names; iteration order is not a semantic
        # environment guarantee. Preserve recorded order, compare removal as a set.
        child_input = ({k.upper(): v for k, v in environment.items()}
                       if os.name == "nt" else dict(environment))
        if len(child_input) != len(environment):
            raise ValueError("case-colliding environment")
        invocation, _, projection = _bind_canonical_pytest_invocation_v1(
            args, repository_root=Path(planned.cwd), python_executable=planned.argv[0],
            run_root=run_paths.process_root, environment=child_input)
        self.parent_controls = _mapper_deadline_controls_v1(limits)
        if mapper_read_binding is not None:
            binding = _mapper_binding_v1(mapper_read_binding)
            if (tuple(binding["parent_argv"]) != planned.argv
                    or binding["command_index"] != planned.command_index
                    or binding["basis"]["deadline_ns"] != limits["child_execution_deadline_ns"]):
                raise ValueError("mapper read binding differs from nested deadline/parent")
            self.parent_controls += _mapper_read_controls_v1(binding)
            if binding['kind'] == 'MAPPER_NATIVE_READ_BINDING_V2':
                identity = environment.get(_MAPPER_ACTIVATION_ENV_V1)
                _mapper_activation_identity_v1(identity)
                self.parent_controls += ((_MAPPER_ACTIVATION_ENV_V1, identity),)
                projection['fixed_environment_controls'] += ((_MAPPER_ACTIVATION_ENV_V1, identity),)
        if any(environment.get(key) != value for key, value in self.parent_controls):
            raise ValueError("mapper environment is not its original deadline binding")
        if _mapper_child_deadline_v1(environment) != limits["child_execution_deadline_ns"]:
            raise ValueError("mapper child deadline differs")
        projection["removed_environment_keys"] += _MAPPER_DEADLINE_ENV_KEYS
        self.child_argv = tuple(invocation.command) if mapper_read_binding is None else tuple(binding["child_argv"])
        self.child_projection = projection
        self.baseline = self._inventory(self.root)
        self.parent_names = tuple(f"command-{planned.command_index}{suffix}" for suffix in
                                  (".json", ".stdout.bin", ".stderr.bin"))
        if any(name in self.baseline for name in self.parent_names):
            raise ValueError("parent evidence slots already exist")
        self.state = "ARMED"

    @staticmethod
    def _directory_identity(info):
        return (info.st_dev, info.st_ino, info.st_mode,
                getattr(info, "st_file_attributes", 0), getattr(info, "st_reparse_tag", 0))

    @classmethod
    def _entry_version(cls, info):
        if stat.S_ISREG(info.st_mode):
            return _scan_same_api_version(info)
        return (*cls._directory_identity(info), info.st_nlink, info.st_size,
                info.st_mtime_ns, info.st_ctime_ns)

    def _fail(self, message):
        raise ValidationReliabilityError("ENGVR_PROCESS_TERMINATION_FAILED", message)

    def _check(self):
        if self.failure is not None:
            self._fail("nested evidence has a previous unresolved observation")
        if (os.getpid() != self.owner_pid or threading.get_ident() != self.owner_thread
                or time.monotonic_ns() >= self.limits["deadline_ns"]
                or self.check_exclusive() is not None):
            self._fail("nested evidence custody, thread, or deadline unavailable")

    def _inventory(self, directory):
        self._check()
        _local_unlinked_path(directory)
        before = directory.lstat()
        names, folded_names = {}, set()
        # Bounded enumeration: never materialize an unbounded directory iterator.
        with os.scandir(directory) as entries:
            for item in entries:
                self._check()
                if len(names) >= self.limits["entry_limit"]:
                    self._fail("nested evidence directory entry allowance exhausted")
                name = item.name
                if name.casefold() in folded_names:
                    self._fail("nested evidence names have a case collision")
                # Use the same pathname API as subsequent custody reads.
                # Windows DirEntry.stat omits device/inode/link information.
                info = (directory / name).lstat()
                if (_stat_is_reparse_point(info) or stat.S_ISLNK(info.st_mode)
                        or not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode))
                        or (stat.S_ISREG(info.st_mode) and info.st_nlink != 1)):
                    self._fail("unsupported nested evidence entry: " + name)
                folded_names.add(name.casefold())
                names[name] = self._entry_version(info)
        after = directory.lstat()
        if self._entry_version(before) != self._entry_version(after):
            self._fail("nested evidence directory changed during enumeration")
        return names

    def _read(self, path):
        self._check()
        _local_unlinked_path(path.parent)
        before = path.lstat()
        if (not stat.S_ISREG(before.st_mode) or _stat_is_reparse_point(before)
                or before.st_nlink != 1 or before.st_size > self.limits["file_byte_limit"]):
            self._fail("unbounded or unsupported evidence file: " + str(path))
        # Limit simultaneous saved and current buffers, as well as acquired bytes.
        if (before.st_size > self.remaining
                or self.retained + 2 * before.st_size > self.limits["retained_byte_limit"]):
            self._fail("nested evidence byte allowance exhausted: " + str(path))
        fd = _open_regular_worktree_descriptor(path, nonblocking=True)
        errors, result = [], None
        try:
            opened = os.fstat(fd)
            if not _same_observed_file(before, opened) or opened.st_nlink != 1:
                self._fail("nested evidence open identity mismatch: " + str(path))
            data = bytearray()
            while True:
                self._check()
                remaining_size = before.st_size - len(data)
                piece = os.read(fd, min(65536, remaining_size + 1))
                # A changed-size sentinel is charged too. No failed-work refund.
                self.remaining -= len(piece)
                if self.remaining < 0 or len(piece) > remaining_size:
                    self._fail("nested evidence changed size or exceeded read allowance")
                if not piece:
                    break
                data.extend(piece)
            after = path.lstat()
            final_fd = os.fstat(fd)
            if (len(data) != before.st_size
                    or _scan_same_api_version(before) != _scan_same_api_version(after)
                    or _scan_same_api_version(opened) != _scan_same_api_version(final_fd)):
                self._fail("nested evidence changed while reading: " + str(path))
            result = (bytes(data), _scan_same_api_version(before), _scan_same_api_version(opened))
        except BaseException as exc:
            errors.append(exc)
        try:
            os.close(fd)
        except BaseException as exc:
            errors.append(exc)
        if errors:
            _scan_raise_errors(errors)
        self._check()
        return result

    def _json(self, raw):
        def pairs(items):
            result = {}
            for key, value in items:
                if key in result:
                    self._fail("duplicate nested receipt field: " + key)
                result[key] = value
            return result
        def constant(value):
            self._fail("nonfinite nested receipt value: " + value)
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)

    def _read_receipt(self, directory, index, expected, parent=None):
        paths = tuple(directory / f"command-{index}{suffix}" for suffix in
                      (".json", ".stdout.bin", ".stderr.bin"))
        observed = {}
        for path in paths:
            observed[path] = self._read(path)
            self.retained += len(observed[path][0])
        payload = self._json(observed[paths[0]][0])
        fields = set(CommandExecutionReceiptV1.__dataclass_fields__)
        if type(payload) is not dict or set(payload) != fields:
            self._fail("nested receipt field set differs")
        converted = dict(payload)
        for name in ("argv", "stdout_required_markers", "registered_argv", "removed_environment_keys"):
            if type(converted[name]) is not list or any(type(x) is not str for x in converted[name]):
                self._fail("nested receipt sequence differs: " + name)
            converted[name] = tuple(converted[name])
        controls = converted["fixed_environment_controls"]
        if (type(controls) is not list or any(type(x) is not list or len(x) != 2
                or any(type(y) is not str for y in x) for x in controls)):
            self._fail("nested receipt environment controls differ")
        converted["fixed_environment_controls"] = tuple(tuple(x) for x in controls)
        if converted["failure_class"] not in {
                None, "ENGVR_PROCESS_START_FAILED", "ENGVR_PROCESS_TIMEOUT",
                "ENGVR_PROCESS_TERMINATION_FAILED", "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
                "ENGVR_NATIVE_EXIT_NONZERO", "ENGVR_REQUIRED_MARKER_MISSING"}:
            self._fail("unrecognized nested receipt failure class")
        child = CommandExecutionReceiptV1(**converted)
        if _command_requires_process_retention_v1(child):
            self._fail("nested receipt retains unresolved process custody")
        for key, value in expected.items():
            actual = getattr(child, key)
            if key == "removed_environment_keys":
                equal = len(actual) == len(set(actual)) and set(actual) == set(value)
            else:
                equal = type(actual) is type(value) and actual == value
            if not equal:
                self._fail("nested receipt original association differs: " + key)
        timeout = child.timeout_seconds_or_null
        cutoff = self.limits["execution_deadline_ns" if parent is not None
                             else "child_execution_deadline_ns"]
        maximum = (cutoff - self.armed_ns) / 1_000_000_000
        if (child.pid is not None and timeout is None) or (timeout is not None and timeout > maximum):
            self._fail("receipt timeout is missing or exceeds the original pre-dispatch remainder")
        stdout, stderr = observed[paths[1]][0], observed[paths[2]][0]
        if (child.stdout_byte_count != len(stdout) or child.stderr_byte_count != len(stderr)
                or child.stderr_was_nonempty != bool(stderr)):
            self._fail("nested receipt and observed stream sizes differ")
        missing = [m for m in child.stdout_required_markers if m.encode("utf-8") not in stdout]
        state = "NOT_REQUIRED" if not child.stdout_required_markers else (
            "MISSING:" + ",".join(missing) if missing else "PASS")
        if child.stdout_marker_state != state or (missing and child.failure_class is None):
            self._fail("nested receipt and observed marker state differ")
        if parent is not None and child != parent:
            self._fail("retained parent and native parent receipt differ")
        return child, observed

    def observe(self, receipt):
        try:
            self._check()
            if self.state != "ARMED" or type(receipt) is not CommandExecutionReceiptV1:
                self._fail("nested evidence observation lacks its armed parent")
            if _command_requires_process_retention_v1(receipt):
                self._fail("parent retains unresolved process custody")
            self.receipt = receipt
            root_now = self._inventory(self.root)
            if self._directory_identity(self.root.lstat()) != self.root_identity:
                self._fail("nested evidence root identity changed")
            for name, version in self.baseline.items():
                if root_now.get(name) != version:
                    self._fail("earlier evidence changed during this occurrence: " + name)
            child_name = None
            if receipt.pid is not None:
                from tools.run_pytest_fresh_basetemp import MAX_NESTED_EVIDENCE_COLLISIONS
                # Exact source-defined allocation, bound to this observed parent PID.
                for counter in range(MAX_NESTED_EVIDENCE_COLLISIONS):
                    candidate = f"nested-pytest-{receipt.pid}-{counter}"
                    if candidate not in self.baseline:
                        child_name = candidate
                        break
                if child_name is None:
                    self._fail("nested evidence collision allowance exhausted")
            additions = set(self.parent_names) | ({child_name} if child_name else set())
            if set(root_now) != set(self.baseline) | additions:
                self._fail("nested evidence membership is missing, extra, or unbound")
            p = self.planned
            expected = dict(schema_version=SCHEMA_VERSION, run_id=p.run_id, phase=p.phase,
                command_index=p.command_index, argv=p.argv, cwd=p.cwd,
                platform=os.name, stdout_required_markers=(), registered_argv=(),
                removed_environment_keys=(), fixed_environment_controls=self.parent_controls,
                stdout_path=str(self.root / self.parent_names[1]),
                stderr_path=str(self.root / self.parent_names[2]))
            parent, saved = self._read_receipt(self.root, p.command_index, expected, parent=receipt)
            if parent.pid is not None and parent.timeout_seconds_or_null is None:
                self._fail("started mapper parent has no bounded execution receipt")
            child = None
            if child_name is not None:
                directory = self.root / child_name
                children = self._inventory(directory)
                if set(children) != {"command-1.json", "command-1.stdout.bin", "command-1.stderr.bin"}:
                    self._fail("nested child evidence is not the exact three-file set")
                expected = dict(schema_version=SCHEMA_VERSION, run_id=p.run_id, phase="nested-pytest",
                    command_index=1, argv=self.child_argv, cwd=p.cwd, platform=os.name,
                    stdout_path=str(directory / "command-1.stdout.bin"),
                    stderr_path=str(directory / "command-1.stderr.bin"), stdout_required_markers=(),
                    **self.child_projection)
                child, seen = self._read_receipt(directory, 1, expected)
                if child.pid is not None and child.timeout_seconds_or_null is None:
                    self._fail("started mapper child has no bounded execution receipt")
                if child.pid == parent.pid:
                    self._fail("parent and child PID are identical")
                saved.update(seen)
                self.child_directory = (directory, self._directory_identity(directory.lstat()))
            # Direct byte rechecks with raw same-API metadata before marking settled.
            if self._inventory(self.root) != root_now:
                self._fail("evidence membership or versions changed during collection")
            self.saved = saved
            self.retained = sum(len(value[0]) for value in saved.values())
            if self.retained > self.limits["retained_byte_limit"]:
                self._fail("retained nested evidence exceeds its allowance")
            self.inconsistent = (parent.failure_class is None and child is not None
                                 and child.failure_class is not None)
            self.state = "SETTLED"
            self.revalidate()
            return self.inconsistent
        except BaseException as exc:
            self.failure, self.state = exc, "HELD"
            raise

    def revalidate(self):
        try:
            self._check()
            if self.state != "SETTLED":
                self._fail("nested evidence is not settled")
            _local_unlinked_path(self.root)
            if self._directory_identity(self.root.lstat()) != self.root_identity:
                self._fail("nested evidence root was substituted")
            if self.child_directory is not None:
                directory, version = self.child_directory
                if (set(self._inventory(directory)) !=
                        {"command-1.json", "command-1.stdout.bin", "command-1.stderr.bin"}
                        or self._directory_identity(directory.lstat()) != version):
                    self._fail("nested evidence child directory changed")
            for path, original in self.saved.items():
                if self._read(path) != original:
                    self._fail("settled nested evidence changed: " + str(path))
        except BaseException as exc:
            self.failure, self.state = exc, "HELD"
            raise


def _recheck_nested_pytest_custody_v1(supervision):
    """No restoration/cleanup may pass an armed, absent, failed, or stale gate."""
    gates = supervision.get("nested_evidence", {})
    if type(gates) is not dict:
        supervision["pending"] = True
        raise ValidationReliabilityError("ENGVR_PROCESS_TERMINATION_FAILED", "invalid nested custody state")
    try:
        for index, gate in gates.items():
            if (type(index) is not int or type(gate) is not _NestedPytestEvidenceV1
                    or gate.planned.command_index != index or gate.paths is not supervision["paths"]
                    or gate.planned.phase != supervision["phase"]):
                raise ValidationReliabilityError("ENGVR_PROCESS_TERMINATION_FAILED", "nested custody association lost")
            gate.revalidate()
    except BaseException as exc:
        supervision["pending"] = True
        supervision["errors"].append(exc)
        raise


def validate_complete_run_evidence(
    paths: ValidationRunPathsV1,
    probe: FilesystemProbeReceiptV1,
    *,
    phase: str,
    command_count_planned: int,
    expected_plan: Sequence[CommandEvidencePlanEntry],
    receipts: Sequence[CommandExecutionReceiptV1],
    cleanup_state: str,
    text_integrity_preflight_state: str,
    rp5a_scan_profiles=None,
    rp5a_reader_profiles=None,
    rp5a_reader_bases=None,
    rp5a_launch_wire_versions=None,
    rp5a_payload_byte_limits=None,
    scan_read_limits=None,
    scan_deadline_ns=None,
    mapper_read_profiles=None,
    mapper_occurrence_records=None,
    preflight_meter=None,
) -> None:
    """Reconcile retained run, command, stream, and cleanup evidence before PASS."""

    _mapper_occurrence_evidence_v1(paths, mapper_read_profiles, mapper_occurrence_records, receipts)
    for receipt in receipts:
        _preflight_command_evidence_v1(receipt, paths, preflight_meter)

    evidence_root = Path(os.path.abspath(os.path.normpath(str(paths.evidence_root))))
    if os.path.lexists(evidence_root / "completion.json"):
        raise _evidence_failure("completion.json already exists before finalization")
    expected_run = _json_compatible(
        _run_provenance_payload(
            paths,
            probe,
            phase=phase,
            command_count=command_count_planned,
            text_integrity_preflight_state=text_integrity_preflight_state,
            rp5a_scan_profiles=rp5a_scan_profiles,
            rp5a_reader_profiles=rp5a_reader_profiles,
            rp5a_reader_bases=rp5a_reader_bases,
            rp5a_launch_wire_versions=rp5a_launch_wire_versions,
            rp5a_payload_byte_limits=rp5a_payload_byte_limits,
            mapper_read_profiles=mapper_read_profiles,
        )
    )
    if _read_evidence_json(evidence_root, "run.json") != expected_run:
        raise _evidence_failure("run.json disagrees with active run provenance")

    immutable_plan = tuple(expected_plan)
    if any(
        not isinstance(entry, CommandEvidencePlanEntry)
        for entry in immutable_plan
    ):
        raise _evidence_failure("expected command plan contains an untyped entry")
    plan_indexes = tuple(entry.command_index for entry in immutable_plan)
    if len(immutable_plan) != command_count_planned:
        raise _evidence_failure(
            "expected command plan length differs from the planned command count"
        )
    if plan_indexes != tuple(range(1, command_count_planned + 1)) or len(
        set(plan_indexes)
    ) != len(plan_indexes):
        raise _evidence_failure(
            "expected command plan indexes are not exact, unique, and contiguous"
        )
    for entry in immutable_plan:
        if entry.run_id != paths.run_id or entry.phase != phase:
            raise _evidence_failure(
                f"expected command-{entry.command_index} plan disagrees with active run"
            )

    receipt_indexes = tuple(receipt.command_index for receipt in receipts)
    expected_indexes = tuple(range(1, len(receipts) + 1))
    if receipt_indexes != expected_indexes or len(set(receipt_indexes)) != len(
        receipt_indexes
    ):
        raise _evidence_failure(
            "command receipt indexes are not exact, unique, and contiguous"
        )
    if len(receipts) > command_count_planned:
        raise _evidence_failure("command receipt count exceeds the planned command count")
    for receipt, planned in zip(
        receipts,
        immutable_plan[: len(receipts)],
        strict=True,
    ):
        if (
            receipt.run_id != planned.run_id
            or receipt.phase != planned.phase
            or receipt.command_index != planned.command_index
            or receipt.argv != planned.argv
            or _evidence_path_key(receipt.cwd) != _evidence_path_key(planned.cwd)
        ):
            raise _evidence_failure(
                f"command-{planned.command_index} receipt disagrees with the exact execution plan"
            )

    expected_command_names = {
        name
        for index in expected_indexes
        for name in (
            f"command-{index}.stdout.bin",
            f"command-{index}.stderr.bin",
            f"command-{index}.json",
        )
    }
    try:
        top_level_entries = tuple(evidence_root.iterdir())
    except OSError as exc:
        raise _evidence_failure(
            f"evidence-root inventory failed: {type(exc).__name__}: {exc}"
        ) from exc
    actual_command_names = {
        path.name for path in top_level_entries if path.name.startswith("command-")
    }
    if actual_command_names != expected_command_names:
        raise _evidence_failure(
            "top-level command evidence set differs from retained command custody"
        )
    if any(
        path.name.startswith(".command-")
        or (path.name.startswith(".") and path.name.endswith(".tmp"))
        for path in top_level_entries
    ):
        raise _evidence_failure("temporary command evidence artifacts remain")

    for receipt in receipts:
        index = receipt.command_index
        stdout_name = f"command-{index}.stdout.bin"
        stderr_name = f"command-{index}.stderr.bin"
        receipt_name = f"command-{index}.json"
        stdout_path, stdout_stat = _require_direct_regular_evidence_file(
            evidence_root,
            stdout_name,
        )
        stderr_path, stderr_stat = _require_direct_regular_evidence_file(
            evidence_root,
            stderr_name,
        )
        expected_stdout = evidence_root / stdout_name
        expected_stderr = evidence_root / stderr_name
        for claimed, expected, stream_name in (
            (receipt.stdout_path, expected_stdout, "stdout"),
            (receipt.stderr_path, expected_stderr, "stderr"),
        ):
            claimed_path = Path(claimed)
            if (
                not claimed_path.is_absolute()
                or ".." in claimed_path.parts
                or _evidence_path_key(claimed_path) != _evidence_path_key(expected)
            ):
                raise _evidence_failure(
                    f"command-{index} {stream_name} receipt path is outside custody"
                )
        if stdout_stat.st_size != receipt.stdout_byte_count:
            raise _evidence_failure(
                f"command-{index} stdout size differs from its receipt"
            )
        if stderr_stat.st_size != receipt.stderr_byte_count:
            raise _evidence_failure(
                f"command-{index} stderr size differs from its receipt"
            )
        if receipt.stderr_was_nonempty != (stderr_stat.st_size > 0):
            raise _evidence_failure(
                f"command-{index} stderr nonempty state differs from retained evidence"
            )
        missing_markers = _file_marker_states(
            (stdout_path,),
            receipt.stdout_required_markers,
        )
        retained_marker_state = (
            "NOT_REQUIRED"
            if not receipt.stdout_required_markers
            else "PASS"
            if not missing_markers
            else "MISSING:" + ",".join(missing_markers)
        )
        if retained_marker_state != receipt.stdout_marker_state:
            raise _evidence_failure(
                f"command-{index} marker state differs from retained stdout"
            )
        if _read_evidence_json(evidence_root, receipt_name) != _json_compatible(
            receipt
        ):
            raise _evidence_failure(
                f"command-{index}.json differs from the in-memory typed receipt"
            )

    cleanup_payload = _read_evidence_json(evidence_root, "cleanup.json")
    expected_cleanup = {
        "schema_version": SCHEMA_VERSION,
        "run_id": paths.run_id,
        "cleanup_target": str(paths.cleanup_target.resolve(strict=False)),
        "cleanup_state": cleanup_state,
        "parent_preserved": True,
    }
    if not isinstance(cleanup_payload, dict) or any(
        cleanup_payload.get(key) != value for key, value in expected_cleanup.items()
    ):
        raise _evidence_failure("cleanup.json disagrees with active cleanup custody")


def validate_published_completion_receipt(
    evidence_root: Path,
    completion: ValidationCompletionReceiptV1,
) -> None:
    if _read_evidence_json(evidence_root, "completion.json") != _json_compatible(
        completion
    ):
        raise _evidence_failure(
            "completion.json differs from the terminal in-memory receipt"
        )


# Opt-in resource custody, deliberately separate from the full host lease.
_WINDOWS_JOB_SCOPE_V1 = ContextVar('_WINDOWS_JOB_SCOPE_V1', default=None)
_WINDOWS_JOB_LIVE_LOCK_V1 = threading.Lock()


def _windows_job_error_v1(operation, code):
    error = OSError(code, f'{operation}: Win32 error {code}')
    error.winerror = code
    error.operation = operation
    return error


def _windows_job_api_v1():
    """Lazy, fixed Win64 declarations; no native mutation during construction."""
    if sys.platform != 'win32':
        raise RuntimeError('Windows job resource backend is unsupported on this platform')
    import ctypes as C
    from types import SimpleNamespace
    D, B, H, S, W = C.c_uint32, C.c_int32, C.c_void_p, C.c_size_t, C.c_uint16
    class Basic(C.Structure):
        _fields_ = [('process_time',C.c_int64),('job_time',C.c_int64),('flags',D),
            ('minimum_ws',S),('maximum_ws',S),('active',D),('affinity',S),('priority',D),('scheduling',D)]
    class Io(C.Structure):
        _fields_ = [(name,C.c_uint64) for name in ('reads','writes','other','read_bytes','write_bytes','other_bytes')]
    class Extended(C.Structure):
        _fields_ = [('basic',Basic),('io',Io),('process_memory',S),('job_memory',S),('peak_process',S),('peak_job',S)]
    class Accounting(C.Structure):
        _fields_ = [(name,C.c_int64) for name in ('user','kernel','period_user','period_kernel')]
        _fields_ += [(name,D) for name in ('faults','total','active','terminated')]
    class Cpu(C.Structure):
        _fields_ = [('flags',D),('rate',D)]
    class Startup(C.Structure):
        _fields_ = [('cb',D),('reserved',H),('desktop',H),('title',H),('x',D),('y',D),
            ('xsize',D),('ysize',D),('xchars',D),('ychars',D),('fill',D),('flags',D),
            ('show',W),('reserved_size',W),('reserved_bytes',H),('stdin',H),('stdout',H),('stderr',H)]
    class StartupEx(C.Structure):
        _fields_ = [('startup',Startup),('attributes',H)]
    class ProcessInfo(C.Structure):
        _fields_ = [('process',H),('thread',H),('pid',D),('tid',D)]
    class FileTime(C.Structure):
        _fields_ = [('low',D),('high',D)]
    sizes = {name:C.sizeof(cls) for name,cls in dict(BASIC_LIMIT=Basic,IO_COUNTERS=Io,
        EXTENDED_LIMIT=Extended,BASIC_ACCOUNTING=Accounting,CPU_RATE=Cpu,
        STARTUPINFOW=Startup,STARTUPINFOEXW=StartupEx,PROCESS_INFORMATION=ProcessInfo).items()}
    if (C.sizeof(H) != 8 or C.sizeof(D) != 4 or C.sizeof(C.c_wchar) != 2
            or sizes != dict(BASIC_LIMIT=64,IO_COUNTERS=48,EXTENDED_LIMIT=144,
                BASIC_ACCOUNTING=48,CPU_RATE=8,STARTUPINFOW=104,STARTUPINFOEXW=112,PROCESS_INFORMATION=24)
            or (Basic.flags.offset,Basic.active.offset,Extended.process_memory.offset,Extended.job_memory.offset,
                Startup.stdin.offset,Startup.stdout.offset,Startup.stderr.offset,StartupEx.attributes.offset,
                ProcessInfo.pid.offset,ProcessInfo.tid.offset,Accounting.total.offset,Accounting.active.offset,
                Accounting.terminated.offset) != (16,40,112,120,80,88,96,104,16,20,36,40,44)):
        raise RuntimeError('unsupported Windows job ABI')
    dll = C.WinDLL('kernel32.dll',use_last_error=True,winmode=0x800)
    api = SimpleNamespace(C=C,D=D,B=B,H=H,S=S,Basic=Basic,Extended=Extended,Accounting=Accounting,
        Cpu=Cpu,StartupEx=StartupEx,ProcessInfo=ProcessInfo,FileTime=FileTime,sizes=sizes)
    definitions = {
        'GetCurrentProcess':([],H), 'CreateJobObjectW':([H,C.c_wchar_p],H),
        'SetInformationJobObject':([H,C.c_int32,H,D],B),
        'QueryInformationJobObject':([H,C.c_int32,H,D,C.POINTER(D)],B),
        'GetHandleInformation':([H,C.POINTER(D)],B),
        'DuplicateHandle':([H,H,H,C.POINTER(H),D,B,D],B),
        'InitializeProcThreadAttributeList':([H,D,D,C.POINTER(S)],B),
        'UpdateProcThreadAttribute':([H,D,S,H,S,H,H],B),
        'DeleteProcThreadAttributeList':([H],None),
        'CreateProcessW':([C.c_wchar_p,H,H,H,B,D,H,C.c_wchar_p,C.POINTER(StartupEx),C.POINTER(ProcessInfo)],B),
        'IsProcessInJob':([H,H,C.POINTER(B)],B),
        'OpenProcess':([D,B,D],H), 'GetProcessId':([H],D),
        'QueryFullProcessImageNameW':([H,D,H,C.POINTER(D)],B),
        'GetProcessTimes':([H,C.POINTER(FileTime),C.POINTER(FileTime),C.POINTER(FileTime),C.POINTER(FileTime)],B),
        'ResumeThread':([H],D), 'WaitForSingleObject':([H,D],D),
        'GetExitCodeProcess':([H,C.POINTER(D)],B), 'TerminateJobObject':([H,D],B),
        'CloseHandle':([H],B),
    }
    for name,(arguments,result) in definitions.items():
        function = getattr(dll,name); function.argtypes=arguments; function.restype=result
        setattr(api,name,function)
    return api


class _WindowsJobScopeV1:
    """One source-owned, single-use resource scope; never a complete host grant."""
    def __init__(self, *, run_id, phase, command_index, argv, cwd, evidence_root, environment,
                 active_process_limit, process_commit_bytes, job_commit_bytes, cpu_rate_10000,
                 execution_deadline_ns, settlement_deadline_ns):
        now=time.monotonic_ns()
        if (type(run_id) is not str or not run_id or type(phase) is not str or not phase
                or type(command_index) is not int or command_index < 1
                or type(argv) is not tuple or not argv or any(type(s) is not str or not s or '\0' in s for s in argv)
                or type(environment) is not dict or any(type(k) is not str or not k or '=' in k or '\0' in k
                    or type(v) is not str or '\0' in v for k,v in environment.items())):
            raise TypeError('exact Windows job invocation operands required')
        integers=(active_process_limit,process_commit_bytes,job_commit_bytes,cpu_rate_10000,
                  execution_deadline_ns,settlement_deadline_ns)
        if (any(type(v) is not int for v in integers) or not 1 <= active_process_limit <= 2
                or not 0 < process_commit_bytes <= job_commit_bytes <= 536870912
                or not 1 <= cpu_rate_10000 <= 2000
                or not now < execution_deadline_ns < settlement_deadline_ns
                or execution_deadline_ns-now > 60_000_000_000
                or settlement_deadline_ns-execution_deadline_ns > 10_000_000_000):
            raise ValueError('Windows job engineering caps/deadlines are outside the explicit profile')
        if (not Path(argv[0]).is_absolute() or not Path(cwd).is_absolute() or not Path(evidence_root).is_absolute()
                or any('..' in Path(value).parts for value in (argv[0],cwd,evidence_root))):
            raise ValueError('exact absolute Windows job paths required')
        selected,_,env=_validate_process_invocation(argv,cwd=Path(cwd),required_markers=(),
            timeout_seconds=(execution_deadline_ns-now)/1e9,termination_grace_seconds=1,environment=environment)
        if len({key.upper() for key in env}) != len(env):
            raise ValueError('case-colliding Windows environment keys')
        command=subprocess.list2cmdline(selected)
        env_parts=[key+'='+env[key] for key in sorted(env,key=str.upper)]
        environment_units=1+sum(len(part.encode('utf-16-le'))//2+1 for part in env_parts)
        if len(command.encode('utf-16-le'))//2+1 > 32767 or environment_units > 32767:
            raise ValueError('Windows command/environment UTF-16 bound exceeded')
        self.identity=(run_id,phase,command_index,selected,str(Path(cwd)),str(Path(evidence_root)))
        self.environment=MappingProxyType(dict(env))
        self.command_line=command
        self.environment_text='\0'.join(env_parts)+'\0\0'
        if not env_parts: self.environment_text='\0\0'
        self.configured=MappingProxyType(dict(limit_flags=0x2308,active_process_limit=active_process_limit,
            process_commit_bytes=process_commit_bytes,job_commit_bytes=job_commit_bytes,
            cpu_flags=5,cpu_rate_10000=cpu_rate_10000))
        self.execution_deadline_ns=execution_deadline_ns; self.settlement_deadline_ns=settlement_deadline_ns
        self.owner=(os.getpid(),threading.get_ident())
        self.state='NEW'; self.history=['NEW']; self.claimed=False; self.entered=False; self.api=None
        self.original_deadlines=(execution_deadline_ns,settlement_deadline_ns)
        self.original_invocation=(self.identity,tuple(self.environment.items()),self.command_line,self.environment_text)
        self.original_profile=tuple(self.configured.items())
        self.handles=dict.fromkeys(('job','process','thread','stdio-0','stdio-1','stdio-2'))
        self.close_attempts=set(); self.handle_close_errors=[]; self.native_errors=[]
        self.queried=None; self.process=None; self.termination_attempted=False
        self.creation=dict(pid=None,creation_filetime_100ns=None,membership_verified_before_resume=False,resume_previous_count=None,
            creation_flags=None)
        self.terminal=dict(root_exit=None,active_processes=None,process_ids=None,termination_attempted=False,
            empty_verified=False,job_handle_closed=False,process_handle_closed=False,primary_thread_handle_closed=False)
        self.accounting=None; self.final_close_test=False
        self.membership_observation=None; self.configured_membership=None; self.creation_membership=None
        self.creation_identity=None

    def check(self, *, settling=False):
        if self.owner != (os.getpid(),threading.get_ident()):
            raise RuntimeError('foreign Windows job scope owner')
        if (self.execution_deadline_ns,self.settlement_deadline_ns) != self.original_deadlines:
            raise RuntimeError('Windows job original deadlines changed')
        if ((self.identity,tuple(self.environment.items()),self.command_line,self.environment_text) != self.original_invocation
                or tuple(self.configured.items()) != self.original_profile):
            raise RuntimeError('Windows job original invocation/profile changed')
        deadline=self.settlement_deadline_ns if settling else self.execution_deadline_ns
        if time.monotonic_ns() >= deadline:
            raise TimeoutError('Windows job settlement deadline' if settling else 'Windows job execution deadline')

    def transition(self,state):
        self.state=state; self.history.append(state)

    def call(self,name,*arguments,settling=False):
        self.check(settling=settling)
        self.api.C.set_last_error(0)
        ok=getattr(self.api,name)(*arguments)
        code=self.api.C.get_last_error() if not ok else 0
        if not ok:
            self.native_errors.append(dict(operation=name,error=int(code)))
            raise _windows_job_error_v1(name,int(code))
        self.check(settling=settling)
        return ok

    def close_handle(self,name):
        value=self.handles.get(name)
        if not value: return True
        if name in self.close_attempts: return False
        self.close_attempts.add(name)
        self.api.C.set_last_error(0)
        try:
            success=bool(self.api.CloseHandle(value))
            code=int(self.api.C.get_last_error()) if not success else None
        except BaseException as exc:
            success=False; code=getattr(exc,'winerror',None)
        if success:
            self.handles[name]=None
            return True
        self.handle_close_errors.append(dict(operation='CloseHandle:'+name,error=code))
        return False

    def query(self,kind,cls, *, settling=False,handle=None):
        value=cls(); length=self.api.D()
        self.call('QueryInformationJobObject',self.handles['job'] if handle is None else handle,kind,
            self.api.C.byref(value),self.api.C.sizeof(value),self.api.C.byref(length),settling=settling)
        if length.value != self.api.C.sizeof(value):
            raise ValueError('incomplete Windows job information structure')
        return value

    def limits(self, *, settling=False):
        ext=self.query(9,self.api.Extended,settling=settling)
        cpu=self.query(15,self.api.Cpu,settling=settling)
        actual=dict(limit_flags=int(ext.basic.flags),active_process_limit=int(ext.basic.active),
            process_commit_bytes=int(ext.process_memory),job_commit_bytes=int(ext.job_memory),
            cpu_flags=int(cpu.flags),cpu_rate_10000=int(cpu.rate))
        if actual != self.configured: raise ValueError('Windows job configured/readback mismatch')
        self.queried=actual
        return dict(actual)

    def membership(self, *, settling=False, bracket=False):
        api=self.api; C=api.C
        self.membership_observation=dict(total=None,active=None,terminated_by_limit=None,
            assigned=None,listed=None,pids=None,returned_bytes=None,accounting_before=None,
            query=None,accounting_after=None,errors=[])
        observation=self.membership_observation
        def sample():
            started=time.monotonic_ns()
            value=self.query(1,api.Accounting,settling=settling)
            return value,dict(total=int(value.total),active=int(value.active),
                terminated_by_limit=int(value.terminated),raw_hex=bytes(value).hex(),
                before_ns=started,after_ns=time.monotonic_ns())
        accounting,before=sample(); observation['accounting_before']=before
        observation.update(total=before['total'],active=before['active'],terminated_by_limit=before['terminated_by_limit'])
        # Observation storage is finite and independent of the unchanged job cap.
        capacity=8
        class Pids(C.Structure):
            _fields_=[('assigned',api.D),('listed',api.D),('ids',api.S*capacity)]
        if (C.sizeof(api.D),C.sizeof(api.S),C.sizeof(Pids),Pids.assigned.offset,
                Pids.listed.offset,Pids.ids.offset)!=(4,8,72,0,4,8):
            raise RuntimeError('unsupported Windows job process-list ABI')
        value=Pids(); length=api.D(0xffffffff)
        query=dict(information_class=3,job_handle=int(self.handles['job']),capacity=capacity,
            supplied_bytes=72,attempted=False,api_return=None,last_error_raw=None,
            raw_hex=bytes(value).hex(),returned_bytes_raw=int(length.value),
            before_ns=None,after_ns=None,status='unavailable',complete=False)
        observation['query']=query
        failures=[]
        try:
            self.check(settling=settling)
            query['before_ns']=time.monotonic_ns(); query['attempted']=True
            C.set_last_error(0)
            returned=api.QueryInformationJobObject(self.handles['job'],3,C.byref(value),72,C.byref(length))
            error=int(C.get_last_error())  # Capture before any further native call.
            raw=bytes(value); returned_length=int(length.value)
            query.update(api_return=int(returned),last_error_raw=error,raw_hex=raw.hex(),
                returned_bytes_raw=returned_length,after_ns=time.monotonic_ns(),
                assigned_raw=int(value.assigned),listed_raw=int(value.listed),
                pid_buffer_raw=tuple(int(pid) for pid in value.ids))
            if not returned:
                query['status']='incomplete' if error==234 else 'api_error'
                self.native_errors.append(dict(operation='QueryInformationJobObject:process-list',error=error))
                raise _windows_job_error_v1('QueryInformationJobObject:process-list',error)
            query['status']='malformed'
            if (not 8<=returned_length<=72 or value.listed>capacity or value.assigned<value.listed
                    or returned_length<8+8*value.listed):
                raise ValueError('invalid Windows job process-list length/count')
            if value.assigned!=value.listed:
                query['status']='incomplete'
                raise ValueError('incomplete Windows job process list')
            ids=tuple(int(value.ids[i]) for i in range(value.listed))
            if any(not 0<pid<=0xffffffff for pid in ids) or len(set(ids))!=len(ids):
                raise ValueError('invalid Windows job process identities')
            query.update(status='complete',complete=True)
            observation.update(assigned=int(value.assigned),listed=int(value.listed),pids=ids,
                returned_bytes=returned_length)
            self.check(settling=settling)
        except BaseException as exc:
            failures.append(exc)
            observation['errors'].append(dict(error_class=type(exc).__name__,message=str(exc),winerror=getattr(exc,'winerror',None)))
        finally:
            # A failed/incomplete list never supplies PIDs. Its surrounding raw
            # accounting is still retained once while ownership/deadlines permit.
            if bracket:
                try:
                    _,observation['accounting_after']=sample()
                except BaseException as exc:
                    failures.append(exc)
                    observation['errors'].append(dict(error_class=type(exc).__name__,message=str(exc),winerror=getattr(exc,'winerror',None)))
        if failures: _scan_raise_errors(failures)
        self.accounting=dict(total_processes=int(accounting.total),active_processes=int(accounting.active),
            terminated_processes=int(accounting.terminated),user_time_100ns=int(accounting.user),kernel_time_100ns=int(accounting.kernel))
        self.terminal.update(active_processes=int(accounting.active),process_ids=list(ids),
            empty_verified=(accounting.active==0 and ids==()))
        return self.terminal['empty_verified']


    def configure(self):
        self.check()
        if self.state != 'NEW': raise RuntimeError('reused Windows job scope')
        self.api=_windows_job_api_v1(); api=self.api; C=api.C
        self.check(); C.set_last_error(0)
        self.handles['job']=api.CreateJobObjectW(None,None)
        if not self.handles['job']:
            code=int(C.get_last_error()); self.native_errors.append(dict(operation='CreateJobObjectW',error=code))
            raise _windows_job_error_v1('CreateJobObjectW',code)
        self.check()
        flags=api.D(); self.call('GetHandleInformation',self.handles['job'],C.byref(flags))
        if flags.value & 1: raise ValueError('owned job handle must not be inheritable')
        ext=api.Extended(); ext.basic.flags=0x2308; ext.basic.active=self.configured['active_process_limit']
        ext.process_memory=self.configured['process_commit_bytes']; ext.job_memory=self.configured['job_commit_bytes']
        self.call('SetInformationJobObject',self.handles['job'],9,C.byref(ext),C.sizeof(ext))
        cpu=api.Cpu(); cpu.flags=5; cpu.rate=self.configured['cpu_rate_10000']
        self.call('SetInformationJobObject',self.handles['job'],15,C.byref(cpu),C.sizeof(cpu))
        self.limits()
        member=api.B()
        self.call('IsProcessInJob',api.GetCurrentProcess(),self.handles['job'],C.byref(member))
        if member.value: raise RuntimeError('controller cannot be in its owned job')
        if not self.membership(): raise RuntimeError('new owned job is not empty')
        self.configured_membership=dict(self.membership_observation)
        self.transition('CONFIGURED_EMPTY')

    def match(self, *, run_id,phase,command_index,argv,cwd,evidence_root,environment,execution_deadline_ns):
        self.check()
        if (_WINDOWS_JOB_SCOPE_V1.get() is not self or self.claimed or self.state != 'CONFIGURED_EMPTY'
                or (run_id,phase,command_index,argv,str(cwd),str(evidence_root)) != self.identity
                or environment != dict(self.environment) or execution_deadline_ns != self.execution_deadline_ns):
            raise ValueError('Windows job exact invocation/custody mismatch')
        self.claimed=True

    @staticmethod
    def _checked_root_creation_flags(flags):
        # Closed source policy for this opt-in backend; never a runtime selector.
        if type(flags) is not int or not 0<=flags<=0xffffffff or flags!=0x0008060C:
            raise ValueError('exact console-detached native root flags required')
        return flags

    def create_suspended(self,original_stdin):
        self.check()
        if not self.claimed or self.state != 'CONFIGURED_EMPTY': raise RuntimeError('unclaimed Windows job creation')
        creation_flags=self._checked_root_creation_flags(0x4|0x8|0x200|0x400|0x80000)
        import msvcrt
        api=self.api; C=api.C
        process=_WindowsJobProcessV1(self); self.process=process
        pairs=[]; nul=None; attrs=None; initialized=False; failures=[]
        try:
            for name in ('stdout','stderr'):
                pair=os.pipe(); pairs.append(pair)
                if any(os.get_inheritable(fd) for fd in pair): raise ValueError('parent pipe descriptors must not be inherited')
                stream=os.fdopen(pair[0],'rb',buffering=0)
                setattr(process,name,stream)
            input_fd=None
            if original_stdin == subprocess.DEVNULL:
                nul=os.open(os.devnull,os.O_RDONLY|os.O_BINARY); input_fd=nul
            else:
                input_fd=original_stdin if type(original_stdin) is int else original_stdin.fileno()
            duplicates=[]
            for index,fd in enumerate((input_fd,pairs[0][1],pairs[1][1])):
                duplicate=api.H(); label='stdio-'+str(index)
                self.check(); C.set_last_error(0)
                ok=api.DuplicateHandle(api.GetCurrentProcess(),msvcrt.get_osfhandle(fd),api.GetCurrentProcess(),
                    C.byref(duplicate),0,True,2)
                self.handles[label]=duplicate.value
                if not ok: raise _windows_job_error_v1('DuplicateHandle',int(C.get_last_error()))
                self.check(); flags=api.D()
                self.call('GetHandleInformation',duplicate,C.byref(flags))
                if not flags.value & 1: raise ValueError('child stdio duplicate is not inheritable')
                duplicates.append(duplicate.value)
            size=api.S(); self.check(); C.set_last_error(0)
            sizing=api.InitializeProcThreadAttributeList(None,2,0,C.byref(size)); error=int(C.get_last_error())
            if sizing or error != 122 or not 0 < size.value <= 65536:
                raise _windows_job_error_v1('InitializeProcThreadAttributeList:size',error)
            self.check(); attrs=C.create_string_buffer(size.value)
            C.set_last_error(0)
            initialized=bool(api.InitializeProcThreadAttributeList(attrs,2,0,C.byref(size)))
            if not initialized:
                raise _windows_job_error_v1('InitializeProcThreadAttributeList',int(C.get_last_error()))
            self.check()
            stdio=(api.H*3)(*duplicates); jobs=(api.H*1)(self.handles['job'])
            self.call('UpdateProcThreadAttribute',attrs,0,0x20002,stdio,C.sizeof(stdio),None,None)
            self.call('UpdateProcThreadAttribute',attrs,0,0x2000D,jobs,C.sizeof(jobs),None,None)
            startup=api.StartupEx(); startup.startup.cb=C.sizeof(startup)
            startup.startup.flags=0x101; startup.startup.show=0
            startup.startup.stdin,startup.startup.stdout,startup.startup.stderr=duplicates
            startup.attributes=C.cast(attrs,api.H).value
            command=C.create_unicode_buffer(self.command_line)
            environment=C.create_unicode_buffer(self.environment_text,len(self.environment_text))
            argv=self.identity[3]; cwd=self.identity[4]; env=dict(self.environment)
            self.check()
            sys.audit('subprocess.Popen',argv[0],list(argv),cwd,env)
            sys.audit('_winapi.CreateProcess',argv[0],self.command_line,cwd)
            self.check(); C.set_last_error(0)
            self.creation['creation_flags']=creation_flags
            ok=api.CreateProcessW(argv[0],command,None,None,True,creation_flags,
                environment,cwd,C.byref(startup),C.byref(process._info))
            # The adapter and PROCESS_INFORMATION already exist before the call.
            self.handles['process']=process._info.process; self.handles['thread']=process._info.thread
            if not ok: raise _windows_job_error_v1('CreateProcessW',int(C.get_last_error()))
            self.creation['pid']=process.pid
            self.transition('CREATED_SUSPENDED')
            self.check()
        except BaseException as exc:
            failures.append(exc)
        finally:
            if initialized:
                try: api.DeleteProcThreadAttributeList(attrs)
                except BaseException as exc: failures.append(exc)
            for index in range(3):
                if not self.close_handle('stdio-'+str(index)):
                    failures.append(RuntimeError('Windows child stdio handle close failed'))
            for index,pair in enumerate(pairs):
                for pos,fd in enumerate(pair):
                    # A successfully wrapped read descriptor belongs to its stream.
                    if pos==0 and getattr(process,('stdout','stderr')[index]) is not None: continue
                    try: os.close(fd)
                    except BaseException as exc: failures.append(exc)
            if nul is not None:
                try: os.close(nul)
                except BaseException as exc: failures.append(exc)
        if failures:
            error=failures[0] if len(failures)==1 else BaseExceptionGroup('Windows job creation and temporary cleanup',failures)
            if process._info.process:
                self.handles['process']=process._info.process; self.handles['thread']=process._info.thread
                self.creation['pid']=process.pid
                error.owned_process=process
            else:
                for stream in (process.stdout,process.stderr):
                    if stream is not None: stream.close()
            raise error
        return process

    def verify_created(self):
        self.check()
        if self.state != 'CREATED_SUSPENDED' or self.process is None: raise RuntimeError('original suspended process required')
        api=self.api; C=api.C
        self.limits()
        member=api.B()
        self.call('IsProcessInJob',self.handles['process'],self.handles['job'],C.byref(member))
        if member.value != 1: raise RuntimeError('created process missing exact owned job membership')
        times=[api.FileTime() for _ in range(4)]
        self.call('GetProcessTimes',self.handles['process'],*(C.byref(value) for value in times))
        stamp=(int(times[0].high)<<32)|int(times[0].low)
        if self.process.pid <= 0 or stamp <= 0: raise RuntimeError('invalid returned native process identity')
        self.creation.update(pid=self.process.pid,creation_filetime_100ns=stamp)
        actual_pid=int(self.call('GetProcessId',self.handles['process']))
        image=C.create_unicode_buffer(32768); capacity=api.D(32768)
        self.call('QueryFullProcessImageNameW',self.handles['process'],0,image,C.byref(capacity))
        if not 0 < capacity.value < 32768: raise ValueError('invalid bounded native process image')
        self.check(); C.set_last_error(0)
        wait=int(api.WaitForSingleObject(self.handles['process'],0))
        if wait==0xffffffff: raise _windows_job_error_v1('WaitForSingleObject:before-resume',int(C.get_last_error()))
        self.creation_identity=dict(pid=actual_pid,creation_filetime_100ns=stamp,
            image=image[:capacity.value],wait_result=wait)
        if (actual_pid != self.process.pid or wait != 258
                or _lexical_path_key(Path(self.creation_identity['image'])) != _lexical_path_key(Path(self.identity[3][0]))):
            raise RuntimeError('suspended process identity/image/wait mismatch')
        self.check()
        self.membership()
        if self.terminal['active_processes'] != 1 or self.terminal['process_ids'] != [self.process.pid]:
            raise RuntimeError('unexpected owned membership before primary-thread resume')
        self.creation_accounting=dict(self.accounting)
        self.creation_membership=dict(self.membership_observation)
        self.creation['membership_verified_before_resume']=True
        self.transition('MEMBERSHIP_VERIFIED')

    def resume(self):
        self.check()
        if self.state != 'MEMBERSHIP_VERIFIED': raise RuntimeError('verified suspended membership required before resume')
        self.api.C.set_last_error(0)
        count=int(self.api.ResumeThread(self.handles['thread']))
        self.creation['resume_previous_count']=count
        if count==0xffffffff: raise _windows_job_error_v1('ResumeThread',int(self.api.C.get_last_error()))
        if count != 1: raise RuntimeError('unexpected primary thread suspend count')
        self.transition('RUNNING')
        if not self.close_handle('thread'): raise RuntimeError('primary thread handle close failed')
        self.check()

    def terminate(self,grace_seconds):
        self.check(settling=True)
        end=min(self.settlement_deadline_ns,time.monotonic_ns()+int(grace_seconds*1e9))
        if not self.termination_attempted:
            self.termination_attempted=True; self.terminal['termination_attempted']=True
            try: self.call('TerminateJobObject',self.handles['job'],1,settling=True)
            except BaseException as exc:
                self.native_errors.append(dict(operation='TerminateJobObject:settlement',error=getattr(exc,'winerror',None)))
                return 'WINDOWS_JOB_TERMINATE:FAILED;TERMINAL:UNPROVEN',False
        while time.monotonic_ns()<end:
            self.check(settling=True)
            root=self.process.poll() if self.process is not None else None
            empty=self.membership(settling=True)
            if root is not None and empty:
                self.terminal['root_exit']=root
                self.transition('EMPTY')
                return 'WINDOWS_JOB_TERMINATE:1;TERMINAL:PROVEN',True
            time.sleep(min(0.01,max(0,(end-time.monotonic_ns())/1e9)))
        return 'WINDOWS_JOB_TERMINATE:1;TERMINAL:UNPROVEN',False

    def finish(self):
        """Close only after observed held-root termination and explicit job emptiness."""
        self.check(settling=True)
        if self.state=='CLOSED': return not self.handle_close_errors
        if self.process is not None and self.process._info.process:
            root=self.process.poll()
            self.terminal['root_exit']=root
            if root is None or not self.membership(settling=True): return False
            self.transition('ROOT_TERMINAL')
        elif self.handles.get('job') and not self.membership(settling=True): return False
        self.transition('EMPTY')
        for name in ('thread','process','job'): self.close_handle(name)
        self.terminal.update(job_handle_closed=not bool(self.handles.get('job')),
            process_handle_closed=not bool(self.handles.get('process')),
            primary_thread_handle_closed=not bool(self.handles.get('thread')))
        if any(self.handles.values()) or self.handle_close_errors: return False
        self.transition('CLOSED')
        return True

    def projection(self):
        return dict(kind='WINDOWS_JOB_RESOURCE_ONLY_V1',configured=dict(self.configured),
            queried=None if self.queried is None else dict(self.queried),creation=dict(self.creation),
            terminal=dict(self.terminal),handle_close_errors=[dict(item) for item in self.handle_close_errors])

    def close_suspended_backstop(self):
        """Explicit cap-one fixture: final handle close, never ordinary success."""
        self.check()
        if (self.state != 'MEMBERSHIP_VERIFIED' or self.configured['active_process_limit'] != 1
                or self.creation['resume_previous_count'] is not None or self.termination_attempted):
            raise RuntimeError('final-close fixture requires one verified unresumed worker')
        self.final_close_test=True
        if not self.close_handle('job'): raise RuntimeError('final owned job handle close failed')
        self.terminal['job_handle_closed']=True
        self.terminal.update(active_processes=None,process_ids=None,empty_verified=False)
        self.terminal['root_exit']=self.process.wait(min(10,max(0,(self.settlement_deadline_ns-time.monotonic_ns())/1e9)))
        for name in ('thread','process'): self.close_handle(name)
        self.terminal.update(process_handle_closed=not bool(self.handles.get('process')),
            primary_thread_handle_closed=not bool(self.handles.get('thread')))
        if any(self.handles.values()) or self.handle_close_errors: raise RuntimeError('final-close fixture handle custody unresolved')
        self.transition('CLOSED')
        return self.projection()


class _WindowsJobProcessV1:
    """Held-handle protocol adapter for the existing supervisor and pipe drains."""
    def __init__(self,scope):
        self.scope=scope; self.args=scope.identity[3]; self.returncode=None
        self.stdout=None; self.stderr=None; self._info=scope.api.ProcessInfo()
        self.last_wait_result=None

    @property
    def pid(self): return int(self._info.pid)

    def poll(self):
        if self.returncode is not None: return self.returncode
        self.scope.check(settling=True)
        if not self.scope.handles.get('process'): raise RuntimeError('original process handle unavailable')
        api=self.scope.api
        result=int(api.WaitForSingleObject(self.scope.handles['process'],0))
        self.last_wait_result=result
        self.scope.check(settling=True)
        if result==258: return None
        if result==0xffffffff: raise _windows_job_error_v1('WaitForSingleObject',int(api.C.get_last_error()))
        if result != 0: raise RuntimeError(f'unexpected process wait result {result}')
        value=api.D()
        self.scope.call('GetExitCodeProcess',self.scope.handles['process'],api.C.byref(value),settling=True)
        self.returncode=int(value.value)  # 259 is a valid exit once the held handle is signaled.
        return self.returncode

    def wait(self,timeout):
        if type(timeout) not in (int,float) or not math.isfinite(timeout) or timeout<0:
            raise ValueError('finite Windows process wait required')
        end=min(self.scope.settlement_deadline_ns,time.monotonic_ns()+int(timeout*1e9))
        while True:
            result=self.poll()
            if result is not None: return result
            left=end-time.monotonic_ns()
            if left<=0: raise subprocess.TimeoutExpired(self.args,timeout)
            code=int(self.scope.api.WaitForSingleObject(self.scope.handles['process'],min(50,max(1,left//1_000_000))))
            self.scope.check(settling=True)
            if code==0xffffffff: raise _windows_job_error_v1('WaitForSingleObject',int(self.scope.api.C.get_last_error()))
            if code not in (0,258): raise RuntimeError(f'unexpected process wait result {code}')


@contextmanager
def _windows_job_scope_v1(scope):
    if type(scope) is not _WindowsJobScopeV1: raise TypeError('exact source-owned Windows job scope required')
    scope.check()
    if scope.entered or scope.state != 'NEW' or _WINDOWS_JOB_SCOPE_V1.get() is not None:
        raise RuntimeError('Windows job scope cannot be reused or reentered')
    if not _WINDOWS_JOB_LIVE_LOCK_V1.acquire(blocking=False):
        raise RuntimeError('only one live Windows job scope is permitted')
    token=_WINDOWS_JOB_SCOPE_V1.set(scope)
    scope.entered=True
    body=None
    try:
        scope.configure()
        yield scope
    except BaseException as exc:
        body=exc
        raise
    finally:
        errors=[]
        try:
            if scope.api is not None and scope.state != 'CLOSED':
                if scope.process is not None and scope.process._info.process:
                    if scope.process.poll() is None or (scope.handles.get('job') and not scope.membership(settling=True)):
                        _,proven=scope.terminate(min(10,max(0,(scope.settlement_deadline_ns-time.monotonic_ns())/1e9)))
                        if not proven: raise RuntimeError('Windows job context retains unresolved process')
                if not scope.finish(): raise RuntimeError('Windows job context retains unresolved handles')
        except BaseException as exc:
            exc.owned_process=scope.process; exc.windows_job=scope.projection(); errors.append(exc)
        finally:
            _WINDOWS_JOB_SCOPE_V1.reset(token)
            # An unresolved scope keeps the live-slot veto; never start another job.
            if not any(scope.handles.values()) and not scope.handle_close_errors:
                _WINDOWS_JOB_LIVE_LOCK_V1.release()
            if body is not None:
                body.windows_job=scope.projection()
        if errors:
            _scan_raise_errors(([body] if body is not None else [])+errors)


def _windows_job_projection_retains_v1(receipt,job):
    if (type(job) is not dict or set(job)!={'kind','configured','queried','creation','terminal','handle_close_errors'}
            or job['kind']!='WINDOWS_JOB_RESOURCE_ONLY_V1' or job['handle_close_errors']!=[]): return True
    terminal=job['terminal']; creation=job['creation']
    fields={'limit_flags','active_process_limit','process_commit_bytes','job_commit_bytes','cpu_flags','cpu_rate_10000'}
    for values in (job['configured'],job['queried']):
        if type(values) is not dict or set(values)!=fields or any(type(v) is not int for v in values.values()): return True
        if (values['limit_flags']!=0x2308 or values['cpu_flags']!=5 or not 1<=values['active_process_limit']<=2
                or not 0<values['process_commit_bytes']<=values['job_commit_bytes']<=536870912
                or not 1<=values['cpu_rate_10000']<=2000): return True
    if (type(terminal) is not dict or type(creation) is not dict
            or set(creation)!={'pid','creation_filetime_100ns','membership_verified_before_resume','resume_previous_count','creation_flags'}
            or set(terminal)!={'root_exit','active_processes','process_ids','termination_attempted','empty_verified',
                'job_handle_closed','process_handle_closed','primary_thread_handle_closed'}
            or type(creation['membership_verified_before_resume']) is not bool
            or type(terminal['termination_attempted']) is not bool): return True
    if (terminal.get('empty_verified') is not True or terminal.get('active_processes') != 0
            or type(terminal.get('active_processes')) is not int or terminal.get('process_ids')!=[]
            or any(terminal.get(name) is not True for name in
                ('job_handle_closed','process_handle_closed','primary_thread_handle_closed'))): return True
    if receipt.pid is None: return receipt.start_failure_class is None or receipt.native_exit_code is not None
    if type(creation['creation_flags']) is not int or creation['creation_flags']!=0x0008060C: return True
    if type(terminal.get('root_exit')) is not int or terminal['root_exit']!=receipt.native_exit_code: return True
    if type(creation.get('pid')) is not int or creation['pid']!=receipt.pid: return True
    if creation['membership_verified_before_resume'] and (type(creation['creation_filetime_100ns']) is not int
            or creation['creation_filetime_100ns']<=0): return True
    if receipt.failure_class is None and (job['configured']!=job['queried']
            or creation.get('membership_verified_before_resume') is not True
            or type(creation.get('resume_previous_count')) is not int or creation['resume_previous_count']!=1): return True
    return False
def hidden_subprocess_kwargs(
    *,
    platform_name: str | None = None,
    new_process_group: bool = True,
) -> dict[str, object]:
    selected_platform = os.name if platform_name is None else platform_name
    if selected_platform != "nt":
        return {"start_new_session": True} if new_process_group else {}
    creationflags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if new_process_group:
        creationflags |= int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    startupinfo_class = getattr(subprocess, "STARTUPINFO", None)
    startupinfo = startupinfo_class() if startupinfo_class is not None else None
    if startupinfo is not None:
        startupinfo.dwFlags |= int(getattr(subprocess, "STARTF_USESHOWWINDOW", 0))
        startupinfo.wShowWindow = int(getattr(subprocess, "SW_HIDE", 0))
    result: dict[str, object] = {"creationflags": creationflags}
    if startupinfo is not None:
        result["startupinfo"] = startupinfo
    return result


def _mirror_bytes(data: bytes, target: object) -> None:
    binary = getattr(target, "buffer", None)
    if binary is not None:
        binary.write(data)
        binary.flush()
    else:
        target.write(data.decode("utf-8", "replace"))
        target.flush()


def _write_evidence_chunk(stream: BinaryIO, data: bytes) -> None:
    written = stream.write(data)
    if written != len(data):
        raise OSError(
            f"short raw-evidence write: expected={len(data)} written={written}"
        )


def _reserve_command_evidence_files(
    evidence_root: Path,
    command_index: int,
) -> tuple[Path, Path, Path, Path, BinaryIO, BinaryIO]:
    """Reserve one command's immutable evidence slots before child creation."""

    if command_index < 1:
        raise ValueError("command_index must be positive")
    root = Path(os.path.abspath(os.path.normpath(str(evidence_root))))
    root.mkdir(parents=True, exist_ok=True)
    stdout_path = root / f"command-{command_index}.stdout.bin"
    stderr_path = root / f"command-{command_index}.stderr.bin"
    receipt_path = root / f"command-{command_index}.json"
    final_paths = (stdout_path, stderr_path, receipt_path)
    if any(os.path.lexists(path) for path in final_paths):
        raise _evidence_failure(
            f"command-{command_index} write-once evidence slot already exists"
        )
    reservation = root / f".command-{command_index}.reserve"
    stdout_stream: BinaryIO | None = None
    stderr_stream: BinaryIO | None = None
    created_paths: list[Path] = []
    try:
        with reservation.open("xb"):
            pass
        if any(os.path.lexists(path) for path in final_paths):
            raise FileExistsError(
                f"command-{command_index} evidence appeared during reservation"
            )
        stdout_stream = stdout_path.open("xb")
        created_paths.append(stdout_path)
        stderr_stream = stderr_path.open("xb")
        created_paths.append(stderr_path)
    except (OSError, ValidationReliabilityError) as exc:
        for stream in (stdout_stream, stderr_stream):
            if stream is not None:
                try:
                    stream.close()
                except OSError:
                    pass
        for created_path in created_paths:
            try:
                created_path.unlink(missing_ok=True)
            except OSError:
                pass
        try:
            reservation.unlink(missing_ok=True)
        except OSError:
            pass
        if isinstance(exc, ValidationReliabilityError):
            raise
        raise _evidence_failure(
            f"command-{command_index} evidence reservation failed: "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    assert stdout_stream is not None
    assert stderr_stream is not None
    return (
        stdout_path,
        stderr_path,
        receipt_path,
        reservation,
        stdout_stream,
        stderr_stream,
    )


def _consume_available_pipe(
    pipe: BinaryIO, destination: BinaryIO, *, outcome: dict[str, object],
    native_terminal: bool,
) -> tuple[bool, bool]:
    """One bounded drain; selected limits apply before retained writes."""
    limit = outcome.get("retention_limit")
    retained = int(outcome.get("retained_byte_count", 0))
    remaining = None if limit is None else max(0, limit - retained)
    quantum = 64 * 1024
    if remaining is not None and outcome.get("evidence_write_enabled", True):
        quantum = min(quantum, remaining + 1)
    try:
        chunk = os.read(pipe.fileno(), quantum)
    except BlockingIOError:
        return False, False
    except OSError as exc:
        if exc.errno in {errno.EAGAIN, errno.EWOULDBLOCK}:
            return False, False
        if native_terminal and (exc.errno == errno.EPIPE or getattr(exc, "winerror", None) in {109, 232}):
            return False, True
        _scan_output_failure(outcome, exc)
        return False, True
    if not chunk:
        if type(pipe) is _LinuxPreflightTailV1 and not native_terminal:
            return False, False
        return False, True
    if "cleanup_drained_byte_count" in outcome and not outcome.get("evidence_write_enabled", True):
        outcome["cleanup_drained_byte_count"] += len(chunk)
    outcome["drained_byte_count"] = int(outcome.get("drained_byte_count", 0)) + len(chunk)
    overflow = remaining is not None and len(chunk) > remaining
    admitted = chunk if remaining is None else chunk[:remaining]
    if outcome.get("evidence_write_enabled", True) and admitted:
        try:
            if type(pipe) is _LinuxPreflightTailV1 and pipe.original_evidence:
                # The manager appends to the supervisor's exclusively reserved
                # file. Drain/account its original bytes without rewriting them.
                info = os.fstat(destination.fileno())
                _preflight_require_v1((info.st_dev,info.st_ino) == pipe.identity,
                    'LINUX_PREFLIGHT_ORIGINAL_EVIDENCE_DESCRIPTOR')
            else:
                _write_evidence_chunk(destination, admitted)
        except BaseException as exc:
            _scan_output_failure(outcome, exc)
        else:
            outcome["retained_byte_count"] = retained + len(admitted)
    if overflow and outcome.get("evidence_write_enabled", True):
        outcome["overflow"] = True
        _scan_output_failure(outcome, ValueError("native scan retained-output overflow"))
    active_mirror = outcome.get("mirror")
    if active_mirror is not None and "evidence_error" not in outcome:
        try:
            _mirror_bytes(admitted, active_mirror)
        except BaseException as exc:
            outcome.setdefault("mirror_error", type(exc).__name__)
            outcome["mirror"] = None
    return True, False


def _finalize_owned_output_resources(
    pipe: BinaryIO, destination: BinaryIO, *, outcome: dict[str, object],
) -> None:
    """Each original close is attempted once, with every failure retained."""
    try:
        destination.flush()
        os.fsync(destination.fileno())
    except BaseException as exc:
        _scan_output_failure(outcome, exc)
    outcome["close_attempted"] = True
    try:
        destination.close()
    except BaseException as exc:
        _scan_output_failure(outcome, exc)
    else:
        outcome["writer_closed"] = True
    try:
        pipe.close()
    except BaseException as exc:
        _scan_output_failure(outcome, exc)
    outcome["evidence_complete"] = "evidence_error" not in outcome


def _supervise_native_output(
    process: subprocess.Popen[bytes], *, stdout_stream: BinaryIO, stderr_stream: BinaryIO,
    stdout_outcome: dict[str, object], stderr_outcome: dict[str, object],
    started_monotonic: float, timeout_seconds: float | None,
    termination_grace_seconds: float, platform_name: str,
    execution_deadline_ns: int | None = None,
) -> tuple[int | None, str, str, str | None]:
    """Multiplex the original two pipes, retaining failure before terminal success."""
    assert process.stdout is not None and process.stderr is not None
    pipes = (process.stdout, process.stderr)
    streams = (stdout_stream, stderr_stream)
    outcomes = (stdout_outcome, stderr_outcome)
    timeout_state = "NOT_CONFIGURED" if timeout_seconds is None else "NOT_TRIGGERED"
    termination_state = "NOT_REQUIRED"
    failure_class = None
    native_exit = None
    terminal_at = None
    pipe_terminal = [False, False]
    termination_attempted = False
    errors = []

    def terminate_once():
        nonlocal termination_attempted, termination_state, failure_class, native_exit, terminal_at
        if termination_attempted:
            return
        termination_attempted = True
        termination_state, proven = _terminate_owned_process_tree(
            process, platform_name=platform_name, grace_seconds=termination_grace_seconds)
        native_exit = process.poll()
        terminal_at = time.monotonic()
        if not proven:
            failure_class = "ENGVR_PROCESS_TERMINATION_FAILED"

    try:
        for pipe in pipes:
            os.set_blocking(pipe.fileno(), False)
        while True:
            polled = process.poll()
            if polled is not None and native_exit is None:
                if type(polled) is not int:
                    raise ValueError("noninteger native exit")
                native_exit = polled
                terminal_at = time.monotonic()
                if type(process) is _LinuxPreflightProcessV1 and not process.scope.slice_observation():
                    failure_class = failure_class or 'ENGVR_PROCESS_DESCENDANTS_REMAIN'
                    terminate_once()
                if (type(process) is _WindowsJobProcessV1 and not process.scope.final_close_test
                        and not process.scope.membership(settling=True)):
                    process.scope.history.append(dict(root_terminal_nonempty=dict(
                        root_exit=polled,accounting=dict(process.scope.accounting),
                        process_ids=list(process.scope.terminal['process_ids']))))
                    failure_class = failure_class or ("ENGVR_NATIVE_EXIT_NONZERO" if polled != 0
                        else "ENGVR_PROCESS_DESCENDANTS_REMAIN")
                    terminate_once()
            progress = False
            for index, (pipe, stream, outcome) in enumerate(zip(pipes, streams, outcomes, strict=True)):
                if not pipe_terminal[index]:
                    consumed, eof = _consume_available_pipe(
                        pipe, stream, outcome=outcome, native_terminal=native_exit is not None)
                    progress = progress or consumed
                    pipe_terminal[index] = eof
                    outcome["eof_observed"] = eof
                if any("evidence_error" in value for value in outcomes):
                    for value in outcomes:
                        value["evidence_write_enabled"] = False
                        value["mirror"] = None
                    failure_class = failure_class or "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED"
                    terminate_once()
            # A late exit/EOF observation must not outrank the original cutoff.
            # No hard wall-clock claim: scheduling, process creation and native I/O
            # are not preempted by this cooperative observation.
            if (not termination_attempted and execution_deadline_ns is not None
                    and (time.monotonic_ns() >= execution_deadline_ns
                         or (timeout_seconds is not None
                             and time.monotonic() - started_monotonic >= timeout_seconds))):
                timeout_state = "TRIGGERED"
                failure_class = failure_class or "ENGVR_PROCESS_TIMEOUT"
                for value in outcomes:
                    value["evidence_write_enabled"] = False
                    value["mirror"] = None
                terminate_once()
            # Errors above precede the simultaneous exit/EOF success observation.
            if native_exit is not None and all(pipe_terminal):
                break
            now = time.monotonic()
            if (not termination_attempted and timeout_seconds is not None
                    and now - started_monotonic >= timeout_seconds):
                timeout_state = "TRIGGERED"
                failure_class = "ENGVR_PROCESS_TIMEOUT"
                for value in outcomes:
                    value["evidence_write_enabled"] = False
                    value["mirror"] = None
                terminate_once()
            if ((terminal_at is not None and now - terminal_at >= OUTPUT_DRAIN_COMPLETION_WAIT_SECONDS)
                    or (type(process) is _WindowsJobProcessV1
                        and time.monotonic_ns() >= process.scope.settlement_deadline_ns)):
                failure_class = "ENGVR_PROCESS_TERMINATION_FAILED"
                termination_state += ";NATIVE_TREE_UNPROVEN_OUTPUT_PIPE_OPEN"
                break
            if not progress:
                time.sleep(OUTPUT_POLL_INTERVAL_SECONDS)
    except BaseException as exc:
        errors.append(exc)
        for value in outcomes:
            value["evidence_write_enabled"] = False
            value["mirror"] = None
        try:
            terminate_once()
        except BaseException as termination_error:
            errors.append(termination_error)
    finally:
        for pipe, stream, outcome in zip(pipes, streams, outcomes, strict=True):
            _finalize_owned_output_resources(pipe, stream, outcome=outcome)
    if errors:
        for outcome in outcomes:
            errors.extend(outcome.get("errors", ()))
        _scan_raise_errors(errors)
    return native_exit, timeout_state, termination_state, failure_class


def _file_marker_states(paths: Sequence[Path], markers: Sequence[str]) -> tuple[str, ...]:
    """Find exact legacy marker lines with bounded state and no whole-file read."""

    encoded_markers = {marker: marker.encode("utf-8") for marker in markers}
    pending = set(markers)
    horizontal_strip = frozenset((9, 11, 12, 32))

    for path in paths:
        if not pending:
            break
        states: dict[str, tuple[str, int]] = {
            marker: ("LEADING", 0) for marker in pending
        }

        def finish_line() -> None:
            for marker, (phase, _position) in tuple(states.items()):
                if phase in {"AFTER_MARKER", "TRAILING_ONLY"}:
                    pending.discard(marker)
            states.clear()
            states.update({marker: ("LEADING", 0) for marker in pending})

        with path.open("rb") as stream:
            while pending:
                chunk = stream.read(64 * 1024)
                if not chunk:
                    break
                for byte in chunk:
                    if byte in {10, 13}:
                        finish_line()
                        continue
                    for marker in tuple(pending):
                        phase, position = states[marker]
                        encoded = encoded_markers[marker]
                        if phase == "INVALID":
                            continue
                        if phase == "LEADING":
                            if byte in horizontal_strip:
                                continue
                            if byte == encoded[0]:
                                position = 1
                                phase = (
                                    "AFTER_MARKER"
                                    if position == len(encoded)
                                    else "MARKER"
                                )
                            else:
                                phase = "INVALID"
                        elif phase == "MARKER":
                            if byte != encoded[position]:
                                phase = "INVALID"
                            else:
                                position += 1
                                if position == len(encoded):
                                    phase = "AFTER_MARKER"
                        elif phase == "AFTER_MARKER":
                            if byte in horizontal_strip:
                                phase = "TRAILING_ONLY"
                            else:
                                phase = "INVALID"
                        elif phase == "TRAILING_ONLY" and byte not in horizontal_strip:
                            phase = "INVALID"
                        states[marker] = (phase, position)
            finish_line()
    return tuple(marker for marker in markers if marker in pending)


def _hidden_taskkill(argv: Sequence[str]) -> int:
    process = subprocess.Popen(
        list(argv),
        shell=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **hidden_subprocess_kwargs(platform_name="nt", new_process_group=False),
    )
    try:
        process.communicate(timeout=TERMINATION_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        try:
            process.kill()
            process.communicate(timeout=TERMINATION_GRACE_SECONDS)
        except (OSError, subprocess.TimeoutExpired) as exc:
            error = ValidationReliabilityError(
                "ENGVR_PROCESS_TERMINATION_FAILED",
                "termination helper did not reach a confirmed terminal state; "
                f"PID={process.pid}; bounded post-kill wait failed",
            )
            # Retain unresolved ownership and the original partial output, if supplied.
            error.owned_process = process
            error.stdout_prefix = getattr(exc, "output", None)
            error.stderr_prefix = getattr(exc, "stderr", None)
            raise error from exc
        return 124
    return int(process.returncode)


def _posix_process_group_exists(process_group_id: int) -> bool:
    try:
        os.killpg(process_group_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _terminate_owned_process_tree(
    process: subprocess.Popen[bytes],
    *,
    platform_name: str,
    grace_seconds: float,
) -> tuple[str, bool]:
    if type(process) is _WindowsJobProcessV1:
        return process.scope.terminate(grace_seconds)
    if type(process) is _LinuxPreflightProcessV1:
        return process.scope.terminate(grace_seconds)
    pid = process.pid
    actions: list[str] = []
    if platform_name == "nt":
        result = _hidden_taskkill(("taskkill.exe", "/PID", str(pid), "/T"))
        actions.append(f"TASKKILL_T:{result}")
        tree_action_proven = result == 0
        try:
            process.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            result = _hidden_taskkill(("taskkill.exe", "/PID", str(pid), "/T", "/F"))
            actions.append(f"TASKKILL_T_F:{result}")
            tree_action_proven = result == 0
    else:
        try:
            os.killpg(pid, signal.SIGTERM)
            actions.append("SIGTERM:0")
        except ProcessLookupError:
            actions.append("SIGTERM:NOT_FOUND")
        except OSError as exc:
            actions.append(f"SIGTERM:{type(exc).__name__}")
        try:
            process.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            pass
        if _posix_process_group_exists(pid):
            try:
                os.killpg(pid, signal.SIGKILL)
                actions.append("SIGKILL:0")
            except ProcessLookupError:
                actions.append("SIGKILL:NOT_FOUND")
            except OSError as exc:
                actions.append(f"SIGKILL:{type(exc).__name__}")
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        return ";".join(actions) + ";TERMINAL:UNPROVEN", False
    if platform_name == "nt" and not tree_action_proven:
        return ";".join(actions) + ";TERMINAL:UNPROVEN", False
    if platform_name != "nt":
        deadline = time.monotonic() + grace_seconds
        while _posix_process_group_exists(pid) and time.monotonic() < deadline:
            time.sleep(0.05)
        if _posix_process_group_exists(pid):
            return ";".join(actions) + ";TERMINAL:UNPROVEN", False
    return ";".join(actions) + ";TERMINAL:PROVEN", True


def _validate_process_invocation(
    argv: tuple[object, ...],
    *,
    cwd: Path,
    required_markers: tuple[object, ...],
    timeout_seconds: float | None,
    termination_grace_seconds: float,
    environment: Mapping[object, object] | None,
) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, str] | None]:
    if not argv or any(not isinstance(part, str) or not part for part in argv):
        raise ValueError("argv must contain nonempty strings")
    if any("\0" in part for part in argv):
        raise ValueError("argv cannot contain embedded NUL bytes")
    if any(
        not isinstance(marker, str) or not marker or "\0" in marker
        for marker in required_markers
    ):
        raise ValueError("required markers must be nonempty NUL-free strings")
    if timeout_seconds is not None and timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if termination_grace_seconds <= 0:
        raise ValueError("termination_grace_seconds must be positive")
    if "\0" in str(cwd):
        raise ValueError("cwd cannot contain an embedded NUL byte")
    if not cwd.exists():
        raise FileNotFoundError(f"cwd does not exist: {cwd}")
    if not cwd.is_dir():
        raise NotADirectoryError(f"cwd is not a directory: {cwd}")
    selected_environment: dict[str, str] | None = None
    if environment is not None:
        try:
            items = tuple(environment.items())
        except Exception as exc:
            raise TypeError("environment must be a string mapping") from exc
        selected_environment = {}
        for key, value in items:
            if not isinstance(key, str) or not key:
                raise TypeError("environment keys must be nonempty strings")
            if not isinstance(value, str):
                raise TypeError("environment values must be strings")
            if "\0" in key or "\0" in value:
                raise ValueError("environment cannot contain embedded NUL bytes")
            if "=" in key:
                raise ValueError("environment keys cannot contain '='")
            selected_environment[key] = value
    return (
        tuple(part for part in argv if isinstance(part, str)),
        tuple(marker for marker in required_markers if isinstance(marker, str)),
        selected_environment,
    )


def _close_prestart_evidence_stream(
    stream: BinaryIO,
    outcome: dict[str, object],
) -> None:
    try:
        stream.flush()
        os.fsync(stream.fileno())
    except BaseException as exc:
        outcome.setdefault("evidence_error", exc)
    try:
        stream.close()
    except BaseException as exc:
        outcome.setdefault("evidence_error", exc)
    outcome["evidence_complete"] = "evidence_error" not in outcome


def supervise_command(
    argv: Sequence[str],
    *,
    cwd: Path,
    run_id: str,
    phase: str,
    command_index: int,
    evidence_root: Path,
    required_markers: Sequence[str] = (),
    timeout_seconds: float | None = None,
    termination_grace_seconds: float = TERMINATION_GRACE_SECONDS,
    environment: Mapping[str, str] | None = None,
    mirror_stdout: bool = True,
    mirror_stderr: bool = True,
    platform_name: str | None = None,
    launch_input: _ScanLaunchInput | None = None,
    execution_deadline_ns: int | None = None,
    output_limits: dict | None = None,
    output_observation: dict | None = None,
    preflight_launch: tuple | None = None,
) -> CommandExecutionReceiptV1:
    """Launch one shell-free child and retain PID, output, and native exit custody."""

    if output_limits is not None:
        if (type(output_limits) is not dict
                or set(output_limits) != {"stdout_bytes", "stderr_bytes", "combined_output_bytes"}
                or any(type(v) is not int or v < 0 for v in output_limits.values())
                or output_limits["stdout_bytes"] + output_limits["stderr_bytes"] > output_limits["combined_output_bytes"]
                or type(output_observation) is not dict or output_observation):
            raise ValueError("exact finite separate and combined native output operands required")
    elif output_observation is not None:
        raise ValueError("native output observation requires finite limits")
    if execution_deadline_ns is not None:
        remaining_seconds = _execution_remaining_seconds_v1(execution_deadline_ns)
        if timeout_seconds is not None and (type(timeout_seconds) not in (int, float)
                or not math.isfinite(timeout_seconds) or timeout_seconds <= 0):
            raise ValueError("relative execution cap must be finite and positive")
        timeout_seconds = (remaining_seconds if timeout_seconds is None
                           else min(timeout_seconds, remaining_seconds))
    selected_platform = os.name if platform_name is None else platform_name
    evidence_root = Path(evidence_root).resolve(strict=False)
    (
        stdout_path,
        stderr_path,
        receipt_path,
        reservation_path,
        stdout_stream,
        stderr_stream,
    ) = _reserve_command_evidence_files(evidence_root, command_index)
    started_utc = _utc_now_text()
    started_monotonic = time.monotonic()
    try:
        raw_argv: tuple[object, ...] = tuple(argv)
    except Exception as exc:
        raw_argv = ()
        tuple_error: Exception | None = exc
    else:
        tuple_error = None
    try:
        raw_markers: tuple[object, ...] = tuple(required_markers)
    except Exception as exc:
        raw_markers = ()
        marker_tuple_error: Exception | None = exc
    else:
        marker_tuple_error = None
    try:
        cwd_text = os.fspath(cwd)
        if not isinstance(cwd_text, str):
            raise TypeError("cwd must be a text path")
        receipt_cwd = Path(os.path.abspath(os.path.normpath(cwd_text)))
    except Exception as exc:
        receipt_cwd = Path.cwd().resolve()
        cwd_error: Exception | None = exc
    else:
        cwd_error = None
    receipt_argv = tuple(
        part if isinstance(part, str) else f"<INVALID_ARG:{type(part).__name__}>"
        for part in raw_argv
    ) or ("<INVALID_EMPTY_ARGV>",)
    receipt_markers = tuple(
        marker
        if isinstance(marker, str) and marker
        else f"<INVALID_MARKER:{type(marker).__name__}>"
        for marker in raw_markers
    )
    pid: int | None = None
    native_exit: int | None = None
    start_failure: str | None = None
    receipt_timeout_seconds = (
        float(timeout_seconds)
        if isinstance(timeout_seconds, (int, float)) and timeout_seconds > 0
        else None
    )
    timeout_state = (
        "NOT_CONFIGURED" if receipt_timeout_seconds is None else "NOT_TRIGGERED"
    )
    termination_state = "NOT_REQUIRED"
    failure_class: str | None = None
    stdout_outcome: dict[str, object] = {
        "drained_byte_count": 0,
        "evidence_write_enabled": True,
        "mirror": sys.stdout if mirror_stdout else None,
    }
    stderr_outcome: dict[str, object] = {
        "drained_byte_count": 0,
        "evidence_write_enabled": True,
        "mirror": sys.stderr if mirror_stderr else None,
    }
    if output_limits is not None:
        for stream, outcome in (("stdout", stdout_outcome), ("stderr", stderr_outcome)):
            outcome.update(retention_limit=output_limits[stream + "_bytes"], cleanup_drained_byte_count=0)
    process: subprocess.Popen[bytes] | None = None
    selected_argv: tuple[str, ...] | None = None
    selected_markers: tuple[str, ...] | None = None
    selected_environment: dict[str, str] | None = None
    receipt = None
    job_scope = None
    linux_scope = None
    linux_start_failed = False
    try:
        try:
            if tuple_error is not None:
                raise tuple_error
            if marker_tuple_error is not None:
                raise marker_tuple_error
            if cwd_error is not None:
                raise cwd_error
            selected_argv, selected_markers, selected_environment = (
                _validate_process_invocation(
                    raw_argv,
                    cwd=receipt_cwd,
                    required_markers=raw_markers,
                    timeout_seconds=timeout_seconds,
                    termination_grace_seconds=termination_grace_seconds,
                    environment=environment,
                )
            )
            if preflight_launch is not None:
                if type(preflight_launch) is not tuple or len(preflight_launch) != 2:
                    raise ValueError("original preflight launch projection required")
                _preflight_launch_guard_v1(selected_argv, selected_environment,
                    expected_argv=preflight_launch[0], expected_environment=preflight_launch[1])
            elif _preflight_vector_v1(selected_argv) and (os.environ if selected_environment is None else selected_environment).get(RUN_ID_ENV):
                raise ValueError("selected canonical preflight has no parent startup projection")
            job_scope = _WINDOWS_JOB_SCOPE_V1.get()
            linux_scope = _LINUX_PREFLIGHT_PROCESS_V1.get()
            if linux_scope is not None:
                if (type(linux_scope) is not _LinuxPreflightScopeV1 or job_scope is not None
                        or selected_platform != 'posix' or output_limits is None or launch_input is not None
                        or phase != 'fast-preflight-native-service'
                        or execution_deadline_ns != linux_scope.execution_deadline_ns):
                    raise ValueError('exact isolated Linux service supervision required')
            if job_scope is not None:
                if type(job_scope) is not _WindowsJobScopeV1 or output_limits is None or selected_platform != 'nt':
                    raise ValueError("explicit bounded Windows job invocation required")
                job_scope.match(run_id=run_id,phase=phase,command_index=command_index,argv=selected_argv,
                    cwd=receipt_cwd,evidence_root=evidence_root,environment=selected_environment,
                    execution_deadline_ns=execution_deadline_ns)
            original_stdin = subprocess.DEVNULL
            if launch_input is not None:
                if type(launch_input) not in (_ScanLaunchInput, _PreflightLaunchInputV1):
                    raise TypeError("original source-known launch input required")
                if type(launch_input) is _PreflightLaunchInputV1:
                    if (preflight_launch is None or phase != "fast-preflight"
                            or output_limits != launch_input.output_limits
                            or execution_deadline_ns != launch_input.deadline_ns
                            or selected_environment != launch_input.environment):
                        raise ValueError("preflight launch lacks its original bounded projection")
                original_stdin = launch_input._claim(
                    run_id=run_id, phase=phase, command_index=command_index,
                    argv=selected_argv, cwd=receipt_cwd)
            if execution_deadline_ns is not None:
                # Reservation, input validation and startup preparations consume
                # the original allowance, rather than moving its deadline.
                _execution_remaining_seconds_v1(execution_deadline_ns)
            if job_scope is not None:
                process = job_scope.create_suspended(original_stdin)
            elif linux_scope is not None:
                process = linux_scope.create(selected_argv,receipt_cwd,selected_environment)
            else:
                process = subprocess.Popen(
                    list(selected_argv),
                    cwd=receipt_cwd,
                    env=selected_environment,
                    shell=False,
                    stdin=original_stdin,
                    close_fds=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    **hidden_subprocess_kwargs(
                        platform_name=selected_platform,
                        new_process_group=True,
                    ),
                )
            pid = process.pid
        except Exception as exc:
            owned = getattr(exc, 'owned_process', None)
            if linux_scope is not None and type(owned) is _LinuxPreflightProcessV1 and owned is linux_scope.process:
                process = owned
                pid = process.pid
                linux_start_failed = True
            if (job_scope is not None and type(owned) is _WindowsJobProcessV1
                    and owned is job_scope.process and owned._info.process):
                process = owned
                pid = process.pid
            if process is not None and job_scope is None and linux_scope is None:
                raise
            start_failure = (str(exc) if job_scope is not None or linux_scope is not None else type(exc).__name__)
            failure_class = "ENGVR_PROCESS_START_FAILED"
            if process is None:
                _close_prestart_evidence_stream(stdout_stream, stdout_outcome)
                _close_prestart_evidence_stream(stderr_stream, stderr_outcome)
            elif not linux_start_failed:
                _scan_output_failure(stdout_outcome, exc)
        except BaseException as body:
            owned = getattr(body, 'owned_process', None)
            if (type(linux_scope) is _LinuxPreflightScopeV1 and type(owned) is _LinuxPreflightProcessV1
                    and owned is linux_scope.process):
                process = owned
                pid = process.pid
            if (job_scope is not None and type(owned) is _WindowsJobProcessV1
                    and owned is job_scope.process and owned._info.process):
                process = owned
                pid = process.pid
            if process is not None:
                if job_scope is not None or type(linux_scope) is _LinuxPreflightScopeV1:
                    failures = [body]
                    try:
                        _terminate_owned_process_tree(process,platform_name=selected_platform,
                            grace_seconds=termination_grace_seconds)
                        (job_scope if job_scope is not None else linux_scope).finish()
                    except BaseException as cleanup_error:
                        failures.append(cleanup_error)
                    _scan_raise_errors(failures)
                raise
            failures = [body]
            for stream, outcome in ((stdout_stream, stdout_outcome), (stderr_stream, stderr_outcome)):
                _close_prestart_evidence_stream(stream, outcome)
                if "evidence_error" in outcome:
                    failures.append(outcome["evidence_error"])
            _scan_raise_errors(failures)

        if linux_start_failed:
            try:
                linux_scope.recover_failed_start()
                termination_state='OWNED_FAILED_START_RESOURCE_SETTLED;NO_APPLICATION_SUCCESS'
            except BaseException as exc:
                linux_scope.history.append(dict(supervisor_startup_cleanup_error=repr(exc)))
                termination_state='OWNED_FAILED_START_RESOURCE_UNRESOLVED'
                failure_class='ENGVR_PROCESS_TERMINATION_FAILED'
            # Preserve actual spool bytes even without a completed application
            # command. A qualified empty slice permits EOF, not an invented exit.
            for pipe,stream,outcome in ((process.stdout,stdout_stream,stdout_outcome),
                    (process.stderr,stderr_stream,stderr_outcome)):
                try:
                    with linux_scope.query.owned_resource_phase():
                        for attempt in range(1025):
                            linux_scope.query.check(settling=True)
                            consumed,eof=_consume_available_pipe(pipe,stream,outcome=outcome,
                                native_terminal=linux_scope.settled)
                            if eof:
                                outcome['eof_observed']=True
                                break
                            if not consumed:
                                _scan_output_failure(outcome,RuntimeError('LINUX_PREFLIGHT_STARTUP_STREAM_TERMINAL_UNPROVED'))
                                break
                        else:_scan_output_failure(outcome,RuntimeError('LINUX_PREFLIGHT_STARTUP_STREAM_BOUND'))
                except BaseException as exc:_scan_output_failure(outcome,exc)
                finally:_finalize_owned_output_resources(pipe,stream,outcome=outcome)
        if process is not None and not linux_start_failed:
            if job_scope is not None and not any('evidence_error' in value for value in (stdout_outcome,stderr_outcome)):
                try:
                    job_scope.verify_created()
                except Exception as exc:
                    _scan_output_failure(stdout_outcome, exc)
            if launch_input is not None:
                try:
                    launch_input._attached(process)
                except Exception as exc:
                    _scan_output_failure(stdout_outcome, exc)
            if job_scope is not None and not any('evidence_error' in value for value in (stdout_outcome,stderr_outcome)):
                try:
                    job_scope.resume()
                except Exception as exc:
                    _scan_output_failure(stdout_outcome, exc)
            native_exit, timeout_state, termination_state, failure_class = (
                _supervise_native_output(
                    process,
                    stdout_stream=stdout_stream,
                    stderr_stream=stderr_stream,
                    stdout_outcome=stdout_outcome,
                    stderr_outcome=stderr_outcome,
                    started_monotonic=started_monotonic,
                    timeout_seconds=timeout_seconds,
                    termination_grace_seconds=termination_grace_seconds,
                    platform_name=selected_platform,
                    **({"execution_deadline_ns": execution_deadline_ns}
                       if execution_deadline_ns is not None else {}),
                )
            )
            if failure_class != "ENGVR_PROCESS_TERMINATION_FAILED" and any(
                "evidence_error" in outcome
                for outcome in (stdout_outcome, stderr_outcome)
            ):
                failure_class = "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED"
            if failure_class is None and native_exit != 0:
                failure_class = "ENGVR_NATIVE_EXIT_NONZERO"
            if launch_input is not None:
                try:
                    launch_input._finished(process, native_exit)
                except Exception as exc:
                    _scan_output_failure(stdout_outcome, exc)
                    if failure_class != "ENGVR_PROCESS_TERMINATION_FAILED":
                        failure_class = "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED"

        if job_scope is not None:
            try:
                if not job_scope.finish():
                    failure_class = "ENGVR_PROCESS_TERMINATION_FAILED"
            except Exception as exc:
                _scan_output_failure(stdout_outcome, exc)
                failure_class = "ENGVR_PROCESS_TERMINATION_FAILED"
        if type(linux_scope) is _LinuxPreflightScopeV1:
            try:
                if not linux_scope.finish():
                    failure_class = 'ENGVR_PROCESS_TERMINATION_FAILED'
            except BaseException as exc:
                _scan_output_failure(stdout_outcome,exc)
                failure_class = 'ENGVR_PROCESS_TERMINATION_FAILED'
        try:
            reservation_path.unlink()
        except OSError as exc:
            if process is not None and failure_class != "ENGVR_PROCESS_TERMINATION_FAILED":
                failure_class = "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED"
            stdout_outcome.setdefault("evidence_error", exc)

        try:
            stdout_count = stdout_path.stat().st_size
        except OSError as exc:
            stdout_outcome.setdefault("evidence_error", exc)
            stdout_count = None if output_limits is not None else 0
        try:
            stderr_count = stderr_path.stat().st_size
        except OSError as exc:
            stderr_outcome.setdefault("evidence_error", exc)
            stderr_count = None if output_limits is not None else 0
        if process is not None and failure_class != "ENGVR_PROCESS_TERMINATION_FAILED" and any(
            "evidence_error" in outcome for outcome in (stdout_outcome, stderr_outcome)
        ):
            failure_class = "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED"

        raw_evidence_complete = all(
            bool(outcome.get("evidence_complete", False))
            and "evidence_error" not in outcome
            for outcome in (stdout_outcome, stderr_outcome)
        )
        missing_markers: tuple[str, ...] = ()
        active_markers = (
            selected_markers if selected_markers is not None else receipt_markers
        )
        if not active_markers:
            marker_state = "NOT_REQUIRED"
        elif not raw_evidence_complete:
            marker_state = "EVIDENCE_UNAVAILABLE"
            if process is not None and failure_class != "ENGVR_PROCESS_TERMINATION_FAILED":
                failure_class = "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED"
        else:
            try:
                missing_markers = _file_marker_states(
                    (stdout_path,),
                    active_markers,
                )
            except OSError:
                marker_state = "EVIDENCE_UNAVAILABLE"
                if process is not None and failure_class != "ENGVR_PROCESS_TERMINATION_FAILED":
                    failure_class = "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED"
            else:
                marker_state = (
                    "PASS"
                    if not missing_markers
                    else "MISSING:" + ",".join(missing_markers)
                )
                if failure_class is None and missing_markers:
                    failure_class = "ENGVR_REQUIRED_MARKER_MISSING"
        elapsed = time.monotonic() - started_monotonic
        bounded_observation = None
        if output_limits is not None:
            bounded_observation = {"combined_output_grant": output_limits["combined_output_bytes"]}
            for stream, outcome in (("stdout", stdout_outcome), ("stderr", stderr_outcome)):
                bounded_observation[stream] = {
                    "retention_limit": outcome["retention_limit"],
                    "drained_byte_count": outcome["drained_byte_count"] if process is not None else None,
                    "cleanup_drained_byte_count": outcome["cleanup_drained_byte_count"] if process is not None else None,
                    "retained_byte_count": (stdout_count if stream == "stdout" else stderr_count) if process is not None else None,
                    "overflow": bool(outcome.get("overflow", False)),
                    "complete": (bool(outcome.get("evidence_complete", False)) and "evidence_error" not in outcome
                        and bool(outcome.get("eof_observed", False)) and bool(outcome.get("evidence_write_enabled", True))
                        and (stdout_count if stream == "stdout" else stderr_count) == outcome["drained_byte_count"] and process is not None),
                    "errors": [str(error) for error in outcome.get("errors", (outcome["evidence_error"],) if "evidence_error" in outcome else ())],
                }
            if type(launch_input) is _PreflightLaunchInputV1:
                # Failed prefixes retain their original unqualified result.
                # A complete proof must still match the parent-emitted frame.
                basis_counts = (dict(launch_input.basis_counts) if launch_input.result is None
                    else launch_input._proof_basis_counts())
                bounded_observation["preflight"] = {"identity": launch_input.identity,
                    "basis_counts": basis_counts,
                    "initial_limits": launch_input.delegated, "input_bytes": launch_input.extent,
                    "row_total": launch_input.row_total, "parent_spend": launch_input.parent_spend,
                    "parent_tail": launch_input.tail, "receiver": launch_input.result}
            if type(launch_input) is _PreflightLaunchInputV1 and launch_input.native_basis is not None:
                bounded_observation['preflight'].update(basis_kind='NATIVE_IMMUTABLE_V2',native_read_observation=
                    None if launch_input.result is None else launch_input.result['native_read_observation'])
            if job_scope is not None:
                bounded_observation['windows_job'] = job_scope.projection()
            output_observation.update(bounded_observation)
        if linux_start_failed:
            # The unchanged receipt schema does not pair a start-failure field
            # with a genuinely bound PID. Preserve that case in its projection.
            if pid is not None:start_failure=None
            else:failure_class='ENGVR_PROCESS_START_FAILED'
            bounded_observation['linux_startup']=dict(primary_error=repr(linux_scope.startup_error),
                bound_pid=pid,resource_settled=linux_scope.settled,
                recovery_error=None if linux_scope.failure_recovery_error is None else repr(linux_scope.failure_recovery_error))
            output_observation.update(bounded_observation)
        receipt = CommandExecutionReceiptV1(
            schema_version=SCHEMA_VERSION,
            run_id=run_id,
            phase=phase,
            command_index=command_index,
            argv=receipt_argv if selected_argv is None else selected_argv,
            cwd=str(receipt_cwd),
            pid=pid,
            platform=selected_platform,
            start_time_utc=started_utc,
            end_time_utc=_utc_now_text(),
            elapsed_monotonic_seconds=elapsed,
            native_exit_code=native_exit,
            start_failure_class=start_failure,
            timeout_seconds_or_null=receipt_timeout_seconds,
            timeout_state=timeout_state,
            termination_state=termination_state,
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            stdout_byte_count=stdout_count,
            stderr_byte_count=stderr_count,
            stdout_required_markers=active_markers,
            stdout_marker_state=marker_state,
            stderr_was_nonempty=None if stderr_count is None else stderr_count > 0,
            failure_class=failure_class,
            output_observation=bounded_observation,
            **(_COMMAND_PROJECTION_V1.get() or {}),
        )
        try:
            atomic_write_json(receipt_path, receipt)
        except Exception as publication_error:
            if _command_requires_process_retention_v1(receipt):
                error = ValidationReliabilityError(
                    "ENGVR_PROCESS_TERMINATION_FAILED",
                    "command receipt publication failed with unresolved process custody",
                )
                error.command_receipt = receipt
                error.owned_process = process
                raise error from publication_error
            if receipt.pid is not None:
                receipt = replace(
                    receipt,
                    failure_class="ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
                )
            else:
                raise
        return receipt
    except BaseException as exc:
        if process is not None:
            # A taskkill error may already own a different, unresolved process.
            if getattr(exc, "owned_process", process) is not process:
                exc.command_process = process
            else:
                exc.owned_process = process
        if receipt is not None and not hasattr(exc, "command_receipt"):
            exc.command_receipt = receipt
        raise


def _lexical_absolute_path(path: Path | str, *, field_name: str) -> Path:
    value = Path(path)
    if not value.is_absolute():
        raise ValidationReliabilityError(
            "ENGVR_RUN_SCOPED_CLEANUP_FAILED",
            f"{field_name} must be absolute: {value}",
        )
    if ".." in value.parts:
        raise ValidationReliabilityError(
            "ENGVR_RUN_SCOPED_CLEANUP_FAILED",
            f"{field_name} has traversal ambiguity: {value}",
        )
    return Path(os.path.abspath(os.path.normpath(str(value))))


def _lexical_path_key(path: Path) -> str:
    return os.path.normcase(os.path.normpath(os.path.abspath(str(path))))


def _lexically_inside_or_equal(path: Path, parent: Path) -> bool:
    try:
        return os.path.normcase(os.path.commonpath((str(path), str(parent)))) == (
            os.path.normcase(str(parent))
        )
    except ValueError:
        return False


def _path_is_junction(path: Path) -> bool:
    predicate = getattr(path, "is_junction", None)
    return bool(predicate()) if callable(predicate) else False


def remove_exact_run_owned_process_tree(
    target: Path | str,
    *,
    expected_run_root: Path | str,
    repo_root: Path | str,
    evidence_root: Path | str | None = None,
) -> int:
    cleanup_target = _lexical_absolute_path(target, field_name="cleanup target")
    expected = _lexical_absolute_path(
        expected_run_root,
        field_name="expected run root",
    )
    repository = _lexical_absolute_path(repo_root, field_name="repository root")
    if _lexical_path_key(cleanup_target) != _lexical_path_key(expected):
        raise ValidationReliabilityError(
            "ENGVR_RUN_SCOPED_CLEANUP_FAILED",
            "cleanup target is not the exact current run-owned root",
        )
    if cleanup_target == cleanup_target.parent:
        raise ValidationReliabilityError(
            "ENGVR_RUN_SCOPED_CLEANUP_FAILED",
            "cleanup target cannot be a filesystem root or process-root parent",
        )
    cleanup_canonical = cleanup_target.resolve(strict=False)
    expected_canonical = expected.resolve(strict=False)
    if cleanup_canonical != expected_canonical:
        raise ValidationReliabilityError(
            "ENGVR_RUN_SCOPED_CLEANUP_FAILED",
            "cleanup target canonical path differs from the expected run root",
        )
    if cleanup_target.name.endswith(".evidence"):
        raise ValidationReliabilityError(
            "ENGVR_RUN_SCOPED_CLEANUP_FAILED",
            "refusing an evidence directory as a process cleanup target",
        )
    if cleanup_target.exists() and (
        cleanup_target.is_symlink() or _path_is_junction(cleanup_target)
    ):
        raise ValidationReliabilityError(
            "ENGVR_RUN_SCOPED_CLEANUP_FAILED",
            "cleanup target cannot be a symlink or junction",
        )
    local = (
        _lexically_inside_or_equal(cleanup_target, repository)
        or _path_is_relative_to(cleanup_canonical, repository.resolve(strict=False))
    )
    if local:
        _local_cleanup_owner(repository, cleanup_target,
                             None if evidence_root is None else Path(evidence_root))
    if evidence_root is not None:
        evidence = _lexical_absolute_path(
            evidence_root,
            field_name="evidence root",
        )
        evidence_canonical = evidence.resolve(strict=False)
        if (
            _lexical_path_key(cleanup_target) == _lexical_path_key(evidence)
            or _lexically_inside_or_equal(evidence, cleanup_target)
            or _path_is_relative_to(evidence_canonical, cleanup_canonical)
        ):
            raise ValidationReliabilityError(
                "ENGVR_RUN_SCOPED_CLEANUP_FAILED",
                "cleanup target conflicts with the retained evidence root",
            )

    retried_paths: set[str] = set()

    def recover_windows_read_only(
        failed_function: object,
        failed_path: object,
        exception: BaseException,
    ) -> None:
        if os.name != "nt" or not isinstance(exception, PermissionError):
            raise exception
        retry_path = _lexical_absolute_path(
            Path(os.fsdecode(failed_path)),
            field_name="read-only retry path",
        )
        retry_canonical = retry_path.resolve(strict=False)
        if not (
            _lexically_inside_or_equal(retry_path, cleanup_target)
            and _path_is_relative_to(retry_canonical, cleanup_canonical)
        ):
            raise exception
        retry_key = _lexical_path_key(retry_path)
        if retry_key in retried_paths:
            raise exception
        if not callable(failed_function):
            raise exception
        retried_paths.add(retry_key)
        try:
            os.chmod(retry_path, stat.S_IWRITE, follow_symlinks=False)
            failed_function(retry_path)
        except Exception as retry_exc:
            raise ValidationReliabilityError(
                "ENGVR_RUN_SCOPED_CLEANUP_FAILED",
                "exact read-only path retry failed: "
                f"{type(retry_exc).__name__}: {retry_exc}",
            ) from retry_exc

    if os.path.lexists(cleanup_target):
        shutil.rmtree(cleanup_target, onexc=recover_windows_read_only)
    if os.path.lexists(cleanup_target):
        raise OSError("run root remains after exact cleanup")
    if local:
        with _RUN_NAME_LOCK:
            _LOCAL_RUN_OWNERS.pop(_lexical_path_key(cleanup_target), None)
    return len(retried_paths)


def cleanup_validation_run(paths: ValidationRunPathsV1) -> str:
    # Preserve lexical identity so an exchanged root link is rejected, not followed.
    target = _lexical_absolute_path(paths.cleanup_target, field_name="cleanup target")
    state = "PASS_ALREADY_ABSENT"
    read_only_retry_count = 0
    try:
        if os.path.lexists(target):
            read_only_retry_count = remove_exact_run_owned_process_tree(
                target,
                expected_run_root=paths.process_root,
                repo_root=paths.repo_root,
                evidence_root=paths.evidence_root,
            )
            state = "PASS_REMOVED_EXACT_RUN_ROOT"
        if os.path.lexists(target):
            raise OSError("run root remains after cleanup")
    except (OSError, ValidationReliabilityError) as exc:
        state = f"FAIL:{type(exc).__name__}:{exc}"
    atomic_write_json(
        paths.evidence_root / "cleanup.json",
        {
            "schema_version": SCHEMA_VERSION,
            "run_id": paths.run_id,
            "cleanup_target": str(target),
            "cleanup_state": state,
            "parent_preserved": True,
            "process_child_name": paths.process_child_name,
            "deepest_projected_path": str(paths.deepest_projected_path),
            "deepest_projected_path_text_length": (
                paths.deepest_projected_path_text_length
            ),
            "filesystem_probe_state": paths.filesystem_probe_state,
            "read_only_retry_count": read_only_retry_count,
        },
    )
    if state.startswith("FAIL"):
        raise ValidationReliabilityError("ENGVR_RUN_SCOPED_CLEANUP_FAILED", state)
    return state


# Selected RP5A native capture shares the ordinary supervisor's process owner.
def _scan_raise_errors(errors):
    unique = []
    for error in errors:
        if not any(error is earlier for earlier in unique):
            unique.append(error)
    if len(unique) == 1:
        raise unique[0]
    if unique:
        raise BaseExceptionGroup("native scan body and cleanup failures", unique)


def _scan_output_failure(outcome, error):
    outcome.setdefault("errors", []).append(error)
    outcome.setdefault("evidence_error", error)
    outcome["evidence_write_enabled"] = False
    outcome["mirror"] = None


def _capture_scan_output(
    argv, *, cwd, environment, stdout_stream, stderr_stream,
    stdout_limit, stderr_limit, deadline_ns, allow_no_match,
):
    """Own both original writers from entry; return only complete native evidence."""
    outcomes = tuple({"drained_byte_count": 0, "retained_byte_count": 0,
                      "retention_limit": limit, "evidence_write_enabled": True, "mirror": None}
                     for limit in (stdout_limit, stderr_limit))
    errors = []
    process = None
    native_exit = None
    try:
        for limit in (stdout_limit, stderr_limit):
            if type(limit) is not int or limit < 0:
                raise ValueError("scan channel limit must be a nonnegative integer")
        if type(allow_no_match) is not bool:
            raise ValueError("scan no-match policy must be an exact Boolean")
        now = _scan_deadline(deadline_ns)
        if stdout_stream is stderr_stream:
            raise ValueError("scan output writers alias")
        left, right = (os.fstat(stream.fileno()) for stream in (stdout_stream, stderr_stream))
        if (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino):
            raise ValueError("scan output files alias")
        for value in (left, right):
            if not stat.S_ISREG(value.st_mode) or value.st_nlink != 1 or value.st_size != 0:
                raise ValueError("scan output must be an original empty regular file")
        timeout = (deadline_ns - now) / 1_000_000_000
        selected, _, child = _validate_process_invocation(
            tuple(argv), cwd=Path(cwd), required_markers=(), timeout_seconds=timeout,
            termination_grace_seconds=TERMINATION_GRACE_SECONDS, environment=environment)
        _scan_deadline(deadline_ns)
        process = subprocess.Popen(
            list(selected), cwd=cwd, env=child, shell=False, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            **hidden_subprocess_kwargs(platform_name=os.name, new_process_group=True))
        native_exit, timeout_state, termination_state, failure = _supervise_native_output(
            process, stdout_stream=stdout_stream, stderr_stream=stderr_stream,
            stdout_outcome=outcomes[0], stderr_outcome=outcomes[1],
            started_monotonic=now / 1_000_000_000, timeout_seconds=timeout,
            termination_grace_seconds=TERMINATION_GRACE_SECONDS, platform_name=os.name)
        for outcome in outcomes:
            errors.extend(outcome.get("errors", ()))
        if errors:
            _scan_raise_errors(errors)
        if (failure is not None or type(native_exit) is not int
                or native_exit not in ({0, 1} if allow_no_match else {0})
                or not all(value.get("evidence_complete") is True
                           and value.get("writer_closed") is True for value in outcomes)):
            raise RuntimeError(f"native scan incomplete: exit={native_exit!r}; {failure}; {timeout_state}; {termination_state}")
        completed = subprocess.CompletedProcess(list(selected), native_exit)
        _scan_deadline(deadline_ns)
        return completed, outcomes[0], outcomes[1]
    except BaseException as exc:
        # Preserve the actual terminal observation and original channel counters.
        # None means no confirmed native exit, never an invented zero or one.
        exc.scan_native_exit_code = native_exit
        exc.scan_output_outcomes = outcomes
        errors = [exc]
        # After transfer, supervision owns close even if its result is a failure.
        if process is None:
            for stream, outcome in zip((stdout_stream, stderr_stream), outcomes, strict=True):
                if outcome.get("close_attempted"):
                    continue
                outcome["close_attempted"] = True
                try:
                    stream.close()
                except BaseException as close_error:
                    errors.append(close_error)
        _scan_raise_errors(errors)


def _scan_deadline(deadline_ns):
    if type(deadline_ns) is not int or deadline_ns <= 0:
        raise ValueError("scan deadline must be an original positive integer")
    now = time.monotonic_ns()
    if type(now) is not int or now >= deadline_ns:
        raise TimeoutError("original scan deadline expired")
    return now


@dataclass(frozen=True)
class _ScanRunReadLimits:
    byte_limit: int
    node_limit: int
    depth_limit: int
    profile_limit: int

    def __post_init__(self):
        for value in (self.byte_limit, self.node_limit, self.depth_limit, self.profile_limit):
            if type(value) is not int or value <= 0:
                raise ValueError("scan record limits must be exact positive integers")


@dataclass(frozen=True)
class _Rp5aScanProfile:
    run_id: str
    command_index: int
    repo_root: str
    scratch_root: str
    expected_inventory: tuple[str, ...]
    inventory_path_limit: int
    inventory_utf8_limit: int
    file_sizes: tuple[tuple[str, int], ...]
    git_executable: str
    search_executable: str
    search_engine: str
    child_environment: tuple[tuple[str, str], ...]
    output_bytes: int
    scratch_bytes: int
    stderr_bytes_per_call: int
    readback_bytes: int
    deadline_ns: int
    max_invocations: int

    def __post_init__(self):
        if type(self.run_id) is not str or not self.run_id:
            raise ValueError("scan profile run identity missing")
        for name in ("command_index", "deadline_ns", "max_invocations"):
            if type(getattr(self, name)) is not int or getattr(self, name) <= 0:
                raise ValueError("scan profile positive integer required: " + name)
        for name in ("inventory_path_limit", "inventory_utf8_limit", "output_bytes", "scratch_bytes",
                     "stderr_bytes_per_call", "readback_bytes"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ValueError("scan profile nonnegative integer required: " + name)
        for name in ("repo_root", "scratch_root", "git_executable", "search_executable"):
            value = getattr(self, name)
            if type(value) is not str or not Path(value).is_absolute() or "\0" in value or ".." in Path(value).parts:
                raise ValueError("scan profile absolute original path required: " + name)
        if self.search_engine not in {"git", "rg"} or (self.search_engine == "git" and self.search_executable != self.git_executable):
            raise ValueError("scan profile engine/executable mismatch")
        if type(self.expected_inventory) is not tuple or len(self.expected_inventory) > self.inventory_path_limit:
            raise ValueError("scan inventory exceeds original cardinality")
        from tools.pr168_rp5a_git_grep_scanner import _scan_admitted_paths
        _scan_admitted_paths(self.expected_inventory, path_limit=self.inventory_path_limit,
                             byte_limit=self.inventory_utf8_limit)
        if type(self.file_sizes) is not tuple or len(self.file_sizes) > len(self.expected_inventory):
            raise ValueError("scan size observations exceed inventory")
        seen = set()
        inventory = set(self.expected_inventory)
        for pair in self.file_sizes:
            if (type(pair) is not tuple or len(pair) != 2 or type(pair[0]) is not str
                    or pair[0] not in inventory or pair[0] in seen
                    or type(pair[1]) is not int or pair[1] < 0):
                raise ValueError("invalid original scan size observation")
            seen.add(pair[0])
        if type(self.child_environment) is not tuple:
            raise ValueError("scan environment must be owned immutable pairs")
        keys = set()
        for pair in self.child_environment:
            if (type(pair) is not tuple or len(pair) != 2 or any(type(v) is not str for v in pair)
                    or not pair[0] or "=" in pair[0] or "\0" in pair[0] or "\0" in pair[1]
                    or pair[0].upper() in keys):
                raise ValueError("invalid scan child environment")
            keys.add(pair[0].upper())



@dataclass(frozen=True)
class _Rp5aReadBasisV1:
    baseline_ref: str
    historical_runner_bytes: bytes
    stdout_bytes_per_call: int
    status_record_limit: int
    path_byte_limit: int
    source_byte_limit: int
    manifest_node_limit: int
    manifest_command_limit: int
    manifest_argument_limit: int

    def __post_init__(self):
        if (type(self.baseline_ref) is not str
                or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", self.baseline_ref) is None):
            raise ValueError("original unique historical Git reference required")
        for name in tuple(self.__dataclass_fields__)[2:]:
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError("original positive reader basis counter required: " + name)
        if (type(self.historical_runner_bytes) is not bytes or not self.historical_runner_bytes
                or len(self.historical_runner_bytes) > self.source_byte_limit):
            raise ValueError("bounded immutable complete historical runner required")


def _rp5a_basis_projection_v1(basis, *, wire=False):
    if type(basis) is not _Rp5aReadBasisV1:
        raise TypeError("original typed RP5A reader basis required")
    values = {name: getattr(basis, name) for name in basis.__dataclass_fields__}
    values["historical_runner_bytes"] = (_ScanHex(basis.historical_runner_bytes) if wire
                                          else basis.historical_runner_bytes.hex())
    return MappingProxyType(values) if wire else values


def _rp5a_basis_from_projection_v1(value):
    if not isinstance(value, Mapping) or set(value) != set(_Rp5aReadBasisV1.__dataclass_fields__):
        raise ValueError("invalid closed RP5A reader basis")
    original = value["historical_runner_bytes"]
    if (type(original) is not str or len(original) % 2
            or re.fullmatch(r"[0-9a-f]+", original) is None
            or type(value["source_byte_limit"]) is not int
            or len(original) // 2 > value["source_byte_limit"]):
        raise ValueError("invalid original historical byte representation")
    return _Rp5aReadBasisV1(**{**dict(value), "historical_runner_bytes": bytes.fromhex(original)})


def _rp5a_basis_map_projection_v1(bases):
    if not isinstance(bases, Mapping):
        raise TypeError("original reader basis mapping required")
    result = {}
    for index, basis in bases.items():
        if type(index) is not int or index <= 0:
            raise ValueError("invalid reader basis occurrence")
        result[str(index)] = _rp5a_basis_projection_v1(basis)
    return result


@dataclass(frozen=True)
class _ScanRunSnapshot:
    raw: bytes
    value: Mapping[str, object]


def _scan_lexical_json_limits(raw, limits):
    # Count containers, keys, strings and primitive tokens before constructing JSON.
    nodes = depth = 0
    string = escaped = token = False
    for byte in raw:
        if string:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                string = False
            continue
        if byte in b" \t\r\n,:{}[]\"":
            token = False
        if byte == 34:
            nodes += 1
            string = True
        elif byte in (123, 91):
            nodes += 1
            depth += 1
            if depth > limits.depth_limit:
                raise ValueError("scan run JSON depth overflow")
        elif byte in (125, 93):
            depth -= 1
            if depth < 0:
                raise ValueError("scan run JSON malformed nesting")
        elif byte not in b" \t\r\n,:" and not token:
            nodes += 1
            token = True
        if nodes > limits.node_limit:
            raise ValueError("scan run JSON node overflow")
    if string or depth:
        raise ValueError("scan run JSON truncated")


def _scan_owned_json(raw, limits):
    _scan_lexical_json_limits(raw, limits)

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate scan JSON key")
            result[key] = value
        return result

    def constant(value):
        raise ValueError("nonfinite scan JSON token: " + value)

    def real(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("nonfinite scan JSON real")
        return result

    value = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=pairs,
                       parse_constant=constant, parse_float=real)

    def freeze(value):
        if type(value) is dict:
            return MappingProxyType({key: freeze(item) for key, item in value.items()})
        if type(value) is list:
            return tuple(freeze(item) for item in value)
        return value

    return freeze(value)


def _scan_file_identity(value):
    if (not stat.S_ISREG(value.st_mode) or value.st_nlink != 1
            or _stat_is_reparse_point(value)):
        raise ValueError("scan file is not an original single-link regular file")
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns


def _scan_same_api_version(value):
    return (*_scan_file_identity(value), value.st_ctime_ns, value.st_mode)


def _read_scan_run_snapshot(evidence_root: Path, *, limits: _ScanRunReadLimits, deadline_ns: int):
    if type(limits) is not _ScanRunReadLimits:
        raise TypeError("original scan run limits required")
    _scan_deadline(deadline_ns)
    _local_unlinked_path(evidence_root)
    directory = evidence_root.lstat()
    path, before = _require_direct_regular_evidence_file(evidence_root, "run.json")
    identity = _scan_file_identity(before)
    if before.st_size > limits.byte_limit:
        raise ValueError("scan run record exceeds pre-read byte allowance")
    fd = None
    errors = []
    try:
        fd = _open_regular_worktree_descriptor(path, nonblocking=True)
        opened = os.fstat(fd)
        if _scan_file_identity(opened) != identity:
            raise ValueError("scan run descriptor differs from selected path")
        raw = bytearray()
        while True:
            _scan_deadline(deadline_ns)
            count = min(DEFAULT_SCAN_CHUNK_BYTES, limits.byte_limit - len(raw) + 1)
            chunk = os.read(fd, count)
            if type(chunk) is not bytes or len(chunk) > count:
                raise ValueError("invalid scan run descriptor read")
            if not chunk:
                break
            if len(raw) + len(chunk) > limits.byte_limit:
                raise ValueError("scan run record overflow")
            raw.extend(chunk)
        if len(raw) != before.st_size or _scan_same_api_version(os.fstat(fd)) != _scan_same_api_version(opened):
            raise ValueError("scan run record changed or truncated")
        if _scan_same_api_version(path.lstat()) != _scan_same_api_version(before):
            raise ValueError("scan run path changed")
        owned = bytes(raw)
        result = _ScanRunSnapshot(owned, _scan_owned_json(owned, limits))
    except BaseException as exc:
        errors.append(exc)
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except BaseException as exc:
                errors.append(exc)
    _scan_raise_errors(errors)
    _local_unlinked_path(evidence_root)
    after_directory = evidence_root.lstat()
    if (directory.st_dev, directory.st_ino, directory.st_mode) != (
            after_directory.st_dev, after_directory.st_ino, after_directory.st_mode):
        raise ValueError("scan evidence directory changed")
    if _scan_same_api_version(path.lstat()) != _scan_same_api_version(before):
        raise ValueError("scan run path changed after close")
    _scan_deadline(deadline_ns)
    return result


def _scan_profile_projection(profiles):
    if not isinstance(profiles, Mapping):
        raise TypeError("scan profiles must be an original mapping")
    result = {}
    for index, profile in profiles.items():
        if type(index) is not int or index <= 0 or type(profile) is not _Rp5aScanProfile or profile.command_index != index:
            raise ValueError("scan profile index mismatch")
        result[str(index)] = asdict(profile)
    return result



def _rp5a_reader_profiles_from_run_v1(attestation, value, *, command_index, repo_root,
                                    inherited_run_id, read_limits, deadline_ns, include_wire_binding=False):
    value = _mapper_strip_run_extension_v1(value)
    fields_run = {"schema_version", "run_id", "phase", "command_count", "text_integrity_preflight_state",
                  "paths", "filesystem_probe", "rp5a_scan_profiles", "rp5a_reader_profiles",
                  "rp5a_reader_bases", "rp5a_launch_wire_version"}
    if type(include_wire_binding) is not bool:
        raise TypeError("wire binding selection must be an exact Boolean")
    declared_version = value.get("rp5a_launch_wire_version")
    if type(declared_version) is int and declared_version == 3:
        fields_run |= {"rp5a_launch_wire_versions", "rp5a_payload_byte_limits"}
    if (set(value) != fields_run or type(declared_version) is not int
            or declared_version not in (2, 3)):
        raise ValueError("missing or invalid original reader-bearing run provenance")
    tables = (value["rp5a_scan_profiles"], value["rp5a_reader_profiles"])
    bases = value["rp5a_reader_bases"]
    if any(type(table) is not MappingProxyType for table in (*tables, bases)):
        raise ValueError("original immutable reader profile tables required")
    if (not tables[1] or set(tables[1]) != set(bases) or not set(tables[0]) <= set(tables[1])
            or sum(len(table) for table in tables) > read_limits.profile_limit):
        raise ValueError("invalid original reader/scanner profile coverage or count")
    parsed = []
    roots = []
    for table in tables:
        selected = {}
        for key, member in table.items():
            if (type(key) is not str or re.fullmatch(r"[1-9][0-9]*", key) is None
                    or int(key) > value["command_count"] or type(member) is not MappingProxyType
                    or set(member) != set(_Rp5aScanProfile.__dataclass_fields__)):
                raise ValueError("noncanonical original reader/scanner profile")
            profile = _Rp5aScanProfile(**dict(member))
            scratch = Path(profile.scratch_root)
            if (str(profile.command_index) != key or profile.run_id != inherited_run_id
                    or Path(profile.repo_root) != repo_root or profile.deadline_ns > deadline_ns
                    or scratch == attestation.process_root or not scratch.is_relative_to(attestation.process_root)
                    or scratch.is_relative_to(attestation.evidence_root) or attestation.evidence_root.is_relative_to(scratch)
                    or any(scratch.is_relative_to(root) or root.is_relative_to(scratch) for root in roots)):
                raise ValueError("original role allocation identity/deadline/overlap mismatch")
            _local_unlinked_path(scratch)
            if not scratch.is_dir():
                raise ValueError("original role scratch is unavailable")
            roots.append(scratch)
            selected[key] = profile
        parsed.append(selected)
    selected_version = 2
    selected_payload = 0
    if declared_version == 3:
        wire_map = value["rp5a_launch_wire_versions"]
        payload_map = value["rp5a_payload_byte_limits"]
        if (type(wire_map) is not MappingProxyType or type(payload_map) is not MappingProxyType
                or set(wire_map) != set(bases) or set(payload_map) != set(bases)):
            raise ValueError("streamed provenance tables require exact original reader coverage")
        versions, counts = _rp5a_wire_projection_v3(
            {int(key): member for key, member in wire_map.items()},
            {int(key): member for key, member in payload_map.items()},
            readers=parsed[1], scanners=parsed[0], command_count=value["command_count"])
        selected_version = versions[str(command_index)]
        selected_payload = counts[str(command_index)]
    parsed_bases = {key: _rp5a_basis_from_projection_v1(member) for key, member in bases.items()}
    index = str(command_index)
    if index not in parsed[1]:
        raise ValueError("selected reader occurrence is absent")
    result = attestation, parsed[0].get(index), parsed[1][index], parsed_bases[index]
    return (*result, selected_version, selected_payload) if include_wire_binding else result


def _read_scan_profile_for_run(
    repo_root: Path, *, command_index: int, inherited_run_id: str,
    inherited_evidence_root: Path, explicit_basetemp: Path,
    read_limits: _ScanRunReadLimits, deadline_ns: int,
    expected_phase=None, expected_command_count=None, reader_required=False, include_wire_binding=False,
):
    attestation = attest_inherited_validation_run(
        repo_root, inherited_run_id=inherited_run_id,
        inherited_evidence_root=inherited_evidence_root, explicit_basetemp=explicit_basetemp,
        scan_read_limits=read_limits, scan_deadline_ns=deadline_ns)
    snapshot = attestation._scan_snapshot
    if type(snapshot) is not _ScanRunSnapshot:
        raise ValueError("scan attestation lacks original bounded snapshot")
    value = snapshot.value
    if (type(value.get("schema_version")) is not int or value["schema_version"] != SCHEMA_VERSION
            or type(value.get("phase")) is not str or not value["phase"]
            or type(value.get("command_count")) is not int or value["command_count"] <= 0
            or type(command_index) is not int or not 1 <= command_index <= value["command_count"]):
        raise ValueError("invalid scan run header")
    if expected_phase is not None and value["phase"] != expected_phase:
        raise ValueError("scan phase differs from original launch")
    if expected_command_count is not None and value["command_count"] != expected_command_count:
        raise ValueError("scan count differs from original launch")
    if reader_required:
        return _rp5a_reader_profiles_from_run_v1(
            attestation, value, command_index=command_index, repo_root=repo_root,
            inherited_run_id=inherited_run_id, read_limits=read_limits, deadline_ns=deadline_ns,
            include_wire_binding=include_wire_binding)
    if any(key in value for key in ("rp5a_reader_profiles", "rp5a_reader_bases", "rp5a_launch_wire_version")):
        raise ValueError("reader-bearing provenance requires its original reader consumer")
    table = value.get("rp5a_scan_profiles")
    if not isinstance(table, Mapping) or not 0 < len(table) <= read_limits.profile_limit:
        raise ValueError("invalid bounded scan profile table")
    fields = tuple(_Rp5aScanProfile.__dataclass_fields__)
    for key, member in table.items():
        if (type(key) is not str or re.fullmatch(r"[1-9][0-9]*", key) is None
                or not isinstance(member, Mapping) or set(member) != set(fields)
                or type(member["command_index"]) is not int or str(member["command_index"]) != key):
            raise ValueError("noncanonical scan profile member")
    selected = table.get(str(command_index))
    if selected is None:
        raise ValueError("selected scan occurrence has no original profile")
    profile = _Rp5aScanProfile(**dict(selected))
    scratch = Path(profile.scratch_root)
    if (profile.run_id != inherited_run_id or Path(profile.repo_root) != repo_root
            or profile.deadline_ns > deadline_ns or scratch == attestation.process_root
            or not scratch.is_relative_to(attestation.process_root)
            or scratch == attestation.evidence_root or scratch.is_relative_to(attestation.evidence_root)
            or attestation.evidence_root.is_relative_to(scratch)):
        raise ValueError("scan profile differs from original run paths/deadline")
    _local_unlinked_path(scratch)
    if not scratch.is_dir():
        raise ValueError("original scan scratch does not exist")
    result = (attestation, profile)
    _scan_deadline(min(deadline_ns, profile.deadline_ns))
    return result



def _rp5a_consumer_role_v1(argv, repo_root):
    """Classify actual Python entry/selected pytest paths, never payload prose."""
    if type(argv) is not tuple or not argv or any(type(v) is not str for v in argv):
        raise TypeError("original command vector required")
    offset = 1
    while offset < len(argv) and argv[offset] in ("-B", "-I", "-u"):
        offset += 1
    if offset >= len(argv):
        return None
    root = Path(repo_root)
    entry = argv[offset].replace("\\", "/")
    if Path(entry).is_absolute():
        try:
            entry = Path(entry).relative_to(root).as_posix()
        except ValueError:
            return None
    if entry == "tools/build_pr168_rp5a_legacy_semantic_audit.py":
        return "EVIDENCE" if "--validation-scope-evidence-only" in argv[offset + 1:] else "SCANNER"
    if entry == "tools/validate_pr168_rp5a_legacy_semantic_audit.py":
        return "VALIDATE"
    if entry == "tools/run_pytest_fresh_basetemp.py":
        arguments = argv[offset + 1:]
    elif argv[offset:offset + 2] == ("-m", "pytest"):
        arguments = argv[offset + 2:]
    else:
        return None
    value_options = {"-k", "-m", "-c", "-o", "-p", "--basetemp", "--rootdir", "--confcutdir",
                     "--ignore", "--ignore-glob", "--deselect", "--maxfail", "--tb", "--color",
                     "--import-mode", "--override-ini", "--inifile", "--durations"}
    skip = False
    literals = False
    for value in arguments:
        if skip:
            skip = False
            continue
        if not literals and value == "--":
            literals = True
            continue
        if not literals and value.startswith("-"):
            skip = value in value_options
            continue
        selected = value.split("::", 1)[0].replace("\\", "/").rstrip("/")
        if Path(selected).is_absolute():
            try:
                selected = Path(selected).relative_to(root).as_posix()
            except ValueError:
                continue
        parts = selected.split("/")
        if parts[:2] == ["tests", "pr168_rp5a"] and all(p not in ("", ".", "..") for p in parts):
            return "PYTEST"
    return None


def _rp5a_wire_projection_v3(versions, payload_limits, *, readers, scanners, command_count):
    if not isinstance(versions, Mapping) or not isinstance(payload_limits, Mapping):
        raise TypeError("original immutable launch wire maps required")
    if set(versions) != set(payload_limits):
        raise ValueError("wire/payload maps require exact coverage")
    projected_versions = {}
    projected_limits = {}
    for index, version in versions.items():
        if type(index) is not int or not 1 <= index <= command_count or type(version) is not int or version not in (2, 3):
            raise ValueError("invalid original per-occurrence wire binding")
        count = _scan_v3_integer(payload_limits[index], "per-occurrence payload limit")
        if (version == 2 and count != 0) or (version == 3 and str(index) not in scanners):
            raise ValueError("streamed payload requires an original scanner occurrence")
        projected_versions[str(index)] = version
        projected_limits[str(index)] = count
    if set(projected_versions) != set(readers) or 3 not in projected_versions.values():
        raise ValueError("streamed tables require all reader occurrences and an actual v3 member")
    return projected_versions, projected_limits


def _scan_launch_wire_tables_v3(plan, inputs, readers, scanner_keys, repo_root):
    if not any(item.wire_version == 3 for item in inputs.values()):
        return None, None
    if set(inputs) != set(readers):
        raise ValueError("streamed plan requires exact reader input coverage")
    versions = {}
    payloads = {}
    for index, original in inputs.items():
        if (type(index) is not int or not 1 <= index <= len(plan) or type(original) is not _ScanLaunchInput
                or original.wire_version not in (2, 3)):
            raise ValueError("invalid original streamed launch occurrence")
        if original.wire_version == 3 and (
                index not in scanner_keys or _rp5a_consumer_role_v1(plan[index - 1].argv, repo_root) != "SCANNER"):
            raise ValueError("streamed launch is restricted to the original full scanner role")
        versions[index] = original.wire_version
        payloads[index] = original.payload_bytes
    _rp5a_wire_projection_v3(versions, payloads, readers={str(i) for i in readers},
                             scanners={str(i) for i in scanner_keys}, command_count=len(plan))
    return MappingProxyType(versions), MappingProxyType(payloads)


@dataclass(frozen=True)
class _ScanLaunch:
    paths: ValidationRunPathsV1
    phase: str
    plan: tuple
    profiles: Mapping[int, _Rp5aScanProfile]
    read_limits: _ScanRunReadLimits
    deadline_ns: int
    process_id: int
    thread_id: int

    launch_inputs: Mapping = field(default_factory=lambda: MappingProxyType({}), kw_only=True)
    reader_profiles: Mapping = field(default_factory=lambda: MappingProxyType({}), kw_only=True)
    reader_bases: Mapping = field(default_factory=lambda: MappingProxyType({}), kw_only=True)
    rp5a_launch_wire_versions: Mapping | None = field(default=None, kw_only=True)
    rp5a_payload_byte_limits: Mapping | None = field(default=None, kw_only=True)

    def __post_init__(self):
        # Own the new mappings even when the caller retained a mappingproxy's
        # backing dictionary. Preserve every original profile/basis object.
        if (type(self.reader_profiles) is not MappingProxyType
                or type(self.reader_bases) is not MappingProxyType):
            raise TypeError("reader launch mappings must be immutable")
        _scan_profile_projection(self.reader_profiles)
        _rp5a_basis_map_projection_v1(self.reader_bases)
        if set(self.reader_profiles) != set(self.reader_bases):
            raise ValueError("reader launch mappings require exact coverage")
        object.__setattr__(self, "reader_profiles", MappingProxyType(dict(self.reader_profiles)))
        object.__setattr__(self, "reader_bases", MappingProxyType(dict(self.reader_bases)))
        if (self.rp5a_launch_wire_versions is None) != (self.rp5a_payload_byte_limits is None):
            raise ValueError("streamed launch tables must appear together")
        if self.rp5a_launch_wire_versions is not None:
            if (type(self.rp5a_launch_wire_versions) is not MappingProxyType
                    or type(self.rp5a_payload_byte_limits) is not MappingProxyType):
                raise TypeError("streamed launch tables must be immutable")
            expected = _scan_launch_wire_tables_v3(self.plan, self.launch_inputs, self.reader_profiles,
                                                   set(self.profiles), self.paths.repo_root)
            if expected != (self.rp5a_launch_wire_versions, self.rp5a_payload_byte_limits):
                raise ValueError("streamed launch tables differ from actual original inputs")
            object.__setattr__(self, "rp5a_launch_wire_versions", MappingProxyType(dict(expected[0])))
            object.__setattr__(self, "rp5a_payload_byte_limits", MappingProxyType(dict(expected[1])))
        elif any(item.wire_version == 3 for item in self.launch_inputs.values()):
            raise ValueError("streamed input requires its exact original launch tables")


def _prepare_scan_launch(paths, *, phase, plan, profiles, read_limits, deadline_ns, launch_inputs=None,
                         reader_profiles=None, reader_bases=None):
    if type(paths) is not ValidationRunPathsV1 or type(plan) is not tuple or type(read_limits) is not _ScanRunReadLimits:
        raise TypeError("original scan launch operands required")
    _scan_deadline(deadline_ns)
    readers = {} if reader_profiles is None else dict(reader_profiles)
    bases = {} if reader_bases is None else dict(reader_bases)
    _scan_profile_projection(readers)
    _rp5a_basis_map_projection_v1(bases)
    if set(readers) != set(bases):
        raise ValueError("reader profiles and bases require exact coverage")
    if readers:
        roles = {row.command_index: _rp5a_consumer_role_v1(row.argv, paths.repo_root) for row in plan}
        if (set(readers) != {i for i, role in roles.items() if role is not None}
                or set(profiles) != {i for i, role in roles.items() if role == "SCANNER"}):
            raise ValueError("reader/scanner profiles differ from original role-derived coverage")
    _scan_profile_projection(profiles)
    if len(profiles) + len(readers) > read_limits.profile_limit:
        raise ValueError("scan launch profile count exceeds read allowance")
    for index, planned in enumerate(plan, 1):
        if (planned.command_index != index or planned.run_id != paths.run_id
                or planned.phase != phase or planned.cwd != str(paths.repo_root)):
            raise ValueError("scan launch original plan differs")
    roots = []
    for index, profile in (*profiles.items(), *readers.items()):
        if index > len(plan) or profile.run_id != paths.run_id or profile.repo_root != str(paths.repo_root) or profile.deadline_ns > deadline_ns:
            raise ValueError("scan profile does not belong to original launch")
        scratch = Path(profile.scratch_root)
        if (scratch == paths.process_root or not scratch.is_relative_to(paths.process_root)
                or scratch.is_relative_to(paths.evidence_root) or paths.evidence_root.is_relative_to(scratch)
                or any(scratch.is_relative_to(root) or root.is_relative_to(scratch) for root in roots)):
            raise ValueError("scan scratch roots overlap or escape original process root")
        _local_unlinked_path(scratch)
        if not scratch.is_dir():
            raise ValueError("scan source did not admit an existing scratch directory")
        roots.append(scratch)
    inputs = {} if launch_inputs is None else dict(launch_inputs)
    if (set(inputs) != set(readers)) if readers else bool(set(inputs) - set(profiles)):
        raise ValueError("launch input belongs to an unselected occurrence")
    for index, original_input in inputs.items():
        expected = _ScanLaunchIdentity(paths.run_id, phase, index, len(plan), plan[index - 1].argv, str(paths.repo_root))
        if type(original_input) is not _ScanLaunchInput or original_input.identity != expected:
            raise ValueError("original scan input differs from selected plan")
        if readers:
            if original_input.rp5a_read_basis is not bases[index] or original_input.parent_identity is not None:
                raise ValueError("direct parent input lost original reader basis identity")
            scratch = original_input.scratch_root
            if (scratch == paths.process_root or not scratch.is_relative_to(paths.process_root)
                    or scratch.is_relative_to(paths.evidence_root) or paths.evidence_root.is_relative_to(scratch)
                    or any(scratch.is_relative_to(root) or root.is_relative_to(scratch) for root in roots)):
                raise ValueError("input scratch overlaps the original scanner/reader allocation")
            _local_unlinked_path(scratch)
            if not scratch.is_dir():
                raise ValueError("input scratch was not admitted")
            roots.append(scratch)
    versions, payload_limits = _scan_launch_wire_tables_v3(plan, inputs, readers, set(profiles), paths.repo_root)
    return _ScanLaunch(paths, phase, plan, MappingProxyType(dict(profiles)), read_limits,
                       deadline_ns, os.getpid(), threading.get_ident(),
                       launch_inputs=MappingProxyType(inputs), reader_profiles=MappingProxyType(readers),
                       reader_bases=MappingProxyType(bases), rp5a_launch_wire_versions=versions,
                       rp5a_payload_byte_limits=payload_limits)


_SCAN_TRANSPORT_KEYS = (
    "QTT_SCAN_COMMAND_INDEX", "QTT_SCAN_PHASE", "QTT_SCAN_COMMAND_COUNT", "QTT_SCAN_DEADLINE_NS",
    "QTT_SCAN_BYTE_LIMIT", "QTT_SCAN_NODE_LIMIT", "QTT_SCAN_DEPTH_LIMIT", "QTT_SCAN_PROFILE_LIMIT",
)


def _scan_child_launch_environment(parent, *, launch, planned):
    if (type(launch) is not _ScanLaunch or launch.process_id != os.getpid()
            or launch.thread_id != threading.get_ident() or not any(planned is row for row in launch.plan)):
        raise ValueError("scan launch original owner/occurrence required")
    profile = launch.reader_profiles.get(planned.command_index) or launch.profiles.get(planned.command_index)
    if profile is None:
        raise ValueError("unselected scan occurrence")
    deadline = min(launch.deadline_ns, profile.deadline_ns)
    _scan_deadline(deadline)
    child = {}
    seen = set()
    controlled = set(_SCAN_TRANSPORT_KEYS) | {RUN_ID_ENV, EVIDENCE_ROOT_ENV, PROCESS_ROOT_ENV}
    for key, value in parent.items():
        if (type(key) is not str or type(value) is not str or not key or "=" in key
                or "\0" in key or "\0" in value or key.upper() in seen):
            raise ValueError("invalid scan launch environment")
        seen.add(key.upper())
        if key.upper() not in controlled:
            child[key] = value
    child.update({RUN_ID_ENV: launch.paths.run_id, EVIDENCE_ROOT_ENV: str(launch.paths.evidence_root),
                  PROCESS_ROOT_ENV: str(launch.paths.process_root)})
    values = (planned.command_index, launch.phase, len(launch.plan), deadline,
              launch.read_limits.byte_limit, launch.read_limits.node_limit,
              launch.read_limits.depth_limit, launch.read_limits.profile_limit)
    child.update({key: str(value) for key, value in zip(_SCAN_TRANSPORT_KEYS, values, strict=True)})
    return child


def _scan_read_forwarded_profile(repo_root, *, environment, explicit_basetemp, reader_required=False,
                                 include_wire_binding=False):
    original = {}
    for key, value in environment.items():
        if type(key) is not str or key.upper() in original or type(value) is not str:
            raise ValueError("invalid forwarded scan environment")
        original[key.upper()] = value
    values = []
    for key in _SCAN_TRANSPORT_KEYS:
        value = original.get(key)
        if type(value) is not str or not value:
            raise ValueError("missing forwarded scan operand: " + key)
        if key != "QTT_SCAN_PHASE":
            if re.fullmatch(r"[1-9][0-9]*", value) is None:
                raise ValueError("noncanonical forwarded scan integer")
            value = int(value)
        values.append(value)
    index, phase, count, deadline, byte_limit, nodes, depth, profile_limit = values
    result = _read_scan_profile_for_run(
        repo_root, command_index=index, inherited_run_id=original.get(RUN_ID_ENV),
        inherited_evidence_root=Path(original[EVIDENCE_ROOT_ENV]), explicit_basetemp=explicit_basetemp,
        read_limits=_ScanRunReadLimits(byte_limit, nodes, depth, profile_limit), deadline_ns=deadline,
        expected_phase=phase, expected_command_count=count, reader_required=reader_required,
        include_wire_binding=include_wire_binding)
    if str(result[0].process_root) != original.get(PROCESS_ROOT_ENV):
        raise ValueError("forwarded scan process root differs")
    _scan_deadline(min(deadline, (result[2] if reader_required else result[1]).deadline_ns))
    return result


class _ScanReservationLedger:
    def __init__(self, profile, *, reader_only=False):
        if type(profile) is not _Rp5aScanProfile:
            raise TypeError("original scan profile required")
        if type(reader_only) is not bool:
            raise TypeError("reader ledger role must be an exact Boolean")
        self._reader_only = reader_only
        self.profile = profile
        self.process_id = os.getpid()
        self.thread_id = threading.get_ident()
        self.state = "READY"
        self.spent_output = 0
        self.spent_readback = 0
        self.invocations = 0
        self.active = None
        self.last_ns = _scan_deadline(profile.deadline_ns)

    def check(self):
        if (os.getpid(), threading.get_ident()) != (self.process_id, self.thread_id):
            raise ValueError("foreign scan ledger owner")
        now = _scan_deadline(self.profile.deadline_ns)
        if now < self.last_ns:
            raise ValueError("scan monotonic clock regressed")
        self.last_ns = now
        if self.state in {"HELD", "CLOSED"}:
            raise ValueError("scan ledger is not reusable")
        return now

    def hold(self):
        if (os.getpid(), threading.get_ident()) != (self.process_id, self.thread_id):
            raise ValueError("foreign owner cannot change scan ledger")
        self.state = "HELD"

    def reserve(self, stdout_bound, pattern_bytes):
        self.check()
        if (self.state != "READY" or self.active is not None
                or self.invocations >= self.profile.max_invocations):
            raise ValueError("scan reservation unavailable")
        if any(type(value) is not int or value < 0 for value in (stdout_bound, pattern_bytes)):
            raise ValueError("invalid scan reservation operands")
        diagnostic = self.profile.stderr_bytes_per_call
        allowance = min(self.profile.output_bytes - self.spent_output - diagnostic,
                        self.profile.scratch_bytes - pattern_bytes - diagnostic,
                        self.profile.readback_bytes - self.spent_readback)
        if allowance < 0 or (stdout_bound > 0 and allowance == 0):
            raise ValueError("original cumulative scan allowance exhausted")
        reservation = (min(stdout_bound, allowance), diagnostic, pattern_bytes)
        self.active = reservation
        self.state = "INFLIGHT"
        self.invocations += 1
        return reservation

    def settle(self, reservation, *, stdout_bytes, stderr_bytes, readback_bytes):
        self.check()
        if self.state != "INFLIGHT" or self.active is not reservation:
            raise ValueError("original scan reservation required")
        if (any(type(v) is not int or v < 0 for v in (stdout_bytes, stderr_bytes, readback_bytes))
                or stdout_bytes > reservation[0] or stderr_bytes > reservation[1]
                or readback_bytes != stdout_bytes):
            raise ValueError("scan actual byte charges differ")
        self.spent_output += stdout_bytes + stderr_bytes
        self.spent_readback += readback_bytes
        self.active = None
        self.state = "READY"


def _scan_candidate_fence(check_candidate):
    if not callable(check_candidate) or check_candidate() is not None:
        raise ValueError("original scan candidate fence must return None or raise")


class _ScanScratch:
    """One exact disposable directory, original writers and retained duplicates."""
    def __init__(self, root, *, pattern, stdout_limit, stderr_limit, deadline_ns):
        self.root = Path(root)
        self.pattern = pattern
        self.stdout_limit = stdout_limit
        self.stderr_limit = stderr_limit
        self.deadline_ns = deadline_ns
        self.files = {}
        self.transferred = False
        self.capture_complete = False
        self.read_started = False
        self.read_complete = False
        self.readback_bytes = 0
        self.pattern_path = None
        self.directory_identity = None

    def check(self):
        _scan_deadline(self.deadline_ns)
        _local_unlinked_path(self.root)
        value = self.root.lstat()
        identity = (value.st_dev, value.st_ino, value.st_mode)
        if self.directory_identity is not None and identity != self.directory_identity:
            raise ValueError("original scan scratch directory changed")
        return identity

    def _allocate(self, role):
        self.check()
        fd, raw_path = tempfile.mkstemp(prefix="scan-" + role + "-", dir=self.root)
        path = Path(raw_path)
        entry = {"path": path, "writer": None, "reader": None,
                 "writer_close_attempted": False, "reader_close_attempted": False}
        self.files[role] = entry
        duplicate = None
        try:
            os.set_inheritable(fd, False)
            duplicate = os.dup(fd)
            os.set_inheritable(duplicate, False)
            value = os.fstat(fd)
            if _scan_file_identity(value) != _scan_file_identity(path.lstat()):
                raise ValueError("allocated scan path differs from descriptor")
            entry["identity"] = value.st_dev, value.st_ino
            entry["writer"] = os.fdopen(fd, "wb", buffering=0)
            fd = None
            entry["reader"] = os.fdopen(duplicate, "rb", buffering=0)
            duplicate = None
        except BaseException as body:
            errors = [body]
            for remaining in (fd, duplicate):
                if remaining is not None:
                    try:
                        os.close(remaining)
                    except BaseException as cleanup:
                        errors.append(cleanup)
            _scan_raise_errors(errors)
        return entry

    def __enter__(self):
        try:
            self.directory_identity = self.check()
            if any(self.root.iterdir()):
                raise ValueError("scan scratch directory must initially be empty")
            if self.pattern is not None:
                if type(self.pattern) is not bytes:
                    raise TypeError("scan pattern must be original bytes")
                entry = self._allocate("pattern")
                writer = entry["writer"]
                offset = 0
                while offset < len(self.pattern):
                    self.check()
                    count = writer.write(memoryview(self.pattern)[offset:])
                    if type(count) is not int or not 0 < count <= len(self.pattern) - offset:
                        raise OSError("invalid pattern write progress")
                    offset += count
                writer.flush()
                os.fsync(writer.fileno())
                entry["writer_close_attempted"] = True
                writer.close()
                reader = entry["reader"]
                reader.seek(0)
                readback = bytearray()
                while True:
                    chunk = reader.read(min(DEFAULT_SCAN_CHUNK_BYTES, len(self.pattern) - len(readback) + 1))
                    if type(chunk) is not bytes:
                        raise ValueError("invalid pattern readback")
                    if not chunk:
                        break
                    if len(readback) + len(chunk) > len(self.pattern):
                        raise ValueError("pattern readback overflow")
                    readback.extend(chunk)
                    self.check()
                if readback != self.pattern:
                    raise ValueError("pattern exact readback mismatch")
                self._retain_version(entry)
                self.pattern_path = entry["path"]
            self._allocate("stdout")
            self._allocate("stderr")
            self.check()
            return self
        except BaseException as body:
            self._cleanup(body)

    def _retain_version(self, entry):
        descriptor = os.fstat(entry["reader"].fileno())
        path_stat = entry["path"].lstat()
        if (_scan_file_identity(descriptor) != _scan_file_identity(path_stat)
                or (descriptor.st_dev, descriptor.st_ino) != entry["identity"]):
            raise ValueError("scan original descriptor/path identity changed")
        entry["descriptor_version"] = _scan_same_api_version(descriptor)
        entry["path_version"] = _scan_same_api_version(path_stat)

    def _verify_version(self, entry):
        if (_scan_same_api_version(os.fstat(entry["reader"].fileno())) != entry["descriptor_version"]
                or _scan_same_api_version(entry["path"].lstat()) != entry["path_version"]):
            raise ValueError("scan file version changed")

    def take_writers(self):
        self.check()
        if self.transferred:
            raise ValueError("scan writers already transferred")
        if "pattern" in self.files:
            self._verify_version(self.files["pattern"])
        self.transferred = True
        # From this point the shared capture owns every close, even on denial.
        for role in ("stdout", "stderr"):
            self.files[role]["writer_close_attempted"] = True
        return self.files["stdout"]["writer"], self.files["stderr"]["writer"]

    def captured(self, result):
        self.check()
        if not self.transferred or self.capture_complete or type(result) is not tuple or len(result) != 3:
            raise ValueError("invalid scan capture handoff")
        completed, stdout, stderr = result
        if type(completed) is not subprocess.CompletedProcess or type(completed.returncode) is not int:
            raise ValueError("actual completed native scan required")
        for role, outcome, limit in (("stdout", stdout, self.stdout_limit), ("stderr", stderr, self.stderr_limit)):
            entry = self.files[role]
            if (outcome.get("evidence_complete") is not True or outcome.get("writer_closed") is not True
                    or not entry["writer"].closed):
                raise ValueError("scan writer closure unproven")
            count = outcome.get("retained_byte_count")
            if type(count) is not int or not 0 <= count <= limit:
                raise ValueError("invalid retained scan count")
            self._retain_version(entry)
            if os.fstat(entry["reader"].fileno()).st_size != count:
                raise ValueError("scan retained count differs from descriptor size")
            entry["count"] = count
        if "pattern" in self.files:
            self._verify_version(self.files["pattern"])
        self.capture_complete = True

    def stdout_chunks(self, *, readback_limit):
        if not self.capture_complete or self.read_started or type(readback_limit) is not int or readback_limit < 0:
            raise ValueError("scan readback is unavailable")
        self.read_started = True
        entry = self.files["stdout"]
        expected = entry["count"]
        if expected > readback_limit:
            raise ValueError("scan stdout readback allowance exceeded")
        self._verify_version(entry)
        reader = entry["reader"]
        reader.seek(0)
        while True:
            self.check()
            remaining = expected - self.readback_bytes
            count = min(DEFAULT_SCAN_CHUNK_BYTES, remaining + 1)
            chunk = reader.read(count)
            if type(chunk) is not bytes or len(chunk) > count:
                raise ValueError("invalid scan stdout read progress")
            if not chunk:
                break
            if len(chunk) > remaining:
                raise ValueError("scan stdout grew during readback")
            self.readback_bytes += len(chunk)
            yield chunk
        if self.readback_bytes != expected:
            raise ValueError("scan stdout truncated during readback")
        self._verify_version(entry)
        self.check()
        self.read_complete = True

    def _cleanup(self, body=None):
        errors = [] if body is None else [body]
        safe = False
        try:
            self.check()
            if set(self.root.iterdir()) != {entry["path"] for entry in self.files.values()}:
                raise ValueError("scan scratch complete entry set changed")
            # Uncertain capture/partial allocation is held; no guessed cleanup.
            if self.capture_complete:
                for entry in self.files.values():
                    self._verify_version(entry)
                safe = True
            elif body is None:
                raise ValueError("scan incomplete capture retains scratch evidence")
        except BaseException as exc:
            errors.append(exc)
        for entry in self.files.values():
            for role in ("writer", "reader"):
                stream = entry[role]
                attempted = role + "_close_attempted"
                if stream is not None and not entry[attempted]:
                    entry[attempted] = True
                    try:
                        stream.close()
                    except BaseException as exc:
                        errors.append(exc)
                        safe = False
        if safe:
            try:
                for entry in self.files.values():
                    if _scan_same_api_version(entry["path"].lstat()) != entry["path_version"]:
                        raise ValueError("scan path changed before exact unlink")
                    entry["path"].unlink()
                self.check()
                if any(self.root.iterdir()):
                    raise ValueError("scan scratch not empty after exact cleanup")
            except BaseException as exc:
                errors.append(exc)
        _scan_raise_errors(errors)

    def __exit__(self, exc_type, exc, traceback):
        self._cleanup(exc)
        return False


def _execute_scan_with_scratch(
    ledger, *, stdout_bound, pattern, command, parser, check_candidate,
    deadline_ns, allow_no_match,
):
    if type(ledger) is not _ScanReservationLedger:
        raise TypeError("original scan ledger required")
    ledger.check()
    deadline = min(deadline_ns, ledger.profile.deadline_ns)
    _scan_candidate_fence(check_candidate)
    reservation = ledger.reserve(stdout_bound, 0 if pattern is None else len(pattern))
    try:
        scratch = _ScanScratch(ledger.profile.scratch_root, pattern=pattern,
                               stdout_limit=reservation[0], stderr_limit=reservation[1], deadline_ns=deadline)
        with scratch:
            argv = command(scratch.pattern_path)
            _scan_candidate_fence(check_candidate)
            ledger.check()
            _scan_deadline(deadline)
            stdout, stderr = scratch.take_writers()
            captured = _capture_scan_output(
                argv, cwd=Path(ledger.profile.repo_root), environment=dict(ledger.profile.child_environment),
                stdout_stream=stdout, stderr_stream=stderr, stdout_limit=reservation[0],
                stderr_limit=reservation[1], deadline_ns=deadline, allow_no_match=allow_no_match)
            scratch.captured(captured)
            value = parser(scratch.stdout_chunks(readback_limit=reservation[0]), captured[0].returncode)
            if not scratch.read_complete:
                raise ValueError("scan parser did not consume complete original stdout")
            _scan_candidate_fence(check_candidate)
            ledger.check()
            _scan_deadline(deadline)
        _scan_candidate_fence(check_candidate)
        ledger.check()
        _scan_deadline(deadline)
        ledger.settle(reservation, stdout_bytes=captured[1]["retained_byte_count"],
                      stderr_bytes=captured[2]["retained_byte_count"], readback_bytes=scratch.readback_bytes)
        return value
    except BaseException:
        ledger.hold()
        raise


class _ScanPhaseController:
    def __init__(self, profile, ledger, *, check_candidate, max_matched_files, structured_byte_limit):
        if (type(profile) is not _Rp5aScanProfile or type(ledger) is not _ScanReservationLedger
                or ledger.profile is not profile or ledger._reader_only is not False
                or ledger.invocations != 0 or ledger.state != "READY"):
            raise ValueError("scan controller requires original unused profile/ledger")
        if any(type(value) is not int or value <= 0 for value in (max_matched_files, structured_byte_limit)):
            raise ValueError("invalid existing scan limits")
        self.profile = profile
        self.ledger = ledger
        self.check_candidate = check_candidate
        self.max_matched_files = max_matched_files
        self.structured_byte_limit = structured_byte_limit
        self.state = "INVENTORY"
        self.selected = ()
        self.positive_names = []
        self.line_files = ()
        self.skipped_large = ()
        self.names_offset = self.lines_offset = 0
        self.reasons = []

    def check(self):
        self.ledger.check()
        if self.state in {"HELD", "INFLIGHT", "DONE"}:
            raise ValueError("scan phase cannot admit work")
        _scan_candidate_fence(self.check_candidate)

    def hold(self):
        self.ledger.hold()
        self.state = "HELD"

    def reason(self, reason):
        if reason not in self.reasons:
            self.reasons.append(reason)

    def _acquire(self, stage, batch, callback):
        self.check()
        if self.state != stage:
            raise ValueError("scan phase mismatch")
        previous = self.ledger.invocations
        self.state = "INFLIGHT"
        try:
            value = callback(batch)
            if self.ledger.state != "READY" or self.ledger.invocations != previous + 1:
                raise ValueError("scan acquisition did not settle its original reservation")
            self.ledger.check()
            _scan_candidate_fence(self.check_candidate)
            self.state = stage
            return value
        except BaseException:
            self.hold()
            raise

    def inventory(self, callback):
        value = self._acquire("INVENTORY", self.profile.expected_inventory, callback)
        try:
            if type(value) is not tuple or value != self.profile.expected_inventory:
                raise ValueError("scan inventory differs from independent original inventory")
            self.state = "SELECT"
            self.check()
            return value
        except BaseException:
            self.hold()
            raise

    def select(self, all_scannable, selected):
        self.check()
        if self.state != "SELECT" or type(all_scannable) is not tuple or type(selected) is not tuple:
            raise ValueError("original scan selection required")
        try:
            if (len(all_scannable) > len(self.profile.expected_inventory) or len(selected) > len(all_scannable)
                    or len(set(all_scannable)) != len(all_scannable) or len(set(selected)) != len(selected)
                    or not set(all_scannable) <= set(self.profile.expected_inventory) or not set(selected) <= set(all_scannable)):
                raise ValueError("invalid original scan selection")
            self.selected = selected
            if selected != all_scannable:
                self.reason("MAX_FILES_SCANNED")
            self.state = "NAMES" if selected else "NAMES_COMPLETE"
        except BaseException:
            self.hold()
            raise

    def names(self, callback):
        batch = self.selected[self.names_offset:self.names_offset + 50]
        if not batch:
            raise ValueError("empty or repeated scan names acquisition")
        value = self._acquire("NAMES", batch, callback)
        try:
            if (type(value) is not tuple or len(value) > len(batch)
                    or len(set(value)) != len(value) or not set(value) <= set(batch)):
                raise ValueError("scan names do not belong to original batch")
            remaining = self.max_matched_files - len(self.positive_names)
            self.positive_names.extend(value[:remaining])
            self.names_offset += len(batch)
            if len(self.positive_names) >= self.max_matched_files:
                self.reason("MAX_MATCHED_FILES")
                self.state = "NAMES_COMPLETE"
            elif self.names_offset == len(self.selected):
                self.state = "NAMES_COMPLETE"
            return value
        except BaseException:
            self.hold()
            raise

    def seal_names(self):
        self.check()
        if self.state != "NAMES_COMPLETE":
            raise ValueError("scan names phase is unfinished")
        try:
            sizes = dict(self.profile.file_sizes)
            names = tuple(sorted(self.positive_names, key=lambda path: (path.casefold(), path)))
            if any(path not in sizes for path in names):
                raise ValueError("missing original scan size observation")
            self.skipped_large = tuple(path for path in names if sizes[path] > self.structured_byte_limit)
            self.line_files = tuple(path for path in names if sizes[path] <= self.structured_byte_limit)
            if self.skipped_large:
                self.reason("PASS_B_LARGE_FILE_LINE_SCAN_SKIPPED")
            self.state = "LINES" if self.line_files else "COMPLETE"
            return self.line_files
        except BaseException:
            self.hold()
            raise

    def lines(self, callback):
        batch = self.line_files[self.lines_offset:self.lines_offset + 50]
        if not batch:
            raise ValueError("empty or repeated scan line acquisition")
        value = self._acquire("LINES", batch, callback)
        try:
            if type(value) is not tuple:
                raise ValueError("owned scan line tuple required")
            last = {}
            counts = {}
            sizes = dict(self.profile.file_sizes)
            for row in value:
                if (type(row) is not tuple or len(row) != 3 or row[0] not in batch
                        or type(row[1]) is not int or not 0 < row[1] <= sizes[row[0]] + 1
                        or row[1] <= last.get(row[0], 0) or type(row[2]) is not bytes):
                    raise ValueError("invalid original scan line record")
                path = row[0]
                last[path] = row[1]
                counts[path] = counts.get(path, 0) + 1
                if counts[path] > 51:
                    raise ValueError("native scan line overflow exceeds sentinel")
                if counts[path] == 51:
                    self.reason("MAX_LINE_HITS_PER_FILE")
            self.lines_offset += len(batch)
            if self.lines_offset == len(self.line_files):
                self.state = "COMPLETE"
            return value
        except BaseException:
            self.hold()
            raise

    def stop(self, reason):
        self.check()
        if self.state not in {"NAMES", "NAMES_COMPLETE", "LINES", "COMPLETE"} or self.ledger.state != "READY":
            raise ValueError("scan cannot stop an unsettled acquisition")
        self.reason(reason)
        self.state = "COMPLETE"

    def finish(self):
        self.check()
        if self.state != "COMPLETE" or self.ledger.state != "READY":
            raise ValueError("scan did not complete its selected phase")
        result = ("SCAN_BUDGET_EXHAUSTED" if self.reasons else "SCAN_BUDGET_OK", tuple(self.reasons))
        self.check()
        self.state = "DONE"
        self.ledger.state = "CLOSED"
        return result


@dataclass(frozen=True)
class _ScanCandidateSurface:
    path: str
    kind: str
    mode: int
    content: bytes | _ScanDiskSnapshotV3 | _ScanPayloadSpanV3
    children: tuple[str, ...]


@dataclass(frozen=True)
class _ScanLaunchIdentity:
    run_id: str
    phase: str
    command_index: int
    command_count: int
    argv: tuple[str, ...]
    repo_root: str


def _scan_candidate_path(path, *, root_allowed=False):
    if root_allowed and path == ".":
        return path
    if (type(path) is not str or not path or path.startswith("/") or "\0" in path
            or any(part in {"", ".", ".."} for part in path.split("/"))
            or any(0xD800 <= ord(character) <= 0xDFFF for character in path)):
        raise ValueError("invalid original candidate path")
    if os.name == "nt":
        for part in path.split("/"):
            stem = part.split(".")[0].upper()
            if (any(character in '<>:"\\|?*' or ord(character) < 32 for character in part)
                    or part.endswith((" ", ".")) or stem in {"CON", "PRN", "AUX", "NUL"}
                    or re.fullmatch(r"(?:COM|LPT)[1-9\u00b9\u00b2\u00b3]", stem)):
                raise ValueError("unsupported original Windows candidate path")
    return path


def _scan_utf8_charge(text, remaining):
    if type(text) is not str:
        raise ValueError("original candidate text required")
    for character in text:
        code = ord(character)
        if 0xD800 <= code <= 0xDFFF:
            raise ValueError("candidate text is not strict UTF-8")
        remaining -= 1 if code < 128 else 2 if code < 2048 else 3 if code < 65536 else 4
        if remaining < 0:
            raise ValueError("original candidate byte allowance exceeded")
    return remaining


_SCAN_V3_CHUNK = 65_536
_SCAN_V3_MAX = (1 << 63) - 1


def _scan_v3_integer(value, name):
    if type(value) is not int or not 0 <= value <= _SCAN_V3_MAX:
        raise ValueError("invalid streamed candidate integer: " + name)
    return value


@dataclass(frozen=True)
class _ScanDiskSnapshotV3:
    path: str
    snapshot_path: Path
    snapshot_version: tuple
    source_identity: tuple
    mode: int
    length: int

    def __post_init__(self):
        _scan_candidate_path(self.path)
        if (type(self.snapshot_path) is not type(Path()) or not self.snapshot_path.is_absolute()
                or ".." in self.snapshot_path.parts):
            raise ValueError("original absolute disk snapshot path required")
        if type(self.mode) is not int or not 0 <= self.mode <= 0o7777:
            raise ValueError("original disk snapshot mode required")
        _scan_v3_integer(self.length, "snapshot length")
        for value, length in ((self.snapshot_version, 6), (self.source_identity, 4)):
            if type(value) is not tuple or len(value) != length or any(type(v) is not int or v < 0 for v in value):
                raise ValueError("original same-API snapshot/source observation required")
        if (self.snapshot_version[2] != self.length or self.source_identity[2] != self.length
                or self.snapshot_version[:2] == self.source_identity[:2]):
            raise ValueError("snapshot extent or independent physical identity differs")


def _scan_snapshot_root_v3(root):
    if type(root) is not type(Path()) or not root.is_absolute() or ".." in root.parts:
        raise ValueError("original absolute snapshot root required")
    _local_unlinked_path(root)
    if not root.is_dir():
        raise ValueError("original snapshot directory unavailable")
    return root


def _scan_snapshot_path_v3(carrier, root):
    if type(carrier) is not _ScanDiskSnapshotV3:
        raise TypeError("original disk snapshot carrier required")
    _scan_snapshot_root_v3(root)
    path = carrier.snapshot_path
    if path == root or not path.is_relative_to(root):
        raise ValueError("snapshot escaped its original external area")
    _local_unlinked_path(path.parent)
    before = path.lstat()
    if (_scan_file_identity(before) != carrier.snapshot_version[:4]
            or (before.st_dev, before.st_ino) == carrier.source_identity[:2]):
        raise ValueError("snapshot path identity/extent changed or aliases source")
    return before


@contextmanager
def _scan_snapshot_descriptor_v3(carrier, root, check):
    before = _scan_snapshot_path_v3(carrier, root)
    descriptor = None
    errors = []
    try:
        check()
        descriptor = _open_regular_worktree_descriptor(carrier.snapshot_path, nonblocking=True)
        os.set_inheritable(descriptor, False)
        if _scan_same_api_version(os.fstat(descriptor)) != carrier.snapshot_version:
            raise ValueError("snapshot descriptor differs from original retained version")
        yield descriptor
        if _scan_same_api_version(os.fstat(descriptor)) != carrier.snapshot_version:
            raise ValueError("snapshot changed during bounded acquisition")
    except BaseException as error:
        errors.append(error)
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except BaseException as error:
                errors.append(error)
        try:
            after = _scan_snapshot_path_v3(carrier, root)
            if _scan_same_api_version(after) != _scan_same_api_version(before):
                raise ValueError("snapshot pathname changed during/after close")
            check()
        except BaseException as error:
            errors.append(error)
    _scan_raise_errors(errors)


def _scan_readonly_duplicate_v3(descriptor):
    if os.name != "nt":
        import fcntl
        if fcntl.fcntl(descriptor, fcntl.F_GETFL) & os.O_ACCMODE != os.O_RDONLY:
            raise ValueError("streamed launch descriptor must be read-only")
        return os.dup(descriptor)
    # Duplicate the same file object/cursor with read rights only; neither
    # close the borrowed handle nor reopen a payload-selected pathname.
    import _winapi
    import msvcrt
    process = _winapi.GetCurrentProcess()
    handle = _winapi.DuplicateHandle(process, msvcrt.get_osfhandle(descriptor),
                                    process, 0x120089, False, 0)
    try:
        return msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
    except BaseException as body:
        errors = [body]
        try:
            _winapi.CloseHandle(handle)
        except BaseException as error:
            errors.append(error)
        _scan_raise_errors(errors)


class _ScanPayloadLeaseV3:
    __slots__ = ("_fd", "_raw_data_start", "_payload_bytes", "_extent", "_version",
                 "_process_id", "_thread_id", "_deadline_ns", "_last_ns", "_remaining",
                 "_initial_consumption_complete", "_closed", "_held", "_close_attempted")

    def __init__(self, descriptor, *, raw_data_start, payload_bytes, extent,
                 descriptor_version, deadline_ns, read_allowance):
        for value, name in ((raw_data_start, "raw start"), (payload_bytes, "payload"),
                            (extent, "extent")):
            _scan_v3_integer(value, name)
        if (type(descriptor) is not int or descriptor < 0 or raw_data_start + payload_bytes != extent
                or type(read_allowance) is not int or read_allowance <= 0):
            raise ValueError("invalid original payload lease")
        self._fd = descriptor
        self._raw_data_start = raw_data_start
        self._payload_bytes = payload_bytes
        self._extent = extent
        self._version = descriptor_version
        self._process_id = os.getpid()
        self._thread_id = threading.get_ident()
        self._deadline_ns = deadline_ns
        self._last_ns = _scan_deadline(deadline_ns)
        self._remaining = read_allowance
        self._initial_consumption_complete = self._closed = self._held = self._close_attempted = False
        self._check()

    @property
    def raw_data_start(self):
        return self._raw_data_start

    @property
    def payload_bytes(self):
        return self._payload_bytes

    @property
    def extent(self):
        return self._extent

    @property
    def descriptor_version(self):
        return self._version

    @property
    def initial_consumption_complete(self):
        return self._initial_consumption_complete

    @property
    def closed(self):
        return self._closed

    @property
    def held(self):
        return self._held

    @property
    def remaining(self):
        return self._remaining

    def _check(self, *, releasing=False):
        if (os.getpid(), threading.get_ident()) != (self._process_id, self._thread_id):
            raise ValueError("foreign payload lease owner")
        if self._closed or (self._held and not releasing):
            raise ValueError("payload lease is closed or held")
        now = _scan_deadline(self._deadline_ns)
        if now < self._last_ns:
            raise ValueError("payload lease clock regressed")
        self._last_ns = now
        if (_scan_same_api_version(os.fstat(self._fd)) != self._version
                or os.fstat(self._fd).st_size != self._extent or os.get_inheritable(self._fd)):
            raise ValueError("original payload descriptor changed")

    def _hold(self):
        self._held = True

    def _read(self, span, position, request, *, charge=None):
        try:
            self._check()
            if type(span) is not _ScanPayloadSpanV3 or span.lease is not self:
                raise ValueError("foreign original payload span")
            _scan_v3_integer(position, "span position")
            if (position > span.length or type(request) is not int
                    or not 0 < request <= _SCAN_V3_CHUNK):
                raise ValueError("invalid bounded span request")
            count = min(request, span.length - position)
            if not count:
                return b""
            if count > self._remaining:
                raise ValueError("payload lease cumulative read allowance exhausted")
            os.lseek(self._fd, self._raw_data_start + span.offset + position, os.SEEK_SET)
            chunk = os.read(self._fd, count)
            if type(chunk) is bytes:
                self._remaining -= len(chunk)
                if charge is not None:
                    charge(len(chunk))
            if type(chunk) is not bytes or not chunk or len(chunk) > count or self._remaining < 0:
                raise ValueError("invalid payload span read progress")
            self._check()
            return chunk
        except BaseException:
            self._hold()
            raise

    def _comparison_complete(self, *, full_initial=False):
        self._check()
        if full_initial or self._initial_consumption_complete:
            os.lseek(self._fd, self._extent, os.SEEK_SET)
            suffix = os.read(self._fd, 1)
            if type(suffix) is bytes:
                self._remaining -= len(suffix)
            if type(suffix) is not bytes or suffix or self._remaining < 0:
                self._hold()
                raise ValueError("payload physical suffix or allowance mismatch")
            self._check()
            if full_initial:
                # Only the original fence grants this after every admitted row,
                # physical EOF and descriptor-version check has succeeded.
                self._initial_consumption_complete = True

    def close(self):
        if self._close_attempted:
            raise ValueError("payload lease close already attempted")
        if (os.getpid(), threading.get_ident()) != (self._process_id, self._thread_id):
            raise ValueError("foreign payload lease release")
        errors = []
        try:
            self._check(releasing=True)
        except BaseException as error:
            errors.append(error)
        self._close_attempted = True
        try:
            os.close(self._fd)
            self._closed = True
        except BaseException as error:
            errors.append(error)
        if errors or not self._initial_consumption_complete:
            self._hold()
        _scan_raise_errors(errors)


@dataclass(frozen=True)
class _ScanPayloadSpanV3:
    lease: _ScanPayloadLeaseV3
    offset: int
    length: int

    def __post_init__(self):
        if type(self.lease) is not _ScanPayloadLeaseV3:
            raise TypeError("original process-local payload lease required")
        _scan_v3_integer(self.offset, "span offset")
        _scan_v3_integer(self.length, "span length")
        if self.length > _SCAN_V3_MAX - self.offset or self.offset + self.length > self.lease.payload_bytes:
            raise ValueError("payload span exceeds original extent")


def _scan_v3_native_read(descriptor, request, charge, check):
    if type(request) is not int or not 0 < request <= _SCAN_V3_CHUNK:
        raise ValueError("invalid streamed binary request")
    check()
    chunk = os.read(descriptor, request)
    if type(chunk) is bytes:
        charge(len(chunk))
    if type(chunk) is not bytes or len(chunk) > request:
        raise ValueError("invalid streamed binary progress")
    check()
    return chunk

def _scan_candidate_rows(rows, *, limits, candidate_read_bytes, wire_version=1,
                         surface_role="legacy", snapshot_root=None, payload_lease=None):
    if type(wire_version) is not int or wire_version not in (1, 2, 3):
        raise ValueError("unsupported original candidate row version")
    if wire_version != 3:
        if surface_role != "legacy" or snapshot_root is not None or payload_lease is not None:
            raise ValueError("legacy rows cannot bind disk snapshots or payload leases")
    elif surface_role == "sender":
        if payload_lease is not None:
            raise ValueError("sender rows cannot acquire a child lease")
        _scan_snapshot_root_v3(snapshot_root)
    elif surface_role == "receiver":
        if snapshot_root is not None or type(payload_lease) is not _ScanPayloadLeaseV3:
            raise ValueError("receiver rows require their one original lease")
    else:
        raise ValueError("streamed rows require an explicit sender or receiver role")
    snapshot_identities = set()
    cursor = 0
    if (type(limits) is not _ScanRunReadLimits or type(rows) is not tuple
            or type(candidate_read_bytes) is not int or candidate_read_bytes < 0
            or len(rows) > limits.node_limit):
        raise ValueError("invalid original candidate row envelope")
    seen = {}
    aliases = set()
    nodes = 1
    remaining = candidate_read_bytes
    for row in rows:
        if type(row) is not _ScanCandidateSurface:
            raise TypeError("original native candidate surface required")
        width = (8 if row.kind == "FILE" else 6) if wire_version == 3 else 7
        nodes += width + len(row.children) if type(row.children) is tuple else limits.node_limit + 1
        if nodes > limits.node_limit:
            raise ValueError("candidate member node allowance exceeded")
        _scan_candidate_path(row.path, root_allowed=row.kind == "DIRECTORY")
        if row.path in seen or (os.name == "nt" and row.path.casefold() in aliases):
            raise ValueError("duplicate candidate surface")
        if (row.kind not in {"FILE", "DIRECTORY", "ABSENT"} or type(row.mode) is not int
                or not 0 <= row.mode <= 0o7777 or type(row.children) is not tuple
                or ((wire_version != 3 or row.kind != "FILE") and type(row.content) is not bytes)):
            raise ValueError("unsupported candidate kind/mode/content")
        if row.kind == "FILE":
            if row.children:
                raise ValueError("file candidate cannot contain directory members")
            if wire_version == 3:
                if surface_role == "sender":
                    if (type(row.content) is not _ScanDiskSnapshotV3 or row.content.path != row.path
                            or row.content.mode != row.mode):
                        raise ValueError("sender requires the exact original disk carrier")
                    _scan_snapshot_path_v3(row.content, snapshot_root)
                    physical = row.content.snapshot_version[:2]
                    if physical in snapshot_identities:
                        raise ValueError("distinct sender rows alias one snapshot file")
                    snapshot_identities.add(physical)
                elif (type(row.content) is not _ScanPayloadSpanV3 or row.content.lease is not payload_lease
                        or row.content.offset != cursor):
                    raise ValueError("receiver requires contiguous spans from its exact lease")
                length = row.content.length
                if length > _SCAN_V3_MAX - cursor:
                    raise ValueError("streamed candidate extent overflow")
                cursor += length
                remaining -= length
            else:
                remaining -= len(row.content)
        elif row.kind == "ABSENT":
            if row.mode or row.content or row.children:
                raise ValueError("absence candidate must have empty structural fields")
        else:
            if row.content or row.children != tuple(sorted(row.children)) or len(set(row.children)) != len(row.children):
                raise ValueError("directory candidate requires complete sorted unique membership")
            child_aliases = set()
            for name in row.children:
                _scan_candidate_path(name)
                if "/" in name or (os.name == "nt" and name.casefold() in child_aliases):
                    raise ValueError("invalid candidate immediate member")
                remaining = _scan_utf8_charge(name, remaining)
                child_aliases.add(name.casefold())
        if remaining < 0:
            raise ValueError("candidate byte allowance exceeded")
        seen[row.path] = row
        aliases.add(row.path.casefold())
    for path in seen:
        pieces = path.split("/")
        for index in range(1, len(pieces)):
            parent = seen.get("/".join(pieces[:index]))
            if parent is not None and parent.kind != "DIRECTORY":
                raise ValueError("declared candidate file/absence has descendants")
    if wire_version == 3 and surface_role == "receiver" and cursor != payload_lease.payload_bytes:
        raise ValueError("receiver rows do not cover their exact original payload")
    return rows


class _ScanCandidateFence:
    def __init__(self, repo_root, rows, *, limits, candidate_read_bytes, deadline_ns,
                 wire_version=1, surface_role="legacy", snapshot_root=None, payload_lease=None):
        self.root = Path(repo_root)
        if not self.root.is_absolute() or ".." in self.root.parts:
            raise ValueError("original absolute candidate root required")
        self.limits = limits
        self.wire_version = wire_version
        self.surface_role = surface_role
        self.snapshot_root = snapshot_root
        self.payload_lease = payload_lease
        if wire_version == 3 and surface_role == "sender":
            _scan_snapshot_root_v3(snapshot_root)
            if snapshot_root.is_relative_to(self.root) or self.root.is_relative_to(snapshot_root):
                raise ValueError("snapshot area must be independent and external to the repository")
        self.rows = _scan_candidate_rows(rows, limits=limits, candidate_read_bytes=candidate_read_bytes,
            wire_version=wire_version, surface_role=surface_role, snapshot_root=snapshot_root,
            payload_lease=payload_lease)
        self.remaining = candidate_read_bytes
        self.deadline_ns = deadline_ns
        self.process_id = os.getpid()
        self.thread_id = threading.get_ident()
        self.held = False
        self.last_ns = _scan_deadline(deadline_ns)
        self.identities = {}
        _local_unlinked_path(self.root)
        if wire_version == 3:
            observed = self.root.lstat()
            self._root_identity_v3 = observed.st_dev, observed.st_ino, observed.st_mode
            self._parent_identities_v3 = {}
            self._all_rows_v3 = self.rows

    def _clock(self):
        if self.wire_version == 3 and (os.getpid(), threading.get_ident()) != (self.process_id, self.thread_id):
            raise ValueError("foreign streamed candidate owner")
        now = _scan_deadline(self.deadline_ns)
        if now < self.last_ns:
            raise ValueError("candidate monotonic clock regressed")
        self.last_ns = now

    def __call__(self):
        if self.wire_version == 3:
            self._check_v3()
            return None
        if (os.getpid(), threading.get_ident()) != (self.process_id, self.thread_id):
            raise ValueError("foreign candidate fence owner")
        if self.held:
            raise ValueError("candidate fence is held")
        try:
            self._clock()
            _local_unlinked_path(self.root)
            for row in self.rows:
                path = self.root if row.path == "." else self.root.joinpath(*row.path.split("/"))
                _local_unlinked_path(path.parent)
                if not path.parent.is_dir():
                    raise ValueError("candidate ordinary parent is missing")
                try:
                    before = path.lstat()
                except FileNotFoundError:
                    if row.kind != "ABSENT":
                        raise
                    continue
                if row.kind == "ABSENT":
                    raise ValueError("original absent candidate now exists")
                if stat.S_ISLNK(before.st_mode) or _stat_is_reparse_point(before):
                    raise ValueError("candidate link/reparse substitution")
                identity = before.st_dev, before.st_ino, before.st_mode
                if stat.S_IMODE(before.st_mode) != row.mode:
                    raise ValueError("candidate mode changed")
                if row.path in self.identities and self.identities[row.path] != identity:
                    raise ValueError("candidate identity changed")
                self.identities.setdefault(row.path, identity)
                if row.kind == "DIRECTORY":
                    if not stat.S_ISDIR(before.st_mode):
                        raise ValueError("candidate directory changed kind")
                    names = []
                    with os.scandir(path) as entries:
                        for entry in entries:
                            if len(names) >= len(row.children):
                                raise ValueError("candidate directory gained a member")
                            self.remaining = _scan_utf8_charge(entry.name, self.remaining)
                            names.append(entry.name)
                    after = path.lstat()
                    if (tuple(sorted(names)) != row.children
                            or (before.st_dev, before.st_ino, before.st_mode, before.st_mtime_ns, before.st_ctime_ns)
                            != (after.st_dev, after.st_ino, after.st_mode, after.st_mtime_ns, after.st_ctime_ns)):
                        raise ValueError("candidate directory membership changed")
                else:
                    _scan_file_identity(before)
                    if before.st_size != len(row.content) or before.st_size > self.remaining:
                        raise ValueError("candidate file size or read allowance differs")
                    descriptor = None
                    errors = []
                    try:
                        descriptor = _open_regular_worktree_descriptor(path, nonblocking=True)
                        opened = os.fstat(descriptor)
                        if _scan_file_identity(opened) != _scan_file_identity(before):
                            raise ValueError("candidate selected descriptor differs")
                        offset = 0
                        while True:
                            self._clock()
                            request = min(64 * 1024, len(row.content) - offset + 1)
                            chunk = os.read(descriptor, request)
                            if type(chunk) is not bytes or len(chunk) > request:
                                raise ValueError("invalid candidate native read")
                            if not chunk:
                                break
                            self.remaining -= len(chunk)
                            if self.remaining < 0 or chunk != row.content[offset:offset + len(chunk)]:
                                raise ValueError("candidate bytes/read allowance changed")
                            offset += len(chunk)
                        if (offset != len(row.content) or _scan_same_api_version(os.fstat(descriptor)) != _scan_same_api_version(opened)
                                or _scan_same_api_version(path.lstat()) != _scan_same_api_version(before)):
                            raise ValueError("candidate file changed while observed")
                    except BaseException as exc:
                        errors.append(exc)
                    finally:
                        if descriptor is not None:
                            try:
                                os.close(descriptor)
                            except BaseException as exc:
                                errors.append(exc)
                    _scan_raise_errors(errors)
                    if _scan_same_api_version(path.lstat()) != _scan_same_api_version(before):
                        raise ValueError("candidate file changed after close")
                self._clock()
            self._clock()
        except BaseException:
            self.held = True
            raise
        return None

    def _charge_v3(self, count):
        self.remaining -= count
        if self.remaining < 0:
            raise ValueError("streamed candidate cumulative read allowance exhausted")

    def _file_v3(self, row, path, before, *, source_limit=None):
        expected_length = row.content.length
        if before.st_size != expected_length or 2 * expected_length > self.remaining:
            raise ValueError("streamed candidate size/read allowance differs")
        if self.surface_role == "sender" and _scan_file_identity(before) != row.content.source_identity:
            raise ValueError("current candidate differs from independently captured source identity")
        current = None
        errors = []
        actual_data = bytearray() if source_limit is not None else None
        expected_data = bytearray() if source_limit is not None else None
        try:
            current = _open_regular_worktree_descriptor(path, nonblocking=True)
            opened = os.fstat(current)
            if _scan_file_identity(opened) != _scan_file_identity(before):
                raise ValueError("streamed candidate selected descriptor differs")
            with ExitStack() as stack:
                expected = (stack.enter_context(_scan_snapshot_descriptor_v3(
                    row.content, self.snapshot_root, self._clock)) if self.surface_role == "sender" else None)
                offset = 0
                while offset < expected_length:
                    chunk = _scan_v3_native_read(current, min(_SCAN_V3_CHUNK, expected_length - offset),
                                                 self._charge_v3, self._clock)
                    if not chunk:
                        raise ValueError("current candidate ended before its original extent")
                    if actual_data is not None:
                        if len(actual_data) + len(chunk) > source_limit:
                            raise ValueError("original finite source exceeds selected limit")
                        actual_data.extend(chunk)
                    compared = 0
                    while compared < len(chunk):
                        if expected is None:
                            part = self.payload_lease._read(row.content, offset + compared, len(chunk) - compared,
                                                            charge=self._charge_v3)
                        else:
                            part = _scan_v3_native_read(expected, len(chunk) - compared,
                                                       self._charge_v3, self._clock)
                        if not part or part != chunk[compared:compared + len(part)]:
                            raise ValueError("streamed candidate bytes differ from original baseline")
                        if expected_data is not None:
                            expected_data.extend(part)
                        compared += len(part)
                    offset += len(chunk)
                suffix = _scan_v3_native_read(current, 1, self._charge_v3, self._clock)
                if suffix:
                    raise ValueError("current candidate has an unexpected physical suffix")
                if expected is not None:
                    if _scan_v3_native_read(expected, 1, self._charge_v3, self._clock):
                        raise ValueError("snapshot has an unexpected physical suffix")
                elif self.payload_lease._read(row.content, expected_length, 1) != b"":
                    raise ValueError("payload span logical EOF differs")
                if (_scan_same_api_version(os.fstat(current)) != _scan_same_api_version(opened)
                        or _scan_same_api_version(path.lstat()) != _scan_same_api_version(before)):
                    raise ValueError("streamed current source changed during comparison")
        except BaseException as error:
            errors.append(error)
        finally:
            if current is not None:
                try:
                    os.close(current)
                except BaseException as error:
                    errors.append(error)
            try:
                if _scan_same_api_version(path.lstat()) != _scan_same_api_version(before):
                    raise ValueError("streamed current source changed after close")
            except BaseException as error:
                errors.append(error)
        _scan_raise_errors(errors)
        if actual_data is not None:
            return bytes(actual_data), bytes(expected_data)
        return None

    def _check_v3(self, *, source_relative=None, source_limit=None):
        if (os.getpid(), threading.get_ident()) != (self.process_id, self.thread_id) or self.held:
            raise ValueError("foreign or held streamed candidate fence")
        acquired_source = None
        try:
            self._clock()
            _local_unlinked_path(self.root)
            root_stat = self.root.lstat()
            if (root_stat.st_dev, root_stat.st_ino, root_stat.st_mode) != self._root_identity_v3:
                raise ValueError("streamed candidate root identity changed")
            for row in self.rows:
                self._clock()
                path = self.root if row.path == "." else self.root.joinpath(*row.path.split("/"))
                _local_unlinked_path(path.parent)
                parent = path.parent.lstat()
                if not stat.S_ISDIR(parent.st_mode):
                    raise ValueError("candidate ordinary parent is missing")
                parent_key = str(path.parent)
                parent_identity = parent.st_dev, parent.st_ino, parent.st_mode
                if self._parent_identities_v3.setdefault(parent_key, parent_identity) != parent_identity:
                    raise ValueError("candidate ordinary parent identity changed")
                try:
                    before = path.lstat()
                except FileNotFoundError:
                    if row.kind != "ABSENT":
                        raise
                    continue
                if row.kind == "ABSENT":
                    raise ValueError("original absent candidate now exists")
                if stat.S_ISLNK(before.st_mode) or _stat_is_reparse_point(before):
                    raise ValueError("candidate link/reparse substitution")
                identity = before.st_dev, before.st_ino, before.st_mode
                if stat.S_IMODE(before.st_mode) != row.mode:
                    raise ValueError("candidate mode changed")
                if self.identities.setdefault(row.path, identity) != identity:
                    raise ValueError("candidate identity changed")
                if row.kind == "DIRECTORY":
                    if not stat.S_ISDIR(before.st_mode):
                        raise ValueError("candidate directory changed kind")
                    names = []
                    with os.scandir(path) as entries:
                        for entry in entries:
                            self._clock()
                            if len(names) >= len(row.children):
                                raise ValueError("candidate directory gained a member")
                            self.remaining = _scan_utf8_charge(entry.name, self.remaining)
                            names.append(entry.name)
                    after = path.lstat()
                    if (tuple(sorted(names)) != row.children
                            or (before.st_dev, before.st_ino, before.st_mode, before.st_mtime_ns, before.st_ctime_ns)
                            != (after.st_dev, after.st_ino, after.st_mode, after.st_mtime_ns, after.st_ctime_ns)):
                        raise ValueError("candidate directory membership changed")
                else:
                    _scan_file_identity(before)
                    value = self._file_v3(row, path, before,
                                          source_limit=source_limit if row.path == source_relative else None)
                    if row.path == source_relative:
                        acquired_source = value
                self._clock()
            if self.payload_lease is not None:
                self.payload_lease._comparison_complete(full_initial=self.rows is self._all_rows_v3)
            self._clock()
        except BaseException:
            self.held = True
            if self.payload_lease is not None:
                self.payload_lease._hold()
            raise
        return acquired_source

    def close_payload_lease(self):
        if self.wire_version != 3 or self.payload_lease is None:
            return None
        try:
            self.payload_lease.close()
        except BaseException:
            self.held = True
            raise
        return None

    def observe_surfaces(self, paths):
        if type(paths) is not tuple or len(paths) != len(set(paths)):
            raise ValueError("original finite surface selection required")
        originals = {row.path: row for row in self.rows}
        if not set(paths) <= set(originals):
            raise ValueError("surface selection escaped original candidate")
        all_rows = self.rows
        try:
            self.rows = tuple(originals[path] for path in paths)
            self()
        finally:
            self.rows = all_rows
        return MappingProxyType({path: originals[path] for path in paths})

    def read_original_source(self, relative, limit):
        if relative not in ("tools/run_validation_gates.py", "tools/validation_scope_registry.py"):
            raise ValueError("reader source path is fixed by the original owner")
        if self.wire_version == 3:
            if type(limit) is not int or limit <= 0:
                raise ValueError("original positive source byte limit required")
            original_rows = self.rows
            selected = tuple(row for row in original_rows if row.path == relative)
            if len(selected) != 1 or selected[0].kind != "FILE" or selected[0].content.length > limit:
                raise ValueError("original complete source unavailable or oversized")
            try:
                self.rows = selected
                return self._check_v3(source_relative=relative, source_limit=limit)
            finally:
                self.rows = original_rows
        row = self.observe_surfaces((relative,))[relative]
        if row.kind != "FILE" or len(row.content) > limit:
            raise ValueError("original complete source unavailable or oversized")
        path = self.root / relative
        observed = path.lstat()
        data = bytearray()
        try:
            with _regular_worktree_source(path, observed).open() as stream:
                while block := stream.read(min(65536, limit - len(data) + 1)):
                    self._clock()
                    self.remaining -= len(block)
                    if self.remaining < 0 or len(data) + len(block) > limit:
                        raise ValueError("source acquisition allowance exhausted")
                    data.extend(block)
            if bytes(data) != row.content:
                raise ValueError("current source differs from original candidate frame")
        except BaseException:
            self.held = True
            raise
        return bytes(data), row.content


@dataclass(frozen=True)
class _ScanHex:
    value: bytes


def _scan_launch_payload(identity, rows, *, limits, candidate_read_bytes, rp5a_read_basis=None, parent_identity=None,
                         wire_version=None, snapshot_root=None, surface_role=None, payload_lease=None):
    selected_version = (1 if rp5a_read_basis is None else 2) if wire_version is None else wire_version
    if type(selected_version) is not int or selected_version not in (1, 2, 3):
        raise ValueError("unsupported explicitly selected launch version")
    if (selected_version == 1) != (rp5a_read_basis is None):
        raise ValueError("launch version requires its original reader basis")
    if selected_version != 3:
        if snapshot_root is not None or payload_lease is not None or surface_role not in (None, "legacy"):
            raise ValueError("legacy launch cannot use streamed operands")
        selected_role = "legacy"
    else:
        if parent_identity is not None:
            raise ValueError("streamed launch cannot delegate")
        selected_role = "sender" if surface_role is None else surface_role
        _scan_v3_integer(candidate_read_bytes, "candidate allowance")
    if (type(identity) is not _ScanLaunchIdentity or type(identity.run_id) is not str or not identity.run_id
            or type(identity.phase) is not str or not identity.phase
            or type(identity.command_index) is not int or type(identity.command_count) is not int
            or not 1 <= identity.command_index <= identity.command_count
            or type(identity.argv) is not tuple or not identity.argv
            or any(type(arg) is not str or not arg or "\0" in arg for arg in identity.argv)
            or type(identity.repo_root) is not str or not Path(identity.repo_root).is_absolute()):
        raise ValueError("invalid original scan launch identity")
    _scan_candidate_rows(rows, limits=limits, candidate_read_bytes=candidate_read_bytes,
                         wire_version=selected_version, surface_role=selected_role,
                         snapshot_root=snapshot_root, payload_lease=payload_lease)
    if selected_version == 3:
        _scan_v3_integer(identity.command_index, "command index")
        _scan_v3_integer(identity.command_count, "command count")
        cursor = 0
        projected = []
        for row in rows:
            extent = ()
            if row.kind == "FILE":
                extent = (cursor, row.content.length)
                if row.content.length > _SCAN_V3_MAX - cursor:
                    raise ValueError("streamed payload extent overflow")
                cursor += row.content.length
            projected.append((row.path, row.kind, row.mode, extent, row.children))
        candidate_projection = tuple(projected)
    else:
        candidate_projection = tuple((row.path, row.kind, row.mode, _ScanHex(row.content), row.children) for row in rows)
    result = {
        "run_id": identity.run_id, "phase": identity.phase, "command_index": identity.command_index,
        "command_count": identity.command_count, "argv": identity.argv, "repo_root": identity.repo_root,
        "candidate_files": candidate_projection,
        "candidate_read_bytes": candidate_read_bytes,
    }
    if rp5a_read_basis is None:
        if parent_identity is not None:
            raise ValueError("parent identity requires the complete reader extension")
    else:
        basis = _rp5a_basis_projection_v1(rp5a_read_basis, wire=True)
        parent = None
        if parent_identity is not None:
            # Reuse the original identity domain without introducing a second
            # permissive identity codec or a payload-selected delegation chain.
            _scan_launch_payload(parent_identity, (), limits=limits, candidate_read_bytes=1)
            if (identity.run_id != parent_identity.run_id or identity.repo_root != parent_identity.repo_root
                    or identity.phase != "nested-pytest" or identity.command_index != 1 or identity.command_count != 1):
                raise ValueError("RP5A delegation must be the original single pytest hop")
            parent = MappingProxyType({name: getattr(parent_identity, name)
                                       for name in _ScanLaunchIdentity.__dataclass_fields__})
        result.update(wire_version=selected_version, rp5a_read_basis=basis, parent_identity=parent)
        if selected_version == 3:
            result["payload_byte_count"] = cursor
    return MappingProxyType(result)


_SCAN_V3_FIELDS = (
    "run_id", "phase", "command_index", "command_count", "argv", "repo_root",
    "candidate_files", "candidate_read_bytes", "wire_version", "rp5a_read_basis",
    "parent_identity", "payload_byte_count",
)


def _scan_v3_direct_null(payload):
    if (type(payload) is not MappingProxyType or type(payload.get("wire_version")) is not int
            or payload.get("wire_version") != 3 or payload.get("parent_identity", False) is not None):
        return False
    if set(payload) != set(_SCAN_V3_FIELDS):
        raise ValueError("v3 null requires the exact direct streamed control fields")
    basis = payload["rp5a_read_basis"]
    if type(basis) is not MappingProxyType or type(basis.get("historical_runner_bytes")) is not _ScanHex:
        raise ValueError("v3 null requires a complete original reader basis")
    _Rp5aReadBasisV1(**{**dict(basis), "historical_runner_bytes": basis["historical_runner_bytes"].value})
    _scan_v3_integer(payload["payload_byte_count"], "payload bytes")
    return True


def _read_scan_launch_v3(fd, *, limits, deadline_ns, expected_identity,
                         expected_rp5a_read_basis, expected_payload_bytes):
    _scan_v3_integer(expected_payload_bytes, "independent payload bytes")
    before = os.fstat(fd)
    version = _scan_same_api_version(before)
    if os.lseek(fd, 0, os.SEEK_CUR) != 0 or not 4 < before.st_size <= _SCAN_V3_MAX:
        raise ValueError("invalid streamed launch position/extent")
    owned = _scan_readonly_duplicate_v3(fd)
    lease = None
    errors = []
    result = None
    try:
        os.set_inheritable(owned, False)

        def acquire(size):
            raw = bytearray()
            while len(raw) < size:
                _scan_deadline(deadline_ns)
                if _scan_same_api_version(os.fstat(owned)) != version:
                    raise ValueError("streamed launch changed while reading control")
                request = min(_SCAN_V3_CHUNK, size - len(raw))
                part = os.read(owned, request)
                if type(part) is not bytes or not part or len(part) > request:
                    raise ValueError("streamed control ended or made invalid progress")
                raw.extend(part)
            return bytes(raw)

        length = int.from_bytes(acquire(4), "big")
        if (not 0 < length <= min(limits.byte_limit, 0xFFFFFFFF)
                or expected_payload_bytes > _SCAN_V3_MAX - 4 - length
                or before.st_size != 4 + length + expected_payload_bytes):
            raise ValueError("streamed control/payload extent differs from independent allocation")
        raw = acquire(length)
        if any(byte > 127 for byte in raw):
            raise ValueError("streamed control must be canonical ASCII")
        value = _scan_owned_json(raw, limits)
        if type(value) is not MappingProxyType or set(value) != set(_SCAN_V3_FIELDS):
            raise ValueError("invalid closed streamed control fields")
        if (type(value["wire_version"]) is not int or value["wire_version"] != 3
                or value["parent_identity"] is not None):
            raise ValueError("streamed launch cannot change version or delegate")
        if _scan_v3_integer(value["payload_byte_count"], "payload count") != expected_payload_bytes:
            raise ValueError("payload count differs from independent allowance")
        allowance = _scan_v3_integer(value["candidate_read_bytes"], "candidate allowance")
        if allowance <= 0:
            raise ValueError("positive original candidate allowance required")
        basis = _rp5a_basis_from_projection_v1(value["rp5a_read_basis"])
        if basis != expected_rp5a_read_basis:
            raise ValueError("streamed reader basis differs from original parent")
        identity = _ScanLaunchIdentity(*(value[key] for key in _ScanLaunchIdentity.__dataclass_fields__))
        if type(expected_identity) is not _ScanLaunchIdentity or identity != expected_identity:
            raise ValueError("streamed identity differs from original expectation")
        for number in (identity.command_index, identity.command_count):
            _scan_v3_integer(number, "command identity")
        raw_rows = value["candidate_files"]
        if type(raw_rows) is not tuple or len(raw_rows) > limits.node_limit:
            raise ValueError("invalid bounded streamed rows")
        cursor = 0
        for row in raw_rows:
            if type(row) is not tuple or len(row) != 5 or type(row[3]) is not tuple:
                raise ValueError("invalid streamed candidate row shape")
            extent = row[3]
            if row[1] == "FILE":
                if len(extent) != 2:
                    raise ValueError("streamed file requires one exact extent")
                offset = _scan_v3_integer(extent[0], "file offset")
                count = _scan_v3_integer(extent[1], "file length")
                if offset != cursor or count > _SCAN_V3_MAX - cursor:
                    raise ValueError("streamed extents have gaps, overlaps or overflow")
                cursor += count
            elif extent:
                raise ValueError("non-file candidate cannot carry a payload extent")
        if cursor != expected_payload_bytes:
            raise ValueError("streamed rows do not cover exactly the admitted payload")
        lease = _ScanPayloadLeaseV3(owned, raw_data_start=4 + length, payload_bytes=cursor,
            extent=before.st_size, descriptor_version=version, deadline_ns=deadline_ns, read_allowance=allowance)
        rows = tuple(_ScanCandidateSurface(row[0], row[1], row[2],
            _ScanPayloadSpanV3(lease, *row[3]) if row[1] == "FILE" else b"", row[4]) for row in raw_rows)
        canonical = _scan_launch_payload(identity, rows, limits=limits, candidate_read_bytes=allowance,
            rp5a_read_basis=expected_rp5a_read_basis, wire_version=3, surface_role="receiver", payload_lease=lease)
        if _scan_launch_measure(canonical, limits=limits) != length:
            raise ValueError("streamed control measurement differs")
        position = 0
        for part in _scan_launch_parts(canonical):
            if raw[position:position + len(part)] != part:
                raise ValueError("noncanonical streamed control bytes")
            position += len(part)
        if position != length:
            raise ValueError("streamed control coverage differs")
        lease._check()
        result = (identity, rows, allowance, expected_rp5a_read_basis, None, lease)
    except BaseException as error:
        errors.append(error)
    if errors:
        try:
            if lease is not None:
                lease._hold()
                lease.close()
            else:
                os.close(owned)
        except BaseException as error:
            errors.append(error)
        _scan_raise_errors(errors)
    return result


def _scan_v2_direct_null_v1(payload):
    if (type(payload) is not MappingProxyType or type(payload.get("wire_version")) is not int
            or payload.get("wire_version") != 2 or payload.get("parent_identity", False) is not None):
        return False
    if set(payload) != {"run_id", "phase", "command_index", "command_count", "argv", "repo_root",
                        "candidate_files", "candidate_read_bytes", "wire_version", "rp5a_read_basis", "parent_identity"}:
        raise ValueError("null requires the closed direct reader-bearing frame")
    basis = payload["rp5a_read_basis"]
    if type(basis) is not MappingProxyType or type(basis.get("historical_runner_bytes")) is not _ScanHex:
        raise ValueError("null requires complete typed reader basis")
    _Rp5aReadBasisV1(**{**dict(basis), "historical_runner_bytes": basis["historical_runner_bytes"].value})
    return True


def _scan_launch_measure(payload, *, limits):
    size = nodes = 0
    direct_null = _scan_v2_direct_null_v1(payload) or _scan_v3_direct_null(payload)

    def text_size(value):
        count = 2
        for char in value:
            code = ord(char)
            if 0xD800 <= code <= 0xDFFF:
                raise ValueError("launch text is not valid Unicode")
            count += 2 if code in {8, 9, 10, 12, 13, 34, 92} else 6 if code < 32 or 127 <= code <= 65535 else 12 if code > 65535 else 1
            if count > limits.byte_limit:
                raise ValueError("launch scalar exceeds byte allowance")
        return count

    def walk(value, depth, *, direct_parent=False):
        nonlocal size, nodes
        nodes += 1
        if nodes > limits.node_limit:
            raise ValueError("launch node allowance exceeded")
        if value is None and direct_null and direct_parent:
            size += 4
        elif type(value) is str:
            size += text_size(value)
        elif type(value) is int:
            if value.bit_length() > limits.byte_limit * 4:
                raise ValueError("launch integer exceeds byte allowance")
            size += len(str(value))
        elif type(value) is _ScanHex:
            size += 2 + 2 * len(value.value)
        elif type(value) in {tuple, MappingProxyType}:
            if depth > limits.depth_limit:
                raise ValueError("launch container depth exceeded")
            size += 2 + max(0, len(value) - 1)
            if type(value) is tuple:
                for item in value:
                    walk(item, depth + 1)
            else:
                size += len(value)
                for key, item in value.items():
                    if type(key) is not str:
                        raise ValueError("launch key must be exact text")
                    walk(key, depth + 1)
                    walk(item, depth + 1, direct_parent=value is payload and key == "parent_identity")
        else:
            raise TypeError("unsupported launch representation")
        if size > limits.byte_limit or size > 0xFFFFFFFF:
            raise ValueError("launch byte allowance exceeded")

    walk(payload, 1)
    if size <= 0:
        raise ValueError("empty launch payload")
    return size



def _scan_launch_parts(payload, *, _root=True):
    def text(value):
        encoded = json.encoder.encode_basestring_ascii(value).encode("ascii")
        for offset in range(0, len(encoded), 64 * 1024):
            yield encoded[offset:offset + 64 * 1024]

    direct_null = _root and (_scan_v2_direct_null_v1(payload) or _scan_v3_direct_null(payload))
    if type(payload) is str:
        yield from text(payload)
    elif type(payload) is int:
        yield str(payload).encode("ascii")
    elif type(payload) is _ScanHex:
        yield b'"'
        for offset in range(0, len(payload.value), 32 * 1024):
            yield payload.value[offset:offset + 32 * 1024].hex().encode("ascii")
        yield b'"'
    elif type(payload) is tuple:
        yield b"["
        for index, item in enumerate(payload):
            if index:
                yield b","
            yield from _scan_launch_parts(item, _root=False)
        yield b"]"
    elif type(payload) is MappingProxyType:
        yield b"{"
        for index, (key, item) in enumerate(payload.items()):
            if index:
                yield b","
            yield from text(key)
            yield b":"
            if direct_null and key == "parent_identity":
                yield b"null"
            else:
                yield from _scan_launch_parts(item, _root=False)
        yield b"}"
    else:
        raise TypeError("unsupported measured launch value")


def _read_scan_launch_fd(fd, *, limits, deadline_ns, expected_identity, expected_wire_version=1,
                         expected_parent_identity=None, expected_rp5a_read_basis=None, expected_payload_bytes=None):
    if type(fd) is not int or type(limits) is not _ScanRunReadLimits:
        raise TypeError("original launch descriptor and limits required")
    if type(expected_wire_version) is not int or expected_wire_version not in (1, 2, 3):
        raise ValueError("unsupported independently selected launch wire version")
    if expected_wire_version == 1:
        if expected_parent_identity is not None or expected_rp5a_read_basis is not None:
            raise ValueError("legacy launch cannot admit reader/delegation expectations")
    elif type(expected_rp5a_read_basis) is not _Rp5aReadBasisV1:
        raise ValueError("v2 requires independently bound original reader basis")
    if expected_wire_version == 3:
        if expected_parent_identity is not None:
            raise ValueError("streamed launch cannot admit parent delegation")
        return _read_scan_launch_v3(fd, limits=limits, deadline_ns=deadline_ns, expected_identity=expected_identity,
            expected_rp5a_read_basis=expected_rp5a_read_basis, expected_payload_bytes=expected_payload_bytes)
    if expected_payload_bytes is not None:
        raise ValueError("legacy launch cannot admit a streamed payload allowance")
    before = os.fstat(fd)
    _scan_file_identity(before)
    if os.lseek(fd, 0, os.SEEK_CUR) != 0 or not 4 < before.st_size <= limits.byte_limit + 4:
        raise ValueError("invalid launch input position/extent")
    owned = os.dup(fd)
    errors = []
    raw = bytearray()
    try:
        os.set_inheritable(owned, False)
        while True:
            _scan_deadline(deadline_ns)
            count = min(64 * 1024, before.st_size - len(raw) + 1)
            chunk = os.read(owned, count)
            if type(chunk) is not bytes or len(chunk) > count:
                raise ValueError("invalid launch input progress")
            if not chunk:
                break
            if len(raw) + len(chunk) > before.st_size:
                raise ValueError("launch input suffix or growth")
            raw.extend(chunk)
        if len(raw) != before.st_size or _scan_same_api_version(os.fstat(owned)) != _scan_same_api_version(before):
            raise ValueError("launch input truncated or changed")
        length = int.from_bytes(raw[:4], "big")
        if length <= 0 or length > limits.byte_limit or length != len(raw) - 4:
            raise ValueError("launch frame length differs")
        value = _scan_owned_json(bytes(raw[4:]), limits)
    except BaseException as exc:
        errors.append(exc)
    finally:
        try:
            os.close(owned)
        except BaseException as exc:
            errors.append(exc)
    _scan_raise_errors(errors)
    fields = {"run_id", "phase", "command_index", "command_count", "argv", "repo_root", "candidate_files", "candidate_read_bytes"}
    if expected_wire_version == 2:
        fields |= {"wire_version", "rp5a_read_basis", "parent_identity"}
    if type(value) is not MappingProxyType or set(value) != fields:
        raise ValueError("invalid closed launch fields")
    basis = parent = None
    if expected_wire_version == 2:
        if type(value["wire_version"]) is not int or value["wire_version"] != 2:
            raise ValueError("reader launch wire version mismatch")
        basis = _rp5a_basis_from_projection_v1(value["rp5a_read_basis"])
        if basis != expected_rp5a_read_basis:
            raise ValueError("reader basis differs from original parent profile")
        parent_value = value["parent_identity"]
        if expected_parent_identity is None:
            if parent_value is not None:
                raise ValueError("direct reader launch cannot delegate")
        else:
            fields_parent = tuple(_ScanLaunchIdentity.__dataclass_fields__)
            if type(parent_value) is not MappingProxyType or set(parent_value) != set(fields_parent):
                raise ValueError("invalid closed parent identity")
            parent = _ScanLaunchIdentity(*(parent_value[key] for key in fields_parent))
            if type(expected_parent_identity) is not _ScanLaunchIdentity or parent != expected_parent_identity:
                raise ValueError("reader parent differs from independently selected original")
    identity = _ScanLaunchIdentity(*(value[key] for key in ("run_id", "phase", "command_index", "command_count", "argv", "repo_root")))
    if type(expected_identity) is not _ScanLaunchIdentity or identity != expected_identity:
        raise ValueError("launch differs from independent original expectation")
    if type(value["candidate_read_bytes"]) is not int or value["candidate_read_bytes"] <= 0:
        raise ValueError("original positive candidate allowance required")
    raw_rows = value["candidate_files"]
    if type(raw_rows) is not tuple or len(raw_rows) > limits.node_limit:
        raise ValueError("invalid bounded candidate transport")
    rows = []
    for row in raw_rows:
        if (type(row) is not tuple or len(row) != 5 or type(row[3]) is not str
                or len(row[3]) % 2 or re.fullmatch(r"[0-9a-f]*", row[3]) is None):
            raise ValueError("invalid restricted candidate byte representation")
        if len(row[3]) // 2 > value["candidate_read_bytes"]:
            raise ValueError("candidate byte operand exceeds original allowance")
        rows.append(_ScanCandidateSurface(row[0], row[1], row[2], bytes.fromhex(row[3]), row[4]))
    result = tuple(rows)
    _scan_launch_payload(identity, result, limits=limits, candidate_read_bytes=value["candidate_read_bytes"],
                         rp5a_read_basis=basis, parent_identity=parent)
    _scan_deadline(deadline_ns)
    if expected_wire_version == 2:
        return identity, result, value["candidate_read_bytes"], basis, parent
    return identity, result, value["candidate_read_bytes"]


class _ScanLaunchInput:
    def __init__(self, identity, candidate_files, *, limits, candidate_read_bytes,
                 deadline_ns, scratch_root, scratch_bytes, parent_frame_reread_bytes, check_candidate,
                 rp5a_read_basis=None, parent_identity=None, wire_version=None, snapshot_root=None):
        self.wire_version = (1 if rp5a_read_basis is None else 2) if wire_version is None else wire_version
        self.snapshot_root = snapshot_root
        self.rp5a_read_basis = rp5a_read_basis
        self.parent_identity = parent_identity
        self.identity = identity
        self.candidate_files = candidate_files
        self.limits = limits
        self.candidate_read_bytes = candidate_read_bytes
        self.deadline_ns = deadline_ns
        self.scratch_root = Path(scratch_root)
        self.scratch_bytes = scratch_bytes
        self.remaining_reread = parent_frame_reread_bytes
        self.check_candidate = check_candidate
        self.process_id = os.getpid()
        self.thread_id = threading.get_ident()
        self.state = "PREPARING"
        self.entry_attempted = False
        self.path = None
        self.reader = None
        self.writer = None
        self.writer_close_attempted = False
        self.reader_close_attempted = False
        self.process = None
        self.last_ns = _scan_deadline(deadline_ns)
        self.payload = _scan_launch_payload(identity, candidate_files, limits=limits,
                                           candidate_read_bytes=candidate_read_bytes,
                                           rp5a_read_basis=rp5a_read_basis, parent_identity=parent_identity,
                                           wire_version=wire_version, snapshot_root=snapshot_root)
        self.length = _scan_launch_measure(self.payload, limits=limits)
        self.payload_bytes = self.payload["payload_byte_count"] if self.wire_version == 3 else 0
        self.extent = self.length + 4 + self.payload_bytes
        if self.wire_version == 3:
            _scan_v3_integer(self.extent, "complete frame extent")
            root = Path(identity.repo_root)
            if (snapshot_root.is_relative_to(root) or root.is_relative_to(snapshot_root)
                    or snapshot_root.is_relative_to(self.scratch_root) or self.scratch_root.is_relative_to(snapshot_root)):
                raise ValueError("snapshot area aliases repository or launch cleanup allocation")
        required_reads = (self.payload_bytes + 3 * (self.extent + self.payload_bytes)
                          if self.wire_version == 3 else 3 * self.extent)
        if (type(scratch_bytes) is not int or type(parent_frame_reread_bytes) is not int
                or scratch_bytes < self.extent or parent_frame_reread_bytes < required_reads):
            raise ValueError("original launch input allocation cannot cover its measured lifetime")

    def _check(self):
        if (os.getpid(), threading.get_ident()) != (self.process_id, self.thread_id):
            raise ValueError("foreign launch input owner")
        now = _scan_deadline(self.deadline_ns)
        if now < self.last_ns:
            raise ValueError("launch input clock regressed")
        self.last_ns = now
        if self.wire_version != 3:
            _scan_candidate_fence(self.check_candidate)
        if self.wire_version == 3 and hasattr(self, "directory_identity"):
            current = self.scratch_root.lstat()
            if (_stat_is_reparse_point(current) or not stat.S_ISDIR(current.st_mode)
                    or (current.st_dev, current.st_ino, current.st_mode) != self.directory_identity):
                raise ValueError("streamed input scratch identity changed")
        else:
            _local_unlinked_path(self.scratch_root)
            if not self.scratch_root.is_dir():
                raise ValueError("original input scratch directory unavailable")

    def _parts(self):
        if self.wire_version == 3:
            yield from self._parts_v3()
            return
        yield self.length.to_bytes(4, "big")
        yield from _scan_launch_parts(self.payload)

    def _compare(self):
        if self.wire_version == 3:
            return self._compare_v3()
        self._check()
        if self.process is not None and self.process.poll() is None:
            raise ValueError("cannot reread launch input while child is live")
        if self.remaining_reread < self.extent:
            raise ValueError("cumulative parent frame reread allowance exhausted")
        if (_scan_same_api_version(os.fstat(self.reader.fileno())) != self.descriptor_version
                or _scan_same_api_version(self.path.lstat()) != self.path_version):
            raise ValueError("original launch frame changed")
        self.reader.seek(0)
        count = 0
        for expected in self._parts():
            offset = 0
            while offset < len(expected):
                self._check()
                chunk = self.reader.read(len(expected) - offset)
                if type(chunk) is not bytes or not chunk or len(chunk) > len(expected) - offset:
                    raise ValueError("invalid parent frame read progress")
                self.remaining_reread -= len(chunk)
                if chunk != expected[offset:offset + len(chunk)]:
                    raise ValueError("parent launch frame byte mismatch")
                offset += len(chunk)
                count += len(chunk)
        suffix = self.reader.read(1)
        if type(suffix) is not bytes or suffix or count != self.extent:
            if type(suffix) is bytes:
                self.remaining_reread -= len(suffix)
            raise ValueError("parent launch frame suffix/extent mismatch")
        if (_scan_same_api_version(os.fstat(self.reader.fileno())) != self.descriptor_version
                or _scan_same_api_version(self.path.lstat()) != self.path_version):
            raise ValueError("launch frame changed during parent comparison")
        self._check()

    def _charge_v3(self, count):
        self.remaining_reread -= count
        if self.remaining_reread < 0:
            raise ValueError("streamed input cumulative acquisition allowance exhausted")

    def _parts_v3(self):
        yield self.length.to_bytes(4, "big")
        buffer = bytearray()
        for part in _scan_launch_parts(self.payload):
            offset = 0
            while offset < len(part):
                take = min(_SCAN_V3_CHUNK - len(buffer), len(part) - offset)
                buffer.extend(part[offset:offset + take])
                offset += take
                if len(buffer) == _SCAN_V3_CHUNK:
                    yield bytes(buffer)
                    buffer.clear()
        if buffer:
            yield bytes(buffer)
        for row in self.candidate_files:
            if row.kind != "FILE":
                continue
            with _scan_snapshot_descriptor_v3(row.content, self.snapshot_root, self._check) as descriptor:
                remaining = row.content.length
                while remaining:
                    request = min(_SCAN_V3_CHUNK, remaining)
                    if request > self.remaining_reread:
                        raise ValueError("streamed snapshot acquisition allowance exhausted")
                    chunk = _scan_v3_native_read(descriptor, request, self._charge_v3, self._check)
                    if not chunk:
                        raise ValueError("original snapshot ended before its admitted extent")
                    remaining -= len(chunk)
                    yield chunk
                if _scan_v3_native_read(descriptor, 1, self._charge_v3, self._check):
                    raise ValueError("original snapshot grew beyond its admitted extent")

    def _write_v3(self):
        parts = self._parts_v3()
        errors = []
        written = 0
        try:
            for chunk in parts:
                offset = 0
                while offset < len(chunk):
                    self._check()
                    count = self.writer.write(memoryview(chunk)[offset:])
                    if type(count) is not int or not 0 < count <= len(chunk) - offset:
                        raise OSError("invalid streamed launch write progress")
                    offset += count
                    written += count
        except BaseException as error:
            errors.append(error)
        finally:
            try:
                parts.close()
            except BaseException as error:
                errors.append(error)
        _scan_raise_errors(errors)
        return written

    def _compare_v3(self):
        self._check()
        _local_unlinked_path(self.scratch_root)
        if self.process is not None and self.process.poll() is None:
            raise ValueError("cannot reread streamed launch input while child is live")
        needed = self.extent + self.payload_bytes
        if self.remaining_reread < needed:
            raise ValueError("cumulative streamed readback allowance exhausted")
        self._check_frame_v3()
        _scan_candidate_fence(self.check_candidate)
        self.reader.seek(0)
        count = 0
        parts = self._parts_v3()
        errors = []
        try:
            for expected in parts:
                offset = 0
                while offset < len(expected):
                    self._check()
                    self._check_frame_v3()
                    request = min(_SCAN_V3_CHUNK, len(expected) - offset)
                    chunk = self.reader.read(request)
                    if type(chunk) is bytes:
                        self._charge_v3(len(chunk))
                    if type(chunk) is not bytes or not chunk or len(chunk) > request:
                        raise ValueError("invalid streamed parent frame read progress")
                    if chunk != expected[offset:offset + len(chunk)]:
                        raise ValueError("streamed parent frame byte mismatch")
                    count += len(chunk)
                    offset += len(chunk)
        except BaseException as error:
            errors.append(error)
        finally:
            try:
                parts.close()
            except BaseException as error:
                errors.append(error)
        _scan_raise_errors(errors)
        suffix = self.reader.read(1)
        if type(suffix) is bytes:
            self._charge_v3(len(suffix))
        if type(suffix) is not bytes or suffix or count != self.extent:
            raise ValueError("streamed parent frame suffix/extent mismatch")
        self._check_frame_v3()
        self._check()

    def _check_frame_v3(self):
        if (_scan_same_api_version(os.fstat(self.reader.fileno())) != self.descriptor_version
                or _scan_same_api_version(self.path.lstat()) != self.path_version
                or os.fstat(self.reader.fileno()).st_size != self.extent):
            raise ValueError("original streamed launch frame changed")

    def __enter__(self):
        # Refuse duplicate entry before callbacks, allocation or cleanup. A
        # rejected nested entry must not close the original live owner's frame.
        if (os.getpid(), threading.get_ident()) != (self.process_id, self.thread_id):
            raise ValueError("foreign launch input owner")
        if self.state != "PREPARING" or self.entry_attempted:
            raise ValueError("launch input entry is single use")
        self.entry_attempted = True
        try:
            self._check()
            directory = self.scratch_root.lstat()
            self.directory_identity = directory.st_dev, directory.st_ino, directory.st_mode
            descriptor, raw_path = tempfile.mkstemp(prefix="scan-launch-", dir=self.scratch_root)
            self.path = Path(raw_path)
            try:
                os.set_inheritable(descriptor, False)
                self.writer = os.fdopen(descriptor, "wb", buffering=0)
            except BaseException as allocation_error:
                errors = [allocation_error]
                try:
                    os.close(descriptor)
                except BaseException as close_error:
                    errors.append(close_error)
                _scan_raise_errors(errors)
            written = 0
            if self.wire_version == 3:
                written = self._write_v3()
            else:
                for chunk in self._parts():
                    offset = 0
                    while offset < len(chunk):
                        self._check()
                        count = self.writer.write(memoryview(chunk)[offset:])
                        if type(count) is not int or not 0 < count <= len(chunk) - offset:
                            raise OSError("invalid launch frame write progress")
                        offset += count
                        written += count
            if written != self.extent:
                raise ValueError("launch frame measurement differs from emission")
            self.writer.flush()
            os.fsync(self.writer.fileno())
            original = os.fstat(self.writer.fileno())
            reader_fd = _open_regular_worktree_descriptor(self.path, nonblocking=True)
            try:
                os.set_inheritable(reader_fd, False)
                read_stat = os.fstat(reader_fd)
                if _scan_file_identity(read_stat) != _scan_file_identity(original):
                    raise ValueError("launch readonly descriptor differs from original writer")
                self.reader = os.fdopen(reader_fd, "rb", buffering=0)
            except BaseException as body:
                errors = [body]
                try:
                    os.close(reader_fd)
                except BaseException as close_error:
                    errors.append(close_error)
                _scan_raise_errors(errors)
            self.writer_close_attempted = True
            self.writer.close()
            self.descriptor_version = _scan_same_api_version(os.fstat(self.reader.fileno()))
            self.path_version = _scan_same_api_version(self.path.lstat())
            if _scan_file_identity(os.fstat(self.reader.fileno())) != _scan_file_identity(self.path.lstat()):
                raise ValueError("launch frame original path changed")
            self._compare()
            self.reader.seek(0)
            self.state = "READY"
            return self
        except BaseException as body:
            self.state = "HELD"
            self._close(body)

    def _claim(self, *, run_id, phase, command_index, argv, cwd):
        self._check()
        if (self.state != "READY" or (run_id, phase, command_index, tuple(argv), str(cwd))
                != (self.identity.run_id, self.identity.phase, self.identity.command_index,
                    self.identity.argv, self.identity.repo_root)):
            raise ValueError("launch input does not belong to this original occurrence")
        self._compare()
        self.reader.seek(0)
        self.state = "ISSUED"
        return self.reader

    def _attached(self, process):
        if self.state != "ISSUED" or type(process.pid) is not int or process.pid <= 0:
            self.state = "HELD"
            raise ValueError("launch input lacks actual process association")
        self.process = process
        self.state = "ATTACHED"

    def _finished(self, process, native_exit):
        try:
            if (self.state != "ATTACHED" or self.process is not process or type(native_exit) is not int
                    or process.poll() is None or process.returncode != native_exit):
                raise ValueError("launch input original child terminal state unproven")
            if self.reader.tell() != self.extent:
                raise ValueError("child did not consume exact original input extent")
            self._compare()
            self.state = "CONSUMED"
        except BaseException:
            self.state = "HELD"
            raise

    def _close(self, body=None):
        errors = [] if body is None else [body]
        if self.process is not None and self.process.poll() is None:
            self.state = "HELD"
            errors.append(RuntimeError("live child retains original launch input custody"))
            _scan_raise_errors(errors)
        safe = self.path is not None and hasattr(self, "path_version")
        if self.wire_version == 3 and self.state == "HELD":
            safe = False
            if body is None:
                errors.append(ValueError("held streamed launch retains its original frame evidence"))
        if safe:
            try:
                _local_unlinked_path(self.scratch_root)
                current = self.scratch_root.lstat()
                if (current.st_dev, current.st_ino, current.st_mode) != self.directory_identity:
                    raise ValueError("launch scratch identity changed")
                if _scan_same_api_version(self.path.lstat()) != self.path_version:
                    raise ValueError("launch input path changed before cleanup")
            except BaseException as exc:
                errors.append(exc)
                safe = False
        for role in ("writer", "reader"):
            stream = getattr(self, role)
            attempted = role + "_close_attempted"
            if stream is not None and not getattr(self, attempted):
                setattr(self, attempted, True)
                try:
                    stream.close()
                except BaseException as exc:
                    errors.append(exc)
                    safe = False
        if safe:
            try:
                if _scan_same_api_version(self.path.lstat()) != self.path_version:
                    raise ValueError("launch input path changed at unlink")
                self.path.unlink()
                self.state = "CLOSED"
            except BaseException as exc:
                errors.append(exc)
        _scan_raise_errors(errors)

    def __exit__(self, exc_type, exc, traceback):
        self._close(exc)
        return False


def _read_scan_bound_launch_fd(fd, *, repo_root, environment, explicit_basetemp, original_argv):
    attestation, profile = _scan_read_forwarded_profile(
        repo_root, environment=environment, explicit_basetemp=explicit_basetemp)
    # Numeric spelling has already been checked by the one forwarded-profile read.
    lowered = {key.upper(): value for key, value in environment.items()}
    limits = _ScanRunReadLimits(*(int(lowered[key]) for key in (
        "QTT_SCAN_BYTE_LIMIT", "QTT_SCAN_NODE_LIMIT", "QTT_SCAN_DEPTH_LIMIT", "QTT_SCAN_PROFILE_LIMIT")))
    identity = _ScanLaunchIdentity(attestation.run_id, lowered["QTT_SCAN_PHASE"], profile.command_index,
                                  int(lowered["QTT_SCAN_COMMAND_COUNT"]), tuple(original_argv), str(repo_root))
    deadline = min(int(lowered["QTT_SCAN_DEADLINE_NS"]), profile.deadline_ns)
    _, rows, candidate_read_bytes = _read_scan_launch_fd(
        fd, limits=limits, deadline_ns=deadline, expected_identity=identity)
    fence = _ScanCandidateFence(repo_root, rows, limits=limits,
                                candidate_read_bytes=candidate_read_bytes, deadline_ns=deadline)
    _scan_candidate_fence(fence)
    result = (attestation, profile, fence)
    _scan_deadline(deadline)
    return result

def _read_rp5a_bound_launch_fd_v1(fd, *, repo_root, environment, explicit_basetemp, original_argv,
                                  expected_role, expected_parent_identity=None):
    if expected_role not in {"SCANNER", "VALIDATE", "PYTEST", "EVIDENCE"}:
        raise ValueError("unknown independently selected RP5A consumer role")
    lowered = {key.upper(): value for key, value in environment.items()}
    # Direct script callers do not have a pytest basetemp argument. Its fixed
    # original child p root is independently selected from the inherited owner.
    if explicit_basetemp is None:
        explicit_basetemp = Path(lowered[PROCESS_ROOT_ENV]) / PYTEST_BASETEMP_DIR_NAME
    attestation, scanner, reader, basis, selected_version, selected_payload = _scan_read_forwarded_profile(
        repo_root, environment=environment, explicit_basetemp=explicit_basetemp, reader_required=True, include_wire_binding=True)
    limits = _ScanRunReadLimits(*(int(lowered[key]) for key in (
        "QTT_SCAN_BYTE_LIMIT", "QTT_SCAN_NODE_LIMIT", "QTT_SCAN_DEPTH_LIMIT", "QTT_SCAN_PROFILE_LIMIT")))
    outer_identity = _ScanLaunchIdentity(attestation.run_id, lowered["QTT_SCAN_PHASE"],
        reader.command_index, int(lowered["QTT_SCAN_COMMAND_COUNT"]), tuple(original_argv), str(repo_root))
    if expected_parent_identity is None:
        if _rp5a_consumer_role_v1(tuple(original_argv), repo_root) != expected_role:
            raise ValueError("RP5A role differs from actual original entry")
        identity = outer_identity
    else:
        parent = expected_parent_identity
        if (type(parent) is not _ScanLaunchIdentity or expected_role != "PYTEST"
                or (parent.run_id, parent.phase, parent.command_index, parent.command_count, parent.repo_root)
                != (outer_identity.run_id, outer_identity.phase, outer_identity.command_index,
                    outer_identity.command_count, outer_identity.repo_root)
                or _rp5a_consumer_role_v1(parent.argv, repo_root) != "PYTEST"):
            raise ValueError("invalid independently bound original pytest parent")
        identity = _ScanLaunchIdentity(attestation.run_id, "nested-pytest", 1, 1, tuple(original_argv), str(repo_root))
    if (scanner is not None) != (expected_role == "SCANNER"):
        raise ValueError("scanner allocation does not match reader consumer role")
    deadline = min(int(lowered["QTT_SCAN_DEADLINE_NS"]), reader.deadline_ns)
    if selected_version == 3 and (expected_role != "SCANNER" or scanner is None or expected_parent_identity is not None):
        raise ValueError("streamed transport requires the direct original scanner entry")
    decoded = _read_scan_launch_fd(
        fd, limits=limits, deadline_ns=deadline, expected_identity=identity,
        expected_wire_version=selected_version, expected_parent_identity=expected_parent_identity,
        expected_rp5a_read_basis=basis, expected_payload_bytes=selected_payload if selected_version == 3 else None)
    _, rows, allowance, original_basis, parent = decoded[:5]
    lease = decoded[5] if selected_version == 3 else None
    try:
        bindings = ({"wire_version": 3, "surface_role": "receiver", "payload_lease": lease}
                    if selected_version == 3 else {})
        fence = _ScanCandidateFence(repo_root, rows, limits=limits,
                                    candidate_read_bytes=allowance, deadline_ns=deadline, **bindings)
        fence()
        fence.transport_extent = os.fstat(fd).st_size
        return attestation, scanner, reader, original_basis, fence, parent
    except BaseException as body:
        errors = [body]
        if lease is not None:
            try:
                lease._hold()
                lease.close()
            except BaseException as error:
                errors.append(error)
        _scan_raise_errors(errors)


# Original mapper acquisition: one shared native binding, no scanner role expansion.
import copy
# Original occurrence -> family -> direct CLI, or None for the two retained
# mapper pytest wrappers. No data payload can add routes or executable text.
_REPORT_READ_ROUTES_V1 = (
    (66, 'QB', 'tools/validate_pr166_qb_bounded_quantum_benchmark.py', None),
    (67, 'QC', 'tools/validate_pr166_qc_quantum_selected_replay_paper_retest.py', None),
    (68, 'MAPPER', 'tools/validate_pr162e_q_quantum_automapper.py', None),
    (429, 'QB', None, ('tests/stage1_prediction_markets/pr166_qb_bounded_quantum_benchmark/test_pr166_qb_idempotence.py', '-q', '--durations=50')),
    (430, 'QB', None, ('tests/stage1_prediction_markets/pr166_qb_bounded_quantum_benchmark', '-q', '--ignore', 'tests/stage1_prediction_markets/pr166_qb_bounded_quantum_benchmark/test_pr166_qb_idempotence.py', '--durations=50')),
    (431, 'QC', None, ('tests/stage1_prediction_markets/pr166_qc_quantum_selected_replay_paper_retest/test_pr166_qc_idempotence.py', '-q', '--durations=50')),
    (432, 'QC', None, ('tests/stage1_prediction_markets/pr166_qc_quantum_selected_replay_paper_retest', '-q', '--ignore', 'tests/stage1_prediction_markets/pr166_qc_quantum_selected_replay_paper_retest/test_pr166_qc_idempotence.py', '--durations=50')),
    (433, 'MAPPER', None, ('tests/stage1_prediction_markets/pr162e_q_quantum_automapper/test_pr162e_q_idempotence.py', '-q', '--durations=50')),
    (434, 'MAPPER', None, ('tests/stage1_prediction_markets/pr162e_q_quantum_automapper', '-q', '--ignore', 'tests/stage1_prediction_markets/pr162e_q_quantum_automapper/test_pr162e_q_idempotence.py', '--durations=50')),
)


_MAPPER_INTEGER_MAX_V1 = (1 << 63) - 1
def _mapper_need_v1(condition, message):
    if not condition:
        raise ValueError(message)

def _mapper_relative_v1(name):
    _mapper_need_v1(type(name) is str and name and '\\' not in name and ':' not in name, 'UNSAFE_MEMBER')
    parts = name.split('/')
    p = PurePosixPath(name)
    _mapper_need_v1(not p.is_absolute() and all(x not in ('', '.', '..') for x in parts), 'UNSAFE_MEMBER')
    return p

def _mapper_int_v1(value, name, *, positive=False):
    if type(value) is not int or not int(positive) <= value <= _MAPPER_INTEGER_MAX_V1:
        raise ValueError('RUNTIME_INTEGER:' + name)
    return value

def _mapper_add_v1(a, b):
    _mapper_int_v1(a, 'sum_left'); _mapper_int_v1(b, 'sum_right')
    if b > _MAPPER_INTEGER_MAX_V1 - a:
        raise ValueError('RUNTIME_INTEGER_OVERFLOW')
    return a + b

def _mapper_portable_relative_v1(name):
    """Portable, nonaliasing relative spelling; physical identity is also checked."""
    p = _mapper_relative_v1(name)
    reserved = {'CON', 'PRN', 'AUX', 'NUL', 'CONIN$', 'CONOUT$'}
    reserved |= {prefix + digit for prefix in ('COM', 'LPT') for digit in '123456789¹²³'}
    for part in p.parts:
        if (any(ord(c) < 32 or c in '<>:"|?*' for c in part)
                or part.endswith((' ', '.')) or part.split('.')[0].upper() in reserved):
            raise ValueError('BASIS_NONPORTABLE_PATH')
    return p

def _mapper_absolute_v1(value):
    if type(value) is not str or not value or '\0' in value:
        raise ValueError('BASIS_ABSOLUTE_PATH')
    p = Path(value)
    if not p.is_absolute() or str(p) != os.path.normpath(value) or '..' in p.parts:
        raise ValueError('BASIS_ABSOLUTE_PATH')
    return p

def _mapper_stamp_v1(info, *, directory=False):
    if (getattr(info, 'st_file_attributes', 0) & 0x400 or
            not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))):
        raise ValueError('BASIS_UNSUPPORTED_FILE_KIND')
    if not directory and info.st_nlink != 1:
        raise ValueError('BASIS_MULTIPLE_LINKS')
    common = [info.st_dev, info.st_ino, info.st_mode]
    if not directory:
        common += [info.st_size, info.st_mtime_ns, info.st_nlink, info.st_ctime_ns]
    return common

def _mapper_chain_v1(path, observe=os.lstat):
    return [[str(p), _mapper_stamp_v1(observe(p), directory=True)]
            for p in (*reversed(path.parents), path)]

def _mapper_profile_v1(profile):
    """Validate representation, not acceptance. Every resource operand is explicit."""
    fields = {'kind', 'position', 'generation', 'root', 'root_chain', 'basis',
              'basis_chain', 'basis_lstat', 'basis_fstat', 'entries', 'limits',
              'chunk_bytes', 'deadline_ns'}
    _mapper_need_v1(type(profile) is dict and set(profile) == fields, 'BASIS_PROFILE_FIELDS')
    _mapper_need_v1(profile['kind'] == 'MAPPER_DISK_BASIS_V1', 'BASIS_PROFILE_KIND')
    _mapper_need_v1(type(profile['position']) is int and profile['position'] in tuple(row[0] for row in _REPORT_READ_ROUTES_V1), 'BASIS_POSITION')
    _mapper_need_v1(type(profile['generation']) is str and bool(profile['generation']), 'BASIS_GENERATION')
    root = _mapper_absolute_v1(profile['root']); basis = _mapper_absolute_v1(profile['basis'])
    _mapper_need_v1(not basis.is_relative_to(root) and not root.is_relative_to(basis.parent), 'BASIS_ROOT_OVERLAP')
    _mapper_int_v1(profile['chunk_bytes'], 'chunk', positive=True)
    _mapper_int_v1(profile['deadline_ns'], 'deadline', positive=True)
    limits = profile['limits']
    _mapper_need_v1(type(limits) is dict and set(limits) == {'attempts', 'target_bytes', 'basis_bytes', 'metadata_calls', 'single_target_buffer'}, 'BASIS_LIMIT_FIELDS')
    for name, value in limits.items(): _mapper_int_v1(value, name)
    def stamp(value, n):
        _mapper_need_v1(type(value) is list and len(value) == n and all(type(x) is int for x in value), 'BASIS_STAMP_FIELDS')
        _mapper_need_v1(value[0] >= 0 and value[1] > 0 and value[2] >= 0, 'BASIS_STAMP_IDENTITY')
        if n == 7:
            _mapper_need_v1(value[3] >= 0 and value[5] == 1 and stat.S_ISREG(value[2]), 'BASIS_STAMP_FILE')
        else: _mapper_need_v1(stat.S_ISDIR(value[2]), 'BASIS_STAMP_DIRECTORY')
    for name, path in (('root_chain', root), ('basis_chain', basis.parent)):
        expected = [str(p) for p in (*reversed(path.parents), path)]
        chain = profile[name]
        _mapper_need_v1(type(chain) is list and len(chain) == len(expected), 'BASIS_CHAIN_FIELDS')
        for row, wanted in zip(chain, expected):
            _mapper_need_v1(type(row) is list and len(row) == 2 and row[0] == wanted, 'BASIS_CHAIN_PATH')
            stamp(row[1], 3)
    stamp(profile['basis_lstat'], 7); stamp(profile['basis_fstat'], 7)
    _mapper_need_v1(profile['basis_lstat'][:6] == profile['basis_fstat'][:6], 'BASIS_CROSS_API_IDENTITY')
    entries = profile['entries']; _mapper_need_v1(type(entries) is list and bool(entries), 'BASIS_ENTRIES')
    names = set(); identities = set(); end = attempts = target = reference = 0
    for row in entries:
        _mapper_need_v1(type(row) is dict and set(row) == {'path', 'offset', 'length', 'attempt_limit', 'lstat', 'fstat', 'parent_chain'}, 'BASIS_ENTRY_FIELDS')
        name = row['path']; _mapper_portable_relative_v1(name)
        _mapper_need_v1(name.casefold() not in names, 'BASIS_ALIAS_SPELLING'); names.add(name.casefold())
        for field in ('offset', 'length', 'attempt_limit'):
            _mapper_int_v1(row[field], field, positive=field == 'attempt_limit')
        _mapper_need_v1(row['offset'] == end, 'BASIS_NONCONTIGUOUS_SEGMENT')
        end = _mapper_add_v1(end, row['length'])
        stamp(row['lstat'], 7); stamp(row['fstat'], 7)
        _mapper_need_v1(row['lstat'][:6] == row['fstat'][:6] and row['lstat'][3] == row['length'], 'BASIS_ENTRY_IDENTITY')
        identity = tuple(row['lstat'][:2]); _mapper_need_v1(identity not in identities, 'BASIS_PHYSICAL_ALIAS'); identities.add(identity)
        parent = root.joinpath(*name.split('/')).parent
        expected_chain = [str(p) for p in (*reversed(parent.parents), parent)]
        chain = row['parent_chain']; _mapper_need_v1(type(chain) is list and len(chain) == len(expected_chain), 'BASIS_ENTRY_PARENT_CHAIN')
        for pair, wanted in zip(chain, expected_chain):
            _mapper_need_v1(type(pair) is list and len(pair) == 2 and pair[0] == wanted, 'BASIS_ENTRY_PARENT_PATH')
            stamp(pair[1], 3)
        _mapper_need_v1(chain[:len(profile['root_chain'])] == profile['root_chain'], 'BASIS_ENTRY_ROOT_DRIFT')
        attempts = _mapper_add_v1(attempts, row['attempt_limit'])
        # Overflow is checked before addition even though Python integers grow.
        t = row['attempt_limit'] * _mapper_add_v1(row['length'], 1)
        b = row['attempt_limit'] * row['length']
        target = _mapper_add_v1(target, t); reference = _mapper_add_v1(reference, b)
    _mapper_need_v1(end == profile['basis_lstat'][3], 'BASIS_FINAL_EXTENT')
    _mapper_need_v1(tuple(profile['basis_lstat'][:2]) not in identities, 'BASIS_ALIASES_INPUT')
    _mapper_need_v1(limits['attempts'] <= attempts and limits['target_bytes'] <= target and limits['basis_bytes'] <= reference, 'BASIS_EXCESS_UNUSED_ALLOCATION')
    return {'unique_files': len(entries), 'basis_extent': end, 'attempt_envelope': attempts,
            'target_byte_reservation_envelope': target, 'basis_byte_reservation_envelope': reference,
            'is_authentic_resource_grant': False}

class _MapperDiskBasisV1:
    """Pinned original-generation, disk-backed comparator for one process/thread.

    Does not sandbox Python or preempt blocking OS calls. The original parent
    must supervise termination and retain input/evidence custody. The caller
    supplies an independently bound identity; the profile cannot approve itself.
    """
    def __init__(self, profile, *, expected_position, expected_generation, clock):
        import threading
        self.profile = copy.deepcopy(profile)
        self.shape = _mapper_profile_v1(self.profile)
        _mapper_need_v1(type(expected_position) is int and expected_position == profile['position']
             and type(expected_generation) is str and expected_generation == profile['generation'], 'BASIS_WRONG_OCCURRENCE_OR_GENERATION')
        _mapper_need_v1(callable(clock), 'BASIS_CLOCK_REQUIRED')
        self.clock = clock; self.last_clock = None; self.owner = (os.getpid(), threading.get_ident())
        self.busy = False; self.poisoned = False; self.closed = False
        self.counters = {k: 0 for k in ('attempts', 'target_bytes', 'basis_bytes', 'metadata_calls', 'target_read_calls', 'basis_read_calls')}
        self.reserved = {'target_bytes': 0, 'basis_bytes': 0}; self.by_path = {}; self.events = []
        self.root = Path(profile['root']); self.basis = Path(profile['basis'])
        self.entries = {row['path']: row for row in self.profile['entries']}
        self.fd = None
        self._check()
        try:
            self._chains()
            _mapper_need_v1(self._stamp(self.basis) == profile['basis_lstat'], 'BASIS_INITIAL_PATH_CHANGED')
            self.fd = os.open(self.basis, os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0))
            os.set_inheritable(self.fd, False)
            _mapper_need_v1(self._stamp(fd=self.fd) == profile['basis_fstat'], 'BASIS_INITIAL_HANDLE_CHANGED')
            self._basis_current()
        except BaseException as primary:
            self.poisoned = True
            if self.fd is not None:
                fd,self.fd = self.fd,None
                try: os.close(fd)
                except BaseException as secondary:
                    raise BaseExceptionGroup('basis initialization and close failed', [primary, secondary])
            raise

    def _check(self):
        import threading
        _mapper_need_v1((os.getpid(), threading.get_ident()) == self.owner, 'BASIS_FOREIGN_OWNER')
        _mapper_need_v1(not self.closed and not self.poisoned, 'BASIS_SESSION_UNUSABLE')
        try:
            now = self.clock(); _mapper_int_v1(now, 'clock')
            _mapper_need_v1(self.last_clock is None or now >= self.last_clock, 'BASIS_CLOCK_REGRESSION')
            self.last_clock = now
            if now >= self.profile['deadline_ns']: raise TimeoutError('BASIS_DEADLINE')
        except BaseException:
            self.poisoned = True
            raise

    def _stat(self, path=None, fd=None):
        self._check()
        _mapper_need_v1(self.counters['metadata_calls'] < self.profile['limits']['metadata_calls'], 'BASIS_METADATA_EXHAUSTED')
        self.counters['metadata_calls'] += 1
        result = os.fstat(fd) if fd is not None else os.lstat(path)
        self._check()
        return result

    def _stamp(self, path=None, fd=None):
        return _mapper_stamp_v1(self._stat(path, fd))

    def _chains(self, entry=None):
        for key, path in (('root_chain', self.root), ('basis_chain', self.basis.parent)):
            _mapper_need_v1(_mapper_chain_v1(path, self._stat) == self.profile[key], 'BASIS_PINNED_DIRECTORY_CHANGED')
        if entry is not None:
            parent = self.root.joinpath(*entry['path'].split('/')).parent
            _mapper_need_v1(_mapper_chain_v1(parent, self._stat) == entry['parent_chain'], 'BASIS_PINNED_PARENT_CHANGED')

    def _basis_current(self):
        self._chains()
        _mapper_need_v1(self._stamp(self.basis) == self.profile['basis_lstat'] and self._stamp(fd=self.fd) == self.profile['basis_fstat'], 'BASIS_CHANGED')

    def _read(self, fd, request, lane):
        self._check()
        _mapper_need_v1(type(request) is int and request > 0, 'BASIS_POSITIVE_READ_REQUIRED')
        self.counters[lane + '_read_calls'] += 1
        data = os.read(fd, request)
        if type(data) is not bytes:
            self.poisoned = True; raise ValueError('BASIS_UNKNOWN_DELIVERED_BYTES')
        self.counters[lane + '_bytes'] = _mapper_add_v1(self.counters[lane + '_bytes'], len(data))
        if len(data) > request:
            self.poisoned = True; raise ValueError('BASIS_OVERSIZED_READ')
        self._check(); return data

    def read_json(self, name, parser):
        return self._acquire(name, parser, decode_text=True)

    def compare_bytes(self, name):
        return self._acquire(name, lambda value: None, decode_text=False)

    def _acquire(self, name, parser, *, decode_text):
        _mapper_portable_relative_v1(name); self._check()
        _mapper_need_v1(not self.busy and name in self.entries and callable(parser), 'BASIS_REENTRANT_OR_UNBOUND_READ')
        row = self.entries[name]; limits = self.profile['limits']; n = row['length']
        _mapper_need_v1(self.counters['attempts'] < limits['attempts'] and self.by_path.get(name, 0) < row['attempt_limit'], 'BASIS_ATTEMPTS_EXHAUSTED')
        self.counters['attempts'] += 1; self.by_path[name] = self.by_path.get(name, 0) + 1
        event = {'path':name,'ordinal':self.counters['attempts'],'outcome':'BEFORE_OPEN', 'target_bytes':0,'basis_bytes':0,'descriptor_closed':False}
        self.events.append(event); before = dict(self.counters)
        self.busy = True; target_fd = None; primary = None
        try:
            _mapper_need_v1(n + 1 <= limits['single_target_buffer'], 'BASIS_SINGLE_BUFFER_EXHAUSTED')
            for lane, amount in (('target_bytes', n + 1), ('basis_bytes', n)):
                _mapper_need_v1(amount <= limits[lane] - self.reserved[lane], 'BASIS_RESERVATION_EXHAUSTED')
            self.reserved['target_bytes'] += n + 1; self.reserved['basis_bytes'] += n
            self._basis_current(); self._chains(row)
            path = self.root.joinpath(*name.split('/'))
            _mapper_need_v1(self._stamp(path) == row['lstat'], 'BASIS_TARGET_GENERATION_CHANGED')
            target_fd = os.open(path, os.O_RDONLY | getattr(os,'O_BINARY',0) | getattr(os,'O_NOFOLLOW',0))
            os.set_inheritable(target_fd,False)
            _mapper_need_v1(self._stamp(fd=target_fd) == row['fstat'], 'BASIS_TARGET_HANDLE_CHANGED')
            os.lseek(self.fd, row['offset'], os.SEEK_SET)
            data = bytearray(); remaining = n
            event['outcome'] = 'READING'
            while remaining:
                chunk = self._read(target_fd, min(self.profile['chunk_bytes'], remaining), 'target')
                _mapper_need_v1(bool(chunk), 'BASIS_TARGET_TRUNCATED')
                compared = 0
                while compared < len(chunk):
                    expected = self._read(self.fd, len(chunk) - compared, 'basis')
                    _mapper_need_v1(bool(expected), 'BASIS_REFERENCE_TRUNCATED')
                    _mapper_need_v1(expected == chunk[compared:compared+len(expected)], 'BASIS_BYTES_DIFFER')
                    compared += len(expected)
                data.extend(chunk); remaining -= len(chunk)
            _mapper_need_v1(self._read(target_fd, 1, 'target') == b'', 'BASIS_TARGET_GREW')
            _mapper_need_v1(self._stamp(fd=target_fd) == row['fstat'] and self._stamp(path) == row['lstat'], 'BASIS_POSTREAD_TARGET_CHANGED')
            self._basis_current(); self._chains(row)
            event['outcome']='DECODE'
            text = (data.decode('utf-8', errors='strict').replace('\r\n','\n').replace('\r','\n')
                    if decode_text else None)
            self._check(); event['outcome']='PARSE'; result=parser(text); self._check()
            # Parser is synchronous. It may not hand out a lazy dependency on fd.
            self._basis_current(); self._chains(row)
            _mapper_need_v1(self._stamp(path) == row['lstat'], 'BASIS_TARGET_CHANGED_DURING_PARSE')
            event['outcome']='RETURNED'; return result
        except BaseException as exc:
            primary=exc
            if isinstance(exc,TimeoutError) or isinstance(exc,ValueError) and str(exc).startswith('BASIS_'):
                self.poisoned=True
            event['exception_type']=type(exc).__name__
            event['reason']=str(exc) if str(exc).startswith('BASIS_') else 'ORIGINAL_DECODER_OR_PARSER_EXCEPTION'
            raise
        finally:
            event['target_bytes']=self.counters['target_bytes']-before['target_bytes']
            event['basis_bytes']=self.counters['basis_bytes']-before['basis_bytes']
            self.busy=False
            if target_fd is not None:
                try:
                    os.close(target_fd); event['descriptor_closed']=True
                except BaseException as close_error:
                    self.poisoned=True
                    if primary is not None: raise BaseExceptionGroup('read and target close failed',[primary,close_error])
                    raise
            if primary is None:
                try: self._check()
                except BaseException:
                    self.poisoned=True; event['outcome']='FINAL_CHECK_FAILED'; raise

    def close(self):
        import threading
        _mapper_need_v1((os.getpid(),threading.get_ident())==self.owner and not self.busy, 'BASIS_CLOSE_WITHOUT_OWNERSHIP')
        if self.closed: return
        self.closed=True
        if self.fd is not None:
            fd,self.fd=self.fd,None
            os.close(fd)

# Runtime records live under the existing validation evidence owner, never Git.
_MAPPER_ACTIVATION_ENV_V1 = 'QTT_MAPPER_ACTIVATION_IDENTITY'


def _mapper_activation_limits_v1(binding):
    limits = binding['activation_limits']
    fields = {'target_bytes', 'basis_bytes', 'metadata_calls', 'record_bytes', 'evidence_deadline_ns'}
    if type(limits) is not dict or set(limits) != fields:
        raise ValueError('MAPPER_ACTIVATION_LIMIT_FIELDS')
    for name, value in limits.items():
        _mapper_int_v1(value, name, positive=name in ('metadata_calls', 'record_bytes', 'evidence_deadline_ns'))
    if limits['evidence_deadline_ns'] < binding['basis']['deadline_ns']:
        raise ValueError('MAPPER_ACTIVATION_EVIDENCE_BEFORE_EXECUTION_DEADLINE')
    entries = binding['basis']['entries']
    if (limits['target_bytes'] < sum(row['length'] + 1 for row in entries)
            or limits['basis_bytes'] < sum(row['length'] for row in entries)):
        raise ValueError('MAPPER_ACTIVATION_INSUFFICIENT_BYTE_ALLOWANCE')
    if limits['record_bytes'] > binding['run_read_limits']['byte_limit']:
        raise ValueError('MAPPER_ACTIVATION_RECORD_READ_CEILING')
    return limits


def _mapper_activation_path_v1(binding):
    return Path(binding['evidence_root']) / ('mapper-read-' + str(binding['command_index']) + '.json')


def _mapper_occurrence_generation_v1(binding):
    return json.dumps([binding['basis']['generation'], binding['run_id'], binding['phase'],
                       binding['command_index'], binding['original_position']],
                      ensure_ascii=True, separators=(',', ':'))


def _mapper_activation_record_v1(template, record):
    """The observed profile cannot replace expected bytes, roots or allowances."""
    template = _mapper_binding_v1(template)
    if template['kind'] != 'MAPPER_NATIVE_READ_BINDING_V2':
        raise ValueError('MAPPER_ACTIVATION_REQUIRES_V2')
    record = _mapper_plain_v1(record)
    if (type(record) is not dict or set(record) != {'kind', 'binding', 'observed'}
            or record['kind'] != 'MAPPER_OCCURRENCE_ACTIVATION_V1'):
        raise ValueError('MAPPER_ACTIVATION_RECORD_FIELDS')
    live = _mapper_binding_v1(record['binding'])
    reverse = copy.deepcopy(live)
    if live['basis']['generation'] != _mapper_occurrence_generation_v1(template):
        raise ValueError('MAPPER_ACTIVATION_GENERATION')
    reverse['basis']['generation'] = template['basis']['generation']
    if len(live['basis']['entries']) != len(template['basis']['entries']):
        raise ValueError('MAPPER_ACTIVATION_ENTRY_ROSTER')
    for old, current, restored in zip(template['basis']['entries'], live['basis']['entries'],
                                       reverse['basis']['entries'], strict=True):
        if current['lstat'][2:4] != old['lstat'][2:4] or current['fstat'][2:4] != old['fstat'][2:4]:
            raise ValueError('MAPPER_ACTIVATION_MODE_OR_LENGTH')
        restored['lstat'], restored['fstat'] = old['lstat'], old['fstat']
    if reverse != template:
        raise ValueError('MAPPER_ACTIVATION_TEMPLATE_DRIFT')
    observed = record['observed']; limits = template['activation_limits']
    if type(observed) is not dict or set(observed) != {'files', 'target_bytes', 'basis_bytes', 'metadata_calls'}:
        raise ValueError('MAPPER_ACTIVATION_OBSERVATION_FIELDS')
    for key, value in observed.items(): _mapper_int_v1(value, key)
    expected_bytes = sum(row['length'] for row in template['basis']['entries'])
    if (observed['files'] != len(template['basis']['entries'])
            or observed['target_bytes'] != expected_bytes or observed['basis_bytes'] != expected_bytes
            or not 0 < observed['metadata_calls'] <= limits['metadata_calls']):
        raise ValueError('MAPPER_ACTIVATION_OBSERVATION_CONFLICT')
    return live


def _mapper_activation_identity_v1(text):
    if type(text) is not str or len(text) > 200:
        raise ValueError('MAPPER_ACTIVATION_IDENTITY_EXTENT')
    try: value = json.loads(text)
    except (ValueError, TypeError) as exc: raise ValueError('MAPPER_ACTIVATION_IDENTITY') from exc
    if (type(value) is not list or len(value) != 7
            or any(type(v) is not int or abs(v) > 2**63 - 1 for v in value)
            or value[0] < 0 or value[1] <= 0 or not stat.S_ISREG(value[2])
            or value[3] < 0 or value[5] != 1
            or json.dumps(value, separators=(',', ':')) != text):
        raise ValueError('MAPPER_ACTIVATION_IDENTITY')
    return value


def _mapper_read_activation_v1(template, identity, *, expected_raw=None, evidence_review=False):
    """Bounded data read pinned by the original parent's launch environment."""
    template = _mapper_binding_v1(template)
    identity = _mapper_activation_identity_v1(identity)
    limits = _mapper_activation_limits_v1(template)
    if identity[3] > limits['record_bytes']:
        raise ValueError('MAPPER_ACTIVATION_RECORD_TOO_LARGE')
    path = _mapper_activation_path_v1(template)
    deadline = (limits['evidence_deadline_ns'] if evidence_review else template['basis']['deadline_ns'])
    _scan_deadline(deadline); _local_unlinked_path(path.parent)
    parents = _mapper_chain_v1(path.parent)
    if _mapper_stamp_v1(path.lstat()) != identity:
        raise ValueError('MAPPER_ACTIVATION_PATH_CHANGED')
    fd = _open_regular_worktree_descriptor(path, nonblocking=True)
    errors = []; raw = bytearray()
    try:
        opened = _mapper_stamp_v1(os.fstat(fd))
        if opened[:6] != identity[:6]: raise ValueError('MAPPER_ACTIVATION_HANDLE_CHANGED')
        while True:
            _scan_deadline(deadline)
            amount = min(template['basis']['chunk_bytes'], identity[3] - len(raw) + 1)
            data = os.read(fd, amount)
            if type(data) is not bytes or len(data) > amount:
                raise ValueError('MAPPER_ACTIVATION_READ_RESULT')
            raw.extend(data)
            if len(raw) > identity[3]: raise ValueError('MAPPER_ACTIVATION_GREW')
            if not data: break
        if (len(raw) != identity[3] or _mapper_stamp_v1(os.fstat(fd)) != opened
                or _mapper_stamp_v1(path.lstat()) != identity):
            raise ValueError('MAPPER_ACTIVATION_READ_DRIFT')
    except BaseException as exc: errors.append(exc)
    try: os.close(fd)
    except BaseException as exc: errors.append(exc)
    _scan_raise_errors(errors)
    if _mapper_chain_v1(path.parent) != parents or _mapper_stamp_v1(path.lstat()) != identity:
        raise ValueError('MAPPER_ACTIVATION_AFTER_CLOSE_DRIFT')
    _scan_deadline(deadline)
    raw = bytes(raw)
    if expected_raw is not None and raw != expected_raw:
        raise ValueError('MAPPER_ACTIVATION_RETAINED_BYTES_DRIFT')
    read_limits = _ScanRunReadLimits(**template['run_read_limits'])
    record = _scan_owned_json(raw, read_limits)
    live = _mapper_activation_record_v1(template, record)
    return live, raw


@dataclass(frozen=True, slots=True)
class _MapperOccurrenceRecordV1:
    template_json: bytes
    record_json: bytes
    identity: str
    process_id: int
    thread_id: int

    def template(self):
        return _mapper_binding_v1(json.loads(self.template_json))

    def binding(self):
        return _mapper_activation_record_v1(self.template(), json.loads(self.record_json))

    def verify(self):
        import threading
        if (os.getpid(), threading.get_ident()) != (self.process_id, self.thread_id):
            raise ValueError('MAPPER_ACTIVATION_FOREIGN_OWNER')
        return _mapper_read_activation_v1(self.template(), self.identity, expected_raw=self.record_json, evidence_review=True)[0]


def _mapper_publish_occurrence_v1(template, *, candidate, entry):
    """Rebind physical versions once, after the original custody admission.

    Expected binary segments never change. This is not source acceptance and
    cannot admit a different result produced by an earlier command.
    """
    import threading
    from tools.run_validation_gates import _ValidationCandidateCustodyV1
    template = _mapper_binding_v1(template)
    if template['kind'] != 'MAPPER_NATIVE_READ_BINDING_V2':
        raise ValueError('MAPPER_ACTIVATION_REQUIRES_V2')
    if (type(candidate) is not _ValidationCandidateCustodyV1
            or candidate.active_occurrence != template['command_index']
            or entry is not candidate.plan[template['command_index'] - 1]
            or tuple(entry.argv) != tuple(template['parent_argv'])
            or str(candidate.root) != template['repo_root']
            or entry.run_id != template['run_id'] or entry.phase != template['phase']
            or len(candidate.plan) != template['command_count']):
        raise ValueError('MAPPER_ACTIVATION_ORIGINAL_CUSTODY_REQUIRED')
    candidate._check()
    attempted = getattr(candidate, '_mapper_activation_attempts_v1', None)
    if attempted is None:
        attempted = set(); candidate._mapper_activation_attempts_v1 = attempted
    index = template['command_index']
    if index in attempted: raise ValueError('MAPPER_ACTIVATION_NOT_RETRIED')
    attempted.add(index)
    limits = _mapper_activation_limits_v1(template)
    if limits['evidence_deadline_ns'] > candidate.deadline_ns:
        raise ValueError('MAPPER_ACTIVATION_EVIDENCE_EXCEEDS_ANCESTOR')
    # Readback + CLI/parent + optional child + finalizer; reserve even on failure.
    record_reads = 3 if template['child_argv'] is None else 4
    total_reads = _mapper_add_v1(_mapper_add_v1(limits['target_bytes'], limits['basis_bytes']),
                                record_reads * (limits['record_bytes'] + 1))
    if total_reads > candidate.remaining_read_bytes:
        raise ValueError('MAPPER_ACTIVATION_ANCESTOR_READ_ALLOWANCE')
    if limits['record_bytes'] >= candidate.snapshot_byte_limit:
        raise ValueError('MAPPER_ACTIVATION_ANCESTOR_RETAINED_ALLOWANCE')
    candidate.remaining_read_bytes -= total_reads
    candidate.snapshot_byte_limit -= limits['record_bytes']
    usage = {'files': 0, 'target_bytes': 0, 'basis_bytes': 0, 'metadata_calls': 0}
    # Failure usage remains on the existing candidate; failed work is not lost.
    ledger = getattr(candidate, '_mapper_activation_usage_v1', None)
    if ledger is None:
        ledger = {}; candidate._mapper_activation_usage_v1 = ledger
    ledger[index] = usage
    live = copy.deepcopy(template)
    live['basis']['generation'] = _mapper_occurrence_generation_v1(template)
    profile = live['basis']; root = Path(profile['root'])
    def observe(path=None, fd=None):
        candidate._check(); _scan_deadline(profile['deadline_ns'])
        if usage['metadata_calls'] >= limits['metadata_calls']:
            raise ValueError('MAPPER_ACTIVATION_METADATA_ALLOWANCE')
        usage['metadata_calls'] += 1
        result = os.fstat(fd) if fd is not None else os.lstat(path)
        _scan_deadline(profile['deadline_ns']); return result
    if _mapper_chain_v1(root, observe) != profile['root_chain']:
        raise ValueError('MAPPER_ACTIVATION_ROOT_REPLACED')
    for row in profile['entries']:
        original = candidate._occurrence_before.get(row['path'])
        if original is None or len(original[1]) != row['length']:
            raise ValueError('MAPPER_ACTIVATION_INPUT_OUTSIDE_CANDIDATE')
        path = root.joinpath(*row['path'].split('/'))
        if _mapper_chain_v1(path.parent, observe) != row['parent_chain']:
            raise ValueError('MAPPER_ACTIVATION_PARENT_REPLACED')
        before = _mapper_stamp_v1(observe(path))
        if before[2:4] != row['lstat'][2:4] or stat.S_IMODE(before[2]) != original[0]:
            raise ValueError('MAPPER_ACTIVATION_MODE_OR_LENGTH')
        fd = _open_regular_worktree_descriptor(path, nonblocking=True)
        errors = []
        try:
            opened = _mapper_stamp_v1(observe(fd=fd))
            if opened[:6] != before[:6]: raise ValueError('MAPPER_ACTIVATION_TARGET_SUBSTITUTED')
        except BaseException as exc: errors.append(exc)
        try: os.close(fd)
        except BaseException as exc: errors.append(exc)
        _scan_raise_errors(errors)
        if _mapper_stamp_v1(observe(path)) != before:
            raise ValueError('MAPPER_ACTIVATION_TARGET_CHANGED')
        row['lstat'], row['fstat'] = before, opened
    preflight = copy.deepcopy(profile)
    preflight['limits'] = {
        'attempts':len(profile['entries']), 'target_bytes':sum(x['length']+1 for x in profile['entries']),
        'basis_bytes':sum(x['length'] for x in profile['entries']),
        'metadata_calls':limits['metadata_calls'] - usage['metadata_calls'],
        'single_target_buffer':profile['limits']['single_target_buffer']}
    for row in preflight['entries']: row['attempt_limit'] = 1
    reader = None; errors = []
    try:
        reader = _MapperDiskBasisV1(preflight, expected_position=template['original_position'],
                                   expected_generation=profile['generation'], clock=time.monotonic_ns)
        for row in profile['entries']:
            candidate._check()
            reader.compare_bytes(row['path'])
            usage['files'] += 1
        # An early input may not change while later inputs are being compared.
        for row in profile['entries']:
            reader._chains(row)
            if reader._stamp(root.joinpath(*row['path'].split('/'))) != row['lstat']:
                raise ValueError('MAPPER_ACTIVATION_INPUT_CHANGED_AFTER_COMPARISON')
        reader._basis_current()
    except BaseException as exc:
        errors.append(exc)
        if reader is None:
            # Initializer metadata attempts are not externally observable here.
            # Never report the known prefix as an exact total after that failure.
            usage['metadata_calls'] = None
    if reader is not None:
        usage['target_bytes'] = reader.counters['target_bytes']
        usage['basis_bytes'] = reader.counters['basis_bytes']
        usage['metadata_calls'] += reader.counters['metadata_calls']
        try: reader.close()
        except BaseException as exc: errors.append(exc)
    _scan_raise_errors(errors)
    candidate._check(); _scan_deadline(profile['deadline_ns'])
    record = {'kind':'MAPPER_OCCURRENCE_ACTIVATION_V1','binding':live,'observed':dict(usage)}
    _mapper_activation_record_v1(template, record)
    raw = json.dumps(record, ensure_ascii=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    if len(raw) > limits['record_bytes']: raise ValueError('MAPPER_ACTIVATION_RECORD_TOO_LARGE')
    path = _mapper_activation_path_v1(template)
    _local_unlinked_path(path.parent); parents = _mapper_chain_v1(path.parent)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os,'O_BINARY',0), 0o600)
    errors = []
    try:
        view = memoryview(raw)
        while view:
            candidate._check(); _scan_deadline(profile['deadline_ns'])
            n = os.write(fd, view)
            if type(n) is not int or not 0 < n <= len(view): raise OSError('invalid activation write progress')
            view = view[n:]
        os.fsync(fd)
        final = _mapper_stamp_v1(os.fstat(fd))
        if final[:6] != _mapper_stamp_v1(path.lstat())[:6]:
            raise ValueError('MAPPER_ACTIVATION_PUBLICATION_SUBSTITUTED')
    except BaseException as exc: errors.append(exc)
    try: os.close(fd)
    except BaseException as exc: errors.append(exc)
    _scan_raise_errors(errors)
    if _mapper_chain_v1(path.parent) != parents:
        raise ValueError('MAPPER_ACTIVATION_PUBLICATION_PARENT_CHANGED')
    identity = json.dumps(_mapper_stamp_v1(path.lstat()), separators=(',', ':'))
    result = _MapperOccurrenceRecordV1(
        json.dumps(template, ensure_ascii=True, separators=(',', ':'), allow_nan=False).encode('utf-8'),
        raw, identity, os.getpid(), threading.get_ident())
    result.verify()
    candidate._check(); _scan_deadline(profile['deadline_ns'])
    return result


def _mapper_occurrence_evidence_v1(paths, templates, records, receipts):
    """Check the exact activation prefix before final success, without rebinding."""
    if records is None: records = {}
    if type(records) is not dict:
        raise _evidence_failure('invalid mapper activation custody')
    templates = {} if templates is None else _mapper_plain_v1(templates)
    expected = {str(receipt.command_index) for receipt in receipts
                if str(receipt.command_index) in templates
                and templates[str(receipt.command_index)]['kind'] == 'MAPPER_NATIVE_READ_BINDING_V2'}
    if set(records) != expected:
        raise _evidence_failure('mapper activation records differ from executed prefix')
    actual = {p.name for p in paths.evidence_root.iterdir() if p.name.startswith('mapper-read-')}
    wanted = {'mapper-read-' + k + '.json' for k in expected}
    if actual != wanted:
        raise _evidence_failure('mapper activation file roster differs')
    for key, record in records.items():
        if type(record) is not _MapperOccurrenceRecordV1 or record.template() != templates[key]:
            raise _evidence_failure('mapper activation lost its original template')
        try: record.verify()
        except (ValueError, OSError, RuntimeError) as exc:
            raise _evidence_failure('mapper activation evidence changed: ' + str(exc)) from exc
        receipt = next(x for x in receipts if str(x.command_index) == key)
        if (_MAPPER_ACTIVATION_ENV_V1, record.identity) not in receipt.fixed_environment_controls:
            raise _evidence_failure('mapper activation missing from original process receipt')


# The following definitions are integrated into tools/validation_reliability.py.
_MAPPER_READ_ENV_KEYS_V1 = (
    'QTT_MAPPER_READ_INDEX', 'QTT_MAPPER_READ_PHASE', 'QTT_MAPPER_READ_COUNT',
    'QTT_MAPPER_RUN_BYTES', 'QTT_MAPPER_RUN_NODES', 'QTT_MAPPER_RUN_DEPTH',
    'QTT_MAPPER_RUN_PROFILES', 'QTT_MAPPER_READ_DEADLINE',
)
_MAPPER_PYTEST_BOOTSTRAP_V1 = (
    'from tools.run_pytest_fresh_basetemp import _mapper_pytest_main_v1; '
    'raise SystemExit(_mapper_pytest_main_v1())'
)


def _mapper_plain_v1(value):
    if isinstance(value, Mapping):
        return {key: _mapper_plain_v1(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [_mapper_plain_v1(item) for item in value]
    if type(value) in (str, int, bool, float, type(None)):
        return value
    raise ValueError('MAPPER_NON_DATA_PROFILE')


def _mapper_original_position_v1(argv, repo_root):
    if type(argv) is not tuple or not argv or any(type(v) is not str for v in argv):
        raise ValueError('MAPPER_ORIGINAL_ARGV')
    offset = 1
    while offset < len(argv) and argv[offset] in ('-B', '-I', '-u'):
        offset += 1
    if offset >= len(argv):
        return None
    for position, family, script, pytest_scope in _REPORT_READ_ROUTES_V1:
        if script is None:
            continue
        cli = Path(script)
        if Path(argv[offset]) in (cli, Path(repo_root)/cli):
            if argv[offset+1:] not in ((), ('--repo-root', str(repo_root)), ('--repo-root', '.')):
                raise ValueError('MAPPER_CLI_SCOPE')
            return position
    args = _mapper_nested_pytest_args_v1(argv, Path(repo_root))
    if args is None:
        return None
    from tools.run_pytest_fresh_basetemp import _split_pytest_options_v1
    retained, _, _ = _split_pytest_options_v1(args)
    return next(row[0] for row in _REPORT_READ_ROUTES_V1 if row[3] == tuple(retained))


def _mapper_child_command_v1(parent, repo_root, process_root):
    args = _mapper_nested_pytest_args_v1(tuple(parent), Path(repo_root))
    if args is None:
        raise ValueError('MAPPER_PYTEST_PARENT_REQUIRED')
    from tools.run_pytest_fresh_basetemp import _split_pytest_options_v1
    prefix, literals, explicit = _split_pytest_options_v1(args)
    if literals or explicit != str(Path(process_root)/'p'):
        raise ValueError('MAPPER_CHILD_BASETEMP')
    # Pure projection: final provenance comparison can occur after owned process
    # directories have been cleaned. Live path admission stays at dispatch.
    arguments = ('-c', str(Path(repo_root)/'pytest.ini'), '-o', 'addopts=',
        '-o', 'cache_dir=' + str(Path(process_root)/'pytest-cache'),
        '--rootdir=' + str(repo_root), '--confcutdir=' + str(repo_root),
        *prefix, '--basetemp', str(Path(process_root)/'p'))
    return (parent[0], '-B', '-c', _MAPPER_PYTEST_BOOTSTRAP_V1, *arguments)


def _mapper_binding_v1(value):
    value = _mapper_plain_v1(value)
    fields = {'kind', 'run_id', 'phase', 'command_index', 'command_count',
              'original_position', 'repo_root', 'process_root', 'evidence_root',
              'parent_argv', 'child_argv', 'run_read_limits', 'basis'}
    if type(value) is dict and value.get('kind') == 'MAPPER_NATIVE_READ_BINDING_V2':
        fields.add('activation_limits')
    if (type(value) is not dict or set(value) != fields
            or value['kind'] not in ('MAPPER_NATIVE_READ_BINDING_V1', 'MAPPER_NATIVE_READ_BINDING_V2')):
        raise ValueError('MAPPER_BINDING_FIELDS')
    for key in ('run_id', 'phase'):
        if type(value[key]) is not str or not value[key] or '\0' in value[key]:
            raise ValueError('MAPPER_BINDING_TEXT')
    for key in ('command_index', 'command_count', 'original_position'):
        _mapper_int_v1(value[key], key, positive=True)
    if value['command_index'] > value['command_count']:
        raise ValueError('MAPPER_BINDING_INDEX')
    for key in ('repo_root', 'process_root', 'evidence_root'):
        _mapper_absolute_v1(value[key])
    parent = value['parent_argv']
    if type(parent) is not list or not parent or any(type(x) is not str for x in parent) or not Path(parent[0]).is_absolute():
        raise ValueError('MAPPER_BINDING_PARENT')
    position = _mapper_original_position_v1(tuple(parent), Path(value['repo_root']))
    if position is None or position != value['original_position']:
        raise ValueError('MAPPER_BINDING_POSITION')
    child = value['child_argv']
    if position in tuple(row[0] for row in _REPORT_READ_ROUTES_V1 if row[2] is not None):
        if child is not None:
            raise ValueError('MAPPER_CLI_CANNOT_DELEGATE')
    elif type(child) is not list or tuple(child) != _mapper_child_command_v1(parent, value['repo_root'], value['process_root']):
        raise ValueError('MAPPER_BINDING_CHILD')
    limits = value['run_read_limits']
    if type(limits) is not dict or set(limits) != set(_ScanRunReadLimits.__dataclass_fields__):
        raise ValueError('MAPPER_RUN_LIMIT_FIELDS')
    for key, item in limits.items():
        _mapper_int_v1(item, key, positive=True)
    _mapper_profile_v1(value['basis'])
    if value['basis']['position'] != position or value['basis']['root'] != value['repo_root']:
        raise ValueError('MAPPER_BINDING_BASIS_IDENTITY')
    if value['kind'] == 'MAPPER_NATIVE_READ_BINDING_V2':
        _mapper_activation_limits_v1(value)
    # A mapper profile never changes the scanner wire version or scanner role.
    return value


def _mapper_profiles_projection_v1(profiles, *, run_id, phase, command_count, paths):
    if not isinstance(profiles, Mapping) or not profiles or len(profiles) > len(_REPORT_READ_ROUTES_V1):
        raise ValueError('MAPPER_PROFILE_TABLE')
    result = {}
    for key, item in profiles.items():
        if type(key) is not str or re.fullmatch(r'[1-9][0-9]*', key) is None:
            raise ValueError('MAPPER_PROFILE_KEY')
        binding = _mapper_binding_v1(item)
        if (str(binding['command_index']) != key or binding['run_id'] != run_id
                or binding['phase'] != phase or binding['command_count'] != command_count):
            raise ValueError('MAPPER_PROFILE_RUN_IDENTITY')
        for name in ('repo_root', 'process_root', 'evidence_root'):
            expected = paths[name] if isinstance(paths, Mapping) else getattr(paths, name)
            if binding[name] != str(expected):
                raise ValueError('MAPPER_PROFILE_PATH_IDENTITY')
        result[key] = binding
    if len({b['original_position'] for b in result.values()}) != len(result):
        raise ValueError('MAPPER_DUPLICATE_ORIGINAL_POSITION')
    return result


def _mapper_strip_run_extension_v1(value):
    if 'mapper_read_profiles' not in value:
        return value
    _mapper_profiles_projection_v1(value['mapper_read_profiles'], run_id=value.get('run_id'),
        phase=value.get('phase'), command_count=value.get('command_count'), paths=value.get('paths'))
    # Only this validated, named optional extension is stripped. Unknown keys
    # remain for the existing exact-field reader to reject.
    return MappingProxyType({k:v for k,v in value.items() if k != 'mapper_read_profiles'})


def _mapper_read_controls_v1(binding):
    b = _mapper_binding_v1(binding)
    limits = b['run_read_limits']
    values = (b['command_index'], b['phase'], b['command_count'], limits['byte_limit'],
              limits['node_limit'], limits['depth_limit'], limits['profile_limit'], b['basis']['deadline_ns'])
    return (*zip(_MAPPER_READ_ENV_KEYS_V1, map(str, values)), (PROCESS_ROOT_ENV, b['process_root']))


def _mapper_read_profile_for_process_v1(repo_root, *, environment, actual_argv, role):
    if role not in ('PARENT', 'CHILD'):
        raise ValueError('MAPPER_PROCESS_ROLE')
    env = {}
    for key, value in environment.items():
        if type(key) is not str or type(value) is not str or key.upper() in env:
            raise ValueError('MAPPER_ENVIRONMENT_ALIAS')
        env[key.upper()] = value
    unknown = ({key for key in env if key.startswith('QTT_MAPPER_')} - set(_MAPPER_READ_ENV_KEYS_V1)
               - set(_MAPPER_DEADLINE_ENV_KEYS) - {_MAPPER_ACTIVATION_ENV_V1})
    if unknown:
        raise ValueError('MAPPER_UNKNOWN_CONTROL')
    values = []
    for key in _MAPPER_READ_ENV_KEYS_V1:
        item = env.get(key)
        if type(item) is not str or not item or (key != 'QTT_MAPPER_READ_PHASE' and re.fullmatch(r'[1-9][0-9]*', item) is None):
            raise ValueError('MAPPER_MISSING_OR_INVALID_CONTROL:' + key)
        if key != 'QTT_MAPPER_READ_PHASE' and len(item) > 19:
            raise ValueError('MAPPER_CONTROL_INTEGER_EXTENT')
        values.append(item if key == 'QTT_MAPPER_READ_PHASE' else _mapper_int_v1(int(item), key, positive=True))
    index, phase, count, size, nodes, depth, profiles, deadline = values
    for key in (RUN_ID_ENV, PROCESS_ROOT_ENV, EVIDENCE_ROOT_ENV):
        if not env.get(key):
            raise ValueError('MAPPER_MISSING_RUN_CONTEXT:' + key)
    attestation = attest_inherited_validation_run(Path(repo_root), inherited_run_id=env[RUN_ID_ENV],
        inherited_evidence_root=Path(env[EVIDENCE_ROOT_ENV]), explicit_basetemp=Path(env[PROCESS_ROOT_ENV])/'p',
        scan_read_limits=_ScanRunReadLimits(size,nodes,depth,profiles), scan_deadline_ns=deadline)
    value = attestation._scan_snapshot.value
    base_fields = {'schema_version','run_id','phase','command_count','text_integrity_preflight_state','paths','filesystem_probe'}
    optional = {'rp5a_scan_profiles','rp5a_reader_profiles','rp5a_reader_bases','rp5a_launch_wire_version',
                'rp5a_launch_wire_versions','rp5a_payload_byte_limits'}
    if not base_fields <= set(value) or set(value)-base_fields-optional != {'mapper_read_profiles'}:
        raise ValueError('MAPPER_RUN_FIELDS')
    if type(value.get('schema_version')) is not int or value['schema_version'] != SCHEMA_VERSION:
        raise ValueError('MAPPER_RUN_VERSION')
    if value['phase'] != phase or type(value['command_count']) is not int or value['command_count'] != count:
        raise ValueError('MAPPER_RUN_ASSOCIATION')
    table = _mapper_profiles_projection_v1(value['mapper_read_profiles'],run_id=env[RUN_ID_ENV],phase=phase,command_count=count,paths=value['paths'])
    if len(table) > profiles or str(index) not in table:
        raise ValueError('MAPPER_SELECTED_PROFILE_MISSING')
    binding = table[str(index)]
    expected_controls = dict(_mapper_read_controls_v1(binding))
    if expected_controls != {k:env.get(k) for k in expected_controls}:
        raise ValueError('MAPPER_CONTROL_PROFILE_DRIFT')
    if str(attestation.process_root) != env[PROCESS_ROOT_ENV] or binding['repo_root'] != str(repo_root):
        raise ValueError('MAPPER_PROCESS_ROOT_DRIFT')
    expected = binding['parent_argv'] if role == 'PARENT' else binding['child_argv']
    if expected is None or type(actual_argv) is not tuple or actual_argv != tuple(expected):
        raise ValueError('MAPPER_ACTUAL_ARGV_DRIFT')
    if binding['kind'] == 'MAPPER_NATIVE_READ_BINDING_V2':
        binding, _ = _mapper_read_activation_v1(binding, env.get(_MAPPER_ACTIVATION_ENV_V1))
    elif _MAPPER_ACTIVATION_ENV_V1 in env:
        raise ValueError('MAPPER_LEGACY_BINDING_CANNOT_USE_ACTIVATION')
    return attestation, binding


@contextmanager
def _mapper_bound_reads_v1(binding):
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import serialization
    b = _mapper_binding_v1(binding)
    family = next(row[1] for row in _REPORT_READ_ROUTES_V1 if row[0] == b['original_position'])
    reader = _MapperDiskBasisV1(b['basis'], expected_position=b['original_position'],
        expected_generation=b['basis']['generation'], clock=time.monotonic_ns)
    if not _MAPPER_READ_LOCK_V1.acquire(blocking=False):
        reader.close()
        raise ValueError('MAPPER_CONCURRENT_BINDING')
    primary = None
    installed = False
    try:
        if serialization._REPORT_READ_BINDING_V1 is not None:
            raise ValueError('MAPPER_REENTRANT_BINDING')
        serialization._REPORT_READ_BINDING_V1 = (family, reader)
        installed = True
        yield reader
    except BaseException as exc:
        primary = exc
        raise
    finally:
        if installed:
            serialization._REPORT_READ_BINDING_V1 = None
        try:
            reader.close()
        except BaseException as close_error:
            if primary is not None:
                raise BaseExceptionGroup('mapper use and close failed', [primary, close_error])
            raise
        finally:
            _MAPPER_READ_LOCK_V1.release()


_MAPPER_READ_LOCK_V1 = threading.Lock()


# Complete definitions proposed for tools/validation_reliability.py. Existing
# error, native opener and porcelain parser owners are reused, not replaced.

def _scope_git_text(repo_root: Path, args: Sequence[str]) -> tuple[int, str, str]:
    """Reuse the existing root-discovered, no-fetch/no-hook Git process owner."""
    from tools.ci_branch_context import _run_validation_scope_read
    completed = _run_validation_scope_read(repo_root, args)
    return completed.returncode, completed.stdout, completed.stderr


def _scope_git_path(path: str) -> str:
    """Reject unrepresentable identities; never trim/unquote a native pathname."""
    if type(path) is not str or not path or path != path.strip():
        raise ValueError("invalid or whitespace-aliased Git path")
    if "\\" in path or ":" in path or any(ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF for c in path):
        raise ValueError("Git path is not a portable exact repository identity")
    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("Git path is not an exact relative repository identity")
    return path


def _scope_nul_paths(raw: str) -> tuple[str, ...]:
    if type(raw) is not str:
        raise ValueError("scope pathname stream must be decoded text")
    if not raw:
        return ()
    if not raw.endswith("\0"):
        raise ValueError("scope pathname stream is not NUL-terminated")
    paths = tuple(_scope_git_path(p) for p in raw[:-1].split("\0"))
    if len(paths) != len(set(paths)) or len({p.casefold() for p in paths}) != len(paths):
        raise ValueError("duplicate path in a single complete Git diff stream")
    return paths


def _scope_required_query(repo_root: Path, args: Sequence[str], git_stdout) -> str:
    result = git_stdout(repo_root, args)
    if type(result) is not tuple or len(result) != 3:
        raise ValidationReliabilityError("ENGVR_PREPUBLICATION_CUSTODY_FAILED", "invalid Git query result shape")
    code, stdout, stderr = result
    if type(code) is not int or type(stdout) is not str or type(stderr) is not str:
        raise ValidationReliabilityError("ENGVR_PREPUBLICATION_CUSTODY_FAILED", "invalid native Git exit/stream types")
    if code != 0:
        raise ValidationReliabilityError(
            "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
            f"required Git scope query failed: {tuple(args)!r}; exit={code}; stderr={stderr!r}",
        )
    return stdout


def _scope_git_committed_paths(
    repo_root: Path, *, base_ref: str | None = None,
    head_ref: str | None = None, git_stdout=None,
) -> tuple[str, ...]:
    query = _scope_git_text if git_stdout is None else git_stdout
    base = "refs/remotes/origin/main" if base_ref is None else base_ref
    head = "HEAD" if head_ref is None else head_ref
    for ref in (base, head):
        if type(ref) is not str or not ref or ref.startswith("-") or any(c in ref for c in "\0\r\n"):
            raise ValidationReliabilityError("ENGVR_REMOTE_STATE_DRIFT", "invalid exact comparison reference")
    merge_raw = _scope_required_query(repo_root, ("merge-base", "--all", base, head), query)
    merge_base = merge_raw.rstrip("\r\n")
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", merge_base):
        raise ValidationReliabilityError("ENGVR_REMOTE_STATE_DRIFT", "missing or ambiguous native merge-base identity")
    raw_diff = _scope_required_query(
        repo_root,
        ("diff", "--name-only", "-z", "--no-renames", "--no-ext-diff", "--no-textconv", "--ignore-submodules=none", merge_base, head, "--"),
        query,
    )
    try:
        return _scope_nul_paths(raw_diff)
    except ValueError as exc:
        raise ValidationReliabilityError("ENGVR_PREPUBLICATION_CUSTODY_FAILED", str(exc)) from exc


def _scope_git_change_snapshot(
    repo_root: Path, *, base_ref: str | None = None,
    head_ref: str | None = None, git_stdout=None,
) -> tuple[tuple[str, ...], tuple[tuple[str, str, str | None], ...]]:
    """Complete branch delta plus worktree/index/untracked identities, never a grant.

    Caller binds accepted source/root/reference generations and custody.
    Required-query failure never falls back to another comparison.
    """
    query = _scope_git_text if git_stdout is None else git_stdout
    committed = _scope_git_committed_paths(
        repo_root, base_ref=base_ref, head_ref=head_ref, git_stdout=query)
    raw_status = _scope_required_query(
        repo_root,
        ("status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignore-submodules=none"),
        query,
    )
    try:
        records = parse_git_status_porcelain_v1_z(raw_status)
        destinations = set()
        for code, destination, original in records:
            _scope_git_path(destination)
            if destination in destinations or code == "!!":
                raise ValueError("duplicate or unrequested ignored status entry")
            destinations.add(destination)
            if original is not None:
                _scope_git_path(original)
    except ValueError as exc:
        raise ValidationReliabilityError("ENGVR_PREPUBLICATION_CUSTODY_FAILED", str(exc)) from exc
    all_paths = set(committed)
    for _code, destination, original in records:
        all_paths.add(destination)
        if original is not None:
            all_paths.add(original)
    if len({p.casefold() for p in all_paths}) != len(all_paths):
        raise ValidationReliabilityError("ENGVR_PREPUBLICATION_CUSTODY_FAILED", "case-colliding Git identities")
    return committed, records



# First-phase observations share the existing custody and native process owner.
# None of these logical counters establishes a native host resource grant.
_PREFLIGHT_OBSERVATION_V1 = ContextVar("_PREFLIGHT_OBSERVATION_V1", default=None)
_PREFLIGHT_SCRIPTS_V1 = (
    "tools/validate_grand_global_debug_logical_consistency_audit.py",
    "tools/validate_ci_branch_context_matrix.py",
    "tools/validate_repair_pr_changed_file_scope.py",
    "tools/validate_nested_validator_contracts.py",
    "tools/validate_validation_inventory.py",
    "tools/validate_validation_scope_registry.py",
    "tools/changed_area_validation_router.py",
    "tools/cross_platform_path_invariant.py",
)


def _preflight_vector_v1(argv):
    if type(argv) is not tuple or len(argv) < 2 or any(type(value) is not str for value in argv):
        return False
    script = argv[1].replace("\\", "/")
    if script not in _PREFLIGHT_SCRIPTS_V1:
        return False
    tail = () if script == _PREFLIGHT_SCRIPTS_V1[5] else ("--repo-root", ".")
    return argv[2:] == tail


def _preflight_stamp_v1(info):
    directory = stat.S_ISDIR(info.st_mode)
    identity = tuple(_mapper_stamp_v1(info, directory=directory))
    return identity + ((info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_nlink) if directory else ())


def _preflight_chain_v1(path, *, optional=False):
    result = []
    for parent in (*reversed(path.parents), path):
        try:
            info = parent.lstat()
        except FileNotFoundError:
            if not optional:
                raise
            result.append((str(parent), None))
            break
        if not stat.S_ISDIR(info.st_mode) or _stat_is_reparse_point(info):
            raise ValidationReliabilityError("ENGVR_PREPUBLICATION_CUSTODY_FAILED", f"unsupported ancestor: {parent}")
        result.append((str(parent), _preflight_stamp_v1(info)))
    return tuple(result)


class _PreflightObservationV1:
    """One original occurrence's supplied immutable basis and logical allowance.

    The environment/custody owner supplies these inputs. Construction is neither
    semantic acceptance nor proof of exclusivity, bootstrap trust or containment.
    """
    def __init__(self, *, root, run_id, occurrence, argv, files, directories,
                 limits, deadline_ns, git_executable=None, evidence_root=None, native_basis=None):
        keys = {"attempts", "bytes", "entries", "retained_bytes", "git_attempts",
                "stdout_bytes", "stderr_bytes", "combined_output_bytes"}
        if (type(limits) is not dict or set(limits) != keys
                or any(type(k) is not str for k in limits)
                or any(type(v) is not int or v < 0 for v in limits.values())
                or type(deadline_ns) is not int or deadline_ns <= 0
                or type(run_id) is not str or not run_id
                or type(occurrence) is not int or not 1 <= occurrence <= 8
                or not _preflight_vector_v1(argv) or argv[1].replace("\\", "/") != _PREFLIGHT_SCRIPTS_V1[occurrence - 1]
                or type(files) is not dict or type(directories) is not dict):
            raise ValueError("exact original preflight association and finite inputs required")
        if native_basis is not None:
            _preflight_require_v1(type(native_basis) is _LinuxImmutableSourceBasisV2 and
                native_basis.root == Path(root).absolute(), 'LINUX_V2_OBSERVATION_BASIS')
            native_basis.check_live()
            _preflight_require_v1(all(native_basis.files.get(k)==v and v[1]=='WORKTREE' for k,v in files.items()),
                'LINUX_V2_OBSERVATION_SELECTION')
        if any(type(k) is not str or (type(v) is not bytes if native_basis is None else type(v) is not tuple) for k, v in files.items()):
            raise ValueError("immutable expected file bytes required")
        if any(type(k) is not str or type(v) is not tuple
               or any(type(item) is not tuple or len(item) != 2
                      or type(item[0]) is not str or item[1] not in ("file", "directory") for item in v)
               for k, v in directories.items()):
            raise ValueError("complete directory name/type observations required")
        for roster in directories.values():
            names = [item[0] for item in roster]
            if (len(names) != len(set(names)) or any(not name or Path(name).name != name
                    or name in (".", "..") or "\\" in name or "/" in name or "\0" in name for name in names)):
                raise ValueError("distinct immediate directory names required")
        self.root = Path(root).absolute()
        self.run_id, self.occurrence, self.argv = run_id, occurrence, argv
        self.files = MappingProxyType(dict(files))
        self.directories = MappingProxyType(dict(directories))
        for name in (*files, *directories):
            if name != ".":
                _scope_git_path(name)
        self.remaining = dict(limits)
        self.observed = dict.fromkeys(limits, 0)
        self.reserved = dict.fromkeys(limits, 0)
        self.retained_entries = 0
        self.failure, self.measurement_complete = None, True
        self.deadline_ns, self.last_clock = deadline_ns, -1
        self.pid, self.thread = os.getpid(), threading.get_ident()
        self.git_executable, self.evidence_root = git_executable, evidence_root
        self.git_receipts = []
        self._startup_catalog = None
        self.native_basis = native_basis
        self.native_read_observation = None if native_basis is None else dict(manifest_acquired_bytes=0,
            manifest_retained_bytes=0,source_bytes_read=0,owned_evidence_bytes_read=0)

    def fail(self, detail):
        if self.failure is None:
            self.failure = ValidationReliabilityError("ENGVR_PREPUBLICATION_CUSTODY_FAILED", str(detail))
            if isinstance(detail, BaseException):
                self.failure.__cause__ = detail
                for name in ("owned_process", "command_process", "command_receipt"):
                    if hasattr(detail, name):
                        setattr(self.failure, name, getattr(detail, name))
        raise self.failure

    def check(self):
        if self.failure is not None:
            raise self.failure
        now = time.monotonic_ns()
        if (type(now) is not int or now < self.last_clock or now >= self.deadline_ns
                or self.pid != os.getpid() or self.thread != threading.get_ident()):
            self.fail("preflight deadline/clock/process association failed")
        self.last_clock = now
        if self.native_basis is not None: self.native_basis.check_live()

    def reserve(self, key, amount=1):
        self.check()
        if type(amount) is not int or amount < 0 or amount > self.remaining[key]:
            self.fail("preflight reservation exhausted: " + key)
        self.remaining[key] -= amount
        self.reserved[key] += amount
        if key in ("attempts", "git_attempts"):
            self.observed[key] += amount

    def received(self, key, amount):
        if type(amount) is not int or amount < 0:
            self.measurement_complete = False
            self.fail("unmeasured preflight delivery: " + key)
        previous = self.remaining[key]
        self.observed[key] += amount
        self.remaining[key] = max(0, previous - amount)
        if amount > previous:
            self.fail("preflight delivery exceeded: " + key)
        self.check()

    def relative(self, path):
        self.check()
        path = Path(path).absolute()
        if ".." in path.parts or not path.is_relative_to(self.root):
            self.fail("preflight path/root mismatch: " + str(path))
        return path.relative_to(self.root).as_posix()


@contextmanager
def _preflight_observation_v1(value, *, run_id, occurrence, argv, root):
    if (type(value) is not _PreflightObservationV1 or value.run_id != run_id
            or type(occurrence) is not int or value.occurrence != occurrence
            or value.argv != argv or value.root != Path(root).absolute()
            or _PREFLIGHT_OBSERVATION_V1.get() is not None):
        raise ValueError("preflight context lost original run/occurrence/root")
    value.check()
    token = _PREFLIGHT_OBSERVATION_V1.set(value)
    try:
        yield value
        value.check()
    finally:
        _PREFLIGHT_OBSERVATION_V1.reset(token)


def _preflight_active_v1(root=None):
    value = _PREFLIGHT_OBSERVATION_V1.get()
    selected = os.environ.get(RUN_ID_ENV) and any(
        str(sys.argv[0]).replace("\\", "/").endswith(script) for script in _PREFLIGHT_SCRIPTS_V1)
    if value is not None:
        value.check()
        if selected and (value.run_id != os.environ[RUN_ID_ENV]
                         or value.argv != (sys.executable, *sys.argv)
                         or value.root != Path.cwd()
                         or value.root != Path(__file__).resolve().parents[1]):
            value.fail("active canonical preflight lost actual run/vector/module/cwd association")
        if root is not None and Path(root).absolute() != value.root:
            value.fail("preflight module/argument root mismatch")
    elif selected:
        raise ValidationReliabilityError("ENGVR_PREPUBLICATION_CUSTODY_FAILED",
                                        "selected preflight has no original observation binding")
    return value


def _preflight_failure_v1(value, exc):
    if value is not None:
        value.fail(exc)
    if isinstance(exc, ValidationReliabilityError):
        raise exc
    raise ValidationReliabilityError("ENGVR_PREPUBLICATION_CUSTODY_FAILED", f"{type(exc).__name__}: {exc}") from exc


def _preflight_startup_path_v1(name, path_type=Path):
    """Pure spelling check; physical custody still belongs to each acquisition."""
    from pathlib import PureWindowsPath
    import ntpath
    if (type(name) is not str or not name
            or any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in name)):
        raise ValueError("exact startup pathname string required")
    path = path_type(name)
    if (not path.is_absolute() or str(path) != name
            or any(part in (".", "..") for part in name.replace("\\", "/").split("/"))):
        raise ValueError("noncanonical startup pathname: " + name)
    if isinstance(path, PureWindowsPath):
        if ntpath.isreserved(name) or name.startswith(("\\\\?\\", "\\\\.\\")):
            raise ValueError("aliased startup pathname: " + name)
    elif "\\" in name:
        raise ValueError("nonportable startup pathname: " + name)
    return name


@contextmanager
def _preflight_startup_access_v1(observation, startup_basis):
    """Install an exact data catalog on the existing, active I/O owner only."""
    if type(observation) is not _PreflightObservationV1:
        raise ValueError("original startup observation required")
    previous = observation._startup_catalog
    installed = False
    try:
        if _preflight_active_v1() is not observation or previous is not None:
            raise ValueError("startup access requires the exact active observation without reentry")
        observation.check()
        observation.reserve("attempts")
        if (type(startup_basis) is not dict or len(startup_basis) != 3
                or any(type(k) is not str for k in startup_basis)
                or set(startup_basis) != {"files", "directories", "absent"}):
            raise ValueError("exact startup catalog fields required")
        files, directories, absent = (startup_basis[k] for k in ("files", "directories", "absent"))
        if type(files) is not dict or type(directories) is not dict or type(absent) is not tuple:
            raise ValueError("exact startup catalog containers required")
        # Bound declared cardinality before copying mappings or constructing
        # indexes. These are logical entries/content retention, not heap/RAM.
        entries = len(files) + len(directories) + len(absent)
        for roster in directories.values():
            if type(roster) is not tuple:
                raise ValueError("immutable startup directory roster required")
            entries += len(roster)
        if entries > observation.remaining["entries"]:
            raise ValueError("startup catalog entry capacity unavailable")
        retained = 0
        for raw in files.values():
            if type(raw) is not bytes:
                raise ValueError("exact startup expected bytes required")
            retained += len(raw)
        observation.reserve("entries", entries)
        observation.reserve("retained_bytes", retained)
        frozen_files, frozen_directories, frozen_absent = dict(files), dict(directories), tuple(absent)
        observation.retained_entries += entries
        observation.observed["retained_bytes"] += retained
        identities = set()
        for collection in (frozen_files, frozen_directories, frozen_absent):
            for name in collection:
                _preflight_startup_path_v1(name)
                key = name.casefold()
                if key in identities:
                    raise ValueError("duplicate, case-aliased or contradictory startup status: " + name)
                identities.add(key)
        for parent, roster in frozen_directories.items():
            names = set()
            for item in roster:
                if (type(item) is not tuple or len(item) != 2 or type(item[0]) is not str
                        or type(item[1]) is not str or item[1] not in ("file", "directory")):
                    raise ValueError("exact startup directory name/kind pair required")
                name, kind = item
                if (not name or name in (".", "..") or "/" in name or "\\" in name
                        or name.casefold() in names):
                    raise ValueError("distinct immediate startup directory names required")
                child = _preflight_startup_path_v1(str(Path(parent) / name))
                names.add(name.casefold())
                if (child in frozen_absent or child in frozen_files and kind != "file"
                        or child in frozen_directories and kind != "directory"):
                    raise ValueError("startup roster contradicts declared status")
                # Reject cross-catalog case aliases even when a directory alone
                # could have named the same physical child on this platform.
                if child.casefold() in identities and not any(child in c for c in
                        (frozen_files, frozen_directories, frozen_absent)):
                    raise ValueError("startup roster aliases a catalog pathname")
        for collection, kind in ((frozen_files, "file"), (frozen_directories, "directory"), (frozen_absent, None)):
            for name in collection:
                path = Path(name)
                parent = str(path.parent)
                if parent in frozen_directories:
                    observed_kind = next((k for n, k in frozen_directories[parent] if n == path.name), None)
                    if observed_kind != kind:
                        raise ValueError("startup declaration contradicts its complete parent roster")
                if path.is_relative_to(observation.root):
                    relative = path.relative_to(observation.root).as_posix()
                    if relative in observation.files and (kind != "file" or observation.native_basis is None
                            and frozen_files[name] != observation.files[relative]):
                        raise ValueError("startup declaration contradicts repository file facts")
                    if relative in observation.directories and (kind != "directory" or frozen_directories[name] != observation.directories[relative]):
                        raise ValueError("startup declaration contradicts repository directory facts")
        if (len(identities) + sum(map(len, frozen_directories.values())) != entries
                or sum(map(len, frozen_files.values())) != retained):
            raise ValueError("startup catalog changed during acquisition")
        observation._startup_catalog = (MappingProxyType(frozen_files), MappingProxyType(frozen_directories), frozen_absent)
        installed = True
        observation.check()
        yield
        observation.check()
    except BaseException as exc:
        _preflight_failure_v1(observation, exc)
    finally:
        if installed:
            observation._startup_catalog = previous


def _preflight_operand_v1(value, path, operation, *, evidence=False):
    """Select a basis before the shared reader/status/enumerator performs I/O."""
    if value._startup_catalog is not None:
        if evidence:
            value.fail("startup access cannot read native Git evidence")
        name = _preflight_startup_path_v1(str(path))
        files, directories, absent = value._startup_catalog
        if operation == "file" and name in files:
            return files[name]
        if operation == "directory" and name in directories:
            return directories[name]
        if operation == "kind":
            if name in files:
                return "file"
            if name in directories:
                return "directory"
            if name in absent:
                return None
        value.fail("undeclared startup " + operation + " operand: " + name)
    if evidence:
        allowed = {Path(p).absolute() for receipt in value.git_receipts
                   for p in (receipt.stdout_path, receipt.stderr_path)}
        if path not in allowed:
            value.fail("unowned Git evidence readback")
        return None
    name = value.relative(path)
    if operation == "kind":
        if value.native_basis is not None:
            _preflight_require_v1(bool(value.directories) and (not name.startswith('.git/') or name in value.files),
                'LINUX_V2_UNSELECTED_KIND_OPERAND')
        return None
    basis = value.files if operation == "file" else value.directories
    if name not in basis:
        value.fail("missing preflight " + operation + " basis: " + name)
    if operation == "file" and value.native_basis is not None:
        value.native_basis.check_live()
        return None
    return basis[name]

def _preflight_kind_v1(path, *, optional=False):
    value = _preflight_active_v1()
    path = Path(path).absolute()
    try:
        if value is None:
            # Preserve unselected legacy diagnostics without promoting them to
            # original-run custody. Unlike exists/is_file, errors are not absence.
            try:
                info = path.lstat()
            except FileNotFoundError:
                if optional:
                    return None
                raise
            if _stat_is_reparse_point(info) or stat.S_ISLNK(info.st_mode):
                raise ValueError("linked diagnostic path: " + str(path))
            if stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
                return "file"
            if stat.S_ISDIR(info.st_mode):
                return "directory"
            raise ValueError("unsupported diagnostic path: " + str(path))
        value.reserve("attempts")
        declared = _preflight_operand_v1(value, path, "kind")
        if value.native_basis is not None and value._startup_catalog is None:
            declared = value.native_basis.status(value.relative(path),optional=optional)
        chain = _preflight_chain_v1(path.parent, optional=optional)
        kind = None
        if chain[-1][1] is None:
            if chain != _preflight_chain_v1(path.parent, optional=True):
                raise ValueError("optional preflight ancestor changed")
        else:
            try:
                info = path.lstat()
            except FileNotFoundError:
                if not optional or chain != _preflight_chain_v1(path.parent):
                    raise
            else:
                if _stat_is_reparse_point(info) or stat.S_ISLNK(info.st_mode):
                    raise ValueError("linked preflight path: " + str(path))
                if stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
                    kind = "file"
                elif stat.S_ISDIR(info.st_mode):
                    kind = "directory"
                else:
                    raise ValueError("unsupported preflight path: " + str(path))
                if (chain != _preflight_chain_v1(path.parent)
                        or _preflight_stamp_v1(info) != _preflight_stamp_v1(path.lstat())):
                    raise ValueError("preflight path generation changed: " + str(path))
        if (value._startup_catalog is not None or value.native_basis is not None) and kind != declared:
            raise ValueError("startup status differs from declaration: " + str(path))
        # All successful statuses, including both kinds of absence, settle
        # after their last observation. Consumed work is never refunded.
        value.check()
        return kind
    except BaseException as exc:
        _preflight_failure_v1(value, exc)


def _preflight_read_bytes_v1(path, *, evidence=False):
    value = _preflight_active_v1()
    path = Path(path).absolute()
    if value is None:
        # This is the original unselected read interface, not canonical custody.
        # _preflight_active_v1 has already rejected missing selected bindings.
        try:
            return path.read_bytes()
        except OSError as exc:
            _preflight_failure_v1(None, exc)
    descriptor, errors, result = None, [], None
    native_acquisition = None
    try:
        value.reserve("attempts")
        expected = _preflight_operand_v1(value, path, "file", evidence=evidence)
        chain = _preflight_chain_v1(path.parent)
        before = path.lstat()
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or _stat_is_reparse_point(before)):
            raise ValueError("unsupported preflight file: " + str(path))
        if value is not None:
            if ((expected is not None and len(expected) != before.st_size)
                    or before.st_size + 1 > value.remaining["bytes"]):
                value.fail("insufficient full preflight acquisition capacity: " + str(path))
            value.reserve("retained_bytes", before.st_size)
        if value.native_basis is not None and value._startup_catalog is None and not evidence:
            native_acquisition = value.native_basis.open_entry(value.relative(path))
            descriptor = native_acquisition.__enter__()
        else:
            descriptor = _open_regular_worktree_descriptor(path, nonblocking=True)
        opened = os.fstat(descriptor)
        if not _same_observed_file(before, opened) or opened.st_nlink != 1:
            raise ValueError("preflight descriptor substitution: " + str(path))
        data = bytearray()
        while True:
            if value is not None:
                value.check()
            requested = min(65536, before.st_size - len(data) + 1)
            block = os.read(descriptor, requested)
            if type(block) is not bytes:
                if value is not None:
                    value.measurement_complete = False
                raise ValueError("unmeasured preflight file delivery")
            if value is not None:
                if value.native_read_observation is not None:
                    key = 'source_bytes_read' if native_acquisition is not None else 'owned_evidence_bytes_read'
                    value.native_read_observation[key] += len(block)
                value.received("bytes", len(block))
            if len(block) > requested or len(data) + len(block) > before.st_size:
                raise ValueError("preflight file grew or reader overdelivered: " + str(path))
            if not block:
                break
            if expected is not None and block != expected[len(data):len(data) + len(block)]:
                raise ValueError("preflight expected bytes differ: " + str(path))
            data.extend(block)
            if value is not None:
                value.observed["retained_bytes"] += len(block)
        if (len(data) != before.st_size
                or _scan_same_api_version(opened) != _scan_same_api_version(os.fstat(descriptor))
                or _scan_same_api_version(before) != _scan_same_api_version(path.lstat())
                or chain != _preflight_chain_v1(path.parent)):
            raise ValueError("incomplete or changed preflight file: " + str(path))
        result = bytes(data)
    except BaseException as exc:
        errors.append(exc)
    if descriptor is not None:
        try:
            if native_acquisition is not None: native_acquisition.__exit__(None,None,None)
            else: os.close(descriptor)
        except BaseException as exc:
            errors.append(exc)
    if errors:
        _preflight_failure_v1(value, errors[0] if len(errors) == 1 else BaseExceptionGroup("preflight read/close", errors))
    if value is not None:
        value.check()
    return result


def _preflight_read_text_v1(path):
    # Decode outside acquisition: a payload error does not falsify complete I/O.
    return _preflight_read_bytes_v1(path).decode("utf-8", errors="strict").replace("\r\n", "\n").replace("\r", "\n")


def _preflight_directory_v1(path):
    value = _preflight_active_v1()
    path = Path(path).absolute()
    iterator, errors, result = None, [], []
    native_acquisition = None
    try:
        expected = None
        if value is not None:
            value.reserve("attempts")
            expected = _preflight_operand_v1(value, path, "directory")
            if value.native_basis is not None and value._startup_catalog is None:
                native_acquisition = value.native_basis.open_entry(value.relative(path))
                native_acquisition.__enter__()
        chain = _preflight_chain_v1(path)
        iterator = os.scandir(path)
        names = set()
        for entry in iterator:
            if value is not None:
                value.received("entries", 1)
            if entry.name in names:
                raise ValueError("duplicate preflight directory entry: " + entry.name)
            names.add(entry.name)
            # Windows DirEntry.stat caches zero inode/device/link counts. Use
            # the same no-follow pathname API for both generation observations.
            info = Path(entry.path).lstat()
            if _stat_is_reparse_point(info) or stat.S_ISLNK(info.st_mode):
                raise ValueError("linked preflight directory entry: " + entry.path)
            if stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
                kind = "file"
            elif stat.S_ISDIR(info.st_mode):
                kind = "directory"
            else:
                raise ValueError("unsupported preflight directory entry: " + entry.path)
            if _preflight_stamp_v1(info) != _preflight_stamp_v1(Path(entry.path).lstat()):
                raise ValueError("changed preflight directory entry: " + entry.path)
            result.append((Path(entry.path), kind))
            if value is not None:
                value.retained_entries += 1
        if chain != _preflight_chain_v1(path):
            raise ValueError("changed preflight directory generation: " + str(path))
        if expected is not None and sorted((p.name, k) for p, k in result) != sorted(expected):
            raise ValueError("preflight directory basis differs: " + str(path))
    except BaseException as exc:
        errors.append(exc)
    if iterator is not None:
        try:
            iterator.close()
        except BaseException as exc:
            errors.append(exc)
    if native_acquisition is not None:
        try: native_acquisition.__exit__(None,None,None)
        except BaseException as exc: errors.append(exc)
    if errors:
        _preflight_failure_v1(value, errors[0] if len(errors) == 1 else BaseExceptionGroup("preflight directory/close", errors))
    try:
        if chain != _preflight_chain_v1(path):
            raise ValueError("directory generation changed during close: " + str(path))
    except BaseException as exc:
        _preflight_failure_v1(value, exc)
    if value is not None:
        value.check()
    return tuple(result)


def _preflight_files_v1(root, pattern="*", *, recursive=False, include_directories=False):
    from fnmatch import fnmatch
    # Observe the complete directory before filtering, preserve iterator order.
    result = []
    for path, kind in _preflight_directory_v1(root):
        if (kind == "file" or include_directories) and fnmatch(path.name, pattern):
            result.append(path)
        if kind == "directory" and recursive:
            result.extend(_preflight_files_v1(path, pattern, recursive=True, include_directories=include_directories))
    return tuple(result)


def _preflight_pth_v1(raw, *, site_root, bound_roots):
    if type(raw) is not bytes or b"\0" in raw:
        raise ValueError("complete startup bytes required")
    selected = []
    for line in raw.decode("utf-8-sig", errors="strict").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        if line.startswith(("import ", "import\t")):
            raise ValueError("unsupported executable startup .pth line")
        path = (Path(site_root) / line.rstrip()).absolute()
        if ".." in path.parts or not any(path.is_relative_to(Path(root).absolute()) for root in bound_roots):
            raise ValueError("startup .pth path leaves bound roots")
        selected.append(path)
    return tuple(selected)


def _preflight_environment_v1(argv, environment, *, cache_root):
    if not _preflight_vector_v1(argv) or type(environment) is not dict:
        raise ValueError("original first-eight vector/environment required")
    projected, removed, seen = {}, [], set()
    for key, value in environment.items():
        if (type(key) is not str or type(value) is not str or not key or "=" in key
                or "\0" in key or "\0" in value or key.upper() in seen):
            raise ValueError("invalid or case-colliding startup environment")
        seen.add(key.upper())
        if key.upper().startswith("PYTHON"):
            removed.append(key)
        else:
            projected[key] = value
    cache = Path(cache_root).absolute()
    _preflight_chain_v1(cache.parent)
    cache.mkdir(exist_ok=False)
    if _preflight_directory_v1(cache):
        raise ValueError("startup cache is not empty")
    fixed = {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1", "PYTHONPYCACHEPREFIX": str(cache)}
    projected.update(fixed)
    return projected, {"registered_argv": argv, "removed_environment_keys": tuple(removed),
                       "fixed_environment_controls": tuple(fixed.items())}


def _preflight_launch_guard_v1(argv, environment, *, expected_argv, expected_environment):
    if (type(argv) is not tuple or not _preflight_vector_v1(argv) or argv != expected_argv
            or type(environment) is not dict or environment != expected_environment):
        raise ValidationReliabilityError("ENGVR_PREPUBLICATION_CUSTODY_FAILED", "actual startup vector/environment differs")


def _preflight_git_process_v1(value, argv, *, root, environment):
    """Finite Git observations use the existing native supervisor and receipts."""
    value.check()
    environment = {k: v for k, v in environment.items() if k.upper() not in _PREFLIGHT_INPUT_KEYS_V1}
    if (type(value.git_executable) is not str or not Path(value.git_executable).is_absolute()
            or value.evidence_root is None or not Path(value.evidence_root).is_absolute()):
        value.fail("missing admitted absolute Git/evidence operands")
    executable = Path(value.git_executable)
    _local_unlinked_path(executable.parent)
    info = executable.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or _stat_is_reparse_point(info):
        value.fail("unsupported admitted Git executable")
    value.reserve("git_attempts")
    limits = {name: value.remaining[name] for name in ("stdout_bytes", "stderr_bytes", "combined_output_bytes")}
    if limits["stdout_bytes"] + limits["stderr_bytes"] > limits["combined_output_bytes"]:
        value.fail("separate Git streams exceed combined allowance")
    observation = {}
    try:
        receipt = supervise_command((value.git_executable, *argv[1:]), cwd=root,
            run_id=value.run_id, phase="preflight-git", command_index=len(value.git_receipts) + 1,
            evidence_root=Path(value.evidence_root), environment=environment,
            execution_deadline_ns=value.deadline_ns, mirror_stdout=False, mirror_stderr=False,
            output_limits=limits, output_observation=observation)
    except BaseException as exc:
        value.measurement_complete = False
        _preflight_failure_v1(value, exc)
    value.git_receipts.append(receipt)
    # Record both streams even if one exhausts the ancestor allowance.
    failures = []
    for key, stream in (("stdout_bytes", "stdout"), ("stderr_bytes", "stderr")):
        try:
            value.received(key, observation[stream]["drained_byte_count"])
        except BaseException as exc:
            failures.append(exc)
    try:
        value.received("combined_output_bytes", sum(observation[s]["drained_byte_count"] for s in ("stdout", "stderr")))
    except BaseException as exc:
        failures.append(exc)
    if failures or receipt.failure_class not in (None, "ENGVR_NATIVE_EXIT_NONZERO") or type(receipt.native_exit_code) is not int:
        exc = ValidationReliabilityError(receipt.failure_class or "ENGVR_PREPUBLICATION_CUSTODY_FAILED",
            f"Git observation failed; native_exit={receipt.native_exit_code}; evidence={receipt.stderr_path}")
        exc.command_receipt = receipt
        value.fail(exc)
    try:
        payloads = []
        for stream, path in (("stdout", receipt.stdout_path), ("stderr", receipt.stderr_path)):
            item = observation[stream]
            if not item["complete"] or item["overflow"]:
                value.fail("incomplete Git stream: " + stream)
            payloads.append(_preflight_read_bytes_v1(Path(path), evidence=True).decode("utf-8", errors="strict"))
        if receipt.native_exit_code != 0:
            exc = ValidationReliabilityError("ENGVR_PREPUBLICATION_CUSTODY_FAILED",
                f"required Git query failed: exit={receipt.native_exit_code}; stderr={payloads[1]!r}")
            exc.command_receipt = receipt
            value.fail(exc)
        return subprocess.CompletedProcess(tuple(argv), receipt.native_exit_code, *payloads)
    except BaseException as exc:
        _preflight_failure_v1(value, exc)


def _preflight_startup_v1(argv, environment, *, binding, cache_root):
    """Inspect supplied startup bytes from the already trusted same interpreter.

    This supported subset does not certify its parent's bootstrap or native host
    containment. No child probe, executable hook, or approval callback is used.
    An absent independently supplied startup closure remains unavailable.
    """
    import sysconfig
    import site
    import struct
    keys = {"observation", "version", "abi", "stdlib_roots", "site_roots",
            "loader_environment", "config_paths", "customizer_paths", "startup_basis"}
    if (type(binding) is not dict or set(binding) != keys
            or type(binding["observation"]) is not _PreflightObservationV1):
        raise ValueError("original host startup byte/identity binding unavailable")
    observation = binding["observation"]
    actual_abi = (sys.implementation.cache_tag, sysconfig.get_config_var("SOABI"),
                  struct.calcsize("P") * 8, sysconfig.get_config_var("Py_GIL_DISABLED"),
                  getattr(sys, "abiflags", ""))
    if (not _preflight_vector_v1(argv) or argv != observation.argv
            or Path(argv[0]).absolute() != Path(sys.executable).absolute()
            or type(binding["version"]) is not tuple or len(binding["version"]) != 3
            or any(type(v) is not int for v in binding["version"])
            or tuple(sys.version_info[:3]) != (3, 14, 6)
            or binding["version"] != tuple(sys.version_info[:3])
            or type(binding["abi"]) is not tuple or len(binding["abi"]) != 5
            or any(type(binding["abi"][i]) is not int for i in (2, 3))
            or binding["abi"] != actual_abi):
        raise ValueError("startup executable/version/ABI association unavailable")
    stdlib = tuple(dict.fromkeys(str(Path(sysconfig.get_path(k)).absolute()) for k in ("stdlib", "platstdlib")))
    sites = tuple(str(Path(p).absolute()) for p in site.getsitepackages())
    if binding["stdlib_roots"] != stdlib or binding["site_roots"] != sites:
        raise ValueError("startup standard-library/site roots differ")
    loaders = {k: v for k, v in environment.items() if k.upper() in {
        "PATH", "SYSTEMROOT", "WINDIR", "LD_LIBRARY_PATH", "LD_PRELOAD", "DYLD_LIBRARY_PATH",
        "DYLD_INSERT_LIBRARIES", "__PYVENV_LAUNCHER__"}}
    if type(binding["loader_environment"]) is not dict or loaders != binding["loader_environment"]:
        raise ValueError("startup loader environment differs")
    if any(k.upper() in {"LD_PRELOAD", "DYLD_INSERT_LIBRARIES", "__PYVENV_LAUNCHER__"} for k in loaders):
        raise ValueError("unsupported startup loader injection")
    executable = Path(argv[0]).absolute()
    config_paths = tuple(dict.fromkeys((
        str(executable.parent / "pyvenv.cfg"), str(executable.parent.parent / "pyvenv.cfg"),
        str(executable.with_suffix("._pth")),
        str(executable.parent / f"python{sys.version_info.major}{sys.version_info.minor}._pth"))))
    if binding["config_paths"] != config_paths:
        raise ValueError("incomplete applicable startup configuration candidates")
    search_roots = tuple(dict.fromkeys((str(Path.cwd()), str(Path(argv[1]).absolute().parent), str(executable.parent), *stdlib, *sites)))
    customizers = tuple(str(Path(root) / (name + suffix)) for root in search_roots
                        for name in ("sitecustomize", "usercustomize")
                        for suffix in (".py", ".pyc", ".pyd", ".so", ""))
    if binding["customizer_paths"] != customizers:
        raise ValueError("incomplete startup customizer candidate set")
    with _preflight_observation_v1(observation, run_id=observation.run_id,
            occurrence=observation.occurrence, argv=argv, root=observation.root), _preflight_startup_access_v1(observation, binding["startup_basis"]):
        _preflight_read_bytes_v1(executable)
        for path in config_paths:
            if _preflight_kind_v1(Path(path), optional=True) is not None:
                raw = _preflight_read_bytes_v1(Path(path))
                if path.endswith("._pth"):
                    # ._pth alters the complete resolver; unsupported by this subset.
                    raise ValueError("unsupported executable ._pth configuration: " + path)
                raw.decode("utf-8", errors="strict")
        for path in customizers:
            if _preflight_kind_v1(Path(path), optional=True) is not None:
                raise ValueError("unadmitted startup customizer: " + path)
        for root in dict.fromkeys((*stdlib, *sites)):
            for path in _preflight_files_v1(Path(root), recursive=True):
                raw = _preflight_read_bytes_v1(path)
                if str(path.parent) in sites and path.suffix == ".pth":
                    additions = _preflight_pth_v1(raw, site_root=path.parent, bound_roots=search_roots)
                    if any(str(p) not in search_roots for p in additions):
                        raise ValueError("startup .pth adds an unbound customizer search root")
    return _preflight_environment_v1(argv, environment, cache_root=cache_root)


# First-phase transport is data, never a source of host or semantic authority.
_PREFLIGHT_MAX_V1 = (1 << 63) - 1
_PREFLIGHT_DIMENSIONS_V1 = ('attempts', 'bytes', 'entries', 'retained_bytes',
    'git_attempts', 'stdout_bytes', 'stderr_bytes', 'combined_output_bytes')
_PREFLIGHT_TRANSPORT_FIELDS_V1 = ('frame_byte_limit', 'header_byte_limit', 'lexical_units',
    'depth', 'quoted_bytes', 'read_calls', 'write_calls', 'chunk_bytes',
    'retained_buffer_bytes', 'receiver_byte_limit')
_PREFLIGHT_INPUT_KEYS_V1 = ('QTT_PREFLIGHT_INPUT_BYTES', 'QTT_PREFLIGHT_HEADER_LIMIT',
    'QTT_PREFLIGHT_PARSE_LIMITS', 'QTT_PREFLIGHT_ORIGINAL_POSITION', 'QTT_PREFLIGHT_DEADLINE_NS')
_PREFLIGHT_NATIVE_INPUT_V1 = ContextVar('_PREFLIGHT_NATIVE_INPUT_V1', default=None)
_LINUX_PREFLIGHT_PROCESS_V1 = ContextVar('_LINUX_PREFLIGHT_PROCESS_V1', default=None)
_LINUX_PREFLIGHT_LEASE_V1 = ContextVar('_LINUX_PREFLIGHT_LEASE_V1', default=None)


def _preflight_require_v1(condition, detail):
    if not condition:
        raise ValidationReliabilityError('ENGVR_PREPUBLICATION_CUSTODY_FAILED', detail)


def _preflight_integer_v1(value, *, positive=False):
    _preflight_require_v1(type(value) is int and int(positive) <= value <= _PREFLIGHT_MAX_V1,
        'preflight exact integer range')
    return value


def _preflight_keys_v1(value, keys):
    _preflight_require_v1(type(value) is dict and set(value) == set(keys)
        and all(type(k) is str for k in value), 'preflight exact object fields: ' + ','.join(keys))


def _preflight_text_v1(value):
    _preflight_require_v1(type(value) is str and bool(value) and all(ord(c) >= 32
        and not 127 <= ord(c) <= 159 and not 0xD800 <= ord(c) <= 0xDFFF for c in value),
        'preflight exact nonempty text')
    return value


def _preflight_relative_v1(value, *, directory=False):
    _preflight_text_v1(value)
    if directory and value == '.':
        return value
    _preflight_require_v1('\\' not in value and ':' not in value and not value.startswith('/')
        and all(p not in ('', '.', '..') for p in value.split('/')), 'preflight portable relative path')
    _scope_git_path(value)
    return value


def _preflight_transport_chain_v1(path):
    # Directory membership changes from our own evidence writes are expected;
    # physical ancestor identity, type and reparse rejection are not relaxed.
    _local_unlinked_path(path)
    result = []
    for parent in (*reversed(path.parents),path):
        info = parent.lstat()
        _preflight_require_v1(stat.S_ISDIR(info.st_mode) and not _stat_is_reparse_point(info),
            'preflight unsupported transport ancestor')
        result.append((str(parent),_NestedPytestEvidenceV1._directory_identity(info)))
    return tuple(result)


def _preflight_limits_v1(value, *, transport=False):
    _preflight_keys_v1(value, _PREFLIGHT_TRANSPORT_FIELDS_V1 if transport else _PREFLIGHT_DIMENSIONS_V1)
    for v in value.values():
        _preflight_integer_v1(v, positive=transport)
    if transport:
        _preflight_require_v1(value['header_byte_limit'] <= value['frame_byte_limit']
            and value['chunk_bytes'] <= 65536, 'preflight transport capacity relation')
    else:
        _preflight_require_v1(value['stdout_bytes'] + value['stderr_bytes'] <= value['combined_output_bytes'],
            'preflight separate streams exceed combined allowance')
    return dict(value)


def _preflight_canonical_v1(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode('ascii')


def _preflight_json_v1(raw, limits, check, *, canonical_encoding=True):
    # Bound recursive decoding before json.loads allocates the object graph.
    depth = units = quoted = 0
    string = escape = False
    for offset, b in enumerate(raw):
        if offset % 4096 == 0:
            check()
        if string:
            quoted += 1
            if escape:
                escape = False
            elif b == 92:
                escape = True
            elif b == 34:
                string = False
        elif b == 34:
            string = True
            units += 1
        elif b in (123, 91):
            depth += 1
            units += 1
        elif b in (125, 93):
            depth -= 1
        elif b not in (32, 9, 10, 13, 58, 44):
            units += 1
        _preflight_require_v1(0 <= depth <= limits['depth'] and units <= limits['lexical_units']
            and quoted <= limits['quoted_bytes'], 'preflight lexical/depth/quoted capacity')
    _preflight_require_v1(not string and not escape and depth == 0, 'preflight incomplete JSON')
    def pairs(rows):
        result = {}
        for k, v in rows:
            _preflight_require_v1(k not in result, 'preflight duplicate JSON key: ' + k)
            _preflight_require_v1(not any(0xD800 <= ord(c) <= 0xDFFF for c in k), 'preflight surrogate key')
            result[k] = v
        return result
    def integer(token):
        _preflight_require_v1(len(token) <= 19 and token.isascii() and token.isdecimal(), 'preflight integer token')
        return _preflight_integer_v1(int(token))
    def reject(token):
        raise ValueError('preflight noninteger JSON number: ' + token)
    result = json.loads(raw.decode('utf-8', errors='strict'), object_pairs_hook=pairs,
        parse_int=integer, parse_float=reject, parse_constant=reject)
    def scalars(value):
        if type(value) is str:
            _preflight_require_v1(not any(0xD800 <= ord(c) <= 0xDFFF for c in value), 'preflight surrogate text')
        elif type(value) is dict:
            for v in value.values(): scalars(v)
        elif type(value) is list:
            for v in value: scalars(v)
    scalars(result)
    if canonical_encoding:
        _preflight_require_v1(_preflight_canonical_v1(result) == raw, 'preflight noncanonical JSON')
    check()
    return result, dict(lexical_units=units, quoted_bytes=quoted)


class _PreflightTransportV1:
    """One already reserved transport tranche; consumption never refunds it."""
    def __init__(self, limits, deadline_ns, check=None):
        self.limits = _preflight_limits_v1(limits, transport=True)
        self.deadline_ns = _preflight_integer_v1(deadline_ns, positive=True)
        self.external_check = check
        self.read_calls = self.write_calls = self.received = self.emitted = 0
        self.readback_bytes = self.lexical_units = self.quoted_bytes = self.peak_buffers = 0
        self.last_ns = -1
        self.failure = None
    def check(self):
        if self.failure is not None:
            raise self.failure
        now = time.monotonic_ns()
        _preflight_require_v1(self.last_ns <= now < self.deadline_ns, 'preflight transport deadline/clock')
        self.last_ns = now
        if self.external_check is not None:
            _preflight_require_v1(self.external_check() is None, 'preflight transport custody check')
    def buffers(self, count):
        self.peak_buffers = max(self.peak_buffers, count)
        _preflight_require_v1(count <= self.limits['retained_buffer_bytes'], 'preflight transport buffer capacity')
        self.check()
    def parse(self,raw,*,canonical_encoding=True):
        limits = dict(self.limits)
        limits['lexical_units'] -= self.lexical_units
        limits['quoted_bytes'] -= self.quoted_bytes
        try:
            result,work = _preflight_json_v1(raw,limits,self.check,canonical_encoding=canonical_encoding)
        except BaseException as exc:
            self.failure = exc
            raise
        self.lexical_units += work['lexical_units']; self.quoted_bytes += work['quoted_bytes']
        return result
    def read(self, fd, size, *, eof=False):
        _preflight_require_v1(0 < size <= self.limits['chunk_bytes'], 'preflight transport read size')
        self.check()
        _preflight_require_v1(self.read_calls < self.limits['read_calls'], 'preflight transport read calls')
        self.read_calls += 1
        def charge(count):
            self.received += count
            _preflight_require_v1(self.received <= self.limits['frame_byte_limit'], 'preflight cumulative transport read capacity')
        block = _scan_v3_native_read(fd, size, charge, self.check)
        if eof:
            _preflight_require_v1(not block, 'preflight trailing bytes')
        return block
    def exact(self, fd, size, *, retained=0):
        _preflight_integer_v1(size)
        self.buffers(retained + 2 * size + min(size, self.limits['chunk_bytes']))
        result = bytearray()
        while len(result) < size:
            block = self.read(fd, min(self.limits['chunk_bytes'], size-len(result)))
            _preflight_require_v1(bool(block), 'preflight truncated frame')
            result.extend(block)
        self.check()
        return bytes(result)
    def write(self, fd, data):
        offset = 0
        while offset < len(data):
            self.check()
            _preflight_require_v1(self.write_calls < self.limits['write_calls'], 'preflight transport write calls')
            self.write_calls += 1
            size = min(self.limits['chunk_bytes'], len(data)-offset)
            n = os.write(fd, memoryview(data)[offset:offset+size])
            _preflight_require_v1(type(n) is int and 0 < n <= size, 'preflight invalid write progress')
            self.emitted += n
            _preflight_require_v1(self.emitted <= self.limits['frame_byte_limit'], 'preflight cumulative transport write capacity')
            offset += n
            self.check()


def _preflight_rosters_v1(rows, *, absolute=False):
    _preflight_require_v1(type(rows) is list, 'preflight directory array')
    result, folded, order = {}, set(), []
    for row in rows:
        _preflight_require_v1(type(row) is list and len(row) == 2 and type(row[1]) is list, 'preflight directory row')
        name = row[0]
        if absolute:
            _preflight_startup_path_v1(name)
        else:
            _preflight_relative_v1(name, directory=True)
        _preflight_require_v1(name.casefold() not in folded, 'preflight directory alias')
        folded.add(name.casefold()); order.append(name.encode('utf-8'))
        children, seen = [], set()
        for item in row[1]:
            _preflight_require_v1(type(item) is list and len(item) == 2 and type(item[1]) is str
                and item[1] in ('file', 'directory'), 'preflight directory entry')
            leaf = _preflight_relative_v1(item[0])
            _preflight_require_v1('/' not in leaf and leaf.casefold() not in seen, 'preflight immediate alias')
            seen.add(leaf.casefold()); children.append((leaf,item[1]))
        _preflight_require_v1([p[0].encode('utf-8') for p in children] == sorted(p[0].encode('utf-8') for p in children),
            'preflight directory child order')
        result[name] = tuple(children)
    _preflight_require_v1(order == sorted(order), 'preflight directory order')
    return result


def _preflight_catalog_consistency_v1(files, directories):
    names = list(files) + list(directories)
    _preflight_require_v1(len({p.casefold() for p in names}) == len(names), 'preflight catalog alias')
    for name, kind in [(p,'file') for p in files] + [(p,'directory') for p in directories if p != '.']:
        parent, _, leaf = name.rpartition('/')
        if (parent or '.') in directories:
            _preflight_require_v1(dict(directories[parent or '.']).get(leaf) == kind, 'preflight parent roster contradiction')
        for ancestor in Path(name).parents:
            _preflight_require_v1(ancestor.as_posix() not in files, 'preflight file ancestor contradiction')


def _preflight_identity_v1(identity):
    _preflight_keys_v1(identity, ('run_id','phase','command_index','original_position','command_count',
        'argv','repo_root','process_root','evidence_root','parent_pid'))
    _preflight_text_v1(identity['run_id'])
    n = _preflight_integer_v1(identity['original_position'], positive=True)
    _preflight_require_v1(n <= 8 and type(identity['command_index']) is int and identity['command_index'] == n
        and type(identity['command_count']) is int and identity['command_count'] == 8
        and identity['phase'] == 'fast-preflight', 'preflight original position/phase')
    argv = identity['argv']
    _preflight_require_v1(type(argv) is list and _preflight_vector_v1(tuple(argv))
        and argv[1].replace('\\','/') == _PREFLIGHT_SCRIPTS_V1[n-1], 'preflight fixed route')
    _preflight_startup_path_v1(argv[0])
    roots = [Path(_preflight_startup_path_v1(identity[k])) for k in ('repo_root','process_root','evidence_root')]
    for i, root in enumerate(roots):
        for other in roots[i+1:]:
            _preflight_require_v1(not root.is_relative_to(other) and not other.is_relative_to(root), 'preflight root separation')
    _preflight_integer_v1(identity['parent_pid'], positive=True)


def _preflight_header_v1(header, payload_size, expected):
    _preflight_keys_v1(header, ('identity','allowance','deadline_ns','git','files','directories'))
    _preflight_identity_v1(header['identity']); _preflight_identity_v1(expected)
    _preflight_require_v1(header['identity'] == expected, 'preflight invocation identity mismatch')
    allowance = _preflight_limits_v1(header['allowance'])
    _preflight_require_v1(type(header['files']) is list and type(header['directories']) is list,
        'preflight catalog arrays')
    count = len(header['files'])+len(header['directories'])
    for row in header['directories']:
        _preflight_require_v1(type(row) is list and len(row) == 2 and type(row[1]) is list,
            'preflight directory row')
        count += len(row[1])
    # Admit indexing/retention before constructing the corresponding maps.
    _preflight_require_v1(payload_size <= allowance['retained_bytes'] and count <= allowance['entries'],
        'preflight decoded basis allowance')
    _preflight_integer_v1(header['deadline_ns'], positive=True)
    _preflight_keys_v1(header['git'], ('executable','evidence_root'))
    git = header['git']
    if allowance['git_attempts'] == 0:
        _preflight_require_v1(git == dict(executable=None,evidence_root=None), 'preflight unselected Git')
    else:
        _preflight_startup_path_v1(git['executable']); _preflight_startup_path_v1(git['evidence_root'])
        _preflight_require_v1(git['evidence_root'] == str(Path(expected['evidence_root']) /
            ('preflight-'+str(expected['command_index'])) / 'git'), 'preflight Git evidence namespace')
    _preflight_require_v1(type(header['files']) is list, 'preflight file array')
    names, offset, order = {}, 0, []
    for row in header['files']:
        _preflight_require_v1(type(row) is list and len(row) == 3, 'preflight file row')
        name = _preflight_relative_v1(row[0])
        start, length = (_preflight_integer_v1(v) for v in row[1:])
        _preflight_require_v1(start == offset and length <= payload_size-offset, 'preflight contiguous payload')
        _preflight_require_v1(name not in names, 'preflight duplicate file')
        names[name] = length; offset += length; order.append(name.encode('utf-8'))
    _preflight_require_v1(offset == payload_size and order == sorted(order), 'preflight complete ordered payload')
    directories = _preflight_rosters_v1(header['directories'])
    _preflight_catalog_consistency_v1(names, directories)
    return directories, count


def _preflight_header_v2(header,payload_size,expected):
    _preflight_keys_v1(header,('identity','allowance','deadline_ns','git','native_basis','selection'))
    _preflight_identity_v1(header['identity']);_preflight_identity_v1(expected)
    _preflight_require_v1(header['identity']==expected and payload_size==0,'LINUX_V2_CHILD_IDENTITY_OR_BODY')
    _preflight_integer_v1(header['deadline_ns'],positive=True)
    allowance=_preflight_limits_v1(header['allowance'])
    descriptor=_linux_source_descriptor_v2(header['native_basis'])
    _preflight_require_v1(descriptor['byte_length']<=allowance['retained_bytes'] and
        descriptor['catalog_entry_count']<=allowance['entries'],'LINUX_V2_CATALOG_ALLOWANCE')
    _preflight_require_v1(header['selection']==('NONE' if expected['original_position'] in (2,6) else 'ALL_WORKTREE'),
        'LINUX_V2_FIXED_SELECTION')
    _preflight_keys_v1(header['git'],('executable','evidence_root'))
    git=header['git']
    if allowance['git_attempts']==0:
        _preflight_require_v1(git==dict(executable=None,evidence_root=None),'preflight unselected Git')
    else:
        _preflight_startup_path_v1(git['executable']);_preflight_startup_path_v1(git['evidence_root'])
        _preflight_require_v1(git['evidence_root']==str(Path(expected['evidence_root'])/('preflight-'+str(expected['command_index']))/'git'),
            'preflight Git evidence namespace')
    return descriptor['catalog_entry_count']


def _preflight_encode_header_v1(header, limits, check, buffer_check):
    # Bound emission before joining header chunks. No joined archive body.
    measured = 0
    def add(n):
        nonlocal measured
        measured += n
        _preflight_require_v1(measured <= limits['header_byte_limit'],'preflight header emission capacity')
        if measured % 4096 < 12: check()
    def measure(value,depth=0):
        check()
        _preflight_require_v1(depth <= limits['depth'],'preflight header encoding depth')
        if type(value) is str:
            add(2)
            for c in value:
                code=ord(c)
                _preflight_require_v1(not 0xD800 <= code <= 0xDFFF,'preflight surrogate text')
                add(2 if c in '\"\\\b\f\n\r\t' else 6 if code < 32 or 127 <= code <= 65535 else 12 if code > 65535 else 1)
        elif value is None: add(4)
        elif type(value) is bool: add(4 if value else 5)
        elif type(value) is int:
            _preflight_integer_v1(value); add(len(str(value)))
        elif type(value) is list:
            add(2+max(0,len(value)-1))
            for v in value: measure(v,depth+1)
        elif type(value) is dict:
            add(2+max(0,len(value)-1)+len(value))
            for k,v in value.items(): measure(k,depth+1); measure(v,depth+1)
        else: raise ValueError('preflight header is data only')
    measure(header)
    _preflight_require_v1(3*measured <= limits['retained_buffer_bytes'],'preflight header buffer capacity')
    buffer_check(3*measured)
    encoder = json.JSONEncoder(ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False)
    parts, count = [], 0
    for part in encoder.iterencode(header):
        check()
        raw = part.encode('ascii'); count += len(raw)
        _preflight_require_v1(count <= limits['header_byte_limit'], 'preflight header emission capacity')
        parts.append(raw)
    raw = b''.join(parts)
    _preflight_require_v1(len(raw) == measured,'preflight header encoding measurement differs')
    return raw


def _preflight_frame_read_v1(fd, *, magic, extent, meter, validate):
    import struct
    _preflight_integer_v1(extent, positive=True)
    _preflight_require_v1(extent <= meter.limits['frame_byte_limit'], 'preflight frame limit')
    prefix = meter.exact(fd, 24)
    actual_magic, h, p = struct.unpack('>8sQQ', prefix)
    _preflight_integer_v1(h, positive=True); _preflight_integer_v1(p)
    _preflight_require_v1((actual_magic in magic if type(magic) is tuple else actual_magic == magic) and h <= meter.limits['header_byte_limit']
        and 24+h+p == extent, 'preflight prefix/extent')
    raw = meter.exact(fd, h)
    header = meter.parse(raw)
    if actual_magic in (b'QTTPA02\n',b'QTTPF02\n'):
        _preflight_require_v1(('basis_kind' in header if actual_magic==b'QTTPA02\n' else 'native_basis' in header),
            'LINUX_V2_WIRE_SHAPE')
        if actual_magic==b'QTTPF02\n':
            _preflight_require_v1(p==0 and 24+h<=1048576,'LINUX_V2_CHILD_FRAME_CAPACITY')
    else:
        _preflight_require_v1('native_basis' not in header and 'basis_kind' not in header,'PREFLIGHT_V1_NEW_FIELDS')
    segments, result = validate(header, p)
    # All ranges, shape and association are checked before retaining any body.
    values = []
    retained = h
    for length in segments:
        values.append(meter.exact(fd, length, retained=retained))
        retained += length
    meter.read(fd, 1, eof=True)
    _preflight_require_v1(meter.received == extent, 'preflight exact consumed frame')
    meter.check()
    return header, values, result


def _preflight_regular_v1(info):
    _preflight_require_v1(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
        and not _stat_is_reparse_point(info), 'preflight regular single-link input required')


def _preflight_decimal_v1(text):
    _preflight_require_v1(type(text) is str and 1 <= len(text) <= 19 and text.isascii()
        and text.isdecimal() and (text == '0' or not text.startswith('0')), 'preflight canonical decimal control')
    return _preflight_integer_v1(int(text), positive=True)


def _preflight_result_bound_v1(identity, *, native_basis=None):
    # Finite worst-case numeric width, fixed failure classes, no exception text.
    result = _preflight_result_v1(identity, None, None, _PREFLIGHT_MAX_V1, False, False, None, False,
        'PREFLIGHT_APPLICATION_EXCEPTION')
    result['pid'] = _PREFLIGHT_MAX_V1
    for key in ('initial_limits','remaining_limits','observed','reserved'):
        result[key] = dict.fromkeys(_PREFLIGHT_DIMENSIONS_V1, _PREFLIGHT_MAX_V1)
    result['retained_entries'] = _PREFLIGHT_MAX_V1
    if native_basis is not None:
        result['basis_kind']='NATIVE_IMMUTABLE_V2'
        result['native_read_observation']=dict.fromkeys(('manifest_acquired_bytes','manifest_retained_bytes',
            'source_bytes_read','owned_evidence_bytes_read'),_PREFLIGHT_MAX_V1)
    return len((json.dumps(result, indent=2, sort_keys=True)+'\n').encode('utf-8')) + 128


def _preflight_result_v1(identity, observation, initial, consumed, decoded, entered, exit_code, complete, failure, *, basis_kind=None):
    result = dict(run_id=identity['run_id'], phase=identity['phase'], command_index=identity['command_index'],
        original_position=identity['original_position'], argv=identity['argv'], cwd=identity['repo_root'],
        pid=os.getpid(), parent_pid=os.getppid(), input_bytes_consumed=consumed,
        decode_complete=decoded, application_entered=entered, application_exit=exit_code,
        observation_complete=complete, initial_limits=initial,
        remaining_limits=None if observation is None else dict(observation.remaining),
        observed=None if observation is None else dict(observation.observed),
        reserved=None if observation is None else dict(observation.reserved),
        retained_entries=None if observation is None else observation.retained_entries, failure_class=failure)
    if observation is not None and observation.native_basis is not None:
        result.update(basis_kind='NATIVE_IMMUTABLE_V2',native_read_observation=dict(observation.native_read_observation))
    elif basis_kind=='NATIVE_IMMUTABLE_V2':
        result.update(basis_kind=basis_kind,native_read_observation=None)
    return result


def _preflight_cli_v1(main, script_file):
    """Explicit CLI boundary. Imports are trusted bootstrap, not metered reads."""
    environment, seen = {}, set()
    for key, value in os.environ.items():
        _preflight_require_v1(key.upper() not in seen, 'preflight case-colliding environment')
        seen.add(key.upper()); environment[key.upper()] = value
    controls = set(_PREFLIGHT_INPUT_KEYS_V1)
    selected = bool(controls & seen) or bool(environment.get(RUN_ID_ENV))
    if not selected:
        return main()
    _preflight_require_v1(controls <= seen and all(environment.get(k) for k in
        (RUN_ID_ENV, PROCESS_ROOT_ENV, EVIDENCE_ROOT_ENV)), 'preflight missing/partial input controls')
    _preflight_require_v1(not any(k.startswith(('QTT_SCAN_', 'QTT_MAPPER_')) for k in seen), 'preflight competing transport')
    extent = _preflight_decimal_v1(environment[_PREFLIGHT_INPUT_KEYS_V1[0]])
    hlimit = _preflight_decimal_v1(environment[_PREFLIGHT_INPUT_KEYS_V1[1]])
    parsers = environment[_PREFLIGHT_INPUT_KEYS_V1[2]].split(',')
    _preflight_require_v1(len(parsers) == 5, 'preflight parser controls arity')
    lexical, depth, quoted, calls, chunk = map(_preflight_decimal_v1, parsers)
    n = _preflight_decimal_v1(environment[_PREFLIGHT_INPUT_KEYS_V1[3]])
    deadline = _preflight_decimal_v1(environment[_PREFLIGHT_INPUT_KEYS_V1[4]])
    identity = dict(run_id=environment[RUN_ID_ENV],phase='fast-preflight',command_index=n,
        original_position=n,command_count=8,argv=[sys.executable,*sys.argv],repo_root=str(Path.cwd()),
        process_root=environment[PROCESS_ROOT_ENV],evidence_root=environment[EVIDENCE_ROOT_ENV],parent_pid=os.getppid())
    _preflight_identity_v1(identity)
    _preflight_require_v1(Path(script_file).resolve() == Path.cwd()/_PREFLIGHT_SCRIPTS_V1[n-1]
        and Path(__file__).resolve().parents[1] == Path.cwd(), 'preflight actual module/root mismatch')
    # These ceilings are consequences of the admitted frame extent/algorithm,
    # not new grants. The sender must cover the same demand in its reserved tranche.
    native_selected = sys.platform=='linux' and environment.get('QTT_LINUX_PREFLIGHT_CONTROL') is not None
    bound = _preflight_result_bound_v1(identity)
    limits = dict(frame_byte_limit=extent,header_byte_limit=min(hlimit,extent),lexical_units=lexical,depth=depth,
        quoted_bytes=quoted,read_calls=calls,write_calls=1,chunk_bytes=chunk,
        retained_buffer_bytes=3*extent+2*bound,receiver_byte_limit=bound)
    meter = _PreflightTransportV1(limits, deadline)
    path = Path(identity['process_root'])/('preflight-input-'+str(n)+'.bin')
    evidence = Path(identity['evidence_root'])/('preflight-'+str(n))
    chain = _preflight_transport_chain_v1(path.parent)
    evidence_chain = _preflight_transport_chain_v1(evidence)
    before = path.lstat(); opened = os.fstat(0)
    _preflight_regular_v1(before); _preflight_regular_v1(opened)
    _preflight_require_v1(_same_observed_file(before, opened) and before.st_size == extent
        and opened.st_size == extent and os.lseek(0, 0, os.SEEK_CUR) == 0, 'preflight original stdin identity/extent/cursor')
    def stable():
        meter.check()
        _preflight_require_v1(_scan_same_api_version(path.lstat()) == _scan_same_api_version(before)
            and _scan_same_api_version(os.fstat(0)) == _scan_same_api_version(opened)
            and chain == _preflight_transport_chain_v1(path.parent)
            and evidence_chain == _preflight_transport_chain_v1(evidence), 'preflight frame or evidence identity changed')
    def validate(header, payload):
        _preflight_require_v1(header['deadline_ns']==deadline,'preflight child deadline binding')
        if 'native_basis' in header:
            _preflight_require_v1(native_selected,'LINUX_V2_NATIVE_CHILD_REQUIRED')
            count=_preflight_header_v2(header,payload,identity)
            return [],(None,count,0)
        dirs,count=_preflight_header_v1(header,payload,identity)
        return [row[2] for row in header['files']],(dirs,count,payload)
    observation = initial = None
    decoded_kind = None
    decoded = entered = complete = False
    exit_code = None
    failure = 'PREFLIGHT_DECODE_FAILED'
    errors = []
    try:
        header, values, (directories,count,payload) = _preflight_frame_read_v1(0,
            magic=(b'QTTPF01\n',b'QTTPF02\n') if native_selected else b'QTTPF01\n',extent=extent,meter=meter,validate=validate)
        stable(); decoded = True
        if 'native_basis' in header:
            decoded_kind='NATIVE_IMMUTABLE_V2'
            bound=_preflight_result_bound_v1(identity,native_basis=True)
        initial = dict(header['allowance'])
        residual = dict(initial)
        residual['entries'] -= count; residual['retained_bytes'] -= payload
        # Reserve before constructing these corresponding indexes.
        basis=None
        if 'native_basis' in header:
            control=Path(environment['QTT_LINUX_PREFLIGHT_CONTROL'])
            query=_LinuxPreflightQueriesV1(evidence_root=evidence/'native-basis-observations',deadline_ns=deadline)
            binding,_,_=_linux_preflight_control_read_v1(control/'binding/native.json',deadline_ns=deadline,query=query)
            _preflight_require_v1(binding['repository']==identity['repo_root'] and binding['runtime']==environment['QTT_LINUX_PREFLIGHT_RUNTIME']
                and tuple(binding['vectors'][n-1])==tuple(identity['argv']) and binding['grants']['rows'][n-1]['deadline_ns']==deadline,
                'LINUX_V2_CHILD_ORIGINAL_BINDING')
            lease=_LinuxPreflightHostLeaseV1(binding=binding,control_path=control/'binding/native.json',runtime=binding['runtime'],query=query,
                declaration_chain=tuple((p,tuple(s)) for p,s in binding['declaration_chain']),declaration_version=tuple(binding['declaration_version']),
                parent_pid=identity['parent_pid'])
            basis=_LinuxImmutableSourceBasisV2(lease,header['native_basis'],binding['source_run_id'])
            files={p:row for p,row in basis.files.items() if row[1]=='WORKTREE'} if header['selection']=='ALL_WORKTREE' else {}
            directories={p:v for p,v in basis.directories.items() if p!='.git' and not p.startswith('.git/')} if files else {}
            residual['retained_bytes']-=basis.manifest_retained_bytes
            _preflight_require_v1(residual['retained_bytes']>=0,'LINUX_V2_MANIFEST_RETENTION_ALLOWANCE')
        else:
            files={row[0]:raw for row,raw in zip(header['files'],values,strict=True)}
        observation = _PreflightObservationV1(root=Path.cwd(),run_id=identity['run_id'],occurrence=n,
            argv=tuple(identity['argv']),files=files,directories=directories,limits=residual,deadline_ns=deadline,
            git_executable=header['git']['executable'],evidence_root=header['git']['evidence_root'],native_basis=basis)
        observation._linux_parent_pid_v1 = identity['parent_pid']
        observation.reserved['entries'] = count; observation.reserved['retained_bytes'] = payload
        observation.retained_entries = count
        if basis is not None:
            observation.reserved['retained_bytes']+=basis.manifest_retained_bytes
            observation.native_read_observation.update(manifest_acquired_bytes=basis.manifest_acquired_bytes,
                manifest_retained_bytes=basis.manifest_retained_bytes)
        failure = 'PREFLIGHT_APPLICATION_EXCEPTION'
        with _preflight_observation_v1(observation,run_id=identity['run_id'],occurrence=n,
                argv=tuple(identity['argv']),root=Path.cwd()):
            entered = True
            exit_code = main()
            _preflight_require_v1(type(exit_code) is int, 'preflight application exact native return required')
            observation.check(); stable()
            complete = True
            failure = None if exit_code == 0 else 'PREFLIGHT_APPLICATION_DENIED'
            result = _preflight_result_v1(identity,observation,initial,meter.received,decoded,entered,exit_code,complete,failure)
            _preflight_write_result_v1(evidence,result,bound,meter.check)
        stable()
        return exit_code
    except BaseException as exc:
        errors.append(exc)
        if observation is not None and observation.failure is not None:
            failure = 'PREFLIGHT_OBSERVATION_FAILED'
        if not (evidence/'receiver.json').exists():
            try:
                stable()
                result = _preflight_result_v1(identity,observation,initial,meter.received,decoded,entered,
                    exit_code,False,failure,basis_kind=decoded_kind)
                _preflight_write_result_v1(evidence,result,bound,meter.check)
            except BaseException as write_error:
                errors.append(write_error)
        _scan_raise_errors(errors)


def _preflight_write_result_v1(evidence, result, bound, check):
    check()
    _preflight_chain_v1(evidence)
    raw = (json.dumps(result,indent=2,sort_keys=True)+'\n').encode('utf-8')
    _preflight_require_v1(len(raw) <= bound, 'preflight receiver emission capacity')
    atomic_write_json(evidence/'receiver.json',result)
    check()


class _PreflightHostLeaseV1:
    """Native owner interface; the default supplies no host authority.

    A provisioned native owner must override every check using its actual job or
    cgroup, ancestor restrictions, bootstrap and exclusive custody. Declaration
    bytes cannot construct this live object or select an implementation.
    """
    def check_parent(self, root, index_path):
        raise RuntimeError('PREFLIGHT_NATIVE_HOST_PROVIDER_UNAVAILABLE')
    def check_launch(self, plan_entry, argv, environment, scratch_roots, deadline_ns):
        raise RuntimeError('PREFLIGHT_NATIVE_HOST_PROVIDER_UNAVAILABLE')
    def check_child(self, actual_process):
        raise RuntimeError('PREFLIGHT_NATIVE_HOST_PROVIDER_UNAVAILABLE')
    def check_settled(self, actual_process):
        raise RuntimeError('PREFLIGHT_NATIVE_HOST_PROVIDER_UNAVAILABLE')


class _PreflightNativeInputV1:
    """Live, source-owned input lease; never reconstructed from declaration JSON."""
    def __init__(self, *, path, root, index_path, expected_path_version, expected_chain,
            limits, deadline_ns, host_lease, capture_limits, terminal_limits, git_executable=None):
        _preflight_require_v1(isinstance(host_lease,_PreflightHostLeaseV1), 'PREFLIGHT_NATIVE_HOST_PROVIDER_UNAVAILABLE')
        self.path = Path(_preflight_startup_path_v1(str(path)))
        self.root = Path(_preflight_startup_path_v1(str(root)))
        self.index_path = index_path
        self.expected_path_version, self.expected_chain = expected_path_version, expected_chain
        self.limits = _preflight_limits_v1(limits,transport=True)
        self.deadline_ns = _preflight_integer_v1(deadline_ns,positive=True)
        self.host_lease = host_lease
        self.git_executable = git_executable
        self.capture_limits = _preflight_limits_v1(capture_limits)
        self.terminal_limits = _preflight_limits_v1(terminal_limits)
        self.pid, self.thread = os.getpid(), threading.get_ident()
        self.state = 'AVAILABLE'
        self.meter = _PreflightTransportV1(self.limits,self.deadline_ns,self.check)
    def check(self):
        _preflight_require_v1((os.getpid(),threading.get_ident()) == (self.pid,self.thread)
            and time.monotonic_ns() < self.deadline_ns, 'preflight native input host/deadline association')
        _preflight_require_v1(self.host_lease.check_parent(self.root,self.index_path) is None,
            'preflight native parent custody rejected')
    def consume(self, validate):
        self.check()
        _preflight_require_v1(self.state == 'AVAILABLE','preflight declaration is single use')
        self.state = 'CONSUMING'
        fd = None
        errors = []
        result = None
        try:
            _preflight_require_v1(_preflight_chain_v1(self.path.parent) == self.expected_chain,
                'preflight declaration ancestor identity')
            before = self.path.lstat(); _preflight_regular_v1(before)
            _preflight_require_v1(_scan_same_api_version(before) == self.expected_path_version,
                'preflight declaration physical identity')
            fd = _open_regular_worktree_descriptor(self.path,nonblocking=True)
            opened = os.fstat(fd); _preflight_regular_v1(opened)
            _preflight_require_v1(_same_observed_file(before,opened),'preflight declaration descriptor identity')
            result = _preflight_frame_read_v1(fd,magic=(b'QTTPA01\n',b'QTTPA02\n') if
                type(self.host_lease) is _LinuxPreflightHostLeaseV1 and self.host_lease.binding.get('native_basis') is not None
                else b'QTTPA01\n',extent=before.st_size,
                meter=self.meter,validate=validate)
            _preflight_require_v1(_scan_same_api_version(self.path.lstat()) == self.expected_path_version
                and _scan_same_api_version(os.fstat(fd)) == _scan_same_api_version(opened)
                and _preflight_chain_v1(self.path.parent) == self.expected_chain,'preflight declaration drift')
        except BaseException as exc:
            errors.append(exc)
        if fd is not None:
            try: os.close(fd)
            except BaseException as exc: errors.append(exc)
        try: self.check()
        except BaseException as exc: errors.append(exc)
        self.state = 'FAILED' if errors else 'CONSUMED'
        _scan_raise_errors(errors)
        return result


@contextmanager
def _preflight_native_input_v1(value):
    _preflight_require_v1(type(value) is _PreflightNativeInputV1 and _PREFLIGHT_NATIVE_INPUT_V1.get() is None,
        'preflight original native input owner required')
    value.check()
    token = _PREFLIGHT_NATIVE_INPUT_V1.set(value)
    try:
        yield value
    finally:
        _PREFLIGHT_NATIVE_INPUT_V1.reset(token)


def _preflight_acquire_native_input_v1(path, root):
    value = _PREFLIGHT_NATIVE_INPUT_V1.get()
    if type(value) is not _PreflightNativeInputV1:
        raise RuntimeError('PREFLIGHT_NATIVE_HOST_PROVIDER_UNAVAILABLE: --preflight-input needs live input custody, identity and native grants')
    _preflight_require_v1(value.path == Path(path) and value.root == Path(root) and value.state == 'AVAILABLE',
        'preflight native input location/root/generation mismatch')
    value.check()
    return value


class _PreflightLaunchInputV1:
    """Private alternative in the existing supervisor's stdin lifecycle."""
    def __init__(self, *, identity, observation, row_total, parent_tail_reserve, limits, parent_meter,
            settlement_deadline_ns, host_lease, plan_entry, environment, scratch_roots, output_limits):
        _preflight_identity_v1(identity)
        _preflight_require_v1(isinstance(host_lease,_PreflightHostLeaseV1), 'PREFLIGHT_NATIVE_HOST_PROVIDER_UNAVAILABLE')
        _preflight_require_v1(type(observation) is _PreflightObservationV1 and observation.argv == tuple(identity['argv'])
            and observation.root == Path(identity['repo_root']) and observation.run_id == identity['run_id']
            and observation.occurrence == identity['command_index'], 'preflight transfer observation identity')
        observation.check()
        self.identity, self.observation = dict(identity), observation
        self.tail = _preflight_limits_v1(parent_tail_reserve)
        self.row_total = _preflight_limits_v1(row_total)
        self.limits = _preflight_limits_v1(limits,transport=True)
        self.output_limits = dict(output_limits)
        _preflight_keys_v1(self.output_limits,('stdout_bytes','stderr_bytes','combined_output_bytes'))
        for v in self.output_limits.values(): _preflight_integer_v1(v)
        _preflight_require_v1(self.output_limits['stdout_bytes']+self.output_limits['stderr_bytes'] <= self.output_limits['combined_output_bytes'],
            'preflight application stream capacity')
        self.deadline_ns = observation.deadline_ns
        self.settlement_deadline_ns = _preflight_integer_v1(settlement_deadline_ns,positive=True)
        _preflight_require_v1(time.monotonic_ns() < self.deadline_ns < self.settlement_deadline_ns <= parent_meter.deadline_ns,
            'preflight execution/settlement ancestor deadlines')
        self.parent_meter, self.host_lease = parent_meter, host_lease
        self.plan_entry, self.environment, self.scratch_roots = plan_entry, environment, scratch_roots
        self.pid, self.thread = os.getpid(), threading.get_ident()
        self.reader = self.process = self.result = None
        self.state = 'PREPARING'
        self.path = Path(identity['process_root'])/('preflight-input-'+str(identity['command_index'])+'.bin')
        self.evidence = Path(identity['evidence_root'])/('preflight-'+str(identity['command_index']))
        self.initial_parent = dict(observation.remaining)
        self.parent_spend = {k:self.row_total[k]-self.initial_parent[k] for k in self.row_total}
        for debit in self.parent_spend.values(): _preflight_integer_v1(debit)
        self.delegated = {k: observation.remaining[k]-self.tail[k] for k in _PREFLIGHT_DIMENSIONS_V1}
        _preflight_limits_v1(self.delegated)
        # Remove delegated credit once, before any allocation/failed issue.
        self.transfer_debit = dict(self.delegated)
        for key, amount in self.delegated.items():
            observation.remaining[key] -= amount
        self.native_basis=observation.native_basis
        git = dict(executable=None,evidence_root=None) if not self.delegated['git_attempts'] else dict(
            executable=observation.git_executable,evidence_root=str(self.evidence/'git'))
        if self.native_basis is None:
            self.segments=tuple(observation.files[p] for p in sorted(observation.files,key=lambda s:s.encode('utf-8')))
            offset,files=0,[]
            for name,raw in zip(sorted(observation.files,key=lambda s:s.encode('utf-8')),self.segments,strict=True):
                files.append([name,offset,len(raw)]);offset+=len(raw)
            self.header=dict(identity=identity,allowance=self.delegated,deadline_ns=self.deadline_ns,git=git,files=files,
                directories=[[p,[list(v) for v in observation.directories[p]]] for p in sorted(observation.directories,key=lambda s:s.encode('utf-8'))])
            _,basis_entries=_preflight_header_v1(self.header,offset,identity)
        else:
            self.native_basis.check_live()
            _preflight_require_v1(type(host_lease) is _LinuxPreflightHostLeaseV1 and self.native_basis.lease is host_lease,
                'LINUX_V2_PARENT_ACTUAL_LEASE')
            self.segments=();offset=0
            self.header=dict(identity=identity,allowance=self.delegated,deadline_ns=self.deadline_ns,git=git,
                native_basis=dict(self.native_basis.descriptor),selection='NONE' if identity['original_position'] in (2,6) else 'ALL_WORKTREE')
            basis_entries=_preflight_header_v2(self.header,0,identity)
        self.basis_counts=MappingProxyType(dict(entries=basis_entries,bytes=offset))
        self.result_bound=_preflight_result_bound_v1(identity,native_basis=self.native_basis)
        self.raw_header = _preflight_encode_header_v1(self.header,self.limits,self._check,
            lambda size:self.parent_meter.buffers(size+2*self.result_bound+self.limits['chunk_bytes']))
        self.parent_meter.parse(self.raw_header)
        import struct
        self.prefix = struct.pack('>8sQQ',b'QTTPF01\n' if self.native_basis is None else b'QTTPF02\n',len(self.raw_header),offset)
        self.extent = 24+len(self.raw_header)+offset
        if self.native_basis is not None:
            _preflight_require_v1(self.extent<=1048576,'LINUX_V2_CHILD_FRAME_CAPACITY')
        if type(host_lease) is _LinuxPreflightHostLeaseV1:
            host_lease.reserve_input(self.identity['original_position'],self.extent,self.result_bound)
        # These immutable operands bind counts to the validated emitted frame,
        # independently of every child-reported ledger. No body copy is made.
        self._basis_frame = (basis_entries,offset,self.prefix,self.raw_header,self.segments)
        _preflight_require_v1(self.extent <= self.limits['frame_byte_limit']
            and self.result_bound <= self.limits['receiver_byte_limit']
            and 3*self.extent+2*self.result_bound <= self.limits['retained_buffer_bytes'], 'preflight measured transport demand')
        self.parent_meter.buffers(3*len(self.raw_header)+2*self.result_bound+self.limits['chunk_bytes'])
        self.controls = dict(zip(_PREFLIGHT_INPUT_KEYS_V1,(str(self.extent),str(self.limits['header_byte_limit']),
            ','.join(str(self.limits[k]) for k in ('lexical_units','depth','quoted_bytes','read_calls','chunk_bytes')),
            str(identity['original_position']),str(self.deadline_ns))))
    def _check(self):
        _preflight_require_v1((self.pid,self.thread) == (os.getpid(),threading.get_ident()), 'preflight foreign input owner')
        self.parent_meter.check()
        _preflight_require_v1(time.monotonic_ns() < (self.settlement_deadline_ns if self.process is not None
            and self.process.poll() is not None else self.deadline_ns), 'preflight input deadline')
    def _parts(self):
        yield self.prefix; yield self.raw_header; yield from self.segments
    def _proof_basis_counts(self):
        self._check()
        if self.native_basis is not None:self.native_basis.check_live()
        entries, body_bytes, prefix, header, segments = self._basis_frame
        counts = dict(self.basis_counts)
        _preflight_keys_v1(counts,('entries','bytes'))
        for value in counts.values(): _preflight_integer_v1(value)
        _preflight_require_v1(counts == dict(entries=entries,bytes=body_bytes)
            and (self.prefix,self.raw_header,self.segments) == (prefix,header,segments)
            and sum(len(part) for part in self.segments) == body_bytes
            and self.extent == 24+len(header)+body_bytes, 'preflight emitted basis binding differs')
        return counts
    def _stable(self):
        self._check()
        _preflight_require_v1(_scan_same_api_version(self.path.lstat()) == self.path_version
            and _scan_same_api_version(os.fstat(self.reader.fileno())) == self.descriptor_version
            and _preflight_transport_chain_v1(self.path.parent) == self.chain, 'preflight input identity drift')
    def _compare(self):
        self._stable()
        _preflight_require_v1(self.process is None or self.process.poll() is not None, 'preflight live input readback denied')
        self.reader.seek(0)
        for part in self._parts():
            offset = 0
            while offset < len(part):
                block = self.parent_meter.read(self.reader.fileno(), min(self.parent_meter.limits['chunk_bytes'],len(part)-offset))
                self.parent_meter.readback_bytes += len(block)
                _preflight_require_v1(block and block == part[offset:offset+len(block)], 'preflight input byte readback differs')
                offset += len(block)
        self.parent_meter.read(self.reader.fileno(),1,eof=True)
        self._stable()
    def __enter__(self):
        _preflight_require_v1(self.state == 'PREPARING','preflight input entry is single use')
        self.state = 'CREATING'
        try:
            return self._create()
        except BaseException as exc:
            self.state = 'HELD'
            errors = [exc]
            if self.reader is not None:
                try: self.reader.close()
                except BaseException as error: errors.append(error)
            _scan_raise_errors(errors)
    def _create(self):
        self._check()
        _preflight_chain_v1(self.path.parent); _preflight_chain_v1(self.evidence.parent)
        self.evidence.mkdir(exist_ok=False)
        if self.delegated['git_attempts']: (self.evidence/'git').mkdir(exist_ok=False)
        fd = None
        try:
            fd = os.open(self.path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|int(getattr(os,'O_BINARY',0)),0o600)
            for part in self._parts(): self.parent_meter.write(fd,part)
            os.fsync(fd)
            created = os.fstat(fd); _preflight_regular_v1(created)
            reader_fd = _open_regular_worktree_descriptor(self.path,nonblocking=True)
            try:
                _preflight_require_v1(_same_observed_file(created,os.fstat(reader_fd)), 'preflight writer/reader identity')
                self.reader = os.fdopen(reader_fd,'rb',buffering=0)
            except BaseException:
                os.close(reader_fd); raise
        finally:
            if fd is not None: os.close(fd)
        self.path_version = _scan_same_api_version(self.path.lstat())
        self.descriptor_version = _scan_same_api_version(os.fstat(self.reader.fileno()))
        self.chain = _preflight_transport_chain_v1(self.path.parent)
        self.evidence_chain = _preflight_transport_chain_v1(self.evidence)
        self._compare(); self.reader.seek(0)
        self.state = 'READY'
        return self
    def _claim(self, *, run_id,phase,command_index,argv,cwd):
        _preflight_require_v1(self.state == 'READY' and (run_id,phase,command_index,tuple(argv),str(cwd)) ==
            (self.identity['run_id'],'fast-preflight',self.identity['command_index'],tuple(self.identity['argv']),self.identity['repo_root']),
            'preflight launch association or replay')
        self._compare(); self.reader.seek(0)
        _preflight_require_v1(self.host_lease.check_launch(self.plan_entry,tuple(argv),self.environment,
            self.scratch_roots,self.deadline_ns) is None,'preflight native launch rejected')
        self.state = 'ISSUED'
        return self.reader
    def _attached(self,process):
        _preflight_require_v1(self.state == 'ISSUED' and type(process.pid) is int, 'preflight child association')
        self.process = process; self.state = 'ATTACHED'
        _preflight_require_v1(self.host_lease.check_child(process) is None,'preflight native child membership rejected')
    def _finished(self,process,native_exit):
        try:
            _preflight_require_v1(self.state == 'ATTACHED' and process is self.process and type(native_exit) is int
                and process.poll() is not None and process.returncode == native_exit,'preflight process termination unproven')
            _preflight_require_v1(self.host_lease.check_settled(process) is None,'preflight native settlement rejected')
            _preflight_require_v1(self.reader.tell() == self.extent,'preflight input cursor consumption')
            self._compare()
            self.result = _preflight_read_result_v1(self,process.pid,native_exit)
            self.state = 'CONSUMED'
        except BaseException:
            self.state = 'HELD'; raise
    def __exit__(self,exc_type,exc,tb):
        if self.process is not None and self.process.poll() is None:
            self.state = 'HELD'
            raise RuntimeError('preflight live process retains input custody') from exc
        errors = [] if exc is None else [exc]
        try: self._stable()
        except BaseException as error: errors.append(error)
        if self.reader is not None:
            try: self.reader.close()
            except BaseException as error: errors.append(error)
        # Keep failed input evidence; normal run cleanup owns successful deletion.
        if not errors and self.state == 'CONSUMED': self.state = 'CLOSED'
        _scan_raise_errors(errors)
        return False


def _preflight_read_result_v1(launch,pid,native_exit):
    launch._check()
    _preflight_require_v1(launch.evidence_chain == _preflight_transport_chain_v1(launch.evidence), 'preflight receiver ancestor identity')
    path = launch.evidence/'receiver.json'
    before = path.lstat(); _preflight_regular_v1(before)
    _preflight_require_v1(before.st_size <= launch.limits['receiver_byte_limit'], 'preflight receiver size')
    fd = _open_regular_worktree_descriptor(path,nonblocking=True)
    try:
        opened = os.fstat(fd); _preflight_regular_v1(opened)
        _preflight_require_v1(_same_observed_file(before,opened), 'preflight receiver descriptor identity')
        raw = launch.parent_meter.exact(fd,before.st_size)
        launch.parent_meter.read(fd,1,eof=True)
        _preflight_require_v1(_scan_same_api_version(path.lstat()) == _scan_same_api_version(before)
            and _scan_same_api_version(os.fstat(fd)) == _scan_same_api_version(opened), 'preflight receiver generation drift')
    finally:
        os.close(fd)
    result = launch.parent_meter.parse(raw,canonical_encoding=False)
    _preflight_verify_result_v1(result,identity=launch.identity,initial=launch.delegated,
        extent=launch.extent,pid=pid,native_exit=native_exit,basis_counts=launch._proof_basis_counts(),native_basis=launch.native_basis)
    launch._check()
    return result


def _preflight_verify_result_v1(result, *, identity, initial, extent, pid, native_exit, basis_counts, native_basis=None):
    shape = _preflight_result_v1(identity,None,None,None,False,False,None,False,None)
    if native_basis is not None:
        _preflight_require_v1(type(native_basis) is _LinuxImmutableSourceBasisV2,'LINUX_V2_VERIFIER_ACTUAL_BASIS')
        native_basis.check_live()
        shape.update(basis_kind=None,native_read_observation=None)
    _preflight_keys_v1(result,shape)
    for key in ('run_id','phase','command_index','original_position','argv'):
        _preflight_require_v1(type(result[key]) is type(identity[key]) and result[key] == identity[key], 'preflight receiver identity: '+key)
    _preflight_require_v1(result['cwd'] == identity['repo_root'] and type(result['pid']) is int and result['pid'] == pid
        and type(result['parent_pid']) is int and result['parent_pid'] == identity['parent_pid'], 'preflight receiver process/root')
    _preflight_require_v1(type(result['input_bytes_consumed']) is int and result['input_bytes_consumed'] == extent
        and result['decode_complete'] is True and result['application_entered'] is True
        and result['observation_complete'] is True and type(result['application_exit']) is int
        and result['application_exit'] == native_exit, 'preflight receiver incomplete application/transport')
    _preflight_require_v1(result['initial_limits'] == initial,'preflight copied/changed initial allowance')
    for k in ('initial_limits','remaining_limits','observed','reserved'):
        _preflight_keys_v1(result[k],_PREFLIGHT_DIMENSIONS_V1)
        for v in result[k].values(): _preflight_integer_v1(v)
    for k in initial:
        remaining,observed,reserved = (result[name][k] for name in ('remaining_limits','observed','reserved'))
        debit = initial[k]-remaining
        _preflight_require_v1(0 <= debit <= initial[k] and observed <= debit and reserved <= debit,
            'preflight receiver debit relation: '+k)
    _preflight_integer_v1(result['retained_entries'])
    _preflight_require_v1(result['retained_entries'] <= initial['entries']-result['remaining_limits']['entries'],
        'preflight receiver retained entry relation')
    _preflight_require_v1(result['failure_class'] == (None if native_exit == 0 else 'PREFLIGHT_APPLICATION_DENIED'),
        'preflight receiver failure/exit disagreement')
    # Only the fully decoded, normally returned and completely observed child
    # above has this lifecycle. Failed prefixes keep their unknown work intact.
    _preflight_keys_v1(basis_counts,('entries','bytes'))
    for value in basis_counts.values(): _preflight_integer_v1(value)
    observed, reserved = result['observed'], result['reserved']
    debits = {key:initial[key]-result['remaining_limits'][key] for key in initial}
    for key in ('attempts','git_attempts'):
        _preflight_require_v1(debits[key] == observed[key] == reserved[key],
            'preflight receiver exact accounting: '+key)
    for key in ('bytes','stdout_bytes','stderr_bytes','combined_output_bytes'):
        _preflight_require_v1(debits[key] == observed[key] and reserved[key] == 0,
            'preflight receiver exact accounting: '+key)
    _preflight_require_v1(observed['combined_output_bytes'] == observed['stdout_bytes']+observed['stderr_bytes'],
        'preflight receiver exact Git stream sum')
    _preflight_require_v1(reserved['entries'] == basis_counts['entries']
        and debits['entries'] == basis_counts['entries']+observed['entries']
        and result['retained_entries'] == debits['entries'], 'preflight receiver exact entry accounting')
    manifest_retained=0
    if native_basis is not None:
        native=result['native_read_observation']
        _preflight_keys_v1(native,('manifest_acquired_bytes','manifest_retained_bytes','source_bytes_read','owned_evidence_bytes_read'))
        for v in native.values():_preflight_integer_v1(v)
        _preflight_require_v1(result['basis_kind']=='NATIVE_IMMUTABLE_V2' and basis_counts['bytes']==0
            and basis_counts['entries']==native_basis.descriptor['catalog_entry_count']
            and native['manifest_acquired_bytes']==native['manifest_retained_bytes']==native_basis.descriptor['byte_length']
            and observed['bytes']==native['source_bytes_read']+native['owned_evidence_bytes_read'], 'LINUX_V2_EXACT_READ_ACCOUNTING')
        manifest_retained=native['manifest_retained_bytes']
    _preflight_require_v1(debits['retained_bytes'] == reserved['retained_bytes']
        == basis_counts['bytes']+manifest_retained+observed['retained_bytes'], 'preflight receiver exact retained-byte accounting')
    _preflight_require_v1(observed['bytes'] == observed['retained_bytes'],
        'preflight receiver complete acquisition byte accounting')


def _preflight_command_evidence_v1(receipt, paths, parent_meter):
    controls = dict(receipt.fixed_environment_controls)
    if not any(k in controls for k in _PREFLIGHT_INPUT_KEYS_V1):
        return
    _preflight_require_v1(all(k in controls for k in _PREFLIGHT_INPUT_KEYS_V1)
        and type(receipt.output_observation) is dict and type(parent_meter) is _PreflightTransportV1,
        'preflight command evidence projection or terminal grant missing')
    proof = receipt.output_observation.get('preflight')
    native_basis=getattr(parent_meter,'native_basis',None)
    _preflight_keys_v1(proof,('identity','initial_limits','input_bytes','receiver','row_total','parent_spend','parent_tail','basis_counts',
        *([] if native_basis is None else ['basis_kind','native_read_observation'])))
    if native_basis is not None:
        native_basis.check_live()
        _preflight_require_v1(proof['basis_kind']=='NATIVE_IMMUTABLE_V2' and type(proof['receiver']) is dict and
            proof['native_read_observation']==proof['receiver'].get('native_read_observation'),'LINUX_V2_PROOF_READ_ACCOUNTING')
    for name in ('row_total','parent_spend','parent_tail'):
        _preflight_keys_v1(proof[name],_PREFLIGHT_DIMENSIONS_V1)
        for value in proof[name].values(): _preflight_integer_v1(value)
    _preflight_limits_v1(proof['initial_limits'])
    _preflight_require_v1(all(proof['row_total'][k] == proof['parent_spend'][k]
        + proof['initial_limits'][k] + proof['parent_tail'][k] for k in _PREFLIGHT_DIMENSIONS_V1),
        'preflight parent/child allowance conservation')
    identity = proof['identity']
    _preflight_identity_v1(identity)
    _preflight_require_v1(identity['run_id'] == paths.run_id and identity['phase'] == receipt.phase
        and identity['command_index'] == receipt.command_index and tuple(identity['argv']) == receipt.argv
        and identity['repo_root'] == receipt.cwd == str(paths.repo_root)
        and identity['process_root'] == str(paths.process_root) and identity['evidence_root'] == str(paths.evidence_root)
        and _preflight_decimal_v1(controls['QTT_PREFLIGHT_INPUT_BYTES']) == proof['input_bytes'],
        'preflight command proof differs from actual plan/run')
    _preflight_verify_result_v1(proof['receiver'],identity=identity,initial=proof['initial_limits'],
        extent=proof['input_bytes'],pid=receipt.pid,native_exit=receipt.native_exit_code,basis_counts=proof['basis_counts'],
        native_basis=getattr(parent_meter,'native_basis',None))
    directory = paths.evidence_root/('preflight-'+str(receipt.command_index))
    _preflight_transport_chain_v1(directory)
    path,info = _require_direct_regular_evidence_file(directory,'receiver.json')
    _preflight_require_v1(info.st_size <= _preflight_result_bound_v1(identity,native_basis=getattr(parent_meter,'native_basis',None)),'preflight final receiver bound')
    expected = (json.dumps(proof['receiver'],indent=2,sort_keys=True)+'\n').encode('utf-8')
    fd = _open_regular_worktree_descriptor(path,nonblocking=True)
    errors = []
    try:
        opened = os.fstat(fd); _preflight_regular_v1(opened)
        _preflight_require_v1(_same_observed_file(info,opened),'preflight final receiver descriptor')
        raw = parent_meter.exact(fd,info.st_size)
        parent_meter.read(fd,1,eof=True)
        _preflight_require_v1(raw == expected and _scan_same_api_version(path.lstat()) == _scan_same_api_version(info)
            and _scan_same_api_version(os.fstat(fd)) == _scan_same_api_version(opened),
            'preflight final receiver differs from measured parent result')
    except BaseException as exc: errors.append(exc)
    try: os.close(fd)
    except BaseException as exc: errors.append(exc)
    try: parent_meter.check()
    except BaseException as exc: errors.append(exc)
    _scan_raise_errors(errors)


# Closed, prospective Linux first-phase profile. These literals are policy;
# observing a number or decoding a declaration never constructs a live lease.
_LINUX_PREFLIGHT_PROPERTIES_V1 = (
    ('Type','exec'), ('Restart','no'), ('RemainAfterExit','yes'), ('DynamicUser','yes'),
    ('UMask','0077'), ('NoNewPrivileges','yes'), ('CapabilityBoundingSet',''),
    ('AmbientCapabilities',''), ('PrivateDevices','yes'), ('PrivateNetwork','yes'),
    ('PrivateIPC','yes'), ('InaccessiblePaths','+/dev/shm +/dev/mqueue +/dev/hugepages'),
    ('PrivateTmp','yes'), ('ProtectSystem','strict'), ('ProtectHome','tmpfs'),
    ('ReadOnlyPaths','+/home +/root +/run +/run/user'),
    ('MountAPIVFS','yes'), ('ProtectProc','invisible'), ('ProtectControlGroups','yes'),
    ('ProtectKernelTunables','yes'), ('ProtectKernelModules','yes'), ('ProtectKernelLogs','yes'),
    ('RestrictSUIDSGID','yes'), ('RestrictRealtime','yes'), ('RestrictNamespaces','yes'),
    ('LockPersonality','yes'), ('RestrictAddressFamilies','AF_UNIX'),
    ('SystemCallArchitectures','native'), ('SystemCallFilter','~@mount @reboot @swap @raw-io @module'),
    ('MemoryAccounting','yes'), ('MemoryMax','6442450944'), ('MemorySwapMax','0'),
    ('TasksAccounting','yes'), ('TasksMax','64'), ('CPUAccounting','yes'),
    ('CPUQuota','200%'), ('CPUQuotaPeriodSec','100ms'), ('RuntimeMaxSec','3600'),
    ('TimeoutStartSec','60'), ('TimeoutStopSec','10'), ('KillMode','control-group'),
    ('SendSIGKILL','yes'), ('LimitCORE','0'), ('LimitNOFILE','1024'), ('LimitFSIZE','67108864'),
)
_LINUX_PREFLIGHT_SLICE_PROPERTIES_V1 = (
    ('Description','s','QTT PR298 first-phase engineering'), ('StopWhenUnneeded','b','false'),
    ('MemoryAccounting','b','true'), ('MemoryMax','t','6442450944'), ('MemorySwapMax','t','0'),
    ('TasksAccounting','b','true'), ('TasksMax','t','64'), ('CPUAccounting','b','true'),
    ('CPUQuotaPerSecUSec','t','2000000'), ('CPUQuotaPeriodUSec','t','100000'),
)


def _linux_preflight_path_v1(value):
    _preflight_require_v1(type(value) is str and len(value.encode('utf-8')) <= 4096
        and value.startswith('/') and not value.endswith('/') and
        all(re.fullmatch(r'[A-Za-z0-9_.-]+', part, flags=re.ASCII) and part not in ('.','..')
            for part in value[1:].split('/')), 'LINUX_PREFLIGHT_NATIVE_PATH')
    _preflight_require_v1(len(value[1:].split('/')) <= 64, 'LINUX_PREFLIGHT_NATIVE_PATH_DEPTH')
    return value


def _linux_preflight_name_v1(pid, origin_ns):
    _preflight_integer_v1(pid,positive=True); _preflight_integer_v1(origin_ns)
    name = 'qtt'+str(pid)+'n'+str(origin_ns)
    _preflight_require_v1(len(name) <= 64 and re.fullmatch(r'[A-Za-z0-9]+',name,flags=re.ASCII),
        'LINUX_PREFLIGHT_NATIVE_NAME')
    return name


def _linux_preflight_grants_v1(origin_ns):
    _preflight_integer_v1(origin_ns)
    mib, gib = 1024**2, 1024**3
    parent = dict(zip(_PREFLIGHT_DIMENSIONS_V1,(2_000_000,32*gib,4_000_000,2*gib,0,0,0,0),strict=True))
    transport = dict(zip(_PREFLIGHT_TRANSPORT_FIELDS_V1,
        (2*gib,16*mib,16_000_000,64,64*mib,2_000_000,2_000_000,65536,2*gib,8*mib),strict=True))
    rows = []
    for position in range(1,9):
        git = position in (1,3,5,7,8)
        rows.append(dict(limits=dict(zip(_PREFLIGHT_DIMENSIONS_V1,
            (2_000_000,16*gib,2_000_000,gib,64 if git else 0,
             16*mib if git else 0,16*mib if git else 0,32*mib if git else 0),strict=True)),
            parent_tail_reserve=dict.fromkeys(_PREFLIGHT_DIMENSIONS_V1,0),
            deadline_ns=origin_ns+3480*10**9,settlement_deadline_ns=origin_ns+3490*10**9,
            transport={**transport,'frame_byte_limit':512*mib,'header_byte_limit':8*mib,
                'lexical_units':4_000_000,'retained_buffer_bytes':gib},
            application_output_limits=dict(stdout_bytes=16*mib,stderr_bytes=16*mib,combined_output_bytes=32*mib)))
    return dict(native=transport,capture=dict(parent),terminal=dict(parent),rows=rows,
        parent_limits=dict(capture=dict(parent),terminal=dict(parent),transport={**transport,'frame_byte_limit':64*gib},
            deadline_ns=origin_ns+3490*10**9),candidate_limits=dict(entry_limit=100_000,
            snapshot_byte_limit=512*mib,read_byte_limit=64*gib,deadline_ns=origin_ns+3490*10**9),
        native_deadline_ns=origin_ns+3490*10**9,execution_deadline_ns=origin_ns+3500*10**9,
        settlement_deadline_ns=origin_ns+3720*10**9)


def _linux_preflight_storage_reservation_v1(extents, receiver_extents, page_size):
    """Prospective coexistence, including failed work; no deallocation refund."""
    _preflight_require_v1(type(extents) is tuple and len(extents) == 8 and
        type(receiver_extents) is tuple and len(receiver_extents) == 8,
        'LINUX_PREFLIGHT_EIGHT_STORAGE_RESERVATIONS')
    _preflight_integer_v1(page_size,positive=True)
    _preflight_require_v1(page_size & (page_size-1) == 0, 'LINUX_PREFLIGHT_PAGE_SIZE')
    mib = 1024**2
    for position,(extent,receiver) in enumerate(zip(extents,receiver_extents,strict=True),1):
        _preflight_integer_v1(extent); _preflight_integer_v1(receiver)
        _preflight_require_v1(24 <= extent <= 64*mib and receiver <= 8*mib,
            'LINUX_PREFLIGHT_FILE_INTERSECTION:'+str(position)+':'+str(extent))
    def pages(n): return ((n+page_size-1)//page_size)*page_size
    # Two application streams for all eight; two cumulative Git streams for five.
    allocated = sum(pages(n) for n in (*extents,*receiver_extents,*([16*mib]*26)))
    allocated += 16*mib+16*mib  # Ancillary envelope and unavailable metadata reserve.
    _preflight_require_v1(allocated <= 1024*mib, 'LINUX_PREFLIGHT_SHARED_RUNTIME_CAPACITY:'+str(allocated))
    return allocated


def _linux_preflight_ancestor_values_v1(memory, tasks, cpu, *, owned=False):
    """Only interpret successfully acquired applicable non-root interface bytes."""
    def decimal(raw):
        _preflight_require_v1(type(raw) is bytes and re.fullmatch(rb'(0|[1-9][0-9]*)\n',raw),
            'LINUX_PREFLIGHT_CONTROLLER_DECIMAL')
        return int(raw)
    values = []
    for raw, minimum in ((memory,6442450944),(tasks,64)):
        if raw == b'max\n':
            _preflight_require_v1(not owned,'LINUX_PREFLIGHT_OWNED_UNBOUNDED')
            values.append('max')
        else:
            n = decimal(raw)
            _preflight_require_v1(n == minimum if owned else n >= minimum,'LINUX_PREFLIGHT_ANCESTOR_CAPACITY')
            values.append(n)
    _preflight_require_v1(type(cpu) is bytes and re.fullmatch(rb'(max|[1-9][0-9]*) [1-9][0-9]*\n',cpu),
        'LINUX_PREFLIGHT_CPU_SHAPE')
    quota,period = cpu.rstrip(b'\n').split(b' '); period = int(period)
    if quota == b'max':
        _preflight_require_v1(not owned,'LINUX_PREFLIGHT_OWNED_UNBOUNDED')
        ratio = ('max',period)
    else:
        quota = int(quota)
        _preflight_require_v1((quota,period) == (200000,100000) if owned else quota >= 2*period,
            'LINUX_PREFLIGHT_CPU_CAPACITY')
        ratio = (quota,period)
    return (*values,ratio)


def _linux_preflight_service_argv_v1(*, name, private_root, runtime, control, spool, repository, installation,
        interpreter, startup_deadline_ns, environment, installation_source=None):
    _preflight_require_v1(type(name) is str and len(name) <= 64 and re.fullmatch(r'qtt[0-9]+n[0-9]+',name),
        'LINUX_PREFLIGHT_UNIT_NAME')
    for p in (private_root,runtime,control,spool,repository,installation,interpreter,
            '/dev/shm','/dev/mqueue','/dev/hugepages','/tmp','/var/tmp',
            '/home','/root','/run','/run/user'): _linux_preflight_path_v1(p)
    _preflight_integer_v1(startup_deadline_ns,positive=True)
    _preflight_require_v1(type(environment) is dict and environment == _linux_preflight_environment_v1(
        repository=repository,installation=installation,runtime=runtime,control=control),
        'LINUX_PREFLIGHT_LITERAL_ENVIRONMENT')
    _preflight_require_v1(runtime=='/run/'+name,'LINUX_PREFLIGHT_RUNTIME_LOGICAL_PATH')
    backing=runtime+'/payload'
    installation_source=control+'/installation' if installation_source is None else _linux_preflight_path_v1(installation_source)
    _preflight_require_v1(installation_source==control+'/installation' or (control=='/run/'+name[:-1]+'control/runtime-roundtrip-control' and name.endswith('1') and installation_source=='/run/'+name[:-1]+'control/installation'), 'LINUX_PREFLIGHT_INSTALLATION_SOURCE_OPERAND')
    bindings = [('/usr','/usr'),('/lib','/lib'),('/lib64','/lib64'),(repository,repository),
        (installation_source,installation),*( (control+'/'+n,control+'/'+n) for n in ('declaration','binding','release')),
        (spool,spool)]
    for a,b in bindings: _linux_preflight_path_v1(a); _linux_preflight_path_v1(b)
    properties = (*_LINUX_PREFLIGHT_PROPERTIES_V1,('RootDirectory',private_root),('WorkingDirectory',repository),
        ('BindReadOnlyPaths',' '.join(a+':'+b for a,b in bindings)),
        ('BindPaths',backing+':'+runtime+' '+backing+'/tmp:/tmp '+backing+'/var-tmp:/var/tmp'),
        ('ReadWritePaths','+'+runtime+' +/tmp +/var/tmp'),('StandardInput','null'),
        ('StandardOutput','append:'+spool+'/command-1.stdout.bin'),('StandardError','append:'+spool+'/command-1.stderr.bin'))
    entry = (interpreter,'-I','-B','-X','utf8',repository+'/tools/run_validation_gates.py',
        '--linux-preflight-enter','--phase','fast-preflight','--startup-deadline-ns',str(startup_deadline_ns))
    return tuple(['/usr/bin/systemd-run','--system','--no-ask-password','--expand-environment=no',
        '--unit='+name+'.service','--slice='+name+'.slice',*('--property='+k+'='+v for k,v in properties),
        *('--setenv='+k+'='+v for k,v in environment.items()),'--',*entry])


def _linux_preflight_environment_v1(*, repository, installation, runtime, control):
    for path in (repository,installation,runtime,control): _linux_preflight_path_v1(path)
    return dict(PATH=installation+'/bin:/usr/bin',LD_LIBRARY_PATH=installation+'/lib',LANG='C.UTF-8',LC_ALL='C.UTF-8',
        TZ='UTC',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8',
        TEMP=runtime+'/tmp',TMP=runtime+'/tmp',TMPDIR=runtime+'/tmp',
        QTT_VALIDATION_PROCESS_ROOT=runtime+'/process',QTT_VALIDATION_EVIDENCE_ROOT=runtime+'/evidence',
        QTT_LINUX_PREFLIGHT_CONTROL=control,QTT_LINUX_PREFLIGHT_RUNTIME=runtime,
        GITHUB_EVENT_NAME='pull_request',GITHUB_REPOSITORY='Q8Meow/QTT_New0526',
        GITHUB_HEAD_REF='repair/main-cumulative-v35-final-r5-local-20260922',GITHUB_BASE_REF='main',
        GITHUB_REF='refs/pull/298/merge',GITHUB_EVENT_PATH=control+'/declaration/event.json',
        CI='true',GITHUB_ACTIONS='true')


def _linux_preflight_child_environment_v1(fixed, environment, runtime):
    """Validate the original startup projection, without reintroducing stripped keys."""
    _preflight_require_v1(type(fixed) is dict and type(environment) is dict,
        'LINUX_PREFLIGHT_ENVIRONMENT_TYPE')
    exceptions = {PROCESS_ROOT_ENV,EVIDENCE_ROOT_ENV,'TEMP','TMP','TMPDIR'}
    _preflight_require_v1(all(environment.get(k) == v for k,v in fixed.items()
        if k not in exceptions and not k.upper().startswith('PYTHON')),
        'LINUX_PREFLIGHT_ENVIRONMENT')
    python = {k:v for k,v in environment.items() if k.upper().startswith('PYTHON')}
    cache = python.get('PYTHONPYCACHEPREFIX')
    _preflight_require_v1(type(cache) is str and Path(cache).is_absolute()
        and Path(cache).is_relative_to(Path(runtime))
        and python == dict(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',PYTHONPYCACHEPREFIX=cache),
        'LINUX_PREFLIGHT_PYTHON_PROJECTION')
    _preflight_require_v1(not any(k.upper().startswith(
        ('AWS_','AZURE_','SSH_','ACTIONS_','GH_TOKEN','GITHUB_TOKEN')) for k in environment),
        'LINUX_PREFLIGHT_CREDENTIAL_ENVIRONMENT')


class _LinuxPreflightQueriesV1:
    """Bounded observations of one owned native profile, using existing supervision."""
    def __init__(self, *, evidence_root, deadline_ns, reserved_output_bytes=0, startup_closeout_bytes=0):
        _preflight_require_v1(sys.platform == 'linux','LINUX_PREFLIGHT_PLATFORM')
        self.evidence_root = Path(evidence_root)
        self.deadline_ns = _preflight_integer_v1(deadline_ns,positive=True)
        self.pid,self.thread = os.getpid(),threading.get_ident()
        self.attempts,self.retained,self.failure = 0,0,None
        _preflight_integer_v1(reserved_output_bytes)
        self.retained_limit = 256*1024**2-reserved_output_bytes
        _preflight_require_v1(self.retained_limit > 0,'LINUX_PREFLIGHT_CONTROLLER_OUTPUT_RESERVATION')
        self.observations = []
        self.observation = None
        _preflight_require_v1(startup_closeout_bytes in (0,32*1024**2)
            and startup_closeout_bytes < self.retained_limit,'LINUX_PREFLIGHT_STARTUP_OUTPUT_RESERVATION')
        self.startup_output_limit=startup_closeout_bytes
        self.startup_output_bytes=0
        self.startup_fixture_reservation=0
        self.startup_fixture_bytes=0
        self.resource_spent_ns=0
        self.resource_depth=0
        self._startup_argv=None
        self.last_command_receipt=None
    def remaining_output(self):
        if self.resource_depth:
            return min(self.retained_limit-self.retained,
                self.startup_output_limit-self.startup_output_bytes-self.startup_fixture_reservation)
        return self.retained_limit-self.startup_output_limit-(self.retained-self.startup_output_bytes-self.startup_fixture_bytes)

    @contextmanager
    def owned_resource_phase(self):
        """All startup diagnostics and final units/handles share one 40s debit."""
        if self.resource_depth:
            yield
            return
        start=time.monotonic_ns()
        previous=self.deadline_ns
        _preflight_require_v1(self.resource_spent_ns < 40*10**9 and self.startup_output_limit,
            'LINUX_PREFLIGHT_OWNED_RESOURCE_ALLOWANCE_UNAVAILABLE')
        self.deadline_ns=min(previous,start+40*10**9-self.resource_spent_ns)
        self.resource_depth=1
        try:
            self.check(settling=True)
            yield
            self.check(settling=True)
        finally:
            self.resource_spent_ns+=time.monotonic_ns()-start
            self.resource_depth=0
            self.deadline_ns=previous

    def startup_diagnostic(self,scope,kind):
        """Only the failed attempt's fixed unit/status/journal/stop operands."""
        _preflight_require_v1(type(scope) is _LinuxPreflightScopeV1 and scope.query is self
            and scope.startup_error is not None and scope.service_created and self.resource_depth==1
            and scope.closeout_attempts < 6,'LINUX_PREFLIGHT_STARTUP_DIAGNOSTIC_CUSTODY')
        unit=scope.name+'.service'
        _preflight_require_v1(re.fullmatch(r'qtt[0-9]+n[0-9]+',scope.name) is not None,
            'LINUX_PREFLIGHT_STARTUP_DIAGNOSTIC_UNIT')
        observed=datetime.now(UTC)
        _preflight_require_v1(scope.attempt_utc is not None and observed>=scope.attempt_utc,
            'LINUX_PREFLIGHT_STARTUP_DIAGNOSTIC_INTERVAL')
        if kind=='status':
            argv=('/usr/bin/systemctl','show','--no-pager','--all',
                '--property='+','.join(scope._FAILED_STATUS),unit)
        elif kind=='journal':
            _preflight_require_v1(re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',scope.boot_id)
                is not None,'LINUX_PREFLIGHT_STARTUP_DIAGNOSTIC_BOOT')
            stamp=lambda value:value.strftime('%Y-%m-%d %H:%M:%S.%f UTC')
            # journalctl v255 parses a 32-hex boot descriptor, not /proc's UUID spelling.
            # Retain the original observed UUID for all manager identity checks.
            argv=('/usr/bin/journalctl','--system','--no-pager','--quiet','--boot='+scope.boot_id.replace('-',''),
                '--unit='+unit,'--since='+stamp(scope.attempt_utc),'--until='+stamp(observed),
                '--output=json','--all','--lines=201')
        elif kind=='stop':
            _preflight_require_v1(scope.owned_unit_status is not None and not scope.stop_attempted,
                'LINUX_PREFLIGHT_STARTUP_STOP_OWNERSHIP')
            scope.stop_attempted=True
            argv=('/usr/bin/systemctl','stop',unit)
        else:raise ValueError('unsupported startup diagnostic')
        scope.closeout_attempts+=1
        self.last_command_receipt=None
        self._startup_argv=argv
        error=None;raw=b'';stderr=b''
        try:
            raw=self.command(argv,settling=True)
        except BaseException as exc:
            error=exc
        finally:self._startup_argv=None
        receipt=self.last_command_receipt
        if receipt is not None and tuple(receipt.argv)==argv:
            raw=Path(receipt.stdout_path).read_bytes()
            stderr=Path(receipt.stderr_path).read_bytes()
        else:receipt=None
        complete=receipt is not None and all(receipt.output_observation.get(s,{}).get('complete')
            and not receipt.output_observation[s].get('overflow')
            and not receipt.output_observation[s].get('errors') for s in ('stdout','stderr'))
        success=complete and receipt.native_exit_code==0 and receipt.failure_class is None
        record=dict(kind=kind,argv=list(argv),observation_utc=observed.isoformat(),
            receipt=None if receipt is None else _json_compatible(receipt),
            command_settled=receipt is not None and not _command_requires_process_retention_v1(receipt),
            error=None if error is None else repr(error),complete=complete,success=success)
        if kind=='journal':
            records=raw.splitlines()
            record.update(entry_count=len(records),complete=bool(success and len(records)<201))
            try:
                decoded=[json.loads(row) for row in records]
                _preflight_require_v1(all(type(row) is dict for row in decoded),
                    'LINUX_PREFLIGHT_STARTUP_JOURNAL_RECORD')
                record['entries']=decoded
            except BaseException as exc:
                record.update(complete=False,decode_error=repr(exc))
        scope.history.append(dict(startup_diagnostic=record))
        return record,raw,stderr
    def check(self, *, settling=False):
        if self.failure is not None and not settling: raise self.failure
        _preflight_require_v1((os.getpid(),threading.get_ident()) == (self.pid,self.thread)
            and time.monotonic_ns() < self.deadline_ns,'LINUX_PREFLIGHT_QUERY_CUSTODY_OR_DEADLINE')
        self.attempts += 1
        if self.observation is not None:
            self.observation.reserve('attempts')
        _preflight_require_v1(self.attempts <= 32768,'LINUX_PREFLIGHT_QUERY_ATTEMPTS')
    def record(self, kind, operand, raw):
        if self.observation is not None:
            if self.observation.native_read_observation is not None:
                self.observation.native_read_observation['owned_evidence_bytes_read']+=len(raw)
            self.observation.received('bytes',len(raw))
            self.observation.reserve('retained_bytes',len(raw))
            self.observation.observed['retained_bytes'] += len(raw)
        self.retained += len(raw)
        if self.resource_depth:self.startup_output_bytes+=len(raw)
        _preflight_require_v1(self.remaining_output()>=0,'LINUX_PREFLIGHT_PARTITIONED_QUERY_OUTPUT')
        _preflight_require_v1(self.retained <= self.retained_limit,'LINUX_PREFLIGHT_QUERY_OUTPUT')
        path = self.evidence_root/('native-response-'+str(len(self.observations)+1)+'.bin')
        _atomic_write_bytes_v1(path,raw)
        self.observations.append(dict(kind=kind,operand=operand,path=str(path),bytes=len(raw)))
        return raw
    def read(self,path,*,settling=False):
        self.check(settling=settling)
        _preflight_require_v1(self.remaining_output() >= 1048576,
            'LINUX_PREFLIGHT_NATIVE_RESPONSE_RESERVATION')
        p = Path(path); before = p.lstat()
        _preflight_require_v1(stat.S_ISREG(before.st_mode) and not stat.S_ISLNK(before.st_mode),
            'LINUX_PREFLIGHT_NATIVE_READ_TYPE:'+str(path))
        fd = os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
        raw = bytearray()
        recorded = False
        try:
            opened = os.fstat(fd)
            _preflight_require_v1((before.st_dev,before.st_ino) == (opened.st_dev,opened.st_ino),
                'LINUX_PREFLIGHT_NATIVE_READ_IDENTITY')
            raw = bytearray()
            while True:
                self.check(settling=settling)
                block = os.read(fd,min(65536,1048577-len(raw)))
                if not block: break
                raw.extend(block)
                if len(raw) > 1048576:
                    self.record('failed-read-prefix',str(path),bytes(raw[:1048576]))
                    recorded = True
                    _preflight_require_v1(False,'LINUX_PREFLIGHT_QUERY_RESPONSE')
            after = p.lstat()
            _preflight_require_v1((after.st_dev,after.st_ino) == (opened.st_dev,opened.st_ino),
                'LINUX_PREFLIGHT_NATIVE_READ_REPLACED')
            result = self.record('read',str(path),bytes(raw))
            recorded = True
            self.check(settling=settling)
            return result
        except BaseException as exc:
            if self.failure is None: self.failure = exc
            if not recorded and len(raw) <= 1048576:
                self.record('failed-read-prefix',str(path),bytes(raw))
            raise
        finally: os.close(fd)
    def command(self,argv,*,settling=False,cwd=None,git_environment=None):
        self.check(settling=settling)
        _preflight_require_v1(type(argv) is tuple and argv and (argv[0] in (
            '/usr/bin/systemctl','/usr/bin/systemd-run','/usr/bin/systemd-analyze',
            '/usr/bin/busctl','/usr/bin/mount','/usr/bin/umount','/usr/bin/git')
            or (argv[0]=='/usr/bin/journalctl' and argv==self._startup_argv and self.resource_depth==1)),
            'LINUX_PREFLIGHT_ADMINISTRATIVE_PROGRAM')
        for value in argv:
            _preflight_require_v1(type(value) is str and '\0' not in value and '\n' not in value,
                'LINUX_PREFLIGHT_ADMINISTRATIVE_ARGUMENT')
        environment = dict(PATH='/usr/bin',LANG='C.UTF-8',LC_ALL='C.UTF-8')
        selected_cwd = Path('/') if cwd is None else Path(_linux_preflight_path_v1(str(cwd)))
        if git_environment is not None:
            _preflight_require_v1(argv[0] == '/usr/bin/git' and type(git_environment) is dict
                and all(k.startswith('GIT_') for k in git_environment),
                'LINUX_PREFLIGHT_GIT_OWNER_ENVIRONMENT')
            environment.update(git_environment)
        remaining_output = self.remaining_output()
        _preflight_require_v1(remaining_output >= 2,'LINUX_PREFLIGHT_QUERY_OUTPUT_EXHAUSTED')
        stream_limit = min(1048576,remaining_output//2)
        token = _LINUX_PREFLIGHT_PROCESS_V1.set(None)
        try:
            observation = {}
            receipt = supervise_command(argv,cwd=selected_cwd,run_id='linux-admin-'+str(self.pid),phase='fast-preflight-native-query',
                command_index=self.attempts,evidence_root=self.evidence_root,timeout_seconds=10,
                execution_deadline_ns=self.deadline_ns,environment=environment,
                output_limits=dict(stdout_bytes=stream_limit,stderr_bytes=stream_limit,combined_output_bytes=2*stream_limit),
                output_observation=observation,mirror_stdout=False,mirror_stderr=False)
        finally: _LINUX_PREFLIGHT_PROCESS_V1.reset(token)
        raw = Path(receipt.stdout_path).read_bytes(); error = Path(receipt.stderr_path).read_bytes()
        self.last_command_receipt=receipt
        self.retained += len(raw)+len(error)
        if self.resource_depth:self.startup_output_bytes+=len(raw)+len(error)
        self.observations.append(dict(kind='command',argv=argv,receipt=_json_compatible(receipt)))
        _preflight_require_v1(self.retained <= self.retained_limit,'LINUX_PREFLIGHT_QUERY_OUTPUT')
        _preflight_require_v1(not receipt.failure_class and receipt.native_exit_code == 0,
            'LINUX_PREFLIGHT_NATIVE_COMMAND:'+repr(argv)+':'+str(receipt.native_exit_code)+':'+repr(error))
        self.check(settling=settling)
        return raw


def _linux_preflight_mounts_v1(raw):
    _preflight_require_v1(type(raw) is bytes and len(raw) <= 1048576,'LINUX_PREFLIGHT_MOUNT_RESPONSE')
    rows = []
    def decode(value):
        return re.sub(r'\\([0-7]{3})',lambda match: chr(int(match[1],8)),value)
    for line in raw.decode('utf-8','strict').splitlines():
        fields = line.split(' ')
        _preflight_require_v1(fields.count('-') == 1,'LINUX_PREFLIGHT_MOUNT_SHAPE')
        split = fields.index('-')
        _preflight_require_v1(split >= 6 and len(fields) == split+4,'LINUX_PREFLIGHT_MOUNT_FIELDS')
        rows.append(dict(id=int(fields[0]),parent=int(fields[1]),device=fields[2],root=decode(fields[3]),
            path=decode(fields[4]),options=frozenset(fields[5].split(',')),fs=fields[split+1],
            source=decode(fields[split+2]),super_options=frozenset(fields[split+3].split(','))))
    _preflight_require_v1(len(rows) <= 4096 and len({r['id'] for r in rows}) == len(rows),'LINUX_PREFLIGHT_MOUNT_ROSTER')
    return tuple(rows)


def _linux_preflight_project_chain_v1(root_fd, logical, query):
    """Controller projects the actual held service namespace, including '/'."""
    _linux_preflight_path_v1(logical)
    _preflight_require_v1(len(logical[1:].split('/')) <= 64,'LINUX_PREFLIGHT_PROJECTION_DEPTH')
    owned = os.dup(root_fd)
    try:
        result = [('/',_preflight_stamp_v1(os.fstat(owned)))]
        prefix = ''
        for component in logical[1:].split('/'):
            query.check()
            opened = os.open(component,os.O_PATH|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=owned)
            os.close(owned); owned = opened
            info = os.fstat(owned)
            _preflight_require_v1(stat.S_ISDIR(info.st_mode),'LINUX_PREFLIGHT_PROJECT_DIRECTORY')
            prefix += '/'+component
            result.append((prefix,_preflight_stamp_v1(info)))
        return tuple(result)
    finally: os.close(owned)


def _linux_preflight_process_identity_v1(pid,query,*,settling=False):
    _preflight_integer_v1(pid,positive=True)
    raw = query.read('/proc/'+str(pid)+'/stat',settling=settling)
    close = raw.rfind(b') ')
    _preflight_require_v1(raw.startswith(str(pid).encode()+b' (') and close > 0,'LINUX_PREFLIGHT_PROCESS_STAT')
    fields = raw[close+2:].split()
    _preflight_require_v1(len(fields) >= 20 and fields[19].isdigit(),'LINUX_PREFLIGHT_PROCESS_START')
    namespaces = {}
    for name in ('mnt','cgroup','ipc','net','pid','user'):
        query.check(settling=settling)
        info = os.stat('/proc/'+str(pid)+'/ns/'+name)
        namespaces[name] = (info.st_dev,info.st_ino)
    return dict(pid=pid,start=int(fields[19]),namespaces=namespaces)


class _LinuxPreflightTailV1:
    """One actual manager-owned regular spool; live EOF is only pending data."""
    def __init__(self,path,*,original_evidence=False):
        self.path = Path(path)
        self.original_evidence = original_evidence
        before = self.path.lstat()
        _preflight_require_v1(stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
            'LINUX_PREFLIGHT_SPOOL_TYPE')
        self.stream = self.path.open('rb',buffering=0)
        opened = os.fstat(self.stream.fileno())
        _preflight_require_v1((before.st_dev,before.st_ino) == (opened.st_dev,opened.st_ino),
            'LINUX_PREFLIGHT_SPOOL_IDENTITY')
        self.identity = (opened.st_dev,opened.st_ino)
    def fileno(self):
        info = os.fstat(self.stream.fileno()); path = self.path.lstat()
        _preflight_require_v1((info.st_dev,info.st_ino) == (path.st_dev,path.st_ino) == self.identity
            and info.st_nlink == path.st_nlink == 1 and max(info.st_size,path.st_size) <= 67108864,
            'LINUX_PREFLIGHT_SPOOL_CUSTODY_OR_EXTENT')
        return self.stream.fileno()
    def close(self): self.stream.close()


def _linux_preflight_control_read_v1(path, *, deadline_ns, pending=False, query=None):
    """Initial absence is bounded pending; a published failure is never retried."""
    for attempt in range(600 if pending else 1):
        _preflight_require_v1(time.monotonic_ns() < deadline_ns,'LINUX_PREFLIGHT_STARTUP_DEADLINE')
        if query is not None: query.check()
        try: before = Path(path).lstat()
        except FileNotFoundError:
            if not pending: raise
            time.sleep(0.1)
            continue
        _preflight_require_v1(stat.S_ISREG(before.st_mode) and before.st_uid == 0 and
            stat.S_IMODE(before.st_mode) == 0o444 and before.st_nlink == 1 and before.st_size <= 1048576,
            'LINUX_PREFLIGHT_CONTROL_PERMISSIONS_OR_EXTENT')
        chain = _preflight_chain_v1(Path(path).parent)
        fd = os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:
            opened = os.fstat(fd)
            _preflight_require_v1(_scan_same_api_version(before) == _scan_same_api_version(opened),
                'LINUX_PREFLIGHT_CONTROL_OPEN')
            raw = bytearray()
            while len(raw) < before.st_size:
                _preflight_require_v1(time.monotonic_ns() < deadline_ns,'LINUX_PREFLIGHT_CONTROL_DEADLINE')
                part = os.read(fd,min(65536,before.st_size-len(raw)))
                _preflight_require_v1(bool(part),'LINUX_PREFLIGHT_CONTROL_TRUNCATED')
                raw.extend(part)
            _preflight_require_v1(os.read(fd,1) == b'' and
                _scan_same_api_version(os.fstat(fd)) == _scan_same_api_version(opened) and
                _scan_same_api_version(Path(path).lstat()) == _scan_same_api_version(before) and
                _preflight_chain_v1(Path(path).parent) == chain,'LINUX_PREFLIGHT_CONTROL_DRIFT')
        finally: os.close(fd)
        _preflight_require_v1(time.monotonic_ns() < deadline_ns,'LINUX_PREFLIGHT_CONTROL_LATE')
        def pairs(values):
            result = {}
            for key,value in values:
                _preflight_require_v1(key not in result,'LINUX_PREFLIGHT_CONTROL_DUPLICATE')
                result[key] = value
            return result
        if query is not None: query.record('control',str(path),bytes(raw))
        value = json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda text: (_ for _ in ()).throw(ValueError(text)))
        _preflight_require_v1(type(value) is dict,'LINUX_PREFLIGHT_CONTROL_RECORD')
        return value, _scan_same_api_version(before), chain
    raise RuntimeError('LINUX_PREFLIGHT_STARTUP_PUBLICATION_UNAVAILABLE')


def _linux_preflight_cgroup_path_v1(pid,query):
    raw = query.read('/proc/'+str(pid)+'/cgroup')
    _preflight_require_v1(raw.count(b'\n') == 1 and raw.startswith(b'0::/'),'LINUX_PREFLIGHT_UNIFIED_MEMBERSHIP')
    value = raw[3:-1].decode('ascii','strict')
    _linux_preflight_path_v1(value)
    return value


def _linux_preflight_status_v1(pid,query,*,credentials=False):
    raw = query.read('/proc/'+str(pid)+'/status')
    values = {}
    for line in raw.decode('ascii','strict').splitlines():
        key,sep,value = line.partition(':')
        if key in ('CapInh','CapPrm','CapEff','CapBnd','CapAmb','NoNewPrivs'):
            _preflight_require_v1(sep and key not in values,'LINUX_PREFLIGHT_STATUS_DUPLICATE')
            values[key] = value.strip()
    _preflight_require_v1(set(values) == {'CapInh','CapPrm','CapEff','CapBnd','CapAmb','NoNewPrivs'}
        and values['NoNewPrivs'] == '1' and all(int(values[k],16) == 0 for k in values if k != 'NoNewPrivs'),
        'LINUX_PREFLIGHT_CAPABILITY_OR_NO_NEW_PRIVILEGES')
    if credentials:
        for key in ('Uid','Gid'):
            rows=[line.split(':',1)[1].split() for line in raw.decode('ascii','strict').splitlines() if line.startswith(key+':')]
            _preflight_require_v1(len(rows)==1 and len(rows[0])==4 and all(re.fullmatch(r'[0-9]+',v) for v in rows[0])
                and len(set(rows[0]))==1 and int(rows[0][0])>0,'LINUX_PREFLIGHT_KERNEL_CREDENTIALS:'+key)
            values[key]=int(rows[0][0])
    return values


def _linux_preflight_mount_containment_v1(*, pid, process, runtime, query, root_fd=None,
        mounts=None, private_root=None, mappings=None, history=None, service_process=None):
    """One bracketed, descriptor-selected view; never infer cover from row order."""
    parents=('/home','/root','/run','/run/user')
    allowed={str(runtime),'/tmp','/var/tmp','/dev','/dev/pts','/proc','/sys'}
    record=dict(pid=pid,parents=[],covered=[],violations=[],descriptors=[])
    owned_root=None;result={};errors=[]
    def require(value,label):
        _preflight_require_v1(value,'LINUX_PREFLIGHT_CONTAINMENT_'+label)
    def checked(operation,*args,**kwargs):
        query.check();return operation(*args,**kwargs)
    def acquire(operation,*args,**kwargs):
        # The close debit is consumed before acquisition and is never refunded.
        query.check();query.check();return operation(*args,**kwargs)
    def failure(where,exc):
        errors.append(exc);record['violations'].append(dict(operand=where,error=repr(exc)))
    def close(fd):
        try:os.close(fd)
        except BaseException as exc:
            retained=getattr(query,'containment_retained_descriptors',[])
            retained.append(fd);query.containment_retained_descriptors=retained
            failure('close:'+str(fd),exc)
    def stamp(info):
        return (info.st_dev,info.st_ino,info.st_mode,info.st_uid,info.st_gid)
    def within(child,parent):return parent=='/' or child==parent or child.startswith(parent+'/')
    def fdfields(raw):
        rows=[line.partition(b':')[2].strip() for line in raw.splitlines() if line.partition(b':')[0]==b'mnt_id']
        require(len(rows)==1 and re.fullmatch(rb'[1-9][0-9]*',rows[0]) is not None,'FDINFO_MOUNT_ID')
        return int(rows[0])
    def walk(path):
        _linux_preflight_path_v1(path)
        fd=acquire(os.dup,view)
        try:
            chain=[('/',_preflight_stamp_v1(checked(os.fstat,fd)))];prefix=''
            for part in path[1:].split('/'):
                new=acquire(os.open,part,os.O_PATH|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd)
                previous=fd;fd=new;close(previous)
                info=checked(os.fstat,fd)
                require(stat.S_ISDIR(info.st_mode),'DIRECTORY:'+path)
                prefix+='/'+part;chain.append((prefix,_preflight_stamp_v1(info)))
            return fd,chain
        except BaseException:
            close(fd);raise
    def witness(path):
        fd,chain=walk(path)
        try:
            before=checked(os.fstat,fd)
            raw=query.read('/proc/self/fdinfo/'+str(fd))
            identifier=fdfields(raw)
            require(identifier in by_id,'FDINFO_UNKNOWN_MOUNT:'+path)
            selected=by_id[identifier]
            require(within(path,selected['path']),'FDINFO_COVERING_PATH:'+path)
            require(str(os.major(before.st_dev))+':'+str(os.minor(before.st_dev))==selected['device'],
                'FDINFO_DEVICE:'+path)
            after=checked(os.fstat,fd)
            require(stamp(before)==stamp(after),'OBJECT_CHANGED:'+path)
            second,current=walk(path)
            try:require(chain==current,'CHAIN_CHANGED:'+path)
            finally:close(second)
            return dict(chain=chain,identity=(before.st_dev,before.st_ino),mount={
                k:sorted(v) if isinstance(v,frozenset) else v for k,v in selected.items()}),before,identifier
        finally:close(fd)
    try:
        query.check()
        _linux_preflight_path_v1(str(runtime))
        require(_linux_preflight_process_identity_v1(pid,query)==process,'PROCESS_BEFORE')
        _linux_preflight_status_v1(pid,query)
        if service_process is not None and service_process['pid']!=pid:
            require(_json_compatible(_linux_preflight_process_identity_v1(service_process['pid'],query))==
                _json_compatible(service_process),'SERVICE_PROCESS_BEFORE')
        cgroup=_linux_preflight_cgroup_path_v1(pid,query)
        if root_fd is None:
            require(pid==os.getpid(),'CURRENT_ROOT_OWNER')
            owned_root=acquire(os.open,'/',os.O_PATH|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
            view=owned_root
        else:view=root_fd
        root_before=checked(os.fstat,view)
        require(stamp(root_before)==stamp(checked(os.stat,'/proc/'+str(pid)+'/root')),'VIEW_ROOT_BEFORE')
        before=(_linux_preflight_mounts_v1(query.read('/proc/'+str(pid)+'/mountinfo'))
            if mounts is None else mounts)
        require(type(before) is tuple and 0<len(before)<=4096,'MOUNT_ROSTER')
        by_id={row['id']:row for row in before};require(len(by_id)==len(before),'DUPLICATE_ID')
        by_path={}
        for row in before:
            require(type(row['id']) is int and row['id']>0 and type(row['parent']) is int and row['parent']>0,
                'MOUNT_IDENTIFIERS')
            for path in (row['path'],row['root']):
                if path!='/':_linux_preflight_path_v1(path)
            require(re.fullmatch(r'[0-9]+:[0-9]+',row['device']) is not None,'MOUNT_DEVICE')
            by_path.setdefault(row['path'],[]).append(row)
            current=row;seen=set()
            while current['id'] in by_id:
                require(current['id'] not in seen,'MOUNT_GRAPH_CYCLE')
                seen.add(current['id']);parent=by_id.get(current['parent'])
                if parent is None:
                    require(current['path']=='/','MOUNT_GRAPH_ORPHAN');break
                require(within(current['path'],parent['path']),'MOUNT_GRAPH_PATH')
                current=parent
        require(sum(row['parent'] not in by_id for row in before)==1,'MOUNT_GRAPH_ROOT')
        for path in parents:
            row=dict(path=path,observation=None,error=None)
            try:
                observed,info,identifier=witness(path);row['observation']=observed
                row['stat']=dict(zip(('device','inode','mode','uid','gid'),stamp(info),strict=True))
                require('ro' in observed['mount']['options'] and 'rw' not in observed['mount']['options'],
                    'PARENT_WRITABLE:'+path)
                require((info.st_uid,info.st_gid)==(0,0) and stat.S_IMODE(info.st_mode)==(0o700 if path=='/root' else 0o755),
                    'PARENT_OWNER_MODE:'+path)
                if private_root is not None:
                    # Only the controller supplies its original private-root owner.
                    host_fd=acquire(os.open,private_root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
                    try:
                        host_root=checked(os.fstat,host_fd)
                        for part in path[1:].split('/'):
                            new=acquire(os.open,part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=host_fd)
                            previous=host_fd;host_fd=new;close(previous)
                        host=checked(os.fstat,host_fd)
                        require(stamp(host)==stamp(info) and host.st_dev==host_root.st_dev,'PARENT_HOST_OBJECT:'+path)
                        native=_LinuxSourceNativeV2()
                        acl=native.acl(host_fd,attempt=lambda name:query.check(),delivered=lambda count:None)
                        query.record('containment-parent-acl',path,_preflight_canonical_v1(native.last_acl))
                        require(acl==(None,None),'PARENT_ACL:'+path)
                    finally:close(host_fd)
                else:
                    require(type(mappings) is dict and path in mappings,'PARENT_MAPPING_MISSING:'+path)
                    expected=mappings[path]
                    require(type(expected) is dict and set(expected)=={'chain','identity','mount'}
                        and _json_compatible(observed)==_json_compatible(expected),'PARENT_MAPPING_CHANGED:'+path)
                result[path]=observed
            except BaseException as exc:row['error']=repr(exc);failure(path,exc)
            record['parents'].append(row)
        lower_ids=set()
        for row in before:
            if 'rw' not in row['options']:continue
            path=row['path']
            if path in allowed:
                if row['fs'] not in ('tmpfs','devpts','proc','sysfs') or len(by_path[path])!=1:
                    failure(path,ValidationReliabilityError('ENGVR_PREPUBLICATION_CUSTODY_FAILED',
                        'LINUX_PREFLIGHT_UNACCOUNTED_WRITABLE_MOUNT:'+path))
                continue
            evidence=dict(lower={k:sorted(v) if isinstance(v,frozenset) else v for k,v in row.items()},visible=None,error=None)
            try:
                require(len(by_path[path])>1,'UNACCOUNTED_WRITABLE_MOUNT:'+path)
                visible,info,identifier=witness(path);evidence['visible']=visible
                require(identifier!=row['id'] and by_id[identifier]['path']==path
                    and 'ro' in by_id[identifier]['options'] and 'rw' not in by_id[identifier]['options'],
                    'VISIBLE_WRITABLE_OR_UNRELATED:'+path)
                current=by_id[identifier];ancestors=[]
                while current['parent'] in by_id:
                    current=by_id[current['parent']];ancestors.append(current)
                require(row['id'] not in {a['id'] for a in ancestors},'LOWER_IS_VISIBLE_ANCESTOR:'+path)
                require(row['parent'] in {a['id'] for a in ancestors},'COVER_ANCESTRY:'+path)
                between=ancestors[:next(i for i,a in enumerate(ancestors) if a['id']==row['parent'])]
                require(any(a['path']!=path and a['path']!=by_id[row['parent']]['path']
                    and within(path,a['path']) and within(a['path'],by_id[row['parent']]['path'])
                    and 'ro' in a['options'] and 'rw' not in a['options'] for a in between),
                    'COVER_INTERVENING_MOUNT:'+path)
                lower_ids.add(row['id'])
            except BaseException as exc:evidence['error']=repr(exc);failure(path,exc)
            record['covered'].append(evidence)
        if lower_ids:
            # No descriptor inherited beyond standard handles, nor any held
            # descriptor into an excluded lower mount. Keep the iterator live.
            directory=acquire(os.scandir,'/proc/'+str(pid)+'/fd')
            try:
                for count,entry in enumerate(directory,1):
                    require(count<=1024 and re.fullmatch(r'[0-9]+',entry.name) is not None,'DESCRIPTOR_ROSTER')
                    fd=int(entry.name)
                    raw=query.read('/proc/'+str(pid)+'/fdinfo/'+entry.name)
                    identifier=fdfields(raw)
                    flags=[line.partition(b':')[2].strip() for line in raw.splitlines() if line.partition(b':')[0]==b'flags']
                    require(len(flags)==1 and re.fullmatch(rb'[0-7]+',flags[0]) is not None,'DESCRIPTOR_FLAGS')
                    value=int(flags[0],8);record['descriptors'].append(dict(fd=fd,mount_id=identifier,flags=value))
                    require(identifier not in lower_ids and (fd<=2 or value&os.O_CLOEXEC),'INHERITED_OR_COVERED_DESCRIPTOR')
            finally:
                try:directory.close()
                except BaseException as exc:
                    retained=getattr(query,'containment_retained_descriptors',[])
                    retained.append(directory);query.containment_retained_descriptors=retained
                    failure('descriptor-roster-close',exc)
        after=_linux_preflight_mounts_v1(query.read('/proc/'+str(pid)+'/mountinfo'))
        require({r['id']:r for r in after}==by_id,'MOUNT_TABLE_CHANGED')
        require(stamp(checked(os.fstat,view))==stamp(root_before)
            and stamp(checked(os.stat,'/proc/'+str(pid)+'/root'))==stamp(root_before),'VIEW_ROOT_AFTER')
        require(_linux_preflight_process_identity_v1(pid,query)==process,'PROCESS_AFTER')
        _linux_preflight_status_v1(pid,query)
        require(_linux_preflight_cgroup_path_v1(pid,query)==cgroup,'CGROUP_CHANGED')
        if service_process is not None and service_process['pid']!=pid:
            require(_json_compatible(_linux_preflight_process_identity_v1(service_process['pid'],query))==
                _json_compatible(service_process),'SERVICE_PROCESS_AFTER')
        query.check()
    except BaseException as exc:failure('view',exc)
    finally:
        if owned_root is not None:close(owned_root)
    record['complete']=not errors
    if history is not None:history.append(dict(mount_containment=record))
    try:query.record('mount-containment',str(pid),_preflight_canonical_v1(record))
    except BaseException as exc:failure('evidence',exc);record['complete']=False
    if errors:
        error=ValidationReliabilityError('ENGVR_PREPUBLICATION_CUSTODY_FAILED',
            'LINUX_PREFLIGHT_MOUNT_CONTAINMENT:'+repr(record['violations']))
        if query.failure is None:query.failure=error
        raise error
    return result


class _LinuxPreflightHostLeaseV1(_PreflightHostLeaseV1):
    """Actual unprivileged service identity; cannot be issued by a JSON approval."""
    def __init__(self, *, binding, control_path, runtime, query, declaration_chain, declaration_version, parent_pid=None):
        _preflight_require_v1(sys.platform == 'linux' and os.geteuid() != 0,'LINUX_PREFLIGHT_SERVICE_CONTEXT')
        self.binding,self.control_path,self.runtime,self.query = binding,Path(control_path),Path(runtime),query
        self.parent_pid = parent_pid
        if parent_pid is not None:
            _preflight_require_v1(type(parent_pid) is int and parent_pid==os.getppid()==binding['process']['pid']
                and binding.get('native_basis',{}).get('kind')=='NATIVE_IMMUTABLE_V2','LINUX_V2_ORIGINAL_CHILD_PARENT')
        self.pid,self.thread = os.getpid(),threading.get_ident()
        self.failure = None
        self.children = {}
        self.reserved_inputs = {}
        self.storage_reservation = None
        self.declaration_chain,self.declaration_version = declaration_chain,declaration_version
        self.root = Path(binding['repository'])
        self.index = Path(binding['index'])
        self.deadline_ns = binding['grants']['native_deadline_ns']
        self.initial = _linux_preflight_process_identity_v1(self.pid,query)
        self.cgroup = _linux_preflight_cgroup_path_v1(self.pid,query)
        self.control_version = _scan_same_api_version(self.control_path.lstat())
        self.control_chain = _preflight_chain_v1(self.control_path.parent)
        self.check_parent(self.root,self.index)
    def _check(self):
        if self.failure is not None: raise self.failure
        self.query.check()

        _preflight_require_v1((self.pid,self.thread) == (os.getpid(),threading.get_ident())
            and time.monotonic_ns() < self.deadline_ns,'LINUX_PREFLIGHT_SERVICE_OWNER')
    def check_parent(self,root,index_path):
        try:
            self._check()
            b = self.binding
            actual = _linux_preflight_process_identity_v1(self.pid,self.query)
            if self.parent_pid is None:
                _preflight_require_v1(_json_compatible(actual)==b['process'] and actual==self.initial,
                    'LINUX_PREFLIGHT_ORIGINAL_SERVICE_PROCESS')
            else:
                parent=_linux_preflight_process_identity_v1(self.parent_pid,self.query)
                _preflight_require_v1(os.getppid()==self.parent_pid and _json_compatible(parent)==b['process']
                    and actual==self.initial and actual['namespaces']==parent['namespaces'], 'LINUX_V2_CHILD_PROCESS_ASSOCIATION')
            _preflight_require_v1(Path(root) == self.root and Path(index_path) == self.index and
                self.cgroup == b['service_cgroup'] == _linux_preflight_cgroup_path_v1(self.pid,self.query),
                'LINUX_PREFLIGHT_SOURCE_AND_CGROUP_ASSOCIATION')
            _preflight_require_v1(_scan_same_api_version(self.control_path.lstat()) == self.control_version
                and _preflight_chain_v1(self.control_path.parent) == self.control_chain,'LINUX_PREFLIGHT_CONTROL_GENERATION')
            _linux_preflight_status_v1(self.pid,self.query)
            for name,path in (('repository',self.root),('index',self.index)):
                info = path.lstat()
                _preflight_require_v1([info.st_dev,info.st_ino] == b['identities'][name] and info.st_uid == 0
                    and stat.S_IMODE(info.st_mode) & 0o222 == 0,'LINUX_PREFLIGHT_ORIGINAL_SOURCE_OBJECT')
            base = Path('/sys/fs/cgroup')/self.cgroup.lstrip('/')
            _linux_preflight_ancestor_values_v1(self.query.read(base/'memory.max'),self.query.read(base/'pids.max'),
                self.query.read(base/'cpu.max'),owned=True)
            _preflight_require_v1(self.query.read(base/'memory.swap.max') == b'0\n','LINUX_PREFLIGHT_SWAP')
            mounts = _linux_preflight_mounts_v1(self.query.read('/proc/self/mountinfo'))
            for target in (str(self.root),str(self.control_path.parent),b['declaration_parent'],b['installation']):
                match = [m for m in mounts if m['path'] == target]
                _preflight_require_v1(len(match) == 1 and 'ro' in match[0]['options'],
                    'LINUX_PREFLIGHT_READONLY_MOUNT:'+target)
            _linux_preflight_mount_containment_v1(pid=self.pid,process=actual,runtime=str(self.runtime),
                query=self.query,mounts=mounts,mappings=b.get('host_service_mappings'),service_process=b['process'])
            self.check_runtime(b,self.runtime,self.query)
            for target in (str(self.runtime),'/tmp','/var/tmp'):
                match = [m for m in mounts if m['path'] == target]
                _preflight_require_v1(len(match) == 1 and match[0]['fs'] == 'tmpfs'
                    and {'noexec','nodev','nosuid'} <= match[0]['options']
                    and match[0]['device'] == b['runtime_device'],'LINUX_PREFLIGHT_RUNTIME_MOUNT')
            _preflight_require_v1(_json_compatible(_preflight_chain_v1(Path(b['declaration']).parent)) == b['declaration_chain']
                and list(_scan_same_api_version(Path(b['declaration']).lstat())) == b['declaration_version'],
                'LINUX_PREFLIGHT_SERVICE_NAMESPACE_BASIS')
            self._check()
        except BaseException as exc:
            if self.failure is None: self.failure = exc
            raise
    @staticmethod
    def check_runtime(binding,runtime,query):
        _preflight_require_v1(type(binding.get('runtime_identity')) is list and len(binding['runtime_identity'])==2
            and all(type(v) is int and v>=0 for v in binding['runtime_identity'])
            and type(binding.get('runtime_uid')) is int and binding['runtime_uid']>0
            and type(binding.get('runtime_gid')) is int and binding['runtime_gid']>0,
            'LINUX_PREFLIGHT_RUNTIME_BINDING_SHAPE')
        credentials=_linux_preflight_status_v1(os.getpid(),query,credentials=True)
        _preflight_require_v1(credentials['Uid']==binding['runtime_uid']==os.geteuid()
            and credentials['Gid']==binding['runtime_gid']==os.getegid(),'LINUX_PREFLIGHT_RUNTIME_CREDENTIAL_BINDING')
        query.check();info=Path(runtime).lstat()
        _preflight_require_v1(stat.S_ISDIR(info.st_mode) and [info.st_dev,info.st_ino]==binding['runtime_identity']
            and (info.st_uid,info.st_gid)==(binding['runtime_uid'],binding['runtime_gid'])
            and stat.S_IMODE(info.st_mode)==0o700,'LINUX_PREFLIGHT_RUNTIME_OWNERSHIP')
        mounts=_linux_preflight_mounts_v1(query.read('/proc/self/mountinfo'))
        for logical,child,mode in ((str(runtime),None,0o700),('/tmp','tmp',0o1777),('/var/tmp','var-tmp',0o1777)):
            query.check();view=Path(logical).lstat()
            query.check();expected=(Path(runtime)/child).lstat() if child else info
            selected=[m for m in mounts if m['path']==logical]
            _preflight_require_v1(stat.S_ISDIR(view.st_mode) and (view.st_dev,view.st_ino)==(expected.st_dev,expected.st_ino)
                and stat.S_IMODE(view.st_mode)==mode and len(selected)==1 and selected[0]['fs']=='tmpfs'
                and selected[0]['device']==binding['runtime_device']
                and ('size=1048576k' in selected[0]['super_options'] or 'size=1073741824' in selected[0]['super_options'])
                and {'rw','noexec','nodev','nosuid'}<=selected[0]['options'], 'LINUX_PREFLIGHT_RUNTIME_ALIAS:'+logical)
        return credentials

    def check_launch(self,plan_entry,argv,environment,scratch_roots,deadline_ns):
        self.check_parent(self.root,self.index)
        n = plan_entry.command_index
        _preflight_require_v1(1 <= n <= 8 and tuple(argv) == tuple(self.binding['vectors'][n-1])
            and deadline_ns == self.binding['grants']['rows'][n-1]['deadline_ns'],
            'LINUX_PREFLIGHT_ORIGINAL_LAUNCH')
        _preflight_require_v1(all(Path(p).is_relative_to(self.runtime) for p in scratch_roots),
            'LINUX_PREFLIGHT_SCRATCH_AUTHORITY')
        _linux_preflight_child_environment_v1(self.binding['environment'],environment,self.runtime)
        _preflight_require_v1(self.storage_reservation is not None,
            'LINUX_PREFLIGHT_TRANSPORT_RESERVATION_REQUIRED')
    def reserve_plan(self,extents,receivers):
        self._check()
        _preflight_require_v1(self.storage_reservation is None,'LINUX_PREFLIGHT_STORAGE_ONE_SHOT')
        self.storage_reservation = _linux_preflight_storage_reservation_v1(tuple(extents),tuple(receivers),os.sysconf('SC_PAGESIZE'))
        self.reserved_extents,self.reserved_receivers = tuple(extents),tuple(receivers)
    def reserve_input(self,position,extent,receiver):
        self._check()
        _preflight_require_v1(self.storage_reservation is not None and position not in self.reserved_inputs
            and extent <= self.reserved_extents[position-1] and receiver <= self.reserved_receivers[position-1]
            and extent <= 67108864,'LINUX_PREFLIGHT_ACTUAL_INPUT_INTERSECTION')
        self.reserved_inputs[position] = (extent,receiver)
    def check_child(self,actual_process):
        self.check_parent(self.root,self.index)
        _preflight_require_v1(type(actual_process) is subprocess.Popen and actual_process not in self.children,
            'LINUX_PREFLIGHT_ORIGINAL_CHILD_HANDLE')
        identity = _linux_preflight_process_identity_v1(actual_process.pid,self.query)
        fd = os.pidfd_open(actual_process.pid,0)
        try:
            _preflight_require_v1(_linux_preflight_process_identity_v1(actual_process.pid,self.query) == identity
                and _linux_preflight_cgroup_path_v1(actual_process.pid,self.query) == self.cgroup,
                'LINUX_PREFLIGHT_CHILD_MEMBERSHIP')
        except BaseException:
            os.close(fd); raise
        self.children[actual_process] = (identity,fd)
    def check_settled(self,actual_process):
        self._check()
        import select
        _preflight_require_v1(actual_process in self.children and actual_process.poll() is not None,
            'LINUX_PREFLIGHT_CHILD_TERMINAL')
        identity,fd = self.children[actual_process]
        poll = select.poll(); poll.register(fd,select.POLLIN)
        _preflight_require_v1(bool(poll.poll(0)) and not _posix_process_group_exists(identity['pid']),
            'LINUX_PREFLIGHT_CHILD_TREE_UNRESOLVED')
        os.close(fd); del self.children[actual_process]
        self.query.check()


def _linux_acl_parse_v2(raw, *, default, mode):
    """The Linux little-endian POSIX ACL ABI; no name-service lookups."""
    import struct
    if raw is None:
        return None
    _preflight_require_v1(type(raw) is bytes and 4 <= len(raw) <= 1028 and
        (len(raw)-4) % 8 == 0 and struct.unpack_from('<I',raw)[0] == 2, 'LINUX_ACL_ENCODING')
    rows = tuple(struct.iter_unpack('<HHI',raw[4:]))
    if not rows:
        _preflight_require_v1(default, 'LINUX_ACL_EMPTY_ACCESS')
        return ()
    order = {1:0,2:1,4:2,8:3,16:4,32:5}
    previous = (-1,-1)
    seen = set()
    for tag,perm,qualifier in rows:
        _preflight_require_v1(tag in order and not perm & ~7 and
            (qualifier != 0xffffffff if tag in (2,8) else qualifier == 0xffffffff), 'LINUX_ACL_ENTRY')
        key = (order[tag],qualifier)
        _preflight_require_v1(key > previous and (tag,qualifier) not in seen, 'LINUX_ACL_ORDER_OR_DUPLICATE')
        previous = key; seen.add((tag,qualifier))
    tags = [r[0] for r in rows]
    _preflight_require_v1(all(tags.count(t) == 1 for t in (1,4,32)) and tags.count(16) <= 1
        and (not any(t in tags for t in (2,8)) or tags.count(16) == 1), 'LINUX_ACL_BASE_OR_MASK')
    if not default:
        values = {t:p for t,p,q in rows if t not in (2,8)}
        _preflight_require_v1((values[1],values.get(16,values[4]),values[32]) ==
            ((mode >> 6)&7,(mode >> 3)&7,mode&7), 'LINUX_ACL_MODE_DISAGREEMENT')
    return rows


def _linux_acl_rights_v2(rows, *, mode, owner_uid, owner_gid, uid, groups, requested):
    """DAC summary only. A matching denial cannot fall through to other."""
    _preflight_require_v1(type(requested) is int and 0 <= requested <= 7 and type(groups) is tuple,
        'LINUX_ACL_RIGHTS_OPERANDS')
    if rows is None:
        perm = (mode >> (6 if uid == owner_uid else 3 if owner_gid in groups else 0)) & 7
        return perm & requested == requested
    base = {t:p for t,p,q in rows if t not in (2,8)}
    mask = base.get(16,7)
    if uid == owner_uid: return base[1] & requested == requested
    for tag,perm,qualifier in rows:
        if tag == 2 and qualifier == uid: return perm & mask & requested == requested
    matched = ([base[4]] if owner_gid in groups else []) + [p for t,p,q in rows if t == 8 and q in groups]
    if matched: return any(p & mask & requested == requested for p in matched)
    return base[32] & requested == requested


class _LinuxSourceNativeV2:
    """Fixed Linux ABI observations. No buffer resizing or permission fallback."""
    def __init__(self,attempt=None):
        import ctypes
        _preflight_require_v1(sys.platform == 'linux' and ctypes.sizeof(ctypes.c_void_p) == 8
            and ctypes.sizeof(ctypes.c_int) == 4 and os.uname().machine == 'x86_64', 'LINUX_V2_NATIVE_ABI')
        self.ctypes = ctypes
        self.attempt = attempt
        self.last_acl = {}
        self.lib = ctypes.CDLL(None,use_errno=True)
        self.lib.flistxattr.argtypes = (ctypes.c_int,ctypes.c_void_p,ctypes.c_size_t)
        self.lib.flistxattr.restype = ctypes.c_ssize_t
        self.lib.fgetxattr.argtypes = (ctypes.c_int,ctypes.c_char_p,ctypes.c_void_p,ctypes.c_size_t)
        self.lib.fgetxattr.restype = ctypes.c_ssize_t
        self.lib.fremovexattr.argtypes = (ctypes.c_int,ctypes.c_char_p)
        self.lib.fremovexattr.restype = ctypes.c_int
        self.lib.ioctl.argtypes = (ctypes.c_int,ctypes.c_ulong,ctypes.POINTER(ctypes.c_int))
        self.lib.ioctl.restype = ctypes.c_int
    def _call(self, function, *args):
        if self.attempt is not None:self.attempt()
        self.ctypes.set_errno(0)
        result = function(*args)
        error = self.ctypes.get_errno()
        if result < 0: raise OSError(error,os.strerror(error))
        return result
    def acl(self, fd, *, attempt, delivered):
        import errno
        self.last_acl = dict(names_hex=None,values=[],failure=None)
        names = self.ctypes.create_string_buffer(65536)
        attempt('flistxattr')
        try:count = self._call(self.lib.flistxattr,fd,names,65536)
        except OSError as error:
            self.last_acl['failure']=dict(operation='flistxattr',errno=error.errno,error=str(error));raise
        delivered(count)
        _preflight_require_v1(count <= 65536, 'LINUX_ACL_NAMES_OVERDELIVERY')
        raw = bytes(names.raw[:count])
        self.last_acl = dict(names_hex=raw.hex(),values=[],failure=None)
        _preflight_require_v1(not raw or raw.endswith(b'\0'), 'LINUX_ACL_NAMES_FRAGMENT')
        parts = raw[:-1].split(b'\0') if raw else []
        _preflight_require_v1(all(parts) and len(set(parts)) == len(parts) if raw else True,
            'LINUX_ACL_NAMES_DUPLICATE')
        _preflight_require_v1(b'security.capability' not in parts, 'LINUX_EXECUTION_CAPABILITY_XATTR')
        values = []
        for name in (b'system.posix_acl_access',b'system.posix_acl_default'):
            buffer = self.ctypes.create_string_buffer(1028)
            attempt('fgetxattr:'+name.decode('ascii'))
            try: count = self._call(self.lib.fgetxattr,fd,name,buffer,1028)
            except OSError as error:
                if error.errno != errno.ENODATA:
                    self.last_acl['failure']=dict(attribute=name.decode(),errno=error.errno,error=str(error));raise
                value = None
            else:
                delivered(count)
                _preflight_require_v1(count <= 1028, 'LINUX_ACL_VALUE_OVERDELIVERY')
                value = bytes(buffer.raw[:count])
            self.last_acl['values'].append(dict(attribute=name.decode(),raw_hex=None if value is None else value.hex()))
            _preflight_require_v1((value is not None) == (name in parts), 'LINUX_ACL_NAMES_VALUES_CHANGED')
            values.append(value)
        return tuple(values)
    def remove_acl(self, fd):
        import errno
        for name in (b'system.posix_acl_access',b'system.posix_acl_default'):
            try: self._call(self.lib.fremovexattr,fd,name)
            except OSError as error:
                if error.errno != errno.ENODATA: raise
    def flags(self, fd, value=None):
        operand = self.ctypes.c_int(0 if value is None else value)
        self._call(self.lib.ioctl,fd,0x80086601 if value is None else 0x40086602,self.ctypes.byref(operand))
        return operand.value & 0xffffffff
    def mount(self,fd):
        """Fixed statx/statmount queries distinguish idmapped ext4 views."""
        import struct
        c=self.ctypes
        self.lib.statx.argtypes=(c.c_int,c.c_char_p,c.c_int,c.c_uint,c.c_void_p)
        self.lib.statx.restype=c.c_int
        sx=c.create_string_buffer(256)
        self._call(self.lib.statx,fd,b'',0x1000|0x100,0x4000,sx)
        mask=struct.unpack_from('<I',sx.raw,0)[0]
        _preflight_require_v1(mask&0x4000,'LINUX_V2_UNIQUE_MOUNT_ID_UNSUPPORTED')
        unique=struct.unpack_from('<Q',sx.raw,144)[0]
        request=c.create_string_buffer(struct.pack('<IIQQ',24,0,unique,3),24)
        result=c.create_string_buffer(512)
        self.lib.syscall.restype=c.c_long
        self._call(self.lib.syscall,c.c_long(457),c.byref(request),c.byref(result),c.c_size_t(512),c.c_uint(0))
        raw=bytes(result.raw)
        size=struct.unpack_from('<I',raw,0)[0];returned=struct.unpack_from('<Q',raw,8)[0]
        _preflight_require_v1(size==512 and returned&3==3 and struct.unpack_from('<Q',raw,40)[0]==unique,
            'LINUX_V2_STATMOUNT_COMPLETE')
        return dict(unique_id=unique,old_id=struct.unpack_from('<I',raw,56)[0],
            device=list(struct.unpack_from('<II',raw,16)),magic=struct.unpack_from('<Q',raw,24)[0],
            attributes=struct.unpack_from('<Q',raw,64)[0],raw_hex=raw.hex())


def _linux_source_open_v2(path,attempt=None):
    """Walk original components with directory descriptors, never follow aliases."""
    path = Path(path)
    _preflight_require_v1(path.is_absolute() and '..' not in path.parts, 'LINUX_V2_ABSOLUTE_OPERAND')
    if attempt is not None:attempt()
    fd = os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        for n,component in enumerate(path.parts[1:]):
            flags = os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK
            if n < len(path.parts)-2: flags |= os.O_DIRECTORY
            if attempt is not None:attempt()
            opened = os.open(component,flags,dir_fd=fd)
            os.close(fd); fd = opened
        result,fd = fd,None
        return result
    finally:
        if fd is not None: os.close(fd)


class _LinuxInstallationCopyV2:
    """Only the selected installation is copied, streaming and without its ACLs."""
    def __init__(self, census, root, *, deadline_ns, setup_uid):
        _preflight_require_v1(type(census) is _LinuxPreflightCensusV1 and census.complete
            and type(setup_uid) is int and setup_uid > 0, 'LINUX_INSTALLATION_SETTLED_CENSUS')
        self.census,self.root,self.deadline_ns = census,Path(root),deadline_ns
        self.native = _LinuxSourceNativeV2()
        self.rows = [row for row in census.records if row['role'] == 'installation']
        self.row_index = {row['path']:row for row in self.rows}
        _preflight_require_v1(all(row['version'][7] in (0,setup_uid) for row in self.rows),
            'LINUX_INSTALLATION_PROVISIONING_OWNER')
        self.files,self.directories,self.original = {},{},{}
        self.byte_count,self.read_bytes,self.copy_bytes = 0,0,0
        self.copy_verified = False
        self.observations = []
        self.metadata_calls,self.xattr_bytes=0,0
    def _check(self):
        _preflight_require_v1(time.monotonic_ns() < self.deadline_ns, 'LINUX_INSTALLATION_DEADLINE')
    def _observe(self,row):
        self._check()
        self.current_path,self.current_operation=row['path'],'source-and-acl-observation'
        path = Path(row['observed_path'])
        _preflight_require_v1(self.census._version(path.lstat()) == row['version'], 'LINUX_INSTALLATION_SOURCE_CHANGED')
        for hop in row['aliases']:
            alias=Path(hop['path'])
            _preflight_require_v1(self.census._version(alias.lstat()) == hop['version'] and
                os.readlink(alias) == hop['target'], 'LINUX_INSTALLATION_ALIAS_CHANGED')
        fd=_linux_source_open_v2(path)
        try:
            before=os.fstat(fd)
            acl=self.native.acl(fd,attempt=lambda op:self._attempt(),delivered=self._delivered)
            expected=tuple(None if ref is None else self.census.acl_pool[ref] for ref in row['acl'])
            _preflight_require_v1(acl==expected and self.census._version(os.fstat(fd))==row['version']==self.census._version(before),
                'LINUX_INSTALLATION_ACL_CHANGED')
        finally:os.close(fd)
        return path
    def _attempt(self):
        self._check();self.metadata_calls+=1
        _preflight_require_v1(self.metadata_calls<=2_000_000,'LINUX_INSTALLATION_METADATA_CAPACITY')
    def _delivered(self,amount):
        self.xattr_bytes+=amount;self._check()
    def copy_installation(self,destination):
        destination=Path(destination)
        _preflight_require_v1(os.geteuid() == 0 and not destination.exists(), 'LINUX_INSTALLATION_OWNED_NEW_COPY')
        for row in self.rows:
            self._check()
            path=self._observe(row)
            target=destination/Path(row['path']).relative_to(self.root)
            mode=row['version'][2]
            if row['kind'] == 'directory':
                target.mkdir(mode=0o700)
                fd=_linux_source_open_v2(target)
                try:
                    self.native.remove_acl(fd)  # Before any descendant exists.
                    os.fchown(fd,0,0); os.fchmod(fd,0o700)
                    _preflight_require_v1(self.native.acl(fd,attempt=lambda op:self._attempt(),delivered=self._delivered)
                        == (None,None), 'LINUX_INSTALLATION_DESTINATION_ACL')
                finally: os.close(fd)
                self.directories[row['path']] = tuple((name,self.row_index[str(Path(row['path'])/name)]['kind']) for name in row['roster'])
                with os.scandir(path) as stream:observed_names=sorted(e.name for e in stream)
                _preflight_require_v1(observed_names==sorted(row['roster']), 'LINUX_INSTALLATION_ORIGINAL_ROSTER_CHANGED')
                continue
            self.byte_count += row['logical_bytes']
            _preflight_require_v1(self.byte_count <= 1024**3 and not mode & (stat.S_ISUID|stat.S_ISGID),
                'LINUX_INSTALLATION_EXTENT_OR_SETID')
            source=_linux_source_open_v2(path); output=None
            try:
                _preflight_require_v1(self.census._version(os.fstat(source)) == row['version'], 'LINUX_INSTALLATION_OPEN_CHANGED')
                output=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
                self.native.remove_acl(output); os.fchown(output,0,0)
                extent=0
                while True:
                    self._check()
                    raw=os.read(source,min(65536,row['logical_bytes']-extent+1))
                    self.read_bytes += len(raw); extent += len(raw)
                    _preflight_require_v1(extent <= row['logical_bytes'], 'LINUX_INSTALLATION_SOURCE_GREW')
                    if not raw: break
                    view=memoryview(raw)
                    while view:
                        self._check(); written=os.write(output,view)
                        _preflight_require_v1(0 < written <= len(view), 'LINUX_INSTALLATION_SHORT_WRITE')
                        self.copy_bytes += written; view=view[written:]
                _preflight_require_v1(extent == row['logical_bytes'] and self.census._version(os.fstat(source)) == row['version'],
                    'LINUX_INSTALLATION_COPY_EXTENT')
                os.fchmod(output,0o555 if mode & 0o111 else 0o444); os.fsync(output)
            finally:
                if output is not None: os.close(output)
                os.close(source)
            # Actual two-stream comparison; retained startup bytes come from these reads.
            source=_linux_source_open_v2(self._observe(row)); copied=_linux_source_open_v2(target)
            try:
                before=os.fstat(copied); pieces=[]; extent=0
                _preflight_require_v1(before.st_uid == 0 and stat.S_IMODE(before.st_mode) == (0o555 if mode&0o111 else 0o444)
                    and before.st_nlink == 1 and before.st_size == row['logical_bytes'], 'LINUX_INSTALLATION_COPY_ATTRIBUTES')
                while True:
                    self._check(); amount=min(65536,row['logical_bytes']-extent+1)
                    left,right=os.read(source,amount),os.read(copied,amount)
                    self.read_bytes += len(left)
                    _preflight_require_v1(left == right and extent+len(left) <= row['logical_bytes'], 'LINUX_INSTALLATION_COPY_BYTES')
                    if not left: break
                    pieces.append(left); extent+=len(left)
                _preflight_require_v1(extent == row['logical_bytes'] and self.census._version(os.fstat(source)) == row['version']
                    and _scan_same_api_version(os.fstat(copied)) == _scan_same_api_version(before) == _scan_same_api_version(target.lstat()),
                    'LINUX_INSTALLATION_COPY_GENERATION')
                _preflight_require_v1(self.native.acl(copied,attempt=lambda op:self._attempt(),delivered=self._delivered)
                    == (None,None), 'LINUX_INSTALLATION_DESTINATION_ACL')
                self.files[row['path']]=b''.join(pieces)
            finally: os.close(copied);os.close(source)
            self._observe(row)
        for row in reversed(self.rows):
            if row['kind']=='directory':
                target=destination/Path(row['path']).relative_to(self.root)
                fd=_linux_source_open_v2(target)
                try:
                    os.fchmod(fd,0o555)
                    _preflight_require_v1(self.native.acl(fd,attempt=lambda op:self._attempt(),delivered=self._delivered)==(None,None),
                        'LINUX_INSTALLATION_FINAL_ACL')
                    actual=os.fstat(fd)
                    _preflight_require_v1(actual.st_uid==actual.st_gid==0 and stat.S_IMODE(actual.st_mode)==0o555,
                        'LINUX_INSTALLATION_DIRECTORY_ATTRIBUTES')
                    with os.scandir(fd) as stream:observed_names=sorted(e.name for e in stream)
                    _preflight_require_v1(observed_names==sorted(row['roster']), 'LINUX_INSTALLATION_COPY_ROSTER_CHANGED')
                finally: os.close(fd)
        for row in self.rows:
            path=self._observe(row)
            if row['kind']=='directory':
                with os.scandir(path) as stream:observed_names=sorted(e.name for e in stream)
                _preflight_require_v1(observed_names==sorted(row['roster']), 'LINUX_INSTALLATION_ORIGINAL_ROSTER_CHANGED')
        self.copy_verified=True


def _linux_source_row_v2(relative,role,info,flags):
    return [relative,role,info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns,
        info.st_mode,info.st_uid,info.st_gid,info.st_nlink,flags]


def _linux_source_descriptor_v2(value):
    _preflight_keys_v1(value,('kind','path','physical_version','byte_length','catalog_entry_count'))
    _preflight_require_v1(value['kind']=='NATIVE_IMMUTABLE_V2', 'LINUX_V2_BASIS_KIND')
    _preflight_startup_path_v1(value['path'])
    _preflight_require_v1(Path(value['path']).name=='source-basis.json' and
        type(value['physical_version']) is list and len(value['physical_version'])==6, 'LINUX_V2_MANIFEST_DESCRIPTOR')
    for v in value['physical_version']: _preflight_integer_v1(v)
    _preflight_require_v1(0 < _preflight_integer_v1(value['byte_length']) <= 32*1024**2 and
        0 < _preflight_integer_v1(value['catalog_entry_count']) <= 300000, 'LINUX_V2_MANIFEST_BOUNDS')
    return value


def _linux_source_manifest_v2(value):
    _preflight_keys_v1(value,('basis_kind','run_id','repository_root','index_path','source_root_identity',
        'source_generation_ns','files','directories','category_totals'))
    _preflight_require_v1(value['basis_kind']=='NATIVE_IMMUTABLE_V2', 'LINUX_V2_MANIFEST_KIND')
    _preflight_text_v1(value['run_id']); _preflight_startup_path_v1(value['repository_root'])
    root=Path(value['repository_root']); _preflight_require_v1(value['index_path']==str(root/'.git/index'), 'LINUX_V2_INDEX')
    _preflight_integer_v1(value['source_generation_ns'],positive=True)
    _preflight_require_v1(type(value['source_root_identity']) is list and len(value['source_root_identity'])==2,
        'LINUX_V2_ROOT_IDENTITY')
    for v in value['source_root_identity']: _preflight_integer_v1(v)
    files,dirs={},{}
    names=set();rosters={};identities=set()
    for key,target,directory in (('files',files,False),('directories',dirs,True)):
        rows=value[key]
        _preflight_require_v1(type(rows) is list and len(rows)<=100000, 'LINUX_V2_CATALOG_ARRAY')
        order=[]
        for row in rows:
            _preflight_require_v1(type(row) is list and len(row)==(13 if directory else 12), 'LINUX_V2_CATALOG_ROW')
            name=_preflight_relative_v1(row[0],directory=directory)
            _preflight_require_v1(len(str(root/name).encode('utf-8'))<=4096 and
                (0 if name=='.' else len(name.split('/')))<=64, 'LINUX_V2_CATALOG_PATH_BOUND')
            _preflight_require_v1(name.casefold() not in names and row[1]==('GIT_ADMIN' if name=='.git' or name.startswith('.git/') else 'WORKTREE'),
                'LINUX_V2_CATALOG_ALIAS_OR_ROLE')
            names.add(name.casefold());order.append(name.encode('utf-8'))
            for v in row[2:12]: _preflight_integer_v1(v)
            identity=tuple(row[2:4])
            _preflight_require_v1(row[2]==value['source_root_identity'][0] and identity not in identities,
                'LINUX_V2_CATALOG_DEVICE_OR_INODE_ALIAS')
            identities.add(identity)
            _preflight_require_v1((stat.S_ISDIR(row[7]) if directory else stat.S_ISREG(row[7]) and row[10]==1)
                and row[8]==row[9]==0 and not row[7]&0o222 and row[11]&0x10 and row[11]<=0xffffffff,
                'LINUX_V2_CATALOG_PROTECTION')
            target[name]=tuple(row[:12])
            if directory:
                rosters[name]=_preflight_rosters_v1([[name,row[12]]])[name]
        _preflight_require_v1(order==sorted(order), 'LINUX_V2_CATALOG_ORDER')
    _preflight_require_v1('.' in dirs and '.git' in dirs and '.git/index' in files and
        list(dirs['.'][2:4])==value['source_root_identity'], 'LINUX_V2_COMPLETE_ROOT_AND_INDEX')
    _preflight_catalog_consistency_v1(files,rosters)
    for name,roster in rosters.items():
        for child,kind in roster:
            relative=child if name=='.' else name+'/'+child
            _preflight_require_v1(relative in (dirs if kind=='directory' else files), 'LINUX_V2_COMPLETE_ROSTER')
    totals=dict(R=sum(r[4] for r in files.values() if r[1]=='WORKTREE'),
        G=sum(r[4] for r in files.values() if r[1]=='GIT_ADMIN'),I=files['.git/index'][4])
    _preflight_keys_v1(value['category_totals'],totals)
    _preflight_require_v1(value['category_totals']==totals and totals['R']+totals['G']<=64*1024**3,
        'LINUX_V2_SOURCE_CAPACITY')
    count=len(files)+len(dirs)+sum(map(len,rosters.values()))
    _preflight_require_v1(count<=300000, 'LINUX_V2_CATALOG_CARDINALITY')
    return files,dirs,rosters,count


class _LinuxImmutableSourceBasisV2:
    """One process view of the controller-sealed original inode generation."""

    def __init__(self, lease, descriptor, run_id):
        _preflight_require_v1(type(lease) is _LinuxPreflightHostLeaseV1, 'LINUX_V2_ACTUAL_LEASE_REQUIRED')
        lease.check_parent(lease.root, lease.index)
        descriptor = _linux_source_descriptor_v2(descriptor)
        _preflight_require_v1(descriptor == lease.binding.get('native_basis') and descriptor['path'] == str(lease.control_path.parent.parent / 'declaration/source-basis.json'), 'LINUX_V2_CONTROLLER_DESCRIPTOR_BINDING')
        self.lease, self.descriptor, self.root = (lease, dict(descriptor), lease.root)
        self.pid, self.thread = (os.getpid(), threading.get_ident())
        self.deadline_ns = lease.deadline_ns
        self.failure = None
        self.state = 'READABLE'
        self.metadata_calls = 0
        self.metadata_reserved = 0
        self.metadata_rejected = 0
        self.owned = {}
        self.native = _LinuxSourceNativeV2(self._meta_attempt)
        self.namespace = self._meta(os.stat, '/proc/self/ns/mnt')
        self.user_namespace = self._meta(os.stat, '/proc/self/ns/user')
        self.manifest_acquired_bytes = 0
        self.manifest_retained_bytes = 0
        path = Path(descriptor['path'])
        fd = self._open_path(path)
        try:
            before = self._meta(os.fstat, fd)
            _preflight_require_v1(list(_scan_same_api_version(before)) == descriptor['physical_version'] and before.st_uid == 0 and (stat.S_IMODE(before.st_mode) == 292) and (before.st_size == descriptor['byte_length']), 'LINUX_V2_MANIFEST_PHYSICAL_VERSION')
            parts = []
            while self.manifest_acquired_bytes < before.st_size:
                _preflight_require_v1(time.monotonic_ns() < self.deadline_ns, 'LINUX_V2_MANIFEST_DEADLINE')
                block = os.read(fd, min(65536, before.st_size - self.manifest_acquired_bytes))
                self.manifest_acquired_bytes += len(block)
                _preflight_require_v1(block and self.manifest_acquired_bytes <= before.st_size, 'LINUX_V2_MANIFEST_DELIVERY')
                parts.append(block)
            sentinel = os.read(fd, 1)
            self.manifest_acquired_bytes += len(sentinel)
            _preflight_require_v1(sentinel == b'' and list(_scan_same_api_version(self._meta(os.fstat, fd))) == descriptor['physical_version'] == list(_scan_same_api_version(self._meta(path.lstat))), 'LINUX_V2_MANIFEST_CHANGED')
            self.raw = b''.join(parts)
            self.manifest_retained_bytes = len(self.raw)
        finally:
            self._close(fd)
        limits = dict(lexical_units=32 * 1024 ** 2, depth=64, quoted_bytes=32 * 1024 ** 2)
        value, _ = _preflight_json_v1(self.raw, limits, lambda: _preflight_require_v1(time.monotonic_ns() < self.deadline_ns, 'LINUX_V2_PARSE_DEADLINE'))
        self.files, self.directory_records, self.directories, count = _linux_source_manifest_v2(value)
        _preflight_require_v1(value['repository_root'] == str(self.root) and value['index_path'] == str(lease.index) and (value['run_id'] == run_id) and (count == descriptor['catalog_entry_count']) and (value['source_generation_ns'] <= time.monotonic_ns()), 'LINUX_V2_MANIFEST_RUN_BINDING')
        self.run_id = run_id
        self.count = count
        self.state = 'IN_USE'
        self.last_clock = -1
        self.check_live()

    def check_live(self):
        if self.failure is not None:
            raise self.failure
        try:
            now = time.monotonic_ns()
            _preflight_require_v1(self.metadata_calls <= 2000000 and self.state in ('READABLE', 'IN_USE') and (self.lease.failure is None) and ((self.pid, self.thread) == (os.getpid(), threading.get_ident())) and (self.last_clock <= now < min(self.deadline_ns, self.lease.deadline_ns)), 'LINUX_V2_LIVE_LEASE')
            self.last_clock = now
            for name, before in (('mnt', self.namespace), ('user', self.user_namespace)):
                now = self._meta(os.stat, '/proc/self/ns/' + name)
                _preflight_require_v1((now.st_dev, now.st_ino) == (before.st_dev, before.st_ino), 'LINUX_V2_NAMESPACE_CHANGED')
            _preflight_require_v1(_scan_same_api_version(self._meta(self.lease.control_path.lstat)) == self.lease.control_version and list(_scan_same_api_version(self._meta(Path(self.descriptor['path']).lstat))) == self.descriptor['physical_version'], 'LINUX_V2_LIVE_CONTROL_GENERATION')
        except BaseException as exc:
            self.failure = exc
            self.state = 'FAILED'
            raise

    def _entry(self, name):
        _preflight_relative_v1(name, directory=True)
        row = self.files.get(name, self.directory_records.get(name))
        _preflight_require_v1(row is not None, 'LINUX_V2_UNDECLARED_ENTRY:' + name)
        return row

    def verify_fd(self, name, fd):
        self.check_live()
        row = self._entry(name)
        info = self._meta(os.fstat, fd)
        path = self.root / name
        _preflight_require_v1(_linux_source_row_v2(name, row[1], info, self.native.flags(fd)) == list(row) and _preflight_stamp_v1(self._meta(path.lstat)) == _preflight_stamp_v1(info), 'LINUX_V2_SOURCE_GENERATION:' + name)
        self.check_live()

    @contextmanager
    def open_entry(self, relative_path):
        self.check_live()
        row = self._entry(relative_path)
        opened = []
        try:
            fd = self._open_path(self.root)
            opened.append(('.', fd))
            self.verify_fd('.', fd)
            relative = '.'
            for component in () if relative_path == '.' else Path(relative_path).parts:
                relative = component if relative == '.' else relative + '/' + component
                fd = self._meta(os.open, component, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=opened[-1][1])
                name = relative
                opened.append((name, fd))
                self.verify_fd(name, fd)
            yield opened[-1][1]
            for name, fd in reversed(opened):
                self.verify_fd(name, fd)
            self.check_live()
        except BaseException as exc:
            self.failure = exc
            self.state = 'FAILED'
            raise
        finally:
            self._close_many([fd for name,fd in reversed(opened)])

    def catalog_snapshot(self, paths, observation):
        """A complete metadata barrier with held parents; no application bytes."""
        self.check_live()
        _preflight_require_v1(type(observation) is _PreflightObservationV1 and observation.native_basis is self, 'LINUX_V2_CANDIDATE_OBSERVATION_OWNER')
        expected = {p for p, r in self.files.items() if r[1] == 'WORKTREE'}
        _preflight_require_v1(type(paths) is tuple and set(paths) == expected and (len(paths) == len(expected)), 'LINUX_V2_EXACT_CANDIDATE_CATALOG')
        root_fd = self._open_path(self.root)

        def walk(name, fd):
            observation.reserve('attempts')
            row = self._entry(name)
            before = self._meta(os.fstat, fd)
            _preflight_require_v1(_linux_source_row_v2(name, row[1], before, self.native.flags(fd)) == list(row), 'LINUX_V2_CANDIDATE_GENERATION:' + name)
            if name in self.directories:
                with self._scan(fd) as stream:
                    observed = []
                    while True:
                        self._meta_attempt()
                        try: entry = next(stream)
                        except StopIteration: break
                        observation.received('entries', 1)
                        _preflight_require_v1(len(observed) < len(self.directories[name]), 'LINUX_V2_CANDIDATE_EXTRA_ENTRY')
                        observed.append(entry.name)
                        observation.retained_entries += 1
                _preflight_require_v1(sorted(observed, key=lambda v: v.encode('utf-8')) == [n for n, k in self.directories[name]], 'LINUX_V2_CANDIDATE_ROSTER:' + name)
                for child, kind in self.directories[name]:
                    relative = child if name == '.' else name + '/' + child
                    opened = self._meta(os.open, child, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK | (os.O_DIRECTORY if kind == 'directory' else 0), dir_fd=fd)
                    try:
                        walk(relative, opened)
                    finally:
                        self._close(opened)
            _preflight_require_v1(_preflight_stamp_v1(self._meta(os.fstat, fd)) == _preflight_stamp_v1(before), 'LINUX_V2_CANDIDATE_CHANGED:' + name)
        try:
            walk('.', root_fd)
            root_info = self._meta(os.fstat, root_fd)
            _preflight_require_v1(_preflight_stamp_v1(root_info) == _preflight_stamp_v1(self._meta(self.root.lstat)), 'LINUX_V2_CANDIDATE_ROOT_REPLACED')
            self.check_live()
            return {p: self.files[p] for p in paths}
        except BaseException as exc:
            self.failure = exc
            self.state = 'FAILED'
            raise
        finally:
            self._close(root_fd)

    def status(self, name, *, optional=False):
        self.check_live()
        if name in self.files or name in self.directories:
            with self.open_entry(name):
                pass
            return 'file' if name in self.files else 'directory'
        _preflight_require_v1(optional, 'LINUX_V2_REQUIRED_ENTRY_ABSENT:' + name)
        parts = Path(name).parts
        parent = '.'
        for component in parts:
            roster = self.directories.get(parent)
            _preflight_require_v1(roster is not None, 'LINUX_V2_ABSENCE_PARENT')
            if component not in {n for n, k in roster}:
                with self.open_entry(parent):
                    try:
                        self._meta((self.root / name).lstat)
                    except FileNotFoundError:
                        pass
                    else:
                        raise RuntimeError('LINUX_V2_ABSENCE_CHANGED')
                self.check_live()
                return None
            parent = component if parent == '.' else parent + '/' + component
        raise RuntimeError('LINUX_V2_INCOMPLETE_ABSENCE')

    def _reserve(self, amount):
        _preflight_require_v1(time.monotonic_ns() < self.deadline_ns,
            'LINUX_V2_METADATA_DEADLINE')
        if self.metadata_reserved+amount > 2000000:
            self.metadata_rejected += 1
            raise ValidationReliabilityError('ENGVR_PREFLIGHT_DENIED','LINUX_V2_METADATA_CAPACITY')
        self.metadata_reserved += amount

    def _meta_attempt(self):
        self._reserve(1)
        self.metadata_calls += 1

    def _meta(self, function, *args, **kwargs):
        if function is os.open: return self._open(*args, **kwargs)
        self._meta_attempt()
        return function(*args, **kwargs)

    def _open(self, *args, **kwargs):
        _preflight_require_v1(len(self.owned)<1023,'LINUX_V2_READER_DESCRIPTOR_CAPACITY')
        self._reserve(2)
        self.metadata_calls += 1
        fd=os.open(*args, **kwargs)
        self.owned[fd]=True
        return fd

    def _close(self, fd):
        _preflight_require_v1(fd in self.owned and self.pid==os.getpid()
            and self.thread==threading.get_ident(),'LINUX_V2_READER_OWNED_CLOSE')
        del self.owned[fd]
        self.metadata_calls += 1
        try: os.close(fd)
        except BaseException as exc:
            if self.failure is None:self.failure=exc
            self.state='FAILED'
            raise

    def _close_many(self, handles):
        errors=[]
        for fd in handles:
            try:self._close(fd)
            except BaseException as exc:errors.append(exc)
        _scan_raise_errors(errors)

    @contextmanager
    def _scan(self, fd):
        self._reserve(2)
        self.metadata_calls += 1
        stream=os.scandir(fd)
        try: yield stream
        finally:
            self.metadata_calls += 1
            stream.close()

    def _open_path(self, path):
        opened=[]
        try:
            for i,component in enumerate(Path(path).parts):
                opened.append(self._open(component,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC
                    |(os.O_DIRECTORY if i<len(Path(path).parts)-1 else 0),
                    **({} if not opened else dict(dir_fd=opened[-1]))))
            self._close_many(reversed(opened[:-1]))
            return opened[-1]
        except BaseException as exc:
            errors=[exc]
            for fd in reversed(opened):
                if fd in self.owned:
                    try:self._close(fd)
                    except BaseException as cleanup:errors.append(cleanup)
            _scan_raise_errors(errors)


class _LinuxImmutableSourceSealV2:
    """Original-checkout transitions with prepaid, independent rollback custody."""

    def __init__(self, census, *, deadline_ns, workspace, run_id):
        _preflight_require_v1(type(census) is _LinuxPreflightCensusV1 and census.complete
            and os.geteuid() == 0, 'LINUX_V2_COMPLETE_CENSUS_REQUIRED')
        self.census, self.root = census, census.roots['repository']
        self.rows = [r for r in census.records if r['role'] == 'repository']
        self.row_index = {r['path']: r for r in self.rows}
        self.deadline_ns, self.workspace, self.run_id = deadline_ns, Path(workspace), run_id
        self.pid, self.thread = os.getpid(), threading.get_ident()
        self.state, self.failure, self.phase = 'ENUMERATED', None, 'work'
        self.native = _LinuxSourceNativeV2(self._meta_attempt)
        self.journal, self.journal_bytes, self.journal_path, self.journal_identity = [], 0, None, None
        self.journal_fd, self.journal_torn = None, False
        self.journal_ids = {r['path']: n for n, r in enumerate(self.rows)}
        self.journal_reservation = None
        self.journal_counts = {p: dict(reserved=0, calls=0, bytes=0, rejected=0,native_reserved=32)
            for p in ('work', 'settlement')}
        self.protected, self.post, self.original_flags, self.originals = [], {}, {}, {}
        self.attempts, self.completed_originals = set(), set()
        self.read_bytes, self.read_attempts, self.auxiliary_read_bytes = 0, 0, 0
        self.read_rejected, self.metadata_calls, self.rejected_reservations = 0, 0, []
        self.owned, self.anchors, self.close_failures = {}, [], []
        self.close_failure_count=0
        self.restoration_outcomes = {i:'NOT_OBSERVED' for i in range(len(self.rows))}
        self.error_count, self.error_examples = 0, []
        self.primitive, self.recovery_cases = {}, []
        self.byte_count = sum(r['logical_bytes'] for r in self.rows)
        self.files = {r['path']: None for r in self.rows if r['kind'] == 'file'}
        self.directories = {r['path']: tuple((name, self.row_index[str(Path(r['path'])/name)]['kind'])
            for name in r['roster']) for r in self.rows if r['kind'] == 'directory'}
        n, e, a = len(self.rows), sum(len(r['roster']) for r in self.rows), len(self.root.parts)
        d = len(self.directories)
        _preflight_require_v1(n > 0 and e == n-1 and 1 <= a <= 65
            and self.byte_count <= 64*1024**3, 'LINUX_V2_SOURCE_GEOMETRY')
        bounds = dict(original=8*n, protection=12*n, postprotection=6*n+2*e,
            readability=8*n+2*e, postreadability=6*n+2*e, projection=2*n,
            postpublication=6*n+2*e, terminal=6*n+2*e, setup=4096+16*a,
            settlement=16*n+2*e+4096+16*a)
        work = sum(v for k,v in bounds.items() if k != 'settlement')
        _preflight_require_v1(work == 54*n+10*e+4096+16*a
            and work+bounds['settlement'] <= 2000000, 'LINUX_V2_PREPAID_SOURCE_CAPACITY')
        # Open/close, actual observations, terminal iterator calls and unwind
        # associations are all included; no optimistic size-derived read count.
        programme = dict(original=5*n+2*d, protection=10*n+2*d,
            postprotection=5*n+5*d+e, readability=7*n+5*d+e,
            postreadability=5*n+5*d+e, projection=n+1,
            postpublication=5*n+5*d+e, terminal=5*n+5*d+e,
            settlement=12*n+5*d+e+16*a)
        _preflight_require_v1(all(v <= bounds[k] for k,v in programme.items()),
            'LINUX_V2_FIXED_STAGE_PROGRAMME_CAPACITY')
        self.accounting = dict(units='admitted native metadata calls; byte reads and journal separate',
            nodes=n, edges=e, ancestors=a, work=work, settlement=bounds['settlement'],
            unallocated=2000000-work-bounds['settlement'], programme=programme,
            stages={k:dict(limit=v, reserved=0, performed=0, rejected=0) for k,v in bounds.items()})
        self.stage = 'setup'
        self.verify_stages = iter(('postprotection','postreadability','postpublication','terminal'))

    def _check(self):
        _preflight_require_v1(os.getpid() == self.pid and threading.get_ident() == self.thread
            and time.monotonic_ns() < self.deadline_ns and self.phase in ('work','settlement')
            and (self.failure is None or self.phase == 'settlement'), 'LINUX_V2_SOURCE_PHASE_OR_DEADLINE')

    def _reserve(self, amount):
        self._check()
        row = self.accounting['stages'][self.stage]
        if row['reserved']+amount > row['limit']:
            row['rejected'] += 1
            if len(self.rejected_reservations) < 64:
                self.rejected_reservations.append(dict(stage=self.stage, amount=amount,
                    reserved=row['reserved'], limit=row['limit']))
            raise ValidationReliabilityError('ENGVR_PREFLIGHT_DENIED','LINUX_V2_SOURCE_STAGE_CAPACITY:'+self.stage)
        row['reserved'] += amount

    def _performed(self, stage=None):
        self.metadata_calls += 1
        self.accounting['stages'][self.stage if stage is None else stage]['performed'] += 1

    def _meta_attempt(self):
        self._reserve(1)
        self._performed()

    def _meta(self, function, *args, **kwargs):
        if function is os.open:
            return self._open(*args, **kwargs)
        self._meta_attempt()
        return function(*args, **kwargs)

    def _open(self, *args, **kwargs):
        _preflight_require_v1(len(self.owned)<1023,'LINUX_V2_DESCRIPTOR_CAPACITY')
        self._reserve(2)  # The close obligation cannot be spent by later work.
        stage = self.stage
        self._performed()
        fd = os.open(*args, **kwargs)
        self.owned[fd] = stage
        return fd

    def _close(self, fd):
        _preflight_require_v1(fd in self.owned and os.getpid() == self.pid
            and threading.get_ident() == self.thread, 'LINUX_V2_OWNED_CLOSE')
        stage = self.owned.pop(fd)
        self._performed(stage)
        try:
            os.close(fd)
        except BaseException as exc:
            self.close_failure_count+=1
            if len(self.close_failures)<64:
                self.close_failures.append(dict(fd=fd,error=repr(exc).encode('utf-8')[:384].decode('utf-8','replace')))
            raise

    def _anchor(self):
        if self.anchors:
            return self.anchors[-1][0]
        self.stage = 'setup'
        parent = None
        for part in self.root.parts:
            fd = self._open(part, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,
                **({} if parent is None else dict(dir_fd=parent)))
            info = self._meta(os.fstat, fd)
            self.anchors.append((fd, (info.st_dev,info.st_ino), part))
            parent = fd
        _preflight_require_v1(tuple(self.row_index[str(self.root)]['version'][:2])
            == self.anchors[-1][1], 'LINUX_V2_ROOT_ANCHOR_IDENTITY')
        return parent

    def _open_path(self, path):
        """Rare exact administration/primitive path, with prepaid closes."""
        path = Path(path)
        parent = None
        opened = []
        try:
            for i, part in enumerate(path.parts):
                fd = self._open(part, os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC
                    | (os.O_DIRECTORY if i < len(path.parts)-1 else 0),
                    **({} if parent is None else dict(dir_fd=parent)))
                opened.append(fd)
                parent = fd
            for handle in reversed(opened[:-1]):
                self._close(handle)
            return opened[-1]
        except BaseException:
            for handle in reversed(opened):
                if handle in self.owned:
                    self._close(handle)
            raise

    def _anchors_live(self):
        previous=self.stage
        self.stage='setup' if self.phase=='work' else 'settlement'
        try:
            for index,(fd,identity,name) in enumerate(self.anchors):
                info=self._meta(os.fstat,fd)
                path_info=self._meta(os.stat,name,follow_symlinks=False,
                    **({} if index==0 else dict(dir_fd=self.anchors[index-1][0])))
                _preflight_require_v1(stat.S_ISDIR(info.st_mode) and stat.S_ISDIR(path_info.st_mode)
                    and (info.st_dev,info.st_ino)==identity==(path_info.st_dev,path_info.st_ino),
                    'LINUX_V2_ANCESTOR_ASSOCIATION')
        finally:self.stage=previous

    def _roster(self, fd, row):
        self._reserve(2)
        stage = self.stage
        self._performed()
        stream = os.scandir(fd)
        names = []
        try:
            while True:
                self._meta_attempt()  # Includes StopIteration and native failures.
                try:
                    entry = next(stream)
                except StopIteration:
                    break
                _preflight_require_v1(len(names) < len(row['roster']), 'LINUX_V2_ROSTER_OVERFLOW')
                names.append(entry.name)
        finally:
            self._performed(stage)
            stream.close()
        _preflight_require_v1(sorted(names,key=lambda s:s.encode('utf-8')) == row['roster'],
            'LINUX_V2_SEAL_ROSTER:'+row['path'])

    def _identity(self, fd, row, kind):
        info, flags = self._meta(os.fstat, fd), self.native.flags(fd)
        version, original = self.census._version(info), row['version']
        path = row['path']
        if kind == 'original':
            _preflight_require_v1(version == original and not flags & 16,
                'LINUX_V2_ORIGINAL_GENERATION:'+path)
        elif kind == 'sealed':
            _preflight_require_v1(version == self.post.get(path)
                and flags == self.original_flags[path]|16, 'LINUX_V2_SEAL_GENERATION:'+path)
        else:
            _preflight_require_v1(path in self.completed_originals
                and all(version[i] == original[i] for i in (0,1,3,4,6,9,10))
                and stat.S_IFMT(version[2]) == stat.S_IFMT(original[2]),
                'LINUX_V2_RECOVERY_IDENTITY:'+path)
            mode = 0o555 if row['kind']=='directory' or original[2]&0o111 else 0o444
            allowed_owner = {(original[7],original[8])}
            allowed_modes, allowed_flags = {stat.S_IMODE(original[2])}, {self.original_flags[path]}
            if (path,'chown') in self.attempts: allowed_owner.add((0,0))
            if (path,'chmod') in self.attempts: allowed_modes.add(mode)
            if (path,'set-immutable') in self.attempts: allowed_flags.add(self.original_flags[path]|16)
            _preflight_require_v1((version[7],version[8]) in allowed_owner
                and stat.S_IMODE(version[2]) in allowed_modes and flags in allowed_flags
                and (version[5] == original[5] or any((path,op) in self.attempts
                    for op in ('chown','chmod','set-immutable'))),
                'LINUX_V2_RECOVERY_FOREIGN_FIELDS:'+path)
        return info, flags

    def _walk(self, enter, leave=None, *, roster=False, recovering=False):
        root_fd = self._anchor()
        self._anchors_live()
        errors = []
        def visit(row, fd, parent, name):
            safe = True
            try:
                self._check()
                enter(row,fd)
                if row['kind'] == 'directory':
                    if roster: self._roster(fd,row)
                    for child_name in row['roster']:
                        child = self.row_index[str(Path(row['path'])/child_name)]
                        child_fd = None
                        try:
                            child_fd = self._open(child_name,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC
                                | (os.O_DIRECTORY if child['kind']=='directory' else 0),dir_fd=fd)
                            if not visit(child,child_fd,fd,child_name): safe = False
                        except BaseException as exc:
                            if not recovering:
                                if child_fd is not None:
                                    closing,child_fd=child_fd,None
                                    try:self._close(closing)
                                    except BaseException as close_error:_scan_raise_errors([exc,close_error])
                                raise
                            safe = False
                            self._error(child['path'],exc)
                            errors.append(exc)
                        finally:
                            if child_fd is not None:
                                try:self._close(child_fd)
                                except BaseException as exc:
                                    if not recovering:raise
                                    safe=False
                                    self._error(child['path'],exc)
                                    errors.append(exc)
                if leave is not None: leave(row,fd,safe)
                if parent is not None:
                    at_path = self._meta(os.stat,name,dir_fd=parent,follow_symlinks=False)
                    _preflight_require_v1((at_path.st_dev,at_path.st_ino)
                        == tuple(row['version'][:2]), 'LINUX_V2_UNWIND_ASSOCIATION:'+row['path'])
                return safe
            except BaseException as exc:
                if not recovering: raise
                self._error(row['path'],exc)
                errors.append(exc)
                return False
        parent = self.anchors[-2][0] if len(self.anchors)>1 else None
        visit(self.row_index[str(self.root)],root_fd,parent,self.root.name)
        self._anchors_live()
        return errors

    def _error(self, path, exc):
        self.error_count += 1
        self.restoration_outcomes[self.journal_ids[path]] = 'UNRESOLVED'
        if len(self.error_examples)<64:
            raw = repr(exc).encode('utf-8')[:384]
            self.error_examples.append(dict(entry=self.journal_ids[path],error=raw.decode('utf-8','replace')))

    def _jcall(self, function, *args, **kwargs):
        counts=self.journal_counts[self.phase]
        if counts['calls']>=counts['native_reserved']:
            counts['rejected']+=1
            raise ValidationReliabilityError('ENGVR_PREFLIGHT_DENIED','LINUX_V2_JOURNAL_NATIVE_RESERVATION')
        counts['calls'] += 1
        return function(*args, **kwargs)

    def _journal_open(self):
        _preflight_require_v1(self.journal_path is not None and self.journal_fd is None,
            'LINUX_V2_JOURNAL_OWNER')
        self.journal_fd = self._jcall(os.open,self.journal_path,
            os.O_WRONLY|os.O_APPEND|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
        info = self._jcall(os.fstat,self.journal_fd)
        self.journal_identity = (info.st_dev,info.st_ino)
        self._journal_identity()

    def _journal_identity(self):
        fd_info = self._jcall(os.fstat,self.journal_fd)
        path_info = self._jcall(os.lstat,self.journal_path)
        _preflight_require_v1((fd_info.st_dev,fd_info.st_ino) == self.journal_identity
            == (path_info.st_dev,path_info.st_ino) and fd_info.st_uid == 0
            and fd_info.st_nlink == 1 and stat.S_ISREG(fd_info.st_mode)
            and stat.S_IMODE(fd_info.st_mode) == 0o600 and fd_info.st_size == self.journal_bytes
            and self.census._version(fd_info) == self.census._version(path_info), 'LINUX_V2_JOURNAL_CUSTODY')

    def _record(self, value):
        self._check()
        raw = _preflight_canonical_v1(value)+b'\n'
        counts = self.journal_counts[self.phase]
        limit = self.journal_reservation[self.phase]
        prefix = b'\n' if self.journal_torn and self.phase == 'settlement' else b''
        _preflight_require_v1(not self.journal_torn or self.phase == 'settlement',
            'LINUX_V2_JOURNAL_TORN_WORK_STOP')
        raw = prefix+raw
        if counts['reserved']+len(raw)>limit['bytes'] or counts.get('records',0)+1>limit['records']:
            counts['rejected']+=1
            raise ValidationReliabilityError('ENGVR_PREFLIGHT_DENIED','LINUX_V2_JOURNAL_PHASE_CAPACITY')
        counts['reserved']+=len(raw)
        counts['records']=counts.get('records',0)+1
        counts['native_reserved']+=13
        before_calls=counts['calls']
        self._journal_identity()
        view=memoryview(raw)
        try:
            for unused in range(8):
                self._check()
                count=self._jcall(os.write,self.journal_fd,view)
                _preflight_require_v1(0<count<=len(view),'LINUX_V2_JOURNAL_WRITE')
                self.journal_bytes+=count
                counts['bytes']+=count
                view=view[count:]
                if not view: break
            _preflight_require_v1(not view,'LINUX_V2_JOURNAL_WRITE_ATTEMPTS')
            self._jcall(os.fsync,self.journal_fd)
            self._journal_identity()
        except BaseException:
            self.journal_torn=True
            raise
        finally:
            _preflight_require_v1(counts['calls']-before_calls<=13,'LINUX_V2_JOURNAL_NATIVE_BOUND')
        self.journal_torn=False
        self.journal.append(value)

    def _prepare_journal(self):
        originals = [dict(entry=self.journal_ids[p],original=v) for p,v in self.originals.items()]
        original_bytes = sum(len(_preflight_canonical_v1(v))+1 for v in originals)
        def events(operations):
            return sum(max(len(_preflight_canonical_v1(dict(entry=i,operation=op,result=result)))+1
                for result in ('COMPLETED','UNCERTAIN','OBSERVED'))
                +len(_preflight_canonical_v1(dict(entry=i,operation=op,result='ATTEMPT')))+1
                for i in range(len(self.rows)) for op in operations)
        work = original_bytes+events(('chown','chmod','set-immutable'))
        settlement = events(('restore-flags','restore-owner','restore-mode'))+65536
        diagnostics=sum(v.get('evidence',{}).get('journal_bytes',0) for v in self.recovery_cases)
        _preflight_require_v1(work+settlement+diagnostics<=32*1024**2,'LINUX_V2_JOURNAL_PROSPECTIVE_CAPACITY')
        n=len(self.rows)
        self.journal_reservation = dict(work=dict(bytes=work,records=7*n),
            settlement=dict(bytes=settlement,records=6*n+64),native_setup_close=64)
        self._journal_open()
        for value in originals:
            self._record(value)
            self.completed_originals.add(value['original']['path'])

    def _transition(self, path, operation, call):
        path=str(path)
        self.current_path,self.current_operation=path,operation
        index=self.journal_ids[path]
        self._record(dict(entry=index,operation=operation,result='ATTEMPT'))
        if self.phase=='work': self.attempts.add((path,operation))
        try:
            call()
            self._fault('after-'+operation,path)
        except BaseException as exc:
            try: self._record(dict(entry=index,operation=operation,result='UNCERTAIN'))
            except BaseException as record_error:
                self._error(path,record_error)
            raise
        self._record(dict(entry=index,operation=operation,result='COMPLETED'))

    def _fault(self, point, path):
        # Private finite recovery diagnostics set this callback only for their
        # disposable source tree. It is never serialized or a host grant.
        hook=getattr(self,'_diagnostic_fault',None)
        if hook is not None: hook(point,path)

    def protect(self):
        _preflight_require_v1(self.state=='ENUMERATED' and self.primitive.get('complete')
            and self.primitive.get('restored'),'LINUX_V2_PRIMITIVE_REQUIRED')
        self._anchor()
        self.state='PROTECTING'
        try:
            self.stage='original'
            def acquire(row,fd):
                info,flags=self._identity(fd,row,'original')
                path=row['path']
                self.original_flags[path]=flags
                self.originals[path]=dict(path=path,version=row['version'],flags=flags,
                    kind=row['kind'],roster=row['roster'])
            def acquired(row,fd,safe):
                if row['kind']=='directory': self._identity(fd,row,'original')
            self._walk(acquire,acquired)
            self._prepare_journal()
            self._fault('before-mutation',str(self.root))
            self.stage='protection'
            def change(row,fd):
                before,flags=self._identity(fd,row,'original')
                path=row['path']
                self.protected.append(self.originals[path])
                self._transition(path,'chown',lambda:self._meta(os.fchown,fd,0,0))
                mode=0o555 if row['kind']=='directory' or before.st_mode&0o111 else 0o444
                self._transition(path,'chmod',lambda:self._meta(os.fchmod,fd,mode))
                self._transition(path,'set-immutable',lambda:self.native.flags(fd,flags|16))
                after=self._meta(os.fstat,fd)
                _preflight_require_v1(self.native.flags(fd)==flags|16 and after.st_size==before.st_size
                    and after.st_mtime_ns==before.st_mtime_ns and after.st_uid==after.st_gid==0
                    and stat.S_IMODE(after.st_mode)==mode,'LINUX_V2_TRANSITION_READBACK')
                self.post[path]=self.census._version(after)
            def changed(row,fd,safe):
                if row['kind']=='directory': self._identity(fd,row,'sealed')
            self._walk(change,changed)
            self.state='SEALED'
            self.verify(protected=True)
            self._fault('after-full-protection',str(self.root))
        except BaseException as exc:
            self.failure,self.state=exc,'FAILED'
            raise

    def verify(self, *, protected):
        try:
            _preflight_require_v1(protected and self.phase=='work' and len(self.post)==len(self.rows),
                'LINUX_V2_COMPLETE_SEAL')
            self.stage=next(self.verify_stages)
            self._walk(lambda row,fd:self._identity(fd,row,'sealed'),
                lambda row,fd,safe:self._identity(fd,row,'sealed') if row['kind']=='directory' else None,
                roster=True)
        except BaseException as exc:
            if self.failure is None:self.failure=exc
            self.state='FAILED'
            raise

    def _read(self, fd, amount):
        self._check()
        if self.read_attempts>=2000000:
            self.read_rejected+=1
            raise ValidationReliabilityError('ENGVR_PREFLIGHT_DENIED','LINUX_V2_READ_ATTEMPTS')
        self.read_attempts+=1
        block=os.read(fd,amount)
        self.read_bytes+=len(block)
        _preflight_require_v1(self.read_bytes<=64*1024**3,'LINUX_V2_READ_BYTE_CAPACITY')
        return block

    def readability(self):
        _preflight_require_v1(self.state=='SEALED','LINUX_V2_READABILITY_STATE')
        try:
            self.stage='readability'
            def read(row,fd):
                self._identity(fd,row,'sealed')
                if row['kind']=='directory': return
                self.current_path,self.current_operation=row['path'],'readability'
                extent=0
                while True:
                    self._fault('during-readability',row['path'])
                    block=self._read(fd,min(65536,row['logical_bytes']-extent+1))
                    extent+=len(block)
                    _preflight_require_v1(extent<=row['logical_bytes'],'LINUX_V2_READ_EXTENT')
                    if not block: break
                _preflight_require_v1(extent==row['logical_bytes'],'LINUX_V2_READ_TRUNCATED')
                self._identity(fd,row,'sealed')
            self._walk(read,lambda row,fd,safe:self._identity(fd,row,'sealed')
                if row['kind']=='directory' else None,roster=True)
            self.verify(protected=True)
            self.state='READABLE'
        except BaseException as exc:
            self.failure,self.state=exc,'FAILED'
            raise

    def restore(self, *, deadline_ns=None, processes_settled=False):
        _preflight_require_v1(processes_settled and self.phase=='work','LINUX_V2_SINGLE_SETTLEMENT_ENTRY')
        self.forward_failure=None if self.failure is None else repr(self.failure)
        self.forward_accounting=json.loads(json.dumps(self.accounting))
        self.phase,self.stage,self.state='settlement','settlement','SETTLING'
        if deadline_ns is not None: self.deadline_ns=deadline_ns
        errors=[]
        try:
            self._check()
            _preflight_require_v1(all(v.get('restored') and v.get('removed') for v in self.recovery_cases),
                'LINUX_V2_RECOVERY_FIXTURE_UNRESOLVED')
            if self.attempts:
                def inspect(row,fd): self._identity(fd,row,'recovery')
                def recover(row,fd,safe):
                    path=row['path']
                    _preflight_require_v1(safe,'LINUX_V2_RETAIN_UNRESOLVED_SUBTREE:'+path)
                    info,flags=self._identity(fd,row,'recovery')
                    original=row['version']
                    changes=(('restore-flags',flags!=self.original_flags[path],
                        lambda:self.native.flags(fd,self.original_flags[path])),
                        ('restore-owner',(info.st_uid,info.st_gid)!=(original[7],original[8]),
                        lambda:self._meta(os.fchown,fd,original[7],original[8])),
                        ('restore-mode',stat.S_IMODE(info.st_mode)!=stat.S_IMODE(original[2]),
                        lambda:self._meta(os.fchmod,fd,stat.S_IMODE(original[2]))))
                    for op,needed,call in changes:
                        if needed: self._transition(path,op,call)
                        else:
                            self._record(dict(entry=self.journal_ids[path],operation=op,result='ATTEMPT'))
                            self._record(dict(entry=self.journal_ids[path],operation=op,result='OBSERVED'))
                    after=self._meta(os.fstat,fd)
                    _preflight_require_v1(all(self.census._version(after)[i]==original[i]
                        for i in (0,1,2,3,4,6,7,8,9,10)) and self.native.flags(fd)==self.original_flags[path],
                        'LINUX_V2_RESTORE_READBACK:'+path)
                    self.restoration_outcomes[self.journal_ids[path]]='RESTORED_READBACK'
                errors.extend(self._walk(inspect,recover,roster=True,recovering=True))
            else:
                _preflight_require_v1(not self.primitive or self.primitive.get('restored'),
                    'LINUX_V2_PRIMITIVE_RESTORATION_UNRESOLVED')
        except BaseException as exc: errors.append(exc)
        finally:
            for fd,identity,name in reversed(self.anchors):
                try:
                    if fd in self.owned: self._close(fd)
                except BaseException as exc: errors.append(exc)
            if self.journal_fd is not None:
                fd,self.journal_fd=self.journal_fd,None
                try: self._jcall(os.close,fd)
                except BaseException as exc:
                    self.close_failure_count+=1
                    if len(self.close_failures)<64:
                        self.close_failures.append(dict(journal_fd=fd,error=repr(exc).encode('utf-8')[:384].decode('utf-8','replace')))
                    errors.append(exc)
            if self.owned or self.close_failures:
                errors.append(RuntimeError('LINUX_V2_UNRESOLVED_OWNED_DESCRIPTOR'))
        self.state='FAILED' if errors else 'RESTORED'
        self.settlement_errors=[repr(e).encode('utf-8')[:384].decode('utf-8','replace') for e in errors[:64]]
        if errors:
            raise ValidationReliabilityError('ENGVR_PREFLIGHT_DENIED',
                'LINUX_V2_RESTORATION_FAILED:'+str(len(errors))+':see retained indexed outcomes')

    def evidence(self):
        return dict(accounting=self.accounting, rejected_reservations=self.rejected_reservations,
            journal_reservation=self.journal_reservation,journal_counts=self.journal_counts,
            journal_bytes=self.journal_bytes,journal_torn=self.journal_torn,
            forward_failure=getattr(self,'forward_failure',None),
            forward_accounting=getattr(self,'forward_accounting',None),
            restoration_outcomes=self.restoration_outcomes,restoration_error_count=self.error_count,
            restoration_error_examples=self.error_examples,close_failures=self.close_failures,
            close_failure_count=self.close_failure_count,settlement_errors=getattr(self,'settlement_errors',[]),
            recovery_cases=self.recovery_cases,recovery_reservation=getattr(self,'recovery_reservation',None),
            owned_descriptor_count=len(self.owned))

    def recovery_check(self, *, setup_uid, evidence_root, query, grants):
        """Three tiny real same-filesystem rollbacks, before the real checkout."""
        _preflight_require_v1(self.state=='ENUMERATED' and not self.recovery_cases
            and type(setup_uid) is int and setup_uid>0,'LINUX_V2_RECOVERY_FIXTURE_STATE')
        tiny_ancestors=len((self.workspace/'immutable-recovery-1').parts)
        # For each four-node/three-edge case: original 22, protection 42,
        # complete verification 28; anchor work <=15A. Restoration <=56+16A.
        # A further 100 setup operations cover creation, baseline observations
        # and proved removal of all twelve disposable nodes.
        reservation=dict(work=dict(limit=3*(92+15*tiny_ancestors),reserved=0),
            settlement=dict(limit=3*(56+16*tiny_ancestors),reserved=0))
        total=sum(v['limit'] for v in reservation.values())
        _preflight_require_v1(self.accounting['stages']['setup']['reserved']+total+100
            <=self.accounting['stages']['setup']['limit'],'LINUX_V2_RECOVERY_SETUP_PROGRAMME')
        self._reserve(total)
        self.recovery_reservation=reservation
        for number,point in enumerate(('after-chmod','after-set-immutable','after-full-protection'),1):
            self.stage='setup'
            area=self.workspace/('immutable-recovery-'+str(number))
            result=dict(number=number,nodes=4,point=point,synthetic_fault=True,native_operations=True,
                complete=False,restored=False,removed=False,creation_attempted=True,retained_path=str(area))
            self.recovery_cases.append(result)
            self._meta(os.mkdir,area,0o750)
            children=[area/('payload-'+str(i)) for i in range(3)]
            for child in children:
                fd=self._open(child,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o640)
                try:
                    _preflight_require_v1(os.write(fd,b'owned recovery fixture\n')==23,'LINUX_V2_RECOVERY_FIXTURE_WRITE')
                    os.fsync(fd)
                finally:self._close(fd)
            for path in (*children,area):
                self._meta(os.chown,path,setup_uid,setup_uid,follow_symlinks=False)
            rows=[]
            for path,kind,roster in ((area,'directory',[p.name for p in children]),
                    *((p,'file',[]) for p in children)):
                info=self._meta(os.lstat,path)
                _preflight_require_v1(info.st_dev==self.row_index[str(self.root)]['version'][0],
                    'LINUX_V2_RECOVERY_FIXTURE_FILESYSTEM')
                rows.append(dict(role='repository',path=str(path),observed_path=str(path),kind=kind,
                    version=self.census._version(info),logical_bytes=info.st_size if kind=='file' else 0,
                    roster=roster,aliases=[],acl=None))
            census=_LinuxPreflightCensusV1.__new__(_LinuxPreflightCensusV1)
            census.complete=True
            census.roots=dict(repository=area)
            census.records=rows
            trial=type(self)(census,deadline_ns=self.deadline_ns,workspace=self.workspace,
                run_id=self.run_id+'-recovery-'+str(number))
            trial.journal_path=Path(evidence_root)/('source-recovery-'+str(number)+'.jsonl')
            trial.primitive=dict(self.primitive)
            # Subordinate counters describe the same calls; only this parent's
            # setup ledger contributes them to the checkout's 2M allocation.
            performed=trial._performed
            reserve=trial._reserve
            def admission(amount):
                reserve(amount)
                ledger=reservation[trial.phase]
                _preflight_require_v1(ledger['reserved']+amount<=ledger['limit'],
                    'LINUX_V2_RECOVERY_PREPAID_PHASE')
                ledger['reserved']+=amount
            def count(stage=None):
                self._performed()
                performed(stage)
            trial._reserve=admission
            trial._performed=count
            triggered=[]
            def inject(actual,path):
                if actual==point and not triggered:
                    triggered.append(dict(point=actual,path=path))
                    raise RuntimeError('LINUX_V2_INJECTED_RECOVERY_DIAGNOSTIC:'+point)
            trial._diagnostic_fault=inject
            result['triggered']=triggered
            try:
                try: trial.protect()
                except RuntimeError as exc:
                    result['injected_failure']=repr(exc)
                    _preflight_require_v1(bool(triggered),'LINUX_V2_RECOVERY_NOT_INJECTED')
                else:raise RuntimeError('LINUX_V2_RECOVERY_FAULT_NOT_EXERCISED')
                if number==3:
                    result['denied_start']=_LinuxPreflightScopeV1.denied_start_fixture(trial,query,grants)
                trial.restore(deadline_ns=self.deadline_ns,processes_settled=True)
                result['restored']=trial.state=='RESTORED'
                for row in rows:
                    info=self._meta(os.lstat,row['path'])
                    _preflight_require_v1(all(self.census._version(info)[i]==row['version'][i]
                        for i in (0,1,2,3,4,6,7,8,9,10)),'LINUX_V2_RECOVERY_FIXTURE_READBACK')
                for child in children:
                    fd=self._open(child,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
                    try:
                        _preflight_require_v1(os.read(fd,24)==b'owned recovery fixture\n'
                            and os.read(fd,1)==b'','LINUX_V2_RECOVERY_FIXTURE_BYTES')
                    finally:self._close(fd)
                    self._meta(os.unlink,child)
                self._meta(os.rmdir,area)
                result['removed']=result['complete']=True
            except BaseException as exc:
                result['failure']=repr(exc)
                raise
            finally:
                result['evidence']=trial.evidence()
                if hasattr(trial,'denied_start_result'):result['denied_start']=trial.denied_start_result
                result['retained_path']=None if result['removed'] else str(area)
        _preflight_require_v1(len(self.recovery_cases)==3 and all(v['complete'] for v in self.recovery_cases),
            'LINUX_V2_RECOVERY_PROOF_REQUIRED')

    def primitive_check(self, query):
        """One owned same-filesystem primitive; native denial never gets retried."""
        self._check()
        own = self._meta(os.stat, '/proc/self/ns/user')
        initial = self._meta(os.stat, '/proc/1/ns/user')
        _preflight_require_v1((own.st_dev, own.st_ino) == (initial.st_dev, initial.st_ino) and query.read('/proc/self/uid_map').split() == [b'0', b'0', b'4294967295'], 'LINUX_V2_INITIAL_USER_NAMESPACE')
        mounts = _linux_preflight_mounts_v1(query.read('/proc/self/mountinfo'))
        chosen = max((m for m in mounts if self.root.is_relative_to(Path(m['path']))), key=lambda m: len(m['path']))
        _preflight_require_v1(chosen['fs'] == 'ext4' and chosen['root'] == '/' and (not any((Path(m['path']).is_relative_to(self.root) and Path(m['path']) != self.root for m in mounts))), 'LINUX_V2_ORIGINAL_EXT4_NO_SUBMOUNTS')
        descriptor = self._open_path(self.root)
        try:
            actual = self.native.mount(descriptor)
            info = self._meta(os.fstat, descriptor)
            self.mount_observation = actual
            _preflight_require_v1(actual['magic'] == 61267 and actual['old_id'] == chosen['id'] and (actual['device'] == [os.major(info.st_dev), os.minor(info.st_dev)]) and (not actual['attributes'] & 1048576), 'LINUX_V2_EXT4_IDENTITY_OR_IDMAPPED_VIEW')
        finally:
            self._close(descriptor)
        _preflight_require_v1(self._meta(self.workspace.stat).st_dev == self._meta(self.root.stat).st_dev and (not self.workspace.is_relative_to(self.root)), 'LINUX_V2_PRIMITIVE_SAME_FILESYSTEM')
        area = self.workspace / 'immutable-primitive'
        self._meta(os.mkdir, area, 448)
        path = area / 'held'
        fd = self._meta(os.open, path, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 384)
        directory = self._open_path(area)
        original = {}
        errors = []
        self.primitive = dict(path=str(area), complete=False, write_denial=None, create_denial=None, restored=False, mount=actual)
        restoration = []
        try:
            _preflight_require_v1(os.write(fd, b'QTT immutable primitive\n') == 24, 'LINUX_V2_PRIMITIVE_WRITE')
            os.fsync(fd)
            for label, handle in (('file', fd), ('directory', directory)):
                self.primitive['operation'] = 'get-original-flags:' + label
                flags = self.native.flags(handle)
                original[label] = flags
                _preflight_require_v1(not flags & 16, 'LINUX_V2_PREEXISTING_IMMUTABLE')
                self.primitive['operation'] = 'set-immutable:' + label
                self.native.flags(handle, flags | 16)
                _preflight_require_v1(self.native.flags(handle) == flags | 16, 'LINUX_V2_PRIMITIVE_READBACK')
            try:
                os.pwrite(fd, b'X', 0)
            except OSError as exc:
                self.primitive['write_denial'] = dict(errno=exc.errno, error=str(exc))
                _preflight_require_v1(exc.errno == 1, 'LINUX_V2_PRIMITIVE_WRITE_DENIAL')
            else:
                raise RuntimeError('LINUX_V2_PREOPENED_WRITE_SUCCEEDED')
            try:
                unexpected = self._meta(os.open, 'unexpected', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 384, dir_fd=directory)
            except OSError as exc:
                self.primitive['create_denial'] = dict(errno=exc.errno, error=str(exc))
                _preflight_require_v1(exc.errno == 1, 'LINUX_V2_PRIMITIVE_CREATE_DENIAL')
            else:
                self._close(unexpected)
                raise RuntimeError('LINUX_V2_PROTECTED_CREATE_SUCCEEDED')
            _preflight_require_v1(os.pread(fd, 25, 0) == b'QTT immutable primitive\n', 'LINUX_V2_PRIMITIVE_BYTES')
            self.primitive['complete'] = True
        except BaseException as exc:
            errors.append(exc)
            self.primitive['failure'] = repr(exc)
            self.primitive['errno'] = getattr(exc, 'errno', None)
        finally:
            for label, handle in (('directory', directory), ('file', fd)):
                if label in original:
                    try:
                        now = self.native.flags(handle)
                        _preflight_require_v1(now in (original[label], original[label] | 16), 'LINUX_V2_PRIMITIVE_FOREIGN_FLAGS')
                        if now != original[label]:
                            self.native.flags(handle, original[label])
                        _preflight_require_v1(self.native.flags(handle) == original[label], 'LINUX_V2_PRIMITIVE_RESTORE')
                    except BaseException as exc:
                        errors.append(exc)
                        restoration.append(repr(exc))
            try:
                self.primitive['observed_bytes_hex'] = os.pread(fd, 25, 0).hex()
                info, area_info = (self._meta(os.fstat, fd), self._meta(os.fstat, directory))
                _preflight_require_v1((self._meta(path.lstat).st_dev, self._meta(path.lstat).st_ino) == (info.st_dev, info.st_ino) and (self._meta(area.lstat).st_dev, self._meta(area.lstat).st_ino) == (area_info.st_dev, area_info.st_ino), 'LINUX_V2_PRIMITIVE_CLEANUP_IDENTITY')
            except BaseException as exc:
                restoration.append(repr(exc))
                errors.append(exc)
            self._close(directory)
            self._close(fd)
        self.primitive['original_flags'] = original
        self.primitive['restoration_errors'] = restoration
        self.primitive['restored'] = not restoration
        if not restoration:
            if self._meta(path.exists):
                self._meta(os.unlink, path)
            self._meta(os.rmdir, area)
            self.primitive['removed'] = True
        if errors:
            self.state = 'FAILED'
            self.failure = errors[0]
        _scan_raise_errors(errors)

    def publish(self, path):
        _preflight_require_v1(self.state == 'READABLE', 'LINUX_V2_PUBLISH_STATE')
        self.stage = 'projection'
        files = []
        dirs = []
        for row in self.rows:
            path_value = Path(row['path'])
            relative = path_value.relative_to(self.root).as_posix()
            info = self._meta(path_value.lstat)
            flags = self.original_flags[str(path_value)] | 16
            item = _linux_source_row_v2(relative, 'GIT_ADMIN' if relative == '.git' or relative.startswith('.git/') else 'WORKTREE', info, flags)
            if row['kind'] == 'directory':
                item.append([list(v) for v in self.directories[str(path_value)]])
                dirs.append(item)
            else:
                files.append(item)
        files.sort(key=lambda r: r[0].encode('utf-8'))
        dirs.sort(key=lambda r: r[0].encode('utf-8'))
        totals = self.census.document()['logical_bytes']
        value = dict(basis_kind='NATIVE_IMMUTABLE_V2', run_id=self.run_id, repository_root=str(self.root), index_path=str(self.root / '.git/index'), source_root_identity=list(self.post[str(self.root)][:2]), source_generation_ns=time.monotonic_ns(), files=files, directories=dirs, category_totals={k: totals[k] for k in ('R', 'G', 'I')})
        parsed = _linux_source_manifest_v2(value)
        raw = _preflight_canonical_v1(value)
        _preflight_require_v1(len(raw) <= 32 * 1024 ** 2, 'LINUX_V2_MANIFEST_CAPACITY')
        _atomic_write_bytes_v1(path, raw, control_mode=292)
        self.raw = raw
        self.descriptor = dict(kind='NATIVE_IMMUTABLE_V2', path=str(path), physical_version=list(_scan_same_api_version(self._meta(Path(path).lstat))), byte_length=len(raw), catalog_entry_count=parsed[3])
        self.verify(protected=True)
        return self.descriptor

    def read_administration(self, path, limit):
        """The existing exact Git/config owner, after seal, without an eager tree."""
        self.stage = 'setup'
        self._check()
        path = Path(path)
        _preflight_require_v1(str(path) in self.files and self.state in ('READABLE', 'IN_USE'), 'LINUX_V2_ADMINISTRATION_OPERAND')
        fd = self._open_path(path)
        try:
            before = self._meta(os.fstat, fd)
            _preflight_require_v1(before.st_size <= limit and self.census._version(before) == self.post[str(path)] and (self.native.flags(fd) == self.original_flags[str(path)] | 16), 'LINUX_V2_ADMINISTRATION_IDENTITY')
            parts = []
            extent = 0
            while True:
                self._check()
                block = self._read(fd, min(65536, before.st_size - extent + 1))
                self.auxiliary_read_bytes += len(block)
                extent += len(block)
                _preflight_require_v1(extent <= before.st_size, 'LINUX_V2_ADMINISTRATION_EXTENT')
                if not block:
                    break
                parts.append(block)
            _preflight_require_v1(extent == before.st_size and self.census._version(self._meta(os.fstat, fd)) == self.post[str(path)] == self.census._version(self._meta(path.lstat)) and (self.native.flags(fd) == self.original_flags[str(path)] | 16), 'LINUX_V2_ADMINISTRATION_CHANGED')
            self._check()
            return b''.join(parts)
        finally:
            self._close(fd)




class _LinuxPreflightCensusV1:
    """Bounded metadata observation, never byte capture, custody or a grant."""
    def __init__(self, repository, installation, git, *, deadline_ns, installation_acl=False, setup_uid=None):
        self.installation_acl, self.setup_uid = installation_acl, setup_uid
        self.acl_pool, self.acl_pool_bytes = [], 0
        self.acl_native = _LinuxSourceNativeV2() if installation_acl else None
        self.xattr_bytes = 0
        self.roots = dict(repository=Path(repository), installation=Path(installation), git=Path(git))
        _preflight_require_v1(all(p.is_absolute() for p in self.roots.values()), 'LINUX_CENSUS_ABSOLUTE_ROOTS')
        self.deadline_ns = min(deadline_ns, time.monotonic_ns()+600*10**9)
        self.records = []
        self.counts = dict(files=0, entries=0, metadata_attempts=0, verification_records=0,
            direct_regular_file_payload_reads=0, direct_regular_file_payload_bytes=0)
        self.retained = 0
        self.complete = False
        self.started = False
        self.failures = []
        self.current_path = None
        self.current_operation = None
        self.last_stat = None
    def _check(self):
        _preflight_require_v1(time.monotonic_ns() < self.deadline_ns, 'LINUX_CENSUS_DEADLINE')
    def _attempt(self, operation, path):
        self.current_path, self.current_operation = str(path), operation
        self.counts['metadata_attempts'] += 1
        self._check()
        _preflight_require_v1(self.counts['metadata_attempts'] <= 2_000_000, 'LINUX_CENSUS_OPERATIONS')
    def _retain(self, value):
        self._check()
        amount = len(_preflight_canonical_v1(value))+1
        # Reserve bounded envelope/failure/report space before retaining records.
        _preflight_require_v1(self.retained+amount <= 31*1024**2, 'LINUX_CENSUS_SERIALIZED_CAPACITY')
        self.retained += amount
    @staticmethod
    def _version(info):
        return [info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns,
            info.st_ctime_ns, info.st_nlink, info.st_uid, info.st_gid,
            getattr(info, 'st_file_attributes', 0), getattr(info, 'st_reparse_tag', 0)]
    def _stat(self, path):
        self._attempt('lstat', path)
        _preflight_require_v1(len(str(path).encode('utf-8')) <= 4096, 'LINUX_CENSUS_PATH_BYTES')
        info = path.lstat()
        self.last_stat = dict(path=str(path), version=self._version(info))
        return info
    def _acl(self, path, *, installation=False):
        if self.acl_native is None:
            self._attempt('listxattr', path)
            _preflight_require_v1(hasattr(os, 'listxattr'), 'LINUX_CENSUS_ACL_OBSERVATION_UNAVAILABLE')
            names = os.listxattr(path, follow_symlinks=False)
            _preflight_require_v1(not any(n in ('system.posix_acl_access','system.posix_acl_default')
                for n in names), 'LINUX_CENSUS_UNSUPPORTED_ACL')
            return None
        self._attempt('acl-open-nofollow',path)
        fd = _linux_source_open_v2(path,attempt=lambda:self._attempt('acl-open-component',path))
        try:
            self._attempt('acl-fstat-before',path)
            before = os.fstat(fd)
            self._attempt('acl-lstat-before',path)
            _preflight_require_v1(self._version(before)==self._version(path.lstat()), 'LINUX_CENSUS_ACL_IDENTITY')
            def delivered(count):
                self.xattr_bytes += count
                self._check()
            raw = self.acl_native.acl(fd,attempt=lambda op:self._attempt(op,path),delivered=delivered)
            refs=[]
            for default,value in zip((False,True),raw,strict=True):
                _preflight_require_v1(not default or value is None or stat.S_ISDIR(before.st_mode), 'LINUX_ACL_DEFAULT_REGULAR_FILE')
                if value is None: refs.append(None);continue
                if value not in self.acl_pool:
                    _preflight_require_v1(len(self.acl_pool)<4096 and self.acl_pool_bytes+len(value)<=4*1024**2,
                        'LINUX_ACL_INTERN_CAPACITY')
                    self._retain(value.hex()); self.acl_pool.append(value);self.acl_pool_bytes+=len(value)
                refs.append(self.acl_pool.index(value))
                _linux_acl_parse_v2(value,default=default,mode=before.st_mode)
            _preflight_require_v1(installation or raw==(None,None), 'LINUX_CENSUS_UNSUPPORTED_ACL')
            _preflight_require_v1(not installation or (type(self.setup_uid) is int and self.setup_uid>0
                and before.st_uid in (0,self.setup_uid) and not before.st_mode&(stat.S_ISUID|stat.S_ISGID)),
                'LINUX_INSTALLATION_OWNER_OR_SETID')
            self._attempt('acl-fstat-after',path)
            after=os.fstat(fd)
            self._attempt('acl-lstat-after',path)
            _preflight_require_v1(self._version(after)==self._version(before)==self._version(path.lstat()),
                'LINUX_CENSUS_ACL_CHANGED')
            return refs
        finally: os.close(fd)
    def _roster(self, path, *, retaining, expected=None):
        self._attempt('scandir', path)
        names = []
        with os.scandir(path) as stream:
            while True:
                self._attempt('scandir-next', path)
                try:
                    entry = next(stream)
                except StopIteration:
                    break
                self.counts['entries'] += 1
                _preflight_require_v1(self.counts['entries'] <= 200000, 'LINUX_CENSUS_ENTRIES')
                _preflight_require_v1(len(str(path/entry.name).encode('utf-8')) <= 4096, 'LINUX_CENSUS_PATH_BYTES')
                if retaining:
                    self._retain(entry.name)
                if expected is not None:
                    _preflight_require_v1(len(names) < len(expected) and entry.name in expected,
                        'LINUX_CENSUS_ROSTER_CHANGED')
                names.append(entry.name)
        names.sort(key=lambda name:name.encode('utf-8'))
        _preflight_require_v1(len({n.casefold() for n in names}) == len(names), 'LINUX_CENSUS_CASE_ALIAS')
        return names
    def _alias(self, path, root):
        hops = []
        current = path
        for _ in range(64):
            info = self._stat(current)
            if not stat.S_ISLNK(info.st_mode):
                _preflight_require_v1(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                    and not _stat_is_reparse_point(info), 'LINUX_CENSUS_ALIAS_REGULAR_TARGET')
                return current, info, hops
            self._attempt('readlink', current)
            target = os.readlink(current)
            hop = dict(path=str(current), version=self._version(info), target=target)
            self._retain(hop)
            hops.append(hop)
            current = Path(os.path.normpath(str(current.parent/target)))
            _preflight_require_v1(current.is_relative_to(root) and current != root,
                'LINUX_CENSUS_ALIAS_OUTSIDE_INSTALLATION')
            # Never follow an intermediate directory alias, even inside the prefix.
            for parent in (*reversed(current.relative_to(root).parents),):
                actual = root/parent
                parent_info = self._stat(actual)
                _preflight_require_v1(stat.S_ISDIR(parent_info.st_mode)
                    and not _stat_is_reparse_point(parent_info), 'LINUX_CENSUS_ALIAS_DIRECTORY')
        raise ValidationReliabilityError('ENGVR_PREFLIGHT_DENIED', 'LINUX_CENSUS_ALIAS_DEPTH')
    def _walk(self, role, path, depth):
        self.current_path, self.current_operation = str(path), 'walk'
        self._check()
        _preflight_require_v1(depth <= 64, 'LINUX_CENSUS_DEPTH')
        info = self._stat(path)
        observed, hops = path, []
        if stat.S_ISLNK(info.st_mode) and role == 'installation':
            observed, info, hops = self._alias(path, self.roots[role])
            if self.installation_acl:
                _preflight_require_v1(all(hop['version'][7] in (0,self.setup_uid) for hop in hops),
                    'LINUX_INSTALLATION_ALIAS_OWNER')
        _preflight_require_v1(not _stat_is_reparse_point(info) and
            (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode) and info.st_nlink == 1),
            'LINUX_CENSUS_UNSUPPORTED_SOURCE_KIND')
        acl = self._acl(observed,installation=role == 'installation')
        directory = stat.S_ISDIR(info.st_mode)
        if not directory:
            self.counts['files'] += 1
            _preflight_require_v1(self.counts['files'] <= 100000, 'LINUX_CENSUS_FILES')
            _preflight_integer_v1(info.st_size)
        row = dict(role=role, path=str(path), observed_path=str(observed),
            kind='directory' if directory else 'file', version=self._version(info),
            logical_bytes=0 if directory else info.st_size, aliases=[], roster=[], acl=acl)
        self._retain(row)
        row['aliases'] = hops
        self.records.append(row)
        if directory:
            row['roster'] = self._roster(path, retaining=True)
            for name in row['roster']:
                self._walk(role, path/name, depth+1)
    def _verify(self):
        for row in self.records:
            path = Path(row['observed_path'])
            info = self._stat(path)
            _preflight_require_v1(self._version(info) == row['version'], 'LINUX_CENSUS_VERSION_CHANGED')
            _preflight_require_v1(self._acl(path,installation=row['role']=='installation')==row['acl'], 'LINUX_CENSUS_ACL_CHANGED')
            for hop in row['aliases']:
                alias = Path(hop['path'])
                _preflight_require_v1(self._version(self._stat(alias)) == hop['version'], 'LINUX_CENSUS_ALIAS_CHANGED')
                self._attempt('readlink', alias)
                _preflight_require_v1(os.readlink(alias) == hop['target'], 'LINUX_CENSUS_ALIAS_CHANGED')
            if row['kind'] == 'directory':
                _preflight_require_v1(self._roster(path, retaining=False, expected=set(row['roster'])) == row['roster'],
                    'LINUX_CENSUS_ROSTER_CHANGED')
                _preflight_require_v1(self._version(self._stat(path)) == row['version'], 'LINUX_CENSUS_VERSION_CHANGED')
            self.counts['verification_records'] += 1
        self._check()
    def run(self):
        _preflight_require_v1(not self.started, 'LINUX_CENSUS_SINGLE_SWEEP')
        self.started = True
        try:
            for role, root in self.roots.items():
                self._walk(role, root, 0)
            self._verify()
            self.complete = True
        except Exception as exc:
            self.failures.append(dict(path=self.current_path, operation=self.current_operation,
                error=repr(exc)[:2048], errno=getattr(exc, 'errno', None), last_successful_stat=self.last_stat))
        return self.document()
    def document(self):
        totals = dict(R=0, G=0, I=0, S=0, E=0)
        file_counts = dict.fromkeys(totals, 0)
        physical = {}
        largest = dict(R=[], G=[])
        index_found = False
        for row in self.records:
            if row['kind'] != 'file':
                continue
            path = Path(row['path'])
            category = 'S' if row['role'] == 'installation' else 'E' if row['role'] == 'git' else (
                'G' if path.is_relative_to(self.roots['repository']/'.git') else 'R')
            amount = row['logical_bytes']
            totals[category] += amount
            file_counts[category] += 1
            physical[tuple(row['version'][:2])] = amount
            if path == self.roots['repository']/'.git/index':
                totals['I'], file_counts['I'], index_found = amount, 1, True
            if category in largest:
                largest[category].append(dict(path=str(path), bytes=amount))
                largest[category].sort(key=lambda v:(-v['bytes'], v['path']))
                del largest[category][20:]
        return dict(schema='QTT_PR298_CAPTURE_CENSUS_V1', roots={k:str(v) for k,v in self.roots.items()},
            complete_size_census=self.complete, complete_capture=False, counts=dict(self.counts),
            logical_bytes=totals, file_counts=file_counts, active_index_found=index_found,
            physical_unique_files=len(physical), physical_unique_bytes=sum(physical.values()),
            largest_working_files=largest['R'], largest_git_files=largest['G'], records=self.records,
            failures=list(self.failures), metadata_retention_accounted_bytes=self.retained,
            acl_values_hex=[value.hex() for value in self.acl_pool],acl_distinct_raw_bytes=self.acl_pool_bytes,
            last_acl_observation=None if self.acl_native is None else self.acl_native.last_acl,
            xattr_delivered_bytes=self.xattr_bytes,
            bootstrap_and_manager_io='SEPARATE_NOT_MEASURED_AS_ZERO',
            observation_is_content_identity=False, observation_is_custody=False, observation_is_authority=False)
class _LinuxPreflightCaptureV1:
    """Exact original bytes and authorized metadata transitions, never a checkout copy."""
    def __init__(self,root,*,byte_limit,deadline_ns,installation=False,shared_capture=None):
        self.root = Path(_linux_preflight_path_v1(str(root)))
        self.byte_limit,self.deadline_ns,self.installation = byte_limit,deadline_ns,installation
        self.files,self.directories,self.original,self.aliases = {},{}, {},{}
        self.byte_count,self.entries,self.read_bytes = 0,0,0
        self.shared_capture = dict(files=0,entries=0) if shared_capture is None else shared_capture
        self.protected = []
        self._walk(self.root,0)
    def _check(self,path,depth):
        _preflight_require_v1(time.monotonic_ns() < self.deadline_ns and depth <= 64
            and len(str(path).encode('utf-8')) <= 4096,'LINUX_PREFLIGHT_CAPTURE_DEADLINE_OR_PATH')
    def _walk(self,path,depth):
        self._check(path,depth)
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) and self.installation:
            target = path.resolve(strict=True)
            _preflight_require_v1(target.is_relative_to(self.root) and target != path,
                'LINUX_PREFLIGHT_INSTALLATION_ALIAS')
            resolved = target.lstat()
            _preflight_require_v1(stat.S_ISREG(resolved.st_mode),'LINUX_PREFLIGHT_ALIAS_REGULAR_TARGET')
            self.aliases[str(path)] = str(target)
            info = resolved
            observed_path = target
        else:
            observed_path = path
        _preflight_require_v1(not any(name in ('system.posix_acl_access','system.posix_acl_default')
            for name in os.listxattr(observed_path,follow_symlinks=False)),'LINUX_PREFLIGHT_UNSUPPORTED_ACL:'+str(path))
        self.original[str(path)] = dict(device=info.st_dev,inode=info.st_ino,uid=info.st_uid,gid=info.st_gid,
            mode=stat.S_IMODE(info.st_mode),version=_preflight_stamp_v1(info))
        if stat.S_ISDIR(info.st_mode):
            before = _preflight_stamp_v1(info)
            delivered = []
            with os.scandir(path) as scan:
                for entry in scan:
                    self.entries += 1; self.shared_capture['entries'] += 1
                    _preflight_require_v1(self.shared_capture['entries'] <= 200000,
                        'LINUX_PREFLIGHT_CAPTURE_ENTRIES')
                    delivered.append(entry.name)
            names = tuple(sorted(delivered,key=lambda text:text.encode('utf-8')))
            _preflight_require_v1(len({n.casefold() for n in names}) == len(names),'LINUX_PREFLIGHT_CAPTURE_ALIAS')
            roster = []
            for name in names:
                child = path/name
                self._walk(child,depth+1)
                roster.append((name,'directory' if str(child) in self.directories else 'file'))
            _preflight_require_v1(_preflight_stamp_v1(path.lstat()) == before,'LINUX_PREFLIGHT_CAPTURE_DIRECTORY_DRIFT')
            self.directories[str(path)] = tuple(roster)
        else:
            self.shared_capture['files'] += 1
            _preflight_require_v1(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                and self.shared_capture['files'] <= 100000,'LINUX_PREFLIGHT_CAPTURE_REGULAR_FILE:'+str(path))
            self.byte_count += info.st_size
            _preflight_require_v1(self.byte_count <= self.byte_limit,
                'LINUX_PREFLIGHT_CAPTURE_BYTE_CAPACITY:'+json.dumps(dict(root=str(self.root),path=str(path),
                    attempted_bytes=self.byte_count,byte_limit=self.byte_limit,file_bytes=info.st_size,
                    acquired_bytes=self.read_bytes,files=self.shared_capture['files'],
                    entries=self.shared_capture['entries'],complete_capture=False),sort_keys=True))
            fd = os.open(observed_path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
            try:
                opened = os.fstat(fd)
                _preflight_require_v1(_scan_same_api_version(opened) == _scan_same_api_version(info),
                    'LINUX_PREFLIGHT_CAPTURE_OPEN_CHANGED')
                pieces = []
                remaining = info.st_size
                while remaining:
                    self._check(path,depth)
                    block = os.read(fd,min(remaining,65536))
                    _preflight_require_v1(bool(block),'LINUX_PREFLIGHT_CAPTURE_TRUNCATED')
                    self.read_bytes += len(block)
                    pieces.append(block); remaining -= len(block)
                _preflight_require_v1(os.read(fd,1) == b'' and _scan_same_api_version(os.fstat(fd)) ==
                    _scan_same_api_version(info) == _scan_same_api_version(observed_path.lstat()),
                    'LINUX_PREFLIGHT_CAPTURE_FILE_DRIFT')
                self.files[str(path)] = b''.join(pieces)
            finally: os.close(fd)
    def protect(self):
        _preflight_require_v1(not self.installation and not self.protected and os.geteuid() == 0,
            'LINUX_PREFLIGHT_PROTECTION_OWNER')
        for text,original in self.original.items():
            path = Path(text); info = path.lstat()
            _preflight_require_v1(_preflight_stamp_v1(info) == original['version'],
                'LINUX_PREFLIGHT_PREPROTECTION_GENERATION')
            os.chown(path,0,0,follow_symlinks=False)
            self.protected.append(text)  # Retain even if the following chmod fails.
            os.chmod(path,0o555 if stat.S_ISDIR(info.st_mode) or original['mode'] & 0o111 else 0o444,
                follow_symlinks=False)
        self.verify(protected=True)
    def verify(self,*,protected):
        for text,original in self.original.items():
            self._check(Path(text),len(Path(text).relative_to(self.root).parts))
            path = Path(self.aliases.get(text,text)); info = path.lstat()
            _preflight_require_v1((info.st_dev,info.st_ino) == (original['device'],original['inode']),
                'LINUX_PREFLIGHT_CAPTURE_OBJECT_CHANGED')
            if protected:
                expected = 0o555 if text in self.directories or original['mode'] & 0o111 else 0o444
                _preflight_require_v1((info.st_uid,info.st_gid,stat.S_IMODE(info.st_mode)) == (0,0,expected),
                    'LINUX_PREFLIGHT_PROTECTED_ATTRIBUTES')
            if text in self.files:
                fd = os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
                try:
                    before = os.fstat(fd)
                    _preflight_require_v1((before.st_dev,before.st_ino) == (info.st_dev,info.st_ino),
                        'LINUX_PREFLIGHT_VERIFY_DESCRIPTOR')
                    raw = self.files[text]
                    for offset in range(0,len(raw),65536):
                        self._check(path,0)
                        observed = os.read(fd,min(65536,len(raw)-offset))
                        self.read_bytes += len(observed)
                        _preflight_require_v1(observed == raw[offset:offset+65536],
                            'LINUX_PREFLIGHT_CAPTURE_BYTES_CHANGED:'+text)
                    _preflight_require_v1(os.read(fd,1) == b'' and _scan_same_api_version(os.fstat(fd)) ==
                        _scan_same_api_version(before) == _scan_same_api_version(path.lstat()),
                        'LINUX_PREFLIGHT_VERIFY_CHANGED')
                finally: os.close(fd)
            else:
                with os.scandir(path) as scan: names = tuple(sorted(e.name for e in scan))
                _preflight_require_v1(names == tuple(sorted(n for n,k in self.directories[text])),
                    'LINUX_PREFLIGHT_CAPTURE_ROSTER_CHANGED')
    def copy_installation(self,destination):
        _preflight_require_v1(self.installation and not Path(destination).exists(),'LINUX_PREFLIGHT_COPY_ONLY_INSTALLATION')
        destination = Path(destination)
        for text in sorted(self.directories,key=lambda p:len(Path(p).parts)):
            target = destination/Path(text).relative_to(self.root)
            target.mkdir(mode=0o755)
        for text,raw in self.files.items():
            target = destination/Path(text).relative_to(self.root)
            with target.open('xb') as stream:
                _preflight_require_v1(stream.write(raw) == len(raw),'LINUX_PREFLIGHT_INSTALLATION_COPY_SHORT')
                os.fchmod(stream.fileno(),0o555 if self.original[text]['mode'] & 0o111 else 0o444)
                stream.flush(); os.fsync(stream.fileno())
            _preflight_require_v1(target.read_bytes() == raw,'LINUX_PREFLIGHT_INSTALLATION_COPY_DIFFERS')
        for text in sorted(self.directories,key=lambda p:len(Path(p).parts),reverse=True):
            os.chmod(destination/Path(text).relative_to(self.root),0o555)
        self.verify(protected=False)
    def restore(self):
        errors = []
        for text in reversed(self.protected):
            try:
                path = Path(text); original = self.original[text]; info = path.lstat()
                _preflight_require_v1((info.st_dev,info.st_ino) == (original['device'],original['inode']),
                    'LINUX_PREFLIGHT_RESTORE_OBJECT_CHANGED')
                os.chown(path,original['uid'],original['gid'],follow_symlinks=False)
                os.chmod(path,original['mode'],follow_symlinks=False)
                actual = path.lstat()
                _preflight_require_v1((actual.st_uid,actual.st_gid,stat.S_IMODE(actual.st_mode)) ==
                    (original['uid'],original['gid'],original['mode']),'LINUX_PREFLIGHT_RESTORE_ATTRIBUTES')
            except BaseException as exc: errors.append(exc)
        _scan_raise_errors(errors)


class _LinuxPreflightProcessV1:
    """Transient service adapter beneath supervise_command; launcher status is separate."""
    def __init__(self,scope):
        self.scope = scope
        self.pid = None
        self.returncode = None
        self.pidfd = None
        self.next_poll = 0.0
        self.stdout = _LinuxPreflightTailV1(scope.spool/'command-1.stdout.bin',original_evidence=True)
        self.stderr = _LinuxPreflightTailV1(scope.spool/'command-1.stderr.bin',original_evidence=True)
    def poll(self):
        if self.returncode is not None: return self.returncode
        if self.pidfd is None: raise RuntimeError('LINUX_PREFLIGHT_MAIN_PIDFD_UNAVAILABLE')
        if time.monotonic() < self.next_poll: return None
        self.next_poll = time.monotonic()+0.2
        self.scope.query.check(settling=True)
        import select
        poll = select.poll(); poll.register(self.pidfd,select.POLLIN)
        if not poll.poll(0): return None
        status = self.scope.show(self.scope.name+'.service',settling=True)
        _preflight_require_v1(status['InvocationID'] == self.scope.invocation,
            'LINUX_PREFLIGHT_TERMINAL_INVOCATION')
        code,number = int(status['ExecMainCode']),int(status['ExecMainStatus'])
        if code == 0 and status['ActiveState'] in ('activating','active','deactivating'):
            # The held pidfd can signal before the manager processes SIGCHLD.
            # This is a retained pending observation, not a failed witness retry.
            self.scope.history.append(dict(terminal_manager_pending=status,main_pidfd_terminal=True))
            return None
        _preflight_require_v1(code in (1,2,3),'LINUX_PREFLIGHT_NATIVE_EXIT_UNAVAILABLE')
        self.returncode = number if code == 1 else -number
        self.scope.history.append(dict(terminal_unit=status,main_pidfd_terminal=True))
        if self.returncode == 0:
            _preflight_require_v1(status['Result'] == 'success','LINUX_PREFLIGHT_MANAGER_RESULT')
        return self.returncode
    def wait(self,timeout=None):
        end = self.scope.settlement_deadline_ns if timeout is None else min(self.scope.settlement_deadline_ns,
            time.monotonic_ns()+int(timeout*10**9))
        while time.monotonic_ns() < end:
            result = self.poll()
            if result is not None: return result
            time.sleep(0.1)
        raise subprocess.TimeoutExpired(self.scope.argv,timeout)


def _linux_preflight_syscalls_v1(query):
    """Resolve the five source-owned groups from trusted installed systemd/seccomp."""
    import ctypes
    groups = ('@mount','@reboot','@swap','@raw-io','@module')
    raw = query.command(('/usr/bin/systemd-analyze','--no-pager','syscall-filter',*groups))
    seen, names = set(),set()
    for line in raw.decode('ascii','strict').splitlines():
        word = line.strip()
        if not word or word.startswith('#'): continue
        if word.startswith('@'):
            _preflight_require_v1(word in groups and not line[:1].isspace() and word not in seen,
                'LINUX_PREFLIGHT_SYSCALL_GROUP_SHAPE')
            seen.add(word)
        else:
            _preflight_require_v1(re.fullmatch('[a-zA-Z0-9_]{1,128}',word) is not None,
                'LINUX_PREFLIGHT_SYSCALL_NAME')
            names.add(word)
    _preflight_require_v1(seen == set(groups) and 0 < len(names) <= 4096,'LINUX_PREFLIGHT_SYSCALL_GROUP_COVERAGE')
    # No install or fallback: these are the trusted native system libraries used
    # by the selected manager. Only name/number queries are invoked, never load().
    native = ctypes.CDLL('libseccomp.so.2')
    resolve = native.seccomp_syscall_resolve_name
    resolve.argtypes,resolve.restype = [ctypes.c_char_p],ctypes.c_int
    name_for = native.seccomp_syscall_resolve_num_arch
    name_for.argtypes,name_for.restype = [ctypes.c_uint32,ctypes.c_int],ctypes.c_void_p
    libc = ctypes.CDLL(None); release = libc.free
    release.argtypes,release.restype = [ctypes.c_void_p],None
    expected = set()
    for name in sorted(names):
        query.check()
        number = resolve(name.encode('ascii'))
        if number == -1:
            query.record('syscall-name-unavailable',name,b'libseccomp native name returned -1')
            continue
        pointer = name_for(0,number)
        _preflight_require_v1(bool(pointer),'LINUX_PREFLIGHT_SYSCALL_NUMBER_NAME')
        try:
            value = ctypes.string_at(pointer).decode('ascii','strict')
            _preflight_require_v1(re.fullmatch('[a-zA-Z0-9_]{1,128}',value) is not None,
                'LINUX_PREFLIGHT_SYSCALL_RESOLVED_NAME')
            expected.add(value)
        finally: release(pointer)
    _preflight_require_v1(expected,'LINUX_PREFLIGHT_SYSCALL_GROUP_UNAVAILABLE')
    query.record('syscall-policy',groups,' '.join(sorted(expected)).encode('ascii'))
    return frozenset(expected)


_LINUX_PREFLIGHT_SERVICE_READBACK_V1 = {
    'Type':'exec','Restart':'no','RemainAfterExit':'yes','DynamicUser':'yes','UMask':'0077',
    'NoNewPrivileges':'yes','CapabilityBoundingSet':'','AmbientCapabilities':'',
    'PrivateDevices':'yes','PrivateNetwork':'yes','PrivateIPC':'yes','PrivateTmp':'yes',
    'ProtectSystem':'strict','ProtectHome':'tmpfs','MountAPIVFS':'yes','ProtectProc':'invisible',
    'ProtectControlGroups':'yes','ProtectKernelTunables':'yes','ProtectKernelModules':'yes',
    'ProtectKernelLogs':'yes','RestrictSUIDSGID':'yes','RestrictRealtime':'yes','RestrictNamespaces':'yes',
    'LockPersonality':'yes','RestrictAddressFamilies':'AF_UNIX','SystemCallArchitectures':'native',
    'MemoryAccounting':'yes','MemoryMax':'6442450944','MemorySwapMax':'0','TasksAccounting':'yes',
    'TasksMax':'64','CPUAccounting':'yes','CPUQuotaPerSecUSec':'2s','CPUQuotaPeriodUSec':'100ms',
    'RuntimeMaxUSec':'1h','TimeoutStartUSec':'1min','TimeoutStopUSec':'10s','KillMode':'control-group',
    'SendSIGKILL':'yes','LimitCORE':'0','LimitNOFILE':'1024','LimitFSIZE':'67108864',
    'StandardInput':'null',
    'StandardOutput':'append','StandardError':'append',
}


def _linux_preflight_unit_policy_v1(status, *, name, root, repository, runtime, syscall_filter):
    _preflight_require_v1(type(status) is dict,'LINUX_PREFLIGHT_UNIT_READBACK_TYPE')
    expected = {**_LINUX_PREFLIGHT_SERVICE_READBACK_V1,'RootDirectory':root,'WorkingDirectory':repository,
        'RuntimeDirectory':'','Slice':name+'.slice'}
    for key,wanted in expected.items():
        _preflight_require_v1(status.get(key) == wanted,'LINUX_PREFLIGHT_UNIT_READBACK:'+key)
    for key,logical,label in (
            ('InaccessiblePaths',('/dev/shm','/dev/mqueue','/dev/hugepages'),'LINUX_PREFLIGHT_DEVICE_MASK_READBACK'),
            ('ReadWritePaths',(runtime,'/tmp','/var/tmp'),'LINUX_PREFLIGHT_WRITABLE_PATH_READBACK'),
            ('ReadOnlyPaths',('/home','/root','/run','/run/user'),'LINUX_PREFLIGHT_READONLY_PARENT_READBACK')):
        for path in logical: _linux_preflight_path_v1(path)
        value=status.get(key)
        _preflight_require_v1(type(value) is str,label)
        tokens=value.split()
        _preflight_require_v1(len(tokens)==len(logical) and len(set(tokens))==len(logical)
            and set(tokens)=={'+'+path for path in logical},label)
    filter_text = status.get('SystemCallFilter','')
    _preflight_require_v1(type(syscall_filter) is frozenset and syscall_filter
        and filter_text.startswith('~') and set(filter_text[1:].split()) == syscall_filter,
        'LINUX_PREFLIGHT_SYSCALL_FILTER_READBACK')


class _LinuxPreflightScopeV1:
    """One newly allocated slice, one service and original held native witnesses."""
    _STATUS = ('InvocationID','ControlGroup','MainPID','ExecMainCode','ExecMainStatus','Result','ActiveState',
        'MemoryMax','MemorySwapMax','TasksMax','CPUQuotaPerSecUSec','CPUQuotaPeriodUSec','DynamicUser',
        'NoNewPrivileges','PrivateDevices','PrivateNetwork','PrivateIPC','ProtectSystem','ProtectHome','RuntimeDirectoryMode')
    _STATUS = tuple(dict.fromkeys((*_STATUS,*_LINUX_PREFLIGHT_SERVICE_READBACK_V1,
        'RootDirectory','WorkingDirectory','RuntimeDirectory','Slice','InaccessiblePaths','ReadWritePaths','ReadOnlyPaths','SystemCallFilter',
        'StopWhenUnneeded')))
    def __init__(self,*,name,query,control,runtime,private_root,spool,repository,installation,interpreter,
            source,header,blobs,vectors,grants,event,environment):
        self.name,self.query = name,query
        self.control,self.runtime,self.private_root,self.spool = map(Path,(control,runtime,private_root,spool))
        self.repository,self.installation,self.interpreter = repository,installation,interpreter
        self.source,self.header,self.blobs,self.vectors,self.grants = source,header,blobs,vectors,grants
        self.environment,self.event = environment,event
        self.execution_deadline_ns,self.settlement_deadline_ns = grants['execution_deadline_ns'],grants['settlement_deadline_ns']
        self.history,self.slice_files = [],{}
        self.slice_fd,self.root_fd,self.process = None,None,None
        self.slice_created,self.service_created,self.terminated,self.settled = False,False,False,False
        self.invocation = None
        self.attempt_utc=None
        self.startup_error=None
        self.launcher_receipt=None
        self.failure_recovery_started=False
        self.failure_recovery_error=None
        self.closeout_attempts=self.closeout_slice_observations=0
        self.owned_unit_status=None
        self.stop_attempted=self.stop_acknowledged=self.slice_stop_attempted=False
        self.installation_source=self.control/'installation'
        self.runtime_backing=self.runtime/'payload'
        self.runtime_identity=self.runtime_underlay=self.runtime_mounted_identity=self.runtime_mount=None
        self.runtime_fd=self.runtime_envelope_fd=None
        self.runtime_envelope_attempted=False
        self.runtime_mount_attempted=False
        self.runtime_children={}
    _FAILED_STATUS=('Id','LoadState','ActiveState','SubState','Result','MainPID','ControlPID',
        'ExecMainPID','ExecMainCode','ExecMainStatus','InvocationID','ControlGroup','Slice','Job','Type','Restart','Transient')

    def _runtime_call(self,operation,*args,settling=False,**kwargs):
        self.query.check(settling=settling)
        return operation(*args,**kwargs)

    def _runtime_acl(self,fd,*,settling=False):
        native=_LinuxSourceNativeV2()
        try:
            acl=native.acl(fd,attempt=lambda name:self.query.check(settling=settling),delivered=lambda count:None)
            _preflight_require_v1(acl==(None,None),'LINUX_PREFLIGHT_RUNTIME_ACL')
        finally:
            self.query.record('runtime-acl',str(fd),_preflight_canonical_v1(native.last_acl))

    def _runtime_directory(self,path,identity,uid,gid,mode,*,settling=False):
        info=self._runtime_call(os.lstat,path,settling=settling)
        _preflight_require_v1(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode)
            and (info.st_dev,info.st_ino)==identity and (info.st_uid,info.st_gid)==(uid,gid)
            and stat.S_IMODE(info.st_mode)==mode,'LINUX_PREFLIGHT_RUNTIME_DIRECTORY:'+str(path))
        return info

    def prepare_runtime(self):
        _preflight_require_v1(str(self.runtime)=='/run/'+self.name and self.runtime_identity is None,
            'LINUX_PREFLIGHT_RUNTIME_ENVELOPE_OPERAND')
        self.runtime_envelope_attempted=True
        self.history.append(dict(runtime_envelope_create_attempt=str(self.runtime)))
        self._runtime_call(os.mkdir,self.runtime,0o700)
        info=self._runtime_call(os.lstat,self.runtime)
        self.runtime_identity=(info.st_dev,info.st_ino)
        self._runtime_directory(self.runtime,self.runtime_identity,0,0,0o700)
        self.runtime_envelope_fd=self._runtime_call(os.open,self.runtime,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        self._runtime_acl(self.runtime_envelope_fd)
        self._runtime_call(os.mkdir,self.runtime_backing,0o700)
        info=self._runtime_call(os.lstat,self.runtime_backing)
        self.runtime_underlay=(info.st_dev,info.st_ino)
        self._runtime_directory(self.runtime_backing,self.runtime_underlay,0,0,0o700)
        self.runtime_mount_attempted=True
        self.history.append(dict(runtime_mount_attempt=str(self.runtime_backing),underlay=self.runtime_underlay,
            envelope=self.runtime_identity))
        self.query.command(('/usr/bin/mount','-t','tmpfs','-o','size=1073741824,noexec,nodev,nosuid,mode=0700',
            'qtt-runtime',str(self.runtime_backing)))
        mounts=_linux_preflight_mounts_v1(self.query.read('/proc/self/mountinfo'))
        selected=[m for m in mounts if m['path']==str(self.runtime_backing)]
        _preflight_require_v1(len(selected)==1 and selected[0]['fs']=='tmpfs' and selected[0]['root']=='/'
            and {'noexec','nodev','nosuid','rw'}<=selected[0]['options']
            and ('size=1048576k' in selected[0]['super_options'] or 'size=1073741824' in selected[0]['super_options']),
            'LINUX_PREFLIGHT_RUNTIME_BACKING_MOUNT')
        self.runtime_mount=selected[0]
        self.runtime_fd=self._runtime_call(os.open,self.runtime_backing,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        info=self._runtime_call(os.fstat,self.runtime_fd)
        self.runtime_mounted_identity=(info.st_dev,info.st_ino)
        _preflight_require_v1(str(os.major(info.st_dev))+':'+str(os.minor(info.st_dev))==self.runtime_mount['device'],
            'LINUX_PREFLIGHT_RUNTIME_MOUNT_DEVICE')
        self._runtime_directory(self.runtime_backing,self.runtime_mounted_identity,0,0,0o700)
        self._runtime_acl(self.runtime_fd)
        for name in ('tmp','var-tmp'):
            self._runtime_call(os.mkdir,name,0o1777,dir_fd=self.runtime_fd)
            self._runtime_call(os.chmod,name,0o1777,dir_fd=self.runtime_fd,follow_symlinks=False)
            info=self._runtime_call(os.stat,name,dir_fd=self.runtime_fd,follow_symlinks=False)
            self.runtime_children[name]=(info.st_dev,info.st_ino)
            self._runtime_directory(self.runtime_backing/name,self.runtime_children[name],0,0,0o1777)
        self.history.append(dict(runtime_prepared=dict(envelope=self.runtime_identity,underlay=self.runtime_underlay,
            mounted=self.runtime_mounted_identity,mount={k:sorted(v) if isinstance(v,frozenset) else v
                for k,v in self.runtime_mount.items()},children=self.runtime_children)))

    def prepare_view(self):
        # Create these views only beneath the newly owned private root. Existing
        # objects are validated; unexpected objects are never repaired in place.
        for logical,mode in (('/home',0o755),('/root',0o700),('/run',0o755),('/run/user',0o755)):
            self.query.check()  # reserve close before opening
            fd=self._runtime_call(os.open,self.private_root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
            try:
                storage=self._runtime_call(os.fstat,fd).st_dev
                for part in logical[1:].split('/'):
                    created=False
                    try:self._runtime_call(os.mkdir,part,mode=mode,dir_fd=fd);created=True
                    except FileExistsError:pass
                    self.query.check()  # next descriptor's close, without refund
                    new=self._runtime_call(os.open,part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd)
                    previous=fd;fd=new;os.close(previous)
                    if created:
                        self._runtime_call(os.fchown,fd,0,0);self._runtime_call(os.fchmod,fd,mode)
                    info=self._runtime_call(os.fstat,fd)
                    _preflight_require_v1(stat.S_ISDIR(info.st_mode) and info.st_dev==storage
                        and (info.st_uid,info.st_gid)==(0,0) and stat.S_IMODE(info.st_mode)==mode,
                        'LINUX_PREFLIGHT_PRIVATE_PARENT:'+logical)
                    self._runtime_acl(fd)
            finally:os.close(fd)
        for absolute in ('/usr','/lib','/lib64','/proc','/sys','/dev','/tmp','/var/tmp',self.repository,self.installation,
                str(self.runtime),str(self.spool),*(str(self.control/n) for n in ('declaration','binding','release'))):
            self._runtime_call((self.private_root/absolute.lstrip('/')).mkdir,parents=True,exist_ok=True,mode=0o755)
        etc=self.private_root/'etc'
        self._runtime_call(etc.mkdir,mode=0o755)
        for name,raw in (('passwd',b'root:x:0:0:root:/root:/usr/sbin/nologin\n'),('group',b'root:x:0:\n'),
                ('nsswitch.conf',b'passwd: files\ngroup: files\nhosts: files\n'),
                ('qtt-gitconfig',('[safe]\n\tdirectory = '+self.repository+'\n').encode('ascii'))):
            self._runtime_call(_atomic_write_bytes_v1,etc/name,raw,control_mode=0o444)

    def _runtime_live(self,process,cgroup):
        import select
        poll=select.poll();poll.register(self.process.pidfd,select.POLLIN)
        self.query.check()
        _preflight_require_v1(not poll.poll(0) and process==_linux_preflight_process_identity_v1(self.process.pid,self.query)
            and cgroup==_linux_preflight_cgroup_path_v1(self.process.pid,self.query),
            'LINUX_PREFLIGHT_RUNTIME_PROCESS_CHANGED')
        status=self.show(self.name+'.service')
        _preflight_require_v1(status['InvocationID']==self.invocation and status['MainPID']==str(process['pid'])
            and status['ControlGroup']==cgroup,'LINUX_PREFLIGHT_RUNTIME_INVOCATION_CHANGED')
        self._startup_manager()

    def handoff_runtime(self,process,cgroup,mounts):
        self._runtime_live(process,cgroup)
        credentials=_linux_preflight_status_v1(process['pid'],self.query,credentials=True)
        uid,gid=credentials['Uid'],credentials['Gid']
        self._runtime_directory(self.runtime,self.runtime_identity,0,0,0o700)
        self._runtime_acl(self.runtime_envelope_fd)
        self._runtime_directory(self.runtime_backing,self.runtime_mounted_identity,0,0,0o700)
        held=self._runtime_call(os.fstat,self.runtime_fd)
        _preflight_require_v1(stat.S_ISDIR(held.st_mode) and (held.st_uid,held.st_gid)==(0,0)
            and stat.S_IMODE(held.st_mode)==0o700 and (held.st_dev,held.st_ino)==self.runtime_mounted_identity,
            'LINUX_PREFLIGHT_RUNTIME_HELD_ROOT')
        self._runtime_acl(self.runtime_fd)
        effect=dict(runtime_handoff_attempt=dict(identity=self.runtime_mounted_identity,uid=uid,gid=gid),complete=False)
        self.history.append(effect)
        self._runtime_call(os.fchown,self.runtime_fd,uid,gid)
        self._runtime_call(os.fchmod,self.runtime_fd,0o700)
        handed=self._runtime_call(os.fstat,self.runtime_fd)
        _preflight_require_v1(stat.S_ISDIR(handed.st_mode) and (handed.st_uid,handed.st_gid)==(uid,gid)
            and stat.S_IMODE(handed.st_mode)==0o700 and (handed.st_dev,handed.st_ino)==self.runtime_mounted_identity,
            'LINUX_PREFLIGHT_RUNTIME_HANDOFF_READBACK')
        self._runtime_directory(self.runtime_backing,self.runtime_mounted_identity,uid,gid,0o700)
        self._runtime_acl(self.runtime_fd)
        self._runtime_directory(self.runtime,self.runtime_identity,0,0,0o700)
        for logical,identity,mode,owner in ((str(self.runtime),self.runtime_mounted_identity,0o700,(uid,gid)),
                ('/tmp',self.runtime_children['tmp'],0o1777,(0,0)),
                ('/var/tmp',self.runtime_children['var-tmp'],0o1777,(0,0))):
            view=self._runtime_call(os.stat,logical.lstrip('/'),dir_fd=self.root_fd,follow_symlinks=False)
            match=[m for m in mounts if m['path']==logical]
            _preflight_require_v1(stat.S_ISDIR(view.st_mode) and (view.st_dev,view.st_ino)==identity
                and (view.st_uid,view.st_gid)==owner and stat.S_IMODE(view.st_mode)==mode
                and len(match)==1 and match[0]['fs']=='tmpfs' and match[0]['device']==self.runtime_mount['device']
                and {'rw','noexec','nodev','nosuid'}<=match[0]['options'],
                'LINUX_PREFLIGHT_RUNTIME_VIEW_MAPPING:'+logical)
        self._runtime_live(process,cgroup)
        _preflight_require_v1(_linux_preflight_status_v1(process['pid'],self.query,credentials=True)==credentials,
            'LINUX_PREFLIGHT_RUNTIME_CREDENTIALS_CHANGED')
        effect['complete']=True
        return dict(runtime_identity=list(self.runtime_mounted_identity),runtime_uid=uid,runtime_gid=gid)

    def unmount_runtime(self):
        _preflight_require_v1(not self.service_created or self.settled,'LINUX_PREFLIGHT_RUNTIME_UNSETTLED')
        _preflight_require_v1(not self.runtime_envelope_attempted or self.runtime_identity is not None,
            'LINUX_PREFLIGHT_RUNTIME_ENVELOPE_CREATION_UNRESOLVED')
        if self.runtime_envelope_fd is not None:
            self._runtime_acl(self.runtime_envelope_fd,settling=True)
            fd=self.runtime_envelope_fd;self.runtime_envelope_fd=None
            self._runtime_call(os.close,fd,settling=True)
        if self.runtime_fd is not None:
            fd=self.runtime_fd;self.runtime_fd=None
            self._runtime_call(os.close,fd,settling=True)
        if self.runtime_mount_attempted:
            mounts=_linux_preflight_mounts_v1(self.query.read('/proc/self/mountinfo',settling=True))
            selected=[m for m in mounts if m['path']==str(self.runtime_backing)]
            if selected:
                _preflight_require_v1(len(selected)==1 and self.runtime_mount is not None
                    and selected[0]==self.runtime_mount,'LINUX_PREFLIGHT_RUNTIME_MOUNT_CHANGED')
                self.query.command(('/usr/bin/umount',str(self.runtime_backing)),settling=True)
            else:_preflight_require_v1(self.runtime_mount is None,'LINUX_PREFLIGHT_RUNTIME_MOUNT_LOST')
        if self.runtime_underlay is not None:
            self._runtime_directory(self.runtime_backing,self.runtime_underlay,0,0,0o700,settling=True)
        if self.runtime_identity is not None:
            self._runtime_directory(self.runtime,self.runtime_identity,0,0,0o700,settling=True)
        self.history.append(dict(runtime_unmounted=True,underlay=self.runtime_underlay,envelope=self.runtime_identity))

    def remove_runtime(self,evidence_root):
        if self.runtime_identity is not None:
            self._runtime_directory(self.runtime,self.runtime_identity,0,0,0o700,settling=True)
            self._runtime_directory(self.runtime_backing,self.runtime_underlay,0,0,0o700,settling=True)
            self._runtime_call(remove_exact_run_owned_process_tree,self.runtime,expected_run_root=self.runtime,
                repo_root=self.repository,evidence_root=evidence_root,settling=True)
            self.history.append(dict(runtime_envelope_removed=str(self.runtime)))

    @classmethod
    def runtime_fixture(cls,query,grants,*,repository,installation,interpreter):
        """One real short runtime roundtrip, before protecting the checkout."""
        parent=query.evidence_root.parent
        name=parent.name.removesuffix('control')+'1'
        control=parent/'runtime-roundtrip-control'
        query.check();control.mkdir(mode=0o700,exist_ok=False)
        identity=(control.stat().st_dev,control.stat().st_ino)
        root,spool=control/'root',query.evidence_root/'runtime-roundtrip-streams'
        for path,mode in ((root,0o755),(spool,0o700)):query.check();path.mkdir(mode=mode,exist_ok=False)
        for child in ('binding','release','declaration'):
            query.check();(control/child).mkdir(mode=0o555)
        _atomic_write_bytes_v1(control/'declaration/input.bin',b'QTT runtime engineering fixture only\n',control_mode=0o444)
        runtime=Path('/run')/name
        environment=_linux_preflight_environment_v1(repository=repository,installation=installation,
            runtime=str(runtime),control=str(control))
        limited={**grants,'execution_deadline_ns':min(grants['execution_deadline_ns'],time.monotonic_ns()+60*10**9)}
        scope=cls(name=name,query=query,control=control,runtime=runtime,private_root=root,spool=spool,
            repository=repository,installation=installation,interpreter=interpreter,source=None,header=None,
            blobs=None,vectors=(),grants=limited,event={},environment=environment)
        scope.installation_source=parent/'installation'
        result=dict(engineering_only=True,complete=False,settled=False,exported=False,unmounted=False,removed=False)
        query.runtime_fixture_result=result
        errors=[];receipt=None
        try:
            # Share the already reserved denied-start output tranche, without refund.
            remaining=query.startup_fixture_reservation-query.startup_fixture_bytes
            _preflight_require_v1(remaining>=2,'LINUX_PREFLIGHT_RUNTIME_FIXTURE_STREAM_ALLOWANCE')
            scope.prepare_runtime();scope.prepare_view()
            scope.expected_syscalls=_linux_preflight_syscalls_v1(query)
            scope.start_slice()
            scope.startup_deadline_ns=scope.execution_deadline_ns
            launch=_linux_preflight_service_argv_v1(name=name,private_root=str(root),runtime=str(runtime),
                control=str(control),spool=str(spool),repository=repository,installation=installation,
                installation_source=str(scope.installation_source),interpreter=interpreter,
                startup_deadline_ns=scope.startup_deadline_ns,environment=environment)
            program='''import json,os,sys,time
from pathlib import Path
sys.path.insert(0,os.getcwd())
from tools import validation_reliability as o
control=Path(os.environ['QTT_LINUX_PREFLIGHT_CONTROL'])
runtime=Path(os.environ['QTT_LINUX_PREFLIGHT_RUNTIME'])
deadline=int(sys.argv[1])
query=o._LinuxPreflightQueriesV1(evidence_root=runtime/'native-observations',deadline_ns=deadline)
binding,version,chain=o._linux_preflight_control_read_v1(control/'binding/native.json',deadline_ns=deadline,pending=True,query=query)
process=o._linux_preflight_process_identity_v1(os.getpid(),query)
o._preflight_require_v1(o._json_compatible(process)==binding['process'] and binding['runtime']==str(runtime)
    and o._linux_preflight_cgroup_path_v1(os.getpid(),query)==binding['service_cgroup'],'RUNTIME_FIXTURE_PROCESS')
o._linux_preflight_mount_containment_v1(pid=os.getpid(),process=process,runtime=str(runtime),query=query,
    mappings=binding.get('host_service_mappings'))
credentials=o._LinuxPreflightHostLeaseV1.check_runtime(binding,runtime,query)
marker=b'QTT runtime roundtrip engineering only\\n'
rows=[]
for parent in (runtime,Path('/tmp'),Path('/var/tmp')):
    query.check();path=parent/'runtime-marker'
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    try:
        query.check();o._preflight_require_v1(os.write(fd,marker)==len(marker),'RUNTIME_FIXTURE_WRITE')
        query.check();os.fsync(fd)
    finally:os.close(fd)
    raw=query.read(path)
    o._preflight_require_v1(raw==marker,'RUNTIME_FIXTURE_BYTES')
    rows.append(dict(path=str(path),bytes=len(raw),hex=raw.hex()))
o._LinuxPreflightHostLeaseV1.check_runtime(binding,runtime,query)
o._linux_preflight_mount_containment_v1(pid=os.getpid(),process=process,runtime=str(runtime),query=query,
    mappings=binding.get('host_service_mappings'))
o._preflight_require_v1(o._scan_same_api_version((control/'binding/native.json').lstat())==version
    and o._preflight_chain_v1(control/'binding')==chain,'RUNTIME_FIXTURE_BINDING_CHANGED')
probe=dict(name=binding['name'],pid=os.getpid(),start=process['start'],passed=True,engineering_only=True,
    runtime_identity=binding['runtime_identity'],uid=credentials['Uid'],gid=credentials['Gid'],markers=rows)
o.atomic_write_json(runtime/'probe.json',probe)
release,_,_=o._linux_preflight_control_read_v1(control/'release/release.json',deadline_ns=deadline,pending=True,query=query)
o._preflight_require_v1(release==dict(name=binding['name'],pid=os.getpid(),start=process['start'],invocation=binding['invocation']),
    'RUNTIME_FIXTURE_RELEASE')
query.check()
print(json.dumps(probe),flush=True)
'''
            # A literal programme; no archive/JSON expression is evaluated.
            scope.argv=(interpreter,'-I','-B','-X','utf8','-c',
                'exec(compile('+repr(program)+',"<qtt-runtime-roundtrip>","exec"))',str(scope.startup_deadline_ns))
            scope.launch_argv=launch[:launch.index('--')+1]+scope.argv
            token=_LINUX_PREFLIGHT_PROCESS_V1.set(scope)
            try:
                receipt=supervise_command(scope.argv,cwd=Path(repository),run_id=name,phase='fast-preflight-native-service',
                    command_index=1,evidence_root=spool,environment=environment,timeout_seconds=60,
                    execution_deadline_ns=scope.execution_deadline_ns,output_limits=dict(stdout_bytes=remaining//2,
                        stderr_bytes=remaining//2,combined_output_bytes=2*(remaining//2)),output_observation={},
                    mirror_stdout=False,mirror_stderr=False)
            finally:_LINUX_PREFLIGHT_PROCESS_V1.reset(token)
            _preflight_require_v1(scope.settled and scope.startup_error is None and receipt.native_exit_code==0
                and receipt.failure_class is None and not _command_requires_process_retention_v1(receipt),
                'LINUX_PREFLIGHT_RUNTIME_FIXTURE_NATIVE_FAILURE')
        except BaseException as exc:
            errors.append(exc)
            if scope.service_created and not scope.settled:
                try:
                    if scope.startup_error is not None:scope.recover_failed_start()
                    else:
                        if not scope.terminated:scope.terminate(10)
                        scope.finish()
                except BaseException as error:errors.append(error)
        result['settled']=not scope.service_created or scope.settled
        try:
            delivered=sum((spool/('command-1.'+stream+'.bin')).stat().st_size for stream in ('stdout','stderr')
                if (spool/('command-1.'+stream+'.bin')).exists())
            query.startup_fixture_bytes+=delivered;query.retained+=delivered
            _preflight_require_v1(query.startup_fixture_bytes<=query.startup_fixture_reservation,
                'LINUX_PREFLIGHT_RUNTIME_FIXTURE_OUTPUT')
            if result['settled']:
                destination=query.evidence_root/'runtime-roundtrip-export'
                query.check(settling=True);destination.mkdir(mode=0o700)
                exported=[]
                for relative in ('runtime-marker','tmp/runtime-marker','var-tmp/runtime-marker','probe.json'):
                    path=scope.runtime_backing/relative
                    if path.exists():
                        raw=query.read(path,settling=True)
                        if relative.endswith('runtime-marker'):
                            _preflight_require_v1(raw==b'QTT runtime roundtrip engineering only\n',
                                'LINUX_PREFLIGHT_RUNTIME_FIXTURE_RETAINED_BYTES')
                        _atomic_write_bytes_v1(destination/relative,raw)
                        _preflight_require_v1((destination/relative).read_bytes()==raw,'LINUX_PREFLIGHT_RUNTIME_FIXTURE_EXPORT')
                        exported.append(relative)
                native=scope.runtime_backing/'native-observations'
                if native.exists():
                    for path in sorted(native.iterdir()):
                        raw=query.read(path,settling=True)
                        _atomic_write_bytes_v1(destination/'native-observations'/path.name,raw)
                        _preflight_require_v1((destination/'native-observations'/path.name).read_bytes()==raw,
                            'LINUX_PREFLIGHT_RUNTIME_FIXTURE_QUERY_EXPORT')
                result.update(exported=True,retained_files=exported)
                if not errors:
                    _preflight_require_v1(len(exported)==4,'LINUX_PREFLIGHT_RUNTIME_FIXTURE_MISSING_MARKERS')
                with query.owned_resource_phase():
                    scope.close_owned_units();scope.unmount_runtime();result['unmounted']=True
                    scope.remove_runtime(query.evidence_root)
                    info=control.lstat()
                    _preflight_require_v1(stat.S_ISDIR(info.st_mode) and (info.st_dev,info.st_ino)==identity,
                        'LINUX_PREFLIGHT_RUNTIME_FIXTURE_CONTROL_CHANGED')
                    remove_exact_run_owned_process_tree(control,expected_run_root=control,
                        repo_root=repository,evidence_root=query.evidence_root)
                    result['removed']=True
        except BaseException as exc:errors.append(exc)
        result.update(complete=not errors,history=scope.history,failures=[repr(e) for e in errors],
            receipt=None if receipt is None else _json_compatible(receipt))
        _atomic_write_bytes_v1(query.evidence_root/'runtime-roundtrip-result.json',_preflight_canonical_v1(result))
        _scan_raise_errors(errors)
        return result

    def _startup_status(self):
        record,raw,error=self.query.startup_diagnostic(self,'status')
        result={}
        try:
            for line in raw.decode('utf-8','strict').splitlines():
                key,sep,value=line.partition('=')
                _preflight_require_v1(sep and key in self._FAILED_STATUS and key not in result,
                    'LINUX_PREFLIGHT_FAILED_START_STATUS_SHAPE')
                result[key]=value
        finally:
            record.update(raw_fields=dict(result),missing_fields=[k for k in self._FAILED_STATUS if k not in result])
        _preflight_require_v1(record['complete'] and record['command_settled'] and record['receipt'] is not None
            and not record['receipt']['timeout_state']=='TRIGGERED',
            'LINUX_PREFLIGHT_FAILED_START_STATUS_UNAVAILABLE')
        if result.get('Id')==self.name+'.service' and result.get('LoadState')=='not-found':
            _preflight_require_v1(record['receipt']['native_exit_code'] in (0,4)
                and self.owned_unit_status is not None and self.stop_acknowledged
                and result.get('ActiveState')=='inactive' and result.get('Job') in ('','0')
                and 'Job' in result,'LINUX_PREFLIGHT_FAILED_START_ABSENCE_UNOWNED')
            self.history.append(dict(authentic_absence_after_stop=dict(result)))
            return result
        _preflight_require_v1(record['success'] and not record['missing_fields'],
            'LINUX_PREFLIGHT_FAILED_START_STATUS_INCOMPLETE')
        _preflight_require_v1(result['Id']==self.name+'.service' and result['LoadState']=='loaded'
            and result['Slice']==self.name+'.slice' and result['Type']=='exec'
            and result['Restart']=='no' and result['Transient']=='yes'
            and re.fullmatch(r'[0-9a-f]{32}',result['InvocationID']) is not None,
            'LINUX_PREFLIGHT_FAILED_START_UNIT_OWNERSHIP')
        _preflight_require_v1(result['ControlGroup'] in ('',self.slice_cgroup+'/'+self.name+'.service'),
            'LINUX_PREFLIGHT_FAILED_START_CONTROL_GROUP')
        if self.invocation is not None:
            _preflight_require_v1(result['InvocationID']==self.invocation,
                'LINUX_PREFLIGHT_FAILED_START_INVOCATION')
        else:self.invocation=result['InvocationID']
        self.owned_unit_status=dict(result)
        return result

    def _startup_terminal(self,status):
        if status.get('LoadState')=='not-found':return self.stop_acknowledged
        # systemctl v255 renders the native (uo) Job id 0 as an explicit Job=.
        # A missing field or a completely blank response is never zero evidence.
        return (status['ActiveState'] in ('failed','inactive') and status['Job'] in ('','0')
            and status['MainPID']=='0' and status['ControlPID']=='0')

    def _startup_manager(self):
        _preflight_require_v1(self.query.read('/proc/sys/kernel/random/boot_id',settling=True)
            .decode('ascii','strict').strip()==self.boot_id
            and _linux_preflight_process_identity_v1(1,self.query,settling=True)==self.manager_identity,
            'LINUX_PREFLIGHT_FAILED_START_MANAGER_CHANGED')

    def _startup_pidfd_terminal(self):
        if self.process.pidfd is None:return True
        import select
        poll=select.poll();poll.register(self.process.pidfd,select.POLLIN)
        result=poll.poll(0)
        self.history.append(dict(failed_start_pidfd_observation=result,pid=self.process.pid))
        return bool(result) and all(fd==self.process.pidfd and flags & select.POLLIN
            and not flags & (select.POLLERR|select.POLLNVAL) for fd,flags in result)

    def recover_failed_start(self):
        """Resource settlement only; never manufacture a process PID or exit."""
        if self.failure_recovery_started:
            if self.settled:return True
            raise self.failure_recovery_error or RuntimeError('LINUX_PREFLIGHT_FAILED_START_UNRESOLVED')
        self.failure_recovery_started=True
        try:
            _preflight_require_v1(self.startup_error is not None and self.service_created and self.process is not None
                and self.launcher_receipt is not None and not _command_requires_process_retention_v1(self.launcher_receipt),
                'LINUX_PREFLIGHT_FAILED_START_LAUNCHER_UNSETTLED')
            with self.query.owned_resource_phase():
                self._startup_manager()
                status_error=None;status=None
                try:status=self._startup_status()
                except BaseException as exc:status_error=exc
                # Diagnostics precede any stop; journal failure remains secondary.
                try:self.query.startup_diagnostic(self,'journal')
                except BaseException as exc:self.history.append(dict(startup_journal_error=repr(exc)))
                if status_error is not None:raise status_error
                if not self._startup_terminal(status):
                    stop,_,_=self.query.startup_diagnostic(self,'stop')
                    _preflight_require_v1(stop['success'],'LINUX_PREFLIGHT_FAILED_START_STOP_UNACKNOWLEDGED')
                    self.stop_acknowledged=True
                    status=self._startup_status()
                _preflight_require_v1(self._startup_terminal(status),
                    'LINUX_PREFLIGHT_FAILED_START_UNIT_NOT_TERMINAL')
                self._startup_manager()
                _preflight_require_v1(self._startup_pidfd_terminal(),
                    'LINUX_PREFLIGHT_FAILED_START_BOUND_PIDFD_NONTERMINAL')
                _preflight_require_v1(self.closeout_slice_observations<2,
                    'LINUX_PREFLIGHT_FAILED_START_SLICE_OBSERVATION_LIMIT')
                self.closeout_slice_observations+=1
                _preflight_require_v1(self.slice_observation(),'LINUX_PREFLIGHT_FAILED_START_SLICE_POPULATED')
            self.settled=True
            self.history.append(dict(failed_start_resource_settled=True,application_success=False,
                primary_error=repr(self.startup_error),terminal_status=status,
                closeout_commands=self.closeout_attempts,held_slice_observations=self.closeout_slice_observations))
            return True
        except BaseException as exc:
            self.failure_recovery_error=exc
            self.history.append(dict(failed_start_resource_settled=False,error=repr(exc),
                primary_error=repr(self.startup_error)))
            raise

    def close_owned_units(self):
        """Original exact units and held descriptors; charged to shared 40s."""
        _preflight_require_v1(not self.service_created or self.settled,
            'LINUX_PREFLIGHT_UNIT_RELEASE_BEFORE_SETTLEMENT')
        with self.query.owned_resource_phase():
            if self.service_created and not self.stop_acknowledged:
                _preflight_require_v1(not self.stop_attempted,'LINUX_PREFLIGHT_STOP_ALREADY_ATTEMPTED')
                self.stop_attempted=True
                self.query.command(('/usr/bin/systemctl','stop',self.name+'.service'),settling=True)
                self.stop_acknowledged=True
            if self.slice_created:
                _preflight_require_v1(not self.slice_stop_attempted,'LINUX_PREFLIGHT_SLICE_STOP_ALREADY_ATTEMPTED')
                self.slice_stop_attempted=True
                self.query.command(('/usr/bin/systemctl','stop',self.name+'.slice'),settling=True)
            failures=[]
            for key,(descriptor,identity) in tuple(self.slice_files.items()):
                del self.slice_files[key]
                try:os.close(descriptor)
                except BaseException as exc:failures.append(exc)
            for name in ('root_fd','slice_fd'):
                descriptor=getattr(self,name)
                if descriptor is not None:
                    setattr(self,name,None)
                    try:os.close(descriptor)
                    except BaseException as exc:failures.append(exc)
            if self.process is not None and self.process.pidfd is not None:
                descriptor=self.process.pidfd;self.process.pidfd=None
                try:os.close(descriptor)
                except BaseException as exc:failures.append(exc)
            if getattr(self.query,'containment_retained_descriptors',()):
                failures.append(ValidationReliabilityError('ENGVR_PREPUBLICATION_CUSTODY_FAILED',
                    'LINUX_PREFLIGHT_CONTAINMENT_DESCRIPTOR_CUSTODY_UNRESOLVED'))
            self.history.append(dict(owned_unit_handles_closed=not failures,errors=[repr(e) for e in failures]))
            _scan_raise_errors(failures)

    @classmethod
    def denied_start_fixture(cls,source,query,grants):
        """The third tiny seal's single actual intentionally absent executable."""
        control=query.evidence_root.parent
        root=control/'startup-denial-root'
        root.mkdir(mode=0o755,exist_ok=False)
        root_info=root.lstat()
        _preflight_require_v1(stat.S_ISDIR(root_info.st_mode) and not stat.S_ISLNK(root_info.st_mode),
            'LINUX_PREFLIGHT_DENIED_ROOT_TYPE')
        root_identity=(root_info.st_dev,root_info.st_ino)
        spool=query.evidence_root/'startup-denial-streams'
        spool.mkdir(mode=0o700,exist_ok=False)
        name=source.run_id.replace('-recovery-3','')+'0'
        missing='/qtt-intentionally-absent-fixture-executable'
        _preflight_require_v1(not (root/missing.lstrip('/')).exists(),'LINUX_PREFLIGHT_DENIED_EXECUTABLE_EXISTS')
        limited={**grants,'execution_deadline_ns':min(grants['execution_deadline_ns'],time.monotonic_ns()+60*10**9)}
        scope=cls(name=name,query=query,control=control,runtime=root,private_root=root,spool=spool,
            repository=str(source.root),installation='',interpreter=missing,source=source,header=None,
            blobs=None,vectors=None,grants=limited,event={},environment=dict(PATH='/usr/bin',LANG='C.UTF-8',LC_ALL='C.UTF-8'))
        result=dict(intentional_denial=True,application_launched=False,settled=False,removed=False,root=str(root))
        source.denied_start_result=result
        try:
            _preflight_require_v1(query.startup_fixture_reservation==0 and
                query.startup_output_bytes+2097152<=query.startup_output_limit,
                'LINUX_PREFLIGHT_DENIED_STREAM_RESERVATION')
            query.startup_fixture_reservation=2097152
            scope.start_slice()
            scope.argv=(missing,)
            scope.launch_argv=('/usr/bin/systemd-run','--system','--no-ask-password','--expand-environment=no',
                '--unit='+name+'.service','--slice='+name+'.slice',
                *('--property='+k+'='+v for k,v in _LINUX_PREFLIGHT_PROPERTIES_V1),
                '--property=RootDirectory='+str(root),'--property=WorkingDirectory=/',
                '--property=StandardInput=null','--property=StandardOutput=append:'+str(spool/'command-1.stdout.bin'),
                '--property=StandardError=append:'+str(spool/'command-1.stderr.bin'),'--',missing)
            token=_LINUX_PREFLIGHT_PROCESS_V1.set(scope)
            try:
                receipt=supervise_command(scope.argv,cwd=source.root,run_id=name,phase='fast-preflight-native-service',
                    command_index=1,evidence_root=spool,environment=scope.environment,timeout_seconds=60,
                    execution_deadline_ns=scope.execution_deadline_ns,output_limits=dict(stdout_bytes=1048576,
                        stderr_bytes=1048576,combined_output_bytes=2097152),output_observation={},mirror_stdout=False,mirror_stderr=False)
            finally:_LINUX_PREFLIGHT_PROCESS_V1.reset(token)
            delivered=sum((spool/('command-1.'+stream+'.bin')).stat().st_size for stream in ('stdout','stderr'))
            query.startup_fixture_bytes+=delivered
            query.retained+=delivered
            _preflight_require_v1(query.startup_fixture_bytes<=query.startup_fixture_reservation,
                'LINUX_PREFLIGHT_DENIED_STREAM_OUTPUT')
            result.update(receipt=_json_compatible(receipt),settled=scope.settled)
            _preflight_require_v1(scope.startup_error is not None and scope.settled
                and scope.launcher_receipt is not None and scope.launcher_receipt.native_exit_code!=0
                and receipt.native_exit_code is None and receipt.pid is None
                and receipt.failure_class=='ENGVR_PROCESS_START_FAILED',
                'LINUX_PREFLIGHT_DENIED_START_NOT_QUALIFIED')
            scope.close_owned_units()
            with query.owned_resource_phase():
                root_info=root.lstat()
                _preflight_require_v1(stat.S_ISDIR(root_info.st_mode) and not stat.S_ISLNK(root_info.st_mode)
                    and (root_info.st_dev,root_info.st_ino)==root_identity,
                    'LINUX_PREFLIGHT_DENIED_ROOT_CHANGED')
                # Namespace preparation may create manager-owned mountpoints in
                # this exact disposable private root. Existing removal owner only.
                remove_exact_run_owned_process_tree(root,expected_run_root=root,repo_root=source.root,
                    evidence_root=query.evidence_root)
                result['removed']=True
            return result
        except BaseException as exc:
            result['error']=repr(exc)
            raise
        finally:
            result.update(history=scope.history,settled=scope.settled,
                launcher_receipt=None if scope.launcher_receipt is None else _json_compatible(scope.launcher_receipt))
            _atomic_write_bytes_v1(query.evidence_root/'startup-denial-result.json',_preflight_canonical_v1(result))
    def show(self,unit,*,settling=False):
        _preflight_require_v1(unit in (self.name+'.slice',self.name+'.service'),'LINUX_PREFLIGHT_EXACT_UNIT')
        raw = self.query.command(('/usr/bin/systemctl','show','--no-pager','--all',
            '--property='+','.join(self._STATUS),unit),settling=settling)
        result = {}
        for line in raw.decode('utf-8','strict').splitlines():
            key,sep,value = line.partition('=')
            _preflight_require_v1(sep and key in self._STATUS and key not in result,'LINUX_PREFLIGHT_UNIT_PROPERTY')
            result[key] = value
        required = self._STATUS[:8] if unit.endswith('.service') else ('InvocationID','ControlGroup','ActiveState')
        _preflight_require_v1(all(key in result for key in required),'LINUX_PREFLIGHT_UNIT_STATUS_INCOMPLETE')
        return result
    def start_slice(self):
        self.query.check()
        existing = self.query.command(('/usr/bin/systemctl','list-units','--all','--plain','--no-legend',
            self.name+'.slice',self.name+'.service'))
        _preflight_require_v1(not existing.strip(),'LINUX_PREFLIGHT_UNIT_COLLISION')
        values = tuple(v for row in _LINUX_PREFLIGHT_SLICE_PROPERTIES_V1 for v in row)
        self.slice_created = True  # A denied/ambiguous native return never erases the attempt.
        self.query.command(('/usr/bin/busctl','--system','--no-pager','call','org.freedesktop.systemd1',
            '/org/freedesktop/systemd1','org.freedesktop.systemd1.Manager','StartTransientUnit',
            'ssa(sv)a(sa(sv))',self.name+'.slice','fail',str(len(_LINUX_PREFLIGHT_SLICE_PROPERTIES_V1)),*values,'0'))
        self.slice_created = True
        status = self.show(self.name+'.slice')
        _preflight_require_v1(status['InvocationID'] and status['ControlGroup'] and status['ActiveState'] == 'active',
            'LINUX_PREFLIGHT_SLICE_NOT_ACTIVE')
        for key,wanted in dict(StopWhenUnneeded='no',MemoryAccounting='yes',MemoryMax='6442450944',
                MemorySwapMax='0',TasksAccounting='yes',TasksMax='64',CPUAccounting='yes',
                CPUQuotaPerSecUSec='2s',CPUQuotaPeriodUSec='100ms').items():
            _preflight_require_v1(status.get(key) == wanted,'LINUX_PREFLIGHT_SLICE_PROPERTY:'+key)
        self.slice_invocation,self.slice_cgroup = status['InvocationID'],status['ControlGroup']
        _linux_preflight_path_v1(self.slice_cgroup)
        own = _linux_preflight_process_identity_v1(os.getpid(),self.query)
        manager = _linux_preflight_process_identity_v1(1,self.query)
        self.manager_identity=manager
        self.boot_id=self.query.read('/proc/sys/kernel/random/boot_id').decode('ascii','strict').strip()
        _preflight_require_v1(own['namespaces']['cgroup'] == manager['namespaces']['cgroup']
            and own['namespaces']['pid'] == manager['namespaces']['pid'],
            'LINUX_PREFLIGHT_HOST_MANAGER_NAMESPACE')
        mount = [row for row in _linux_preflight_mounts_v1(self.query.read('/proc/self/mountinfo'))
            if row['path'] == '/sys/fs/cgroup' and row['fs'] == 'cgroup2' and row['root'] == '/']
        _preflight_require_v1(len(mount) == 1,'LINUX_PREFLIGHT_TRUE_CGROUP2_ROOT')
        root = Path('/sys/fs/cgroup')
        root_fd = os.open(root,os.O_PATH|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:
            root_info = os.fstat(root_fd)
            fdinfo = self.query.read('/proc/'+str(os.getpid())+'/fdinfo/'+str(root_fd))
            identifiers = [line.split(b':',1)[1].strip() for line in fdinfo.splitlines() if line.startswith(b'mnt_id:')]
            _preflight_require_v1(identifiers == [str(mount[0]['id']).encode('ascii')],
                'LINUX_PREFLIGHT_DESCRIPTOR_FILESYSTEM_ASSOCIATION')
            _preflight_require_v1(str(os.major(root_info.st_dev))+':'+str(os.minor(root_info.st_dev)) == mount[0]['device'],
                'LINUX_PREFLIGHT_CGROUP_MOUNT_IDENTITY')
            self.slice_path = root/self.slice_cgroup.lstrip('/')
            self.slice_fd = os.open(self.slice_path,os.O_PATH|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
            info = os.fstat(self.slice_fd)
            self.slice_identity = (info.st_dev,info.st_ino)
            current = self.slice_path
            for level in range(33):
                _preflight_require_v1(level < 32,'LINUX_PREFLIGHT_ANCESTOR_DEPTH')
                if current == root:
                    controllers = set(self.query.read(root/'cgroup.controllers').split())
                    enabled = set(self.query.read(root/'cgroup.subtree_control').split())
                    _preflight_require_v1({b'cpu',b'memory',b'pids'} <= controllers & enabled,
                        'LINUX_PREFLIGHT_ROOT_CONTROLLER_AVAILABILITY')
                    for key in ('memory.max','pids.max','cpu.max'):
                        _preflight_require_v1(not (root/key).exists(),'LINUX_PREFLIGHT_UNEXPECTED_ROOT_INTERFACE')
                    self.history.append(dict(verified_root=str(root),nonroot_limits='NOT_APPLICABLE',
                        mount=sorted((k,str(v)) for k,v in mount[0].items()),manager=manager))
                    break
                values = _linux_preflight_ancestor_values_v1(self.query.read(current/'memory.max'),
                    self.query.read(current/'pids.max'),self.query.read(current/'cpu.max'),owned=current == self.slice_path)
                _linux_preflight_project_chain_v1(root_fd,'/'+current.relative_to(root).as_posix(),self.query)
                controllers = set(self.query.read(current/'cgroup.controllers').split())
                enabled = set(self.query.read(current/'cgroup.subtree_control').split())
                _preflight_require_v1({b'cpu',b'memory',b'pids'} <= controllers
                    and (current == self.slice_path or {b'cpu',b'memory',b'pids'} <= enabled),
                    'LINUX_PREFLIGHT_ANCESTOR_CONTROLLER_ENABLEMENT')
                usage = {key:self.query.read(current/key).decode('ascii') for key in
                    ('memory.current','pids.current','cpu.stat','cgroup.events')}
                self.history.append(dict(ancestor=str(current),values=values,usage=usage))
                current = current.parent
            _preflight_require_v1(self.query.read(self.slice_path/'memory.swap.max') == b'0\n','LINUX_PREFLIGHT_SLICE_SWAP')
            for key in ('cgroup.events','memory.current','memory.peak','memory.events','pids.current','pids.events','cpu.stat'):
                fd = os.open(key,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=self.slice_fd)
                self.slice_files[key] = (fd,(os.fstat(fd).st_dev,os.fstat(fd).st_ino))
        finally: os.close(root_fd)
    def slice_observation(self):
        self.query.check(settling=True)
        info = os.fstat(self.slice_fd); now = self.slice_path.lstat()
        _preflight_require_v1((info.st_dev,info.st_ino) == (now.st_dev,now.st_ino) == self.slice_identity,
            'LINUX_PREFLIGHT_HELD_SLICE_UNAVAILABLE')
        result = {}
        for key,(fd,identity) in self.slice_files.items():
            self.query.check(settling=True)
            current = os.fstat(fd)
            _preflight_require_v1((current.st_dev,current.st_ino) == identity,'LINUX_PREFLIGHT_SLICE_FILE_CHANGED')
            os.lseek(fd,0,os.SEEK_SET)
            raw = os.read(fd,1048577)
            _preflight_require_v1(len(raw) <= 1048576,'LINUX_PREFLIGHT_SLICE_RESPONSE')
            result[key] = self.query.record('held-slice',key,raw).decode('ascii','strict')
        self.history.append(dict(slice_observation=result))
        events = dict(line.split() for line in result['cgroup.events'].splitlines())
        _preflight_require_v1(events.get('populated') in ('0','1'),'LINUX_PREFLIGHT_POPULATION_UNAVAILABLE')
        return events['populated'] == '0'
    def create(self,argv,cwd,environment):
        self.query.check()
        _preflight_require_v1(self.process is None and tuple(argv) == self.argv and str(cwd) == self.repository
            and environment == self.environment,'LINUX_PREFLIGHT_EXACT_SUPERVISOR_ADAPTER')
        self.process = _LinuxPreflightProcessV1(self)
        try:
            _preflight_require_v1(not self.service_created,'LINUX_PREFLIGHT_ONE_SHOT_SERVICE')
            self.service_created = True  # The native attempt may partially create it even if reporting fails.
            self.attempt_utc=datetime.now(UTC)
            self.query.last_command_receipt=None
            try:self.query.command(self.launch_argv)
            finally:
                observed=self.query.last_command_receipt
                if observed is not None and tuple(observed.argv)==self.launch_argv:
                    self.launcher_receipt=observed
                    self.history.append(dict(original_launch_receipt=_json_compatible(observed)))
            status = self.show(self.name+'.service')
            _preflight_require_v1(status['InvocationID'] and int(status['MainPID']) > 0,
                'LINUX_PREFLIGHT_MAIN_PROCESS_UNAVAILABLE')
            self.invocation = status['InvocationID']
            self.process.pid = int(status['MainPID'])
            self.process.pidfd = os.pidfd_open(self.process.pid,0)
            self._bind_and_release(status)
            return self.process
        except BaseException as exc:
            self.startup_error=exc
            self.history.append(dict(original_startup_error=repr(exc),bound_pid=self.process.pid,
                bound_pidfd=self.process.pidfd is not None))
            exc.owned_process = self.process
            raise
    def _check_device_masks(self,mounts):
        # Acquire every original operand once before deciding. Failed acquisitions
        # remain errors in the existing history, including failed startup evidence.
        fields=('st_mode','st_uid','st_gid','st_dev','st_ino')
        reference=dict(path='/run/systemd/inaccessible/dir',stat=None,error=None)
        rows=[]
        for path in ('/dev/shm','/dev/mqueue','/dev/hugepages'):
            selected=[{k:sorted(v) if isinstance(v,frozenset) else v for k,v in m.items()}
                for m in mounts if m['path']==path]
            row=dict(path=path,mounts=selected,stat=None,error=None)
            try:
                info=os.stat(path.lstrip('/'),dir_fd=self.root_fd,follow_symlinks=False)
                row['stat']={key:getattr(info,key) for key in fields}
            except BaseException as exc: row['error']=repr(exc)
            rows.append(row)
        try:
            info=Path(reference['path']).stat()
            reference['stat']={key:getattr(info,key) for key in fields}
        except BaseException as exc: reference['error']=repr(exc)
        self.history.append(dict(device_mask_observation=dict(reference=reference,targets=rows)))
        _preflight_require_v1(reference['error'] is None and reference['stat'] is not None,
            'LINUX_PREFLIGHT_DEVICE_MASK_REFERENCE')
        expected=reference['stat']
        for row in rows:
            info=row['stat'];selected=row['mounts']
            _preflight_require_v1(row['error'] is None and info is not None and len(selected)==1
                and 'ro' in selected[0]['options'] and stat.S_ISDIR(info['st_mode'])
                and stat.S_IMODE(info['st_mode'])==0 and info['st_uid']==0
                and (info['st_dev'],info['st_ino'])==(expected['st_dev'],expected['st_ino']),
                'LINUX_PREFLIGHT_DEVICE_MASK:'+row['path'])

    def _bind_and_release(self,status):
        import select
        pid = self.process.pid
        process = _linux_preflight_process_identity_v1(pid,self.query)
        controller = _linux_preflight_process_identity_v1(os.getpid(),self.query)
        _preflight_require_v1(process['namespaces']['ipc'] != controller['namespaces']['ipc']
            and process['namespaces']['net'] != controller['namespaces']['net']
            and process['namespaces']['mnt'] != controller['namespaces']['mnt'],
            'LINUX_PREFLIGHT_PRIVATE_NAMESPACES')
        _linux_preflight_unit_policy_v1(status,name=self.name,root=str(self.private_root),
            repository=self.repository,runtime=str(self.runtime),syscall_filter=self.expected_syscalls)
        cgroup = _linux_preflight_cgroup_path_v1(pid,self.query)
        _preflight_require_v1(cgroup == status['ControlGroup'] and cgroup.startswith(self.slice_cgroup+'/'),
            'LINUX_PREFLIGHT_SERVICE_SLICE_MEMBERSHIP')
        self.root_fd = os.open('/proc/'+str(pid)+'/root',os.O_PATH|os.O_DIRECTORY|os.O_CLOEXEC)
        root = os.fstat(self.root_fd); expected_root = self.private_root.stat()
        _preflight_require_v1((root.st_dev,root.st_ino) == (expected_root.st_dev,expected_root.st_ino),
            'LINUX_PREFLIGHT_ORIGINAL_PRIVATE_ROOT')
        mounts = _linux_preflight_mounts_v1(self.query.read('/proc/'+str(pid)+'/mountinfo'))
        mappings = {}
        for logical,source in ((self.repository,Path(self.repository)),(self.installation,self.installation_source),
                *((str(self.control/name),self.control/name) for name in ('declaration','binding','release'))):
            chain = _linux_preflight_project_chain_v1(self.root_fd,logical,self.query)
            view = os.stat(logical.lstrip('/'),dir_fd=self.root_fd,follow_symlinks=False)
            host = source.stat()
            _preflight_require_v1((view.st_dev,view.st_ino) == (host.st_dev,host.st_ino),
                'LINUX_PREFLIGHT_BIND_OBJECT_MAPPING:'+logical)
            selected = [m for m in mounts if m['path'] == logical]
            _preflight_require_v1(len(selected) == 1 and 'ro' in selected[0]['options'],
                'LINUX_PREFLIGHT_BIND_READONLY:'+logical)
            mappings[logical] = dict(chain=chain,identity=(view.st_dev,view.st_ino),mount={
                k:sorted(v) if isinstance(v,frozenset) else v for k,v in selected[0].items()})
        self._check_device_masks(mounts)
        self._runtime_live(process,cgroup)
        mappings.update(_linux_preflight_mount_containment_v1(pid=pid,process=process,runtime=str(self.runtime),
            query=self.query,root_fd=self.root_fd,mounts=mounts,private_root=self.private_root,history=self.history))
        self._runtime_live(process,cgroup)
        runtime_mounts = [m for m in mounts if m['path'] == str(self.runtime)]
        _preflight_require_v1(len(runtime_mounts) == 1,'LINUX_PREFLIGHT_RUNTIME_ASSOCIATION')
        runtime_binding=self.handoff_runtime(process,cgroup,mounts)
        declaration = self.control/'declaration/input.bin'
        projected_chain = _linux_preflight_project_chain_v1(self.root_fd,str(declaration.parent),self.query)
        info = os.stat(str(declaration).lstrip('/'),dir_fd=self.root_fd,follow_symlinks=False)
        _preflight_require_v1(_scan_same_api_version(info) == _scan_same_api_version(declaration.stat()),
            'LINUX_PREFLIGHT_DECLARATION_MAPPING')
        index = Path(self.repository)/'.git/index'
        seen_index = os.stat(str(index).lstrip('/'),dir_fd=self.root_fd,follow_symlinks=False)
        _preflight_require_v1((seen_index.st_dev,seen_index.st_ino) == (index.stat().st_dev,index.stat().st_ino),
            'LINUX_PREFLIGHT_ORIGINAL_INDEX_MAPPING')
        poll = select.poll(); poll.register(self.process.pidfd,select.POLLIN)
        _preflight_require_v1(not poll.poll(0) and process == _linux_preflight_process_identity_v1(pid,self.query),
            'LINUX_PREFLIGHT_PROJECTION_PROCESS_CHANGED')
        self.binding = dict(profile='QTT_PR298_LINUX_PREFLIGHT_V1',name=self.name,invocation=self.invocation,
            boot_id=self.query.read('/proc/sys/kernel/random/boot_id').decode('ascii').strip(),process=process,
            slice_cgroup=self.slice_cgroup,slice_identity=self.slice_identity,service_cgroup=cgroup,
            repository=self.repository,index=str(index),installation=self.installation,runtime=str(self.runtime),
            **runtime_binding,runtime_device=runtime_mounts[0]['device'],declaration=str(declaration),declaration_parent=str(declaration.parent),
            declaration_chain=projected_chain,declaration_version=_scan_same_api_version(info),grants=self.grants,
            startup_deadline_ns=self.startup_deadline_ns,vectors=self.vectors,environment=self.environment,
            identities=dict(repository=(Path(self.repository).stat().st_dev,Path(self.repository).stat().st_ino),
                index=(seen_index.st_dev,seen_index.st_ino)),host_service_mappings=mappings)
        if type(self.source) is _LinuxImmutableSourceSealV2:
            self.source.verify(protected=True)
            manifest=Path(self.source.descriptor['path'])
            projected=os.stat(str(manifest).lstrip('/'),dir_fd=self.root_fd,follow_symlinks=False)
            _preflight_require_v1(list(_scan_same_api_version(projected))==self.source.descriptor['physical_version']
                and manifest.read_bytes()==self.source.raw,'LINUX_V2_MANIFEST_NAMESPACE_BINDING')
            self.binding.update(native_basis=dict(self.source.descriptor),source_run_id=self.source.run_id)
            self.source.state='IN_USE'
        self._runtime_live(process,cgroup)
        raw = _preflight_canonical_v1(self.binding)
        _preflight_require_v1(len(raw) <= 1048576,'LINUX_PREFLIGHT_BINDING_RESPONSE_BOUND')
        _atomic_write_bytes_v1(self.control/'binding/native.json',raw,control_mode=0o444)
        self.history.append(dict(binding=self.binding))
        response_path = self.runtime_backing/'probe.json'
        response = None
        for attempt in range(600):
            self.query.check()
            _preflight_require_v1(time.monotonic_ns() < self.startup_deadline_ns and not poll.poll(0),
                'LINUX_PREFLIGHT_STARTUP_RESPONSE_DEADLINE')
            try: raw = self.query.read(response_path)
            except FileNotFoundError:
                time.sleep(0.1); continue
            response = json.loads(raw)
            break
        _preflight_require_v1(type(response) is dict and response.get('name') == self.name
            and response.get('pid') == pid and response.get('start') == process['start']
            and response.get('passed') is True,'LINUX_PREFLIGHT_STARTUP_PROBE_REJECTED:'+repr(response))
        self.history.append(dict(actual_probe=response))
        _atomic_write_bytes_v1(self.control/'release/release.json',_preflight_canonical_v1(
            dict(name=self.name,pid=pid,start=process['start'],invocation=self.invocation)),control_mode=0o444)
    def terminate(self,grace_seconds):
        if self.startup_error is not None:
            return 'OWNED_FAILED_START_RESOURCE_SETTLEMENT',self.recover_failed_start()
        _preflight_require_v1(not self.terminated,'LINUX_PREFLIGHT_TERMINATION_ALREADY_ATTEMPTED')
        self.terminated = True
        self.query.command(('/usr/bin/systemctl','kill','--kill-whom=all','--signal=KILL',self.name+'.service'),settling=True)
        until = min(self.settlement_deadline_ns,time.monotonic_ns()+int(grace_seconds*10**9))
        while time.monotonic_ns() < until:
            if self.process.poll() is not None and self.slice_observation():
                return 'OWNED_SYSTEMD_KILL;PIDFD_TERMINAL;HELD_SLICE_EMPTY',True
            time.sleep(0.1)
        return 'OWNED_SYSTEMD_KILL;SETTLEMENT_UNRESOLVED',False
    def finish(self):
        if self.startup_error is not None:return self.recover_failed_start()
        _preflight_require_v1(self.process is not None and self.process.poll() is not None
            and self.slice_observation(),'LINUX_PREFLIGHT_TERMINAL_CUSTODY_UNESTABLISHED')
        self.settled = True
        return True


def _linux_preflight_git_environment_v1(root, observation):
    """An exact sealed Git trust statement, conditional on original native custody."""
    control = os.environ.get('QTT_LINUX_PREFLIGHT_CONTROL')
    if control is None: return {}
    lease = _LINUX_PREFLIGHT_LEASE_V1.get()
    if type(lease) is _LinuxPreflightHostLeaseV1:
        lease.check_parent(root,lease.index)
        config = Path('/etc/qtt-gitconfig')
        before = config.lstat()
        _preflight_require_v1(before.st_uid == 0 and stat.S_IMODE(before.st_mode) == 0o444
            and before.st_nlink == 1 and lease.query.read(config) ==
                ('[safe]\n\tdirectory = '+str(root)+'\n').encode('ascii')
            and _scan_same_api_version(config.lstat()) == _scan_same_api_version(before),
            'LINUX_PREFLIGHT_PARENT_GIT_EXACT_CONFIG')
        return {'GIT_CONFIG_GLOBAL':str(config)}
    _preflight_require_v1(sys.platform == 'linux' and os.geteuid() != 0
        and type(observation) is _PreflightObservationV1 and observation.root == Path(root),
        'LINUX_PREFLIGHT_GIT_REQUIRES_ORIGINAL_CHILD_OBSERVATION')
    control = Path(_linux_preflight_path_v1(control))
    query = getattr(observation,'_linux_native_queries_v1',None)
    if query is None:
        query = _LinuxPreflightQueriesV1(evidence_root=observation.evidence_root,deadline_ns=observation.deadline_ns)
        query.observation = observation
        observation._linux_native_queries_v1 = query
        binding,_,_ = _linux_preflight_control_read_v1(control/'binding/native.json',deadline_ns=observation.deadline_ns,query=query)
        observation._linux_native_binding_v1 = binding
    binding = observation._linux_native_binding_v1
    _preflight_require_v1(binding['repository'] == str(root) and binding['profile'] == 'QTT_PR298_LINUX_PREFLIGHT_V1'
        and getattr(observation,'_linux_parent_pid_v1',None) == binding['process']['pid'] == os.getppid(),
        'LINUX_PREFLIGHT_GIT_ORIGINAL_PARENT')
    actual = _linux_preflight_process_identity_v1(os.getppid(),query)
    _preflight_require_v1(_json_compatible(actual) == binding['process']
        and _linux_preflight_cgroup_path_v1(os.getpid(),query) == binding['service_cgroup'],
        'LINUX_PREFLIGHT_GIT_KERNEL_ASSOCIATION')
    _linux_preflight_status_v1(os.getpid(),query)
    info = Path(root).lstat()
    _preflight_require_v1([info.st_dev,info.st_ino] == binding['identities']['repository']
        and info.st_uid == 0 and stat.S_IMODE(info.st_mode) & 0o222 == 0,
        'LINUX_PREFLIGHT_GIT_ORIGINAL_REPOSITORY')
    cfg = Path('/etc/qtt-gitconfig'); before = cfg.lstat()
    _preflight_require_v1(before.st_uid == 0 and stat.S_IMODE(before.st_mode) == 0o444 and before.st_nlink == 1,
        'LINUX_PREFLIGHT_GIT_CONFIG_PERMISSIONS')
    _preflight_require_v1(query.read(cfg) == ('[safe]\n\tdirectory = '+str(root)+'\n').encode('ascii')
        and _scan_same_api_version(cfg.lstat()) == _scan_same_api_version(before),'LINUX_PREFLIGHT_GIT_EXACT_CONFIG')
    return {'GIT_CONFIG_GLOBAL':str(cfg)}
