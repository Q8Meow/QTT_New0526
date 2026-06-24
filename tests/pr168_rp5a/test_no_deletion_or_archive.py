from tests.pr168_rp5a._helpers import load_report


def test_no_deletion_or_archive() -> None:
    report = load_report("PR168_RP5A_NoDeletionProof.report.json")
    assert report["deleted_file_count"] == 0
    assert report["moved_file_count"] == 0
    assert report["archived_file_count"] == 0
    assert report["legacy_artifact_content_modified_count"] == 0
