"""Prior repo reuse helpers for PR161A."""

from __future__ import annotations

from typing import Mapping

from . import constants as c


def is_prior_repo_reuse(record: Mapping[str, object]) -> bool:
    return record.get("value_materialization_state") == c.ValueMaterializationState.VALUE_FILLED_PRIOR_REPO_REUSE.value

