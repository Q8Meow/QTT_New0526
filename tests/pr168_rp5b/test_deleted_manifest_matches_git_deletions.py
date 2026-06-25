from tests.pr168_rp5b._helpers import assert_rp5b_valid, final_summary, load_rows


def test_deleted_manifest_matches_git_deletions() -> None:
    assert_rp5b_valid()
    assert load_rows("deleted_from_active_tree_rows") == []
    assert final_summary()["files_deleted_count"] == 0
