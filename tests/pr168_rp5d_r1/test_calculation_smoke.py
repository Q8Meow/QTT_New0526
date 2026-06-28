from ._helpers import read_jsonl


def test_calculation_smoke_is_deterministic_non_profit_evidence() -> None:
    rows = read_jsonl("calc_smoke.jsonl")
    assert len(rows) == len(read_jsonl("promote.jsonl"))
    assert all(row["deterministic_reproducible_flag"] is True for row in rows)
    assert all(row["profit_proof_flag"] is False and row["real_market_evidence_flag"] is False for row in rows)
