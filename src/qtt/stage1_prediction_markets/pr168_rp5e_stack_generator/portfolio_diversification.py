"""Portfolio diversification facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def portfolio_diversification_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "port_div.jsonl")
