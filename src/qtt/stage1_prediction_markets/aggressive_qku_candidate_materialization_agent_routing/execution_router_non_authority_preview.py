"""Execution-router non-authority preview helpers."""

from __future__ import annotations


def execution_router_non_authority_previews(routes):
    return [
        {
            "qku_id": record["qku_id"],
            "route_ref": record["route_id"],
            "execution_router_preview_only_flag": True,
            "submit_cancel_reduce_close_order_allowed_flag": False,
            "live_order_authority": False,
        }
        for record in routes
    ]
