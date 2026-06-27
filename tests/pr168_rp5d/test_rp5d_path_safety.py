from __future__ import annotations

from ._helpers import report


def test_path_safety_limits_are_zero_violation() -> None:
    run = report("rp5d_run_receipt.report.json")
    registry = report("rp5d_artifact_name_registry.json")

    assert run["long_filename_violation_count"] == 0
    assert run["long_repo_relative_path_violation_count"] == 0
    assert run["long_windows_absolute_path_violation_count"] == 0
    assert run["case_collision_count"] == 0
    assert run["unsafe_filename_count"] == 0
    assert run["unregistered_abbreviation_count"] == 0
    assert all(row["safe_filename_flag"] is True for row in registry["entries"])
