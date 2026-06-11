from __future__ import annotations


def test_connector_reference_rows_do_not_bind_connectors(pr165_d2_records):
    rows = pr165_d2_records["PR165_D2_ConnectorVenueReadinessReferenceRouting.report.json"]
    assert len(rows) == 3985
    assert all(row["connector_binding_allowed_in_this_pr"] is False for row in rows[:100])
    assert any("PR174" in row["future_connector_pr_refs"] for row in rows)
