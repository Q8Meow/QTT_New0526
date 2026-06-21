from tests.pr168_gfp2.pr168_gfp2_test_support import load


def test_prior_fake_negative_authority_is_reopened_and_routed_to_recompute() -> None:
    rows = load("PR168_GFP2_FakeNegativeReopenQueue.report.json")
    assert rows
    for row in rows[:1000]:
        assert row["new_classification"] == "PRIOR_FAKE_NEGATIVE_REOPEN_REQUIRED"
        assert row["downstream_repair_route"] == "PR168-RP2"
