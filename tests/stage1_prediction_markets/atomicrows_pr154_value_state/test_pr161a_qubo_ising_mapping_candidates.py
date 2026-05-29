from .pr161a_test_support import records, summary


def test_pr161a_qubo_ising_mapping_candidates_exist():
    mappings = records("qubo_ising")
    assert len(mappings) == summary()["qubo_candidate_count"] + summary()["ising_candidate_count"]
    assert all(record["classical_baseline_formula_id"] for record in mappings)

