"""Shared contracts and deterministic JSON helpers for PR168-RP5D-R1."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, getcontext
import json
from pathlib import Path
from typing import Any, Iterable

getcontext().prec = 28

REPO_ROOT = Path(__file__).resolve().parents[4]
GENERATED_DIR = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_rp5d_r1"
GENERATED_REF_PREFIX = "docs/master_plan/generated/pr168_rp5d_r1"

PR_ID = "PR168-RP5D-R1"
BRANCH_NAME = "pr168-rp5d-r1-exec-now-unlock"
BASELINE_SHA_VCS_METADATA_ONLY = "1db3421c2d8516aee58744277a9ee0d319d6e72f"
RUN_ID = "PR168_RP5D_R1_DETERMINISTIC_RUN_20260628T000000Z"
CREATED_AT_UTC = "2026-06-28T00:00:00Z"
REPORT_VERSION = "PR168-RP5D-R1-v1.0"
STAGE_PROFILE_ID = "STAGE1_PREDICTION_MARKETS"
MARKET_FAMILY = "PREDICTION_MARKETS"
EXECUTION_AUTHORITY_REF = "RP5D_R1_EXEC_AUTH::REPLAY_PAPER_CONTRACT_PROOF_ONLY"
BLOCKER_POLICY_REF = "RP5D_R1_BLOCKER_POLICY::PRECISE_EXECUTION_CONTRACT_ONLY"
VALIDATOR_REF = "tools/validate_pr168_rp5d_r1_exec_now_unlock.py"
WINDOWS_REPO_ROOT_ASSUMPTION = r"C:\Users\Owner\Projects\QTT_New0526\\"

JSON_OUTPUTS = ("art_reg.json",)

REPORT_OUTPUTS = (
    "missing_req.report.json",
    "exec_auth.report.json",
    "exec_now_summary.report.json",
    "to_rp5f.report.json",
    "to_rp5g.report.json",
    "to_rank4.report.json",
    "to_qopt1.report.json",
    "to_vs2.report.json",
    "to_mem1.report.json",
    "to_orch1.report.json",
    "to_paper.report.json",
    "to_live_dry.report.json",
    "to_shadow.report.json",
    "future.report.json",
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
    "proof_tier.jsonl",
    "tier_overlay.jsonl",
    "count_integrity.jsonl",
    "contract_matrix.jsonl",
    "promote_audit.jsonl",
    "calc_smoke.jsonl",
    "edge_profit_map.jsonl",
    "unlock_util.jsonl",
    "marg_unlock.jsonl",
    "promo_diverse.jsonl",
    "rp5e_unlock_in.jsonl",
    "unlock_select.jsonl",
    "unlock_tiers.jsonl",
    "gap_family.jsonl",
    "gap_dedupe.jsonl",
    "unlock_plan.jsonl",
    "contract_patch.jsonl",
    "input_bind.jsonl",
    "unit_adapt.jsonl",
    "pnl_map.jsonl",
    "fixture_bind.jsonl",
    "tca_comp.jsonl",
    "fee_ready.jsonl",
    "spread_ready.jsonl",
    "slip_ready.jsonl",
    "lat_ready.jsonl",
    "fill_ready.jsonl",
    "capacity_ready.jsonl",
    "cash_settle.jsonl",
    "exec_now_proof.jsonl",
    "promote.jsonl",
    "nonpromote.jsonl",
    "tier_delta.jsonl",
    "source_req.jsonl",
    "exec_adj_delta.jsonl",
    "tca_delta.jsonl",
    "fdr_carry.jsonl",
    "port_cap_carry.jsonl",
    "champ_carry.jsonl",
    "regime_carry.jsonl",
    "marg_carry.jsonl",
    "q_struct_carry.jsonl",
    "q_solver_carry.jsonl",
    "q_interp_carry.jsonl",
    "classic_exec.jsonl",
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
    "no_hardcode.jsonl",
    "research_rec.jsonl",
    "downstream.jsonl",
)

REQUIRED_INPUT_REFS = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/master_plan/generated/PR168_RP5C_FinalSummary.report.json",
    "docs/master_plan/generated/pr168_vs1/vs1_run_receipt.report.json",
    "docs/master_plan/generated/pr168_rp5d/rp5d_run_receipt.report.json",
    "docs/master_plan/generated/pr168_rp5e/run_receipt.report.json",
    "docs/master_plan/generated/rp5c/immutable_qku_formula_library.jsonl",
    "docs/master_plan/generated/rp5c/immutable_qku_library.jsonl",
    "docs/master_plan/generated/rp5c/immutable_formula_library.jsonl",
    "docs/master_plan/generated/rp5c/formula_ontology.jsonl",
    "docs/master_plan/generated/rp5c/qku_market_applicability_matrix.jsonl",
    "docs/master_plan/generated/rp5c/agent_qku_access_policy_registry.jsonl",
    "docs/master_plan/generated/rp5c/stage_agent_qku_universe_resolver.jsonl",
    "tools/pr168_rp5c_library_reader.py",
    "docs/master_plan/generated/pr168_vs1/selected_computable_qku_formula_bindings.jsonl",
    "docs/master_plan/generated/pr168_vs1/temporary_stack_candidate_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/order_variable_candidate_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/tca_breakdown_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/expected_cash_pnl_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/quantum_structural_readiness_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/paper_intent_candidate_previews.jsonl",
    "docs/master_plan/generated/pr168_vs1/no_orphan_qku_formula_proof.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_artifact_name_registry.json",
    "docs/master_plan/generated/pr168_rp5d/rp5d_comp_materialization.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_contract_bundles.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_exec_tiers.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_computable_universe.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_agent_exec_resolver.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_stage_agent_exec_view.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_artifact_dag.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_no_orphan_qku_formula.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_future_pr_handoff.report.json",
    "docs/master_plan/generated/pr168_rp5d/rp5d_quantum_compat.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_optimizer_readiness.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_alpha_readiness.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_tca_readiness.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_capacity_readiness.jsonl",
    "docs/master_plan/generated/pr168_rp5e/art_reg.json",
    "docs/master_plan/generated/pr168_rp5e/read_rec.jsonl",
    "docs/master_plan/generated/pr168_rp5e/unlock_pri.jsonl",
    "docs/master_plan/generated/pr168_rp5e/gap_rank.jsonl",
    "docs/master_plan/generated/pr168_rp5e/triage52.jsonl",
    "docs/master_plan/generated/pr168_rp5e/queue_dedupe.jsonl",
    "docs/master_plan/generated/pr168_rp5e/to_unlock.report.json",
    "docs/master_plan/generated/pr168_rp5e/agent_route.jsonl",
    "docs/master_plan/generated/pr168_rp5e/agent_consume.jsonl",
    "docs/master_plan/generated/pr168_rp5e/artifact_io.jsonl",
    "docs/master_plan/generated/pr168_rp5e/file_route.jsonl",
    "docs/master_plan/generated/pr168_rp5e/lineage.jsonl",
    "docs/master_plan/generated/pr168_rp5e/dag.jsonl",
    "docs/master_plan/generated/pr168_rp5e/val_lineage.jsonl",
    "docs/master_plan/generated/pr168_rp5e/orph_art.jsonl",
    "docs/master_plan/generated/pr168_rp5e/orph_qku.jsonl",
    "docs/master_plan/generated/pr168_rp5e/no_meta.jsonl",
    "docs/master_plan/generated/pr168_rp5e/no_mut.jsonl",
    "docs/master_plan/generated/pr168_rp5e/no_hardcode.jsonl",
    "docs/master_plan/generated/pr168_rp5e/q_obj.jsonl",
    "docs/master_plan/generated/pr168_rp5e/q_coeffs.jsonl",
    "docs/master_plan/generated/pr168_rp5e/q_solver.jsonl",
    "docs/master_plan/generated/pr168_rp5e/q_interp.jsonl",
    "docs/master_plan/generated/pr168_rp5e/classic.jsonl",
    "docs/master_plan/generated/pr168_rp5e/tca_ready.jsonl",
    "docs/master_plan/generated/pr168_rp5e/capacity.jsonl",
    "docs/master_plan/generated/pr168_rp5e/exec_prev.jsonl",
    "docs/master_plan/generated/pr168_rp5e/fdr_ctrl.jsonl",
    "docs/master_plan/generated/pr168_rp5e/port_div.jsonl",
    "docs/master_plan/generated/pr168_rp5e/marg_util.jsonl",
    "docs/master_plan/generated/pr168_rp5e/downstream.jsonl",
    "docs/master_plan/generated/pr168_rp5e/to_live_dry.report.json",
    "docs/master_plan/generated/pr168_rp5e/to_shadow.report.json",
    "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
)

OPTIONAL_INPUT_REFS = (
    "docs/master_plan/generated/PR168_RP_RouteTriage.report.json",
    "docs/master_plan/generated/PR168_RP_FullMasterPlanSectionCrosswalk.report.json",
    "docs/master_plan/generated/PR168_RP_MarketSpecificSectionIndexes.report.json",
    "docs/master_plan/generated/PR168_RP_CommandActionMatrix.report.json",
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

BLOCKER_CODES = (
    "MISSING_RP5E_UNLOCK_HANDOFF",
    "MISSING_RP5D_EXEC_TIER_REF",
    "MISSING_COMPUTABILITY_REF",
    "MISSING_CONTRACT_BUNDLE_REF",
    "MISSING_INPUT_BINDING",
    "MISSING_UNIT_ADAPTER",
    "MISSING_FORMULA_TO_PNL_MAP",
    "MISSING_MARKET_DATA_FIXTURE_BINDING",
    "MISSING_FEE_MODEL",
    "MISSING_SPREAD_MODEL",
    "MISSING_SLIPPAGE_MODEL",
    "MISSING_LATENCY_MODEL",
    "MISSING_FILL_MODEL",
    "MISSING_CAPACITY_CROWDING_MODEL",
    "MISSING_CASHFLOW_SEMANTICS",
    "MISSING_SETTLEMENT_SEMANTICS",
    "MISSING_AGENT_DUTY_REF",
    "MISSING_DOWNSTREAM_CONSUMER",
    "MISSING_VALIDATION_REF",
    "MISSING_EXECUTION_AUTHORITY_REF",
    "MISSING_BLOCKER_POLICY_REF",
    "MISSING_POLICY_DEFAULT_PROVENANCE",
    "SOURCE_REQUIRED_NOT_ACCEPTED",
    "VENUE_SEMANTICS_REQUIRED",
    "FIXTURE_NOT_AUTHORITY",
    "PROMOTION_PROOF_INCOMPLETE",
    "CONTRACT_MATRIX_INCOMPLETE",
    "CALCULATION_SMOKE_FAILED",
    "PROOF_TIER_MISSING",
    "TIER_OVERLAY_MISSING",
    "COUNT_INTEGRITY_FAILED",
    "METADATA_ONLY_ROW",
    "FORMULA_MUTATION_ATTEMPT",
    "QKU_MUTATION_ATTEMPT",
    "GLOBAL_BAN_ATTEMPT",
    "PAPER_SUBMIT_AUTHORITY_ATTEMPT",
    "LIVE_DRYRUN_EXECUTION_ATTEMPT",
    "SHADOW_AUTHORITY_ATTEMPT",
    "LIMITED_LIVE_CANARY_ATTEMPT",
    "LIVE_AUTHORITY_ATTEMPT",
    "CONNECTOR_WRITE_ATTEMPT",
    "PRIVATE_STATE_FETCH_ATTEMPT",
    "CASH_ACCOUNT_READ_ATTEMPT",
    "PROFIT_PROOF_ATTEMPT",
    "FINAL_RANK_ATTEMPT",
    "CHAMPION_SELECTION_ATTEMPT",
    "ORDER_VARIABLE_OPTIMIZATION_ATTEMPT",
    "QOPT_EXECUTION_ATTEMPT",
    "QUANTUM_BACKEND_ATTEMPT",
    "PROPRIETARY_DEFAULT_CLAIM_ATTEMPT",
    "CONFIDENTIAL_INPUT_ATTEMPT",
    "QTT_SHA_AUTHORITY_ATTEMPT",
    "ATOMICROWS_SHA_REF_ATTEMPT",
    "ORPHAN_ARTIFACT_ATTEMPT",
    "HARDCODED_THRESHOLD_ATTEMPT",
)

UPSTREAM_BLOCKER_TO_R1 = {
    "RP5D_MATERIALIZE_INPUT_CONTRACT": "MISSING_INPUT_BINDING",
    "RP5D_MATERIALIZE_UNIT_CONTRACT": "MISSING_UNIT_ADAPTER",
    "RP5D_MATERIALIZE_FORMULA_TO_PNL_MAP": "MISSING_FORMULA_TO_PNL_MAP",
    "RP5D_MATERIALIZE_MARKET_DATA_BINDING": "MISSING_MARKET_DATA_FIXTURE_BINDING",
    "RP5D_MATERIALIZE_TCA_BINDING": "MISSING_FEE_MODEL",
    "RP5D_MATERIALIZE_FILL_LIQUIDITY_BINDING": "MISSING_FILL_MODEL",
    "RP5D_MATERIALIZE_LATENCY_BINDING": "MISSING_LATENCY_MODEL",
    "RP5D_MATERIALIZE_CAPACITY_BINDING": "MISSING_CAPACITY_CROWDING_MODEL",
    "RP5D_MATERIALIZE_PORTFOLIO_BINDING": "MISSING_DOWNSTREAM_CONSUMER",
    "RP5D_MATERIALIZE_SCENARIO_BINDING": "MISSING_DOWNSTREAM_CONSUMER",
    "RP5D_MATERIALIZE_OVERFIT_FDR_BINDING": "MISSING_DOWNSTREAM_CONSUMER",
    "RP5D_MATERIALIZE_NO_TRADE_BINDING": "MISSING_DOWNSTREAM_CONSUMER",
    "RP5D_MATERIALIZE_RANKING_READINESS": "MISSING_DOWNSTREAM_CONSUMER",
    "RP5D_MATERIALIZE_CHAMPION_CHALLENGER_READINESS": "MISSING_DOWNSTREAM_CONSUMER",
    "RP5D_MATERIALIZE_REGIME_MEMORY_READINESS": "MISSING_DOWNSTREAM_CONSUMER",
    "RP5D_MATERIALIZE_ALPHA_EDGE_READINESS": "MISSING_DOWNSTREAM_CONSUMER",
    "RP5D_MATERIALIZE_LATENCY_HOT_PATH_READINESS": "MISSING_LATENCY_MODEL",
    "RP5D_MATERIALIZE_QUANTUM_MAPPING": "MISSING_DOWNSTREAM_CONSUMER",
    "RP5D_MATERIALIZE_CLASSICAL_FALLBACK": "MISSING_DOWNSTREAM_CONSUMER",
    "RP5D_AGENT_ROUTE_UNRESOLVED_ACTION_REQUIRED": "MISSING_AGENT_DUTY_REF",
}

FALSE_FLAG_FIELDS = (
    "metadata_is_proof_flag",
    "accepted_source_fact_flag",
    "paper_authority_flag",
    "shadow_authority_flag",
    "live_authority_flag",
    "order_authority_flag",
    "profit_proof_flag",
    "qopt_execution_flag",
    "quantum_backend_execution_flag",
    "quantum_advantage_claim_flag",
    "proprietary_claim_flag",
    "qtt_sha_authority_flag",
    "atomicrows_sha_ref_flag",
    "paper_submit_authority_flag",
    "connector_write_flag",
    "private_state_fetch_flag",
    "cash_account_read_flag",
    "formula_mutation_flag",
    "qku_mutation_flag",
    "global_ban_flag",
)

FORBIDDEN_STATE_VALUES = (
    "REAL_POSITIVE",
    "REAL_NEGATIVE",
    "CHAMPION",
    "LIVE_CANDIDATE",
    "ORDER_READY",
    "FINAL_TRADE_RANK",
    "PROFIT_PROVEN",
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
)

FORBIDDEN_TEXT_PARTS = (
    ("Re", "pairPlanV1"),
    ("Re", "pairPatchV1"),
    ("re", "pair ROI"),
    ("re", "pair utility"),
    ("re", "pair queue"),
)


@dataclass(frozen=True)
class RunConfig:
    offline: bool = True
    fixture: str = "sample"
    target_min: int = 5
    target_max: int = 15
    max_unlock_candidates_attempted: int = 20


@dataclass(frozen=True)
class CommonEnvelopeV1:
    schema_version: str
    row_id: str
    run_id: str
    created_at_utc: str
    source_pr: str
    upstream_refs: tuple[str, ...]
    downstream_refs: tuple[str, ...]
    owner_agent: str
    consumer_agents: tuple[str, ...]
    validation_refs: tuple[str, ...]
    execution_authority_ref: str
    blocker_policy_ref: str
    provenance_tier: str


@dataclass(frozen=True)
class RP5EUnlockInputV1(CommonEnvelopeV1):
    unlock_candidate_id: str


@dataclass(frozen=True)
class UnlockCandidateSelectionV1(CommonEnvelopeV1):
    unlock_candidate_id: str


@dataclass(frozen=True)
class AdapterGapFamilyV1(CommonEnvelopeV1):
    gap_family_id: str


@dataclass(frozen=True)
class ExecutableUnlockPlanV1(CommonEnvelopeV1):
    unlock_plan_id: str


@dataclass(frozen=True)
class ExecutionContractPatchV1(CommonEnvelopeV1):
    contract_patch_id: str


@dataclass(frozen=True)
class InputBindingReadyV1(CommonEnvelopeV1):
    unlock_candidate_id: str


UnitAdapterReadyV1 = InputBindingReadyV1
FormulaToPnLMapReadyV1 = InputBindingReadyV1
MarketDataFixtureBindingReadyV1 = InputBindingReadyV1
TCAComponentReadyV1 = InputBindingReadyV1
FillLatencyCapacityReadyV1 = InputBindingReadyV1
CashflowSettlementReadyV1 = InputBindingReadyV1
ReplayPaperExecutableNowProofV1 = InputBindingReadyV1
ExecutableProofProvenanceV1 = InputBindingReadyV1
TierOverlayDeltaV1 = InputBindingReadyV1
CountIntegrityAuditV1 = InputBindingReadyV1
ContractCompletenessMatrixV1 = InputBindingReadyV1
CalculationSmokeTestV1 = InputBindingReadyV1
PromotionAuditV1 = InputBindingReadyV1
PromotionReceiptV1 = InputBindingReadyV1
NonPromotionReceiptV1 = InputBindingReadyV1
TierDeltaLedgerV1 = InputBindingReadyV1
CarryForwardReadinessV1 = InputBindingReadyV1
RuntimeModeBoundaryV1 = InputBindingReadyV1
EdgeProfitContributionMapV1 = InputBindingReadyV1
ExecutableUnlockUtilityLedgerV1 = InputBindingReadyV1
MarginalUnlockUtilityV1 = InputBindingReadyV1
PromotionDiversityLedgerV1 = InputBindingReadyV1
ArtifactIOMatrixV1 = InputBindingReadyV1
FileRouteRegistryV1 = InputBindingReadyV1


def dec(value: str | int | float | Decimal) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def score(value: str | int | float | Decimal) -> str:
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


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(payload), encoding="utf-8")


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
    provenance_tier: str = "RP5D_R1_EXECUTION_CONTRACT_OVERLAY_NOT_PROFIT_PROOF",
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
    for flag in FALSE_FLAG_FIELDS:
        out.setdefault(flag, False)
    out.setdefault("accepted_source_fact_flag", False)
    out.setdefault("producer_agent", owner_agent)
    out.setdefault("consumer_agent_refs", consumers)
    out.setdefault("upstream_artifact_refs", upstream)
    out.setdefault("downstream_artifact_refs", downstream)
    out.setdefault("orphan_flag", False)
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
            "generated_surface_authority_class": "RP5D_R1_GENERATED_EXECUTION_CONTRACT_OVERLAY_NOT_SOURCE_TRUTH",
        },
        row_id=f"{path.stem.upper()}_MANIFEST",
        owner_agent="GovernanceAgent",
        consumer_agents=["RP5D_R1Validator", "ArtifactNameAgent", "PathSafetyAgent"],
        upstream_refs=[generated_ref(path.name)],
        downstream_refs=[generated_ref("run_receipt.report.json")],
    )
    write_json(path.with_name(manifest_name(path.name)), manifest)


def schema_name(filename: str) -> str:
    stem = filename.removesuffix(".jsonl").removesuffix(".json").replace(".report", "")
    return "".join(part.capitalize() for part in stem.split("_") if part) + "V1"
