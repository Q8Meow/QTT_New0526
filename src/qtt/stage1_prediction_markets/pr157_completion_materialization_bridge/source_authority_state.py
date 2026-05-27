"""PR157 source-authority state helpers.

This module is intentionally classification-only. It never performs source retrieval
or source acceptance execution.
"""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def pr154_authority_class(record: Mapping[str, Any], source_population: str) -> str:
    if bool(record.get("materialization_allowed")):
        if source_population == c.SourcePopulation.PR154_INTERNAL_CONTROL_PLANE.value:
            return c.AuthorityClass.OWNER_INTERNAL_POLICY.value
        if source_population in {
            c.SourcePopulation.PR154_PUBLIC_EXTERNAL_CAPTURED.value,
            c.SourcePopulation.PR154_PUBLIC_EXTERNAL_RETRY.value,
        }:
            return c.AuthorityClass.EXISTING_ACCEPTED_SOURCE_EVIDENCE.value
        if source_population == c.SourcePopulation.PR154_OWNER_ROUTE.value:
            return c.AuthorityClass.OWNER_ROUTE_DECISION.value
        if source_population == c.SourcePopulation.PR154_PRIVATE_DOC_ATTESTATION.value:
            return c.AuthorityClass.OWNER_PRIVATE_DOC_ATTESTATION.value
        if source_population == c.SourcePopulation.PR154_SPLIT_RECLASSIFICATION.value:
            return c.AuthorityClass.DETERMINISTIC_SPLIT_RECLASSIFICATION.value
        return c.AuthorityClass.EXISTING_PR154_PR155_VALID_VALUE.value
    if source_population in {
        c.SourcePopulation.PR154_PUBLIC_EXTERNAL_CAPTURED.value,
        c.SourcePopulation.PR154_PUBLIC_EXTERNAL_RETRY.value,
    }:
        return c.AuthorityClass.MISSING_EXTERNAL_SOURCE_EVIDENCE.value
    if source_population == c.SourcePopulation.PR154_PRIVATE_DOC_ATTESTATION.value:
        return c.AuthorityClass.MISSING_PRIVATE_DOC_ATTESTATION.value
    return c.AuthorityClass.MISSING_OWNER_INPUT.value


def source_packet_ref(record: Mapping[str, Any]) -> str | None:
    path = record.get("materialized_value_source_path")
    key = record.get("materialized_value_source_record_key")
    if path and key:
        return f"{path}::{key}"
    return None


def source_locator(record: Mapping[str, Any]) -> Any:
    return record.get("quote_span_or_machine_field_locator") or record.get("official_source_locator")
