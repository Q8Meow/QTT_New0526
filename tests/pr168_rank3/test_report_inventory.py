from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_no_rp3_top_level_report_silently_ignored() -> None:
    assert_rank3_valid()
    inventory = rows("rp3_report_inventory")
    assert len(inventory) == 106
    assert all(row["consumed_flag"] for row in inventory)
