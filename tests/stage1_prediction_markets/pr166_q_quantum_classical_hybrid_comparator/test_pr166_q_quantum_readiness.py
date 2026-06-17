from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_q_quantum_structural_readiness_materializes_all_families():
    rows = assert_report_contract("PR166_Q_QuantumStructuralReadiness.report.json", 559)
    first = rows[0]
    assert first["qubo_ready_flag"] is True
    assert first["bqm_ready_flag"] is True
    assert first["ising_ready_flag"] is True
    assert first["cqm_ready_flag"] is True
    assert first["dqm_ready_flag"] is True
    assert first["quadratic_program_ready_flag"] is True
    assert first["binary_variables"]
    assert first["bqm_representation_candidate"]["linear"]
    assert first["ising_representation_candidate"]["h"]
    assert first["cqm_representation_candidate"]["constraints"]
    assert first["dqm_representation_candidate"]["cases"]
    assert first["quadratic_program_representation_candidate"]["variables"]
    assert first["quantum_backend_execution_flag"] is False
    assert first["quantum_advantage_claim_flag"] is False


def test_pr166_q_model_family_registries_have_family_specific_payloads():
    families = {
        "PR166_Q_QUBOReadinessRegistry.report.json": "QUBO",
        "PR166_Q_BQMReadinessRegistry.report.json": "BQM",
        "PR166_Q_IsingReadinessRegistry.report.json": "Ising",
        "PR166_Q_CQMReadinessRegistry.report.json": "CQM",
        "PR166_Q_DQMReadinessRegistry.report.json": "DQM",
        "PR166_Q_QuadraticProgramReadinessRegistry.report.json": "QuadraticProgram",
    }
    for filename, family in families.items():
        rows = assert_report_contract(filename, 559)
        assert {row["target_model_family"] for row in rows} == {family}
        assert all(row["model_family_ready_flag"] is True for row in rows)
