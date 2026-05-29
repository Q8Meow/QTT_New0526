from src.qtt.stage1_prediction_markets.source_intelligence.pr159s_open_intake import constants as c
from tests.stage1_prediction_markets.source_intelligence.pr159s_test_support import load


def test_pr159s_profit_validation_state_does_not_fabricate_results():
    payload = load(c.PROFIT_VALIDATION_STATE_REGISTRY_PATH)
    assert payload["record_count"] == 868
    assert all(record["profit_proven_status_assigned_by_pr159s_flag"] is False for record in payload["records"])
    assert all(record["non_profitable_status_assigned_by_pr159s_flag"] is False for record in payload["records"])
    assert {record["profit_validation_tag"] for record in payload["records"]} == {
        c.ProfitValidationTag.PROFIT_NOT_TESTED.value,
        c.ProfitValidationTag.PROMOTION_EVIDENCE_NOT_IN_SCOPE_FOR_THIS_PR.value,
    }

