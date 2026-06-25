from tests.pr168_rp5b._helpers import load_report, load_rows


def test_rp5a_inputs_exist() -> None:
    report = load_report("PR168_RP5B_RP5AInputIntegrity.report.json")
    rows = load_rows("rp5a_input_integrity_rows")
    assert report["rp5a_input_integrity_passed"] is True
    assert rows
    assert all(row["integrity_status"] == "PASS" for row in rows)
