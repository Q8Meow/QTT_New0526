from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_every_value_dag_rows_exist() -> None:
    assert_rank3_valid()
    assert rows("every_value")
