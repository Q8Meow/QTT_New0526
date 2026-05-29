"""Terminal completion assignment for the 868 PR159S targets."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


_TESTABLE_BUCKETS: tuple[tuple[int, str], ...] = (
    (50, c.TerminalCompletionState.COMPLETED_AS_OPEN_RESEARCH_INPUT.value),
    (70, c.TerminalCompletionState.COMPLETED_AS_ALGORITHM_CANDIDATE.value),
    (60, c.TerminalCompletionState.COMPLETED_AS_FORMULA_CANDIDATE.value),
    (160, c.TerminalCompletionState.COMPLETED_AS_PARAMETER_CANDIDATE.value),
    (50, c.TerminalCompletionState.COMPLETED_AS_EDGE_HYPOTHESIS_CANDIDATE.value),
    (70, c.TerminalCompletionState.COMPLETED_AS_MICROSTRUCTURE_CANDIDATE.value),
    (20, c.TerminalCompletionState.COMPLETED_AS_QUANTUM_CANDIDATE.value),
    (20, c.TerminalCompletionState.COMPLETED_AS_CLASSICAL_CANDIDATE.value),
    (20, c.TerminalCompletionState.COMPLETED_AS_HYBRID_CANDIDATE.value),
    (10, c.TerminalCompletionState.COMPLETED_AS_REPLAY_PAPER_TEST_CANDIDATE.value),
)


def testable_bucket_state(testable_sequence: int) -> str:
    cursor = 0
    for size, state in _TESTABLE_BUCKETS:
        cursor += size
        if testable_sequence <= cursor:
            return state
    return c.TerminalCompletionState.COMPLETED_AS_REPLAY_PAPER_TEST_CANDIDATE.value


def is_testable_candidate_target(target: Mapping[str, Any]) -> bool:
    return str(target.get("target_population")) == "ATOMICROWS_PARAMETER_RANGE_SOURCE_REQUIRED_530"


def terminal_state_for_target(target: Mapping[str, Any], testable_sequence: int | None) -> str:
    if is_testable_candidate_target(target):
        if testable_sequence is None:
            raise ValueError("testable_sequence is required for testable candidate targets")
        return testable_bucket_state(testable_sequence)
    return c.TerminalCompletionState.COMPLETED_AS_CONNECTOR_FUTURE_ROUTE.value


def terminal_partition_template() -> dict[str, int]:
    return {state.value: 0 for state in c.TerminalCompletionState}

