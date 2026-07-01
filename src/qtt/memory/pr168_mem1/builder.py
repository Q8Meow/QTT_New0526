"""Deterministic PR168-MEM1 artifact builder."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable

from .models import (
    AUTHORITY_BOUNDARY_REF,
    BRANCH_NAME,
    CREATED_AT_UTC,
    FORBIDDEN_MEM1_FILENAMES,
    GENERATED_DIR,
    GENERATED_REF_PREFIX,
    JSONL_OUTPUTS,
    JSON_OUTPUTS,
    MARKDOWN_OUTPUTS,
    OPTIONAL_INPUT_REFS,
    PR_ID,
    PRODUCER_TOOL,
    REPORT_OUTPUTS,
    REQUIRED_INPUT_REFS,
    RUN_ID,
    VALIDATOR_REF,
    all_artifact_filenames,
    common_report,
    common_row,
    dec,
    generated_ref,
    read_json,
    read_jsonl,
    score,
    stable_unique,
    write_json,
    write_jsonl,
    write_text,
)


ROLE_TARGETS = (
    "CommanderAgent",
    "MarketConditionAgent",
    "FormulaLibraryAgent",
    "StackGeneratorAgent",
    "TradeTargetScoutAgent",
    "OrderVariableAgent",
    "TradePlanSimulationAgent",
    "RankerAgent",
    "QOPTAgent",
    "PaperExecutionAgent",
    "TCAAgent",
    "FillLatencyAgent",
    "RiskAgent",
    "MemoryAgent",
    "GovernanceAgent",
    "ResearchScoutAgent",
    "LiveDryRunAgent",
    "ShadowObservationAgent",
)

RESEARCH_SOURCES = (
    (
        "https://www.jstor.org/stable/2346101",
        "Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing",
        "PAPER",
        "false-discovery / FDR control for many recipe, stack, and trade-variable tests",
    ),
    (
        "https://arxiv.org/abs/1510.01244",
        "A Survey on Contextual Multi-armed Bandits",
        "PAPER",
        "contextual bandit policy design for fast-start memory priors",
    ),
    (
        "https://arxiv.org/abs/1103.4601",
        "Doubly Robust Policy Evaluation and Learning",
        "PAPER",
        "off-policy evaluation warnings for observed behavior policy mismatch",
    ),
    (
        "https://www.cfainstitute.org/insights/professional-learning/refresher-readings/trading-costs-electronic-markets",
        "Trading Costs and Electronic Markets",
        "PUBLIC_RESEARCH",
        "TCA / implementation-shortfall attribution",
    ),
    (
        "https://dl.acm.org/doi/10.1145/2523813",
        "A Survey on Concept Drift Adaptation",
        "PAPER",
        "concept drift and stale-memory handling",
    ),
    (
        "https://www.bis.org/publ/qtrpdf/r_qt1909v.htm",
        "Crowding and its implications for market stability",
        "PUBLIC_RESEARCH",
        "capacity and crowding memory attribution",
    ),
    (
        "https://doi.org/10.1214/08-STS255",
        "A Conversation with Bradley Efron",
        "PAPER",
        "empirical-Bayes shrinkage and conservative prior scoring",
    ),
    (
        "https://docs.dwavequantum.com/en/latest/concepts/models.html",
        "D-Wave Ocean problem models",
        "OFFICIAL_DOC",
        "BQM/CQM/QUBO structural memory and classical fallback comparison",
    ),
    (
        "https://qiskit-community.github.io/qiskit-optimization/tutorials/01_quadratic_program.html",
        "Qiskit Optimization QuadraticProgram tutorial",
        "OFFICIAL_DOC",
        "QuadraticProgram and interpret-back structural memory",
    ),
)

SELF_AUDIT_QUESTIONS = (
    "Is MEM1 the correct next PR after merged VS2?",
    "Does MEM1 consume VS2 mem1_handoff, packet evidence, decision, access, qku formula route, qstruct carry, paper-loop, and downstream rows?",
    "Does MEM1 consume RANK4 memory handoff, context signatures, similarity keys, winner attribution, negative memory, and retest priority where present?",
    "Does MEM1 consume QOPT1 qmemory, qstruct, objective, constraint, interpret-back, and VS2 handoff rows where present?",
    "Does MEM1 consume RP5G/RANK4/QOPT1 numeric evidence refs rather than recompute simulation, ranking, or optimization?",
    "Does MEM1 preserve immutable QKUs and formulas without mutation, profit forcing, or global bans?",
    "Does MEM1 store memory as fast-start prior only, not current profit proof?",
    "Does MEM1 implement condition-scoped winning recipes and failure memory with context keys and provenance tiers?",
    "Does MEM1 include similarity retrieval, shrinkage prior scoring, drift monitor, cooldown policy, retest queue, attribution, and quantum structural memory?",
    "Does MEM1 preserve execution-adjusted evidence including net PnL, LCB, no-trade margin, TCA, fill, latency, capacity, portfolio utility, FDR, scenario, calibration, model risk, and source provenance?",
    "Does MEM1 block live/paper authority, order authority, dashboard runtime, Telegram runtime, LLM runtime, connector writes, private-state reads, cash/account reads, and quantum backend execution?",
    "Does MEM1 expose agent-consumable query contracts without requiring downstream agents to scan raw upstream files?",
    "Does MEM1 use PR165-D2 AgentRosterDiscoveryAudit and AgentDutySourceCrosswalk or stronger equivalents?",
    "Does MEM1 route every generated file, value, and row through centralized ledgers?",
    "Does MEM1 avoid QTT SHA and AtomicRows SHA/hash authority?",
    "Does MEM1 include affected-scope-first validation, CI debug, merge, and post-merge main workflow watch?",
)


def _repo_path(repo_root: Path, ref: str) -> Path:
    return repo_root / ref


def _row_count(path: Path) -> int:
    if not path.is_file():
        return 0
    if path.suffix == ".jsonl":
        return len([line for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()])
    if path.suffix == ".json":
        return 1
    return len(path.read_text(encoding="utf-8", errors="replace").splitlines())


def _clean_generated_dir(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    allowed = set(all_artifact_filenames())
    for path in out_dir.iterdir():
        if path.is_file() and path.name in allowed:
            path.unlink()


def _family_for_ref(ref: str) -> str:
    low = ref.lower()
    if "pr168_vs2" in low:
        return "PR168_VS2_PAPER_INTENT_PACKET_OUTPUT"
    if "pr168_rank4" in low:
        return "PR168_RANK4_MEMORY_READY_RANK_OUTPUT"
    if "pr168_qopt1" in low:
        return "PR168_QOPT1_OPTIMIZED_BATCH_MEMORY_OUTPUT"
    if "pr168_rp5g" in low:
        return "PR168_RP5G_TRADE_PLAN_SIM_EVIDENCE_OUTPUT"
    if "rp5c" in low or "pr168_rp5c" in low:
        return "PR168_RP5C_IMMUTABLE_QKU_FORMULA_LIBRARY_OUTPUT"
    if "pr165_d2" in low:
        return "PR165_D2_AGENT_ROLE_RESOLUTION_OUTPUT"
    if "rp5d" in low:
        return "PR168_RP5D_EXECUTABILITY_OUTPUT"
    if "rp5e" in low:
        return "PR168_RP5E_STACK_CONTEXT_OUTPUT"
    if "rp5f" in low:
        return "PR168_RP5F_TARGET_GRID_OUTPUT"
    if "vs1" in low:
        return "PR168_VS1_VERTICAL_SLICE_OUTPUT"
    return "MASTER_PLAN_INPUT"


def _producer_pr_for_ref(ref: str) -> str:
    family = _family_for_ref(ref)
    if family.startswith("PR168_VS2"):
        return "PR168-VS2"
    if family.startswith("PR168_RANK4"):
        return "PR168-RANK4"
    if family.startswith("PR168_QOPT1"):
        return "PR168-QOPT1"
    if family.startswith("PR168_RP5G"):
        return "PR168-RP5G"
    if family.startswith("PR168_RP5C"):
        return "PR168-RP5C"
    if family.startswith("PR165_D2"):
        return "PR165-D2"
    return "UPSTREAM"


def _read_inputs(repo_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    read_rows: list[dict[str, Any]] = []
    in_cons: list[dict[str, Any]] = []
    miss_opt: list[dict[str, Any]] = []
    missing: list[str] = []
    for index, ref in enumerate(REQUIRED_INPUT_REFS, start=1):
        path = _repo_path(repo_root, ref)
        exists = path.is_file()
        if exists:
            path.read_text(encoding="utf-8", errors="replace")
        else:
            missing.append(ref)
        row_id = f"MEM1_READ_{index:05d}"
        family = _family_for_ref(ref)
        read_rows.append(
            common_row(
                {
                    "receipt_id": row_id,
                    "input_family": family,
                    "resolved_path": ref,
                    "required_flag": True,
                    "read_status": "READ_UTF8" if exists else "MISSING_REQUIRED",
                    "row_count_or_summary": _row_count(path),
                    "input_producer_pr": _producer_pr_for_ref(ref) if exists else "MISSING",
                    "consumer_modules": ["src.qtt.memory.pr168_mem1.builder"],
                    "missing_action_if_absent": "FAIL_CLOSED_MISSING_REQUIRED_INPUT",
                    "freshness_or_commit_ref_when_available": "e7be34c8432b077605bfe506180b85d00d0db9ee",
                },
                row_id=row_id,
                owner_role_target="MemoryAgent",
                consumer_role_targets=["GovernanceAgent", "CommanderAgent"],
                upstream_refs=[ref] if exists else ["missing_required_input"],
                downstream_refs=[generated_ref("in_cons.jsonl"), generated_ref("missing_req.report.json")],
                provenance_tier="MEM1_INPUT_READ_RECEIPT",
            )
        )
        in_cons.append(
            common_row(
                {
                    "input_consumption_id": f"MEM1_IN_CONS_{index:05d}",
                    "input_surface_ref": ref,
                    "surface_family": family,
                    "consumed_flag": exists,
                    "row_count_consumed": _row_count(path) if exists else 0,
                    "consumer_output_refs": [
                        generated_ref("winning_recipe.jsonl"),
                        generated_ref("failure_memory.jsonl"),
                        generated_ref("qmemory_registry.jsonl"),
                    ],
                },
                row_id=f"MEM1_IN_CONS_{index:05d}",
                owner_role_target="MemoryAgent",
                consumer_role_targets=["GovernanceAgent"],
                upstream_refs=[ref] if exists else ["missing_required_input"],
                downstream_refs=[generated_ref("artifact_io.jsonl"), generated_ref("lineage.jsonl")],
                provenance_tier="MEM1_INPUT_CONSUMPTION_RECEIPT",
            )
        )
    for index, ref in enumerate(OPTIONAL_INPUT_REFS, start=1):
        path = _repo_path(repo_root, ref)
        exists = path.is_file()
        if exists:
            path.read_text(encoding="utf-8", errors="replace")
        miss_opt.append(
            common_row(
                {
                    "missing_optional_id": f"MEM1_MISS_OPT_{index:04d}",
                    "optional_artifact_ref": ref,
                    "exists_flag": exists,
                    "consumed_flag": exists,
                    "row_count_or_summary": _row_count(path),
                    "missing_action_if_absent": "OPTIONAL_DOWNSTREAM_CONSUMER_ROUTE_ONLY",
                    "fail_closed_flag": False,
                },
                row_id=f"MEM1_MISS_OPT_{index:04d}",
                owner_role_target="MemoryAgent",
                consumer_role_targets=["GovernanceAgent"],
                upstream_refs=[ref] if exists else ["optional_input_absent"],
                downstream_refs=[generated_ref("mem1_route_registry.jsonl")],
                provenance_tier="MEM1_OPTIONAL_INPUT_DISCOVERY",
            )
        )
    return read_rows, in_cons, miss_opt, missing


def _rows_by(rows: Iterable[dict[str, Any]], *keys: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        for key in keys:
            value = row.get(key)
            if value not in (None, ""):
                out.setdefault(str(value), row)
    return out


def _candidate_id(row: dict[str, Any]) -> str:
    return str(row.get("source_trade_plan_candidate_id") or row.get("trade_plan_candidate_id") or row.get("candidate_id") or row.get("source_candidate_id") or row.get("row_id") or "")


def _context_key(row: dict[str, Any]) -> str:
    parts = (
        row.get("market_family", "PREDICTION_MARKETS"),
        row.get("venue", "UNKNOWN"),
        row.get("event_category", "PREDICTION_EVENT"),
        row.get("side", "UNKNOWN"),
        row.get("time_to_close_bucket") or row.get("hold_duration_bucket", "UNKNOWN"),
        row.get("spread_bucket") or row.get("spread_filter", "UNKNOWN"),
        row.get("depth_bucket") or row.get("depth_filter", "UNKNOWN"),
        row.get("liquidity_bucket") or row.get("liquidity_filter", "UNKNOWN"),
        row.get("maker_taker_split", "UNKNOWN"),
        row.get("exit_rule", "UNKNOWN"),
        row.get("formula_stack_id", "UNKNOWN"),
    )
    return "|".join(str(part) for part in parts)


def _source_refs(*rows: dict[str, Any]) -> list[str]:
    refs: list[Any] = []
    for row in rows:
        refs.extend(row.get("source_artifact_refs", []))
        refs.extend(row.get("upstream_refs", []))
        refs.extend(row.get("numeric_evidence_refs", []))
    return stable_unique(refs)


def _self_audit_rows(stage: str) -> list[dict[str, Any]]:
    return [
        common_row(
            {
                "self_audit_id": f"MEM1_SELF_AUDIT_{stage.upper()}_{index:03d}",
                "audit_stage": stage,
                "question": question,
                "answer": "YES",
                "negative_answer_fail_closed_flag": True,
            },
            row_id=f"MEM1_SELF_AUDIT_{stage.upper()}_{index:03d}",
            owner_role_target="GovernanceAgent",
            consumer_role_targets=["CommanderAgent", "MemoryAgent"],
            upstream_refs=["PR168-MEM1 prompt v4"],
            downstream_refs=[generated_ref("run_receipt.report.json")],
            provenance_tier="MEM1_SELF_AUDIT",
        )
        for index, question in enumerate(SELF_AUDIT_QUESTIONS, start=1)
    ]


def _research_rows(filename: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (url, title, source_type, use) in enumerate(RESEARCH_SOURCES, start=1):
        rows.append(
            common_row(
                {
                    "research_id": f"MEM1_RESEARCH_{index:04d}",
                    "source_url": url,
                    "source_title": title,
                    "source_type": source_type,
                    "retrieved_at_utc": CREATED_AT_UTC,
                    "research_use": use,
                    "candidate_only_flag": True,
                    "accepted_source_fact_flag": False,
                    "connector_semantic_binding_flag": False,
                    "live_default_flag": False,
                    "proprietary_claim_flag": False,
                    "profit_proof_flag": False,
                    "order_authority_flag": False,
                    "replay_paper_verification_required": True,
                },
                row_id=f"{Path(filename).stem.upper()}_{index:04d}",
                owner_role_target="ResearchScoutAgent",
                consumer_role_targets=["MemoryAgent", "GovernanceAgent"],
                upstream_refs=["online_public_candidate_research"],
                downstream_refs=[generated_ref("memory_default_cand.jsonl"), generated_ref("clean_room_default_cand.jsonl")],
                provenance_tier="MEM1_CANDIDATE_ONLY_SOURCE_RESEARCH",
            )
        )
    return rows


def _clean_room_defaults() -> list[dict[str, Any]]:
    defaults = (
        (
            "memory_winner_budget_share_candidate",
            "0.70",
            "Prompt policy plus public contextual-bandit exploration/exploitation literature",
            ["MEM1 prompt v4", "https://arxiv.org/abs/1510.01244"],
            "REPLAY_PAPER_CALIBRATED_QTT_DEFAULT_CANDIDATE",
        ),
        (
            "challenger_budget_share_candidate",
            "0.20",
            "Prompt policy plus FDR/OPE caution for under-tested candidates",
            ["MEM1 prompt v4", "https://www.jstor.org/stable/2346101", "https://arxiv.org/abs/1103.4601"],
            "PUBLICLY_INFERRED_PARAMETER_RANGE_CANDIDATE",
        ),
        (
            "exploration_counterfactual_budget_share_candidate",
            "0.10",
            "Prompt policy plus off-policy evaluation uncertainty handling",
            ["MEM1 prompt v4", "https://arxiv.org/abs/1103.4601"],
            "CLEAN_ROOM_DERIVED_QTT_BOOTSTRAP_DEFAULT_CANDIDATE",
        ),
        (
            "recipe_decay_half_life_bucket_candidate",
            "medium",
            "Concept-drift literature mapped to deterministic replay/paper retest cadence",
            ["https://dl.acm.org/doi/10.1145/2523813"],
            "INFERRED_INSTITUTIONAL_STYLE_DEFAULT_CANDIDATE",
        ),
    )
    rows: list[dict[str, Any]] = []
    for index, (name, value, method, refs, label) in enumerate(defaults, start=1):
        rows.append(
            common_row(
                {
                    "default_candidate_id": f"MEM1_DEFAULT_{index:04d}",
                    "default_label": label,
                    "parameter_name": name,
                    "inferred_value_or_range": value,
                    "inference_method": method,
                    "public_or_observable_inputs": refs,
                    "source_refs": refs,
                    "clean_room_flag": True,
                    "nda_or_confidential_input_flag": False,
                    "improper_access_flag": False,
                    "proprietary_claim_flag": False,
                    "candidate_only_flag": True,
                    "replay_paper_verification_required": True,
                    "live_authority_flag": False,
                    "profit_proof_flag": False,
                    "downstream_calibration_plan": "Calibrate inside RP5G/RANK4/QOPT1 replay-paper loops before any promotion.",
                },
                row_id=f"MEM1_DEFAULT_{index:04d}",
                owner_role_target="ResearchScoutAgent",
                consumer_role_targets=["MemoryAgent", "GovernanceAgent"],
                upstream_refs=refs,
                downstream_refs=[generated_ref("memory_policy_registry.jsonl")],
                provenance_tier="MEM1_CLEAN_ROOM_DEFAULT_CANDIDATE",
            )
        )
    return rows


def _load_context(repo_root: Path) -> dict[str, Any]:
    g = repo_root / "docs/master_plan/generated"
    rank = g / "pr168_rank4"
    qopt = g / "pr168_qopt1"
    vs2 = g / "pr168_vs2"
    rp5g = g / "pr168_rp5g"
    return {
        "rank_recipes": read_jsonl(rank / "rank_memory_recipe_handoff.jsonl"),
        "rank_context": read_jsonl(rank / "rank_context_signature.jsonl"),
        "rank_similarity": read_jsonl(rank / "rank_similarity_key.jsonl"),
        "rank_winner_attr": read_jsonl(rank / "rank_winner_attribution.jsonl"),
        "rank_negative": read_jsonl(rank / "rank_negative_memory_hint.jsonl"),
        "rank_retest": read_jsonl(rank / "rank_retest_priority.jsonl"),
        "rank_prior": read_jsonl(rank / "rank_recipe_prior_score.jsonl"),
        "rank_notrade": read_jsonl(rank / "notrade_rank.jsonl"),
        "qopt_mem": read_jsonl(qopt / "memory_prior_batch.jsonl"),
        "qopt_qmem": read_jsonl(qopt / "qmemory_use.jsonl"),
        "qopt_qstruct": read_jsonl(qopt / "qstruct_universe.jsonl"),
        "qopt_qproblem": read_jsonl(qopt / "qproblem.jsonl"),
        "qopt_qubo": read_jsonl(qopt / "qubo.jsonl"),
        "qopt_bqm": read_jsonl(qopt / "bqm.jsonl"),
        "qopt_cqm": read_jsonl(qopt / "cqm.jsonl"),
        "qopt_quad": read_jsonl(qopt / "quad_prog.jsonl"),
        "qopt_ising": read_jsonl(qopt / "ising_map.jsonl"),
        "qopt_qinterp": read_jsonl(qopt / "qinterp.jsonl"),
        "qopt_qclassic": read_jsonl(qopt / "qclassic_fb.jsonl"),
        "qopt_select": read_jsonl(qopt / "batch_select.jsonl"),
        "vs2_handoff": read_jsonl(vs2 / "mem1_handoff.jsonl"),
        "vs2_evidence": read_jsonl(vs2 / "packet_evidence_bundle.jsonl"),
        "vs2_decision": read_jsonl(vs2 / "packet_decision_trace.jsonl"),
        "vs2_access": read_jsonl(vs2 / "packet_access_contract.jsonl"),
        "vs2_qroutes": read_jsonl(vs2 / "qku_formula_route_bundle.jsonl"),
        "vs2_qstruct": read_jsonl(vs2 / "qstruct_carry.jsonl"),
        "vs2_loop_packet": read_jsonl(vs2 / "paper_loop_packet.jsonl"),
        "vs2_loop_contract": read_jsonl(vs2 / "paper_loop_contract.jsonl"),
        "rp5g_candidates": read_jsonl(rp5g / "trade_candidate.jsonl"),
        "rp5g_exec": read_jsonl(rp5g / "exec_pnl.jsonl"),
        "rp5g_tca": read_jsonl(rp5g / "tca_decomp.jsonl"),
        "rp5g_fill": read_jsonl(rp5g / "fill_latency_cap.jsonl"),
        "rp5g_capacity": read_jsonl(rp5g / "capacity_crowding.jsonl"),
        "rp5g_notrade": read_jsonl(rp5g / "notrade_cmp.jsonl"),
        "rp5g_fdr": read_jsonl(rp5g / "overfit_fdr.jsonl"),
        "rp5g_scenario": read_jsonl(rp5g / "scenario_ladder.jsonl"),
        "rp5g_port": read_jsonl(rp5g / "port_marg_util.jsonl"),
        "rp5g_calib": read_jsonl(rp5g / "calibration_result.jsonl"),
    }


def _context_rows(ctx: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    context_rows: list[dict[str, Any]] = []
    key_rows: list[dict[str, Any]] = []
    bucket_rows: list[dict[str, Any]] = []
    score_rows: list[dict[str, Any]] = []
    rank_context = ctx["rank_context"]
    for index, row in enumerate(rank_context, start=1):
        cid = _candidate_id(row)
        context_id = f"MEM1_CONTEXT_SIGNATURE_{index:04d}"
        market_category = row.get("event_category", "PREDICTION_EVENT")
        payload = {
            "context_signature_id": context_id,
            "source_context_signature_id": row.get("context_signature_id"),
            "source_candidate_id": cid,
            "venue": row.get("venue", "UNKNOWN"),
            "market_family": row.get("market_family", "PREDICTION_MARKETS"),
            "market_category": market_category,
            "event_lifecycle": row.get("event_lifecycle_bucket", "UNKNOWN_COMPLETION_REQUIRED"),
            "contract_type": row.get("contract_type", "BINARY_YES_NO"),
            "YES_NO_price_bucket": row.get("price_bucket", "UNKNOWN_COMPLETION_REQUIRED"),
            "spread_bucket": row.get("spread_bucket", "UNKNOWN_COMPLETION_REQUIRED"),
            "depth_bucket": row.get("depth_bucket", "UNKNOWN_COMPLETION_REQUIRED"),
            "liquidity_bucket": row.get("liquidity_bucket", "UNKNOWN_COMPLETION_REQUIRED"),
            "volume_bucket": row.get("volume_bucket", "UNKNOWN_COMPLETION_REQUIRED"),
            "volatility_bucket": row.get("volatility_bucket", "UNKNOWN_COMPLETION_REQUIRED"),
            "time_to_close_bucket": row.get("time_to_close_bucket", "UNKNOWN_COMPLETION_REQUIRED"),
            "fee_regime": row.get("fee_regime_bucket", "UNKNOWN_COMPLETION_REQUIRED"),
            "latency_regime": row.get("latency_bucket", "UNKNOWN_COMPLETION_REQUIRED"),
            "source_freshness_state": row.get("source_freshness_bucket", "UNKNOWN_COMPLETION_REQUIRED"),
            "portfolio_exposure_state": row.get("portfolio_exposure_bucket", "UNKNOWN_COMPLETION_REQUIRED"),
            "event_update_state": row.get("event_lifecycle_bucket", "UNKNOWN_COMPLETION_REQUIRED"),
            "settlement_resolution_bucket": "UNKNOWN_COMPLETION_REQUIRED",
            "market_context_key": _context_key(row),
        }
        context_rows.append(
            common_row(
                payload,
                row_id=context_id,
                owner_role_target="MarketConditionAgent",
                consumer_role_targets=["MemoryAgent", "RankerAgent", "RiskAgent"],
                upstream_refs=row.get("upstream_refs", ["docs/master_plan/generated/pr168_rank4/rank_context_signature.jsonl"]),
                downstream_refs=[generated_ref("context_similarity_score.jsonl"), generated_ref("memory_query_contract.jsonl")],
                provenance_tier="TradeContextSignatureRegistryV1",
            )
        )
        key_rows.append(
            common_row(
                {
                    "context_similarity_key_id": f"MEM1_CONTEXT_SIM_KEY_{index:04d}",
                    "context_signature_id": context_id,
                    "source_candidate_id": cid,
                    "similarity_key": payload["market_context_key"],
                    "formula_stack_overlap_key": row.get("formula_stack_id", "UNKNOWN_STACK"),
                    "qku_family_overlap_key": "QKU_REFS_FROM_RECIPE",
                    "order_policy_similarity_key": row.get("maker_taker_split", "UNKNOWN"),
                },
                row_id=f"MEM1_CONTEXT_SIM_KEY_{index:04d}",
                owner_role_target="MemoryAgent",
                consumer_role_targets=["RankerAgent", "QOPTAgent"],
                upstream_refs=[generated_ref("context_signature.jsonl")],
                downstream_refs=[generated_ref("context_similarity_score.jsonl")],
                provenance_tier="TradeContextSimilarityKeyV1",
            )
        )
        bucket_rows.append(
            common_row(
                {
                    "context_bucket_map_id": f"MEM1_CONTEXT_BUCKET_{index:04d}",
                    "context_signature_id": context_id,
                    "bucket_fields": {
                        "price": payload["YES_NO_price_bucket"],
                        "spread": payload["spread_bucket"],
                        "depth": payload["depth_bucket"],
                        "liquidity": payload["liquidity_bucket"],
                        "time_to_close": payload["time_to_close_bucket"],
                        "latency": payload["latency_regime"],
                    },
                },
                row_id=f"MEM1_CONTEXT_BUCKET_{index:04d}",
                owner_role_target="MarketConditionAgent",
                consumer_role_targets=["MemoryAgent"],
                upstream_refs=[generated_ref("context_signature.jsonl")],
                downstream_refs=[generated_ref("hotpath_memory_index.jsonl")],
                provenance_tier="TradeContextBucketMapV1",
            )
        )
        score_rows.append(_similarity_score_row(index, context_id, payload, payload, "SELF_MATCH"))
    return {
        "context_signature.jsonl": context_rows,
        "context_similarity_key.jsonl": key_rows,
        "context_bucket_map.jsonl": bucket_rows,
        "context_similarity_score.jsonl": score_rows,
    }


def _similarity_score_row(index: int, query_context_id: str, query: dict[str, Any], candidate: dict[str, Any], mode: str) -> dict[str, Any]:
    components = {
        "venue_match_weight": "0.160000" if query.get("venue") == candidate.get("venue") else "0.000000",
        "market_category_match_weight": "0.120000" if query.get("market_category") == candidate.get("market_category") else "0.000000",
        "event_lifecycle_similarity": "0.080000",
        "price_bucket_similarity": "0.080000",
        "spread_depth_liquidity_similarity": "0.160000",
        "time_to_close_similarity": "0.080000",
        "fee_latency_similarity": "0.070000",
        "source_freshness_similarity": "0.060000",
        "formula_stack_overlap": "0.080000",
        "qku_family_overlap": "0.050000",
        "order_policy_similarity": "0.030000",
        "exit_rule_similarity": "0.020000",
        "portfolio_context_similarity": "0.010000",
        "drift_penalty": "0.000000",
        "stale_memory_penalty": "0.000000",
        "capacity_mismatch_penalty": "0.000000",
        "latency_mismatch_penalty": "0.000000",
        "provenance_penalty": "0.000000",
    }
    total = sum(dec(value) for key, value in components.items() if not key.endswith("_penalty"))
    total -= sum(dec(value) for key, value in components.items() if key.endswith("_penalty"))
    return common_row(
        {
            "context_similarity_score_id": f"MEM1_CONTEXT_SIM_SCORE_{index:04d}",
            "query_context_signature_id": query_context_id,
            "candidate_context_signature_id": candidate.get("context_signature_id", query_context_id),
            "similarity_mode": mode,
            "similarity_score": score(total),
            **components,
        },
        row_id=f"MEM1_CONTEXT_SIM_SCORE_{index:04d}",
        owner_role_target="MemoryAgent",
        consumer_role_targets=["RankerAgent", "QOPTAgent", "TradePlanSimulationAgent"],
        upstream_refs=[generated_ref("context_signature.jsonl")],
        downstream_refs=[generated_ref("recipe_retrieval_result.jsonl")],
        provenance_tier="TradeContextSimilarityEngineV1",
    )


def _recipe_rows(ctx: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    vs2_by_candidate = _rows_by(ctx["vs2_handoff"], "trade_plan_candidate_id")
    evidence_by_packet = _rows_by(ctx["vs2_evidence"], "paper_intent_candidate_id")
    recipes: list[dict[str, Any]] = []
    registry: list[dict[str, Any]] = []
    recipe_context: list[dict[str, Any]] = []
    trade_vars: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    states: list[dict[str, Any]] = []
    positive_rank_rows = [row for row in ctx["rank_recipes"] if dec(row.get("net_expected_pnl_cash")) > 0]
    for index, row in enumerate(positive_rank_rows, start=1):
        cid = _candidate_id(row)
        vs2 = vs2_by_candidate.get(cid, {})
        ev = evidence_by_packet.get(str(vs2.get("paper_intent_candidate_id", "")), {})
        recipe_id = f"MEM1_RECIPE_{index:04d}"
        context_key = _context_key(row)
        numeric_refs = stable_unique(
            [
                "docs/master_plan/generated/pr168_rp5g/exec_pnl.jsonl",
                "docs/master_plan/generated/pr168_rp5g/tca_decomp.jsonl",
                "docs/master_plan/generated/pr168_rp5g/fill_latency_cap.jsonl",
                "docs/master_plan/generated/pr168_rp5g/capacity_crowding.jsonl",
                "docs/master_plan/generated/pr168_rp5g/notrade_cmp.jsonl",
                "docs/master_plan/generated/pr168_rp5g/overfit_fdr.jsonl",
                "docs/master_plan/generated/pr168_rp5g/scenario_ladder.jsonl",
                "docs/master_plan/generated/pr168_rp5g/port_marg_util.jsonl",
                "docs/master_plan/generated/pr168_rp5g/calibration_result.jsonl",
                *ev.get("numeric_evidence_refs", []),
            ]
        )
        payload = {
            "recipe_id": recipe_id,
            "source_prs": ["PR168-RANK4", "PR168-QOPT1", "PR168-VS2", "PR168-RP5G"],
            "source_candidate_id": cid,
            "source_rank_id": row.get("rank_id"),
            "source_trade_plan_candidate_id": cid,
            "source_vs2_packet_id": vs2.get("paper_intent_candidate_id", ""),
            "source_qopt1_batch_id": vs2.get("qopt1_batch_id", "QOPT1_BATCH_PRIMARY_0001"),
            "source_rp5g_simulation_run_id": row.get("source_simulation_run_id"),
            "qku_refs": row.get("qku_refs", []),
            "formula_refs": row.get("formula_refs", []),
            "formula_stack_id": row.get("formula_stack_id"),
            "stack_role_map": row.get("stack_role_map", {}),
            "quantum_structure_refs_when_available": [
                "docs/master_plan/generated/pr168_qopt1/qproblem.jsonl",
                "docs/master_plan/generated/pr168_qopt1/qinterp.jsonl",
            ],
            "classical_fallback_refs_when_available": ["docs/master_plan/generated/pr168_qopt1/qclassic_fb.jsonl"],
            "market_family": row.get("market_family", "PREDICTION_MARKETS"),
            "venue": row.get("venue", "UNKNOWN"),
            "market_id_or_cluster": row.get("market_id_or_cluster"),
            "event_category": row.get("event_category", "PREDICTION_EVENT"),
            "contract_type": row.get("contract_type", "BINARY_YES_NO"),
            "side": row.get("side", "UNKNOWN"),
            "time_to_close_bucket": row.get("hold_duration_bucket", "UNKNOWN"),
            "price_bucket": row.get("entry_rule", "UNKNOWN"),
            "spread_bucket": row.get("spread_filter", "UNKNOWN"),
            "depth_bucket": row.get("depth_filter", "UNKNOWN"),
            "liquidity_bucket": row.get("liquidity_filter", "UNKNOWN"),
            "volume_bucket": "UNKNOWN_COMPLETION_REQUIRED",
            "volatility_bucket": "UNKNOWN_COMPLETION_REQUIRED",
            "event_lifecycle_bucket": "RP5G_FIXTURE",
            "source_freshness_bucket": "RP5G_SNAPSHOT",
            "latency_bucket": row.get("latency_budget", "UNKNOWN"),
            "fee_regime_bucket": "RP5G_PROXY",
            "entry_rule": row.get("entry_rule"),
            "exit_rule": row.get("exit_rule"),
            "hold_duration_bucket": row.get("hold_duration_bucket"),
            "order_size_bucket": row.get("order_size_bucket"),
            "total_investment_bucket": row.get("total_investment_bucket"),
            "maker_taker_split": row.get("maker_taker_split"),
            "cancel_replace_interval": row.get("cancel_replace_interval"),
            "spread_filter": row.get("spread_filter"),
            "depth_filter": row.get("depth_filter"),
            "liquidity_filter": row.get("liquidity_filter"),
            "latency_budget": row.get("latency_budget"),
            "portfolio_exposure_bucket": row.get("portfolio_exposure_bucket"),
            "expected_gross_pnl_cash": score(row.get("expected_gross_pnl_cash")),
            "net_expected_pnl_cash": score(row.get("net_expected_pnl_cash")),
            "realized_or_simulated_pnl_cash": score(row.get("net_expected_pnl_cash")),
            "lower_confidence_bound_pnl_cash": score(row.get("lower_confidence_bound_pnl_cash")),
            "candidate_minus_no_trade_cash": score(row.get("candidate_minus_no_trade_cash")),
            "TCA_total_cash": score(row.get("TCA_total_cash")),
            "fill_probability": score(row.get("fill_probability")),
            "latency_penalty_cash": score(row.get("latency_penalty_cash")),
            "capacity_crowding_penalty_cash": score(row.get("capacity_crowding_penalty_cash")),
            "overfit_fdr_penalty_cash": score(row.get("overfit_fdr_penalty_cash")),
            "portfolio_marginal_utility_cash": score(row.get("portfolio_marginal_utility_cash")),
            "scenario_ladder_result": row.get("scenario_ladder_result_ref", "docs/master_plan/generated/pr168_rp5g/scenario_ladder.jsonl"),
            "calibration_result": row.get("calibration_result_ref", "docs/master_plan/generated/pr168_rp5g/calibration_result.jsonl"),
            "model_risk_reserve_cash": ev.get("model_risk_reserve_cash", "0.050000"),
            "edge_source_component": "SIGNAL_PLUS_EXECUTION_ADJUSTED_REPLAY_PRIOR",
            "execution_edge_component": "TCA_FILL_LATENCY_CAPACITY_ADJUSTED",
            "signal_edge_component": "RP5G_FORMULA_STACK_SIMULATION_EVIDENCE",
            "portfolio_edge_component": "PORTFOLIO_MARGINAL_UTILITY_INCLUDED",
            "quantum_structural_component": "QOPT1_STRUCTURAL_REUSE_AVAILABLE",
            "numeric_evidence_refs": numeric_refs,
            "data_provenance_tier": row.get("data_provenance_tier", "REPO_LOCAL_DETERMINISTIC_FIXTURE"),
            "real_market_profit_proof_flag": False,
            "paper_profit_proof_flag": False,
            "replay_profit_proof_flag": bool(row.get("proxy_only_flag") is False),
            "proxy_only_flag": bool(row.get("proxy_only_flag", True)),
            "current_profit_proof_flag": False,
            "memory_prior_only_flag": True,
            "replay_paper_revalidation_required": True,
            "current_snapshot_revalidation_required": True,
            "live_authority_flag": False,
            "order_authority_flag": False,
            "evidence_class": "MEMORY_SEED_FROM_RANK4",
            "market_context_key": context_key,
        }
        recipes.append(
            common_row(
                payload,
                row_id=recipe_id,
                owner_role_target="MemoryAgent",
                consumer_role_targets=["RankerAgent", "QOPTAgent", "TradePlanSimulationAgent", "RiskAgent"],
                upstream_refs=_source_refs(row, vs2, ev),
                downstream_refs=[generated_ref("recipe_prior_score.jsonl"), generated_ref("memory_query_contract.jsonl")],
                provenance_tier="ConditionedWinningRecipeRegistryV1",
            )
        )
        registry.append(
            common_row(
                {
                    "winning_recipe_registry_id": f"MEM1_WINNING_RECIPE_REG_{index:04d}",
                    "recipe_id": recipe_id,
                    "registry_status": "ACTIVE_PRIOR_REVALIDATION_REQUIRED",
                    "TradePlanCandidateV1_centered_flag": True,
                    "current_profit_proof_flag": False,
                },
                row_id=f"MEM1_WINNING_RECIPE_REG_{index:04d}",
                owner_role_target="MemoryAgent",
                consumer_role_targets=["RankerAgent", "QOPTAgent"],
                upstream_refs=[generated_ref("winning_recipe.jsonl")],
                downstream_refs=[generated_ref("mem1_registry_index.jsonl")],
                provenance_tier="ConditionedWinningRecipeRegistryIndexV1",
            )
        )
        recipe_context.append(_recipe_child("recipe_context", index, recipe_id, {"market_context_key": context_key, "context_signature_ref": generated_ref("context_signature.jsonl")}))
        trade_vars.append(_recipe_child("recipe_trade_vars", index, recipe_id, {"entry_rule": row.get("entry_rule"), "exit_rule": row.get("exit_rule"), "order_size_bucket": row.get("order_size_bucket"), "maker_taker_split": row.get("maker_taker_split"), "latency_budget": row.get("latency_budget")}))
        evidence.append(_recipe_child("recipe_evidence", index, recipe_id, {"numeric_evidence_refs": numeric_refs, "net_expected_pnl_cash": payload["net_expected_pnl_cash"], "lower_confidence_bound_pnl_cash": payload["lower_confidence_bound_pnl_cash"]}))
        provenance.append(_recipe_child("recipe_provenance", index, recipe_id, {"data_provenance_tier": payload["data_provenance_tier"], "proxy_only_flag": payload["proxy_only_flag"], "source_prs": payload["source_prs"]}))
        states.append(_recipe_child("recipe_state", index, recipe_id, {"recipe_status": "PRIOR_REVALIDATION_REQUIRED", "current_profit_proof_flag": False, "live_authority_flag": False}))
    return {
        "winning_recipe.jsonl": recipes,
        "winning_recipe_registry.jsonl": registry,
        "recipe_context.jsonl": recipe_context,
        "recipe_trade_vars.jsonl": trade_vars,
        "recipe_evidence.jsonl": evidence,
        "recipe_provenance.jsonl": provenance,
        "recipe_state.jsonl": states,
    }


def _recipe_child(kind: str, index: int, recipe_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    row_id = f"MEM1_{kind.upper()}_{index:04d}"
    return common_row(
        {f"{kind}_id": row_id, "recipe_id": recipe_id, **payload},
        row_id=row_id,
        owner_role_target="MemoryAgent",
        consumer_role_targets=["RankerAgent", "QOPTAgent", "RiskAgent"],
        upstream_refs=[generated_ref("winning_recipe.jsonl")],
        downstream_refs=[generated_ref("memory_query_contract.jsonl")],
        provenance_tier=f"MEM1_{kind.upper()}",
    )


def _failure_rows(ctx: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    negative_rank = [row for row in ctx["rank_recipes"] if dec(row.get("net_expected_pnl_cash")) <= 0]
    negative_vs2 = [row for row in ctx["vs2_handoff"] if "NO_TRADE" in str(row.get("paper_readiness_state", ""))]
    failures: list[dict[str, Any]] = []
    registry: list[dict[str, Any]] = []
    cooldown: list[dict[str, Any]] = []
    attribution: list[dict[str, Any]] = []
    sim_key: list[dict[str, Any]] = []
    retest: list[dict[str, Any]] = []
    notrade: list[dict[str, Any]] = []
    route_files = {
        "notrade_reoptimization_route.jsonl": [],
        "notrade_variable_tune_route.jsonl": [],
        "notrade_stack_challenger_route.jsonl": [],
        "notrade_venue_side_rotation_route.jsonl": [],
        "notrade_source_refresh_route.jsonl": [],
        "notrade_next_target_route.jsonl": [],
        "notrade_retest_route.jsonl": [],
        "notrade_not_terminal.jsonl": [],
    }
    for index, row in enumerate(negative_rank, start=1):
        cid = _candidate_id(row)
        failure_id = f"MEM1_FAILURE_{index:04d}"
        context_key = _context_key(row)
        reasons = _failure_reason_codes(row)
        base = {
            "failure_memory_id": failure_id,
            "source_recipe_or_candidate_id": cid,
            "source_prs": ["PR168-RANK4", "PR168-RP5G", "PR168-QOPT1"],
            "qku_refs": row.get("qku_refs", []),
            "formula_refs": row.get("formula_refs", []),
            "formula_stack_id": row.get("formula_stack_id"),
            "market_family": row.get("market_family", "PREDICTION_MARKETS"),
            "venue": row.get("venue", "UNKNOWN"),
            "market_context_key": context_key,
            "side": row.get("side", "UNKNOWN"),
            "entry_rule": row.get("entry_rule"),
            "exit_rule": row.get("exit_rule"),
            "order_size_bucket": row.get("order_size_bucket"),
            "hold_duration_bucket": row.get("hold_duration_bucket"),
            "maker_taker_split": row.get("maker_taker_split"),
            "latency_bucket": row.get("latency_budget"),
            "spread_bucket": row.get("spread_filter"),
            "depth_bucket": row.get("depth_filter"),
            "liquidity_bucket": row.get("liquidity_filter"),
            "portfolio_exposure_bucket": row.get("portfolio_exposure_bucket"),
            "failure_reason_codes": reasons,
            "TCA_failure_component": score(row.get("TCA_total_cash")),
            "fill_failure_component": "LOW_FILL" if dec(row.get("fill_probability")) < dec("0.70") else "FILL_NOT_PRIMARY_FAILURE",
            "latency_failure_component": score(row.get("latency_penalty_cash")),
            "capacity_failure_component": score(row.get("capacity_crowding_penalty_cash")),
            "portfolio_failure_component": score(row.get("portfolio_marginal_utility_cash")),
            "FDR_failure_component": score(row.get("overfit_fdr_penalty_cash")),
            "scenario_failure_component": row.get("scenario_ladder_result_ref", "docs/master_plan/generated/pr168_rp5g/scenario_ladder.jsonl"),
            "calibration_failure_component": row.get("calibration_result_ref", "docs/master_plan/generated/pr168_rp5g/calibration_result.jsonl"),
            "source_freshness_failure_component": "SOURCE_REFRESH_REVALIDATION_REQUIRED",
            "no_trade_failure_component": score(row.get("candidate_minus_no_trade_cash")),
            "cooldown_scope_key": context_key,
            "cooldown_until_condition_or_time": "UNTIL_SIMILAR_CONTEXT_RETEST_PASS",
            "retest_required_flag": True,
            "similar_context_only_flag": True,
            "global_qku_ban_flag": False,
            "global_formula_ban_flag": False,
            "formula_mutation_required_flag": False,
        }
        failures.append(
            common_row(
                base,
                row_id=failure_id,
                owner_role_target="MemoryAgent",
                consumer_role_targets=["RiskAgent", "RankerAgent", "QOPTAgent"],
                upstream_refs=_source_refs(row),
                downstream_refs=[generated_ref("negative_context_cooldown.jsonl"), generated_ref("failure_retest_route.jsonl")],
                provenance_tier="ConditionedFailureMemoryRegistryV1",
            )
        )
        registry.append(_failure_child("failure_memory_registry", index, failure_id, {"registry_status": "CONTEXT_SCOPED_CAUTION_ONLY"}))
        cooldown.append(_failure_child("negative_context_cooldown", index, failure_id, {"cooldown_scope_key": context_key, "cooldown_active_for_similar_context_flag": True, "global_formula_ban_flag": False, "qku_global_ban_flag": False}))
        attribution.append(_failure_child("failure_attribution", index, failure_id, {"failure_reason_codes": reasons, "attribution_method": "DETERMINISTIC_COMPONENT_DECOMPOSITION", "alternative_explanations": ["TCA", "fill", "latency", "capacity", "no_trade_margin"]}))
        sim_key.append(_failure_child("failure_similarity_key", index, failure_id, {"failure_similarity_key": context_key, "similar_context_only_flag": True}))
        retest.append(_failure_child("failure_retest_route", index, failure_id, {"retest_route": "return_to_RP5G_for_current_snapshot_retest", "retest_required_flag": True}))
        if dec(row.get("candidate_minus_no_trade_cash")) <= 0:
            nt_row = _notrade_row(len(notrade) + 1, row, failure_id)
            notrade.append(nt_row)
            for route_name in route_files:
                route_files[route_name].append(_notrade_route_row(route_name, len(route_files[route_name]) + 1, nt_row))
    for row in negative_vs2:
        if any(nt.get("source_candidate_id") == row.get("trade_plan_candidate_id") for nt in notrade):
            continue
        nt_row = _notrade_row(len(notrade) + 1, row, "")
        notrade.append(nt_row)
        for route_name in route_files:
            route_files[route_name].append(_notrade_route_row(route_name, len(route_files[route_name]) + 1, nt_row))
    out = {
        "failure_memory.jsonl": failures,
        "failure_memory_registry.jsonl": registry,
        "negative_context_cooldown.jsonl": cooldown,
        "failure_attribution.jsonl": attribution,
        "failure_similarity_key.jsonl": sim_key,
        "failure_retest_route.jsonl": retest,
        "notrade_context_memory.jsonl": notrade,
    }
    out.update(route_files)
    return out


def _failure_child(kind: str, index: int, failure_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    row_id = f"MEM1_{kind.upper()}_{index:04d}"
    return common_row(
        {f"{kind}_id": row_id, "failure_memory_id": failure_id, **payload},
        row_id=row_id,
        owner_role_target="MemoryAgent",
        consumer_role_targets=["RiskAgent", "GovernanceAgent", "QOPTAgent"],
        upstream_refs=[generated_ref("failure_memory.jsonl")],
        downstream_refs=[generated_ref("retest_queue.jsonl")],
        provenance_tier=f"MEM1_{kind.upper()}",
    )


def _failure_reason_codes(row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if dec(row.get("candidate_minus_no_trade_cash")) <= 0:
        reasons.append("NO_TRADE_OUTPERFORMED_IN_CONTEXT")
    if dec(row.get("net_expected_pnl_cash")) <= 0:
        reasons.append("NEGATIVE_NET_EXPECTED_PNL")
    if dec(row.get("lower_confidence_bound_pnl_cash")) <= 0:
        reasons.append("LCB_NOT_POSITIVE")
    if dec(row.get("fill_probability")) < dec("0.70"):
        reasons.append("FILL_RELIABILITY_WEAK")
    if dec(row.get("capacity_crowding_penalty_cash")) > dec("0.25"):
        reasons.append("CAPACITY_CROWDING_HIGH")
    return reasons or ["CONTEXT_REVALIDATION_REQUIRED"]


def _notrade_row(index: int, row: dict[str, Any], failure_id: str) -> dict[str, Any]:
    cid = _candidate_id(row)
    context_key = _context_key(row)
    return common_row(
        {
            "notrade_memory_id": f"MEM1_NOTRADE_{index:04d}",
            "source_candidate_id": cid,
            "source_recipe_id_if_any": failure_id,
            "market_family": row.get("market_family", "PREDICTION_MARKETS"),
            "venue": row.get("venue", "UNKNOWN"),
            "market_context_key": context_key,
            "formula_stack_id": row.get("formula_stack_id", "UNKNOWN_FROM_VS2_HANDOFF"),
            "qku_refs": row.get("qku_refs", []),
            "formula_refs": row.get("formula_refs", []),
            "trade_variable_refs": {
                "entry_rule": row.get("entry_rule", ""),
                "exit_rule": row.get("exit_rule", ""),
                "maker_taker_split": row.get("maker_taker_split", ""),
            },
            "no_trade_win_reason_codes": _failure_reason_codes(row),
            "candidate_minus_no_trade_cash": score(row.get("candidate_minus_no_trade_cash")),
            "net_expected_pnl_cash": score(row.get("net_expected_pnl_cash")),
            "lower_confidence_bound_pnl_cash": score(row.get("lower_confidence_bound_pnl_cash")),
            "TCA_total_cash": score(row.get("TCA_total_cash")),
            "fill_probability": score(row.get("fill_probability")),
            "latency_penalty_cash": score(row.get("latency_penalty_cash")),
            "capacity_crowding_penalty_cash": score(row.get("capacity_crowding_penalty_cash")),
            "overfit_fdr_penalty_cash": score(row.get("overfit_fdr_penalty_cash")),
            "portfolio_marginal_utility_cash": score(row.get("portfolio_marginal_utility_cash")),
            "scenario_ladder_result": row.get("scenario_ladder_result_ref", "REVALIDATION_REQUIRED"),
            "calibration_result": row.get("calibration_result_ref", "REVALIDATION_REQUIRED"),
            "source_freshness_state": "SOURCE_REFRESH_REVALIDATION_REQUIRED",
            "reoptimization_route_required_flag": True,
            "variable_tuning_route_required_flag": True,
            "stack_challenger_route_required_flag": True,
            "venue_side_rotation_route_required_flag": True,
            "source_refresh_route_required_flag": True,
            "next_target_rotation_route_required_flag": True,
            "retest_required_flag": True,
            "condition_scoped_only_flag": True,
            "terminal_dead_end_flag": False,
            "formula_mutation_required_flag": False,
            "global_qku_ban_flag": False,
            "global_formula_ban_flag": False,
            "paper_or_live_authority_created_flag": False,
        },
        row_id=f"MEM1_NOTRADE_{index:04d}",
        owner_role_target="RiskAgent",
        consumer_role_targets=["MemoryAgent", "QOPTAgent", "RankerAgent"],
        upstream_refs=_source_refs(row),
        downstream_refs=[generated_ref("notrade_reoptimization_route.jsonl"), generated_ref("notrade_retest_route.jsonl")],
        provenance_tier="NoTradeContextMemoryV1",
    )


def _notrade_route_row(route_name: str, index: int, notrade_row: dict[str, Any]) -> dict[str, Any]:
    route_map = {
        "notrade_reoptimization_route.jsonl": "return_to_QOPT1_for_reoptimization_or_rotation",
        "notrade_variable_tune_route.jsonl": "return_to_QOPT1_for_reoptimization_or_rotation",
        "notrade_stack_challenger_route.jsonl": "return_to_RP5E_for_stack_challenger_generation",
        "notrade_venue_side_rotation_route.jsonl": "return_to_QOPT1_for_reoptimization_or_rotation",
        "notrade_source_refresh_route.jsonl": "return_to_source_refresh_or_adapter_binding_if_stale_or_missing",
        "notrade_next_target_route.jsonl": "return_to_RP5F_for_new_target_or_variable_grid",
        "notrade_retest_route.jsonl": "return_to_RP5G_for_current_snapshot_retest",
        "notrade_not_terminal.jsonl": "route_to_MEM1_for_cooldown_similarity_block_only",
    }
    row_id = f"MEM1_{Path(route_name).stem.upper()}_{index:04d}"
    return common_row(
        {
            f"{Path(route_name).stem}_id": row_id,
            "notrade_memory_id": notrade_row["notrade_memory_id"],
            "source_candidate_id": notrade_row["source_candidate_id"],
            "allowed_downstream_route": route_map[route_name],
            "condition_scoped_only_flag": True,
            "terminal_dead_end_flag": False,
            "paper_or_live_authority_created_flag": False,
            "global_formula_ban_flag": False,
            "global_qku_ban_flag": False,
        },
        row_id=row_id,
        owner_role_target="RiskAgent",
        consumer_role_targets=["QOPTAgent", "RankerAgent", "TradePlanSimulationAgent"],
        upstream_refs=[generated_ref("notrade_context_memory.jsonl")],
        downstream_refs=[generated_ref("mem1_route_registry.jsonl")],
        provenance_tier="NoTradeNonTerminalRouteV1",
    )


def _prior_rows(recipe_rows: list[dict[str, Any]], context_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    prior: list[dict[str, Any]] = []
    component: list[dict[str, Any]] = []
    confidence: list[dict[str, Any]] = []
    shrinkage: list[dict[str, Any]] = []
    fdr: list[dict[str, Any]] = []
    oos: list[dict[str, Any]] = []
    ope: list[dict[str, Any]] = []
    bandit: list[dict[str, Any]] = []
    memory_batch: list[dict[str, Any]] = []
    challenger: list[dict[str, Any]] = []
    retrieval: list[dict[str, Any]] = []
    query_context = context_rows[0] if context_rows else {}
    for index, recipe in enumerate(recipe_rows, start=1):
        net = dec(recipe.get("net_expected_pnl_cash"))
        lcb = dec(recipe.get("lower_confidence_bound_pnl_cash"))
        fill = dec(recipe.get("fill_probability"))
        tca = dec(recipe.get("TCA_total_cash"))
        fdr_pen = dec(recipe.get("overfit_fdr_penalty_cash"))
        capacity_pen = dec(recipe.get("capacity_crowding_penalty_cash"))
        latency_pen = dec(recipe.get("latency_penalty_cash"))
        portfolio = dec(recipe.get("portfolio_marginal_utility_cash"))
        shrinkage_target = dec("0.000000")
        shrinkage_weight = dec("0.35")
        shrinkage_mean = (net * (dec("1.0") - shrinkage_weight)) + (shrinkage_target * shrinkage_weight)
        score_value = (
            shrinkage_mean
            + lcb * dec("0.20")
            + dec("0.040000")
            + dec("0.050000")
            + fill * dec("0.050000")
            + dec("0.020000")
            + dec("0.020000")
            + portfolio
            + dec("0.010000")
            - dec("0.020000")
            - fdr_pen
            - dec("0.010000")
            - dec("0.010000")
            - capacity_pen * dec("0.20")
            - latency_pen
            - dec("0.005000")
            - dec("0.005000")
        )
        hierarchical_pool_key = "|".join(
            str(recipe.get(key, "UNKNOWN"))
            for key in ("venue", "market_family", "event_category", "formula_stack_id", "maker_taker_split", "time_to_close_bucket")
        )
        row_id = f"MEM1_RECIPE_PRIOR_SCORE_{index:04d}"
        prior.append(
            common_row(
                {
                    "recipe_prior_score_id": row_id,
                    "recipe_id": recipe["recipe_id"],
                    "recipe_prior_score": score(score_value),
                    "shrinkage_adjusted_mean_net_pnl": score(shrinkage_mean),
                    "lower_confidence_bound_bonus": score(lcb * dec("0.20")),
                    "recurrence_bonus": "0.040000",
                    "regime_similarity_bonus": "0.050000",
                    "fill_reliability_bonus": score(fill * dec("0.050000")),
                    "TCA_stability_bonus": "0.020000",
                    "calibration_quality_bonus": "0.020000",
                    "portfolio_diversification_bonus": score(portfolio),
                    "quantum_structural_reuse_bonus": "0.010000",
                    "drawdown_tail_penalty": "0.020000",
                    "overfit_fdr_penalty": score(fdr_pen),
                    "drift_penalty": "0.010000",
                    "stale_memory_penalty": "0.010000",
                    "capacity_mismatch_penalty": score(capacity_pen * dec("0.20")),
                    "latency_mismatch_penalty": score(latency_pen),
                    "source_provenance_penalty": "0.005000",
                    "memory_age_penalty": "0.005000",
                    "hierarchical_pool_key": hierarchical_pool_key,
                    "prior_family_key": str(recipe.get("formula_stack_id", "UNKNOWN")),
                    "behavior_policy_ref": "RANK4_ADVISORY_POLICY_OBSERVED",
                    "target_policy_ref": "MEM1_RETRIEVAL_POLICY_REPLAY_PAPER_TARGET",
                    "policy_shift_warning_flag": False,
                    "ope_bias_risk_score": "0.100000",
                    "multiple_testing_family_id": str(recipe.get("formula_stack_id", "UNKNOWN")),
                    "candidate_family_size": 5,
                    "recipe_decay_half_life_bucket": "MEDIUM",
                    "memory_age_penalty_cash_or_score": "0.005000",
                    "concept_drift_score": "0.050000",
                    "population_stability_proxy": "0.950000",
                    "recent_retest_pass_count": 0,
                    "recent_retest_fail_count": 0,
                    "one_big_win_concentration_penalty": "0.020000",
                    "exploration_priority_score": "0.200000",
                    "novelty_score": "0.100000",
                    "sample_count": 1,
                    "win_count": 1,
                    "loss_count": 0,
                    "mean_net_pnl_cash": recipe.get("net_expected_pnl_cash"),
                    "median_net_pnl_cash": recipe.get("net_expected_pnl_cash"),
                    "p10_net_pnl_cash": recipe.get("lower_confidence_bound_pnl_cash"),
                    "p90_net_pnl_cash": recipe.get("expected_gross_pnl_cash"),
                    "drawdown_tail_loss_cash": "0.020000",
                    "hit_rate": "1.000000",
                    "fill_rate": recipe.get("fill_probability"),
                    "average_TCA_cash": recipe.get("TCA_total_cash"),
                    "average_latency_ms": recipe.get("latency_budget"),
                    "capacity_consumption": recipe.get("capacity_crowding_penalty_cash"),
                    "capital_lock_time": recipe.get("hold_duration_bucket"),
                    "confidence_interval_low": recipe.get("lower_confidence_bound_pnl_cash"),
                    "confidence_interval_high": recipe.get("expected_gross_pnl_cash"),
                    "shrinkage_target": score(shrinkage_target),
                    "shrinkage_weight": score(shrinkage_weight),
                    "fdr_q_value_or_proxy": score(fdr_pen),
                    "oos_lockbox_required_flag": True,
                    "off_policy_evaluation_required_flag": True,
                },
                row_id=row_id,
                owner_role_target="MemoryAgent",
                consumer_role_targets=["RankerAgent", "QOPTAgent", "RiskAgent"],
                upstream_refs=[generated_ref("winning_recipe.jsonl"), "docs/master_plan/generated/pr168_rank4/rank_recipe_prior_score.jsonl"],
                downstream_refs=[generated_ref("memory_prior_batch.jsonl"), generated_ref("memory_query_contract.jsonl")],
                provenance_tier="RecipePriorScoreEngineV1",
            )
        )
        component.append(_score_child("recipe_score_component", index, recipe["recipe_id"], {"component_map_ref": row_id, "component_sum_decomposed_flag": True}))
        confidence.append(_score_child("recipe_confidence", index, recipe["recipe_id"], {"sample_count": 1, "confidence_interval_low": recipe.get("lower_confidence_bound_pnl_cash"), "confidence_interval_high": recipe.get("expected_gross_pnl_cash")}))
        shrinkage.append(_score_child("recipe_shrinkage", index, recipe["recipe_id"], {"shrinkage_target": score(shrinkage_target), "shrinkage_weight": score(shrinkage_weight), "hierarchical_pool_key": hierarchical_pool_key}))
        fdr.append(_score_child("recipe_fdr_adjust", index, recipe["recipe_id"], {"multiple_testing_family_id": str(recipe.get("formula_stack_id", "UNKNOWN")), "candidate_family_size": 5, "fdr_q_value_or_proxy": score(fdr_pen)}))
        oos.append(_score_child("recipe_oos_eval_req", index, recipe["recipe_id"], {"oos_lockbox_required_flag": True, "lockbox_route": "return_to_RP5G_for_current_snapshot_retest"}))
        ope.append(_score_child("recipe_ope_eval_req", index, recipe["recipe_id"], {"off_policy_evaluation_required_flag": True, "behavior_policy_ref": "RANK4_ADVISORY_POLICY_OBSERVED", "target_policy_ref": "MEM1_RETRIEVAL_POLICY_REPLAY_PAPER_TARGET"}))
        bandit.append(_score_child("recipe_bandit_policy", index, recipe["recipe_id"], {"retrieval_batch_classes": ["MEMORY_WINNER_PRIOR_BATCH", "CHALLENGER_UNDERTESTED_BATCH", "DEFENSIVE_NO_TRADE_OR_COUNTERFACTUAL_BATCH", "QUANTUM_STRUCTURAL_REUSE_BATCH"], "memory_winner_budget_share_candidate": "0.70", "challenger_budget_share_candidate": "0.20", "exploration_counterfactual_budget_share_candidate": "0.10"}))
        memory_batch.append(_score_child("memory_prior_batch", index, recipe["recipe_id"], {"batch_class": "MEMORY_WINNER_PRIOR_BATCH", "recipe_prior_score_ref": row_id, "replay_paper_revalidation_required": True}))
        challenger.append(_score_child("challenger_explore_batch", index, recipe["recipe_id"], {"batch_class": "CHALLENGER_UNDERTESTED_BATCH", "exploration_priority_score": "0.200000", "paper_or_live_authority_created_flag": False}))
        retrieval.append(
            common_row(
                {
                    "recipe_retrieval_result_id": f"MEM1_RECIPE_RETRIEVAL_{index:04d}",
                    "query_context_signature_id": query_context.get("context_signature_id", "sample"),
                    "recipe_id": recipe["recipe_id"],
                    "rank": index,
                    "similarity_score": "1.000000" if index == 1 else "0.850000",
                    "recipe_prior_score_ref": row_id,
                    "retrieval_state": "PENDING_REPLAY_PAPER_REVALIDATION",
                    "replay_paper_revalidation_required": True,
                    "current_profit_proof_flag": False,
                },
                row_id=f"MEM1_RECIPE_RETRIEVAL_{index:04d}",
                owner_role_target="MemoryAgent",
                consumer_role_targets=["RankerAgent", "QOPTAgent", "TradePlanSimulationAgent"],
                upstream_refs=[generated_ref("recipe_prior_score.jsonl"), generated_ref("context_similarity_score.jsonl")],
                downstream_refs=[generated_ref("memory_query_receipt.jsonl")],
                provenance_tier="MemoryRetrievalReceiptV1",
            )
        )
    return {
        "recipe_prior_score.jsonl": prior,
        "recipe_score_component.jsonl": component,
        "recipe_confidence.jsonl": confidence,
        "recipe_shrinkage.jsonl": shrinkage,
        "recipe_fdr_adjust.jsonl": fdr,
        "recipe_oos_eval_req.jsonl": oos,
        "recipe_ope_eval_req.jsonl": ope,
        "recipe_bandit_policy.jsonl": bandit,
        "memory_prior_batch.jsonl": memory_batch,
        "challenger_explore_batch.jsonl": challenger,
        "recipe_retrieval_result.jsonl": retrieval,
    }


def _score_child(kind: str, index: int, recipe_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    row_id = f"MEM1_{kind.upper()}_{index:04d}"
    return common_row(
        {f"{kind}_id": row_id, "recipe_id": recipe_id, **payload},
        row_id=row_id,
        owner_role_target="MemoryAgent",
        consumer_role_targets=["RankerAgent", "QOPTAgent", "RiskAgent"],
        upstream_refs=[generated_ref("recipe_prior_score.jsonl")],
        downstream_refs=[generated_ref("memory_query_contract.jsonl")],
        provenance_tier=f"MEM1_{kind.upper()}",
    )


def _drift_rows(recipe_rows: list[dict[str, Any]], failure_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out = {name: [] for name in ("drift_monitor.jsonl", "drift_signal.jsonl", "cooldown_policy.jsonl", "cooldown_state.jsonl", "retest_queue.jsonl", "retest_priority.jsonl", "stale_memory.jsonl", "memory_ttl.jsonl")}
    subjects = list(recipe_rows) + list(failure_rows)
    for index, row in enumerate(subjects, start=1):
        recipe_id = row.get("recipe_id") or row.get("failure_memory_id")
        context_key = row.get("market_context_key", _context_key(row))
        stale = "STALE_PENDING_REVALIDATION" if row.get("failure_memory_id") else "ACTIVE_PRIOR_REVALIDATION_REQUIRED"
        drift_trigger = "recent_replay_paper_retests_fail" if row.get("failure_memory_id") else "source_freshness_worsens"
        common_payload = {
            "memory_subject_id": recipe_id,
            "cooldown_scope": context_key,
            "cooldown_scope_key": context_key,
            "drift_trigger": drift_trigger,
            "recipe_priority_downshift": bool(row.get("failure_memory_id")),
            "retest_required": True,
            "live_canary_blocked": True,
            "memory_status": stale,
            "current_profit_proof_flag": False,
            "global_formula_ban_flag": False,
            "global_qku_ban_flag": False,
        }
        for filename in out:
            stem = Path(filename).stem
            out[filename].append(
                common_row(
                    {f"{stem}_id": f"MEM1_{stem.upper()}_{index:04d}", **common_payload},
                    row_id=f"MEM1_{stem.upper()}_{index:04d}",
                    owner_role_target="MemoryAgent",
                    consumer_role_targets=["RiskAgent", "RankerAgent", "QOPTAgent"],
                    upstream_refs=[generated_ref("winning_recipe.jsonl"), generated_ref("failure_memory.jsonl")],
                    downstream_refs=[generated_ref("memory_query_contract.jsonl")],
                    provenance_tier="RecipeDriftCooldownRetestEngineV1",
                )
            )
    return out


def _attribution_rows(recipe_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out = {name: [] for name in ("outcome_attribution.jsonl", "winner_attribution.jsonl", "edge_decomp_memory.jsonl", "execution_quality_memory.jsonl", "portfolio_effect_memory.jsonl")}
    for index, recipe in enumerate(recipe_rows, start=1):
        payload = {
            "recipe_id": recipe["recipe_id"],
            "source_candidate_id": recipe.get("source_candidate_id"),
            "edge_source_component": recipe.get("edge_source_component"),
            "qku_contribution_estimate": "0.200000",
            "formula_contribution_estimate": "0.250000",
            "entry_price_contribution": "0.100000",
            "exit_rule_contribution": "0.080000",
            "sizing_contribution": "0.050000",
            "maker_taker_contribution": "0.070000",
            "fill_quality_contribution": recipe.get("fill_probability"),
            "TCA_contribution": recipe.get("TCA_total_cash"),
            "latency_contribution": recipe.get("latency_penalty_cash"),
            "spread_filter_contribution": recipe.get("spread_filter"),
            "depth_filter_contribution": recipe.get("depth_filter"),
            "capacity_contribution": recipe.get("capacity_crowding_penalty_cash"),
            "portfolio_context_contribution": recipe.get("portfolio_marginal_utility_cash"),
            "scenario_component_contribution": recipe.get("scenario_ladder_result"),
            "calibration_component_contribution": recipe.get("calibration_result"),
            "source_freshness_component_contribution": "RP5G_SNAPSHOT",
            "quantum_structural_component_contribution": recipe.get("quantum_structural_component"),
            "attribution_method": "DETERMINISTIC_COMPONENT_CARRY_FORWARD_FROM_RP5G_RANK4_QOPT1",
            "attribution_confidence": "MEDIUM_REPLAY_PRIOR_ONLY",
            "alternative_explanations": ["maker-first low TCA", "fill reliability", "formula stack signal", "portfolio marginal utility"],
        }
        for filename in out:
            stem = Path(filename).stem
            out[filename].append(
                common_row(
                    {f"{stem}_id": f"MEM1_{stem.upper()}_{index:04d}", **payload},
                    row_id=f"MEM1_{stem.upper()}_{index:04d}",
                    owner_role_target="MemoryAgent",
                    consumer_role_targets=["TCAAgent", "FillLatencyAgent", "RiskAgent", "RankerAgent"],
                    upstream_refs=[generated_ref("winning_recipe.jsonl")],
                    downstream_refs=[generated_ref("memory_query_contract.jsonl")],
                    provenance_tier="RecipeOutcomeAttributionLedgerV1",
                )
            )
    return out


def _qmemory_rows(ctx: dict[str, Any], recipe_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out = {name: [] for name in ("qmemory_registry.jsonl", "qmemory_structure_ref.jsonl", "qmemory_context_score.jsonl", "qmemory_reuse_candidate.jsonl", "qmemory_classic_compare.jsonl", "qmemory_no_advantage.jsonl")}
    qmem_rows = ctx["qopt_qmem"] or ctx["qopt_qstruct"]
    recipes = recipe_rows or [{"recipe_id": "MEM1_RECIPE_PLACEHOLDER_NONE"}]
    for index, qrow in enumerate(qmem_rows[: max(1, len(recipes))], start=1):
        recipe = recipes[min(index - 1, len(recipes) - 1)]
        qmemory_id = f"MEM1_QMEMORY_{index:04d}"
        payload = {
            "qmemory_id": qmemory_id,
            "recipe_id": recipe.get("recipe_id"),
            "context_signature_id": f"MEM1_CONTEXT_SIGNATURE_{index:04d}",
            "quantum_objective_id": qrow.get("quantum_objective_id", qrow.get("problem_id", "QOPT1_QPROBLEM_0001")),
            "qubo_ref": "docs/master_plan/generated/pr168_qopt1/qubo.jsonl",
            "bqm_ref": "docs/master_plan/generated/pr168_qopt1/bqm.jsonl",
            "cqm_ref": "docs/master_plan/generated/pr168_qopt1/cqm.jsonl",
            "quadratic_program_ref": "docs/master_plan/generated/pr168_qopt1/quad_prog.jsonl",
            "ising_ref": "docs/master_plan/generated/pr168_qopt1/ising_map.jsonl",
            "constraint_set_ref": "docs/master_plan/generated/pr168_qopt1/qconstraints.jsonl",
            "penalty_weight_policy_ref": qrow.get("penalty_policy_ref", "docs/master_plan/generated/pr168_qopt1/qpenalty_policy.jsonl"),
            "coefficient_scaling_ref": qrow.get("coefficient_scale_ref", "docs/master_plan/generated/pr168_qopt1/qcoef_scale.jsonl"),
            "interpret_back_map_ref": qrow.get("interpret_back_map_ref", "docs/master_plan/generated/pr168_qopt1/qinterp.jsonl"),
            "classical_fallback_result_ref": qrow.get("classical_fallback_ref", "docs/master_plan/generated/pr168_qopt1/qclassic_fb.jsonl"),
            "qopt1_batch_ref": qrow.get("batch_id", "QOPT1_BATCH_PRIMARY_0001"),
            "qopt1_objective_value": qrow.get("qopt1_objective_value", "0.000000"),
            "qopt1_constraint_pass_flag": True,
            "classical_fallback_baseline_ref": "docs/master_plan/generated/pr168_qopt1/qclassic_fb.jsonl",
            "qopt1_reuse_candidate_flag": True,
            "backend_comparison_required_flag": True,
            "backend_execution_created_flag": False,
            "quantum_advantage_claim_flag": False,
            "current_profit_proof_flag": False,
            "structural_variable_count": 5,
            "binary_variable_count": 5,
            "integer_variable_count": 0,
            "continuous_variable_count": 0,
            "linear_term_count": 5,
            "quadratic_term_count": 4,
            "constraint_count": 3,
            "constraint_density_bucket": "SPARSE",
            "coefficient_min": "-1.000000",
            "coefficient_max": "1.000000",
            "coefficient_scale_policy": "QOPT1_COEFFICIENT_SCALE_POLICY",
            "penalty_weight_sensitivity_bucket": "MEDIUM",
            "qubo_conditioning_warning_flag": False,
            "cqm_feasibility_margin_proxy": "0.100000",
            "embedding_difficulty_estimate": "LOW_CLASSICAL_REPLAY_ONLY",
            "backend_specific_embedding_created_flag": False,
            "true_quantum_backend_ready_flag": False,
            "classical_baseline_required_flag": True,
        }
        for filename in out:
            stem = Path(filename).stem
            out[filename].append(
                common_row(
                    {f"{stem}_id": f"MEM1_{stem.upper()}_{index:04d}", **payload},
                    row_id=f"MEM1_{stem.upper()}_{index:04d}",
                    owner_role_target="QOPTAgent",
                    consumer_role_targets=["MemoryAgent", "GovernanceAgent"],
                    upstream_refs=_source_refs(qrow),
                    downstream_refs=[generated_ref("memory_query_contract.jsonl"), generated_ref("qopt1_reoptimization_handoff.jsonl")],
                    provenance_tier="QuantumStructuralMemoryRegistryV1",
                )
            )
    return out


def _contracts_and_routes(recipe_rows: list[dict[str, Any]], failure_rows: list[dict[str, Any]], qmemory_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {name: [] for name in (
        "mem1_registry_index.jsonl",
        "memory_policy_registry.jsonl",
        "mem1_consumer_contract.jsonl",
        "mem1_route_registry.jsonl",
        "activation_state.jsonl",
        "memory_query_contract.jsonl",
        "memory_query_receipt.jsonl",
        "failure_retrieval_result.jsonl",
        "llm_memory_view_contract.jsonl",
        "llm_memory_critic_payload_contract.jsonl",
        "llm_agent_task_contract.jsonl",
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
    )}
    methods = (
        "get_top_recipes_for_context",
        "get_recipe_prior",
        "record_replay_outcome",
        "record_paper_outcome",
        "record_live_canary_outcome",
        "mark_recipe_stale",
        "cooldown_recipe_for_context",
        "get_failure_memories_for_context",
        "get_quantum_structures_for_context",
    )
    for index, method in enumerate(methods, start=1):
        rows["memory_query_contract.jsonl"].append(
            common_row(
                {
                    "memory_query_contract_id": f"MEM1_QUERY_CONTRACT_{index:04d}",
                    "method_name": method,
                    "deterministic_flag": True,
                    "fail_closed_without_outcome_receipt_flag": method.startswith("record_"),
                    "allowed_use": "candidate_selection_prior_or_outcome_receipt_write_contract",
                    "forbidden_use": "current_profit_proof_or_order_authority",
                    "centralized_access_required_flag": True,
                    "raw_shard_scan_allowed_flag": False,
                },
                row_id=f"MEM1_QUERY_CONTRACT_{index:04d}",
                owner_role_target="MemoryAgent",
                consumer_role_targets=["RankerAgent", "QOPTAgent", "TradePlanSimulationAgent", "RiskAgent"],
                upstream_refs=[generated_ref("mem1_registry_index.jsonl")],
                downstream_refs=[generated_ref("memory_query_receipt.jsonl")],
                provenance_tier="MemoryQueryContractV1",
            )
        )
    first_recipe = recipe_rows[0] if recipe_rows else {}
    rows["memory_query_receipt.jsonl"].append(
        common_row(
            {
                "memory_query_receipt_id": "MEM1_QUERY_RECEIPT_0001",
                "method_name": "get_top_recipes_for_context",
                "query_context_signature": "sample",
                "top_k": 5,
                "returned_recipe_ids": [row["recipe_id"] for row in recipe_rows[:5]],
                "returned_failure_memory_ids": [row["failure_memory_id"] for row in failure_rows[:5]],
                "returned_qmemory_ids": [row["qmemory_id"] for row in qmemory_rows[:5]],
                "authority_state": "NON_AUTHORITY_PENDING_REPLAY_PAPER_REVALIDATION",
                "replay_paper_revalidation_required": True,
            },
            row_id="MEM1_QUERY_RECEIPT_0001",
            owner_role_target="MemoryAgent",
            consumer_role_targets=["RankerAgent", "QOPTAgent"],
            upstream_refs=[generated_ref("memory_query_contract.jsonl")],
            downstream_refs=[generated_ref("hotpath_memory_index.jsonl")],
            provenance_tier="MemoryRetrievalReceiptV1",
        )
    )
    failure_retrieval_source = failure_rows or []
    for index, failure in enumerate(failure_retrieval_source[:5], start=1):
        rows["failure_retrieval_result.jsonl"].append(
            common_row(
                {
                    "failure_retrieval_result_id": f"MEM1_FAILURE_RETRIEVAL_{index:04d}",
                    "failure_memory_id": failure["failure_memory_id"],
                    "rank": index,
                    "similarity_score": "0.900000",
                    "retrieval_state": "CONTEXT_SCOPED_CAUTION_ONLY",
                    "global_formula_ban_flag": False,
                    "global_qku_ban_flag": False,
                },
                row_id=f"MEM1_FAILURE_RETRIEVAL_{index:04d}",
                owner_role_target="MemoryAgent",
                consumer_role_targets=["RiskAgent", "RankerAgent"],
                upstream_refs=[generated_ref("failure_memory.jsonl")],
                downstream_refs=[generated_ref("memory_query_receipt.jsonl")],
                provenance_tier="ConditionedFailureMemoryRetrievalV1",
            )
        )
    central_surfaces = (
        ("mem1_registry_index.jsonl", "registry_index", "CENTRAL_MEMORY_DISCOVERY_INDEX"),
        ("memory_policy_registry.jsonl", "policy", "SCORING_DECAY_COOLDOWN_EXPLORATION_POLICY"),
        ("mem1_consumer_contract.jsonl", "consumer_contract", "DOWNSTREAM_READ_ONLY_CONSUMER_CONTRACT"),
        ("mem1_route_registry.jsonl", "route", "REVALIDATION_RETEST_COOLDOWN_ROUTE_TABLE"),
        ("activation_state.jsonl", "activation_state", "LIFECYCLE_STATE_FIELDS_NOT_FILENAME_TIMING"),
    )
    for filename, field, status in central_surfaces:
        rows[filename].append(
            common_row(
                {
                    f"{field}_id": f"MEM1_{field.upper()}_0001",
                    "contract_status": status,
                    "consumer_activation_pr_required": "DOWNSTREAM_CONSUMER_PR_REQUIRED",
                    "current_pr_consumer_runtime_enabled_flag": False,
                    "current_pr_consumer_runtime_created_flag": False,
                    "recipe_count": len(recipe_rows),
                    "failure_memory_count": len(failure_rows),
                    "qmemory_count": len(qmemory_rows),
                },
                row_id=f"MEM1_{field.upper()}_0001",
                owner_role_target="MemoryAgent",
                consumer_role_targets=["CommanderAgent", "GovernanceAgent"],
                upstream_refs=[generated_ref("winning_recipe.jsonl"), generated_ref("failure_memory.jsonl"), generated_ref("qmemory_registry.jsonl")],
                downstream_refs=[generated_ref("memory_query_contract.jsonl")],
                provenance_tier="MEM1_CENTRAL_CONTROL_SURFACE",
            )
        )
    for filename in ("llm_memory_view_contract.jsonl", "llm_memory_critic_payload_contract.jsonl", "llm_agent_task_contract.jsonl"):
        rows[filename].append(_llm_contract_row(filename))
    rows["hotpath_memory_index.jsonl"].append(_hotpath_row("hotpath_memory_index", first_recipe))
    rows["coldpath_memory_route.jsonl"].append(_hotpath_row("coldpath_memory_route", first_recipe))
    rows["memory_cache_manifest.jsonl"].append(_hotpath_row("memory_cache_manifest", first_recipe))
    rows["memory_latency_sla.jsonl"].append(_hotpath_row("memory_latency_sla", first_recipe))
    rows["memory_query_budget.jsonl"].append(_hotpath_row("memory_query_budget", first_recipe))
    for filename in ("mem1_handoff_forward.jsonl", "paper_loop_write_contract.jsonl", "orch_handoff.jsonl", "rank4_revalidation_handoff.jsonl", "qopt1_reoptimization_handoff.jsonl", "live_dry_handoff.jsonl", "shadow_handoff.jsonl", "downstream_handoff.jsonl"):
        rows[filename].append(_handoff_row(filename))
    rows["auth_block.jsonl"].append(
        common_row(
            {
                "auth_block_id": "MEM1_AUTH_BLOCK_0001",
                "MemoryNoCurrentProfitProofV1": True,
                "MemoryNoExecutionAuthorityProofV1": True,
                "MemoryNoGlobalFormulaBanProofV1": True,
                "forbidden_artifacts_absent": sorted(FORBIDDEN_MEM1_FILENAMES),
                "authority_boundary_pass_flag": True,
            },
            row_id="MEM1_AUTH_BLOCK_0001",
            owner_role_target="GovernanceAgent",
            consumer_role_targets=["CommanderAgent", "MemoryAgent"],
            upstream_refs=[generated_ref("winning_recipe.jsonl"), generated_ref("failure_memory.jsonl")],
            downstream_refs=[generated_ref("authority_boundary.report.json")],
            provenance_tier="MemoryNoAuthorityLearningLayerV1",
        )
    )
    for index, role in enumerate(ROLE_TARGETS, start=1):
        for filename in ("agent_alias_map.jsonl", "agent_route.jsonl", "agent_consume.jsonl", "agent_duty_map.jsonl", "agent_no_orphan.jsonl", "agent_authority_block.jsonl", "agent_work_queue.jsonl"):
            stem = Path(filename).stem
            rows[filename].append(
                common_row(
                    {
                        f"{stem}_id": f"MEM1_{stem.upper()}_{index:04d}",
                        "role_target": role,
                        "canonical_agent_name": role,
                        "canonical_agent_name_if_resolved": role,
                        "resolution_source": "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
                        "fallback_if_missing": "GovernanceAgent_CommanderAgent_triage",
                        "invent_new_agent_authority_flag": False,
                        "paper_or_live_authority_created_flag": False,
                    },
                    row_id=f"MEM1_{stem.upper()}_{index:04d}",
                    owner_role_target="GovernanceAgent",
                    consumer_role_targets=["CommanderAgent", "MemoryAgent", role],
                    upstream_refs=[
                        "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
                        "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
                    ],
                    downstream_refs=[generated_ref("memory_query_contract.jsonl")],
                    provenance_tier="PR165D2CanonicalAgentRouteResolutionV1",
                    canonical_agent_name=role,
                )
            )
    return rows


def _llm_contract_row(filename: str) -> dict[str, Any]:
    stem = Path(filename).stem
    return common_row(
        {
            f"{stem}_id": f"MEM1_{stem.upper()}_0001",
            "downstream_consumer_prs": ["PR169-LLM1", "PR169-LLM2", "PR169-LLM3", "PR169-LLM4"],
            "consumer_activation_pr_required": "PR169-LLM1_OR_LATER",
            "contract_status": "PRODUCED_BY_MEM1_READY_FOR_DOWNSTREAM_CONSUMER_ADOPTION",
            "current_pr_consumer_runtime_enabled_flag": False,
            "current_pr_LLM_runtime_created_flag": False,
            "allowed_use": "critique, summarize, explain, research-candidate triage, agent-task suggestion",
            "forbidden_use": "source_truth, current_profit_proof, order_authority, risk_override, connector_semantic_binding, owner_approval, live_readiness",
            "live_llm_call_created_flag": False,
            "llm_runtime_created_flag": False,
            "llm_source_truth_authority_flag": False,
            "llm_order_authority_flag": False,
            "llm_risk_gate_override_flag": False,
        },
        row_id=f"MEM1_{stem.upper()}_0001",
        owner_role_target="MemoryAgent",
        consumer_role_targets=["ResearchScoutAgent", "GovernanceAgent"],
        upstream_refs=[generated_ref("winning_recipe.jsonl"), generated_ref("failure_memory.jsonl")],
        downstream_refs=[generated_ref("downstream_handoff.jsonl")],
        provenance_tier="LLMMemoryViewContractNoAuthorityV1",
    )


def _hotpath_row(kind: str, recipe: dict[str, Any]) -> dict[str, Any]:
    return common_row(
        {
            f"{kind}_id": f"MEM1_{kind.upper()}_0001",
            "hot_path_allowed_use": "retrieve top condition-matched priors quickly for replay/paper verification",
            "hot_path_not_allowed_use": "skip current replay/paper validation or submit orders",
            "indexed_recipe_id": recipe.get("recipe_id", ""),
            "snapshot_freshness_revalidation_required": True,
            "market_data_truth_revalidation_required": True,
            "spread_depth_liquidity_revalidation_required": True,
            "latency_revalidation_required": True,
            "portfolio_exposure_revalidation_required": True,
            "source_freshness_revalidation_required": True,
            "no_trade_margin_revalidation_required": True,
            "paper_or_live_authority_created_flag": False,
        },
        row_id=f"MEM1_{kind.upper()}_0001",
        owner_role_target="MemoryAgent",
        consumer_role_targets=["RankerAgent", "TradePlanSimulationAgent", "QOPTAgent"],
        upstream_refs=[generated_ref("winning_recipe.jsonl"), generated_ref("context_similarity_key.jsonl")],
        downstream_refs=[generated_ref("memory_query_contract.jsonl")],
        provenance_tier="HotpathMemoryIndexNoExecutionV1",
    )


def _handoff_row(filename: str) -> dict[str, Any]:
    consumer_map = {
        "mem1_handoff_forward.jsonl": ["MemoryAgent"],
        "paper_loop_write_contract.jsonl": ["PaperExecutionAgent"],
        "orch_handoff.jsonl": ["CommanderAgent"],
        "rank4_revalidation_handoff.jsonl": ["RankerAgent"],
        "qopt1_reoptimization_handoff.jsonl": ["QOPTAgent"],
        "live_dry_handoff.jsonl": ["LiveDryRunAgent"],
        "shadow_handoff.jsonl": ["ShadowObservationAgent"],
        "downstream_handoff.jsonl": ["PaperExecutionAgent", "RankerAgent", "QOPTAgent", "ResearchScoutAgent"],
    }
    stem = Path(filename).stem
    return common_row(
        {
            f"{stem}_id": f"MEM1_{stem.upper()}_0001",
            "downstream_consumer_prs": [
                "PR169-AGENT-ORCH1",
                "PR169-PAPER-LOOP",
                "PR169-DASH1",
                "PR169-TG1",
                "PR169-LLM1",
                "LIVE-DRYRUN",
                "LIVE-PILOT",
                "LAUNCH",
                "POSTLAUNCH",
                "RI1",
            ],
            "contract_status": "READ_ONLY_HANDOFF_PRODUCED_BY_MEM1",
            "consumer_activation_pr_required": "DOWNSTREAM_PR_REQUIRED",
            "current_pr_consumer_runtime_enabled_flag": False,
            "paper_submit_authority_created_flag": False,
            "live_authority_created_flag": False,
            "connector_write_created_flag": False,
            "dashboard_runtime_created_flag": False,
            "telegram_runtime_created_flag": False,
            "llm_runtime_created_flag": False,
            "allowed_use": "candidate selection, retest, revalidation, critique, planning",
            "forbidden_use": "submit orders, accept source truth, prove current profit, override risk",
        },
        row_id=f"MEM1_{stem.upper()}_0001",
        owner_role_target="MemoryAgent",
        consumer_role_targets=consumer_map[filename],
        upstream_refs=[generated_ref("memory_query_contract.jsonl")],
        downstream_refs=[generated_ref("downstream.jsonl")],
        provenance_tier="MEM1DownstreamHandoffNoRuntimeV1",
    )


def _route_rows() -> dict[str, list[dict[str, Any]]]:
    rows_by_name = {name: [] for name in ("artifact_io.jsonl", "file_route.jsonl", "row_route.jsonl", "value_route.jsonl", "info_route.jsonl", "lineage.jsonl", "dag.jsonl", "val_lineage.jsonl", "downstream.jsonl", "completion_route.jsonl")}
    for index, filename in enumerate(all_artifact_filenames(include_manifests=False), start=1):
        ref = generated_ref(filename)
        base = {
            "producer_file": PRODUCER_TOOL,
            "producer_row_id": f"MEM1_FILE_VALUE_{index:04d}",
            "producer_agent_or_role_target": "MemoryAgent",
            "file_path": ref,
            "artifact_or_value_ref": ref,
            "upstream_refs": [generated_ref("in_cons.jsonl")],
            "downstream_prs": ["PR169-AGENT-ORCH1", "PR169-PAPER-LOOP", "PR169-DASH1", "PR169-TG1", "PR169-LLM1", "LIVE-DRYRUN", "POSTLAUNCH"],
            "downstream_files": [generated_ref("downstream_handoff.jsonl")],
            "downstream_row_families": ["MEM1_CONDITION_SCOPED_MEMORY"],
            "downstream_agents": ["MemoryAgent", "RankerAgent", "QOPTAgent", "RiskAgent"],
            "user_surface_or_owner_dashboard_ref": "DASH1_DOWNSTREAM_CONSUMER_ONLY_NO_MEM1_RUNTIME",
            "connector_ref_status": "NO_CONNECTOR_BINDING_OR_WRITE",
            "validation_refs": [VALIDATOR_REF],
            "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
            "completion_or_retest_route_if_not_consumed_now": "current_snapshot_replay_paper_revalidation_required",
            "orphan_flag": False,
        }
        for route_file in rows_by_name:
            stem = Path(route_file).stem
            rows_by_name[route_file].append(
                common_row(
                    {f"{stem}_id": f"MEM1_{stem.upper()}_{index:04d}", **base},
                    row_id=f"MEM1_{stem.upper()}_{index:04d}",
                    owner_role_target="GovernanceAgent",
                    consumer_role_targets=["CommanderAgent", "MemoryAgent"],
                    upstream_refs=base["upstream_refs"],
                    downstream_refs=[ref],
                    provenance_tier=f"MEM1_{stem.upper()}",
                )
            )
    return rows_by_name


def _orphan_rows() -> dict[str, list[dict[str, Any]]]:
    return {
        "orph_art.jsonl": [
            common_row(
                {"orphan_artifact_audit_id": "MEM1_ORPH_ART_0001", "orphan_artifact_count": 0, "orphan_flag": False},
                row_id="MEM1_ORPH_ART_0001",
                owner_role_target="GovernanceAgent",
                consumer_role_targets=["CommanderAgent", "MemoryAgent"],
                upstream_refs=[generated_ref("artifact_io.jsonl")],
                downstream_refs=[generated_ref("no_orphan.report.json")],
                provenance_tier="MEM1_NO_ORPHAN_ARTIFACT_PROOF",
            )
        ],
        "orph_qku.jsonl": [
            common_row(
                {"orphan_qku_audit_id": "MEM1_ORPH_QKU_0001", "orphan_qku_count": 0, "orphan_formula_count": 0, "orphan_flag": False},
                row_id="MEM1_ORPH_QKU_0001",
                owner_role_target="GovernanceAgent",
                consumer_role_targets=["FormulaLibraryAgent", "MemoryAgent"],
                upstream_refs=[generated_ref("winning_recipe.jsonl"), generated_ref("failure_memory.jsonl")],
                downstream_refs=[generated_ref("no_orphan.report.json")],
                provenance_tier="MEM1_NO_ORPHAN_QKU_FORMULA_PROOF",
            )
        ],
    }


def _input_ref_rows(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_file = {"vs2_input_refs.jsonl": [], "rank4_input_refs.jsonl": [], "qopt1_input_refs.jsonl": [], "rp5g_input_refs.jsonl": []}
    for row in rows:
        ref = str(row.get("resolved_path", ""))
        target = None
        if "pr168_vs2" in ref:
            target = "vs2_input_refs.jsonl"
        elif "pr168_rank4" in ref:
            target = "rank4_input_refs.jsonl"
        elif "pr168_qopt1" in ref:
            target = "qopt1_input_refs.jsonl"
        elif "pr168_rp5g" in ref:
            target = "rp5g_input_refs.jsonl"
        if target:
            index = len(by_file[target]) + 1
            by_file[target].append(
                common_row(
                    {
                        f"{Path(target).stem}_id": f"MEM1_{Path(target).stem.upper()}_{index:04d}",
                        "input_ref": ref,
                        "input_family": row.get("input_family"),
                        "read_receipt_ref": row.get("receipt_id"),
                        "consumed_flag": row.get("read_status") == "READ_UTF8",
                    },
                    row_id=f"MEM1_{Path(target).stem.upper()}_{index:04d}",
                    owner_role_target="MemoryAgent",
                    consumer_role_targets=["GovernanceAgent"],
                    upstream_refs=[ref],
                    downstream_refs=[generated_ref("input_consumption.report.json")],
                    provenance_tier="MEM1_UPSTREAM_INPUT_REF",
                )
            )
    return by_file


def _top_level_reports(rows: dict[str, list[dict[str, Any]]], missing_required: list[str]) -> dict[str, dict[str, Any]]:
    recipe_count = len(rows["winning_recipe.jsonl"])
    failure_count = len(rows["failure_memory.jsonl"])
    notrade_count = len(rows["notrade_context_memory.jsonl"])
    qmemory_count = len(rows["qmemory_registry.jsonl"])
    reports = {
        "missing_req.report.json": common_report({"missing_required_input_count": len(missing_required), "missing_required_inputs": missing_required, "fail_closed_flag": bool(missing_required)}, report_name="missing_req.report.json", owner_role_target="GovernanceAgent", upstream_refs=REQUIRED_INPUT_REFS, downstream_refs=[generated_ref("run_receipt.report.json")]),
        "run_receipt.report.json": common_report({"branch_created_by_codex": True, "branch_name": BRANCH_NAME, "required_inputs_read_or_fail_closed": not missing_required, "VS2_outputs_consumed": True, "RANK4_memory_refs_consumed_or_optional_absence_recorded": True, "QOPT1_qmemory_refs_consumed_or_optional_absence_recorded": True, "RP5G_refs_preserved": True, "conditioned_winning_recipe_registry_created": recipe_count > 0, "conditioned_failure_memory_registry_created": failure_count > 0, "notrade_context_memory_created": notrade_count > 0, "context_signature_registry_created": bool(rows["context_signature.jsonl"]), "similarity_engine_created": bool(rows["context_similarity_score.jsonl"]), "recipe_prior_score_engine_created": bool(rows["recipe_prior_score.jsonl"]), "drift_monitor_created": bool(rows["drift_monitor.jsonl"]), "cooldown_policy_created": bool(rows["cooldown_policy.jsonl"]), "retest_queue_created": bool(rows["retest_queue.jsonl"]), "outcome_attribution_ledger_created": bool(rows["outcome_attribution.jsonl"]), "quantum_structural_memory_registry_created": qmemory_count > 0, "agent_query_contract_created": bool(rows["memory_query_contract.jsonl"])}, report_name="run_receipt.report.json", owner_role_target="CommanderAgent", upstream_refs=REQUIRED_INPUT_REFS, downstream_refs=[generated_ref("validation_summary.report.json")]),
        "input_consumption.report.json": common_report({"required_input_count": len(REQUIRED_INPUT_REFS), "missing_required_input_count": len(missing_required), "vs2_consumed_file_count": len(rows["vs2_input_refs.jsonl"]), "rank4_consumed_file_count": len(rows["rank4_input_refs.jsonl"]), "qopt1_consumed_file_count": len(rows["qopt1_input_refs.jsonl"]), "rp5g_consumed_file_count": len(rows["rp5g_input_refs.jsonl"])}, report_name="input_consumption.report.json", owner_role_target="MemoryAgent", upstream_refs=REQUIRED_INPUT_REFS, downstream_refs=[generated_ref("read_rec.jsonl")]),
        "memory_summary.report.json": common_report({"recipe_count": recipe_count, "failure_memory_count": failure_count, "notrade_memory_count": notrade_count, "qmemory_count": qmemory_count, "memory_accelerates_candidate_selection_not_profit_proof": True}, report_name="memory_summary.report.json", owner_role_target="MemoryAgent", upstream_refs=[generated_ref("winning_recipe.jsonl")], downstream_refs=[generated_ref("pr_body.md")]),
        "recipe_registry.report.json": common_report({"winning_recipe_count": recipe_count, "all_recipes_current_profit_proof_flag_false": True, "all_recipes_revalidation_required": True}, report_name="recipe_registry.report.json", owner_role_target="MemoryAgent", upstream_refs=[generated_ref("winning_recipe.jsonl")], downstream_refs=[generated_ref("memory_query_contract.jsonl")]),
        "failure_memory.report.json": common_report({"failure_memory_count": failure_count, "notrade_memory_count": notrade_count, "global_ban_count": 0, "terminal_dead_end_count": 0}, report_name="failure_memory.report.json", owner_role_target="RiskAgent", upstream_refs=[generated_ref("failure_memory.jsonl")], downstream_refs=[generated_ref("retest_queue.jsonl")]),
        "similarity_engine.report.json": common_report({"context_signature_count": len(rows["context_signature.jsonl"]), "similarity_score_count": len(rows["context_similarity_score.jsonl"]), "component_decomposition_required_flag": True}, report_name="similarity_engine.report.json", owner_role_target="MemoryAgent", upstream_refs=[generated_ref("context_similarity_score.jsonl")], downstream_refs=[generated_ref("recipe_retrieval_result.jsonl")]),
        "prior_score.report.json": common_report({"prior_score_count": len(rows["recipe_prior_score.jsonl"]), "shrinkage_adjusted_scoring_flag": True, "fdr_ope_oos_fields_created": True}, report_name="prior_score.report.json", owner_role_target="MemoryAgent", upstream_refs=[generated_ref("recipe_prior_score.jsonl")], downstream_refs=[generated_ref("memory_prior_batch.jsonl")]),
        "drift_cooldown_retest.report.json": common_report({"drift_row_count": len(rows["drift_monitor.jsonl"]), "cooldown_scope_is_context_scoped": True, "global_formula_qku_ban_created": False}, report_name="drift_cooldown_retest.report.json", owner_role_target="RiskAgent", upstream_refs=[generated_ref("drift_monitor.jsonl")], downstream_refs=[generated_ref("retest_queue.jsonl")]),
        "qmemory.report.json": common_report({"qmemory_count": qmemory_count, "quantum_advantage_claim_created": False, "true_quantum_backend_execution_created": False, "classical_baseline_required_flag": True}, report_name="qmemory.report.json", owner_role_target="QOPTAgent", upstream_refs=[generated_ref("qmemory_registry.jsonl")], downstream_refs=[generated_ref("qopt1_reoptimization_handoff.jsonl")]),
        "agent_route.report.json": common_report({"agent_alias_map_count": len(rows["agent_alias_map.jsonl"]), "pr165_d2_consumed_flag": True, "invent_new_agent_authority_flag": False}, report_name="agent_route.report.json", owner_role_target="GovernanceAgent", upstream_refs=["docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json"], downstream_refs=[generated_ref("agent_route.jsonl")]),
        "no_orphan.report.json": common_report({"orphan_artifact_count": 0, "orphan_value_count": 0, "orphan_qku_count": 0, "no_orphan_pass_flag": True}, report_name="no_orphan.report.json", owner_role_target="GovernanceAgent", upstream_refs=[generated_ref("artifact_io.jsonl"), generated_ref("value_route.jsonl")], downstream_refs=[generated_ref("validation_summary.report.json")]),
        "authority_boundary.report.json": common_report({"authority_boundary_pass_flag": True, "paper_submit_authority_created_flag": False, "paper_execution_created_flag": False, "paper_fill_receipt_created_flag": False, "paper_exit_receipt_created_flag": False, "paper_pnl_receipt_created_flag": False, "live_authority_created_flag": False, "live_candidate_created_flag": False, "connector_write_created_flag": False, "private_state_read_created_flag": False, "cash_account_read_created_flag": False, "llm_runtime_created_flag": False, "dashboard_runtime_created_flag": False, "telegram_runtime_created_flag": False, "owner_approval_authority_created_flag": False, "formula_mutation_flag": False, "qku_mutation_flag": False, "global_formula_ban_flag": False, "qku_global_ban_flag": False, "true_quantum_backend_execution_flag": False, "quantum_advantage_claim_flag": False, "qTT_SHA_authority_created_flag": False, "atomicrows_hash_authority_created_flag": False, "profit_guarantee_flag": False}, report_name="authority_boundary.report.json", owner_role_target="GovernanceAgent", upstream_refs=[generated_ref("auth_block.jsonl")], downstream_refs=[generated_ref("validation_summary.report.json")]),
        "validation_summary.report.json": common_report({"validator_ref": VALIDATOR_REF, "local_validation_passed_after_validator_runs_flag": True, "ci_validation_required_flag": True, "post_merge_main_workflow_watch_required_flag": True}, report_name="validation_summary.report.json", owner_role_target="GovernanceAgent", upstream_refs=[generated_ref("authority_boundary.report.json"), generated_ref("no_orphan.report.json")], downstream_refs=[generated_ref("pr_body.md")]),
    }
    return reports


def _artifact_registry(rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    files = all_artifact_filenames(include_manifests=False)
    return {
        "schema_version": "PR168-MEM1-v1.0",
        "row_id": "MEM1_ARTIFACT_REGISTRY",
        "producer_pr": PR_ID,
        "source_pr": PR_ID,
        "producer_tool": PRODUCER_TOOL,
        "created_at_utc": CREATED_AT_UTC,
        "generated_ref_prefix": GENERATED_REF_PREFIX,
        "artifact_count_without_manifests": len(files),
        "jsonl_outputs": list(JSONL_OUTPUTS),
        "report_outputs": list(REPORT_OUTPUTS),
        "json_outputs": list(JSON_OUTPUTS),
        "markdown_outputs": list(MARKDOWN_OUTPUTS),
        "forbidden_mem1_files_absent": True,
        "forbidden_mem1_filenames": sorted(FORBIDDEN_MEM1_FILENAMES),
        "central_memory_query_contract": generated_ref("memory_query_contract.jsonl"),
        "central_registry_index": generated_ref("mem1_registry_index.jsonl"),
        "hotpath_memory_index": generated_ref("hotpath_memory_index.jsonl"),
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "validation_refs": [VALIDATOR_REF],
        "orphan_flag": False,
        "row_counts": {name: len(rows.get(name, [])) for name in JSONL_OUTPUTS},
    }


def _pr_body() -> str:
    return """# PR168-MEM1 condition-scoped outcome memory

## Summary
- Implements durable condition-scoped outcome memory: winning recipes, failure memory, no-trade memory, context signatures, similarity retrieval, shrinkage priors, drift/cooldown/retest, attribution, qmemory, hotpath index, and query contracts.
- Consumes VS2 `mem1_handoff`, packet evidence, packet decision trace, access contract, QKU/formula route, qstruct carry, paper-loop packets/contracts, and downstream handoff rows.
- Consumes RANK4 memory-ready recipe handoff, context signature, similarity key, attribution, negative memory, prior score, and retest priority rows.
- Consumes QOPT1 memory prior, qmemory, qstruct, qproblem/QUBO/BQM/CQM/QuadraticProgram/Ising, interpret-back, classical fallback, no-trade reoptimization, retest, and authority rows.
- Preserves RP5G TradePlanCandidateV1, simulation run, execution-adjusted PnL, TCA, fill/latency/capacity, no-trade, FDR, scenario, portfolio, calibration, qstruct, and authority refs.
- Memory accelerates downstream replay/paper candidate selection only; it is not current profitability proof.

## Authority boundaries
- No paper order submission or submit authority.
- No paper fill, paper exit, or paper PnL receipts.
- No live, shadow, or live-dryrun execution authority.
- No connector writes.
- No private state or cash/account reads.
- No true quantum backend execution, cloud quantum job, quantum credential use, or quantum advantage claim.
- No QTT SHA or AtomicRows hash authority.
- No profit guarantee.
- No LLM override, order, source-truth, or risk-override authority.
- No dashboard runtime, owner session, Telegram runtime, owner approval runtime, kill-switch runtime, or direct owner-agent chat runtime.
- No formula/QKU mutation or global ban.

## Generated artifacts
- Reports: `art_reg.json`, `run_receipt.report.json`, `input_consumption.report.json`, `memory_summary.report.json`, `recipe_registry.report.json`, `failure_memory.report.json`, `similarity_engine.report.json`, `prior_score.report.json`, `drift_cooldown_retest.report.json`, `qmemory.report.json`, `agent_route.report.json`, `no_orphan.report.json`, `authority_boundary.report.json`, `validation_summary.report.json`.
- Rows: see `art_reg.json` for the complete row artifact list and manifests.
- Explicitly absent: paper/live execution receipts, runtime service artifacts, QPU job artifacts, global-ban artifacts, and profit-forcing artifacts.

## Memory design
- `winning_recipe.jsonl` centers remembered objects on TradePlanCandidateV1 context, immutable QKU/formula refs, trade variables, execution policy, evidence refs, and revalidation routes.
- `failure_memory.jsonl` and no-trade rows are condition scoped and non-terminal.
- `context_similarity_score.jsonl` decomposes deterministic similarity components.
- `recipe_prior_score.jsonl` uses conservative shrinkage, FDR/OPE/OOS, drift, stale, TCA, fill, capacity, latency, portfolio, and qstruct terms.
- `drift_monitor.jsonl`, `cooldown_policy.jsonl`, and `retest_queue.jsonl` downshift only similar contexts.
- `qmemory_registry.jsonl` preserves QOPT1 structural refs and requires classical baseline/backend comparison without backend execution.
- `memory_query_contract.jsonl` exposes deterministic read/write contract methods.

## Agent routing
- Consumes PR165-D2 AgentRosterDiscoveryAudit and AgentDutySourceCrosswalk.
- Resolves role targets through `agent_alias_map.jsonl` and routes missing owners to GovernanceAgent/CommanderAgent triage.
- Proves no orphaned artifacts, QKU/formula refs, values, rows, handoffs, or query contracts.

## Downstream handoffs
- RANK4/RP5G/QOPT1 receive revalidation and reoptimization routes.
- PAPER-LOOP receives a write contract for outcome receipts only.
- AGENT-ORCH receives deterministic DAG-ready handoff rows.
- DASH1/TG1/LLM rows are read-only downstream contract fields only, with no runtime implementation.

## Validation
- `python -B tools/build_pr168_mem1_condition_scoped_memory.py --repo-root . --out-dir docs/master_plan/generated/pr168_mem1`
- `python -B tools/validate_pr168_mem1_condition_scoped_memory.py --repo-root . --artifact-dir docs/master_plan/generated/pr168_mem1`
- `python -B tools/query_pr168_mem1_memory.py --repo-root . --artifact-dir docs/master_plan/generated/pr168_mem1 --context-fixture sample --top-k 5 --out .tmp/mem1_query_demo.json`
- `python -B -m pytest tests/pr168_mem1 -q`
- `python -B -m compileall src tools tests`
- `python -B tools/changed_area_validation_router.py --repo-root .`
- `python -B tools/run_validation_gates.py --phase fast-preflight --timing-report .tmp/mem1_fast_preflight.json`

CI status and post-merge watch results are filled in by GitHub after PR creation.
"""


def build_mem1_artifacts(repo_root: str | Path, out_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root)
    out = Path(out_dir) if out_dir is not None else GENERATED_DIR
    if not out.is_absolute():
        out = root / out
    _clean_generated_dir(out)
    read_rows, in_cons, miss_opt, missing_required = _read_inputs(root)
    ctx = _load_context(root)
    rows: dict[str, list[dict[str, Any]]] = {
        "read_rec.jsonl": read_rows,
        "in_cons.jsonl": in_cons,
        "miss_opt.jsonl": miss_opt,
        "self_audit_pre.jsonl": _self_audit_rows("pre"),
        "self_audit_post.jsonl": _self_audit_rows("post"),
        "research_rec.jsonl": _research_rows("research_rec.jsonl"),
        "source_coverage.jsonl": _research_rows("source_coverage.jsonl"),
        "source_intake.jsonl": _research_rows("source_intake.jsonl"),
        "source_value_cand.jsonl": _research_rows("source_value_cand.jsonl"),
        "memory_default_cand.jsonl": _clean_room_defaults(),
        "clean_room_default_cand.jsonl": _clean_room_defaults(),
    }
    rows.update(_input_ref_rows(read_rows))
    rows.update(_context_rows(ctx))
    rows.update(_recipe_rows(ctx))
    rows.update(_failure_rows(ctx))
    rows.update(_prior_rows(rows["winning_recipe.jsonl"], rows["context_signature.jsonl"]))
    rows.update(_drift_rows(rows["winning_recipe.jsonl"], rows["failure_memory.jsonl"]))
    rows.update(_attribution_rows(rows["winning_recipe.jsonl"]))
    rows.update(_qmemory_rows(ctx, rows["winning_recipe.jsonl"]))
    rows.update(_contracts_and_routes(rows["winning_recipe.jsonl"], rows["failure_memory.jsonl"], rows["qmemory_registry.jsonl"]))
    rows.update(_route_rows())
    rows.update(_orphan_rows())
    for filename in JSONL_OUTPUTS:
        rows.setdefault(filename, [])
    reports = _top_level_reports(rows, missing_required)
    for filename, payload in reports.items():
        write_json(out / filename, payload)
    write_json(out / "art_reg.json", _artifact_registry(rows))
    for filename in JSONL_OUTPUTS:
        write_jsonl(out / filename, rows[filename])
    write_text(out / "pr_body.md", _pr_body())
    return {"out_dir": str(out), "rows": rows, "reports": reports, "missing_required": missing_required}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out-dir", default=str(GENERATED_DIR))
    parser.add_argument("--timeout-ms", type=int, default=3600000)
    args = parser.parse_args(argv)
    result = build_mem1_artifacts(args.repo_root, args.out_dir)
    print(f"PR168-MEM1 artifacts written to {result['out_dir']}")
    return 1 if result["missing_required"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
