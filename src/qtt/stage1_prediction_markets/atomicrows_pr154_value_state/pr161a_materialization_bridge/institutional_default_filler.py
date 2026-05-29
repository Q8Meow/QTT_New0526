"""Institutional default helper for PR161A."""

from __future__ import annotations

from . import constants as c


def institutional_default_value() -> str:
    return c.DefaultBasis.INSTITUTIONAL_QTT_STARTER_DEFAULT.value

