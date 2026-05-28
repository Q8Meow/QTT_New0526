from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import master_report, records


def test_pr160_no_invented_external_facts_or_source_packets():
    assert master_report()["invented_external_fact_count"] == 0
    assert master_report()["invented_source_packet_count"] == 0
    assert all(item["source_acceptance_executed_flag"] is False for item in records())
