"""PR159S candidate reuse helpers for PR161A."""

from __future__ import annotations

from typing import Mapping


def has_pr159s_linkage(record: Mapping[str, object]) -> bool:
    return bool(record.get("pr159s_linkage"))

