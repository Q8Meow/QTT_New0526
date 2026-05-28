def test_pr159r_no_invented_source_packets(pr159r_artifacts):
    assert pr159r_artifacts["master"]["invented_source_packet_count"] == 0
    assert pr159r_artifacts["accepted"]["record_count"] == pr159r_artifacts["master"]["count_invariant_receipt"]["new_accepted_source_packet_count"]
    assert all(record["accepted_packet_id"].startswith("PR159R_ACCEPTED_PACKET__") for record in pr159r_artifacts["accepted"]["records"])
