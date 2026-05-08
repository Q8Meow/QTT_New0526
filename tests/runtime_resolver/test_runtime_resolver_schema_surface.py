import json
from pathlib import Path


SCHEMA_PATH = Path("schemas/runtime_resolver/runtime_resolver.schema.json")
GUARDRAIL_FIELDS = {
    "resolver_execution_allowed",
    "candidate_resolution_allowed",
    "cross_platform_selection_allowed",
    "market_selection_allowed",
    "selected_candidate_allowed",
    "connector_binding_allowed",
    "source_retrieval_allowed",
    "source_acceptance_execution_allowed",
    "private_state_fetch_allowed",
    "runtime_cash_fetch_allowed",
    "live_venue_access_allowed",
    "api_key_use_allowed",
    "order_execution_allowed",
    "profit_claim_allowed",
}
REQUIRED_BEFORE_ENABLE_MARKERS = {
    "accepted_source_evidence_required_before_resolution",
    "owner_approval_required_before_live_use",
}


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_runtime_resolver_schema_is_source_required_and_disabled():
    schema = _schema()
    properties = schema["properties"]

    assert properties["mode"]["const"] == "SOURCE_REQUIRED"
    assert properties["execution"]["const"] == "DISABLED"
    assert properties["schema_authority_class"]["const"] == (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_RUNTIME_RESOLVER_AUTHORITY"
    )
    assert properties["surface_kind"]["const"] == "RUNTIME_RESOLVER_SOURCE_REQUIRED"
    assert schema["additionalProperties"] is True


def test_runtime_resolver_schema_requires_disabled_guardrails():
    schema = _schema()
    properties = schema["properties"]
    required = set(schema["required"])

    assert GUARDRAIL_FIELDS.issubset(required)
    assert all(properties[field]["const"] is False for field in GUARDRAIL_FIELDS)


def test_runtime_resolver_schema_requires_source_before_resolution():
    schema = _schema()
    properties = schema["properties"]
    required = set(schema["required"])

    assert REQUIRED_BEFORE_ENABLE_MARKERS.issubset(required)
    assert all(
        properties[field]["const"] is True
        for field in REQUIRED_BEFORE_ENABLE_MARKERS
    )


def test_runtime_resolver_schema_does_not_define_runtime_authority():
    schema = _schema()
    properties = schema["properties"]

    assert "resolver_runtime_authority" not in properties
    assert "candidate_selection_authority" not in properties
    assert "connector_binding_authority" not in properties
    assert "source_retrieval_authority" not in properties
    assert "order_execution_authority" not in properties
