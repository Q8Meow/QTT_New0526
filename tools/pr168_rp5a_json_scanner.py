#!/usr/bin/env python3
"""Structured JSON and JSONL pointer scanning for PR168-RP5A."""

from __future__ import annotations

from collections.abc import Iterator
import json
import io
from pathlib import Path
from typing import Any

from tools.pr168_rp5a_config import REPO_ROOT, MAX_STRUCTURED_JSON_BYTES, MAX_TOTAL_LINE_HITS
from tools.pr168_rp5a_term_taxonomy import iter_text_matches


def _escape_pointer_token(token: object) -> str:
    return str(token).replace("~", "~0").replace("/", "~1")


def _read_structured_text(path: Path, *, errors: str) -> str:
    from tools.validation_reliability import _scan_raise_errors

    stream = path.open("rb")
    failures = []
    data = bytearray()
    try:
        while True:
            request = min(64 * 1024, MAX_STRUCTURED_JSON_BYTES - len(data) + 1)
            chunk = stream.read(request)
            if type(chunk) is not bytes or len(chunk) > request:
                raise ValueError("invalid structured text read progress")
            if not chunk:
                break
            if len(data) + len(chunk) > MAX_STRUCTURED_JSON_BYTES:
                raise ValueError("structured text exceeds existing byte ceiling")
            data.extend(chunk)
    except BaseException as exc:
        failures.append(exc)
    finally:
        try:
            stream.close()
        except BaseException as exc:
            failures.append(exc)
    _scan_raise_errors(failures)
    return data.decode("utf-8", errors=errors)


def iter_json_matches(value: Any, pointer: str = "", *, max_matches: int | None = None) -> Iterator[dict[str, object]]:
    if max_matches is not None and (type(max_matches) is not int or max_matches < 0):
        raise ValueError("structured match allowance must be a nonnegative integer")
    remaining = [max_matches]

    def matched(text, path, kind):
        for match in iter_text_matches(text, max_matches=remaining[0]):
            if remaining[0] is not None:
                remaining[0] -= 1
            yield {
                "match_type": kind, "json_pointer_or_line_ref": path,
                "matched_term_id": match["term_id"],
                "matched_term_text_or_regex": match["term_text_or_regex"],
                "matched_text": match["matched_text"], "term_family": match["term_family"],
                "severity": match["severity"], "matched_text_short": str(text)[:200],
            }

    def walk(item, path):
        if remaining[0] == 0:
            return
        if isinstance(item, dict):
            for key, child in item.items():
                if remaining[0] == 0:
                    return
                key_path = f"{path}/{_escape_pointer_token(key)}"
                yield from matched(key, key_path, "JSON_KEY")
                yield from walk(child, key_path)
        elif isinstance(item, list):
            for index, child in enumerate(item):
                if remaining[0] == 0:
                    return
                yield from walk(child, f"{path}/{index}")
        elif isinstance(item, (str, int, float, bool)) or item is None:
            yield from matched("" if item is None else str(item), path or "/", "JSON_VALUE")

    yield from walk(value, pointer)


def scan_json_file(path: str, repo_root: Path = REPO_ROOT, *, max_matches: int = MAX_TOTAL_LINE_HITS) -> list[dict[str, object]]:
    if type(max_matches) is not int or not 0 <= max_matches <= MAX_TOTAL_LINE_HITS:
        raise ValueError("invalid structured match allowance")
    if max_matches == 0:
        return []
    text = _read_structured_text(repo_root / path, errors="strict")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return []
    return list(iter_json_matches(payload, max_matches=max_matches))


def scan_jsonl_file(path: str, repo_root: Path = REPO_ROOT, *, max_matches: int = MAX_TOTAL_LINE_HITS) -> list[dict[str, object]]:
    if type(max_matches) is not int or not 0 <= max_matches <= MAX_TOTAL_LINE_HITS:
        raise ValueError("invalid structured match allowance")
    if max_matches == 0:
        return []
    text = _read_structured_text(repo_root / path, errors="replace")
    rows = []
    for line_number, line in enumerate(io.StringIO(text, newline=None), 1):
        if max_matches is not None and len(rows) >= max_matches:
            break
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        remaining = None if max_matches is None else max_matches - len(rows)
        rows.extend(iter_json_matches(payload, f"/line/{line_number}", max_matches=remaining))
    return rows
