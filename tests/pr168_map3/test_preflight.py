from __future__ import annotations

from tests.pr168_map3._helpers import summary


def test_pr236_preflight_summary_is_true() -> None:
    assert summary()["pr236_merged_preflight_passed_flag"] is True
