def test_pr159r_exact_agent_ids_only_when_supported(pr159r_artifacts):
    for record in pr159r_artifacts["agent_matrix"]["records"]:
        if record["exact_agent_id_or_null"] is not None:
            assert record["exact_agent_id_supported_by_existing_artifact_flag"] is True

