"""Explicit-only agent, role, and consumer-class binding for PR156."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c
from .io import as_list, text_or_none
from .models import AgentBindingContext, OptionalArtifactSet


def _stable_unique(values: list[str]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(value for value in values if value)))


def _text_values(record: Mapping[str, Any], keys: tuple[str, ...]) -> tuple[str, ...]:
    values: list[str] = []
    for key in keys:
        value = record.get(key)
        if isinstance(value, list):
            values.extend(str(item).strip() for item in value if str(item).strip())
        else:
            text = text_or_none(value)
            if text:
                values.append(text)
    return _stable_unique(values)


def _source_refs(record: Mapping[str, Any]) -> tuple[str, ...]:
    return _text_values(record, c.EXPLICIT_BINDING_SOURCE_REF_KEYS)


def _list_records(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    records: list[Mapping[str, Any]] = []
    for key in c.EXPLICIT_BINDING_RECORD_KEYS:
        for item in as_list(payload.get(key)):
            if isinstance(item, Mapping):
                records.append(item)
    return records


def load_agent_binding_context(optional: OptionalArtifactSet) -> AgentBindingContext:
    agent_map: dict[str, tuple[str, ...]] = {}
    role_map: dict[str, tuple[str, ...]] = {}
    consumer_map: dict[str, tuple[str, ...]] = {}

    consumed_paths = tuple(
        sorted(
            str(item["artifact_path"])
            for item in optional.consumed_artifacts
            if item.get("artifact_key") in c.AGENT_BINDING_OPTIONAL_KEYS
        )
    )

    for key in c.AGENT_BINDING_OPTIONAL_KEYS:
        payload = optional.artifacts.get(key, {})
        for record in _list_records(payload):
            refs = _source_refs(record)
            if not refs:
                continue
            agent_ids = _text_values(record, c.EXPLICIT_AGENT_ID_KEYS)
            roles = _text_values(record, c.EXPLICIT_ROLE_KEYS)
            consumers = _text_values(record, c.EXPLICIT_CONSUMER_CLASS_KEYS)
            for ref in refs:
                if agent_ids:
                    agent_map[ref] = _stable_unique([*agent_map.get(ref, ()), *agent_ids])
                if roles:
                    role_map[ref] = _stable_unique([*role_map.get(ref, ()), *roles])
                if consumers:
                    consumer_map[ref] = _stable_unique([*consumer_map.get(ref, ()), *consumers])

    return AgentBindingContext(
        consumed_artifact_paths=consumed_paths,
        explicit_agent_bindings_by_ref=agent_map,
        explicit_role_bindings_by_ref=role_map,
        explicit_consumer_class_bindings_by_ref=consumer_map,
    )


def binding_for_pr155_record(
    registry_record_id: str,
    context: AgentBindingContext,
) -> dict[str, Any]:
    agent_ids = list(context.explicit_agent_bindings_by_ref.get(registry_record_id, ()))
    roles = list(context.explicit_role_bindings_by_ref.get(registry_record_id, ()))
    consumers = list(
        context.explicit_consumer_class_bindings_by_ref.get(registry_record_id, ())
    )
    basis_artifacts = list(context.consumed_artifact_paths)

    if agent_ids:
        return {
            "agent_binding_state": c.AGENT_BOUND_NONLIVE_EXPLICIT,
            "bound_agent_ids": agent_ids,
            "bound_agent_roles": roles,
            "bound_consumer_classes": consumers,
            "binding_basis_artifacts": basis_artifacts,
            "binding_basis_reason": c.EXPLICIT_BINDING_MAP_REASON,
            "binding_block_codes": [],
        }
    if roles:
        return {
            "agent_binding_state": c.ROLE_BOUND_NONLIVE_EXPLICIT,
            "bound_agent_ids": [],
            "bound_agent_roles": roles,
            "bound_consumer_classes": consumers,
            "binding_basis_artifacts": basis_artifacts,
            "binding_basis_reason": c.EXPLICIT_BINDING_MAP_REASON,
            "binding_block_codes": [],
        }
    if consumers:
        return {
            "agent_binding_state": c.CONSUMER_CLASS_BOUND_NONLIVE_EXPLICIT,
            "bound_agent_ids": [],
            "bound_agent_roles": [],
            "bound_consumer_classes": consumers,
            "binding_basis_artifacts": basis_artifacts,
            "binding_basis_reason": c.EXPLICIT_BINDING_MAP_REASON,
            "binding_block_codes": [],
        }
    return {
        "agent_binding_state": c.BINDING_PENDING_EXPLICIT_AGENT_MAP_MISSING,
        "bound_agent_ids": [],
        "bound_agent_roles": [],
        "bound_consumer_classes": [],
        "binding_basis_artifacts": basis_artifacts,
        "binding_basis_reason": c.NO_EXPLICIT_BINDING_MAP_REASON,
        "binding_block_codes": [c.PR156_EXPLICIT_BINDING_MAP_MISSING],
    }
