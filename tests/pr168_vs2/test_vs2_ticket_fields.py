from .test_support import packet_ids, read_jsonl


def test_ticket_fields_cover_every_packet() -> None:
    packets = packet_ids()
    covered = {row["paper_intent_candidate_id"] for row in read_jsonl("paper_ticket_fields.jsonl")}
    assert covered == packets


def test_ticket_field_map_has_required_source_and_completion_route() -> None:
    for row in read_jsonl("paper_ticket_field_map.jsonl"):
        assert row["required_for_paper_loop_flag"] is True
        assert row["source_ref"]
        assert row["completion_route_if_missing"].endswith("packet_completion_queue.jsonl")
