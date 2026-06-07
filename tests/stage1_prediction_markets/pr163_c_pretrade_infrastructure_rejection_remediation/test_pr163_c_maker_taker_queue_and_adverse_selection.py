from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records


def test_pr163_c_maker_taker_queue_and_adverse_selection():
    maker_rows = load_records("PR163_C_MakerTakerQueueModelRegistry.report.json")
    adverse_rows = load_records("PR163_C_AdverseSelectionModelRegistry.report.json")
    assert len(maker_rows) == len(adverse_rows)
    assert all(0 <= row["queue_position_proxy"] <= 1 for row in maker_rows)
    assert all(row["adverse_selection_penalty"] >= 0 for row in adverse_rows)
