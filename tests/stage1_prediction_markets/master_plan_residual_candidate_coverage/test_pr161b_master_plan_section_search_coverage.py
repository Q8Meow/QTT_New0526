from .pr161b_test_support import records, report, summary


def test_pr161b_master_plan_section_search_coverage_accounts_for_every_section():
    payload = report("section_search_coverage")
    assert payload["master_plan_section_count_expected"] == 3006
    assert payload["master_plan_section_count_observed"] == 3006
    assert payload["master_plan_sections_searched_count"] == 3006
    assert payload["master_plan_sections_unsearched_count"] == 0
    assert payload["master_plan_section_search_error_count"] == 0
    assert summary()["sections_with_candidate_like_items_count"] > 0
    for record in records("section_search_coverage"):
        assert record["searched_flag"] is True
        assert record["extraction_pass_ids_applied"]
        if not record["candidate_like_item_found_flag"]:
            assert record["no_candidate_reason_if_none"]
