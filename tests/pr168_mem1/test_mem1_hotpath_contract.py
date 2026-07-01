from .test_support import read_jsonl


def test_hotpath_index_requires_current_revalidation_and_no_execution() -> None:
    row = read_jsonl("hotpath_memory_index.jsonl")[0]
    assert row["hot_path_allowed_use"] == "retrieve top condition-matched priors quickly for replay/paper verification"
    assert row["hot_path_not_allowed_use"] == "skip current replay/paper validation or submit orders"
    assert row["snapshot_freshness_revalidation_required"] is True
    assert row["paper_or_live_authority_created_flag"] is False
