from tests.pr168_recovery1._helpers import assert_recovery1_valid, report


def test_rp5_ready_batch_is_nonlive_nonproof() -> None:
    assert_recovery1_valid()
    batch = report("PR168_RECOVERY1_RP5ReadyBatch.report.json")["records"]["rows"]
    assert batch
    assert all(row["active_live_candidate_flag"] is False for row in batch)
