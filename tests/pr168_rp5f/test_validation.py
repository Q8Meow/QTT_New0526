from ._helpers import assert_valid


def test_rp5f_validator_accepts_generated_dynamic_target_layer() -> None:
    result = assert_valid()

    assert result["dynamic_target_count"] == 5
    assert result["order_variable_grid_count"] == 5
    assert result["trade_seed_count"] == 5

