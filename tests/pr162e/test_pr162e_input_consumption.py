from tests.pr162e.helpers import records


def test_input_consumption_records_missing_and_resolved_inputs():
    rows = records("PR162E_InputConsumption.report.json")
    assert any(row["missing_status"] == "FOUND" for row in rows)
    assert any(row["missing_status"] == "UPSTREAM_NOT_FOUND_WITH_REPAIR_ROUTE" for row in rows)
