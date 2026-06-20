from __future__ import annotations

import pytest

from tools import qtt_authority_reason_code_registry as registry


def test_required_reason_codes_are_registered() -> None:
    for code in [
        "NO_LIVE_ORDER_AUTHORITY",
        "NO_CONNECTOR_TRUTH_OR_BINDING",
        "NO_SOURCE_TRUTH_AUTHORITY",
        "MISSING_NUMERIC_INPUTS",
        "MISSING_DEFAULT_THRESHOLD",
        "formula_inputs_missing",
        "no_trade_candidate_dominates",
        "FUTURE_LIVE_GATE_REQUIRED",
        "REGISTRY_SEED_CONTRACT_ONLY",
        "NO_FORBIDDEN_AUTHORITY_CREATED",
        "PR168_RANK_PROVISIONAL_RANKING_DEFAULT",
        "PR168_RANK_NO_TRADE_SURFACE_SELECTED",
    ]:
        assert code in registry.all_reason_code_names()


def test_unknown_codes_fail_closed() -> None:
    with pytest.raises(KeyError):
        registry.get_authority_boundary_code("UNKNOWN")
    with pytest.raises(KeyError):
        registry.get_gap_reason_code("UNKNOWN")
    with pytest.raises(KeyError):
        registry.get_negative_recovery_reason_code("UNKNOWN")
    with pytest.raises(KeyError):
        registry.get_pretrade_decision_reason_code("UNKNOWN")


def test_connector_boundary_is_candidate_only() -> None:
    code = registry.get_authority_boundary_code("NO_CONNECTOR_TRUTH_OR_BINDING")
    assert code["connector_truth_authority"] is False
    assert code["connector_semantic_binding_state"] == "NOT_BOUND_CANDIDATE_ONLY"
