"""Shared validation path, process, receipt, and text-integrity support.

This module deliberately has no command-line entry point.  The central validation
runner remains the sole owner of command planning and aggregate acceptance.
"""

from __future__ import annotations

import ast
from contextlib import ExitStack, contextmanager
from dataclasses import asdict, dataclass, is_dataclass, replace
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
        if not self.process_root_is_external_to_repo:
            raise ValueError("process_root must be external to the repository")
        if self.process_root == self.repo_root or _path_is_relative_to(
            self.process_root, self.repo_root
        ):
            raise ValueError("process_root must actually be external to the repository")
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


def _open_regular_worktree_descriptor(path: Path) -> int:
    flags = os.O_RDONLY | int(getattr(os, "O_BINARY", 0))
    if os.name != "nt":
        flags |= int(getattr(os, "O_NOFOLLOW", 0))
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


def _status_paths(repo_root: Path) -> tuple[str, ...]:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    raw = _git_bytes(
        repo_root,
        ("status", "--porcelain=v1", "-z", "--untracked-files=all"),
        environment=environment,
    )
    records = [record for record in raw.split(b"\0") if record]
    paths: list[str] = []
    skip_source = False
    for record in records:
        if skip_source:
            paths.append(normalize_repo_path(record.decode("utf-8", "surrogateescape")))
            skip_source = False
            continue
        if len(record) < 4:
            continue
        code = record[:2]
        paths.append(normalize_repo_path(record[3:].decode("utf-8", "surrogateescape")))
        skip_source = b"R" in code or b"C" in code
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
    records = [record for record in raw.split(b"\0") if record]
    result: dict[str, str] = {}
    skip_source = False
    previous_code = ""
    for record in records:
        if skip_source:
            path = normalize_repo_path(record.decode("utf-8", "surrogateescape"))
            result[path] = previous_code + ":SOURCE"
            skip_source = False
            continue
        if len(record) < 4:
            continue
        code = record[:2].decode("ascii", "replace")
        path = normalize_repo_path(record[3:].decode("utf-8", "surrogateescape"))
        result[path] = code
        previous_code = code
        skip_source = "R" in code or "C" in code
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
    if resolved == root or _path_is_relative_to(resolved, root):
        raise ValidationReliabilityError(
            "ENGVR_SHORT_PROCESS_ROOT_UNAVAILABLE",
            f"candidate is repository-local: {candidate}",
        )
    return resolved


def _safe_relative_projection(value: str) -> Path:
    normalized = normalize_repo_path(value)
    parts = [
        re.sub(r"[^A-Za-z0-9._-]", "_", part) or "_"
        for part in PurePosixPath(normalized).parts
        if part not in {"", ".", "..", "/"}
    ]
    return Path(*parts) if parts else Path("sentinel.bin")


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
    text = value.replace("\\", "/")
    if (
        not text
        or text.startswith(("/", "-"))
        or ":" in text
        or any(character.isspace() for character in text)
    ):
        return None
    path = PurePosixPath(text)
    if any(part in {"", ".", ".."} for part in path.parts):
        return None
    if not all(re.fullmatch(r"[A-Za-z0-9._-]+", part) for part in path.parts):
        return None
    return path.as_posix()


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
    if repo_root is not None:
        for source_path in _selected_pytest_source_files(
            repo_root,
            projected_relative_paths,
        ):
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
        if safe is not None and not safe.startswith(
            ("validation-output/", "pytest-basetemp/", "command-")
        ):
            fixture_suffixes.add(safe)

    test_component = max(
        test_components or {"test_validation_path_budget0"},
        key=lambda item: (len(item), item),
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
        safe = _safe_fixture_path_text(str(value))
        if safe is None:
            continue
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
    return max(candidates, key=lambda item: (len(str(item)), str(item)))


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
    for source, raw_candidate in _candidate_parents(
        explicit_process_root,
        environment=env,
        platform_name=selected_platform,
    ):
        process_root: Path | None = None
        process_root_owned = False
        try:
            parent = _validate_candidate_parent(raw_candidate, root)
            parent.mkdir(parents=True, exist_ok=True)
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
            evidence_root = parent / f"{selected_run_id}.evidence"
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
                process_root_is_external_to_repo=True,
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
                candidate_evidence_root = parent / f"{selected_run_id}.evidence"
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
) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": paths.run_id,
        "phase": phase,
        "command_count": command_count,
        "text_integrity_preflight_state": text_integrity_preflight_state,
        "paths": paths,
        "filesystem_probe": probe,
    }


def write_run_provenance(
    paths: ValidationRunPathsV1,
    probe: FilesystemProbeReceiptV1,
    *,
    phase: str,
    command_count: int,
    text_integrity_preflight_state: str = "NOT_RUN",
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


def attest_inherited_validation_run(
    repo_root: Path,
    *,
    inherited_run_id: str,
    inherited_evidence_root: Path,
    explicit_basetemp: Path,
) -> InheritedRunAttestation:
    """Prove inherited helper values name one active external outer run."""

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
    if _lexically_inside_or_equal(evidence, repository) or _path_is_relative_to(
        evidence.resolve(strict=True),
        repository.resolve(strict=True),
    ):
        raise _evidence_failure("inherited evidence root must be outside the repository")

    payload = _read_evidence_json(evidence, "run.json")
    if not isinstance(payload, dict):
        raise _evidence_failure("inherited run.json must contain an object")
    path_payload = payload.get("paths")
    probe_payload = payload.get("filesystem_probe")
    if not isinstance(path_payload, dict) or not isinstance(probe_payload, dict):
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
    if _lexically_inside_or_equal(process_root, repository) or _path_is_relative_to(
        process_root.resolve(strict=False),
        repository.resolve(strict=True),
    ):
        raise _evidence_failure("inherited process root is repository-local")
    if not _lexically_inside_or_equal(pytest_root, process_root):
        raise _evidence_failure("inherited pytest basetemp root is not run-scoped")
    if (
        path_payload.get("process_root_is_external_to_repo") is not True
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
    pipe: BinaryIO,
    destination: BinaryIO,
    *,
    outcome: dict[str, object],
    native_terminal: bool,
) -> tuple[bool, bool]:
    """Consume at most one bounded chunk; return (progress, end_of_stream)."""

    try:
        chunk = os.read(pipe.fileno(), 64 * 1024)
    except BlockingIOError:
        return False, False
    except OSError as exc:
        if exc.errno in {errno.EAGAIN, errno.EWOULDBLOCK}:
            return False, False
        if native_terminal and (
            exc.errno == errno.EPIPE or getattr(exc, "winerror", None) in {109, 232}
        ):
            return False, True
        outcome.setdefault("evidence_error", exc)
        return False, True
    if not chunk:
        return False, True
    outcome["drained_byte_count"] = int(
        outcome.get("drained_byte_count", 0)
    ) + len(chunk)
    if bool(outcome.get("evidence_write_enabled", True)):
        try:
            _write_evidence_chunk(destination, chunk)
        except BaseException as exc:
            outcome.setdefault("evidence_error", exc)
            outcome["evidence_write_enabled"] = False
    active_mirror = outcome.get("mirror")
    if active_mirror is not None:
        try:
            _mirror_bytes(chunk, active_mirror)
        except BaseException as exc:
            outcome.setdefault("mirror_error", type(exc).__name__)
            outcome["mirror"] = None
    return True, False


def _finalize_owned_output_resources(
    pipe: BinaryIO,
    destination: BinaryIO,
    *,
    outcome: dict[str, object],
) -> None:
    """Flush and close raw resources from their sole supervisor owner."""

    try:
        destination.flush()
        os.fsync(destination.fileno())
    except BaseException as exc:
        outcome.setdefault("evidence_error", exc)
    try:
        destination.close()
    except BaseException as exc:
        outcome.setdefault("evidence_error", exc)
    try:
        pipe.close()
    except (OSError, ValueError):
        pass
    outcome["evidence_complete"] = "evidence_error" not in outcome


def _supervise_native_output(
    process: subprocess.Popen[bytes],
    *,
    stdout_stream: BinaryIO,
    stderr_stream: BinaryIO,
    stdout_outcome: dict[str, object],
    stderr_outcome: dict[str, object],
    started_monotonic: float,
    timeout_seconds: float | None,
    termination_grace_seconds: float,
    platform_name: str,
) -> tuple[int | None, str, str, str | None]:
    """Multiplex both child pipes without cross-thread descriptor ownership."""

    assert process.stdout is not None
    assert process.stderr is not None
    pipes = (process.stdout, process.stderr)
    destinations = (stdout_stream, stderr_stream)
    outcomes = (stdout_outcome, stderr_outcome)
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
    native_exit: int | None = None
    pipe_terminal = [False, False]
    native_terminal_observed_at: float | None = None
    try:
        try:
            for pipe in pipes:
                os.set_blocking(pipe.fileno(), False)
        except (OSError, ValueError) as exc:
            for outcome in outcomes:
                outcome.setdefault("evidence_error", exc)
            termination_state, tree_terminal = _terminate_owned_process_tree(
                process,
                platform_name=platform_name,
                grace_seconds=termination_grace_seconds,
            )
            native_exit = process.poll()
            failure_class = (
                "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED"
                if tree_terminal
                else "ENGVR_PROCESS_TERMINATION_FAILED"
            )
            return native_exit, timeout_state, termination_state, failure_class

        while True:
            polled = process.poll()
            if polled is not None and native_exit is None:
                native_exit = int(polled)
                native_terminal_observed_at = time.monotonic()

            progress = False
            for index, (pipe, destination, outcome) in enumerate(
                zip(pipes, destinations, outcomes, strict=True)
            ):
                if pipe_terminal[index]:
                    continue
                consumed, reached_eof = _consume_available_pipe(
                    pipe,
                    destination,
                    outcome=outcome,
                    native_terminal=native_exit is not None,
                )
                progress = progress or consumed
                pipe_terminal[index] = reached_eof

            if native_exit is not None and all(pipe_terminal):
                break

            now = time.monotonic()
            if (
                native_exit is None
                and timeout_seconds is not None
                and now - started_monotonic >= timeout_seconds
            ):
                timeout_state = "TRIGGERED"
                termination_state, tree_terminal = _terminate_owned_process_tree(
                    process,
                    platform_name=platform_name,
                    grace_seconds=termination_grace_seconds,
                )
                native_exit = process.poll()
                if not tree_terminal:
                    failure_class = "ENGVR_PROCESS_TERMINATION_FAILED"
                    break
                failure_class = "ENGVR_PROCESS_TIMEOUT"
                native_terminal_observed_at = time.monotonic()
                continue

            if (
                native_exit is not None
                and native_terminal_observed_at is not None
                and now - native_terminal_observed_at
                >= OUTPUT_DRAIN_COMPLETION_WAIT_SECONDS
            ):
                failure_class = "ENGVR_PROCESS_TERMINATION_FAILED"
                termination_state += ";NATIVE_TREE_UNPROVEN_OUTPUT_PIPE_OPEN"
                break
            if not progress:
                time.sleep(OUTPUT_POLL_INTERVAL_SECONDS)
    finally:
        for pipe, destination, outcome in zip(
            pipes,
            destinations,
            outcomes,
            strict=True,
        ):
            _finalize_owned_output_resources(
                pipe,
                destination,
                outcome=outcome,
            )
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
        process.kill()
        process.communicate()
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
        process = subprocess.Popen(
            list(selected_argv),
            cwd=receipt_cwd,
            env=selected_environment,
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **hidden_subprocess_kwargs(
                platform_name=selected_platform,
                new_process_group=True,
            ),
        )
        pid = process.pid
    except Exception as exc:
        start_failure = type(exc).__name__
        failure_class = "ENGVR_PROCESS_START_FAILED"
        _close_prestart_evidence_stream(stdout_stream, stdout_outcome)
        _close_prestart_evidence_stream(stderr_stream, stderr_outcome)

    if process is not None:
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
    )
    try:
        atomic_write_json(receipt_path, receipt)
    except Exception:
        if receipt.pid is not None:
            receipt = replace(
                receipt,
                failure_class="ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
            )
        else:
            raise
    return receipt


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
    if (
        _lexically_inside_or_equal(cleanup_target, repository)
        or _path_is_relative_to(cleanup_canonical, repository.resolve(strict=False))
    ):
        raise ValidationReliabilityError(
            "ENGVR_RUN_SCOPED_CLEANUP_FAILED",
            "refusing repository-local cleanup target",
        )
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
    return len(retried_paths)


def cleanup_validation_run(paths: ValidationRunPathsV1) -> str:
    target = paths.cleanup_target.resolve(strict=False)
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
