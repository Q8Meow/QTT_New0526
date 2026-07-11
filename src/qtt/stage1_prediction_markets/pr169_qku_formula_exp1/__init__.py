"""Centralized executable formula/QKU expansion contracts.

This package is a deterministic, repository-local extension of the existing
RP5C/MAP3/PR162D/PR162E computation plane.  It has no connector, order,
private-state, runtime-agent, or quantum-backend authority.
"""

from .catalog import CARD_NAMES, card_rows
from .runtime import FormulaQKUService

__all__ = ["CARD_NAMES", "FormulaQKUService", "card_rows"]
