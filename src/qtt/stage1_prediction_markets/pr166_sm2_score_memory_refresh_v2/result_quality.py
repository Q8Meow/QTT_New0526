"""Result quality extension point for PR166-SM2."""

from __future__ import annotations

from .report_writer import build_score_contexts

__all__ = ["build_score_contexts"]
