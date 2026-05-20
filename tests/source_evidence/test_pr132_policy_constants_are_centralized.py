from src.qtt.stage1_prediction_markets.market_data_ingest import policy
from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_policy_constants_are_centralized():
    constants = support.main_report()["PR132_NORMALIZED_POLICY_CONSTANTS"]

    assert tuple(constants["stage1_venue_ids"]) == policy.STAGE1_VENUE_IDS
    assert tuple(constants["shared_scope_ids"]) == policy.SHARED_SCOPE_IDS
    assert tuple(constants["allowed_adapter_input_classes"]) == (
        policy.ALLOWED_ADAPTER_INPUT_CLASSES
    )
    assert tuple(constants["allowed_canonical_event_kind_classes"]) == (
        policy.ALLOWED_CANONICAL_EVENT_KIND_CLASSES
    )
    assert tuple(constants["allowed_source_dependency_states"]) == (
        policy.ALLOWED_SOURCE_DEPENDENCY_STATES
    )
    assert tuple(constants["blocked_action_ids"]) == policy.BLOCKED_ACTION_IDS
    assert constants["package_authority_class"] == policy.PACKAGE_AUTHORITY_CLASS
