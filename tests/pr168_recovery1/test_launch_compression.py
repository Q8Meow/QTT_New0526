from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_launch_compression_handoffs_exist() -> None:
    assert_recovery1_valid()
    assert any(row["handoff_family"] == "RP5_RANK4_QOPT1" for row in rows("downstream_handoff"))
