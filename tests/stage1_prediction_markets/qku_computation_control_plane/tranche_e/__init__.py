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
    def __init__(self, policy, *, same_domain=False, suppress=False, on_exit=None, transform=None, valid_until_ns=None):
        self.policy, self.same_domain, self.suppress = policy, same_domain, suppress
        self.on_exit, self.transform = on_exit, transform
        self.read_calls, self.active = 0, False
        self.last_snapshot = None
        self.valid_until_ns = valid_until_ns

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
                "SYNTHETIC::PROCESS", evaluated_ns - 1, evaluated_ns + 60_000_000_000 if self.valid_until_ns is None else self.valid_until_ns)
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
            self.policy.registry_version, "SYNTHETIC::PROCESS", evaluated_ns, evaluated_ns + 60_000_000_000 if self.valid_until_ns is None else self.valid_until_ns, (), tuple(entries))
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


def _synthetic_probability_issuance(*, same_domain=False, suppress=False, on_exit=None, transform=None, valid_until_ns=None):
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import ProbabilityProducerScopeV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.protocols import ProbabilityIssuerReadRequestV1
    scope = ProbabilityProducerScopeV1("GEMINI_TITAN_DIRECT", "SYNTHETIC::MODEL", "SYNTHETIC::CELL",
        "SYNTHETIC::LOCK", "SYNTHETIC::REFERENCE", "SYNTHETIC::FAMILY", "SYNTHETIC::POLICY", "SYNTHETIC::ENVIRONMENT", 1)
    reader = _SyntheticProbabilityIssuerV1(policy_store().snapshot, same_domain=same_domain, suppress=suppress,
                                           on_exit=on_exit, transform=transform, valid_until_ns=valid_until_ns)
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


"""Normative synthetic operands; construction does not import numerical libraries."""
from types import MappingProxyType

BASE_NS = 1_600_000_000_000_000_000
FEATURES = ('touch_imbalance', 'microprice_displacement_ticks', 'spread_ticks')
BLOCK = tuple(((x / 2., x, 2. + x), y) for x, y in
              zip((-1., -1., -1., -1., 1., 1., 1., 1.),
                  (0, 0, 0, 1, 0, 1, 1, 1), strict=True))

def _v35_full_bank_operands():
    def clusters(partition, count, offset):
        result = []
        for k in range(count):
            t = BASE_NS + offset + k * 1_000_000
            rows = tuple((f'ENG:{partition}:R{k:03d}:{j}', values, y)
                         for j, (values, y) in enumerate(BLOCK))
            result.append((f'ENG:{partition}:C{k:03d}', t, t + 2_000,
                           t, t + 1_000, rows))
        return tuple(result)
    return MappingProxyType(dict(
        fit_clusters=clusters('FIT', 97, 0),
        calibration_clusters=clusters('CAL', 100, 1_000_000_000),
        final_cluster_ids=tuple(f'ENG:FINAL:C{i:03d}' for i in range(30)),
        final_row_ids=tuple(f'ENG:FINAL:R{i:03d}' for i in range(30)),
        final_start_ns=BASE_NS + 3_000_000_000,
        feature_names=FEATURES,
        requests=tuple((f'ENG:Q:{i}', (x / 2., x, 2. + x))
                       for i, x in enumerate((-1., -0.5, 0., 0.5, 1.))),
        input_lock_id='ENG:INPUT-LOCK', prediction_input_lock_id='ENG:QUERY-LOCK',
        plan_id='ENG:FULL-BANK-PLAN', master_seed=0, replicate_count=1000,
        method='PAIRED_IID_CLUSTERS', block_length=None,
        fit_cutoff_ns=BASE_NS + 500_000_000,
        calibration_cutoff_ns=BASE_NS + 2_000_000_000,
        embargo_ns=1_000, max_plan_cells=197_000, max_expanded_rows=800,
        max_prediction_cells=5_005, max_feature_cells=7_242, max_fit_calls=3_003))

"""Pre-candidate engineering reference. Never call QTT to obtain expected output."""
import json
import math
import sys
import threading
import warnings
from fractions import Fraction


def _v35_independent_model_reference(parameters):
    # These imports happen only in the separately authorized selected MODEL run.
    import numpy as np
    import scipy
    import sklearn
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    from sklearn.linear_model import LogisticRegression
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.frozen import FrozenEstimator
    from sklearn.exceptions import ConvergenceWarning
    from threadpoolctl import threadpool_limits
    expected = ('3.14.7', '2.5.2', '1.18.1', '1.9.0')
    actual = (sys.version.split()[0], np.__version__, scipy.__version__, sklearn.__version__)
    if actual != expected:
        raise RuntimeError(f'selected MODEL mismatch: {actual!r}; expected {expected!r}')
    if len(threading.enumerate()) != 1:
        raise RuntimeError('reference requires its original synchronous worker')
    fr = tuple(r for c in parameters['fit_clusters'] for r in c[5])
    cr = tuple(r for c in parameters['calibration_clusters'] for r in c[5])
    xf = np.ascontiguousarray([r[1] for r in fr], dtype=np.float64)
    xc = np.ascontiguousarray([r[1] for r in cr], dtype=np.float64)
    yf = np.asarray([r[2] for r in fr], dtype=np.int64)
    yc = np.asarray([r[2] for r in cr], dtype=np.int64)
    base = LogisticRegression(C=1.0, l1_ratio=0.0, dual=False, tol=0.0001,
        fit_intercept=True, intercept_scaling=1, class_weight=None, random_state=None,
        solver='lbfgs', max_iter=100, verbose=0, warm_start=False, n_jobs=None)
    model = Pipeline([('scaler', StandardScaler(copy=True, with_mean=True, with_std=True)),
                      ('base', base)])
    with threadpool_limits(limits=1), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        model.fit(xf, yf)
        frozen_before = tuple(np.array(x, copy=True) for x in
            (base.coef_, base.intercept_, model.named_steps['scaler'].mean_,
             model.named_steps['scaler'].var_, model.named_steps['scaler'].scale_))
        calibrated = CalibratedClassifierCV(FrozenEstimator(model), method='sigmoid',
                                            cv=None, n_jobs=1, ensemble=False).fit(xc, yc)
    if any(issubclass(w.category, ConvergenceWarning) for w in caught):
        raise RuntimeError('independent reference did not converge')
    scaler = model.named_steps['scaler']
    after = (base.coef_, base.intercept_, scaler.mean_, scaler.var_, scaler.scale_)
    if not all(np.array_equal(a, b) for a, b in zip(frozen_before, after, strict=True)):
        raise RuntimeError('reference frozen estimator changed')
    if not (scaler.mean_.tolist() == [0., 0., 2.] and scaler.var_.tolist() == [0.25, 1., 1.]
            and scaler.scale_.tolist() == [0.5, 1., 1.] and int(scaler.n_samples_seen_) == 776):
        raise RuntimeError('reference fixture/scaler moments differ')
    if len(calibrated.calibrated_classifiers_) != 1:
        raise RuntimeError('reference calibrator count')
    calibrators = calibrated.calibrated_classifiers_[0].calibrators
    if len(calibrators) != 1:
        raise RuntimeError('reference sigmoid count')
    sigmoid = calibrators[0]
    if base.classes_.tolist() != [0, 1]:
        raise RuntimeError('reference class order')
    coefficients = tuple(float(v) for v in base.coef_.ravel())
    intercept = float(base.intercept_[0])
    a, b = float(sigmoid.a_), float(sigmoid.b_)
    if not all(math.isfinite(v) for v in (*coefficients, intercept, a, b)) or not all(v > 0 for v in coefficients) or a >= 0:
        raise RuntimeError('reference finite/nondegenerate geometry')
    export = dict(schema='QTT_MODEL_DATA_ONLY_V35', kind='CALIBRATED_LOGISTIC',
        feature_names=list(parameters['feature_names']), environment=dict(zip(('python','numpy','scipy','scikit-learn'),actual,strict=True)),
        scaler=dict(mean=[float(v).hex() for v in scaler.mean_],
                    var=[float(v).hex() for v in scaler.var_],
                    scale=[float(v).hex() for v in scaler.scale_],n_samples_seen=int(scaler.n_samples_seen_)),
        coefficients=[float(v).hex() for v in base.coef_.ravel()],
        intercept=float(np.asarray(base.intercept_).ravel()[0]).hex(), classes=[0,1],
        calibration=dict(method='sigmoid',response='decision_function',a=a.hex(),b=b.hex()),
        fit_ids=[r[0] for r in fr],calibration_ids=[r[0] for r in cr],final_ids=list(parameters['final_row_ids']))
    requests = tuple(parameters['requests'])
    query = np.ascontiguousarray([r[1] for r in requests],dtype=np.float64)
    native = calibrated.predict_proba(query)[:,1]
    scalar = []
    for (key, values), nv in zip(requests, native, strict=True):
        scaled = tuple((v - m) / z for v, m, z in zip(values, (0., 0., 2.), (0.5, 1., 1.), strict=True))
        margin = math.fsum((intercept, *(c * v for c, v in zip(coefficients, scaled, strict=True))))
        u = -(a*margin+b)
        e = math.exp(-abs(u))
        p = 1/(1+e) if u >= 0 else e/(1+e)
        # Same retained parity magnitudes, compared with exact rational arithmetic.
        allowance = Fraction(1, 10**15) + Fraction(1, 10**12)*abs(Fraction.from_float(float(nv)))
        if abs(Fraction.from_float(float(nv))-Fraction.from_float(p)) > allowance:
            raise RuntimeError('independent native/scalar representation differs')
        scalar.append((key,margin,p))
    if not all(scalar[i][2] < scalar[i+1][2] for i in range(4)):
        raise RuntimeError('reference predictions not feature-sensitive')
    return dict(model=export, predictions=tuple(scalar),
                reference_work=dict(base_fits=1,calibration_fits=1),
                warning_categories=tuple(w.category.__name__ for w in caught),
                native_acceptance=False, operational_use=False)


def _v35_full_bank_source(parameters, scope, wall_origin_ns, valid_until_ns):
    """Original typed synthetic custody, with no adapter or venue invocation."""
    from dataclasses import replace
    from datetime import datetime, timedelta, timezone
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import models as m
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
        PITClockSetV3, PITEventDispositionV1)
    from src.qtt.stage1_prediction_markets.market_data_ingest import policy
    from src.qtt.stage1_prediction_markets.market_data_ingest.adapter import (
        build_pit_read_requests_v2, PITCanonicalEventV2, _PITCatalogPayloadV2)
    from src.qtt.stage1_prediction_markets.market_data_ingest.binding import build_selected_pit_public_data_contracts_v2
    from tests.source_evidence.test_s1_pit_data_phase_a_01 import _build_source_and_rights
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    def utc(ns):
        assert type(ns) is int and ns % 1000 == 0
        return epoch + timedelta(microseconds=ns//1000)
    observed = utc(wall_origin_ns//1000*1000)
    expires = utc(valid_until_ns//1000*1000)
    original_sources, original_rights = _build_source_and_rights()
    sources = tuple(replace(v, receipt_id='ENG:SOURCE:'+v.profile_id.value,
        checked_at_utc=observed, effective_at_utc=observed, expires_at_utc=expires) for v in original_sources)
    rights = tuple(replace(v, receipt_id='ENG:RIGHTS:'+v.profile_id.value,
        checked_at_utc=observed, expires_at_utc=expires) for v in original_rights)
    contracts = build_selected_pit_public_data_contracts_v2(policy.PIT_SELECTED_SCOPE_V2,
        sources, rights, evaluated_at_utc=observed)
    contract = next(c for c in contracts if c.profile_id.value == scope.profile_id)
    request = next(r for r in build_pit_read_requests_v2(contracts)
        if r.profile_id == contract.profile_id and r.event_kind.value == 'CATALOG'
        and r.path_or_channel == '/markets' and r.read_action.value == 'GET')
    assert request.access_class.value == 'PUBLIC_UNAUTHENTICATED_READ'
    manifest = m.ProbabilityModelCellManifestV2(scope.cell_manifest_ref, 'PM-QAML-FILL-V2', scope.profile_id,
        'ENG:VENUE-SCOPE', 'QSP-02', parameters['feature_names'], ('ratio','ticks','ticks'), 'ENG:LABEL',
        'ENG:HORIZON', 'ENG:CLUSTER-RULE', 'ENG:SPLIT', 'ENG:ESTIMATOR', 'ENG:CALIBRATION',
        'ENG:UNCERTAINTY', 'ENG:OOD', 'ENG:DRIFT', ('ENG:CAPABILITY',), expires)
    source_rows, pit_rows, references, final_catalog = [], [], [], []
    dependencies = [contract.scope_receipt_ref, contract.source_currentization_receipt_ref,
        contract.rights_receipt_ref, 'ENG:PIT', 'ENG:FRESHNESS', 'ENG:CONTINUITY', 'ENG:CAPABILITY',
        'ENG:SEMANTICS', 'ENG:LABEL-AUTHORITY', 'ENG:CLOCK-QUALITY']
    clusters = tuple((*c, False) for c in (*parameters['fit_clusters'], *parameters['calibration_clusters']))
    clusters += tuple((cid, parameters['final_start_ns']+i*1000000, parameters['final_start_ns']+i*1000000,
        parameters['final_start_ns']+i*1000000, parameters['final_start_ns']+i*1000000,
        ((rid, (0.,0.,2.), None),), True)
        for i,(cid,rid) in enumerate(zip(parameters['final_cluster_ids'],parameters['final_row_ids'],strict=True)))
    for cluster_ordinal, (cid, available, mature, _, _, rows, final) in enumerate(clusters, 1):
        row_ids = tuple(r[0] for r in rows)
        row = m._ProbabilityMaturityClusterV1(cid, row_ids, cluster_ordinal, mature, available)
        (final_catalog if final else references).append(row)
        snapshot_ref = 'ENG:SNAPSHOT:'+cid
        dependencies.append(snapshot_ref)
        for rid, values, label in rows:
            i = len(source_rows)+1
            at = utc(available)
            event_id, commit_ref = 'ENG:EVENT:'+str(i), 'ENG:COMMIT:'+str(i)
            feature = m.SelectedFeatureVectorV2(scope.profile_id, manifest.scope_id, 'ENG:MARKET', 'ENG:CONTRACT',
                'YES', 'NOT_APPLICABLE', manifest.task_id, manifest.cell_manifest_id, cid, manifest.horizon_or_lead_bucket,
                manifest.feature_pack_id, 'ENG:FEATURE-V2', manifest.ordered_feature_names, values, manifest.feature_units,
                (False,False,False), at, at, at, at, at, i, None, event_id, snapshot_ref,
                contract.rights_receipt_ref, 'ENG:PIT', 'ENG:FRESHNESS', 'ENG:CONTINUITY', 'ENG:CAPABILITY', 'ENG:SEMANTICS')
            target = m.SelectedLabelRecordV2(manifest.label_contract_id, feature.contract_id, cid, 'BINARY', label,
                'UNIT_INTERVAL', 'REALIZED', at, None if final else utc(mature), None if final else utc(mature),
                'PENDING' if final else 'MATURED', 'ENG:LABEL-AUTHORITY', None, 'ENG:LABEL-V1')
            clocks = PITClockSetV3(at, None, at, i*4, at, i*4+1, at, i*4+2, at, i*4+3, None, None,
                'ENG:SYNTHETIC-PROCESS', 'ENG:SYNTHETIC-MONOTONIC', 'ENG:SYNTHETIC-WALL', 'ENG:CLOCK-QUALITY', 0)
            event = PITCanonicalEventV2(event_id, contract.profile_id, feature.market_id, feature.contract_id,
                '/markets', 'ENG:CONNECTION', 'ENG:CAPTURE', i, request.event_kind, 'PIT_CANONICAL_EVENT_V2',
                contract.wire_dialect_policy, contract.source_contract_version, None, None, None, None,
                _PITCatalogPayloadV2(request.event_kind, (('market_id','ENG:MARKET'),)), contract.depth_class, clocks,
                'ENG:PRE-STATE', snapshot_ref, PITEventDispositionV1.COMMITTED, None, contract.rights_receipt_ref,
                contract.source_currentization_receipt_ref, commit_ref, None, None, None, True, True, True, True, True,
                m.NO_EFFECTS_V1)
            dependencies.append(commit_ref)
            source_rows.append((rid, feature, target))
            pit_rows.append((rid, contract, request, event))
    assert len(source_rows) == 1606 and len(references) == 197 and len(final_catalog) == 30
    assert len(set(r[0] for r in source_rows)) == 1606 and len(set(dependencies)) < 4096
    source = MappingProxyType(dict(manifest=manifest, feature_rows=tuple(source_rows),
        input_lock_ref=scope.input_lock_ref, binding_ref='ENG:BINDING', pit_rows=tuple(pit_rows),
        prediction_parameters=parameters))
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import _probability_bind_pit_rows_v1
    _probability_bind_pit_rows_v1(source, source['feature_rows'], set(dependencies), wall_origin_ns)
    return source, tuple(references), tuple(final_catalog), tuple(dependencies), (sources, rights, contracts)


_V35_SERVICE_CONDITIONS = (
    'NEGATIVE_OR_ZERO_EXECUTION_ADJUSTED_LCB', 'MISSING_OR_STALE_REQUIRED_EVIDENCE',
    'REPLAY_OR_PAPER_LANE_MISSING', 'LOCK_OR_SCOPE_CONFLICT',
    'UNCERTAINTY_OR_MODEL_RISK_DOMINATES_EDGE', 'CAPACITY_OR_LIQUIDITY_HARD_VETO',
    'STRONGEST_CLASSICAL_OR_NO_TRADE_DOMINATES', 'INDEPENDENT_REVIEW_NOT_CLOSED',
)
_V35_SERVICE_GROUP_ROLES = ('receipt_refs', 'adjudication_basis.required_evidence_receipt_refs',
    *_V35_SERVICE_CONDITIONS)


def _v35_service_resource_profile(original):
    """The adopted service grant has different units from producer read limits."""
    from dataclasses import fields, replace
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import ResourceBoundsProfileV1
    assert type(original) is ResourceBoundsProfileV1
    selected = replace(original, maximum_input_cardinality=40960, maximum_input_bytes=167772160)
    changed = {'maximum_input_cardinality', 'maximum_input_bytes'}
    for field in fields(original):
        if field.name not in changed:
            assert getattr(selected, field.name) is getattr(original, field.name)
    assert selected.maximum_input_cardinality == 10 * 4096
    assert selected.maximum_input_bytes == 10 * 4096 * 4 * 1024
    return selected


def _v35_service_groups(receipt_refs, adjudication_basis, conditions):
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import model_risk as risk
    assert risk.NO_TRADE_CONDITION_IDS_V1 == _V35_SERVICE_CONDITIONS
    if (type(conditions) is not tuple or len(conditions) != 8
            or any(type(row) is not risk.NoTradeConditionOutcomeV1 for row in conditions)
            or tuple(row.condition_id for row in conditions) != _V35_SERVICE_CONDITIONS):
        raise ValueError('SERVICE_CONDITION_ROSTER')
    if type(adjudication_basis) is not risk.ModelRiskAdjudicationBasisV1:
        raise ValueError('SERVICE_EXPLICIT_BASIS_ROLE')
    return (receipt_refs, adjudication_basis.required_evidence_receipt_refs,
            *(row.evidence_receipt_refs for row in conditions))


def _v35_service_group_observation(groups):
    """Validate the fixed envelope without reshaping or collapsing occurrences."""
    if type(groups) is not tuple or len(groups) != 10:
        raise ValueError('SERVICE_TEN_GROUPS')
    encoded_lengths = {}
    lengths, byte_totals = [], []
    for group in groups:
        if type(group) is not tuple or len(group) > 4096:
            raise ValueError('SERVICE_GROUP_BOUND')
        seen = set()
        byte_total = 0
        for ref in group:
            if type(ref) is not str or not ref or len(ref) > 1024:
                raise ValueError('SERVICE_REFERENCE_SCALARS')
            if ref in seen:
                raise ValueError('SERVICE_DUPLICATE_WITHIN_GROUP')
            seen.add(ref)
            if ref not in encoded_lengths:
                if len(encoded_lengths) >= 4096:
                    raise ValueError('SERVICE_UNION_BOUND')
                size = 0
                for character in ref:
                    point = ord(character)
                    if 0xD800 <= point <= 0xDFFF:
                        raise ValueError('SERVICE_REFERENCE_SURROGATE')
                    size += 1 if point < 128 else 2 if point < 2048 else 3 if point < 65536 else 4
                if size > 4096:
                    raise ValueError('SERVICE_REFERENCE_BYTES')
                encoded_lengths[ref] = size
            # A bounded per-distinct-reference length cache avoids an aggregate
            # encoding buffer; every occurrence still consumes its full bytes.
            byte_total += encoded_lengths[ref]
        lengths.append(len(group))
        byte_totals.append(byte_total)
    return dict(group_roles=_V35_SERVICE_GROUP_ROLES, group_lengths=tuple(lengths),
        group_byte_totals=tuple(byte_totals), distinct_union_count=len(encoded_lengths),
        total_occurrences=sum(lengths), total_bytes=sum(byte_totals))


def _v35_service_check_allowance(observed, profile):
    if observed['total_occurrences'] > profile.maximum_input_cardinality:
        raise ValueError('SERVICE_REFERENCE_COUNT_BOUND')
    if observed['total_bytes'] > profile.maximum_input_bytes:
        raise ValueError('SERVICE_REFERENCE_BYTES_BOUND')


def _v35_service_resource_checks():
    """Cheap grouped policy checks; never a substitute for the real service call."""
    from dataclasses import asdict, replace
    import pytest
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import model_risk as risk
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import ResourceBoundsProfileV1
    assert risk.NO_TRADE_CONDITION_IDS_V1 == _V35_SERVICE_CONDITIONS
    assert len(_V35_SERVICE_GROUP_ROLES) == 10
    assert _V35_SERVICE_GROUP_ROLES[:2] == ('receipt_refs', 'adjudication_basis.required_evidence_receipt_refs')
    old = ResourceBoundsProfileV1('ENG:SERVICE', 8192, 268435456, 1, 1, 1)
    fixed = _v35_service_resource_profile(old)
    assert asdict(old) == dict(profile_id='ENG:SERVICE', maximum_input_cardinality=8192,
        maximum_input_bytes=268435456, maximum_dependency_depth=1, maximum_bootstrap_repetitions=1, maximum_concurrency=1)
    # 4,096 distinct strings, each 1,024 Unicode scalar values and exactly 4,096
    # UTF-8 bytes. The same tuple appears in ten roles without being collapsed.
    maximum = tuple('\U0001f600' * 1022 + chr(0x10000 + i // 1024) + chr(0x10000 + i % 1024)
                    for i in range(4096))
    groups = (maximum,) * 10
    observed = _v35_service_group_observation(groups)
    assert observed['group_lengths'] == (4096,) * 10
    assert observed['group_byte_totals'] == (16777216,) * 10
    assert (observed['distinct_union_count'], observed['total_occurrences'], observed['total_bytes']) == (4096,40960,167772160)
    _v35_service_check_allowance(observed, fixed)
    checks = ['roster-and-roles', 'derived-fixed-profile', 'unrelated-profile-fields', 'exact-full-boundary']
    for name, profile, reason in (
            ('old-producer-unit-denied', old, 'SERVICE_REFERENCE_COUNT_BOUND'),
            ('count-one-under', replace(fixed, maximum_input_cardinality=40959), 'SERVICE_REFERENCE_COUNT_BOUND'),
            ('byte-one-under', replace(fixed, maximum_input_bytes=167772159), 'SERVICE_REFERENCE_BYTES_BOUND')):
        with pytest.raises(ValueError, match=reason):
            _v35_service_check_allowance(observed, profile)
        checks.append(name)
    scalar = _v35_service_group_observation((('a','\u00e9','\u4e00','\U0001f600'),) * 10)
    assert scalar['group_lengths'] == (4,) * 10 and scalar['group_byte_totals'] == (10,) * 10
    assert scalar['distinct_union_count'] == 4 and scalar['total_occurrences'] == 40 and scalar['total_bytes'] == 100
    checks.extend(('utf8-1-2-3-4-byte-scalars', 'between-group-occurrences-charged'))
    empty = ((),) * 10
    negative = (
        ('nine-groups', empty[:-1], 'SERVICE_TEN_GROUPS'),
        ('eleven-groups', (*empty,()), 'SERVICE_TEN_GROUPS'),
        ('group-container', ([],*empty[1:]), 'SERVICE_GROUP_BOUND'),
        ('duplicate-within', (('same','same'),*empty[1:]), 'SERVICE_DUPLICATE_WITHIN_GROUP'),
        ('group-overflow', ((*maximum,'extra'),*empty[1:]), 'SERVICE_GROUP_BOUND'),
        ('union-overflow', (maximum,('extra',),*empty[2:]), 'SERVICE_UNION_BOUND'),
        ('scalar-overflow', (('a'*1025,),*empty[1:]), 'SERVICE_REFERENCE_SCALARS'),
        ('empty-reference', (('',),*empty[1:]), 'SERVICE_REFERENCE_SCALARS'),
        ('nontext', ((1,),*empty[1:]), 'SERVICE_REFERENCE_SCALARS'),
        ('high-surrogate', (('\ud800',),*empty[1:]), 'SERVICE_REFERENCE_SURROGATE'),
        ('low-surrogate', (('\udfff',),*empty[1:]), 'SERVICE_REFERENCE_SURROGATE'),
    )
    for name, values, reason in negative:
        with pytest.raises(ValueError, match=reason):
            _v35_service_group_observation(values)
        checks.append(name)
    print(json.dumps(dict(stage='CHEAP_SERVICE_RESOURCE_POLICY', checks=checks, fixed_profile=asdict(fixed),
        exact_boundary=observed, reference_fits=0, candidate_fits=0, production_guard_qualification=False)),flush=True)


def _v35_full_bank_engineering():
    """Opt-in real engineering chain. Every synthetic grant stays test-owned."""
    import os, time, platform, importlib.metadata, sysconfig, struct
    from pathlib import Path
    from dataclasses import replace
    from contextlib import ExitStack
    flag = os.environ.pop('QTT_V35_FULL_BANK_ENGINEERING', None)
    if flag is None:
        return
    assert flag == '1', 'invalid explicit full-bank selector'
    expected = Path(r'C:\Users\Owner\Downloads\V35_R5_Test_Environments\MODEL_WINDOWS\python\tools\python.exe')
    assert Path(sys.executable).resolve() == expected.resolve() and platform.python_version() == '3.14.7'
    assert struct.calcsize('P') == 8 and sysconfig.get_config_var('Py_GIL_DISABLED') == 0
    environment_root = expected.parents[2]
    for line in (environment_root/'requirements.txt').read_text(encoding='utf-8').splitlines():
        if line.strip():
            name, version = line.split('==')
            assert importlib.metadata.version(name) == version, line
    task_cutoff = int(os.environ.pop('QTT_V35_FULL_BANK_DEADLINE_NS'))
    root = Path(os.environ.pop('QTT_V35_FULL_BANK_WORKSPACE'))
    assert root.is_absolute() and root.is_dir() and not root.is_symlink() and not any(root.iterdir())
    root_identity = (root.stat().st_dev, root.stat().st_ino)
    wall, mono = time.time_ns(), time.monotonic_ns()
    cutoff = min(task_cutoff, mono+7200*10**9)
    assert cutoff > mono
    expiry = (wall+(cutoff-mono))//1000*1000
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import models as m
    original_service_profile = m.ResourceBoundsProfileV1('ENG:SERVICE',8192,268435456,1,1,1)
    service_profile = _v35_service_resource_profile(original_service_profile)
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import input_resolver as inputs
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import persistence as storage
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import serialization as codec
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import receipts as receipt_owner
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.protocols import ProbabilityIssuerReadRequestV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.sqlite_reference import SQLiteReferenceAdapterV1
    scope = m.ProbabilityProducerScopeV1('KALSHI_US_DCM_DIRECT','ENG:MODEL','ENG:MANIFEST','ENG:INPUT-LOCK',
        'ENG:REFERENCE','ENG:FAMILY','ENG:POLICY','ENG:ENVIRONMENT',1)
    parameters = _v35_full_bank_operands()
    assert (len(parameters['fit_clusters']),len(parameters['calibration_clusters']),len(parameters['final_row_ids'])) == (97,100,30)
    source, reference_rows, final_rows, source_refs, source_custody = _v35_full_bank_source(parameters,scope,wall,expiry)
    protocol_names = ('ExperimentProtocolV1','CandidateAndVariantInventoryV1','SearchAndResearchBudgetV1',
        'FalsificationAndNoTradePolicyV1','ProtocolChangeControlV1','MetricsDefinitionRegistryV1','EventTimeAndClockSchemaV1',
        'EconomicAccountingClassRegistryV1','MetricUnitAndBasisRegistryV1','ModelInventoryAndRiskTierV1',
        'IndependentValidationProtocolV1','UseLimitAndRollbackPolicyV1','EvidenceSufficiencyPolicyV1')
    protocols = tuple((n,'ENG:PROTOCOL:'+n) for n in protocol_names)
    assert len({r for _,r in protocols}) == 13
    print(json.dumps({'stage':'CHEAP_TYPED_SOURCE_CHECKED','source_rows':1606,'reference_clusters':197,
        'final_clusters':30,'scope':scope.as_dict(),'operation_cutoff_ns':cutoff,'valid_until_ns':expiry,
        'reference_fits':0,'candidate_fits':0,'canonical_acceptance':False}),flush=True)
    # Stable synthetic issuer identities across differently ordered read cuts.
    def identities(snapshot):
        entries=[]
        for context,grant,decision_text in snapshot.entries:
            identity=json.dumps((grant.role,grant.principal_ref,grant.subject_refs),ensure_ascii=False,separators=(',',':'))
            grant=replace(grant,grant_ref='ENG:GRANT:'+identity,decision_ref='ENG:DECISION:'+identity)
            decision=json.loads(decision_text); decision['row_id']=grant.decision_ref
            entries.append((context,grant,json.dumps(decision,sort_keys=True,separators=(',',':'),ensure_ascii=False)))
        return replace(snapshot,entries=tuple(entries))
    reader = _SyntheticProbabilityIssuerV1(policy_store().snapshot, transform=identities, valid_until_ns=expiry)
    resolver = AgentCapabilityResolverV1(policy_store(),{},probability_issuer_reader=reader)
    roles = ('SOURCE_RIGHTS','ENVIRONMENT','MODEL_BUILD','MODEL_REVIEW','USE_POLICY','CATALOG')
    role_refs = {role:'ENG:PARENT:'+role for role in roles}
    issuer_requests = tuple(ProbabilityIssuerReadRequestV1(role,scope,
        inputs._probability_receipt_subjects_v1(role,scope,'ENG:CATALOG',None),'ENG:ISSUER:'+role) for role in roles)
    producer_request=ProbabilityIssuerReadRequestV1('COMPUTATION',scope,('ENG:RESULT',),'ENG:ISSUER:COMPUTATION')
    with resolver._resolve_probability_issuer_context_v1((*issuer_requests,producer_request),evaluated_ns=time.time_ns()) as issuer_snapshot:
        admissions=tuple(resolver._admit_probability_issuer_v1(r,trusted_snapshot=issuer_snapshot) for r in (*issuer_requests,producer_request))
    trace=dict(context_ref='ENG:CONTEXT',causation_id='ENG:CAUSE',correlation_id='ENG:CORRELATION',traceparent='ENG:TRACE',tracestate='ENG:STATE')
    records={}
    adapter=SQLiteReferenceAdapterV1(root/'receipts.db',busy_timeout_ms=0,max_transaction_attempts=1)
    artifact=None
    def seed(record):
        # Explicit historical synthetic source/review-basis fixture hydration.
        # The positive result and review MUST pass the original issued append.
        assert record.typed_payload.control_kind not in ('PREDICTION_RESULT','PREDICTION_REVIEW')
        connection=adapter._connection
        assert not connection.in_transaction
        connection.execute('BEGIN IMMEDIATE')
        try:
            connection.execute('INSERT INTO receipt_records VALUES(?,?,?,?,?)',
                (record.record_id,record.effective_at.isoformat(),record.recorded_at.isoformat(),record.aggregate_id,codec.deterministic_json(record)))
            connection.execute('COMMIT')
        except BaseException:
            if connection.in_transaction:
                connection.execute('ROLLBACK')
            raise
        records[record.record_id]=record
    def record(ref,kind,body,dependencies=(),at=None):
        at=time.time_ns() if at is None else at
        return receipt_owner._probability_control_record_v1(record_id=ref,
            payload=receipt_owner.ProbabilityProducerControlReceiptV1('PROBABILITY_PRODUCER_CONTROL_V1',kind,scope,
                at,at,at,tuple(dict.fromkeys(dependencies)),expiry,body),**trace)
    def acceptance(role,claims,extra=()):
        i=roles.index(role); parents=tuple(role_refs[p] for p in inputs._PROBABILITY_ACCEPTANCE_PARENTS_V1[role])
        at=time.time_ns()
        seed(record(role_refs[role],'ACCEPTANCE_RECEIPT',dict(role=role,binding_ref='ENG:BINDING',
            subject_refs=issuer_requests[i].subject_refs,depends_on=parents,issuer_ref=issuer_requests[i].issuer_ref,
            observed_ns=at,claims=claims,issuer_admission_refs=admissions[i].authority_dependency_refs),
            (*parents,*admissions[i].authority_dependency_refs,*extra),at))
    try:
        environment=(('python','3.14.7'),('numpy','2.5.2'),('scipy','1.18.1'),('scikit-learn','1.9.0'))
        acceptance('SOURCE_RIGHTS',dict(input_lock_ref=scope.input_lock_ref,reference_cohort_ref=scope.reference_cohort_ref,
            catalog_ref='ENG:CATALOG',input_class='SCOPED_DATA_RIGHTS_AND_SOURCE_SEMANTICS_NOT_DOCUMENTATION_ONLY'),source_refs)
        acceptance('ENVIRONMENT',dict(environment_ref=scope.environment_ref,versions=environment,
            check_class='TARGET_ENVIRONMENT_WITH_BOUNDED_SYNTHETIC_ADAPTER_PARITY'))
        reference_started=time.time_ns()
        reference=_v35_independent_model_reference(parameters)
        reference_completed=time.time_ns()
        from threadpoolctl import threadpool_info
        pools=threadpool_info()
        assert pools and all(p['num_threads']==1 for p in pools)
        selected_site=Path(sysconfig.get_path('purelib')).resolve()
        origins={name:str(Path(sys.modules[name].__file__).resolve()) for name in ('numpy','scipy','sklearn','threadpoolctl')}
        assert all(Path(path).is_relative_to(selected_site) for path in origins.values())
        reference_export_text=json.dumps(reference['model'],sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))
        reference_export_bytes=reference_export_text.encode('utf-8','strict')
        reference_predictions=tuple((key,margin.hex(),probability.hex()) for key,margin,probability in reference['predictions'])
        print(json.dumps({'stage':'INDEPENDENT_REFERENCE_FROZEN','reference_work':reference['reference_work'],
            'reference_predictions':reference_predictions,'warnings':reference['warning_categories'],
            'started_ns':reference_started,'completed_ns':reference_completed,'import_origins':origins,'native_pools':pools}),flush=True)
        model=m._ProbabilityAdmissionModelV1(scope,parameters['feature_names'],'CALIBRATED_LOGISTIC',reference_export_text,
            reference_rows,parameters['calibration_cutoff_ns'],reference_completed,expiry,('f.mean',),(('f.mean','REAL'),),
            1000,None,source_refs)
        catalog=m._ProbabilityAdmissionCatalogV1('ENG:CATALOG',scope,1,197,final_rows[-1].available_ns,final_rows,source_refs)
        limits=m._ProbabilityAdmissionLimitsV1(2048,2048,256,1048576,1048576,67108864)
        budget=m._ProbabilityMaterializationReadBudgetV1(8192,268435456,1048576,8192)
        acceptance('MODEL_BUILD',dict(model_artifact_ref=scope.model_artifact_ref,feature_names=model.feature_names,
            model_kind=model.model_kind,reference_cohort_ref=scope.reference_cohort_ref,reference_cutoff_ns=model.reference_cutoff_ns,
            artifact_available_ns=model.available_ns,build_class='FROZEN_BASE_PIPELINE_AND_SELECTED_CALIBRATOR',
            export_parity_kind='ACTUAL_SUBJECT_PIPELINE_ROUNDTRIP',started_ns=reference_started,completed_ns=reference_completed))
        acceptance('MODEL_REVIEW',dict(model_artifact_ref=scope.model_artifact_ref,review_class='CONCEPTUAL_AND_IMPLEMENTATION_REVIEW',
            scope_of_conclusion='BOUNDED_OFFLINE_DIAGNOSTICS_ONLY',blocker_codes=()))
        acceptance('USE_POLICY',dict(policy_ref=scope.policy_ref,family_ref=scope.family_ref,targets=model.targets,
            target_domains=model.target_domains,replicate_count=1000,precision_protocol_ref=None,
            limits={k:getattr(limits,k) for k in limits.__dataclass_fields__},purpose='OFFLINE_PRODUCER_DIAGNOSTICS',permitted_model_use_modes=()))
        acceptance('CATALOG',dict(catalog_ref=catalog.catalog_ref,owner_epoch=1,after_ordinal=197,
            complete_through_ns=catalog.complete_through_ns,row_count=30,membership_class='IMMUTABLE_ORIGINAL_OBSERVATION_MEMBERSHIP'))
        artifacts={}; descriptors=[]
        for role,obj,ref in (('MODEL',model,scope.model_artifact_ref),('CATALOG',catalog,catalog.catalog_ref),('POLICY',limits,scope.policy_ref)):
            frames=tuple(codec._iter_probability_input_object_frames_v1(role,obj,budget=budget,
                expected_environment=environment if role=='POLICY' else None))
            artifacts[ref]=frames
            descriptors.append(dict(role=role,object_ref=ref,frame_count=len(frames),byte_count=sum(map(len,frames))))
        bound=time.time_ns()
        seed(record('ENG:BINDING','INPUT_BINDING',dict(owner_epoch=1,objects=tuple(descriptors),acceptance_manifest_ref='ENG:ACCEPTANCE'),at=bound))
        seed(record('ENG:ACCEPTANCE','ACCEPTANCE_MANIFEST',dict(binding_ref='ENG:BINDING',receipt_refs=tuple(role_refs.values())),at=bound))
        def custody(path):
            assert path.parent == root and (root.stat().st_dev,root.stat().st_ino) == root_identity and not root.is_symlink()
            assert time.monotonic_ns()<cutoff and time.time_ns()<expiry
        artifact=storage.SQLiteProbabilityArtifactStoreV1(root/'artifact.db',check_custody=custody,
            deadline_monotonic_ns=cutoff,max_artifact_bytes=67108864,max_frames=8192,max_metadata_bytes=262144,
            storage_reserved_bytes=553648128,create=True)
        with resolver._resolve_probability_issuer_context_v1(issuer_requests,evaluated_ns=time.time_ns()) as initial:
            for r in issuer_requests:
                resolver._admit_probability_issuer_v1(r,trusted_snapshot=initial)
        cut=m._ProbabilityRevocationCutV1('ENG:CHECKPOINT',0,None,(),time.time_ns(),expiry)
        fence=inputs._ProbabilityDependencyFenceV1(persistence=adapter,issuer_resolver=resolver,scope=scope,issuer_snapshot=initial,
            source_issuer_ref=issuer_requests[0].issuer_ref,stream_ref='ENG:STREAM',baseline_ref='ENG:BASELINE',baseline_ordinal=0,
            baseline_invalidated_refs=(),cut=cut,max_prepared=32,max_pending=2,max_records=8192,initial_latch=False,
            input_artifacts=artifacts,artifact_writer=artifact,construction_inputs=source)
        producer_limits=storage.ProbabilityProducerReadLimitsV1(8192,268435456,1048576,5000000,cutoff)
        at=time.time_ns()
        read_request=storage.ProbabilityProducerReadRequestV1(scope,'CONSTRUCT_CANDIDATE','ENG:BINDING',None,None,at,at,producer_limits)
        intent=dict(request_id='ENG:CONSTRUCT',receipt_id='ENG:WINDOW',scope=scope.as_dict(),expected_head_ref=None,
            expected_sequence=0,expected_high_watermark=0,selection_cutoff_ns=final_rows[-1].available_ns,result_ref='ENG:RESULT')
        construction=inputs._resolve_probability_construction_inputs_v1(read_request=read_request,intent=intent,
            persistence=adapter,issuer_resolver=resolver,budget=budget)
        import pytest
        from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
        admitted_snapshot=construction[0]['snapshot']
        original_state=construction[0]['state']
        prepare=dict(current_owner_epoch=1,publication_ns=time.time_ns(),limits=limits)
        with pytest.raises(ComputationControlPlaneError,match='CATALOG_CURSOR_MISMATCH'):
            inputs._prepare_probability_window_v1(admitted_snapshot,intent,original_state,**prepare)
        for bad_catalog,reason in (
                (replace(catalog,after_ordinal=0),'PREDICTION_CUSTODY_CURSOR'),
                (replace(catalog,rows=(replace(catalog.rows[0],ordinal=197),*catalog.rows[1:])),'PREDICTION_FINAL_CUSTODY'),
                (replace(catalog,rows=(replace(catalog.rows[0],row_ids=('ENG:WRONG-FINAL',)),*catalog.rows[1:])),'PREDICTION_FINAL_CUSTODY')):
            with pytest.raises(ComputationControlPlaneError,match=reason):
                inputs._prepare_probability_window_v1(replace(admitted_snapshot,catalog=bad_catalog),intent,original_state,
                    prediction_source=source,**prepare)
        assert original_state['high_watermark']==original_state['sequence']==0 and original_state['head_ref'] is None
        entry=fence._registered_v1(construction[0]['snapshot'],kind='MATERIALIZATION',evaluated_ns=time.time_ns())
        deps=tuple(dict.fromkeys((*entry['dependencies'],*admissions[-1].authority_dependency_refs)))
        write=m.ProbabilityPredictionArtifactWriteRequestV1('ENG:ARTIFACT',scope,'ENG:RESULT',deps,expiry,67108864,8192,cutoff)
        read_at=time.time_ns()
        readback=m.ProbabilityPredictionReadRequestV1(scope,'REVIEW_COMMITTED_RESULT','ENG:RESULT',None,read_at,read_at,producer_limits)
        result=inputs._construct_probability_prediction_result_v1(construction=construction,issuer_resolver=resolver,
            write_request=write,producer_request=producer_request,spine_metadata=trace,readback_request=readback)
        attempt=entry['metadata']['prediction_attempt']
        bank=attempt['bank']
        assert attempt['status']=='ARTIFACT_AND_RECEIPT_CONFIRMED_COMMITTED'
        assert attempt['work']==dict(base_fit_calls=1001,calibration_fit_calls=1001,calibration_verification_calls=1001)
        assert codec._bounded_probability_json_v1(bank['original_model'],max_bytes=1048576).encode()==reference_export_bytes
        _v35_full_bank_check_bank(bank,parameters,reference_predictions)
        with artifact.open_prediction_artifact_v1(artifact_ref='ENG:ARTIFACT',scope=scope,max_bytes=67108864,max_frames=8192) as emitted:
            decoded,frames=codec._decode_prediction_artifact_v1(emitted.immutable_bytes,max_bytes=67108864,max_frames=8192)
            assert decoded==bank and frames==emitted.frame_count
        print(json.dumps({'stage':'REAL_CONSTRUCTOR_SEAL_COMMIT_READBACK','candidate_work':attempt['work'],
            'artifact_bytes':emitted.byte_count,'artifact_frames':emitted.frame_count,'sql_accounting':[dict(v) for v in artifact.accounting]}),flush=True)
        _v35_full_bank_review_use(scope,parameters,model,artifact,adapter,resolver,reader,fence,result,
            readback,producer_limits,protocols,role_refs,trace,record,seed,expiry,cutoff,reference_predictions,service_profile)
        assert reference_export_text.encode()==reference_export_bytes
        assert json.dumps(reference['model'],sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()==reference_export_bytes
        print(json.dumps({'stage':'FULL_BANK_ENGINEERING_COMPLETE','reference_work':reference['reference_work'],
            'candidate_work':attempt['work'],'complete_bank':1000,'canonical_acceptance':False,'operational_use':False}),flush=True)
    except BaseException as failure:
        attempt=locals().get('entry',{}).get('metadata',{}).get('prediction_attempt')
        print(json.dumps({'stage':'FULL_BANK_ENGINEERING_FAILED','error_type':type(failure).__name__,
            'error':str(failure),'candidate_attempt':None if attempt is None else
            {'status':attempt['status'],'work':attempt['work']},'root':str(root)}),flush=True)
        raise
    finally:
        original_error=sys.exception()
        cleanup_errors=[]; released=[]
        for label,handle in (('artifact',artifact),('receipts',adapter)):
            if handle is not None:
                try:
                    handle.close(); released.append(label)
                except BaseException as error:
                    cleanup_errors.append(error)
        print(json.dumps({'stage':'OWNED_SQLITE_HANDLE_SETTLEMENT','released':released,
            'cleanup_errors':[repr(e) for e in cleanup_errors],'root':str(root),'evidence_retained':True}),flush=True)
        if cleanup_errors:
            raise BaseExceptionGroup('full-bank body and owned cleanup',
                ([original_error] if original_error is not None else [])+cleanup_errors)


def _v35_full_bank_check_bank(bank, parameters, frozen_predictions):
    """Independent expected predictions and complete native draw observations."""
    import numpy as np
    expected={key:(margin,probability) for key,margin,probability in frozen_predictions}
    assert bank['schema']=='QTT_REQUEST_LOCKED_PREDICTION_BANK_V36' and bank['replicate_count']==1000
    assert bank['state']=='COMPLETE' and len(bank['records'])==len(bank['plans'])==1000
    assert bank['expanded_row_counts']==((776,800),)*1000
    assert bank['actual_fit_calls']==dict(base_fit_calls=1001,calibration_fit_calls=1001)
    assert bank['successful_fit_calls']==2002
    for key,(margin,probability) in expected.items():
        assert tuple(float(v).hex() for v in bank['original_predictions'][key])==(margin,probability)
    lineages=set(); draw_cells=0; checked=0
    for ordinal,(row,plan) in enumerate(zip(bank['records'],bank['plans'],strict=True)):
        assert row['replicate']==ordinal and row['status']=='VALID' and row['reason'] is None
        assert set(row['values'])==set(expected)
        for key,value in row['values'].items():
            assert value==expected[key][1]
            checked+=1
        for code,(indices,n) in enumerate(zip(plan,(97,100),strict=True),1):
            direct=np.random.Generator(np.random.PCG64(np.random.SeedSequence([0,code,ordinal])))
            want=tuple(int(v) for v in direct.integers(0,n,size=n,dtype=np.int64,endpoint=False))
            assert tuple(indices)==want
            draw_cells+=len(indices)
        lineages.add(tuple(tuple(v) for v in plan))
    ranks=((1000+39)//40,(39*1000+39)//40)
    assert ranks==(25,975) and draw_cells==197000 and len(lineages)==1000 and checked==5000
    for key,(_,probability) in expected.items():
        ordered=sorted(float.fromhex(row['values'][key]) for row in bank['records'])
        assert bank['intervals'][key]==tuple(ordered[r-1] for r in ranks)==(float.fromhex(probability),)*2
    print(json.dumps({'stage':'FULL_BANK_INDEPENDENT_CHECKS','draw_cells':draw_cells,'distinct_lineages':len(lineages),
        'replicate_predictions':checked,'interval_ranks':ranks,'all_original_ordinals_retained':True}),flush=True)


def _v35_full_bank_review_use(scope,parameters,model,artifact,adapter,resolver,reader,fence,result,
        original_readback,producer_limits,protocols,role_refs,trace,make_record,seed,expiry,cutoff,reference_predictions,service_profile):
    import time
    from contextlib import contextmanager
    from dataclasses import replace
    from datetime import datetime,timedelta,timezone
    from decimal import Decimal
    import pytest
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import models as m
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import input_resolver as inputs
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import evidence as ev
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import model_risk as risk
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as numerical
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import service as composition
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.protocols import ProbabilityIssuerReadRequestV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError,ReasonCode
    conditions=tuple(risk.NoTradeConditionOutcomeV1(n,i==0,('ENG:NO-TRADE',) if i==0 else (),
        (ReasonCode.ST12F_MODEL_RISK_VETO,) if i==0 else ()) for i,n in enumerate(risk.NO_TRADE_CONDITION_IDS_V1))
    prefix=(scope.model_artifact_ref,result.record_id,'ENG:ARTIFACT',parameters['prediction_input_lock_id'])
    evidence_refs=tuple('ENG:INDEPENDENT-EVIDENCE:'+str(i) for i in range(13))
    basis_refs=('ENG:VALIDATION','ENG:USE-LIMIT','ENG:RISK')
    claims_extra=(
        dict(prediction_basis_kind='INDEPENDENT_PREDICTION_VALIDATION',protocol_coverage=tuple(
            (name,ref,'SUPPORTED_FOR_REVIEW',(eref,)) for (name,ref),eref in zip(protocols,evidence_refs,strict=True)),
            result_commit_observed_ns=time.time_ns()),
        dict(prediction_basis_kind='BOUND_PREDICTION_USE_LIMIT',parent_use_policy_ref=role_refs['USE_POLICY'],
            feature_names=model.feature_names,query_rule='EXACT_COMMITTED_QUERY_LOCK_AND_ACCEPTED_PARENT_CONTEXT',
            permitted_model_use_modes=(),maximum_valid_until_ns=expiry),
        dict(prediction_basis_kind='PREDICTION_MODEL_RISK_BASIS',validation_receipt_refs=(basis_refs[0],),use_limit_ref=basis_refs[1],
            conditions=conditions,scope_of_conclusion='PREDICTION_EVIDENCE_ONLY_NOT_ST12F_ECONOMIC_PROMOTION'))
    subjects=((*prefix,*evidence_refs),prefix,prefix)
    parents=((result.record_id,role_refs['MODEL_BUILD'],role_refs['MODEL_REVIEW'],*evidence_refs),
        (role_refs['USE_POLICY'],result.record_id),(result.record_id,basis_refs[0],basis_refs[1]))
    basis_roles=('MODEL_REVIEW','USE_POLICY','MODEL_REVIEW')
    requests=tuple(ProbabilityIssuerReadRequestV1(role,scope,subject,'ENG:ISSUER:'+role)
        for role,subject in zip(basis_roles,subjects,strict=True))
    with resolver._resolve_probability_issuer_context_v1(requests,evaluated_ns=time.time_ns()) as snapshot:
        admissions=tuple(resolver._admit_probability_issuer_v1(r,trusted_snapshot=snapshot) for r in requests)
    basis_cut=time.time_ns()
    common=dict(protocol_ref=protocols[10][1],effective_cutoff_ns=basis_cut,recorded_cutoff_ns=basis_cut,
        qualification_scope='SYNTHETIC_REFERENCE',purpose='BOUNDED_OFFLINE_DIAGNOSTICS_ONLY',
        conclusion='SUPPORTED_FOR_REVIEW',blocker_codes=())
    for ref,request,admission,parent,extra in zip(basis_refs,requests,admissions,parents,claims_extra,strict=True):
        seed(make_record(ref,'ACCEPTANCE_RECEIPT',dict(role=request.role,binding_ref='ENG:BINDING',subject_refs=request.subject_refs,
            depends_on=parent,issuer_ref=request.issuer_ref,observed_ns=basis_cut,claims={**common,**extra},
            issuer_admission_refs=admission.authority_dependency_refs),(*parent,*admission.authority_dependency_refs),basis_cut))
    basis=m.ProbabilityPredictionReviewBasisReadRequestV1(scope,'ASSEMBLE_INDEPENDENT_PREDICTION_REVIEW',result.record_id,
        (basis_refs[0],),basis_refs[1],basis_refs[2],basis_cut,basis_cut,producer_limits,'ENG:BINDING')
    reviewer=ProbabilityIssuerReadRequestV1('MODEL_REVIEW',scope,(scope.model_artifact_ref,result.record_id),'ENG:ISSUER:MODEL_REVIEW')
    readback=m.ProbabilityPredictionReadRequestV1(scope,'ADMIT_COMMITTED_PREDICTION',result.record_id,'ENG:REVIEW',
        basis_cut,basis_cut,producer_limits)
    review=ev._append_probability_prediction_review_v1(basis_request=basis,review_ref='ENG:REVIEW',reviewer_request=reviewer,
        persistence=adapter,issuer_resolver=resolver,expected_protocol_bindings=protocols,existing_conditions=conditions,
        spine_metadata=trace,readback_request=readback)
    assert review.typed_payload.body['review_state']=='CALIBRATED_FOR_DECLARED_CONTEXT'
    limits=m.ProbabilityPredictionReadLimitsV1(producer_limits,67108864,8192,268435456)
    resolve_call=dict(scope=scope,read_request=readback,expected_model=json.loads(model.export_text),
        prediction_input_lock_id=parameters['prediction_input_lock_id'],feature_names=model.feature_names,
        requests=parameters['requests'],persistence=adapter,issuer_resolver=resolver,expected_protocol_bindings=protocols,
        artifact_reader=artifact,existing_conditions=conditions,limits=limits)
    for invalid,reason in ((protocols[:-1],'PROTOCOL_ROSTER'),(protocols[:-1]+(protocols[0],),'PROTOCOL_ROSTER'),
            (protocols[:-1]+((protocols[-1][0],'ENG:OTHER-VERSION'),),'PROTOCOL_VERSION_MISMATCH')):
        with pytest.raises(ComputationControlPlaneError,match=reason):
            inputs._resolve_committed_prediction_v1(**{**resolve_call,'expected_protocol_bindings':invalid})
    with pytest.raises(ComputationControlPlaneError,match='ARTIFACT_READER_UNAVAILABLE'):
        inputs._resolve_committed_prediction_v1(**{**resolve_call,'artifact_reader':None})
    with pytest.raises(ComputationControlPlaneError,match='PREDICTION_READ_BINDING'):
        inputs._resolve_committed_prediction_v1(**{**resolve_call,'scope':replace(scope,generation=2)})
    with pytest.raises(ComputationControlPlaneError):
        inputs._resolve_committed_prediction_v1(**{**resolve_call,'read_request':replace(readback,effective_cutoff_ns=basis_cut-1)})
    reader.same_domain=True
    try:
        with pytest.raises(ComputationControlPlaneError,match='reviewer controls a producing domain'):
            inputs._resolve_committed_prediction_v1(**resolve_call)
    finally:
        reader.same_domain=False
    prepared=inputs._resolve_committed_prediction_v1(**resolve_call)
    assert prepared.state=='SCORE_RESEARCH_ONLY' and prepared.values is not None
    assert prepared.values==tuple((key,float.fromhex(p),float.fromhex(p),float.fromhex(p)) for key,_,p in reference_predictions)
    original_work=dict(fence._registrations[id(next(v['object'] for v in fence._registrations.values() if v['kind']=='MATERIALIZATION'))]['metadata']['prediction_attempt']['work'])
    use_cut=time.time_ns()//1000*1000
    assert prepared.observed_ns <= use_cut < expiry
    observed=datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(microseconds=use_cut//1000)
    context=m.ComputationExecutionContextV1('ENG:CONTEXT',observed,observed,'ENG:EPOCH','ENG:INPUT-VERSION',
        timedelta(seconds=7200),m.ComputationScopeV1('ENG:MARKET','ENG:VENUE','ENG:EVENT','ENG:CONTRACT','ENG:NO-EFFECT','ENG:SNAPSHOT'),
        '3.4','3.4',tuple(m.ImplementationVersionPinV1(mid,numerical.IMPLEMENTATION_REGISTRY[mid].contract.implementation_id)
            for mid in ('MATH-02','MATH-06')))
    request=risk.ProbabilityNativeUseRequestV1(scope,prepared,context,prepared.request_keys[0],
        ('FIVAB::MATH-02::calibrated_model_probability','FIVAB::MATH-02::calibration_state'),None,'ENG:ACCEPTED-USE',basis_cut,basis_cut)
    use_dependencies=tuple(dict.fromkeys((*prepared.dependency_refs,scope.policy_ref,request.selected_use_decision_ref,
        'ENG:USE-POLICY','ENG:USE-TRANSITION')))
    state={'available':True,'reads':0,'checks':0,'exits':0,'denials':0}; admitted=[]
    @contextmanager
    def read_use(original,*,evaluated_ns,deadline_ns):
        assert original is request and state['available'] and not reader.active
        state['reads']+=1
        value=risk.ProbabilityNativeUseAdmissionV1(original,original.selected_use_decision_ref,'ENG:USE-POLICY','ENG:USE-TRANSITION',
            basis_cut,expiry,use_dependencies,fence.policy.policy_version,fence.policy_epoch,fence.policy.registry_version,
            fence.process_ref,fence.generation,fence.cut.checkpoint_ref)
        admitted.append(value)
        try:
            yield value
        finally:
            state['exits']+=1
    def check_use(original,*,evaluated_ns):
        from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import OwnerAdapterError
        assert any(original is v for v in admitted)
        state['checks']+=1
        if not state['available']:
            state['denials']+=1
            raise OwnerAdapterError(ReasonCode.OWNER_DATA_MISSING, 'SYNTHETIC_NATIVE_USE_DECISION_REMOVED')
    reader.read_probability_native_use=read_use
    reader.check_probability_native_use=check_use
    controls=tuple(risk.ModelRiskControlEvidenceV1(identity,risk.ModelRiskControlStateV1.BLOCKED_WITH_TYPED_REASON,(),
        (ReasonCode.ST12F_EVIDENCE_INCOMPLETE,),('ENG:UNQUALIFIED',),False) for identity in risk.MODEL_RISK_CONTROL_IDS_V1)
    comparison=risk.PermanentNoTradeEvidenceComparisonV1('ENG:COMPARISON',scope.input_lock_ref,
        Decimal('0.1'),Decimal('1'),Decimal('0.8'),Decimal('0'),'CANDIDATE')
    basis_risk=risk.ModelRiskAdjudicationBasisV1('MATH-02',observed,
        datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(microseconds=expiry//1000),('ENG:REQUIRED',),None,None,
        Decimal('0.05'),Decimal('0.05'),False,False,('ENG:CAPACITY',),'READY_FOR_INDEPENDENT_REVIEW','ENG:PENDING-REVIEW')
    original_resource=m.ResourceBoundsProfileV1('ENG:SERVICE',producer_limits.max_records,producer_limits.max_total_bytes,1,1,1)
    assert service_profile == _v35_service_resource_profile(original_resource)
    resource=service_profile
    compose_call=dict(owner_registry=inputs.CanonicalOwnerPacketRegistryV1(),
        agent_capability_resolver=resolver,native_use_request=request,clock_facts=(use_cut,)*5,prediction_read_limits=limits,
        existing_conditions=conditions,assessment_id='ENG:ASSESSMENT',input_lock_id=scope.input_lock_ref,controls=controls,
        comparison=comparison,adjudication_basis=basis_risk,limitations=('SYNTHETIC_FULL_BANK_ENGINEERING_ONLY',),
        receipt_refs=('ENG:RISK',),evaluated_ns=time.time_ns(),deadline_ns=cutoff,resource_bounds_profile=resource)
    from unittest.mock import patch
    from dataclasses import asdict
    actual_builder=inputs._build_probability_owner_registry_v1
    builder_results=[]; service_observations=[]; builder_calls=[0]
    def observe_original_builder(**kwargs):
        builder_calls[0]+=1
        assert builder_calls[0]==1 and not builder_results
        assert set(kwargs)=={'base_registry','request','capability_resolver','clock_facts','existing_conditions','limits','evaluated_ns','deadline_ns'}
        assert kwargs['base_registry'] is compose_call['owner_registry'] and kwargs['request'] is request
        assert kwargs['capability_resolver'] is resolver and kwargs['existing_conditions'] is conditions
        assert kwargs['limits'] is limits and kwargs['clock_facts'] is compose_call['clock_facts']
        assert kwargs['evaluated_ns']==compose_call['evaluated_ns'] and kwargs['deadline_ns']==cutoff
        original=actual_builder(**kwargs)
        builder_results.append(original)
        registry, built_conditions=original
        groups=_v35_service_groups(compose_call['receipt_refs'],basis_risk,built_conditions)
        observed=_v35_service_group_observation(groups)
        service_observations.append(observed)
        print(json.dumps(dict(stage='REAL_SERVICE_RESOURCE_OBSERVATION',**observed,
            fixed_profile=asdict(resource),builder_calls=builder_calls[0],returned_object_preserved=True)),flush=True)
        _v35_service_check_allowance(observed,resource)
        return original
    with patch.object(inputs,'_build_probability_owner_registry_v1',observe_original_builder):
        service,assessment=composition._compose_probability_native_service_v1(**compose_call)
    assert inputs._build_probability_owner_registry_v1 is actual_builder and len(builder_results)==builder_calls[0]==1
    assert service.owner_registry is builder_results[0][0] and service.resource_bounds_profile is service_profile
    assert assessment.terminal_state=='NO_TRADE' and assessment.permanent_no_trade_wins and not assessment.automatic_promotion_allowed
    assert service.mode_snapshot_input_resolver is service.mode_snapshot_owner_projection_adapter is service.mode_snapshot_projection_bundle is None
    assert len(service.owner_registry.packets)==2 and state['reads']==state['exits']==1 and state['checks']>0
    checks_before_removal=state['checks']
    assert state['denials']==0
    state['available']=False
    with pytest.raises(ComputationControlPlaneError,match='probability input authority is no longer current') as missing_use:
        service.owner_registry._check_probability_packet_refs_v1(tuple(p.packet_id for p in service.owner_registry.packets),context=context)
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import OwnerAdapterError
    assert missing_use.value.reason_code is ReasonCode.INPUT_PACKET_MISMATCH
    assert type(missing_use.value.__cause__) is OwnerAdapterError
    assert missing_use.value.__cause__.reason_code is ReasonCode.OWNER_DATA_MISSING
    assert str(missing_use.value.__cause__).endswith('SYNTHETIC_NATIVE_USE_DECISION_REMOVED')
    assert state['checks']==checks_before_removal+1 and state['denials']==1 and state['reads']==state['exits']==1
    assert service.resource_bounds_profile is service_profile and len(builder_results)==1 and len(service_observations)==1
    actual_work=dict(fence._registrations[id(next(v['object'] for v in fence._registrations.values() if v['kind']=='MATERIALIZATION'))]['metadata']['prediction_attempt']['work'])
    assert actual_work==original_work==dict(base_fit_calls=1001,calibration_fit_calls=1001,calibration_verification_calls=1001)
    assert prepared.model_use_authorized is prepared.source_authentication is prepared.native_packet_created is False
    print(json.dumps({'stage':'REAL_REVIEW_PREPARED_SERVICE_CONSUMPTION','prepared_queries':len(prepared.values),
        'packet_count':2,'use_port_counts':state,'missing_use_rejected':True,'missing_use_error':str(missing_use.value),
        'missing_use_cause':str(missing_use.value.__cause__),'terminal_state':assessment.terminal_state,
        'mode_active':False,'canonical_acceptance':False,'service_resource_observation':service_observations[0]}),flush=True)
