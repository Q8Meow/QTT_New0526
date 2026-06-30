"""Shared deterministic contracts for PR168-VS2 artifacts."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, getcontext
import json
from pathlib import Path
from typing import Any, Iterable

getcontext().prec = 28

REPO_ROOT = Path(__file__).resolve().parents[4]
GENERATED_DIR = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_vs2"
GENERATED_REF_PREFIX = "docs/master_plan/generated/pr168_vs2"

PR_ID = "PR168-VS2"
BRANCH_NAME = "pr168-vs2-paper-intent-candidate-generator"
RUN_ID = "PR168_VS2_DETERMINISTIC_RUN_20260630T110000Z"
CREATED_AT_UTC = "2026-06-30T11:00:00Z"
REPORT_VERSION = "PR168-VS2-v1.0"
PRODUCER_TOOL = "tools/build_pr168_vs2_paper_intent_candidates.py"
VALIDATOR_REF = "tools/validate_pr168_vs2_paper_intent_candidates.py"
EXECUTION_AUTHORITY_REF = (
    "VS2_EXEC_AUTH::PAPER_INTENT_CANDIDATE_COMPILATION_ONLY_NO_SUBMIT_NO_EXECUTION"
)
AUTHORITY_BOUNDARY_REF = (
    "VS2_AUTH_BOUNDARY::NO_PAPER_SUBMIT_NO_LIVE_NO_CONNECTOR_NO_PRIVATE_CASH_"
    "NO_DASHBOARD_TELEGRAM_LLM_RUNTIME"
)
BLOCKER_POLICY_REF = (
    "VS2_BLOCKER_POLICY::DEFER_PACKET_COMPLETION_TO_CANONICAL_AGENT_NO_FORMULA_REPAIR"
)

JSON_OUTPUTS = ("art_reg.json",)
MARKDOWN_OUTPUTS = ("pr_body.md",)

REPORT_OUTPUTS = (
    "run_receipt.report.json",
    "input_consumption.report.json",
    "paper_intent_summary.report.json",
    "packet_registry.report.json",
    "paper_readiness.report.json",
    "paper_loop_handoff.report.json",
    "mem1_handoff.report.json",
    "agent_route.report.json",
    "no_orphan.report.json",
    "authority_boundary.report.json",
    "validation_summary.report.json",
    "missing_req.report.json",
)

JSONL_OUTPUTS = (
    "read_rec.jsonl",
    "in_cons.jsonl",
    "miss_opt.jsonl",
    "self_audit_pre.jsonl",
    "self_audit_post.jsonl",
    "research_rec.jsonl",
    "source_coverage.jsonl",
    "source_intake.jsonl",
    "source_value_cand.jsonl",
    "venue_order_semantic_cand.jsonl",
    "paper_default_cand.jsonl",
    "vs2_qku_paper_elig.jsonl",
    "vs2_formula_paper_elig.jsonl",
    "vs2_candidate_paper_elig.jsonl",
    "vs2_batch_paper_elig.jsonl",
    "qopt1_input_refs.jsonl",
    "rank4_input_refs.jsonl",
    "rp5g_input_refs.jsonl",
    "vs2_packet_registry.jsonl",
    "packet_access_contract.jsonl",
    "packet_evidence_bundle.jsonl",
    "packet_decision_trace.jsonl",
    "packet_idempotency_key.jsonl",
    "qku_formula_route_bundle.jsonl",
    "qstruct_carry.jsonl",
    "packet_completion_queue.jsonl",
    "paper_intent_candidate.jsonl",
    "paper_ticket_fields.jsonl",
    "paper_ticket_field_map.jsonl",
    "paper_order_policy.jsonl",
    "paper_entry_plan.jsonl",
    "paper_exit_plan.jsonl",
    "paper_cancel_replace_plan.jsonl",
    "paper_tif_plan.jsonl",
    "paper_lifecycle_plan.jsonl",
    "paper_packet_explain.jsonl",
    "venue_norm_intent.jsonl",
    "price_unit_norm.jsonl",
    "side_norm.jsonl",
    "tick_min_size_ref.jsonl",
    "venue_semantic_cand.jsonl",
    "paper_readiness.jsonl",
    "paper_gate.jsonl",
    "paper_risk_check.jsonl",
    "paper_tca_check.jsonl",
    "paper_fill_latency_check.jsonl",
    "paper_capacity_check.jsonl",
    "paper_fdr_check.jsonl",
    "paper_scenario_check.jsonl",
    "paper_portfolio_check.jsonl",
    "paper_notrade_check.jsonl",
    "paper_model_risk_check.jsonl",
    "paper_stale_check.jsonl",
    "paper_source_fresh_check.jsonl",
    "no_live_submit.jsonl",
    "no_connector_write.jsonl",
    "no_private_state.jsonl",
    "no_cash_read.jsonl",
    "no_order_submit.jsonl",
    "paper_loop_packet.jsonl",
    "paper_loop_contract.jsonl",
    "paper_loop_handoff.jsonl",
    "paper_loop_manifest.jsonl",
    "paper_loop_input_schema_hint.jsonl",
    "paper_loop_revalidation_req.jsonl",
    "mem1_handoff.jsonl",
    "downstream_handoff.jsonl",
    "orch_handoff.jsonl",
    "live_dry_handoff.jsonl",
    "shadow_handoff.jsonl",
    "intent_dedupe.jsonl",
    "near_clone_intent.jsonl",
    "hotpath_intent.jsonl",
    "coldpath_intent.jsonl",
    "latency_sla_intent.jsonl",
    "intent_priority.jsonl",
    "auth_block.jsonl",
    "agent_alias_map.jsonl",
    "agent_route.jsonl",
    "agent_consume.jsonl",
    "agent_duty_map.jsonl",
    "agent_no_orphan.jsonl",
    "agent_authority_block.jsonl",
    "agent_work_queue.jsonl",
    "artifact_io.jsonl",
    "file_route.jsonl",
    "row_route.jsonl",
    "value_route.jsonl",
    "info_route.jsonl",
    "lineage.jsonl",
    "dag.jsonl",
    "val_lineage.jsonl",
    "downstream.jsonl",
    "completion_route.jsonl",
    "orph_art.jsonl",
    "orph_qku.jsonl",
)

FORBIDDEN_VS2_FILENAMES = frozenset(
    {
        "owner_surface_registry.jsonl",
        "owner_surface_contract.jsonl",
        "owner_surface_proj_manifest.jsonl",
        "owner_packet_route.jsonl",
        "owner_action_registry.jsonl",
        "owner_review_policy.jsonl",
        "owner_safe_action_policy.jsonl",
        "owner_notify_transport.jsonl",
        "owner_view_projection.jsonl",
        "paper_owner_visibility_policy.jsonl",
        "owner_command_queue_seed.jsonl",
        "dash1_handoff.jsonl",
        "tg1_handoff.jsonl",
        "owner_agent_chat_route.jsonl",
        "owner_surface_api_hint.jsonl",
        "owner_surface_no_runtime.jsonl",
        "llm_critic_handoff.jsonl",
        "llm_commander_handoff.jsonl",
        "packet_repair_queue.jsonl",
    }
)

READY_FORBIDDEN_TOKENS = (
    "READY_AFTER_",
    "PAPER_ORDER_INTENT",
    "PAPER_ORDER_SUBMIT_READY",
    "LIVE_CANDIDATE",
    "ORDER_READY",
    "FINAL_CHAMPION",
    "FINAL_TRADE_RANK_FOR_EXECUTION",
    "BUY_SELL_OPEN_CLOSE_READY",
    "QUANTUM_ADVANTAGE_PROVEN",
)

AUTHORITY_FALSE_FIELDS = (
    "final_champion_selected_flag",
    "final_trade_rank_for_execution_flag",
    "paper_order_intent_created_flag",
    "paper_submit_authority_created_flag",
    "paper_execution_created_flag",
    "live_authority_created_flag",
    "live_candidate_created_flag",
    "shadow_execution_authority_created_flag",
    "live_dryrun_execution_authority_created_flag",
    "connector_write_created_flag",
    "private_state_read_created_flag",
    "cash_account_read_created_flag",
    "credential_access_created_flag",
    "wallet_access_created_flag",
    "buy_sell_open_close_logic_created_flag",
    "cancel_replace_amend_reduce_authority_created_flag",
    "realized_pnl_receipt_created_flag",
    "profit_guarantee_flag",
    "owner_dashboard_runtime_created_flag",
    "telegram_bot_runtime_created_flag",
    "telegram_command_execution_runtime_created_flag",
    "owner_approval_authority_created_by_vs2_flag",
    "owner_kill_switch_runtime_created_by_vs2_flag",
    "true_quantum_backend_execution_flag",
    "cloud_quantum_job_created_flag",
    "quantum_credential_used_flag",
    "quantum_advantage_claim_flag",
    "memory_prior_as_current_profit_proof_flag",
    "durable_MEM1_storage_created_flag",
    "MEM1_query_api_created_flag",
    "exit_sell_close_authority_created_flag",
    "external_candidate_as_source_fact_flag",
    "non_official_value_as_live_default_flag",
    "live_canary_promotion_created_by_vs2_flag",
    "shadow_execution_authority_created_by_vs2_flag",
    "qTT_SHA_authority_created_flag",
    "atomicrows_hash_authority_created_flag",
    "accepted_source_fact_flag",
    "connector_semantic_binding_flag",
    "source_fact_acceptance_flag",
    "live_default_flag",
    "proprietary_claim_flag",
    "profit_proof_flag",
    "formula_mutation_flag",
    "qku_mutation_flag",
    "formula_repair_into_profit_flag",
    "qku_logic_mutation_flag",
    "edit_immutable_formula_expression",
    "change_formula_because_packet_failed",
    "force_positive_PnL",
    "bypass_no_trade",
    "turn_deferred_into_ready_by_label",
    "create_paper_submit_authority",
    "create_live_buy_sell_open_close_authority",
    "formula_computation_created_by_vs2_flag",
    "trade_variable_optimization_created_by_vs2_flag",
    "rank4_recomputed_by_vs2_flag",
    "qopt1_recomputed_by_vs2_flag",
    "paper_loop_execution_created_by_vs2_flag",
    "buy_sell_open_close_authority_created_by_vs2_flag",
    "llm_runtime_created_by_vs2_flag",
    "llm_live_call_in_ci_flag",
    "llm_order_authority_flag",
    "llm_source_truth_authority_flag",
    "llm_risk_gate_override_flag",
)

AUTHORITY_TRUE_FIELDS = (
    "paper_intent_candidate_only_flag",
    "advisory_only_flag",
    "future_execution_router_required_before_real_orders_flag",
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
    "docs/master_plan/generated/pr168_rp5g/art_reg.json",
    "docs/master_plan/generated/pr168_rp5g/run_receipt.report.json",
    "docs/master_plan/generated/pr168_rp5g/trade_candidate.jsonl",
    "docs/master_plan/generated/pr168_rp5g/sim_run.jsonl",
    "docs/master_plan/generated/pr168_rp5g/exec_pnl.jsonl",
    "docs/master_plan/generated/pr168_rp5g/tca_decomp.jsonl",
    "docs/master_plan/generated/pr168_rp5g/fill_latency_cap.jsonl",
    "docs/master_plan/generated/pr168_rp5g/capacity_crowding.jsonl",
    "docs/master_plan/generated/pr168_rp5g/notrade_cmp.jsonl",
    "docs/master_plan/generated/pr168_rp5g/overfit_fdr.jsonl",
    "docs/master_plan/generated/pr168_rp5g/scenario_ladder.jsonl",
    "docs/master_plan/generated/pr168_rp5g/port_marg_util.jsonl",
    "docs/master_plan/generated/pr168_rp5g/calibration_result.jsonl",
    "docs/master_plan/generated/pr168_rp5g/qstruct_problem.jsonl",
    "docs/master_plan/generated/pr168_rp5g/q_interp.jsonl",
    "docs/master_plan/generated/pr168_rp5g/q_classic_fb.jsonl",
    "docs/master_plan/generated/pr168_rank4/art_reg.json",
    "docs/master_plan/generated/pr168_rank4/run_receipt.report.json",
    "docs/master_plan/generated/pr168_rank4/rank_score.jsonl",
    "docs/master_plan/generated/pr168_rank4/notrade_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/tca_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/fill_lat_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/capacity_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/fdr_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/scenario_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/calib_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/vs2_handoff.jsonl",
    "docs/master_plan/generated/pr168_rank4/qopt_interpret_back_rank_map.jsonl",
    "docs/master_plan/generated/pr168_qopt1/art_reg.json",
    "docs/master_plan/generated/pr168_qopt1/run_receipt.report.json",
    "docs/master_plan/generated/pr168_qopt1/batch_universe.jsonl",
    "docs/master_plan/generated/pr168_qopt1/batch_select.jsonl",
    "docs/master_plan/generated/pr168_qopt1/qinterp.jsonl",
    "docs/master_plan/generated/pr168_qopt1/qproblem.jsonl",
    "docs/master_plan/generated/pr168_qopt1/qubo.jsonl",
    "docs/master_plan/generated/pr168_qopt1/bqm.jsonl",
    "docs/master_plan/generated/pr168_qopt1/cqm.jsonl",
    "docs/master_plan/generated/pr168_qopt1/quad_prog.jsonl",
    "docs/master_plan/generated/pr168_qopt1/ising_map.jsonl",
    "docs/master_plan/generated/pr168_qopt1/qclassic_fb.jsonl",
    "docs/master_plan/generated/pr168_qopt1/vs2_handoff.jsonl",
    "docs/master_plan/generated/pr168_qopt1/notrade_reopt.jsonl",
    "docs/master_plan/generated/pr168_qopt1/retest_queue.jsonl",
    "docs/master_plan/generated/pr168_qopt1/agent_work_queue.jsonl",
    "docs/master_plan/generated/pr168_qopt1/auth_block.jsonl",
    "docs/master_plan/generated/pr168_qopt1/value_route.jsonl",
    "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
)

OPTIONAL_INPUT_REFS = (
    "docs/master_plan/generated/PR165_D2_MasterPlanSectionCrosswalk.report.json",
    "docs/master_plan/generated/PR165_D2_CommandActionMatrix.report.json",
    "docs/master_plan/generated/PR165_D2_RouteTriageMatrix.report.json",
    "docs/master_plan/generated/pr168_rank4/rank_llm_non_authority.jsonl",
    "docs/master_plan/generated/pr168_qopt1/var_tune_frontier.jsonl",
    "docs/master_plan/generated/pr168_qopt1/stack_chall_frontier.jsonl",
    "docs/master_plan/generated/pr168_qopt1/venue_side_rotate.jsonl",
    "docs/master_plan/generated/pr168_qopt1/adapter_source_refresh.jsonl",
    "docs/master_plan/generated/pr168_qopt1/next_target_rotate.jsonl",
)


def dec(value: Any, default: str = "0") -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value is None or value == "":
        return Decimal(default)
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


def score(value: Any, default: str = "0") -> str:
    return str(dec(value, default).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


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


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    rows_tuple = tuple(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(stable_json(row, compact=True) for row in rows_tuple), encoding="utf-8")
    manifest = {
        "schema_version": REPORT_VERSION,
        "row_id": f"MANIFEST::{path.name}",
        "producer_pr": PR_ID,
        "source_pr": PR_ID,
        "producer_tool": PRODUCER_TOOL,
        "created_at_utc": CREATED_AT_UTC,
        "artifact_filename": path.name,
        "row_count": len(rows_tuple),
        "manual_edit_allowed_flag": False,
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "execution_authority_ref": EXECUTION_AUTHORITY_REF,
        "validation_refs": [VALIDATOR_REF],
        "orphan_flag": False,
    }
    for field in AUTHORITY_TRUE_FIELDS:
        manifest[field] = True
    for field in AUTHORITY_FALSE_FIELDS:
        manifest[field] = False
    write_json(path.with_name(manifest_name(path.name)), manifest)


def common_row(
    row: dict[str, Any],
    *,
    row_id: str,
    owner_agent: str,
    consumer_agents: Iterable[str],
    upstream_refs: Iterable[str],
    downstream_refs: Iterable[str],
    source_artifact_refs: Iterable[str] | None = None,
    validation_refs: Iterable[str] = (VALIDATOR_REF,),
    provenance_tier: str = "VS2_PAPER_INTENT_PACKET_COMPILATION",
    role_target_name: str | None = None,
    canonical_agent_name: str | None = None,
) -> dict[str, Any]:
    out = dict(row)
    upstream = stable_unique(upstream_refs)
    downstream = stable_unique(downstream_refs)
    consumers = stable_unique(consumer_agents)
    out.setdefault("schema_version", REPORT_VERSION)
    out.setdefault("row_id", row_id)
    out.setdefault("run_id", RUN_ID)
    out.setdefault("producer_pr", PR_ID)
    out.setdefault("source_pr", PR_ID)
    out.setdefault("producer_tool", PRODUCER_TOOL)
    out.setdefault("created_at_utc", CREATED_AT_UTC)
    out.setdefault("source_artifact_refs", stable_unique(source_artifact_refs or upstream))
    out.setdefault("upstream_refs", upstream)
    out.setdefault("downstream_refs", downstream)
    out.setdefault("owner_agent", owner_agent)
    out.setdefault("producer_agent", owner_agent)
    out.setdefault("consumer_agents", consumers)
    out.setdefault("consumer_agent_refs", consumers)
    out.setdefault("validation_refs", stable_unique(validation_refs))
    out.setdefault("authority_boundary_ref", AUTHORITY_BOUNDARY_REF)
    out.setdefault("execution_authority_ref", EXECUTION_AUTHORITY_REF)
    out.setdefault("blocker_policy_ref", BLOCKER_POLICY_REF)
    out.setdefault("connector_refs_or_future_connector_status", "FUTURE_CONNECTOR_STATUS_ONLY_NO_BIND_WRITE_READ")
    out.setdefault("provenance_tier", provenance_tier)
    out.setdefault("orphan_flag", False)
    out.setdefault("role_target_name", role_target_name or owner_agent)
    out.setdefault("canonical_agent_name", canonical_agent_name or owner_agent)
    out.setdefault("agent_alias_map_ref", generated_ref("agent_alias_map.jsonl"))
    out.setdefault("agent_resolution_status", "TRIAGE_REQUIRED")
    out.setdefault("invent_new_agent_authority_flag", False)
    for field in AUTHORITY_TRUE_FIELDS:
        out.setdefault(field, True)
    for field in AUTHORITY_FALSE_FIELDS:
        out.setdefault(field, False)
    return out


def common_report(
    payload: dict[str, Any],
    *,
    report_name: str,
    owner_agent: str,
    upstream_refs: Iterable[str],
    downstream_refs: Iterable[str],
) -> dict[str, Any]:
    return common_row(
        {"report_name": report_name, "manual_edit_allowed_flag": False, **payload},
        row_id=f"VS2_REPORT::{report_name}",
        owner_agent=owner_agent,
        consumer_agents=["CommanderAgent", "GovernanceAgent", "PaperExecutionAgent"],
        upstream_refs=upstream_refs,
        downstream_refs=downstream_refs,
        provenance_tier="VS2_COMPACT_REPORT",
    )
