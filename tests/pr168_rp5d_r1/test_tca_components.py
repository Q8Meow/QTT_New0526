from ._helpers import read_jsonl


def test_tca_components_include_required_parts() -> None:
    row = read_jsonl("tca_comp.jsonl")[0]
    assert "fees_model_readiness" in row
    assert "spread_model_readiness" in row
    assert "slippage_model_readiness" in row
    assert row["real_venue_fee_truth_flag"] is False
