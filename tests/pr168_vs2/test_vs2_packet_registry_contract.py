from .test_support import packet_ids, read_jsonl


def test_registry_indexes_every_packet() -> None:
    packets = packet_ids()
    registry = {row["paper_intent_candidate_id"] for row in read_jsonl("vs2_packet_registry.jsonl")}
    assert registry == packets


def test_packet_access_contract_points_future_consumers_to_central_surfaces() -> None:
    for row in read_jsonl("packet_access_contract.jsonl"):
        assert row["current_pr_source_of_truth_ref"].endswith("vs2_packet_registry.jsonl")
        assert any(ref.endswith("paper_loop_packet.jsonl") for ref in row["paper_loop_primary_inputs"])
        assert any(ref.endswith("mem1_handoff.jsonl") for ref in row["mem1_primary_inputs"])
