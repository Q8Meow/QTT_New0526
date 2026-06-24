#!/usr/bin/env python3
"""Budgeted repo file listing and text scanning for PR168-RP5A."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import json
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
from tools.pr168_rp5a_term_taxonomy import match_text


PASS_A_BATCH_SIZE = 50
PASS_B_BATCH_SIZE = 50

LAST_SCAN_STATS: dict[str, object] = {
    "scan_budget_status": "SCAN_BUDGET_OK",
    "budget_exhausted_flag": False,
    "budget_exhaustion_reasons": [],
    "rg_used_flag": False,
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


def git_tracked_files(repo_root: Path = REPO_ROOT) -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo_root,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        return []
    return sorted(path.decode("utf-8", errors="replace") for path in completed.stdout.split(b"\0") if path)


def scannable_files(repo_root: Path = REPO_ROOT) -> list[str]:
    return [path for path in git_tracked_files(repo_root) if should_scan_path(path)]


def read_text_lossy(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def scan_files_for_terms(
    files: list[str],
    repo_root: Path = REPO_ROOT,
    *,
    max_wall_seconds: int = MAX_WALL_SECONDS,
    max_files_scanned: int = MAX_FILES_SCANNED,
    max_matched_files: int = MAX_MATCHED_FILES,
    max_total_line_hits: int = MAX_TOTAL_LINE_HITS,
    progress_interval_seconds: int = PROGRESS_INTERVAL_SECONDS,
) -> tuple[list[dict[str, object]], dict[str, dict[str, object]], dict[str, object]]:
    started_at = time.monotonic()
    rg_rows = _scan_files_for_terms_with_rg(
        files,
        repo_root,
        started_at=started_at,
        max_wall_seconds=max_wall_seconds,
        max_files_scanned=max_files_scanned,
        max_matched_files=max_matched_files,
        max_total_line_hits=max_total_line_hits,
        progress_interval_seconds=progress_interval_seconds,
    )
    if rg_rows is not None:
        line_rows, index = _index_line_rows(rg_rows)
        LAST_SCAN_STATS["matched_files_count"] = len(index)
        return line_rows, index, dict(LAST_SCAN_STATS)
    line_rows, index = _scan_files_for_terms_with_python(
        files,
        repo_root,
        started_at=started_at,
        max_wall_seconds=max_wall_seconds,
        max_files_scanned=max_files_scanned,
        max_total_line_hits=max_total_line_hits,
        progress_interval_seconds=progress_interval_seconds,
    )
    return line_rows, index, dict(LAST_SCAN_STATS)


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


def _line_may_match(text: str) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in _pass_a_fixed_patterns_lower_tuple())


def _normalize_rg_path(raw_path: str) -> str:
    file_path = raw_path.replace("\\", "/")
    while file_path.startswith("./"):
        file_path = file_path[2:]
    return file_path


def _budget_status(started_at: float, max_wall_seconds: int) -> bool:
    return time.monotonic() - started_at >= max_wall_seconds


def _batch_timeout_seconds(started_at: float, max_wall_seconds: int) -> int:
    remaining = max_wall_seconds - (time.monotonic() - started_at)
    return max(1, min(20, int(remaining)))


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
    files: list[str],
    repo_root: Path,
    *,
    started_at: float,
    max_wall_seconds: int,
    max_files_scanned: int,
    max_matched_files: int,
    max_total_line_hits: int,
    progress_interval_seconds: int,
) -> list[dict[str, object]] | None:
    rg_executable = shutil.which("rg")
    if rg_executable is None:
        LAST_SCAN_STATS.update({"rg_used_flag": False, "python_fallback_used_flag": True})
        return None

    scan_files = files[:max_files_scanned]
    tracked = set(scan_files)
    LAST_SCAN_STATS.update(
        {
            "scan_budget_status": "SCAN_BUDGET_OK",
            "budget_exhausted_flag": False,
            "budget_exhaustion_reasons": [],
            "rg_used_flag": True,
            "python_fallback_used_flag": False,
            "files_available_count": len(files),
            "files_scanned_count": len(scan_files),
            "candidate_files_count": 0,
            "matched_files_count": 0,
            "matched_files_processed_count": 0,
            "capped_file_count": 0,
            "capped_match_count": 0,
            "total_line_hits_emitted": 0,
            "skipped_large_line_scan_file_count": 0,
            "skipped_large_line_scan_files_limited": [],
            "max_wall_seconds": max_wall_seconds,
            "max_files_scanned": max_files_scanned,
            "max_matched_files": max_matched_files,
            "max_total_line_hits": max_total_line_hits,
            "max_line_hits_per_file": MAX_LINE_HITS_PER_FILE,
        }
    )
    if len(files) > len(scan_files):
        _mark_budget_exhausted("MAX_FILES_SCANNED")

    pattern_path = _write_pattern_file()
    matched_files: list[str] = []
    matched_seen: set[str] = set()
    files_processed = 0
    last_progress = 0.0
    last_progress = _progress(
        "rp5a_rg_pass_a_files_with_matches",
        files_processed=0,
        matched_files=0,
        started_at=started_at,
        last_print=last_progress,
        progress_interval_seconds=progress_interval_seconds,
        force=True,
    )
    try:
        for batch_start in range(0, len(scan_files), PASS_A_BATCH_SIZE):
            if _budget_status(started_at, max_wall_seconds):
                _mark_budget_exhausted("MAX_WALL_SECONDS_PASS_A")
                break
            batch = scan_files[batch_start : batch_start + PASS_A_BATCH_SIZE]
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False) as output_file:
                output_path = Path(output_file.name)
            command = [
                rg_executable,
                "--fixed-strings",
                "--files-with-matches",
                "--ignore-case",
                "--no-messages",
                "--color",
                "never",
                "--file",
                str(pattern_path),
                "--",
                *batch,
            ]
            try:
                with output_path.open("w", encoding="utf-8", newline="\n") as output:
                    try:
                        completed = subprocess.run(
                            command,
                            cwd=repo_root,
                            check=False,
                            stdout=output,
                            stderr=subprocess.DEVNULL,
                            text=True,
                            encoding="utf-8",
                            errors="replace",
                            timeout=_batch_timeout_seconds(started_at, max_wall_seconds),
                        )
                    except FileNotFoundError:
                        LAST_SCAN_STATS.update({"rg_used_flag": False, "python_fallback_used_flag": True})
                        return None
                    except subprocess.TimeoutExpired:
                        _mark_budget_exhausted("RG_PASS_A_BATCH_TIMEOUT")
                        break
                if completed.returncode not in {0, 1}:
                    LAST_SCAN_STATS.update({"rg_used_flag": False, "python_fallback_used_flag": True})
                    return None
                with output_path.open("r", encoding="utf-8", errors="replace") as handle:
                    for line in handle:
                        file_path = _normalize_rg_path(line.strip())
                        if file_path in tracked and file_path not in matched_seen:
                            matched_seen.add(file_path)
                            matched_files.append(file_path)
                            if len(matched_files) >= max_matched_files:
                                _mark_budget_exhausted("MAX_MATCHED_FILES")
                                break
            finally:
                try:
                    output_path.unlink()
                except OSError:
                    pass
            files_processed += len(batch)
            LAST_SCAN_STATS["candidate_files_count"] = len(matched_files)
            last_progress = _progress(
                "rp5a_rg_pass_a_files_with_matches",
                files_processed=files_processed,
                matched_files=len(matched_files),
                started_at=started_at,
                last_print=last_progress,
                progress_interval_seconds=progress_interval_seconds,
            )
            if LAST_SCAN_STATS.get("budget_exhausted_flag"):
                break
    finally:
        try:
            pattern_path.unlink()
        except OSError:
            pass

    matched_files = sorted(matched_files, key=lambda value: (value.casefold(), value))[:max_matched_files]
    LAST_SCAN_STATS["candidate_files_count"] = len(matched_files)
    large_line_scan_skips: list[str] = []
    line_scan_files: list[str] = []
    for file_path in matched_files:
        try:
            size = (repo_root / file_path).stat().st_size
        except OSError:
            size = 0
        if size > MAX_STRUCTURED_JSON_BYTES:
            large_line_scan_skips.append(file_path)
        else:
            line_scan_files.append(file_path)
    if large_line_scan_skips:
        _mark_budget_exhausted("PASS_B_LARGE_FILE_LINE_SCAN_SKIPPED")
        LAST_SCAN_STATS.update(
            {
                "skipped_large_line_scan_file_count": len(large_line_scan_skips),
                "skipped_large_line_scan_files_limited": large_line_scan_skips[:50],
                "skipped_large_line_scan_files_all": large_line_scan_skips,
            }
        )
    if not matched_files:
        _progress(
            "rp5a_rg_pass_b_bounded_line_hits",
            files_processed=0,
            matched_files=0,
            started_at=started_at,
            last_print=0.0,
            progress_interval_seconds=progress_interval_seconds,
            force=True,
        )
        return []

    pattern_path = _write_pattern_file()
    rows: list[dict[str, object]] = []
    hits_by_file: dict[str, int] = {}
    capped_files: set[str] = set()
    capped_match_count = 0
    matched_processed = 0
    last_progress = 0.0
    last_progress = _progress(
        "rp5a_rg_pass_b_bounded_line_hits",
        files_processed=0,
        matched_files=len(matched_files),
        started_at=started_at,
        last_print=last_progress,
        progress_interval_seconds=progress_interval_seconds,
        force=True,
    )
    try:
        for batch_start in range(0, len(line_scan_files), PASS_B_BATCH_SIZE):
            if _budget_status(started_at, max_wall_seconds):
                _mark_budget_exhausted("MAX_WALL_SECONDS_PASS_B")
                break
            if len(rows) >= max_total_line_hits:
                _mark_budget_exhausted("MAX_TOTAL_LINE_HITS")
                break
            batch = line_scan_files[batch_start : batch_start + PASS_B_BATCH_SIZE]
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False) as output_file:
                output_path = Path(output_file.name)
            command = [
                rg_executable,
                "--vimgrep",
                "--fixed-strings",
                "--ignore-case",
                "--no-messages",
                "--color",
                "never",
                "--max-count",
                str(MAX_LINE_HITS_PER_FILE),
                "--file",
                str(pattern_path),
                "--",
                *batch,
            ]
            try:
                with output_path.open("w", encoding="utf-8", newline="\n") as output:
                    try:
                        completed = subprocess.run(
                            command,
                            cwd=repo_root,
                            check=False,
                            stdout=output,
                            stderr=subprocess.DEVNULL,
                            text=True,
                            encoding="utf-8",
                            errors="replace",
                            timeout=_batch_timeout_seconds(started_at, max_wall_seconds),
                        )
                    except FileNotFoundError:
                        LAST_SCAN_STATS.update({"rg_used_flag": False, "python_fallback_used_flag": True})
                        return None
                    except subprocess.TimeoutExpired:
                        _mark_budget_exhausted("RG_PASS_B_BATCH_TIMEOUT")
                        break
                if completed.returncode not in {0, 1}:
                    continue
                with output_path.open("r", encoding="utf-8", errors="replace") as handle:
                    for output_line in handle:
                        if len(rows) >= max_total_line_hits:
                            _mark_budget_exhausted("MAX_TOTAL_LINE_HITS")
                            break
                        try:
                            raw_path, line_number_text, _column, text = output_line.rstrip("\n").split(":", 3)
                        except ValueError:
                            continue
                        file_path = _normalize_rg_path(raw_path)
                        if file_path not in tracked:
                            continue
                        current_hits = hits_by_file.get(file_path, 0)
                        if current_hits >= MAX_LINE_HITS_PER_FILE:
                            capped_files.add(file_path)
                            capped_match_count += 1
                            continue
                        matches = match_text(text)
                        if not matches:
                            continue
                        try:
                            line_number = int(line_number_text)
                        except ValueError:
                            line_number = 0
                        kind = classify_file_kind(file_path)
                        for match in matches:
                            if len(rows) >= max_total_line_hits:
                                _mark_budget_exhausted("MAX_TOTAL_LINE_HITS")
                                break
                            if hits_by_file.get(file_path, 0) >= MAX_LINE_HITS_PER_FILE:
                                capped_files.add(file_path)
                                capped_match_count += 1
                                break
                            rows.append(
                                {
                                    "file_path": file_path,
                                    "file_kind": kind,
                                    "line_number": line_number,
                                    "matched_term_id": match["term_id"],
                                    "matched_term_text_or_regex": match["term_text_or_regex"],
                                    "matched_text": match["matched_text"],
                                    "term_family": match["term_family"],
                                    "severity": match["severity"],
                                    "text_short": text.strip()[:200],
                                    "line_hits_capped_flag": False,
                                }
                            )
                            hits_by_file[file_path] = hits_by_file.get(file_path, 0) + 1
                        if LAST_SCAN_STATS.get("budget_exhausted_flag"):
                            break
            finally:
                try:
                    output_path.unlink()
                except OSError:
                    pass
            matched_processed += len(batch)
            LAST_SCAN_STATS["matched_files_processed_count"] = matched_processed
            LAST_SCAN_STATS["total_line_hits_emitted"] = len(rows)
            last_progress = _progress(
                "rp5a_rg_pass_b_bounded_line_hits",
                files_processed=matched_processed,
                matched_files=len(hits_by_file),
                started_at=started_at,
                last_print=last_progress,
                progress_interval_seconds=progress_interval_seconds,
            )
            if LAST_SCAN_STATS.get("budget_exhausted_flag"):
                break
    finally:
        try:
            pattern_path.unlink()
        except OSError:
            pass

    if capped_files:
        for row in rows:
            if row["file_path"] in capped_files:
                row["line_hits_capped_flag"] = True
    LAST_SCAN_STATS.update(
        {
            "capped_file_count": len(capped_files),
            "capped_match_count": capped_match_count,
            "total_line_hits_emitted": len(rows),
        }
    )
    _progress(
        "rp5a_rg_pass_b_bounded_line_hits",
        files_processed=matched_processed,
        matched_files=len(hits_by_file),
        started_at=started_at,
        last_print=last_progress,
        progress_interval_seconds=progress_interval_seconds,
        force=True,
    )
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
    files: list[str],
    repo_root: Path = REPO_ROOT,
    *,
    started_at: float,
    max_wall_seconds: int,
    max_files_scanned: int,
    max_total_line_hits: int,
    progress_interval_seconds: int,
) -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    scan_files = files[:max_files_scanned]
    LAST_SCAN_STATS.update(
        {
            "scan_budget_status": "SCAN_BUDGET_OK",
            "budget_exhausted_flag": False,
            "budget_exhaustion_reasons": [],
            "rg_used_flag": False,
            "python_fallback_used_flag": True,
            "files_available_count": len(files),
            "files_scanned_count": len(scan_files),
            "candidate_files_count": 0,
            "matched_files_count": 0,
            "matched_files_processed_count": 0,
            "capped_file_count": 0,
            "capped_match_count": 0,
            "total_line_hits_emitted": 0,
            "skipped_large_line_scan_file_count": 0,
            "skipped_large_line_scan_files_limited": [],
            "skipped_large_line_scan_files_all": [],
            "max_wall_seconds": max_wall_seconds,
            "max_files_scanned": max_files_scanned,
            "max_total_line_hits": max_total_line_hits,
            "max_line_hits_per_file": MAX_LINE_HITS_PER_FILE,
        }
    )
    if len(files) > len(scan_files):
        _mark_budget_exhausted("MAX_FILES_SCANNED")

    line_rows: list[dict[str, object]] = []
    file_index: dict[str, dict[str, object]] = {}
    capped_files: set[str] = set()
    capped_match_count = 0
    last_progress = 0.0
    files_processed = 0
    for file_number, file_path in enumerate(scan_files, start=1):
        files_processed = file_number
        if _budget_status(started_at, max_wall_seconds):
            _mark_budget_exhausted("MAX_WALL_SECONDS_PYTHON_FALLBACK")
            break
        if len(line_rows) >= max_total_line_hits:
            _mark_budget_exhausted("MAX_TOTAL_LINE_HITS")
            break
        full_path = repo_root / file_path
        try:
            with full_path.open("r", encoding="utf-8", errors="replace") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if len(line_rows) >= max_total_line_hits:
                        _mark_budget_exhausted("MAX_TOTAL_LINE_HITS")
                        break
                    if not _line_may_match(line):
                        continue
                    matches = match_text(line)
                    if not matches:
                        continue
                    kind = classify_file_kind(file_path)
                    file_index.setdefault(
                        file_path,
                        {
                            "file_path": file_path,
                            "file_kind": kind,
                            "matched_term_ids": set(),
                            "matched_terms": set(),
                            "term_families": set(),
                            "severities": [],
                            "line_refs": [],
                            "match_count": 0,
                        },
                    )
                    bucket = file_index[file_path]
                    for match in matches:
                        if int(bucket["match_count"]) >= MAX_LINE_HITS_PER_FILE:
                            capped_files.add(file_path)
                            capped_match_count += 1
                            break
                        bucket["matched_term_ids"].add(str(match["term_id"]))
                        bucket["matched_terms"].add(str(match["term_text_or_regex"]))
                        bucket["term_families"].add(str(match["term_family"]))
                        bucket["severities"].append(str(match["severity"]))
                        bucket["match_count"] = int(bucket["match_count"]) + 1
                        if len(bucket["line_refs"]) < 250:
                            bucket["line_refs"].append(f"L{line_number}")
                        line_rows.append(
                            {
                                "file_path": file_path,
                                "file_kind": kind,
                                "line_number": line_number,
                                "matched_term_id": match["term_id"],
                                "matched_term_text_or_regex": match["term_text_or_regex"],
                                "matched_text": match["matched_text"],
                                "term_family": match["term_family"],
                                "severity": match["severity"],
                                "text_short": line.strip()[:200],
                                "line_hits_capped_flag": False,
                            }
                        )
                    if LAST_SCAN_STATS.get("budget_exhausted_flag"):
                        break
        except OSError:
            continue
        last_progress = _progress(
            "rp5a_python_fallback_bounded_line_hits",
            files_processed=file_number,
            matched_files=len(file_index),
            started_at=started_at,
            last_print=last_progress,
            progress_interval_seconds=progress_interval_seconds,
        )
    for row in line_rows:
        if row["file_path"] in capped_files:
            row["line_hits_capped_flag"] = True
    LAST_SCAN_STATS.update(
        {
            "candidate_files_count": len(file_index),
            "matched_files_count": len(file_index),
            "matched_files_processed_count": files_processed,
            "capped_file_count": len(capped_files),
            "capped_match_count": capped_match_count,
            "total_line_hits_emitted": len(line_rows),
        }
    )
    return line_rows, file_index


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
