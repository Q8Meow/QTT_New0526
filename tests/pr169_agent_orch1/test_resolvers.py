from __future__ import annotations

from src.qtt.agents import pr169_agent_orch1_resolvers as resolvers
from tools import build_pr169_agent_orch1 as builder

from .conftest import ARTIFACT_DIR, jsonl


def test_agent_orch_service_lists_core_artifacts():
    api = resolvers.AgentOrchService(ARTIFACT_DIR)
    manifest = api.load_manifest()
    assert manifest["canonical_registry_ref"] == builder.REGISTRY_REF
    dag = api.get_dag("AGENT_ORCH1_DAG")
    assert dag["dag_id"] == "AGENT_ORCH1_DAG"
    assert len(api.list_nodes("AGENT_ORCH1_DAG")) == len(builder.DAG_STAGE_FAMILIES)
    assert len(api.list_edges("AGENT_ORCH1_DAG")) == len(builder.DAG_STAGE_FAMILIES) - 1
    assert api.list_tasks()
    assert api.list_task_envelopes()
    assert api.list_workflows()


def test_agent_orch_service_task_and_receipt_lookup():
    api = resolvers.AgentOrchService(ARTIFACT_DIR)
    task = api.list_tasks()[0]
    task_id = task["task_id"]
    assert api.get_task(task_id)["task_id"] == task_id
    assert api.get_task_envelope(task_id)["task_id"] == task_id
    downstream = api.get_downstream_routes(task_id)
    assert downstream
    receipt = api.list_task_receipts()[0]
    assert api.get_task_receipt(receipt["task_id"])["task_id"] == receipt["task_id"]
    assert api.list_decision_receipts()
    assert api.list_dispute_receipts()
    assert api.list_escalation_receipts()


def test_agent_orch_service_candidate_route_lookup():
    api = resolvers.AgentOrchService(ARTIFACT_DIR)
    candidate_id = jsonl("pretrade_tasks.jsonl")[0]["candidate_id"]
    assert api.get_qku_tasks(candidate_id)
    assert api.get_formula_tasks(candidate_id)
    assert api.get_no_trade_tasks(candidate_id)
    assert api.get_paper_prep(candidate_id)
    assert api.get_hotpath_prep(candidate_id)
    assert api.get_llm_tasks(candidate_id)
    assert api.get_quantum_tasks(candidate_id)
    assert api.get_owner_request_tasks("REQUEST_PRETRADE_RECHECK")
