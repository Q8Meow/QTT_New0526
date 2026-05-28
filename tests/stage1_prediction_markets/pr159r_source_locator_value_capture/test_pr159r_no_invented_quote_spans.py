def test_pr159r_no_invented_quote_spans(pr159r_artifacts):
    accepted_candidate_ids = {
        record["candidate_packet_id"]
        for record in pr159r_artifacts["accepted"]["records"]
    }
    for record in pr159r_artifacts["candidates"]["records"]:
        locator = record["quote_span_or_machine_field_locator"]
        assert locator["locator"] or locator["quote_span"] or locator["machine_field_locator"]
        if record["extracted_value_or_range_or_enum_or_null"] is not None:
            assert record["candidate_packet_id"] in accepted_candidate_ids
            assert record["target_field_scope_match_flag"] is True
