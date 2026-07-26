import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane import (
    serialization,
    source_rights,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ReasonCode,
    SerializationSafetyError,
    SourcePolicyError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
    deterministic_json,
    safe_json_loads,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.source_rights import (
    SourceRightsV1,
    reject_secret_material,
)


SECRET_KEYS = (
    "api key",
    "API-SECRET",
    "authorization",
    "Bearer.Token",
    "password",
    "pass_phrase",
    "access-token",
    "refresh/token",
    "SESSION TOKEN",
    "cookie",
    "credential",
    "private.key",
    "seed phrase",
    "wallet-secret",
)


def test_both_consumers_share_one_immutable_secret_policy() -> None:
    assert source_rights.SECRET_KEY_POLICY is serialization.SECRET_KEY_POLICY
    assert serialization.SECRET_KEY_POLICY.forbidden_normalized_terms == frozenset(
        serialization.SECRET_KEY_POLICY.forbidden_normalized_terms
    )
    with pytest.raises(AttributeError):
        serialization.SECRET_KEY_POLICY.forbidden_normalized_terms = frozenset()  # type: ignore[misc]


@pytest.mark.parametrize("field_name", SECRET_KEYS)
def test_normalized_secret_keys_are_rejected_without_echo(field_name: str) -> None:
    secret_value = "never-echo-this-value"
    with pytest.raises(SerializationSafetyError) as serialized:
        deterministic_json({field_name: secret_value})
    assert serialized.value.reason_code is ReasonCode.SECRET_MATERIAL_REJECTED
    assert secret_value not in str(serialized.value)
    with pytest.raises(SourcePolicyError) as source:
        reject_secret_material(
            "source_metadata",
            {"nested": [[{field_name: secret_value}]]},
        )
    assert source.value.reason_code is ReasonCode.SECRET_MATERIAL_REJECTED
    assert secret_value not in str(source.value)


def test_policy_avoids_declared_false_positives_and_recurses() -> None:
    allowed = {
        "token_count": 12,
        "token-budget": 30,
        "credential.state": "DENIED",
    }
    assert deterministic_json(allowed) == (
        '{"credential.state":"DENIED","token-budget":30,"token_count":12}'
    )
    assert safe_json_loads(deterministic_json(allowed)) == allowed
    reject_secret_material("source_metadata", {"nested": [[allowed]]})


@pytest.mark.parametrize(
    "scalar",
    ("text", b"bytes", 7, 0.25, True, None),
)
def test_source_secret_recursion_terminates_for_supported_scalar_leaves(
    scalar: object,
) -> None:
    reject_secret_material(
        "source_metadata",
        {"first": [["second", scalar]]},
    )


def test_source_secret_recursion_depth_is_bounded() -> None:
    nested: object = None
    for _depth in range(66):
        nested = [nested]
    with pytest.raises(SourcePolicyError) as raised:
        reject_secret_material("source_metadata", nested)
    assert raised.value.reason_code is ReasonCode.INVALID_CONTRACT


def test_source_rights_remain_public_reference_only() -> None:
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
