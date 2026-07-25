import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.authority import (
    AuthenticationBindingV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    AuthorityDeniedError,
    ReasonCode,
)


def test_authentication_identities_are_complete_bound_and_distinct() -> None:
    binding = AuthenticationBindingV1(
        "principal-1",
        "session-1",
        "request-1",
        "trace-1",
        "idempotency-1",
    )
    assert binding.request_identity == "request-1"
    with pytest.raises(AuthorityDeniedError) as caught:
        AuthenticationBindingV1(
            "principal-1",
            "shared",
            "shared",
            "trace-1",
            "idempotency-1",
        )
    assert caught.value.reason_code is ReasonCode.INVALID_CONTRACT
