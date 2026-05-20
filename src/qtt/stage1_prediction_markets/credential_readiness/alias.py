from __future__ import annotations

import re
from typing import Any, Iterable, Mapping

from src.qtt.stage1_prediction_markets.credential_readiness import policy


TOKEN_SHAPE_PATTERNS = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"\b(?:sk|pk)_(?:live|test)_[A-Za-z0-9_]{8,}", re.IGNORECASE),
)

SECRET_KEY_PARTS = (
    "api_key",
    "apikey",
    "bearer",
    "oauth",
    "cookie",
    "session",
    "private_key",
    "privatekey",
    "wallet_secret",
    "walletsecret",
    "password",
    "recovery_phrase",
    "device_secret",
    "authorization",
    "signing_key",
)

ENV_LOOKUP_PREFIXES = ("ENV:", "$", "${")
LIVE_PROVIDER_PREFIXES = ("vault://", "aws-secrets://", "gcp-secrets://", "azure-keyvault://")


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")


def secret_like_findings(payload: Mapping[str, Any]) -> list[str]:
    findings: list[str] = []
    allowed_labels = set(policy.ALLOWED_REDACTED_SECRET_EXAMPLES)
    for path, value in _walk(payload):
        if isinstance(value, Mapping):
            for key in value:
                key_lower = str(key).lower()
                if any(part in key_lower for part in SECRET_KEY_PARTS):
                    findings.append(f"secret-like key at {path}.{key}")
        if isinstance(value, str):
            if value in allowed_labels:
                continue
            value_upper = value.upper()
            if value_upper.startswith(("RAW_SECRET_VALUE_", "UNREDACTED_SECRET_VALUE_")):
                findings.append(f"unredacted secret-like symbolic value at {path}")
            if value.startswith(ENV_LOOKUP_PREFIXES):
                findings.append(f"environment lookup value at {path}")
            if value.lower().startswith(LIVE_PROVIDER_PREFIXES):
                findings.append(f"live provider lookup value at {path}")
            if any(pattern.search(value) for pattern in TOKEN_SHAPE_PATTERNS):
                findings.append(f"token-shaped value at {path}")
    return findings


def _scope_field(scope_ref: policy.ScopeRef) -> dict[str, str]:
    return {scope_ref.field_name: scope_ref.value}


def credential_alias_id(scope_ref: policy.ScopeRef) -> str:
    return f"PR131_{scope_ref.value}_CREDENTIAL_ALIAS_REGISTRY_RECORD_V1"


def alias_placeholder_value(scope_ref: policy.ScopeRef) -> str:
    return f"PR131_{scope_ref.value}_SYMBOLIC_ALIAS_PLACEHOLDER_METADATA_ONLY"


def build_credential_alias_registry_records(
    private_state_handoff_ref: str,
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for scope_ref in policy.stage1_scope_refs():
        alias_class = policy.alias_class_for(scope_ref)
        records.append(
            {
                **policy.common_record_fields("CREDENTIAL_ALIAS_REGISTRY_RECORD"),
                "credential_alias_id": credential_alias_id(scope_ref),
                "alias_class": alias_class,
                **_scope_field(scope_ref),
                "credential_scope": (
                    "STAGE1_VENUE_CREDENTIAL_ALIAS_READINESS_METADATA_ONLY"
                    if scope_ref.scope_kind == "venue"
                    else "STAGE1_SHARED_TAXONOMY_CREDENTIAL_ALIAS_METADATA_ONLY"
                ),
                "alias_placeholder_value": alias_placeholder_value(scope_ref),
                "alias_value_is_secret": False,
                "alias_value_is_live_credential": False,
                "alias_value_is_production_authority": False,
                "alias_value_is_environment_lookup": False,
                "alias_value_is_provider_lookup": False,
                "owner_approval_required_for_live_resolution": True,
                "future_provider_ref_allowed": True,
                "future_provider_ref_metadata_only": True,
                "live_resolution_performed": False,
                "credential_provider_called": False,
                "network_io_created": False,
                "raw_secret_stored": False,
                "raw_secret_hash_created": False,
                "secret_like_payload_rejected_count": len(policy.SECRET_LIKE_REJECTION_CLASSES),
                "rejection_receipt_refs": [
                    f"PR131_SECRET_LIKE_REJECTION_{index:02d}_{rejection_class}"
                    for index, rejection_class in enumerate(
                        policy.SECRET_LIKE_REJECTION_CLASSES,
                        start=1,
                    )
                ],
                "downstream_handoff_ref": "PR131_CREDENTIAL_READINESS_DOWNSTREAM_HANDOFF_V1",
                "private_state_downstream_handoff_dependency_ref": private_state_handoff_ref,
            }
        )
    return records


def validate_alias_registry_records(records: list[Mapping[str, Any]]) -> list[str]:
    failures: list[str] = []
    expected_ids = {scope.value for scope in policy.stage1_scope_refs()}
    seen: set[str] = set()
    for record in records:
        scope_value = str(record.get("venue_id") or record.get("scope_id") or "")
        seen.add(scope_value)
        if scope_value not in expected_ids:
            failures.append(f"unexpected alias registry scope: {scope_value}")
        if record.get("alias_class") not in policy.ALLOWED_ALIAS_CLASSES:
            failures.append("alias registry record has unsupported alias class")
        if record.get("alias_placeholder_value") in {"", None}:
            failures.append("alias placeholder value is required")
        if secret_like_findings(record):
            failures.append("alias registry record contains secret-like payload")
        for flag in (
            "alias_value_is_secret",
            "alias_value_is_live_credential",
            "alias_value_is_production_authority",
            "alias_value_is_environment_lookup",
            "alias_value_is_provider_lookup",
            "live_resolution_performed",
            "credential_provider_called",
            "raw_secret_stored",
            "raw_secret_hash_created",
        ):
            if record.get(flag) is not False:
                failures.append(f"alias registry {flag} must be false")
    if seen != expected_ids:
        failures.append("alias registry must cover exactly three venues plus shared scope")
    if "PREDICTION_MARKETS_GENERAL" in {
        str(record.get("venue_id")) for record in records
    }:
        failures.append("PREDICTION_MARKETS_GENERAL must not be a venue_id")
    return failures
