def test_pr159r_no_invented_values_or_ranges(pr159r_artifacts):
    accepted_target_ids = {
        record["target_id_or_row_id"]
        for record in pr159r_artifacts["accepted"]["records"]
    }
    for record in pr159r_artifacts["locator_matrix"]["records"]:
        extracted = record["extracted_value_or_range_or_enum_or_null"]
        if extracted is not None:
            assert record["target_id_or_row_id"] in accepted_target_ids
            assert record["target_field_scope_match_flag"] is True
    assert pr159r_artifacts["master"]["invented_value_count"] == 0
