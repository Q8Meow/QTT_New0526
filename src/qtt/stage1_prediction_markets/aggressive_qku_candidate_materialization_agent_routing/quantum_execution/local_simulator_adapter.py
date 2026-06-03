"""Local simulator adapter."""

from __future__ import annotations

from .backend_adapter_base import BackendAdapter


def local_simulator_adapter() -> BackendAdapter:
    return BackendAdapter("PR162D-LOCAL-SIMULATOR-ADAPTER", "LOCAL_SIMULATOR_IF_AVAILABLE")
