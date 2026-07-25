import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    HealthEnvelopeV1,
    HealthState,
)


def test_health_is_a_read_only_contract_not_process_proof() -> None:
    health = HealthEnvelopeV1(
        "qku-control-plane",
        HealthState.HEALTHY_CONTRACT,
        ("STATIC_CONTRACT_VALIDATED",),
    )
    assert health.state is HealthState.HEALTHY_CONTRACT
    assert not health.starts_process
    with pytest.raises(ContractValidationError):
        HealthEnvelopeV1(
            "qku-control-plane",
            HealthState.HEALTHY_CONTRACT,
            starts_process=True,
        )
