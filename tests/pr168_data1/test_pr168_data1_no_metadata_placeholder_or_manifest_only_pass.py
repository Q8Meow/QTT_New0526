from tools.pr168_data1_validator import run_validation


def test_pr168_data1_no_metadata_placeholder_or_manifest_only_pass() -> None:
    run_validation("no_metadata_placeholder_or_manifest_only_pass")
