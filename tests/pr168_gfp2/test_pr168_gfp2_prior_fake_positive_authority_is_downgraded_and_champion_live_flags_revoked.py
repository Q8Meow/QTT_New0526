from tests.pr168_gfp2.pr168_gfp2_test_support import load


def test_prior_fake_positive_authority_is_downgraded_and_champion_live_flags_revoked() -> None:
    for row in load("PR168_GFP2_FakePositiveCorrectionQueue.report.json"):
        assert row["champion_eligible"] is False
        assert row["live_candidate_worthy"] is False
        assert row["profit_evidence_created_flag"] is False
        assert row["requires_real_market_recompute_flag"] is True
