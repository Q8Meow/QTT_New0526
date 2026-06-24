#!/usr/bin/env python3
"""Structured JSON and JSONL pointer scanning for PR168-RP5A."""

from __future__ import annotations

from collections.abc import Iterator
import json
from pathlib import Path
from typing import Any

from tools.pr168_rp5a_config import REPO_ROOT
from tools.pr168_rp5a_term_taxonomy import match_text


def _escape_pointer_token(token: object) -> str:
    return str(token).replace("~", "~0").replace("/", "~1")


def iter_json_matches(value: Any, pointer: str = "") -> Iterator[dict[str, object]]:
    if isinstance(value, dict):
        for key, item in value.items():
            key_pointer = f"{pointer}/{_escape_pointer_token(key)}"
            for match in match_text(key):
                yield {
                    "match_type": "JSON_KEY",
                    "json_pointer_or_line_ref": key_pointer,
                    "matched_term_id": match["term_id"],
                    "matched_term_text_or_regex": match["term_text_or_regex"],
                    "matched_text": match["matched_text"],
                    "term_family": match["term_family"],
                    "severity": match["severity"],
                    "matched_text_short": str(key)[:200],
                }
            yield from iter_json_matches(item, key_pointer)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            yield from iter_json_matches(item, f"{pointer}/{index}")
        return
    if isinstance(value, (str, int, float, bool)) or value is None:
        text = "" if value is None else str(value)
        for match in match_text(text):
            yield {
                "match_type": "JSON_VALUE",
                "json_pointer_or_line_ref": pointer or "/",
                "matched_term_id": match["term_id"],
                "matched_term_text_or_regex": match["term_text_or_regex"],
                "matched_text": match["matched_text"],
                "term_family": match["term_family"],
                "severity": match["severity"],
                "matched_text_short": text[:200],
            }


def scan_json_file(path: str, repo_root: Path = REPO_ROOT) -> list[dict[str, object]]:
    full_path = repo_root / path
    try:
        payload = json.loads(full_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return list(iter_json_matches(payload))


def scan_jsonl_file(path: str, repo_root: Path = REPO_ROOT) -> list[dict[str, object]]:
    full_path = repo_root / path
    rows: list[dict[str, object]] = []
    try:
        with full_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError:
                    continue
                for row in iter_json_matches(payload, f"/line/{line_number}"):
                    rows.append(row)
    except OSError:
        return []
    return rows
