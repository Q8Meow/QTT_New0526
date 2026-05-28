def test_pr159r_accepted_packets_require_target_field_match(pr159r_artifacts):
    assert all(record["target_field_scope_match_flag"] is True for record in pr159r_artifacts["accepted"]["records"])

