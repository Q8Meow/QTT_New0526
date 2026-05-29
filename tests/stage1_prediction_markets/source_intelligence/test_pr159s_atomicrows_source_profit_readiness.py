from src.qtt.stage1_prediction_markets.source_intelligence.pr159s_open_intake import constants as c
from tests.stage1_prediction_markets.source_intelligence.pr159s_test_support import count_receipt, load


def test_pr159s_atomicrows_source_profit_readiness_reconciles():
    payload = load(c.ATOMICROWS_SOURCE_PROFIT_READINESS_DELTA_PATH)
    receipt = count_receipt()
    assert payload["record_count"] == 845
    assert receipt["atomicrows_candidate_ready_count"] == 845
    assert receipt["atomicrows_official_source_ready_count"] == 0
    assert receipt["atomicrows_replay_paper_candidate_ready_count"] == 530
    assert receipt["atomicrows_non_profitable_retired_count"] == 0

