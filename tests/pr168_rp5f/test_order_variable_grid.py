from ._helpers import assert_rows_have_contract


def test_order_variable_grid_is_bounded_and_not_full_cartesian() -> None:
    grids = assert_rows_have_contract("var_grid.jsonl")
    templates = assert_rows_have_contract("var_template.jsonl")

    assert len(grids) == len(templates)
    assert all(row["bounded_grid_flag"] is True for row in grids)
    assert all(row["full_cartesian_persisted_flag"] is False for row in grids)
    assert all(row["grid_generation_mode"] == "BOUNDED_FRONTIER_SAMPLE_NOT_FULL_CARTESIAN" for row in grids)
    assert all(row["grid_size"] <= 500 for row in grids)
    assert all(row["side_values"] == ["YES", "NO"] for row in grids)

