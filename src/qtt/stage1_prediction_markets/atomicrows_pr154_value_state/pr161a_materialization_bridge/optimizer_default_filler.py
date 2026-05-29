"""Optimizer default helper for PR161A."""

from __future__ import annotations

from . import constants as c


def optimizer_default_value() -> str:
    return c.DefaultBasis.OPTIMIZER_LIBRARY_DEFAULT_IF_SOURCE_AVAILABLE.value

