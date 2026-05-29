"""Hybrid arbitration helper for PR161A."""

from __future__ import annotations

from . import constants as c


def hybrid_arbitration_default_basis() -> str:
    return c.DefaultBasis.HYBRID_ARBITRATION_QTT_CANDIDATE_DEFAULT.value

