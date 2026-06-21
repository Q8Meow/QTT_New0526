from tests.pr168_gfp2.pr168_gfp2_test_support import root


def test_prior_metadata_only_noncomputable_is_reopened_without_structural_proof() -> None:
    report = root("PR168_GFP2_MetadataNonComputableReopenQueue.report.json")
    assert report["summary"]["metadata_noncomputable_reopen_count"] == 0
    assert report["summary"]["empty_reason"]
