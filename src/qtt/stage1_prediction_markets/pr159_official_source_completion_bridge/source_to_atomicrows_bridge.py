"""PR159 source-to-AtomicRows bridge helpers."""

from __future__ import annotations

from typing import Mapping


def row_source_ready(record: Mapping[str, object]) -> bool:
    return record.get("accepted_source_packet_ref_or_null") is not None


__all__ = ["row_source_ready"]
