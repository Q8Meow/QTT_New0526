from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_feature_matrix_has_required_institutional_controls() -> None:
    assert_rank3_valid()
    required = {"TCA_total_candidate", "fill_adjusted_expected_pnl", "lower_confidence_bound_edge_or_gap", "FDR_model_risk_state", "source_reliability_penalty_or_gap", "no_trade_margin_candidate"}
    assert all(required <= set(row) for row in rows("feature_matrix"))
