from src.qtt.stage1_prediction_markets.source_intelligence.pr159s_open_intake import constants as c
from tests.stage1_prediction_markets.source_intelligence.pr159s_test_support import count_receipt


def test_pr159s_terminal_completion_counts_reconcile():
    receipt = count_receipt()
    assert receipt["processed_total"] == 868
    assert receipt["processed_atomicrows"] == 845
    assert receipt["processed_pr154"] == 23
    assert receipt["terminal_completion_total"] == 868
    assert receipt["source_profit_classified_total"] == 868
    assert receipt["orphan_target_count"] == 0
    assert receipt["generic_blocker_count"] == 0
    assert sum(receipt["terminal_completion_partition"].values()) == 868
    assert receipt["terminal_completion_partition"][c.TerminalCompletionState.COMPLETED_AS_CONNECTOR_FUTURE_ROUTE.value] == 338

