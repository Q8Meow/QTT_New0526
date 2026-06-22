from tests.pr168_gfp2r._helpers import assert_positive_count, record_rows, records


def test_pr168_gfp2r_quantum_formula_variant_coverage_exists() -> None:
    assert_positive_count("quantum_formula_variant_coverage_count")
    assert records("PR168_GFP2R_QuantumFormulaVariantCoverageLedger")["quantum_formula_variant_coverage_count"] > 0
    assert record_rows("PR168_GFP2R_QuantumFormulaVariantCoverageLedger")
