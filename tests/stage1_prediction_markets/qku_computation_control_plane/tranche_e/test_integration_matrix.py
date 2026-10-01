"""Compact frozen-owner, mandatory-admission, route, and receipt matrix."""

from __future__ import annotations

from dataclasses import replace
import inspect
from pathlib import Path
from types import MappingProxyType, SimpleNamespace

import pytest

from src.qtt.dashboard.owner_action_registry import ACTION_DEFINITIONS
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.agent_policy import (
    HELD_OPERATION_IDS,
    IMPLEMENTED_OPERATION_IDS,
    NO_EFFECT_PROFILE_REF,
    NO_TRADE_REOPTIMIZATION_VARIABLE_IDS,
    ST12E_BINDING_OUTSIDE_SCOPE,
    AgentCapabilityDecisionStateV1,
    AgentCapabilityDecisionV1,
    AgentCapabilityResolverV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    AuthorityDeniedError,
    ContractValidationError,
    NoTradeReoptimizationRouteError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import (
    CanonicalOwnerPacketRegistryV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.service import (
    QKUComputationControlPlaneV1,
)

from . import (
    TEST_CONTEXT_REF,
    TEST_PRINCIPAL_ID,
    make_resolver,
    policy_store,
    repo_root,
    resolve_decision,
)


class _CountingAdmission:
    def __init__(self, decision: AgentCapabilityDecisionV1) -> None:
        self.calls = 0
        self.decision = decision

    def admit_operation(self, request: object) -> AgentCapabilityDecisionV1:
        self.calls += 1
        return self.decision


class _OperationBodyTouched(AssertionError):
    pass


class _AdmissionProbeRequest:
    request_id = "REQUEST::ST12E::TEST"
    operation_name = "resolve_identity"
    principal_id = TEST_PRINCIPAL_ID
    capability_bundle_id = "ST12E_TEST_BUNDLE"
    idempotency_key = "ST12E_IDEMPOTENCY::TEST"
    context = SimpleNamespace(context_id=TEST_CONTEXT_REF)

    def __init__(self) -> None:
        self.operation_body_reads = 0

    @property
    def identity_query(self) -> object:
        self.operation_body_reads += 1
        raise _OperationBodyTouched


def _service(admission: object) -> QKUComputationControlPlaneV1:
    return QKUComputationControlPlaneV1(
        CanonicalOwnerPacketRegistryV1(),
        agent_capability_resolver=admission,
    )


def test_frozen_snapshot_and_task_envelope_are_immutable_indexes() -> None:
    snapshot = policy_store().snapshot
    resolver = make_resolver()
    bundle = next(iter(resolver._bundles.values()))

    assert isinstance(snapshot.policy_rows, MappingProxyType)
    assert isinstance(snapshot.parameter_scope_rows, MappingProxyType)
    assert isinstance(bundle.task_envelope, MappingProxyType)
    with pytest.raises(TypeError):
        snapshot.policy_rows["NEW"] = {}  # type: ignore[index]
    with pytest.raises(TypeError):
        bundle.task_envelope["operation_id"] = "compute_stack"  # type: ignore[index]

    from dataclasses import fields, FrozenInstanceError
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import models
    from . import _synthetic_probability_issuance
    import time
    for cls, count in ((models.ProbabilityPredictionArtifactWriteRequestV1, 8),
                       (models.ProbabilityPredictionArtifactSealV1, 8),
                       (models.ProbabilityPredictionReviewBasisReadRequestV1, 10)):
        assert len(fields(cls)) == count
        assert cls.__dataclass_params__.frozen
    resolver, reader, requests = _synthetic_probability_issuance()
    now = time.time_ns()
    with resolver._resolve_probability_issuer_context_v1(requests, evaluated_ns=now) as original:
        admissions = tuple(resolver._admit_probability_issuer_v1(request, trusted_snapshot=original) for request in requests)
        assert all(admission.no_effect_flags is models.NO_EFFECTS_V1 for admission in admissions)
        assert resolver._admit_probability_issuer_v1(requests[0], trusted_snapshot=original) is admissions[0]
        with pytest.raises(FrozenInstanceError):
            requests[0].issuer_ref = "SYNTHETIC::OTHER"
    assert reader.read_calls == 1 and not reader.active
    assert resolver._probability_last_issuer_view_v1["snapshot"] is original


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

    from . import _synthetic_registered_prediction
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ContractValidationError
    import time
    probability_resolver, reader, fence, prepared, entry = _synthetic_registered_prediction()
    reads = reader.read_calls
    monkeypatch.setattr(Path, "read_bytes", _forbidden_read)
    monkeypatch.setattr(Path, "open", _forbidden_read)
    assert fence._registered_v1(prepared, kind="PREDICTION", evaluated_ns=time.time_ns()) is entry
    with pytest.raises(ContractValidationError):
        fence._registered_v1(replace(prepared), kind="PREDICTION", evaluated_ns=time.time_ns())
    assert prepared.model_use_authorized is False and prepared.native_packet_created is False
    fence._source_synchronized_v1 = False
    with pytest.raises(ContractValidationError):
        fence._registered_v1(prepared, kind="PREDICTION", evaluated_ns=time.time_ns())
    assert reader.read_calls == reads

    _exercise_synthetic_probability_packet_factory(monkeypatch)


def _exercise_synthetic_probability_packet_factory(monkeypatch):
    """Native use/packet integration from an explicitly synthetic issued diagnostic.

    The fixture does not stand in for fitted-model, source, or review acceptance.
    Its boundary starts at the original registered prepared object; the existing
    numerical/artifact and committed-reader groups exercise separate preceding
    ports. This helper does not prove the full producer-to-committed-reader chain.
    """
    from contextlib import contextmanager
    from dataclasses import FrozenInstanceError
    from datetime import datetime, timedelta, timezone
    from decimal import Decimal
    import builtins
    import io
    import socket
    import sqlite3
    import subprocess
    import time
    from . import _synthetic_registered_prediction
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as numerical
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import input_resolver as inputs
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import model_risk as risk
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import service as composition
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import (
        ProbabilityOutcomeJoinV1, _build_probability_owner_registry_v1,
        _resolve_formula_input_binding, FORMULA_INPUT_AUTHORITY_BY_MATH_ID)
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
        ComputationExecutionContextV1, ComputationScopeV1, ImplementationVersionPinV1,
        ProbabilityPredictionReadLimitsV1, ResourceBoundsProfileV1)
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.model_risk import (
        ProbabilityNativeUseRequestV1, ProbabilityNativeUseAdmissionV1,
        NoTradeConditionOutcomeV1, NO_TRADE_CONDITION_IDS_V1)
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.persistence import (
        ProbabilityProducerReadLimitsV1, ProbabilityProducerReadSnapshotV1)
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import (
        ProbabilityProducerControlReceiptV1, _probability_control_record_v1)
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import InputAuthorityError

    tick = [1_800_000_000_000_000_000]
    def advancing_utc():
        tick[0] += 1_000_000
        return tick[0]
    def forbidden(*args, **kwargs):
        raise AssertionError("synthetic native-use/packet consumption attempted I/O or numerical fitting")

    with monkeypatch.context() as clock_patch:
        clock_patch.setattr(time, "time_ns", advancing_utc)
        for mode in ("two", "four", "request_copy", "exit_revoked", "checker_value", "checker_revoked",
                     "service", "service_revoked"):
            resolver, reader, fence, prepared, entry = _synthetic_registered_prediction()
            initial_issuer_reads = reader.read_calls
            at = prepared.observed_ns
            expiry = prepared.valid_until_ns
            scope = fence.scope
            trace = dict(context_ref="SYNTHETIC::PACKET-CONTEXT", causation_id="SYNTHETIC::CAUSE",
                correlation_id="SYNTHETIC::CORRELATION", traceparent="SYNTHETIC::TRACE", tracestate="SYNTHETIC::STATE")
            result_body = dict(artifact_ref="SYNTHETIC::ARTIFACT", artifact_byte_count=1, artifact_frame_count=1,
                input_lock_id=scope.input_lock_ref, prediction_input_lock_id=prepared.prediction_input_lock_ref,
                plan_id="SYNTHETIC::PLAN", producer_ref="SYNTHETIC::COMPUTATION",
                producer_control_domain_ref="SYNTHETIC::PRODUCER-DOMAIN", input_available_ns=at - 5000,
                started_ns=at - 4000, completed_ns=at - 3000)
            result = _probability_control_record_v1(record_id=prepared.result_ref,
                payload=ProbabilityProducerControlReceiptV1("PROBABILITY_PRODUCER_CONTROL_V1", "PREDICTION_RESULT",
                    scope, at - 3000, at - 3000, at - 3000, prepared.dependency_refs, expiry, result_body), **trace)
            review_dependencies = (prepared.result_ref, "SYNTHETIC::VALIDATION", "SYNTHETIC::USE-LIMIT", "SYNTHETIC::RISK")
            review_body = dict(result_ref=prepared.result_ref, artifact_ref=result_body["artifact_ref"],
                reviewer_ref="SYNTHETIC::REVIEWER", reviewer_control_domain_ref="SYNTHETIC::REVIEW-DOMAIN",
                review_state="CALIBRATED_FOR_DECLARED_CONTEXT", validation_receipt_refs=(review_dependencies[1],),
                use_limit_ref=review_dependencies[2], model_risk_receipt_ref=review_dependencies[3],
                result_commit_observed_ns=at - 2000, started_ns=at - 2000, completed_ns=at - 1000, blocker_codes=())
            review = _probability_control_record_v1(record_id=prepared.review_ref,
                payload=ProbabilityProducerControlReceiptV1("PROBABILITY_PRODUCER_CONTROL_V1", "PREDICTION_REVIEW",
                    scope, at - 1000, at - 1000, at - 1000, review_dependencies, expiry, review_body), **trace)
            cutoffs = time.time_ns()
            observed = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=cutoffs // 1000)
            context = ComputationExecutionContextV1("SYNTHETIC::PACKET-CONTEXT", observed, observed,
                "SYNTHETIC::EPOCH", "SYNTHETIC::INPUT-VERSION", timedelta(seconds=30),
                ComputationScopeV1("SYNTHETIC::MARKET", "SYNTHETIC::VENUE", "SYNTHETIC::EVENT",
                    "SYNTHETIC::CONTRACT", "SYNTHETIC::NO-EFFECT", "SYNTHETIC::INPUT-SNAPSHOT"), "3.4", "3.4",
                tuple(ImplementationVersionPinV1(math_id, numerical.IMPLEMENTATION_REGISTRY[math_id].contract.implementation_id)
                      for math_id in ("MATH-02", "MATH-06")))
            conditions = tuple(NoTradeConditionOutcomeV1(name, index == 0,
                ("SYNTHETIC::EXISTING-VETO",) if index == 0 else (),
                (ReasonCode.ST12F_MODEL_RISK_VETO,) if index == 0 else ())
                for index, name in enumerate(NO_TRADE_CONDITION_IDS_V1))
            entry["metadata"].update(scope=scope, cutoffs=(cutoffs, cutoffs), result=result, review=review,
                model=SimpleNamespace(available_ns=at - 5000, valid_until_ns=expiry), conditions=conditions,
                read_snapshot=ProbabilityProducerReadSnapshotV1(scope,
                    {prepared.result_ref: result, prepared.review_ref: review}, (), (), at))
            binding_ids = ("FIVAB::MATH-02::calibrated_model_probability", "FIVAB::MATH-02::calibration_state")
            outcome = None
            if mode == "four":
                binding_ids += ("FIVAB::MATH-06::p_win", "FIVAB::MATH-06::p_void")
                outcome = ProbabilityOutcomeJoinV1(context.execution_identity_tuple, prepared.request_keys[0],
                    Decimal("0.8"), "SYNTHETIC::VALIDITY", "SYNTHETIC::FILL-CONDITIONING",
                    ("SYNTHETIC::VALIDITY", "SYNTHETIC::FILL-CONDITIONING"), at, expiry)
            request = ProbabilityNativeUseRequestV1(scope, prepared, context, prepared.request_keys[0], binding_ids,
                outcome, "SYNTHETIC::ACCEPTED-USE", cutoffs, cutoffs)
            dependencies = tuple(dict.fromkeys((*prepared.dependency_refs, scope.policy_ref,
                request.selected_use_decision_ref, "SYNTHETIC::USE-POLICY", "SYNTHETIC::USE-TRANSITION",
                *(outcome.dependency_refs if outcome is not None else ()))))
            counts = {"read": 0, "check": 0, "exit": 0}
            admitted = []
            @contextmanager
            def read_use(original, *, evaluated_ns, deadline_ns):
                assert original is request and not reader.active
                counts["read"] += 1
                admission = ProbabilityNativeUseAdmissionV1(replace(original) if mode == "request_copy" else original,
                    original.selected_use_decision_ref, "SYNTHETIC::USE-POLICY", "SYNTHETIC::USE-TRANSITION",
                    cutoffs, expiry, dependencies, fence.policy.policy_version, fence.policy_epoch,
                    fence.policy.registry_version, fence.process_ref, fence.generation, fence.cut.checkpoint_ref)
                admitted.append(admission)
                try:
                    yield admission
                finally:
                    counts["exit"] += 1
                    if mode == "exit_revoked":
                        fence._source_synchronized_v1 = False
            def check_use(original, *, evaluated_ns):
                assert original is admitted[0] and counts["exit"] == 1
                counts["check"] += 1
                if mode == "checker_revoked":
                    fence._source_synchronized_v1 = False
                return True if mode == "checker_value" else None
            deadline = time.monotonic_ns() + 60_000_000_000
            limits = ProbabilityPredictionReadLimitsV1(
                ProbabilityProducerReadLimitsV1(128, 1_000_000, 65536, 1000, deadline), 1_000_000, 256, 1_000_000)
            with monkeypatch.context() as guard:
                guard.setattr(reader, "read_probability_native_use", read_use, raising=False)
                guard.setattr(reader, "check_probability_native_use", check_use, raising=False)
                guard.setattr(reader, "read_probability_issuers", forbidden)
                for owner, name in ((builtins, "open"), (io, "open"), (socket, "create_connection"),
                        (sqlite3, "connect"), (subprocess, "Popen"), (numerical, "_probability_fit_prediction_v1"),
                        (numerical, "_probability_construct_prediction_bank_v1"),
                        (numerical, "_probability_construct_continuous_bank_v1")):
                    guard.setattr(owner, name, forbidden)
                call = dict(base_registry=CanonicalOwnerPacketRegistryV1(), request=request,
                    capability_resolver=resolver, clock_facts=(cutoffs,) * 5, existing_conditions=conditions,
                    limits=limits, deadline_ns=deadline)
                if mode in ("service", "service_revoked"):
                    controls = tuple(risk.ModelRiskControlEvidenceV1(identity,
                        risk.ModelRiskControlStateV1.BLOCKED_WITH_TYPED_REASON, (),
                        (ReasonCode.ST12F_EVIDENCE_INCOMPLETE,), ("SYNTHETIC::UNQUALIFIED",), False)
                        for identity in risk.MODEL_RISK_CONTROL_IDS_V1)
                    comparison = risk.PermanentNoTradeEvidenceComparisonV1("SYNTHETIC::COMPARISON",
                        scope.input_lock_ref, Decimal("0.1"), Decimal("1"), Decimal("0.8"), Decimal("0"), "CANDIDATE")
                    # Missing lane/control evidence remains unavailable; composing
                    # this candidate cannot invent a passing review or permission.
                    basis = risk.ModelRiskAdjudicationBasisV1("MATH-02", observed,
                        observed + timedelta(seconds=30), ("SYNTHETIC::REQUIRED",), None, None,
                        Decimal("0.05"), Decimal("0.05"), False, False, ("SYNTHETIC::CAPACITY",),
                        "READY_FOR_INDEPENDENT_REVIEW", "SYNTHETIC::PENDING-REVIEW")
                    resource = ResourceBoundsProfileV1("SYNTHETIC::SERVICE",
                        limits.metadata_limits.max_records, limits.metadata_limits.max_total_bytes, 1, 1, 1)
                    factory_results, assessments, constructed = [], [], []
                    actual_factory = inputs._build_probability_owner_registry_v1
                    actual_adjudicate = risk.ModelRiskEvidenceAdjudicatorV1.adjudicate
                    actual_service = composition.QKUComputationControlPlaneV1

                    def build_once(**kwargs):
                        result = actual_factory(**kwargs)
                        factory_results.append(result)
                        return result

                    def adjudicate_once(self, **kwargs):
                        result = actual_adjudicate(self, **kwargs)
                        assessments.append(result)
                        return result

                    def construct_once(**kwargs):
                        result = actual_service(**kwargs)
                        constructed.append(result)
                        if mode == "service_revoked":
                            fence._source_synchronized_v1 = False
                        return result

                    compose_call = dict(owner_registry=call["base_registry"],
                        agent_capability_resolver=resolver, native_use_request=request,
                        clock_facts=call["clock_facts"], prediction_read_limits=limits,
                        existing_conditions=conditions, assessment_id="SYNTHETIC::RISK",
                        input_lock_id=scope.input_lock_ref, controls=controls, comparison=comparison,
                        adjudication_basis=basis, limitations=("SYNTHETIC::PREPARED-BOUNDARY-ONLY",),
                        receipt_refs=("SYNTHETIC::ASSESSMENT",), evaluated_ns=time.time_ns(),
                        deadline_ns=deadline, resource_bounds_profile=resource)
                    with monkeypatch.context() as joined:
                        joined.setattr(inputs, "_build_probability_owner_registry_v1", build_once)
                        joined.setattr(risk.ModelRiskEvidenceAdjudicatorV1, "adjudicate", adjudicate_once)
                        joined.setattr(composition, "QKUComputationControlPlaneV1", construct_once)
                        if mode == "service_revoked":
                            with pytest.raises(InputAuthorityError) as rejected:
                                composition._compose_probability_native_service_v1(**compose_call)
                            assert rejected.value.reason_code is ReasonCode.INPUT_PACKET_MISMATCH
                        else:
                            service, assessment = composition._compose_probability_native_service_v1(**compose_call)
                    assert len(factory_results) == len(assessments) == len(constructed) == 1
                    assert counts["read"] == counts["exit"] == 1 and counts["check"] > 0
                    assert reader.read_calls == initial_issuer_reads
                    if mode == "service_revoked":
                        continue
                    registry, retained = factory_results[0]
                    assert service is constructed[0] and type(service) is actual_service
                    assert assessment is assessments[0] and service.owner_registry is registry
                    assert service.agent_capability_resolver is resolver and service.resource_bounds_profile is resource
                    assert service.mode_snapshot_input_resolver is None
                    assert service.mode_snapshot_owner_projection_adapter is service.mode_snapshot_projection_bundle is None
                    assert service.computation_evidence_service is None
                    assert assessment.control_evidence is controls
                    assert assessment.permanent_no_trade_comparison is comparison
                    assert assessment.adjudication_basis is basis
                    assert assessment.terminal_state == "NO_TRADE" and assessment.permanent_no_trade_wins is True
                    assert assessment.automatic_promotion_allowed is False
                    assert assessment.champion_challenger_evidence_only is True
                    assert tuple(row.active for row in assessment.no_trade_condition_outcomes) == (
                        True, True, True, False, False, False, False, True)
                    assert set(conditions[0].evidence_receipt_refs) <= set(
                        assessment.no_trade_condition_outcomes[0].evidence_receipt_refs)
                    assert set(conditions[0].reason_codes) <= set(assessment.no_trade_condition_outcomes[0].reason_codes)
                    with pytest.raises(FrozenInstanceError):
                        service.owner_registry = call["base_registry"]
                if mode not in ("two", "four", "service"):
                    with pytest.raises(ContractValidationError):
                        _build_probability_owner_registry_v1(**call, evaluated_ns=time.time_ns())
                    assert all(item["kind"] != "NATIVE_USE" for item in fence._registrations.values())
                else:
                    if mode != "service":
                        registry, retained = _build_probability_owner_registry_v1(**call, evaluated_ns=time.time_ns())
                    assert counts["read"] == counts["exit"] == 1 and counts["check"] > 0
                    assert len(registry.packets) == len(binding_ids) and len({packet.packet_id for packet in registry.packets}) == len(binding_ids)
                    assert retained[0] == conditions[0] and retained[0].active
                    expected = {binding_ids[0]: 0.6, binding_ids[1]: "CALIBRATED_FOR_DECLARED_CONTEXT"}
                    if mode == "four":
                        expected.update({binding_ids[2]: Decimal("0.48"), binding_ids[3]: Decimal("0.2")})
                    for binding in (b for rows in FORMULA_INPUT_AUTHORITY_BY_MATH_ID.values() for b in rows if b.binding_id in binding_ids):
                        resolved = _resolve_formula_input_binding(binding.math_spec_id, binding=binding, context=context,
                            owner_registry=registry, caller_assertions=MappingProxyType({}))
                        assert resolved.value == expected[binding.binding_id]
                    registry._check_probability_packet_refs_v1(tuple(p.packet_id for p in registry.packets), context=context)
                    assert prepared.model_use_authorized is prepared.source_authentication is prepared.native_packet_created is False
                    with pytest.raises(ContractValidationError):
                        resolver._check_probability_native_use_v1(replace(admitted[0]), evaluated_ns=time.time_ns())
                    fence._source_synchronized_v1 = False
                    with pytest.raises(InputAuthorityError):
                        registry._check_probability_packet_refs_v1((registry.packets[-1].packet_id,), context=context)
                assert reader.read_calls == initial_issuer_reads


def test_service_requires_one_typed_admission_owner_and_no_none_bypass() -> None:
    registry = CanonicalOwnerPacketRegistryV1()

    with pytest.raises(TypeError):
        QKUComputationControlPlaneV1(registry)  # type: ignore[call-arg]

    with pytest.raises(ContractValidationError) as missing:
        QKUComputationControlPlaneV1(
            registry,
            agent_capability_resolver=None,  # type: ignore[arg-type]
        )
    assert missing.value.reason_code is ReasonCode.INVALID_CONTRACT

    class _MalformedAdmission:
        def admit_operation(self, _request: object) -> object:
            return object()

    malformed = _service(_MalformedAdmission())
    request = _AdmissionProbeRequest()
    with pytest.raises(AuthorityDeniedError) as incompatible:
        malformed.resolve_identity(request)  # type: ignore[arg-type]
    assert incompatible.value.reason_code is ReasonCode.TASK_ENVELOPE_MISSING
    assert request.operation_body_reads == 0

    package = repo_root() / (
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane"
    )
    production_source = "\n".join(
        (package / name).read_text(encoding="utf-8")
        for name in ("agent_policy.py", "service.py")
    )
    assert "InternalNoEffectAdmissionProfileV1" not in production_source
    assert "INTERNAL_NO_EFFECT_ADMISSION_PROFILE" not in production_source
    assert "OWNER::TEST" not in production_source
    assert "CAPABILITY::READ_ONLY_TEST" not in production_source
    assert (
        "AGENT_ORCH1_RECEIPT_EXPLICITLY_NOT_APPLICABLE_INTERNAL_NO_EFFECT"
        not in production_source
    )

    from . import _synthetic_probability_issuance
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import OwnerAdapterError
    import time
    resolver, reader, requests = _synthetic_probability_issuance()
    missing = AgentCapabilityResolverV1(policy_store(), {})
    with pytest.raises(OwnerAdapterError):
        with missing._resolve_probability_issuer_context_v1(requests, evaluated_ns=time.time_ns()):
            raise AssertionError("missing original issuer was admitted")
    with pytest.raises(OwnerAdapterError):
        with resolver._resolve_probability_native_use_v1(object(), evaluated_ns=time.time_ns(),
                                                        deadline_ns=time.monotonic_ns() + 1_000_000_000):
            raise AssertionError("issuer attestation became model-use permission")
    assert reader.read_calls == 0


def test_all_fifteen_public_operations_execute_exactly_one_central_admission() -> None:
    exact_operation_names = (
        "resolve_identity",
        "resolve_contextual_computability",
        "resolve_applicable_stack",
        "resolve_required_inputs",
        "compute_component",
        "compute_stack",
        "compare_with_no_trade",
        "evaluate_trade_plan",
        "get_snapshot_view",
        "explain_resolution",
        "submit_candidate_proposal",
        "request_materialization_work_order",
        "compile_replay_paper_cohort",
        "register_replay_paper_result",
        "build_evidence_bundle",
    )
    structural_counts = {
        operation_name: inspect.getsource(
            getattr(QKUComputationControlPlaneV1, operation_name)
        ).count("_admit_agent_request(self, request)")
        for operation_name in exact_operation_names
    }

    assert IMPLEMENTED_OPERATION_IDS == exact_operation_names
    assert HELD_OPERATION_IDS == ()
    assert structural_counts == {
        operation_name: 1 for operation_name in exact_operation_names
    }

    from . import _synthetic_probability_issuance
    import time
    resolver, reader, requests = _synthetic_probability_issuance()
    with resolver._resolve_probability_issuer_context_v1(requests, evaluated_ns=time.time_ns()) as snapshot:
        for request in requests:
            resolver._admit_probability_issuer_v1(request, trusted_snapshot=snapshot)
    assert resolver.last_decision is None
    assert tuple(name for name in IMPLEMENTED_OPERATION_IDS) == exact_operation_names
    assert not any("probability" in name for name in exact_operation_names)


def test_eligible_denied_and_no_trade_decisions_control_body_execution() -> None:
    eligible = resolve_decision(make_resolver())
    denied = resolve_decision(
        make_resolver(
            envelope_overrides={"direct_provider_requested": True}
        )
    )
    no_trade = resolve_decision(
        make_resolver(
            envelope_overrides={
                "terminal_no_trade": True,
                "reoptimization_variable_ids": (
                    "market",
                    "venue",
                    "size",
                    "next_target",
                ),
            }
        ),
        requested_scope_refs={
            "qku_scope_refs": ("QKU::ST12E::TEST",),
            "formula_scope_refs": ("MATH-01",),
        },
    )

    eligible_request = _AdmissionProbeRequest()
    with pytest.raises(_OperationBodyTouched):
        _service(_CountingAdmission(eligible)).resolve_identity(
            eligible_request  # type: ignore[arg-type]
        )
    assert eligible_request.operation_body_reads == 1

    denied_request = _AdmissionProbeRequest()
    with pytest.raises(AuthorityDeniedError) as denied_error:
        _service(_CountingAdmission(denied)).resolve_identity(
            denied_request  # type: ignore[arg-type]
        )
    assert not isinstance(
        denied_error.value, NoTradeReoptimizationRouteError
    )
    assert denied_request.operation_body_reads == 0

    no_trade_request = _AdmissionProbeRequest()
    with pytest.raises(NoTradeReoptimizationRouteError) as routed:
        _service(_CountingAdmission(no_trade)).resolve_identity(
            no_trade_request  # type: ignore[arg-type]
        )
    assert routed.value.decision is no_trade
    assert no_trade_request.operation_body_reads == 0
    assert no_trade.decision_state is (
        AgentCapabilityDecisionStateV1.NO_TRADE_REOPTIMIZATION_ROUTED
    )
    assert no_trade.terminal_route == (
        "PRETRADE1_BOUNDED_TRADEPLAN_VARIABLE_REOPTIMIZATION"
    )
    assert {
        "qku_scope_refs=QKU::ST12E::TEST",
        "formula_scope_refs=MATH-01",
        "reoptimization_variable_id=market",
        "reoptimization_variable_id=venue",
        "reoptimization_variable_id=size",
        "reoptimization_variable_id=next_target",
    } <= set(no_trade.scope_refs)
    assert no_trade.agent_orch_receipt_ref
    assert no_trade.st12c_causation_correlation_refs
    assert "OWNER_REVIEW_REQUIRED" in no_trade.alternative_route_refs
    assert no_trade.no_effect_profile_ref == NO_EFFECT_PROFILE_REF
    assert "QKU_AND_FORMULA_IMMUTABLE" in no_trade.limitation_codes
    assert no_trade.runtime_effect_authorized is False
    assert set(("market", "venue", "size", "next_target")) <= set(
        NO_TRADE_REOPTIMIZATION_VARIABLE_IDS
    )


def test_idempotency_and_receipt_links_remain_existing_no_effect_truth() -> None:
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
    repeated = resolve_decision(resolver)
    duplicate = resolve_decision(
        resolver,
        capability_bundle_id=second_bundle.bundle_id,
        request_idempotency_key="ST12E_IDEMPOTENCY::SECOND",
    )

    assert first is repeated
    assert first.agent_orch_receipt_ref.startswith(
        "AGENT_ORCH1::AGENTDECISIONRECEIPTV1_"
    )
    assert first.agent_orch_receipt_ref in first.evidence_refs
    assert first.task_id in first.evidence_refs
    assert first.st12c_causation_correlation_refs
    assert first.no_effect_profile_ref == NO_EFFECT_PROFILE_REF
    assert first.runtime_effect_authorized is False
    assert ReasonCode.IDEMPOTENCY_CONFLICT in duplicate.reason_codes
    assert not duplicate.eligible


def test_all_parameter_rows_retain_no_orphan_and_orthogonal_route_fields() -> None:
    rows = policy_store().snapshot.parameter_scope_rows

    assert tuple(rows) == tuple(
        sorted(rows, key=lambda value: int(value.rsplit("::", 1)[1]))
    )
    for parameter_id, row in rows.items():
        assert row.parameter_id == parameter_id
        assert row.upstream_source_universe_ref
        assert row.mapped_compatibility_refs
        assert row.unmapped_compatibility_refs
        assert row.current_principal_refs_or_exact_gap
        assert "ComputationParameterPolicyV1::" in row.value_policy_ref
        assert row.st12e_binding_state
        assert row.st12e_capability_binding_ref_or_explicit_absence
        assert row.st12e_certified_source_universe_ref_or_explicit_absence
        assert row.st12e_current_principal_refs_or_explicit_absence
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


def test_owner_actions_and_outside_e_parameters_remain_request_only() -> None:
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

    outside_parameter_id = next(
        parameter_id
        for parameter_id, row in policy_store().snapshot.parameter_scope_rows.items()
        if row.st12e_binding_state == ST12E_BINDING_OUTSIDE_SCOPE
    )
    decision = resolve_decision(
        make_resolver(), requested_parameter_ids=(outside_parameter_id,)
    )
    assert ReasonCode.PARAMETER_SCOPE_MISMATCH in decision.reason_codes
    assert not decision.eligible
