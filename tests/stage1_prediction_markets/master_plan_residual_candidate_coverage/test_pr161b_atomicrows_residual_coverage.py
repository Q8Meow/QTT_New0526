from .pr161b_test_support import records, summary


def test_pr161b_atomicrows_residual_coverage_maps_candidates_to_rows():
    assert summary()["atomicrows_residual_mapping_count"] > 0
    assert records("atomicrows_residual")[0]["covered_by_atomicrows_row_ids"]
