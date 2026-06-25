#!/usr/bin/env python3
"""Targeted identity preservation rows for RP5B deletion-selected artifacts."""

from __future__ import annotations

from typing import Any

from tools.pr168_rp5b_config import DELETE_ACTIONS


def build_identity_preservation_rows(
    verification_rows: list[dict[str, Any]],
    identity_custody_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    custody_by_file: dict[str, list[dict[str, Any]]] = {}
    for row in identity_custody_rows:
        for path in row.get("current_file_refs_limited", []) or []:
            custody_by_file.setdefault(str(path), []).append(row)
    rows: list[dict[str, Any]] = []
    for verification in verification_rows:
        if verification.get("final_action") not in DELETE_ACTIONS:
            continue
        if not verification.get("contains_unique_qku_formula_identity_now_flag"):
            continue
        for identity in custody_by_file.get(str(verification["file_path"]), []):
            rows.append(
                {
                    "row_id": f"RP5B_IDENTITY_PRESERVE_{len(rows) + 1:07d}",
                    "source_file_path": verification["file_path"],
                    "identity_type": identity.get("identity_type", "UNKNOWN"),
                    "identity_ref": identity.get("identity_ref", "UNKNOWN"),
                    "identity_json_path_or_line": "RP5A_IDENTITY_CUSTODY_GRAPH",
                    "preservation_scope": "TARGETED_DELETION_SAFETY_ONLY",
                    "future_canonical_reclaim_pr": "PR168_RP5C",
                    "preserved_in_rp5b_flag": True,
                    "replacement_ref": "docs/master_plan/generated/rp5b/qku_formula_identity_preservation_rows.jsonl",
                }
            )
    return rows
