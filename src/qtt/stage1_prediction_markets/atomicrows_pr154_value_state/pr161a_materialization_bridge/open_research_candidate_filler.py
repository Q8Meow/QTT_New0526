"""Open-research candidate helpers for PR161A."""

from __future__ import annotations

from typing import Mapping

from . import constants as c


def is_open_research_candidate(record: Mapping[str, object]) -> bool:
    return record.get("value_authority_class") in {
        c.ValueAuthorityClass.OPEN_RESEARCH_CANDIDATE_VALUE.value,
        c.ValueAuthorityClass.OPEN_SOURCE_INTELLIGENCE_CANDIDATE_VALUE.value,
    }

