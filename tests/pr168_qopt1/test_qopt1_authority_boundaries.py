from ._helpers import report, rows


def test_authority_boundaries_are_false_everywhere_important() -> None:
    assert report("authority_boundary.report.json")["authority_boundary_pass_flag"] is True
    for filename in ("auth_block.jsonl", "batch_select.jsonl", "qproblem.jsonl", "vs2_handoff.jsonl", "paper_handoff.jsonl"):
        for row in rows(filename):
            assert row["final_champion_selected_flag"] is False
            assert row["paper_order_intent_created_flag"] is False
            assert row["live_authority_created_flag"] is False
            assert row["true_quantum_backend_execution_flag"] is False
            assert row["quantum_advantage_claim_flag"] is False
