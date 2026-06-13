"""Shard input audit extension point for PR166-SM2."""

from __future__ import annotations

from .report_writer import load_sources

__all__ = ["load_sources"]
