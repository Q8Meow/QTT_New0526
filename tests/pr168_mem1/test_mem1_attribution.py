from .test_support import read_jsonl


def test_outcome_attribution_separates_signal_and_execution_components() -> None:
    row = read_jsonl("outcome_attribution.jsonl")[0]
    assert row["qku_contribution_estimate"]
    assert row["formula_contribution_estimate"]
    assert row["TCA_contribution"]
    assert row["fill_quality_contribution"]
    assert row["quantum_structural_component_contribution"]
    assert row["attribution_method"]
