"""Typed, deterministic plugin contracts used by generated PR162E artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence


ALLOWED_MATERIALIZATION_STATUSES = frozenset(
    {
        "COMPUTABLE_PLUGIN_READY",
        "COMPUTABLE_REPAIR_READY",
        "POST_REPAIR_RETEST_READY",
        "TERMINAL_NO_TRADE_NONLIVE",
    }
)

ALLOWED_RUNTIME_LANES = frozenset(
    {
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
    }
)

FORBIDDEN_RUNTIME_LANES = frozenset(
    {
        "LIVE_HOT_PATH_APPROVED",
        "LIVE_EXECUTION_APPROVED",
        "ORDER_RELEASE_APPROVED",
        "PRIVATE_STATE_ALLOWED",
        "SOURCE_TRUTH_ACCEPTANCE_ALLOWED",
        "CONNECTOR_BINDING_ALLOWED",
        "QUANTUM_BACKEND_EXECUTION_ALLOWED",
        "PROFIT_EVIDENCE_ALLOWED",
    }
)


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
