import json

from tests.source_evidence.pr127_execution_lifecycle_support import REPO_ROOT


def test_pr127_per_venue_execution_lifecycle_schema():
    schema_dir = REPO_ROOT / "schemas/source_evidence/execution_lifecycle"
    schema_names = [
        "per_venue_execution_lifecycle_model.schema.json",
        "per_venue_execution_lifecycle_phase.schema.json",
        "per_venue_execution_lifecycle_transition.schema.json",
        "per_venue_fill_integrity_placeholder.schema.json",
        "per_venue_cashflow_pnl_placeholder.schema.json",
        "per_venue_latency_component_placeholder.schema.json",
        "per_venue_settlement_finality_placeholder.schema.json",
        "per_venue_reconciliation_placeholder.schema.json",
        "per_venue_execution_lifecycle_validation_receipt.schema.json",
        "per_venue_execution_lifecycle_rejection.schema.json",
        "per_venue_execution_lifecycle_cross_venue_normalization_handoff.schema.json",
    ]

    for schema_name in schema_names:
        schema = json.loads((schema_dir / schema_name).read_text(encoding="utf-8"))

        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["type"] == "object"
        assert schema["required"]
        assert schema["additionalProperties"] is True
