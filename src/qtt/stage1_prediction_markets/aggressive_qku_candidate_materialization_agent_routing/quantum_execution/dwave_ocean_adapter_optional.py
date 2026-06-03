"""Optional D-Wave Ocean-compatible adapter surface."""

from __future__ import annotations

from .backend_adapter_base import BackendAdapter
from .backend_dependency_detector import dependency_status_records


def dwave_ocean_dependency_available() -> bool:
    return any(
        record["module_name"] == "dimod" and record["dependency_available_flag"]
        for record in dependency_status_records()
    )


def dwave_ocean_adapter() -> BackendAdapter:
    return BackendAdapter("PR162D-DWAVE-OCEAN-OPTIONAL-ADAPTER", "DWAVE_OCEAN_COMPATIBLE_OPTIONAL")
