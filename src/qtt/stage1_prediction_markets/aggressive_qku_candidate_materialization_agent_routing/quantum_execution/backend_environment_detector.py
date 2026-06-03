"""Quantum backend environment readiness detector without secret capture."""

from __future__ import annotations

import os


ENVIRONMENT_ALIASES = (
    ("QISKIT_IBM_TOKEN", "QISKIT_REMOTE_SIMULATOR_REPLAY_PAPER_ONLY"),
    ("DWAVE_API_TOKEN", "DWAVE_REMOTE_REPLAY_PAPER_ONLY"),
    ("QTT_OWNER_ENABLE_REMOTE_QUANTUM_REPLAY_PAPER", "OWNER_REMOTE_QUANTUM_ENABLE_FLAG"),
)


def environment_status_records() -> list[dict[str, object]]:
    return [
        {
            "environment_alias": alias,
            "env_var_name": env_name,
            "present_flag": bool(os.environ.get(env_name)),
            "secret_value_captured_flag": False,
            "remote_execution_enabled_by_default_flag": False,
            "live_pretrade_dependency_flag": False,
        }
        for env_name, alias in ENVIRONMENT_ALIASES
    ]
