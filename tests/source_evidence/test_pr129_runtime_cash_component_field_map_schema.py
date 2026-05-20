from pathlib import Path
import json


SCHEMA_DIR = Path("src/qtt/stage1_prediction_markets/capital_risk")
SCHEMA_FILES = [
    "runtime_cash_component_field_map.schema.json",
    "venue_balance_semantic_binding.schema.json",
    "runtime_cash_decimal_policy.schema.json",
    "runtime_available_after_commitments_receipt.schema.json",
    "runtime_cash_component_source_packet_required_rejection_receipt.schema.json",
    "runtime_cash_component_unknown_rejection_receipt.schema.json",
    "runtime_cash_component_reconciliation_report.schema.json",
    "new_exposure_cash_gate_receipt.schema.json",
    "runtime_cash_downstream_handoff.schema.json",
]


def test_pr129_runtime_cash_component_schema_family_exists_and_is_fixture_only():
    for filename in SCHEMA_FILES:
        schema = json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["required"]
        assert schema["additionalProperties"] is True
        assert schema["properties"]["fixture_authority_class"]["const"] == (
            "TEST_FIXTURE_NOT_EXTERNAL_FACT"
        )
