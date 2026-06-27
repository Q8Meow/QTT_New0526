"""Beam-search-ready preview facade.

RP5E materializes readiness traces only; it does not run an optimizer backend.
"""

from __future__ import annotations

from .search_budget_scheduler import search_trace_rows


def beam_search_ready_rows() -> list[dict[str, object]]:
    return [row for row in search_trace_rows() if row.get("beam_width")]
