from __future__ import annotations

from tests.source_evidence.pr125_revalidation_scheduler_support import (
    materiality_by_event,
    snapshot,
)


def test_pr125_live_trading_blocking_marks_scope_no_new_or_increased_exposure():
    event = materiality_by_event("EVENT_LIVE_TRADING_BLOCKING_RATE_LIMIT")
    snap = snapshot()

    assert event["materiality_class"] == "LIVE_TRADING_BLOCKING"
    assert event["no_new_or_increased_exposure_required"] is True
    assert "FORECASTEX_IBKR_LIVE_EXPOSURE_SCOPE" in snap[
        "no_new_or_increased_exposure_scope_ids"
    ]
    assert snap["live_pretrade_use_allowed_flag"] is False
