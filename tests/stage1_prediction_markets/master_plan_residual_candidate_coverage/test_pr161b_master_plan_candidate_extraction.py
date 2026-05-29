from .pr161b_test_support import candidate_records, summary


def test_pr161b_master_plan_candidate_extraction_has_required_fields():
    assert summary()["master_plan_candidate_extraction_count"] > 0
    sample = candidate_records()[0]
    assert sample["extraction_source_path"] == "docs/master_plan/QTT_MasterPlan_Current.md"
    assert sample["residual_candidate_id"].startswith("PR161B_CANDIDATE_")
    assert sample["normalized_candidate_name"]
    assert sample["candidate_type"]
