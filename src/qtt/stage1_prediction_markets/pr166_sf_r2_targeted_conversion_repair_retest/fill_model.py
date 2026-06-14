"""Thin PR166-SF-R2 surface module backed by centralized report generation."""

from __future__ import annotations

from .report_writer import build_payloads, build_payloads_with_shards, write_artifacts

__all__ = ["build_payloads", "build_payloads_with_shards", "write_artifacts"]
