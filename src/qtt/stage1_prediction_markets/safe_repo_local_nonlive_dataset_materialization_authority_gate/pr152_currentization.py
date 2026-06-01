"""PR152 currentization evidence for PR162A final-summary reporting."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c


def pr152_currentization_evidence(repo_root: Path) -> dict[str, Any]:
    missing_inputs = [
        rel
        for rel in (
            c.PR152_CURRENTIZATION_REPORT_REF,
            c.PR152_CURRENTIZATION_VALIDATOR_REF,
        )
        if not (repo_root / rel).exists()
    ]
    if missing_inputs:
        return {
            "pr152_currentization_result": c.PR152_CURRENTIZATION_RESULT_PENDING,
            "pr152_currentization_validation_command": c.PR152_CURRENTIZATION_VALIDATION_COMMAND,
            "pr152_currentization_report_ref": c.PR152_CURRENTIZATION_REPORT_REF,
            "pr152_currentization_missing_evidence": missing_inputs,
            "pr152_currentization_failure_count": 0,
            "pr152_currentization_failure_samples": [],
        }

    from src.qtt.stage1_prediction_markets.grand_global_debug_logical_consistency_audit import (
        constants as pr152_constants,
    )
    from src.qtt.stage1_prediction_markets.grand_global_debug_logical_consistency_audit.report import (
        validate_repository_artifacts,
    )

    try:
        failures = validate_repository_artifacts(repo_root)
    except Exception as exc:  # pragma: no cover - defensive command-equivalence guard.
        failures = [f"PR152_VALIDATION_EXCEPTION:{type(exc).__name__}"]

    return {
        "pr152_currentization_result": c.PR152_CURRENTIZATION_RESULT_PASS
        if not failures
        else c.PR152_CURRENTIZATION_RESULT_FAILED,
        "pr152_currentization_validation_command": c.PR152_CURRENTIZATION_VALIDATION_COMMAND,
        "pr152_currentization_success_marker": pr152_constants.SUCCESS_MARKER,
        "pr152_currentization_report_ref": c.PR152_CURRENTIZATION_REPORT_REF,
        "pr152_currentization_failure_count": len(failures),
        "pr152_currentization_failure_samples": failures[:5],
    }
