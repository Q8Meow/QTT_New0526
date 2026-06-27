from __future__ import annotations

from ._helpers import rows


def test_vs1_agent_duty_discovery_and_agent_dag_are_materialized():
    evidence = rows("agent_duty_evidence_discovery_receipts.jsonl")[0]
    dag = rows("vs1_agent_dag_receipts.jsonl")
    node_ids = {row["agent_id"] for row in dag}

    assert evidence["discovery_status"] in {
        "FOUND_CANONICAL_PR165_D2",
        "FOUND_PR165_D2_CANONICAL",
        "FALLBACK_TO_RP5C_CURRENT_AGENT_DUTY_SURFACES",
    }
    assert "CommanderAgent" in node_ids
    assert "GovernanceAgent" in node_ids
    assert all(row["consumer_agent_refs"] for row in dag)
