"""Owner/internal default helper for PR161A."""

from __future__ import annotations

from . import constants as c


def owner_internal_default_basis() -> str:
    return c.DefaultBasis.QTT_OWNER_INTERNAL_DEFAULT.value

