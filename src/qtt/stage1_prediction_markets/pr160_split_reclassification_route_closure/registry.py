"""Common PR160 report and registry payload wrappers."""

from __future__ import annotations

from typing import Any, Mapping


def report_payload(
    report_type: str,
    records: list[Mapping[str, Any]],
    common: Mapping[str, Any],
    **extra: Any,
) -> dict[str, Any]:
    return {
        "report_type": report_type,
        **dict(common),
        "record_count": len(records),
        "records": list(records),
        **extra,
    }


def registry_payload(
    registry_type: str,
    records: list[Mapping[str, Any]],
    common: Mapping[str, Any],
    **extra: Any,
) -> dict[str, Any]:
    return {
        "registry_type": registry_type,
        **dict(common),
        "record_count": len(records),
        "records": list(records),
        **extra,
    }
