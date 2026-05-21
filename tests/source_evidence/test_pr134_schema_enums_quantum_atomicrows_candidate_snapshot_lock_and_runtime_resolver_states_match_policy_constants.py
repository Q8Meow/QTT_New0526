from .pr134_runtime_resolver_snapshot_support import schema
from src.qtt.stage1_prediction_markets.runtime_resolver_snapshot_executor import policy


def test_schema_enums_quantum_atomicrows_candidate_snapshot_lock_and_runtime_resolver_states_match_policy_constants():
    snapshot_schema = schema("runtime_resolver_snapshot.schema.json")
    input_schema = schema("runtime_resolver_input_lock.schema.json")
    rejection_schema = schema("runtime_resolver_rejection_receipt.schema.json")

    assert snapshot_schema["properties"]["runtime_resolver_snapshot_class"]["enum"] == list(
        policy.ALLOWED_RUNTIME_RESOLVER_SNAPSHOT_CLASSES
    )
    assert snapshot_schema["properties"]["runtime_resolver_readiness_state"]["enum"] == list(
        policy.ALLOWED_RUNTIME_RESOLVER_READINESS_STATES
    )
    assert input_schema["properties"]["runtime_resolver_input_class"]["enum"] == list(
        policy.ALLOWED_RUNTIME_RESOLVER_INPUT_CLASSES
    )
    assert rejection_schema["properties"]["rejected_reason_code"]["enum"] == list(
        policy.REJECTION_REASON_CODES
    )
    for field_name in policy.QUANTUM_FORWARD_RUNTIME_RESOLVER_METADATA_FIELDS:
        assert field_name in snapshot_schema["properties"]
    for field_name in policy.ATOMICROWS_PRE_BRIDGE_METADATA_FIELDS:
        assert field_name in snapshot_schema["properties"]
    for field_name in policy.VERSIONED_CANDIDATE_SET_SNAPSHOT_LOCK_FIELDS:
        assert field_name in snapshot_schema["properties"]
