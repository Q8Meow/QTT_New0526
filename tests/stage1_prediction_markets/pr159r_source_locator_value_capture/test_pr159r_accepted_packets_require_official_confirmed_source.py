def test_pr159r_accepted_packets_require_official_confirmed_source(pr159r_artifacts):
    assert all(record["official_source_confidence"] == "OFFICIAL_CONFIRMED" for record in pr159r_artifacts["accepted"]["records"])

