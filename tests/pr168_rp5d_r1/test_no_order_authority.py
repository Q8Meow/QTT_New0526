from ._helpers import all_rows


def test_no_rows_create_order_authority() -> None:
    assert all(row.get("order_authority_flag") is False for row in all_rows())
