def test_pr159r_target_agent_applicability_no_orphan_matrix_exists(pr159r_artifacts):
    assert pr159r_artifacts["agent_matrix"]["record_count"] == 869

