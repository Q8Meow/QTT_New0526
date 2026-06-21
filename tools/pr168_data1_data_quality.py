#!/usr/bin/env python3
"""Freshness and coverage audit rows for DATA1."""

from __future__ import annotations

from collections import Counter

from tools.pr168_data1_config import authority_flags, route_defaults


def build_quality_rows(snapshot_rows: list[dict[str, object]], l2_rows: list[dict[str, object]], feature_rows: list[dict[str, object]], now_utc: str) -> list[dict[str, object]]:
    by_venue = Counter(str(row.get("venue")) for row in snapshot_rows)
    l2_by_venue = Counter(str(row.get("venue")) for row in l2_rows)
    feature_by_venue = Counter(str(row.get("venue")) for row in feature_rows)
    rows = []
    for venue in sorted(set(by_venue) | set(l2_by_venue) | set(feature_by_venue)):
        rows.append(
            {
                "quality_row_id": f"quality_{venue}",
                "venue": venue,
                "snapshot_row_count": by_venue[venue],
                "forward_l2_row_count": l2_by_venue[venue],
                "feature_row_count": feature_by_venue[venue],
                "data_freshness_seconds": 0,
                "coverage_flags": [
                    "CURRENT_ORDERBOOK_PRESENT" if l2_by_venue[venue] else "CURRENT_ORDERBOOK_MISSING",
                    "COMPUTABLE_FEATURES_PRESENT" if feature_by_venue[venue] else "COMPUTABLE_FEATURES_MISSING",
                    "HISTORICAL_FULL_BOOK_GAP_ROUTED",
                ],
                "data_quality_score_non_proof": round(min(1.0, (by_venue[venue] + l2_by_venue[venue] + feature_by_venue[venue]) / 20.0), 4),
                "created_at_utc": now_utc,
                **route_defaults("governance"),
                **authority_flags(),
            }
        )
    return rows
