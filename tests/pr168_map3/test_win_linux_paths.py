from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_generated_paths_use_portable_short_form() -> None:
    rows = records("PR168_MAP3_PathAudit.report.json")
    assert all("\\" not in row["physical_path"] for row in rows)
    assert all(row["path_length"] < row["hard_fail_physical_path_length"] for row in rows)
