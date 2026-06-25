from tests.pr168_rp5b._helpers import final_summary, load_rows
from tools.pr168_rp5b_config import ZERO_DELETION_RESULT_NOTE


def test_final_summary_counts() -> None:
    summary = final_summary()
    assert summary["cleanup_candidate_count"] == len(load_rows("cleanup_candidate_rows"))
    assert summary["files_kept_count"] == len(load_rows("legacy_keep_reason_rows"))
    assert summary["semantic_supersession_row_count"] == len(load_rows("legacy_semantic_supersession_rows"))
    assert summary["files_deleted_count"] == 0
    assert summary["safe_delete_candidate_count"] == 0
    assert summary["cleanup_result_note"] == ZERO_DELETION_RESULT_NOTE
