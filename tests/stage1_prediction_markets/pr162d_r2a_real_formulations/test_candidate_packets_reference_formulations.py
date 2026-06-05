from __future__ import annotations


def test_candidate_packets_reference_formulations_or_fill_actions(records, summary):
    packets = records("PR162D_R2A_CandidatePacketV1Registry.report.json")
    formulation_ids = {
        row["formulation_id"]
        for row in records("PR162D_R2A_FormulationRecordRegistry.report.json")
    }
    assert len(packets) == summary["candidate_packet_v1_count"]
    assert len(packets) == summary["formulation_backed_qku_count"]
    assert all(packet.get("formulation_ref") or packet.get("exact_fill_action_ref") for packet in packets)
    assert all(packet["formulation_ref"] in formulation_ids for packet in packets if packet.get("formulation_ref"))
    assert all(packet["packet_only_flag"] is False for packet in packets)
    assert all(packet["route_only_flag"] is False for packet in packets)
    assert all(packet["metadata_only_flag"] is False for packet in packets)
    assert all(packet["quantum_label_only_flag"] is False for packet in packets)
