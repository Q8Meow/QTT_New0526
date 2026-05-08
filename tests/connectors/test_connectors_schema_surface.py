import json
from pathlib import Path


SCHEMA_PATH = Path("schemas/connectors/source_required_placeholders.schema.json")
CAPABILITY_SCHEMA_PATH = Path(
    "schemas/connectors/connector_capability_registry.schema.json"
)
GUARDRAIL_FIELDS = {
    "connector_semantic_binding_allowed",
    "live_connector_allowed",
    "api_key_required_or_allowed",
    "source_acceptance_execution_allowed",
    "private_state_fetch_allowed",
    "order_execution_allowed",
    "runtime_cash_fetch_allowed",
    "profit_claim_allowed",
}
CAPABILITY_SURFACE_DEFS = {
    "connector_authority_scope_flags",
    "connector_forbidden_action_flags",
    "connector_source_required_field_placeholders",
    "connector_capability_card",
    "connector_readiness_record",
    "connector_capability_registry",
    "no_claim_flags",
}


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _capability_schema() -> dict:
    return json.loads(CAPABILITY_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_connectors_schema_surface_is_source_required_and_disabled():
    schema = _schema()
    properties = schema["properties"]

    assert properties["mode"]["const"] == "SOURCE_REQUIRED"
    assert properties["execution"]["const"] == "DISABLED"
    assert properties["schema_authority_class"]["const"] == (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_CONNECTOR_AUTHORITY"
    )
    assert properties["surface_kind"]["const"] == "CONNECTOR_SOURCE_REQUIRED_PLACEHOLDER"


def test_connectors_schema_requires_disabled_guardrails():
    schema = _schema()
    properties = schema["properties"]
    required = set(schema["required"])

    assert GUARDRAIL_FIELDS.issubset(required)
    assert all(properties[field]["const"] is False for field in GUARDRAIL_FIELDS)


def test_connectors_schema_does_not_define_runtime_connector_authority():
    schema = _schema()

    assert schema["additionalProperties"] is True
    assert "connector_binding_authority" not in schema["properties"]
    assert "runtime_authority" not in schema["properties"]
    assert "order_execution_authority" not in schema["properties"]


def test_connector_capability_registry_schema_surface_is_static_source_required():
    schema = _capability_schema()
    properties = schema["properties"]

    assert properties["mode"]["const"] == "SOURCE_REQUIRED"
    assert properties["execution"]["const"] == "DISABLED"
    assert properties["schema_authority_class"]["const"] == (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_CONNECTOR_AUTHORITY"
    )
    assert properties["surface_kind"]["const"] == (
        "CONNECTOR_CAPABILITY_REGISTRY_STATIC_SCAFFOLD"
    )
    assert properties["deterministic_output"]["const"] is True


def test_connector_capability_registry_schema_defines_registry_card_and_readiness_surfaces():
    schema = _capability_schema()

    assert CAPABILITY_SURFACE_DEFS.issubset(set(schema["$defs"]))
    assert (
        schema["$defs"]["connector_capability_card"]["properties"]["semantic_binding_state"][
            "const"
        ]
        == "UNBOUND"
    )
    assert (
        schema["$defs"]["connector_readiness_record"]["properties"]["semantic_value"][
            "$ref"
        ]
        == "#/$defs/source_required_value"
    )


def test_connector_capability_registry_schema_requires_disabled_authority_flags():
    schema = _capability_schema()
    no_claim_properties = schema["$defs"]["no_claim_flags"]["properties"]
    forbidden_properties = schema["$defs"]["connector_forbidden_action_flags"][
        "properties"
    ]

    assert all(
        item["const"] is False for item in no_claim_properties.values()
    )
    assert all(
        item["const"] is False for item in forbidden_properties.values()
    )
    assert (
        schema["$defs"]["connector_authority_scope_flags"]["properties"][
            "accepted_source_evidence_required_before_semantic_binding"
        ]["const"]
        is True
    )
    assert (
        schema["$defs"]["connector_authority_scope_flags"]["properties"][
            "connector_semantic_binding_allowed"
        ]["const"]
        is False
    )
