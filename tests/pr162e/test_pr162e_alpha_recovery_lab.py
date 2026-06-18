from tests.pr162e.helpers import records


def test_alpha_recovery_lab_has_expected_score_components():
    row = records("PR162E_AlphaRecoveryLab.report.json")[0]
    assert "expected_repair_value" in row
    assert "expected_post_repair_score_components" in row
