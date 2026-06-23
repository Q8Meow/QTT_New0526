from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_repair_ablation_has_delta_and_controls() -> None:
    assert_recovery1_valid()
    assert all(row["unchanged_baseline_controls"] and row["ablation_delta_net_expected_pnl_or_gap"] >= 0 for row in rows("repair_ablation"))
