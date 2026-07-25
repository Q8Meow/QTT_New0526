from dataclasses import fields

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.authority import (
    Capability,
    CapabilityEnvelopeV1,
    TRANCHE_A_AUTHORITY,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    AuthorityDeniedError,
    ReasonCode,
)


def test_every_tranche_a_capability_defaults_to_deny() -> None:
    assert len(fields(TRANCHE_A_AUTHORITY)) == 10
    assert not any(
        getattr(TRANCHE_A_AUTHORITY, item.name)
        for item in fields(TRANCHE_A_AUTHORITY)
    )
    for capability in Capability:
        with pytest.raises(AuthorityDeniedError) as caught:
            TRANCHE_A_AUTHORITY.deny(capability)
        assert caught.value.reason_code is ReasonCode.CAPABILITY_DENIED
    with pytest.raises(AuthorityDeniedError) as caught:
        CapabilityEnvelopeV1(
            order_release_allowed=0,  # type: ignore[arg-type]
        )
    assert caught.value.reason_code is ReasonCode.INVALID_CONTRACT
