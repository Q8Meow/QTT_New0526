from tests.pr168_rp5a._helpers import file_rows, load_rows


def test_blast_radius_exists() -> None:
    rows = load_rows("blast_radius_rows")
    assert rows
    assert {row["file_path"] for row in file_rows()} == {row["file_path"] for row in rows}
