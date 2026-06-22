from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_dedupe_quality_rows_have_fdr_and_equivalence_clusters() -> None:
    rows = records("PR168_MAP3_Dedupe.report.json")
    assert rows
    assert all(row["duplicate_equivalence_cluster_id"] for row in rows)
    assert all(row["FDR_trial_family_id"] for row in rows)
