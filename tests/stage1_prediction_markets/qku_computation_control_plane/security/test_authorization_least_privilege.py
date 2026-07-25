import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.authority import (
    Capability,
    CapabilityRequirementV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    AuthorityDeniedError,
)


def test_capability_requirements_are_exact_and_never_granted() -> None:
    requirement = CapabilityRequirementV1(
        "principal-1",
        "describe-contract",
        (Capability.PROVIDER_CONNECTION,),
    )
    assert not requirement.granted
    with pytest.raises(AuthorityDeniedError):
        CapabilityRequirementV1(
            "principal-1",
            "describe-contract",
            (Capability.PROVIDER_CONNECTION,),
            direct_provider_authority=True,
        )
    with pytest.raises(AuthorityDeniedError):
        CapabilityRequirementV1(
            "principal-1",
            "describe-contract",
            (Capability.ORDER_RELEASE,),
            granted=True,
        )
