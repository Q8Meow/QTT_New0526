from decimal import Decimal

from ._helpers import rows


def test_model_risk_and_uncertainty_reserve_exist() -> None:
    for row in rows("rank_model_risk.jsonl"):
        assert Decimal(row["combined_model_risk_score"]) >= 0
        assert Decimal(row["uncertainty_reserve_cash"]) >= 0
    assert rows("rank_uncert_reserve.jsonl")

