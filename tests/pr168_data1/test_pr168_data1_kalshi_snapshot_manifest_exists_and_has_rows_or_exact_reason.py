from tools.pr168_data1_validator import run_validation


def test_pr168_data1_kalshi_snapshot_manifest_exists_and_has_rows_or_exact_reason() -> None:
    run_validation("kalshi_snapshot_manifest_exists_and_has_rows_or_exact_reason")
