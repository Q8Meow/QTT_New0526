"""Optional dependency status detector."""

from __future__ import annotations

import importlib.util


OPTIONAL_DEPENDENCIES = (
    ("qiskit", "QISKIT_COMPATIBLE_OPTIONAL"),
    ("qiskit_algorithms", "QISKIT_ALGORITHMS_OPTIONAL"),
    ("dimod", "DWAVE_DIMOD_OPTIONAL"),
    ("dwave.system", "DWAVE_SYSTEM_OPTIONAL"),
)


def dependency_status_records() -> list[dict[str, object]]:
    records = []
    for module_name, family in OPTIONAL_DEPENDENCIES:
        try:
            installed = importlib.util.find_spec(module_name) is not None
        except ModuleNotFoundError:
            installed = False
        records.append(
            {
                "dependency_id": f"PR162D-DEPENDENCY-{family}",
                "module_name": module_name,
                "backend_adapter_family": family,
                "dependency_available_flag": installed,
                "missing_dependency_breaks_ci_flag": False,
                "package_install_attempted_flag": False,
                "remote_execution_required_flag": False,
            }
        )
    return records
