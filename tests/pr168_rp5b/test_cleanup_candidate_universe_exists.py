from tests.pr168_rp5b._helpers import final_summary, load_rows


def test_cleanup_candidate_universe_exists() -> None:
    rows = load_rows("cleanup_candidate_rows")
    assert rows
    assert len(rows) == final_summary()["cleanup_candidate_count"]
    assert all(row["rp5b_reverification_required_flag"] is True for row in rows)
    assert {"file_path", "rp5a_classification", "file_kind"}.issubset(rows[0])
