from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import master_report, records


def test_pr160_no_scoring_ranking_selection_execution():
    assert master_report()["scoring_ranking_selection_execution_count"] == 0
    assert all(item["scoring_ranking_selection_execution_created_flag"] is False for item in records())
