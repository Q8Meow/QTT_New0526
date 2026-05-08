import json
from pathlib import Path


SCHEMA_PATH = Path("schemas/connectors/source_required_placeholders.schema.json")
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


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


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
