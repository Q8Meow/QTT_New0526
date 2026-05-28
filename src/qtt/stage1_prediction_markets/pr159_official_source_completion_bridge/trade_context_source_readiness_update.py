"""Trade-context source readiness metadata for PR159."""

from __future__ import annotations

from typing import Any, Mapping


def build_trade_context_updates(records: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "row_id": record["row_id"],
            "trade_context_source_ready_flag": record["accepted_source_packet_ref_or_null"] is not None,
            "metadata_only_no_selection_execution": True,
            "selection_execution_created": False,
            "replay_execution_created": False,
            "paper_execution_created": False,
            "live_order_authority_created": False,
        }
        for record in sorted(records, key=lambda item: item["row_id"])
    ]

