from .conftest import assert_rows


def test_pr166_sf_connector_ref_routing_has_no_binding(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_ConnectorRefRouting.report.json")
    assert len(rows) == 6502
    for row in rows[:200]:
        assert row["future_connector_pr_refs"]
        assert row["connector_binding_allowed_in_this_pr"] is False
        assert row["private_state_fetch_allowed_in_this_pr"] is False
        assert row["runtime_cash_receipt_allowed_in_this_pr"] is False
        assert row["source_truth_acceptance_allowed_in_this_pr"] is False
