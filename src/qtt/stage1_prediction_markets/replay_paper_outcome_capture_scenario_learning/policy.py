"""PR161E policy helpers."""

from __future__ import annotations

from . import constants as c


def no_authority_policy_record() -> dict[str, bool]:
    return dict(c.NO_AUTHORITY_CONFIRMATION)


def owner_approval_record() -> dict[str, bool]:
    return dict(c.OWNER_APPROVALS)
