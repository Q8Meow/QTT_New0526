from tests.pr168_rp5a._helpers import file_rows, load_rows


def test_qku_formula_identity_dependency_exists() -> None:
    rows = load_rows("qku_formula_identity_dependency_rows")
    assert rows
    assert {row["file_path"] for row in file_rows()} <= {row["file_path"] for row in rows}
