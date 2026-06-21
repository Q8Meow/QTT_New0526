from tools.pr168_data1_validator import run_validation


def test_pr168_data1_snapshots_have_asof_source_url_endpoint_and_authority_fields() -> None:
    run_validation("snapshots_have_asof_source_url_endpoint_and_authority_fields")
