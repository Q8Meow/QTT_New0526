from .pr161b_test_support import report


def test_pr161b_orchestration_preflight_receipt_consumes_required_artifacts():
    receipt = report("orchestration_preflight")["records"][0]
    assert receipt["receipt_id"] == "PR161B_ORCHESTRATION_PREFLIGHT_RECEIPT"
    assert receipt["active_branch"] == receipt["expected_branch"]
    assert receipt["master_plan_section_count_expected"] == 3006
    assert receipt["master_plan_section_count_observed"] == 3006
    assert receipt["fallback_crosswalk_path_used"] == "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json"
    assert receipt["source_intake_posture"] == "OPEN_CANDIDATE_FIRST"
    assert receipt["owner_pr161b_residual_coverage_approval_recorded"] is True
