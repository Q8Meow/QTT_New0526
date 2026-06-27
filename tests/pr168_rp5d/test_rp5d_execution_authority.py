from __future__ import annotations

from ._helpers import report


def test_execution_authority_is_non_executing_and_centralized() -> None:
    authority = report("rp5d_execution_authority.report.json")

    assert authority["execution_mode"] == "RP5D_COMPUTABILITY_TIERING_ONLY_NON_EXECUTING"
    for key, value in authority.items():
        if key.endswith("_authorized"):
            assert value is False, key
