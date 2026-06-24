from tests.pr168_rp5a._helpers import file_rows, load_rows


def test_validation_dependency_graph_exists() -> None:
    rows = load_rows("validation_dependency_rows")
    assert rows
    assert {row["file_path"] for row in file_rows()} <= {row["file_path_or_prefix"] for row in rows}
