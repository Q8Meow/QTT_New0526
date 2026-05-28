"""Registry payload helpers for PR158."""

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


def report_payload(report_type: str, counts: Mapping[str, Any], common: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "report_type": report_type,
        **dict(common),
        **dict(counts),
        "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
    }

