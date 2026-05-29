"""Official candidate intake helpers for PR161A."""

from __future__ import annotations

from typing import Mapping

from . import constants as c


def is_official_candidate(record: Mapping[str, object]) -> bool:
    return record.get("source_intake_state") == c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_OFFICIAL_CANDIDATE.value

