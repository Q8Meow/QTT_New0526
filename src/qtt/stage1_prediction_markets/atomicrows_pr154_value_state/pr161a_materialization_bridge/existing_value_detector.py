"""Existing value detection for PR161A."""

from __future__ import annotations

from typing import Mapping


def value_present_before_pr161a(record: Mapping[str, object]) -> bool:
    return bool(record)

