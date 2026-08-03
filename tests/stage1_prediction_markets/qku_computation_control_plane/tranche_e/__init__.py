"""Shared typed fixtures for the compact ST12-E test matrices."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Mapping

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.agent_policy import (
    EXPLICIT_ABSENCE,
    NO_EFFECT_PROFILE_REF,
    POLICY_VERSION,
    AgentBoundaryStateViewV1,
    AgentCapabilityBundleV1,
    AgentCapabilityPolicyStoreV1,
    AgentCapabilityResolverV1,
    AgentSafetyStateV1,
)


TEST_BUNDLE_ID = "ST12E_TEST_BUNDLE"
TEST_CONTEXT_REF = "CTX::ST12E::TEST"
TEST_PRINCIPAL_ID = "parameter_selector_agent"
TEST_SOURCE_AGENT_ID = "AGENT_NL_10"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


@lru_cache(maxsize=1)
def policy_store() -> AgentCapabilityPolicyStoreV1:
    return AgentCapabilityPolicyStoreV1.from_generated(repo_root())


def task_envelope(
    *,
    operation_id: str = "resolve_identity",
    principal_id: str = TEST_PRINCIPAL_ID,
    current_agent_id: str = TEST_PRINCIPAL_ID,
    source_agent_ids: tuple[str, ...] = (TEST_SOURCE_AGENT_ID,),
    role_ref: str = "RANKING_AGENT",
    duty_ref: str = "RANKING_AGENT",
    overrides: Mapping[str, object] | None = None,
) -> dict[str, object]:
    snapshot = policy_store().snapshot
    task_row = next(iter(snapshot.agent_orch_task_rows.values()))
    envelope: dict[str, object] = {
        "principal_id": principal_id,
        "current_agent_id": current_agent_id,
        "certified_source_agent_ids": source_agent_ids,
        "role_ref": role_ref,
        "duty_ref": duty_ref,
        "task_id": str(task_row["task_id"]),
        "operation_id": operation_id,
        "objective_ref": "OBJECTIVE::NO_EFFECT_QKU_REVIEW",
        "prohibited_objective_refs": (
            "SOURCE_TRUTH",
            "MODE_ACTIVATION",
            "ORDER_RELEASE",
        ),
        "qku_scope_refs": ("QKU::ST12E::TEST",),
        "formula_scope_refs": ("MATH-01",),
        "data_scope_refs": ("PUBLIC_TEST_PACKET",),
        "tool_scope_refs": ("QKUComputationControlPlaneV1",),
        "action_scope_refs": ("REQUEST_AGENT_TASK",),
        "context_ref": TEST_CONTEXT_REF,
        "market_scope": "prediction_market",
        "venue_scope": "NO_PROVIDER_ACCESS",
        "candidate_scope_ref": "TradePlanCandidateV1::TEST",
        "portfolio_scope_ref_or_none": EXPLICIT_ABSENCE,
        "mode_eligibility_ref_without_activation": EXPLICIT_ABSENCE,
        "snapshot_version_requirements": (snapshot.registry_version,),
        "policy_version": POLICY_VERSION,
        "registry_version": snapshot.registry_version,
        "implementation_version_requirements": ("MATH-01::1.1R1",),
        "deadline": "2099-01-01T00:00:00+00:00",
        "latency_class": "NO_EFFECT_OFFLINE",
        "idempotency_key": "ST12E_IDEMPOTENCY::TEST",
        "retry_policy_ref": str(task_row["retry_policy_ref_or_gap"]),
        "money_budget": 0,
        "compute_budget": 1,
        "token_budget": 0,
        "tool_call_budget": 0,
        "external_call_budget": 0,
        "peer_challenge_requirement": False,
        "segregation_of_duties_requirement": True,
        "abstention_route": "ABSTAIN_AND_OWNER_REVIEW",
        "quarantine_route": "AGENT_ORCH1_QUARANTINE_ROUTE",
        "owner_escalation_route": "OWNER_REVIEW_REQUIRED",
        "no_effect_profile_ref": NO_EFFECT_PROFILE_REF,
    }
    if overrides:
        envelope.update(overrides)
    return envelope


def make_resolver(
    *,
    operation_id: str = "resolve_identity",
    envelope_overrides: Mapping[str, object] | None = None,
    bundle_overrides: Mapping[str, object] | None = None,
    boundary_state: AgentBoundaryStateViewV1 | None = None,
) -> AgentCapabilityResolverV1:
    bundle_values: dict[str, object] = {
        "bundle_id": TEST_BUNDLE_ID,
        "principal_id": TEST_PRINCIPAL_ID,
        "current_agent_id": TEST_PRINCIPAL_ID,
        "certified_source_agent_ids": (TEST_SOURCE_AGENT_ID,),
        "role_ref": "RANKING_AGENT",
        "duty_ref": "RANKING_AGENT",
        "permission_scope": (
            "research",
            "summarize",
            "critique",
            "explain",
            "propose",
            "route",
        ),
    }
    if bundle_overrides:
        bundle_values.update(bundle_overrides)
    bundle_values["task_envelope"] = task_envelope(
        operation_id=operation_id,
        principal_id=str(bundle_values["principal_id"]),
        current_agent_id=str(bundle_values["current_agent_id"]),
        source_agent_ids=tuple(bundle_values["certified_source_agent_ids"]),
        role_ref=str(bundle_values["role_ref"]),
        duty_ref=str(bundle_values["duty_ref"]),
        overrides=envelope_overrides,
    )
    bundle_values["boundary_state"] = boundary_state or AgentBoundaryStateViewV1(
        state=AgentSafetyStateV1.GREEN,
        state_ref="ST12D_SAFETY_STATE::READ_ONLY_TEST",
        observed_at="2026-08-02T00:00:00+00:00",
        valid_until="2099-01-01T00:00:00+00:00",
    )
    bundle = AgentCapabilityBundleV1(**bundle_values)
    return AgentCapabilityResolverV1(
        policy_store(), {str(bundle_values["bundle_id"]): bundle}
    )


def resolve_decision(
    resolver: AgentCapabilityResolverV1,
    *,
    request_id: str = "REQUEST::ST12E::TEST",
    principal_id: str = TEST_PRINCIPAL_ID,
    capability_bundle_id: str = TEST_BUNDLE_ID,
    operation_id: str = "resolve_identity",
    context_ref: str = TEST_CONTEXT_REF,
    requested_scope_refs: Mapping[str, tuple[str, ...]] | None = None,
    requested_parameter_ids: tuple[str, ...] = (),
    request_idempotency_key: str | None = "ST12E_IDEMPOTENCY::TEST",
):
    return resolver.resolve(
        request_id=request_id,
        principal_id=principal_id,
        capability_bundle_id=capability_bundle_id,
        operation_id=operation_id,
        context_ref=context_ref,
        requested_scope_refs=requested_scope_refs,
        requested_parameter_ids=requested_parameter_ids,
        request_idempotency_key=request_idempotency_key,
    )
