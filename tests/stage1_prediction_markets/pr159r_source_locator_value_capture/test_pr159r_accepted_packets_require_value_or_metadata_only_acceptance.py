def test_pr159r_accepted_packets_require_value_or_metadata_only_acceptance(pr159r_artifacts):
    for record in pr159r_artifacts["accepted"]["records"]:
        assert record["accepted_value_or_range_or_enum_or_metadata"] is not None

