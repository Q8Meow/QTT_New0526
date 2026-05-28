def test_pr159r_official_source_search_plan_exists(pr159r_artifacts):
    assert pr159r_artifacts["search_plan"]["report_type"] == "PR159R_OFFICIAL_SOURCE_SEARCH_PLAN_REPORT"
    assert pr159r_artifacts["search_plan"]["record_count"] == 869

