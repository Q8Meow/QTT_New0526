def test_pr159r_every_target_has_responsible_agent_role_or_consumer_class(pr159r_artifacts):
    assert all(
        record["responsible_agent_role_ids"] or record["consumer_class_ids"]
        for record in pr159r_artifacts["agent_matrix"]["records"]
    )

