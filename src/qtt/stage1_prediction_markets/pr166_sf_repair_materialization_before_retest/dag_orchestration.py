"""DAG orchestration facade for PR166-SF."""

from __future__ import annotations

from .report_writer import dag_edges

__all__ = ["dag_edges"]
