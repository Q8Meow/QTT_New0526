import pytest

from src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.decision import (
    lower_confidence_bound_edge,
    no_trade_decision_reason,
    positive_negative_decision,
)
from src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.execution_costs import (
    adverse_selection_penalty,
    capacity_crowding_penalty,
    execution_adjusted_edge,
    explicit_fee_cost,
    implementation_shortfall,
    latency_decay,
    market_impact_penalty,
    partial_fill_penalty,
    queue_nonfill_penalty,
    slippage_cost,
    spread_cost,
)
from src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.pnl import (
    compare_replay_paper_pnl,
    compute_before_after_delta,
    compute_paper_candidate_pnl,
    compute_replay_candidate_pnl,
    net_expected_pnl_candidate,
)
from src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.tca import tca_decomposition


def test_positive_binary_contract_survives_costs_and_lcb():
    spread = spread_cost(0.56, 0.58, "buy", 10)
    fee = explicit_fee_cost(0.001, 10)
    adjusted = execution_adjusted_edge(0.08, spread_cost_value=spread / 10, explicit_fee_cost_value=fee / 10)
    pnl = net_expected_pnl_candidate(10, adjusted)
    lcb = lower_confidence_bound_edge(adjusted, 0.005, 2.0)

    assert adjusted > 0
    assert pnl > 0
    assert positive_negative_decision(pnl, lcb, threshold=0.0)["decision"] == "COMPUTED_POSITIVE_EDGE"


def test_gross_positive_can_become_net_negative_after_tca():
    adjusted = execution_adjusted_edge(
        0.03,
        spread_cost_value=0.01,
        explicit_fee_cost_value=0.005,
        slippage_cost_value=0.02,
        market_impact_value=0.01,
    )
    pnl = net_expected_pnl_candidate(100, adjusted)

    assert adjusted < 0
    assert positive_negative_decision(pnl, adjusted, threshold=0.0)["decision"] == "COMPUTED_NEGATIVE_EDGE"


def test_execution_cost_components_are_directional_and_deterministic():
    assert spread_cost(0.49, 0.51, "buy", 100) == pytest.approx(1.0)
    assert slippage_cost(0.50, 0.53, "buy", 100) == pytest.approx(3.0)
    assert slippage_cost(0.50, 0.47, "sell", 100) == pytest.approx(3.0)
    assert implementation_shortfall(0.50, 0.52, "buy", 100, fees=0.25) == pytest.approx(2.25)
    assert market_impact_penalty(25, visible_depth=100, impact_coefficient=0.2) == pytest.approx(2.5)
    assert adverse_selection_penalty(0.20, adverse_move_size=0.05, quantity=100) == pytest.approx(1.0)
    assert latency_decay(0.08, latency_ms=100, half_life_ms=100) == pytest.approx(0.04)
    assert queue_nonfill_penalty(0.08, fill_probability=0.25) == pytest.approx(0.06)
    assert partial_fill_penalty(0.08, requested_quantity=100, filled_quantity=25) == pytest.approx(0.06)
    assert capacity_crowding_penalty(150, capacity_limit=100, crowding_coefficient=0.2) == pytest.approx(0.1)


def test_tca_decomposition_returns_total_and_components():
    result = tca_decomposition(
        explicit_fees=1,
        spread_cost=2,
        slippage=3,
        market_impact=4,
        adverse_selection_penalty=5,
        implementation_shortfall=6,
        nonfill_or_opportunity_cost=7,
    )
    assert result["total_tca_cost"] == 28
    assert result["market_impact"] == 4


def test_replay_paper_receipts_and_no_trade_reason_are_deterministic():
    replay = compute_replay_candidate_pnl({"position_size": 10, "execution_adjusted_edge": 0.05})
    paper = compute_paper_candidate_pnl({"position_size": 10, "execution_adjusted_edge": 0.03})

    assert replay["net_expected_pnl_candidate"] == pytest.approx(0.5)
    assert paper["net_expected_pnl_candidate"] == pytest.approx(0.3)
    assert compare_replay_paper_pnl(replay, paper)["replay_minus_paper"] == pytest.approx(0.2)
    assert compute_before_after_delta(paper, replay)["before_after_delta"] == pytest.approx(0.2)
    assert no_trade_decision_reason(["CAPACITY_EXCEEDED"]) == "NO_TRADE_DUE_TO_CAPACITY_EXCEEDED"
