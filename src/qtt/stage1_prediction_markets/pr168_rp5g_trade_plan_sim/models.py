"""Shared contracts and deterministic JSON helpers for PR168-RP5G."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, getcontext
import json
from pathlib import Path
from typing import Any, Iterable

getcontext().prec = 28

REPO_ROOT = Path(__file__).resolve().parents[4]
GENERATED_DIR = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_rp5g"
GENERATED_REF_PREFIX = "docs/master_plan/generated/pr168_rp5g"

PR_ID = "PR168-RP5G"
BRANCH_NAME = "pr168-rp5g-trade-plan-sim-engine"
BASELINE_SHA_VCS_METADATA_ONLY = "352a977e1c7903c2eda7aa60a297a9cc4b28b6ec"
RUN_ID = "PR168_RP5G_DETERMINISTIC_RUN_20260629T120000Z"
CREATED_AT_UTC = "2026-06-29T12:00:00Z"
REPORT_VERSION = "PR168-RP5G-v3.0"
EXECUTION_AUTHORITY_REF = "RP5G_EXEC_AUTH::REPLAY_PAPER_SIMULATION_EVIDENCE_ONLY_NO_ORDER_AUTHORITY"
BLOCKER_POLICY_REF = "RP5G_BLOCKER_POLICY::NUMERIC_EVIDENCE_AND_NON_AUTHORITY_HANDOFF_ONLY"
VALIDATOR_REF = "tools/validate_pr168_rp5g_trade_plan_sim.py"

JSON_OUTPUTS = ("art_reg.json",)
MARKDOWN_OUTPUTS = ("pr_body.md",)

REPORT_OUTPUTS = (
    "missing_req.report.json",
    "exec_auth.report.json",
    "exec_now_count.report.json",
    "rank4_handoff.report.json",
    "qopt1_handoff.report.json",
    "vs2_handoff.report.json",
    "mem1_handoff.report.json",
    "orch1_handoff.report.json",
    "paper_handoff.report.json",
    "live_dry_handoff.report.json",
    "shadow_handoff.report.json",
    "future.report.json",
    "no_orphan.report.json",
    "v3_self_audit.report.json",
    "v3_self_audit_final.report.json",
    "run_receipt.report.json",
)

JSONL_OUTPUTS = (
    "read_rec.jsonl",
    "in_cons.jsonl",
    "miss_opt.jsonl",
    "self_audit_pre.jsonl",
    "self_audit_post.jsonl",
    "mode_bound.jsonl",
    "blockers.jsonl",
    "params.jsonl",
    "policy_prov.jsonl",
    "master_trace.jsonl",
    "roadmap_trace.jsonl",
    "research_rec.jsonl",
    "source_coverage.jsonl",
    "source_intake.jsonl",
    "source_value_cand.jsonl",
    "institutional_default_cand.jsonl",
    "source_cov_max.jsonl",
    "source_claim_map.jsonl",
    "source_val_cand.jsonl",
    "nonofficial_cand.jsonl",
    "src_replay_plan.jsonl",
    "qku_access.jsonl",
    "library_query.jsonl",
    "agent_duty_map.jsonl",
    "owner_audit.jsonl",
    "owner_enable.jsonl",
    "live_shadow_route.jsonl",
    "rp5f_ingest.jsonl",
    "seed_consume.jsonl",
    "target_consume.jsonl",
    "grid_consume.jsonl",
    "stale_reval_consume.jsonl",
    "edge_input_consume.jsonl",
    "qku_compute_consume.jsonl",
    "trade_candidate.jsonl",
    "sim_run.jsonl",
    "data_prov.jsonl",
    "factual_gate.jsonl",
    "edge_capture_result.jsonl",
    "sim_result.jsonl",
    "exec_pnl.jsonl",
    "tca_decomp.jsonl",
    "fill_inputs_used.jsonl",
    "fill_latency_cap.jsonl",
    "queue_fill_result.jsonl",
    "adverse_select_result.jsonl",
    "latency_decay.jsonl",
    "capacity_crowding.jsonl",
    "cash_settle_result.jsonl",
    "calibration_result.jsonl",
    "overfit_fdr.jsonl",
    "scenario_ladder.jsonl",
    "notrade_cmp.jsonl",
    "port_marg_util.jsonl",
    "exec_rank_preview.jsonl",
    "champ_chall_preview.jsonl",
    "regime_outcome_key.jsonl",
    "negative_memory_hint.jsonl",
    "repair_retest_route.jsonl",
    "exec_now_delta.jsonl",
    "exec_now_proof.jsonl",
    "exec_now_reject.jsonl",
    "sched52_triage_consume.jsonl",
    "adapter_queue_demand.jsonl",
    "qstruct_problem.jsonl",
    "qobj_coeff.jsonl",
    "q_constraints.jsonl",
    "q_interp.jsonl",
    "q_classic_fb.jsonl",
    "qopt_handoff.jsonl",
    "qstruct_complete.jsonl",
    "q_quality.jsonl",
    "q_penalty.jsonl",
    "q_scale.jsonl",
    "q_counterfactual.jsonl",
    "q_influence_handoff.jsonl",
    "agent_route.jsonl",
    "agent_consume.jsonl",
    "artifact_io.jsonl",
    "file_route.jsonl",
    "lineage.jsonl",
    "dag.jsonl",
    "val_lineage.jsonl",
    "orph_art.jsonl",
    "orph_qku.jsonl",
    "no_meta.jsonl",
    "no_mut.jsonl",
    "no_sha.jsonl",
    "no_auth.jsonl",
    "downstream.jsonl",
    "completion_route.jsonl",
    "qku_compute_state.jsonl",
    "formula_compute_state.jsonl",
    "stack_compute_state.jsonl",
    "trade_compute_state.jsonl",
    "compute_completion_route.jsonl",
    "qku_comp.jsonl",
    "formula_comp.jsonl",
    "stack_comp.jsonl",
    "var_eval.jsonl",
    "var_reject.jsonl",
    "comp_fail.jsonl",
    "pm_microstructure.jsonl",
    "yes_no_parity_result.jsonl",
    "cross_venue_result.jsonl",
    "orderbook_imbalance_result.jsonl",
    "liquidity_decay_result.jsonl",
    "event_lifecycle_result.jsonl",
    "source_change_sensitivity.jsonl",
    "calibration_bucket.jsonl",
    "purged_walk_forward.jsonl",
    "lockbox_validation.jsonl",
    "search_family_fdr.jsonl",
    "false_discovery_audit.jsonl",
    "leak_audit.jsonl",
    "wf_purge.jsonl",
    "lockbox.jsonl",
    "fdr_family.jsonl",
    "trial_count.jsonl",
    "model_risk.jsonl",
    "portfolio_utility.jsonl",
    "capacity_limit.jsonl",
    "crowding_limit.jsonl",
    "near_clone_cluster.jsonl",
    "exposure_budget.jsonl",
    "marg_util.jsonl",
    "cap_crowd.jsonl",
    "clone_cluster.jsonl",
    "exposure_delta.jsonl",
    "policy_scn.jsonl",
    "queue_scn.jsonl",
    "lat_scn.jsonl",
    "fill_scn.jsonl",
    "owner_q1_edge.jsonl",
    "owner_q2_route.jsonl",
    "owner_q3_auto_path.jsonl",
    "edge_attr.jsonl",
    "obj_decomp.jsonl",
    "topk_sim.jsonl",
    "value_route.jsonl",
    "row_route.jsonl",
    "info_route.jsonl",
    "user_route.jsonl",
    "conn_route.jsonl",
    "handoff_route.jsonl",
    "order_auto_path.jsonl",
    "live_shadow_handoff.jsonl",
    "auth_block.jsonl",
    "authority_block.jsonl",
    "order_ready_prev.jsonl",
    "outcome_proof.jsonl",
    "agent_alias_map.jsonl",
    "agent_no_orphan.jsonl",
    "agent_authority_block.jsonl",
    "agent_intel.jsonl",
    "agent_task.jsonl",
    "agent_receipt.jsonl",
    "agent_missed.jsonl",
)

REQUIRED_INPUT_REFS = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/master_plan/generated/PR168_RP5C_FinalSummary.report.json",
    "docs/master_plan/generated/pr168_vs1/vs1_run_receipt.report.json",
    "docs/master_plan/generated/pr168_rp5d/rp5d_run_receipt.report.json",
    "docs/master_plan/generated/pr168_rp5e/run_receipt.report.json",
    "docs/master_plan/generated/pr168_rp5d_r1/run_receipt.report.json",
    "docs/master_plan/generated/pr168_rp5f/art_reg.json",
    "docs/master_plan/generated/pr168_rp5f/run_receipt.report.json",
    "docs/master_plan/generated/pr168_rp5f/targets.jsonl",
    "docs/master_plan/generated/pr168_rp5f/var_grid.jsonl",
    "docs/master_plan/generated/pr168_rp5f/trade_seed.jsonl",
    "docs/master_plan/generated/pr168_rp5f/pre_submit_reval.jsonl",
    "docs/master_plan/generated/pr168_rp5f/no_stale_candidate.jsonl",
    "docs/master_plan/generated/pr168_rp5f/qku_compute_route.jsonl",
    "docs/master_plan/generated/pr168_rp5f/qku_target_use.jsonl",
    "docs/master_plan/generated/pr168_rp5f/tca_inputs.jsonl",
    "docs/master_plan/generated/pr168_rp5f/fill_inputs.jsonl",
    "docs/master_plan/generated/pr168_rp5f/queue_fill_inputs.jsonl",
    "docs/master_plan/generated/pr168_rp5f/adverse_select.jsonl",
    "docs/master_plan/generated/pr168_rp5f/lat_inputs.jsonl",
    "docs/master_plan/generated/pr168_rp5f/capacity_inputs.jsonl",
    "docs/master_plan/generated/pr168_rp5f/cash_settle_inputs.jsonl",
    "docs/master_plan/generated/pr168_rp5f/pm_edge_hints.jsonl",
    "docs/master_plan/generated/pr168_rp5f/yes_no_parity.jsonl",
    "docs/master_plan/generated/pr168_rp5f/orderbook_imbalance.jsonl",
    "docs/master_plan/generated/pr168_rp5f/port_cap.jsonl",
    "docs/master_plan/generated/pr168_rp5f/marg_util.jsonl",
    "docs/master_plan/generated/pr168_rp5f/q_grid.jsonl",
    "docs/master_plan/generated/pr168_rp5f/q_constraints.jsonl",
    "docs/master_plan/generated/pr168_rp5f/q_interp.jsonl",
    "docs/master_plan/generated/pr168_rp5f/classic_fallback.jsonl",
    "docs/master_plan/generated/pr168_rp5f/agent_route.jsonl",
    "docs/master_plan/generated/pr168_rp5f/artifact_io.jsonl",
    "docs/master_plan/generated/pr168_rp5f/file_route.jsonl",
    "docs/master_plan/generated/pr168_rp5f/dag.jsonl",
    "docs/master_plan/generated/pr168_rp5f/orph_art.jsonl",
    "docs/master_plan/generated/pr168_rp5f/orph_qku.jsonl",
    "docs/master_plan/generated/pr168_rp5e/topk.jsonl",
    "docs/master_plan/generated/pr168_rp5e/ctx_univ.jsonl",
    "docs/master_plan/generated/pr168_rp5d_r1/promote.jsonl",
    "docs/master_plan/generated/pr168_rp5d_r1/exec_now_proof.jsonl",
    "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
)

OPTIONAL_INPUT_REFS = (
    "docs/master_plan/generated/PR168_RP_RouteTriage.report.json",
    "docs/master_plan/generated/PR168_RP_FullMasterPlanSectionCrosswalk.report.json",
    "docs/master_plan/generated/PR168_RP_MarketSpecificSectionIndexes.report.json",
    "docs/master_plan/generated/PR168_RP_CommandActionMatrix.report.json",
)

FALSE_FLAG_FIELDS = (
    "metadata_is_proof_flag",
    "accepted_source_fact_flag",
    "paper_authority_flag",
    "paper_submit_authority_flag",
    "shadow_authority_flag",
    "live_authority_flag",
    "live_submit_authority_flag",
    "order_authority_flag",
    "profit_guarantee_flag",
    "profit_proof_flag",
    "qopt_execution_flag",
    "quantum_backend_execution_flag",
    "quantum_advantage_claim_flag",
    "proprietary_claim_flag",
    "qtt_sha_authority_flag",
    "atomicrows_sha_ref_flag",
    "connector_write_flag",
    "private_state_fetch_flag",
    "cash_account_read_flag",
    "formula_mutation_flag",
    "formula_deletion_flag",
    "qku_mutation_flag",
    "qku_deletion_flag",
    "global_ban_flag",
    "source_fact_acceptance_flag",
    "connector_semantic_binding_flag",
    "live_default_flag",
    "real_order_authority_created_flag",
    "paper_submit_authority_created_flag",
    "live_order_authority_created_flag",
    "buy_sell_open_close_logic_created_flag",
    "buy_sell_open_close_created_flag",
    "live_or_shadow_authority_created_flag",
    "order_authority_created_flag",
    "runtime_authority_created_flag",
    "paper_order_authority_created_flag",
    "live_submit_ready_flag",
    "paper_submit_ready_flag",
    "order_submit_ready_flag",
    "connector_write_created_flag",
    "real_market_profit_proof_flag",
    "real_market_loss_proof_flag",
)

FORBIDDEN_STATE_VALUES = (
    "FINAL_CHAMPION",
    "FINAL_TRADE_RANK",
    "LIVE_CANDIDATE",
    "ORDER_READY",
    "PROFIT_GUARANTEE",
    "QUANTUM_ADVANTAGE_PROVEN",
    "PAPER_ORDER_SUBMIT_READY",
    "SHADOW_EXECUTABLE_NOW",
    "LIVE_EXECUTABLE_NOW",
    "ORDER_SUBMIT_READY",
    "BUY_SELL_OPEN_CLOSE_READY",
    "CONNECTOR_WRITE_READY",
    "PRIVATE_STATE_READY",
    "CASH_ACCOUNT_READY",
    "LIVE_DRYRUN_EXECUTION_READY",
    "LIMITED_LIVE_CANARY_READY",
    "FIXED_TRADE_PLAN",
    "NON_EXPIRING_TRADE_PLAN",
    "STALE_CANDIDATE_APPROVED",
    "SOURCE_FACT_ACCEPTED",
    "CONNECTOR_SEMANTIC_BOUND",
    "QOPT_EXECUTED",
    "QUANTUM_BACKEND_EXECUTED",
)

PARAM_DEFAULTS: dict[str, object] = {
    "z_value_lcb_default": "1.645",
    "z_value_conservative_default": "1.960",
    "no_trade_required_margin_cash": "0.000000",
    "fdr_q_value_default": "0.100000",
    "max_candidates_per_target": 2,
    "max_stacks_per_target": 1,
    "max_variable_combinations_per_stack": 2,
    "successive_halving_eta": 3,
    "thin_book_penalty_rate": "0.080000",
    "queue_position_penalty_rate": "0.030000",
    "adverse_selection_penalty_rate": "0.060000",
    "alpha_decay_per_ms": "0.000004",
    "capital_lock_rate_per_hour": "0.000010",
}


@dataclass(frozen=True)
class CommonEnvelopeV1:
    schema_version: str = REPORT_VERSION
    row_id: str = ""
    run_id: str = RUN_ID
    created_at_utc: str = CREATED_AT_UTC
    source_pr: str = PR_ID
    upstream_refs: tuple[str, ...] = ()
    downstream_refs: tuple[str, ...] = ()
    owner_agent: str = ""
    consumer_agents: tuple[str, ...] = ()
    validation_refs: tuple[str, ...] = (VALIDATOR_REF,)
    execution_authority_ref: str = EXECUTION_AUTHORITY_REF
    blocker_policy_ref: str = BLOCKER_POLICY_REF
    connector_refs_or_future_connector_status: str = "FUTURE_CONNECTOR_STATUS_ONLY_NO_WRITE"
    provenance_tier: str = "RP5G_REPLAY_PAPER_SIMULATION_EVIDENCE"


ROW_MODEL_NAMES = (
    "MasterPlanTraceV1",
    "RoadmapTraceV1",
    "LibraryQueryReceiptV1",
    "AgentDutyMapV1",
    "SourceCoverageReceiptV1",
    "InstitutionalDefaultCandidateV1",
    "RP5FSeedConsumptionReceiptV1",
    "TradePlanCandidateV1",
    "TradePlanSimulationRunV1",
    "TradePlanInputProvenanceV1",
    "ReplayPaperFactualGateV1",
    "ExecutionAdjustedPnLV1",
    "TCADecompositionV1",
    "FillQueueLatencyCapacityV1",
    "QueueFillResultV1",
    "AdverseSelectionPenaltyV1",
    "LatencyDecayResultV1",
    "CapacityCrowdingResultV1",
    "CashflowSettlementResultV1",
    "CalibrationResultV1",
    "OverfitFDRControlResultV1",
    "ScenarioLadderResultV1",
    "NoTradeComparatorResultV1",
    "PortfolioMarginalUtilityResultV1",
    "ExecutionAdjustedSimulationRankV1",
    "ChampionChallengerSimulationPreviewV1",
    "RegimeConditionedOutcomeKeyV1",
    "NegativeOutcomeMemoryHintV1",
    "RepairRetestRouteV1",
    "ExecutableNowDeltaResultV1",
    "QuantumStructuralProblemV1",
    "QuantumObjectiveCoefficientMapV1",
    "QuantumConstraintMapV1",
    "QuantumInterpretBackMapV1",
    "ClassicalFallbackComparisonV1",
    "DownstreamHandoffV1",
    "ArtifactIOMatrixV1",
    "FileRouteRegistryV1",
    "NoOrphanSimulationProofV1",
)


def _make_row_model(name: str) -> type[CommonEnvelopeV1]:
    cls = type(name, (CommonEnvelopeV1,), {"__module__": __name__})
    return dataclass(frozen=True)(cls)


for _row_model_name in ROW_MODEL_NAMES:
    globals()[_row_model_name] = _make_row_model(_row_model_name)


def dec(value: str | int | float | Decimal) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def score(value: str | int | float | Decimal) -> str:
    return str(dec(value).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def clamp(value: str | int | float | Decimal, low: Decimal = Decimal("0"), high: Decimal = Decimal("1")) -> Decimal:
    raw = dec(value)
    return max(low, min(high, raw))


def rel_ref(path: Path | str) -> str:
    p = Path(path)
    if p.is_absolute():
        p = p.relative_to(REPO_ROOT)
    return p.as_posix()


def generated_ref(filename: str) -> str:
    return f"{GENERATED_REF_PREFIX}/{filename}"


def manifest_name(filename: str) -> str:
    return f"{Path(filename).stem}.manifest.json"


def all_artifact_filenames(include_manifests: bool = True) -> tuple[str, ...]:
    base = tuple(dict.fromkeys((*JSON_OUTPUTS, *REPORT_OUTPUTS, *JSONL_OUTPUTS, *MARKDOWN_OUTPUTS)))
    if not include_manifests:
        return base
    manifests = tuple(manifest_name(name) for name in JSONL_OUTPUTS)
    return tuple(dict.fromkeys((*base, *manifests)))


def stable_json(payload: Any, *, compact: bool = False) -> str:
    separators = (",", ":") if compact else None
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=None if compact else 2, separators=separators) + "\n"


def read_json(path: Path) -> Any:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(payload), encoding="utf-8")


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def stable_unique(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            out.extend(stable_unique(value))
            continue
        text = str(value).strip()
        if text:
            out.append(text)
    return sorted(dict.fromkeys(out), key=lambda item: (item.casefold(), item))


def with_common(
    row: dict[str, Any],
    *,
    row_id: str,
    owner_agent: str,
    consumer_agents: Iterable[str],
    upstream_refs: Iterable[str],
    downstream_refs: Iterable[str],
    validation_refs: Iterable[str] = (VALIDATOR_REF,),
    blocker_policy_ref: str = BLOCKER_POLICY_REF,
    execution_authority_ref: str = EXECUTION_AUTHORITY_REF,
    provenance_tier: str = "RP5G_REPLAY_PAPER_SIMULATION_EVIDENCE",
) -> dict[str, Any]:
    upstream = stable_unique(upstream_refs)
    downstream = stable_unique(downstream_refs)
    consumers = stable_unique(consumer_agents)
    validation = stable_unique(validation_refs)
    out = dict(row)
    out.setdefault("schema_version", REPORT_VERSION)
    out.setdefault("row_id", row_id)
    out.setdefault("run_id", RUN_ID)
    out.setdefault("created_at_utc", CREATED_AT_UTC)
    out.setdefault("source_pr", PR_ID)
    out.setdefault("upstream_refs", upstream)
    out.setdefault("downstream_refs", downstream)
    out.setdefault("owner_agent", owner_agent)
    out.setdefault("consumer_agents", consumers)
    out.setdefault("validation_refs", validation)
    out.setdefault("execution_authority_ref", execution_authority_ref)
    out.setdefault("blocker_policy_ref", blocker_policy_ref)
    out.setdefault("connector_refs_or_future_connector_status", "FUTURE_CONNECTOR_STATUS_ONLY_NO_WRITE")
    out.setdefault("provenance_tier", provenance_tier)
    for flag in FALSE_FLAG_FIELDS:
        out.setdefault(flag, False)
    out.setdefault("candidate_only_flag", False)
    out.setdefault("orphan_flag", False)
    out.setdefault("fixed_trade_instruction_flag", False)
    out.setdefault("non_expiring_trade_plan_flag", False)
    out.setdefault("stale_candidate_authority_flag", False)
    out.setdefault("producer_agent", owner_agent)
    out.setdefault("consumer_agent_refs", consumers)
    out.setdefault("upstream_artifact_refs", upstream)
    out.setdefault("downstream_artifact_refs", downstream)
    out.setdefault("master_plan_trace_refs", [generated_ref("master_trace.jsonl")])
    return out


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]], *, schema_version_name: str) -> None:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(stable_json(row, compact=True) for row in materialized), encoding="utf-8")
    manifest = with_common(
        {
            "manifest_id": f"{path.stem.upper()}_MANIFEST",
            "physical_filename": rel_ref(path),
            "schema_version_name": schema_version_name,
            "row_count": len(materialized),
            "shard_file_path": rel_ref(path),
            "row_shard_family": path.name,
            "manifest_for_shard_family_required_flag": True,
            "generated_surface_authority_class": "RP5G_GENERATED_REPLAY_PAPER_SIMULATION_EVIDENCE_NOT_ORDER_AUTHORITY",
        },
        row_id=f"{path.stem.upper()}_MANIFEST",
        owner_agent="GovernanceAgent",
        consumer_agents=["RP5GValidator", "ArtifactNameAgent", "PathSafetyAgent"],
        upstream_refs=[generated_ref(path.name)],
        downstream_refs=[generated_ref("run_receipt.report.json")],
    )
    write_json(path.with_name(manifest_name(path.name)), manifest)


def schema_name(filename: str) -> str:
    stem = filename.removesuffix(".jsonl").removesuffix(".json").replace(".report", "")
    return "".join(part.capitalize() for part in stem.split("_") if part) + "V1"

