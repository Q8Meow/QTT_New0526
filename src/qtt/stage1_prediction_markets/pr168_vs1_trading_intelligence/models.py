"""Shared constants and deterministic JSON helpers for PR168-VS1."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, getcontext
import json
from pathlib import Path
from typing import Any, Iterable

getcontext().prec = 28

REPO_ROOT = Path(__file__).resolve().parents[4]
GENERATED_DIR = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_vs1"
GENERATED_REF_PREFIX = "docs/master_plan/generated/pr168_vs1"

PR_ID = "PR168-VS1"
BRANCH_NAME = "pr168-vs1-trading-intelligence-vertical-slice"
BASELINE_SHA = "2b7c93df4805734ca503cc1c845a61e539b6dee7"
RUN_ID = "PR168_VS1_DETERMINISTIC_RUN_20260626T000000Z"
CREATED_AT_UTC = "2026-06-26T00:00:00Z"
REPORT_VERSION = "PR168-VS1-v1.0"
STAGE_PROFILE_ID = "STAGE1_PREDICTION_MARKETS"
MARKET_FAMILY = "PREDICTION_MARKETS"
EXECUTION_AUTHORITY_REF = "VS1_EXECUTION_AUTHORITY::PR168_VS1_PREVIEW_ONLY"
BLOCKER_POLICY_REF = "VS1_BLOCKER_POLICY::PR168_VS1"

PLATFORM_IDS = ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR")
FIXTURE_CASES = (
    "positive_edge_fixture",
    "negative_edge_fixture",
    "thin_book_fixture",
    "crowded_capacity_fixture",
    "portfolio_conflict_fixture",
)
SELECTOR_AGENT_IDS = (
    "research_agent",
    "parameter_selector_agent",
    "connector_venue_readiness_future_consumer",
    "risk_manager_agent",
    "quantum_optimizer_agent",
)

ROLE_TO_ONTOLOGY = {
    "signal_probability": "signal_probability",
    "calibration": "calibration",
    "market_implied_probability": "market_implied_probability",
    "tca_cost": "tca_cost",
    "fill_queue_liquidity": "fill_queue_liquidity",
    "latency_staleness": "latency_staleness",
    "capacity_crowding": "capacity_crowding",
    "portfolio_risk": "portfolio_risk",
    "regime_scenario": "regime_scenario",
    "exit_timing": "exit_timing",
    "quantum_objective_constraint": "quantum_objective_constraint",
    "classical_fallback": "classical_fallback",
}
ROLE_ORDER = tuple(ROLE_TO_ONTOLOGY)

REQUIRED_BLOCKER_CODES = (
    "NO_TRADE_WINS",
    "NO_ELIGIBLE_POSITIVE_NET_CASH_PNL_CANDIDATE_FOUND",
    "REJECT_LCB_NOT_POSITIVE",
    "REJECT_FILL_TOO_LOW",
    "REJECT_TCA_WIPES_EDGE",
    "REJECT_CAPACITY_GATE",
    "REJECT_PORTFOLIO_GATE",
    "REJECT_SCENARIO_LADDER",
    "REJECT_AGENT_ROUTE",
    "REJECT_NO_ORPHAN_PROOF",
    "REJECT_UNKNOWN_NEEDS_REVIEW",
    "REJECT_METADATA_ONLY_BINDING",
    "REJECT_IMPOSSIBLE_PRICE",
    "REJECT_IMPOSSIBLE_FILL",
    "REJECT_GATE_RELAXATION_ATTEMPT",
    "REJECT_HINDSIGHT_BACKSOLVE",
    "REJECT_EXTERNAL_SOURCE_FACT_AUTHORITY",
)

JSONL_OUTPUTS = (
    "vs1_reading_receipts.jsonl",
    "vs1_crosswalk_discovery_receipts.jsonl",
    "vs1_blocker_policy_registry.jsonl",
    "vs1_policy_parameter_registry.jsonl",
    "vs1_agent_dag_receipts.jsonl",
    "vs1_agent_artifact_routing_ledger.jsonl",
    "vs1_upstream_downstream_artifact_dag.jsonl",
    "vs1_no_orphan_artifact_ledger.jsonl",
    "trade_target_fixtures.jsonl",
    "market_condition_snapshots.jsonl",
    "stage_agent_universe_query_receipts.jsonl",
    "agent_duty_evidence_discovery_receipts.jsonl",
    "context_formula_selection_receipts.jsonl",
    "selected_computable_qku_formula_bindings.jsonl",
    "temporary_stack_candidate_receipts.jsonl",
    "trade_plan_variable_search_receipts.jsonl",
    "order_variable_candidate_receipts.jsonl",
    "tca_breakdown_receipts.jsonl",
    "expected_cash_pnl_receipts.jsonl",
    "overfit_fdr_control_receipts.jsonl",
    "capacity_crowding_receipts.jsonl",
    "portfolio_diversification_receipts.jsonl",
    "scenario_ladder_receipts.jsonl",
    "objective_term_ledger.jsonl",
    "constraint_penalty_policy_receipts.jsonl",
    "trade_plan_quantum_encoding_receipts.jsonl",
    "no_trade_comparator_receipts.jsonl",
    "trade_plan_candidates.jsonl",
    "execution_adjusted_ranking_receipts.jsonl",
    "champion_challenger_selection_receipts.jsonl",
    "quantum_structural_readiness_receipts.jsonl",
    "paper_intent_candidate_previews.jsonl",
    "external_research_candidate_receipts.jsonl",
    "no_pnl_forcing_proof.jsonl",
    "no_orphan_qku_formula_proof.jsonl",
)

REPORT_OUTPUTS = (
    "vs1_execution_authority_receipt.report.json",
    "vs1_run_receipt.report.json",
    "vs1_to_rp5d_rp5e_rp5f_rp5g_rank4_qopt_mem1_agent_orch_handoff.report.json",
)


@dataclass(frozen=True)
class RunConfig:
    fixture: str = "all"
    top_k: int = 10
    max_identities: int = 50
    max_stacks_per_fixture: int = 20
    dump_temp: bool = False


def rel_ref(path: Path | str) -> str:
    p = Path(path)
    if p.is_absolute():
        p = p.relative_to(REPO_ROOT)
    return p.as_posix()


def generated_ref(filename: str) -> str:
    return f"{GENERATED_REF_PREFIX}/{filename}"


def dec(value: str | int | float | Decimal) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def ratio(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def stable_json(payload: Any, *, compact: bool = False) -> str:
    separators = (",", ":") if compact else None
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=None if compact else 2, separators=separators) + "\n"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(payload), encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]], *, schema_version_name: str) -> None:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(stable_json(row, compact=True) for row in materialized), encoding="utf-8")
    manifest = {
        "blocker_policy_ref": BLOCKER_POLICY_REF,
        "created_at_utc": CREATED_AT_UTC,
        "downstream_consumer_refs": ["VS1Validator", "VS1RunReceipt", "FutureHandoffConsumers"],
        "execution_authority_ref": EXECUTION_AUTHORITY_REF,
        "external_research_used_flag": False if path.name == "external_research_candidate_receipts.jsonl" else None,
        "generated_surface_authority_class": "VS1_GENERATED_PREVIEW_ARTIFACT_NOT_SOURCE_TRUTH",
        "manifest_id": f"{path.stem.upper()}_MANIFEST",
        "physical_filename": rel_ref(path),
        "pr_id": PR_ID,
        "report_version": REPORT_VERSION,
        "row_count": len(materialized),
        "row_count_within_bound_flag": True,
        "schema_version_name": schema_version_name,
        "shard_file_path": rel_ref(path),
    }
    write_json(path.with_suffix(".manifest.json"), {k: v for k, v in manifest.items() if v is not None})


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def with_common(
    row: dict[str, Any],
    *,
    producer_agent: str,
    consumer_agent_refs: Iterable[str],
    upstream_artifact_refs: Iterable[str],
    downstream_artifact_refs: Iterable[str],
    blocker_codes: Iterable[str] = (),
) -> dict[str, Any]:
    out = dict(row)
    out.setdefault("run_id", RUN_ID)
    out.setdefault("execution_authority_ref", EXECUTION_AUTHORITY_REF)
    out.setdefault("blocker_policy_ref", BLOCKER_POLICY_REF)
    out.setdefault("producer_agent", producer_agent)
    out.setdefault("consumer_agent_refs", sorted(dict.fromkeys(consumer_agent_refs)))
    out.setdefault("upstream_artifact_refs", sorted(dict.fromkeys(upstream_artifact_refs)))
    out.setdefault("downstream_artifact_refs", sorted(dict.fromkeys(downstream_artifact_refs)))
    if blocker_codes:
        out.setdefault("blocker_codes", sorted(dict.fromkeys(blocker_codes)))
    return out


def qku_ref(identity: dict[str, Any]) -> str:
    return str(identity.get("qku_id") or f"{identity['identity_row_id']}::QKU_REF_NOT_PRESENT_IN_RP5C_ROW")


def formula_ref(identity: dict[str, Any]) -> str:
    return str(identity.get("formula_id") or f"{identity['identity_row_id']}::FORMULA_REF_NOT_PRESENT_IN_RP5C_ROW")
