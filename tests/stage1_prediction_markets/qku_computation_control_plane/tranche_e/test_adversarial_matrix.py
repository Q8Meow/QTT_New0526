"""Bypass, scope, injection, safety, and idempotency ST12-E matrix."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.agent_policy import (
    QUANTUM_FORMULATION_FIELDS,
    QUANTUM_TUPLE_FIELDS,
    AgentBoundaryStateViewV1,
    AgentCapabilityDecisionStateV1,
    AgentSafetyStateV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    AuthorityDeniedError,
    ReasonCode,
)

from . import make_resolver, resolve_decision


@pytest.mark.parametrize(
    ("case_id", "envelope_overrides", "bundle_overrides", "call_overrides", "reason"),
    (
        (
            "principal",
            {},
            {},
            {"principal_id": "unknown_agent"},
            ReasonCode.PRINCIPAL_UNKNOWN,
        ),
        (
            "current-agent",
            {"current_agent_id": "dashboard_agent"},
            {},
            {},
            ReasonCode.PRINCIPAL_AMBIGUOUS,
        ),
        (
            "role",
            {"role_ref": "RISK_AGENT"},
            {},
            {},
            ReasonCode.ROLE_MISMATCH,
        ),
        (
            "duty",
            {"duty_ref": "RISK_AGENT"},
            {},
            {},
            ReasonCode.DUTY_MISMATCH,
        ),
        (
            "bundle-duty-not-current",
            {},
            {"duty_ref": "RISK_AGENT"},
            {},
            ReasonCode.DUTY_MISMATCH,
        ),
        (
            "operation",
            {"operation_id": "compute_component"},
            {},
            {},
            ReasonCode.OPERATION_NOT_ALLOWED,
        ),
        (
            "context",
            {"context_ref": "CTX::OUTSIDE"},
            {},
            {},
            ReasonCode.CONTEXT_SCOPE_MISMATCH,
        ),
        (
            "policy-version",
            {"policy_version": "STALE"},
            {},
            {},
            ReasonCode.TASK_ENVELOPE_STALE,
        ),
        (
            "source-unmapped",
            {},
            {"certified_source_agent_ids": ("AGENT_NL_99",)},
            {},
            ReasonCode.SOURCE_AGENT_ID_UNMAPPED,
        ),
        (
            "permission-broader",
            {},
            {"permission_scope": ("order_authority",)},
            {},
            ReasonCode.SELF_PROMOTION_FORBIDDEN,
        ),
        (
            "no-effect-profile",
            {"no_effect_profile_ref": "GRANTED"},
            {},
            {},
            ReasonCode.SELF_PROMOTION_FORBIDDEN,
        ),
        (
            "mode-activation-state",
            {"mode_eligibility_ref_without_activation": "ALLOW"},
            {},
            {},
            ReasonCode.MODE_ACTIVATION_FORBIDDEN,
        ),
        (
            "formula-mutation",
            {"formula_mutation_requested": True},
            {},
            {},
            ReasonCode.SELF_PROMOTION_FORBIDDEN,
        ),
        (
            "qku-mutation",
            {"qku_mutation_requested": True},
            {},
            {},
            ReasonCode.SELF_PROMOTION_FORBIDDEN,
        ),
        (
            "untyped-effect-flag",
            {"direct_provider_requested": 1},
            {},
            {},
            ReasonCode.TASK_SCOPE_MISMATCH,
        ),
        (
            "segregation-of-duties",
            {"segregation_of_duties_requirement": False},
            {},
            {},
            ReasonCode.SEGREGATION_OF_DUTIES_VIOLATION,
        ),
        (
            "peer-challenge",
            {"peer_challenge_requirement": True},
            {},
            {},
            ReasonCode.PEER_CHALLENGE_REQUIRED,
        ),
        (
            "self-review",
            {"self_review_requested": True},
            {},
            {},
            ReasonCode.SEGREGATION_OF_DUTIES_VIOLATION,
        ),
        (
            "retry",
            {"retry_count": 3},
            {},
            {},
            ReasonCode.RETRY_NOT_ALLOWED,
        ),
        (
            "money-budget",
            {"money_budget": 1},
            {},
            {},
            ReasonCode.BUDGET_EXCEEDED,
        ),
        (
            "deadline",
            {"deadline": "2000-01-01T00:00:00+00:00"},
            {},
            {},
            ReasonCode.DEADLINE_EXCEEDED,
        ),
        (
            "unregistered-tool",
            {"tool_scope_refs": ("QKUComputationControlPlaneV1", "Browser")},
            {},
            {},
            ReasonCode.LLM_TOOL_NOT_ALLOWED,
        ),
        (
            "unregistered-action",
            {"action_scope_refs": ("SUBMIT_ORDER",)},
            {},
            {},
            ReasonCode.ACTION_SCOPE_MISMATCH,
        ),
        (
            "prompt-injection",
            {"untrusted_content_instruction_detected": True},
            {},
            {},
            ReasonCode.UNTRUSTED_CONTENT_INSTRUCTION_REJECTED,
        ),
        (
            "memory-prior",
            {"memory_prior_ref": "MEM1::PRIOR"},
            {},
            {},
            ReasonCode.MEMORY_PRIOR_REVALIDATION_REQUIRED,
        ),
        (
            "quantum-label-only",
            {"quantum_challenger": True, "quantum_formulation_bundle": {"label": "QUBO"}},
            {},
            {},
            ReasonCode.QPU_EFFECT_FORBIDDEN,
        ),
    ),
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_identity_task_and_policy_bypass_attempts_fail_closed(
    case_id: str,
    envelope_overrides: dict[str, object],
    bundle_overrides: dict[str, object],
    call_overrides: dict[str, object],
    reason: ReasonCode,
) -> None:
    del case_id
    decision = resolve_decision(
        make_resolver(
            envelope_overrides=envelope_overrides,
            bundle_overrides=bundle_overrides,
        ),
        **call_overrides,
    )

    assert decision.decision_state is (
        AgentCapabilityDecisionStateV1.OWNER_ESCALATION_REQUIRED
        if reason is ReasonCode.PEER_CHALLENGE_REQUIRED
        else AgentCapabilityDecisionStateV1.DENIED
    )
    assert reason in decision.reason_codes
    assert decision.runtime_effect_authorized is False


@pytest.mark.parametrize(
    ("scope_field", "reason"),
    (
        ("qku_scope_refs", ReasonCode.QKU_SCOPE_MISMATCH),
        ("formula_scope_refs", ReasonCode.FORMULA_SCOPE_MISMATCH),
        ("data_scope_refs", ReasonCode.DATA_SCOPE_MISMATCH),
        ("tool_scope_refs", ReasonCode.TOOL_SCOPE_MISMATCH),
        ("action_scope_refs", ReasonCode.ACTION_SCOPE_MISMATCH),
    ),
)
def test_declared_request_scope_cannot_escape_task_envelope(
    scope_field: str, reason: ReasonCode
) -> None:
    decision = resolve_decision(
        make_resolver(),
        requested_scope_refs={scope_field: ("OUTSIDE_ENVELOPE",)},
    )
    assert decision.decision_state is AgentCapabilityDecisionStateV1.DENIED
    assert reason in decision.reason_codes


def test_parameter_scope_mismatch_fails_closed() -> None:
    decision = resolve_decision(
        make_resolver(),
        requested_parameter_ids=("ST10-PARAM::9999",),
    )
    assert ReasonCode.PARAMETER_SCOPE_MISMATCH in decision.reason_codes
    assert not decision.eligible


@pytest.mark.parametrize(
    ("flag", "reason"),
    (
        ("direct_provider_requested", ReasonCode.DIRECT_PROVIDER_FORBIDDEN),
        ("private_state_requested", ReasonCode.PRIVATE_STATE_FORBIDDEN),
        ("accepted_source_truth_requested", ReasonCode.SOURCE_TRUTH_FORBIDDEN),
        (
            "replay_paper_effect_requested",
            ReasonCode.REPLAY_PAPER_EFFECT_FORBIDDEN,
        ),
        ("llm_inference_requested", ReasonCode.LLM_INFERENCE_FORBIDDEN),
        ("qpu_effect_requested", ReasonCode.QPU_EFFECT_FORBIDDEN),
        ("mode_activation_requested", ReasonCode.MODE_ACTIVATION_FORBIDDEN),
        ("order_release_requested", ReasonCode.ORDER_RELEASE_FORBIDDEN),
        ("capital_effect_requested", ReasonCode.CAPITAL_EFFECT_FORBIDDEN),
        (
            "execution_router_bypass_requested",
            ReasonCode.EXECUTION_ROUTER_BYPASS_FORBIDDEN,
        ),
        ("self_promotion_requested", ReasonCode.SELF_PROMOTION_FORBIDDEN),
        (
            "self_quarantine_release_requested",
            ReasonCode.SELF_QUARANTINE_RELEASE_FORBIDDEN,
        ),
        ("qku_mutation_requested", ReasonCode.SELF_PROMOTION_FORBIDDEN),
        ("formula_mutation_requested", ReasonCode.SELF_PROMOTION_FORBIDDEN),
        (
            "parameter_value_mutation_requested",
            ReasonCode.PARAMETER_SCOPE_MISMATCH,
        ),
        (
            "tradeplan_optimization_execution_requested",
            ReasonCode.OPERATION_NOT_ALLOWED,
        ),
    ),
)
def test_every_forbidden_effect_attempt_has_one_typed_denial(
    flag: str, reason: ReasonCode
) -> None:
    decision = resolve_decision(
        make_resolver(envelope_overrides={flag: True})
    )
    assert reason in decision.reason_codes
    assert not decision.eligible


@pytest.mark.parametrize(
    ("state", "reason"),
    (
        (AgentSafetyStateV1.MISSING, ReasonCode.SAFETY_STATE_MISSING),
        (AgentSafetyStateV1.STALE, ReasonCode.SAFETY_STATE_STALE),
        (AgentSafetyStateV1.CONFLICT, ReasonCode.SAFETY_STATE_CONFLICT),
    ),
)
def test_missing_stale_or_conflicting_safety_state_denies(
    state: AgentSafetyStateV1, reason: ReasonCode
) -> None:
    boundary = AgentBoundaryStateViewV1(
        state=state,
        state_ref=f"SAFETY::{state.value}",
        observed_at="2026-08-02T00:00:00+00:00",
        valid_until="2099-01-01T00:00:00+00:00",
    )
    decision = resolve_decision(make_resolver(boundary_state=boundary))
    assert reason in decision.reason_codes
    assert not decision.eligible


def test_nonmaterial_safety_exception_is_limited_to_local_read_only_ops() -> None:
    boundary = AgentBoundaryStateViewV1(
        state=AgentSafetyStateV1.MISSING,
        state_ref="SAFETY::UNAVAILABLE_RECORDED",
        observed_at="ABSENT_NOT_APPLICABLE",
        valid_until="ABSENT_NOT_APPLICABLE",
        safety_state_non_material=True,
    )
    local = resolve_decision(make_resolver(boundary_state=boundary))
    compute = resolve_decision(
        make_resolver(
            operation_id="compute_component", boundary_state=boundary
        ),
        operation_id="compute_component",
    )

    assert local.eligible
    assert ReasonCode.SAFETY_STATE_MISSING in compute.reason_codes
    assert not compute.eligible


def test_quarantined_output_cannot_release_itself() -> None:
    decision = resolve_decision(
        make_resolver(bundle_overrides={"quarantined": True})
    )
    assert decision.decision_state is AgentCapabilityDecisionStateV1.QUARANTINED
    assert decision.reason_codes == (ReasonCode.QUARANTINED,)
    assert not decision.eligible


def test_idempotency_key_cannot_be_reused_for_different_authority_request() -> None:
    resolver = make_resolver()
    first = resolve_decision(resolver)
    second = resolve_decision(
        resolver, request_id="REQUEST::ST12E::DIFFERENT"
    )

    assert first.eligible
    assert ReasonCode.IDEMPOTENCY_CONFLICT in second.reason_codes
    assert not second.eligible


def test_missing_bundle_is_a_typed_denial() -> None:
    decision = resolve_decision(
        make_resolver(), capability_bundle_id="MISSING"
    )
    assert decision.reason_codes == (ReasonCode.TASK_ENVELOPE_MISSING,)
    assert not decision.eligible


@pytest.mark.parametrize(
    ("bundle_field", "reason"),
    (
        ("certified_source_agent_ids", ReasonCode.SOURCE_AGENT_ID_UNMAPPED),
        ("permission_scope", ReasonCode.OPERATION_NOT_ALLOWED),
    ),
)
def test_empty_identity_or_permission_cannot_pass_vacuously(
    bundle_field: str, reason: ReasonCode
) -> None:
    with pytest.raises(AuthorityDeniedError) as captured:
        make_resolver(bundle_overrides={bundle_field: ()})

    assert captured.value.reason_code is reason


@pytest.mark.parametrize("value", (float("nan"), float("inf"), float("-inf")))
def test_nonfinite_compute_budget_is_rejected_before_resolution(value: float) -> None:
    with pytest.raises(AuthorityDeniedError) as captured:
        make_resolver(envelope_overrides={"compute_budget": value})

    assert captured.value.reason_code is ReasonCode.BUDGET_EXCEEDED


@pytest.mark.parametrize(
    "variables",
    (
        (),
        ("formula",),
        ("market", "market"),
        "market",
    ),
)
def test_no_trade_reoptimization_requires_a_bounded_tradeplan_scope(
    variables: object,
) -> None:
    decision = resolve_decision(
        make_resolver(
            envelope_overrides={
                "terminal_no_trade": True,
                "reoptimization_variable_ids": variables,
            }
        )
    )

    assert ReasonCode.TASK_SCOPE_MISMATCH in decision.reason_codes
    assert not decision.eligible


def test_peer_challenge_boolean_cannot_bypass_independence_evidence() -> None:
    decision = resolve_decision(
        make_resolver(
            envelope_overrides={
                "peer_challenge_requirement": True,
                "peer_challenge_satisfied": True,
            }
        )
    )

    assert ReasonCode.PEER_CHALLENGE_REQUIRED in decision.reason_codes
    assert not decision.eligible


def test_independent_peer_challenge_uses_existing_identity_and_receipt() -> None:
    snapshot = make_resolver().policy_store.snapshot
    peer_binding = next(
        binding
        for binding in snapshot.identity_map.bindings.values()
        if "parameter_selector_agent" not in binding.current_principal_refs
    )
    peer_receipt_ref = next(
        iter(snapshot.agent_orch_receipt_refs_by_candidate_id.values())
    )
    decision = resolve_decision(
        make_resolver(
            envelope_overrides={
                "peer_challenge_requirement": True,
                "peer_challenge_satisfied": True,
                "peer_challenge_principal_id": peer_binding.current_principal_refs[0],
                "peer_challenge_duty_ref": peer_binding.current_duty_refs[0],
                "peer_challenge_receipt_ref": peer_receipt_ref,
                "peer_reasoning_chain_ref": "INDEPENDENT_REASONING::TEST",
            }
        )
    )

    assert decision.eligible
    assert peer_receipt_ref in decision.evidence_refs
    assert decision.peer_sod_disposition == "PEER_CHALLENGE_AND_SOD_ENFORCED"


def test_optional_task_scope_requires_an_explicit_absence_token() -> None:
    with pytest.raises(AuthorityDeniedError) as captured:
        make_resolver(envelope_overrides={"qku_scope_refs": ()})

    assert captured.value.reason_code is ReasonCode.TASK_SCOPE_MISMATCH


def test_held_operation_contract_is_denied_without_implementation() -> None:
    operation_id = "compile_replay_paper_cohort"
    decision = resolve_decision(
        make_resolver(operation_id=operation_id), operation_id=operation_id
    )
    assert ReasonCode.REPLAY_PAPER_EFFECT_FORBIDDEN in decision.reason_codes
    assert not decision.eligible


def test_coefficient_level_quantum_reference_is_advisory_and_no_effect() -> None:
    coefficient_bundle = {
        field: (
            (f"REFERENCE_ONLY::{field}",)
            if field in QUANTUM_TUPLE_FIELDS
            else f"REFERENCE_ONLY::{field}"
        )
        for field in QUANTUM_FORMULATION_FIELDS
    }
    decision = resolve_decision(
        make_resolver(
            envelope_overrides={
                "quantum_challenger": True,
                "quantum_formulation_bundle": coefficient_bundle,
            }
        )
    )
    assert decision.eligible
    assert decision.runtime_effect_authorized is False


def test_candidate_lane_and_live_review_action_remain_request_only() -> None:
    candidate_packet = {
        "candidate_id": "CANDIDATE::TEST",
        "provenance_refs": ("OWNER_SUBMITTED_TEXT::TEST",),
        "source_class": "CANDIDATE_PROVISIONAL",
        "retrieval_state_or_explicit_absence": "ABSENT_NOT_APPLICABLE",
        "effective_state_or_explicit_absence": "ABSENT_NOT_APPLICABLE",
        "downstream_consumer_ref": "RESEARCH_REVIEW_OWNER",
        "validation_route": "SOURCE_REVALIDATION_REQUIRED",
        "terminal_disposition": "PROVISIONAL_ONLY",
        "accepted_source_truth": False,
    }
    for action_id in (
        "SUBMIT_RESEARCH_CANDIDATE",
        "ADD_SOURCE_REQUEST",
        "PROMOTE_TO_LIVE_REVIEW_REQUEST",
    ):
        decision = resolve_decision(
            make_resolver(
                envelope_overrides={
                    "action_scope_refs": (action_id,),
                    **(
                        {"candidate_information_packet": candidate_packet}
                        if action_id
                        in {"SUBMIT_RESEARCH_CANDIDATE", "ADD_SOURCE_REQUEST"}
                        else {}
                    ),
                }
            ),
            requested_scope_refs={"action_scope_refs": (action_id,)},
        )
        assert decision.eligible
        assert decision.decision_state is not AgentCapabilityDecisionStateV1.DENIED
        assert decision.runtime_effect_authorized is False


def test_candidate_lane_requires_provenance_and_cannot_accept_source_truth() -> None:
    missing_packet = resolve_decision(
        make_resolver(
            envelope_overrides={
                "action_scope_refs": ("SUBMIT_RESEARCH_CANDIDATE",),
            }
        ),
        requested_scope_refs={
            "action_scope_refs": ("SUBMIT_RESEARCH_CANDIDATE",)
        },
    )
    accepted_truth = resolve_decision(
        make_resolver(
            envelope_overrides={
                "action_scope_refs": ("ADD_SOURCE_REQUEST",),
                "candidate_information_packet": {
                    "candidate_id": "CANDIDATE::TEST",
                    "provenance_refs": ("OWNER_SUBMITTED_TEXT::TEST",),
                    "source_class": "CANDIDATE_PROVISIONAL",
                    "retrieval_state_or_explicit_absence": "ABSENT_NOT_APPLICABLE",
                    "effective_state_or_explicit_absence": "ABSENT_NOT_APPLICABLE",
                    "downstream_consumer_ref": "RESEARCH_REVIEW_OWNER",
                    "validation_route": "SOURCE_REVALIDATION_REQUIRED",
                    "terminal_disposition": "PROVISIONAL_ONLY",
                    "accepted_source_truth": True,
                },
            }
        ),
        requested_scope_refs={"action_scope_refs": ("ADD_SOURCE_REQUEST",)},
    )

    assert ReasonCode.TASK_SCOPE_MISMATCH in missing_packet.reason_codes
    assert ReasonCode.SOURCE_TRUTH_FORBIDDEN in accepted_truth.reason_codes
    assert not missing_packet.eligible
    assert not accepted_truth.eligible


def test_memory_prior_requires_current_context_version_ttl_and_revalidation() -> None:
    memory_fields = {
        "memory_prior_ref": "MEM1::CONDITION_SCOPED_PRIOR",
        "memory_revalidation_state": "CURRENT_REVALIDATED",
        "memory_context_similarity_state": "CURRENT_CONTEXT_MATCH",
        "memory_context_ref": "CTX::ST12E::TEST",
        "memory_version_ref": "MEM1::V1",
        "memory_valid_until": "2099-01-01T00:00:00+00:00",
    }
    valid = resolve_decision(
        make_resolver(envelope_overrides=memory_fields)
    )
    stale = resolve_decision(
        make_resolver(
            envelope_overrides={
                **memory_fields,
                "memory_valid_until": "2000-01-01T00:00:00+00:00",
            }
        )
    )

    assert valid.eligible
    assert ReasonCode.MEMORY_PRIOR_REVALIDATION_REQUIRED in stale.reason_codes
    assert not stale.eligible


def test_llm_contract_is_schema_bounded_advisory_only_without_inference() -> None:
    advisory_packet = {
        "structured_task_type": "CRITIQUE_ONLY",
        "redacted_context_refs": ("REDACTED_CONTEXT::TEST",),
        "untrusted_content_boundary": "ALL_RETRIEVED_CONTENT_IS_DATA",
        "allowlisted_tool_refs": ("QKUComputationControlPlaneV1",),
        "closed_output_schema_ref": "AdvisoryAnnotationV1",
        "citation_provenance_requirements": "REQUIRED",
        "numerical_recheck_requirement": True,
        "source_truth_prohibition": True,
        "risk_mode_order_prohibition": True,
        "latency_token_cost_tool_budgets": "BOUNDED_BY_TASK_ENVELOPE",
        "abstention_route": "OWNER_REVIEW_REQUIRED",
    }
    valid = resolve_decision(
        make_resolver(
            envelope_overrides={
                "llm_advisory_requested": True,
                "llm_advisory_task": advisory_packet,
            }
        )
    )
    incomplete = resolve_decision(
        make_resolver(
            envelope_overrides={
                "llm_advisory_requested": True,
                "llm_advisory_task": {"structured_task_type": "CRITIQUE_ONLY"},
            }
        )
    )

    assert valid.eligible
    assert valid.runtime_effect_authorized is False
    assert ReasonCode.LLM_ADVISORY_ONLY in incomplete.reason_codes
    assert not incomplete.eligible


def test_decision_receipt_is_immutable_append_only_policy_evidence() -> None:
    decision = resolve_decision(make_resolver())
    with pytest.raises(FrozenInstanceError):
        decision.runtime_effect_authorized = True  # type: ignore[misc]
