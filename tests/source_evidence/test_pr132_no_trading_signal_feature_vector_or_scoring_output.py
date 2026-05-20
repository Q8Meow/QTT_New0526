from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_no_trading_signal_feature_vector_or_scoring_output():
    evidence = support.main_report()["PR132_NO_LIVE_NETWORK_EVIDENCE"]

    assert evidence["feature_vector_created_count"] == 0
    assert evidence["trading_signal_created_count"] == 0
    assert evidence["scoring_ranking_arbitration_output_created_count"] == 0
    for event in support.canonical_events():
        assert event["adapter_output_is_feature_vector"] is False
        assert event["adapter_output_is_trading_signal"] is False
        assert event["adapter_output_is_scoring_input"] is False
