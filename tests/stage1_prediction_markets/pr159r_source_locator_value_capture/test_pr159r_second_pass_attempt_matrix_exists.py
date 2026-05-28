def test_pr159r_second_pass_attempt_matrix_exists(pr159r_artifacts):
    assert pr159r_artifacts["second_pass_attempts"]["record_count"] == 869
    accepted = [
        record
        for record in pr159r_artifacts["second_pass_attempts"]["records"]
        if record["accepted_packet_possible_flag"]
    ]
    assert len(accepted) == pr159r_artifacts["master"]["count_invariant_receipt"]["new_accepted_source_packet_count"]
