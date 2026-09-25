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
    """Expand JSON-native compact records without coercion or silent row loss.

    Absent/null optional containers retain their empty-container behavior.
    A record overrides a default field; two keys in the same object must not
    decode to the same field. Mutable defaults are decoded afresh per record.
    This codec does not admit a source generation or authorize its use.
    """
    if type(payload) is not dict:
        raise TypeError("compact payload must be a JSON object")
    if shared_dictionary is None:
        shared_dictionary = {}
    if type(shared_dictionary) is not dict:
        raise TypeError("shared dictionary must be a JSON object or None")
    defaults = payload.get("compact_record_defaults")
    defaults = {} if defaults is None else defaults
    aliases = shared_dictionary.get("compact_field_by_alias")
    aliases = {} if aliases is None else aliases
    strings = shared_dictionary.get("compact_string_values")
    strings = [] if strings is None else strings
    records = payload.get("records")
    records = [] if records is None else records
    if type(defaults) is not dict or type(aliases) is not dict:
        raise TypeError("compact defaults and field aliases must be JSON objects")
    if type(strings) is not list or any(type(item) is not str for item in strings):
        raise TypeError("compact string values must be a JSON array of strings")
    if type(records) is not list:
        raise TypeError("compact records must be a JSON array")
    if any(type(alias) is not str or type(field) is not str
           for alias, field in aliases.items()):
        raise TypeError("compact field aliases must map strings to strings")
    if len(set(aliases.values())) != len(aliases):
        raise ValueError("compact field aliases must be one-to-one")
    field_by_alias = dict(aliases)
    strings = list(strings)
    expanded: list[dict[str, Any]] = []
    for record in records:
        if type(record) is not dict:
            raise TypeError("every compact record must be a JSON object")
        decoded_defaults = _decode_compact_value(defaults, field_by_alias, strings)
        decoded_record = _decode_compact_value(record, field_by_alias, strings)
        if type(decoded_defaults) is not dict or type(decoded_record) is not dict:
            raise TypeError("compact defaults and records must decode to JSON objects")
        expanded.append({**decoded_defaults, **decoded_record})
    return expanded


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


def _compact_string_at(index: Any, strings: list[Any]) -> str:
    """Read only a producer-domain string-table index; never coerce it."""
    if type(index) is not int:
        raise TypeError("compact string index must be a JSON integer, not a boolean")
    if index < 0 or index >= len(strings):
        raise IndexError("compact string index is outside the string table")
    value = strings[index]
    if type(value) is not str:
        raise TypeError("compact string-table entry must be a string")
    return value


def _decode_compact_value(
    value: Any,
    field_by_alias: dict[str, str],
    strings: list[Any],
) -> Any:
    if isinstance(value, dict):
        if set(value) == {"$s"}:
            return _compact_string_at(value["$s"], strings)
        if set(value) == {"$l"}:
            indexes = value["$l"]
            if type(indexes) is not list:
                raise TypeError("compact string-list indices must be a JSON array")
            return [_compact_string_at(index, strings) for index in indexes]
        decoded: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError("compact object keys must be strings")
            field = field_by_alias.get(key, key)
            if type(field) is not str:
                raise TypeError("decoded compact field must be a string")
            if field in decoded:
                raise ValueError("compact object keys decode to the same field")
            decoded[field] = _decode_compact_value(item, field_by_alias, strings)
        return decoded
    if isinstance(value, list):
        return [_decode_compact_value(item, field_by_alias, strings) for item in value]
    return value
