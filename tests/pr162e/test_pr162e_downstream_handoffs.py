from tests.pr162e.helpers import load_report


def test_downstream_handoff_counts_follow_actual_pr167_flags():
    assert load_report("PR162E_To_PR162F.report.json")["record_count"] == 438
    assert load_report("PR162E_To_PR166_QC_Retest.report.json")["record_count"] == 190
    assert load_report("PR162E_TerminalNoTradeNonLive.report.json")["record_count"] == 385
    assert load_report("PR162E_To_FutureConnectors.report.json")["record_count"] == 559
