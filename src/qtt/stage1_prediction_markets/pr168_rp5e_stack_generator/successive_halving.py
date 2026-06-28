"""Successive-halving-ready budget facade."""

from __future__ import annotations

from .search_budget_scheduler import search_trace_rows


def successive_halving_ready_rows() -> list[dict[str, object]]:
    return [row for row in search_trace_rows() if row.get("successive_halving_eta")]
