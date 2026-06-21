from tests.pr168_gfp2.pr168_gfp2_test_support import load


def test_to_pr168_rp2_and_rank2_handoffs_exist() -> None:
    assert load("PR168_GFP2_To_PR168_RP2_RealMarketReplayRecompute.report.json")
    assert load("PR168_GFP2_To_PR168_RANK2_ProvenanceAwareRankingSeed.report.json")
