from tests.pr168_rp5a._helpers import load_report, load_rows


def test_identity_custody_graph_exists() -> None:
    rows = load_rows("identity_custody_rows")
    report = load_report("PR168_RP5A_IdentityCustodyGraph.report.json")
    assert report["identity_custody_row_count"] == len(rows)
