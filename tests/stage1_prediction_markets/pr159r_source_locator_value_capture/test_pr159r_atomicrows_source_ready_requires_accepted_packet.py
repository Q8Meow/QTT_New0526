def test_pr159r_atomicrows_source_ready_requires_accepted_packet(pr159r_artifacts):
    for record in pr159r_artifacts["atomic_completion"]["records"]:
        if record["source_ready_flag"]:
            assert record["accepted_source_packet_ref_or_null"]

