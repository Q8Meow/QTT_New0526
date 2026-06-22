from __future__ import annotations

from tests.pr168_map3._helpers import report


def test_yolo_guard_is_recorded_as_upstream_ref() -> None:
    payload = report("PR168_MAP3_OnlineScout.report.json")
    assert "PR168_MAP3_YOLO_SAFETY_GUARD" in payload["upstream_input_refs"]
