"""Cross-contract, authority, boundary, and value-level validation."""

from __future__ import annotations

import ast
from collections import Counter
from dataclasses import dataclass, fields, replace
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
from .bindings import (
    SOURCE_CLAIM_BINDING_RULES,
    TRANCHE_A_SOURCE_CLAIM_BINDING_RULES,
    TRANCHE_B_SOURCE_CLAIM_BINDING_RULES,
)
from .context import ComputationContextKeyV1
from .freshness import (
    DeadlineBudgetV1,
    DeadlineResolverV1,
    FreshnessPolicyV1,
    FreshnessResolverV1,
    FreshnessStateV1,
)
from .input_resolver import ContextualInputValueV1
from .errors import ComputationControlPlaneError, ContractValidationError, ReasonCode
from .implementation_registry import (
    DiscreteLinearBiasV1,
    DiscreteVariableV1,
    IMPLEMENTATION_REGISTRY,
    TRANCHE_A_MATH_IDS,
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
from .oracle_contracts import (
    GOLDEN_VECTOR_BY_MATH_ID,
    ORACLE_BY_MATH_ID,
    TRANCHE_A_ORACLE_PACK,
    TRANCHE_B_ORACLE_COVERAGE_ROWS,
)
from .parameter_policy import (
    PARAMETER_POLICIES,
    STEP12_PARAMETER_POLICIES,
    TRANCHE_B_PARAMETER_POLICIES,
    ParameterPolicyResolverV1,
)
from .plugin_adapter import PR162EPluginAdapterV1
from .protocols import ExistingOwnerProjectionAdapterV1
from .quantum_adapter import (
    PR162EQuantumAdapterV1,
    QuantumModelKind,
    QuantumStructuralReadinessProjectionV1,
)
from .service import (
    AGENT_DUTY_ROUTES,
    INSTITUTIONAL_FEATURE_SOCKETS,
    QKUComputationControlPlaneServiceV1,
    StructuredResolutionExplanationV1,
    TRANCHE_B_SERVICE_BINDINGS,
    output_schema_ref,
)
from .point_in_time import (
    PointInTimeEvidenceV1,
    PointInTimeFieldClassV1,
)
from .stack_resolver import StackApplicabilityContextV1
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
from .specification import (
    MATH_IO_CONTRACTS,
    TRANCHE_B_MATH_SPECIFICATIONS,
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

_TRANCHE_B_MACHINE_ROWS_JSON = r'''{"closure_rows":[{"authority_owner":"RuntimePlatformV1","canonical_implementation_owner":"QKUComputationControlPlaneV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-LATENCY::006","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-LATENCY::006","codex_online_research_allowed":false,"control_id":"ST11-LATENCY::006","control_slug":"budget-ledger","domain":"latency","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/clocks.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/latency_budget.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/deadlines.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/telemetry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/stale_policy.py","tests/stage1_prediction_markets/qku_computation_control_plane/latency/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/latency/test_budget_ledger.py","tools/independent_validate_qku_computation_control_plane_latency.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain latency","python tools/independent_validate_qku_computation_control_plane_latency.py"],"implementation_specification":{"algorithm_or_rule":"Assign budgets to every dependency and prove the sum plus safety margin fits the decision TTL. Use distinct monotonic and wall clocks; normalize units; decompose queue, compute and provider latency; enforce TTL, deadlines and skew; treat traces as correlation only; reject stale results or use preapproved fast classical fallback.","authority_boundary":"IMPLEMENTATION_OWNER=QKUComputationControlPlaneV1; AUTHORITY_OWNER=RuntimePlatformV1; INDEPENDENT_AUDITOR=IndependentLatencyAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"RuntimePlatformV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"consume_existing_owner_refs":["RuntimePlatformV1","RP5G_LATENCY","HOTPATH_FOUNDATIONS"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"STALE_REJECT_CANCEL_DEADLINE_OR_USE_PREAPPROVED_FAST_CLASSICAL_FALLBACK","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/clocks.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/latency_budget.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/deadlines.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/telemetry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/stale_policy.py","tests/stage1_prediction_markets/qku_computation_control_plane/latency/"],"implementation_disposition":"IMPLEMENT_MONOTONIC_CLOCK_TTL_DEADLINE_AND_TELEMETRY_BOUNDARY_IN_CONTROL_PLANE; NO_LLM_OR_QPU_HOTPATH","implementation_owner":"QKUComputationControlPlaneV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentLatencyAuditorV1","independent_validator_owner":"IndependentLatencyAuditorV1","input_contract":"monotonic and wall-clock timestamps, deadlines, TTLs, queue and provider timing","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"unit-normalized latency decomposition, percentile/SLO, stale/deadline decisions and correlation-only traces","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_LATENCY_BUDGET_LEDGER_PASS","ST12_LATENCY_BUDGET_LEDGER_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_FORMAL_DOMAIN_DERIVATION","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/latency/test_budget_ledger.py","tools/independent_validate_qku_computation_control_plane_latency.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain latency","python tools/independent_validate_qku_computation_control_plane_latency.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentLatencyAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::099"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"RuntimePlatformV1","canonical_implementation_owner":"QKUComputationControlPlaneV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-LATENCY::007","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-LATENCY::007","codex_online_research_allowed":false,"control_id":"ST11-LATENCY::007","control_slug":"ttl-and-edge-decay","domain":"latency","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/clocks.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/latency_budget.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/deadlines.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/telemetry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/stale_policy.py","tests/stage1_prediction_markets/qku_computation_control_plane/latency/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/latency/test_ttl_and_edge_decay.py","tools/independent_validate_qku_computation_control_plane_latency.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain latency","python tools/independent_validate_qku_computation_control_plane_latency.py"],"implementation_specification":{"algorithm_or_rule":"Verify source TTL, snapshot TTL, result TTL, edge half-life, decision age, and submit delay are explicit. Use distinct monotonic and wall clocks; normalize units; decompose queue, compute and provider latency; enforce TTL, deadlines and skew; treat traces as correlation only; reject stale results or use preapproved fast classical fallback.","authority_boundary":"IMPLEMENTATION_OWNER=QKUComputationControlPlaneV1; AUTHORITY_OWNER=RuntimePlatformV1; INDEPENDENT_AUDITOR=IndependentLatencyAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"RuntimePlatformV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"consume_existing_owner_refs":["RuntimePlatformV1","RP5G_LATENCY","HOTPATH_FOUNDATIONS"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"STALE_REJECT_CANCEL_DEADLINE_OR_USE_PREAPPROVED_FAST_CLASSICAL_FALLBACK","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/clocks.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/latency_budget.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/deadlines.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/telemetry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/stale_policy.py","tests/stage1_prediction_markets/qku_computation_control_plane/latency/"],"implementation_disposition":"IMPLEMENT_MONOTONIC_CLOCK_TTL_DEADLINE_AND_TELEMETRY_BOUNDARY_IN_CONTROL_PLANE; NO_LLM_OR_QPU_HOTPATH","implementation_owner":"QKUComputationControlPlaneV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentLatencyAuditorV1","independent_validator_owner":"IndependentLatencyAuditorV1","input_contract":"monotonic and wall-clock timestamps, deadlines, TTLs, queue and provider timing","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"unit-normalized latency decomposition, percentile/SLO, stale/deadline decisions and correlation-only traces","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_LATENCY_TTL_AND_EDGE_DECAY_PASS","ST12_LATENCY_TTL_AND_EDGE_DECAY_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_FORMAL_DOMAIN_DERIVATION","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/latency/test_ttl_and_edge_decay.py","tools/independent_validate_qku_computation_control_plane_latency.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain latency","python tools/independent_validate_qku_computation_control_plane_latency.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentLatencyAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::099"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"RuntimePlatformV1","canonical_implementation_owner":"QKUComputationControlPlaneV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-LATENCY::008","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-LATENCY::008","codex_online_research_allowed":false,"control_id":"ST11-LATENCY::008","control_slug":"clock-skew","domain":"latency","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/clocks.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/latency_budget.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/deadlines.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/telemetry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/stale_policy.py","tests/stage1_prediction_markets/qku_computation_control_plane/latency/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/latency/test_clock_skew.py","tools/independent_validate_qku_computation_control_plane_latency.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain latency","python tools/independent_validate_qku_computation_control_plane_latency.py"],"implementation_specification":{"algorithm_or_rule":"Verify NTP/PTP or equivalent assumptions, skew measurement, cross-venue observation alignment, and fail-closed thresholds. Use distinct monotonic and wall clocks; normalize units; decompose queue, compute and provider latency; enforce TTL, deadlines and skew; treat traces as correlation only; reject stale results or use preapproved fast classical fallback.","authority_boundary":"IMPLEMENTATION_OWNER=QKUComputationControlPlaneV1; AUTHORITY_OWNER=RuntimePlatformV1; INDEPENDENT_AUDITOR=IndependentLatencyAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"RuntimePlatformV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"consume_existing_owner_refs":["RuntimePlatformV1","RP5G_LATENCY","HOTPATH_FOUNDATIONS"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"STALE_REJECT_CANCEL_DEADLINE_OR_USE_PREAPPROVED_FAST_CLASSICAL_FALLBACK","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/clocks.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/latency_budget.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/deadlines.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/telemetry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/stale_policy.py","tests/stage1_prediction_markets/qku_computation_control_plane/latency/"],"implementation_disposition":"IMPLEMENT_MONOTONIC_CLOCK_TTL_DEADLINE_AND_TELEMETRY_BOUNDARY_IN_CONTROL_PLANE; NO_LLM_OR_QPU_HOTPATH","implementation_owner":"QKUComputationControlPlaneV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentLatencyAuditorV1","independent_validator_owner":"IndependentLatencyAuditorV1","input_contract":"monotonic and wall-clock timestamps, deadlines, TTLs, queue and provider timing","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"unit-normalized latency decomposition, percentile/SLO, stale/deadline decisions and correlation-only traces","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_LATENCY_CLOCK_SKEW_PASS","ST12_LATENCY_CLOCK_SKEW_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_FORMAL_DOMAIN_DERIVATION","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/latency/test_clock_skew.py","tools/independent_validate_qku_computation_control_plane_latency.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain latency","python tools/independent_validate_qku_computation_control_plane_latency.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentLatencyAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::099"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"RuntimePlatformV1","canonical_implementation_owner":"QKUComputationControlPlaneV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-LATENCY::009","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-LATENCY::009","codex_online_research_allowed":false,"control_id":"ST11-LATENCY::009","control_slug":"queueing","domain":"latency","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/clocks.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/latency_budget.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/deadlines.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/telemetry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/stale_policy.py","tests/stage1_prediction_markets/qku_computation_control_plane/latency/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/latency/test_queueing.py","tools/independent_validate_qku_computation_control_plane_latency.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain latency","python tools/independent_validate_qku_computation_control_plane_latency.py"],"implementation_specification":{"algorithm_or_rule":"Verify service, agent, provider, QPU, work-order, and outbox queues have bounds, priorities, admission, and backpressure. Use distinct monotonic and wall clocks; normalize units; decompose queue, compute and provider latency; enforce TTL, deadlines and skew; treat traces as correlation only; reject stale results or use preapproved fast classical fallback.","authority_boundary":"IMPLEMENTATION_OWNER=QKUComputationControlPlaneV1; AUTHORITY_OWNER=RuntimePlatformV1; INDEPENDENT_AUDITOR=IndependentLatencyAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"RuntimePlatformV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"consume_existing_owner_refs":["RuntimePlatformV1","RP5G_LATENCY","HOTPATH_FOUNDATIONS"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"STALE_REJECT_CANCEL_DEADLINE_OR_USE_PREAPPROVED_FAST_CLASSICAL_FALLBACK","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/clocks.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/latency_budget.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/deadlines.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/telemetry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/stale_policy.py","tests/stage1_prediction_markets/qku_computation_control_plane/latency/"],"implementation_disposition":"IMPLEMENT_MONOTONIC_CLOCK_TTL_DEADLINE_AND_TELEMETRY_BOUNDARY_IN_CONTROL_PLANE; NO_LLM_OR_QPU_HOTPATH","implementation_owner":"QKUComputationControlPlaneV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentLatencyAuditorV1","independent_validator_owner":"IndependentLatencyAuditorV1","input_contract":"monotonic and wall-clock timestamps, deadlines, TTLs, queue and provider timing","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"unit-normalized latency decomposition, percentile/SLO, stale/deadline decisions and correlation-only traces","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_LATENCY_QUEUEING_PASS","ST12_LATENCY_QUEUEING_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_FORMAL_DOMAIN_DERIVATION","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/latency/test_queueing.py","tools/independent_validate_qku_computation_control_plane_latency.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain latency","python tools/independent_validate_qku_computation_control_plane_latency.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentLatencyAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::099"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"RuntimePlatformV1","canonical_implementation_owner":"QKUComputationControlPlaneV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-LATENCY::010","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-LATENCY::010","codex_online_research_allowed":false,"control_id":"ST11-LATENCY::010","control_slug":"deadlines-and-cancellation","domain":"latency","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/clocks.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/latency_budget.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/deadlines.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/telemetry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/stale_policy.py","tests/stage1_prediction_markets/qku_computation_control_plane/latency/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/latency/test_deadlines_and_cancellation.py","tools/independent_validate_qku_computation_control_plane_latency.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain latency","python tools/independent_validate_qku_computation_control_plane_latency.py"],"implementation_specification":{"algorithm_or_rule":"Verify propagated deadlines, cancellation, timeout, partial completion, and fallback behavior. Use distinct monotonic and wall clocks; normalize units; decompose queue, compute and provider latency; enforce TTL, deadlines and skew; treat traces as correlation only; reject stale results or use preapproved fast classical fallback.","authority_boundary":"IMPLEMENTATION_OWNER=QKUComputationControlPlaneV1; AUTHORITY_OWNER=RuntimePlatformV1; INDEPENDENT_AUDITOR=IndependentLatencyAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"RuntimePlatformV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"consume_existing_owner_refs":["RuntimePlatformV1","RP5G_LATENCY","HOTPATH_FOUNDATIONS"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"STALE_REJECT_CANCEL_DEADLINE_OR_USE_PREAPPROVED_FAST_CLASSICAL_FALLBACK","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/clocks.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/latency_budget.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/deadlines.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/telemetry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/stale_policy.py","tests/stage1_prediction_markets/qku_computation_control_plane/latency/"],"implementation_disposition":"IMPLEMENT_MONOTONIC_CLOCK_TTL_DEADLINE_AND_TELEMETRY_BOUNDARY_IN_CONTROL_PLANE; NO_LLM_OR_QPU_HOTPATH","implementation_owner":"QKUComputationControlPlaneV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentLatencyAuditorV1","independent_validator_owner":"IndependentLatencyAuditorV1","input_contract":"monotonic and wall-clock timestamps, deadlines, TTLs, queue and provider timing","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"unit-normalized latency decomposition, percentile/SLO, stale/deadline decisions and correlation-only traces","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_LATENCY_DEADLINES_AND_CANCELLATION_PASS","ST12_LATENCY_DEADLINES_AND_CANCELLATION_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_FORMAL_DOMAIN_DERIVATION","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/latency/test_deadlines_and_cancellation.py","tools/independent_validate_qku_computation_control_plane_latency.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain latency","python tools/independent_validate_qku_computation_control_plane_latency.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentLatencyAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::099"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"ComputationEvidenceServiceV1","canonical_implementation_owner":"QKUComputationControlPlaneV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-MODEL-RISK::001","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-MODEL-RISK::001","codex_online_research_allowed":false,"control_id":"ST11-MODEL-RISK::001","control_slug":"model-inventory","domain":"model_risk","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk_registry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_validation.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/monitoring.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/fdr.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/time_split.py","tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_model_inventory.py","tools/independent_validate_qku_computation_control_plane_model_risk.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain model_risk","python tools/independent_validate_qku_computation_control_plane_model_risk.py"],"implementation_specification":{"algorithm_or_rule":"Classify every statistical, financial, AI, optimization, simulation, policy, and deterministic component by model status and materiality. Maintain intended use and materiality inventory; independently verify implementation; apply uncertainty, calibration, FDR, purged time splits, stress and no-trade comparison; route limitations to monitoring and revalidation.","authority_boundary":"IMPLEMENTATION_OWNER=QKUComputationControlPlaneV1; AUTHORITY_OWNER=ComputationEvidenceServiceV1; INDEPENDENT_AUDITOR=IndependentModelRiskAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"ComputationEvidenceServiceV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"consume_existing_owner_refs":["ComputationEvidenceServiceV1","RP5G","RANK4","QOPT1","MEM1"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"NO_TRADE_OR_RESEARCH_ONLY_WITH_LIMITATION_AND_REVALIDATION_WORK_ORDER","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk_registry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_validation.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/monitoring.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/fdr.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/time_split.py","tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/"],"implementation_disposition":"IMPLEMENT_MODEL_RISK_REGISTRY_VALIDATION_AND_MONITORING_WITH_INDEPENDENT_SECOND_LINE_VALIDATOR","implementation_owner":"QKUComputationControlPlaneV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentModelRiskAuditorV1","independent_validator_owner":"IndependentModelRiskAuditorV1","input_contract":"component inventory, intended-use profiles, evidence bundles, parameter policies, outcomes","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"independent validation receipts, limitations, FDR/calibration/time-split decisions, monitoring state","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_MODEL_RISK_MODEL_INVENTORY_PASS","ST12_MODEL_RISK_MODEL_INVENTORY_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_model_inventory.py","tools/independent_validate_qku_computation_control_plane_model_risk.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain model_risk","python tools/independent_validate_qku_computation_control_plane_model_risk.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentModelRiskAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":[],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"ComputationEvidenceServiceV1","canonical_implementation_owner":"QKUComputationControlPlaneV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-MODEL-RISK::002","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-MODEL-RISK::002","codex_online_research_allowed":false,"control_id":"ST11-MODEL-RISK::002","control_slug":"intended-use","domain":"model_risk","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk_registry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_validation.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/monitoring.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/fdr.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/time_split.py","tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_intended_use.py","tools/independent_validate_qku_computation_control_plane_model_risk.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain model_risk","python tools/independent_validate_qku_computation_control_plane_model_risk.py"],"implementation_specification":{"algorithm_or_rule":"Verify purpose, users, decision influence, limitations, prohibited uses, and scope-extension controls for every material model. Maintain intended use and materiality inventory; independently verify implementation; apply uncertainty, calibration, FDR, purged time splits, stress and no-trade comparison; route limitations to monitoring and revalidation.","authority_boundary":"IMPLEMENTATION_OWNER=QKUComputationControlPlaneV1; AUTHORITY_OWNER=ComputationEvidenceServiceV1; INDEPENDENT_AUDITOR=IndependentModelRiskAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"ComputationEvidenceServiceV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"consume_existing_owner_refs":["ComputationEvidenceServiceV1","RP5G","RANK4","QOPT1","MEM1"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"NO_TRADE_OR_RESEARCH_ONLY_WITH_LIMITATION_AND_REVALIDATION_WORK_ORDER","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk_registry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_validation.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/monitoring.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/fdr.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/time_split.py","tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/"],"implementation_disposition":"IMPLEMENT_MODEL_RISK_REGISTRY_VALIDATION_AND_MONITORING_WITH_INDEPENDENT_SECOND_LINE_VALIDATOR","implementation_owner":"QKUComputationControlPlaneV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentModelRiskAuditorV1","independent_validator_owner":"IndependentModelRiskAuditorV1","input_contract":"component inventory, intended-use profiles, evidence bundles, parameter policies, outcomes","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"independent validation receipts, limitations, FDR/calibration/time-split decisions, monitoring state","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_MODEL_RISK_INTENDED_USE_PASS","ST12_MODEL_RISK_INTENDED_USE_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_intended_use.py","tools/independent_validate_qku_computation_control_plane_model_risk.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain model_risk","python tools/independent_validate_qku_computation_control_plane_model_risk.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentModelRiskAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":[],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"ComputationEvidenceServiceV1","canonical_implementation_owner":"QKUComputationControlPlaneV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-MODEL-RISK::003","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-MODEL-RISK::003","codex_online_research_allowed":false,"control_id":"ST11-MODEL-RISK::003","control_slug":"materiality-tiering","domain":"model_risk","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk_registry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_validation.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/monitoring.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/fdr.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/time_split.py","tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_materiality_tiering.py","tools/independent_validate_qku_computation_control_plane_model_risk.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain model_risk","python tools/independent_validate_qku_computation_control_plane_model_risk.py"],"implementation_specification":{"algorithm_or_rule":"Independently assign risk tier from inherent risk, exposure, purpose, use, complexity, and aggregate dependencies. Maintain intended use and materiality inventory; independently verify implementation; apply uncertainty, calibration, FDR, purged time splits, stress and no-trade comparison; route limitations to monitoring and revalidation.","authority_boundary":"IMPLEMENTATION_OWNER=QKUComputationControlPlaneV1; AUTHORITY_OWNER=ComputationEvidenceServiceV1; INDEPENDENT_AUDITOR=IndependentModelRiskAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"ComputationEvidenceServiceV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"consume_existing_owner_refs":["ComputationEvidenceServiceV1","RP5G","RANK4","QOPT1","MEM1"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"NO_TRADE_OR_RESEARCH_ONLY_WITH_LIMITATION_AND_REVALIDATION_WORK_ORDER","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk_registry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_validation.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/monitoring.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/fdr.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/time_split.py","tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/"],"implementation_disposition":"IMPLEMENT_MODEL_RISK_REGISTRY_VALIDATION_AND_MONITORING_WITH_INDEPENDENT_SECOND_LINE_VALIDATOR","implementation_owner":"QKUComputationControlPlaneV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentModelRiskAuditorV1","independent_validator_owner":"IndependentModelRiskAuditorV1","input_contract":"component inventory, intended-use profiles, evidence bundles, parameter policies, outcomes","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"independent validation receipts, limitations, FDR/calibration/time-split decisions, monitoring state","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_MODEL_RISK_MATERIALITY_TIERING_PASS","ST12_MODEL_RISK_MATERIALITY_TIERING_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_materiality_tiering.py","tools/independent_validate_qku_computation_control_plane_model_risk.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain model_risk","python tools/independent_validate_qku_computation_control_plane_model_risk.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentModelRiskAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":[],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"ComputationEvidenceServiceV1","canonical_implementation_owner":"QKUComputationControlPlaneV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-MODEL-RISK::004","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-MODEL-RISK::004","codex_online_research_allowed":false,"control_id":"ST11-MODEL-RISK::004","control_slug":"conceptual-soundness","domain":"model_risk","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk_registry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_validation.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/monitoring.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/fdr.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/time_split.py","tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_conceptual_soundness.py","tools/independent_validate_qku_computation_control_plane_model_risk.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain model_risk","python tools/independent_validate_qku_computation_control_plane_model_risk.py"],"implementation_specification":{"algorithm_or_rule":"Challenge mathematics, assumptions, domains, objectives, constraints, distributions, causal claims, and approximations. Maintain intended use and materiality inventory; independently verify implementation; apply uncertainty, calibration, FDR, purged time splits, stress and no-trade comparison; route limitations to monitoring and revalidation.","authority_boundary":"IMPLEMENTATION_OWNER=QKUComputationControlPlaneV1; AUTHORITY_OWNER=ComputationEvidenceServiceV1; INDEPENDENT_AUDITOR=IndependentModelRiskAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"ComputationEvidenceServiceV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"consume_existing_owner_refs":["ComputationEvidenceServiceV1","RP5G","RANK4","QOPT1","MEM1"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"NO_TRADE_OR_RESEARCH_ONLY_WITH_LIMITATION_AND_REVALIDATION_WORK_ORDER","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk_registry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_validation.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/monitoring.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/fdr.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/time_split.py","tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/"],"implementation_disposition":"IMPLEMENT_MODEL_RISK_REGISTRY_VALIDATION_AND_MONITORING_WITH_INDEPENDENT_SECOND_LINE_VALIDATOR","implementation_owner":"QKUComputationControlPlaneV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentModelRiskAuditorV1","independent_validator_owner":"IndependentModelRiskAuditorV1","input_contract":"component inventory, intended-use profiles, evidence bundles, parameter policies, outcomes","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"independent validation receipts, limitations, FDR/calibration/time-split decisions, monitoring state","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_MODEL_RISK_CONCEPTUAL_SOUNDNESS_PASS","ST12_MODEL_RISK_CONCEPTUAL_SOUNDNESS_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_conceptual_soundness.py","tools/independent_validate_qku_computation_control_plane_model_risk.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain model_risk","python tools/independent_validate_qku_computation_control_plane_model_risk.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentModelRiskAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":[],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"ComputationEvidenceServiceV1","canonical_implementation_owner":"QKUComputationControlPlaneV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-MODEL-RISK::005","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-MODEL-RISK::005","codex_online_research_allowed":false,"control_id":"ST11-MODEL-RISK::005","control_slug":"data-quality","domain":"model_risk","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk_registry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_validation.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/monitoring.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/fdr.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/time_split.py","tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_data_quality.py","tools/independent_validate_qku_computation_control_plane_model_risk.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain model_risk","python tools/independent_validate_qku_computation_control_plane_model_risk.py"],"implementation_specification":{"algorithm_or_rule":"Challenge representativeness, point-in-time legality, missingness, revisions, leakage, labels, sample size, and source limitations. Maintain intended use and materiality inventory; independently verify implementation; apply uncertainty, calibration, FDR, purged time splits, stress and no-trade comparison; route limitations to monitoring and revalidation.","authority_boundary":"IMPLEMENTATION_OWNER=QKUComputationControlPlaneV1; AUTHORITY_OWNER=ComputationEvidenceServiceV1; INDEPENDENT_AUDITOR=IndependentModelRiskAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"ComputationEvidenceServiceV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"consume_existing_owner_refs":["ComputationEvidenceServiceV1","RP5G","RANK4","QOPT1","MEM1"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"NO_TRADE_OR_RESEARCH_ONLY_WITH_LIMITATION_AND_REVALIDATION_WORK_ORDER","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk_registry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_validation.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/monitoring.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/fdr.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/time_split.py","tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/"],"implementation_disposition":"IMPLEMENT_MODEL_RISK_REGISTRY_VALIDATION_AND_MONITORING_WITH_INDEPENDENT_SECOND_LINE_VALIDATOR","implementation_owner":"QKUComputationControlPlaneV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentModelRiskAuditorV1","independent_validator_owner":"IndependentModelRiskAuditorV1","input_contract":"component inventory, intended-use profiles, evidence bundles, parameter policies, outcomes","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"independent validation receipts, limitations, FDR/calibration/time-split decisions, monitoring state","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_MODEL_RISK_DATA_QUALITY_PASS","ST12_MODEL_RISK_DATA_QUALITY_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_data_quality.py","tools/independent_validate_qku_computation_control_plane_model_risk.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain model_risk","python tools/independent_validate_qku_computation_control_plane_model_risk.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentModelRiskAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":[],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"ComputationEvidenceServiceV1","canonical_implementation_owner":"QKUComputationControlPlaneV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-MODEL-RISK::006","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-MODEL-RISK::006","codex_online_research_allowed":false,"control_id":"ST11-MODEL-RISK::006","control_slug":"implementation-verification","domain":"model_risk","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk_registry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_validation.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/monitoring.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/fdr.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/time_split.py","tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_implementation_verification.py","tools/independent_validate_qku_computation_control_plane_model_risk.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain model_risk","python tools/independent_validate_qku_computation_control_plane_model_risk.py"],"implementation_specification":{"algorithm_or_rule":"Verify code/solver behavior against independent formulations, golden vectors, boundaries, properties, and mutation sensitivity. Maintain intended use and materiality inventory; independently verify implementation; apply uncertainty, calibration, FDR, purged time splits, stress and no-trade comparison; route limitations to monitoring and revalidation.","authority_boundary":"IMPLEMENTATION_OWNER=QKUComputationControlPlaneV1; AUTHORITY_OWNER=ComputationEvidenceServiceV1; INDEPENDENT_AUDITOR=IndependentModelRiskAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"ComputationEvidenceServiceV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"consume_existing_owner_refs":["ComputationEvidenceServiceV1","RP5G","RANK4","QOPT1","MEM1"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"NO_TRADE_OR_RESEARCH_ONLY_WITH_LIMITATION_AND_REVALIDATION_WORK_ORDER","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk_registry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_validation.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/monitoring.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/fdr.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/time_split.py","tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/"],"implementation_disposition":"IMPLEMENT_MODEL_RISK_REGISTRY_VALIDATION_AND_MONITORING_WITH_INDEPENDENT_SECOND_LINE_VALIDATOR","implementation_owner":"QKUComputationControlPlaneV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentModelRiskAuditorV1","independent_validator_owner":"IndependentModelRiskAuditorV1","input_contract":"component inventory, intended-use profiles, evidence bundles, parameter policies, outcomes","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"independent validation receipts, limitations, FDR/calibration/time-split decisions, monitoring state","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_MODEL_RISK_IMPLEMENTATION_VERIFICATION_PASS","ST12_MODEL_RISK_IMPLEMENTATION_VERIFICATION_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_implementation_verification.py","tools/independent_validate_qku_computation_control_plane_model_risk.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain model_risk","python tools/independent_validate_qku_computation_control_plane_model_risk.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentModelRiskAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":[],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"ComputationEvidenceServiceV1","canonical_implementation_owner":"QKUComputationControlPlaneV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-MODEL-RISK::007","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-MODEL-RISK::007","codex_online_research_allowed":false,"control_id":"ST11-MODEL-RISK::007","control_slug":"effective-challenge","domain":"model_risk","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk_registry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_validation.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/monitoring.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/fdr.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/time_split.py","tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_effective_challenge.py","tools/independent_validate_qku_computation_control_plane_model_risk.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain model_risk","python tools/independent_validate_qku_computation_control_plane_model_risk.py"],"implementation_specification":{"algorithm_or_rule":"Require an objective reviewer independent of builder logic with authority to create blocking defects and require repair. Maintain intended use and materiality inventory; independently verify implementation; apply uncertainty, calibration, FDR, purged time splits, stress and no-trade comparison; route limitations to monitoring and revalidation.","authority_boundary":"IMPLEMENTATION_OWNER=QKUComputationControlPlaneV1; AUTHORITY_OWNER=ComputationEvidenceServiceV1; INDEPENDENT_AUDITOR=IndependentModelRiskAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"ComputationEvidenceServiceV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"consume_existing_owner_refs":["ComputationEvidenceServiceV1","RP5G","RANK4","QOPT1","MEM1"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"NO_TRADE_OR_RESEARCH_ONLY_WITH_LIMITATION_AND_REVALIDATION_WORK_ORDER","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk_registry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_validation.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/monitoring.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/fdr.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/time_split.py","tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/"],"implementation_disposition":"IMPLEMENT_MODEL_RISK_REGISTRY_VALIDATION_AND_MONITORING_WITH_INDEPENDENT_SECOND_LINE_VALIDATOR","implementation_owner":"QKUComputationControlPlaneV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentModelRiskAuditorV1","independent_validator_owner":"IndependentModelRiskAuditorV1","input_contract":"component inventory, intended-use profiles, evidence bundles, parameter policies, outcomes","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"independent validation receipts, limitations, FDR/calibration/time-split decisions, monitoring state","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_MODEL_RISK_EFFECTIVE_CHALLENGE_PASS","ST12_MODEL_RISK_EFFECTIVE_CHALLENGE_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_effective_challenge.py","tools/independent_validate_qku_computation_control_plane_model_risk.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain model_risk","python tools/independent_validate_qku_computation_control_plane_model_risk.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentModelRiskAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":[],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"ComputationEvidenceServiceV1","canonical_implementation_owner":"QKUComputationControlPlaneV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-MODEL-RISK::008","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-MODEL-RISK::008","codex_online_research_allowed":false,"control_id":"ST11-MODEL-RISK::008","control_slug":"outcomes-analysis","domain":"model_risk","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk_registry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_validation.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/monitoring.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/fdr.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/time_split.py","tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_outcomes_analysis.py","tools/independent_validate_qku_computation_control_plane_model_risk.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain model_risk","python tools/independent_validate_qku_computation_control_plane_model_risk.py"],"implementation_specification":{"algorithm_or_rule":"Define comparisons to replay/PAPER outcomes, calibration, error, residual, drift, regime, and economic results without fabricating evidence. Maintain intended use and materiality inventory; independently verify implementation; apply uncertainty, calibration, FDR, purged time splits, stress and no-trade comparison; route limitations to monitoring and revalidation.","authority_boundary":"IMPLEMENTATION_OWNER=QKUComputationControlPlaneV1; AUTHORITY_OWNER=ComputationEvidenceServiceV1; INDEPENDENT_AUDITOR=IndependentModelRiskAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"ComputationEvidenceServiceV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"consume_existing_owner_refs":["ComputationEvidenceServiceV1","RP5G","RANK4","QOPT1","MEM1"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"NO_TRADE_OR_RESEARCH_ONLY_WITH_LIMITATION_AND_REVALIDATION_WORK_ORDER","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk_registry.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_validation.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/monitoring.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/fdr.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/time_split.py","tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/"],"implementation_disposition":"IMPLEMENT_MODEL_RISK_REGISTRY_VALIDATION_AND_MONITORING_WITH_INDEPENDENT_SECOND_LINE_VALIDATOR","implementation_owner":"QKUComputationControlPlaneV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentModelRiskAuditorV1","independent_validator_owner":"IndependentModelRiskAuditorV1","input_contract":"component inventory, intended-use profiles, evidence bundles, parameter policies, outcomes","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"independent validation receipts, limitations, FDR/calibration/time-split decisions, monitoring state","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_MODEL_RISK_OUTCOMES_ANALYSIS_PASS","ST12_MODEL_RISK_OUTCOMES_ANALYSIS_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_outcomes_analysis.py","tools/independent_validate_qku_computation_control_plane_model_risk.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain model_risk","python tools/independent_validate_qku_computation_control_plane_model_risk.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentModelRiskAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":[],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"RuntimePlatformV1","canonical_implementation_owner":"QKUComputationControlPlaneV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-OPERATIONS::005","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-OPERATIONS::005","codex_online_research_allowed":false,"control_id":"ST11-OPERATIONS::005","control_slug":"database-migrations","domain":"operations","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/runtime.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/config.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/health.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/backup.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/supervision.py","tools/build_qku_computation_control_plane.py","tools/validate_qku_computation_control_plane.py","tools/independent_validate_qku_computation_control_plane.py","tools/run_validation_gates.py","tools/validation_inventory.py","tools/validation_scope_registry.py","tools/changed_area_validation_router.py","tests/fail_closed/test_run_validation_gates.py","tests/tools/test_validation_inventory.py","tests/tools/test_validation_scope_registry.py","tests/tools/test_changed_area_validation_router.py"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_database_migrations.py","tools/independent_validate_qku_computation_control_plane_operations.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain operations","python tools/independent_validate_qku_computation_control_plane_operations.py"],"implementation_specification":{"algorithm_or_rule":"Verify forward/backward migration, compatibility window, transactionality, backup, rollback, and schema-version checks. Use typed configuration, supervised lifecycle, forward-only tested migrations, SQLite safety, durable receipts, bounded queues, backup/restore, alerts, drills and centralized validation/publication integration.","authority_boundary":"IMPLEMENTATION_OWNER=QKUComputationControlPlaneV1; AUTHORITY_OWNER=RuntimePlatformV1; INDEPENDENT_AUDITOR=IndependentOperationsAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"RuntimePlatformV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"consume_existing_owner_refs":["RuntimePlatformV1","VAL1","SVC1GeneratedProjectionFabric"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"SUBMIT_DISABLED_SAFE_HARBOR_ROLLBACK_OR_SERVICE_STOP","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/runtime.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/config.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/health.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/backup.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/supervision.py","tools/build_qku_computation_control_plane.py","tools/validate_qku_computation_control_plane.py","tools/independent_validate_qku_computation_control_plane.py","tools/run_validation_gates.py","tools/validation_inventory.py","tools/validation_scope_registry.py","tools/changed_area_validation_router.py","tests/fail_closed/test_run_validation_gates.py","tests/tools/test_validation_inventory.py","tests/tools/test_validation_scope_registry.py","tests/tools/test_changed_area_validation_router.py"],"implementation_disposition":"IMPLEMENT_BOUNDED_RUNTIME_CONFIG_HEALTH_BACKUP_AND_VALIDATION_INTEGRATION; NO_PROVIDER_EFFECT","implementation_owner":"QKUComputationControlPlaneV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentOperationsAuditorV1","independent_validator_owner":"IndependentOperationsAuditorV1","input_contract":"configuration, service topology, migrations, events, receipts, capacity and health","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"supervised runtime states, durable storage, backup/restore, alerts, drills and validation/publication receipts","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_OPERATIONS_DATABASE_MIGRATIONS_PASS","ST12_OPERATIONS_DATABASE_MIGRATIONS_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_database_migrations.py","tools/independent_validate_qku_computation_control_plane_operations.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain operations","python tools/independent_validate_qku_computation_control_plane_operations.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentOperationsAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::085","ST10-FILE::086","ST10-FILE::087","ST10-FILE::091","ST10-FILE::088","ST10-FILE::089","ST10-FILE::090","ST10-FILE::112","ST10-FILE::092","ST10-FILE::093","ST10-FILE::094"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"RuntimePlatformV1","canonical_implementation_owner":"QKUComputationControlPlaneV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-OPERATIONS::006","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-OPERATIONS::006","codex_online_research_allowed":false,"control_id":"ST11-OPERATIONS::006","control_slug":"sqlite-runtime-safety","domain":"operations","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/runtime.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/config.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/health.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/backup.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/supervision.py","tools/build_qku_computation_control_plane.py","tools/validate_qku_computation_control_plane.py","tools/independent_validate_qku_computation_control_plane.py","tools/run_validation_gates.py","tools/validation_inventory.py","tools/validation_scope_registry.py","tools/changed_area_validation_router.py","tests/fail_closed/test_run_validation_gates.py","tests/tools/test_validation_inventory.py","tests/tools/test_validation_scope_registry.py","tests/tools/test_changed_area_validation_router.py"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_sqlite_runtime_safety.py","tools/independent_validate_qku_computation_control_plane_operations.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain operations","python tools/independent_validate_qku_computation_control_plane_operations.py"],"implementation_specification":{"algorithm_or_rule":"Verify foreign keys per connection, journal mode, fixed SQLite release, connection concurrency, checkpoint, and durability settings. Use typed configuration, supervised lifecycle, forward-only tested migrations, SQLite safety, durable receipts, bounded queues, backup/restore, alerts, drills and centralized validation/publication integration.","authority_boundary":"IMPLEMENTATION_OWNER=QKUComputationControlPlaneV1; AUTHORITY_OWNER=RuntimePlatformV1; INDEPENDENT_AUDITOR=IndependentOperationsAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"RuntimePlatformV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"consume_existing_owner_refs":["RuntimePlatformV1","VAL1","SVC1GeneratedProjectionFabric"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"SUBMIT_DISABLED_SAFE_HARBOR_ROLLBACK_OR_SERVICE_STOP","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/runtime.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/config.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/health.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/backup.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/supervision.py","tools/build_qku_computation_control_plane.py","tools/validate_qku_computation_control_plane.py","tools/independent_validate_qku_computation_control_plane.py","tools/run_validation_gates.py","tools/validation_inventory.py","tools/validation_scope_registry.py","tools/changed_area_validation_router.py","tests/fail_closed/test_run_validation_gates.py","tests/tools/test_validation_inventory.py","tests/tools/test_validation_scope_registry.py","tests/tools/test_changed_area_validation_router.py"],"implementation_disposition":"IMPLEMENT_BOUNDED_RUNTIME_CONFIG_HEALTH_BACKUP_AND_VALIDATION_INTEGRATION; NO_PROVIDER_EFFECT","implementation_owner":"QKUComputationControlPlaneV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentOperationsAuditorV1","independent_validator_owner":"IndependentOperationsAuditorV1","input_contract":"configuration, service topology, migrations, events, receipts, capacity and health","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"supervised runtime states, durable storage, backup/restore, alerts, drills and validation/publication receipts","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_OPERATIONS_SQLITE_RUNTIME_SAFETY_PASS","ST12_OPERATIONS_SQLITE_RUNTIME_SAFETY_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_sqlite_runtime_safety.py","tools/independent_validate_qku_computation_control_plane_operations.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain operations","python tools/independent_validate_qku_computation_control_plane_operations.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentOperationsAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::085","ST10-FILE::086","ST10-FILE::087","ST10-FILE::091","ST10-FILE::088","ST10-FILE::089","ST10-FILE::090","ST10-FILE::112","ST10-FILE::092","ST10-FILE::093","ST10-FILE::094"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"RuntimePlatformV1","canonical_implementation_owner":"QKUComputationControlPlaneV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-OPERATIONS::007","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-OPERATIONS::007","codex_online_research_allowed":false,"control_id":"ST11-OPERATIONS::007","control_slug":"backup-restore","domain":"operations","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/runtime.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/config.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/health.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/backup.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/supervision.py","tools/build_qku_computation_control_plane.py","tools/validate_qku_computation_control_plane.py","tools/independent_validate_qku_computation_control_plane.py","tools/run_validation_gates.py","tools/validation_inventory.py","tools/validation_scope_registry.py","tools/changed_area_validation_router.py","tests/fail_closed/test_run_validation_gates.py","tests/tools/test_validation_inventory.py","tests/tools/test_validation_scope_registry.py","tests/tools/test_changed_area_validation_router.py"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_backup_restore.py","tools/independent_validate_qku_computation_control_plane_operations.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain operations","python tools/independent_validate_qku_computation_control_plane_operations.py"],"implementation_specification":{"algorithm_or_rule":"Verify backup consistency, restore testing, retention, corruption detection, and recovery objectives. Use typed configuration, supervised lifecycle, forward-only tested migrations, SQLite safety, durable receipts, bounded queues, backup/restore, alerts, drills and centralized validation/publication integration.","authority_boundary":"IMPLEMENTATION_OWNER=QKUComputationControlPlaneV1; AUTHORITY_OWNER=RuntimePlatformV1; INDEPENDENT_AUDITOR=IndependentOperationsAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"RuntimePlatformV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"consume_existing_owner_refs":["RuntimePlatformV1","VAL1","SVC1GeneratedProjectionFabric"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"SUBMIT_DISABLED_SAFE_HARBOR_ROLLBACK_OR_SERVICE_STOP","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/runtime.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/config.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/health.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/backup.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/supervision.py","tools/build_qku_computation_control_plane.py","tools/validate_qku_computation_control_plane.py","tools/independent_validate_qku_computation_control_plane.py","tools/run_validation_gates.py","tools/validation_inventory.py","tools/validation_scope_registry.py","tools/changed_area_validation_router.py","tests/fail_closed/test_run_validation_gates.py","tests/tools/test_validation_inventory.py","tests/tools/test_validation_scope_registry.py","tests/tools/test_changed_area_validation_router.py"],"implementation_disposition":"IMPLEMENT_BOUNDED_RUNTIME_CONFIG_HEALTH_BACKUP_AND_VALIDATION_INTEGRATION; NO_PROVIDER_EFFECT","implementation_owner":"QKUComputationControlPlaneV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentOperationsAuditorV1","independent_validator_owner":"IndependentOperationsAuditorV1","input_contract":"configuration, service topology, migrations, events, receipts, capacity and health","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"supervised runtime states, durable storage, backup/restore, alerts, drills and validation/publication receipts","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_OPERATIONS_BACKUP_RESTORE_PASS","ST12_OPERATIONS_BACKUP_RESTORE_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_backup_restore.py","tools/independent_validate_qku_computation_control_plane_operations.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain operations","python tools/independent_validate_qku_computation_control_plane_operations.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentOperationsAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::085","ST10-FILE::086","ST10-FILE::087","ST10-FILE::091","ST10-FILE::088","ST10-FILE::089","ST10-FILE::090","ST10-FILE::112","ST10-FILE::092","ST10-FILE::093","ST10-FILE::094"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"RuntimePlatformV1","canonical_implementation_owner":"QKUComputationControlPlaneV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-OPERATIONS::008","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-OPERATIONS::008","codex_online_research_allowed":false,"control_id":"ST11-OPERATIONS::008","control_slug":"event-and-receipt-durability","domain":"operations","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/runtime.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/config.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/health.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/backup.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/supervision.py","tools/build_qku_computation_control_plane.py","tools/validate_qku_computation_control_plane.py","tools/independent_validate_qku_computation_control_plane.py","tools/run_validation_gates.py","tools/validation_inventory.py","tools/validation_scope_registry.py","tools/changed_area_validation_router.py","tests/fail_closed/test_run_validation_gates.py","tests/tools/test_validation_inventory.py","tests/tools/test_validation_scope_registry.py","tests/tools/test_changed_area_validation_router.py"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_event_and_receipt_durability.py","tools/independent_validate_qku_computation_control_plane_operations.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain operations","python tools/independent_validate_qku_computation_control_plane_operations.py"],"implementation_specification":{"algorithm_or_rule":"Verify append-only event/receipt persistence, ordering, duplicate defense, replay/fold reconstruction, and correction. Use typed configuration, supervised lifecycle, forward-only tested migrations, SQLite safety, durable receipts, bounded queues, backup/restore, alerts, drills and centralized validation/publication integration.","authority_boundary":"IMPLEMENTATION_OWNER=QKUComputationControlPlaneV1; AUTHORITY_OWNER=RuntimePlatformV1; INDEPENDENT_AUDITOR=IndependentOperationsAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"RuntimePlatformV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"consume_existing_owner_refs":["RuntimePlatformV1","VAL1","SVC1GeneratedProjectionFabric"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"SUBMIT_DISABLED_SAFE_HARBOR_ROLLBACK_OR_SERVICE_STOP","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/runtime.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/config.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/health.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/backup.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/supervision.py","tools/build_qku_computation_control_plane.py","tools/validate_qku_computation_control_plane.py","tools/independent_validate_qku_computation_control_plane.py","tools/run_validation_gates.py","tools/validation_inventory.py","tools/validation_scope_registry.py","tools/changed_area_validation_router.py","tests/fail_closed/test_run_validation_gates.py","tests/tools/test_validation_inventory.py","tests/tools/test_validation_scope_registry.py","tests/tools/test_changed_area_validation_router.py"],"implementation_disposition":"IMPLEMENT_BOUNDED_RUNTIME_CONFIG_HEALTH_BACKUP_AND_VALIDATION_INTEGRATION; NO_PROVIDER_EFFECT","implementation_owner":"QKUComputationControlPlaneV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentOperationsAuditorV1","independent_validator_owner":"IndependentOperationsAuditorV1","input_contract":"configuration, service topology, migrations, events, receipts, capacity and health","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"supervised runtime states, durable storage, backup/restore, alerts, drills and validation/publication receipts","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_OPERATIONS_EVENT_AND_RECEIPT_DURABILITY_PASS","ST12_OPERATIONS_EVENT_AND_RECEIPT_DURABILITY_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_event_and_receipt_durability.py","tools/independent_validate_qku_computation_control_plane_operations.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain operations","python tools/independent_validate_qku_computation_control_plane_operations.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentOperationsAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::085","ST10-FILE::086","ST10-FILE::087","ST10-FILE::091","ST10-FILE::088","ST10-FILE::089","ST10-FILE::090","ST10-FILE::112","ST10-FILE::092","ST10-FILE::093","ST10-FILE::094"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"RuntimePlatformV1","canonical_implementation_owner":"QKUComputationControlPlaneV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-OPERATIONS::009","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-OPERATIONS::009","codex_online_research_allowed":false,"control_id":"ST11-OPERATIONS::009","control_slug":"capacity-and-backpressure","domain":"operations","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/runtime.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/config.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/health.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/backup.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/supervision.py","tools/build_qku_computation_control_plane.py","tools/validate_qku_computation_control_plane.py","tools/independent_validate_qku_computation_control_plane.py","tools/run_validation_gates.py","tools/validation_inventory.py","tools/validation_scope_registry.py","tools/changed_area_validation_router.py","tests/fail_closed/test_run_validation_gates.py","tests/tools/test_validation_inventory.py","tests/tools/test_validation_scope_registry.py","tests/tools/test_changed_area_validation_router.py"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_capacity_and_backpressure.py","tools/independent_validate_qku_computation_control_plane_operations.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain operations","python tools/independent_validate_qku_computation_control_plane_operations.py"],"implementation_specification":{"algorithm_or_rule":"Verify bounded queues, worker pools, storage growth, disk pressure, rate limits, and graceful shedding. Use typed configuration, supervised lifecycle, forward-only tested migrations, SQLite safety, durable receipts, bounded queues, backup/restore, alerts, drills and centralized validation/publication integration.","authority_boundary":"IMPLEMENTATION_OWNER=QKUComputationControlPlaneV1; AUTHORITY_OWNER=RuntimePlatformV1; INDEPENDENT_AUDITOR=IndependentOperationsAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"RuntimePlatformV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"consume_existing_owner_refs":["RuntimePlatformV1","VAL1","SVC1GeneratedProjectionFabric"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"SUBMIT_DISABLED_SAFE_HARBOR_ROLLBACK_OR_SERVICE_STOP","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/runtime.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/config.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/health.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/backup.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/supervision.py","tools/build_qku_computation_control_plane.py","tools/validate_qku_computation_control_plane.py","tools/independent_validate_qku_computation_control_plane.py","tools/run_validation_gates.py","tools/validation_inventory.py","tools/validation_scope_registry.py","tools/changed_area_validation_router.py","tests/fail_closed/test_run_validation_gates.py","tests/tools/test_validation_inventory.py","tests/tools/test_validation_scope_registry.py","tests/tools/test_changed_area_validation_router.py"],"implementation_disposition":"IMPLEMENT_BOUNDED_RUNTIME_CONFIG_HEALTH_BACKUP_AND_VALIDATION_INTEGRATION; NO_PROVIDER_EFFECT","implementation_owner":"QKUComputationControlPlaneV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentOperationsAuditorV1","independent_validator_owner":"IndependentOperationsAuditorV1","input_contract":"configuration, service topology, migrations, events, receipts, capacity and health","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"supervised runtime states, durable storage, backup/restore, alerts, drills and validation/publication receipts","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_OPERATIONS_CAPACITY_AND_BACKPRESSURE_PASS","ST12_OPERATIONS_CAPACITY_AND_BACKPRESSURE_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_capacity_and_backpressure.py","tools/independent_validate_qku_computation_control_plane_operations.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain operations","python tools/independent_validate_qku_computation_control_plane_operations.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentOperationsAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::085","ST10-FILE::086","ST10-FILE::087","ST10-FILE::091","ST10-FILE::088","ST10-FILE::089","ST10-FILE::090","ST10-FILE::112","ST10-FILE::092","ST10-FILE::093","ST10-FILE::094"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"QuantumBenchmarkServiceV1","canonical_implementation_owner":"QuantumBenchmarkServiceV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-QUANTUM::007","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-QUANTUM::007","codex_online_research_allowed":false,"control_id":"ST11-QUANTUM::007","control_slug":"penalty-adequacy","domain":"quantum","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_compiler.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_mapping_adapter.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_penalty.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_interpret_back.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_feasibility.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_comparator.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_fallback.py","tests/stage1_prediction_markets/qku_computation_control_plane/quantum/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_penalty_adequacy.py","tools/independent_validate_qku_computation_control_plane_quantum.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain quantum","python tools/independent_validate_qku_computation_control_plane_quantum.py"],"implementation_specification":{"algorithm_or_rule":"Verify penalties dominate infeasible gains without destroying numerical resolution; no guessed universal penalty. Classify original problem shape; map variables, objective and constraints with explicit scaling and penalties; interpret back; revalidate original-model feasibility; compare the same formulation to a classical baseline; fall back deterministically.","authority_boundary":"IMPLEMENTATION_OWNER=QuantumBenchmarkServiceV1; AUTHORITY_OWNER=QuantumBenchmarkServiceV1; INDEPENDENT_AUDITOR=IndependentQuantumAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"QuantumBenchmarkServiceV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QuantumBenchmarkServiceV1","codex_online_research_required":false,"consume_existing_owner_refs":["PR162E_Q_QUANTUM_AUTOMAPPER","QuantumBenchmarkServiceV1","QOPT1"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"DETERMINISTIC_SAME_FORMULATION_CLASSICAL_FALLBACK_OR_NO_TRADE","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_compiler.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_mapping_adapter.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_penalty.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_interpret_back.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_feasibility.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_comparator.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_fallback.py","tests/stage1_prediction_markets/qku_computation_control_plane/quantum/"],"implementation_disposition":"IMPLEMENT_READ_ONLY_MAPPER_COMPARATOR_AND_INTERPRET_BACK_ADAPTER_CONSUMING_MERGED_PR162E_Q; NO_QPU","implementation_owner":"QuantumBenchmarkServiceV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentQuantumAuditorV1","independent_validator_owner":"IndependentQuantumAuditorV1","input_contract":"original problem, mapping profile, variables, constraints, coefficients, backend/seed metadata","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"mapped candidate, interpreted result, original-model feasibility, same-formulation comparison and fallback receipt","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_QUANTUM_PENALTY_ADEQUACY_PASS","ST12_QUANTUM_PENALTY_ADEQUACY_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_penalty_adequacy.py","tools/independent_validate_qku_computation_control_plane_quantum.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain quantum","python tools/independent_validate_qku_computation_control_plane_quantum.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentQuantumAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::101"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"QuantumBenchmarkServiceV1","canonical_implementation_owner":"QuantumBenchmarkServiceV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-QUANTUM::008","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-QUANTUM::008","codex_online_research_allowed":false,"control_id":"ST11-QUANTUM::008","control_slug":"converter-compatibility","domain":"quantum","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_compiler.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_mapping_adapter.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_penalty.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_interpret_back.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_feasibility.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_comparator.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_fallback.py","tests/stage1_prediction_markets/qku_computation_control_plane/quantum/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_converter_compatibility.py","tools/independent_validate_qku_computation_control_plane_quantum.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain quantum","python tools/independent_validate_qku_computation_control_plane_quantum.py"],"implementation_specification":{"algorithm_or_rule":"Verify converter chains support the actual problem and preserve mapping/interpretation metadata. Classify original problem shape; map variables, objective and constraints with explicit scaling and penalties; interpret back; revalidate original-model feasibility; compare the same formulation to a classical baseline; fall back deterministically.","authority_boundary":"IMPLEMENTATION_OWNER=QuantumBenchmarkServiceV1; AUTHORITY_OWNER=QuantumBenchmarkServiceV1; INDEPENDENT_AUDITOR=IndependentQuantumAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"QuantumBenchmarkServiceV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QuantumBenchmarkServiceV1","codex_online_research_required":false,"consume_existing_owner_refs":["PR162E_Q_QUANTUM_AUTOMAPPER","QuantumBenchmarkServiceV1","QOPT1"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"DETERMINISTIC_SAME_FORMULATION_CLASSICAL_FALLBACK_OR_NO_TRADE","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_compiler.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_mapping_adapter.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_penalty.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_interpret_back.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_feasibility.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_comparator.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_fallback.py","tests/stage1_prediction_markets/qku_computation_control_plane/quantum/"],"implementation_disposition":"IMPLEMENT_READ_ONLY_MAPPER_COMPARATOR_AND_INTERPRET_BACK_ADAPTER_CONSUMING_MERGED_PR162E_Q; NO_QPU","implementation_owner":"QuantumBenchmarkServiceV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentQuantumAuditorV1","independent_validator_owner":"IndependentQuantumAuditorV1","input_contract":"original problem, mapping profile, variables, constraints, coefficients, backend/seed metadata","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"mapped candidate, interpreted result, original-model feasibility, same-formulation comparison and fallback receipt","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_QUANTUM_CONVERTER_COMPATIBILITY_PASS","ST12_QUANTUM_CONVERTER_COMPATIBILITY_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_converter_compatibility.py","tools/independent_validate_qku_computation_control_plane_quantum.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain quantum","python tools/independent_validate_qku_computation_control_plane_quantum.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentQuantumAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::101"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"QuantumBenchmarkServiceV1","canonical_implementation_owner":"QuantumBenchmarkServiceV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-QUANTUM::009","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-QUANTUM::009","codex_online_research_allowed":false,"control_id":"ST11-QUANTUM::009","control_slug":"interpret-back","domain":"quantum","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_compiler.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_mapping_adapter.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_penalty.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_interpret_back.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_feasibility.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_comparator.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_fallback.py","tests/stage1_prediction_markets/qku_computation_control_plane/quantum/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_interpret_back.py","tools/independent_validate_qku_computation_control_plane_quantum.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain quantum","python tools/independent_validate_qku_computation_control_plane_quantum.py"],"implementation_specification":{"algorithm_or_rule":"Verify each sample/result maps back to original variables, units, cash/economic outputs, and candidate identity. Classify original problem shape; map variables, objective and constraints with explicit scaling and penalties; interpret back; revalidate original-model feasibility; compare the same formulation to a classical baseline; fall back deterministically.","authority_boundary":"IMPLEMENTATION_OWNER=QuantumBenchmarkServiceV1; AUTHORITY_OWNER=QuantumBenchmarkServiceV1; INDEPENDENT_AUDITOR=IndependentQuantumAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"QuantumBenchmarkServiceV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QuantumBenchmarkServiceV1","codex_online_research_required":false,"consume_existing_owner_refs":["PR162E_Q_QUANTUM_AUTOMAPPER","QuantumBenchmarkServiceV1","QOPT1"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"DETERMINISTIC_SAME_FORMULATION_CLASSICAL_FALLBACK_OR_NO_TRADE","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_compiler.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_mapping_adapter.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_penalty.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_interpret_back.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_feasibility.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_comparator.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_fallback.py","tests/stage1_prediction_markets/qku_computation_control_plane/quantum/"],"implementation_disposition":"IMPLEMENT_READ_ONLY_MAPPER_COMPARATOR_AND_INTERPRET_BACK_ADAPTER_CONSUMING_MERGED_PR162E_Q; NO_QPU","implementation_owner":"QuantumBenchmarkServiceV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentQuantumAuditorV1","independent_validator_owner":"IndependentQuantumAuditorV1","input_contract":"original problem, mapping profile, variables, constraints, coefficients, backend/seed metadata","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"mapped candidate, interpreted result, original-model feasibility, same-formulation comparison and fallback receipt","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_QUANTUM_INTERPRET_BACK_PASS","ST12_QUANTUM_INTERPRET_BACK_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_interpret_back.py","tools/independent_validate_qku_computation_control_plane_quantum.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain quantum","python tools/independent_validate_qku_computation_control_plane_quantum.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentQuantumAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::101"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"QuantumBenchmarkServiceV1","canonical_implementation_owner":"QuantumBenchmarkServiceV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-QUANTUM::010","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-QUANTUM::010","codex_online_research_allowed":false,"control_id":"ST11-QUANTUM::010","control_slug":"original-model-feasibility","domain":"quantum","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_compiler.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_mapping_adapter.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_penalty.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_interpret_back.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_feasibility.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_comparator.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_fallback.py","tests/stage1_prediction_markets/qku_computation_control_plane/quantum/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_original_model_feasibility.py","tools/independent_validate_qku_computation_control_plane_quantum.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain quantum","python tools/independent_validate_qku_computation_control_plane_quantum.py"],"implementation_specification":{"algorithm_or_rule":"Independently revalidate all original constraints after interpret-back; converted-model feasibility alone is insufficient. Classify original problem shape; map variables, objective and constraints with explicit scaling and penalties; interpret back; revalidate original-model feasibility; compare the same formulation to a classical baseline; fall back deterministically.","authority_boundary":"IMPLEMENTATION_OWNER=QuantumBenchmarkServiceV1; AUTHORITY_OWNER=QuantumBenchmarkServiceV1; INDEPENDENT_AUDITOR=IndependentQuantumAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"QuantumBenchmarkServiceV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QuantumBenchmarkServiceV1","codex_online_research_required":false,"consume_existing_owner_refs":["PR162E_Q_QUANTUM_AUTOMAPPER","QuantumBenchmarkServiceV1","QOPT1"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"DETERMINISTIC_SAME_FORMULATION_CLASSICAL_FALLBACK_OR_NO_TRADE","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_compiler.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_mapping_adapter.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_penalty.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_interpret_back.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_feasibility.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_comparator.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_fallback.py","tests/stage1_prediction_markets/qku_computation_control_plane/quantum/"],"implementation_disposition":"IMPLEMENT_READ_ONLY_MAPPER_COMPARATOR_AND_INTERPRET_BACK_ADAPTER_CONSUMING_MERGED_PR162E_Q; NO_QPU","implementation_owner":"QuantumBenchmarkServiceV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentQuantumAuditorV1","independent_validator_owner":"IndependentQuantumAuditorV1","input_contract":"original problem, mapping profile, variables, constraints, coefficients, backend/seed metadata","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"mapped candidate, interpreted result, original-model feasibility, same-formulation comparison and fallback receipt","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_QUANTUM_ORIGINAL_MODEL_FEASIBILITY_PASS","ST12_QUANTUM_ORIGINAL_MODEL_FEASIBILITY_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_original_model_feasibility.py","tools/independent_validate_qku_computation_control_plane_quantum.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain quantum","python tools/independent_validate_qku_computation_control_plane_quantum.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentQuantumAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::101"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"QuantumBenchmarkServiceV1","canonical_implementation_owner":"QuantumBenchmarkServiceV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-QUANTUM::011","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-QUANTUM::011","codex_online_research_allowed":false,"control_id":"ST11-QUANTUM::011","control_slug":"same-formulation-comparator","domain":"quantum","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_compiler.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_mapping_adapter.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_penalty.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_interpret_back.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_feasibility.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_comparator.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_fallback.py","tests/stage1_prediction_markets/qku_computation_control_plane/quantum/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_same_formulation_comparator.py","tools/independent_validate_qku_computation_control_plane_quantum.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain quantum","python tools/independent_validate_qku_computation_control_plane_quantum.py"],"implementation_specification":{"algorithm_or_rule":"Verify strongest classical comparator uses the same objective, constraints, data lock, costs, and evaluation basis. Classify original problem shape; map variables, objective and constraints with explicit scaling and penalties; interpret back; revalidate original-model feasibility; compare the same formulation to a classical baseline; fall back deterministically.","authority_boundary":"IMPLEMENTATION_OWNER=QuantumBenchmarkServiceV1; AUTHORITY_OWNER=QuantumBenchmarkServiceV1; INDEPENDENT_AUDITOR=IndependentQuantumAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"QuantumBenchmarkServiceV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QuantumBenchmarkServiceV1","codex_online_research_required":false,"consume_existing_owner_refs":["PR162E_Q_QUANTUM_AUTOMAPPER","QuantumBenchmarkServiceV1","QOPT1"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"DETERMINISTIC_SAME_FORMULATION_CLASSICAL_FALLBACK_OR_NO_TRADE","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_compiler.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_mapping_adapter.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_penalty.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_interpret_back.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_feasibility.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_comparator.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_fallback.py","tests/stage1_prediction_markets/qku_computation_control_plane/quantum/"],"implementation_disposition":"IMPLEMENT_READ_ONLY_MAPPER_COMPARATOR_AND_INTERPRET_BACK_ADAPTER_CONSUMING_MERGED_PR162E_Q; NO_QPU","implementation_owner":"QuantumBenchmarkServiceV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentQuantumAuditorV1","independent_validator_owner":"IndependentQuantumAuditorV1","input_contract":"original problem, mapping profile, variables, constraints, coefficients, backend/seed metadata","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"mapped candidate, interpreted result, original-model feasibility, same-formulation comparison and fallback receipt","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_QUANTUM_SAME_FORMULATION_COMPARATOR_PASS","ST12_QUANTUM_SAME_FORMULATION_COMPARATOR_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_same_formulation_comparator.py","tools/independent_validate_qku_computation_control_plane_quantum.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain quantum","python tools/independent_validate_qku_computation_control_plane_quantum.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentQuantumAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::101"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"QuantumBenchmarkServiceV1","canonical_implementation_owner":"QuantumBenchmarkServiceV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-QUANTUM::012","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-QUANTUM::012","codex_online_research_allowed":false,"control_id":"ST11-QUANTUM::012","control_slug":"small-instance-oracle","domain":"quantum","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_compiler.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_mapping_adapter.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_penalty.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_interpret_back.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_feasibility.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_comparator.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_fallback.py","tests/stage1_prediction_markets/qku_computation_control_plane/quantum/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_small_instance_oracle.py","tools/independent_validate_qku_computation_control_plane_quantum.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain quantum","python tools/independent_validate_qku_computation_control_plane_quantum.py"],"implementation_specification":{"algorithm_or_rule":"Use brute-force or exact classical enumeration on bounded instances to validate mapping, penalties, energies, and interpretations. Classify original problem shape; map variables, objective and constraints with explicit scaling and penalties; interpret back; revalidate original-model feasibility; compare the same formulation to a classical baseline; fall back deterministically.","authority_boundary":"IMPLEMENTATION_OWNER=QuantumBenchmarkServiceV1; AUTHORITY_OWNER=QuantumBenchmarkServiceV1; INDEPENDENT_AUDITOR=IndependentQuantumAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"QuantumBenchmarkServiceV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QuantumBenchmarkServiceV1","codex_online_research_required":false,"consume_existing_owner_refs":["PR162E_Q_QUANTUM_AUTOMAPPER","QuantumBenchmarkServiceV1","QOPT1"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"DETERMINISTIC_SAME_FORMULATION_CLASSICAL_FALLBACK_OR_NO_TRADE","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_compiler.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_mapping_adapter.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_penalty.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_interpret_back.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_feasibility.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_comparator.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_fallback.py","tests/stage1_prediction_markets/qku_computation_control_plane/quantum/"],"implementation_disposition":"IMPLEMENT_READ_ONLY_MAPPER_COMPARATOR_AND_INTERPRET_BACK_ADAPTER_CONSUMING_MERGED_PR162E_Q; NO_QPU","implementation_owner":"QuantumBenchmarkServiceV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentQuantumAuditorV1","independent_validator_owner":"IndependentQuantumAuditorV1","input_contract":"original problem, mapping profile, variables, constraints, coefficients, backend/seed metadata","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"mapped candidate, interpreted result, original-model feasibility, same-formulation comparison and fallback receipt","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_QUANTUM_SMALL_INSTANCE_ORACLE_PASS","ST12_QUANTUM_SMALL_INSTANCE_ORACLE_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_small_instance_oracle.py","tools/independent_validate_qku_computation_control_plane_quantum.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain quantum","python tools/independent_validate_qku_computation_control_plane_quantum.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentQuantumAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::101"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"QuantumBenchmarkServiceV1","canonical_implementation_owner":"QuantumBenchmarkServiceV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-QUANTUM::013","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-QUANTUM::013","codex_online_research_allowed":false,"control_id":"ST11-QUANTUM::013","control_slug":"maturity-state-separation","domain":"quantum","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_compiler.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_mapping_adapter.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_penalty.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_interpret_back.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_feasibility.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_comparator.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_fallback.py","tests/stage1_prediction_markets/qku_computation_control_plane/quantum/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_maturity_state_separation.py","tools/independent_validate_qku_computation_control_plane_quantum.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain quantum","python tools/independent_validate_qku_computation_control_plane_quantum.py"],"implementation_specification":{"algorithm_or_rule":"Verify specified, mapped, simulator, noisy, QPU, feasible, economic-utility, snapshot, and allow states are never inferred. Classify original problem shape; map variables, objective and constraints with explicit scaling and penalties; interpret back; revalidate original-model feasibility; compare the same formulation to a classical baseline; fall back deterministically.","authority_boundary":"IMPLEMENTATION_OWNER=QuantumBenchmarkServiceV1; AUTHORITY_OWNER=QuantumBenchmarkServiceV1; INDEPENDENT_AUDITOR=IndependentQuantumAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"QuantumBenchmarkServiceV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QuantumBenchmarkServiceV1","codex_online_research_required":false,"consume_existing_owner_refs":["PR162E_Q_QUANTUM_AUTOMAPPER","QuantumBenchmarkServiceV1","QOPT1"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"DETERMINISTIC_SAME_FORMULATION_CLASSICAL_FALLBACK_OR_NO_TRADE","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_compiler.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_mapping_adapter.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_penalty.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_interpret_back.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_feasibility.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_comparator.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_fallback.py","tests/stage1_prediction_markets/qku_computation_control_plane/quantum/"],"implementation_disposition":"IMPLEMENT_READ_ONLY_MAPPER_COMPARATOR_AND_INTERPRET_BACK_ADAPTER_CONSUMING_MERGED_PR162E_Q; NO_QPU","implementation_owner":"QuantumBenchmarkServiceV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentQuantumAuditorV1","independent_validator_owner":"IndependentQuantumAuditorV1","input_contract":"original problem, mapping profile, variables, constraints, coefficients, backend/seed metadata","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"mapped candidate, interpreted result, original-model feasibility, same-formulation comparison and fallback receipt","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_QUANTUM_MATURITY_STATE_SEPARATION_PASS","ST12_QUANTUM_MATURITY_STATE_SEPARATION_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_maturity_state_separation.py","tools/independent_validate_qku_computation_control_plane_quantum.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain quantum","python tools/independent_validate_qku_computation_control_plane_quantum.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentQuantumAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::101"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"QuantumBenchmarkServiceV1","canonical_implementation_owner":"QuantumBenchmarkServiceV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-QUANTUM::014","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-QUANTUM::014","codex_online_research_allowed":false,"control_id":"ST11-QUANTUM::014","control_slug":"sample-frequency-boundary","domain":"quantum","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_compiler.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_mapping_adapter.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_penalty.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_interpret_back.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_feasibility.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_comparator.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_fallback.py","tests/stage1_prediction_markets/qku_computation_control_plane/quantum/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_sample_frequency_boundary.py","tools/independent_validate_qku_computation_control_plane_quantum.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain quantum","python tools/independent_validate_qku_computation_control_plane_quantum.py"],"implementation_specification":{"algorithm_or_rule":"Verify sample frequency is not treated as market probability, fill probability, confidence, or profit probability. Classify original problem shape; map variables, objective and constraints with explicit scaling and penalties; interpret back; revalidate original-model feasibility; compare the same formulation to a classical baseline; fall back deterministically.","authority_boundary":"IMPLEMENTATION_OWNER=QuantumBenchmarkServiceV1; AUTHORITY_OWNER=QuantumBenchmarkServiceV1; INDEPENDENT_AUDITOR=IndependentQuantumAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"QuantumBenchmarkServiceV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QuantumBenchmarkServiceV1","codex_online_research_required":false,"consume_existing_owner_refs":["PR162E_Q_QUANTUM_AUTOMAPPER","QuantumBenchmarkServiceV1","QOPT1"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"DETERMINISTIC_SAME_FORMULATION_CLASSICAL_FALLBACK_OR_NO_TRADE","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_compiler.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_mapping_adapter.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_penalty.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_interpret_back.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_feasibility.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_comparator.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_fallback.py","tests/stage1_prediction_markets/qku_computation_control_plane/quantum/"],"implementation_disposition":"IMPLEMENT_READ_ONLY_MAPPER_COMPARATOR_AND_INTERPRET_BACK_ADAPTER_CONSUMING_MERGED_PR162E_Q; NO_QPU","implementation_owner":"QuantumBenchmarkServiceV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentQuantumAuditorV1","independent_validator_owner":"IndependentQuantumAuditorV1","input_contract":"original problem, mapping profile, variables, constraints, coefficients, backend/seed metadata","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"mapped candidate, interpreted result, original-model feasibility, same-formulation comparison and fallback receipt","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_QUANTUM_SAMPLE_FREQUENCY_BOUNDARY_PASS","ST12_QUANTUM_SAMPLE_FREQUENCY_BOUNDARY_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_sample_frequency_boundary.py","tools/independent_validate_qku_computation_control_plane_quantum.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain quantum","python tools/independent_validate_qku_computation_control_plane_quantum.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentQuantumAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::101"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"SecurityComplianceBoundaryV1","canonical_implementation_owner":"QKUComputationControlPlaneV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-SECURITY::008","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-SECURITY::008","codex_online_research_allowed":false,"control_id":"ST11-SECURITY::008","control_slug":"sql-and-path-safety","domain":"security","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/capability_guard.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/boundary_validation.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/path_safety.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/redaction.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/security_policy.py","tests/stage1_prediction_markets/qku_computation_control_plane/security/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/security/test_sql_and_path_safety.py","tools/independent_validate_qku_computation_control_plane_security.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain security","python tools/independent_validate_qku_computation_control_plane_security.py"],"implementation_specification":{"algorithm_or_rule":"Verify parameterized SQL, safe paths, explicit schema ownership, no traversal, and no foreign-root writes. Apply default deny, least privilege, strict schema and path validation, redaction, bounded resources, replay protection, submit-disable and kill-state checks before any authority-sensitive transition.","authority_boundary":"IMPLEMENTATION_OWNER=QKUComputationControlPlaneV1; AUTHORITY_OWNER=SecurityComplianceBoundaryV1; INDEPENDENT_AUDITOR=IndependentSecurityAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"SecurityComplianceBoundaryV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"consume_existing_owner_refs":["AgentCapabilityResolverV1","KillSwitchControllerV1","SecurityComplianceBoundaryV1","VAL1"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"DENY_OPERATION_QUARANTINE_INPUT_AND_PRESERVE_AUDIT_RECEIPT","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/capability_guard.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/boundary_validation.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/path_safety.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/redaction.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/security_policy.py","tests/stage1_prediction_markets/qku_computation_control_plane/security/"],"implementation_disposition":"IMPLEMENT_BOUNDED_DEFAULT_DENY_SECURITY_BOUNDARY_IN_EXISTING_CONTROL_PLANE","implementation_owner":"QKUComputationControlPlaneV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentSecurityAuditorV1","independent_validator_owner":"IndependentSecurityAuditorV1","input_contract":"typed principals, capability bundles, untrusted inputs, source packets, owner requests","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"default-deny decisions, structured denials, redacted audit receipts, kill/submit-disable states","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_SECURITY_SQL_AND_PATH_SAFETY_PASS","ST12_SECURITY_SQL_AND_PATH_SAFETY_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/security/test_sql_and_path_safety.py","tools/independent_validate_qku_computation_control_plane_security.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain security","python tools/independent_validate_qku_computation_control_plane_security.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentSecurityAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":[],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"SecurityComplianceBoundaryV1","canonical_implementation_owner":"QKUComputationControlPlaneV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-SECURITY::009","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-SECURITY::009","codex_online_research_allowed":false,"control_id":"ST11-SECURITY::009","control_slug":"output-handling","domain":"security","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/capability_guard.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/boundary_validation.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/path_safety.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/redaction.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/security_policy.py","tests/stage1_prediction_markets/qku_computation_control_plane/security/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/security/test_output_handling.py","tools/independent_validate_qku_computation_control_plane_security.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain security","python tools/independent_validate_qku_computation_control_plane_security.py"],"implementation_specification":{"algorithm_or_rule":"Verify LLM, provider, solver, and external tool outputs are typed and cannot directly drive code, SQL, configuration, or orders. Apply default deny, least privilege, strict schema and path validation, redaction, bounded resources, replay protection, submit-disable and kill-state checks before any authority-sensitive transition.","authority_boundary":"IMPLEMENTATION_OWNER=QKUComputationControlPlaneV1; AUTHORITY_OWNER=SecurityComplianceBoundaryV1; INDEPENDENT_AUDITOR=IndependentSecurityAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"SecurityComplianceBoundaryV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"consume_existing_owner_refs":["AgentCapabilityResolverV1","KillSwitchControllerV1","SecurityComplianceBoundaryV1","VAL1"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"DENY_OPERATION_QUARANTINE_INPUT_AND_PRESERVE_AUDIT_RECEIPT","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/capability_guard.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/boundary_validation.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/path_safety.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/redaction.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/security_policy.py","tests/stage1_prediction_markets/qku_computation_control_plane/security/"],"implementation_disposition":"IMPLEMENT_BOUNDED_DEFAULT_DENY_SECURITY_BOUNDARY_IN_EXISTING_CONTROL_PLANE","implementation_owner":"QKUComputationControlPlaneV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentSecurityAuditorV1","independent_validator_owner":"IndependentSecurityAuditorV1","input_contract":"typed principals, capability bundles, untrusted inputs, source packets, owner requests","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"default-deny decisions, structured denials, redacted audit receipts, kill/submit-disable states","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_SECURITY_OUTPUT_HANDLING_PASS","ST12_SECURITY_OUTPUT_HANDLING_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/security/test_output_handling.py","tools/independent_validate_qku_computation_control_plane_security.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain security","python tools/independent_validate_qku_computation_control_plane_security.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentSecurityAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":[],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"SecurityComplianceBoundaryV1","canonical_implementation_owner":"QKUComputationControlPlaneV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-SECURITY::010","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-SECURITY::010","codex_online_research_allowed":false,"control_id":"ST11-SECURITY::010","control_slug":"supply-chain-provenance","domain":"security","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/capability_guard.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/boundary_validation.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/path_safety.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/redaction.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/security_policy.py","tests/stage1_prediction_markets/qku_computation_control_plane/security/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/security/test_supply_chain_provenance.py","tools/independent_validate_qku_computation_control_plane_security.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain security","python tools/independent_validate_qku_computation_control_plane_security.py"],"implementation_specification":{"algorithm_or_rule":"Verify pinned dependencies, final-vs-draft standard status, vulnerability review, license/rights review, and SBOM-ready ownership. Apply default deny, least privilege, strict schema and path validation, redaction, bounded resources, replay protection, submit-disable and kill-state checks before any authority-sensitive transition.","authority_boundary":"IMPLEMENTATION_OWNER=QKUComputationControlPlaneV1; AUTHORITY_OWNER=SecurityComplianceBoundaryV1; INDEPENDENT_AUDITOR=IndependentSecurityAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"SecurityComplianceBoundaryV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"consume_existing_owner_refs":["AgentCapabilityResolverV1","KillSwitchControllerV1","SecurityComplianceBoundaryV1","VAL1"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"DENY_OPERATION_QUARANTINE_INPUT_AND_PRESERVE_AUDIT_RECEIPT","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/capability_guard.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/boundary_validation.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/path_safety.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/redaction.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/security_policy.py","tests/stage1_prediction_markets/qku_computation_control_plane/security/"],"implementation_disposition":"IMPLEMENT_BOUNDED_DEFAULT_DENY_SECURITY_BOUNDARY_IN_EXISTING_CONTROL_PLANE","implementation_owner":"QKUComputationControlPlaneV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentSecurityAuditorV1","independent_validator_owner":"IndependentSecurityAuditorV1","input_contract":"typed principals, capability bundles, untrusted inputs, source packets, owner requests","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"default-deny decisions, structured denials, redacted audit receipts, kill/submit-disable states","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_SECURITY_SUPPLY_CHAIN_PROVENANCE_PASS","ST12_SECURITY_SUPPLY_CHAIN_PROVENANCE_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/security/test_supply_chain_provenance.py","tools/independent_validate_qku_computation_control_plane_security.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain security","python tools/independent_validate_qku_computation_control_plane_security.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentSecurityAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":[],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"SourceCurrentizationOwnerV1","canonical_implementation_owner":"SourceCurrentizationOwnerV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-SOURCE::006","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-SOURCE::006","codex_online_research_allowed":false,"control_id":"ST11-SOURCE::006","control_slug":"future-dated-content","domain":"source","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_binding.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_epochs.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_rights.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/provider_profiles.py","tests/stage1_prediction_markets/qku_computation_control_plane/source/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/source/test_future_dated_content.py","tools/independent_validate_qku_computation_control_plane_source.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain source","python tools/independent_validate_qku_computation_control_plane_source.py"],"implementation_specification":{"algorithm_or_rule":"Exclude future-effective or not-yet-active facts from current implementation while preserving dated future epochs. Bind atomic facts to exact source, effective epoch, rights, freshness and conflict state; prefer direct current primary sources; exclude future epochs; fail closed until SourceCurrentizationOwnerV1 revalidates.","authority_boundary":"IMPLEMENTATION_OWNER=SourceCurrentizationOwnerV1; AUTHORITY_OWNER=SourceCurrentizationOwnerV1; INDEPENDENT_AUDITOR=IndependentSourceAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"SourceCurrentizationOwnerV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"SourceCurrentizationOwnerV1","codex_online_research_required":false,"consume_existing_owner_refs":["SourceCurrentizationOwnerV1","Step10R5SourceStateRegistry"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"UNAVAILABLE_FAIL_CLOSED_UNTIL_SOURCE_CURRENTIZATION_OWNER_REVALIDATES","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_binding.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_epochs.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_rights.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/provider_profiles.py","tests/stage1_prediction_markets/qku_computation_control_plane/source/"],"implementation_disposition":"IMPLEMENT_EXACT_VERSIONED_SOURCE_BINDINGS_FROM_OWNER_RESOLVED_VALUES; FUTURE_REFRESH_BY_SOURCE_CURRENTIZATION_OWNER","implementation_owner":"SourceCurrentizationOwnerV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentSourceAuditorV1","independent_validator_owner":"IndependentSourceAuditorV1","input_contract":"direct primary-source captures and effective epochs","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"versioned provider/method bindings with rights, freshness, conflict and recheck policy","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_SOURCE_FUTURE_DATED_CONTENT_PASS","ST12_SOURCE_FUTURE_DATED_CONTENT_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/source/test_future_dated_content.py","tools/independent_validate_qku_computation_control_plane_source.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain source","python tools/independent_validate_qku_computation_control_plane_source.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentSourceAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::102"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"SourceCurrentizationOwnerV1","canonical_implementation_owner":"SourceCurrentizationOwnerV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-SOURCE::007","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-SOURCE::007","codex_online_research_allowed":false,"control_id":"ST11-SOURCE::007","control_slug":"category-vs-market","domain":"source","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_binding.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_epochs.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_rights.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/provider_profiles.py","tests/stage1_prediction_markets/qku_computation_control_plane/source/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/source/test_category_vs_market.py","tools/independent_validate_qku_computation_control_plane_source.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain source","python tools/independent_validate_qku_computation_control_plane_source.py"],"implementation_specification":{"algorithm_or_rule":"Verify category defaults cannot override exact per-market configuration and record the precedence explicitly. Bind atomic facts to exact source, effective epoch, rights, freshness and conflict state; prefer direct current primary sources; exclude future epochs; fail closed until SourceCurrentizationOwnerV1 revalidates.","authority_boundary":"IMPLEMENTATION_OWNER=SourceCurrentizationOwnerV1; AUTHORITY_OWNER=SourceCurrentizationOwnerV1; INDEPENDENT_AUDITOR=IndependentSourceAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"SourceCurrentizationOwnerV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"SourceCurrentizationOwnerV1","codex_online_research_required":false,"consume_existing_owner_refs":["SourceCurrentizationOwnerV1","Step10R5SourceStateRegistry"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"UNAVAILABLE_FAIL_CLOSED_UNTIL_SOURCE_CURRENTIZATION_OWNER_REVALIDATES","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_binding.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_epochs.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_rights.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/provider_profiles.py","tests/stage1_prediction_markets/qku_computation_control_plane/source/"],"implementation_disposition":"IMPLEMENT_EXACT_VERSIONED_SOURCE_BINDINGS_FROM_OWNER_RESOLVED_VALUES; FUTURE_REFRESH_BY_SOURCE_CURRENTIZATION_OWNER","implementation_owner":"SourceCurrentizationOwnerV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentSourceAuditorV1","independent_validator_owner":"IndependentSourceAuditorV1","input_contract":"direct primary-source captures and effective epochs","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"versioned provider/method bindings with rights, freshness, conflict and recheck policy","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_SOURCE_CATEGORY_VS_MARKET_PASS","ST12_SOURCE_CATEGORY_VS_MARKET_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/source/test_category_vs_market.py","tools/independent_validate_qku_computation_control_plane_source.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain source","python tools/independent_validate_qku_computation_control_plane_source.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentSourceAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::102"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"SourceCurrentizationOwnerV1","canonical_implementation_owner":"SourceCurrentizationOwnerV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-SOURCE::008","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-SOURCE::008","codex_online_research_allowed":false,"control_id":"ST11-SOURCE::008","control_slug":"cached-search-rejection","domain":"source","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_binding.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_epochs.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_rights.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/provider_profiles.py","tests/stage1_prediction_markets/qku_computation_control_plane/source/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/source/test_cached_search_rejection.py","tools/independent_validate_qku_computation_control_plane_source.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain source","python tools/independent_validate_qku_computation_control_plane_source.py"],"implementation_specification":{"algorithm_or_rule":"Reject stale search snippets, secondary summaries, or cached pages when they conflict with direct official material. Bind atomic facts to exact source, effective epoch, rights, freshness and conflict state; prefer direct current primary sources; exclude future epochs; fail closed until SourceCurrentizationOwnerV1 revalidates.","authority_boundary":"IMPLEMENTATION_OWNER=SourceCurrentizationOwnerV1; AUTHORITY_OWNER=SourceCurrentizationOwnerV1; INDEPENDENT_AUDITOR=IndependentSourceAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"SourceCurrentizationOwnerV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"SourceCurrentizationOwnerV1","codex_online_research_required":false,"consume_existing_owner_refs":["SourceCurrentizationOwnerV1","Step10R5SourceStateRegistry"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"UNAVAILABLE_FAIL_CLOSED_UNTIL_SOURCE_CURRENTIZATION_OWNER_REVALIDATES","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_binding.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_epochs.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_rights.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/provider_profiles.py","tests/stage1_prediction_markets/qku_computation_control_plane/source/"],"implementation_disposition":"IMPLEMENT_EXACT_VERSIONED_SOURCE_BINDINGS_FROM_OWNER_RESOLVED_VALUES; FUTURE_REFRESH_BY_SOURCE_CURRENTIZATION_OWNER","implementation_owner":"SourceCurrentizationOwnerV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentSourceAuditorV1","independent_validator_owner":"IndependentSourceAuditorV1","input_contract":"direct primary-source captures and effective epochs","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"versioned provider/method bindings with rights, freshness, conflict and recheck policy","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_SOURCE_CACHED_SEARCH_REJECTION_PASS","ST12_SOURCE_CACHED_SEARCH_REJECTION_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/source/test_cached_search_rejection.py","tools/independent_validate_qku_computation_control_plane_source.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain source","python tools/independent_validate_qku_computation_control_plane_source.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentSourceAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::102"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"SourceCurrentizationOwnerV1","canonical_implementation_owner":"SourceCurrentizationOwnerV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-SOURCE::009","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-SOURCE::009","codex_online_research_allowed":false,"control_id":"ST11-SOURCE::009","control_slug":"url-and-document-drift","domain":"source","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_binding.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_epochs.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_rights.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/provider_profiles.py","tests/stage1_prediction_markets/qku_computation_control_plane/source/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/source/test_url_and_document_drift.py","tools/independent_validate_qku_computation_control_plane_source.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain source","python tools/independent_validate_qku_computation_control_plane_source.py"],"implementation_specification":{"algorithm_or_rule":"Detect redirects, moved pages, changed anchors, deprecated versions, and replacement documentation. Bind atomic facts to exact source, effective epoch, rights, freshness and conflict state; prefer direct current primary sources; exclude future epochs; fail closed until SourceCurrentizationOwnerV1 revalidates.","authority_boundary":"IMPLEMENTATION_OWNER=SourceCurrentizationOwnerV1; AUTHORITY_OWNER=SourceCurrentizationOwnerV1; INDEPENDENT_AUDITOR=IndependentSourceAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"SourceCurrentizationOwnerV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"SourceCurrentizationOwnerV1","codex_online_research_required":false,"consume_existing_owner_refs":["SourceCurrentizationOwnerV1","Step10R5SourceStateRegistry"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"UNAVAILABLE_FAIL_CLOSED_UNTIL_SOURCE_CURRENTIZATION_OWNER_REVALIDATES","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_binding.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_epochs.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_rights.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/provider_profiles.py","tests/stage1_prediction_markets/qku_computation_control_plane/source/"],"implementation_disposition":"IMPLEMENT_EXACT_VERSIONED_SOURCE_BINDINGS_FROM_OWNER_RESOLVED_VALUES; FUTURE_REFRESH_BY_SOURCE_CURRENTIZATION_OWNER","implementation_owner":"SourceCurrentizationOwnerV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentSourceAuditorV1","independent_validator_owner":"IndependentSourceAuditorV1","input_contract":"direct primary-source captures and effective epochs","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"versioned provider/method bindings with rights, freshness, conflict and recheck policy","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_SOURCE_URL_AND_DOCUMENT_DRIFT_PASS","ST12_SOURCE_URL_AND_DOCUMENT_DRIFT_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/source/test_url_and_document_drift.py","tools/independent_validate_qku_computation_control_plane_source.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain source","python tools/independent_validate_qku_computation_control_plane_source.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentSourceAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::102"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"SourceCurrentizationOwnerV1","canonical_implementation_owner":"SourceCurrentizationOwnerV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-SOURCE::010","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-SOURCE::010","codex_online_research_allowed":false,"control_id":"ST11-SOURCE::010","control_slug":"data-grade-classification","domain":"source","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_binding.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_epochs.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_rights.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/provider_profiles.py","tests/stage1_prediction_markets/qku_computation_control_plane/source/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/source/test_data_grade_classification.py","tools/independent_validate_qku_computation_control_plane_source.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain source","python tools/independent_validate_qku_computation_control_plane_source.py"],"implementation_specification":{"algorithm_or_rule":"Classify each interface as current aggregate book, authenticated stream, trade tape, bars, private state, order write, or other exact grade. Bind atomic facts to exact source, effective epoch, rights, freshness and conflict state; prefer direct current primary sources; exclude future epochs; fail closed until SourceCurrentizationOwnerV1 revalidates.","authority_boundary":"IMPLEMENTATION_OWNER=SourceCurrentizationOwnerV1; AUTHORITY_OWNER=SourceCurrentizationOwnerV1; INDEPENDENT_AUDITOR=IndependentSourceAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"SourceCurrentizationOwnerV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"SourceCurrentizationOwnerV1","codex_online_research_required":false,"consume_existing_owner_refs":["SourceCurrentizationOwnerV1","Step10R5SourceStateRegistry"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"UNAVAILABLE_FAIL_CLOSED_UNTIL_SOURCE_CURRENTIZATION_OWNER_REVALIDATES","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_binding.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_epochs.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_rights.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/provider_profiles.py","tests/stage1_prediction_markets/qku_computation_control_plane/source/"],"implementation_disposition":"IMPLEMENT_EXACT_VERSIONED_SOURCE_BINDINGS_FROM_OWNER_RESOLVED_VALUES; FUTURE_REFRESH_BY_SOURCE_CURRENTIZATION_OWNER","implementation_owner":"SourceCurrentizationOwnerV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentSourceAuditorV1","independent_validator_owner":"IndependentSourceAuditorV1","input_contract":"direct primary-source captures and effective epochs","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"versioned provider/method bindings with rights, freshness, conflict and recheck policy","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_SOURCE_DATA_GRADE_CLASSIFICATION_PASS","ST12_SOURCE_DATA_GRADE_CLASSIFICATION_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/source/test_data_grade_classification.py","tools/independent_validate_qku_computation_control_plane_source.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain source","python tools/independent_validate_qku_computation_control_plane_source.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentSourceAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::102"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"SourceCurrentizationOwnerV1","canonical_implementation_owner":"SourceCurrentizationOwnerV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-SOURCE::011","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-SOURCE::011","codex_online_research_allowed":false,"control_id":"ST11-SOURCE::011","control_slug":"kalshi-currentness","domain":"source","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_binding.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_epochs.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_rights.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/provider_profiles.py","tests/stage1_prediction_markets/qku_computation_control_plane/source/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/source/test_kalshi_currentness.py","tools/independent_validate_qku_computation_control_plane_source.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain source","python tools/independent_validate_qku_computation_control_plane_source.py"],"implementation_specification":{"algorithm_or_rule":"Revalidate Kalshi historical routing, orderbook, websocket, fees, fixed-point migration, incentives, and changelog facts. Bind atomic facts to exact source, effective epoch, rights, freshness and conflict state; prefer direct current primary sources; exclude future epochs; fail closed until SourceCurrentizationOwnerV1 revalidates.","authority_boundary":"IMPLEMENTATION_OWNER=SourceCurrentizationOwnerV1; AUTHORITY_OWNER=SourceCurrentizationOwnerV1; INDEPENDENT_AUDITOR=IndependentSourceAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"SourceCurrentizationOwnerV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"SourceCurrentizationOwnerV1","codex_online_research_required":false,"consume_existing_owner_refs":["SourceCurrentizationOwnerV1","Step10R5SourceStateRegistry"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"UNAVAILABLE_FAIL_CLOSED_UNTIL_SOURCE_CURRENTIZATION_OWNER_REVALIDATES","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_binding.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_epochs.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_rights.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/provider_profiles.py","tests/stage1_prediction_markets/qku_computation_control_plane/source/"],"implementation_disposition":"IMPLEMENT_EXACT_VERSIONED_SOURCE_BINDINGS_FROM_OWNER_RESOLVED_VALUES; FUTURE_REFRESH_BY_SOURCE_CURRENTIZATION_OWNER","implementation_owner":"SourceCurrentizationOwnerV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentSourceAuditorV1","independent_validator_owner":"IndependentSourceAuditorV1","input_contract":"direct primary-source captures and effective epochs","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"versioned provider/method bindings with rights, freshness, conflict and recheck policy","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_SOURCE_KALSHI_CURRENTNESS_PASS","ST12_SOURCE_KALSHI_CURRENTNESS_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/source/test_kalshi_currentness.py","tools/independent_validate_qku_computation_control_plane_source.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain source","python tools/independent_validate_qku_computation_control_plane_source.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentSourceAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::102"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"SourceCurrentizationOwnerV1","canonical_implementation_owner":"SourceCurrentizationOwnerV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-SOURCE::012","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-SOURCE::012","codex_online_research_allowed":false,"control_id":"ST11-SOURCE::012","control_slug":"polymarket-global-currentness","domain":"source","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_binding.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_epochs.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_rights.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/provider_profiles.py","tests/stage1_prediction_markets/qku_computation_control_plane/source/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/source/test_polymarket_global_currentness.py","tools/independent_validate_qku_computation_control_plane_source.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain source","python tools/independent_validate_qku_computation_control_plane_source.py"],"implementation_specification":{"algorithm_or_rule":"Revalidate Global CLOB endpoints, fees, rate limits, retention, heartbeat, websocket, collateral, and order semantics. Bind atomic facts to exact source, effective epoch, rights, freshness and conflict state; prefer direct current primary sources; exclude future epochs; fail closed until SourceCurrentizationOwnerV1 revalidates.","authority_boundary":"IMPLEMENTATION_OWNER=SourceCurrentizationOwnerV1; AUTHORITY_OWNER=SourceCurrentizationOwnerV1; INDEPENDENT_AUDITOR=IndependentSourceAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"SourceCurrentizationOwnerV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"SourceCurrentizationOwnerV1","codex_online_research_required":false,"consume_existing_owner_refs":["SourceCurrentizationOwnerV1","Step10R5SourceStateRegistry"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"UNAVAILABLE_FAIL_CLOSED_UNTIL_SOURCE_CURRENTIZATION_OWNER_REVALIDATES","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_binding.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_epochs.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_rights.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/provider_profiles.py","tests/stage1_prediction_markets/qku_computation_control_plane/source/"],"implementation_disposition":"IMPLEMENT_EXACT_VERSIONED_SOURCE_BINDINGS_FROM_OWNER_RESOLVED_VALUES; FUTURE_REFRESH_BY_SOURCE_CURRENTIZATION_OWNER","implementation_owner":"SourceCurrentizationOwnerV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentSourceAuditorV1","independent_validator_owner":"IndependentSourceAuditorV1","input_contract":"direct primary-source captures and effective epochs","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"versioned provider/method bindings with rights, freshness, conflict and recheck policy","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_SOURCE_POLYMARKET_GLOBAL_CURRENTNESS_PASS","ST12_SOURCE_POLYMARKET_GLOBAL_CURRENTNESS_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/source/test_polymarket_global_currentness.py","tools/independent_validate_qku_computation_control_plane_source.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain source","python tools/independent_validate_qku_computation_control_plane_source.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentSourceAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::102"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"SourceCurrentizationOwnerV1","canonical_implementation_owner":"SourceCurrentizationOwnerV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-SOURCE::013","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-SOURCE::013","codex_online_research_allowed":false,"control_id":"ST11-SOURCE::013","control_slug":"polymarket-us-currentness","domain":"source","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_binding.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_epochs.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_rights.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/provider_profiles.py","tests/stage1_prediction_markets/qku_computation_control_plane/source/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/source/test_polymarket_us_currentness.py","tools/independent_validate_qku_computation_control_plane_source.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain source","python tools/independent_validate_qku_computation_control_plane_source.py"],"implementation_specification":{"algorithm_or_rule":"Revalidate US fees, maintenance, API limits, market data, order lifecycle, rounding, and effective dates. Bind atomic facts to exact source, effective epoch, rights, freshness and conflict state; prefer direct current primary sources; exclude future epochs; fail closed until SourceCurrentizationOwnerV1 revalidates.","authority_boundary":"IMPLEMENTATION_OWNER=SourceCurrentizationOwnerV1; AUTHORITY_OWNER=SourceCurrentizationOwnerV1; INDEPENDENT_AUDITOR=IndependentSourceAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"SourceCurrentizationOwnerV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"SourceCurrentizationOwnerV1","codex_online_research_required":false,"consume_existing_owner_refs":["SourceCurrentizationOwnerV1","Step10R5SourceStateRegistry"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"UNAVAILABLE_FAIL_CLOSED_UNTIL_SOURCE_CURRENTIZATION_OWNER_REVALIDATES","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_binding.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_epochs.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_rights.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/provider_profiles.py","tests/stage1_prediction_markets/qku_computation_control_plane/source/"],"implementation_disposition":"IMPLEMENT_EXACT_VERSIONED_SOURCE_BINDINGS_FROM_OWNER_RESOLVED_VALUES; FUTURE_REFRESH_BY_SOURCE_CURRENTIZATION_OWNER","implementation_owner":"SourceCurrentizationOwnerV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentSourceAuditorV1","independent_validator_owner":"IndependentSourceAuditorV1","input_contract":"direct primary-source captures and effective epochs","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"versioned provider/method bindings with rights, freshness, conflict and recheck policy","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_SOURCE_POLYMARKET_US_CURRENTNESS_PASS","ST12_SOURCE_POLYMARKET_US_CURRENTNESS_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/source/test_polymarket_us_currentness.py","tools/independent_validate_qku_computation_control_plane_source.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain source","python tools/independent_validate_qku_computation_control_plane_source.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentSourceAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::102"],"step12_primary_tranche_id":"ST12-TRANCHE-B"},{"authority_owner":"SourceCurrentizationOwnerV1","canonical_implementation_owner":"SourceCurrentizationOwnerV1","certified_step11_custody_ref":"inputs/certified_step11/QTT_Stage1_Step11_To_Step12_Implementation_Closure_Ledger_v1_0.jsonl#ST12-CLOSURE::ST11-SOURCE::014","certified_step11_row_embedded_in_prompt":false,"closure_id":"ST12-CLOSURE::ST11-SOURCE::014","codex_online_research_allowed":false,"control_id":"ST11-SOURCE::014","control_slug":"ibkr-forecastex-currentness","domain":"source","exact_repository_target_paths":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_binding.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_epochs.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_rights.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/provider_profiles.py","tests/stage1_prediction_markets/qku_computation_control_plane/source/"],"exact_test_paths":["tests/stage1_prediction_markets/qku_computation_control_plane/source/test_ibkr_forecastex_currentness.py","tools/independent_validate_qku_computation_control_plane_source.py"],"exact_validation_commands":["python tools/validate_qku_computation_control_plane.py --domain source","python tools/independent_validate_qku_computation_control_plane_source.py"],"implementation_specification":{"algorithm_or_rule":"Revalidate ForecastEx/IBKR interface, BUY-only opposing-contract close, TIF, limits, and settlement semantics. Bind atomic facts to exact source, effective epoch, rights, freshness and conflict state; prefer direct current primary sources; exclude future epochs; fail closed until SourceCurrentizationOwnerV1 revalidates.","authority_boundary":"IMPLEMENTATION_OWNER=SourceCurrentizationOwnerV1; AUTHORITY_OWNER=SourceCurrentizationOwnerV1; INDEPENDENT_AUDITOR=IndependentSourceAuditorV1; NO_OWNER_MAY_ABSORB_ANOTHER_AUTHORITY_DOMAIN; NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_QPU_PROFIT_OR_CRYPTOGRAPHIC_AUTHORITY_WITHOUT_LATER_EXPLICIT_OWNER_AUTHORIZATION","authority_owner":"SourceCurrentizationOwnerV1","bounded_scope":"STEP12_IMPLEMENTATION_ONLY_NO_PROVIDER_PRIVATE_STATE_REPLAY_PAPER_LIVE_ORDER_OR_QPU_EFFECT_WITHOUT_SEPARATE_OWNER_AUTHORIZATION","canonical_owner":"SourceCurrentizationOwnerV1","codex_online_research_required":false,"consume_existing_owner_refs":["SourceCurrentizationOwnerV1","Step10R5SourceStateRegistry"],"failure_behavior":"FAIL_CLOSED_WITH_TYPED_REASON_AND_NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_PROFIT_EFFECT","fallback":"UNAVAILABLE_FAIL_CLOSED_UNTIL_SOURCE_CURRENTIZATION_OWNER_REVALIDATES","files":["src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_binding.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_epochs.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_rights.py","src/qtt/stage1_prediction_markets/qku_computation_control_plane/provider_profiles.py","tests/stage1_prediction_markets/qku_computation_control_plane/source/"],"implementation_disposition":"IMPLEMENT_EXACT_VERSIONED_SOURCE_BINDINGS_FROM_OWNER_RESOLVED_VALUES; FUTURE_REFRESH_BY_SOURCE_CURRENTIZATION_OWNER","implementation_owner":"SourceCurrentizationOwnerV1","implementation_steps":["Load the exact version-pinned Step10R5 input contracts and canonical-owner bindings.","Validate request, source, parameter, unit, basis, timestamp, mode and authority preconditions before computation.","Execute only the declared deterministic or seed-controlled algorithm through the named implementation owner.","Emit typed immutable receipts with exact inputs, outputs, versions, warnings, fallback and no-authority flags.","Run the declared independent oracle, negative cases and material mutation tests before any promotion-sensitive eligibility.","Fail closed to the registered lower safe path, calibration work order, no-trade or submit-disabled state when any invariant fails."],"independent_audit_owner":"IndependentSourceAuditorV1","independent_validator_owner":"IndependentSourceAuditorV1","input_contract":"direct primary-source captures and effective epochs","latency_class":"HOTPATH_SAFE_ONLY_WHEN_PRECOMPILED_DETERMINISTIC_AND_VERSION_PINNED; OTHERWISE_NEARLINE_OR_OFFLINE","open_research_questions":[],"output_contract":"versioned provider/method bindings with rights, freshness, conflict and recheck policy","precision_and_units":"EXACT_DECIMAL_AT_FINANCIAL_BOUNDARIES; EXPLICIT_UNIT_AND_BASIS_ON_EVERY_MATERIAL_NUMERIC_FIELD","reason_codes":["ST12_SOURCE_IBKR_FORECASTEX_CURRENTNESS_PASS","ST12_SOURCE_IBKR_FORECASTEX_CURRENTNESS_FAIL_CLOSED"],"research_basis":"OWNER_RESOLVED_STEP10R5_IMPLEMENTATION_FACTS_PLUS_CURRENT_REPOSITORY_OWNERSHIP_PLUS_DIRECT_PRIMARY_SOURCES","runtime_effect_authorized":false,"schema_contracts":["FormulaExecutionContractV1","ComputationExecutionReceiptV1","DOMAIN_SPECIFIC_STRICT_SCHEMA_FROM_STEP10R5_AND_STEP12_CLOSURE"],"test_oracles":["INDEPENDENT_GOLDEN_VECTOR","BOUNDARY_AND_NEGATIVE_CASE","MATERIAL_MUTATION_REJECTION","CLASSICAL_OR_NO_TRADE_FALLBACK"],"tests":["tests/stage1_prediction_markets/qku_computation_control_plane/source/test_ibkr_forecastex_currentness.py","tools/independent_validate_qku_computation_control_plane_source.py"],"unresolved_implementation_choice":false,"validation_commands":["python tools/validate_qku_computation_control_plane.py --domain source","python tools/independent_validate_qku_computation_control_plane_source.py"]},"implementation_specification_state":"COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION","independent_validator_owner":"IndependentSourceAuditorV1","master_plan_mutation_authorized":false,"owner_authorization_required_before_codex":true,"repository_mutation_authorized":false,"research_completeness_state":"COMPLETE_TERMINAL_CLOSURE_SPECIFICATION","step10_file_disposition_refs":["ST10-FILE::102"],"step12_primary_tranche_id":"ST12-TRANCHE-B"}],"repository_dispositions":[{"action":"CREATE","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"current_main_reconciliation_required_at_implementation_start":true,"dependency_closed":true,"file_disposition_id":"ST10-FILE::019","fixed_commit_authority":false,"purpose":"CONTEXTUAL_COMPUTABILITY_RESOLVER","repository_mutation_authorized":false,"repository_path":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/contextual_computability.py","source_step10_tranche_id":"ST10-TRANCHE-B","step12_target_tranche_id":"ST12-TRANCHE-B"},{"action":"CREATE","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"current_main_reconciliation_required_at_implementation_start":true,"dependency_closed":true,"file_disposition_id":"ST10-FILE::020","fixed_commit_authority":false,"purpose":"APPLICABLE_STACK_RESOLVER","repository_mutation_authorized":false,"repository_path":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/stack_resolver.py","source_step10_tranche_id":"ST10-TRANCHE-B","step12_target_tranche_id":"ST12-TRANCHE-B"},{"action":"CREATE","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"current_main_reconciliation_required_at_implementation_start":true,"dependency_closed":true,"file_disposition_id":"ST10-FILE::021","fixed_commit_authority":false,"purpose":"REQUIRED_INPUT_RESOLVER","repository_mutation_authorized":false,"repository_path":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/input_resolver.py","source_step10_tranche_id":"ST10-TRANCHE-B","step12_target_tranche_id":"ST12-TRANCHE-B"},{"action":"CREATE","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"current_main_reconciliation_required_at_implementation_start":true,"dependency_closed":true,"file_disposition_id":"ST10-FILE::022","fixed_commit_authority":false,"purpose":"EXPLICIT_UNIT_BASIS_CONVERSIONS","repository_mutation_authorized":false,"repository_path":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/unit_conversion.py","source_step10_tranche_id":"ST10-TRANCHE-B","step12_target_tranche_id":"ST12-TRANCHE-B"},{"action":"CREATE","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"current_main_reconciliation_required_at_implementation_start":true,"dependency_closed":true,"file_disposition_id":"ST10-FILE::023","fixed_commit_authority":false,"purpose":"TTL_AND_STALE_POLICY","repository_mutation_authorized":false,"repository_path":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/freshness.py","source_step10_tranche_id":"ST10-TRANCHE-B","step12_target_tranche_id":"ST12-TRANCHE-B"},{"action":"CREATE","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"current_main_reconciliation_required_at_implementation_start":true,"dependency_closed":true,"file_disposition_id":"ST10-FILE::024","fixed_commit_authority":false,"purpose":"AS_OF_AVAILABILITY_GUARDS","repository_mutation_authorized":false,"repository_path":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/point_in_time.py","source_step10_tranche_id":"ST10-TRANCHE-B","step12_target_tranche_id":"ST12-TRANCHE-B"},{"action":"CREATE","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"current_main_reconciliation_required_at_implementation_start":true,"dependency_closed":true,"file_disposition_id":"ST10-FILE::025","fixed_commit_authority":false,"purpose":"REGISTERED_FALLBACK_RESOLUTION","repository_mutation_authorized":false,"repository_path":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/fallback.py","source_step10_tranche_id":"ST10-TRANCHE-B","step12_target_tranche_id":"ST12-TRANCHE-B"},{"action":"CREATE","canonical_owner":"QKUComputationControlPlaneV1","codex_online_research_required":false,"current_main_reconciliation_required_at_implementation_start":true,"dependency_closed":true,"file_disposition_id":"ST10-FILE::026","fixed_commit_authority":false,"purpose":"CENTRAL_TYPED_SERVICE_SURFACE","repository_mutation_authorized":false,"repository_path":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/service.py","source_step10_tranche_id":"ST10-TRANCHE-B","step12_target_tranche_id":"ST12-TRANCHE-B"}],"test_rows":[{"closure_refs":["ST12-CLOSURE::ST11-LATENCY::006"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::081","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/latency/test_budget_ledger.py"},{"closure_refs":["ST12-CLOSURE::ST11-LATENCY::008"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::083","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/latency/test_clock_skew.py"},{"closure_refs":["ST12-CLOSURE::ST11-LATENCY::010"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::086","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/latency/test_deadlines_and_cancellation.py"},{"closure_refs":["ST12-CLOSURE::ST11-LATENCY::009"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::093","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/latency/test_queueing.py"},{"closure_refs":["ST12-CLOSURE::ST11-LATENCY::007"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::100","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/latency/test_ttl_and_edge_decay.py"},{"closure_refs":["ST12-CLOSURE::ST11-MODEL-RISK::004"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::123","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_conceptual_soundness.py"},{"closure_refs":["ST12-CLOSURE::ST11-MODEL-RISK::005"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::124","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_data_quality.py"},{"closure_refs":["ST12-CLOSURE::ST11-MODEL-RISK::007"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::125","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_effective_challenge.py"},{"closure_refs":["ST12-CLOSURE::ST11-MODEL-RISK::006"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::127","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_implementation_verification.py"},{"closure_refs":["ST12-CLOSURE::ST11-MODEL-RISK::002"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::128","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_intended_use.py"},{"closure_refs":["ST12-CLOSURE::ST11-MODEL-RISK::003"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::129","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_materiality_tiering.py"},{"closure_refs":["ST12-CLOSURE::ST11-MODEL-RISK::001"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::130","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_model_inventory.py"},{"closure_refs":["ST12-CLOSURE::ST11-MODEL-RISK::008"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::134","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/model_risk/test_outcomes_analysis.py"},{"closure_refs":["ST12-CLOSURE::ST11-OPERATIONS::007"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::142","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_backup_restore.py"},{"closure_refs":["ST12-CLOSURE::ST11-OPERATIONS::009"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::143","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_capacity_and_backpressure.py"},{"closure_refs":["ST12-CLOSURE::ST11-OPERATIONS::005"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::147","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_database_migrations.py"},{"closure_refs":["ST12-CLOSURE::ST11-OPERATIONS::008"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::150","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_event_and_receipt_durability.py"},{"closure_refs":["ST12-CLOSURE::ST11-OPERATIONS::006"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::158","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/operations/test_sqlite_runtime_safety.py"},{"closure_refs":["ST12-CLOSURE::ST11-QUANTUM::008"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::164","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_converter_compatibility.py"},{"closure_refs":["ST12-CLOSURE::ST11-QUANTUM::009"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::168","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_interpret_back.py"},{"closure_refs":["ST12-CLOSURE::ST11-QUANTUM::013"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::169","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_maturity_state_separation.py"},{"closure_refs":["ST12-CLOSURE::ST11-QUANTUM::010"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::172","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_original_model_feasibility.py"},{"closure_refs":["ST12-CLOSURE::ST11-QUANTUM::007"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::173","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_penalty_adequacy.py"},{"closure_refs":["ST12-CLOSURE::ST11-QUANTUM::011"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::175","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_same_formulation_comparator.py"},{"closure_refs":["ST12-CLOSURE::ST11-QUANTUM::014"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::176","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_sample_frequency_boundary.py"},{"closure_refs":["ST12-CLOSURE::ST11-QUANTUM::012"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::178","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/quantum/test_small_instance_oracle.py"},{"closure_refs":["ST12-CLOSURE::ST11-SECURITY::009"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::191","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/security/test_output_handling.py"},{"closure_refs":["ST12-CLOSURE::ST11-SECURITY::008"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::197","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/security/test_sql_and_path_safety.py"},{"closure_refs":["ST12-CLOSURE::ST11-SECURITY::010"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::198","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/security/test_supply_chain_provenance.py"},{"closure_refs":["ST12-CLOSURE::ST11-SOURCE::008"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::203","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/source/test_cached_search_rejection.py"},{"closure_refs":["ST12-CLOSURE::ST11-SOURCE::007"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::204","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/source/test_category_vs_market.py"},{"closure_refs":["ST12-CLOSURE::ST11-SOURCE::010"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::206","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/source/test_data_grade_classification.py"},{"closure_refs":["ST12-CLOSURE::ST11-SOURCE::006"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::210","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/source/test_future_dated_content.py"},{"closure_refs":["ST12-CLOSURE::ST11-SOURCE::014"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::211","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/source/test_ibkr_forecastex_currentness.py"},{"closure_refs":["ST12-CLOSURE::ST11-SOURCE::011"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::212","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/source/test_kalshi_currentness.py"},{"closure_refs":["ST12-CLOSURE::ST11-SOURCE::012"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::213","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/source/test_polymarket_global_currentness.py"},{"closure_refs":["ST12-CLOSURE::ST11-SOURCE::013"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::214","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/source/test_polymarket_us_currentness.py"},{"closure_refs":["ST12-CLOSURE::ST11-SOURCE::009"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B"],"test_class":"CONTROL_SPECIFICATION_TEST","test_id":"ST12-TEST::220","test_path":"tests/stage1_prediction_markets/qku_computation_control_plane/source/test_url_and_document_drift.py"},{"closure_refs":["ST12-CLOSURE::ST11-LATENCY::001","ST12-CLOSURE::ST11-LATENCY::002","ST12-CLOSURE::ST11-LATENCY::003","ST12-CLOSURE::ST11-LATENCY::004","ST12-CLOSURE::ST11-LATENCY::005","ST12-CLOSURE::ST11-LATENCY::006","ST12-CLOSURE::ST11-LATENCY::007","ST12-CLOSURE::ST11-LATENCY::008","ST12-CLOSURE::ST11-LATENCY::009","ST12-CLOSURE::ST11-LATENCY::010","ST12-CLOSURE::ST11-LATENCY::011","ST12-CLOSURE::ST11-LATENCY::012","ST12-CLOSURE::ST11-LATENCY::013","ST12-CLOSURE::ST11-LATENCY::014","ST12-CLOSURE::ST11-LATENCY::015","ST12-CLOSURE::ST11-LATENCY::016","ST12-CLOSURE::ST11-LATENCY::017","ST12-CLOSURE::ST11-LATENCY::018","ST12-CLOSURE::ST11-LATENCY::019","ST12-CLOSURE::ST11-LATENCY::020"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B","ST12-TRANCHE-D"],"test_class":"DOMAIN_INDEPENDENT_VALIDATOR","test_id":"ST12-TEST::225","test_path":"tools/independent_validate_qku_computation_control_plane_latency.py"},{"closure_refs":["ST12-CLOSURE::ST11-MODEL-RISK::001","ST12-CLOSURE::ST11-MODEL-RISK::002","ST12-CLOSURE::ST11-MODEL-RISK::003","ST12-CLOSURE::ST11-MODEL-RISK::004","ST12-CLOSURE::ST11-MODEL-RISK::005","ST12-CLOSURE::ST11-MODEL-RISK::006","ST12-CLOSURE::ST11-MODEL-RISK::007","ST12-CLOSURE::ST11-MODEL-RISK::008","ST12-CLOSURE::ST11-MODEL-RISK::009","ST12-CLOSURE::ST11-MODEL-RISK::010","ST12-CLOSURE::ST11-MODEL-RISK::011","ST12-CLOSURE::ST11-MODEL-RISK::012","ST12-CLOSURE::ST11-MODEL-RISK::013","ST12-CLOSURE::ST11-MODEL-RISK::014","ST12-CLOSURE::ST11-MODEL-RISK::015","ST12-CLOSURE::ST11-MODEL-RISK::016","ST12-CLOSURE::ST11-MODEL-RISK::017","ST12-CLOSURE::ST11-MODEL-RISK::018","ST12-CLOSURE::ST11-MODEL-RISK::019","ST12-CLOSURE::ST11-MODEL-RISK::020"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-B","ST12-TRANCHE-F"],"test_class":"DOMAIN_INDEPENDENT_VALIDATOR","test_id":"ST12-TEST::227","test_path":"tools/independent_validate_qku_computation_control_plane_model_risk.py"},{"closure_refs":["ST12-CLOSURE::ST11-OPERATIONS::001","ST12-CLOSURE::ST11-OPERATIONS::002","ST12-CLOSURE::ST11-OPERATIONS::003","ST12-CLOSURE::ST11-OPERATIONS::004","ST12-CLOSURE::ST11-OPERATIONS::005","ST12-CLOSURE::ST11-OPERATIONS::006","ST12-CLOSURE::ST11-OPERATIONS::007","ST12-CLOSURE::ST11-OPERATIONS::008","ST12-CLOSURE::ST11-OPERATIONS::009","ST12-CLOSURE::ST11-OPERATIONS::010","ST12-CLOSURE::ST11-OPERATIONS::011","ST12-CLOSURE::ST11-OPERATIONS::012","ST12-CLOSURE::ST11-OPERATIONS::013","ST12-CLOSURE::ST11-OPERATIONS::014","ST12-CLOSURE::ST11-OPERATIONS::015","ST12-CLOSURE::ST11-OPERATIONS::016","ST12-CLOSURE::ST11-OPERATIONS::017","ST12-CLOSURE::ST11-OPERATIONS::018","ST12-CLOSURE::ST11-OPERATIONS::019","ST12-CLOSURE::ST11-OPERATIONS::020"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-A","ST12-TRANCHE-B","ST12-TRANCHE-G","ST12-TRANCHE-H"],"test_class":"DOMAIN_INDEPENDENT_VALIDATOR","test_id":"ST12-TEST::228","test_path":"tools/independent_validate_qku_computation_control_plane_operations.py"},{"closure_refs":["ST12-CLOSURE::ST11-QUANTUM::001","ST12-CLOSURE::ST11-QUANTUM::002","ST12-CLOSURE::ST11-QUANTUM::003","ST12-CLOSURE::ST11-QUANTUM::004","ST12-CLOSURE::ST11-QUANTUM::005","ST12-CLOSURE::ST11-QUANTUM::006","ST12-CLOSURE::ST11-QUANTUM::007","ST12-CLOSURE::ST11-QUANTUM::008","ST12-CLOSURE::ST11-QUANTUM::009","ST12-CLOSURE::ST11-QUANTUM::010","ST12-CLOSURE::ST11-QUANTUM::011","ST12-CLOSURE::ST11-QUANTUM::012","ST12-CLOSURE::ST11-QUANTUM::013","ST12-CLOSURE::ST11-QUANTUM::014","ST12-CLOSURE::ST11-QUANTUM::015","ST12-CLOSURE::ST11-QUANTUM::016","ST12-CLOSURE::ST11-QUANTUM::017","ST12-CLOSURE::ST11-QUANTUM::018","ST12-CLOSURE::ST11-QUANTUM::019","ST12-CLOSURE::ST11-QUANTUM::020"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-A","ST12-TRANCHE-B","ST12-TRANCHE-F"],"test_class":"DOMAIN_INDEPENDENT_VALIDATOR","test_id":"ST12-TEST::229","test_path":"tools/independent_validate_qku_computation_control_plane_quantum.py"},{"closure_refs":["ST12-CLOSURE::ST11-SECURITY::001","ST12-CLOSURE::ST11-SECURITY::002","ST12-CLOSURE::ST11-SECURITY::003","ST12-CLOSURE::ST11-SECURITY::004","ST12-CLOSURE::ST11-SECURITY::005","ST12-CLOSURE::ST11-SECURITY::006","ST12-CLOSURE::ST11-SECURITY::007","ST12-CLOSURE::ST11-SECURITY::008","ST12-CLOSURE::ST11-SECURITY::009","ST12-CLOSURE::ST11-SECURITY::010","ST12-CLOSURE::ST11-SECURITY::011","ST12-CLOSURE::ST11-SECURITY::012","ST12-CLOSURE::ST11-SECURITY::013","ST12-CLOSURE::ST11-SECURITY::014","ST12-CLOSURE::ST11-SECURITY::015","ST12-CLOSURE::ST11-SECURITY::016","ST12-CLOSURE::ST11-SECURITY::017","ST12-CLOSURE::ST11-SECURITY::018","ST12-CLOSURE::ST11-SECURITY::019","ST12-CLOSURE::ST11-SECURITY::020"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-A","ST12-TRANCHE-B","ST12-TRANCHE-D","ST12-TRANCHE-E","ST12-TRANCHE-H"],"test_class":"DOMAIN_INDEPENDENT_VALIDATOR","test_id":"ST12-TEST::230","test_path":"tools/independent_validate_qku_computation_control_plane_security.py"},{"closure_refs":["ST12-CLOSURE::ST11-SOURCE::001","ST12-CLOSURE::ST11-SOURCE::002","ST12-CLOSURE::ST11-SOURCE::003","ST12-CLOSURE::ST11-SOURCE::004","ST12-CLOSURE::ST11-SOURCE::005","ST12-CLOSURE::ST11-SOURCE::006","ST12-CLOSURE::ST11-SOURCE::007","ST12-CLOSURE::ST11-SOURCE::008","ST12-CLOSURE::ST11-SOURCE::009","ST12-CLOSURE::ST11-SOURCE::010","ST12-CLOSURE::ST11-SOURCE::011","ST12-CLOSURE::ST11-SOURCE::012","ST12-CLOSURE::ST11-SOURCE::013","ST12-CLOSURE::ST11-SOURCE::014","ST12-CLOSURE::ST11-SOURCE::015","ST12-CLOSURE::ST11-SOURCE::016","ST12-CLOSURE::ST11-SOURCE::017","ST12-CLOSURE::ST11-SOURCE::018","ST12-CLOSURE::ST11-SOURCE::019","ST12-CLOSURE::ST11-SOURCE::020"],"codex_online_research_allowed":false,"independent_expected_value_required":true,"production_implementation_import_as_expected_value_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION","step12_tranche_refs":["ST12-TRANCHE-A","ST12-TRANCHE-B","ST12-TRANCHE-H"],"test_class":"DOMAIN_INDEPENDENT_VALIDATOR","test_id":"ST12-TEST::231","test_path":"tools/independent_validate_qku_computation_control_plane_source.py"}],"validation_commands":[{"closure_refs":["ST12-CLOSURE::ST11-LATENCY::001","ST12-CLOSURE::ST11-LATENCY::002","ST12-CLOSURE::ST11-LATENCY::003","ST12-CLOSURE::ST11-LATENCY::004","ST12-CLOSURE::ST11-LATENCY::005","ST12-CLOSURE::ST11-LATENCY::006","ST12-CLOSURE::ST11-LATENCY::007","ST12-CLOSURE::ST11-LATENCY::008","ST12-CLOSURE::ST11-LATENCY::009","ST12-CLOSURE::ST11-LATENCY::010","ST12-CLOSURE::ST11-LATENCY::011","ST12-CLOSURE::ST11-LATENCY::012","ST12-CLOSURE::ST11-LATENCY::013","ST12-CLOSURE::ST11-LATENCY::014","ST12-CLOSURE::ST11-LATENCY::015","ST12-CLOSURE::ST11-LATENCY::016","ST12-CLOSURE::ST11-LATENCY::017","ST12-CLOSURE::ST11-LATENCY::018","ST12-CLOSURE::ST11-LATENCY::019","ST12-CLOSURE::ST11-LATENCY::020"],"command":"python tools/independent_validate_qku_computation_control_plane_latency.py","command_id":"ST12-CMD::05","network_access_allowed":false,"provider_effect_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_VALIDATION_COMMAND","script_path":"tools/independent_validate_qku_computation_control_plane_latency.py","step12_tranche_refs":["ST12-TRANCHE-B","ST12-TRANCHE-D"]},{"closure_refs":["ST12-CLOSURE::ST11-MODEL-RISK::001","ST12-CLOSURE::ST11-MODEL-RISK::002","ST12-CLOSURE::ST11-MODEL-RISK::003","ST12-CLOSURE::ST11-MODEL-RISK::004","ST12-CLOSURE::ST11-MODEL-RISK::005","ST12-CLOSURE::ST11-MODEL-RISK::006","ST12-CLOSURE::ST11-MODEL-RISK::007","ST12-CLOSURE::ST11-MODEL-RISK::008","ST12-CLOSURE::ST11-MODEL-RISK::009","ST12-CLOSURE::ST11-MODEL-RISK::010","ST12-CLOSURE::ST11-MODEL-RISK::011","ST12-CLOSURE::ST11-MODEL-RISK::012","ST12-CLOSURE::ST11-MODEL-RISK::013","ST12-CLOSURE::ST11-MODEL-RISK::014","ST12-CLOSURE::ST11-MODEL-RISK::015","ST12-CLOSURE::ST11-MODEL-RISK::016","ST12-CLOSURE::ST11-MODEL-RISK::017","ST12-CLOSURE::ST11-MODEL-RISK::018","ST12-CLOSURE::ST11-MODEL-RISK::019","ST12-CLOSURE::ST11-MODEL-RISK::020"],"command":"python tools/independent_validate_qku_computation_control_plane_model_risk.py","command_id":"ST12-CMD::07","network_access_allowed":false,"provider_effect_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_VALIDATION_COMMAND","script_path":"tools/independent_validate_qku_computation_control_plane_model_risk.py","step12_tranche_refs":["ST12-TRANCHE-B","ST12-TRANCHE-F"]},{"closure_refs":["ST12-CLOSURE::ST11-OPERATIONS::001","ST12-CLOSURE::ST11-OPERATIONS::002","ST12-CLOSURE::ST11-OPERATIONS::003","ST12-CLOSURE::ST11-OPERATIONS::004","ST12-CLOSURE::ST11-OPERATIONS::005","ST12-CLOSURE::ST11-OPERATIONS::006","ST12-CLOSURE::ST11-OPERATIONS::007","ST12-CLOSURE::ST11-OPERATIONS::008","ST12-CLOSURE::ST11-OPERATIONS::009","ST12-CLOSURE::ST11-OPERATIONS::010","ST12-CLOSURE::ST11-OPERATIONS::011","ST12-CLOSURE::ST11-OPERATIONS::012","ST12-CLOSURE::ST11-OPERATIONS::013","ST12-CLOSURE::ST11-OPERATIONS::014","ST12-CLOSURE::ST11-OPERATIONS::015","ST12-CLOSURE::ST11-OPERATIONS::016","ST12-CLOSURE::ST11-OPERATIONS::017","ST12-CLOSURE::ST11-OPERATIONS::018","ST12-CLOSURE::ST11-OPERATIONS::019","ST12-CLOSURE::ST11-OPERATIONS::020"],"command":"python tools/independent_validate_qku_computation_control_plane_operations.py","command_id":"ST12-CMD::08","network_access_allowed":false,"provider_effect_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_VALIDATION_COMMAND","script_path":"tools/independent_validate_qku_computation_control_plane_operations.py","step12_tranche_refs":["ST12-TRANCHE-A","ST12-TRANCHE-B","ST12-TRANCHE-G","ST12-TRANCHE-H"]},{"closure_refs":["ST12-CLOSURE::ST11-QUANTUM::001","ST12-CLOSURE::ST11-QUANTUM::002","ST12-CLOSURE::ST11-QUANTUM::003","ST12-CLOSURE::ST11-QUANTUM::004","ST12-CLOSURE::ST11-QUANTUM::005","ST12-CLOSURE::ST11-QUANTUM::006","ST12-CLOSURE::ST11-QUANTUM::007","ST12-CLOSURE::ST11-QUANTUM::008","ST12-CLOSURE::ST11-QUANTUM::009","ST12-CLOSURE::ST11-QUANTUM::010","ST12-CLOSURE::ST11-QUANTUM::011","ST12-CLOSURE::ST11-QUANTUM::012","ST12-CLOSURE::ST11-QUANTUM::013","ST12-CLOSURE::ST11-QUANTUM::014","ST12-CLOSURE::ST11-QUANTUM::015","ST12-CLOSURE::ST11-QUANTUM::016","ST12-CLOSURE::ST11-QUANTUM::017","ST12-CLOSURE::ST11-QUANTUM::018","ST12-CLOSURE::ST11-QUANTUM::019","ST12-CLOSURE::ST11-QUANTUM::020"],"command":"python tools/independent_validate_qku_computation_control_plane_quantum.py","command_id":"ST12-CMD::09","network_access_allowed":false,"provider_effect_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_VALIDATION_COMMAND","script_path":"tools/independent_validate_qku_computation_control_plane_quantum.py","step12_tranche_refs":["ST12-TRANCHE-A","ST12-TRANCHE-B","ST12-TRANCHE-F"]},{"closure_refs":["ST12-CLOSURE::ST11-SECURITY::001","ST12-CLOSURE::ST11-SECURITY::002","ST12-CLOSURE::ST11-SECURITY::003","ST12-CLOSURE::ST11-SECURITY::004","ST12-CLOSURE::ST11-SECURITY::005","ST12-CLOSURE::ST11-SECURITY::006","ST12-CLOSURE::ST11-SECURITY::007","ST12-CLOSURE::ST11-SECURITY::008","ST12-CLOSURE::ST11-SECURITY::009","ST12-CLOSURE::ST11-SECURITY::010","ST12-CLOSURE::ST11-SECURITY::011","ST12-CLOSURE::ST11-SECURITY::012","ST12-CLOSURE::ST11-SECURITY::013","ST12-CLOSURE::ST11-SECURITY::014","ST12-CLOSURE::ST11-SECURITY::015","ST12-CLOSURE::ST11-SECURITY::016","ST12-CLOSURE::ST11-SECURITY::017","ST12-CLOSURE::ST11-SECURITY::018","ST12-CLOSURE::ST11-SECURITY::019","ST12-CLOSURE::ST11-SECURITY::020"],"command":"python tools/independent_validate_qku_computation_control_plane_security.py","command_id":"ST12-CMD::10","network_access_allowed":false,"provider_effect_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_VALIDATION_COMMAND","script_path":"tools/independent_validate_qku_computation_control_plane_security.py","step12_tranche_refs":["ST12-TRANCHE-A","ST12-TRANCHE-B","ST12-TRANCHE-D","ST12-TRANCHE-E","ST12-TRANCHE-H"]},{"closure_refs":["ST12-CLOSURE::ST11-SOURCE::001","ST12-CLOSURE::ST11-SOURCE::002","ST12-CLOSURE::ST11-SOURCE::003","ST12-CLOSURE::ST11-SOURCE::004","ST12-CLOSURE::ST11-SOURCE::005","ST12-CLOSURE::ST11-SOURCE::006","ST12-CLOSURE::ST11-SOURCE::007","ST12-CLOSURE::ST11-SOURCE::008","ST12-CLOSURE::ST11-SOURCE::009","ST12-CLOSURE::ST11-SOURCE::010","ST12-CLOSURE::ST11-SOURCE::011","ST12-CLOSURE::ST11-SOURCE::012","ST12-CLOSURE::ST11-SOURCE::013","ST12-CLOSURE::ST11-SOURCE::014","ST12-CLOSURE::ST11-SOURCE::015","ST12-CLOSURE::ST11-SOURCE::016","ST12-CLOSURE::ST11-SOURCE::017","ST12-CLOSURE::ST11-SOURCE::018","ST12-CLOSURE::ST11-SOURCE::019","ST12-CLOSURE::ST11-SOURCE::020"],"command":"python tools/independent_validate_qku_computation_control_plane_source.py","command_id":"ST12-CMD::11","network_access_allowed":false,"provider_effect_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_VALIDATION_COMMAND","script_path":"tools/independent_validate_qku_computation_control_plane_source.py","step12_tranche_refs":["ST12-TRANCHE-A","ST12-TRANCHE-B","ST12-TRANCHE-H"]},{"closure_refs":["ST12-CLOSURE::ST11-LATENCY::001","ST12-CLOSURE::ST11-LATENCY::002","ST12-CLOSURE::ST11-LATENCY::003","ST12-CLOSURE::ST11-LATENCY::004","ST12-CLOSURE::ST11-LATENCY::005","ST12-CLOSURE::ST11-LATENCY::006","ST12-CLOSURE::ST11-LATENCY::007","ST12-CLOSURE::ST11-LATENCY::008","ST12-CLOSURE::ST11-LATENCY::009","ST12-CLOSURE::ST11-LATENCY::010","ST12-CLOSURE::ST11-LATENCY::011","ST12-CLOSURE::ST11-LATENCY::012","ST12-CLOSURE::ST11-LATENCY::013","ST12-CLOSURE::ST11-LATENCY::014","ST12-CLOSURE::ST11-LATENCY::015","ST12-CLOSURE::ST11-LATENCY::016","ST12-CLOSURE::ST11-LATENCY::017","ST12-CLOSURE::ST11-LATENCY::018","ST12-CLOSURE::ST11-LATENCY::019","ST12-CLOSURE::ST11-LATENCY::020"],"command":"python tools/validate_qku_computation_control_plane.py --domain latency","command_id":"ST12-CMD::16","network_access_allowed":false,"provider_effect_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_VALIDATION_COMMAND","script_path":"tools/validate_qku_computation_control_plane.py","step12_tranche_refs":["ST12-TRANCHE-B","ST12-TRANCHE-D"]},{"closure_refs":["ST12-CLOSURE::ST11-MODEL-RISK::001","ST12-CLOSURE::ST11-MODEL-RISK::002","ST12-CLOSURE::ST11-MODEL-RISK::003","ST12-CLOSURE::ST11-MODEL-RISK::004","ST12-CLOSURE::ST11-MODEL-RISK::005","ST12-CLOSURE::ST11-MODEL-RISK::006","ST12-CLOSURE::ST11-MODEL-RISK::007","ST12-CLOSURE::ST11-MODEL-RISK::008","ST12-CLOSURE::ST11-MODEL-RISK::009","ST12-CLOSURE::ST11-MODEL-RISK::010","ST12-CLOSURE::ST11-MODEL-RISK::011","ST12-CLOSURE::ST11-MODEL-RISK::012","ST12-CLOSURE::ST11-MODEL-RISK::013","ST12-CLOSURE::ST11-MODEL-RISK::014","ST12-CLOSURE::ST11-MODEL-RISK::015","ST12-CLOSURE::ST11-MODEL-RISK::016","ST12-CLOSURE::ST11-MODEL-RISK::017","ST12-CLOSURE::ST11-MODEL-RISK::018","ST12-CLOSURE::ST11-MODEL-RISK::019","ST12-CLOSURE::ST11-MODEL-RISK::020"],"command":"python tools/validate_qku_computation_control_plane.py --domain model_risk","command_id":"ST12-CMD::18","network_access_allowed":false,"provider_effect_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_VALIDATION_COMMAND","script_path":"tools/validate_qku_computation_control_plane.py","step12_tranche_refs":["ST12-TRANCHE-B","ST12-TRANCHE-F"]},{"closure_refs":["ST12-CLOSURE::ST11-OPERATIONS::001","ST12-CLOSURE::ST11-OPERATIONS::002","ST12-CLOSURE::ST11-OPERATIONS::003","ST12-CLOSURE::ST11-OPERATIONS::004","ST12-CLOSURE::ST11-OPERATIONS::005","ST12-CLOSURE::ST11-OPERATIONS::006","ST12-CLOSURE::ST11-OPERATIONS::007","ST12-CLOSURE::ST11-OPERATIONS::008","ST12-CLOSURE::ST11-OPERATIONS::009","ST12-CLOSURE::ST11-OPERATIONS::010","ST12-CLOSURE::ST11-OPERATIONS::011","ST12-CLOSURE::ST11-OPERATIONS::012","ST12-CLOSURE::ST11-OPERATIONS::013","ST12-CLOSURE::ST11-OPERATIONS::014","ST12-CLOSURE::ST11-OPERATIONS::015","ST12-CLOSURE::ST11-OPERATIONS::016","ST12-CLOSURE::ST11-OPERATIONS::017","ST12-CLOSURE::ST11-OPERATIONS::018","ST12-CLOSURE::ST11-OPERATIONS::019","ST12-CLOSURE::ST11-OPERATIONS::020"],"command":"python tools/validate_qku_computation_control_plane.py --domain operations","command_id":"ST12-CMD::19","network_access_allowed":false,"provider_effect_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_VALIDATION_COMMAND","script_path":"tools/validate_qku_computation_control_plane.py","step12_tranche_refs":["ST12-TRANCHE-A","ST12-TRANCHE-B","ST12-TRANCHE-G","ST12-TRANCHE-H"]},{"closure_refs":["ST12-CLOSURE::ST11-QUANTUM::001","ST12-CLOSURE::ST11-QUANTUM::002","ST12-CLOSURE::ST11-QUANTUM::003","ST12-CLOSURE::ST11-QUANTUM::004","ST12-CLOSURE::ST11-QUANTUM::005","ST12-CLOSURE::ST11-QUANTUM::006","ST12-CLOSURE::ST11-QUANTUM::007","ST12-CLOSURE::ST11-QUANTUM::008","ST12-CLOSURE::ST11-QUANTUM::009","ST12-CLOSURE::ST11-QUANTUM::010","ST12-CLOSURE::ST11-QUANTUM::011","ST12-CLOSURE::ST11-QUANTUM::012","ST12-CLOSURE::ST11-QUANTUM::013","ST12-CLOSURE::ST11-QUANTUM::014","ST12-CLOSURE::ST11-QUANTUM::015","ST12-CLOSURE::ST11-QUANTUM::016","ST12-CLOSURE::ST11-QUANTUM::017","ST12-CLOSURE::ST11-QUANTUM::018","ST12-CLOSURE::ST11-QUANTUM::019","ST12-CLOSURE::ST11-QUANTUM::020"],"command":"python tools/validate_qku_computation_control_plane.py --domain quantum","command_id":"ST12-CMD::20","network_access_allowed":false,"provider_effect_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_VALIDATION_COMMAND","script_path":"tools/validate_qku_computation_control_plane.py","step12_tranche_refs":["ST12-TRANCHE-A","ST12-TRANCHE-B","ST12-TRANCHE-F"]},{"closure_refs":["ST12-CLOSURE::ST11-SECURITY::001","ST12-CLOSURE::ST11-SECURITY::002","ST12-CLOSURE::ST11-SECURITY::003","ST12-CLOSURE::ST11-SECURITY::004","ST12-CLOSURE::ST11-SECURITY::005","ST12-CLOSURE::ST11-SECURITY::006","ST12-CLOSURE::ST11-SECURITY::007","ST12-CLOSURE::ST11-SECURITY::008","ST12-CLOSURE::ST11-SECURITY::009","ST12-CLOSURE::ST11-SECURITY::010","ST12-CLOSURE::ST11-SECURITY::011","ST12-CLOSURE::ST11-SECURITY::012","ST12-CLOSURE::ST11-SECURITY::013","ST12-CLOSURE::ST11-SECURITY::014","ST12-CLOSURE::ST11-SECURITY::015","ST12-CLOSURE::ST11-SECURITY::016","ST12-CLOSURE::ST11-SECURITY::017","ST12-CLOSURE::ST11-SECURITY::018","ST12-CLOSURE::ST11-SECURITY::019","ST12-CLOSURE::ST11-SECURITY::020"],"command":"python tools/validate_qku_computation_control_plane.py --domain security","command_id":"ST12-CMD::21","network_access_allowed":false,"provider_effect_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_VALIDATION_COMMAND","script_path":"tools/validate_qku_computation_control_plane.py","step12_tranche_refs":["ST12-TRANCHE-A","ST12-TRANCHE-B","ST12-TRANCHE-D","ST12-TRANCHE-E","ST12-TRANCHE-H"]},{"closure_refs":["ST12-CLOSURE::ST11-SOURCE::001","ST12-CLOSURE::ST11-SOURCE::002","ST12-CLOSURE::ST11-SOURCE::003","ST12-CLOSURE::ST11-SOURCE::004","ST12-CLOSURE::ST11-SOURCE::005","ST12-CLOSURE::ST11-SOURCE::006","ST12-CLOSURE::ST11-SOURCE::007","ST12-CLOSURE::ST11-SOURCE::008","ST12-CLOSURE::ST11-SOURCE::009","ST12-CLOSURE::ST11-SOURCE::010","ST12-CLOSURE::ST11-SOURCE::011","ST12-CLOSURE::ST11-SOURCE::012","ST12-CLOSURE::ST11-SOURCE::013","ST12-CLOSURE::ST11-SOURCE::014","ST12-CLOSURE::ST11-SOURCE::015","ST12-CLOSURE::ST11-SOURCE::016","ST12-CLOSURE::ST11-SOURCE::017","ST12-CLOSURE::ST11-SOURCE::018","ST12-CLOSURE::ST11-SOURCE::019","ST12-CLOSURE::ST11-SOURCE::020"],"command":"python tools/validate_qku_computation_control_plane.py --domain source","command_id":"ST12-CMD::22","network_access_allowed":false,"provider_effect_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXACT_VALIDATION_COMMAND","script_path":"tools/validate_qku_computation_control_plane.py","step12_tranche_refs":["ST12-TRANCHE-A","ST12-TRANCHE-B","ST12-TRANCHE-H"]}]}'''

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
    for rule in TRANCHE_A_SOURCE_CLAIM_BINDING_RULES:
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
            for rule in TRANCHE_A_SOURCE_CLAIM_BINDING_RULES
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


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _load_tranche_b_machine_rows() -> dict[str, tuple[dict[str, object], ...]]:
    loaded = json.loads(_TRANCHE_B_MACHINE_ROWS_JSON)
    expected = {
        "closure_rows": 38,
        "repository_dispositions": 8,
        "test_rows": 44,
        "validation_commands": 12,
    }
    if (
        not isinstance(loaded, dict)
        or set(loaded) != set(expected)
        or any(
            not isinstance(loaded[name], list)
            or len(loaded[name]) != count
            or any(not isinstance(row, dict) for row in loaded[name])
            for name, count in expected.items()
        )
    ):
        raise ContractValidationError(
            ReasonCode.INCOMPLETE_CONTRACT,
            "Tranche-B embedded machine rows differ from the certified populations",
        )
    return {
        name: tuple(rows)
        for name, rows in loaded.items()
    }


_TRANCHE_B_MACHINE_ROWS = _load_tranche_b_machine_rows()


@dataclass(frozen=True, slots=True)
class TrancheBClosureRowV1:
    closure_id: str
    control_id: str
    control_slug: str
    domain: str
    original_row_json: str

    def __post_init__(self) -> None:
        row = json.loads(self.original_row_json)
        implementation = row.get("implementation_specification")
        if (
            not isinstance(row, dict)
            or row.get("closure_id") != self.closure_id
            or row.get("control_id") != self.control_id
            or row.get("control_slug") != self.control_slug
            or row.get("domain") != self.domain
            or row.get("step12_primary_tranche_id") != "ST12-TRANCHE-B"
            or row.get("research_completeness_state")
            != "COMPLETE_TERMINAL_CLOSURE_SPECIFICATION"
            or row.get("implementation_specification_state")
            != "COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION"
            or row.get("codex_online_research_allowed")
            or row.get("master_plan_mutation_authorized")
            or not isinstance(implementation, dict)
            or implementation.get("codex_online_research_required")
            or implementation.get("runtime_effect_authorized")
            or implementation.get("unresolved_implementation_choice")
            or implementation.get("open_research_questions") != []
            or not implementation.get("canonical_owner")
            or not implementation.get("implementation_owner")
            or not implementation.get("independent_validator_owner")
            or not implementation.get("consume_existing_owner_refs")
            or not implementation.get("schema_contracts")
            or not implementation.get("tests")
            or not implementation.get("validation_commands")
            or not implementation.get("failure_behavior")
            or not implementation.get("fallback")
        ):
            raise ContractValidationError(
                ReasonCode.INCOMPLETE_CONTRACT,
                f"nonterminal or incomplete Tranche-B closure row: {self.closure_id}",
            )


@dataclass(frozen=True, slots=True)
class TrancheBRepositoryDispositionV1:
    disposition_id: str
    repository_path: str
    purpose: str
    original_row_json: str

    def __post_init__(self) -> None:
        row = json.loads(self.original_row_json)
        if (
            row.get("file_disposition_id") != self.disposition_id
            or row.get("repository_path") != self.repository_path
            or row.get("purpose") != self.purpose
            or row.get("action") != "CREATE"
            or row.get("canonical_owner")
            != "QKUComputationControlPlaneV1"
            or row.get("step12_target_tranche_id") != "ST12-TRANCHE-B"
            or not row.get("dependency_closed")
            or row.get("codex_online_research_required")
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                f"invalid Tranche-B repository disposition: {self.disposition_id}",
            )
        validate_relative_path(self.repository_path)


@dataclass(frozen=True, slots=True)
class TrancheBTestRowV1:
    test_id: str
    test_class: str
    certified_test_path: str
    mapped_test_path: str
    domain: str
    original_row_json: str

    def __post_init__(self) -> None:
        row = json.loads(self.original_row_json)
        if (
            row.get("test_id") != self.test_id
            or row.get("test_class") != self.test_class
            or row.get("test_path") != self.certified_test_path
            or row.get("research_completeness_state")
            != "COMPLETE_TERMINAL_EXACT_TEST_SPECIFICATION"
            or row.get("codex_online_research_allowed")
            or not row.get("independent_expected_value_required")
            or row.get(
                "production_implementation_import_as_expected_value_allowed"
            )
            or "ST12-TRANCHE-B" not in row.get("step12_tranche_refs", [])
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                f"invalid Tranche-B test row: {self.test_id}",
            )
        validate_relative_path(self.certified_test_path)
        validate_relative_path(self.mapped_test_path)


@dataclass(frozen=True, slots=True)
class TrancheBValidationCommandV1:
    command_id: str
    command: str
    script_path: str
    domain: str
    original_row_json: str

    def __post_init__(self) -> None:
        row = json.loads(self.original_row_json)
        if (
            row.get("command_id") != self.command_id
            or row.get("command") != self.command
            or row.get("script_path") != self.script_path
            or row.get("research_completeness_state")
            != "COMPLETE_TERMINAL_EXACT_VALIDATION_COMMAND"
            or row.get("network_access_allowed")
            or row.get("provider_effect_allowed")
            or "ST12-TRANCHE-B" not in row.get("step12_tranche_refs", [])
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                f"invalid Tranche-B validation command: {self.command_id}",
            )
        validate_relative_path(self.script_path)


def _row_domain_from_path(path: str) -> str:
    normalized = path.replace("\\", "/").casefold()
    for domain in (
        "latency",
        "model_risk",
        "operations",
        "quantum",
        "security",
        "source",
    ):
        token = domain.replace("_", "-")
        if (
            f"/{domain}/" in normalized
            or f"_{domain}." in normalized
            or f"_{token}." in normalized
            or f"--domain {domain}" in normalized
        ):
            return domain
    raise ContractValidationError(
        ReasonCode.INVALID_CONTRACT,
        f"cannot derive certified Tranche-B domain from {path}",
    )


def _mapped_test_module(domain: str, test_class: str) -> str:
    base = (
        "tests/stage1_prediction_markets/qku_computation_control_plane/"
        "tranche_b/"
    )
    if test_class == "DOMAIN_INDEPENDENT_VALIDATOR":
        return base + "test_manifest_and_ownership.py"
    if domain == "latency":
        return base + "test_resolution_pipeline.py"
    if domain == "operations":
        return base + "test_service_operations.py"
    return base + "test_source_quantum_model_risk.py"


TRANCHE_B_CLOSURE_ROWS = tuple(
    TrancheBClosureRowV1(
        closure_id=str(row["closure_id"]),
        control_id=str(row["control_id"]),
        control_slug=str(row["control_slug"]),
        domain=str(row["domain"]),
        original_row_json=_canonical_json(row),
    )
    for row in _TRANCHE_B_MACHINE_ROWS["closure_rows"]
)
TRANCHE_B_REPOSITORY_DISPOSITIONS = tuple(
    TrancheBRepositoryDispositionV1(
        disposition_id=str(row["file_disposition_id"]),
        repository_path=str(row["repository_path"]),
        purpose=str(row["purpose"]),
        original_row_json=_canonical_json(row),
    )
    for row in _TRANCHE_B_MACHINE_ROWS["repository_dispositions"]
)
TRANCHE_B_TEST_ROWS = tuple(
    TrancheBTestRowV1(
        test_id=str(row["test_id"]),
        test_class=str(row["test_class"]),
        certified_test_path=str(row["test_path"]),
        mapped_test_path=_mapped_test_module(
            _row_domain_from_path(str(row["test_path"])),
            str(row["test_class"]),
        ),
        domain=_row_domain_from_path(str(row["test_path"])),
        original_row_json=_canonical_json(row),
    )
    for row in _TRANCHE_B_MACHINE_ROWS["test_rows"]
)
TRANCHE_B_VALIDATION_COMMANDS = tuple(
    TrancheBValidationCommandV1(
        command_id=str(row["command_id"]),
        command=str(row["command"]),
        script_path=str(row["script_path"]),
        domain=_row_domain_from_path(
            f"{row['script_path']} {row['command']}"
        ),
        original_row_json=_canonical_json(row),
    )
    for row in _TRANCHE_B_MACHINE_ROWS["validation_commands"]
)

_EXPECTED_B_DOMAIN_COUNTS = {
    "latency": 5,
    "model_risk": 8,
    "operations": 5,
    "quantum": 8,
    "security": 3,
    "source": 9,
}
_EXPECTED_B_PRODUCTION_BASENAMES = {
    "contextual_computability.py",
    "stack_resolver.py",
    "input_resolver.py",
    "unit_conversion.py",
    "freshness.py",
    "point_in_time.py",
    "fallback.py",
    "service.py",
}
if (
    Counter(row.domain for row in TRANCHE_B_CLOSURE_ROWS)
    != _EXPECTED_B_DOMAIN_COUNTS
    or len({row.closure_id for row in TRANCHE_B_CLOSURE_ROWS}) != 38
    or len(
        {row.disposition_id for row in TRANCHE_B_REPOSITORY_DISPOSITIONS}
    )
    != 8
    or {
        Path(row.repository_path).name
        for row in TRANCHE_B_REPOSITORY_DISPOSITIONS
    }
    != _EXPECTED_B_PRODUCTION_BASENAMES
    or len({row.test_id for row in TRANCHE_B_TEST_ROWS}) != 44
    or len(
        {row.command_id for row in TRANCHE_B_VALIDATION_COMMANDS}
    )
    != 12
):
    raise ContractValidationError(
        ReasonCode.INVALID_CONTRACT,
        "Tranche-B machine-row identities, paths, or domain counts differ",
    )


TRANCHE_B_INDEPENDENT_VALIDATOR_BY_DOMAIN = MappingProxyType(
    {
        domain: (
            "tools/independent_validate_qku_computation_control_plane_"
            f"{domain}.py"
        )
        for domain in _EXPECTED_B_DOMAIN_COUNTS
    }
)


@dataclass(frozen=True, slots=True)
class TrancheBCoverageRowV1:
    row_id: str
    category: str
    domain: str
    predicate: str
    subject_ref: str
    upstream_owner: str
    exact_selector: str
    transformation: str
    canonical_owner: str
    responsible_agent: str
    central_service_operations: tuple[str, ...]
    downstream_consumers: tuple[str, ...]
    test_path: str
    independent_validator: str
    terminal_route: str
    terminal_status: CoverageTerminalStatusV1
    no_orphan_disposition: str = "VALIDATED_AND_CONSUMED"

    def __post_init__(self) -> None:
        for name in (
            "row_id",
            "category",
            "domain",
            "predicate",
            "subject_ref",
            "upstream_owner",
            "exact_selector",
            "transformation",
            "canonical_owner",
            "responsible_agent",
            "test_path",
            "independent_validator",
            "terminal_route",
            "no_orphan_disposition",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(
                self, name
            ):
                raise ContractValidationError(
                    ReasonCode.INCOMPLETE_CONTRACT,
                    f"Tranche-B coverage {name} is required",
                )
        for name in ("central_service_operations", "downstream_consumers"):
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or not values
                or any(not isinstance(value, str) or not value for value in values)
                or len(values) != len(set(values))
            ):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"Tranche-B coverage {name} must be exact and unique",
                )
        validate_relative_path(self.test_path)
        validate_relative_path(self.independent_validator)
        if not isinstance(self.terminal_status, CoverageTerminalStatusV1):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "Tranche-B terminal coverage status must be typed",
            )


@dataclass(frozen=True, slots=True)
class TrancheBCoverageManifestV1:
    rows: tuple[TrancheBCoverageRowV1, ...]
    derived_predicates: tuple[tuple[str, bool], ...]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.rows, tuple)
            or not self.rows
            or any(
                not isinstance(row, TrancheBCoverageRowV1)
                for row in self.rows
            )
            or len({row.row_id for row in self.rows}) != len(self.rows)
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "Tranche-B manifest rows must be unique typed values",
            )
        if (
            not isinstance(self.derived_predicates, tuple)
            or len(self.derived_predicates) != 8
            or any(
                not isinstance(item, tuple)
                or len(item) != 2
                or not isinstance(item[0], str)
                or not item[0]
                or type(item[1]) is not bool
                for item in self.derived_predicates
            )
            or len({item[0] for item in self.derived_predicates})
            != len(self.derived_predicates)
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "Tranche-B derived predicates must contain eight exact proofs",
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


_B_TEST_BASE = (
    "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_b/"
)


def _b_agent(domain: str) -> str:
    return {
        "latency": "commander_agent",
        "model_risk": "risk_manager_agent",
        "operations": "commander_agent",
        "quantum": "quantum_optimizer_agent",
        "security": "governance_agent",
        "source": "governance_agent",
        "architecture": "governance_agent",
    }[domain]


def _b_validator(domain: str) -> str:
    if domain == "architecture":
        return TRANCHE_B_INDEPENDENT_VALIDATOR_BY_DOMAIN["operations"]
    return TRANCHE_B_INDEPENDENT_VALIDATOR_BY_DOMAIN[domain]


def _b_blueprint() -> tuple[TrancheBCoverageRowV1, ...]:
    rows: list[TrancheBCoverageRowV1] = []
    for closure in TRANCHE_B_CLOSURE_ROWS:
        implementation = json.loads(closure.original_row_json)[
            "implementation_specification"
        ]
        rows.append(
            TrancheBCoverageRowV1(
                row_id=closure.closure_id,
                category="closure_rows",
                domain=closure.domain,
                predicate=closure.control_slug,
                subject_ref=closure.control_id,
                upstream_owner=str(implementation["canonical_owner"]),
                exact_selector=f"closure_id={closure.closure_id}",
                transformation="EXECUTE_EXACT_TERMINAL_CLOSURE_PREDICATE",
                canonical_owner=str(implementation["implementation_owner"]),
                responsible_agent=_b_agent(closure.domain),
                central_service_operations=(
                    "ST10-OP::02",
                    "ST10-OP::04",
                    "ST10-OP::05",
                    "ST10-OP::06",
                ),
                downstream_consumers=tuple(
                    str(value)
                    for value in implementation["consume_existing_owner_refs"]
                ),
                test_path=_mapped_test_module(
                    closure.domain,
                    "CONTROL_SPECIFICATION_TEST",
                ),
                independent_validator=_b_validator(closure.domain),
                terminal_route=(
                    f"{_b_agent(closure.domain)}::"
                    "TYPED_PASS_BLOCKER_OR_REGISTERED_FALLBACK"
                ),
                terminal_status=CoverageTerminalStatusV1.PASS,
            )
        )
    for disposition in TRANCHE_B_REPOSITORY_DISPOSITIONS:
        rows.append(
            TrancheBCoverageRowV1(
                row_id=disposition.disposition_id,
                category="repository_dispositions",
                domain="architecture",
                predicate="exact-production-path-present-and-consumed",
                subject_ref=disposition.repository_path,
                upstream_owner="CERTIFIED_ST12_TRANCHE_B_REPOSITORY_DISPOSITION",
                exact_selector=(
                    f"file_disposition_id={disposition.disposition_id}"
                ),
                transformation="CREATE_EXACT_DECLARED_PRODUCTION_SURFACE",
                canonical_owner="QKUComputationControlPlaneV1",
                responsible_agent="commander_agent",
                central_service_operations=("ST10-OP::02", "ST10-OP::06"),
                downstream_consumers=(
                    "QKUComputationControlPlaneServiceV1",
                    "AGENT-ORCH1",
                ),
                test_path=_B_TEST_BASE + "test_manifest_and_ownership.py",
                independent_validator=_b_validator("architecture"),
                terminal_route="QKUComputationControlPlaneServiceV1",
                terminal_status=CoverageTerminalStatusV1.PASS,
            )
        )
    for policy in TRANCHE_B_PARAMETER_POLICIES:
        rows.append(
            TrancheBCoverageRowV1(
                row_id=policy.parameter_id,
                category="parameter_policy_rows",
                domain="architecture",
                predicate="exact-certified-parameter-policy-retained",
                subject_ref=policy.parameter_audit_id,
                upstream_owner=policy.canonical_owner,
                exact_selector=f"parameter_id={policy.parameter_id}",
                transformation=(
                    "RESOLVE_EXACT_SEED_OR_TYPED_CALIBRATION_BLOCKER"
                ),
                canonical_owner="QKUComputationControlPlaneV1",
                responsible_agent="parameter_selector_agent",
                central_service_operations=(
                    "ST10-OP::04",
                    "ST10-OP::05",
                    "ST10-OP::06",
                ),
                downstream_consumers=(
                    "QKUComputationControlPlaneServiceV1",
                    "AGENT-ORCH1",
                ),
                test_path=_B_TEST_BASE + "test_math_oracle_vectors.py",
                independent_validator=_b_validator("architecture"),
                terminal_route=(
                    "parameter_selector_agent::EXACT_VALUE_OR_CALIBRATION_WORK_ORDER"
                ),
                terminal_status=CoverageTerminalStatusV1.PASS,
            )
        )
    for specification in TRANCHE_B_MATH_SPECIFICATIONS:
        domain = (
            "quantum"
            if specification.math_spec_id
            in {"MATH-46", "MATH-47", "MATH-48", "MATH-49"}
            else "model_risk"
        )
        rows.append(
            TrancheBCoverageRowV1(
                row_id=specification.math_spec_id,
                category="mathematical_specifications",
                domain=domain,
                predicate="registered-callable-and-typed-io-closed",
                subject_ref=specification.name,
                upstream_owner="CERTIFIED_ST12_TRANCHE_B_MATH_PAYLOAD",
                exact_selector=(
                    f"math_spec_id={specification.math_spec_id}"
                ),
                transformation="REGISTER_EXACT_DETERMINISTIC_CALLABLE",
                canonical_owner="QKUComputationControlPlaneV1",
                responsible_agent=_b_agent(domain),
                central_service_operations=("ST10-OP::05", "ST10-OP::06"),
                downstream_consumers=(
                    "QKUComputationControlPlaneServiceV1",
                    "PRETRADE1",
                    "READINESS1",
                ),
                test_path=_B_TEST_BASE + "test_math_oracle_vectors.py",
                independent_validator=_b_validator(domain),
                terminal_route=(
                    "QKUComputationControlPlaneServiceV1::PURE_COMPONENT_OR_STACK"
                ),
                terminal_status=CoverageTerminalStatusV1.PASS,
            )
        )
    for oracle_row in TRANCHE_B_ORACLE_COVERAGE_ROWS:
        domain = (
            "quantum"
            if oracle_row.math_spec_id
            in {"MATH-46", "MATH-47", "MATH-48", "MATH-49"}
            else "model_risk"
        )
        common = dict(
            domain=domain,
            upstream_owner="CERTIFIED_ST12_TRANCHE_B_ORACLE_PAYLOAD",
            exact_selector=f"math_spec_id={oracle_row.math_spec_id}",
            canonical_owner="QKUComputationControlPlaneV1",
            responsible_agent=_b_agent(domain),
            central_service_operations=("ST10-OP::05", "ST10-OP::06"),
            downstream_consumers=(
                "QKUComputationControlPlaneServiceV1",
                "IndependentModelValidatorV1",
            ),
            test_path=_B_TEST_BASE + "test_math_oracle_vectors.py",
            independent_validator=_b_validator(domain),
            terminal_route="INDEPENDENT_ORACLE_AND_MUTATION_VALIDATION",
            terminal_status=CoverageTerminalStatusV1.PASS,
        )
        rows.extend(
            (
                TrancheBCoverageRowV1(
                    row_id=oracle_row.oracle_id,
                    category="independent_oracle_specifications",
                    predicate="independent-oracle-lineage-closed",
                    subject_ref=oracle_row.math_spec_id,
                    transformation="INDEPENDENT_EXPECTED_VALUE_OR_INVARIANT",
                    **common,
                ),
                TrancheBCoverageRowV1(
                    row_id=oracle_row.vector_id,
                    category="golden_vectors_and_invariants",
                    predicate="golden-vector-and-material-mutation-closed",
                    subject_ref=oracle_row.math_spec_id,
                    transformation="EXECUTE_VECTOR_AND_MUTATION_PREDICATE",
                    **common,
                ),
            )
        )
    for test_row in TRANCHE_B_TEST_ROWS:
        rows.append(
            TrancheBCoverageRowV1(
                row_id=test_row.test_id,
                category="test_rows",
                domain=test_row.domain,
                predicate=(
                    f"consolidated-from={test_row.certified_test_path}"
                ),
                subject_ref=test_row.certified_test_path,
                upstream_owner="CERTIFIED_ST12_TRANCHE_B_TEST_PAYLOAD",
                exact_selector=f"test_id={test_row.test_id}",
                transformation="MAP_PREDICATE_TO_COHERENT_TEST_MODULE",
                canonical_owner="QKUComputationControlPlaneV1",
                responsible_agent=_b_agent(test_row.domain),
                central_service_operations=("ST10-OP::02", "ST10-OP::06"),
                downstream_consumers=(
                    "PRIMARY_VALIDATOR",
                    "INDEPENDENT_VALIDATOR",
                ),
                test_path=test_row.mapped_test_path,
                independent_validator=_b_validator(test_row.domain),
                terminal_route="VALIDATION_RUNNER::CERTIFIED_TEST_ROW",
                terminal_status=CoverageTerminalStatusV1.PASS,
            )
        )
    for command in TRANCHE_B_VALIDATION_COMMANDS:
        rows.append(
            TrancheBCoverageRowV1(
                row_id=command.command_id,
                category="validation_command_rows",
                domain=command.domain,
                predicate=command.command,
                subject_ref=command.script_path,
                upstream_owner="CERTIFIED_ST12_TRANCHE_B_COMMAND_PAYLOAD",
                exact_selector=f"command_id={command.command_id}",
                transformation="RUN_WITH_PINNED_PYTHON_MINUS_B",
                canonical_owner="EXISTING_VALIDATION_RUNNER",
                responsible_agent="commander_agent",
                central_service_operations=("ST10-OP::10",),
                downstream_consumers=(
                    "VALIDATION_INVENTORY",
                    "CHANGED_AREA_VALIDATION_ROUTER",
                ),
                test_path=_B_TEST_BASE + "test_manifest_and_ownership.py",
                independent_validator=_b_validator(command.domain),
                terminal_route="VALIDATION_RUNNER::ZERO_RETURN_CODE",
                terminal_status=CoverageTerminalStatusV1.PASS,
            )
        )
    for rule in TRANCHE_B_SOURCE_CLAIM_BINDING_RULES:
        rows.append(
            TrancheBCoverageRowV1(
                row_id=rule.binding_rule_id,
                category="source_claim_binding_rules",
                domain="source",
                predicate="exact-claim-source-epoch-rights-binding",
                subject_ref=rule.source_identity_ref,
                upstream_owner="CURRENT_SOURCE_POLICY_OWNER",
                exact_selector=(
                    f"binding_rule_id={rule.binding_rule_id}"
                ),
                transformation="VALIDATE_EXACT_ATOMIC_CLAIM_NO_SOURCE_SELECTION",
                canonical_owner="QKUComputationControlPlaneV1",
                responsible_agent="governance_agent",
                central_service_operations=("ST10-OP::02", "ST10-OP::04"),
                downstream_consumers=(
                    "RequiredInputResolverV1",
                    "SourceRevalidationSchedulerAdapterV1",
                ),
                test_path=_B_TEST_BASE + "test_source_quantum_model_risk.py",
                independent_validator=_b_validator("source"),
                terminal_route="governance_agent::SOURCE_REVALIDATION_OR_BLOCKER",
                terminal_status=CoverageTerminalStatusV1.PASS,
            )
        )
    return tuple(rows)


_EXPECTED_B_COVERAGE_COUNTS = {
    "closure_rows": 38,
    "repository_dispositions": 8,
    "parameter_policy_rows": 344,
    "mathematical_specifications": 30,
    "independent_oracle_specifications": 30,
    "golden_vectors_and_invariants": 30,
    "test_rows": 44,
    "validation_command_rows": 12,
    "source_claim_binding_rules": 10,
    "total_rows": 546,
}


def _b_row_predicate_passes(row: TrancheBCoverageRowV1) -> bool:
    if not (REPO_ROOT / row.test_path).is_file():
        return False
    if not (REPO_ROOT / row.independent_validator).is_file():
        return False
    if (
        not row.downstream_consumers
        or not row.central_service_operations
        or row.no_orphan_disposition != "VALIDATED_AND_CONSUMED"
    ):
        return False
    if row.category == "closure_rows":
        return any(
            closure.closure_id == row.row_id
            for closure in TRANCHE_B_CLOSURE_ROWS
        )
    if row.category == "repository_dispositions":
        return any(
            disposition.disposition_id == row.row_id
            and disposition.repository_path == row.subject_ref
            and (REPO_ROOT / disposition.repository_path).is_file()
            for disposition in TRANCHE_B_REPOSITORY_DISPOSITIONS
        )
    if row.category == "parameter_policy_rows":
        return any(
            policy.parameter_id == row.row_id
            for policy in TRANCHE_B_PARAMETER_POLICIES
        )
    if row.category == "mathematical_specifications":
        return (
            row.row_id in IMPLEMENTATION_REGISTRY
            and row.row_id in MATH_IO_CONTRACTS
            and callable(IMPLEMENTATION_REGISTRY[row.row_id].callable)
        )
    if row.category == "independent_oracle_specifications":
        return any(
            item.oracle_id == row.row_id
            and not ORACLE_BY_MATH_ID[
                item.math_spec_id
            ].production_import_allowed
            for item in TRANCHE_B_ORACLE_COVERAGE_ROWS
        )
    if row.category == "golden_vectors_and_invariants":
        return any(
            item.vector_id == row.row_id
            and not GOLDEN_VECTOR_BY_MATH_ID[
                item.math_spec_id
            ].production_import_allowed
            for item in TRANCHE_B_ORACLE_COVERAGE_ROWS
        )
    if row.category == "test_rows":
        return any(item.test_id == row.row_id for item in TRANCHE_B_TEST_ROWS)
    if row.category == "validation_command_rows":
        return any(
            item.command_id == row.row_id
            and item.command == row.predicate
            for item in TRANCHE_B_VALIDATION_COMMANDS
        )
    if row.category == "source_claim_binding_rules":
        return any(
            rule.binding_rule_id == row.row_id
            and not rule.source_pack_as_primary_allowed
            and not rule.broad_regex_or_alias_matching_allowed
            and not rule.codex_source_selection_allowed
            for rule in TRANCHE_B_SOURCE_CLAIM_BINDING_RULES
        )
    return False


def _tranche_b_real_numeric_proofs() -> tuple[tuple[str, bool], ...]:
    as_of = datetime(2026, 7, 27, 12, 0, tzinfo=UTC)
    observed = as_of - timedelta(seconds=30)
    traceparent = (
        "00-11111111111111111111111111111111-2222222222222222-01"
    )

    def context(version: str) -> ComputationContextKeyV1:
        return ComputationContextKeyV1(
            context_id="ST12B-MANIFEST-NUMERIC-PROOF",
            as_of=as_of,
            observed_at=observed,
            source_epoch_id="ST12B-MANIFEST-TEST-EPOCH",
            input_version=version,
            maximum_age=timedelta(minutes=5),
        )

    def evidence(
        value: TypedValueV1,
        context_key: ComputationContextKeyV1,
    ) -> ContextualInputValueV1:
        return ContextualInputValueV1(
            typed_value=value,
            point_in_time=PointInTimeEvidenceV1(
                evidence_id=f"PIT::{context_key.input_version}::{value.name}",
                field_id=value.name,
                field_class=PointInTimeFieldClassV1.OBSERVATION,
                observed_time=observed,
                effective_time=observed,
                source_available_time=observed,
                strategy_available_time=observed,
                received_time=observed,
                processed_time=observed,
                as_of_time=as_of,
                source_epoch_id=context_key.source_epoch_id,
                source_revision_id=(
                    f"REVISION::{context_key.input_version}"
                ),
            ),
            freshness_policy=FreshnessPolicyV1(
                policy_id=f"TTL::{value.name}",
                ttl=context_key.maximum_age,
                parameter_policy_ref="ComputationContextKeyV1::maximum_age",
                stale_behavior="FAIL_CLOSED_OR_REGISTERED_FALLBACK",
            ),
            source_identity="CERTIFIED_ST12B_INTEGRATION_VECTOR",
            source_state_id=f"STATE::{context_key.input_version}",
            source_epoch_id=context_key.source_epoch_id,
            rights_state="CERTIFIED_TEST_INPUT",
            value_lineage_ref=(
                f"VALUE::{context_key.input_version}::{value.name}"
            ),
            precision_policy=(
                "DECIMAL34_OR_DECLARED_FLOAT64_METHOD_BOUNDARY"
            ),
            rounding_policy="NO_IMPLICIT_QUANTIZATION",
            producer_ref="TrancheBCoverageManifestV1",
            consumer_refs=("QKUComputationControlPlaneServiceV1",),
        )

    def component(
        service: QKUComputationControlPlaneServiceV1,
        price: Decimal,
        suffix: str,
    ) -> ComputeComponentResponseV1:
        context_key = context(f"COMPONENT::{suffix}")
        values = TypedValueRecordV1(
            (
                TypedValueV1(
                    "contract_price",
                    TypedValueKindV1.DECIMAL,
                    price,
                    "currency",
                    "per_contract",
                ),
                TypedValueV1(
                    "payout_per_winning_contract",
                    TypedValueKindV1.DECIMAL,
                    Decimal("1"),
                    "currency",
                    "per_contract",
                ),
            )
        )
        request = ComputeComponentRequestV1(
            request_id=f"MANIFEST-COMPONENT::{suffix}",
            operation_name="compute_component",
            requested_at=as_of,
            principal_id="ST12B-MANIFEST",
            capability_bundle_id="NO-EFFECT",
            context=context_key,
            idempotency_key=f"ECONOMIC-COMPONENT::{suffix}",
            traceparent=traceparent,
            tracestate="",
            component_id="MATH-01",
            input_values=values,
            expected_output_schema_ref=output_schema_ref("MATH-01"),
        )
        return service.compute_component(
            request,
            contextual_evidence=tuple(
                evidence(value, context_key) for value in values.fields
            ),
        )

    def stack(
        service: QKUComputationControlPlaneServiceV1,
        price: Decimal,
        suffix: str,
    ) -> ComputeStackResponseV1:
        context_key = context(f"STACK::{suffix}")
        values = TypedValueRecordV1(
            (
                TypedValueV1(
                    "contract_price",
                    TypedValueKindV1.DECIMAL,
                    price,
                    "currency",
                    "per_contract",
                ),
                TypedValueV1(
                    "payout_per_winning_contract",
                    TypedValueKindV1.DECIMAL,
                    Decimal("1"),
                    "currency",
                    "per_contract",
                ),
                TypedValueV1(
                    "calibrated_model_probability",
                    TypedValueKindV1.FLOAT64,
                    0.60,
                    "probability",
                    "unit_interval",
                ),
            )
        )
        request = ComputeStackRequestV1(
            request_id=f"MANIFEST-STACK::{suffix}",
            operation_name="compute_stack",
            requested_at=as_of,
            principal_id="ST12B-MANIFEST",
            capability_bundle_id="NO-EFFECT",
            context=context_key,
            idempotency_key=f"ECONOMIC-STACK::{suffix}",
            traceparent=traceparent,
            tracestate="",
            stack_id="ST12B::TEMPLATE::MARKET_PROBABILITY_EDGE",
            component_ids=("MATH-01", "MATH-02"),
            input_values=values,
        )
        applicability = StackApplicabilityContextV1(
            trade_plan_candidate_id=f"TRADE-PLAN::{suffix}",
            context_key=context_key,
            venue="OWNER_SUPPLIED_PURE_COMPUTATION",
            market_family="PREDICTION_MARKETS",
            market_category="binary_event",
            mode="CONTRACT_ONLY",
            required_roles=(
                "market_implied_probability",
                "edge_probability",
            ),
            owner_intent_ref=f"OWNER-INTENT::{suffix}",
            input_lock_ref=f"INPUT-LOCK::{suffix}",
            source_readiness_receipt_refs=(
                f"SOURCE-READINESS::{suffix}",
            ),
            consumer_refs=("READINESS1", "PRETRADE1", "SVC1", "AGENT-ORCH1"),
        )
        return service.compute_stack(
            request,
            applicability=applicability,
            contextual_evidence=tuple(
                evidence(value, context_key) for value in values.fields
            ),
        )

    service = QKUComputationControlPlaneServiceV1(
        repo_root=REPO_ROOT,
        identity_views=(),
    )
    component_base = component(service, Decimal("0.47"), "BASE")
    component_mutated = component(service, Decimal("0.52"), "MUTATION")
    stack_base = stack(service, Decimal("0.47"), "BASE")
    stack_mutated = stack(service, Decimal("0.52"), "MUTATION")
    component_value = component_base.component_result.output_values.fields[
        0
    ].value
    component_mutated_value = (
        component_mutated.component_result.output_values.fields[0].value
    )
    stack_value = stack_base.stack_result.output_values.fields[0].value
    stack_mutated_value = (
        stack_mutated.stack_result.output_values.fields[0].value
    )
    downstream_input = next(
        row
        for row in stack_base.stack_result.component_results[
            1
        ].input_resolution_receipt.inputs
        if row.input_field_id == "market_implied_probability"
    )
    explanation_request = ExplainResolutionRequestV1(
        request_id="MANIFEST-EXPLANATION",
        operation_name="explain_resolution",
        requested_at=as_of,
        principal_id="ST12B-MANIFEST",
        capability_bundle_id="NO-EFFECT",
        context=component_base.context,
        idempotency_key="ECONOMIC-EXPLANATION",
        traceparent=traceparent,
        tracestate="",
        resolution_receipt_id=(
            component_base.component_result.execution_receipt.receipt_id
        ),
        explanation_scope="MANIFEST_DERIVED_PROOF",
        max_evidence_items=100,
    )
    explained = service.explain_resolution(
        explanation_request,
        resolution=component_base.component_result,
        owner_preferences_and_candidate_assertions=(
            "OWNER_PREFERENCE_IS_NOT_OBSERVED_FACT",
        ),
    )
    explanation = explained.explanation
    quantum = (
        PR162EQuantumAdapterV1(REPO_ROOT)
        .structural_readiness_requirements(QuantumModelKind.ISING)
    )
    blueprint = _b_blueprint()
    return (
        (
            "real_numeric_component_execution_proof",
            component_base.status is OperationStatusV1.SUCCEEDED
            and component_value == Decimal("0.47")
            and component_base.component_result.execution_receipt
            is not None,
        ),
        (
            "real_numeric_stack_execution_proof",
            stack_base.status is OperationStatusV1.SUCCEEDED
            and math.isclose(float(stack_value), 0.13, abs_tol=1e-15)
            and stack_base.stack_result.execution_receipt.topological_order
            == ("MATH-01", "MATH-02")
            and downstream_input.resolved_value == 0.47
            and downstream_input.producer_ref == "MATH-01"
            and "MATH-01.p_market->MATH-02.market_implied_probability"
            in stack_base.stack_result.execution_receipt.edge_consumption_refs[
                0
            ],
        ),
        (
            "material_mutation_sensitivity_proof",
            component_mutated_value == Decimal("0.52")
            and component_mutated_value != component_value
            and math.isclose(
                float(stack_mutated_value),
                0.08,
                abs_tol=1e-15,
            )
            and stack_mutated_value != stack_value,
        ),
        (
            "PR165_D2_agent_route_crosswalk_proof",
            len(AGENT_DUTY_ROUTES) == 8
            and len({row.agent_id for row in AGENT_DUTY_ROUTES}) == 8
            and all(
                row.operation_ids
                and row.upstream_refs
                and row.downstream_refs
                and row.authority_non_effects
                for row in AGENT_DUTY_ROUTES
            ),
        ),
        (
            "upstream_downstream_consumption_proof",
            len(blueprint) == 546
            and all(
                row.upstream_owner
                and row.exact_selector
                and row.transformation
                and row.central_service_operations
                and row.responsible_agent
                and row.downstream_consumers
                and row.test_path
                and row.independent_validator
                and row.terminal_route
                for row in blueprint
            ),
        ),
        (
            "institutional_feature_socket_owner_proof",
            len(INSTITUTIONAL_FEATURE_SOCKETS) == 9
            and all(
                not row.implements_economic_engine
                and row.canonical_owner
                in {
                    "RANK4",
                    "PRETRADE1",
                    "MEM1",
                    "QOPT1+PR162E-Q",
                }
                and row.unavailable_disposition
                and row.downstream_consumer
                for row in INSTITUTIONAL_FEATURE_SOCKETS
            ),
        ),
        (
            "LLM_ready_structured_explanation_proof",
            explained.status is OperationStatusV1.SUCCEEDED
            and isinstance(
                explanation,
                StructuredResolutionExplanationV1,
            )
            and bool(explanation.trusted_typed_input_facts)
            and bool(explanation.formula_and_implementation_lineage)
            and bool(explanation.dependency_and_conversion_lineage)
            and bool(explanation.point_in_time_and_freshness_state)
            and explanation.owner_preferences_and_candidate_assertions
            == ("OWNER_PREFERENCE_IS_NOT_OBSERVED_FACT",)
            and "NO_QPU_EFFECT" in explanation.forbidden_effects,
        ),
        (
            "quantum_structural_readiness_proof",
            len(quantum) == 8
            and {row.closure_id for row in quantum}
            == {
                row.closure_id
                for row in TRANCHE_B_CLOSURE_ROWS
                if row.domain == "quantum"
            }
            and all(
                isinstance(row, QuantumStructuralReadinessProjectionV1)
                and row.structural_requirements_complete
                and row.blocker_codes
                and not row.simulator_execution
                and not row.qpu_execution
                and not row.quantum_advantage_claim
                and not row.order_effect
                for row in quantum
            ),
        ),
    )


def build_tranche_b_coverage_manifest(
    *,
    predicate_overrides: MappingProxyType | dict[str, bool] | None = None,
) -> TrancheBCoverageManifestV1:
    overrides = {} if predicate_overrides is None else dict(predicate_overrides)
    blueprint = _b_blueprint()
    unexpected = set(overrides) - {row.row_id for row in blueprint}
    if unexpected:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            f"Tranche-B coverage override has unexpected rows: {sorted(unexpected)!r}",
        )
    rows = tuple(
        replace(
            row,
            terminal_status=(
                CoverageTerminalStatusV1.PASS
                if overrides.get(
                    row.row_id,
                    _b_row_predicate_passes(row),
                )
                else CoverageTerminalStatusV1.FAIL
            ),
        )
        for row in blueprint
    )
    return validate_tranche_b_coverage_manifest(
        TrancheBCoverageManifestV1(
            rows=rows,
            derived_predicates=_tranche_b_real_numeric_proofs(),
        )
    )


def validate_tranche_b_coverage_manifest(
    manifest: TrancheBCoverageManifestV1,
) -> TrancheBCoverageManifestV1:
    if not isinstance(manifest, TrancheBCoverageManifestV1):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "Tranche-B validation requires its exact typed manifest",
        )
    blueprint = _b_blueprint()
    if tuple(row.row_id for row in manifest.rows) != tuple(
        row.row_id for row in blueprint
    ):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "Tranche-B coverage contains a missing, renamed, duplicate, or unexpected row",
        )
    for actual, expected in zip(manifest.rows, blueprint, strict=True):
        for name in (
            "row_id",
            "category",
            "domain",
            "predicate",
            "subject_ref",
            "upstream_owner",
            "exact_selector",
            "transformation",
            "canonical_owner",
            "responsible_agent",
            "central_service_operations",
            "downstream_consumers",
            "test_path",
            "independent_validator",
            "terminal_route",
            "no_orphan_disposition",
        ):
            if getattr(actual, name) != getattr(expected, name):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"Tranche-B coverage metadata changed: {actual.row_id}:{name}",
                )
        if (
            actual.terminal_status is not CoverageTerminalStatusV1.PASS
            or not _b_row_predicate_passes(actual)
        ):
            raise ContractValidationError(
                ReasonCode.VALIDATION_FAILED,
                f"Tranche-B coverage predicate failed: {actual.row_id}",
            )
    if dict(manifest.executed_counts) != _EXPECTED_B_COVERAGE_COUNTS:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            f"Tranche-B coverage counts differ: {dict(manifest.executed_counts)!r}",
        )
    expected_derived = _tranche_b_real_numeric_proofs()
    if (
        manifest.derived_predicates != expected_derived
        or not all(value for _, value in manifest.derived_predicates)
    ):
        raise ContractValidationError(
            ReasonCode.VALIDATION_FAILED,
            "one or more Tranche-B derived execution/routing proofs failed",
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
    relative_paths = tuple(
        dict.fromkeys(
            (
                *PRODUCTION_CORE_PATHS,
                *(
                    row.repository_path
                    for row in TRANCHE_B_REPOSITORY_DISPOSITIONS
                ),
            )
        )
    )
    for relative in relative_paths:
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
    ids = tuple(
        math_id
        for math_id in IMPLEMENTATION_REGISTRY
        if math_id in TRANCHE_A_MATH_IDS
    )
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
                for math_id, record in IMPLEMENTATION_REGISTRY.items()
                if math_id in TRANCHE_A_MATH_IDS
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
            tuple(entry.oracle.math_spec_id for entry in TRANCHE_A_ORACLE_PACK)
            == MATH_IDS
            and tuple(
                entry.vector.math_spec_id for entry in TRANCHE_A_ORACLE_PACK
            )
            == MATH_IDS,
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


def _tranche_b_domain_semantics(domain: str) -> bool:
    if domain == "latency":
        as_of = datetime(2026, 7, 27, 12, 0, tzinfo=UTC)
        policy = FreshnessPolicyV1(
            "ST12B-VALIDATOR-TTL",
            timedelta(seconds=10),
            "CERTIFIED_TEST_POLICY",
            "FAIL_CLOSED",
        )
        boundary = FreshnessResolverV1.resolve_field(
            subject_id="TTL-BOUNDARY",
            observed_time=as_of - timedelta(seconds=10),
            as_of_time=as_of,
            policy=policy,
        )
        unknown = FreshnessResolverV1.resolve_field(
            subject_id="TTL-UNKNOWN",
            observed_time=as_of,
            as_of_time=as_of,
            policy=FreshnessPolicyV1(
                "ST12B-UNKNOWN-TTL",
                None,
                "CERTIFIED_TEST_POLICY",
                "FAIL_CLOSED",
            ),
        )
        deadline = DeadlineResolverV1.resolve(
            DeadlineBudgetV1(
                "ST12B-MONOTONIC-DEADLINE",
                Decimal("1"),
                "CERTIFIED_TEST_POLICY",
                Decimal("10"),
            ),
            monotonic_clock=lambda: 11.0,
        )
        return (
            boundary.state is FreshnessStateV1.FRESH
            and unknown.state is FreshnessStateV1.UNKNOWN_FAIL_CLOSED
            and deadline.within_budget
        )
    if domain == "model_risk":
        return (
            len(TRANCHE_B_MATH_SPECIFICATIONS) == 30
            and len(TRANCHE_B_ORACLE_COVERAGE_ROWS) == 30
            and all(
                row.math_spec_id in IMPLEMENTATION_REGISTRY
                and row.math_spec_id in MATH_IO_CONTRACTS
                and not ORACLE_BY_MATH_ID[
                    row.math_spec_id
                ].production_import_allowed
                and not ORACLE_BY_MATH_ID[
                    row.math_spec_id
                ].primary_validator_import_allowed
                and not GOLDEN_VECTOR_BY_MATH_ID[
                    row.math_spec_id
                ].production_import_allowed
                for row in TRANCHE_B_ORACLE_COVERAGE_ROWS
            )
        )
    if domain == "operations":
        return (
            len(TRANCHE_B_SERVICE_BINDINGS) == 15
            and all(
                binding.pure_in_process
                and not binding.external_or_durable_effect_allowed
                and binding.downstream_routes
                for binding in TRANCHE_B_SERVICE_BINDINGS.values()
            )
            and len(AGENT_DUTY_ROUTES) == 8
            and len(INSTITUTIONAL_FEATURE_SOCKETS) == 9
        )
    if domain == "quantum":
        rows = (
            PR162EQuantumAdapterV1(REPO_ROOT)
            .structural_readiness_requirements(QuantumModelKind.ISING)
        )
        return (
            len(rows) == 8
            and all(
                row.structural_requirements_complete
                and row.blocker_codes
                and row.classical_fallback
                == "DETERMINISTIC_SAME_FORMULATION_CLASSICAL_FALLBACK"
                and row.no_trade_fallback == "NO_TRADE"
                and not row.simulator_execution
                and not row.qpu_execution
                and not row.quantum_advantage_claim
                and not row.order_effect
                for row in rows
            )
        )
    if domain == "security":
        return (
            _no_dynamic_import_or_unsafe_deserialization()
            and _no_runtime_topology()
            and all(
                not binding.external_or_durable_effect_allowed
                for binding in TRANCHE_B_SERVICE_BINDINGS.values()
            )
        )
    if domain == "source":
        return (
            len(TRANCHE_B_SOURCE_CLAIM_BINDING_RULES) == 10
            and all(
                not rule.source_pack_as_primary_allowed
                and not rule.broad_regex_or_alias_matching_allowed
                and not rule.codex_source_selection_allowed
                and rule.permitted_consumers
                for rule in TRANCHE_B_SOURCE_CLAIM_BINDING_RULES
            )
        )
    return False


def validate_tranche_b_domain(domain: str) -> ValidationReportV1:
    if domain not in _EXPECTED_B_DOMAIN_COUNTS:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            f"unknown Tranche-B validation domain: {domain}",
        )
    semantic_pass = _tranche_b_domain_semantics(domain)
    checks = tuple(
        ValidationCheckV1(
            check_id=row.closure_id,
            passed=(
                semantic_pass
                and (REPO_ROOT / _mapped_test_module(
                    domain,
                    "CONTROL_SPECIFICATION_TEST",
                )).is_file()
                and (REPO_ROOT / _b_validator(domain)).is_file()
            ),
            detail=(
                f"{row.control_slug}; exact terminal closure; "
                "typed blocker/fallback and no-effect route"
            ),
        )
        for row in TRANCHE_B_CLOSURE_ROWS
        if row.domain == domain
    )
    if len(checks) != _EXPECTED_B_DOMAIN_COUNTS[domain]:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            f"Tranche-B {domain} closure count differs",
        )
    report = ValidationReportV1(f"tranche_b::{domain}", checks)
    report.assert_passed()
    return report


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
    if math_id == "MATH-16":
        result = call(
            differentials=values["differentials"],
            seed=values["seed"],
            replicates=values["replicates"],
        )
        return {"p_value": result.p_value, "reject": result.reject}
    if math_id == "MATH-17":
        result = call(
            values["sharpe_hat"],
            values["sharpe_ref"],
            values["n"],
            values["skewness"],
            values["kurtosis"],
        )
        return {"psr": result.psr, "z_score": result.z_score}
    if math_id == "MATH-18":
        moments = {
            "sharpe_hat": values["observed_sharpe"],
            "n": 100,
            "skewness": 0.0,
            "kurtosis": 3.0,
        }
        results = tuple(
            call(
                (0.2, 0.5, 1.0),
                trial_count,
                moments,
            )
            for trial_count in values["trial_counts"]
        )
        dsr_values = tuple(result.dsr for result in results)
        return {
            "bounded_0_1": all(
                0.0 <= value <= 1.0 for value in dsr_values
            ),
            "dsr_monotone_nonincreasing_with_trial_count": (
                dsr_values == tuple(sorted(dsr_values, reverse=True))
            ),
        }
    if math_id == "MATH-19":
        result = call(
            split_oos_relative_ranks=values[
                "split_oos_relative_ranks"
            ]
        )
        return {
            "bounded_0_1": 0.0 <= result.pbo <= 1.0,
            "pbo": result.pbo,
        }
    if math_id == "MATH-20":
        intervals = tuple(
            tuple(interval) for interval in values["intervals"]
        )
        test_indices = tuple(values["test_indices"])
        result = call(
            intervals,
            test_indices=test_indices,
            embargo_horizon=values["embargo"],
        )
        test_intervals = tuple(
            intervals[index] for index in test_indices
        )
        no_overlap = all(
            all(
                not (
                    intervals[index][0] <= test_end
                    and intervals[index][1] >= test_start
                )
                for test_start, test_end in test_intervals
            )
            for index in result.training_indices
        )
        embargo_respected = all(
            all(
                not (
                    test_end
                    < intervals[index][0]
                    < test_end + values["embargo"]
                )
                for _, test_end in test_intervals
            )
            for index in result.training_indices
        )
        return {
            "embargo_respected": embargo_respected,
            "no_interval_overlap": no_overlap,
            "training_indices": list(result.training_indices),
        }
    if math_id == "MATH-21":
        result = call(
            values["groups"],
            values["test_groups_per_split"],
        )
        return {
            "every_split_purged_and_embargoed": (
                result.every_split_purged_and_embargoed
            ),
            "no_post_hoc_path_selection": (
                result.no_post_hoc_path_selection
            ),
            "split_count": result.split_count,
        }
    if math_id == "MATH-22":
        result = call(values["samples"])
        return {"dr_estimate": result.dr_estimate}
    if math_id == "MATH-23":
        return {"ips": call(values["weights"], values["rewards"])}
    if math_id == "MATH-24":
        return {"snips": call(values["weights"], values["rewards"])}
    if math_id == "MATH-25":
        result = call(
            values["weights"],
            values["rewards"],
            values["direct_estimates"],
            values["tau"],
        )
        second = call(
            values["weights"],
            values["rewards"],
            values["direct_estimates"],
            values["tau"],
        )
        return {
            "deterministic_selection": result == second,
            "direct_model_indices": list(result.direct_model_indices),
            "importance_corrected_indices": list(
                result.importance_corrected_indices
            ),
        }
    if math_id == "MATH-36":
        result = call(
            values["yes_best_bid"],
            values["no_best_bid"],
            values["payout"],
        )
        return {
            "no_implied_ask": str(result.no_implied_ask),
            "yes_implied_ask": str(result.yes_implied_ask),
        }
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
        "EXACT_COUNT_AND_BOOLEAN",
        "EXACT_INDEX_SET",
        "ENUMERATION_INVARIANT",
        "BRUTE_FORCE_ENUMERATION",
        "EXACT_DISCRETE_ENUMERATION",
    }:
        return actual == expected
    tolerance = 1e-12 if policy.startswith("ABS_TOL_1E-12") else 1e-15
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
