from src.qtt.stage1_prediction_markets.multisource_safe_nonlive_dataset_expansion_strict_qku_coverage import constants as c

from .test_support import records


def test_pr162c_qku_execution_classification_no_silent_placeholders():
    qkus = records("PR162C_QKUExecutionClassificationRegistry.report.json")

    assert len(qkus) == 9360
    assert len({record["qku_id"] for record in qkus}) == 9360
    assert all(record["primary_execution_class"] in c.QKU_EXECUTION_CLASSES for record in qkus)
    assert all(record["primary_market_scope"] in c.MARKET_SCOPES for record in qkus)
    assert all(record["blocker_code"] != "NONE" for record in qkus if record["primary_execution_class"] == c.EXECUTION_METADATA_ONLY_BLOCKED)
