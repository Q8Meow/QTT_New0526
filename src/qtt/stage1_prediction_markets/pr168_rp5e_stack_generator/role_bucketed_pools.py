"""Role-bucketed pool facade."""

from __future__ import annotations

from .context_pool_selector import context_pool_rows


def role_bucketed_pool_rows() -> list[dict[str, object]]:
    return context_pool_rows()
