from __future__ import annotations

import importlib


def test_classical_comparator_mappings_are_importable(records, summary):
    rows = records("PR162D_R2A_ClassicalComparatorRegistry.report.json")
    assert len(rows) == summary["real_classical_comparator_count"]
    assert len(rows) >= 25
    for row in rows:
        module_name, attr = row["callable_ref"].split(":", 1)
        assert callable(getattr(importlib.import_module(module_name), attr))
        assert row["procedure"]
        assert row["compared_quantum_family"]
