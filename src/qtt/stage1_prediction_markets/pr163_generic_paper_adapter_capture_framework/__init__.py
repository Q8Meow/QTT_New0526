"""PR163 generic paper adapter and capture framework."""

from .report_builder import build_payloads, write_artifacts
from .validators import ValidationResult, validate_artifacts

__all__ = [
    "ValidationResult",
    "build_payloads",
    "validate_artifacts",
    "write_artifacts",
]
