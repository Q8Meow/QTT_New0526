from src.qtt.stage1_prediction_markets.multisource_safe_nonlive_dataset_expansion_strict_qku_coverage import constants as c

from .test_support import report


def test_pr162c_pr152_finalization_after_staged_files_documented():
    summary = report("PR162C_FinalSummary.report.json")

    assert summary["pr152_finalization_currentization_command"] == c.PR152_FINALIZATION_CURRENTIZATION_COMMAND
    assert summary["pr152_finalization_currentization_required_before_validation_gates_flag"] is True
    assert summary["pr152_currentization_result"] == c.PR152_CURRENTIZATION_RESULT_PASS
