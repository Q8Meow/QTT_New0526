"""Test support helpers for PR166-S."""

from __future__ import annotations

from typing import Any


def summary_record(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return payloads["PR166_S_FinalSummary.report.json"]["records"][0]
