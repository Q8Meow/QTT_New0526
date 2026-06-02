from src.qtt.stage1_prediction_markets.multisource_safe_nonlive_dataset_expansion_strict_qku_coverage import constants as c

from .test_support import records


def test_pr162c_formula_delta_records_are_source_backed():
    formulas = records("PR162C_QKUFormulaRegistryDelta.report.json")

    assert formulas
    assert all(record["source_class"] in c.SOURCE_CLASSES for record in formulas)
    assert all(record["source_locator"] for record in formulas)
    assert all(record["candidate_provisional_flag"] is True for record in formulas)
    assert all(record["not_live_authority"] is True for record in formulas)
