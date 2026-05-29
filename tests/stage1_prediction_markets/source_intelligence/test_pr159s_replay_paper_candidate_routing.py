from src.qtt.stage1_prediction_markets.source_intelligence.pr159s_open_intake import constants as c
from tests.stage1_prediction_markets.source_intelligence.pr159s_test_support import load


def test_pr159s_replay_paper_candidate_routes_are_not_executions():
    payload = load(c.REPLAY_PAPER_CANDIDATE_ROUTE_PATH)
    assert payload["record_count"] == 530
    assert all(record["route_state"] == c.ReplayPaperRouteState.REPLAY_PAPER_ROUTE_CREATED_NOT_EXECUTED.value for record in payload["records"])
    assert all(record["replay_execution_performed_in_pr159s"] is False for record in payload["records"])
    assert all(record["paper_execution_performed_in_pr159s"] is False for record in payload["records"])

