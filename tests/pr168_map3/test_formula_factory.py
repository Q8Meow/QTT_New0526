from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_formula_factory_has_contract_or_repair_outputs() -> None:
    rows = records("PR168_MAP3_FormulaFactory.report.json")
    assert any(row["factory_output_state"] == "MATERIALIZED_FORMULA_PLUGIN_CONTRACT" for row in rows)
    assert any(
        row["factory_output_state"] == "SEMANTIC_FORMULA_CANDIDATE_REQUIRES_EXPRESSION_REPAIR"
        for row in rows
    )
    for row in rows:
        assert row["safe_formula_expression_or_semantic_definition"]
        assert row["computability_route"]
        assert row["no_orphan_status"] == "NO_ORPHAN_LINKED"
