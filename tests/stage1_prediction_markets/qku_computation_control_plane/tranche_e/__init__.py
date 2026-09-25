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


class _SyntheticProbabilityIssuerV1:
    """Synthetic port mechanics only; never authentic protocol/model acceptance."""
    def __init__(self, policy, *, same_domain=False, suppress=False, on_exit=None, transform=None):
        self.policy, self.same_domain, self.suppress = policy, same_domain, suppress
        self.on_exit, self.transform = on_exit, transform
        self.read_calls, self.active = 0, False
        self.last_snapshot = None

    def read_probability_issuers(self, requests, *, evaluated_ns):
        from dataclasses import asdict
        import json
        from src.qtt.stage1_prediction_markets.qku_computation_control_plane.protocols import (
            ProbabilityIssuerContextV1, ProbabilityIssuerGrantV1, ProbabilityIssuerSnapshotV1)
        reader = self
        entries = []
        for index, request in enumerate(requests):
            domain = "SYNTHETIC::DOMAIN" if self.same_domain else "SYNTHETIC::DOMAIN::" + request.issuer_ref
            context = ProbabilityIssuerContextV1(request.issuer_ref, domain, "SYNTHETIC::AUTH", "SYNTHETIC::SESSION",
                "SYNTHETIC::PROCESS", evaluated_ns - 1, evaluated_ns + 60_000_000_000)
            grant = ProbabilityIssuerGrantV1("SYNTHETIC::GRANT::" + str(index), request.issuer_ref, domain,
                context.authentication_ref, context.session_ref, context.process_ref, self.policy.policy_version,
                1, request.role, request.scope, request.subject_refs, "SYNTHETIC::DECISION::" + str(index),
                self.policy.registry_version, evaluated_ns - 1, context.valid_until_ns,
                "OFFLINE_PRODUCER_RECEIPT_ATTESTATION", "SCOPED_NO_EFFECT_ISSUER_ATTESTATION")
            decision = dict(row_id=grant.decision_ref, object_type="ProbabilityIssuerDecisionViewV1",
                object_version=self.policy.registry_version, principal_ref=request.issuer_ref, role=request.role,
                scope=asdict(request.scope), subject_refs=request.subject_refs, policy_ref=self.policy.policy_version,
                policy_epoch=1, purpose="OFFLINE_PRODUCER_RECEIPT_ATTESTATION",
                authentication_ref=context.authentication_ref, session_ref=context.session_ref,
                process_ref=context.process_ref, control_plane_only=True, fake_receipt_created=False,
                runtime_side_effect_allowed=False, source_truth_created=False, order_submission_created=False,
                live_execution_created=False)
            entries.append((context, grant, json.dumps(decision, sort_keys=True, separators=(",", ":"), ensure_ascii=False)))
        snapshot = ProbabilityIssuerSnapshotV1("SYNTHETIC::ISSUER-SNAPSHOT", self.policy.policy_version, 1,
            self.policy.registry_version, "SYNTHETIC::PROCESS", evaluated_ns, evaluated_ns + 60_000_000_000, (), tuple(entries))
        if self.transform is not None:
            snapshot = self.transform(snapshot)
        self.last_snapshot = snapshot
        class Read:
            def __enter__(self):
                if reader.active:
                    raise AssertionError("synthetic issuer was acquired reentrantly")
                reader.active = True
                reader.read_calls += 1
                return snapshot
            def __exit__(self, typ, value, tb):
                reader.active = False
                if reader.on_exit is not None:
                    reader.on_exit(snapshot)
                return reader.suppress
        return Read()


def _synthetic_probability_issuance(*, same_domain=False, suppress=False, on_exit=None, transform=None):
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import ProbabilityProducerScopeV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.protocols import ProbabilityIssuerReadRequestV1
    scope = ProbabilityProducerScopeV1("GEMINI_TITAN_DIRECT", "SYNTHETIC::MODEL", "SYNTHETIC::CELL",
        "SYNTHETIC::LOCK", "SYNTHETIC::REFERENCE", "SYNTHETIC::FAMILY", "SYNTHETIC::POLICY", "SYNTHETIC::ENVIRONMENT", 1)
    reader = _SyntheticProbabilityIssuerV1(policy_store().snapshot, same_domain=same_domain, suppress=suppress,
                                           on_exit=on_exit, transform=transform)
    resolver = AgentCapabilityResolverV1(policy_store(), {}, probability_issuer_reader=reader)
    requests = tuple(ProbabilityIssuerReadRequestV1(role, scope, ("SYNTHETIC::SUBJECT",), "SYNTHETIC::" + role)
        for role in ("SOURCE_RIGHTS", "MODEL_BUILD", "COMPUTATION", "MODEL_REVIEW"))
    return resolver, reader, requests


def _synthetic_registered_prediction():
    """Original-object lifetime fixture, not an accepted fitted prediction."""
    import time
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
        _ProbabilityRevocationCutV1, PreparedProbabilityPredictionV1)
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import _ProbabilityDependencyFenceV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.persistence import InMemoryPersistenceAdapterV1
    resolver, reader, requests = _synthetic_probability_issuance()
    now = time.time_ns()
    with resolver._resolve_probability_issuer_context_v1(requests, evaluated_ns=now) as snapshot:
        admissions = tuple(resolver._admit_probability_issuer_v1(request, trusted_snapshot=snapshot) for request in requests)
    cut = _ProbabilityRevocationCutV1("SYNTHETIC::CHECKPOINT", 0, None, (), now, now + 30_000_000_000)
    fence = _ProbabilityDependencyFenceV1(persistence=InMemoryPersistenceAdapterV1(), issuer_resolver=resolver,
        scope=requests[0].scope, issuer_snapshot=snapshot, source_issuer_ref=requests[0].issuer_ref,
        stream_ref="SYNTHETIC::STREAM", baseline_ref="SYNTHETIC::BASELINE", baseline_ordinal=0,
        baseline_invalidated_refs=(), cut=cut, max_prepared=8, max_pending=2, max_records=32, initial_latch=False)
    prepared = PreparedProbabilityPredictionV1("SCORE_RESEARCH_ONLY", "SYNTHETIC::RESULT", "SYNTHETIC::REVIEW",
        requests[0].scope.input_lock_ref, "SYNTHETIC::QUERY-LOCK", ("f",), (("query", ("0x0.0p+0",)),),
        (("query", 0.6, 0.5, 0.7),), admissions[0].authority_dependency_refs, now, cut.valid_until_ns, 1, ())
    entry = fence._register_v1(prepared, kind="PREDICTION", view=resolver._probability_last_issuer_view_v1,
        dependency_refs=prepared.dependency_refs, valid_until_ns=prepared.valid_until_ns,
        value_node_limit=10000,
        metadata={"fixture_class": "SYNTHETIC_ORIGINAL_OBJECT_LIFETIME_ONLY"})
    return resolver, reader, fence, prepared, entry


def _synthetic_prediction_receipt_graph():
    """Closed historical wire fixtures, never authentic issuance or acceptance.

    Every dependency and claim here is synthetic. Only test-owned persistence
    may seed these records; production append authority is intentionally absent.
    """
    import time
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import ProbabilityProducerScopeV1, NoEffectFlagsV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import (
        ProbabilityProducerControlReceiptV1, _probability_control_record_v1)
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.protocols import ProbabilityIssuerAdmissionV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.model_risk import NoTradeConditionOutcomeV1, NO_TRADE_CONDITION_IDS_V1

    now = time.time_ns()
    base, expiry = now - 1_000_000_000, now + 60_000_000_000
    scope = ProbabilityProducerScopeV1("KALSHI_US_DCM_DIRECT", "SYNTHETIC::MODEL", "SYNTHETIC::CELL",
        "SYNTHETIC::LOCK", "SYNTHETIC::REFERENCE", "SYNTHETIC::FAMILY", "SYNTHETIC::POLICY", "SYNTHETIC::ENVIRONMENT", 1)
    ids = {key: "SYNTHETIC::" + key for key in ("BINDING", "MANIFEST", "CATALOG", "RESULT", "REVIEW", "ARTIFACT",
        "QUERY-LOCK", "VALIDATION", "USE-LIMIT", "RISK", "PUBLICATION", "REVOCATION")}
    roles = ("SOURCE_RIGHTS", "ENVIRONMENT", "MODEL_BUILD", "MODEL_REVIEW", "USE_POLICY", "CATALOG")
    role_refs = {role: "SYNTHETIC::PARENT::" + role for role in roles}
    records = {}
    def record(ref, kind, body, offset, dependencies=()):
        value = _probability_control_record_v1(record_id=ref,
            payload=ProbabilityProducerControlReceiptV1("PROBABILITY_PRODUCER_CONTROL_V1", kind, scope,
                base + offset, base + offset, base + offset, tuple(dict.fromkeys(dependencies)), expiry, body),
            context_ref="SYNTHETIC::HISTORY", causation_id="SYNTHETIC::CAUSE::" + ref,
            correlation_id="SYNTHETIC::CORRELATION", traceparent="SYNTHETIC::TRACE", tracestate="SYNTHETIC::STATE")
        records[ref] = value
        return value
    record(ids["BINDING"], "INPUT_BINDING", dict(owner_epoch=1, objects=tuple(
        dict(role=role, object_ref=ref, frame_count=1, byte_count=1) for role, ref in
        (("MODEL", scope.model_artifact_ref), ("CATALOG", ids["CATALOG"]), ("POLICY", scope.policy_ref))),
        acceptance_manifest_ref=ids["MANIFEST"]), 10)
    record(ids["MANIFEST"], "ACCEPTANCE_MANIFEST",
        dict(binding_ref=ids["BINDING"], receipt_refs=tuple(role_refs.values())), 10)
    claims = {
        "SOURCE_RIGHTS": dict(input_lock_ref=scope.input_lock_ref, reference_cohort_ref=scope.reference_cohort_ref,
            catalog_ref=ids["CATALOG"], input_class="SCOPED_DATA_RIGHTS_AND_SOURCE_SEMANTICS_NOT_DOCUMENTATION_ONLY"),
        "ENVIRONMENT": dict(environment_ref=scope.environment_ref, versions=(("SYNTHETIC_COMPONENT", "SYNTHETIC_VERSION"),),
            check_class="TARGET_ENVIRONMENT_WITH_BOUNDED_SYNTHETIC_ADAPTER_PARITY"),
        "MODEL_BUILD": dict(model_artifact_ref=scope.model_artifact_ref, feature_names=("f",), model_kind="CALIBRATED_LOGISTIC",
            reference_cohort_ref=scope.reference_cohort_ref, reference_cutoff_ns=base, artifact_available_ns=base + 3,
            build_class="FROZEN_BASE_PIPELINE_AND_SELECTED_CALIBRATOR", export_parity_kind="ACTUAL_SUBJECT_PIPELINE_ROUNDTRIP",
            started_ns=base + 1, completed_ns=base + 2),
        "MODEL_REVIEW": dict(model_artifact_ref=scope.model_artifact_ref, review_class="CONCEPTUAL_AND_IMPLEMENTATION_REVIEW",
            scope_of_conclusion="BOUNDED_OFFLINE_DIAGNOSTICS_ONLY", blocker_codes=()),
        "USE_POLICY": dict(policy_ref=scope.policy_ref, family_ref=scope.family_ref, targets=("f.mean",),
            target_domains=(("f.mean", "REAL"),), replicate_count=1000, precision_protocol_ref=None,
            limits=dict(max_catalog_rows=1000, max_reference_rows=1000, max_targets=32,
                max_model_bytes=65536, max_record_bytes=65536, max_total_bank_bytes=1_000_000),
            purpose="OFFLINE_PRODUCER_DIAGNOSTICS", permitted_model_use_modes=()),
        "CATALOG": dict(catalog_ref=ids["CATALOG"], owner_epoch=1, after_ordinal=0, complete_through_ns=base,
            row_count=0, membership_class="IMMUTABLE_ORIGINAL_OBSERVATION_MEMBERSHIP"),
    }
    admissions = []
    for role in roles:
        authority = "SYNTHETIC::AUTHORITY::" + role
        issuer = "SYNTHETIC::ISSUER::" + role
        admissions.append(ProbabilityIssuerAdmissionV1(role, issuer, (authority,), expiry, NoEffectFlagsV1()))
        record(role_refs[role], "ACCEPTANCE_RECEIPT", dict(role=role, binding_ref=ids["BINDING"],
            subject_refs=(scope.model_artifact_ref,), depends_on=(), issuer_ref=issuer, observed_ns=base + 10,
            claims=claims[role], issuer_admission_refs=(authority,)), 10, (authority,))
    ancestry = (ids["BINDING"], ids["MANIFEST"], *role_refs.values())
    record(ids["RESULT"], "PREDICTION_RESULT", dict(artifact_ref=ids["ARTIFACT"], artifact_byte_count=1,
        artifact_frame_count=1, input_lock_id=scope.input_lock_ref, prediction_input_lock_id=ids["QUERY-LOCK"],
        plan_id="SYNTHETIC::PLAN", producer_ref="SYNTHETIC::COMPUTATION", producer_control_domain_ref="SYNTHETIC::BUILD-DOMAIN",
        input_available_ns=base + 20, started_ns=base + 20, completed_ns=base + 30), 30, ancestry)
    protocol_names = ("ExperimentProtocolV1", "CandidateAndVariantInventoryV1", "SearchAndResearchBudgetV1",
        "FalsificationAndNoTradePolicyV1", "ProtocolChangeControlV1", "MetricsDefinitionRegistryV1", "EventTimeAndClockSchemaV1",
        "EconomicAccountingClassRegistryV1", "MetricUnitAndBasisRegistryV1", "ModelInventoryAndRiskTierV1",
        "IndependentValidationProtocolV1", "UseLimitAndRollbackPolicyV1", "EvidenceSufficiencyPolicyV1")
    protocols = tuple((name, "SYNTHETIC::PROTOCOL::" + name) for name in protocol_names)
    evidence = tuple("SYNTHETIC::EVIDENCE::" + str(i) for i in range(13))
    cutoffs = base + 110
    common = dict(protocol_ref=protocols[10][1], effective_cutoff_ns=cutoffs, recorded_cutoff_ns=cutoffs,
        qualification_scope="SYNTHETIC_REFERENCE", purpose="BOUNDED_OFFLINE_DIAGNOSTICS_ONLY",
        conclusion="SUPPORTED_FOR_REVIEW", blocker_codes=())
    prefix = (scope.model_artifact_ref, ids["RESULT"], ids["ARTIFACT"], ids["QUERY-LOCK"])
    conditions = tuple(NoTradeConditionOutcomeV1(name, False, (), ()) for name in NO_TRADE_CONDITION_IDS_V1)
    basis = (
        ("VALIDATION", "MODEL_REVIEW", 60, (*prefix, *evidence),
         (ids["RESULT"], role_refs["MODEL_BUILD"], role_refs["MODEL_REVIEW"], *evidence),
         dict(prediction_basis_kind="INDEPENDENT_PREDICTION_VALIDATION", protocol_coverage=tuple(
            (name, ref, "SUPPORTED_FOR_REVIEW", (ev,)) for (name, ref), ev in zip(protocols, evidence, strict=True)),
            result_commit_observed_ns=base + 40)),
        ("USE-LIMIT", "USE_POLICY", 70, prefix, (role_refs["USE_POLICY"], ids["RESULT"]),
         dict(prediction_basis_kind="BOUND_PREDICTION_USE_LIMIT", parent_use_policy_ref=role_refs["USE_POLICY"],
            feature_names=("f",), query_rule="EXACT_COMMITTED_QUERY_LOCK_AND_ACCEPTED_PARENT_CONTEXT",
            permitted_model_use_modes=(), maximum_valid_until_ns=expiry)),
        ("RISK", "MODEL_REVIEW", 80, prefix, (ids["RESULT"], ids["VALIDATION"], ids["USE-LIMIT"]),
         dict(prediction_basis_kind="PREDICTION_MODEL_RISK_BASIS", validation_receipt_refs=(ids["VALIDATION"],),
            use_limit_ref=ids["USE-LIMIT"], conditions=conditions,
            scope_of_conclusion="PREDICTION_EVIDENCE_ONLY_NOT_ST12F_ECONOMIC_PROMOTION")),
    )
    for key, role, offset, subjects, parents, extra in basis:
        authority = "SYNTHETIC::AUTHORITY::" + role
        record(ids[key], "ACCEPTANCE_RECEIPT", dict(role=role, binding_ref=ids["BINDING"], subject_refs=subjects,
            depends_on=parents, issuer_ref="SYNTHETIC::ISSUER::" + role, observed_ns=base + offset,
            claims={**common, **extra}, issuer_admission_refs=(authority,)), offset, (*parents, authority))
    record(ids["REVIEW"], "PREDICTION_REVIEW", dict(result_ref=ids["RESULT"], artifact_ref=ids["ARTIFACT"],
        reviewer_ref="SYNTHETIC::INDEPENDENT-REVIEWER", reviewer_control_domain_ref="SYNTHETIC::REVIEW-DOMAIN",
        review_state="CALIBRATED_FOR_DECLARED_CONTEXT", validation_receipt_refs=(ids["VALIDATION"],),
        use_limit_ref=ids["USE-LIMIT"], model_risk_receipt_ref=ids["RISK"], result_commit_observed_ns=base + 40,
        started_ns=base + 90, completed_ns=base + 100, blocker_codes=()), 100,
        (*ancestry, ids["RESULT"], ids["VALIDATION"], ids["USE-LIMIT"], ids["RISK"]))
    record(ids["PUBLICATION"], "PUBLICATION", dict(request_id="SYNTHETIC::PUBLICATION-REQUEST", expected_head_ref=None,
        expected_sequence=0, expected_high_watermark=0, kind="HARD_FAILURE", cutoff_ns=cutoffs, catalog_ref=None,
        result_ref=None, selected_rows=(), family_result=None, reason="SYNTHETIC_HARD_FAILURE",
        after=dict(scope={name: getattr(scope, name) for name in scope.__dataclass_fields__}, head_ref=ids["PUBLICATION"],
            sequence=1, high_watermark=0, last_maturity_ns=0, last_cutoff_ns=cutoffs, bad_streak=0, green_streak=0, latched=True)), 110)
    record(ids["REVOCATION"], "REVOCATION_APPLICATION", dict(notice_id="SYNTHETIC::NOTICE", issuer_ref="SYNTHETIC::SOURCE",
        stream_ref="SYNTHETIC::STREAM", stream_ordinal=1, observed_ns=cutoffs, baseline_ref="SYNTHETIC::BASELINE",
        invalidated_dependency_refs=("SYNTHETIC::UNRELATED-DEPENDENCY",)), 110,
        ("SYNTHETIC::NOTICE", "SYNTHETIC::SOURCE", "SYNTHETIC::BASELINE"))
    return scope, records, ids, protocols, tuple(admissions), conditions, cutoffs
