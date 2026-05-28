"""Master-plan authority flags for PR158."""

from __future__ import annotations

from . import constants as c


MASTER_PLAN_BASIS_REFS = (
    c.MASTER_PLAN_PATH.as_posix(),
    "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md",
)


def owner_editability_lifecycle(value_type: str, unit_or_basis: str, scale: str) -> dict[str, object]:
    return {
        "owner_dashboard_editable_flag": True,
        "owner_value_change_allowed_flag": True,
        "owner_value_change_scope": "QTT_INTERNAL_POLICY_METADATA_ONLY",
        "owner_value_type": value_type,
        "allowed_owner_value_range_or_enum": "OWNER_POLICY_CLASS_ONLY_NO_NUMERIC_RANGE_INVENTED",
        "owner_value_unit_or_basis": unit_or_basis,
        "owner_value_scale": scale,
        "factual_external_value_flag": False,
        "external_fact_override_forbidden_flag": True,
        "owner_policy_assumption_allowed_for_replay_paper_flag": True,
        "owner_policy_assumption_live_blocked_until_gates_flag": True,
        "owner_change_requires_policy_snapshot_flag": True,
        "owner_change_requires_replay_flag": True,
        "owner_change_requires_paper_flag": True,
        "owner_change_allows_shadow_after_gates_flag": True,
        "owner_change_requires_dual_result_review_flag": True,
        "owner_change_requires_owner_promotion_review_flag": True,
        "owner_change_blocks_live_until_review_flag": True,
        "open_orders_unchanged_by_value_change_flag": True,
        "open_positions_unchanged_by_value_change_flag": True,
        "exact_retest_route": c.FutureRoute.REPLAY_AFTER_FUTURE_GATES.value,
        "future_dashboard_control_ref": "PR158_FUTURE_OWNER_DASHBOARD_CONTROL_METADATA_ONLY",
        "future_replay_paper_route": c.FutureRoute.REPLAY_AFTER_FUTURE_GATES.value,
        "future_shadow_route": "FUTURE_SHADOW_AFTER_LIVE_ADJACENT_GATES",
        "future_live_promotion_route": c.FutureRoute.LIVE_ONLY_AFTER_ALL_FUTURE_GATES.value,
    }

