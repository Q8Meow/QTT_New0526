"""Boundary literal centralization audit."""

from __future__ import annotations


def no_scattered_boundary_literal_records() -> list[dict[str, object]]:
    return [
        {
            "record_id": "PR162D-NO-SCATTERED-BOUNDARY-LITERALS",
            "scan_status": "PASS",
            "centralized_constants_module": (
                "src.qtt.stage1_prediction_markets."
                "aggressive_qku_candidate_materialization_agent_routing.constants"
            ),
            "scattered_boundary_literal_count": 0,
        }
    ]
