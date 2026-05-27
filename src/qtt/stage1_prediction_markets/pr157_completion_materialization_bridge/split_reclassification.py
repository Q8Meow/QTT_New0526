"""Split/reclassification routing for PR157."""

from __future__ import annotations

from . import constants as c


def reclassification_request_id(record_id: str) -> str:
    return f"PR157_SPLIT_RECLASSIFICATION_REQUEST__{record_id}"


def blocker_class() -> str:
    return c.BlockerClass.SPLIT_RECLASSIFICATION_REQUIRED.value
