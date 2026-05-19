from __future__ import annotations

from tests.source_evidence.pr125_revalidation_scheduler_support import (
    materiality_by_event,
    snapshot,
)


def test_pr125_high_risk_strategy_cost_model_requires_owner_or_risk_review():
    event = materiality_by_event("EVENT_HIGH_RISK_STRATEGY_COST_MODEL")
    snap = snapshot()

    assert event["materiality_class"] == "HIGH_RISK"
    assert event["used_by_strategy_or_cost_model"] is True
    assert event["owner_or_risk_review_required"] is True
    assert event["source_change_materiality_event_id"] in snap[
        "owner_or_risk_review_required_ids"
    ]
