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
    stdout_byte_count: int
    stderr_byte_count: int
    stdout_required_markers: tuple[str, ...]
    stdout_marker_state: str
    stderr_was_nonempty: bool
    failure_class: str | None

    registered_argv: tuple[str, ...] = field(default=(), kw_only=True)
    removed_environment_keys: tuple[str, ...] = field(default=(), kw_only=True)
    fixed_environment_controls: tuple[tuple[str, str], ...] = field(default=(), kw_only=True)

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
        if self.stdout_byte_count < 0 or self.stderr_byte_count < 0:
            raise ValueError("output byte counts cannot be negative")
        if self.stderr_was_nonempty != (self.stderr_byte_count > 0):
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
    encoded = (
        json.dumps(_json_compatible(payload), indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    try:
        with temporary.open("xb") as stream:
            written = stream.write(encoded)
            if written != len(encoded):
                raise OSError(
                    "short atomic JSON write: "
                    f"expected={len(encoded)} written={written}"
                )
            stream.flush()
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
    scan_read_limits=None,
    scan_deadline_ns=None,
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
    return payload


def write_run_provenance(
    paths: ValidationRunPathsV1,
    probe: FilesystemProbeReceiptV1,
    *,
    phase: str,
    command_count: int,
    text_integrity_preflight_state: str = "NOT_RUN",
    rp5a_scan_profiles=None,
    scan_read_limits=None,
    scan_deadline_ns=None,
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
    scan_read_limits=None,
    scan_deadline_ns=None,
) -> None:
    """Reconcile retained run, command, stream, and cleanup evidence before PASS."""

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
        return False, True
    outcome["drained_byte_count"] = int(outcome.get("drained_byte_count", 0)) + len(chunk)
    overflow = remaining is not None and len(chunk) > remaining
    admitted = chunk if remaining is None else chunk[:remaining]
    if outcome.get("evidence_write_enabled", True) and admitted:
        try:
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
            progress = False
            for index, (pipe, stream, outcome) in enumerate(zip(pipes, streams, outcomes, strict=True)):
                if not pipe_terminal[index]:
                    consumed, eof = _consume_available_pipe(
                        pipe, stream, outcome=outcome, native_terminal=native_exit is not None)
                    progress = progress or consumed
                    pipe_terminal[index] = eof
                if any("evidence_error" in value for value in outcomes):
                    for value in outcomes:
                        value["evidence_write_enabled"] = False
                        value["mirror"] = None
                    failure_class = failure_class or "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED"
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
            if terminal_at is not None and now - terminal_at >= OUTPUT_DRAIN_COMPLETION_WAIT_SECONDS:
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
) -> CommandExecutionReceiptV1:
    """Launch one shell-free child and retain PID, output, and native exit custody."""

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
    process: subprocess.Popen[bytes] | None = None
    selected_argv: tuple[str, ...] | None = None
    selected_markers: tuple[str, ...] | None = None
    selected_environment: dict[str, str] | None = None
    receipt = None
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
            original_stdin = subprocess.DEVNULL
            if launch_input is not None:
                if type(launch_input) is not _ScanLaunchInput:
                    raise TypeError("original scan launch input required")
                original_stdin = launch_input._claim(
                    run_id=run_id, phase=phase, command_index=command_index,
                    argv=selected_argv, cwd=receipt_cwd)
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
            if process is not None:
                raise
            start_failure = type(exc).__name__
            failure_class = "ENGVR_PROCESS_START_FAILED"
            _close_prestart_evidence_stream(stdout_stream, stdout_outcome)
            _close_prestart_evidence_stream(stderr_stream, stderr_outcome)
        except BaseException as body:
            if process is not None:
                raise
            failures = [body]
            for stream, outcome in ((stdout_stream, stdout_outcome), (stderr_stream, stderr_outcome)):
                _close_prestart_evidence_stream(stream, outcome)
                if "evidence_error" in outcome:
                    failures.append(outcome["evidence_error"])
            _scan_raise_errors(failures)

        if process is not None:
            if launch_input is not None:
                try:
                    launch_input._attached(process)
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
            stdout_count = 0
        try:
            stderr_count = stderr_path.stat().st_size
        except OSError as exc:
            stderr_outcome.setdefault("evidence_error", exc)
            stderr_count = 0
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
            stderr_was_nonempty=stderr_count > 0,
            failure_class=failure_class,
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


def _read_scan_profile_for_run(
    repo_root: Path, *, command_index: int, inherited_run_id: str,
    inherited_evidence_root: Path, explicit_basetemp: Path,
    read_limits: _ScanRunReadLimits, deadline_ns: int,
    expected_phase=None, expected_command_count=None,
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


def _prepare_scan_launch(paths, *, phase, plan, profiles, read_limits, deadline_ns, launch_inputs=None):
    if type(paths) is not ValidationRunPathsV1 or type(plan) is not tuple or type(read_limits) is not _ScanRunReadLimits:
        raise TypeError("original scan launch operands required")
    _scan_deadline(deadline_ns)
    _scan_profile_projection(profiles)
    if len(profiles) > read_limits.profile_limit:
        raise ValueError("scan launch profile count exceeds read allowance")
    for index, planned in enumerate(plan, 1):
        if (planned.command_index != index or planned.run_id != paths.run_id
                or planned.phase != phase or planned.cwd != str(paths.repo_root)):
            raise ValueError("scan launch original plan differs")
    roots = []
    for index, profile in profiles.items():
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
    if set(inputs) - set(profiles):
        raise ValueError("launch input belongs to an unselected occurrence")
    for index, original_input in inputs.items():
        expected = _ScanLaunchIdentity(paths.run_id, phase, index, len(plan), plan[index - 1].argv, str(paths.repo_root))
        if type(original_input) is not _ScanLaunchInput or original_input.identity != expected:
            raise ValueError("original scan input differs from selected plan")
    return _ScanLaunch(paths, phase, plan, MappingProxyType(dict(profiles)), read_limits,
                       deadline_ns, os.getpid(), threading.get_ident(),
                       launch_inputs=MappingProxyType(inputs))


_SCAN_TRANSPORT_KEYS = (
    "QTT_SCAN_COMMAND_INDEX", "QTT_SCAN_PHASE", "QTT_SCAN_COMMAND_COUNT", "QTT_SCAN_DEADLINE_NS",
    "QTT_SCAN_BYTE_LIMIT", "QTT_SCAN_NODE_LIMIT", "QTT_SCAN_DEPTH_LIMIT", "QTT_SCAN_PROFILE_LIMIT",
)


def _scan_child_launch_environment(parent, *, launch, planned):
    if (type(launch) is not _ScanLaunch or launch.process_id != os.getpid()
            or launch.thread_id != threading.get_ident() or not any(planned is row for row in launch.plan)):
        raise ValueError("scan launch original owner/occurrence required")
    profile = launch.profiles.get(planned.command_index)
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


def _scan_read_forwarded_profile(repo_root, *, environment, explicit_basetemp):
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
        expected_phase=phase, expected_command_count=count)
    if str(result[0].process_root) != original.get(PROCESS_ROOT_ENV):
        raise ValueError("forwarded scan process root differs")
    _scan_deadline(min(deadline, result[1].deadline_ns))
    return result


class _ScanReservationLedger:
    def __init__(self, profile):
        if type(profile) is not _Rp5aScanProfile:
            raise TypeError("original scan profile required")
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
                or ledger.profile is not profile or ledger.invocations != 0 or ledger.state != "READY"):
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
    content: bytes
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


def _scan_candidate_rows(rows, *, limits, candidate_read_bytes):
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
        nodes += 7 + len(row.children) if type(row.children) is tuple else limits.node_limit + 1
        if nodes > limits.node_limit:
            raise ValueError("candidate member node allowance exceeded")
        _scan_candidate_path(row.path, root_allowed=row.kind == "DIRECTORY")
        if row.path in seen or (os.name == "nt" and row.path.casefold() in aliases):
            raise ValueError("duplicate candidate surface")
        if (row.kind not in {"FILE", "DIRECTORY", "ABSENT"} or type(row.mode) is not int
                or not 0 <= row.mode <= 0o7777 or type(row.content) is not bytes or type(row.children) is not tuple):
            raise ValueError("unsupported candidate kind/mode/content")
        if row.kind == "FILE":
            if row.children:
                raise ValueError("file candidate cannot contain directory members")
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
    return rows


class _ScanCandidateFence:
    def __init__(self, repo_root, rows, *, limits, candidate_read_bytes, deadline_ns):
        self.root = Path(repo_root)
        if not self.root.is_absolute() or ".." in self.root.parts:
            raise ValueError("original absolute candidate root required")
        self.rows = _scan_candidate_rows(rows, limits=limits, candidate_read_bytes=candidate_read_bytes)
        self.remaining = candidate_read_bytes
        self.deadline_ns = deadline_ns
        self.process_id = os.getpid()
        self.thread_id = threading.get_ident()
        self.held = False
        self.last_ns = _scan_deadline(deadline_ns)
        self.identities = {}
        _local_unlinked_path(self.root)

    def _clock(self):
        now = _scan_deadline(self.deadline_ns)
        if now < self.last_ns:
            raise ValueError("candidate monotonic clock regressed")
        self.last_ns = now

    def __call__(self):
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


@dataclass(frozen=True)
class _ScanHex:
    value: bytes


def _scan_launch_payload(identity, rows, *, limits, candidate_read_bytes):
    if (type(identity) is not _ScanLaunchIdentity or type(identity.run_id) is not str or not identity.run_id
            or type(identity.phase) is not str or not identity.phase
            or type(identity.command_index) is not int or type(identity.command_count) is not int
            or not 1 <= identity.command_index <= identity.command_count
            or type(identity.argv) is not tuple or not identity.argv
            or any(type(arg) is not str or not arg or "\0" in arg for arg in identity.argv)
            or type(identity.repo_root) is not str or not Path(identity.repo_root).is_absolute()):
        raise ValueError("invalid original scan launch identity")
    _scan_candidate_rows(rows, limits=limits, candidate_read_bytes=candidate_read_bytes)
    return MappingProxyType({
        "run_id": identity.run_id, "phase": identity.phase, "command_index": identity.command_index,
        "command_count": identity.command_count, "argv": identity.argv, "repo_root": identity.repo_root,
        "candidate_files": tuple((row.path, row.kind, row.mode, _ScanHex(row.content), row.children) for row in rows),
        "candidate_read_bytes": candidate_read_bytes,
    })


def _scan_launch_measure(payload, *, limits):
    size = nodes = 0

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

    def walk(value, depth):
        nonlocal size, nodes
        nodes += 1
        if nodes > limits.node_limit:
            raise ValueError("launch node allowance exceeded")
        if type(value) is str:
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
                    walk(item, depth + 1)
        else:
            raise TypeError("unsupported launch representation")
        if size > limits.byte_limit or size > 0xFFFFFFFF:
            raise ValueError("launch byte allowance exceeded")

    walk(payload, 1)
    if size <= 0:
        raise ValueError("empty launch payload")
    return size



def _scan_launch_parts(payload):
    def text(value):
        encoded = json.encoder.encode_basestring_ascii(value).encode("ascii")
        for offset in range(0, len(encoded), 64 * 1024):
            yield encoded[offset:offset + 64 * 1024]

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
            yield from _scan_launch_parts(item)
        yield b"]"
    elif type(payload) is MappingProxyType:
        yield b"{"
        for index, (key, item) in enumerate(payload.items()):
            if index:
                yield b","
            yield from text(key)
            yield b":"
            yield from _scan_launch_parts(item)
        yield b"}"
    else:
        raise TypeError("unsupported measured launch value")


def _read_scan_launch_fd(fd, *, limits, deadline_ns, expected_identity):
    if type(fd) is not int or type(limits) is not _ScanRunReadLimits:
        raise TypeError("original launch descriptor and limits required")
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
    if type(value) is not MappingProxyType or set(value) != fields:
        raise ValueError("invalid closed launch fields")
    identity = _ScanLaunchIdentity(*(value[key] for key in ("run_id", "phase", "command_index", "command_count", "argv", "repo_root")))
    if type(expected_identity) is not _ScanLaunchIdentity or identity != expected_identity:
        raise ValueError("launch differs from independent original expectation")
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
    _scan_launch_payload(identity, result, limits=limits, candidate_read_bytes=value["candidate_read_bytes"])
    _scan_deadline(deadline_ns)
    return identity, result, value["candidate_read_bytes"]


class _ScanLaunchInput:
    def __init__(self, identity, candidate_files, *, limits, candidate_read_bytes,
                 deadline_ns, scratch_root, scratch_bytes, parent_frame_reread_bytes, check_candidate):
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
        self.path = None
        self.reader = None
        self.writer = None
        self.writer_close_attempted = False
        self.reader_close_attempted = False
        self.process = None
        self.last_ns = _scan_deadline(deadline_ns)
        self.payload = _scan_launch_payload(identity, candidate_files, limits=limits,
                                           candidate_read_bytes=candidate_read_bytes)
        self.length = _scan_launch_measure(self.payload, limits=limits)
        self.extent = self.length + 4
        if (type(scratch_bytes) is not int or type(parent_frame_reread_bytes) is not int
                or scratch_bytes < self.extent or parent_frame_reread_bytes < 3 * self.extent):
            raise ValueError("original launch input allocation cannot cover its measured lifetime")

    def _check(self):
        if (os.getpid(), threading.get_ident()) != (self.process_id, self.thread_id):
            raise ValueError("foreign launch input owner")
        now = _scan_deadline(self.deadline_ns)
        if now < self.last_ns:
            raise ValueError("launch input clock regressed")
        self.last_ns = now
        _scan_candidate_fence(self.check_candidate)
        _local_unlinked_path(self.scratch_root)
        if not self.scratch_root.is_dir():
            raise ValueError("original input scratch directory unavailable")

    def _parts(self):
        yield self.length.to_bytes(4, "big")
        yield from _scan_launch_parts(self.payload)

    def _compare(self):
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

    def __enter__(self):
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
