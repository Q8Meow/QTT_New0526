from tests.pr168_gfp2.pr168_gfp2_test_support import load


def test_every_gap_has_repair_queue() -> None:
    for row in load("PR168_GFP2_GapRoutedUniverseRepairQueue.report.json")[:1000]:
        assert row["gap_reason_codes"]
        assert row["repair_queue_refs"]
