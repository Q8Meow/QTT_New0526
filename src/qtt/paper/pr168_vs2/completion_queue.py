"""VS2 packet completion queue facade."""

from .builder import _build_packet_rows as build_completion_queue_rows

__all__ = ["build_completion_queue_rows"]
