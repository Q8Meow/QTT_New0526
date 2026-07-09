from __future__ import annotations

from tools import build_pr169_agent_orch1 as builder

from .conftest import jsonl


def test_dag_stage_families_and_edges_are_materialized():
    nodes = jsonl("dag_nodes.jsonl")
    edges = jsonl("dag_edges.jsonl")
    node_classes = {row["node_class"] for row in nodes}
    assert set(builder.DAG_STAGE_FAMILIES) <= node_classes
    assert len(edges) == len(builder.DAG_STAGE_FAMILIES) - 1
    for row in nodes + edges:
        assert row["dag_id"] == "AGENT_ORCH1_DAG"
        assert row["runtime_side_effect_allowed"] is False
        assert row["paper_execution_allowed"] is False
        assert row["live_execution_allowed"] is False
        assert row["llm_provider_call_allowed"] is False
        assert row["connector_read_allowed"] is False
        assert row["connector_write_allowed"] is False
        assert row["authority_boundary"]


def test_task_queue_envelopes_and_workflows_are_joinable():
    queue = jsonl("task_queue.jsonl")
    envelopes = {row["task_id"]: row for row in jsonl("task_env.jsonl")}
    workflows = {row["workflow_id"]: row for row in jsonl("workflows.jsonl")}
    assert queue and envelopes and workflows
    for row in queue:
        assert row["task_id"] in envelopes
        assert row["workflow_id"] in workflows
        assert row["queue_state"] in builder.QUEUE_STATES
        assert row["task_ref"]
        assert row["task_key"]
        assert row["safe_next_route"]


def test_receipts_are_contract_only_and_not_fake_runtime_receipts():
    for file_name in (
        "task_receipts.jsonl",
        "decision_receipts.jsonl",
        "dispute_receipts.jsonl",
        "escalation_receipts.jsonl",
        "handoff_receipts.jsonl",
    ):
        rows = jsonl(file_name)
        assert rows
        for row in rows:
            assert "CONTRACT" in row["receipt_class"]
            assert row["runtime_side_effect_created"] is False
            assert row["fake_receipt_created"] is False
            assert row["paper_execution_created"] is False
            assert row["live_execution_created"] is False
