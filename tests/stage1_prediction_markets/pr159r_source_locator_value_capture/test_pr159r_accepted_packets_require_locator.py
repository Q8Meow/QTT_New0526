def test_pr159r_accepted_packets_require_locator(pr159r_artifacts):
    assert all(record["locator_valid_flag"] is True for record in pr159r_artifacts["accepted"]["records"])

