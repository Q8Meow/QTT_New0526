from __future__ import annotations

from tests.pr168_map3._helpers import records, summary


def test_id_mining_scans_repo_artifacts() -> None:
    rows = records("PR168_MAP3_IDMine.report.json")
    assert rows
    assert summary()["id_mining_row_count"] == len(rows)
    assert all("source_file_ref" in row for row in rows)
