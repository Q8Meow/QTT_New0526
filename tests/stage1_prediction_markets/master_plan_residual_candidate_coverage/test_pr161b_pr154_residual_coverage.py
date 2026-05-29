from .pr161b_test_support import records, summary


def test_pr161b_pr154_residual_coverage_maps_candidates_to_targets():
    assert summary()["pr154_residual_mapping_count"] > 0
    assert records("pr154_residual")[0]["covered_by_pr154_target_ids"]
