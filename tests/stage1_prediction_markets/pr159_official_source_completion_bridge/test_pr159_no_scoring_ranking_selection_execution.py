from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import master_report


def test_pr159_no_scoring_ranking_selection_execution():
    assert master_report()["scoring_ranking_selection_execution_count"] == 0
    assert master_report()["no_authority_confirmation"]["scoring_execution_created"] is False
    assert master_report()["no_authority_confirmation"]["ranking_execution_created"] is False
    assert master_report()["no_authority_confirmation"]["selection_execution_created"] is False

