from datetime import UTC, datetime, timedelta

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
    ComputationContextKeyV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    ReasonCode,
)


def test_context_computability_is_point_in_time_and_freshness_bound() -> None:
    context = ComputationContextKeyV1(
        "context-1",
        datetime(2026, 7, 24, 12, tzinfo=UTC),
        datetime(2026, 7, 24, 11, 59, tzinfo=UTC),
        "epoch-1",
        "input-v1",
        timedelta(minutes=5),
    )
    context.assert_fresh()
    assert context.stable_key.count("|") == 4

    stale = ComputationContextKeyV1(
        "context-2",
        datetime(2026, 7, 24, 12, tzinfo=UTC),
        datetime(2026, 7, 24, 11, tzinfo=UTC),
        "epoch-1",
        "input-v1",
        timedelta(minutes=5),
    )
    with pytest.raises(ContractValidationError) as caught:
        stale.assert_fresh()
    assert caught.value.reason_code is ReasonCode.STALE_CONTEXT
