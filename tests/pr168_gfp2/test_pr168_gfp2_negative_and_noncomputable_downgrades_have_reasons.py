from tests.pr168_gfp2.pr168_gfp2_test_support import load


def test_negative_and_noncomputable_downgrades_have_reasons() -> None:
    for row in load("PR168_GFP2_ComputabilityDowngradeLedger.report.json")[:1000]:
        assert row["downgrade_reason"]
        assert row["gap_reason_codes"]
