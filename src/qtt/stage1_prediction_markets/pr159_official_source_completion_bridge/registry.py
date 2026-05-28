"""Small registry/report payload helpers for PR159."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def registry_payload(registry_type: str, records: list[Mapping[str, Any]], common: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "registry_type": registry_type,
        **dict(common),
        "record_count": len(records),
        "records": records,
    }


def report_payload(report_type: str, records: list[Mapping[str, Any]], common: Mapping[str, Any], **extra: Any) -> dict[str, Any]:
    return {
        "report_type": report_type,
        **dict(common),
        **extra,
        "record_count": len(records),
        "records": records,
        "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
    }

