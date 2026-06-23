from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_repair_dedupe_has_representatives() -> None:
    assert_recovery1_valid()
    assert all(row["selected_representative_ref"] for row in rows("repair_dedupe"))
