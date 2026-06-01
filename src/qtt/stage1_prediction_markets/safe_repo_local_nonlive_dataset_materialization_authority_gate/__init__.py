"""PR162A safe repo-local non-live dataset materialization authority gate."""

from __future__ import annotations

from .validator import ValidationResult, validate_artifacts

__all__ = ["ValidationResult", "validate_artifacts"]
