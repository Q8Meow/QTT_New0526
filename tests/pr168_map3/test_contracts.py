from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_formula_contracts_are_not_metadata_only() -> None:
    rows = records("PR168_MAP3_PluginContracts.report.json")
    assert rows
    for row in rows:
        assert row["contract_family"] == "FormulaPluginContractV1"
        assert row["metadata_only_formula_pass_flag"] is False
        assert row["safe_formula_expression_or_semantic_definition"]
