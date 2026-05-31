"""Lightweight shared-dictionary hooks for PR161F compact shards."""

from __future__ import annotations

from collections import Counter
from typing import Any

from . import constants as c


COMPACT_RECORD_VERSION = "PR161F_COMPACT_CANONICAL_RECORD_V1"
SHARED_DICTIONARY_VERSION = "PR161F_SHARED_DICTIONARY_V1"

COMPACTED_REPORT_FILENAMES = frozenset(
    {
        "PR161F_ExecutorInputRegistry.report.json",
        "PR161F_ReplayRunRequestRegistry.report.json",
        "PR161F_PaperRunRequestRegistry.report.json",
        "PR161F_PairedReplayPaperRunPlan.report.json",
        "PR161F_RunArtifactEnvelopeRegistry.report.json",
        "PR161F_ResultPacketEmissionEligibilityGate.report.json",
        "PR161F_QuantumClassicalHybridRunPlan.report.json",
        "PR161F_AtomicRowsPR154RunCompatibilityBridge.report.json",
        "PR161F_AgentRunTaskQueue.report.json",
        "PR161F_OwnerReviewRunReadinessQueue.report.json",
        "PR161F_QKUEndToEndTraceabilityMatrix.report.json",
        "PR161F_QKUGraphTraceabilityBridge.report.json",
    }
)


def build_shared_dictionary(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    compacted = sorted(name for name in COMPACTED_REPORT_FILENAMES if name in payloads)
    role_counts: dict[str, int] = {}
    field_names: set[str] = set()
    string_counts: Counter[str] = Counter()
    for payload in payloads.values():
        for record in payload.get("records") or []:
            role = record.get("agent_role_id") or record.get("assigned_agent_role")
            if role:
                role_counts[str(role)] = role_counts.get(str(role), 0) + 1
            if payload.get("report_filename") in COMPACTED_REPORT_FILENAMES or payload.get("report_type"):
                _collect_compact_terms(record, field_names, string_counts)
    field_alias_by_field = {
        field: _field_alias(index)
        for index, field in enumerate(sorted(field_names), start=1)
    }
    strings = [
        value
        for value, count in sorted(string_counts.items())
        if count > 1 and len(value) >= 8
    ]
    return {
        "dictionary_version": SHARED_DICTIONARY_VERSION,
        "compact_record_version": COMPACT_RECORD_VERSION,
        "compacted_report_filenames": compacted,
        "schema_refs": dict(c.REPORT_SCHEMA_REFS),
        "owner_approvals": dict(c.OWNER_APPROVALS),
        "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
        "agent_roles": list(c.AGENT_ROLES),
        "agent_role_counts_observed_in_compacted_records": {
            key: role_counts[key] for key in sorted(role_counts)
        },
        "compact_field_alias_by_field": field_alias_by_field,
        "compact_field_by_alias": {
            alias: field for field, alias in field_alias_by_field.items()
        },
        "compact_string_values": strings,
        "qku_trace_index_count": c.EXPECTED_PR161C_COUNTS["primary_qku_count"],
        "no_binary_compression_flag": True,
        "external_storage_used_flag": False,
        "qtt_sha_or_checksum_authority_created_flag": False,
        "atomicrows_bundle_sha_hash_freeze_authority_created_flag": False,
    }


def compact_records_for_report(
    records: list[dict[str, Any]],
    filename: str,
    schema_ref: str | None,
    shared_dictionary: dict[str, Any],
) -> list[dict[str, Any]]:
    del filename, schema_ref
    field_alias_by_field = dict(shared_dictionary.get("compact_field_alias_by_field") or {})
    string_index_by_value = {
        value: index
        for index, value in enumerate(shared_dictionary.get("compact_string_values") or [])
        if isinstance(value, str)
    }
    return [
        _encode_compact_value(record, field_alias_by_field, string_index_by_value)
        for record in records
    ]


def hoist_compact_record_defaults(
    records: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not records:
        return {}, []
    defaults: dict[str, Any] = {}
    for field in (
        "pr_label",
        "authority_class",
        "result_state",
        "evidence_state",
        "result_packet_emission_eligibility_state",
    ):
        first = records[0].get(field)
        if first is not None and all(record.get(field) == first for record in records):
            defaults[field] = first
    compacted = [
        {field: value for field, value in record.items() if field not in defaults}
        for record in records
    ]
    return defaults, compacted


def expand_payload_records(
    payload: dict[str, Any],
    shared_dictionary: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    shared_dictionary = shared_dictionary or {}
    defaults = dict(payload.get("compact_record_defaults") or {})
    field_by_alias = dict(shared_dictionary.get("compact_field_by_alias") or {})
    strings = list(shared_dictionary.get("compact_string_values") or [])
    return [
        {
            **_decode_compact_value(defaults, field_by_alias, strings),
            **_decode_compact_value(record, field_by_alias, strings),
        }
        for record in payload.get("records") or []
        if isinstance(record, dict)
    ]


def _field_alias(index: int) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    base = len(alphabet)
    value = index - 1
    chars = []
    while True:
        chars.append(alphabet[value % base])
        value //= base
        if value == 0:
            break
    return "".join(reversed(chars))


def _collect_compact_terms(value: Any, field_names: set[str], string_counts: Counter[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str):
                field_names.add(key)
            _collect_compact_terms(item, field_names, string_counts)
        return
    if isinstance(value, list):
        for item in value:
            _collect_compact_terms(item, field_names, string_counts)
        return
    if isinstance(value, str):
        string_counts[value] += 1


def _encode_compact_value(
    value: Any,
    field_alias_by_field: dict[str, str],
    string_index_by_value: dict[str, int],
) -> Any:
    if isinstance(value, dict):
        return {
            field_alias_by_field.get(key, key): _encode_compact_value(
                item,
                field_alias_by_field,
                string_index_by_value,
            )
            for key, item in value.items()
            if isinstance(key, str)
        }
    if isinstance(value, list):
        if value and all(isinstance(item, str) and item in string_index_by_value for item in value):
            return {"$l": [string_index_by_value[item] for item in value]}
        return [
            _encode_compact_value(item, field_alias_by_field, string_index_by_value)
            for item in value
        ]
    if isinstance(value, str) and value in string_index_by_value:
        return {"$s": string_index_by_value[value]}
    return value


def _decode_compact_value(
    value: Any,
    field_by_alias: dict[str, str],
    strings: list[Any],
) -> Any:
    if isinstance(value, dict):
        if set(value) == {"$s"}:
            return strings[int(value["$s"])]
        if set(value) == {"$l"}:
            return [strings[int(index)] for index in value["$l"]]
        return {
            field_by_alias.get(key, key): _decode_compact_value(item, field_by_alias, strings)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_decode_compact_value(item, field_by_alias, strings) for item in value]
    return value
