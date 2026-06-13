from __future__ import annotations

from .helpers import summary


def test_pr166_s2_no_bad_status_counts_in_summary():
    s = summary()
    assert s["metadata_only_rows"] == 0
    assert s["placeholder_rows"] == 0
    assert s["unknown_status_rows"] == 0
    assert s["generic_blocker_rows"] == 0
