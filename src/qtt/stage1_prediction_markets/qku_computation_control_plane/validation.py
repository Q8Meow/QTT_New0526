"""Cross-contract, authority, boundary, and value-level validation."""

from __future__ import annotations

import ast
from collections import Counter
from dataclasses import dataclass, fields
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from itertools import product
import json
import math
from pathlib import Path
from types import MappingProxyType
from typing import Callable

from .authority import CapabilityEnvelopeV1, assert_no_effect_authority
from .bindings import SOURCE_CLAIM_BINDING_RULES
from .context import ComputationContextKeyV1
from .errors import ComputationControlPlaneError, ContractValidationError, ReasonCode
from .implementation_registry import (
    DiscreteLinearBiasV1,
    DiscreteVariableV1,
    IMPLEMENTATION_REGISTRY,
    load_legacy_formula_comparators,
    LinearTermV1,
    ObjectiveScalingReceiptV1,
    QuantityAndFrictionTermsV1,
    QuadraticConstraintV1,
    QuadraticVariableV1,
    QuboModelV1,
    QuboUpperTermV1,
    compute_math_47_qubo_to_ising_transform,
    get_math_callable,
)
from .identity_adapter import RP5CIdentityAdapterV1
from .models import (
    BenchmarkSignConvention,
    BuildEvidenceBundleRequestV1,
    BuildEvidenceBundleResponseV1,
    CompareWithNoTradeRequestV1,
    CompareWithNoTradeResponseV1,
    CompileReplayPaperCohortRequestV1,
    CompileReplayPaperCohortResponseV1,
    ComputeComponentRequestV1,
    ComputeComponentResponseV1,
    ComputeStackRequestV1,
    ComputeStackResponseV1,
    ComputationExecutionReceiptV1,
    ConfigurationEnvelopeV1,
    ContractFieldV1,
    EvaluateTradePlanRequestV1,
    EvaluateTradePlanResponseV1,
    ExplainResolutionRequestV1,
    ExplainResolutionResponseV1,
    FallbackEnvelopeV1,
    FormulaRuntimeSnapshotV1,
    GetSnapshotViewRequestV1,
    GetSnapshotViewResponseV1,
    HealthEnvelopeV1,
    HealthState,
    IdentityResolutionV1,
    LatencyHotPathSnapshotBoundaryAdapterV1,
    ObjectiveSense,
    OperationCapabilityClass,
    OperationContractV1,
    OperationStatusV1,
    OperationRequestEnvelopeV1,
    OperationResponseEnvelopeV1,
    OperationSideEffectClass,
    RegisterReplayPaperResultRequestV1,
    RegisterReplayPaperResultResponseV1,
    RequestMaterializationWorkOrderRequestV1,
    RequestMaterializationWorkOrderResponseV1,
    ResolveApplicableStackRequestV1,
    ResolveApplicableStackResponseV1,
    ResolveContextualComputabilityRequestV1,
    ResolveContextualComputabilityResponseV1,
    ResolveIdentityRequestV1,
    ResolveIdentityResponseV1,
    ResolveRequiredInputsRequestV1,
    ResolveRequiredInputsResponseV1,
    SnapshotState,
    SubmitCandidateProposalRequestV1,
    SubmitCandidateProposalResponseV1,
    SupervisionEnvelopeV1,
    TransactionEnvelopeV1,
    TypedValueKindV1,
    TypedValueRecordV1,
    TypedValueV1,
    VariableDomain,
)
from .oracle_contracts import GOLDEN_VECTOR_BY_MATH_ID, ORACLE_BY_MATH_ID
from .parameter_policy import PARAMETER_POLICIES, ParameterPolicyResolverV1
from .plugin_adapter import PR162EPluginAdapterV1
from .protocols import ExistingOwnerProjectionAdapterV1
from .quantum_adapter import PR162EQuantumAdapterV1, QuantumModelKind
from .serialization import validate_relative_path
from .source_policy import (
    CERTIFIED_SOURCE_STATES,
    FAK_FOK_RESPONSE_CONTRACT,
    POLYMARKET_ENDPOINT_LIMITS,
    POLYMARKET_SIGNER_BUCKETS,
    SOURCE_CURRENTIZATION_OVERLAYS,
    SourceRevalidationSchedulerAdapterV1,
    classify_trade_lifecycle,
)
from .specification import MATH_IO_CONTRACTS


PRODUCTION_CORE_PATHS = (
    "src/qtt/stage1_prediction_markets/qku_computation_control_plane/__init__.py",
    "src/qtt/stage1_prediction_markets/qku_computation_control_plane/models.py",
    "src/qtt/stage1_prediction_markets/qku_computation_control_plane/errors.py",
    "src/qtt/stage1_prediction_markets/qku_computation_control_plane/context.py",
    "src/qtt/stage1_prediction_markets/qku_computation_control_plane/specification.py",
    "src/qtt/stage1_prediction_markets/qku_computation_control_plane/implementation_registry.py",
    "src/qtt/stage1_prediction_markets/qku_computation_control_plane/identity_adapter.py",
    "src/qtt/stage1_prediction_markets/qku_computation_control_plane/plugin_adapter.py",
    "src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_adapter.py",
    "src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_policy.py",
    "src/qtt/stage1_prediction_markets/qku_computation_control_plane/parameter_policy.py",
    "src/qtt/stage1_prediction_markets/qku_computation_control_plane/bindings.py",
    "src/qtt/stage1_prediction_markets/qku_computation_control_plane/dependency_graph.py",
    "src/qtt/stage1_prediction_markets/qku_computation_control_plane/oracle_contracts.py",
    "src/qtt/stage1_prediction_markets/qku_computation_control_plane/authority.py",
    "src/qtt/stage1_prediction_markets/qku_computation_control_plane/protocols.py",
    "src/qtt/stage1_prediction_markets/qku_computation_control_plane/serialization.py",
    "src/qtt/stage1_prediction_markets/qku_computation_control_plane/validation.py",
    "src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_rights.py",
)

OWNER_IDS = (
    "RP5C_IDENTITY_LIBRARY",
    "PR162E_PLUGIN_FRAMEWORK",
    "PR162E_Q_QUANTUM_AUTOMAPPER",
    "READINESS1",
    "PRETRADE1",
    "SVC1",
    "AGENT_ORCH1",
    "SOURCE_REVALIDATION_SCHEDULER",
    "LATENCY_HOT_PATH_SNAPSHOT_BOUNDARY",
    "PR162D_R2A_FORMULA_SEED_LIBRARY",
)

MATH_IDS = (
    "MATH-01",
    "MATH-02",
    "MATH-03",
    "MATH-04",
    "MATH-05",
    "MATH-06",
    "MATH-07",
    "MATH-08",
    "MATH-09",
    "MATH-10",
    "MATH-11",
    "MATH-12",
    "MATH-13",
    "MATH-14",
    "MATH-15",
    "MATH-46",
    "MATH-47",
    "MATH-48",
    "MATH-49",
)

TRANCHE_A_CONTROL_ROWS = (
    ("ST11-ARCHITECTURE::001", "architecture", "canonical-owner-uniqueness"),
    ("ST11-ARCHITECTURE::002", "architecture", "control-plane-boundary"),
    ("ST11-ARCHITECTURE::003", "architecture", "identity-plane-binding"),
    ("ST11-ARCHITECTURE::004", "architecture", "contract-envelope-completeness"),
    ("ST11-ARCHITECTURE::005", "architecture", "operation-contract-closure"),
    ("ST11-ARCHITECTURE::006", "architecture", "contextual-computability"),
    ("ST11-ARCHITECTURE::007", "architecture", "dependency-graph-soundness"),
    ("ST11-ARCHITECTURE::008", "architecture", "mode-evidence-orthogonality"),
    ("ST11-ARCHITECTURE::009", "architecture", "repository-file-closure"),
    ("ST11-ARCHITECTURE::010", "architecture", "tranche-dag-closure"),
    ("ST11-ARCHITECTURE::011", "architecture", "generated-artifact-ownership"),
    ("ST11-ARCHITECTURE::012", "architecture", "consume-not-rebuild"),
    ("ST11-ARCHITECTURE::013", "architecture", "route-not-runtime"),
    ("ST11-ARCHITECTURE::014", "architecture", "snapshot-boundary"),
    ("ST11-ARCHITECTURE::015", "architecture", "transaction-boundary"),
    ("ST11-ARCHITECTURE::016", "architecture", "schema-cross-consistency"),
    ("ST11-ARCHITECTURE::017", "architecture", "cross-platform-paths"),
    ("ST11-ARCHITECTURE::018", "architecture", "no-orphan-consumers"),
    (
        "ST11-ARCHITECTURE::019",
        "architecture",
        "current-repository-reconciliation",
    ),
    ("ST11-ARCHITECTURE::020", "architecture", "step12-tranche-readiness"),
    ("ST11-OPERATIONS::001", "operations", "runtime-topology"),
    ("ST11-OPERATIONS::002", "operations", "configuration-control"),
    ("ST11-OPERATIONS::003", "operations", "health-readiness"),
    ("ST11-OPERATIONS::004", "operations", "lifecycle-supervision"),
    ("ST11-QUANTUM::001", "quantum", "consume-existing-mapper"),
    ("ST11-QUANTUM::002", "quantum", "problem-shape-classification"),
    ("ST11-QUANTUM::003", "quantum", "model-semantics"),
    ("ST11-QUANTUM::004", "quantum", "objective-sense-and-scale"),
    ("ST11-QUANTUM::005", "quantum", "variable-encoding"),
    ("ST11-QUANTUM::006", "quantum", "constraint-mapping"),
    ("ST11-SECURITY::001", "security", "threat-model-completeness"),
    ("ST11-SECURITY::002", "security", "default-deny-capabilities"),
    ("ST11-SECURITY::003", "security", "authentication-binding"),
    ("ST11-SECURITY::004", "security", "authorization-least-privilege"),
    ("ST11-SECURITY::005", "security", "secret-isolation"),
    ("ST11-SECURITY::006", "security", "input-validation"),
    ("ST11-SECURITY::007", "security", "deserialization-safety"),
    ("ST11-SOURCE::001", "source", "all-29-revalidated"),
    ("ST11-SOURCE::002", "source", "source-precedence"),
    ("ST11-SOURCE::003", "source", "effective-epoch"),
    ("ST11-SOURCE::004", "source", "fact-atomicity"),
    ("ST11-SOURCE::005", "source", "conflict-resolution"),
)

INDEPENDENT_VALIDATOR_BY_DOMAIN = MappingProxyType(
    {
        domain: (
            "tools/independent_validate_qku_computation_control_plane_"
            f"{domain}.py"
        )
        for domain in ("architecture", "operations", "quantum", "security", "source")
    }
)

_SHARED_VALIDATION_TEST_ROWS = (
    (
        "RUN_VALIDATION_GATES",
        "architecture",
        "tests/fail_closed/test_run_validation_gates.py",
    ),
    (
        "CHANGED_AREA_VALIDATION_ROUTER",
        "architecture",
        "tests/tools/test_changed_area_validation_router.py",
    ),
    (
        "VALIDATION_INVENTORY",
        "architecture",
        "tests/tools/test_validation_inventory.py",
    ),
    (
        "VALIDATION_SCOPE_REGISTRY",
        "architecture",
        "tests/tools/test_validation_scope_registry.py",
    ),
    (
        "CI_BRANCH_CONTEXT",
        "architecture",
        "tests/tools/test_ci_branch_context.py",
    ),
)

REPO_ROOT = Path(__file__).resolve().parents[4]

_COMMON_OPERATION_REQUEST_FIELDS = (
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
_COMMON_OPERATION_RESPONSE_FIELDS = (
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


def _operation_contract(
    operation_id: str,
    operation_name: str,
    owner: str,
    request_model: type[OperationRequestEnvelopeV1],
    response_model: type[OperationResponseEnvelopeV1],
    request_tail: tuple[tuple[str, str], ...],
    response_tail: tuple[str, str],
    resolver_name: str | None = None,
) -> OperationContractV1:
    return OperationContractV1(
        operation_id=operation_id,
        operation_name=operation_name,
        owner=owner,
        request_type=request_model.__name__,
        response_type=response_model.__name__,
        schema_version="1.4.0",
        request_fields=tuple(
            ContractFieldV1(name, type_name)
            for name, type_name in (
                *_COMMON_OPERATION_REQUEST_FIELDS,
                *request_tail,
            )
        ),
        response_fields=tuple(
            ContractFieldV1(name, type_name)
            for name, type_name in (
                *_COMMON_OPERATION_RESPONSE_FIELDS,
                response_tail,
            )
        ),
        request_model=request_model,
        response_model=response_model,
        resolver_name=resolver_name,
        metadata={
            "tranche": "ST12-TRANCHE-A",
            "execution_state": "CONTRACT_DEFINITION_ONLY",
        },
    )


_OPERATION_ROWS = (
    _operation_contract(
        "ST10-OP::01",
        "resolve_identity",
        "UnifiedCanonicalIdentityPlaneV1",
        ResolveIdentityRequestV1,
        ResolveIdentityResponseV1,
        (("identity_query", "TypedValueRecordV1"),),
        ("identity_resolution", "IdentityResolutionV1"),
    ),
    _operation_contract(
        "ST10-OP::02",
        "resolve_contextual_computability",
        "QKUComputationControlPlaneV1",
        ResolveContextualComputabilityRequestV1,
        ResolveContextualComputabilityResponseV1,
        (
            ("component_id", "str"),
            (
                "required_computability_classes",
                "tuple[ComputabilityClassV1,...]",
            ),
        ),
        ("computability", "ContextualComputabilityResolutionV1"),
        "ContextualComputabilityResolverV1.resolve",
    ),
    _operation_contract(
        "ST10-OP::03",
        "resolve_applicable_stack",
        "QKUComputationControlPlaneV1",
        ResolveApplicableStackRequestV1,
        ResolveApplicableStackResponseV1,
        (
            ("trade_plan_candidate_id", "str"),
            ("required_launch_roles", "tuple[str,...]"),
        ),
        ("stack_resolution", "StackResolutionV1"),
    ),
    _operation_contract(
        "ST10-OP::04",
        "resolve_required_inputs",
        "QKUComputationControlPlaneV1",
        ResolveRequiredInputsRequestV1,
        ResolveRequiredInputsResponseV1,
        (
            ("component_ids", "tuple[str,...]"),
            ("include_optional", "bool"),
        ),
        ("input_resolution", "InputResolutionV1"),
    ),
    _operation_contract(
        "ST10-OP::05",
        "compute_component",
        "QKUComputationControlPlaneV1",
        ComputeComponentRequestV1,
        ComputeComponentResponseV1,
        (
            ("component_id", "str"),
            ("input_values", "TypedValueRecordV1"),
            ("expected_output_schema_ref", "str"),
        ),
        ("component_result", "ComponentResultV1"),
    ),
    _operation_contract(
        "ST10-OP::06",
        "compute_stack",
        "QKUComputationControlPlaneV1",
        ComputeStackRequestV1,
        ComputeStackResponseV1,
        (
            ("stack_id", "str"),
            ("component_ids", "tuple[str,...]"),
            ("input_values", "TypedValueRecordV1"),
        ),
        ("stack_result", "StackResultV1"),
    ),
    _operation_contract(
        "ST10-OP::07",
        "compare_with_no_trade",
        "QKUComputationControlPlaneV1",
        CompareWithNoTradeRequestV1,
        CompareWithNoTradeResponseV1,
        (
            ("trade_plan_candidate_id", "str"),
            ("no_trade_candidate_id", "str"),
            ("comparison_basis", "str"),
        ),
        ("comparison", "NoTradeComparisonV1"),
    ),
    _operation_contract(
        "ST10-OP::08",
        "evaluate_trade_plan",
        "QKUComputationControlPlaneV1",
        EvaluateTradePlanRequestV1,
        EvaluateTradePlanResponseV1,
        (
            ("trade_plan_candidate_id", "str"),
            ("stack_id", "str"),
            ("accounting_tca_view_ref", "str"),
            ("risk_cash_state_ref", "str"),
            ("no_trade_candidate_id", "str"),
        ),
        ("evaluation", "TradePlanEvaluationV1"),
    ),
    _operation_contract(
        "ST10-OP::09",
        "get_snapshot_view",
        "QKUComputationControlPlaneV1",
        GetSnapshotViewRequestV1,
        GetSnapshotViewResponseV1,
        (
            ("snapshot_id", "str"),
            ("view_class", "str"),
            ("include_value_lineage", "bool"),
        ),
        ("snapshot_view", "SnapshotViewV1"),
    ),
    _operation_contract(
        "ST10-OP::10",
        "explain_resolution",
        "QKUComputationControlPlaneV1",
        ExplainResolutionRequestV1,
        ExplainResolutionResponseV1,
        (
            ("resolution_receipt_id", "str"),
            ("explanation_scope", "str"),
            ("max_evidence_items", "int"),
        ),
        ("explanation", "ResolutionExplanationV1"),
    ),
    _operation_contract(
        "ST10-OP::11",
        "submit_candidate_proposal",
        "QKUComputationControlPlaneV1",
        SubmitCandidateProposalRequestV1,
        SubmitCandidateProposalResponseV1,
        (
            ("candidate_kind", "str"),
            ("proposed_specification", "TypedValueRecordV1"),
            ("source_candidate_refs", "tuple[str,...]"),
            ("requested_owner_review", "bool"),
        ),
        ("proposal", "CandidateProposalV1"),
    ),
    _operation_contract(
        "ST10-OP::12",
        "request_materialization_work_order",
        "QKUComputationControlPlaneV1",
        RequestMaterializationWorkOrderRequestV1,
        RequestMaterializationWorkOrderResponseV1,
        (
            ("missing_contract_ids", "tuple[str,...]"),
            ("reason_codes", "tuple[OperationBlockerCodeV1,...]"),
            ("priority", "str"),
            ("requested_owner", "str"),
        ),
        ("work_order", "MaterializationWorkOrderV1"),
    ),
    _operation_contract(
        "ST10-OP::13",
        "compile_replay_paper_cohort",
        "ReplayPaperCohortCompilerV1",
        CompileReplayPaperCohortRequestV1,
        CompileReplayPaperCohortResponseV1,
        (
            ("template_ids", "tuple[str,...]"),
            ("requested_lanes", "tuple[str,...]"),
            ("input_lock_id", "str"),
            ("campaign_execution_requested", "bool"),
        ),
        ("cohort_compilation", "ReplayPaperCohortCompilationV1"),
    ),
    _operation_contract(
        "ST10-OP::14",
        "register_replay_paper_result",
        "ComputationEvidenceServiceV1",
        RegisterReplayPaperResultRequestV1,
        RegisterReplayPaperResultResponseV1,
        (
            ("cohort_instance_id", "str"),
            ("lane", "str"),
            ("input_lock_id", "str"),
            ("result_packet", "TypedValueRecordV1"),
        ),
        ("registration", "ReplayPaperResultRegistrationV1"),
    ),
    _operation_contract(
        "ST10-OP::15",
        "build_evidence_bundle",
        "ComputationEvidenceServiceV1",
        BuildEvidenceBundleRequestV1,
        BuildEvidenceBundleResponseV1,
        (
            ("component_id", "str"),
            ("input_lock_id", "str"),
            ("evidence_record_refs", "tuple[str,...]"),
            ("required_lanes", "tuple[str,...]"),
        ),
        ("evidence_bundle", "EvidenceBundleResultV1"),
    ),
)

OPERATION_SCHEMA_REGISTRY = MappingProxyType(
    {operation.operation_id: operation for operation in _OPERATION_ROWS}
)
if len(OPERATION_SCHEMA_REGISTRY) != len(_OPERATION_ROWS):
    raise ContractValidationError(
        ReasonCode.INVALID_CONTRACT,
        "certified operation ids must be unique",
    )
TRANCHE_A_OPERATION_CONTRACTS = tuple(OPERATION_SCHEMA_REGISTRY.values())


@dataclass(frozen=True, slots=True)
class ValidationCheckV1:
    check_id: str
    passed: bool
    detail: str


@dataclass(frozen=True, slots=True)
class ValidationReportV1:
    domain: str
    checks: tuple[ValidationCheckV1, ...]

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(check.passed for check in self.checks)

    def assert_passed(self) -> None:
        failed = [check for check in self.checks if not check.passed]
        if failed:
            raise ContractValidationError(
                ReasonCode.VALIDATION_FAILED,
                "; ".join(f"{item.check_id}: {item.detail}" for item in failed),
            )


class CoverageTerminalStatusV1(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True, slots=True)
class CoverageRowV1:
    row_id: str
    category: str
    domain: str
    predicate: str
    subject_ref: str
    test_path: str
    independent_validator: str
    terminal_status: CoverageTerminalStatusV1
    owner: str
    producer: str
    consumer_refs: tuple[str, ...]
    no_orphan_disposition: str

    def __post_init__(self) -> None:
        for name in (
            "row_id",
            "category",
            "domain",
            "predicate",
            "subject_ref",
            "test_path",
            "independent_validator",
            "owner",
            "producer",
            "no_orphan_disposition",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ContractValidationError(
                    ReasonCode.INCOMPLETE_CONTRACT,
                    f"coverage row {name} must be nonempty text",
                )
        validate_relative_path(self.test_path)
        validate_relative_path(self.independent_validator)
        if not isinstance(self.terminal_status, CoverageTerminalStatusV1):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "coverage terminal status must be typed",
            )
        if (
            not isinstance(self.consumer_refs, tuple)
            or not self.consumer_refs
            or any(
                not isinstance(value, str) or not value
                for value in self.consumer_refs
            )
            or len(self.consumer_refs) != len(set(self.consumer_refs))
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                f"coverage row has no exact consumer route: {self.row_id}",
            )


@dataclass(frozen=True, slots=True)
class TrancheACoverageManifestV1:
    rows: tuple[CoverageRowV1, ...]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.rows, tuple)
            or not self.rows
            or any(not isinstance(row, CoverageRowV1) for row in self.rows)
        ):
            raise ContractValidationError(
                ReasonCode.INCOMPLETE_CONTRACT,
                "coverage manifest requires typed immutable rows",
            )
        row_ids = tuple(row.row_id for row in self.rows)
        if len(row_ids) != len(set(row_ids)):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "coverage manifest contains duplicate row identities",
            )

    @property
    def executed_counts(self) -> MappingProxyType:
        counts = Counter(
            row.category
            for row in self.rows
            if row.terminal_status is CoverageTerminalStatusV1.PASS
        )
        counts["total_rows"] = sum(counts.values())
        return MappingProxyType(dict(sorted(counts.items())))


@dataclass(frozen=True, slots=True)
class _CoverageBlueprintV1:
    row_id: str
    category: str
    domain: str
    predicate: str
    subject_ref: str
    test_path: str
    independent_validator: str
    owner: str = "QKUComputationControlPlaneV1"
    producer: str = "TrancheACoverageManifestV1"
    consumer_refs: tuple[str, ...] = (
        "QKU_COMPUTATION_CONTROL_PLANE_PRIMARY_VALIDATION",
        "QKU_COMPUTATION_CONTROL_PLANE_INDEPENDENT_VALIDATION",
    )
    no_orphan_disposition: str = "VALIDATED_AND_CONSUMED"


def _control_test_path(domain: str, predicate: str) -> str:
    return (
        "tests/stage1_prediction_markets/qku_computation_control_plane/"
        f"{domain}/test_{predicate.replace('-', '_')}.py"
    )


def _coverage_blueprint() -> tuple[_CoverageBlueprintV1, ...]:
    rows: list[_CoverageBlueprintV1] = []
    for control_id, domain, predicate in TRANCHE_A_CONTROL_ROWS:
        rows.append(
            _CoverageBlueprintV1(
                row_id=control_id,
                category="closure_rows",
                domain=domain,
                predicate=predicate,
                subject_ref=control_id,
                test_path=_control_test_path(domain, predicate),
                independent_validator=INDEPENDENT_VALIDATOR_BY_DOMAIN[domain],
            )
        )
    for index, path in enumerate(PRODUCTION_CORE_PATHS, 1):
        rows.append(
            _CoverageBlueprintV1(
                row_id=f"ST12A-REPOSITORY::{index:02d}",
                category="repository_dispositions",
                domain="architecture",
                predicate="owned-production-path-present-and-consumed",
                subject_ref=path,
                test_path=_control_test_path(
                    "architecture",
                    "repository-file-closure",
                ),
                independent_validator=INDEPENDENT_VALIDATOR_BY_DOMAIN[
                    "architecture"
                ],
            )
        )
    for policy in PARAMETER_POLICIES:
        rows.append(
            _CoverageBlueprintV1(
                row_id=policy.parameter_id,
                category="parameter_policy_rows",
                domain="architecture",
                predicate="parameter-policy-resolves-exact-certified-row",
                subject_ref=policy.parameter_id,
                test_path=_control_test_path(
                    "architecture",
                    "step12-tranche-readiness",
                ),
                independent_validator=INDEPENDENT_VALIDATOR_BY_DOMAIN[
                    "architecture"
                ],
            )
        )
    for math_id in MATH_IDS:
        domain = "quantum" if math_id in {"MATH-46", "MATH-47", "MATH-48", "MATH-49"} else "architecture"
        validator = INDEPENDENT_VALIDATOR_BY_DOMAIN[domain]
        rows.append(
            _CoverageBlueprintV1(
                row_id=f"ST12A-MATH-SPEC::{math_id}",
                category="mathematical_specifications",
                domain=domain,
                predicate="implementation-and-typed-io-contract-closed",
                subject_ref=math_id,
                test_path=_control_test_path(
                    "architecture",
                    "schema-cross-consistency",
                ),
                independent_validator=validator,
            )
        )
        oracle = ORACLE_BY_MATH_ID[math_id]
        rows.append(
            _CoverageBlueprintV1(
                row_id=f"ST12A-ORACLE::{oracle.oracle_id}",
                category="independent_oracle_specifications",
                domain=domain,
                predicate="independent-oracle-lineage-closed",
                subject_ref=oracle.oracle_id,
                test_path=_control_test_path(
                    "architecture",
                    "no-orphan-consumers",
                ),
                independent_validator=validator,
            )
        )
        vector = GOLDEN_VECTOR_BY_MATH_ID[math_id]
        rows.append(
            _CoverageBlueprintV1(
                row_id=f"ST12A-VECTOR::{vector.vector_id}",
                category="golden_vectors_and_invariants",
                domain=domain,
                predicate="golden-vector-lineage-and-comparison-closed",
                subject_ref=vector.vector_id,
                test_path=_control_test_path(
                    "architecture",
                    "schema-cross-consistency",
                ),
                independent_validator=validator,
            )
        )
    for control_id, domain, predicate in TRANCHE_A_CONTROL_ROWS:
        path = _control_test_path(domain, predicate)
        rows.append(
            _CoverageBlueprintV1(
                row_id=f"ST12A-TEST::{control_id}",
                category="test_rows",
                domain=domain,
                predicate="certified-domain-test-path-present",
                subject_ref=path,
                test_path=path,
                independent_validator=INDEPENDENT_VALIDATOR_BY_DOMAIN[domain],
            )
        )
    for row_name, domain, test_path in _SHARED_VALIDATION_TEST_ROWS:
        validator = INDEPENDENT_VALIDATOR_BY_DOMAIN[domain]
        rows.append(
            _CoverageBlueprintV1(
                row_id=f"ST12A-TEST::SHARED::{row_name}",
                category="test_rows",
                domain=domain,
                predicate="shared-centralized-validation-test-present",
                subject_ref=test_path,
                test_path=test_path,
                independent_validator=validator,
            )
        )
    for domain, validator in INDEPENDENT_VALIDATOR_BY_DOMAIN.items():
        primary_path = "tools/validate_qku_computation_control_plane.py"
        rows.extend(
            (
                _CoverageBlueprintV1(
                    row_id=f"ST12A-COMMAND::PRIMARY::{domain}",
                    category="validation_command_rows",
                    domain=domain,
                    predicate=(
                        "python -B tools/validate_qku_computation_control_plane.py "
                        f"--domain {domain}"
                    ),
                    subject_ref=primary_path,
                    test_path=primary_path,
                    independent_validator=validator,
                ),
                _CoverageBlueprintV1(
                    row_id=f"ST12A-COMMAND::INDEPENDENT::{domain}",
                    category="validation_command_rows",
                    domain=domain,
                    predicate=f"python -B {validator}",
                    subject_ref=validator,
                    test_path=validator,
                    independent_validator=validator,
                ),
            )
        )
    for rule in SOURCE_CLAIM_BINDING_RULES:
        rows.append(
            _CoverageBlueprintV1(
                row_id=rule.binding_rule_id,
                category="source_claim_binding_rules",
                domain="source",
                predicate="exact-source-claim-binding-fail-closed",
                subject_ref=rule.binding_rule_id,
                test_path=_control_test_path("source", "fact-atomicity"),
                independent_validator=INDEPENDENT_VALIDATOR_BY_DOMAIN["source"],
            )
        )
    return tuple(rows)


def _coverage_predicate_passes(
    row: _CoverageBlueprintV1,
    *,
    domain_results: dict[str, bool] | None = None,
) -> bool:
    if not (REPO_ROOT / row.test_path).is_file():
        return False
    if not (REPO_ROOT / row.independent_validator).is_file():
        return False
    if row.category == "closure_rows":
        if domain_results is None:
            return validate_domain(row.domain).passed
        return domain_results[row.domain]
    if row.category == "repository_dispositions":
        return (
            row.subject_ref in PRODUCTION_CORE_PATHS
            and (REPO_ROOT / row.subject_ref).is_file()
        )
    if row.category == "parameter_policy_rows":
        try:
            resolved = ParameterPolicyResolverV1.resolve(row.subject_ref)
        except ComputationControlPlaneError:
            return False
        return resolved.parameter_id == row.subject_ref and resolved.used_day1_seed
    if row.category == "mathematical_specifications":
        return (
            row.subject_ref in IMPLEMENTATION_REGISTRY
            and row.subject_ref in MATH_IO_CONTRACTS
            and callable(IMPLEMENTATION_REGISTRY[row.subject_ref].callable)
        )
    if row.category == "independent_oracle_specifications":
        return any(
            oracle.oracle_id == row.subject_ref
            and oracle.math_spec_id in IMPLEMENTATION_REGISTRY
            and not oracle.production_import_allowed
            and not oracle.primary_validator_import_allowed
            for oracle in ORACLE_BY_MATH_ID.values()
        )
    if row.category == "golden_vectors_and_invariants":
        return any(
            vector.vector_id == row.subject_ref
            and vector.math_spec_id in IMPLEMENTATION_REGISTRY
            and vector.oracle_id
            == ORACLE_BY_MATH_ID[vector.math_spec_id].oracle_id
            and not vector.production_import_allowed
            for vector in GOLDEN_VECTOR_BY_MATH_ID.values()
        )
    if row.category in {"test_rows", "validation_command_rows"}:
        return True
    if row.category == "source_claim_binding_rules":
        return any(
            rule.binding_rule_id == row.subject_ref
            and not rule.source_pack_as_primary_allowed
            and not rule.broad_regex_or_alias_matching_allowed
            and not rule.codex_source_selection_allowed
            for rule in SOURCE_CLAIM_BINDING_RULES
        )
    return False


def build_tranche_a_coverage_manifest(
    *,
    predicate_overrides: MappingProxyType | dict[str, bool] | None = None,
) -> TrancheACoverageManifestV1:
    overrides = {} if predicate_overrides is None else dict(predicate_overrides)
    blueprint = _coverage_blueprint()
    domain_results = {
        domain: validate_domain(domain).passed
        for domain in INDEPENDENT_VALIDATOR_BY_DOMAIN
    }
    unexpected_overrides = set(overrides) - {row.row_id for row in blueprint}
    if unexpected_overrides:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            f"coverage override has unexpected rows: {sorted(unexpected_overrides)!r}",
        )
    rows = tuple(
        CoverageRowV1(
            row_id=row.row_id,
            category=row.category,
            domain=row.domain,
            predicate=row.predicate,
            subject_ref=row.subject_ref,
            test_path=row.test_path,
            independent_validator=row.independent_validator,
            terminal_status=(
                CoverageTerminalStatusV1.PASS
                if overrides.get(
                    row.row_id,
                    _coverage_predicate_passes(
                        row,
                        domain_results=domain_results,
                    ),
                )
                else CoverageTerminalStatusV1.FAIL
            ),
            owner=row.owner,
            producer=row.producer,
            consumer_refs=row.consumer_refs,
            no_orphan_disposition=row.no_orphan_disposition,
        )
        for row in blueprint
    )
    return validate_tranche_a_coverage_manifest(rows)


def validate_tranche_a_coverage_manifest(
    rows: tuple[CoverageRowV1, ...] | TrancheACoverageManifestV1,
) -> TrancheACoverageManifestV1:
    manifest = rows if isinstance(rows, TrancheACoverageManifestV1) else TrancheACoverageManifestV1(rows)
    expected = _coverage_blueprint()
    domain_results = {
        domain: validate_domain(domain).passed
        for domain in INDEPENDENT_VALIDATOR_BY_DOMAIN
    }
    expected_ids = tuple(row.row_id for row in expected)
    actual_ids = tuple(row.row_id for row in manifest.rows)
    if actual_ids != expected_ids:
        missing = tuple(row_id for row_id in expected_ids if row_id not in actual_ids)
        unexpected = tuple(row_id for row_id in actual_ids if row_id not in expected_ids)
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "coverage closure mismatch: "
            f"missing={missing!r}; unexpected={unexpected!r}",
        )
    for actual, blueprint in zip(manifest.rows, expected, strict=True):
        for name in (
            "row_id",
            "category",
            "domain",
            "predicate",
            "subject_ref",
            "test_path",
            "independent_validator",
            "owner",
            "producer",
            "consumer_refs",
            "no_orphan_disposition",
        ):
            if getattr(actual, name) != getattr(blueprint, name):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"coverage row metadata changed: {actual.row_id}:{name}",
                )
        if (
            actual.terminal_status is not CoverageTerminalStatusV1.PASS
            or not _coverage_predicate_passes(
                blueprint,
                domain_results=domain_results,
            )
        ):
            raise ContractValidationError(
                ReasonCode.VALIDATION_FAILED,
                f"coverage predicate failed: {actual.row_id}:{actual.predicate}",
            )
    return manifest


def _check(check_id: str, condition: bool, detail: str) -> ValidationCheckV1:
    return ValidationCheckV1(check_id, bool(condition), detail)


def validate_snapshot_contract(snapshot: FormulaRuntimeSnapshotV1) -> None:
    if snapshot.activated:
        raise ContractValidationError(
            ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
            "snapshot activation is outside Tranche A",
        )
    if len(snapshot.source_epoch_ids) != len(set(snapshot.source_epoch_ids)):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT, "snapshot source epochs must be unique"
        )


def validate_transaction_contract(transaction: TransactionEnvelopeV1) -> None:
    if transaction.committed:
        raise ContractValidationError(
            ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
            "durable commit is outside Tranche A",
        )
    if transaction.relative_output_path is not None:
        validate_relative_path(transaction.relative_output_path)


def validate_operation_contract_closure(
    operations: tuple[OperationContractV1, ...] = TRANCHE_A_OPERATION_CONTRACTS,
) -> tuple[OperationContractV1, ...]:
    if (
        not isinstance(operations, tuple)
        or len(operations) != len(TRANCHE_A_OPERATION_CONTRACTS)
        or any(
            not isinstance(operation, OperationContractV1)
            for operation in operations
        )
        or operations != TRANCHE_A_OPERATION_CONTRACTS
    ):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "operation closure must exactly equal the certified typed roster",
        )
    for attribute in (
        "operation_id",
        "operation_name",
        "request_type",
        "response_type",
    ):
        values = tuple(getattr(operation, attribute) for operation in operations)
        if len(set(values)) != len(operations):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                f"operation closure has a collision in {attribute}",
            )
    for operation in operations:
        if (
            operation.runtime_effect_authorized
            or operation.provider_effect_authorized
            or operation.capability_class
            is not OperationCapabilityClass.CONTRACT_DEFINITION_ONLY
            or operation.side_effect_class
            is not OperationSideEffectClass.PURE_OR_APPEND_ONLY_NON_PROVIDER_EFFECT
            or operation.schema_version != "1.4.0"
            or tuple(field.name for field in operation.request_fields)
            != tuple(field.name for field in fields(operation.request_model))
            or tuple(field.name for field in operation.response_fields)
            != tuple(field.name for field in fields(operation.response_model))
        ):
            raise ContractValidationError(
                ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                f"operation is not contract-only: {operation.operation_id}",
            )
    return operations


def _contract_only_models_are_valid() -> bool:
    configuration = ConfigurationEnvelopeV1(
        "ST12A_CONFIGURATION_CONTRACT",
        "1.0",
        ("ST10-PARAM::0083",),
    )
    health = HealthEnvelopeV1(
        "QKUComputationControlPlaneV1",
        HealthState.HEALTHY_CONTRACT,
        ("STATIC_CONTRACT_VALIDATED",),
    )
    supervision = SupervisionEnvelopeV1(
        "ST12A_SUPERVISION_CONTRACT",
        ("QKUComputationControlPlaneV1",),
    )
    fallback = FallbackEnvelopeV1(
        "ST12A_FALLBACK_CONTRACT",
        (ReasonCode.CAPABILITY_DENIED.value,),
        "NO_EFFECT_FAIL_CLOSED",
    )
    snapshot = FormulaRuntimeSnapshotV1(
        "ST12A_SNAPSHOT_CONTRACT",
        "ST12A_SPECIFICATION_CONTRACT",
        "1.1R1",
        "1.0",
        "CERTIFIED_STEP11_PARAMETER_POLICY",
        ("ST10-SOURCE::01",),
        SnapshotState.CONTRACT_ONLY,
    )
    transaction = TransactionEnvelopeV1(
        "ST12A_TRANSACTION_CONTRACT",
        snapshot.snapshot_id,
        "validation/st12a-contract-output.json",
    )
    receipt = ComputationExecutionReceiptV1(
        "ST12A_RECEIPT_CONTRACT",
        snapshot.specification_id,
        "MATH-01::1.1R1",
        "input-v1",
        '{"contract_only":true}',
    )
    operation = TRANCHE_A_OPERATION_CONTRACTS[0]
    moment = datetime(2026, 7, 24, 12, tzinfo=UTC)
    operation_context = ComputationContextKeyV1(
        "ST12A_OPERATION_CONTEXT",
        moment,
        moment,
        "ST10-SOURCE::01",
        "input-v1",
        timedelta(minutes=1),
    )
    request = operation.bind_request(
        request_id="ST12A_OPERATION_REQUEST",
        operation_name="resolve_identity",
        requested_at=moment,
        principal_id="ST12A_PRINCIPAL",
        capability_bundle_id="ST12A_DEFAULT_DENY_BUNDLE",
        context=operation_context,
        idempotency_key="ECONOMIC::ST12A_OPERATION_REQUEST",
        traceparent="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
        tracestate="",
        identity_query=TypedValueRecordV1(
            (
                TypedValueV1(
                    "formula_id",
                    TypedValueKindV1.TEXT,
                    "FORMULA_QKU",
                    "identifier",
                    "RP5C",
                ),
            )
        ),
    )
    response = operation.bind_response(
        request,
        response_id="ST12A_OPERATION_RESPONSE",
        operation_name="resolve_identity",
        request_id=request.request_id,
        completed_at=moment,
        status=OperationStatusV1.SUCCEEDED,
        context=operation_context,
        warnings=(),
        blocker_codes=(),
        receipt_refs=("RP5C_IDENTITY_00000001",),
        traceparent=request.traceparent,
        tracestate=request.tracestate,
        identity_resolution=IdentityResolutionV1(
            "RP5C_IDENTITY_00000001",
            "RETURN_CANONICAL_IDENTITY_VIEW",
            ("RP5C_IDENTITY_00000001",),
        ),
    )
    validate_snapshot_contract(snapshot)
    validate_transaction_contract(transaction)
    validate_operation_contract_closure()
    return (
        not configuration.mutable_runtime
        and health.state is HealthState.HEALTHY_CONTRACT
        and not supervision.process_supervision_enabled
        and not fallback.permits_new_writes
        and not snapshot.activated
        and not transaction.committed
        and isinstance(request, OperationRequestEnvelopeV1)
        and isinstance(response, OperationResponseEnvelopeV1)
        and operation.request_json(request)
        and operation.response_json(response)
        and not any(
            (
                receipt.provider_effect,
                receipt.private_state_effect,
                receipt.replay_or_paper_effect,
                receipt.order_effect,
                receipt.qpu_effect,
            )
        )
    )


def _package_ast() -> tuple[tuple[Path, ast.Module], ...]:
    trees: list[tuple[Path, ast.Module]] = []
    for relative in PRODUCTION_CORE_PATHS:
        path = REPO_ROOT / relative
        trees.append(
            (
                path,
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path)),
            )
        )
    return tuple(trees)


def _no_runtime_topology() -> bool:
    forbidden_modules = {
        "asyncio",
        "http",
        "multiprocessing",
        "socket",
        "sqlite3",
        "subprocess",
        "threading",
        "urllib",
    }
    forbidden_file_names = {
        "backup.py",
        "database.py",
        "runtime.py",
        "service.py",
        "supervision.py",
    }
    package = REPO_ROOT / Path(PRODUCTION_CORE_PATHS[0]).parent
    if forbidden_file_names & {path.name for path in package.glob("*.py")}:
        return False
    for _, tree in _package_ast():
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(
                alias.name.split(".", 1)[0] in forbidden_modules
                for alias in node.names
            ):
                return False
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.split(".", 1)[0] in forbidden_modules
            ):
                return False
    return True


def _no_dynamic_import_or_unsafe_deserialization() -> bool:
    forbidden_names = {"__import__", "compile", "eval", "exec"}
    forbidden_attributes = {
        ("importlib", "import_module"),
        ("pickle", "load"),
        ("pickle", "loads"),
    }
    for _, tree in _package_ast():
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id in forbidden_names:
                return False
            if (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and (node.func.value.id, node.func.attr) in forbidden_attributes
            ):
                return False
    return True


def _parameter_seed_resolution_valid() -> bool:
    for policy in PARAMETER_POLICIES:
        resolved = ParameterPolicyResolverV1.resolve(policy.parameter_id)
        if (
            resolved.parameter_id != policy.parameter_id
            or resolved.parameter_audit_id != policy.parameter_audit_id
            or resolved.parameter_symbol != policy.parameter_symbol
            or resolved.value
            != policy.effective_day1_seed_value_or_resolution_rule
            or resolved.unit_or_basis != policy.effective_unit_or_basis
            or resolved.resolution_class != policy.effective_resolution_class
            or resolved.authority_class
            != policy.effective_default_authority_class
            or resolved.fallback
            != policy.effective_fallback_behavior_when_value_unavailable
            or resolved.owner_editability
            != policy.effective_owner_dashboard_editability_class
            or not resolved.used_day1_seed
        ):
            return False
    return True


def _existing_owner_views_valid() -> bool:
    identity = RP5CIdentityAdapterV1(REPO_ROOT).get_formula("FORMULA_QKU")
    plugins = PR162EPluginAdapterV1(REPO_ROOT).load_families()
    quantum = PR162EQuantumAdapterV1(REPO_ROOT).load_mappings(
        QuantumModelKind.QUBO
    )
    projections = ExistingOwnerProjectionAdapterV1(REPO_ROOT)
    projection_views = (
        projections.load_readiness(),
        projections.load_pretrade(),
        projections.load_svc(),
        projections.load_agent_orch(),
    )
    source_scheduler = SourceRevalidationSchedulerAdapterV1.load_view()
    snapshot_boundary = LatencyHotPathSnapshotBoundaryAdapterV1.load_view()
    legacy = load_legacy_formula_comparators()
    if not plugins or not quantum or not legacy:
        return False
    consumed_owner_ids = {
        identity.source_owner,
        plugins[0].source_owner,
        quantum[0].source_owner,
        *(view.owner_id for view in projection_views),
        source_scheduler.owner_id,
        snapshot_boundary.owner_id,
        legacy[0].source_owner,
    }
    return (
        consumed_owner_ids == set(OWNER_IDS)
        and len(legacy) == 7
        and all(not view.exact_decimal_alias for view in legacy)
    )


def _architecture_checks() -> tuple[ValidationCheckV1, ...]:
    ids = tuple(IMPLEMENTATION_REGISTRY)
    return (
        _check("ARCH_PRODUCTION_CORE_19", len(PRODUCTION_CORE_PATHS) == 19, "19 paths"),
        _check("ARCH_OWNER_MAP_10", len(OWNER_IDS) == 10, "10 existing owners"),
        _check("ARCH_IMPLEMENTATION_REGISTRY_19", ids == MATH_IDS, repr(ids)),
        _check(
            "ARCH_MATH_SPECIFICATIONS_19_VALUE_LEVEL",
            all(
                record.specification_metadata.certified_formula
                and record.specification_metadata.domain_and_fail_closed_guards
                and record.specification_metadata.implementation_algorithm
                and record.specification_metadata.mandatory_comparator_or_reconciliation
                and record.specification_metadata.precision_and_rounding_policy
                and record.specification_metadata.optional_library_adapter_policy
                and record.specification_metadata.tie_break_policy
                for record in IMPLEMENTATION_REGISTRY.values()
            ),
            "all 19 implementations carry complete frozen math metadata",
        ),
        _check(
            "ARCH_PARAMETER_POLICY_135",
            len(PARAMETER_POLICIES) == 135,
            f"{len(PARAMETER_POLICIES)} rows",
        ),
        _check(
            "ARCH_ORACLE_PACK_19",
            tuple(ORACLE_BY_MATH_ID) == MATH_IDS
            and tuple(GOLDEN_VECTOR_BY_MATH_ID) == MATH_IDS,
            "oracle and vector ids align",
        ),
        _check(
            "ARCH_SINGLE_REGISTRY",
            len({id(IMPLEMENTATION_REGISTRY)}) == 1,
            "one immutable implementation registry",
        ),
        _check(
            "ARCH_PARAMETER_SEEDS_135_VALUE_LEVEL",
            _parameter_seed_resolution_valid(),
            "all 135 exact seed rows resolve with frozen metadata",
        ),
        _check(
            "ARCH_EXISTING_OWNERS_10_CONSUMED",
            _existing_owner_views_valid(),
            "all ten canonical owners are consumed through immutable views",
        ),
        _check(
            "ARCH_OPERATION_CONTRACTS_15",
            len(validate_operation_contract_closure()) == 15,
            "15 complete collision-free data-only operation contracts",
        ),
    )


def _operations_checks() -> tuple[ValidationCheckV1, ...]:
    authority = CapabilityEnvelopeV1()
    assert_no_effect_authority(authority)
    return (
        _check(
            "OPS_AUTHORITY_ALL_FALSE",
            not any(getattr(authority, item.name) for item in fields(authority)),
            "all capabilities are false",
        ),
        _check(
            "OPS_CONTRACT_ONLY",
            _contract_only_models_are_valid(),
            "typed configuration, health, supervision, fallback, snapshot, "
            "transaction, and receipt contracts deny effects",
        ),
        _check(
            "OPS_NO_RUNTIME_TOPOLOGY",
            _no_runtime_topology(),
            "AST and exact package names contain no runtime topology",
        ),
    )


def _quantum_checks() -> tuple[ValidationCheckV1, ...]:
    quantum_ids = tuple(value for value in MATH_IDS if int(value.split("-")[1]) >= 46)
    optional_metadata = {
        row.currentization_id: json.loads(row.exact_facts_json)
        for row in SOURCE_CURRENTIZATION_OVERLAYS
        if row.currentization_id.startswith("ST12A-CURR-DEPENDENCY")
    }
    return (
        _check(
            "QUANTUM_MATH_4",
            quantum_ids == ("MATH-46", "MATH-47", "MATH-48", "MATH-49"),
            repr(quantum_ids),
        ),
        _check(
            "QUANTUM_OPTIONAL_METADATA_ONLY",
            "ST12A-CURR-DEPENDENCY-002" in optional_metadata
            and "ST12A-CURR-DEPENDENCY-003" in optional_metadata,
            "Qiskit Optimization and D-Wave remain metadata only",
        ),
        _check(
            "QUANTUM_NO_BACKEND",
            all(
                not entry.provider_or_qpu_effect_allowed
                for math_id, entry in IMPLEMENTATION_REGISTRY.items()
                if math_id in quantum_ids
            ),
            "all quantum entries deny backend effects",
        ),
    )


def _security_checks() -> tuple[ValidationCheckV1, ...]:
    unsafe_paths = (
        "../escape",
        "/absolute",
        r"C:\absolute",
        r"folder\..\escape",
        "folder//file",
        "folder/./file",
        "folder/NUL.txt",
        "folder/trailing.",
        "folder/stream:name",
    )
    rejected = 0
    for path in unsafe_paths:
        try:
            validate_relative_path(path)
        except ComputationControlPlaneError:
            rejected += 1
    return (
        _check("SECURITY_PATH_TRAVERSAL", rejected == len(unsafe_paths), str(rejected)),
        _check(
            "SECURITY_DEFAULT_DENY",
            not any(
                getattr(CapabilityEnvelopeV1(), item.name)
                for item in fields(CapabilityEnvelopeV1())
            ),
            "all authority fields false",
        ),
        _check(
            "SECURITY_NO_DYNAMIC_IMPORT",
            _no_dynamic_import_or_unsafe_deserialization(),
            "AST contains no dynamic import, eval, exec, or unsafe deserialization",
        ),
    )


def _source_checks() -> tuple[ValidationCheckV1, ...]:
    scheduler = SourceRevalidationSchedulerAdapterV1.load_view()
    return (
        _check(
            "SOURCE_CERTIFIED_29",
            len(CERTIFIED_SOURCE_STATES) == 29,
            f"{len(CERTIFIED_SOURCE_STATES)} rows",
        ),
        _check(
            "SOURCE_OVERLAYS_7",
            len(SOURCE_CURRENTIZATION_OVERLAYS) == 7,
            f"{len(SOURCE_CURRENTIZATION_OVERLAYS)} rows",
        ),
        _check(
            "SOURCE_ENDPOINT_WINDOWS_SEPARATE",
            len(POLYMARKET_ENDPOINT_LIMITS) == 6
            and all(item.burst_window_seconds == 10 for item in POLYMARKET_ENDPOINT_LIMITS)
            and all(
                item.sustained_window_seconds == 600
                for item in POLYMARKET_ENDPOINT_LIMITS
            ),
            "6 endpoint/window pairs",
        ),
        _check(
            "SOURCE_SIGNER_BUCKETS_SEPARATE",
            len(POLYMARKET_SIGNER_BUCKETS) == 2
            and all(item.scope == "SIGNER" for item in POLYMARKET_SIGNER_BUCKETS),
            "2 signer-scoped policies",
        ),
        _check(
            "SOURCE_RETRYING_PENDING",
            classify_trade_lifecycle("RETRYING").value == "PENDING",
            "RETRYING is nonterminal",
        ),
        _check(
            "SOURCE_FAK_FOK_TRADE_IDS",
            FAK_FOK_RESPONSE_CONTRACT.successful_response_field == "tradeIDs"
            and not FAK_FOK_RESPONSE_CONTRACT.inline_transaction_hashes_expected
            and not FAK_FOK_RESPONSE_CONTRACT.accepted_order_resubmission_allowed,
            FAK_FOK_RESPONSE_CONTRACT.custom_rest_followup,
        ),
        _check(
            "SOURCE_REVALIDATION_OWNER_VIEW",
            scheduler.live_critical_interval == "P1D"
            and scheduler.low_risk_interval == "P7D"
            and not scheduler.network_retrieval_allowed,
            "existing scheduler policy consumed without execution",
        ),
    )


_DOMAIN_CHECKS: dict[str, Callable[[], tuple[ValidationCheckV1, ...]]] = {
    "architecture": _architecture_checks,
    "operations": _operations_checks,
    "quantum": _quantum_checks,
    "security": _security_checks,
    "source": _source_checks,
}


def validate_domain(domain: str) -> ValidationReportV1:
    if not isinstance(domain, str) or not domain:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "validation domain must be nonempty text",
        )
    try:
        checks = _DOMAIN_CHECKS[domain]()
    except KeyError as exc:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT, f"unknown validation domain: {domain}"
        ) from exc
    report = ValidationReportV1(domain, checks)
    report.assert_passed()
    return report


def _inputs(math_id: str) -> dict[str, object]:
    return json.loads(GOLDEN_VECTOR_BY_MATH_ID[math_id].inputs_json)


def evaluate_golden_vector(math_id: str) -> dict[str, object]:
    """Primary value evaluator; independent validators must not call this helper."""

    call = get_math_callable(math_id)
    values = _inputs(math_id)
    if math_id == "MATH-01":
        return {"p_market": str(call(values["contract_price"], values["payout_per_winning_contract"]))}
    if math_id == "MATH-02":
        return {"edge_probability": call(values["calibrated_model_probability"], values["market_implied_probability"])}
    if math_id == "MATH-03":
        return {"mid": str(call(values["best_bid"], values["best_ask"]))}
    if math_id == "MATH-04":
        return {"spread": str(call(values["best_bid"], values["best_ask"]))}
    if math_id == "MATH-05":
        return {"relative_spread": str(call(values["best_bid"], values["best_ask"]))}
    if math_id == "MATH-06":
        result = call(
            values["quantity"], values["p"], values["win_cash"], values["lose_cash"],
            values["acquisition_cost"], values["fees"], values["expected_slippage"],
            values["expected_impact"],
        )
        return {"expected_net_cash": str(result.normalize())}
    if math_id == "MATH-07":
        result = call(
            values["probabilities"],
            values["payoffs"],
            QuantityAndFrictionTermsV1(
                Decimal(str(values["quantity"])),
                Decimal(str(values["acquisition_cost"])),
                Decimal(str(values["fees"])),
                Decimal(str(values["expected_slippage"])),
                Decimal(str(values["expected_impact"])),
            ),
        )
        return {"expected_net_cash": str(result.normalize())}
    if math_id == "MATH-08":
        return {"brier_score": str(Decimal(str(call(values["p"], values["y"]))).normalize())}
    if math_id == "MATH-09":
        return {"log_loss": call(values["p"], values["y"], clip_epsilon=values["clip_epsilon"])}
    if math_id == "MATH-10":
        ordered_bins = tuple(
            sorted(values["bins"], key=lambda item: item["mean_confidence"])
        )
        probabilities: list[float] = []
        outcomes: list[int] = []
        means = tuple(float(item["mean_confidence"]) for item in ordered_bins)
        for item in ordered_bins:
            count = int(item["count"])
            successes = float(item["empirical_frequency"]) * count
            if not successes.is_integer():
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    "golden ECE bin frequency cannot be expanded exactly",
                )
            probabilities.extend([float(item["mean_confidence"])] * count)
            outcomes.extend(
                [1] * int(successes) + [0] * (count - int(successes))
            )
        edges = (
            0.0,
            *(
                (left + right) / 2.0
                for left, right in zip(means, means[1:])
            ),
            1.0,
        )
        return {"ece": call(probabilities, outcomes, edges)}
    if math_id == "MATH-11":
        result = call(
            values["successes"],
            values["trials"],
            confidence=values["confidence"],
        )
        return {"lower": result.lower, "upper": result.upper}
    if math_id in {"MATH-12", "MATH-13"}:
        result = call(values["p_values"], values["q"])
        return {
            "largest_rank": result.largest_rank,
            "rejected_original_indices": list(result.rejected_original_indices),
        }
    if math_id == "MATH-14":
        result = call(
            values["series"],
            values["expected_block_length"],
            seed=values["seed"],
            replicates=values["replicates"],
        )
        second = call(
            values["series"],
            values["expected_block_length"],
            seed=values["seed"],
            replicates=values["replicates"],
        )
        return {
            "interval_contains_sample_mean": result.lower <= result.sample_mean <= result.upper,
            "same_seed_reproducible": result == second,
        }
    if math_id == "MATH-15":
        result = call(
            values["loss_differentials"],
            sign_convention=(
                BenchmarkSignConvention.BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS
            ),
            seed=values["seed"],
            replicates=values["replicates"],
        )
        return {"p_value": result.p_value, "reject": result.reject}
    if math_id == "MATH-46":
        terms = tuple(
            QuboUpperTermV1(item["i"], item["j"], item["value"])
            for item in values["upper_terms"]
        )
        result = call(
            values["diagonal"],
            terms,
            values["offset"],
            values["x"],
            scaling_receipt=ObjectiveScalingReceiptV1(
                "GOLDEN::MATH-46::ORIGINAL_OBJECTIVE",
                "normalized objective",
                "normalized objective",
                1.0,
            ),
        )
        return {"energy": result.energy}
    if math_id == "MATH-47":
        source = values["qubo"]
        model = QuboModelV1(
            tuple(source["diagonal"]),
            tuple(
                QuboUpperTermV1(item["i"], item["j"], item["value"])
                for item in source["upper_terms"]
            ),
            source["offset"],
            ObjectiveScalingReceiptV1(
                "GOLDEN::MATH-47::ORIGINAL_OBJECTIVE",
                "normalized objective",
                "normalized objective",
                1.0,
            ),
        )
        ising = compute_math_47_qubo_to_ising_transform(model)
        assignments = tuple(product((0, 1), repeat=len(model.diagonal)))
        parity = all(
            math.isclose(
                model.energy(binary),
                ising.energy(tuple(1 - 2 * value for value in binary)),
                rel_tol=0.0,
                abs_tol=ising.energy_parity_tolerance,
            )
            for binary in assignments
        )
        return {
            "all_binary_assignments_energy_equal_after_ising_transform": parity,
            "assignment_count": len(assignments),
        }
    if math_id == "MATH-48":
        variables = (
            QuadraticVariableV1("x", VariableDomain.BINARY, 0, 1),
            QuadraticVariableV1("y", VariableDomain.BINARY, 0, 1),
        )
        result = call(
            variables,
            (LinearTermV1("x", 1), LinearTermV1("y", 1)),
            (),
            (
                QuadraticConstraintV1(
                    "x+y<=1",
                    (LinearTermV1("x", 1), LinearTermV1("y", 1)),
                    (),
                    "<=",
                    1,
                ),
            ),
            objective_sense=ObjectiveSense.MAXIMIZE,
        )
        return {"all_returned_solutions_feasible": result.feasible, "optimal_objective": result.objective}
    if math_id == "MATH-49":
        variables = tuple(
            DiscreteVariableV1(name, tuple(cases))
            for name, cases in sorted(values["discrete_variables"].items())
        )
        linear = tuple(
            DiscreteLinearBiasV1(
                next(item.name for item in variables if case in item.cases),
                case,
                bias,
            )
            for case, bias in sorted(values["linear_biases"].items())
        )
        result = call(variables, linear, ())
        return {
            "minimum_energy_assignment": dict(result.assignment),
            "one_case_per_variable": result.one_case_per_variable,
        }
    raise ContractValidationError(
        ReasonCode.UNKNOWN_IMPLEMENTATION, f"unhandled golden vector: {math_id}"
    )


def compare_golden_vector(math_id: str) -> bool:
    actual = evaluate_golden_vector(math_id)
    expected = json.loads(GOLDEN_VECTOR_BY_MATH_ID[math_id].expected_json)
    policy = GOLDEN_VECTOR_BY_MATH_ID[math_id].comparison_policy
    if policy in {
        "EXACT_DECIMAL",
        "DECIMAL_CONTEXT_PRECISION_34_EXACT_RESULT",
        "EXACT_ORDER_AND_INDEX_SET",
        "BOOLEAN_INVARIANTS",
        "ENUMERATION_INVARIANT",
        "BRUTE_FORCE_ENUMERATION",
        "EXACT_DISCRETE_ENUMERATION",
    }:
        return actual == expected
    tolerance = 1e-12 if policy == "ABS_TOL_1E-12" else 1e-15
    if set(actual) != set(expected):
        return False
    return all(
        actual[key] == expected[key]
        if isinstance(expected[key], bool)
        else math.isclose(
            float(actual[key]), float(expected[key]), rel_tol=0.0, abs_tol=tolerance
        )
        for key in expected
    )


def validate_all_golden_vectors() -> ValidationReportV1:
    checks = tuple(
        _check(
            f"GOLDEN_{math_id}",
            compare_golden_vector(math_id),
            GOLDEN_VECTOR_BY_MATH_ID[math_id].comparison_policy,
        )
        for math_id in MATH_IDS
    )
    report = ValidationReportV1("golden", checks)
    report.assert_passed()
    return report


def validate_production_core_paths(repo_root: str | Path) -> ValidationReportV1:
    root = Path(repo_root)
    checks = tuple(
        _check(
            f"PATH_{index:02d}",
            (root / relative).is_file(),
            relative,
        )
        for index, relative in enumerate(PRODUCTION_CORE_PATHS, 1)
    )
    report = ValidationReportV1("repository", checks)
    report.assert_passed()
    return report
