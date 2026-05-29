"""PR161B master-plan residual candidate coverage package."""

from .report_builder import build_artifacts, write_artifacts
from .validator import validate_existing_artifacts

__all__ = ["build_artifacts", "write_artifacts", "validate_existing_artifacts"]
