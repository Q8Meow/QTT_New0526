"""PR162C dataset materialization policy.

Default PR162C builds do not fetch network data. Owner materialization commands
are emitted separately.
"""

from __future__ import annotations


def default_materialization_mode() -> str:
    return "OFFLINE_REGISTER_ONLY_NO_NETWORK_MATERIALIZATION"
