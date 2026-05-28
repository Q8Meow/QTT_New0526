from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import master_registry


def test_pr158_owner_editability_lifecycle_preserved():
    owner_editable = [record for record in master_registry()["records"] if record.get("owner_dashboard_editable_flag") is True]
    assert owner_editable
    assert all(record["owner_value_change_allowed_flag"] is True for record in owner_editable)
    assert all(record["owner_change_requires_policy_snapshot_flag"] is True for record in owner_editable)

