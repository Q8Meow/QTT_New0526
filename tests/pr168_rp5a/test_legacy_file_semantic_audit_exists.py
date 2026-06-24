from tests.pr168_rp5a._helpers import file_rows


def test_legacy_file_semantic_audit_exists() -> None:
    rows = file_rows()
    assert rows
    assert all(row["file_path"] and row["matched_terms"] for row in rows)
