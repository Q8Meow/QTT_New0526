from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_recovery_work_items_cover_repair_actions() -> None:
    assert_recovery1_valid()
    work_items = rows("work_item")
    assert {row["work_item_family"] for row in work_items} >= {"STACK_REPAIR", "EXPRESSION_FORMULA", "SOURCE_PROVENANCE"}
