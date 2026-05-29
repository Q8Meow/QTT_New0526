"""End-to-end orchestration graph facade for PR161B."""

from .report_builder import _orchestration_records as build_orchestration_records

__all__ = ["build_orchestration_records"]
