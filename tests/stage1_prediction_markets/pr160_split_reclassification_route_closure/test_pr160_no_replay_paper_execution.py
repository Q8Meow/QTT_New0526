from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import master_report, records


def test_pr160_no_replay_paper_execution():
    assert master_report()["replay_paper_execution_count"] == 0
    assert all(item["can_qtt_use_in_replay_flag"] is False for item in records())
    assert all(item["can_qtt_use_in_paper_flag"] is False for item in records())
