from ._helpers import read_jsonl


def test_overfit_fdr_rows_are_readiness_only_not_statistical_proof() -> None:
    rows = read_jsonl("fdr_ctrl.jsonl")
    assert rows
    for row in rows:
        assert row["false_discovery_control_method"] == "BENJAMINI_HOCHBERG_READY"
        assert float(row["fdr_q_default"]) == 0.10
        assert [float(value) for value in row["fdr_q_sensitivity_values"]] == [0.05, 0.10, 0.20]
        assert row["deflated_performance_claim_flag"] is False
