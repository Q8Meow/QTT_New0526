from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_model_risk_fdr_lcb_states_present() -> None:
    assert_recovery1_valid()
    assert all(row["FDR_state"] and row["LCB_state"] for row in rows("recovery_attribution"))
