"""VS2 idempotency facade."""

from .builder import _build_packet_rows as build_idempotency_rows

__all__ = ["build_idempotency_rows"]
