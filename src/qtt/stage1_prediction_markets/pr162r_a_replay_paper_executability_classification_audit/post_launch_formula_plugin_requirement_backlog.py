"""Post-launch formula plugin requirement backlog."""

from __future__ import annotations

from typing import Any


POST_LAUNCH_REQUIREMENTS = (
    "plugin_registration_contract",
    "plugin_schema_validation",
    "plugin_latency_budget_snapshot",
    "plugin_owner_intake_review",
    "plugin_version_rollback_plan",
)


def post_launch_requirement_records() -> list[dict[str, Any]]:
    return [
        {
            "requirement_id": f"PR162R_A_POST_LAUNCH_FORMULA_PLUGIN::{name}",
            "requirement_name": name,
            "target_pr": "POST_LAUNCH_FORMULA_PLUGIN_BACKLOG",
            "future_scope_only_flag": True,
            "live_order_authority": False,
        }
        for name in POST_LAUNCH_REQUIREMENTS
    ]
