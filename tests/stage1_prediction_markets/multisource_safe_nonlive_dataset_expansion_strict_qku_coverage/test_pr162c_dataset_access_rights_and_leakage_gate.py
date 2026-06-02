from .test_support import records


def test_pr162c_dataset_access_rights_and_leakage_gate():
    access = records("PR162C_DatasetAuthorityAndAccessRightsGate.report.json")
    leakage = records("PR162C_DataQualityLeakageTimeWindowAudit.report.json")

    assert access
    assert all(record["default_network_fetch_allowed_flag"] is False for record in access)
    assert all(record["private_state_required_flag"] is False for record in access)
    assert leakage[0]["leakage_audit_status"] == "PASS"
    assert leakage[0]["row_count_threshold_pass"] is False
