from .conftest import assert_rows


def test_pr166_sf_negative_edges_have_root_causes(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_NegativeEdgeRootCauseLedger.report.json")
    assert len(rows) == 3150
    assert all(row["negative_net_edge_diagnosed_flag"] is True for row in rows[:100])
    assert all(row["root_cause_repair_action"].startswith("PR166_SF_EXACT_REPAIR_ACTION::") for row in rows[:100])
