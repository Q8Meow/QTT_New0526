"""Small deterministic sharding helper for large PR161B reports."""

from __future__ import annotations

import json
from typing import Any, Mapping


GITHUB_WARNING_THRESHOLD_BYTES = 50 * 1024 * 1024


def report_size_bytes(payload: Mapping[str, Any]) -> int:
    return len(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True).encode("utf-8")) + 1


def sharding_status(payload: Mapping[str, Any]) -> dict[str, Any]:
    size = report_size_bytes(payload)
    return {
        "largest_report_size_bytes": size,
        "github_recommended_warning_threshold_bytes": GITHUB_WARNING_THRESHOLD_BYTES,
        "report_sharding_required_flag": size >= GITHUB_WARNING_THRESHOLD_BYTES,
        "report_sharding_status": "NOT_REQUIRED_UNDER_50_MB" if size < GITHUB_WARNING_THRESHOLD_BYTES else "REQUIRED",
    }
