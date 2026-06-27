"""Near-clone suppression facade."""

from __future__ import annotations

from .diversity import diversity_rows


def near_clone_rows() -> list[dict[str, object]]:
    return diversity_rows()
