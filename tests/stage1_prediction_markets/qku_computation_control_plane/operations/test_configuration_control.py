from dataclasses import FrozenInstanceError

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    ParameterPolicyError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    ConfigurationEnvelopeV1,
)


def test_configuration_is_versioned_immutable_and_not_runtime_mutable() -> None:
    configuration = ConfigurationEnvelopeV1(
        "configuration-1",
        "1.0",
        ("ST10-PARAM::0083",),
    )
    with pytest.raises(FrozenInstanceError):
        configuration.version = "2.0"  # type: ignore[misc]
    with pytest.raises(ContractValidationError) as caught:
        ConfigurationEnvelopeV1("configuration-2", "1.0", (), True)
    assert caught.value.reason_code is ReasonCode.RUNTIME_EFFECT_FORBIDDEN
    with pytest.raises(ParameterPolicyError):
        ConfigurationEnvelopeV1(
            "configuration-3",
            "1.0",
            ("NONEXISTENT-PARAMETER",),
        )
