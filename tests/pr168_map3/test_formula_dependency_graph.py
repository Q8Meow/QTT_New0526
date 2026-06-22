from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_formula_dependency_graph_has_inputs_sources_and_unit_refs() -> None:
    rows = records("PR168_MAP3_FormulaDependencyGraph.report.json")
    assert rows
    for row in rows:
        assert row["depends_on_input_ids"]
        assert row["depends_on_source_ids"]
        assert row["depends_on_unit_normalization_refs"]
