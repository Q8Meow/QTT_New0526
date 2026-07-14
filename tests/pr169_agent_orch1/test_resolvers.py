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


class _FakeComputationControlPlane:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    @property
    def physical_layout(self):
        raise AssertionError("the agent facade must not inspect physical storage")

    def resolve(self, selector, context=None, *, agent_id=None):
        self.calls.append(("resolve", selector, context, agent_id))
        return {"resolved": selector}

    def compute(
        self,
        selector,
        inputs,
        context=None,
        *,
        agent_id=None,
        consumer="UNSPECIFIED",
        mode="STATIC_VALIDATION",
    ):
        self.calls.append(
            ("compute", selector, inputs, context, agent_id, consumer, mode)
        )
        return {"receipt_id": "future-receipt"}

    def status(self, selector, context=None, *, agent_id=None):
        self.calls.append(("status", selector, context, agent_id))
        return {"state": "AVAILABLE"}

    def explain(self, receipt_or_selector, context=None, *, agent_id=None):
        self.calls.append(("explain", receipt_or_selector, context, agent_id))
        return {"explanation": "public semantic explanation"}


def test_agent_computation_capabilities_are_generic_and_use_only_public_operations():
    fake = _FakeComputationControlPlane()
    selector = {"component_id": "FUTURE_COMPONENT_9200", "kind": "NEW_KIND"}
    context = {"market_family": "future-market-family"}

    assert resolvers.invoke_computation_capability(
        fake,
        {
            "operation": "resolve",
            "selector": selector,
            "context": context,
            "input_contract": {},
            "policy": {},
        },
        agent_id="agent-next",
    )["resolved"] == selector

    capability = resolvers.AgentComputationCapabilityV1(
        operation="compute",
        selector=selector,
        context=context,
        input_contract={"observations": [1, 2, 3]},
        policy={"consumer": "AGENT_REVIEW", "mode": "REPLAY"},
    )
    assert resolvers.invoke_computation_capability(
        fake,
        capability,
        agent_id="agent-next",
    )["receipt_id"] == "future-receipt"
    assert resolvers.invoke_computation_capability(
        fake,
        {
            "operation": "status",
            "selector": selector,
            "context": context,
            "input_contract": {},
            "policy": {},
        }
    )["state"] == "AVAILABLE"
    assert resolvers.invoke_computation_capability(
        fake,
        {
            "operation": "explain",
            "selector": "future-receipt",
            "context": context,
            "input_contract": {},
            "policy": {},
        }
    )["explanation"] == "public semantic explanation"

    assert [call[0] for call in fake.calls] == ["resolve", "compute", "status", "explain"]
    assert fake.calls[1][1] == selector
    assert fake.calls[1][5:] == ("AGENT_REVIEW", "REPLAY")
