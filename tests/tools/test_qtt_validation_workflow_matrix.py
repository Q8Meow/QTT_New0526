from __future__ import annotations

from pathlib import Path

from tools import run_validation_gates as runner
from tools import validate_pr169_val1 as val1


def test_workflow_matrix_uses_runner_ordered_phases_without_old_alias():
    phases = val1.workflow_matrix_phases(Path(".").resolve())

    assert phases == tuple(runner.ORDERED_PHASES)
    assert runner.DETERMINISTIC_VALIDATORS_PHASE not in phases
    assert set(runner.DETERMINISTIC_VALIDATOR_SHARD_PHASES).issubset(phases)


def test_workflow_val1_checks_pass():
    failures = [
        failure
        for failure in val1.common_report_fields(Path(".").resolve())[
            "fail_closed_reasons"
        ]
        if not str(failure).startswith("VAL1_REPORT_")
    ]

    assert failures == []
