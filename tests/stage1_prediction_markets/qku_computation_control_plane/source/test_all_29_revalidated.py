from datetime import UTC, datetime

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    SourcePolicyError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.source_policy import (
    CERTIFIED_SOURCE_STATES,
    FAK_FOK_RESPONSE_CONTRACT,
    POLYMARKET_ENDPOINT_LIMITS,
    POLYMARKET_SIGNER_BUCKETS,
    SOURCE_CURRENTIZATION_OVERLAYS,
    SourceRevalidationSchedulerAdapterV1,
)


def test_all_29_certified_source_states_are_terminally_materialized() -> None:
    assert len(CERTIFIED_SOURCE_STATES) == 29
    assert len({row.source_state_id for row in CERTIFIED_SOURCE_STATES}) == 29
    assert all(
        row.research_completeness_state
        == "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING"
        for row in CERTIFIED_SOURCE_STATES
    )
    assert len(SOURCE_CURRENTIZATION_OVERLAYS) == 7
    assert {
        row.method_and_path: (
            row.burst_requests,
            row.burst_window_seconds,
            row.sustained_requests,
            row.sustained_window_seconds,
            row.scope,
        )
        for row in POLYMARKET_ENDPOINT_LIMITS
    } == {
        "DELETE /cancel-all": (250, 10, 6000, 600, "CLOUDFLARE_IP"),
        "DELETE /cancel-market-orders": (
            1500,
            10,
            21000,
            600,
            "CLOUDFLARE_IP",
        ),
        "DELETE /order": (5000, 10, 120000, 600, "CLOUDFLARE_IP"),
        "DELETE /orders": (2000, 10, 15000, 600, "CLOUDFLARE_IP"),
        "POST /order": (5000, 10, 120000, 600, "CLOUDFLARE_IP"),
        "POST /orders": (2000, 10, 21000, 600, "CLOUDFLARE_IP"),
    }
    assert {
        row.warning_mode_duration for row in POLYMARKET_SIGNER_BUCKETS
    } == {"two weeks; live enforcement date to be announced"}
    effective = datetime(2026, 7, 24, 4, tzinfo=UTC)
    assert FAK_FOK_RESPONSE_CONTRACT.successful_field_at(effective) == "tradeIDs"
    with pytest.raises(SourcePolicyError):
        FAK_FOK_RESPONSE_CONTRACT.successful_field_at(
            datetime(2026, 7, 24, 3, 59, tzinfo=UTC)
        )
    scheduler = SourceRevalidationSchedulerAdapterV1.load_view()
    assert set(scheduler.live_critical_field_classes).isdisjoint(
        scheduler.low_risk_field_classes
    )
    assert not scheduler.network_retrieval_allowed
    assert not any(
        row.provider_connection_or_effect_authorized
        or row.runtime_online_research_allowed
        or row.codex_online_research_allowed
        for row in CERTIFIED_SOURCE_STATES
    )
