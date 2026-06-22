from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_formula_ontology_has_required_domains() -> None:
    rows = records("PR168_MAP3_FormulaOntology.report.json")
    assert rows
    for row in rows:
        assert row["ontology_category"]
        assert row["ontology_subcategory"]
        assert row["input_domain"]
        assert row["output_domain"]
        assert row["prediction_market_role"]
