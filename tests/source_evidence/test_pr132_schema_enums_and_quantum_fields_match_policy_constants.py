from __future__ import annotations

from collections.abc import Mapping
import json
import re
from typing import Any

from src.qtt.stage1_prediction_markets.market_data_ingest import policy
from tests.source_evidence.pr132_market_data_ingest_support import REPO_ROOT


def _contract_fields(
    schema: Mapping[str, Any],
    node: Mapping[str, Any],
) -> tuple[dict[str, Any], set[str]]:
    properties: dict[str, Any] = {}
    required: set[str] = set()

    reference = node.get("$ref")
    if reference is not None:
        assert isinstance(reference, str)
        prefix = "#/$defs/"
        assert reference.startswith(prefix)
        definitions = schema.get("$defs")
        assert isinstance(definitions, Mapping)
        definition = definitions.get(reference[len(prefix) :])
        assert isinstance(definition, Mapping)
        ref_properties, ref_required = _contract_fields(schema, definition)
        properties.update(ref_properties)
        required.update(ref_required)

    all_of = node.get("allOf", [])
    assert isinstance(all_of, list)
    for child in all_of:
        assert isinstance(child, Mapping)
        child_properties, child_required = _contract_fields(schema, child)
        properties.update(child_properties)
        required.update(child_required)

    node_properties = node.get("properties", {})
    assert isinstance(node_properties, Mapping)
    properties.update(dict(node_properties))

    node_required = node.get("required", [])
    assert isinstance(node_required, list)
    required.update(str(field) for field in node_required)
    return properties, required


def _effective_view(
    schema: Mapping[str, Any],
    branch: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], set[str]]:
    root_properties, root_required = _contract_fields(schema, schema)
    if branch is None:
        return root_properties, root_required

    branch_properties, branch_required = _contract_fields(schema, branch)
    effective_properties = dict(root_properties)
    effective_properties.update(branch_properties)
    return effective_properties, root_required | branch_required


def _legacy_and_v2_views(
    schema: Mapping[str, Any],
) -> tuple[
    tuple[dict[str, Any], set[str]],
    tuple[dict[str, Any], set[str]] | None,
]:
    branches = schema.get("oneOf")
    if branches is None:
        return _effective_view(schema, None), None

    assert isinstance(branches, list)
    assert len(branches) == 2

    legacy: list[Mapping[str, Any]] = []
    v2: list[Mapping[str, Any]] = []
    for branch in branches:
        assert isinstance(branch, Mapping)
        branch_properties, _ = _contract_fields(schema, branch)
        discriminator = branch_properties.get("schema_version")
        assert isinstance(discriminator, Mapping)
        discriminator_value = discriminator.get("const")
        assert isinstance(discriminator_value, str)

        if discriminator_value == policy.SCHEMA_VERSION:
            legacy.append(branch)
        else:
            assert re.fullmatch(r"PIT_[A-Z0-9_]+_V2", discriminator_value)
            v2.append(branch)

    assert len(legacy) == 1
    assert len(v2) == 1
    return _effective_view(schema, legacy[0]), _effective_view(schema, v2[0])


def _assert_enum_when_present(
    properties: Mapping[str, Any],
    field: str,
    expected: tuple[str, ...],
) -> None:
    field_schema = properties.get(field)
    if field_schema is None:
        return
    assert isinstance(field_schema, Mapping)
    assert tuple(field_schema["enum"]) == expected


def test_pr132_schema_enums_and_quantum_fields_match_policy_constants():
    schema_dir = REPO_ROOT / "src/qtt/stage1_prediction_markets/market_data_ingest"
    legacy_fields = frozenset(
        (
            *policy.QUANTUM_FORWARD_METADATA_FIELDS,
            *policy.QUANTUM_ZERO_AUTHORITY_FLAGS,
        )
    )

    for path in sorted(schema_dir.glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(schema, Mapping)
        (v1_properties, v1_required), v2_view = _legacy_and_v2_views(schema)

        assert legacy_fields.issubset(v1_properties)
        assert legacy_fields.issubset(v1_required)

        if v2_view is not None:
            _v2_properties, v2_required = v2_view
            assert legacy_fields.isdisjoint(v2_required)

        _assert_enum_when_present(
            v1_properties,
            "venue_id",
            policy.STAGE1_VENUE_IDS,
        )
        _assert_enum_when_present(
            v1_properties,
            "scope_id",
            policy.SHARED_SCOPE_IDS,
        )
        _assert_enum_when_present(
            v1_properties,
            "event_kind_class",
            policy.ALLOWED_CANONICAL_EVENT_KIND_CLASSES,
        )
        _assert_enum_when_present(
            v1_properties,
            "adapter_input_class",
            policy.ALLOWED_ADAPTER_INPUT_CLASSES,
        )
        _assert_enum_when_present(
            v1_properties,
            "dependency_state",
            policy.ALLOWED_SOURCE_DEPENDENCY_STATES,
        )
        _assert_enum_when_present(
            v1_properties,
            "rejected_reason_code",
            policy.REJECTION_REASON_CODES,
        )
