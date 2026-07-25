from datetime import UTC, datetime

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ReasonCode,
    SourcePolicyError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.source_policy import (
    TradeLifecycleClass,
    classify_trade_lifecycle,
    validate_effective_epoch,
)


def test_future_source_epoch_is_excluded_until_effective() -> None:
    with pytest.raises(SourcePolicyError) as caught:
        validate_effective_epoch(
            "ST10-SOURCE::12",
            as_of=datetime(2026, 6, 30, tzinfo=UTC),
        )
    assert caught.value.reason_code is ReasonCode.SOURCE_EPOCH_STALE
    current = validate_effective_epoch(
        "ST10-SOURCE::12",
        as_of=datetime(2026, 7, 2, tzinfo=UTC),
    )
    assert current.effective_from == "2026-07-01T04:00:00Z"
    with pytest.raises(SourcePolicyError):
        validate_effective_epoch(
            "ST10-SOURCE::12",
            as_of=datetime(2026, 7, 2),
        )
    assert (
        classify_trade_lifecycle("RETRYING")
        is TradeLifecycleClass.PENDING
    )
    with pytest.raises(SourcePolicyError) as caught:
        classify_trade_lifecycle("UNKNOWN")
    assert caught.value.reason_code is ReasonCode.UNKNOWN_LIFECYCLE_STATE
