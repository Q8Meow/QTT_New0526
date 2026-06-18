from tests.pr162e.helpers import records


def test_no_orphan_proof_passes_for_every_plugin():
    rows = records("PR162E_NoOrphanProof.report.json")
    assert len(rows) == 559
    assert all(row["no_orphan_status"] == "PASS" for row in rows)
