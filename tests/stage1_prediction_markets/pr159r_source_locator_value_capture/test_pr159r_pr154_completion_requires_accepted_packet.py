def test_pr159r_pr154_completion_requires_accepted_packet(pr159r_artifacts):
    for record in pr159r_artifacts["pr154_completion"]["records"]:
        if record["source_completed_flag"]:
            assert record["accepted_source_packet_ref_or_null"]

