from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import master_report


def test_pr159_no_replay_paper_execution():
    assert master_report()["no_authority_confirmation"]["replay_execution_created"] is False
    assert master_report()["no_authority_confirmation"]["paper_execution_created"] is False

