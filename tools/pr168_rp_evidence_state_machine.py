#!/usr/bin/env python3
"""Evidence-tier state machine for PR168-RP."""

from __future__ import annotations


EVIDENCE_TIERS = {
    "REPLAY_AND_PAPER_COMPUTED",
    "REPLAY_COMPUTED_ONLY",
    "PAPER_COMPUTED_ONLY",
    "FORMULA_COMPUTED_TEST_VECTOR_ONLY",
    "FORMULA_ASSIGNED_INPUTS_MISSING",
    "QUANTUM_COEFFICIENT_MAP_INPUT_GAP",
    "TERMINAL_NOT_A_TRADING_FORMULA",
    "TERMINAL_NO_TRADE_NONLIVE",
    "EXTERNAL_SCOUTING_VALUE_CANDIDATE_REPLAY_PAPER_REQUIRED",
    "AGENT_DUTY_SOURCE_GAP_ACTIONABLE",
    "CONNECTOR_CANDIDATE_ROUTE_NOT_BOUND",
    "NEGATIVE_RECOVERY_CANDIDATE_CREATED",
    "NEGATIVE_RECOVERY_EXHAUSTED_TRUE_NEGATIVE",
    "PRETRADE_SIMULATION_CANDIDATE_CREATED",
    "PRETRADE_SIMULATION_INPUT_GAP",
    "PRETRADE_NO_TRADE_DOMINATES",
    "LIVE_CANDIDATE_HANDOFF_ONLY_NOT_ORDER_AUTHORITY",
}

COMPUTED_STATUSES = {
    "COMPUTED_POSITIVE_EDGE",
    "REPAIRED_COMPUTED_POSITIVE_EDGE",
    "COMPUTED_NEGATIVE_EDGE",
    "COMPUTED_NEUTRAL_OR_ZERO_EDGE",
    "FORMULA_ASSIGNED_INPUTS_MISSING",
}


def classify_row(*, inputs_complete: bool, quantum_gap: bool = False, numeric_status: str | None = None) -> str:
    if inputs_complete:
        return "REPLAY_AND_PAPER_COMPUTED"
    if quantum_gap:
        return "QUANTUM_COEFFICIENT_MAP_INPUT_GAP"
    return "FORMULA_ASSIGNED_INPUTS_MISSING"


def validate_evidence_tier(tier: str) -> None:
    if tier not in EVIDENCE_TIERS:
        raise ValueError(f"unknown evidence tier: {tier}")


def validate_computed_status(status: str) -> None:
    if status not in COMPUTED_STATUSES:
        raise ValueError(f"unknown computed status: {status}")
