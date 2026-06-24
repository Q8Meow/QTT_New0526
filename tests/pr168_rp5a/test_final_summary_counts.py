from tests.pr168_rp5a._helpers import file_rows, load_report, load_rows


def test_final_summary_counts() -> None:
    report = load_report("PR168_RP5A_FinalSummary.report.json")
    assert report["files_with_stale_terms_count"] == len(file_rows())
    assert report["row_field_semantic_hit_count"] == len(load_rows("row_field_semantic_hit_rows"))
    assert report["deleted_file_count"] == 0
