def test_no_result_profit_live_authority(summary):
    assert summary["replay_result_packet_count"] == 0
    assert summary["paper_result_packet_count"] == 0
    assert summary["profit_evidence_count"] == 0
    assert summary["live_order_authority_count"] == 0
