"""Downstream agent mapper for PR161A."""

from __future__ import annotations

from . import constants as c


def downstream_agent_roles() -> list[str]:
    return list(c.DOWNSTREAM_AGENT_ROLES)

