"""Shared constants and JSON helpers for PR168-RP5E."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, getcontext
import json
from pathlib import Path
from typing import Any, Iterable

getcontext().prec = 28

REPO_ROOT = Path(__file__).resolve().parents[4]
GENERATED_DIR = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_rp5e"
GENERATED_REF_PREFIX = "docs/master_plan/generated/pr168_rp5e"
TMP_RUN_ROOT = REPO_ROOT / ".tmp" / "qtt_stack_runs"

PR_ID = "PR168-RP5E"
BRANCH_NAME = "pr168-rp5e-stack-gen"
BASELINE_SHA_VCS_METADATA_ONLY = "9cf157f4481671732d97797dbb216dd4ce7314ab"
RUN_ID = "PR168_RP5E_DETERMINISTIC_RUN_20260627T000000Z"
CREATED_AT_UTC = "2026-06-27T00:00:00Z"
REPORT_VERSION = "PR168-RP5E-v1.0"
STAGE_PROFILE_ID = "STAGE1_PREDICTION_MARKETS"
MARKET_FAMILY = "PREDICTION_MARKETS"
EXECUTION_AUTHORITY_REF = "RP5E_EXEC_AUTH::STACK_PREVIEW_HANDOFF_ONLY_NO_ORDER_AUTHORITY"
BLOCKER_POLICY_REF = "RP5E_BLOCKER_POLICY::PRECISE_NO_GLOBAL_BAN"
WINDOWS_REPO_ROOT_ASSUMPTION = r"C:\Users\Owner\Projects\QTT_New0526\\"
VALIDATOR_REF = "tools/validate_pr168_rp5e_stack_gen.py"

PLATFORM_IDS = ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR")
GENERATION_MODES = ("HOT_PATH_PREVIEW", "WARM_REPLAY_PAPER_SEARCH", "COLD_RESEARCH_EXPANSION")

JSON_OUTPUTS = ("art_reg.json",)

REPORT_OUTPUTS = (
    "exec_auth.report.json",
    "to_rp5f.report.json",
    "to_rp5g.report.json",
    "to_rank4.report.json",
    "to_qopt1.report.json",
    "to_vs2.report.json",
    "to_mem1.report.json",
    "to_orch1.report.json",
    "to_paper.report.json",
    "to_shadow.report.json",
    "to_live_dry.report.json",
    "to_unlock.report.json",
    "re_handoff.report.json",
    "future.report.json",
    "run_receipt.report.json",
)

JSONL_OUTPUTS = (
    "read_rec.jsonl",
    "in_cons.jsonl",
    "miss_opt.jsonl",
    "xwalk_cons.jsonl",
    "mode_boundary.jsonl",
    "blockers.jsonl",
    "params.jsonl",
    "policy_prov.jsonl",
    "default_cand.jsonl",
    "calib_queue.jsonl",
    "ctx_univ.jsonl",
    "ctx_rules.jsonl",
    "ctx_pools.jsonl",
    "roles.jsonl",
    "role_cov.jsonl",
    "qku_guard.jsonl",
    "templates.jsonl",
    "budget.jsonl",
    "search_trace.jsonl",
    "cand_fam.jsonl",
    "eph_contracts.jsonl",
    "use_dump.jsonl",
    "tmp_manifest.jsonl",
    "fixtures.jsonl",
    "tmp_previews.jsonl",
    "topk.jsonl",
    "discard.jsonl",
    "dump_rec.jsonl",
    "prescreen.jsonl",
    "features.jsonl",
    "edge_feats.jsonl",
    "alpha_hints.jsonl",
    "notrade_hints.jsonl",
    "exec_prev.jsonl",
    "tca_ready.jsonl",
    "fdr_ctrl.jsonl",
    "port_div.jsonl",
    "capacity.jsonl",
    "champ_prev.jsonl",
    "regime_mem.jsonl",
    "marg_util.jsonl",
    "diverse.jsonl",
    "q_tags.jsonl",
    "q_obj.jsonl",
    "q_coeffs.jsonl",
    "q_solver.jsonl",
    "q_interp.jsonl",
    "classic.jsonl",
    "unlock_pri.jsonl",
    "gap_rank.jsonl",
    "triage52.jsonl",
    "queue_dedupe.jsonl",
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
    "no_hardcode.jsonl",
    "research_rec.jsonl",
    "downstream.jsonl",
)

RP5C_REQUIRED_FILES = (
    "docs/master_plan/generated/rp5c/immutable_qku_formula_library.jsonl",
    "docs/master_plan/generated/rp5c/immutable_qku_library.jsonl",
    "docs/master_plan/generated/rp5c/immutable_formula_library.jsonl",
    "docs/master_plan/generated/rp5c/formula_assignment_library.jsonl",
    "docs/master_plan/generated/rp5c/formula_ontology.jsonl",
    "docs/master_plan/generated/rp5c/qku_market_applicability_matrix.jsonl",
    "docs/master_plan/generated/rp5c/market_stage_activation_profile_registry.jsonl",
    "docs/master_plan/generated/rp5c/agent_qku_access_policy_registry.jsonl",
    "docs/master_plan/generated/rp5c/stage_agent_qku_universe_resolver.jsonl",
    "docs/master_plan/generated/rp5c/stage1_agent_computation_universe_seed.jsonl",
    "docs/master_plan/generated/rp5c/stage_computation_universe_view.jsonl",
    "docs/master_plan/generated/rp5c/agent_computation_universe_view.jsonl",
    "docs/master_plan/generated/rp5c/library_query_receipts.jsonl",
    "docs/master_plan/generated/rp5c/no_orphan_identity_rows.jsonl",
    "docs/master_plan/generated/rp5c/no_orphan_generated_surface_rows.jsonl",
    "docs/master_plan/generated/rp5c/no_global_ban_rows.jsonl",
    "docs/master_plan/generated/PR168_RP5C_FinalSummary.report.json",
    "tools/pr168_rp5c_library_reader.py",
)

VS1_REQUIRED_FILES = (
    "docs/master_plan/generated/pr168_vs1/vs1_run_receipt.report.json",
    "docs/master_plan/generated/pr168_vs1/vs1_reading_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/vs1_execution_authority_receipt.report.json",
    "docs/master_plan/generated/pr168_vs1/selected_computable_qku_formula_bindings.jsonl",
    "docs/master_plan/generated/pr168_vs1/temporary_stack_candidate_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/order_variable_candidate_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/tca_breakdown_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/expected_cash_pnl_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/execution_adjusted_ranking_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/champion_challenger_selection_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/quantum_structural_readiness_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/paper_intent_candidate_previews.jsonl",
    "docs/master_plan/generated/pr168_vs1/no_orphan_qku_formula_proof.jsonl",
    "docs/master_plan/generated/pr168_vs1/vs1_to_rp5d_rp5e_rp5f_rp5g_rank4_qopt_mem1_agent_orch_handoff.report.json",
)

RP5D_REQUIRED_FILES = (
    "docs/master_plan/generated/pr168_rp5d/rp5d_run_receipt.report.json",
    "docs/master_plan/generated/pr168_rp5d/rp5d_artifact_name_registry.json",
    "docs/master_plan/generated/pr168_rp5d/rp5d_comp_materialization.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_contract_bundles.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_exec_tiers.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_computable_universe.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_agent_exec_resolver.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_stage_agent_exec_view.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_agent_routing_ledger.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_artifact_dag.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_no_orphan_qku_formula.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_future_pr_handoff.report.json",
    "docs/master_plan/generated/pr168_rp5d/rp5d_quantum_compat.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_optimizer_readiness.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_alpha_readiness.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_tca_readiness.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_capacity_readiness.jsonl",
)

RP5D_QUEUE_FILES = (
    "rp5d_input_queue.jsonl",
    "rp5d_formula_pnl_queue.jsonl",
    "rp5d_unit_queue.jsonl",
    "rp5d_market_data_queue.jsonl",
    "rp5d_tca_queue.jsonl",
    "rp5d_fill_liquidity_queue.jsonl",
    "rp5d_latency_queue.jsonl",
    "rp5d_capacity_queue.jsonl",
    "rp5d_portfolio_queue.jsonl",
    "rp5d_scenario_queue.jsonl",
    "rp5d_overfit_fdr_queue.jsonl",
    "rp5d_no_trade_queue.jsonl",
    "rp5d_rank_queue.jsonl",
    "rp5d_champion_queue.jsonl",
    "rp5d_regime_memory_queue.jsonl",
    "rp5d_alpha_queue.jsonl",
    "rp5d_hot_path_queue.jsonl",
    "rp5d_agent_route_queue.jsonl",
    "rp5d_quantum_map_queue.jsonl",
    "rp5d_classical_fb_queue.jsonl",
)

PR165_D2_REQUIRED_FILES = (
    "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
)

CROSSWALK_OPTIONAL_FILES = (
    "docs/master_plan/generated/PR168_RP_RouteTriage.report.json",
    "docs/master_plan/generated/PR168_RP_FullMasterPlanSectionCrosswalk.report.json",
    "docs/master_plan/generated/PR168_RP_MarketSpecificSectionIndexes.report.json",
    "docs/master_plan/generated/PR168_RP_CommandActionMatrix.report.json",
    "docs/master_plan/generated/PR135RouteTriage.report.json",
    "docs/master_plan/generated/PR135MasterPlanSectionCrosswalk.report.json",
    "docs/master_plan/generated/PR135MarketSpecificSectionIndex.report.json",
    "docs/master_plan/generated/PR135CommandActionMatrix.report.json",
)

MASTER_PLAN_REQUIRED_FILES = ("docs/master_plan/QTT_MasterPlan_Current.md",)

ROLE_NAMES = (
    "signal_probability",
    "calibration",
    "market_implied_probability",
    "TCA_cost",
    "fill_queue_liquidity",
    "latency_staleness",
    "capacity_crowding",
    "portfolio_risk",
    "regime_scenario",
    "exit_timing",
    "quantum_objective_constraint",
    "classical_fallback",
)

BLOCKER_CODES = (
    "MISSING_REQUIRED_INPUT_CONTRACT",
    "MISSING_UNIT_CONTRACT",
    "MISSING_FORMULA_TO_PNL_REF",
    "MISSING_TCA_COMPONENT",
    "MISSING_AGENT_DUTY_REF",
    "MISSING_DOWNSTREAM_CONSUMER",
    "MISSING_VALIDATION_REF",
    "MISSING_EXECUTION_AUTHORITY_REF",
    "MISSING_BLOCKER_POLICY_REF",
    "MISSING_POLICY_DEFAULT_PROVENANCE",
    "HARDCODED_THRESHOLD_ATTEMPT",
    "QUANTUM_STRUCTURE_INCOMPLETE",
    "QUANTUM_SOLVER_COMPAT_INCOMPLETE",
    "CLASSICAL_FALLBACK_MISSING",
    "TEMP_GRID_NOT_DUMPED",
    "FULL_STACK_UNIVERSE_ATTEMPTED",
    "METADATA_ONLY_ROW",
    "FORMULA_MUTATION_ATTEMPT",
    "QKU_MUTATION_ATTEMPT",
    "GLOBAL_BAN_ATTEMPT",
    "PAPER_LIVE_AUTHORITY_ATTEMPT",
    "SHADOW_AUTHORITY_ATTEMPT",
    "QOPT_EXECUTION_ATTEMPT",
    "QUANTUM_BACKEND_ATTEMPT",
    "PROPRIETARY_DEFAULT_CLAIM_ATTEMPT",
    "CONFIDENTIAL_INPUT_ATTEMPT",
    "QTT_SHA_AUTHORITY_ATTEMPT",
    "ATOMICROWS_SHA_REF_ATTEMPT",
    "ORPHAN_ARTIFACT_ATTEMPT",
)

FORBIDDEN_STATE_VALUES = (
    "REAL_POSITIVE",
    "REAL_NEGATIVE",
    "LIVE_CANDIDATE",
    "PAPER_EXECUTABLE_NOW",
    "SHADOW_EXECUTABLE_NOW",
    "LIVE_EXECUTABLE_NOW",
    "ORDER_READY",
    "FINAL_TRADE_RANK",
    "PROFIT_PROVEN",
    "QUANTUM_ADVANTAGE_PROVEN",
    "ORDER_SUBMIT_READY",
    "BUY_SELL_OPEN_CLOSE_READY",
)


@dataclass(frozen=True)
class RunConfig:
    offline: bool = True
    fixture: str = "sample"
    max_stacks: int = 1000
    dump_temp: bool = False


def dec(value: str | int | float | Decimal) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def score(value: Decimal | int | float | str) -> str:
    return str(dec(value).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def ratio(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "0.000000"
    return score(Decimal(numerator) / Decimal(denominator))


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
    base = tuple(dict.fromkeys((*JSON_OUTPUTS, *REPORT_OUTPUTS, *JSONL_OUTPUTS)))
    if not include_manifests:
        return base
    manifests = tuple(manifest_name(name) for name in JSONL_OUTPUTS)
    return tuple(dict.fromkeys((*base, *manifests)))


def stable_json(payload: Any, *, compact: bool = False) -> str:
    separators = (",", ":") if compact else None
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=None if compact else 2, separators=separators) + "\n"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(payload), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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
    provenance_tier: str = "RP5E_GENERATED_PREVIEW_NOT_PROOF",
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
    out.setdefault("provenance_tier", provenance_tier)
    out.setdefault("metadata_is_proof_flag", False)
    out.setdefault("accepted_source_fact_flag", False)
    out.setdefault("paper_authority_flag", False)
    out.setdefault("shadow_authority_flag", False)
    out.setdefault("live_authority_flag", False)
    out.setdefault("qopt_execution_flag", False)
    out.setdefault("quantum_backend_execution_flag", False)
    out.setdefault("quantum_advantage_claim_flag", False)
    out.setdefault("proprietary_claim_flag", False)
    out.setdefault("qtt_sha_authority_flag", False)
    out.setdefault("atomicrows_sha_ref_flag", False)
    out.setdefault("producer_agent", owner_agent)
    out.setdefault("consumer_agent_refs", consumers)
    out.setdefault("upstream_artifact_refs", upstream)
    out.setdefault("downstream_artifact_refs", downstream)
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
            "generated_surface_authority_class": "RP5E_GENERATED_STACK_PREVIEW_ARTIFACT_NOT_SOURCE_TRUTH",
        },
        row_id=f"{path.stem.upper()}_MANIFEST",
        owner_agent="GovernanceAgent",
        consumer_agents=["RP5EValidator", "ArtifactNameAgent", "PathSafetyAgent"],
        upstream_refs=[generated_ref(path.name)],
        downstream_refs=[generated_ref("run_receipt.report.json")],
    )
    write_json(path.with_name(manifest_name(path.name)), manifest)


def schema_name(filename: str) -> str:
    stem = filename.removesuffix(".jsonl").removesuffix(".json").replace(".report", "")
    return "".join(part.capitalize() for part in stem.split("_") if part) + "V1"
