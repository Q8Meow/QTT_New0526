"""GitHub research-pattern helpers for PR161A."""

from __future__ import annotations

from typing import Mapping


def is_github_research_pattern(record: Mapping[str, object]) -> bool:
    return record.get("source_class") == "GITHUB_REPOSITORY"

