from __future__ import annotations

from pathlib import Path

from tools import run_validation_gates as runner
from tools import validate_pr169_val1 as val1
from tools.validation_inventory import canonical_command


def _canonical_phase_commands(phase: str) -> list[tuple[str, ...]]:
    validation_dir = Path("validation-dir")
    pytest_basetemp = Path("pytest-basetemp")
    return [
        canonical_command(command)
        for command in runner.build_phase_commands(
            phase,
            validation_dir,
            pytest_basetemp,
        )
    ]


def test_deterministic_validator_subshards_cover_old_phase_exactly_once():
    old_commands = _canonical_phase_commands(runner.DETERMINISTIC_VALIDATORS_PHASE)
    new_commands = [
        command
        for phase in runner.DETERMINISTIC_VALIDATOR_SHARD_PHASES
        for command in _canonical_phase_commands(phase)
    ]

    assert old_commands
    assert new_commands == old_commands
    assert len(new_commands) == len(set(new_commands))


def test_deterministic_validator_compatibility_alias_not_in_ci_order():
    assert runner.DETERMINISTIC_VALIDATORS_PHASE in runner.VALIDATION_PHASES
    assert runner.DETERMINISTIC_VALIDATORS_PHASE not in runner.ORDERED_PHASES
    assert set(runner.DETERMINISTIC_VALIDATOR_SHARD_PHASES).issubset(
        set(runner.ORDERED_PHASES)
    )


def test_val1_parity_report_marks_split_pass():
    parity = val1.deterministic_shard_parity(Path(".").resolve())

    assert parity["coverage_parity_state"] == "pass"
    assert parity["dropped_selector_count"] == 0
    assert parity["duplicate_selector_count"] == 0
    assert parity["old_command_digest"] == parity["new_command_digest"]
