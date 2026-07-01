"""Shared deterministic contracts for PR168-MEM1 artifacts."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, getcontext
import json
from pathlib import Path
from typing import Any, Iterable

getcontext().prec = 28

REPO_ROOT = Path(__file__).resolve().parents[4]
GENERATED_DIR = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_mem1"
GENERATED_REF_PREFIX = "docs/master_plan/generated/pr168_mem1"

PR_ID = "PR168-MEM1"
BRANCH_NAME = "pr168-mem1-condition-scoped-outcome-memory"
RUN_ID = "PR168_MEM1_DETERMINISTIC_RUN_20260701T120000Z"
CREATED_AT_UTC = "2026-07-01T12:00:00Z"
REPORT_VERSION = "PR168-MEM1-v1.0"
PRODUCER_TOOL = "tools/build_pr168_mem1_condition_scoped_memory.py"
VALIDATOR_REF = "tools/validate_pr168_mem1_condition_scoped_memory.py"
AUTHORITY_BOUNDARY_REF = (
    "MEM1_AUTH_BOUNDARY::MEMORY_PRIOR_ONLY_NO_CURRENT_PROFIT_NO_PAPER_NO_LIVE_"
    "NO_CONNECTOR_NO_PRIVATE_CASH_NO_DASHBOARD_TELEGRAM_LLM_RUNTIME_NO_QPU"
)
EXECUTION_AUTHORITY_REF = "MEM1_EXEC_AUTH::DETERMINISTIC_MEMORY_QUERY_ONLY_NO_ORDER_AUTHORITY"
REVALIDATION_POLICY_REF = (
    "MEM1_REVALIDATION::EVERY_RECIPE_REQUIRES_CURRENT_SNAPSHOT_REPLAY_PAPER_BEFORE_PROMOTION"
)

JSON_OUTPUTS = ("art_reg.json",)
MARKDOWN_OUTPUTS = ("pr_body.md",)

REPORT_OUTPUTS = (
    "run_receipt.report.json",
    "input_consumption.report.json",
    "memory_summary.report.json",
    "recipe_registry.report.json",
    "failure_memory.report.json",
    "similarity_engine.report.json",
    "prior_score.report.json",
    "drift_cooldown_retest.report.json",
    "qmemory.report.json",
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
    "memory_default_cand.jsonl",
    "clean_room_default_cand.jsonl",
    "vs2_input_refs.jsonl",
    "rank4_input_refs.jsonl",
    "qopt1_input_refs.jsonl",
    "rp5g_input_refs.jsonl",
    "mem1_registry_index.jsonl",
    "memory_policy_registry.jsonl",
    "mem1_consumer_contract.jsonl",
    "mem1_route_registry.jsonl",
    "activation_state.jsonl",
    "memory_query_contract.jsonl",
    "memory_query_receipt.jsonl",
    "context_signature.jsonl",
    "context_similarity_key.jsonl",
    "context_bucket_map.jsonl",
    "context_similarity_score.jsonl",
    "winning_recipe.jsonl",
    "winning_recipe_registry.jsonl",
    "recipe_context.jsonl",
    "recipe_trade_vars.jsonl",
    "recipe_evidence.jsonl",
    "recipe_provenance.jsonl",
    "recipe_state.jsonl",
    "failure_memory.jsonl",
    "failure_memory_registry.jsonl",
    "negative_context_cooldown.jsonl",
    "failure_attribution.jsonl",
    "failure_similarity_key.jsonl",
    "failure_retest_route.jsonl",
    "notrade_context_memory.jsonl",
    "notrade_reoptimization_route.jsonl",
    "notrade_variable_tune_route.jsonl",
    "notrade_stack_challenger_route.jsonl",
    "notrade_venue_side_rotation_route.jsonl",
    "notrade_source_refresh_route.jsonl",
    "notrade_next_target_route.jsonl",
    "notrade_retest_route.jsonl",
    "notrade_not_terminal.jsonl",
    "recipe_retrieval_result.jsonl",
    "failure_retrieval_result.jsonl",
    "recipe_prior_score.jsonl",
    "recipe_score_component.jsonl",
    "recipe_confidence.jsonl",
    "recipe_shrinkage.jsonl",
    "recipe_fdr_adjust.jsonl",
    "recipe_oos_eval_req.jsonl",
    "recipe_ope_eval_req.jsonl",
    "recipe_bandit_policy.jsonl",
    "memory_prior_batch.jsonl",
    "challenger_explore_batch.jsonl",
    "llm_memory_view_contract.jsonl",
    "llm_memory_critic_payload_contract.jsonl",
    "llm_agent_task_contract.jsonl",
    "drift_monitor.jsonl",
    "drift_signal.jsonl",
    "cooldown_policy.jsonl",
    "cooldown_state.jsonl",
    "retest_queue.jsonl",
    "retest_priority.jsonl",
    "stale_memory.jsonl",
    "memory_ttl.jsonl",
    "outcome_attribution.jsonl",
    "winner_attribution.jsonl",
    "edge_decomp_memory.jsonl",
    "execution_quality_memory.jsonl",
    "portfolio_effect_memory.jsonl",
    "qmemory_registry.jsonl",
    "qmemory_structure_ref.jsonl",
    "qmemory_context_score.jsonl",
    "qmemory_reuse_candidate.jsonl",
    "qmemory_classic_compare.jsonl",
    "qmemory_no_advantage.jsonl",
    "hotpath_memory_index.jsonl",
    "coldpath_memory_route.jsonl",
    "memory_cache_manifest.jsonl",
    "memory_latency_sla.jsonl",
    "memory_query_budget.jsonl",
    "mem1_handoff_forward.jsonl",
    "paper_loop_write_contract.jsonl",
    "orch_handoff.jsonl",
    "rank4_revalidation_handoff.jsonl",
    "qopt1_reoptimization_handoff.jsonl",
    "live_dry_handoff.jsonl",
    "shadow_handoff.jsonl",
    "downstream_handoff.jsonl",
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

FORBIDDEN_MEM1_FILENAMES = frozenset(
    {
        "paper_order_intent.jsonl",
        "paper_submit.jsonl",
        "paper_fill_receipt.jsonl",
        "paper_exit_receipt.jsonl",
        "paper_pnl_receipt.jsonl",
        "live_order_intent.jsonl",
        "live_submit.jsonl",
        "live_fill_receipt.jsonl",
        "cash_reconciliation_receipt.jsonl",
        "owner_surface_registry.jsonl",
        "owner_action_registry.jsonl",
        "dashboard_runtime.jsonl",
        "telegram_runtime.jsonl",
        "llm_runtime.jsonl",
        "qpu_job.jsonl",
        "quantum_advantage_proof.jsonl",
        "formula_global_ban.jsonl",
        "qku_global_ban.jsonl",
        "formula_profit_forcing_queue.jsonl",
        "qku_profit_forcing_queue.jsonl",
    }
)

FORBIDDEN_FILENAME_TOKENS = (
    "future",
    "later",
    "pending",
    "placeholder",
    "staging",
    "experimental",
)

AUTHORITY_TRUE_FIELDS = (
    "memory_prior_only_flag",
    "replay_paper_revalidation_required",
    "current_snapshot_revalidation_required",
    "execution_router_required_before_real_orders_flag",
)

AUTHORITY_FALSE_FIELDS = (
    "current_profit_proof_flag",
    "current_live_readiness_proof_flag",
    "paper_submit_authority_created_flag",
    "paper_execution_created_flag",
    "paper_fill_receipt_created_flag",
    "paper_exit_receipt_created_flag",
    "paper_pnl_receipt_created_flag",
    "paper_profit_proof_flag",
    "live_authority_created_flag",
    "live_authority_flag",
    "live_candidate_created_flag",
    "order_authority_flag",
    "order_authority_created_flag",
    "connector_write_created_flag",
    "private_state_read_created_flag",
    "cash_account_read_created_flag",
    "true_quantum_backend_execution_flag",
    "cloud_quantum_job_created_flag",
    "quantum_credential_used_flag",
    "quantum_advantage_claim_flag",
    "profit_guarantee_flag",
    "llm_runtime_created_flag",
    "llm_live_call_in_CI_flag",
    "llm_order_authority_flag",
    "llm_source_truth_authority_flag",
    "llm_risk_gate_override_flag",
    "dashboard_runtime_created_flag",
    "telegram_runtime_created_flag",
    "owner_approval_authority_created_flag",
    "exit_sell_close_authority_created_flag",
    "realized_pnl_receipt_created_flag",
    "formula_mutation_flag",
    "qku_mutation_flag",
    "formula_mutation_required_flag",
    "formula_global_ban_flag",
    "qku_global_ban_flag",
    "global_formula_ban_flag",
    "global_qku_ban_flag",
    "global_ban_flag",
    "memory_prior_as_current_profit_proof_flag",
    "qTT_SHA_authority_created_flag",
    "atomicrows_hash_authority_created_flag",
    "accepted_source_fact_flag",
    "connector_semantic_binding_flag",
    "source_truth_authority_flag",
    "source_fact_acceptance_flag",
    "live_default_flag",
    "proprietary_claim_flag",
    "profit_proof_flag",
    "paper_or_live_authority_created_flag",
    "terminal_dead_end_flag",
    "backend_execution_created_flag",
    "backend_specific_embedding_created_flag",
    "true_quantum_backend_ready_flag",
)

REQUIRED_INPUT_REFS = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/master_plan/generated/PR168_RP5C_FinalSummary.report.json",
    "docs/master_plan/generated/rp5c/immutable_qku_formula_library.jsonl",
    "docs/master_plan/generated/rp5c/immutable_qku_library.jsonl",
    "docs/master_plan/generated/rp5c/immutable_formula_library.jsonl",
    "docs/master_plan/generated/rp5c/library_query_receipts.jsonl",
    "docs/master_plan/generated/rp5c/qku_market_applicability_matrix.jsonl",
    "docs/master_plan/generated/rp5c/agent_qku_access_policy_registry.jsonl",
    "docs/master_plan/generated/rp5c/market_stage_activation_profile_registry.jsonl",
    "docs/master_plan/generated/rp5c/no_orphan_identity_rows.jsonl",
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
    "docs/master_plan/generated/pr168_rank4/rank_context_signature.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_similarity_key.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_memory_recipe_handoff.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_winner_attribution.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_negative_memory_hint.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_retest_priority.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_recipe_prior_score.jsonl",
    "docs/master_plan/generated/pr168_rank4/notrade_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/tca_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/fill_lat_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/capacity_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/fdr_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/scenario_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/calib_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/mem1_handoff.jsonl",
    "docs/master_plan/generated/pr168_qopt1/art_reg.json",
    "docs/master_plan/generated/pr168_qopt1/run_receipt.report.json",
    "docs/master_plan/generated/pr168_qopt1/batch_universe.jsonl",
    "docs/master_plan/generated/pr168_qopt1/batch_select.jsonl",
    "docs/master_plan/generated/pr168_qopt1/memory_prior_batch.jsonl",
    "docs/master_plan/generated/pr168_qopt1/qmemory_use.jsonl",
    "docs/master_plan/generated/pr168_qopt1/qstruct_universe.jsonl",
    "docs/master_plan/generated/pr168_qopt1/qinterp.jsonl",
    "docs/master_plan/generated/pr168_qopt1/qproblem.jsonl",
    "docs/master_plan/generated/pr168_qopt1/qubo.jsonl",
    "docs/master_plan/generated/pr168_qopt1/bqm.jsonl",
    "docs/master_plan/generated/pr168_qopt1/cqm.jsonl",
    "docs/master_plan/generated/pr168_qopt1/quad_prog.jsonl",
    "docs/master_plan/generated/pr168_qopt1/ising_map.jsonl",
    "docs/master_plan/generated/pr168_qopt1/qclassic_fb.jsonl",
    "docs/master_plan/generated/pr168_qopt1/notrade_reopt.jsonl",
    "docs/master_plan/generated/pr168_qopt1/retest_queue.jsonl",
    "docs/master_plan/generated/pr168_qopt1/agent_work_queue.jsonl",
    "docs/master_plan/generated/pr168_qopt1/auth_block.jsonl",
    "docs/master_plan/generated/pr168_qopt1/value_route.jsonl",
    "docs/master_plan/generated/pr168_vs2/art_reg.json",
    "docs/master_plan/generated/pr168_vs2/run_receipt.report.json",
    "docs/master_plan/generated/pr168_vs2/vs2_packet_registry.jsonl",
    "docs/master_plan/generated/pr168_vs2/packet_evidence_bundle.jsonl",
    "docs/master_plan/generated/pr168_vs2/packet_decision_trace.jsonl",
    "docs/master_plan/generated/pr168_vs2/packet_access_contract.jsonl",
    "docs/master_plan/generated/pr168_vs2/packet_idempotency_key.jsonl",
    "docs/master_plan/generated/pr168_vs2/qku_formula_route_bundle.jsonl",
    "docs/master_plan/generated/pr168_vs2/qstruct_carry.jsonl",
    "docs/master_plan/generated/pr168_vs2/paper_loop_packet.jsonl",
    "docs/master_plan/generated/pr168_vs2/paper_loop_contract.jsonl",
    "docs/master_plan/generated/pr168_vs2/paper_loop_revalidation_req.jsonl",
    "docs/master_plan/generated/pr168_vs2/mem1_handoff.jsonl",
    "docs/master_plan/generated/pr168_vs2/downstream_handoff.jsonl",
    "docs/master_plan/generated/pr168_vs2/no_orphan.report.json",
    "docs/master_plan/generated/pr168_vs2/authority_boundary.report.json",
    "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
)

OPTIONAL_INPUT_REFS = (
    "docs/master_plan/generated/PR165_D2_MasterPlanSectionCrosswalk.report.json",
    "docs/master_plan/generated/PR165_D2_CommandActionMatrix.report.json",
    "docs/master_plan/generated/PR165_D2_RouteTriageMatrix.report.json",
    "docs/master_plan/generated/PR165_D2_MarketSpecificSelectionIndex.report.json",
    "docs/master_plan/generated/pr168_rank4/rank_llm_non_authority.jsonl",
    "docs/master_plan/generated/pr168_qopt1/var_tune_frontier.jsonl",
    "docs/master_plan/generated/pr168_qopt1/stack_chall_frontier.jsonl",
    "docs/master_plan/generated/pr168_qopt1/venue_side_rotate.jsonl",
    "docs/master_plan/generated/pr168_qopt1/adapter_source_refresh.jsonl",
    "docs/master_plan/generated/pr168_qopt1/next_target_rotate.jsonl",
    "docs/master_plan/generated/pr168_vs2/orch_handoff.jsonl",
    "docs/master_plan/generated/pr168_vs2/live_dry_handoff.jsonl",
    "docs/master_plan/generated/pr168_vs2/shadow_handoff.jsonl",
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
    manifest = common_row(
        {
            "manifest_id": f"MEM1_MANIFEST::{path.name}",
            "artifact_filename": path.name,
            "row_count": len(rows_tuple),
            "manual_edit_allowed_flag": False,
        },
        row_id=f"MEM1_MANIFEST::{path.name}",
        owner_role_target="GovernanceAgent",
        consumer_role_targets=["CommanderAgent", "MemoryAgent"],
        upstream_refs=[generated_ref(path.name)],
        downstream_refs=[generated_ref("art_reg.json")],
        provenance_tier="MEM1_JSONL_MANIFEST",
    )
    write_json(path.with_name(manifest_name(path.name)), manifest)


def common_row(
    row: dict[str, Any],
    *,
    row_id: str,
    owner_role_target: str,
    consumer_role_targets: Iterable[str],
    upstream_refs: Iterable[str],
    downstream_refs: Iterable[str],
    source_artifact_refs: Iterable[str] | None = None,
    validation_refs: Iterable[str] = (VALIDATOR_REF,),
    provenance_tier: str = "MEM1_CONDITION_SCOPED_OUTCOME_MEMORY",
    canonical_agent_name: str | None = None,
) -> dict[str, Any]:
    out = dict(row)
    upstream = stable_unique(upstream_refs)
    downstream = stable_unique(downstream_refs)
    consumers = stable_unique(consumer_role_targets)
    canonical = canonical_agent_name or owner_role_target
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
    out.setdefault("owner_role_target", owner_role_target)
    out.setdefault("canonical_agent_name_if_resolved", canonical)
    out.setdefault("producer_agent_or_role_target", owner_role_target)
    out.setdefault("consumer_role_targets", consumers)
    out.setdefault("consumer_agents_if_resolved", consumers)
    out.setdefault("owner_agent", owner_role_target)
    out.setdefault("producer_agent", owner_role_target)
    out.setdefault("consumer_agents", consumers)
    out.setdefault("validation_refs", stable_unique(validation_refs))
    out.setdefault("authority_boundary_ref", AUTHORITY_BOUNDARY_REF)
    out.setdefault("execution_authority_ref", EXECUTION_AUTHORITY_REF)
    out.setdefault("completion_or_retest_policy_ref", REVALIDATION_POLICY_REF)
    out.setdefault("provenance_tier", provenance_tier)
    out.setdefault("orphan_flag", False)
    out.setdefault("agent_alias_map_ref", generated_ref("agent_alias_map.jsonl"))
    out.setdefault("connector_ref_status", "NO_CONNECTOR_BINDING_OR_WRITE")
    for field in AUTHORITY_TRUE_FIELDS:
        out.setdefault(field, True)
    for field in AUTHORITY_FALSE_FIELDS:
        out.setdefault(field, False)
    return out


def common_report(
    payload: dict[str, Any],
    *,
    report_name: str,
    owner_role_target: str,
    upstream_refs: Iterable[str],
    downstream_refs: Iterable[str],
) -> dict[str, Any]:
    return common_row(
        {"report_name": report_name, "manual_edit_allowed_flag": False, **payload},
        row_id=f"MEM1_REPORT::{report_name}",
        owner_role_target=owner_role_target,
        consumer_role_targets=["CommanderAgent", "GovernanceAgent", "MemoryAgent"],
        upstream_refs=upstream_refs,
        downstream_refs=downstream_refs,
        provenance_tier="MEM1_COMPACT_REPORT",
    )
