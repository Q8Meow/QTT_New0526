from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import master_report


def test_pr160_official_online_docs_classification_only_not_value_authority():
    report = master_report()
    assert report["official_online_docs_used_for_classification_routing_count"] == 0
    assert report["official_online_docs_used_as_accepted_source_value_authority_count"] == 0
    assert report["official_online_docs_not_accepted_value_authority_confirmation"] is True
