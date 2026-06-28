from ._helpers import assert_no_authority, read_json


def test_execution_authority_is_contract_overlay_only() -> None:
    report = read_json("exec_auth.report.json")
    assert report["contract_completion_authorized"] is True
    assert report["paper_order_authority_authorized"] is False
    assert report["live_dryrun_execution_authorized"] is False
    assert_no_authority(report)
