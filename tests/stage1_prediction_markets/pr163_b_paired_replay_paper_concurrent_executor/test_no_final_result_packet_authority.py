def test_no_final_result_packet_authority(summary):
    assert summary["final_replay_result_packet_authority_count"] == 0
    assert summary["final_paper_result_packet_authority_count"] == 0
