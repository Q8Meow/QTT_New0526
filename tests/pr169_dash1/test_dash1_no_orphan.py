from tests.pr169_dash1.conftest import json_doc


def test_no_orphan_report_passes_required_proofs() -> None:
    report = json_doc("owner_dashboard_no_orphan.report.json")
    assert report["status"] == "PASS"
    required_true = [key for key, value in report.items() if key not in {"artifact_id", "status", "registry_rows_checked"}]
    assert required_true
    assert all(report[key] is True for key in required_true)
