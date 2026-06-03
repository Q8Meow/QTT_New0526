"""Provider-compatible dry-run job payload builder."""

from __future__ import annotations

from typing import Any


def build_quantum_job_payload(problem_model: dict[str, Any], backend_family: str) -> dict[str, Any]:
    return {
        "payload_id": f"{problem_model['problem_model_id']}-{backend_family}-PAYLOAD",
        "problem_model_ref": problem_model["problem_model_id"],
        "backend_family": backend_family,
        "problem_model_type": problem_model["problem_model_type"],
        "payload": {
            "objective": problem_model.get("objective_coefficients"),
            "constraints": problem_model.get("constraints", []),
        },
        "dry_run_flag": True,
        "remote_submission_attempted_flag": False,
        "secret_material_included_flag": False,
        "live_order_authority": False,
    }
