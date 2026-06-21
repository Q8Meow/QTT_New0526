from tests.pr168_gfp2.pr168_gfp2_test_support import load


def test_no_metadata_only_quantum_compatibility_pass() -> None:
    quantum = [row for row in load("PR168_GFP2_QuantumStructuralReadinessFullUniverse.report.json") if row["structural_readiness_state"] == "QUANTUM_STRUCTURAL_GAP_ROUTED"]
    assert quantum
    assert all(row["repair_route_if_missing"] for row in quantum[:1000])
