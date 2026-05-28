"""Prior-artifact lookup helpers for PR158."""

from __future__ import annotations

from typing import Any, Mapping


def row_id_from_request(request: Mapping[str, Any]) -> str:
    return str(request.get("record_id_or_row_id") or "")


def target_id_from_request(request: Mapping[str, Any]) -> str:
    return str(request.get("record_id_or_row_id") or "")


def basis_refs(*refs: str | None) -> list[str]:
    return sorted({ref for ref in refs if ref})

