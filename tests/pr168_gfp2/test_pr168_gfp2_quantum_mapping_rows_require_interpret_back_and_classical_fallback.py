from tests.pr168_gfp2.pr168_gfp2_test_support import load


def test_quantum_mapping_rows_require_interpret_back_and_classical_fallback() -> None:
    for row in load("PR168_GFP2_QUBO_BQM_CQM_Ising_QuadraticProgramMappingQueue.report.json")[:1000]:
        assert row["classical_fallback_exists"] is True
        if row["structural_readiness_state"] == "QUANTUM_STRUCTURAL_GAP_ROUTED":
            assert row["interpret_back_map_exists"] is False
            assert row["repair_route_if_missing"]
