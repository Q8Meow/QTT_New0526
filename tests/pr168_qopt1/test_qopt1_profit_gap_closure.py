from ._helpers import rows


def test_profit_gap_closure_never_forces_fake_profit_or_formula_mutation() -> None:
    gap_rows = rows("profit_gap_close.jsonl")
    assert gap_rows
    gap_types = {row["gap_type"] for row in gap_rows}
    assert {"NO_TRADE_MARGIN", "LCB", "TCA", "FILL", "LATENCY", "CAPACITY"} <= gap_types
    for row in gap_rows:
        assert row["fake_profit_forcing_flag"] is False
        assert row["formula_mutation_flag"] is False
