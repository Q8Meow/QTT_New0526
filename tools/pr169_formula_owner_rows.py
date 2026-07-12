from __future__ import annotations

"""Thin row adapter used by existing canonical owner builders.

This module is not a builder and owns no generated surface.  It lets each
existing owner builder project the same bounded PR169 registry input into its
own schema without making the PR169 orchestrator an owner of those files.
"""

import json
from pathlib import Path
from typing import Any


PREFIX = Path("docs/master_plan/generated/pr169_qku_formula_exp1")


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def materialize_from_template(
    template: dict[str, Any], extension: dict[str, Any], old_identity: str, new_identity: str
) -> dict[str, Any]:
    """Preserve an owner's complete schema while replacing its fixture identity."""

    def replace(value: Any) -> Any:
        if isinstance(value, str):
            return value.replace(old_identity, new_identity)
        if isinstance(value, list):
            return [replace(item) for item in value]
        if isinstance(value, dict):
            return {key: replace(item) for key, item in value.items()}
        return value

    row = replace(template)
    row.update(extension)
    return row


def _inputs(repo_root: Path) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    requirements = _jsonl(repo_root / PREFIX / "requirements.jsonl")
    by_card: dict[str, list[dict[str, Any]]] = {}
    for binding in _jsonl(repo_root / PREFIX / "bindings.jsonl"):
        by_card.setdefault(str(binding["card_id"]), []).append(binding)
    return requirements, by_card


def rows(repo_root: Path, owner: str) -> list[dict[str, Any]]:
    requirements, bindings = _inputs(repo_root)
    output = []
    for requirement in requirements:
        card_id = str(requirement["card_id"])
        card_bindings = bindings.get(card_id, [])
        qkus = sorted({str(row["qku_id"]) for row in card_bindings if row.get("qku_id")})
        consumers = sorted({str(row["system_consumer_id"]) for row in card_bindings if row.get("system_consumer_id")})
        common = {
            "row_kind": "PR169_FORMULA_OWNER_EXTENSION_V1",
            "card_id": card_id,
            "canonical_formula_id": requirement["canonical_formula_or_procedure_id"],
            "formula_version": requirement["semantic_version"],
            "numeric_authority_chain_id": requirement["numeric_authority_chain_id"],
            "qku_refs": qkus,
            "system_consumer_refs": consumers,
            "responsible_agent_id": requirement["numeric_authority_chain"]["responsible_PR165_D2_agent_duty"],
            "input_contract_ref": requirement["input_contract_ref"],
            "output_contract_ref": requirement["output_contract_ref"],
            "material_consumer_field": requirement["material_consumer_field"],
            "agent_execution_created": False,
            "runtime_execution_created": False,
            "order_authority_created": False,
            "connector_read_created": False,
            "private_cash_read_created": False,
            "quantum_backend_execution_created": False,
            "destination_acknowledged": False,
            "terminal_state": "VALIDATED_ROUTED_UNACKNOWLEDGED_NO_ORDER_AUTHORITY",
        }
        if owner == "READINESS":
            common.update({"readiness_projection_id": f"PR169_FORMULA_READINESS::{card_id}", "candidate_id": f"PR169_FORMULA::{card_id}", "computability_state": "EXECUTABLE_REQUIRES_DECLARED_INPUTS", "applicability_state": "CONTEXT_BOUNDED", "provider_resolution_required": True})
        elif owner == "PRETRADE":
            common.update({"pretrade_projection_id": f"PR169_FORMULA_PRETRADE::{card_id}", "candidate_id": f"PR169_FORMULA::{card_id}", "provider_field_maps": [row["input_field_map"] for row in card_bindings], "consumer_field_maps": [row["output_field_map"] for row in card_bindings], "freshness_policy": "FORMULA_INPUT_RESOLUTION_V1_FAIL_CLOSED"})
        elif owner == "AGENT_ORCH":
            task_ref = f"PR169_FORMULA_TASK::{card_id}"
            common.update({"formula_task_id": task_ref, "row_id": task_ref, "object_type": "AgentQKUFormulaComputeTaskV1", "object_id": f"formula_task::{card_id}", "task_ref": task_ref, "selected_qku_refs": qkus or consumers, "selected_formula_refs": [requirement["canonical_formula_or_procedure_id"]], "full_library_access_used": False, "library_query_receipt_ref_or_gap": f"BOUNDED_QUERY::{card_id}", "stage_profile_ref_or_gap": requirement["eligible_stages"], "market_applicability_ref_or_gap": "prediction_market", "platform_filter_ref_or_gap": "DECLARED_CONTEXT", "agent_duty_filter_ref_or_gap": "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json", "executability_overlay_ref_or_gap": requirement["implementation_state"], "context_filter_ref_or_gap": requirement["applicability_predicate"], "mem1_filter_ref_or_gap": "CONDITION_SCOPED_PRIOR_ONLY", "projection_file": "formula_tasks.jsonl", "generated_from": "docs/master_plan/generated/pr169_agent_orch1/registry.jsonl", "manual_edit_allowed": False, "provider_state": "PROVIDER_PENDING_CONTRACT_ONLY", "provider_stage": "AGENT_ORCH1_STATIC_CONTRACT_PROVIDER_PENDING", "freshness_state": "STATIC_BUILD_CONTRACT_REVALIDATION_REQUIRED", "lifecycle_state": "MATERIALIZED_CONTRACT", "activation_state": "CONTRACT_ACTIVE_NO_RUNTIME", "timing_state": "STATIC_BUILD_TIME_ONLY", "downstream_owner": "PR169-AGENT-ORCH1", "authority_state": "CONTROL_PLANE_ONLY_NO_ORDER_AUTHORITY", "queue_state": "QUEUED", "task_state": "TASK_CONTRACT_READY_NO_RUNTIME", "retry_state": "RETRY_AVAILABLE_NOT_STARTED", "projection_consumers": ["src/qtt/agents/pr169_agent_orch1_resolvers.py"], "orphan_status": "NOT_ORPHAN"})
        elif owner == "SVC":
            registry_row_id = f"PR169_FORMULA_SVC::{card_id}"
            common.update({"svc_projection_id": registry_row_id, "registry_row_id": registry_row_id, "source_registry_row_id": registry_row_id, "source_registry_ref": f"docs/master_plan/generated/pr169_svc1/service_registry.jsonl::{registry_row_id}", "formula_refs": [requirement["canonical_formula_or_procedure_id"]], "computable_contract_refs_or_gap": [f"PR169_FORMULA_READINESS::{card_id}"], "agent_task_ref": f"PR169_FORMULA_TASK::{card_id}", "pretrade_ref": f"PR169_FORMULA_PRETRADE::{card_id}", "owner_visible_state": "CONFIGURATION_AND_LAST_TYPED_RECEIPT_ONLY", "runtime_llm_call_created": False, "runtime_agent_execution_created": False, "responsible_agent_role_refs": [common["responsible_agent_id"]], "projection_file": "qku_formula_compute_route_views.generated.jsonl", "generated_from": "docs/master_plan/generated/pr169_svc1/service_registry.jsonl", "manual_edit_allowed": False, "orphan_status": "NOT_ORPHAN", "lifecycle_state": "MATERIALIZED_CONTRACT", "timing_state": "STATIC_BUILD_TIME_ONLY", "provider_state": "PROVIDER_PENDING_CONTRACT_ONLY", "freshness_state": "STATIC_BUILD_CONTRACT_REVALIDATION_REQUIRED", "authority_state": "CONTROL_PLANE_ONLY_NO_ORDER_AUTHORITY"})
        else:
            raise ValueError(owner)
        output.append(common)
    return output
