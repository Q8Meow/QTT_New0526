import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.authority import (
    CapabilityEnvelopeV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    AuthorityDeniedError,
    ReasonCode,
)


def test_control_plane_cannot_absorb_effect_authority() -> None:
    with pytest.raises(AuthorityDeniedError) as caught:
        CapabilityEnvelopeV1(order_release_allowed=True)
    assert caught.value.reason_code is ReasonCode.CAPABILITY_DENIED
