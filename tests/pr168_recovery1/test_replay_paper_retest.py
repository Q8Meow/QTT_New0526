from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_replay_and_paper_retest_rows_exist() -> None:
    assert_recovery1_valid()
    assert len(rows("replay_retest")) == len(rows("paper_retest")) == 35
