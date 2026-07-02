from tests.pr169_dash1.conftest import json_doc


def test_authority_boundary_report_blocks_runtime_and_order_authority() -> None:
    report = json_doc("owner_dashboard_authority_boundary.report.json")
    assert report["status"] == "PASS"
    false_keys = [key for key, value in report.items() if isinstance(value, bool) and key != "owner_global_internal_authority_preserved_with_receipts"]
    assert false_keys
    assert all(report[key] is False for key in false_keys)
    assert report["owner_global_internal_authority_preserved_with_receipts"] is True
