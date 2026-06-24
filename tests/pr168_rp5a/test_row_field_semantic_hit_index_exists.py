from tests.pr168_rp5a._helpers import load_rows


def test_row_field_semantic_hit_index_exists() -> None:
    rows = load_rows("row_field_semantic_hit_rows")
    assert rows
    assert all(len(row["matched_text_short"]) <= 200 for row in rows[:1000])
