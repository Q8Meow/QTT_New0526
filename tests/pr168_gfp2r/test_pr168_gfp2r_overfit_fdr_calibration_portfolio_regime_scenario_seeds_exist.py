from tests.pr168_gfp2r._helpers import assert_positive_count, record_count


def test_pr168_gfp2r_overfit_fdr_calibration_portfolio_regime_scenario_seeds_exist() -> None:
    assert_positive_count("fdr_trial_family_seed_count")
    assert_positive_count("portfolio_marginal_utility_seed_count")
    assert_positive_count("regime_conditioned_seed_count")
    assert record_count("PR168_GFP2R_CalibrationSampleSizeGapSeed") > 0
    assert record_count("PR168_GFP2R_ScenarioLadderSeed") > 0
