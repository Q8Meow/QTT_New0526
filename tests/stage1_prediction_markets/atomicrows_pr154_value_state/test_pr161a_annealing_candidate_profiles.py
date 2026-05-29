from .pr161a_test_support import records, summary


def test_pr161a_annealing_candidate_profiles_exist():
    annealing = records("annealing_profiles")
    assert len(annealing) == summary()["annealing_candidate_profile_count"] == 9
    assert any(record["quantum_profile_type"].startswith("ANNEALING_") for record in annealing)
    assert any(record["quantum_profile_type"].startswith("QUANTUM_INSPIRED_") for record in annealing)

