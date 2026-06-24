#!/usr/bin/env python3
"""Identity custody row builder for PR168-RP5A."""

from __future__ import annotations


def build_identity_custody_rows(matched_files: list[str], identity_occurrences: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    matched_set = set(matched_files)
    rows: list[dict[str, object]] = []
    for occurrence in sorted(identity_occurrences.values(), key=lambda item: (str(item["identity_type"]), str(item["identity_ref"]))):
        refs = sorted(str(ref) for ref in occurrence["file_refs"])
        matched_refs = [ref for ref in refs if ref in matched_set]
        if not matched_refs:
            continue
        reclaim_required = len(refs) == len(matched_refs)
        rows.append(
            {
                "row_id": f"RP5A_CUSTODY_{len(rows) + 1:07d}",
                "identity_ref": occurrence["identity_ref"],
                "identity_type": occurrence["identity_type"],
                "current_file_refs_limited": matched_refs[:25],
                "first_seen_file_or_pr_if_known": refs[0] if refs else None,
                "current_canonical_holder_if_any": None if reclaim_required else refs[0],
                "all_known_duplicate_refs_limited": refs[:25],
                "reclaim_required_flag": reclaim_required,
                "future_reclaim_pr": "PR168_RP5C_IMMUTABLE_LIBRARY" if reclaim_required else "PR168_RP5D_EXECUTABILITY_TIERS",
                "custody_risk": "HIGH" if reclaim_required else "MEDIUM",
            }
        )
    return rows
