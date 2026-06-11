def test_pr166_sm_quantum_priority_is_mapping_only_not_execution(pr166_sm_records):
    rows = pr166_sm_records["PR166_SM_QuantumPriorityAfterReplayPaperRegistry.report.json"]
    assert len(rows) == 6502
    for row in rows[:300]:
        assert row["mapping_structures"]
        assert row["variable_domains"]
        assert row["objective_terms"]
        assert row["constraint_terms"] is not None
        assert row["classical_comparator"]
        assert 0.0 <= row["quantum_mapping_readiness_score"] <= 1.0
        assert row["backend_quantum_execution_created"] is False
        assert row["quantum_advantage_claim_created"] is False
        assert row["quantum_backend_execution_count"] == 0
        assert row["quantum_advantage_claim_count"] == 0


def test_pr166_sm_quantum_mapping_readiness_routes_materialization_actions(pr166_sm_records):
    rows = pr166_sm_records["PR166_SM_QuantumMappingCandidateReadiness.report.json"]
    assert len(rows) == 6502
    assert any(row["downstream_pr_refs"] == ["PR166-Q"] for row in rows)
    assert any(row["downstream_pr_refs"] == ["PR162E-Q"] for row in rows)
    for row in rows[:300]:
        assert row["exact_missing_field"]
        assert row["exact_materialization_action"]
        assert row["solver_family_candidates"]
