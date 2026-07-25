"""Source-rights, redaction, and secret-isolation metadata."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import ReasonCode, SourcePolicyError


@dataclass(frozen=True, slots=True)
class SourceRightsV1:
    source_state_id: str
    rights_and_use_state: str
    permitted_use_class: str
    public_documentation_reference_only: bool
    redistribution_authorized: bool = False
    secret_material_allowed: bool = False
    credential_material_allowed: bool = False

    def __post_init__(self) -> None:
        if (
            any(
                not isinstance(value, str) or not value
                for value in (
                    self.source_state_id,
                    self.rights_and_use_state,
                    self.permitted_use_class,
                )
            )
        ):
            raise SourcePolicyError(
                ReasonCode.INCOMPLETE_CONTRACT,
                "source-rights metadata is incomplete",
            )
        for name in (
            "public_documentation_reference_only",
            "redistribution_authorized",
            "secret_material_allowed",
            "credential_material_allowed",
        ):
            if type(getattr(self, name)) is not bool:
                raise SourcePolicyError(
                    ReasonCode.INVALID_CONTRACT,
                    f"{name} must be a boolean",
                )
        if (
            not self.public_documentation_reference_only
            or self.redistribution_authorized
            or self.secret_material_allowed
            or self.credential_material_allowed
        ):
            raise SourcePolicyError(
                ReasonCode.SOURCE_RIGHTS_BLOCKED,
                "Tranche A cannot infer redistribution rights or accept secrets",
            )


def reject_secret_material(field_name: str, value: object) -> None:
    if not isinstance(field_name, str) or not field_name:
        raise SourcePolicyError(
            ReasonCode.INVALID_CONTRACT,
            "secret-material field name must be nonempty text",
        )
    lowered = field_name.casefold()
    forbidden = (
        "api_key",
        "authorization",
        "cookie",
        "credential",
        "password",
        "private_key",
        "secret",
        "token",
        "wallet",
    )
    if any(token in lowered for token in forbidden) or value is not None:
        raise SourcePolicyError(
            ReasonCode.SECRET_MATERIAL_REJECTED,
            "secret or credential material is not accepted by Tranche A",
        )
