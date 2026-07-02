from tests.pr169_dash1.conftest import jsonl


def test_quantum_rows_are_structural_and_qmap_routed() -> None:
    rows = jsonl("owner_quantum_structural_readiness_view.generated.jsonl")
    assert rows
    row = rows[0]
    assert row["qstruct_ref"]
    assert row["classical_fallback_ref"]
    assert row["interpret_back_map_ref"]
    assert row["QMAP1_activation_route"]
    assert "quantum_advantage_claim" in row["forbidden_authority"]
