from __future__ import annotations

from ._helpers import load_rows


def test_rp5c_routes_every_identity_to_rp5d_handoff_without_tiers() -> None:
    identities = load_rows("immutable_qku_formula_library")
    handoff = load_rows("rp5d_executability_handoff")

    assert len(handoff) == len(identities)
    assert all(row["rp5d_handoff_state"] for row in handoff)
    assert all(row["no_executability_tier_decided_flag"] is True for row in handoff)
