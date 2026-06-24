#!/usr/bin/env python3
"""Build row/field-level semantic hit rows."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from tools.pr168_rp5a_config import MAX_STRUCTURED_JSON_BYTES, MAX_TOTAL_LINE_HITS, classify_file_kind
from tools.pr168_rp5a_json_scanner import scan_json_file, scan_jsonl_file

LAST_ROW_FIELD_STATS: dict[str, object] = {
    "skipped_large_structured_file_count": 0,
    "skipped_large_structured_files_limited": [],
    "row_field_budget_exhausted_flag": False,
    "row_field_rows_emitted": 0,
}


def _text_match_type(file_kind: str) -> str:
    if file_kind == "TOOL_SOURCE":
        return "TOOL_STRING"
    if file_kind == "TEST_SOURCE":
        return "TEST_EXPECTATION"
    if file_kind == "VALIDATOR":
        return "VALIDATION_EXPECTATION"
    if file_kind == "MANIFEST":
        return "MANIFEST_REF"
    return "TEXT_LINE"


def build_row_field_hits(line_rows: list[dict[str, object]], repo_root: Path) -> list[dict[str, object]]:
    skipped_large: list[str] = []
    by_file: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in line_rows:
        by_file[str(row["file_path"])].append(row)

    hit_rows: list[dict[str, object]] = []
    row_number = 0
    for file_path, rows in sorted(by_file.items()):
        if row_number >= MAX_TOTAL_LINE_HITS:
            break
        file_kind = classify_file_kind(file_path)
        suffix = Path(file_path).suffix.lower()
        structured: list[dict[str, object]] = []
        try:
            size = (repo_root / file_path).stat().st_size
        except OSError:
            size = MAX_STRUCTURED_JSON_BYTES + 1
        structured_candidate = suffix == ".jsonl" or suffix == ".json" or file_path.endswith(".manifest.json") or file_path.endswith(".report.json")
        if structured_candidate and size > MAX_STRUCTURED_JSON_BYTES:
            skipped_large.append(file_path)
        if size <= MAX_STRUCTURED_JSON_BYTES:
            if suffix == ".jsonl":
                structured = scan_jsonl_file(file_path, repo_root)
            elif suffix == ".json" or file_path.endswith(".manifest.json") or file_path.endswith(".report.json"):
                structured = scan_json_file(file_path, repo_root)

        if structured:
            for item in structured:
                if row_number >= MAX_TOTAL_LINE_HITS:
                    break
                row_number += 1
                hit_rows.append(
                    {
                        "row_id": f"RP5A_HIT_{row_number:07d}",
                        "file_path": file_path,
                        "file_kind": file_kind,
                        "match_type": item["match_type"],
                        "json_pointer_or_line_ref": item["json_pointer_or_line_ref"],
                        "matched_term_id": item["matched_term_id"],
                        "matched_term_text_or_regex": item["matched_term_text_or_regex"],
                        "matched_text_short": str(item["matched_text_short"])[:200],
                        "semantic_risk_level": item["severity"],
                        "term_family": item["term_family"],
                        "line_hits_capped_flag": False,
                        "structured_scan_status": "STRUCTURED_JSON_POINTER_SCAN",
                        "candidate_future_action": "NORMALIZE_OR_ROUTE_TO_RP5B",
                    }
                )
            continue

        for item in rows:
            if row_number >= MAX_TOTAL_LINE_HITS:
                break
            row_number += 1
            structured_status = (
                "STRUCTURED_SCAN_SKIPPED_SIZE_LIMIT"
                if structured_candidate and size > MAX_STRUCTURED_JSON_BYTES
                else "TEXT_LINE_SCAN_ONLY"
            )
            hit_rows.append(
                {
                    "row_id": f"RP5A_HIT_{row_number:07d}",
                    "file_path": file_path,
                    "file_kind": file_kind,
                    "match_type": _text_match_type(file_kind),
                    "json_pointer_or_line_ref": f"L{item['line_number']}",
                    "matched_term_id": item["matched_term_id"],
                    "matched_term_text_or_regex": item["matched_term_text_or_regex"],
                    "matched_text_short": str(item["text_short"])[:200],
                    "semantic_risk_level": item["severity"],
                    "term_family": item["term_family"],
                    "line_hits_capped_flag": bool(item.get("line_hits_capped_flag")),
                    "structured_scan_status": structured_status,
                    "candidate_future_action": "NORMALIZE_OR_ROUTE_TO_RP5B",
                }
            )
    LAST_ROW_FIELD_STATS.update(
        {
            "skipped_large_structured_file_count": len(set(skipped_large)),
            "skipped_large_structured_files_limited": sorted(set(skipped_large))[:50],
            "row_field_budget_exhausted_flag": row_number >= MAX_TOTAL_LINE_HITS,
            "row_field_rows_emitted": row_number,
        }
    )
    return hit_rows
