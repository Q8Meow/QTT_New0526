"""Launch-readiness workflow route facade for PR161B."""

from .report_builder import _launch_readiness_records as build_launch_readiness_records

__all__ = ["build_launch_readiness_records"]
