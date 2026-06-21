from tests.pr168_gfp2r._helpers import rows


def test_pr168_gfp2r_negative_recovery_routes_do_not_force_positive() -> None:
    recovery_rows = rows("recovery_variant")
    assert recovery_rows
    assert all(row["forced_positive_flag"] is False for row in recovery_rows)
