from .pr161a_test_support import records, summary


def test_pr161a_vqe_candidate_profiles_exist():
    vqe = records("vqe_profiles")
    assert len(vqe) == summary()["vqe_candidate_profile_count"] == 5
    assert all(record["quantum_profile_type"].startswith("VQE_") for record in vqe)

