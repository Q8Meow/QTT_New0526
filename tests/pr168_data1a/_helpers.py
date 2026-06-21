from __future__ import annotations

from tools.pr168_data1a_validator import validate_generated_reports


def assert_data1a_valid() -> None:
    failures = validate_generated_reports()
    assert failures == []
