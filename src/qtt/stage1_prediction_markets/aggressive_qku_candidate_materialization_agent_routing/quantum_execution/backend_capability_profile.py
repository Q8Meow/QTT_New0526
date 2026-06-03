"""Backend capability profiles."""

from __future__ import annotations


def backend_capability_records() -> list[dict[str, object]]:
    return [
        {
            "backend_adapter_id": "PR162D-BACKEND-LOCAL-EXACT",
            "backend_adapter_family": "LOCAL_EXACT_ENUMERATOR",
            "supported_problem_models": ["QUBO", "ISING"],
            "supports_remote_execution_flag": False,
            "ci_safe_flag": True,
            "live_pretrade_dependency_flag": False,
            "live_order_authority": False,
        },
        {
            "backend_adapter_id": "PR162D-BACKEND-QISKIT-OPTIONAL",
            "backend_adapter_family": "QISKIT_COMPATIBLE_OPTIONAL",
            "supported_problem_models": ["QUBO", "ISING", "QAOA", "VQE", "SAMPLING_VQE"],
            "supports_remote_execution_flag": True,
            "ci_safe_flag": True,
            "live_pretrade_dependency_flag": False,
            "live_order_authority": False,
        },
        {
            "backend_adapter_id": "PR162D-BACKEND-DWAVE-OCEAN-OPTIONAL",
            "backend_adapter_family": "DWAVE_OCEAN_COMPATIBLE_OPTIONAL",
            "supported_problem_models": ["QUBO", "ISING", "BQM", "CQM", "ANNEALING"],
            "supports_remote_execution_flag": True,
            "ci_safe_flag": True,
            "live_pretrade_dependency_flag": False,
            "live_order_authority": False,
        },
        {
            "backend_adapter_id": "PR162D-BACKEND-PROVIDER-DRY-RUN",
            "backend_adapter_family": "PROVIDER_DRY_RUN_PAYLOAD_ONLY",
            "supported_problem_models": ["QUBO", "ISING", "BQM", "CQM", "QAOA", "VQE"],
            "supports_remote_execution_flag": False,
            "ci_safe_flag": True,
            "live_pretrade_dependency_flag": False,
            "live_order_authority": False,
        },
    ]
