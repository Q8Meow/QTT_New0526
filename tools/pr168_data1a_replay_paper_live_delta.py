#!/usr/bin/env python3
"""Replay/paper/live readiness delta for PR168-DATA1A."""

from __future__ import annotations

from typing import Any

from tools.pr168_data1a_config import generated_ref, report_path, route_defaults


def build_replay_paper_live_delta(
    quality_rows: list[dict[str, Any]],
    historical_summary: dict[str, Any],
    created_at_utc: str,
) -> dict[str, Any]:
    replay_ready = sum(1 for row in quality_rows if row["RP2_replay_paper_ready_flag"])
    paper_ready = sum(1 for row in quality_rows if row["GFP2R_candidate_compute_ready_flag"])
    live_gap_count = len(quality_rows)
    return {
        "replay_paper_live_delta_id": "pr168_data1a_replay_paper_live_readiness_delta",
        "replay_candidate_ready_now": replay_ready,
        "paper_candidate_ready_now": paper_ready,
        "source_acceptance_required_before_real_proof": len(quality_rows),
        "live_hot_path_data_gap": live_gap_count,
        "live_hot_path_data_gap_count": live_gap_count,
        "live_not_authorized_by_DATA1A": True,
        "replay_candidate_ready_count": replay_ready,
        "paper_candidate_ready_count": paper_ready,
        "historical_full_book_gap_flag": historical_summary["historical_full_book_verified_public_rows_count"] == 0,
        "live_authority_created_flag": False,
        "order_authority_created_flag": False,
        "created_at_utc": created_at_utc,
        **route_defaults("governance", data1_refs=[generated_ref(report_path("PR168_DATA1_PR168_RP2_FirstReplayPaperRecomputeBatch"))]),
    }
