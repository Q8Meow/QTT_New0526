from __future__ import annotations

import importlib


def test_quantum_shape_builders_are_callable(records, summary):
    rows = [
        row for row in records("PR162D_R2A_FormulationRecordRegistry.report.json")
        if row["formulation_type"] == "QUANTUM_FORMULATION"
    ]
    assert len({row["callable_ref"] for row in rows}) == summary["real_quantum_shape_builder_count"]
    assert summary["real_quantum_shape_builder_count"] >= 4
    vectors = {
        row["test_vector_id"]: row
        for row in records("PR162D_R2A_TestVectorRegistry.report.json")
    }
    for row in rows:
        module_name, attr = row["callable_ref"].split(":", 1)
        shape = getattr(importlib.import_module(module_name), attr)(dict(vectors[row["test_vector_refs"][0]]["inputs"]))
        assert shape["objective"]
        assert shape["variables"]
        assert shape["domains"]
        assert shape["classical_comparator_ref"]
        assert shape["backend_execution"] is False
        assert shape["quantum_advantage_claim"] is False
