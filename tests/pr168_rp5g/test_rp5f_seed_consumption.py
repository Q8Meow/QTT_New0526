from ._helpers import assert_rows_have_contract


def test_candidates_reference_rp5f_seeds_targets_and_grids() -> None:
    rows = assert_rows_have_contract("trade_candidate.jsonl")
    assert all(row["trade_seed_id"].startswith("RP5F_SEED_") for row in rows)
    assert all(row["target_id"].startswith("RP5F_TARGET_") for row in rows)
    assert all(row["grid_id"].startswith("RP5F_GRID_") for row in rows)

