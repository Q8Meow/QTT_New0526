from src.qtt.stage1_prediction_markets.source_intelligence.pr159s_open_intake import constants as c
from tests.stage1_prediction_markets.source_intelligence.pr159s_test_support import load


def test_pr159s_algorithm_formula_parameter_candidates_are_testable_not_profit_claims():
    payload = load(c.ALGORITHM_FORMULA_CANDIDATE_DELTA_PATH)
    assert payload["record_count"] == 480
    states = payload["candidate_state_counts"]
    assert states[c.TerminalCompletionState.COMPLETED_AS_ALGORITHM_CANDIDATE.value] == 70
    assert states[c.TerminalCompletionState.COMPLETED_AS_FORMULA_CANDIDATE.value] == 60
    assert states[c.TerminalCompletionState.COMPLETED_AS_PARAMETER_CANDIDATE.value] == 160
    assert all(record["profit_validation_tag"] == c.ProfitValidationTag.PROFIT_NOT_TESTED.value for record in payload["records"])

