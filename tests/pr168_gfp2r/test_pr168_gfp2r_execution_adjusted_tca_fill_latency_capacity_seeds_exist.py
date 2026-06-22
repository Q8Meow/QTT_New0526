from tests.pr168_gfp2r._helpers import assert_positive_count, record_count


def test_pr168_gfp2r_execution_adjusted_tca_fill_latency_capacity_seeds_exist() -> None:
    assert_positive_count("execution_adjusted_seed_count")
    assert_positive_count("tca_fill_latency_capacity_seed_count")
    assert record_count("PR168_GFP2R_ExecutionAdjustedCandidateSeed") > 0
    assert record_count("PR168_GFP2R_TCAFillLatencyCapacitySeed") > 0
