import json

from tests.source_evidence.pr128_cross_venue_execution_normalization_support import (
    REPO_ROOT,
)


def test_pr128_cross_venue_execution_normalization_schema():
    schema_dir = REPO_ROOT / "schemas/source_evidence/cross_venue_execution_normalization"
    schema_names = [
        "cross_venue_execution_normalization_taxonomy.schema.json",
        "cross_venue_execution_phase_binding.schema.json",
        "cross_venue_execution_transition_binding.schema.json",
        "cross_venue_execution_normalization_placeholder.schema.json",
        "cross_venue_execution_normalization_validation_receipt.schema.json",
        "cross_venue_execution_normalization_rejection.schema.json",
        "cross_venue_arbitrage_comparability_precondition.schema.json",
        "cross_venue_execution_downstream_handoff.schema.json",
    ]

    for schema_name in schema_names:
        schema = json.loads((schema_dir / schema_name).read_text(encoding="utf-8"))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["type"] == "object"
        assert schema["required"]
        assert schema["additionalProperties"] is True
