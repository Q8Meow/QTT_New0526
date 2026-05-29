from .pr161a_test_support import records, summary


def test_pr161a_qaoa_candidate_profiles_exist():
    qaoa = records("qaoa_profiles")
    assert len(qaoa) == summary()["qaoa_candidate_profile_count"] == 8
    assert all(record["quantum_profile_type"].startswith("QAOA_") for record in qaoa)

