import json
from pathlib import Path


SCHEMA_DIR = Path("src/qtt/stage1_prediction_markets/market_data_ingest")
SCHEMA_FILES = (
    "venue_market_data_adapter_input.schema.json",
    "canonical_market_data_ingest_event.schema.json",
    "venue_market_data_adapter_binding.schema.json",
    "venue_market_data_adapter_rejection.schema.json",
    "market_data_source_dependency.schema.json",
    "market_data_no_live_network_attestation.schema.json",
    "market_data_ingest_downstream_handoff.schema.json",
)


def test_pr132_market_data_ingest_schema():
    for filename in SCHEMA_FILES:
        schema = json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))

        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["additionalProperties"] is False
        assert "schema_version" in schema["required"]
        assert "record_type" in schema["required"]
        assert "created_by" in schema["required"]
        assert "authority_class" in schema["required"]
        assert schema["properties"]["authority_class"]["const"].startswith(
            "FIXTURE_BACKED_MARKET_DATA_INGEST_CONTRACT_ONLY"
        )
