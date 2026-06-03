from __future__ import annotations


def test_pr162d_r1_maps_every_external_candidate_to_qku_agent_replay_paper(records):
    candidates = records("PR162D_R1_ComputableCandidateRegistry.report.json")
    assert candidates
    assert all(record["qku_refs"] for record in candidates)
    assert all(record.get("agent_refs") or record.get("agent_route_refs") for record in candidates)
    assert all(record["replay_paper_route_refs"] for record in candidates)
