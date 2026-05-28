def test_pr159r_candidate_packets_not_accepted_facts(pr159r_artifacts):
    assert all(record["candidate_is_accepted_fact"] is False for record in pr159r_artifacts["candidates"]["records"])

