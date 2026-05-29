from .pr161a_test_support import records, summary


def test_pr161a_quantum_formula_templates_exist():
    templates = records("quantum_formulas")
    assert len(templates) == summary()["quantum_formula_template_count"] == 7
    families = {template["formula_family"] for template in templates}
    assert "QUBO_OBJECTIVE_TEMPLATE" in families
    assert "ISING_OBJECTIVE_TEMPLATE" in families
    assert "QAOA_CANDIDATE_TEMPLATE" in families

