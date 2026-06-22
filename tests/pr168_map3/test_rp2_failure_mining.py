from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_rp2_failure_mining_rows_classify_failure_causes() -> None:
    rows = records("PR168_MAP3_RP2FailureMining.report.json")
    assert rows
    assert all(row["failure_class"] for row in rows)
