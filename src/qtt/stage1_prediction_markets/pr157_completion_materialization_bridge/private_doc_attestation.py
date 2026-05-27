"""Private-document attestation routing for PR157."""

from __future__ import annotations

from . import constants as c


def attestation_request_id(record_id: str) -> str:
    return f"PR157_PRIVATE_DOC_ATTESTATION_REQUEST__{record_id}"


def blocker_class() -> str:
    return c.BlockerClass.PRIVATE_DOC_ATTESTATION_REQUIRED.value
