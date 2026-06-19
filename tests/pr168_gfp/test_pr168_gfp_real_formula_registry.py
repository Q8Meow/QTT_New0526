from src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.registry import (
    get_formula_by_family,
    get_formula_registry,
    get_required_formula_set_registry,
    validate_formula_registry_contract,
)
from src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.validator import _high_risk_formula_issues


def test_formula_registry_has_required_contract_fields():
    contract = validate_formula_registry_contract()

    assert contract["formula_count"] == 35
    assert contract["missing_expression"] == 0
    assert contract["missing_source"] == 0
    assert contract["missing_variable_map"] == 0
    assert contract["missing_function_path"] == 0


def test_required_formula_sets_reference_real_formula_ids():
    formulas = get_formula_registry()
    required_sets = get_required_formula_set_registry()

    assert "PR168_GFP_RFS_TRADABLE_BINARY_CONTRACT_MINIMUM" in required_sets
    for required_set in required_sets.values():
        assert required_set["formula_ids"]
        assert required_set["required_formula_set_is_computed_evidence"] is False
        for formula_id in required_set["formula_ids"]:
            assert formula_id in formulas
            assert formulas[formula_id]["formula_expression"]


def test_formula_by_family_returns_copy():
    formula = get_formula_by_family("GROSS_EDGE")
    formula["formula_expression"] = "mutated"

    assert get_formula_by_family("GROSS_EDGE")["formula_expression"] == "predicted_probability - market_implied_probability"


def test_high_risk_registry_formulas_have_consistent_semantics():
    formulas = get_formula_registry()

    assert formulas["PR168_GFP_FORMULA_CHAMPION_CHALLENGER_ARBITRATION"]["computation_function_name"] == "champion_challenger_score"
    assert formulas["PR168_GFP_FORMULA_PARTIAL_FILL"]["computation_function_name"] == "partial_fill_penalty"
    assert formulas["PR168_GFP_FORMULA_BINARY_CONTRACT_EXPECTED_VALUE"]["unit_contract"].startswith("payout_if_win_is_net_profit")

    for formula_id in [
        "PR168_GFP_FORMULA_CHAMPION_CHALLENGER_ARBITRATION",
        "PR168_GFP_FORMULA_ROBUST_COVARIANCE_OR_HRP_CLUSTER",
        "PR168_GFP_FORMULA_SPREAD_COST",
        "PR168_GFP_FORMULA_PARTIAL_FILL",
        "PR168_GFP_FORMULA_BINARY_CONTRACT_EXPECTED_VALUE",
        "PR168_GFP_FORMULA_CLASSICAL_FALLBACK_OBJECTIVE",
    ]:
        assert _high_risk_formula_issues(formulas[formula_id]) == []
