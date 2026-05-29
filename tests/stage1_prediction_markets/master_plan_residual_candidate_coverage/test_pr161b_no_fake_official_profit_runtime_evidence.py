from .pr161b_test_support import assert_no_runtime_authority, report, summary


def test_pr161b_no_fake_official_profit_runtime_evidence():
    assert summary()["official_facts_profit_replay_paper_live_execution_fabricated_flag"] is False
    for name in ("candidate_inventory", "quantum_optimizer", "final_summary"):
        assert_no_runtime_authority(report(name))
