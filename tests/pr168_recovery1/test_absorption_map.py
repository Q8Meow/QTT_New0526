from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_absorption_map_covers_old_lanes() -> None:
    assert_recovery1_valid()
    absorbed = {row["absorbed_old_pr_ref"] for row in rows("old_roadmap_absorption")}
    assert {"PR162D-R3", "MAP4", "SRC1", "RP4", "PR166-SF/S2"} <= absorbed
