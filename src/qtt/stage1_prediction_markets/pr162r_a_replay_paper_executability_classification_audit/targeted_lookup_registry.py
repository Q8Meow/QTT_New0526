"""Targeted lookup registry.

PR162R-A did not need online lookup because PR162D-R1 source-backed records were
sufficient for classification and local micro-materialization.
"""

from __future__ import annotations

from typing import Any


def targeted_lookup_records() -> list[dict[str, Any]]:
    return [
        {
            "lookup_registry_id": "PR162R_A_TARGETED_LOOKUP_REGISTRY",
            "targeted_lookup_performed_count": 0,
            "reason": "PR162D_R1_SOURCE_BACKED_INPUTS_SUFFICIENT",
            "no_live_order_authority": True,
            "live_order_authority": False,
        }
    ]
