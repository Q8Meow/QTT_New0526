import json

from src.qtt.stage1_prediction_markets.market_data_ingest import policy
from tests.source_evidence.pr132_market_data_ingest_support import REPO_ROOT


def test_pr132_schema_enums_and_quantum_fields_match_policy_constants():
    schema_dir = REPO_ROOT / "src/qtt/stage1_prediction_markets/market_data_ingest"
    for path in schema_dir.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        props = schema["properties"]
        required = set(schema["required"])

        for field in policy.QUANTUM_FORWARD_METADATA_FIELDS:
            assert field in props
            assert field in required
        for field in policy.QUANTUM_ZERO_AUTHORITY_FLAGS:
            assert field in props
            assert field in required
        if "venue_id" in props:
            assert tuple(props["venue_id"]["enum"]) == policy.STAGE1_VENUE_IDS
        if "scope_id" in props:
            assert tuple(props["scope_id"]["enum"]) == policy.SHARED_SCOPE_IDS
        if "event_kind_class" in props:
            assert tuple(props["event_kind_class"]["enum"]) == (
                policy.ALLOWED_CANONICAL_EVENT_KIND_CLASSES
            )
        if "adapter_input_class" in props:
            assert tuple(props["adapter_input_class"]["enum"]) == (
                policy.ALLOWED_ADAPTER_INPUT_CLASSES
            )
        if "dependency_state" in props:
            assert tuple(props["dependency_state"]["enum"]) == (
                policy.ALLOWED_SOURCE_DEPENDENCY_STATES
            )
        if "rejected_reason_code" in props:
            assert tuple(props["rejected_reason_code"]["enum"]) == (
                policy.REJECTION_REASON_CODES
            )
