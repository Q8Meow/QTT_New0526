def test_latency_precompute_routing(summary, records):
    rows = records("PR162R_LatencyPrecomputeRoutingMatrix.report.json")
    assert len(rows) == summary["latency_precompute_rows_count"]
    assert rows
    assert any(row["hot_path_candidate_flag"] for row in rows)
    assert any(row["batch_only_flag"] for row in rows)
    assert all(row["replay_paper_only_flag"] for row in rows)
    assert all(row["benchmark_required_before_live_flag"] for row in rows)
