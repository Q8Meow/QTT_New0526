from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_quantum_map_has_structure_without_backend_or_advantage() -> None:
    rows = records("PR168_MAP3_QMap.report.json")
    assert rows
    for row in rows:
        assert row["candidate_stack_variable_id"]
        assert row["linear_coefficient_sources"]
        assert row["constraint_sources"]
        assert row["quantum_backend_execution_flag"] is False
        assert row["quantum_advantage_claim_flag"] is False
