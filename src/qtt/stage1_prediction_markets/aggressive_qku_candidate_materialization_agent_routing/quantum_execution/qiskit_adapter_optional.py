"""Optional Qiskit-compatible adapter surface."""

from __future__ import annotations

from .backend_adapter_base import BackendAdapter
from .backend_dependency_detector import dependency_status_records


def qiskit_dependency_available() -> bool:
    return any(
        record["module_name"] == "qiskit" and record["dependency_available_flag"]
        for record in dependency_status_records()
    )


def qiskit_adapter() -> BackendAdapter:
    return BackendAdapter("PR162D-QISKIT-OPTIONAL-ADAPTER", "QISKIT_COMPATIBLE_OPTIONAL")
