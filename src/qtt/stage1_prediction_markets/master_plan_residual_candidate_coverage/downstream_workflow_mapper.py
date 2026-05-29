"""Downstream workflow mapper facade for PR161B."""

from .report_builder import _downstream_records as build_downstream_records

__all__ = ["build_downstream_records"]
