import json
from pathlib import Path


SCHEMA_PATH = Path("schemas/runtime_cash/runtime_cash_field_map.schema.json")
GUARDRAIL_FIELDS = {
    "runtime_cash_semantic_population_allowed",
    "account_balance_semantics_allowed",
    "buying_power_semantics_allowed",
    "private_state_fetch_allowed",
    "runtime_cash_fetch_allowed",
    "runtime_cash_receipt_creation_allowed",
    "connector_binding_allowed",
    "live_account_access_allowed",
    "api_key_use_allowed",
    "order_execution_allowed",
    "profit_claim_allowed",
}
REQUIRED_BEFORE_ENABLE_MARKERS = {
    "accepted_source_evidence_required_before_semantics",
    "runtime_cash_receipt_required_before_values",
    "owner_approval_required_before_live_use",
}


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_runtime_cash_field_map_schema_is_source_required_and_disabled():
    schema = _schema()
    properties = schema["properties"]

    assert properties["mode"]["const"] == "SOURCE_REQUIRED"
    assert properties["execution"]["const"] == "DISABLED"
    assert properties["schema_authority_class"]["const"] == (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_RUNTIME_CASH_AUTHORITY"
    )
    assert properties["surface_kind"]["const"] == "RUNTIME_CASH_FIELD_MAP_SOURCE_REQUIRED"
    assert schema["additionalProperties"] is True


def test_runtime_cash_field_map_schema_requires_disabled_guardrails():
    schema = _schema()
    properties = schema["properties"]
    required = set(schema["required"])

    assert GUARDRAIL_FIELDS.issubset(required)
    assert all(properties[field]["const"] is False for field in GUARDRAIL_FIELDS)


def test_runtime_cash_field_map_schema_requires_evidence_and_receipt_before_enable():
    schema = _schema()
    properties = schema["properties"]
    required = set(schema["required"])

    assert REQUIRED_BEFORE_ENABLE_MARKERS.issubset(required)
    assert all(
        properties[field]["const"] is True
        for field in REQUIRED_BEFORE_ENABLE_MARKERS
    )

