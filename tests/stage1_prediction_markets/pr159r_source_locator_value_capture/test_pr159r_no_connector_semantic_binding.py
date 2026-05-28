def test_pr159r_no_connector_semantic_binding(pr159r_artifacts):
    assert pr159r_artifacts["master"]["no_authority_confirmation"]["connector_semantic_binding_created"] is False

