import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    SupervisionEnvelopeV1,
)


def test_supervision_surface_has_no_process_effect() -> None:
    envelope = SupervisionEnvelopeV1(
        "supervision-contract-1",
        ("qku-control-plane",),
    )
    assert not envelope.process_supervision_enabled
    with pytest.raises(ContractValidationError) as caught:
        SupervisionEnvelopeV1(
            "supervision-contract-2",
            ("qku-control-plane",),
            process_supervision_enabled=True,
        )
    assert caught.value.reason_code is ReasonCode.RUNTIME_EFFECT_FORBIDDEN
