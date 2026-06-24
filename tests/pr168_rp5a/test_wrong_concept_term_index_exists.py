from tests.pr168_rp5a._helpers import load_rows


def test_wrong_concept_term_index_exists() -> None:
    rows = load_rows("wrong_concept_term_rows")
    assert rows
    assert any(row["matched_file_count"] > 0 for row in rows)
