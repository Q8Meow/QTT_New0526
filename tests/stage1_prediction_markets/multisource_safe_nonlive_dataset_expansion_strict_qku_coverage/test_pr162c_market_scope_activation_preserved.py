from src.qtt.stage1_prediction_markets.multisource_safe_nonlive_dataset_expansion_strict_qku_coverage import constants as c

from .test_support import records


def test_pr162c_market_scope_activation_preserved():
    market = records("PR162C_QKUMarketClassificationContinuityAudit.report.json")
    activation = records("PR162C_QKUStage1ActivationContinuityAudit.report.json")
    dormancy = records("PR162C_QKUDormancyContinuityAudit.report.json")

    assert len(market) == len(activation) == len(dormancy) == 9360
    assert all(record["primary_market_scope"] in c.MARKET_SCOPES for record in market)
    assert all(record["stage1_prediction_market_activation_status"] in c.ACTIVATION_STATUSES for record in activation)
    assert all(record["dormant_qku_execution_router_excluded_flag"] is True for record in dormancy)
