from .conftest import assert_rows


def test_pr166_sf_repair_dag_has_no_orphan_edges(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_RepairDAGLedger.report.json")
    assert len(rows) == 6502
    for row in rows[:100]:
        assert row["dag_upstream_evidence"]
        assert row["dag_edge_refs"]
        assert row["dag_no_orphan_flag"] is True
