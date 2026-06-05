"""Paper market-state normalization for PR163."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


def selected_snapshot(orderbook_rows: list[dict[str, Any]], index: int) -> tuple[str, dict[str, Any]]:
    row_index = (index - 1) % len(orderbook_rows)
    return f"PR162R_B_ORDERBOOK_FIXTURE_SNAPSHOT::{row_index + 1:04d}", orderbook_rows[row_index]


def selected_latency(latency_rows: list[dict[str, Any]], index: int) -> dict[str, Any]:
    return latency_rows[(index - 1) % len(latency_rows)]


def build_market_state_normalization(
    index: int,
    candidate_packet_id: str,
    row_resolution: dict[str, Any],
    snapshot_ref: str,
    snapshot: dict[str, Any],
    venue_scope: str,
    lifecycle_state: str,
) -> dict[str, Any]:
    return {
        "market_state_normalization_ref": plain_ref("MARKET_STATE_NORMALIZATION", index),
        "candidate_packet_id": candidate_packet_id,
        "venue_scope": venue_scope,
        "market_scope": "BINARY_EVENT_MARKET_SYNTHETIC_REPRESENTATIVE",
        "synthetic_market_id": snapshot.get("market_id", "PR163_SYNTH_MARKET_001"),
        "synthetic_contract_or_token_id": "PR163_SYNTH_TOKEN_YES",
        "event_lifecycle_state": lifecycle_state,
        "selected_snapshot_ref": snapshot_ref,
        "best_bid": snapshot.get("best_bid"),
        "best_ask": snapshot.get("best_ask"),
        "bid_depth": snapshot.get("bid_depth"),
        "ask_depth": snapshot.get("ask_depth"),
        "tick_size": 0.01,
        "truth_status": "SYNTHETIC_OR_CANDIDATE_PAPER_CAPTURE",
        "pr162r_b_binding_refs": row_resolution.get("paper_binding_refs", []),
        "source_candidate_refs": row_resolution.get("source_candidate_refs", []),
        "validation_status": "PASS",
        **no_authority_fields(),
    }
