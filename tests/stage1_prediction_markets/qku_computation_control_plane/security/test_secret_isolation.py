import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ReasonCode,
    SerializationSafetyError,
    SourcePolicyError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
    deterministic_json,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.source_rights import (
    SourceRightsV1,
    reject_secret_material,
)


def test_secret_and_credential_material_is_never_accepted() -> None:
    with pytest.raises(SerializationSafetyError) as caught:
        deterministic_json({"api_key": "forbidden"})
    assert caught.value.reason_code is ReasonCode.SECRET_MATERIAL_REJECTED
    with pytest.raises(SourcePolicyError):
        reject_secret_material("credential", "forbidden")
    with pytest.raises(SourcePolicyError):
        SourceRightsV1(
            "source-1",
            "PUBLIC_REFERENCE_ONLY",
            "METADATA_ONLY",
            True,
            secret_material_allowed=True,
        )
    with pytest.raises(SourcePolicyError):
        SourceRightsV1(
            "source-1",
            "PUBLIC_REFERENCE_ONLY",
            "METADATA_ONLY",
            False,
        )
