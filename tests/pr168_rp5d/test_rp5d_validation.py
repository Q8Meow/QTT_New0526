from __future__ import annotations

from ._helpers import assert_rp5d_valid


def test_rp5d_validator_passes() -> None:
    result = assert_rp5d_valid()

    assert result["validation"] == "PR168_RP5D_REPLAY_PAPER_EXECUTABILITY_OK"
