#!/usr/bin/env python3
"""Independent exact operation-roster and no-runtime validation."""

from __future__ import annotations

import ast
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
import sys
from types import MappingProxyType

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.cohort_compiler import (
    ReplayPaperCohortCompilerV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
    ComputationContextKeyV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    PersistenceContractError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import (
    BuiltEvidenceBundleOutcomeV1,
    ComputationEvidenceServiceV1,
    EvidenceBundleTerminalStateV1,
    RegisteredLaneResultOutcomeV1,
    ReplayResultContractV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_lock import (
    CanonicalReplayPaperInputSnapshotV1,
    ST12F_TEMPLATE_IDS_V1,
    canonical_st12f_parameter_value_refs_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    CompileReplayPaperCohortRequestV1,
    RegisterReplayPaperResultRequestV1,
    TypedValueKindV1,
    TypedValueRecordV1,
    TypedValueV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.persistence import (
    InMemoryPersistenceAdapterV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
    deterministic_json,
)

PACKAGE = (
    REPO_ROOT
    / "src"
    / "qtt"
    / "stage1_prediction_markets"
    / "qku_computation_control_plane"
)
FORBIDDEN_IMPORT_ROOTS = {
    "asyncio",
    "multiprocessing",
    "requests",
    "socket",
    "sqlite3",
    "subprocess",
    "threading",
}
FORBIDDEN_CALL_NAMES = {
    "connect",
    "create_connection",
    "listen",
    "Popen",
    "run",
    "serve_forever",
    "start",
}

OWNER_BUNDLE_FIELDS_V1 = (
    "evidence_id",
    "schema_version",
    "contract_version",
    "evidence_bundle_version",
    "component_or_template_ref",
    "input_lock_id",
    "actual_executed_component_versions",
    "actual_executed_stack_versions",
    "replay_result_ref",
    "paper_result_ref",
    "divergence_assessment_ref",
    "lane_execution_receipt_refs",
    "calibration_and_probability_quality",
    "transaction_cost_decomposition",
    "fill_and_queue_quality",
    "latency_and_staleness",
    "capacity_and_crowding",
    "portfolio_marginal_contribution",
    "false_discovery_and_overfit_controls",
    "regime_and_scenario_outcomes",
    "uncertainty_and_model_risk_reserves",
    "agent_and_model_disagreement",
    "no_trade_comparison",
    "independent_review_state",
    "failure_and_negative_evidence_states",
    "source_and_provenance_refs",
    "d_evidence_reference_projection",
    "g_handoff_projection",
    "terminal_state",
    "blocker_codes",
)

OWNER_LIFECYCLE_TRANSITIONS_V1 = (
    (
        "INCOMPLETE_MISSING_REPLAY",
        "READY_FOR_INDEPENDENT_REVIEW",
        "BOTH_LANES_PRESENT_SAME_LOCK_ALL_REQUIRED_CONTROLS_COMPUTED",
    ),
    (
        "INCOMPLETE_MISSING_PAPER",
        "READY_FOR_INDEPENDENT_REVIEW",
        "BOTH_LANES_PRESENT_SAME_LOCK_ALL_REQUIRED_CONTROLS_COMPUTED",
    ),
    (
        "READY_FOR_INDEPENDENT_REVIEW",
        "CLOSED_INDEPENDENTLY_VALIDATED",
        "SEPARATE_REVIEW_RECEIPT_PASS_AND_ZERO_HARD_VETOES",
    ),
    (
        "READY_FOR_INDEPENDENT_REVIEW",
        "INDEPENDENT_REVIEW_REJECTED",
        "SEPARATE_REVIEW_RECEIPT_REJECT",
    ),
    (
        "CLOSED_INDEPENDENTLY_VALIDATED",
        "STALE",
        "TTL_SOURCE_EPOCH_PARAMETER_IMPLEMENTATION_OR_CONTEXT_CHANGE",
    ),
    (
        "CLOSED_INDEPENDENTLY_VALIDATED",
        "SUPERSEDED",
        "NEWER_VALIDATED_BUNDLE_VERSION_SAME_IDENTITY",
    ),
)
OWNER_CONCURRENCY_CASE_IDS_V1 = (
    "OUTCOME-01",
    "OUTCOME-02",
    "OP14-IDENTICAL",
    "OP14-COMPETING",
    "OP15-ROOT-IDENTICAL",
    "OP15-ROOT-COMPETING",
    "OP15-SIBLING",
    "BITEMPORAL",
    "REVIEW",
    "EVIDENCE-48",
    "METRICS-38",
    "TRUTH",
    "STALE-5",
    "SUPERSEDED",
    "CACHE",
)


@dataclass(frozen=True, slots=True)
class RuntimeTopologyExceptionV1:
    """One exact non-production standard-library runtime exception."""

    file_name: str
    allowed_import: str
    allowed_qualified_call: str
    adapter_class_name: str
    production_marker_name: str


RUNTIME_TOPOLOGY_EXCEPTIONS = MappingProxyType(
    {
        "sqlite_reference.py": RuntimeTopologyExceptionV1(
            file_name="sqlite_reference.py",
            allowed_import="sqlite3",
            allowed_qualified_call="sqlite3.connect",
            adapter_class_name="SQLiteReferenceAdapterV1",
            production_marker_name="is_production_adapter",
        )
    }
)
COMMON_REQUEST_FIELDS = (
    ("request_id", "str"),
    ("operation_name", "CertifiedOperationNameV1"),
    ("requested_at", "TimezoneAwareDateTimeV1"),
    ("principal_id", "str"),
    ("capability_bundle_id", "str"),
    ("context", "ComputationContextKeyV1"),
    ("idempotency_key", "EconomicIdempotencyKeyV1"),
    ("traceparent", "W3CTraceparentV1"),
    ("tracestate", "W3CTracestateV1"),
)
COMMON_RESPONSE_FIELDS = (
    ("response_id", "str"),
    ("operation_name", "CertifiedOperationNameV1"),
    ("request_id", "str"),
    ("completed_at", "TimezoneAwareDateTimeV1"),
    ("status", "OperationStatusV1"),
    ("context", "ComputationContextKeyV1"),
    ("warnings", "tuple[str,...]"),
    ("blocker_codes", "tuple[OperationBlockerCodeV1,...]"),
    ("receipt_refs", "tuple[str,...]"),
    ("traceparent", "W3CTraceparentV1"),
    ("tracestate", "W3CTracestateV1"),
)
EXPECTED_ROWS = (
    (
        "ST10-OP::01",
        "resolve_identity",
        "UnifiedCanonicalIdentityPlaneV1",
        "ResolveIdentityRequestV1",
        "ResolveIdentityResponseV1",
        (("identity_query", "TypedValueRecordV1"),),
        ("identity_resolution", "IdentityResolutionV1"),
        None,
    ),
    (
        "ST10-OP::02",
        "resolve_contextual_computability",
        "QKUComputationControlPlaneV1",
        "ResolveContextualComputabilityRequestV1",
        "ResolveContextualComputabilityResponseV1",
        (
            ("component_id", "str"),
            ("required_computability_classes", "tuple[ComputabilityClassV1,...]"),
        ),
        ("computability", "ContextualComputabilityResolutionV1"),
        "ContextualComputabilityResolverV1.resolve",
    ),
    (
        "ST10-OP::03",
        "resolve_applicable_stack",
        "QKUComputationControlPlaneV1",
        "ResolveApplicableStackRequestV1",
        "ResolveApplicableStackResponseV1",
        (
            ("trade_plan_candidate_id", "str"),
            ("required_launch_roles", "tuple[str,...]"),
        ),
        ("stack_resolution", "StackResolutionV1"),
        None,
    ),
    (
        "ST10-OP::04",
        "resolve_required_inputs",
        "QKUComputationControlPlaneV1",
        "ResolveRequiredInputsRequestV1",
        "ResolveRequiredInputsResponseV1",
        (
            ("component_ids", "tuple[str,...]"),
            ("include_optional", "bool"),
        ),
        ("input_resolution", "InputResolutionV1"),
        None,
    ),
    (
        "ST10-OP::05",
        "compute_component",
        "QKUComputationControlPlaneV1",
        "ComputeComponentRequestV1",
        "ComputeComponentResponseV1",
        (
            ("component_id", "str"),
            ("input_values", "TypedValueRecordV1"),
            ("expected_output_schema_ref", "str"),
        ),
        ("component_result", "ComponentResultV1"),
        None,
    ),
    (
        "ST10-OP::06",
        "compute_stack",
        "QKUComputationControlPlaneV1",
        "ComputeStackRequestV1",
        "ComputeStackResponseV1",
        (
            ("stack_id", "str"),
            ("component_ids", "tuple[str,...]"),
            ("input_values", "TypedValueRecordV1"),
        ),
        ("stack_result", "StackResultV1"),
        None,
    ),
    (
        "ST10-OP::07",
        "compare_with_no_trade",
        "QKUComputationControlPlaneV1",
        "CompareWithNoTradeRequestV1",
        "CompareWithNoTradeResponseV1",
        (
            ("trade_plan_candidate_id", "str"),
            ("no_trade_candidate_id", "str"),
            ("comparison_basis", "str"),
        ),
        ("comparison", "NoTradeComparisonV1"),
        None,
    ),
    (
        "ST10-OP::08",
        "evaluate_trade_plan",
        "QKUComputationControlPlaneV1",
        "EvaluateTradePlanRequestV1",
        "EvaluateTradePlanResponseV1",
        (
            ("trade_plan_candidate_id", "str"),
            ("stack_id", "str"),
            ("accounting_tca_view_ref", "str"),
            ("risk_cash_state_ref", "str"),
            ("no_trade_candidate_id", "str"),
        ),
        ("evaluation", "TradePlanEvaluationV1"),
        None,
    ),
    (
        "ST10-OP::09",
        "get_snapshot_view",
        "QKUComputationControlPlaneV1",
        "GetSnapshotViewRequestV1",
        "GetSnapshotViewResponseV1",
        (
            ("snapshot_id", "str"),
            ("view_class", "str"),
            ("include_value_lineage", "bool"),
        ),
        ("snapshot_view", "SnapshotViewV1"),
        None,
    ),
    (
        "ST10-OP::10",
        "explain_resolution",
        "QKUComputationControlPlaneV1",
        "ExplainResolutionRequestV1",
        "ExplainResolutionResponseV1",
        (
            ("resolution_receipt_id", "str"),
            ("explanation_scope", "str"),
            ("max_evidence_items", "int"),
        ),
        ("explanation", "ResolutionExplanationV1"),
        None,
    ),
    (
        "ST10-OP::11",
        "submit_candidate_proposal",
        "QKUComputationControlPlaneV1",
        "SubmitCandidateProposalRequestV1",
        "SubmitCandidateProposalResponseV1",
        (
            ("candidate_kind", "str"),
            ("proposed_specification", "TypedValueRecordV1"),
            ("source_candidate_refs", "tuple[str,...]"),
            ("requested_owner_review", "bool"),
        ),
        ("proposal", "CandidateProposalV1"),
        None,
    ),
    (
        "ST10-OP::12",
        "request_materialization_work_order",
        "QKUComputationControlPlaneV1",
        "RequestMaterializationWorkOrderRequestV1",
        "RequestMaterializationWorkOrderResponseV1",
        (
            ("missing_contract_ids", "tuple[str,...]"),
            ("reason_codes", "tuple[OperationBlockerCodeV1,...]"),
            ("priority", "str"),
            ("requested_owner", "str"),
        ),
        ("work_order", "MaterializationWorkOrderV1"),
        None,
    ),
    (
        "ST10-OP::13",
        "compile_replay_paper_cohort",
        "ReplayPaperCohortCompilerV1",
        "CompileReplayPaperCohortRequestV1",
        "CompileReplayPaperCohortResponseV1",
        (
            ("template_ids", "tuple[str,...]"),
            ("requested_lanes", "tuple[str,...]"),
            ("input_lock_id", "str"),
            ("campaign_execution_requested", "bool"),
        ),
        ("cohort_compilation", "ReplayPaperCohortCompilationV1"),
        None,
    ),
    (
        "ST10-OP::14",
        "register_replay_paper_result",
        "ComputationEvidenceServiceV1",
        "RegisterReplayPaperResultRequestV1",
        "RegisterReplayPaperResultResponseV1",
        (
            ("cohort_instance_id", "str"),
            ("lane", "str"),
            ("input_lock_id", "str"),
            ("result_packet", "TypedValueRecordV1"),
        ),
        ("registration", "ReplayPaperResultRegistrationV1"),
        None,
    ),
    (
        "ST10-OP::15",
        "build_evidence_bundle",
        "ComputationEvidenceServiceV1",
        "BuildEvidenceBundleRequestV1",
        "BuildEvidenceBundleResponseV1",
        (
            ("component_id", "str"),
            ("input_lock_id", "str"),
            ("evidence_record_refs", "tuple[str,...]"),
            ("required_lanes", "tuple[str,...]"),
        ),
        ("evidence_bundle", "EvidenceBundleResultV1"),
        None,
    ),
)
SUCCESS_MARKER = "QKU_OPERATIONS_INDEPENDENTLY_VALIDATED"


_ST12F_NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)
_ST12F_TRACEPARENT = (
    "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
)


class _CommitFailingAdapterV1(InMemoryPersistenceAdapterV1):
    def __init__(self) -> None:
        super().__init__()
        self.fail_next_commit = False

    def _commit(self, transaction: object) -> None:
        if self.fail_next_commit:
            self.fail_next_commit = False
            raise PersistenceContractError(
                ReasonCode.PERSISTENCE_UNAVAILABLE,
                "independent injected commit failure",
            )
        super()._commit(transaction)  # type: ignore[arg-type]


def _st12f_snapshot() -> CanonicalReplayPaperInputSnapshotV1:
    versions = {
        identity: f"VERSION::{identity}" for identity in ST12F_TEMPLATE_IDS_V1
    }
    return CanonicalReplayPaperInputSnapshotV1(
        decision_time=_ST12F_NOW,
        point_in_time_cutoff=_ST12F_NOW - timedelta(minutes=1),
        market_scope=("MARKET::INDEPENDENT",),
        venue_scope=("VENUE::INDEPENDENT",),
        instrument_scope=("INSTRUMENT::INDEPENDENT",),
        formula_specification_versions=versions,
        implementation_versions=versions,
        parameter_policy_version="ST12F_PARAMETER_POLICY_V1_4",
        parameter_value_refs=canonical_st12f_parameter_value_refs_v1(),
        source_epochs={"SOURCE::1": "EPOCH::1"},
        data_semantics_version="DATA::V1",
        venue_semantics_version="VENUE::V1",
        accounting_definition={"basis": "NET"},
        fee_assumptions={"policy_ref": "FEE::1"},
        spread_assumptions={"policy_ref": "SPREAD::1"},
        slippage_assumptions={"policy_ref": "SLIPPAGE::1"},
        fill_and_queue_assumptions={"policy_ref": "FILL::1"},
        latency_and_staleness_assumptions={"policy_ref": "LATENCY::1"},
        capacity_and_crowding_assumptions={"policy_ref": "CAPACITY::1"},
        portfolio_and_cash_context={
            "permanent_no_trade_baseline_ref": "NO-TRADE::1"
        },
        random_seed_policy={"seed": 17},
        resampling_policy={"trial_family_id": "TRIAL::1"},
        scenario_set_id="SCENARIO::1",
        causation_id="CAUSE::ORIGINAL",
        correlation_id="CORRELATION::ORIGINAL",
        created_by="OWNER::INDEPENDENT",
        created_at=_ST12F_NOW,
    )


def _st12f_runtime(
    adapter: InMemoryPersistenceAdapterV1,
    *,
    identity: str,
) -> tuple[
    ReplayPaperCohortCompilerV1,
    ComputationEvidenceServiceV1,
    object,
    ComputationContextKeyV1,
]:
    snapshot = _st12f_snapshot()
    compiler = ReplayPaperCohortCompilerV1(snapshot, adapter)
    context = ComputationContextKeyV1(
        context_id="MATH-01",
        as_of=_ST12F_NOW,
        observed_at=_ST12F_NOW,
        source_epoch_id="SOURCE::1=EPOCH::1",
        input_version="INPUT::INDEPENDENT",
        maximum_age=timedelta(hours=1),
    )
    request = CompileReplayPaperCohortRequestV1(
        request_id=f"REQUEST::OP13::{identity}",
        operation_name="compile_replay_paper_cohort",
        requested_at=_ST12F_NOW,
        principal_id="PRINCIPAL::INDEPENDENT",
        capability_bundle_id="CAPABILITY::INDEPENDENT",
        context=context,
        idempotency_key=identity,
        traceparent=_ST12F_TRACEPARENT,
        tracestate="qtt=independent",
        template_ids=ST12F_TEMPLATE_IDS_V1,
        requested_lanes=("REPLAY", "PAPER"),
        input_lock_id=f"ST12F-LOCK::{identity}",
        campaign_execution_requested=False,
    )
    compilation = compiler.compile(request)
    return compiler, ComputationEvidenceServiceV1(compiler, adapter), compilation, context


def _st12f_packet(
    compilation: object,
    snapshot: CanonicalReplayPaperInputSnapshotV1,
    *,
    result_id: str,
    run_reference: str,
    fixture: bool,
) -> ReplayResultContractV1:
    cutoff = snapshot.point_in_time_cutoff
    return ReplayResultContractV1(
        result_id=result_id,
        schema_version="QTT_ST12F_LANE_RESULT_CONTRACTS_V1_4",
        contract_version="1.4",
        cohort_template_id="MATH-01",
        expected_result_contract_id="ST12F-REPLAY-CONTRACT::MATH-01",
        input_lock_id=str(getattr(compilation, "input_lock_id")),
        run_reference=run_reference,
        producer_identity="PRODUCER::REPLAY",
        implementation_versions=snapshot.implementation_versions,
        source_epochs=snapshot.source_epochs,
        point_in_time_cutoff=cutoff,
        accounting_definition=deterministic_json(snapshot.accounting_definition),
        scenario_policy={"scenario": snapshot.scenario_set_id},
        resampling_policy=snapshot.resampling_policy,
        economic_metrics={"utility": "1"},
        tca_metrics={"cost": "0.1"},
        fill_metrics={"fill": "1"},
        latency_metrics={"latency": "1ms"},
        capacity_metrics={"capacity": "1"},
        failure_states=(),
        limitations=("LIMITATION::DECLARED",),
        started_at=cutoff,
        completed_at=cutoff + timedelta(seconds=1),
        available_at=cutoff + timedelta(seconds=2),
        closed_at=cutoff + timedelta(seconds=3),
        fixture_only_not_evidence=fixture,
    )


def _st12f_register_request(
    compilation: object,
    context: ComputationContextKeyV1,
    *,
    identity: str,
) -> RegisterReplayPaperResultRequestV1:
    placeholder = TypedValueRecordV1(
        (
            TypedValueV1(
                "placeholder",
                TypedValueKindV1.TEXT,
                "preexisting-packet-supplied-separately",
                "unitless",
                "independent-validator",
            ),
        )
    )
    return RegisterReplayPaperResultRequestV1(
        request_id=f"REQUEST::OP14::{identity}",
        operation_name="register_replay_paper_result",
        requested_at=_ST12F_NOW + timedelta(seconds=1),
        principal_id="PRINCIPAL::INDEPENDENT",
        capability_bundle_id="CAPABILITY::INDEPENDENT",
        context=context,
        idempotency_key=f"IDEMPOTENCY::OP14::{identity}",
        traceparent=_ST12F_TRACEPARENT,
        tracestate="qtt=independent",
        cohort_instance_id=str(getattr(compilation, "compilation_id")),
        lane="REPLAY",
        input_lock_id=str(getattr(compilation, "input_lock_id")),
        result_packet=placeholder,
    )


def _table_counts(adapter: InMemoryPersistenceAdapterV1) -> tuple[tuple[str, int], ...]:
    return tuple(sorted((name, len(rows)) for name, rows in adapter._tables.items()))


def _st12f_executable_operation_checks() -> tuple[bool, ...]:
    failing_adapter = _CommitFailingAdapterV1()
    compiler, failing_service, compilation, context = _st12f_runtime(
        failing_adapter, identity="ROLLBACK"
    )
    snapshot = compiler.canonical_snapshot
    packet = _st12f_packet(
        compilation,
        snapshot,
        result_id="RESULT::ROLLBACK",
        run_reference="RUN::ROLLBACK",
        fixture=False,
    )
    counts_before_failure = _table_counts(failing_adapter)
    indexes_before_failure = tuple(
        len(index) for index in failing_service.immutable_indexes.values()
    )
    failing_adapter.fail_next_commit = True
    rollback_rejected = False
    try:
        failing_service.register_result(
            _st12f_register_request(compilation, context, identity="ROLLBACK"),
            packet,
        )
    except PersistenceContractError as exc:
        rollback_rejected = exc.reason_code is ReasonCode.PERSISTENCE_UNAVAILABLE

    adapter = InMemoryPersistenceAdapterV1()
    compiler, service, compilation, context = _st12f_runtime(
        adapter, identity="DURABLE"
    )
    snapshot = compiler.canonical_snapshot
    counts_before_fixture = _table_counts(adapter)
    fixture = _st12f_packet(
        compilation,
        snapshot,
        result_id="RESULT::FIXTURE",
        run_reference="RUN::FIXTURE",
        fixture=True,
    )
    fixture_outcome = service.register_result(
        _st12f_register_request(compilation, context, identity="FIXTURE"),
        fixture,
    )
    counts_after_fixture = _table_counts(adapter)
    fixture_indexes = tuple(len(index) for index in service.immutable_indexes.values())
    committed_packet = replace(
        fixture,
        result_id="RESULT::COMMITTED",
        run_reference="RUN::COMMITTED",
        fixture_only_not_evidence=False,
    )
    committed_outcome = service.register_result(
        _st12f_register_request(compilation, context, identity="COMMITTED"),
        committed_packet,
    )
    receipt_refs = committed_outcome.receipt_refs
    restarted = ComputationEvidenceServiceV1(compiler, adapter)
    counts_before_replay = _table_counts(adapter)
    replayed_outcome = restarted.register_result(
        _st12f_register_request(compilation, context, identity="REPLAYED"),
        committed_packet,
    )
    conflict_rejected = False
    try:
        restarted.register_result(
            _st12f_register_request(compilation, context, identity="CONFLICT"),
            replace(
                committed_packet,
                result_id="RESULT::CONFLICT",
                run_reference="RUN::CONFLICT",
            ),
        )
    except ContractValidationError as exc:
        conflict_rejected = exc.reason_code is ReasonCode.ST12F_RESULT_SLOT_CONFLICT

    return (
        rollback_rejected,
        _table_counts(failing_adapter) == counts_before_failure,
        tuple(len(index) for index in failing_service.immutable_indexes.values())
        == indexes_before_failure,
        type(fixture_outcome) is RegisteredLaneResultOutcomeV1,
        fixture_outcome.registered_result is fixture,
        fixture_outcome.receipt_refs == (),
        counts_after_fixture == counts_before_fixture,
        fixture_indexes == (0, 0, 0, 0, 0, 0, 0, 0),
        type(committed_outcome) is RegisteredLaneResultOutcomeV1,
        committed_outcome.registered_result == committed_packet
        and committed_outcome.registered_result is not committed_packet,
        len(service.immutable_indexes["lane_results"]) == 1,
        len(service.immutable_indexes["slot_results"]) == 1,
        len(restarted.immutable_indexes["lane_results"]) == 1,
        len(restarted.immutable_indexes["slot_results"]) == 1,
        type(replayed_outcome) is RegisteredLaneResultOutcomeV1,
        replayed_outcome == committed_outcome,
        _table_counts(adapter) == counts_before_replay,
        conflict_rejected,
        len(receipt_refs) == 1
        and receipt_refs[0]
        == "ST12F-RECEIPT::RESULT::COMMITTED::REPLAY_REGISTRATION",
        adapter.get_record(receipt_refs[0]) is not None,
        not hasattr(service, "last_committed_receipt_refs")
        and not hasattr(restarted, "last_committed_receipt_refs"),
    )


def _assignment(tree: ast.Module, name: str) -> ast.expr | None:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            return node.value
    return None


def _class_fields(tree: ast.Module, name: str) -> tuple[str, ...]:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return tuple(
                statement.target.id
                for statement in node.body
                if isinstance(statement, ast.AnnAssign)
                and isinstance(statement.target, ast.Name)
                and statement.target.id != "EXPECTED_OPERATION_NAME"
            )
    return ()


def _class_is_frozen_slots_dataclass(tree: ast.Module, name: str) -> bool:
    class_node = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == name
        ),
        None,
    )
    if class_node is None:
        return False
    return any(
        isinstance(decorator, ast.Call)
        and isinstance(decorator.func, ast.Name)
        and decorator.func.id == "dataclass"
        and {
            keyword.arg: keyword.value.value
            for keyword in decorator.keywords
            if keyword.arg in {"frozen", "slots"}
            and isinstance(keyword.value, ast.Constant)
        }
        == {"frozen": True, "slots": True}
        for decorator in class_node.decorator_list
    )


def _method_return_name(
    tree: ast.Module,
    class_name: str,
    method_name: str,
) -> str | None:
    class_node = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == class_name
        ),
        None,
    )
    if class_node is None:
        return None
    method = next(
        (
            node
            for node in class_node.body
            if isinstance(node, ast.FunctionDef) and node.name == method_name
        ),
        None,
    )
    return (
        method.returns.id
        if method is not None and isinstance(method.returns, ast.Name)
        else None
    )


def _parse_bundle_transition_registry(
    tree: ast.Module,
) -> tuple[tuple[str, str, str], ...]:
    value = _assignment(tree, "_EVIDENCE_BUNDLE_TRANSITION_GUARDS_V1")
    if (
        not isinstance(value, ast.Call)
        or not isinstance(value.func, ast.Name)
        or value.func.id != "MappingProxyType"
        or len(value.args) != 1
        or value.keywords
        or not isinstance(value.args[0], ast.Dict)
    ):
        return ()
    rows: list[tuple[str, str, str]] = []
    for key, guard in zip(value.args[0].keys, value.args[0].values, strict=True):
        if (
            not isinstance(key, ast.Tuple)
            or len(key.elts) != 2
            or not all(isinstance(item, ast.Attribute) for item in key.elts)
            or not all(
                isinstance(item.value, ast.Name)
                and item.value.id == "EvidenceBundleTerminalStateV1"
                for item in key.elts
                if isinstance(item, ast.Attribute)
            )
            or not isinstance(guard, ast.Constant)
            or not isinstance(guard.value, str)
        ):
            return ()
        source, target = key.elts
        assert isinstance(source, ast.Attribute)
        assert isinstance(target, ast.Attribute)
        rows.append((source.attr, target.attr, guard.value))
    return tuple(rows)


@dataclass(frozen=True, slots=True)
class _BundleTransitionProbeV1:
    evidence_id: str
    input_lock_id: str
    component_or_template_ref: str
    evidence_bundle_version: str
    terminal_state: EvidenceBundleTerminalStateV1
    independent_review_state: str


def _validate_complete_bundle_transition_matrix() -> tuple[int, int, int]:
    expected_pairs = {
        (source, target)
        for source, target, _guard in OWNER_LIFECYCLE_TRANSITIONS_V1
    }
    allowed = 0
    prohibited = 0
    failures = 0
    for source in EvidenceBundleTerminalStateV1:
        previous = _BundleTransitionProbeV1(
            evidence_id="EVIDENCE::INDEPENDENT-VALIDATION",
            input_lock_id="LOCK::INDEPENDENT-VALIDATION",
            component_or_template_ref="MATH-01",
            evidence_bundle_version=f"BUNDLE::{source.value}::PRIOR",
            terminal_state=source,
            independent_review_state=source.value,
        )
        for target in EvidenceBundleTerminalStateV1:
            candidate = replace(
                previous,
                evidence_bundle_version=f"BUNDLE::{source.value}::{target.value}",
                terminal_state=target,
                independent_review_state=target.value,
            )
            succeeded = True
            try:
                ComputationEvidenceServiceV1._validate_bundle_transition(
                    previous,
                    candidate,  # type: ignore[arg-type]
                )
            except ContractValidationError:
                succeeded = False
            expected = (source.value, target.value) in expected_pairs
            if succeeded != expected:
                failures += 1
            elif succeeded:
                allowed += 1
            else:
                prohibited += 1
    return allowed, prohibited, failures


def _parse_operation_rows(tree: ast.Module) -> tuple[tuple[object, ...], ...]:
    value = _assignment(tree, "_OPERATION_ROWS")
    if not isinstance(value, ast.Tuple):
        return ()
    rows: list[tuple[object, ...]] = []
    for item in value.elts:
        if (
            not isinstance(item, ast.Call)
            or not isinstance(item.func, ast.Name)
            or item.func.id != "_operation_contract"
            or len(item.args) not in {7, 8}
            or not isinstance(item.args[3], ast.Name)
            or not isinstance(item.args[4], ast.Name)
        ):
            return ()
        try:
            rows.append(
                (
                    ast.literal_eval(item.args[0]),
                    ast.literal_eval(item.args[1]),
                    ast.literal_eval(item.args[2]),
                    item.args[3].id,
                    item.args[4].id,
                    ast.literal_eval(item.args[5]),
                    ast.literal_eval(item.args[6]),
                    ast.literal_eval(item.args[7]) if len(item.args) == 8 else None,
                )
            )
        except (ValueError, TypeError):
            return ()
    return tuple(rows)


def _qualified_callable_name(node: ast.expr) -> str:
    """Return the complete statically qualified name for a call target."""

    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _qualified_callable_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _has_exact_false_marker(
    tree: ast.Module,
    *,
    class_name: str,
    marker_name: str,
) -> bool:
    matching_classes = tuple(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    if len(matching_classes) != 1:
        return False
    marker_values: list[ast.expr] = []
    for statement in matching_classes[0].body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == marker_name
            for target in statement.targets
        ):
            marker_values.append(statement.value)
        elif (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.target.id == marker_name
        ):
            marker_values.append(statement.value)
    return (
        len(marker_values) == 1
        and isinstance(marker_values[0], ast.Constant)
        and marker_values[0].value is False
    )


def _runtime_topology_failures(
    file_name: str,
    tree: ast.Module,
) -> tuple[str, ...]:
    policy = RUNTIME_TOPOLOGY_EXCEPTIONS.get(file_name)
    failures: list[str] = []
    permitted_import_count = 0
    permitted_call_count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root not in FORBIDDEN_IMPORT_ROOTS:
                    continue
                is_exact_exception = (
                    policy is not None
                    and len(node.names) == 1
                    and alias.name == policy.allowed_import
                    and alias.asname is None
                )
                if is_exact_exception:
                    permitted_import_count += 1
                else:
                    failures.append(f"runtime import {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".", 1)[0]
            if root in FORBIDDEN_IMPORT_ROOTS:
                parameter_policy_exception = (
                    file_name == "parameter_policy.py"
                    and node.module == "threading"
                    and {alias.name for alias in node.names} <= {"Condition", "Lock"}
                )
                cache_publication_exception = (
                    file_name == "evidence.py"
                    and node.module == "threading"
                    and tuple((alias.name, alias.asname) for alias in node.names)
                    == (("Lock", None),)
                )
                if not parameter_policy_exception and not cache_publication_exception:
                    failures.append(f"runtime import {node.module}")
        elif isinstance(node, ast.Call):
            qualified_name = _qualified_callable_name(node.func)
            is_exact_exception = (
                policy is not None
                and qualified_name == policy.allowed_qualified_call
            )
            if is_exact_exception:
                permitted_call_count += 1
                continue
            terminal_name = qualified_name.rsplit(".", 1)[-1]
            if terminal_name in FORBIDDEN_CALL_NAMES:
                failures.append(f"runtime call {qualified_name or terminal_name}")
    if policy is not None:
        if permitted_import_count != 1:
            failures.append(
                f"reference exception requires exactly one import {policy.allowed_import}"
            )
        if permitted_call_count != 1:
            failures.append(
                "reference exception requires exactly one call "
                f"{policy.allowed_qualified_call}"
            )
        if not _has_exact_false_marker(
            tree,
            class_name=policy.adapter_class_name,
            marker_name=policy.production_marker_name,
        ):
            failures.append(
                f"{policy.adapter_class_name}.{policy.production_marker_name} "
                "must be literal False"
            )
    return tuple(failures)


def validate_runtime_topology_source(
    *,
    file_name: str,
    source: str,
) -> tuple[str, ...]:
    """Validate a source fragment against the exact centralized runtime policy."""

    tree = ast.parse(source, filename=file_name)
    return _runtime_topology_failures(file_name, tree)


def main() -> int:
    failures: list[str] = []
    parsed: dict[str, ast.Module] = {}
    for path in sorted(PACKAGE.glob("*.py"), key=lambda item: item.name):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parsed[path.name] = tree
        failures.extend(
            f"{path.name}: {failure}"
            for failure in _runtime_topology_failures(path.name, tree)
        )
    validation = parsed.get("validation.py")
    models = parsed.get("models.py")
    if validation is None or models is None:
        failures.append("operation registry source is absent")
    else:
        common_request = _assignment(validation, "_COMMON_OPERATION_REQUEST_FIELDS")
        common_response = _assignment(validation, "_COMMON_OPERATION_RESPONSE_FIELDS")
        if (
            common_request is None
            or ast.literal_eval(common_request) != COMMON_REQUEST_FIELDS
        ):
            failures.append("common request fields differ from the certified schema")
        if (
            common_response is None
            or ast.literal_eval(common_response) != COMMON_RESPONSE_FIELDS
        ):
            failures.append("common response fields differ from the certified schema")
        actual_rows = _parse_operation_rows(validation)
        if actual_rows != EXPECTED_ROWS:
            failures.append("operation roster differs from the exact certified roster")
        if _class_fields(models, "OperationRequestEnvelopeV1") != tuple(
            name for name, _type_name in COMMON_REQUEST_FIELDS
        ):
            failures.append("request envelope top-level fields are not exact")
        if _class_fields(models, "OperationResponseEnvelopeV1") != tuple(
            name for name, _type_name in COMMON_RESPONSE_FIELDS
        ):
            failures.append("response envelope top-level fields are not exact")
        for row in EXPECTED_ROWS:
            request_type = str(row[3])
            response_type = str(row[4])
            request_tail = tuple(name for name, _type_name in row[5])
            response_tail = (row[6][0],)
            if _class_fields(models, request_type) != request_tail:
                failures.append(f"{request_type}: request fields differ")
            if _class_fields(models, response_type) != response_tail:
                failures.append(f"{response_type}: response fields differ")
        model_text = (PACKAGE / "models.py").read_text(encoding="utf-8")
        validation_text = (PACKAGE / "validation.py").read_text(encoding="utf-8")
        for forbidden in ("payload_json", "result_json", "typing.Any"):
            if forbidden in model_text or forbidden in validation_text:
                failures.append(f"untyped operation surface remains: {forbidden}")
        for required in (
            "schema_version=\"1.4.0\"",
            "PURE_OR_APPEND_ONLY_NON_PROVIDER_EFFECT",
            "CONTRACT_DEFINITION_ONLY",
            "ContextualComputabilityResolverV1.resolve",
            "_validate_trace_context",
            "deterministic_json",
        ):
            if required not in model_text and required not in validation_text:
                failures.append(f"operation invariant is absent: {required}")
    evidence = parsed.get("evidence.py")
    if evidence is None:
        failures.append("ST12-F evidence owner source is absent")
    else:
        if _class_fields(evidence, "ComputationEvidenceBundleV1") != OWNER_BUNDLE_FIELDS_V1:
            failures.append("bundle fields differ from the independent exact 30-field roster")
        if _parse_bundle_transition_registry(evidence) != OWNER_LIFECYCLE_TRANSITIONS_V1:
            failures.append("bundle transition registry differs from the independent exact six-transition roster")
        outcome_fields = {
            "RegisteredLaneResultOutcomeV1": (
                "registered_result",
                "receipt_refs",
            ),
            "BuiltEvidenceBundleOutcomeV1": (
                "evidence_bundle",
                "receipt_refs",
            ),
        }
        for class_name, expected_fields in outcome_fields.items():
            if _class_fields(evidence, class_name) != expected_fields:
                failures.append(f"{class_name}: immutable outcome fields differ")
            if not _class_is_frozen_slots_dataclass(evidence, class_name):
                failures.append(f"{class_name}: frozen slots contract is absent")
        if _method_return_name(
            evidence,
            "ComputationEvidenceServiceV1",
            "register_result",
        ) != "RegisteredLaneResultOutcomeV1":
            failures.append("OP14 does not return its immutable atomic outcome")
        if _method_return_name(
            evidence,
            "ComputationEvidenceServiceV1",
            "build_bundle",
        ) != "BuiltEvidenceBundleOutcomeV1":
            failures.append("OP15 does not return its immutable atomic outcome")
        evidence_text = (PACKAGE / "evidence.py").read_text(encoding="utf-8")
        if (
            "_last_committed_receipt_refs" in evidence_text
            or "last_committed_receipt_refs" in evidence_text
        ):
            failures.append("shared mutable last-result state remains")

    grouped_test_path = (
        REPO_ROOT
        / "tests"
        / "stage1_prediction_markets"
        / "qku_computation_control_plane"
        / "tranche_f"
        / "test_replay_paper_evidence_matrix.py"
    )
    if not grouped_test_path.is_file():
        failures.append("grouped replay/PAPER evidence matrix is absent")
    else:
        grouped_tree = ast.parse(
            grouped_test_path.read_text(encoding="utf-8"),
            filename=str(grouped_test_path),
        )
        case_roster = _assignment(grouped_tree, "_CONCURRENCY_CASE_IDS_V1_7")
        if (
            case_roster is None
            or ast.literal_eval(case_roster) != OWNER_CONCURRENCY_CASE_IDS_V1
        ):
            failures.append("grouped concurrency case roster differs from v1.7")
        threading_imports = tuple(
            node
            for node in grouped_tree.body
            if isinstance(node, ast.ImportFrom)
            and node.module == "threading"
        )
        if (
            len(threading_imports) != 1
            or tuple(
                (alias.name, alias.asname)
                for alias in threading_imports[0].names
            )
            != (("Barrier", None), ("Thread", None))
        ):
            failures.append("grouped concurrency test threading import differs")
        if any(
            isinstance(node, ast.Call)
            and (
                (isinstance(node.func, ast.Name) and node.func.id == "sleep")
                or (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "sleep"
                )
            )
            for node in ast.walk(grouped_tree)
        ):
            failures.append("grouped concurrency tests use sleep as proof")
    allowed_transitions, prohibited_transitions, transition_failures = (
        _validate_complete_bundle_transition_matrix()
    )
    if (
        allowed_transitions != 6
        or prohibited_transitions != 58
        or transition_failures
    ):
        failures.append(
            "bundle transition behavior does not reject the complete prohibited matrix"
        )
    forbidden_files = {
        "runtime.py",
        "supervision.py",
        "backup.py",
        "database.py",
    }
    if forbidden_files & {path.name for path in PACKAGE.glob("*.py")}:
        failures.append("a later-tranche runtime module exists")
    service = parsed.get("service.py")
    if service is None:
        failures.append("the centralized Tranche-B service extension is absent")
    else:
        service_class_nodes = tuple(
            node for node in service.body if isinstance(node, ast.ClassDef)
        )
        service_classes = {node.name for node in service_class_nodes}
        if service_classes != {"QKUComputationControlPlaneV1"}:
            failures.append("the central service class roster is not exact")
        else:
            service_methods = {
                node.name
                for node in service_class_nodes[0].body
                if isinstance(node, ast.FunctionDef)
            }
            expected_methods = {
                "__post_init__",
                *(str(row[1]) for row in EXPECTED_ROWS),
            }
            if service_methods != expected_methods:
                failures.append(
                    "the central service does not expose exactly operations 01..15"
                )
        if any(
            isinstance(node, ast.ExceptHandler)
            and isinstance(node.type, ast.Name)
            and node.type.id in {"Exception", "BaseException"}
            for node in ast.walk(service)
        ):
            failures.append("the central service catches an untyped broad exception")
        service_text = (PACKAGE / "service.py").read_text(encoding="utf-8")
        if "last_committed_receipt_refs" in service_text:
            failures.append("public OP14/OP15 still read shared last-result state")
        for required in (
            "outcome = evidence_service.register_result(request)",
            "outcome = evidence_service.build_bundle(request)",
            "refs = outcome.receipt_refs",
            "bundle = outcome.evidence_bundle",
        ):
            if required not in service_text:
                failures.append(
                    f"public atomic outcome consumer is absent: {required}"
                )
    validation_text = (PACKAGE / "validation.py").read_text(encoding="utf-8")
    for required in (
        "ST12B_CENTRAL_SERVICE_OPERATION_IDS = tuple(OPERATION_SCHEMA_REGISTRY)[:12]",
        "tuple(OPERATION_SCHEMA_REGISTRY)[:8]",
        "tuple(OPERATION_SCHEMA_REGISTRY)[8:10]",
        "tuple(OPERATION_SCHEMA_REGISTRY)[10:12]",
        "tuple(OPERATION_SCHEMA_REGISTRY)[12:]",
    ):
        if required not in validation_text:
            failures.append(f"Tranche-B operation capability projection missing: {required}")
    executable_checks = _st12f_executable_operation_checks()
    if not all(executable_checks):
        failures.extend(
            f"ST12-F executable OP14 invariant failed: check_{index}"
            for index, passed in enumerate(executable_checks, start=1)
            if not passed
        )
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(
        f"{SUCCESS_MARKER} operation_contracts={len(EXPECTED_ROWS)} "
        f"executable_op14_checks={len(executable_checks)} "
        f"bundle_fields={len(OWNER_BUNDLE_FIELDS_V1)} "
        f"lifecycle_transitions={allowed_transitions} "
        f"prohibited_transition_rejections={prohibited_transitions}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
