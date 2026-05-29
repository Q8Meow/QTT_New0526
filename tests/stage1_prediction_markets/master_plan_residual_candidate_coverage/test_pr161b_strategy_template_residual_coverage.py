from .pr161b_test_support import records, summary


def test_pr161b_strategy_template_residual_coverage_report_exists():
    assert summary()["strategy_template_residual_candidate_count"] == len(records("strategy_template"))
