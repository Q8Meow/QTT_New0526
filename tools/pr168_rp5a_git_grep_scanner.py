#!/usr/bin/env python3
"""Budgeted repo file listing and text scanning for PR168-RP5A."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import json
import os
import re
import math
import io
import threading
import shutil
import subprocess
import tempfile
import time

from tools.pr168_rp5a_config import (
    MAX_FILES_SCANNED,
    MAX_LINE_HITS_PER_FILE,
    MAX_MATCHED_FILES,
    MAX_STRUCTURED_JSON_BYTES,
    MAX_TOTAL_LINE_HITS,
    MAX_WALL_SECONDS,
    PROGRESS_INTERVAL_SECONDS,
    REPO_ROOT,
    TERM_TAXONOMY,
    classify_file_kind,
    generated_ref,
    should_scan_path,
)
from tools.pr168_rp5a_term_taxonomy import match_text, iter_text_matches
from tools.pr168_rp5a_json_scanner import _read_structured_text


PASS_A_BATCH_SIZE = 50
PASS_B_BATCH_SIZE = 50

LAST_SCAN_STATS: dict[str, object] = {
    "scan_budget_status": "SCAN_BUDGET_OK",
    "budget_exhausted_flag": False,
    "budget_exhaustion_reasons": [],
    "rg_used_flag": False,
    "git_grep_used_flag": False,
    "python_fallback_used_flag": False,
    "files_available_count": 0,
    "files_scanned_count": 0,
    "candidate_files_count": 0,
    "matched_files_count": 0,
    "matched_files_processed_count": 0,
    "capped_file_count": 0,
    "capped_match_count": 0,
    "total_line_hits_emitted": 0,
    "skipped_large_line_scan_file_count": 0,
    "skipped_large_line_scan_files_limited": [],
}


def git_tracked_files(repo_root: Path = REPO_ROOT, *, scan_context=None) -> list[str]:
    if type(scan_context) is not _ScanInvocation:
        raise ValueError("native inventory requires the original scan context")
    scan_context.check(repo_root)
    try:
        result = list(scan_context.controller.inventory(lambda batch: scan_context.acquire("inventory", batch)))
        scan_context.check(repo_root)
        return result
    except BaseException:
        scan_context.controller.hold()
        raise


def scannable_files(repo_root: Path = REPO_ROOT, *, scan_context=None) -> list[str]:
    files = git_tracked_files(repo_root, scan_context=scan_context)
    selected = tuple(path for path in files if should_scan_path(path))
    scan_context.scannable = selected
    result = list(selected)
    scan_context.check(repo_root)
    return result


def read_text_lossy(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def scan_files_for_terms(
    files: list[str], repo_root: Path = REPO_ROOT, *,
    max_wall_seconds: int = MAX_WALL_SECONDS, max_files_scanned: int = MAX_FILES_SCANNED,
    max_matched_files: int = MAX_MATCHED_FILES, max_total_line_hits: int = MAX_TOTAL_LINE_HITS,
    progress_interval_seconds: int = PROGRESS_INTERVAL_SECONDS, scan_context=None,
) -> tuple[list[dict[str, object]], dict[str, dict[str, object]], dict[str, object]]:
    for value in (max_wall_seconds, max_files_scanned, max_matched_files, max_total_line_hits, progress_interval_seconds):
        if type(value) is not int or value <= 0:
            raise ValueError("existing scanner budgets must be exact positive integers")
    if type(files) is not list or any(type(path) is not str for path in files) or len(set(files)) != len(files):
        raise ValueError("scanner selected files must be unique original strings")
    if not _SCAN_PUBLIC_LOCK.acquire(blocking=False):
        raise ValueError("scanner invocation already active")
    try:
        started_ns = time.monotonic_ns()
        started_at = started_ns / 1_000_000_000
        if scan_context is not None:
            if type(scan_context) is not _ScanInvocation:
                raise ValueError("original native scan context required")
            scan_context.check(repo_root)
            if scan_context.controller.max_matched_files != max_matched_files:
                raise ValueError("scanner matched-file allowance differs from original invocation")
            scan_context.soft_deadline_ns = min(scan_context.profile.deadline_ns, started_ns + max_wall_seconds * 1_000_000_000)
        native_rows = _scan_files_for_terms_with_rg(
            files, repo_root, started_at=started_at, max_wall_seconds=max_wall_seconds,
            max_files_scanned=max_files_scanned, max_matched_files=max_matched_files,
            max_total_line_hits=max_total_line_hits, progress_interval_seconds=progress_interval_seconds,
            scan_context=scan_context)
        if native_rows is None:
            line_rows, index = _scan_files_for_terms_with_python(
                files, repo_root, started_at=started_at, max_wall_seconds=max_wall_seconds,
                max_files_scanned=max_files_scanned, max_matched_files=max_matched_files,
                max_total_line_hits=max_total_line_hits, progress_interval_seconds=progress_interval_seconds)
        else:
            line_rows, index = _index_line_rows(native_rows)
            if _budget_status(started_at, max_wall_seconds):
                scan_context.controller.stop("MAX_WALL_SECONDS_AFTER_NATIVE_COMPLETION")
            state, reasons = scan_context.controller.finish()
            for reason in reasons:
                _mark_budget_exhausted(reason)
            LAST_SCAN_STATS["scan_budget_status"] = state
        LAST_SCAN_STATS["matched_files_count"] = len(index)
        if _budget_status(started_at, max_wall_seconds):
            _mark_budget_exhausted("MAX_WALL_SECONDS_AFTER_NATIVE_COMPLETION" if native_rows is not None else "MAX_WALL_SECONDS_PYTHON_FALLBACK")
        result = (line_rows, index, dict(LAST_SCAN_STATS))
        if scan_context is not None:
            scan_context.check(repo_root, finished=True)
        return result
    except BaseException:
        if (type(scan_context) is _ScanInvocation and scan_context.ledger.process_id == os.getpid()
                and scan_context.ledger.thread_id == threading.get_ident()):
            scan_context.controller.hold()
        raise
    finally:
        _SCAN_PUBLIC_LOCK.release()


@lru_cache(maxsize=1)
def _pass_a_fixed_patterns_tuple() -> tuple[str, ...]:
    literal_patterns = [spec.term_text_or_regex for spec in TERM_TAXONOMY if not spec.is_regex]
    regex_trigger_terms = [
        "formula",
        "qku",
        "repair",
        "repaired",
        "failed",
        "negative",
        "banned",
        "unusable",
        "non-computable",
        "non_computable",
        "no-trade",
        "no_trade",
        "notrade",
        "no trade",
        "\u0130",
        "\u0131",
        "\u017f",
        "\u212a",
        "dominated",
        "dominant",
        "permanent",
        "blocked",
        "global",
        "stack",
        "live",
        "champion",
        "source-truth",
        "source truth",
        "source_truth",
        "authority",
        "candidate",
        "accepted",
        "ready",
    ]
    return tuple(sorted({*literal_patterns, *regex_trigger_terms}, key=str.lower))


@lru_cache(maxsize=1)
def _pass_a_fixed_patterns_lower_tuple() -> tuple[str, ...]:
    return tuple(pattern.lower() for pattern in _pass_a_fixed_patterns_tuple())


def _line_may_match(line: str) -> bool:
    if not line.isascii():
        return True
    lowered = line.lower()
    return any(pattern in lowered for pattern in _pass_a_fixed_patterns_lower_tuple()) or "notrade" in lowered or "no trade" in lowered


def _normalize_rg_path(raw_path: str) -> str:
    file_path = raw_path.replace("\\", "/")
    while file_path.startswith("./"):
        file_path = file_path[2:]
    return file_path


def _remaining_scan_seconds(started_at: float, max_wall_seconds: int) -> float:
    now = time.monotonic()
    if (type(started_at) not in {int, float} or type(now) not in {int, float}
            or not math.isfinite(started_at) or not math.isfinite(now) or now < started_at
            or type(max_wall_seconds) is not int or max_wall_seconds <= 0):
        raise ValueError("invalid original scanner wall clock/budget")
    return max(0.0, max_wall_seconds - (now - started_at))


def _budget_status(started_at: float, max_wall_seconds: int) -> bool:
    return _remaining_scan_seconds(started_at, max_wall_seconds) == 0.0


def _batch_timeout_seconds(started_at: float, max_wall_seconds: int) -> float:
    return min(20.0, _remaining_scan_seconds(started_at, max_wall_seconds))


def _mark_budget_exhausted(reason: str) -> None:
    reasons = list(LAST_SCAN_STATS.get("budget_exhaustion_reasons", []))
    if reason not in reasons:
        reasons.append(reason)
    LAST_SCAN_STATS.update(
        {
            "scan_budget_status": "SCAN_BUDGET_EXHAUSTED",
            "budget_exhausted_flag": True,
            "budget_exhaustion_reasons": reasons,
        }
    )


def _progress(
    phase_name: str,
    *,
    files_processed: int,
    matched_files: int,
    started_at: float,
    last_print: float,
    progress_interval_seconds: int,
    force: bool = False,
) -> float:
    now = time.monotonic()
    if force or now - last_print >= progress_interval_seconds:
        print(
            json.dumps(
                {
                    "phase": phase_name,
                    "files_processed": files_processed,
                    "matched_files": matched_files,
                    "elapsed_seconds": round(now - started_at, 3),
                },
                sort_keys=True,
            ),
            flush=True,
        )
        return now
    return last_print


def _write_pattern_file() -> Path:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False) as handle:
        for pattern in _pass_a_fixed_patterns_tuple():
            handle.write(pattern + "\n")
        return Path(handle.name)


def _scan_files_for_terms_with_rg(
    files: list[str], repo_root: Path = REPO_ROOT, *, started_at: float, max_wall_seconds: int,
    max_files_scanned: int, max_matched_files: int, max_total_line_hits: int,
    progress_interval_seconds: int, scan_context=None,
) -> list[dict[str, object]] | None:
    if scan_context is None:
        # Engine choice occurs once, before any allocation or attempt.
        if shutil.which("rg") is None and shutil.which("git") is None:
            return None
        raise ValueError("native scan selected without original resource context")
    if type(scan_context) is not _ScanInvocation:
        raise ValueError("original native scan context required")
    scan_context.check(repo_root)
    if scan_context.scannable is None:
        raise ValueError("native scanner requires its completed original inventory projection")
    selected = tuple(files[:max_files_scanned])
    controller = scan_context.controller
    controller.select(scan_context.scannable, selected)
    _scan_initialize_stats(files, selected, max_wall_seconds, max_files_scanned, max_total_line_hits,
                           engine=scan_context.profile.search_engine)
    while controller.state == "NAMES":
        if _budget_status(started_at, max_wall_seconds):
            controller.stop("MAX_WALL_SECONDS_BEFORE_NATIVE_DISPATCH")
            break
        controller.names(lambda batch: scan_context.acquire("names", batch))
    if controller.state == "NAMES_COMPLETE":
        controller.seal_names()
    LAST_SCAN_STATS.update({"candidate_files_count": len(controller.positive_names),
                           "skipped_large_line_scan_file_count": len(controller.skipped_large),
                           "skipped_large_line_scan_files_limited": list(controller.skipped_large[:50]),
                           "skipped_large_line_scan_files_all": list(controller.skipped_large)})
    rows = []
    hits = {}
    capped = set()
    last_progress = 0.0
    while controller.state == "LINES":
        if _budget_status(started_at, max_wall_seconds):
            controller.stop("MAX_WALL_SECONDS_BEFORE_NATIVE_DISPATCH")
            break
        if len(rows) >= max_total_line_hits:
            controller.stop("MAX_TOTAL_LINE_HITS")
            break
        records = controller.lines(lambda batch: scan_context.acquire("lines", batch))
        native_counts = {}
        for path, number, content in records:
            native_counts[path] = native_counts.get(path, 0) + 1
            if native_counts[path] == MAX_LINE_HITS_PER_FILE + 1:
                capped.add(path)
                continue
            if _budget_status(started_at, max_wall_seconds):
                controller.stop("MAX_WALL_SECONDS_AFTER_NATIVE_COMPLETION")
                break
            text = content.decode("utf-8", errors="replace")
            allowance = min(max_total_line_hits - len(rows), MAX_LINE_HITS_PER_FILE - hits.get(path, 0))
            for match in iter_text_matches(text, max_matches=allowance + 1):
                if _budget_status(started_at, max_wall_seconds):
                    controller.stop("MAX_WALL_SECONDS_AFTER_NATIVE_COMPLETION")
                    break
                if len(rows) >= max_total_line_hits:
                    controller.stop("MAX_TOTAL_LINE_HITS")
                    break
                if hits.get(path, 0) >= MAX_LINE_HITS_PER_FILE:
                    capped.add(path)
                    controller.reason("MAX_LINE_HITS_PER_FILE")
                    break
                rows.append(_scan_line_row(path, number, text, match))
                hits[path] = hits.get(path, 0) + 1
            if controller.state == "COMPLETE" and controller.lines_offset < len(controller.line_files):
                break
        LAST_SCAN_STATS["matched_files_processed_count"] = controller.lines_offset
        last_progress = _progress("rp5a_native_bounded_line_hits", files_processed=controller.lines_offset,
                                  matched_files=len(hits), started_at=started_at, last_print=last_progress,
                                  progress_interval_seconds=progress_interval_seconds)
    for row in rows:
        if row["file_path"] in capped:
            row["line_hits_capped_flag"] = True
    LAST_SCAN_STATS.update({"capped_file_count": len(capped), "capped_match_count": len(capped),
                           "total_line_hits_emitted": len(rows)})
    return rows


def _index_line_rows(line_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    file_index: dict[str, dict[str, object]] = {}
    for row in line_rows:
        file_path = str(row["file_path"])
        bucket = file_index.setdefault(
            file_path,
            {
                "file_path": file_path,
                "file_kind": row["file_kind"],
                "matched_term_ids": set(),
                "matched_terms": set(),
                "term_families": set(),
                "severities": [],
                "line_refs": [],
                "match_count": 0,
            },
        )
        bucket["matched_term_ids"].add(str(row["matched_term_id"]))
        bucket["matched_terms"].add(str(row["matched_term_text_or_regex"]))
        bucket["term_families"].add(str(row["term_family"]))
        bucket["severities"].append(str(row["severity"]))
        bucket["match_count"] = int(bucket["match_count"]) + 1
        if len(bucket["line_refs"]) < 250:
            bucket["line_refs"].append(f"L{row['line_number']}")
    return line_rows, file_index


def _scan_files_for_terms_with_python(
    files: list[str], repo_root: Path = REPO_ROOT, *, started_at: float, max_wall_seconds: int,
    max_files_scanned: int, max_matched_files: int, max_total_line_hits: int,
    progress_interval_seconds: int,
) -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    selected = files[:max_files_scanned]
    _scan_initialize_stats(files, selected, max_wall_seconds, max_files_scanned, max_total_line_hits, engine="python")
    LAST_SCAN_STATS["max_matched_files"] = max_matched_files
    rows = []
    hits = {}
    capped = set()
    skipped = []
    processed = 0
    last_progress = 0.0
    for path in selected:
        if _budget_status(started_at, max_wall_seconds):
            _mark_budget_exhausted("MAX_WALL_SECONDS_PYTHON_FALLBACK")
            break
        if len(rows) >= max_total_line_hits:
            _mark_budget_exhausted("MAX_TOTAL_LINE_HITS")
            break
        size = (repo_root / path).stat().st_size
        if size > MAX_STRUCTURED_JSON_BYTES:
            skipped.append(path)
            _mark_budget_exhausted("PYTHON_LARGE_FILE_LINE_SCAN_SKIPPED")
            continue
        text = _read_structured_text(repo_root / path, errors="replace")
        processed += 1
        for number, line in enumerate(io.StringIO(text, newline=None), 1):
            if _budget_status(started_at, max_wall_seconds):
                _mark_budget_exhausted("MAX_WALL_SECONDS_PYTHON_FALLBACK")
                break
            if not _line_may_match(line):
                continue
            allowance = min(max_total_line_hits - len(rows), MAX_LINE_HITS_PER_FILE - hits.get(path, 0))
            for match in iter_text_matches(line, max_matches=allowance + 1):
                if _budget_status(started_at, max_wall_seconds):
                    _mark_budget_exhausted("MAX_WALL_SECONDS_PYTHON_FALLBACK")
                    break
                if path not in hits and len(hits) >= max_matched_files:
                    _mark_budget_exhausted("MAX_MATCHED_FILES")
                    break
                if len(rows) >= max_total_line_hits:
                    _mark_budget_exhausted("MAX_TOTAL_LINE_HITS")
                    break
                if hits.get(path, 0) >= MAX_LINE_HITS_PER_FILE:
                    capped.add(path)
                    _mark_budget_exhausted("MAX_LINE_HITS_PER_FILE")
                    break
                rows.append(_scan_line_row(path, number, line, match))
                hits[path] = hits.get(path, 0) + 1
            if (len(rows) >= max_total_line_hits or path in capped
                    or (len(hits) >= max_matched_files and path not in hits)
                    or _budget_status(started_at, max_wall_seconds)):
                break
        if len(hits) >= max_matched_files:
            _mark_budget_exhausted("MAX_MATCHED_FILES")
            break
        last_progress = _progress("rp5a_python_fallback_bounded_line_hits", files_processed=processed,
                                  matched_files=len(hits), started_at=started_at, last_print=last_progress,
                                  progress_interval_seconds=progress_interval_seconds)
    for row in rows:
        if row["file_path"] in capped:
            row["line_hits_capped_flag"] = True
    LAST_SCAN_STATS.update({"candidate_files_count": len(hits), "matched_files_count": len(hits),
                           "matched_files_processed_count": processed, "capped_file_count": len(capped),
                           "capped_match_count": len(capped), "total_line_hits_emitted": len(rows),
                           "skipped_large_line_scan_file_count": len(skipped),
                           "skipped_large_line_scan_files_limited": skipped[:50],
                           "skipped_large_line_scan_files_all": skipped})
    return _index_line_rows(rows)


def file_inventory_rows(files: list[str], *, source: str) -> list[dict[str, object]]:
    return [
        {
            "input_source": source,
            "file_path": file_path,
            "file_kind": classify_file_kind(file_path),
            "physical_filename": generated_ref(file_path),
        }
        for file_path in files
    ]


_SCAN_PUBLIC_LOCK = threading.Lock()


def _scan_path_identity(path, *, platform_name=None):
    platform = os.name if platform_name is None else platform_name
    if (type(path) is not str or not path or path.startswith("/") or "\0" in path
            or any(part in {"", ".", "..", ".git"} for part in path.split("/"))
            or any(0xD800 <= ord(character) <= 0xDFFF for character in path)):
        raise ValueError("invalid exact scan path identity")
    if platform in {"nt", "win32"}:
        for part in path.split("/"):
            stem = part.split(".")[0].upper()
            if (any(character in '<>:"\\|?*' or ord(character) < 32 for character in part)
                    or part.endswith((" ", ".")) or part.casefold() == ".git"
                    or stem in {"CON", "PRN", "AUX", "NUL"}
                    or re.fullmatch(r"(?:COM|LPT)[1-9\u00b9\u00b2\u00b3]", stem)):
                raise ValueError("unsupported Windows scan path identity")
    return path


def _scan_admitted_paths(paths, *, path_limit, byte_limit, platform_name=None):
    if (type(paths) is not tuple or type(path_limit) is not int or path_limit < 0
            or type(byte_limit) is not int or byte_limit < 0 or len(paths) > path_limit):
        raise ValueError("invalid bounded scan path tuple")
    consumed = 0
    seen = set()
    aliases = set()
    platform = os.name if platform_name is None else platform_name
    for path in paths:
        if type(path) is not str:
            raise ValueError("scan identity is not text")
        consumed += 1
        for character in path:
            value = ord(character)
            consumed += 1 if value < 128 else 2 if value < 2048 else 3 if value < 65536 else 4
            if consumed > byte_limit:
                raise ValueError("scan inventory UTF-8 allowance exceeded")
        if consumed > byte_limit:
            raise ValueError("scan inventory UTF-8 allowance exceeded")
        _scan_path_identity(path, platform_name=platform)
        if path in seen or (platform in {"nt", "win32"} and path.casefold() in aliases):
            raise ValueError("duplicate or aliased scan identity")
        seen.add(path)
        aliases.add(path.casefold())
    return paths


def _scan_stdout_bound(stage, batch, sizes):
    if stage in {"inventory", "names"}:
        return sum(len(path.encode("utf-8")) + 1 for path in batch)
    if stage != "lines":
        raise ValueError("unknown scan wire stage")
    total = 0
    for path in batch:
        size = sizes.get(path)
        if type(size) is not int or not 0 <= size <= MAX_STRUCTURED_JSON_BYTES:
            raise ValueError("missing or inadmissible original line size")
        # Current selected section 9.3.25 bound, including the overflow line.
        total += size + 51 * (len(path.encode("utf-8")) + len(str(size + 1)) + 3)
    return total


def _scan_wire_bytes(chunks, limit):
    data = bytearray()
    for chunk in chunks:
        if type(chunk) is not bytes or not chunk or len(chunk) > limit - len(data):
            raise ValueError("scan parser chunk exceeds original protocol bound")
        data.extend(chunk)
    return data


def _scan_parse_names(chunks, *, batch, exit_code, inventory=False):
    if type(exit_code) is not int or exit_code not in ({0} if inventory else {0, 1}):
        raise ValueError("invalid native scan exit before parsing")
    data = _scan_wire_bytes(chunks, _scan_stdout_bound("names", batch, {}))
    if exit_code == 1:
        if data:
            raise ValueError("native no-match exit has nonempty stdout")
        return ()
    if not data:
        if inventory and not batch:
            return ()
        raise ValueError("native success lacks required name records")
    if data[-1] != 0:
        raise ValueError("truncated native name record")
    names = []
    seen = set()
    offset = 0
    while offset < len(data):
        end = data.index(0, offset)
        path = bytes(data[offset:end]).decode("utf-8", errors="strict")
        _scan_path_identity(path)
        if path not in batch or path in seen or len(names) >= len(batch):
            raise ValueError("foreign or duplicate native name")
        seen.add(path)
        names.append(path)
        offset = end + 1
    if inventory:
        if set(names) != set(batch):
            raise ValueError("native inventory differs from independent expected identity set")
        return tuple(names)
    return tuple(sorted(names, key=lambda path: (path.casefold(), path)))


def _scan_parse_lines(chunks, *, batch, sizes, engine, exit_code):
    if type(exit_code) is not int or exit_code not in {0, 1} or engine not in {"git", "rg"}:
        raise ValueError("invalid native line completion")
    data = _scan_wire_bytes(chunks, _scan_stdout_bound("lines", batch, sizes))
    if exit_code == 1:
        if data:
            raise ValueError("native no-match exit has line output")
        return ()
    if not data:
        raise ValueError("native success lacks required line records")
    offset = 0
    records = []
    last = {}
    counts = {}
    content_bytes = {}
    while offset < len(data):
        try:
            path_end = data.index(0, offset)
            separator = 0 if engine == "git" else 58
            number_end = data.index(separator, path_end + 1)
            line_end = data.index(10, number_end + 1)
        except ValueError as exc:
            raise ValueError("truncated native line framing") from exc
        path = bytes(data[offset:path_end]).decode("utf-8", errors="strict")
        if path not in batch:
            raise ValueError("foreign native line path")
        number_text = bytes(data[path_end + 1:number_end])
        if (len(number_text) > len(str(sizes[path] + 1))
                or re.fullmatch(rb"[1-9][0-9]*", number_text) is None):
            raise ValueError("noncanonical native line number")
        number = int(number_text)
        if number <= last.get(path, 0) or number > sizes[path] + 1:
            raise ValueError("repeated or excessive native line number")
        content = bytes(data[number_end + 1:line_end])
        content_bytes[path] = content_bytes.get(path, 0) + len(content) + 1
        counts[path] = counts.get(path, 0) + 1
        if counts[path] > 51 or content_bytes[path] > sizes[path] + 1:
            raise ValueError("native line content/record allowance exceeded")
        last[path] = number
        records.append((path, number, content))
        offset = line_end + 1
    return tuple(records)


def _scan_child_environment(parent):
    child = {}
    seen = set()
    for key, value in parent.items():
        if (type(key) is not str or type(value) is not str or not key or "=" in key
                or "\0" in key or "\0" in value or key.upper() in seen):
            raise ValueError("invalid scan child environment")
        upper = key.upper()
        seen.add(upper)
        if (not upper.startswith(("GIT_", "RIPGREP_"))
                and upper not in {"PAGER", "GREP_OPTIONS", "GREP_COLOR", "GREP_COLORS", "LC_ALL", "LANG"}):
            child[key] = value
    child.update({
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_SYSTEM": os.devnull, "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0", "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_NO_LAZY_FETCH": "1", "GIT_ALLOW_PROTOCOL": "", "GIT_TRACE": "0",
        "GIT_TRACE2": "0", "GIT_TRACE2_PERF": "0", "GIT_TRACE2_EVENT": "0",
        "LC_ALL": "C", "LANG": "C",
    })
    return child


def _scan_native_command(profile, stage, batch, pattern_path):
    if stage == "inventory":
        return [profile.git_executable, "--no-pager", "--literal-pathspecs", "ls-files", "--cached", "--full-name", "-z"]
    if stage not in {"names", "lines"} or not batch or pattern_path is None:
        raise ValueError("invalid native scan stage/batch/pattern")
    if profile.search_engine == "git":
        command = [profile.search_executable, "--no-pager", "--literal-pathspecs",
                   "-c", "grep.column=false", "-c", "grep.lineNumber=false",
                   "-c", "grep.fullName=true", "-c", "grep.fallbackToNoIndex=false",
                   "grep", "-z", "--full-name", "--no-color", "--no-heading", "--no-break",
                   "--no-column", "--no-textconv", "--no-recurse-submodules", "--threads=1", "-I", "-F", "-i"]
        command += ["-l"] if stage == "names" else ["-n", "-H", "--max-count=51"]
        return [*command, "-f", str(pattern_path), "--", *batch]
    if "-" in batch:
        raise ValueError("ripgrep stdin spelling is not an admitted file operand")
    command = [profile.search_executable, "--no-config", "--null", "--fixed-strings", "--ignore-case",
               "--color=never", "--no-heading", "--no-column", "--no-follow", "--no-mmap",
               "--encoding=none", "--threads=1", "--sort=path"]
    command += ["--files-with-matches"] if stage == "names" else ["--line-number", "--with-filename", "--max-count=51"]
    return [*command, "--file", str(pattern_path), "--", *batch]


class _ScanInvocation:
    def __init__(self, profile, *, check_candidate, max_matched_files=MAX_MATCHED_FILES):
        from tools.validation_reliability import _Rp5aScanProfile, _ScanReservationLedger, _ScanPhaseController
        if type(profile) is not _Rp5aScanProfile:
            raise TypeError("original scanner profile required")
        if dict(profile.child_environment) != _scan_child_environment(dict(profile.child_environment)):
            raise ValueError("scan child environment was not canonically admitted")
        self.profile = profile
        self.ledger = _ScanReservationLedger(profile)
        self.controller = _ScanPhaseController(profile, self.ledger, check_candidate=check_candidate,
                                                max_matched_files=max_matched_files,
                                                structured_byte_limit=MAX_STRUCTURED_JSON_BYTES)
        self.check_candidate = check_candidate
        self.scannable = None
        self.soft_deadline_ns = profile.deadline_ns

    def check(self, repo_root, *, finished=False):
        from tools.validation_reliability import _scan_deadline, _scan_candidate_fence
        if type(repo_root) not in {Path, type(Path())} or Path(repo_root) != Path(self.profile.repo_root):
            raise ValueError("scanner original root differs")
        if not finished:
            self.ledger.check()
        else:
            if (os.getpid(), threading.get_ident()) != (self.ledger.process_id, self.ledger.thread_id):
                raise ValueError("foreign final scanner owner")
            if self.controller.state != "DONE" or self.ledger.state != "CLOSED":
                raise ValueError("scan finalization missing")
            if _scan_deadline(self.profile.deadline_ns) < self.ledger.last_ns:
                raise ValueError("scan clock regressed at exposure")
        _scan_candidate_fence(self.check_candidate)

    def acquire(self, stage, batch):
        from tools.validation_reliability import _execute_scan_with_scratch
        self.check(Path(self.profile.repo_root))
        sizes = dict(self.profile.file_sizes)
        pattern = None if stage == "inventory" else ("\n".join(_pass_a_fixed_patterns_tuple()) + "\n").encode("utf-8")
        deadline = self.profile.deadline_ns if stage == "inventory" else min(
            self.profile.deadline_ns, self.soft_deadline_ns, time.monotonic_ns() + 20_000_000_000)
        parser = (lambda chunks, code: _scan_parse_lines(
            chunks, batch=batch, sizes=sizes, engine=self.profile.search_engine, exit_code=code)
        ) if stage == "lines" else (lambda chunks, code: _scan_parse_names(
            chunks, batch=batch, exit_code=code, inventory=stage == "inventory"))
        return _execute_scan_with_scratch(
            self.ledger, stdout_bound=_scan_stdout_bound(stage, batch, sizes), pattern=pattern,
            command=lambda path: _scan_native_command(self.profile, stage, batch, path), parser=parser,
            check_candidate=self.check_candidate, deadline_ns=deadline, allow_no_match=stage != "inventory")


def _scan_initialize_stats(files, selected, wall, file_limit, hit_limit, *, engine):
    LAST_SCAN_STATS.clear()
    LAST_SCAN_STATS.update({
        "scan_budget_status": "SCAN_BUDGET_OK", "budget_exhausted_flag": False,
        "budget_exhaustion_reasons": [], "rg_used_flag": engine == "rg",
        "git_grep_used_flag": engine == "git", "python_fallback_used_flag": engine == "python",
        "files_available_count": len(files), "files_scanned_count": len(selected),
        "candidate_files_count": 0, "matched_files_count": 0, "matched_files_processed_count": 0,
        "capped_file_count": 0, "capped_match_count": 0, "total_line_hits_emitted": 0,
        "skipped_large_line_scan_file_count": 0, "skipped_large_line_scan_files_limited": [],
        "skipped_large_line_scan_files_all": [], "max_wall_seconds": wall,
        "max_files_scanned": file_limit, "max_total_line_hits": hit_limit,
        "max_line_hits_per_file": MAX_LINE_HITS_PER_FILE,
    })
    if len(files) > len(selected):
        _mark_budget_exhausted("MAX_FILES_SCANNED")


def _scan_line_row(path, number, text, match):
    return {"file_path": path, "file_kind": classify_file_kind(path), "line_number": number,
            "matched_term_id": match["term_id"], "matched_term_text_or_regex": match["term_text_or_regex"],
            "matched_text": match["matched_text"], "term_family": match["term_family"],
            "severity": match["severity"], "text_short": text.strip()[:200], "line_hits_capped_flag": False}
