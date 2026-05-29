from .pr161a_test_support import records, summary


def test_pr161a_quantum_optimizer_candidate_profiles_exist():
    profiles = records("quantum_profiles")
    assert len(profiles) == summary()["quantum_optimizer_candidate_profile_count"] == 41
    assert all(profile["classical_baseline_required_flag"] is True for profile in profiles)
    assert all(profile["live_use_allowed_flag"] is False for profile in profiles)

