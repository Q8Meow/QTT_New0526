import json

from src.qtt.source_evidence.connector_semantic_implementation import validator
from tests.source_evidence.pr126_connector_semantic_implementation_support import (
    REPO_ROOT,
    artifacts,
)


def test_pr126_connector_semantic_implementation_gate_schema():
    schema_dir = REPO_ROOT / validator.SCHEMA_DIR
    schema_names = [
        "connector_semantic_implementation_gate.schema.json",
        "connector_semantic_implementation_decision_receipt.schema.json",
        "connector_semantic_pr126_fixture_scope_implementation_manifest.schema.json",
        "connector_semantic_implementation_rejection.schema.json",
    ]

    for schema_name in schema_names:
        schema = json.loads((schema_dir / schema_name).read_text(encoding="utf-8"))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["required"]
        assert schema["additionalProperties"] is False

    ok, failures, _ = validator.validate(REPO_ROOT)
    assert ok, failures

    states = json.loads(
        (schema_dir / "connector_semantic_implementation_decision_receipt.schema.json")
        .read_text(encoding="utf-8")
    )["$defs"]["implementationGateState"]["enum"]
    assert "READY_FOR_PR126_FIXTURE_SCOPE_IMPLEMENTATION" in states
    assert "REJECTED_LIVE_TRADING_BLOCKING_MATERIALITY" in states
    assert artifacts()["main_report"]["roadmap_pr_implemented"] == "PR108"
