"""Typed, deterministic plugin contracts used by generated PR162E artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from enum import Enum, StrEnum
import json
import re
from types import MappingProxyType
from typing import Any, Mapping, Sequence


MATERIALIZATION_STATUSES: tuple[str, ...] = (
    "COMPUTABLE_PLUGIN_READY",
    "COMPUTABLE_REPAIR_READY",
    "POST_REPAIR_RETEST_READY",
    "TERMINAL_NO_TRADE_NONLIVE",
)

ALLOWED_RUNTIME_LANE_VALUES: tuple[str, ...] = (
    "STRUCTURAL_ONLY",
    "RESEARCH_CANDIDATE",
    "REPLAY_PATH_ONLY",
    "PAPER_PATH_ONLY",
    "OPEN_TRADE_SIM_ONLY",
    "PRECOMPUTE_PATH",
    "BATCH_RETEST_PATH",
    "BATCH_REPAIR_PATH",
    "MANUAL_NIGHTLY_PATH",
    "OWNER_REVIEW_ONLY",
    "CONNECTOR_READINESS_ROUTE_ONLY",
    "MARKET_PORTABILITY_ROUTE_ONLY",
    "FUTURE_LIVE_ELIGIBILITY_STRUCTURAL_ONLY",
)

FORBIDDEN_RUNTIME_LANE_VALUES: tuple[str, ...] = (
    "LIVE_HOT_PATH_APPROVED",
    "LIVE_EXECUTION_APPROVED",
    "ORDER_RELEASE_APPROVED",
    "PRIVATE_STATE_ALLOWED",
    "SOURCE_TRUTH_ACCEPTANCE_ALLOWED",
    "CONNECTOR_BINDING_ALLOWED",
    "QUANTUM_BACKEND_EXECUTION_ALLOWED",
    "PROFIT_EVIDENCE_ALLOWED",
)

PLUGIN_FAMILIES: tuple[str, ...] = (
    "FORMULA_PLUGIN",
    "ALGORITHM_PLUGIN",
    "PARAMETER_STACK_PLUGIN",
    "FEATURE_TRANSFORM_PLUGIN",
    "SIGNAL_SCORING_PLUGIN",
    "EDGE_ATTRIBUTION_PLUGIN",
    "PROBABILITY_CALIBRATION_PLUGIN",
    "EXPECTED_VALUE_PLUGIN",
    "THRESHOLD_POLICY_PLUGIN",
    "DECISION_RULE_PLUGIN",
    "FORMULA_EQUIVALENCE_PLUGIN",
    "FORMULA_VERSION_PLUGIN",
    "FORMULA_ROLLBACK_PLUGIN",
    "FEATURE_IMPUTATION_PLUGIN",
    "CANDIDATE_FILL_PLUGIN",
    "EXECUTION_COST_PLUGIN",
    "TCA_PLUGIN",
    "IMPL_SHORTFALL_PLUGIN",
    "FILL_MODEL_PLUGIN",
    "NO_FILL_PLUGIN",
    "PARTIAL_FILL_PLUGIN",
    "QUEUE_RISK_PLUGIN",
    "QUEUE_SURVIVAL_PLUGIN",
    "LATENCY_DECAY_PLUGIN",
    "SLIPPAGE_IMPACT_PLUGIN",
    "ADVERSE_SELECTION_PLUGIN",
    "CANCEL_REPLACE_PLUGIN",
    "CAPACITY_CROWDING_PLUGIN",
    "SETTLEMENT_FINALITY_PLUGIN",
    "MODEL_EXECUTION_GAP_PLUGIN",
    "AGGRESSION_LADDER_PLUGIN",
    "ORDERBOOK_STATE_PLUGIN",
    "STALE_BOOK_DIAGNOSTIC_PLUGIN",
    "STALE_BOOK_REPAIR_PLUGIN",
    "COST_REPAIR_PLUGIN",
    "FILL_REPAIR_PLUGIN",
    "LATENCY_REPAIR_PLUGIN",
    "PORTFOLIO_UTILITY_PLUGIN",
    "MARGINAL_UTILITY_PLUGIN",
    "DIVERSIFICATION_PLUGIN",
    "CORRELATION_CLUSTER_PLUGIN",
    "COMMON_DRIVER_EXPOSURE_PLUGIN",
    "RISK_BUDGET_PLUGIN",
    "REGIME_MEMORY_PLUGIN",
    "CONDITION_FINGERPRINT_PLUGIN",
    "NEGATIVE_COMBO_MEMORY_PLUGIN",
    "NEGATIVE_CANDIDATE_REPAIR_PLUGIN",
    "ALPHA_RECOVERY_PLUGIN",
    "CHAMP_CHALLENGER_PLUGIN",
    "OVERFIT_FDR_CONTROL_PLUGIN",
    "HOLDOUT_CONFIDENCE_PLUGIN",
    "LOWER_CONFIDENCE_BOUND_PLUGIN",
    "CALIBRATION_ERROR_PLUGIN",
    "RETEST_PRIORITY_PLUGIN",
    "REPAIR_PRIORITY_PLUGIN",
    "NO_TRADE_REASON_PLUGIN",
    "BANDIT_ARBITRATION_PLUGIN",
    "ENSEMBLE_STACKING_PLUGIN",
    "EXPECTED_REPAIR_VALUE_PLUGIN",
    "REPAIR_ROI_PLUGIN",
    "QUANTUM_RECIPE_PLUGIN",
    "QUBO_ADAPTER_PLUGIN",
    "BQM_ADAPTER_PLUGIN",
    "ISING_ADAPTER_PLUGIN",
    "CQM_ADAPTER_PLUGIN",
    "DQM_ADAPTER_PLUGIN",
    "QUAD_PROGRAM_ADAPTER_PLUGIN",
    "HYBRID_ROUTE_PLUGIN",
    "QUANTUM_PRECOMPUTE_SLATE_PLUGIN",
    "CLASSICAL_FALLBACK_PLUGIN",
    "INTERPRET_BACK_VALIDATOR_PLUGIN",
    "PROOF_VECTOR_VALIDATOR_PLUGIN",
    "FEASIBILITY_VALIDATOR_PLUGIN",
    "COEFFICIENT_SCALING_PLUGIN",
    "UNIT_NORMALIZATION_PLUGIN",
    "PRECISION_BINNING_PLUGIN",
    "PENALTY_TUNING_PLUGIN",
    "QUBIT_COST_ESTIMATOR_PLUGIN",
    "EMBEDDING_READINESS_PLUGIN",
    "QUANTUM_SHOT_BUDGET_STRUCTURAL_PLUGIN",
    "ANNEAL_SCHEDULE_STRUCTURAL_PLUGIN",
    "QUANTUM_ENCODING_REPAIR_PLUGIN",
    "PENALTY_SCALING_REPAIR_PLUGIN",
    "CONSTRAINT_REPAIR_PLUGIN",
    "HYBRID_FALLBACK_REPAIR_PLUGIN",
    "REPLAY_PAPER_RETEST_PLUGIN",
    "OPEN_TRADE_SIM_PLUGIN",
    "OWNER_DASHBOARD_REVIEW_ROUTE",
    "CONNECTOR_READINESS_ROUTE_WITHOUT_BINDING",
    "MARKET_PORTABILITY_ROUTE",
    "AGENT_WORK_ORDER_ROUTE",
    "AGENT_REPAIR_WORK_ORDER_ROUTE",
    "GOVERNANCE_REVIEW_ROUTE",
    "COMMANDER_DAG_ROUTE",
    "FUTURE_LIVE_ELIGIBILITY_STRUCTURAL_ROUTE",
)

ALLOWED_MATERIALIZATION_STATUSES = frozenset(MATERIALIZATION_STATUSES)
ALLOWED_RUNTIME_LANES = frozenset(ALLOWED_RUNTIME_LANE_VALUES)
FORBIDDEN_RUNTIME_LANES = frozenset(FORBIDDEN_RUNTIME_LANE_VALUES)


@dataclass(frozen=True)
class PluginAuthorityEnvelope:
    """Central authority boundary shared by all PR162E plugin rows."""

    authority_envelope_id: str
    no_live_order_authority: bool = True
    no_live_promotion_claim: bool = True
    no_source_truth_acceptance: bool = True
    no_connector_semantic_binding: bool = True
    no_private_state_fetch: bool = True
    no_runtime_cash_receipt: bool = True
    no_profit_evidence: bool = True
    no_quantum_backend_execution: bool = True
    no_quantum_advantage_claim: bool = True
    no_llm_hot_path: bool = True
    no_llm_order_release: bool = True
    no_llm_source_acceptance: bool = True
    no_llm_result_rewrite: bool = True
    no_qtt_sha_freeze_checksum_global_digest_authority: bool = True
    no_atomicrows_bundle_sha_hash_checksum_authority: bool = True

    def __post_init__(self) -> None:
        _require_canonical_text(
            self.authority_envelope_id,
            "authority_envelope_id",
        )
        for field_definition in fields(self):
            if field_definition.name == "authority_envelope_id":
                continue
            if type(getattr(self, field_definition.name)) is not bool:
                raise _package_contract_error(
                    PluginPackageReasonCodeV1.RUNTIME_EFFECT_FORBIDDEN,
                    f"{field_definition.name} must be an exact boolean",
                )

    def to_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PluginRuntimeBudget:
    lane: str
    runtime_budget_ms: int
    timeout_behavior: str = "FAIL_CLOSED_DIAGNOSTIC"
    deterministic_seed_behavior: str = "NO_RANDOMNESS"

    def __post_init__(self) -> None:
        if self.lane not in ALLOWED_RUNTIME_LANES:
            raise ValueError(f"unsupported runtime lane: {self.lane}")
        if self.lane in FORBIDDEN_RUNTIME_LANES:
            raise ValueError(f"forbidden runtime lane: {self.lane}")
        if self.runtime_budget_ms <= 0:
            raise ValueError("runtime_budget_ms must be positive")


@dataclass(frozen=True)
class PluginLineageRef:
    upstream_report_refs: tuple[str, ...]
    upstream_row_refs: tuple[str, ...]
    downstream_report_refs: tuple[str, ...]
    downstream_pr: str
    no_orphan_proof_ref: str

    def to_row(self) -> dict[str, Any]:
        return {
            "upstream_report_refs": list(self.upstream_report_refs),
            "upstream_row_refs": list(self.upstream_row_refs),
            "downstream_report_refs": list(self.downstream_report_refs),
            "downstream_pr": self.downstream_pr,
            "no_orphan_proof_ref": self.no_orphan_proof_ref,
        }


@dataclass(frozen=True)
class PluginContext:
    authority_envelope: PluginAuthorityEnvelope
    runtime_budget: PluginRuntimeBudget
    lineage: PluginLineageRef
    owning_agent: str
    supporting_agents: tuple[str, ...] = ()


@dataclass(frozen=True)
class PluginRequest:
    plugin_id: str
    plugin_family: str
    inputs: Mapping[str, Any]
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class PluginResponse:
    plugin_id: str
    plugin_family: str
    plugin_materialization_status: str
    output_fields: Mapping[str, Any]
    score_components: Mapping[str, float]
    downstream_report_refs: tuple[str, ...]
    terminal_reason: str = ""

    def __post_init__(self) -> None:
        if self.plugin_materialization_status not in ALLOWED_MATERIALIZATION_STATUSES:
            raise ValueError(
                "unsupported materialization status: "
                f"{self.plugin_materialization_status}"
            )
        if (
            self.plugin_materialization_status == "TERMINAL_NO_TRADE_NONLIVE"
            and not self.terminal_reason
        ):
            raise ValueError("terminal responses require terminal_reason")


@dataclass(frozen=True)
class PluginDiagnostic:
    plugin_id: str
    missing_fields: tuple[str, ...]
    stale_fields: tuple[str, ...] = ()
    schema_mismatch_fields: tuple[str, ...] = ()
    candidate_fill_attempts: tuple[Mapping[str, Any], ...] = ()
    root_cause_codes: tuple[str, ...] = ()
    diagnostic_adapter: str = "PR162E_DETERMINISTIC_DIAGNOSTIC_ADAPTER"

    @property
    def repairable(self) -> bool:
        return bool(self.missing_fields or self.candidate_fill_attempts)


@dataclass(frozen=True)
class PluginRepairPlan:
    plugin_id: str
    status: str
    missing_computation_surface: tuple[str, ...]
    candidate_fill_attempt_log: tuple[Mapping[str, Any], ...]
    required_fields_still_missing: tuple[str, ...]
    owning_agent: str
    downstream_repair_route: str
    downstream_retest_route: str
    expected_repair_value: float
    expected_repair_cost_complexity: str
    testable_repair_contract: str


@dataclass(frozen=True)
class PluginRetestPlan:
    plugin_id: str
    original_negative_ref: str
    repair_actions_applied: tuple[str, ...]
    repaired_input_fields: Mapping[str, Any]
    expected_post_repair_score_components: Mapping[str, float]
    retest_route: str
    candidate_lane: str
    owning_agent: str
    no_orphan_route: str


@dataclass(frozen=True)
class ValidationReceipt:
    ok: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


def execution_adjusted_edge(inputs: Mapping[str, Any]) -> float:
    """Compute the PR162E ranking surface without asserting profit evidence."""

    gross = float(inputs.get("gross_edge_candidate", inputs.get("expected_value_delta_candidate", 0.0)) or 0.0)
    deductions = (
        "explicit_fees",
        "explicit_fee_component",
        "estimated_spread_cost",
        "spread_component",
        "estimated_slippage",
        "slippage_component",
        "market_impact",
        "impact_component",
        "adverse_selection_penalty",
        "adverse_selection_component",
        "implementation_shortfall",
        "implementation_shortfall_proxy",
        "latency_decay",
        "latency_component",
        "queue_nonfill_penalty",
        "no_fill_opportunity_cost_component",
        "partial_fill_penalty",
        "cancel_replace_penalty",
        "settlement_or_finality_penalty",
        "settlement_finality_component",
        "capacity_crowding_penalty",
        "marginal_crowding_cost",
        "repair_uncertainty_penalty",
        "overfit_fdr_penalty",
        "false_discovery_penalty",
    )
    return round(gross - sum(float(inputs.get(field, 0.0) or 0.0) for field in deductions), 6)


class PluginAdapterBase:
    """Base deterministic adapter used by local PR162E smoke vectors."""

    plugin_family = "GENERIC_PLUGIN"
    runtime_lane = "STRUCTURAL_ONLY"
    runtime_budget_ms = 25

    def validate_request(self, request: PluginRequest) -> ValidationReceipt:
        errors: list[str] = []
        if not request.plugin_id:
            errors.append("missing plugin_id")
        if not request.plugin_family:
            errors.append("missing plugin_family")
        missing = [field for field in request.required_fields if field not in request.inputs]
        if missing:
            errors.append("missing required fields: " + ",".join(sorted(missing)))
        return ValidationReceipt(ok=not errors, errors=tuple(errors))

    def validate_response(self, response: PluginResponse) -> ValidationReceipt:
        errors: list[str] = []
        if response.plugin_materialization_status not in ALLOWED_MATERIALIZATION_STATUSES:
            errors.append("unsupported materialization status")
        if not response.downstream_report_refs and not response.terminal_reason:
            errors.append("missing downstream refs or terminal reason")
        return ValidationReceipt(ok=not errors, errors=tuple(errors))

    def diagnose_missing_inputs(
        self, request: PluginRequest, context: PluginContext
    ) -> PluginDiagnostic:
        missing = tuple(sorted(field for field in request.required_fields if field not in request.inputs))
        attempts = tuple(
            {
                "field": field,
                "candidate_source": "PR162E_CANDIDATE_FILL_INTERNAL_OR_EXTERNAL_QUEUE",
                "source_truth_accepted": False,
            }
            for field in missing
        )
        return PluginDiagnostic(
            plugin_id=request.plugin_id,
            missing_fields=missing,
            candidate_fill_attempts=attempts,
            root_cause_codes=tuple("MISSING_PARAMETER_VALUE" for _ in missing),
        )

    def evaluate(self, request: PluginRequest, context: PluginContext) -> PluginResponse:
        diagnostic = self.diagnose_missing_inputs(request, context)
        if diagnostic.missing_fields:
            status = "COMPUTABLE_REPAIR_READY"
            output = {
                "diagnostic_adapter": diagnostic.diagnostic_adapter,
                "missing_fields": list(diagnostic.missing_fields),
                "owning_agent": context.owning_agent,
                "repair_route": "PR162E_PluginRepairQueue.report.json",
            }
            score = {"execution_adjusted_edge": 0.0, "no_trade_utility": 0.0}
        else:
            status = "COMPUTABLE_PLUGIN_READY"
            edge = execution_adjusted_edge(request.inputs)
            output = {
                "candidate_lane": context.runtime_budget.lane,
                "not_profit_evidence": True,
                "execution_adjusted_edge": edge,
            }
            score = {
                "execution_adjusted_edge": edge,
                "lower_confidence_bound_edge": round(
                    edge - float(request.inputs.get("false_discovery_penalty", 0.0) or 0.0),
                    6,
                ),
                "no_trade_utility": 0.0,
            }
        return PluginResponse(
            plugin_id=request.plugin_id,
            plugin_family=request.plugin_family,
            plugin_materialization_status=status,
            output_fields=output,
            score_components=score,
            downstream_report_refs=context.lineage.downstream_report_refs,
        )

    def explain(
        self,
        request: PluginRequest,
        response: PluginResponse,
        context: PluginContext,
    ) -> PluginDiagnostic:
        if response.plugin_materialization_status == "COMPUTABLE_PLUGIN_READY":
            return PluginDiagnostic(plugin_id=request.plugin_id, missing_fields=())
        return self.diagnose_missing_inputs(request, context)

    def build_repair_plan(
        self,
        request: PluginRequest,
        context: PluginContext,
    ) -> PluginRepairPlan:
        diagnostic = self.diagnose_missing_inputs(request, context)
        return PluginRepairPlan(
            plugin_id=request.plugin_id,
            status="COMPUTABLE_REPAIR_READY",
            missing_computation_surface=diagnostic.missing_fields,
            candidate_fill_attempt_log=diagnostic.candidate_fill_attempts,
            required_fields_still_missing=diagnostic.missing_fields,
            owning_agent=context.owning_agent,
            downstream_repair_route="PR162E_PluginRepairQueue.report.json",
            downstream_retest_route="PR162E_PostRepairRetestQueue.report.json",
            expected_repair_value=0.0,
            expected_repair_cost_complexity="LOW_TO_MEDIUM_STRUCTURAL_FILL",
            testable_repair_contract="PR162E_PLUGIN_REPAIR_CONTRACT_V1",
        )

    def build_retest_plan(
        self,
        repair_plan: PluginRepairPlan,
        context: PluginContext,
    ) -> PluginRetestPlan:
        return PluginRetestPlan(
            plugin_id=repair_plan.plugin_id,
            original_negative_ref=repair_plan.plugin_id,
            repair_actions_applied=("candidate-fill",),
            repaired_input_fields={},
            expected_post_repair_score_components={"expected_retest_value": 0.0},
            retest_route=repair_plan.downstream_retest_route,
            candidate_lane=context.runtime_budget.lane,
            owning_agent=repair_plan.owning_agent,
            no_orphan_route=context.lineage.no_orphan_proof_ref,
        )


def adapter_smoke_vector() -> tuple[PluginRequest, PluginContext, PluginResponse]:
    envelope = PluginAuthorityEnvelope(
        authority_envelope_id="PR162E_AUTHORITY::NO_LIVE_NO_SOURCE_TRUTH"
    )
    context = PluginContext(
        authority_envelope=envelope,
        runtime_budget=PluginRuntimeBudget(lane="STRUCTURAL_ONLY", runtime_budget_ms=25),
        lineage=PluginLineageRef(
            upstream_report_refs=("PR162E_SMOKE_INPUT",),
            upstream_row_refs=("PR162E_SMOKE_ROW::00001",),
            downstream_report_refs=("PR162E_PluginTestVectors.report.json",),
            downstream_pr="PR162E",
            no_orphan_proof_ref="PR162E_NO_ORPHAN::SMOKE",
        ),
        owning_agent="Formula Materialization Agent",
        supporting_agents=("Governance",),
    )
    request = PluginRequest(
        plugin_id="PR162E_PLUGIN::SMOKE",
        plugin_family="FORMULA_PLUGIN",
        inputs={
            "gross_edge_candidate": 0.05,
            "explicit_fees": 0.01,
            "estimated_spread_cost": 0.005,
            "false_discovery_penalty": 0.002,
        },
        required_fields=("gross_edge_candidate",),
    )
    response = PluginAdapterBase().evaluate(request, context)
    return request, context, response


class PluginPackageReasonCodeV1(StrEnum):
    VERSION_INVALID = "VERSION_INVALID"
    IDENTITY_INVALID = "IDENTITY_INVALID"
    CANONICAL_INPUT_INVALID = "CANONICAL_INPUT_INVALID"
    PROFILE_SCOPE_INVALID = "PROFILE_SCOPE_INVALID"
    FAMILY_UNKNOWN = "FAMILY_UNKNOWN"
    EVIDENCE_INSUFFICIENT = "EVIDENCE_INSUFFICIENT"
    IMPLEMENTATION_MISSING = "IMPLEMENTATION_MISSING"
    NODE_DUPLICATE = "NODE_DUPLICATE"
    EDGE_DUPLICATE = "EDGE_DUPLICATE"
    EDGE_UNKNOWN_NODE = "EDGE_UNKNOWN_NODE"
    SELF_EDGE = "SELF_EDGE"
    DEPENDENCY_CYCLE = "DEPENDENCY_CYCLE"
    ADMISSION_INVALID = "ADMISSION_INVALID"
    OPERATION_PROFILE_INVALID = "OPERATION_PROFILE_INVALID"
    ROLLBACK_INVALID = "ROLLBACK_INVALID"
    SUPERSESSION_INVALID = "SUPERSESSION_INVALID"
    REPRODUCIBILITY_FAILED = "REPRODUCIBILITY_FAILED"
    DYNAMIC_LOAD_FORBIDDEN = "DYNAMIC_LOAD_FORBIDDEN"
    RUNTIME_EFFECT_FORBIDDEN = "RUNTIME_EFFECT_FORBIDDEN"


class PluginPackageContractError(ValueError):
    reason_code: PluginPackageReasonCodeV1
    message: str

    def __init__(
        self,
        reason_code: PluginPackageReasonCodeV1,
        message: str,
    ) -> None:
        if type(reason_code) is not PluginPackageReasonCodeV1:
            reason_code = PluginPackageReasonCodeV1.IDENTITY_INVALID
            message = "reason_code must use PluginPackageReasonCodeV1"
        elif (
            type(message) is not str
            or not message
            or message != message.strip()
            or any(ord(character) < 0x20 for character in message)
        ):
            reason_code = PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID
            message = "message must be nonempty canonical text"
        self.reason_code = reason_code
        self.message = message
        super().__init__(f"{reason_code.value}: {message}")


def _package_contract_error(
    reason_code: PluginPackageReasonCodeV1,
    message: str,
) -> PluginPackageContractError:
    return PluginPackageContractError(reason_code, message)


def _require_canonical_text(
    value: object,
    field_name: str,
    reason_code: PluginPackageReasonCodeV1 = (
        PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID
    ),
) -> str:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or any(ord(character) < 0x20 for character in value)
    ):
        raise _package_contract_error(
            reason_code,
            f"{field_name} must be nonempty canonical text",
        )
    return value


def _require_exact_nonnegative_int(value: object, field_name: str) -> int:
    if type(value) is not int or value < 0:
        raise _package_contract_error(
            PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
            f"{field_name} must be an exact nonnegative integer",
        )
    return value


def _require_typed_tuple(
    value: object,
    field_name: str,
    item_type: type,
    *,
    unique: bool = True,
) -> tuple[object, ...]:
    if type(value) is not tuple or any(type(item) is not item_type for item in value):
        raise _package_contract_error(
            PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
            f"{field_name} must be an exact typed tuple",
        )
    if unique and len(value) != len(set(value)):
        raise _package_contract_error(
            PluginPackageReasonCodeV1.IDENTITY_INVALID,
            f"{field_name} must be duplicate-free",
        )
    return value


def _require_canonical_text_tuple(
    value: object,
    field_name: str,
    *,
    unique: bool = True,
) -> tuple[str, ...]:
    values = _require_typed_tuple(value, field_name, str, unique=unique)
    for item in values:
        _require_canonical_text(item, field_name)
    return values  # type: ignore[return-value]


def _require_reason_tuple(
    value: object,
    field_name: str,
) -> tuple[PluginPackageReasonCodeV1, ...]:
    values = _require_typed_tuple(
        value,
        field_name,
        PluginPackageReasonCodeV1,
    )
    if tuple(sorted(values, key=lambda item: item.value)) != values:
        raise _package_contract_error(
            PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
            f"{field_name} must be sorted by reason-code value",
        )
    return values  # type: ignore[return-value]


@dataclass(frozen=True, slots=True, order=True)
class PackageVersionV1:
    major: int
    minor: int
    patch: int

    def __post_init__(self) -> None:
        for name in ("major", "minor", "patch"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise _package_contract_error(
                    PluginPackageReasonCodeV1.VERSION_INVALID,
                    f"{name} must be an exact nonnegative integer",
                )

    @classmethod
    def parse(cls, text: str) -> PackageVersionV1:
        if type(text) is not str or re.fullmatch(
            r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)",
            text,
        ) is None:
            raise _package_contract_error(
                PluginPackageReasonCodeV1.VERSION_INVALID,
                "version must be canonical final X.Y.Z text",
            )
        try:
            major, minor, patch = (int(part) for part in text.split("."))
        except ValueError as exc:
            raise _package_contract_error(
                PluginPackageReasonCodeV1.VERSION_INVALID,
                "version segments must fit the local integer runtime",
            ) from exc
        return cls(major=major, minor=minor, patch=patch)

    @property
    def canonical(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def compare(self, other: PackageVersionV1) -> int:
        if type(other) is not PackageVersionV1:
            raise _package_contract_error(
                PluginPackageReasonCodeV1.VERSION_INVALID,
                "version comparison requires PackageVersionV1",
            )
        return (self > other) - (self < other)


class PackageAdmissionStateV1(StrEnum):
    ADMITTED_CONTRACT_ONLY_NO_EFFECT = "ADMITTED_CONTRACT_ONLY_NO_EFFECT"
    HELD_EVIDENCE_INSUFFICIENT_NO_ADMISSION = (
        "HELD_EVIDENCE_INSUFFICIENT_NO_ADMISSION"
    )
    HELD_IMPLEMENTATION_MISSING_NO_ADMISSION = (
        "HELD_IMPLEMENTATION_MISSING_NO_ADMISSION"
    )


class PackageCompatibilityStateV1(StrEnum):
    PASS_CONTRACT_ONLY_NO_EFFECT = "PASS_CONTRACT_ONLY_NO_EFFECT"
    BLOCKED_EVIDENCE_INSUFFICIENT = "BLOCKED_EVIDENCE_INSUFFICIENT"
    BLOCKED_MISSING_IMPLEMENTATION = "BLOCKED_MISSING_IMPLEMENTATION"


class PackageRollbackTargetKindV1(StrEnum):
    RETAINED_VALIDATED_PREDECESSOR = "RETAINED_VALIDATED_PREDECESSOR"
    DISABLE_TO_NO_EFFECT = "DISABLE_TO_NO_EFFECT"
    DETERMINISTIC_CLASSICAL_FALLBACK = "DETERMINISTIC_CLASSICAL_FALLBACK"
    NO_TRADE = "NO_TRADE"
    UNAVAILABLE_OWNER_REVIEW_REQUIRED = "UNAVAILABLE_OWNER_REVIEW_REQUIRED"


class PackageOperationEligibilityStateV1(StrEnum):
    ELIGIBLE_CONTRACT_ONLY_NO_EFFECT = "ELIGIBLE_CONTRACT_ONLY_NO_EFFECT"
    BLOCKED_CURRENT_PACKAGE_NO_EFFECT = "BLOCKED_CURRENT_PACKAGE_NO_EFFECT"


class PackageValidationTerminalStateV1(StrEnum):
    VALIDATED_NO_EFFECT_WITH_HELD_DEPENDENCIES = (
        "VALIDATED_NO_EFFECT_WITH_HELD_DEPENDENCIES"
    )
    VALIDATED_NO_EFFECT_ALL_REQUIRED_COMPONENTS_ADMITTED = (
        "VALIDATED_NO_EFFECT_ALL_REQUIRED_COMPONENTS_ADMITTED"
    )
    REJECTED_INVALID = "REJECTED_INVALID"


class PackageSupersessionStateV1(StrEnum):
    INITIAL_CURRENT_NO_PREDECESSOR = "INITIAL_CURRENT_NO_PREDECESSOR"
    VALIDATED_MONOTONE_SUPERSESSION = "VALIDATED_MONOTONE_SUPERSESSION"
    REJECTED_NON_MONOTONE_OR_INCOMPATIBLE = (
        "REJECTED_NON_MONOTONE_OR_INCOMPATIBLE"
    )


@dataclass(frozen=True, slots=True)
class PackageOperationEligibilityV1:
    operation_class: str
    required_component_ids: tuple[str, ...]
    optional_component_ids: tuple[str, ...]
    blocking_component_ids: tuple[str, ...]
    state: PackageOperationEligibilityStateV1
    terminal_failure_route: str

    def __post_init__(self) -> None:
        _require_canonical_text(self.operation_class, "operation_class")
        required = _require_canonical_text_tuple(
            self.required_component_ids,
            "required_component_ids",
        )
        optional = _require_canonical_text_tuple(
            self.optional_component_ids,
            "optional_component_ids",
        )
        blocking = _require_canonical_text_tuple(
            self.blocking_component_ids,
            "blocking_component_ids",
        )
        if set(required).intersection(optional) or not set(blocking).issubset(required):
            raise _package_contract_error(
                PluginPackageReasonCodeV1.OPERATION_PROFILE_INVALID,
                "operation required, optional, and blocker sets are contradictory",
            )
        if type(self.state) is not PackageOperationEligibilityStateV1:
            raise _package_contract_error(
                PluginPackageReasonCodeV1.OPERATION_PROFILE_INVALID,
                "operation state must use PackageOperationEligibilityStateV1",
            )
        _require_canonical_text(
            self.terminal_failure_route,
            "terminal_failure_route",
        )


@dataclass(frozen=True, slots=True)
class SelectedComponentPackageEntryV1:
    package_component_id: str
    package_version: PackageVersionV1
    launch_role_id: str
    role_disposition: str
    admission_state: PackageAdmissionStateV1
    compatibility_state: PackageCompatibilityStateV1
    compatibility_reason_codes: tuple[PluginPackageReasonCodeV1, ...]
    selected_profile_ids: tuple[str, ...]
    required_operation_classes: tuple[str, ...]
    optional_operation_classes: tuple[str, ...]
    primary_plugin_family_or_none: str | None
    supporting_plugin_families: tuple[str, ...]
    existing_owner_paths: tuple[str, ...]
    future_owner_paths: tuple[str, ...]
    canonical_output_contract: str
    direct_dependency_component_ids: tuple[str, ...]
    default_failure_route: str
    latency_class: str
    rollback_target_kind: PackageRollbackTargetKindV1
    fallback_component_id_or_none: str | None
    authority_envelope_id: str

    def __post_init__(self) -> None:
        for name in (
            "package_component_id",
            "launch_role_id",
            "role_disposition",
            "canonical_output_contract",
            "default_failure_route",
            "latency_class",
            "authority_envelope_id",
        ):
            _require_canonical_text(getattr(self, name), name)
        if type(self.package_version) is not PackageVersionV1:
            raise _package_contract_error(
                PluginPackageReasonCodeV1.VERSION_INVALID,
                "package_version must use PackageVersionV1",
            )
        if type(self.admission_state) is not PackageAdmissionStateV1:
            raise _package_contract_error(
                PluginPackageReasonCodeV1.ADMISSION_INVALID,
                "admission_state must use PackageAdmissionStateV1",
            )
        if type(self.compatibility_state) is not PackageCompatibilityStateV1:
            raise _package_contract_error(
                PluginPackageReasonCodeV1.ADMISSION_INVALID,
                "compatibility_state must use PackageCompatibilityStateV1",
            )
        _require_reason_tuple(
            self.compatibility_reason_codes,
            "compatibility_reason_codes",
        )
        _require_canonical_text_tuple(
            self.selected_profile_ids,
            "selected_profile_ids",
        )
        required_operations = _require_canonical_text_tuple(
            self.required_operation_classes,
            "required_operation_classes",
        )
        optional_operations = _require_canonical_text_tuple(
            self.optional_operation_classes,
            "optional_operation_classes",
        )
        if set(required_operations).intersection(optional_operations):
            raise _package_contract_error(
                PluginPackageReasonCodeV1.OPERATION_PROFILE_INVALID,
                "required and optional operation classes must be disjoint",
            )
        if self.primary_plugin_family_or_none is not None:
            _require_canonical_text(
                self.primary_plugin_family_or_none,
                "primary_plugin_family_or_none",
            )
        supporting = _require_canonical_text_tuple(
            self.supporting_plugin_families,
            "supporting_plugin_families",
        )
        if self.primary_plugin_family_or_none in supporting:
            raise _package_contract_error(
                PluginPackageReasonCodeV1.FAMILY_UNKNOWN,
                "primary and supporting plugin families must be distinct",
            )
        existing = _require_canonical_text_tuple(
            self.existing_owner_paths,
            "existing_owner_paths",
        )
        future = _require_canonical_text_tuple(
            self.future_owner_paths,
            "future_owner_paths",
        )
        if set(existing).intersection(future):
            raise _package_contract_error(
                PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
                "existing and future owner paths must be disjoint",
            )
        _require_canonical_text_tuple(
            self.direct_dependency_component_ids,
            "direct_dependency_component_ids",
        )
        if type(self.rollback_target_kind) is not PackageRollbackTargetKindV1:
            raise _package_contract_error(
                PluginPackageReasonCodeV1.ROLLBACK_INVALID,
                "rollback_target_kind must use PackageRollbackTargetKindV1",
            )
        if self.fallback_component_id_or_none is not None:
            _require_canonical_text(
                self.fallback_component_id_or_none,
                "fallback_component_id_or_none",
            )


@dataclass(frozen=True, slots=True)
class SelectedComponentPackageManifestV1:
    schema_version: str
    package_id: str
    package_version: PackageVersionV1
    launch_graph_package_ref: str
    launch_graph_schema_version: str
    selected_scope_schema_version: str
    selected_profile_ids: tuple[str, ...]
    excluded_profile_ids: tuple[str, ...]
    entries: tuple[SelectedComponentPackageEntryV1, ...]
    dependency_edges: tuple[tuple[str, str], ...]
    topological_order: tuple[str, ...]
    operation_eligibility_rows: tuple[PackageOperationEligibilityV1, ...]
    builder_runtime_implementation: str
    builder_runtime_version: PackageVersionV1
    canonical_serialization_policy: str
    authority_envelope: PluginAuthorityEnvelope
    active_live_profile_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in (
            "schema_version",
            "package_id",
            "launch_graph_package_ref",
            "launch_graph_schema_version",
            "selected_scope_schema_version",
            "builder_runtime_implementation",
            "canonical_serialization_policy",
        ):
            _require_canonical_text(getattr(self, name), name)
        if (
            type(self.package_version) is not PackageVersionV1
            or type(self.builder_runtime_version) is not PackageVersionV1
        ):
            raise _package_contract_error(
                PluginPackageReasonCodeV1.VERSION_INVALID,
                "manifest versions must use PackageVersionV1",
            )
        selected = _require_canonical_text_tuple(
            self.selected_profile_ids,
            "selected_profile_ids",
        )
        excluded = _require_canonical_text_tuple(
            self.excluded_profile_ids,
            "excluded_profile_ids",
        )
        if set(selected).intersection(excluded):
            raise _package_contract_error(
                PluginPackageReasonCodeV1.PROFILE_SCOPE_INVALID,
                "selected and excluded profiles must be disjoint",
            )
        entries = _require_typed_tuple(
            self.entries,
            "entries",
            SelectedComponentPackageEntryV1,
        )
        if len({entry.package_component_id for entry in entries}) != len(entries):
            raise _package_contract_error(
                PluginPackageReasonCodeV1.IDENTITY_INVALID,
                "manifest component identities must be unique",
            )
        if type(self.dependency_edges) is not tuple:
            raise _package_contract_error(
                PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
                "dependency_edges must be an exact tuple",
            )
        for edge in self.dependency_edges:
            if (
                type(edge) is not tuple
                or len(edge) != 2
                or any(type(endpoint) is not str for endpoint in edge)
            ):
                raise _package_contract_error(
                    PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
                    "dependency edges must be exact two-string tuples",
                )
            for endpoint in edge:
                _require_canonical_text(endpoint, "dependency edge endpoint")
        if len(self.dependency_edges) != len(set(self.dependency_edges)):
            raise _package_contract_error(
                PluginPackageReasonCodeV1.EDGE_DUPLICATE,
                "dependency edges must be duplicate-free",
            )
        _require_canonical_text_tuple(
            self.topological_order,
            "topological_order",
        )
        operation_rows = _require_typed_tuple(
            self.operation_eligibility_rows,
            "operation_eligibility_rows",
            PackageOperationEligibilityV1,
        )
        if len({row.operation_class for row in operation_rows}) != len(operation_rows):
            raise _package_contract_error(
                PluginPackageReasonCodeV1.OPERATION_PROFILE_INVALID,
                "operation classes must be unique",
            )
        if type(self.authority_envelope) is not PluginAuthorityEnvelope:
            raise _package_contract_error(
                PluginPackageReasonCodeV1.RUNTIME_EFFECT_FORBIDDEN,
                "authority_envelope must use PluginAuthorityEnvelope",
            )
        _require_canonical_text_tuple(
            self.active_live_profile_ids,
            "active_live_profile_ids",
        )


@dataclass(frozen=True, slots=True)
class CompatibilityAndDependencyReceiptV1:
    package_id: str
    package_version: PackageVersionV1
    checked_entry_count: int
    checked_edge_count: int
    checked_operation_count: int
    topological_order: tuple[str, ...]
    operation_eligibility_rows: tuple[PackageOperationEligibilityV1, ...]
    terminal_state: PackageValidationTerminalStateV1
    reason_codes: tuple[PluginPackageReasonCodeV1, ...]
    authority_envelope: PluginAuthorityEnvelope

    def __post_init__(self) -> None:
        _require_canonical_text(self.package_id, "package_id")
        if type(self.package_version) is not PackageVersionV1:
            raise _package_contract_error(
                PluginPackageReasonCodeV1.VERSION_INVALID,
                "package_version must use PackageVersionV1",
            )
        for name in (
            "checked_entry_count",
            "checked_edge_count",
            "checked_operation_count",
        ):
            _require_exact_nonnegative_int(getattr(self, name), name)
        _require_canonical_text_tuple(self.topological_order, "topological_order")
        _require_typed_tuple(
            self.operation_eligibility_rows,
            "operation_eligibility_rows",
            PackageOperationEligibilityV1,
        )
        if type(self.terminal_state) is not PackageValidationTerminalStateV1:
            raise _package_contract_error(
                PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
                "terminal_state must use PackageValidationTerminalStateV1",
            )
        _require_reason_tuple(self.reason_codes, "reason_codes")
        if type(self.authority_envelope) is not PluginAuthorityEnvelope:
            raise _package_contract_error(
                PluginPackageReasonCodeV1.RUNTIME_EFFECT_FORBIDDEN,
                "authority_envelope must use PluginAuthorityEnvelope",
            )


@dataclass(frozen=True, slots=True)
class RollbackAndSupersessionReceiptV1:
    package_id: str
    package_version: PackageVersionV1
    predecessor_package_version_or_none: PackageVersionV1 | None
    superseded_package_versions: tuple[PackageVersionV1, ...]
    retained_predecessor_versions: tuple[PackageVersionV1, ...]
    disabled_component_ids: tuple[str, ...]
    operation_eligibility_rows: tuple[PackageOperationEligibilityV1, ...]
    supersession_state: PackageSupersessionStateV1
    terminal_state: PackageValidationTerminalStateV1
    reason_codes: tuple[PluginPackageReasonCodeV1, ...]
    authority_envelope: PluginAuthorityEnvelope

    def __post_init__(self) -> None:
        _require_canonical_text(self.package_id, "package_id")
        if type(self.package_version) is not PackageVersionV1:
            raise _package_contract_error(
                PluginPackageReasonCodeV1.VERSION_INVALID,
                "package_version must use PackageVersionV1",
            )
        if (
            self.predecessor_package_version_or_none is not None
            and type(self.predecessor_package_version_or_none) is not PackageVersionV1
        ):
            raise _package_contract_error(
                PluginPackageReasonCodeV1.ROLLBACK_INVALID,
                "predecessor version must use PackageVersionV1",
            )
        _require_typed_tuple(
            self.superseded_package_versions,
            "superseded_package_versions",
            PackageVersionV1,
        )
        _require_typed_tuple(
            self.retained_predecessor_versions,
            "retained_predecessor_versions",
            PackageVersionV1,
        )
        _require_canonical_text_tuple(
            self.disabled_component_ids,
            "disabled_component_ids",
        )
        _require_typed_tuple(
            self.operation_eligibility_rows,
            "operation_eligibility_rows",
            PackageOperationEligibilityV1,
        )
        if type(self.supersession_state) is not PackageSupersessionStateV1:
            raise _package_contract_error(
                PluginPackageReasonCodeV1.SUPERSESSION_INVALID,
                "supersession_state must use PackageSupersessionStateV1",
            )
        if type(self.terminal_state) is not PackageValidationTerminalStateV1:
            raise _package_contract_error(
                PluginPackageReasonCodeV1.ROLLBACK_INVALID,
                "terminal_state must use PackageValidationTerminalStateV1",
            )
        _require_reason_tuple(self.reason_codes, "reason_codes")
        if type(self.authority_envelope) is not PluginAuthorityEnvelope:
            raise _package_contract_error(
                PluginPackageReasonCodeV1.RUNTIME_EFFECT_FORBIDDEN,
                "authority_envelope must use PluginAuthorityEnvelope",
            )


@dataclass(frozen=True, slots=True)
class PackageReproducibilityReceiptV1:
    package_id: str
    package_version: PackageVersionV1
    canonical_input_refs: tuple[str, ...]
    builder_runtime_implementation: str
    builder_runtime_version: PackageVersionV1
    canonical_serialization_policy: str
    canonical_core_projection_json: str
    second_build_byte_equal: bool
    pure_build_effect_count: int
    terminal_state: PackageValidationTerminalStateV1
    reason_codes: tuple[PluginPackageReasonCodeV1, ...]
    authority_envelope: PluginAuthorityEnvelope

    def __post_init__(self) -> None:
        for name in (
            "package_id",
            "builder_runtime_implementation",
            "canonical_serialization_policy",
            "canonical_core_projection_json",
        ):
            _require_canonical_text(getattr(self, name), name)
        if (
            type(self.package_version) is not PackageVersionV1
            or type(self.builder_runtime_version) is not PackageVersionV1
        ):
            raise _package_contract_error(
                PluginPackageReasonCodeV1.VERSION_INVALID,
                "reproducibility versions must use PackageVersionV1",
            )
        _require_canonical_text_tuple(
            self.canonical_input_refs,
            "canonical_input_refs",
        )
        if type(self.second_build_byte_equal) is not bool:
            raise _package_contract_error(
                PluginPackageReasonCodeV1.REPRODUCIBILITY_FAILED,
                "second_build_byte_equal must be an exact boolean",
            )
        _require_exact_nonnegative_int(
            self.pure_build_effect_count,
            "pure_build_effect_count",
        )
        if type(self.terminal_state) is not PackageValidationTerminalStateV1:
            raise _package_contract_error(
                PluginPackageReasonCodeV1.REPRODUCIBILITY_FAILED,
                "terminal_state must use PackageValidationTerminalStateV1",
            )
        _require_reason_tuple(self.reason_codes, "reason_codes")
        if type(self.authority_envelope) is not PluginAuthorityEnvelope:
            raise _package_contract_error(
                PluginPackageReasonCodeV1.RUNTIME_EFFECT_FORBIDDEN,
                "authority_envelope must use PluginAuthorityEnvelope",
            )


_PACKAGE_SERIALIZATION_RECORD_TYPES: tuple[type, ...] = (
    PluginAuthorityEnvelope,
    PackageOperationEligibilityV1,
    SelectedComponentPackageEntryV1,
    SelectedComponentPackageManifestV1,
    CompatibilityAndDependencyReceiptV1,
    RollbackAndSupersessionReceiptV1,
    PackageReproducibilityReceiptV1,
)


def _normalize_package_serialization_value(value: object) -> object:
    def normalize(item: object, ancestors: set[int]) -> object:
        if item is None or type(item) in {bool, int}:
            return item
        if type(item) is str:
            return _require_canonical_text(item, "serialized text")
        if type(item) is PackageVersionV1:
            return item.canonical

        item_id = id(item)
        if item_id in ancestors:
            raise _package_contract_error(
                PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
                "canonical serialization values must be acyclic",
            )

        if isinstance(item, Enum):
            if type(item.value) in {list, dict, MappingProxyType}:
                raise _package_contract_error(
                    PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
                    "Enum payloads must remain in the immutable scalar domain",
                )
            ancestors.add(item_id)
            try:
                return normalize(item.value, ancestors)
            finally:
                ancestors.remove(item_id)

        if type(item) in _PACKAGE_SERIALIZATION_RECORD_TYPES:
            ancestors.add(item_id)
            try:
                return {
                    field_definition.name: normalize(
                        getattr(item, field_definition.name),
                        ancestors,
                    )
                    for field_definition in fields(item)
                }
            finally:
                ancestors.remove(item_id)

        if type(item) is tuple:
            ancestors.add(item_id)
            try:
                return [normalize(member, ancestors) for member in item]
            finally:
                ancestors.remove(item_id)

        if type(item) in {dict, MappingProxyType}:
            ancestors.add(item_id)
            try:
                normalized: dict[str, object] = {}
                for key, member in item.items():
                    canonical_key = _require_canonical_text(key, "mapping key")
                    normalized[canonical_key] = normalize(member, ancestors)
                return normalized
            finally:
                ancestors.remove(item_id)

        raise _package_contract_error(
            PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
            f"unsupported canonical serialization type: {type(item).__name__}",
        )

    return normalize(value, set())


def _canonical_package_json(value: object) -> str:
    return json.dumps(
        _normalize_package_serialization_value(value),
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
