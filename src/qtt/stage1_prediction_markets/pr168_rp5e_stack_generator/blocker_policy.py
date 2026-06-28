"""Precise RP5E blocker policies."""

from __future__ import annotations

from .models import BLOCKER_CODES, generated_ref, with_common


def build_blocker_policy_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, code in enumerate(BLOCKER_CODES, start=1):
        rows.append(
            with_common(
                {
                    "blocker_code": code,
                    "blocker_scope": "ROW_OR_ARTIFACT_SPECIFIC",
                    "global_formula_ban_allowed_flag": False,
                    "global_qku_ban_allowed_flag": False,
                    "repair_route_allowed_flag": True,
                    "discard_weak_preview_allowed_flag": True,
                    "future_handoff_allowed_flag": True,
                    "broad_global_blocker_flag": False,
                },
                row_id=f"RP5E_BLOCKER_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=["RP5EValidator", "StackGeneratorAgent"],
                upstream_refs=["docs/master_plan/QTT_MasterPlan_Current.md"],
                downstream_refs=[generated_ref("qku_guard.jsonl"), generated_ref("run_receipt.report.json")],
            )
        )
    return rows
