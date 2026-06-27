"""Execution-adjusted expected cash PnL engine for PR168-VS1."""

from __future__ import annotations

from .runner import compute_fill_probability, compute_trade_plan_receipts

__all__ = ["compute_fill_probability", "compute_trade_plan_receipts"]
