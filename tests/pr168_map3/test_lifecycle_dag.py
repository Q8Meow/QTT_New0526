from __future__ import annotations

from tests.pr168_map3._helpers import records, summary


def test_lifecycle_dag_covers_generated_entities() -> None:
    rows = records("PR168_MAP3_LifecycleDAG.report.json")
    assert len(rows) == summary()["formula_lifecycle_dag_row_count"]
    assert all(row["lifecycle_state"] for row in rows)
