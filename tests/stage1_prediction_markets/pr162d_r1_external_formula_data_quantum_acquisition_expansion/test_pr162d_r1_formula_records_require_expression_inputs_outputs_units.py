from __future__ import annotations


def test_pr162d_r1_formula_records_require_expression_inputs_outputs_units(records):
    formulas = records("PR162D_R1_FormulaAcquisitionLedger.report.json")
    assert formulas
    assert all(record["expression"] and record["input_fields"] and record["output_fields"] and record["units"] for record in formulas)
