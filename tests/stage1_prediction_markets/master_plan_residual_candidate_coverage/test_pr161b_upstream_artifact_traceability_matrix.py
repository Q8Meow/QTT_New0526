from .pr161b_test_support import records, summary


def test_pr161b_upstream_artifact_traceability_matrix_is_complete():
    assert summary()["upstream_artifact_traceability_record_count"] == len(records("upstream_traceability"))
    assert all(record["upstream_pr_ids"] for record in records("upstream_traceability")[:25])
