from __future__ import annotations

from ._helpers import assert_rp5c_valid


def test_rp5c_validator_passes() -> None:
    assert_rp5c_valid()
