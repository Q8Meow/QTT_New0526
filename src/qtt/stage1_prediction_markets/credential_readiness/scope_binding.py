from __future__ import annotations

from typing import Any, Mapping

from src.qtt.stage1_prediction_markets.credential_readiness import policy


def _scope_field(record: Mapping[str, Any]) -> dict[str, str]:
    if record.get("venue_id"):
        return {"venue_id": str(record["venue_id"])}
    return {"scope_id": str(record["scope_id"])}


def build_scope_bindings(
    alias_records: list[Mapping[str, Any]],
) -> list[dict[str, object]]:
    bindings: list[dict[str, object]] = []
    for record in alias_records:
        alias_id = str(record["credential_alias_id"])
        scope_value = str(record.get("venue_id") or record.get("scope_id"))
        bindings.append(
            {
                **policy.common_record_fields("CREDENTIAL_SCOPE_BINDING"),
                "binding_id": f"PR131_{scope_value}_CREDENTIAL_SCOPE_BINDING_V1",
                **_scope_field(record),
                "alias_registry_ref": alias_id,
                "credential_scope_class": str(record["credential_scope"]),
                "allowed_use": "READINESS_METADATA_ONLY",
                "disallowed_use": list(policy.DISALLOWED_SCOPE_USES),
                "downstream_consumer_scope": "PR114_PR115_PR116_METADATA_HANDOFF_ONLY",
                "live_use_requires_future_owner_approval": True,
                "live_use_requires_future_credential_provider_receipt": True,
                "live_use_requires_future_connector_receipt": True,
                "live_use_requires_future_source_evidence_clearance": True,
            }
        )
    return bindings


def validate_scope_bindings(bindings: list[Mapping[str, Any]]) -> list[str]:
    failures: list[str] = []
    seen = {record.get("venue_id") or record.get("scope_id") for record in bindings}
    expected = set(policy.STAGE1_VENUE_IDS) | set(policy.SHARED_SCOPE_IDS)
    if seen != expected:
        failures.append("scope bindings must cover exactly three venues plus shared scope")
    if "PREDICTION_MARKETS_GENERAL" in {
        str(record.get("venue_id")) for record in bindings
    }:
        failures.append("shared scope must not be represented as venue_id")
    for binding in bindings:
        if binding.get("allowed_use") != "READINESS_METADATA_ONLY":
            failures.append("scope binding allowed_use must be metadata only")
        if tuple(binding.get("disallowed_use", [])) != policy.DISALLOWED_SCOPE_USES:
            failures.append("scope binding disallowed_use must mirror centralized policy")
        for flag in (
            "live_use_requires_future_owner_approval",
            "live_use_requires_future_credential_provider_receipt",
            "live_use_requires_future_connector_receipt",
            "live_use_requires_future_source_evidence_clearance",
        ):
            if binding.get(flag) is not True:
                failures.append(f"scope binding {flag} must be true")
    return failures
