from tests.pr168_rp5a._helpers import load_report


def test_no_runtime_or_stack_generation() -> None:
    report = load_report("PR168_RP5A_FinalSummary.report.json")
    assert report["runtime_stack_generation_count"] == 0
    assert report["trade_simulation_count"] == 0
    assert report["live_order_authority_created_count"] == 0
