"""Frozen-owner, service-boundary, receipt, and no-orphan ST12-E checks."""

from __future__ import annotations

from dataclasses import replace
import inspect
from pathlib import Path
from types import MappingProxyType

import pytest

from src.qtt.dashboard.owner_action_registry import ACTION_DEFINITIONS
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.agent_policy import (
    HELD_OPERATION_IDS,
    IMPLEMENTED_OPERATION_IDS,
    NO_EFFECT_PROFILE_REF,
    NO_TRADE_REOPTIMIZATION_VARIABLE_IDS,
    PARAMETER_MAPPING_BLOCKED,
    PARAMETER_MAPPING_EXACT,
    PARAMETER_MAPPING_BLOCKER_REF,
    AgentCapabilityDecisionStateV1,
    AgentCapabilityResolverV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.service import (
    QKUComputationControlPlaneV1,
)

from . import (
    TEST_CONTEXT_REF,
    TEST_PRINCIPAL_ID,
    make_resolver,
    policy_store,
    resolve_decision,
)


def test_frozen_snapshot_has_exact_bounded_indexes() -> None:
    snapshot = policy_store().snapshot

    assert isinstance(snapshot.policy_rows, MappingProxyType)
    assert isinstance(snapshot.parameter_scope_rows, MappingProxyType)
    assert snapshot.identity_map.bindings
    assert snapshot.parameter_scope_rows
    with pytest.raises(TypeError):
        snapshot.policy_rows["NEW"] = {}  # type: ignore[index]


def test_task_envelope_is_frozen_before_request_time_resolution() -> None:
    resolver = make_resolver()
    bundle = next(iter(resolver._bundles.values()))

    assert isinstance(bundle.task_envelope, MappingProxyType)
    with pytest.raises(TypeError):
        bundle.task_envelope["operation_id"] = "compute_stack"  # type: ignore[index]


def test_request_time_resolution_performs_no_file_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resolver = make_resolver()

    def _forbidden_read(*_args, **_kwargs):
        raise AssertionError("request-time policy lookup attempted a file read")

    monkeypatch.setattr(Path, "read_text", _forbidden_read)
    decision = resolve_decision(
        resolver,
        requested_scope_refs={
            "qku_scope_refs": ("QKU::ST12E::TEST",),
            "formula_scope_refs": ("MATH-01",),
            "data_scope_refs": ("PUBLIC_TEST_PACKET",),
            "tool_scope_refs": ("QKUComputationControlPlaneV1",),
            "action_scope_refs": ("REQUEST_AGENT_TASK",),
        },
    )

    assert decision.eligible
    assert decision.runtime_effect_authorized is False


def test_same_request_and_idempotency_key_return_same_decision() -> None:
    resolver = make_resolver()
    first = resolve_decision(resolver)
    second = resolve_decision(resolver)

    assert first is second
    assert first.decision_state is (
        AgentCapabilityDecisionStateV1.ELIGIBLE_FOR_NO_EFFECT_QKU_REQUEST
    )
    assert first.reason_codes == ()


def test_same_request_cannot_claim_a_second_idempotency_key() -> None:
    first_resolver = make_resolver()
    first_bundle = next(iter(first_resolver._bundles.values()))
    second_envelope = dict(first_bundle.task_envelope)
    second_envelope["idempotency_key"] = "ST12E_IDEMPOTENCY::SECOND"
    second_bundle = replace(
        first_bundle,
        bundle_id="ST12E_TEST_BUNDLE_SECOND",
        task_envelope=second_envelope,
    )
    resolver = AgentCapabilityResolverV1(
        policy_store(),
        {
            first_bundle.bundle_id: first_bundle,
            second_bundle.bundle_id: second_bundle,
        },
    )

    first = resolve_decision(resolver)
    duplicate = resolve_decision(
        resolver,
        capability_bundle_id=second_bundle.bundle_id,
        request_idempotency_key="ST12E_IDEMPOTENCY::SECOND",
    )

    assert first.eligible
    assert ReasonCode.IDEMPOTENCY_CONFLICT in duplicate.reason_codes
    assert not duplicate.eligible


def test_cached_eligibility_cannot_mask_a_changed_effect_bearing_envelope() -> None:
    first_resolver = make_resolver()
    first_bundle = next(iter(first_resolver._bundles.values()))
    changed_envelope = dict(first_bundle.task_envelope)
    changed_envelope["formula_mutation_requested"] = True
    changed_bundle = replace(
        first_bundle,
        bundle_id="ST12E_TEST_BUNDLE_CHANGED",
        task_envelope=changed_envelope,
    )
    resolver = AgentCapabilityResolverV1(
        policy_store(),
        {
            first_bundle.bundle_id: first_bundle,
            changed_bundle.bundle_id: changed_bundle,
        },
    )

    first = resolve_decision(resolver)
    changed = resolve_decision(
        resolver, capability_bundle_id=changed_bundle.bundle_id
    )

    assert first.eligible
    assert ReasonCode.IDEMPOTENCY_CONFLICT in changed.reason_codes
    assert ReasonCode.SELF_PROMOTION_FORBIDDEN in changed.reason_codes
    assert not changed.eligible


def test_policy_receipt_links_existing_identity_planes_only() -> None:
    decision = resolve_decision(make_resolver())

    assert decision.agent_orch_receipt_ref.startswith(
        "AGENT_ORCH1::AGENTDECISIONRECEIPTV1_"
    )
    assert decision.st12c_causation_correlation_refs == (
        "OperationRequestEnvelopeV1.request_id=REQUEST::ST12E::TEST",
        (
            "OperationRequestEnvelopeV1.idempotency_key="
            "ST12E_IDEMPOTENCY::TEST"
        ),
    )
    assert decision.agent_orch_receipt_ref in decision.evidence_refs
    assert decision.task_id in decision.evidence_refs
    assert decision.alternative_route_refs
    assert decision.disagreement_state == "NONE_DECLARED"
    assert decision.confidence_state == "SUFFICIENT_FOR_NO_EFFECT_REVIEW"
    assert "QKU_AND_FORMULA_IMMUTABLE" in decision.limitation_codes
    assert decision.no_effect_profile_ref == NO_EFFECT_PROFILE_REF
    assert decision.runtime_effect_authorized is False
    assert not any(
        token in decision.terminal_route
        for token in ("FILL", "CASH", "PNL", "ORDER_SUBMIT")
    )


def test_no_trade_routes_tradeplan_variables_without_formula_mutation() -> None:
    selected_variables = ("market", "venue", "size", "next_target")
    decision = resolve_decision(
        make_resolver(
            envelope_overrides={
                "terminal_no_trade": True,
                "reoptimization_variable_ids": selected_variables,
            }
        )
    )

    assert decision.decision_state is (
        AgentCapabilityDecisionStateV1.NO_TRADE_REOPTIMIZATION_ROUTED
    )
    assert not decision.eligible
    assert decision.reason_codes == (
        ReasonCode.NO_TRADE_REOPTIMIZATION_REQUIRED,
    )
    assert decision.terminal_route == (
        "PRETRADE1_BOUNDED_TRADEPLAN_VARIABLE_REOPTIMIZATION"
    )
    assert set(selected_variables) <= set(NO_TRADE_REOPTIMIZATION_VARIABLE_IDS)
    assert {
        f"reoptimization_variable_id={value}" for value in selected_variables
    } <= set(decision.scope_refs)
    assert "QKU_AND_FORMULA_IMMUTABLE" in decision.limitation_codes
    assert decision.runtime_effect_authorized is False


def test_semantic_disagreement_is_preserved_for_owner_escalation() -> None:
    decision = resolve_decision(
        make_resolver(
            envelope_overrides={
                "disagreement_state": "SEMANTIC_DISAGREEMENT_PRESERVED"
            }
        )
    )

    assert decision.decision_state is (
        AgentCapabilityDecisionStateV1.OWNER_ESCALATION_REQUIRED
    )
    assert decision.reason_codes == (ReasonCode.OWNER_REVIEW_REQUIRED,)
    assert decision.disagreement_state == "SEMANTIC_DISAGREEMENT_PRESERVED"
    assert not decision.eligible


def test_all_parameter_scope_rows_have_owner_consumer_and_terminal_route() -> None:
    rows = policy_store().snapshot.parameter_scope_rows

    assert tuple(rows) == tuple(
        sorted(rows, key=lambda value: int(value.rsplit("::", 1)[1]))
    )
    for parameter_id, row in rows.items():
        assert row.parameter_id == parameter_id
        assert row.source_agent_ids
        assert row.current_principal_refs_or_gap
        assert row.capability_policy_ref.startswith("ST12E_")
        assert "ComputationParameterPolicyV1::" in row.value_policy_ref
        assert row.downstream_consumer_refs
        assert row.lifecycle_state
        assert row.timing_state
        assert row.validator_ref
        assert row.terminal_route
        assert row.semantic_owner
        assert row.implementation_owner
        assert row.producer_ref
        assert row.upstream_artifact_refs
        assert row.upstream_row_or_value_refs
        assert row.current_principal_duty_policy_refs
        assert row.activation_state == "NO_EFFECT_CONTRACT_ONLY"
        if row.mapping_state == PARAMETER_MAPPING_EXACT:
            assert row.current_principal_refs_or_gap != (
                PARAMETER_MAPPING_BLOCKER_REF,
            )
        else:
            assert row.mapping_state == PARAMETER_MAPPING_BLOCKED
            assert row.current_principal_refs_or_gap == (
                PARAMETER_MAPPING_BLOCKER_REF,
            )


@pytest.mark.parametrize("operation_id", IMPLEMENTED_OPERATION_IDS)
def test_every_implemented_service_method_uses_one_admission_boundary(
    operation_id: str,
) -> None:
    source = inspect.getsource(
        getattr(QKUComputationControlPlaneV1, operation_id)
    )
    assert source.count("_admit_agent_request(self, request)") == 1


@pytest.mark.parametrize("operation_id", HELD_OPERATION_IDS)
def test_held_replay_paper_operations_are_not_service_methods(
    operation_id: str,
) -> None:
    assert not hasattr(QKUComputationControlPlaneV1, operation_id)


def test_owner_actions_remain_central_request_only_semantics() -> None:
    action_ids = policy_store().snapshot.owner_action_ids

    for action_id in action_ids:
        definition = ACTION_DEFINITIONS[action_id]
        semantics = str(definition["semantics"]).casefold()
        assert definition["confirmation_class"] in {
            "OWNER_REVIEW_REQUIRED",
            "CRITICAL_CONFIRMATION",
        }
        assert "request" in semantics or "route" in semantics
        assert not any(
            phrase in semantics
            for phrase in (
                "submits an order",
                "activates live",
                "accepts source truth",
            )
        )


def test_parameter_scope_intersection_authorizes_only_selected_principal() -> None:
    decision = resolve_decision(
        make_resolver(),
        requested_parameter_ids=("ST10-PARAM::0024",),
    )
    assert decision.principal_id == TEST_PRINCIPAL_ID
    assert decision.eligible
    assert decision.scope_refs
    assert f"context_ref={TEST_CONTEXT_REF}" in decision.scope_refs
    assert "parameter_id=ST10-PARAM::0024" in decision.scope_refs


def test_aggregate_only_parameter_projection_cannot_authorize_access() -> None:
    blocked_parameter_id = next(
        parameter_id
        for parameter_id, row in policy_store().snapshot.parameter_scope_rows.items()
        if row.mapping_state == PARAMETER_MAPPING_BLOCKED
    )
    decision = resolve_decision(
        make_resolver(), requested_parameter_ids=(blocked_parameter_id,)
    )

    assert ReasonCode.PARAMETER_SCOPE_MISMATCH in decision.reason_codes
    assert not decision.eligible
