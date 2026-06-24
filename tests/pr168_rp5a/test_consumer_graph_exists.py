from tests.pr168_rp5a._helpers import file_rows, load_rows


def test_consumer_graph_exists() -> None:
    rows = load_rows("consumer_graph_rows")
    assert rows
    assert {row["file_path"] for row in file_rows()} <= {row["file_path"] for row in rows}
