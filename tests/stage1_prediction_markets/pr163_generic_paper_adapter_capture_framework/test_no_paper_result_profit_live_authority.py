def test_no_paper_result_profit_live_authority(summary, records):
    rows = records("PR163_NoPaperResultProfitLiveAuthorityAudit.report.json")
    assert rows[0]["paper_result_packet_count"] == 0
    assert rows[0]["profit_evidence_count"] == 0
    assert rows[0]["live_order_authority_count"] == 0
    assert summary["paper_result_packet_count"] == 0
