from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import policy
from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_policy_constants_are_centralized():
    constants = support.main_report()["PR133_VALIDATION_EVIDENCE"]
    normalized = support.main_report()["PR133_MASTER_PLAN_SECTION_CROSSWALK"]
    assert policy.STAGE1_VENUE_IDS == ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR")
    assert policy.SHARED_SCOPE_IDS == ("PREDICTION_MARKETS_GENERAL",)
    assert constants["validator_marker"] == "QTT_ORDERBOOK_AND_EVENT_STATE_SNAPSHOT_BUILDER_OK"
    assert normalized["orderbook_canonicalization_boundary"] == "PR133_ORDERBOOK_CANONICAL_SORT_RULES_POLICY"
