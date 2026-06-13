"""Row-count reconciliation extension point for PR166-SM2."""

from __future__ import annotations

from .report_writer import build_row_payloads

__all__ = ["build_row_payloads"]
