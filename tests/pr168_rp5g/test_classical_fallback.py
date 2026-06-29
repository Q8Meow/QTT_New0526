from decimal import Decimal
from src.qtt.stage1_prediction_markets.pr168_rp5g_trade_plan_sim.classical_fallback import best_classical_candidate


def test_classical_fallback_argmax() -> None:
    row = best_classical_candidate({"a": Decimal("1"), "b": Decimal("2")})
    assert row["best_candidate_id"] == "b"

