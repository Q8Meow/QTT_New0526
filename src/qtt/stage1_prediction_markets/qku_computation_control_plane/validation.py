"""Cross-contract, authority, boundary, and value-level validation."""

from __future__ import annotations

import ast
from dataclasses import dataclass, fields
from decimal import Decimal
from itertools import product
import json
import math
from pathlib import Path
from typing import Callable

from .authority import CapabilityEnvelopeV1, assert_no_effect_authority
from .errors import ComputationControlPlaneError, ContractValidationError, ReasonCode
from .implementation_registry import (
    DiscreteLinearBiasV1,
    DiscreteVariableV1,
    IMPLEMENTATION_REGISTRY,
    load_legacy_formula_comparators,
    LinearTermV1,
    ObjectiveScalingReceiptV1,
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
    ComputationExecutionReceiptV1,
    ConfigurationEnvelopeV1,
    ContractFieldV1,
    FallbackEnvelopeV1,
    FormulaRuntimeSnapshotV1,
    HealthEnvelopeV1,
    HealthState,
    LatencyHotPathSnapshotBoundaryAdapterV1,
    ObjectiveSense,
    OperationCapabilityClass,
    OperationContractV1,
    OperationFailureEnvelopeV1,
    OperationRequestEnvelopeV1,
    OperationResponseEnvelopeV1,
    OperationSideEffectClass,
    SnapshotState,
    SupervisionEnvelopeV1,
    TransactionEnvelopeV1,
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

REPO_ROOT = Path(__file__).resolve().parents[4]

TRANCHE_A_OPERATION_CONTRACTS = tuple(
    OperationContractV1(
        operation_id,
        request_contract,
        response_contract,
        failure_contract,
        request_fields=(
            ContractFieldV1("request_id", "str"),
            ContractFieldV1("contract_version", "str"),
            ContractFieldV1("payload_json", f"{request_contract}DataV1"),
        ),
        response_fields=(
            ContractFieldV1("request_id", "str"),
            ContractFieldV1("result_json", f"{response_contract}DataV1"),
        ),
        failure_reason_codes=(failure_reason,),
    )
    for (
        operation_id,
        request_contract,
        response_contract,
        failure_contract,
        failure_reason,
    ) in (
        (
            "RESOLVE_IDENTITY",
            "ResolveIdentityRequestV1",
            "ResolveIdentityResponseV1",
            "ResolveIdentityFailureV1",
            ReasonCode.OWNER_DATA_MISSING,
        ),
        (
            "RESOLVE_PARAMETER_POLICY",
            "ResolveParameterPolicyRequestV1",
            "ResolveParameterPolicyResponseV1",
            "ResolveParameterPolicyFailureV1",
            ReasonCode.PARAMETER_OUT_OF_POLICY,
        ),
        (
            "RESOLVE_BINDING_PROFILE",
            "ResolveBindingProfileRequestV1",
            "ResolveBindingProfileResponseV1",
            "ResolveBindingProfileFailureV1",
            ReasonCode.INVALID_CONTRACT,
        ),
        (
            "COMPILE_DEPENDENCY_DAG",
            "CompileDependencyDagRequestV1",
            "CompileDependencyDagResponseV1",
            "CompileDependencyDagFailureV1",
            ReasonCode.DEPENDENCY_CYCLE,
        ),
        (
            "RESOLVE_IMPLEMENTATION",
            "ResolveImplementationRequestV1",
            "ResolveImplementationResponseV1",
            "ResolveImplementationFailureV1",
            ReasonCode.UNKNOWN_IMPLEMENTATION,
        ),
        (
            "VALIDATE_NUMERIC_CONTEXT",
            "ValidateNumericContextRequestV1",
            "ValidateNumericContextResponseV1",
            "ValidateNumericContextFailureV1",
            ReasonCode.INVALID_NUMERIC_INPUT,
        ),
        (
            "VALIDATE_SOURCE_POLICY",
            "ValidateSourcePolicyRequestV1",
            "ValidateSourcePolicyResponseV1",
            "ValidateSourcePolicyFailureV1",
            ReasonCode.SOURCE_CONFLICT,
        ),
        (
            "VALIDATE_SOURCE_RIGHTS",
            "ValidateSourceRightsRequestV1",
            "ValidateSourceRightsResponseV1",
            "ValidateSourceRightsFailureV1",
            ReasonCode.SOURCE_RIGHTS_BLOCKED,
        ),
        (
            "VALIDATE_ORACLE_CONTRACT",
            "ValidateOracleContractRequestV1",
            "ValidateOracleContractResponseV1",
            "ValidateOracleContractFailureV1",
            ReasonCode.ORACLE_NOT_INDEPENDENT,
        ),
        (
            "VALIDATE_GOLDEN_VECTOR",
            "ValidateGoldenVectorRequestV1",
            "ValidateGoldenVectorResponseV1",
            "ValidateGoldenVectorFailureV1",
            ReasonCode.VALIDATION_FAILED,
        ),
        (
            "COMPILE_SPECIFICATION_ENVELOPE",
            "CompileSpecificationEnvelopeRequestV1",
            "CompileSpecificationEnvelopeResponseV1",
            "CompileSpecificationEnvelopeFailureV1",
            ReasonCode.INCOMPLETE_CONTRACT,
        ),
        (
            "VALIDATE_SNAPSHOT",
            "ValidateSnapshotRequestV1",
            "ValidateSnapshotResponseV1",
            "ValidateSnapshotFailureV1",
            ReasonCode.STALE_CONTEXT,
        ),
        (
            "VALIDATE_TRANSACTION",
            "ValidateTransactionRequestV1",
            "ValidateTransactionResponseV1",
            "ValidateTransactionFailureV1",
            ReasonCode.PATH_UNSAFE,
        ),
        (
            "DESCRIBE_RUNTIME_BOUNDARIES",
            "DescribeRuntimeBoundariesRequestV1",
            "DescribeRuntimeBoundariesResponseV1",
            "DescribeRuntimeBoundariesFailureV1",
            ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
        ),
        (
            "VALIDATE_AUTHORITY_ENVELOPE",
            "ValidateAuthorityEnvelopeRequestV1",
            "ValidateAuthorityEnvelopeResponseV1",
            "ValidateAuthorityEnvelopeFailureV1",
            ReasonCode.CAPABILITY_DENIED,
        ),
    )
)


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
        or len(operations) != 15
        or any(
            not isinstance(operation, OperationContractV1)
            for operation in operations
        )
    ):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "operation closure requires exactly 15 typed contracts",
        )
    for attribute in (
        "operation_id",
        "input_contract",
        "output_contract",
        "failure_contract",
    ):
        values = tuple(getattr(operation, attribute) for operation in operations)
        if len(set(values)) != 15:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                f"operation closure has a collision in {attribute}",
            )
    for operation in operations:
        if (
            operation.runtime_effect_authorized
            or operation.capability_class
            is not OperationCapabilityClass.NONE_CONTRACT_ONLY
            or operation.side_effect_class is not OperationSideEffectClass.NONE
            or tuple(field.name for field in operation.request_fields)
            != ("request_id", "contract_version", "payload_json")
            or tuple(field.name for field in operation.response_fields)
            != ("request_id", "result_json")
            or not operation.failure_reason_codes
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
    request = operation.bind_request(
        request_id="ST12A_OPERATION_REQUEST",
        contract_version="1.0",
        payload_json='{"formula_id":"FORMULA_QKU"}',
    )
    response = operation.bind_response(
        request,
        result_json='{"contract_only":true}',
    )
    failure = operation.bind_failure(
        request,
        reason_code=operation.failure_reason_codes[0],
        detail="fixture-only fail-closed envelope",
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
        and isinstance(failure, OperationFailureEnvelopeV1)
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
            values["probabilities"], values["payoffs"], values["quantity"],
            values["acquisition_cost"], values["fees"], values["expected_slippage"],
            values["expected_impact"],
        )
        return {"expected_net_cash": str(result.normalize())}
    if math_id == "MATH-08":
        return {"brier_score": str(Decimal(str(call(values["probability"], values["outcome"]))).normalize())}
    if math_id == "MATH-09":
        return {"log_loss": call(values["probability"], values["outcome"], clip_epsilon=values["clip_epsilon"])}
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
        result = call(values["successes"], values["trials"], z=values["z"])
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
            values["mean_block_length"],
            seed=values["seed"],
            replicates=values["replicates"],
        )
        second = call(
            values["series"],
            values["mean_block_length"],
            seed=values["seed"],
            replicates=values["replicates"],
        )
        return {
            "interval_contains_sample_mean": result.lower <= result.sample_mean <= result.upper,
            "same_seed_reproducible": result == second,
        }
    if math_id == "MATH-15":
        result = call(
            values["differentials"],
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
