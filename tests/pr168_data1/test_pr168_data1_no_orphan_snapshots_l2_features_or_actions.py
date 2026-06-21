from tools.pr168_data1_validator import run_validation


def test_pr168_data1_no_orphan_snapshots_l2_features_or_actions() -> None:
    run_validation("no_orphan_snapshots_l2_features_or_actions")
