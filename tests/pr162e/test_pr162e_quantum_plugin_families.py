from tests.pr162e.helpers import plugin_rows


def test_quantum_plugin_families_have_classical_fallback_and_no_backend():
    quantum = [row for row in plugin_rows() if "QUANTUM" in row["plugin_family"] or "ADAPTER" in row["plugin_family"]]
    assert quantum
    assert all(row["quantum_structural_readiness"]["backend_execution_forbidden_flag"] for row in quantum)
    assert all(row["classical_fallback_dependency"] for row in quantum)
