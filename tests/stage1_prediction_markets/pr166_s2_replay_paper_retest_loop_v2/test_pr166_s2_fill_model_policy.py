from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_fill_model_policy_declares_required_inputs():
    row = assert_report_rows("PR166_S2_FillModelPolicy.report.json", 1)[0]
    required = {"top_of_book_bid_ask", "depth_at_candidate_size", "queue_position_proxy", "latency_budget_ms", "quote_staleness_ttl_ms"}
    assert required.issubset(set(row["fill_model_required_inputs"]))
