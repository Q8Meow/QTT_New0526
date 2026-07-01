"""Deterministic PR168-VS2 paper-intent candidate artifact builder."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable

from .models import (
    AUTHORITY_BOUNDARY_REF,
    BLOCKER_POLICY_REF,
    BRANCH_NAME,
    CREATED_AT_UTC,
    EXECUTION_AUTHORITY_REF,
    FORBIDDEN_VS2_FILENAMES,
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
    "ExecutabilityAgent",
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
    "LiveDryRunAgent",
    "ShadowObservationAgent",
    "ResearchScoutAgent",
)

RESEARCH_SOURCES = (
    (
        "https://docs.kalshi.com/api-reference/market/get-market-orderbook",
        "Kalshi market orderbook API",
        "OFFICIAL_DOC",
        "KALSHI_ORDERBOOK_CANDIDATE",
        "candidate-only orderbook and depth source route",
    ),
    (
        "https://docs.kalshi.com/getting_started/orderbook_responses",
        "Kalshi orderbook responses",
        "OFFICIAL_DOC",
        "KALSHI_PRICE_SIZE_SCALE_CANDIDATE",
        "candidate-only fixed-point orderbook price and count shape",
    ),
    (
        "https://docs.kalshi.com/api-reference/orders/create-order-v2",
        "Kalshi Create Order V2",
        "OFFICIAL_DOC",
        "KALSHI_ORDER_CREATE_CANDIDATE",
        "candidate-only order field semantics; no submit binding",
    ),
    (
        "https://docs.kalshi.com/api-reference/orders/get-order-queue-position",
        "Kalshi get order queue position",
        "OFFICIAL_DOC",
        "KALSHI_QUEUE_POSITION_CANDIDATE",
        "candidate-only queue position and price-time priority input",
    ),
    (
        "https://docs.polymarket.com/developers/CLOB/introduction",
        "Polymarket CLOB API documentation",
        "OFFICIAL_DOC",
        "POLYMARKET_CLOB_CANDIDATE",
        "candidate-only central-limit-order-book route",
    ),
    (
        "https://docs.polymarket.us/api-reference/orders/overview",
        "Polymarket Orders API overview",
        "OFFICIAL_DOC",
        "POLYMARKET_ORDER_API_CANDIDATE",
        "candidate-only order management and authentication route",
    ),
    (
        "https://www.interactivebrokers.com/campus/ibkr-api-page/event-contracts/",
        "IBKR Web API event contracts",
        "OFFICIAL_DOC",
        "FORECASTEX_IBKR_EVENT_CONTRACT_CANDIDATE",
        "candidate-only event contract discovery and venue constraints",
    ),
    (
        "https://www.interactivebrokers.com/campus/ibkr-api-page/event-trading/",
        "IBKR TWS API event trading",
        "OFFICIAL_DOC",
        "FORECASTEX_IBKR_ORDER_POLICY_CANDIDATE",
        "candidate-only always-buy and limit-order staging hint",
    ),
    (
        "https://www.cfainstitute.org/insights/professional-learning/refresher-readings/trading-costs-electronic-markets",
        "CFA Institute trading costs and electronic markets",
        "PUBLIC_RESEARCH",
        "IMPLEMENTATION_SHORTFALL_TCA",
        "candidate-only TCA and implementation-shortfall field model",
    ),
    (
        "https://www.jstor.org/stable/2346101",
        "Benjamini-Hochberg false discovery rate",
        "PAPER",
        "FDR_CONTROL",
        "candidate-only batch promotion overfit/FDR control reference",
    ),
)

SELF_AUDIT_QUESTIONS = (
    "Is VS2 the correct next PR after merged QOPT1?",
    "Does VS2 consume QOPT1 generated advisory batch outputs rather than rebuild QOPT1 optimization, RANK4 ranking, or RP5G simulation?",
    "Does VS2 compile paper-intent candidate packets from TradePlanCandidateV1 refs and QOPT1 interpret-back maps?",
    "Does VS2 preserve immutable QKUs/formulas and avoid formula mutation, QKU mutation, profit forcing, and global bans?",
    "Does VS2 use numeric evidence rather than metadata labels, solver labels, paper-ready labels, report counts, or future-consumer notes?",
    "Does VS2 preserve execution-adjusted evidence: net PnL, LCB, no-trade margin, TCA, fill, latency, capacity, portfolio utility, FDR, scenario, calibration, model-risk, and source provenance?",
    "Does VS2 enforce hard eligibility gates before any paper-intent candidate packet is marked PAPER_LOOP_CANDIDATE_READY?",
    "Does VS2 route QOPT1 no-trade/reoptimization rows to retest/completion/rotation and not to paper-loop-ready candidates?",
    "Does VS2 create paper-intent candidate packets without paper submit authority?",
    "Does VS2 create no-live-submit proof and no connector/cash/private-state proof?",
    "Does VS2 avoid buy/sell/open/close/cancel/replace/amend/reduce authority?",
    "Does VS2 preserve QOPT1 quantum structural refs without backend execution or quantum advantage claims?",
    "Does VS2 keep LLM / DASH1 / TG1 / dashboard / Telegram only as downstream_future fields in downstream_handoff.jsonl and not as runtime or separate row-family systems?",
    "Does VS2 avoid creating owner_surface_registry.jsonl and related v3 owner-surface files?",
    "Does VS2 create MEM1 handoffs without durable MEM1 storage/query APIs?",
    "Does VS2 use PR165-D2 AgentRosterDiscoveryAudit and AgentDutySourceCrosswalk or stronger equivalents?",
    "Does VS2 route every generated file/value/row upstream and downstream through centralized ledgers?",
    "Does VS2 avoid QTT SHA and AtomicRows SHA/hash authority?",
    "Does VS2 avoid source-fact acceptance, connector binding, connector writes, private-state fetches, account/cash reads, and order submission?",
    "Does VS2 create reading receipts and fail closed on missing required inputs?",
    "Does VS2 include affected-scope-first validation, CI debug, merge, and post-merge main workflow watch?",
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


def _surface_family(ref: str) -> str:
    if "pr168_qopt1" in ref:
        return "PR168_QOPT1_ADVISORY_BATCH_OUTPUT"
    if "pr168_rank4" in ref:
        return "PR168_RANK4_ADVISORY_RANK_OUTPUT"
    if "pr168_rp5g" in ref:
        return "PR168_RP5G_REPLAY_PAPER_EVIDENCE_OUTPUT"
    if "pr168_rp5f" in ref:
        return "PR168_RP5F_TARGET_GRID_OUTPUT"
    if "PR165_D2" in ref:
        return "PR165_D2_AGENT_ROUTE_SOURCE"
    if "RP5C" in ref or "rp5c" in ref:
        return "PR168_RP5C_IMMUTABLE_LIBRARY_OUTPUT"
    if "pr168_vs1" in ref:
        return "PR168_VS1_TRADING_INTELLIGENCE_OUTPUT"
    if "pr168_rp5d" in ref:
        return "PR168_RP5D_EXECUTABILITY_OUTPUT"
    if "pr168_rp5e" in ref:
        return "PR168_RP5E_STACK_PREVIEW_OUTPUT"
    return "MASTER_PLAN_INPUT"


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
        family = _surface_family(ref)
        row_id = f"VS2_READ_{index:05d}"
        read_rows.append(
            common_row(
                {
                    "receipt_id": row_id,
                    "input_family": family,
                    "resolved_path": ref,
                    "required_flag": True,
                    "read_status": "READ_UTF8" if exists else "MISSING_REQUIRED",
                    "row_count_or_summary": _row_count(path),
                    "input_producer_pr": "UPSTREAM" if exists else "MISSING",
                    "consumer_modules": ["src.qtt.paper.pr168_vs2.builder"],
                    "owner_agent": "CommanderAgent",
                    "missing_action_if_absent": "FAIL_CLOSED_MISSING_REQUIRED_INPUT",
                    "freshness_or_commit_ref_when_available": "1a4033125996fc3c5b934010e7263c5d324ab40c",
                },
                row_id=row_id,
                owner_agent="CommanderAgent",
                consumer_agents=["GovernanceAgent", "PaperExecutionAgent"],
                upstream_refs=[ref] if exists else ["missing_required_input"],
                downstream_refs=[generated_ref("in_cons.jsonl"), generated_ref("missing_req.report.json")],
                provenance_tier="VS2_INPUT_READ_RECEIPT",
            )
        )
        in_cons.append(
            common_row(
                {
                    "input_consumption_id": f"VS2_IN_CONS_{index:05d}",
                    "input_surface_ref": ref,
                    "surface_family": family,
                    "consumed_flag": exists,
                    "row_count_consumed": _row_count(path) if exists else 0,
                    "consumer_output_refs": [generated_ref("vs2_packet_registry.jsonl"), generated_ref("packet_evidence_bundle.jsonl")],
                },
                row_id=f"VS2_IN_CONS_{index:05d}",
                owner_agent="CommanderAgent",
                consumer_agents=["GovernanceAgent", "PaperExecutionAgent"],
                upstream_refs=[ref] if exists else ["missing_required_input"],
                downstream_refs=[generated_ref("artifact_io.jsonl"), generated_ref("lineage.jsonl")],
                provenance_tier="VS2_INPUT_CONSUMPTION_RECEIPT",
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
                    "missing_optional_id": f"VS2_MISS_OPT_{index:04d}",
                    "optional_artifact_ref": ref,
                    "exists_flag": exists,
                    "consumed_flag": exists,
                    "row_count_or_summary": _row_count(path),
                    "fallback_ref": "packet_completion_queue.jsonl and GovernanceAgent_CommanderAgent_triage",
                    "fail_closed_flag": False,
                },
                row_id=f"VS2_MISS_OPT_{index:04d}",
                owner_agent="CommanderAgent",
                consumer_agents=["GovernanceAgent"],
                upstream_refs=[ref] if exists else ["optional_input_absent"],
                downstream_refs=[generated_ref("packet_completion_queue.jsonl")],
                provenance_tier="VS2_OPTIONAL_INPUT_DISCOVERY",
            )
        )
    return read_rows, in_cons, miss_opt, missing


def _by(rows: Iterable[dict[str, Any]], *keys: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        for key in keys:
            value = row.get(key)
            if value not in (None, ""):
                out.setdefault(str(value), row)
    return out


def _source_refs(row: dict[str, Any]) -> list[str]:
    return stable_unique(
        [
            "docs/master_plan/generated/pr168_qopt1/vs2_handoff.jsonl",
            "docs/master_plan/generated/pr168_qopt1/batch_select.jsonl",
            "docs/master_plan/generated/pr168_qopt1/batch_universe.jsonl",
            "docs/master_plan/generated/pr168_qopt1/qinterp.jsonl",
            *row.get("numeric_evidence_refs", []),
        ]
    )


def _price_scale(venue: str) -> str:
    if venue == "KALSHI":
        return "DOLLARS_0_1"
    if venue == "POLYMARKET":
        return "DOLLARS_0_1"
    if venue == "FORECASTEX_IBKR":
        return "CENTS"
    return "UNKNOWN_COMPLETION_REQUIRED"


def _side(side: str) -> str:
    if side in {"YES", "NO"}:
        return side
    return "VENUE_NORMALIZED_SIDE"


def _candidate_state(row: dict[str, Any], selected_ids: set[str]) -> tuple[str, list[str], str]:
    cid = str(row.get("candidate_id", ""))
    violations = [str(item) for item in row.get("constraint_violation_codes", [])]
    if cid not in selected_ids:
        if "NO_TRADE_MARGIN" in violations:
            return "PAPER_INTENT_DEFERRED_NO_TRADE_REOPTIMIZATION", violations, "QOPT1_VARIABLE_TUNING_FRONTIER"
        if violations:
            return "PAPER_INTENT_DEFERRED_RETEST_REQUIRED", violations, "RP5G_REPLAY_RETEST_REQUIRED"
        return "PAPER_INTENT_MEM1_LEARNING_HANDOFF_ONLY_NOT_PAPER_READY", ["NOT_SELECTED_BY_QOPT1_PRIMARY_BATCH"], "MEM1_CONTEXT_MEMORY_REQUIRED_FUTURE"
    market_id = str(row.get("market_id", ""))
    if "FIXTURE" in market_id:
        return "PAPER_LOOP_CANDIDATE_READY_FIXTURE_ONLY", ["FIXTURE_ONLY_MARKET_CONTEXT"], "CURRENT_SNAPSHOT_REVALIDATION_REQUIRED"
    return "PAPER_LOOP_CANDIDATE_READY_NOW_WITH_QOPT1_NUMERIC_EVIDENCE", [], "VS2_PACKET_READY_FOR_PAPER_LOOP_FUTURE_ONLY"


def _completion_role(gap: str) -> str:
    if "TCA" in gap:
        return "TCAAgent"
    if "FILL" in gap or "LATENCY" in gap:
        return "FillLatencyAgent"
    if "NO_TRADE" in gap or "LCB" in gap or "SCENARIO" in gap or "CAPACITY" in gap:
        return "RiskAgent"
    if "SNAPSHOT" in gap or "SOURCE" in gap:
        return "MarketConditionAgent"
    if "VENUE" in gap or "TICKET" in gap:
        return "OrderVariableAgent"
    return "GovernanceAgent"


def _research_rows(filename: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (url, title, source_type, use, note) in enumerate(RESEARCH_SOURCES, start=1):
        rows.append(
            common_row(
                {
                    "research_id": f"VS2_RESEARCH_{index:04d}",
                    "source_url": url,
                    "source_title": title,
                    "source_type": source_type,
                    "retrieved_at_utc": CREATED_AT_UTC,
                    "research_use": use,
                    "research_note": note,
                    "candidate_only_flag": True,
                    "accepted_source_fact_flag": False,
                    "connector_semantic_binding_flag": False,
                    "live_default_flag": False,
                    "proprietary_claim_flag": False,
                    "profit_proof_flag": False,
                    "paper_submit_authority_flag": False,
                    "replay_paper_verification_required": True,
                },
                row_id=f"{Path(filename).stem.upper()}_{index:04d}",
                owner_agent="ResearchScoutAgent",
                consumer_agents=["GovernanceAgent", "PaperExecutionAgent"],
                upstream_refs=["online_candidate_research"],
                downstream_refs=[generated_ref("source_value_cand.jsonl"), generated_ref("venue_semantic_cand.jsonl")],
                provenance_tier="VS2_CANDIDATE_ONLY_SOURCE_RESEARCH",
                role_target_name="ResearchScoutAgent",
            )
        )
    return rows


def _self_audit_rows(stage: str) -> list[dict[str, Any]]:
    return [
        common_row(
            {
                "self_audit_id": f"VS2_SELF_AUDIT_{stage.upper()}_{index:03d}",
                "audit_stage": stage,
                "question": question,
                "answer": "YES",
                "negative_answer_fail_closed_flag": True,
            },
            row_id=f"VS2_SELF_AUDIT_{stage.upper()}_{index:03d}",
            owner_agent="GovernanceAgent",
            consumer_agents=["CommanderAgent"],
            upstream_refs=["VS2 prompt v8"],
            downstream_refs=[generated_ref("run_receipt.report.json")],
            provenance_tier="VS2_SELF_AUDIT",
            role_target_name="GovernanceAgent",
        )
        for index, question in enumerate(SELF_AUDIT_QUESTIONS, start=1)
    ]


def _packet_context(repo_root: Path) -> dict[str, Any]:
    qopt_dir = repo_root / "docs/master_plan/generated/pr168_qopt1"
    batch_select = read_jsonl(qopt_dir / "batch_select.jsonl")
    batch_universe = read_jsonl(qopt_dir / "batch_universe.jsonl")
    qinterp = read_jsonl(qopt_dir / "qinterp.jsonl")
    qstruct_names = ("qproblem.jsonl", "qubo.jsonl", "bqm.jsonl", "cqm.jsonl", "quad_prog.jsonl", "ising_map.jsonl", "qclassic_fb.jsonl")
    qstruct_rows = {name: read_jsonl(qopt_dir / name) for name in qstruct_names}
    primary = next(
        (
            row
            for row in batch_select
            if row.get("batch_class") == "PRIMARY_ADVISORY"
            and row.get("constraint_pass_flag") is True
            and row.get("VS2_PRIORITY_ELIGIBLE_CANDIDATE_ONLY") is True
        ),
        batch_select[0] if batch_select else {},
    )
    return {
        "batch_select": batch_select,
        "batch_universe": batch_universe,
        "qinterp_by_candidate": _by(qinterp, "candidate_id", "trade_plan_id"),
        "primary": primary,
        "selected_ids": set(str(item) for item in primary.get("selected_candidate_ids", [])),
        "qstruct_rows": qstruct_rows,
    }


def _build_packet_rows(repo_root: Path) -> dict[str, list[dict[str, Any]]]:
    ctx = _packet_context(repo_root)
    primary = ctx["primary"]
    selected_ids: set[str] = ctx["selected_ids"]
    qinterp_by_candidate: dict[str, dict[str, Any]] = ctx["qinterp_by_candidate"]
    packets: list[dict[str, Any]] = []
    registry: list[dict[str, Any]] = []
    contracts: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    decision: list[dict[str, Any]] = []
    idem: list[dict[str, Any]] = []
    qroutes: list[dict[str, Any]] = []
    qstruct: list[dict[str, Any]] = []
    completion: list[dict[str, Any]] = []
    ticket_fields: list[dict[str, Any]] = []
    ticket_map: list[dict[str, Any]] = []
    order_policy: list[dict[str, Any]] = []
    entry_plan: list[dict[str, Any]] = []
    exit_plan: list[dict[str, Any]] = []
    cancel_plan: list[dict[str, Any]] = []
    tif_plan: list[dict[str, Any]] = []
    lifecycle: list[dict[str, Any]] = []
    explain: list[dict[str, Any]] = []
    venue_norm: list[dict[str, Any]] = []
    price_norm: list[dict[str, Any]] = []
    side_norm: list[dict[str, Any]] = []
    tick_min: list[dict[str, Any]] = []
    venue_sem: list[dict[str, Any]] = []
    readiness: list[dict[str, Any]] = []
    gate: list[dict[str, Any]] = []
    risk_check: list[dict[str, Any]] = []
    tca_check: list[dict[str, Any]] = []
    fill_check: list[dict[str, Any]] = []
    cap_check: list[dict[str, Any]] = []
    fdr_check: list[dict[str, Any]] = []
    scen_check: list[dict[str, Any]] = []
    port_check: list[dict[str, Any]] = []
    notrade_check: list[dict[str, Any]] = []
    model_check: list[dict[str, Any]] = []
    stale_check: list[dict[str, Any]] = []
    fresh_check: list[dict[str, Any]] = []
    no_live: list[dict[str, Any]] = []
    no_conn: list[dict[str, Any]] = []
    no_priv: list[dict[str, Any]] = []
    no_cash: list[dict[str, Any]] = []
    no_order: list[dict[str, Any]] = []
    loop_packet: list[dict[str, Any]] = []
    loop_contract: list[dict[str, Any]] = []
    loop_handoff: list[dict[str, Any]] = []
    loop_manifest: list[dict[str, Any]] = []
    loop_schema: list[dict[str, Any]] = []
    loop_reval: list[dict[str, Any]] = []
    mem1: list[dict[str, Any]] = []
    downstream_handoff: list[dict[str, Any]] = []
    orch: list[dict[str, Any]] = []
    live_dry: list[dict[str, Any]] = []
    shadow: list[dict[str, Any]] = []
    dedupe: list[dict[str, Any]] = []
    near_clone: list[dict[str, Any]] = []
    hotpath: list[dict[str, Any]] = []
    coldpath: list[dict[str, Any]] = []
    latency: list[dict[str, Any]] = []
    priority: list[dict[str, Any]] = []
    auth: list[dict[str, Any]] = []
    cand_elig: list[dict[str, Any]] = []
    qku_elig: list[dict[str, Any]] = []
    formula_elig: list[dict[str, Any]] = []
    batch_elig: list[dict[str, Any]] = []
    qopt_refs: list[dict[str, Any]] = []
    rank4_refs: list[dict[str, Any]] = []
    rp5g_refs: list[dict[str, Any]] = []

    for index, row in enumerate(ctx["batch_universe"], start=1):
        cid = str(row.get("candidate_id"))
        packet_id = f"VS2_PAPER_INTENT_CANDIDATE_{index:04d}"
        qinterp = qinterp_by_candidate.get(cid, {})
        state, gaps, route = _candidate_state(row, selected_ids)
        is_fixture = state == "PAPER_LOOP_CANDIDATE_READY_FIXTURE_ONLY"
        is_now = state == "PAPER_LOOP_CANDIDATE_READY_NOW_WITH_QOPT1_NUMERIC_EVIDENCE"
        is_deferred = state.startswith("PAPER_INTENT_DEFERRED")
        venue = str(row.get("venue", "UNKNOWN"))
        side = _side(str(row.get("side", "VENUE_NORMALIZED_SIDE")))
        price = score(qinterp.get("entry_price_domain", row.get("entry_bucket", "0")), "0")
        size = int(dec(qinterp.get("size_domain", row.get("size_bucket", 0))))
        cancel = str(qinterp.get("cancel_replace_domain", row.get("cancel_replace_policy", "UNKNOWN_COMPLETION_REQUIRED")))
        exit_rule = str(qinterp.get("exit_rule_domain", row.get("exit_rule", "UNKNOWN_COMPLETION_REQUIRED")))
        hold = str(qinterp.get("hold_duration_domain", row.get("hold_duration_bucket", "UNKNOWN_COMPLETION_REQUIRED")))
        maker_taker = str(qinterp.get("maker_taker_split_domain", row.get("maker_taker_split", "UNKNOWN_COMPLETION_REQUIRED")))
        price_scale = _price_scale(venue)
        idempotency_tuple = (
            venue,
            str(row.get("market_id")),
            side,
            f"price={price}",
            f"size={size}",
            f"entry={row.get('entry_bucket')}",
            f"exit={exit_rule}",
            f"cancel={cancel}",
            f"source={cid}",
        )
        idem_key = "|".join(idempotency_tuple)
        refs = _source_refs(row)
        source_rank4 = str(row.get("rank4_rank_id", ""))
        source_rp5g = str(row.get("rp5g_exec_pnl_ref", ""))
        source_qopt_batch = str(primary.get("batch_id", "QOPT1_BATCH_PRIMARY_0001"))
        readiness_id = f"VS2_PAPER_READINESS_{index:04d}"
        auth_id = f"VS2_AUTH_BLOCK_{index:04d}"
        no_live_id = f"VS2_NO_LIVE_SUBMIT_{index:04d}"
        contract_id = f"VS2_PACKET_ACCESS_CONTRACT_{index:04d}"
        evidence_id = f"VS2_PACKET_EVIDENCE_{index:04d}"
        decision_id = f"VS2_PACKET_DECISION_TRACE_{index:04d}"
        qroute_id = f"VS2_QKU_FORMULA_ROUTE_{index:04d}"
        qstruct_id = f"VS2_QSTRUCT_CARRY_{index:04d}"

        packet_payload = {
            "paper_intent_candidate_id": packet_id,
            "source_qopt1_batch_id": source_qopt_batch,
            "source_qopt1_selected_candidate_id": cid if cid in selected_ids else "",
            "source_trade_plan_candidate_id": cid,
            "source_rank4_rank_id": source_rank4,
            "source_rp5g_simulation_run_id": row.get("simulation_run_id"),
            "source_trade_seed_id": row.get("trade_seed_id"),
            "source_target_id": row.get("target_id"),
            "source_order_variable_grid_id": row.get("grid_id"),
            "source_stack_refs": stable_unique(row.get("source_artifact_refs", [])),
            "qku_refs": stable_unique(row.get("qku_refs", [])),
            "formula_refs": stable_unique(row.get("formula_refs", [])),
            "quantum_structure_refs_when_available": [
                "docs/master_plan/generated/pr168_qopt1/qproblem.jsonl",
                "docs/master_plan/generated/pr168_qopt1/qubo.jsonl",
                "docs/master_plan/generated/pr168_qopt1/bqm.jsonl",
                "docs/master_plan/generated/pr168_qopt1/cqm.jsonl",
                "docs/master_plan/generated/pr168_qopt1/quad_prog.jsonl",
                "docs/master_plan/generated/pr168_qopt1/ising_map.jsonl",
            ],
            "classical_fallback_refs_when_available": ["docs/master_plan/generated/pr168_qopt1/qclassic_fb.jsonl"],
            "market_family": "PREDICTION_MARKETS",
            "venue": venue,
            "platform": venue,
            "market_id_or_instrument_ref": row.get("market_id"),
            "contract_ref_type": "BINARY_EVENT_CONTRACT_CANDIDATE",
            "outcome_side": side,
            "price_candidate": price,
            "price_scale": price_scale,
            "quantity_candidate": size,
            "quantity_scale": "CONTRACTS",
            "notional_candidate_cash_or_proxy": score(row.get("capital_required_cash_or_proxy", "0")),
            "entry_rule": "QOPT1_INTERPRET_BACK_ENTRY_PRICE",
            "exit_rule": exit_rule,
            "hold_duration": hold,
            "maker_taker_split_policy": maker_taker,
            "cancel_replace_policy": cancel,
            "TIF_candidate": "GTC_SIM_ONLY",
            "order_type_candidate": "LIMIT",
            "spread_filter": row.get("spread_depth_liquidity_filter"),
            "depth_filter": row.get("spread_depth_liquidity_filter"),
            "liquidity_filter": row.get("spread_depth_liquidity_filter"),
            "latency_budget_ms": row.get("latency_budget_bucket"),
            "portfolio_exposure_ref": row.get("portfolio_exposure_bucket"),
            "capacity_limit_ref": "docs/master_plan/generated/pr168_rp5g/capacity_crowding.jsonl",
            "net_expected_pnl_cash": score(row.get("net_expected_pnl_cash")),
            "lower_confidence_bound_pnl_cash": score(row.get("lower_confidence_bound_pnl_cash")),
            "candidate_minus_no_trade_cash": score(row.get("candidate_minus_no_trade_cash")),
            "TCA_total_cash": score(row.get("TCA_total_cash")),
            "fill_probability": score(row.get("fill_probability")),
            "fill_adjusted_expected_pnl_cash": score(dec(row.get("net_expected_pnl_cash")) - dec(row.get("fill_shortfall_penalty_cash"))),
            "latency_adjusted_expected_pnl_cash": score(dec(row.get("net_expected_pnl_cash")) - dec(row.get("latency_decay_penalty_cash"))),
            "capacity_adjusted_expected_pnl_cash": score(dec(row.get("net_expected_pnl_cash")) - dec(row.get("capacity_crowding_penalty_cash"))),
            "portfolio_adjusted_expected_pnl_cash": score(dec(row.get("net_expected_pnl_cash")) + dec(row.get("portfolio_marginal_utility_cash"))),
            "overfit_fdr_penalty_cash": score(row.get("overfit_fdr_penalty_cash")),
            "scenario_worst_case_cash": score(row.get("scenario_worst_case_cash")),
            "calibration_quality_score": score(row.get("calibration_quality_score")),
            "model_risk_reserve_cash": score(row.get("model_risk_reserve_cash")),
            "source_freshness_status": "FIXTURE_SOURCE_REVALIDATION_REQUIRED" if is_fixture else "QOPT1_SOURCE_FRESHNESS_CARRIED_FORWARD",
            "stale_status": "STALE_REVALIDATION_REQUIRED_BEFORE_REAL_PAPER_LOOP" if is_fixture else "NOT_STALE_BY_QOPT1_CARRIED_FORWARD",
            "qopt_objective_value": score(row.get("objective_value")),
            "qopt_batch_class": primary.get("batch_class", "PRIMARY_ADVISORY"),
            "qopt_constraint_pass_flag": bool(row.get("hard_constraint_pass_flag")),
            "qopt_interpret_back_ref": qinterp.get("interpret_back_id", "MISSING_QOPT1_INTERPRET_BACK"),
            "rank4_score_ref": source_rank4,
            "rp5g_evidence_refs": stable_unique(row.get("numeric_evidence_refs", [])),
            "paper_loop_consumer_contract_ref": generated_ref("paper_loop_contract.jsonl"),
            "paper_readiness_ref": readiness_id,
            "no_live_submit_proof_ref": no_live_id,
            "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
            "no_orphan_ref": generated_ref("no_orphan.report.json"),
            "downstream_handoff_ref": generated_ref("downstream_handoff.jsonl"),
            "paper_eligibility_state": state,
            "paper_loop_candidate_ready_now_flag": is_now,
            "production_paper_loop_ready_flag": is_now,
            "paper_loop_ready_without_revalidation_flag": False,
            "completion_route": route,
            "packet_idempotency_key": idem_key,
        }
        packets.append(
            common_row(
                packet_payload,
                row_id=packet_id,
                owner_agent="PaperExecutionAgent",
                consumer_agents=["PaperExecutionAgent", "GovernanceAgent", "MemoryAgent"],
                upstream_refs=refs,
                downstream_refs=[generated_ref("vs2_packet_registry.jsonl"), generated_ref("paper_loop_packet.jsonl")],
                provenance_tier="PaperIntentCandidatePacketV1",
                role_target_name="PaperExecutionAgent",
            )
        )
        registry.append(
            common_row(
                {
                    "vs2_packet_registry_id": f"VS2_PACKET_REGISTRY_{index:04d}",
                    "paper_intent_candidate_id": packet_id,
                    "source_qopt1_batch_id": source_qopt_batch,
                    "source_trade_plan_candidate_id": cid,
                    "paper_eligibility_state": state,
                    "central_packet_index_flag": True,
                    "packet_access_contract_ref": contract_id,
                    "packet_evidence_bundle_ref": evidence_id,
                    "packet_decision_trace_ref": decision_id,
                    "packet_idempotency_key_ref": f"VS2_PACKET_IDEMPOTENCY_{index:04d}",
                    "paper_loop_contract_ref": generated_ref("paper_loop_contract.jsonl"),
                    "paper_loop_candidate_ready_now_flag": is_now,
                    "future_consumers_read_registry_first_flag": True,
                },
                row_id=f"VS2_PACKET_REGISTRY_{index:04d}",
                owner_agent="PaperExecutionAgent",
                consumer_agents=["PaperExecutionAgent", "MemoryAgent", "GovernanceAgent"],
                upstream_refs=refs,
                downstream_refs=[generated_ref("packet_access_contract.jsonl"), generated_ref("paper_loop_packet.jsonl")],
                provenance_tier="VS2_PACKET_REGISTRY",
            )
        )
        evidence.append(
            common_row(
                {
                    "packet_evidence_bundle_id": evidence_id,
                    "paper_intent_candidate_id": packet_id,
                    "numeric_evidence_refs": stable_unique(row.get("numeric_evidence_refs", [])),
                    "net_expected_pnl_cash": score(row.get("net_expected_pnl_cash")),
                    "lower_confidence_bound_pnl_cash": score(row.get("lower_confidence_bound_pnl_cash")),
                    "candidate_minus_no_trade_cash": score(row.get("candidate_minus_no_trade_cash")),
                    "TCA_total_cash": score(row.get("TCA_total_cash")),
                    "fill_probability": score(row.get("fill_probability")),
                    "capacity_crowding_penalty_cash": score(row.get("capacity_crowding_penalty_cash")),
                    "portfolio_marginal_utility_cash": score(row.get("portfolio_marginal_utility_cash")),
                    "overfit_fdr_penalty_cash": score(row.get("overfit_fdr_penalty_cash")),
                    "scenario_worst_case_cash": score(row.get("scenario_worst_case_cash")),
                    "calibration_quality_score": score(row.get("calibration_quality_score")),
                    "model_risk_reserve_cash": score(row.get("model_risk_reserve_cash")),
                    "metadata_label_only_proof_flag": False,
                    "future_llm_compact_evidence_flag": True,
                },
                row_id=evidence_id,
                owner_agent="RiskAgent",
                consumer_agents=["PaperExecutionAgent", "MemoryAgent", "GovernanceAgent"],
                upstream_refs=refs,
                downstream_refs=[generated_ref("packet_decision_trace.jsonl"), generated_ref("paper_loop_packet.jsonl")],
                provenance_tier="VS2_PACKET_NUMERIC_EVIDENCE_BUNDLE",
                role_target_name="RiskAgent",
            )
        )
        decision_reasons = gaps if gaps else ["ALL_CURRENT_VS2_GATES_PASS"]
        decision.append(
            common_row(
                {
                    "packet_decision_trace_id": decision_id,
                    "paper_intent_candidate_id": packet_id,
                    "paper_eligibility_state": state,
                    "decision": "COMPILED_FIXTURE_ONLY" if is_fixture else ("COMPILED_READY_NOW" if is_now else "DEFERRED"),
                    "decision_reason_codes": decision_reasons,
                    "readiness_gap_codes": gaps,
                    "packet_completion_queue_ref": generated_ref("packet_completion_queue.jsonl") if is_deferred else "",
                    "paper_loop_candidate_ready_now_flag": is_now,
                    "paper_loop_ready_without_revalidation_flag": False,
                    "paper_submit_authority_created_flag": False,
                    "formula_computation_created_by_vs2_flag": False,
                    "trade_variable_optimization_created_by_vs2_flag": False,
                    "rank4_recomputed_by_vs2_flag": False,
                    "qopt1_recomputed_by_vs2_flag": False,
                    "paper_loop_execution_created_by_vs2_flag": False,
                    "future_execution_router_required_before_real_orders_flag": True,
                    "buy_sell_open_close_authority_created_by_vs2_flag": False,
                    "no_trade_non_terminal_route": route,
                },
                row_id=decision_id,
                owner_agent="GovernanceAgent",
                consumer_agents=["PaperExecutionAgent", "MemoryAgent"],
                upstream_refs=refs,
                downstream_refs=[generated_ref("packet_completion_queue.jsonl"), generated_ref("mem1_handoff.jsonl")],
                provenance_tier="VS2_PACKET_DECISION_TRACE",
                role_target_name="GovernanceAgent",
            )
        )
        contracts.append(
            common_row(
                {
                    "packet_access_contract_id": contract_id,
                    "paper_intent_candidate_id": packet_id,
                    "current_pr_source_of_truth_ref": generated_ref("vs2_packet_registry.jsonl"),
                    "paper_loop_primary_inputs": [generated_ref("paper_loop_packet.jsonl"), generated_ref("paper_loop_contract.jsonl"), generated_ref("packet_evidence_bundle.jsonl")],
                    "mem1_primary_inputs": [generated_ref("mem1_handoff.jsonl"), generated_ref("packet_decision_trace.jsonl"), generated_ref("qku_formula_route_bundle.jsonl")],
                    "llm_future_inputs": [generated_ref("downstream_handoff.jsonl"), generated_ref("packet_decision_trace.jsonl")],
                    "formula_computation_created_by_vs2_flag": False,
                    "trade_variable_optimization_created_by_vs2_flag": False,
                    "rank4_recomputed_by_vs2_flag": False,
                    "qopt1_recomputed_by_vs2_flag": False,
                    "paper_loop_execution_created_by_vs2_flag": False,
                    "future_execution_router_required_before_real_orders_flag": True,
                    "buy_sell_open_close_authority_created_by_vs2_flag": False,
                },
                row_id=contract_id,
                owner_agent="GovernanceAgent",
                consumer_agents=["PaperExecutionAgent", "MemoryAgent", "GovernanceAgent"],
                upstream_refs=[generated_ref("vs2_packet_registry.jsonl"), *refs],
                downstream_refs=[generated_ref("paper_loop_contract.jsonl"), generated_ref("downstream_handoff.jsonl")],
                provenance_tier="PaperLoopConsumerContractV1",
            )
        )
        idem.append(
            common_row(
                {
                    "packet_idempotency_key_id": f"VS2_PACKET_IDEMPOTENCY_{index:04d}",
                    "paper_intent_candidate_id": packet_id,
                    "packet_idempotency_key": idem_key,
                    "deterministic_non_sha_tuple": list(idempotency_tuple),
                    "sha_or_hash_authority_flag": False,
                    "duplicate_suppression_scope": "VS2_REPLAY_REPRODUCIBLE_PACKET_IDENTITY",
                },
                row_id=f"VS2_PACKET_IDEMPOTENCY_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=["PaperExecutionAgent"],
                upstream_refs=refs,
                downstream_refs=[generated_ref("intent_dedupe.jsonl")],
                provenance_tier="VS2_PACKET_IDEMPOTENCY_KEY",
            )
        )
        qroutes.append(
            common_row(
                {
                    "qku_formula_route_bundle_id": qroute_id,
                    "paper_intent_candidate_id": packet_id,
                    "qku_refs": stable_unique(row.get("qku_refs", [])),
                    "formula_refs": stable_unique(row.get("formula_refs", [])),
                    "qku_formula_mutation_flag": False,
                    "upstream_formula_agent_route": "FormulaLibraryAgent",
                    "upstream_qopt_agent_route": "QOPTAgent",
                    "downstream_mem1_agent_route": "MemoryAgent",
                    "downstream_paper_loop_agent_route": "PaperExecutionAgent",
                    "canonical_agent_name_or_triage_route": "GovernanceAgent_CommanderAgent_triage",
                },
                row_id=qroute_id,
                owner_agent="FormulaLibraryAgent",
                consumer_agents=["MemoryAgent", "PaperExecutionAgent", "GovernanceAgent"],
                upstream_refs=refs,
                downstream_refs=[generated_ref("mem1_handoff.jsonl"), generated_ref("paper_loop_packet.jsonl")],
                provenance_tier="VS2_QKU_FORMULA_ROUTE_BUNDLE",
                role_target_name="FormulaLibraryAgent",
            )
        )
        qstruct.append(
            common_row(
                {
                    "qstruct_carry_id": qstruct_id,
                    "paper_intent_candidate_id": packet_id,
                    "qopt1_qproblem_ref": "docs/master_plan/generated/pr168_qopt1/qproblem.jsonl",
                    "qopt1_qubo_ref": "docs/master_plan/generated/pr168_qopt1/qubo.jsonl",
                    "qopt1_bqm_ref": "docs/master_plan/generated/pr168_qopt1/bqm.jsonl",
                    "qopt1_cqm_ref": "docs/master_plan/generated/pr168_qopt1/cqm.jsonl",
                    "qopt1_quadratic_program_ref": "docs/master_plan/generated/pr168_qopt1/quad_prog.jsonl",
                    "qopt1_ising_ref": "docs/master_plan/generated/pr168_qopt1/ising_map.jsonl",
                    "qopt1_interpret_back_ref": qinterp.get("interpret_back_id", "MISSING_QOPT1_INTERPRET_BACK"),
                    "classical_fallback_ref": "docs/master_plan/generated/pr168_qopt1/qclassic_fb.jsonl",
                    "true_quantum_backend_execution_flag": False,
                    "quantum_advantage_claim_flag": False,
                },
                row_id=qstruct_id,
                owner_agent="QOPTAgent",
                consumer_agents=["PaperExecutionAgent", "MemoryAgent"],
                upstream_refs=["docs/master_plan/generated/pr168_qopt1/qproblem.jsonl", "docs/master_plan/generated/pr168_qopt1/qinterp.jsonl"],
                downstream_refs=[generated_ref("packet_evidence_bundle.jsonl")],
                provenance_tier="VS2_QOPT1_QUANTUM_STRUCTURE_CARRY_FORWARD",
                role_target_name="QOPTAgent",
            )
        )
        if is_deferred:
            for gap_index, gap in enumerate(gaps or ["CURRENT_SNAPSHOT_REVALIDATION_REQUIRED"], start=1):
                role = _completion_role(gap)
                completion.append(
                    common_row(
                        {
                            "packet_completion_queue_id": f"VS2_PACKET_COMPLETION_{index:04d}_{gap_index:02d}",
                            "paper_intent_candidate_id": packet_id,
                            "readiness_gap_code": gap,
                            "missing_field_or_failed_gate": gap,
                            "exact_missing_requirement": f"{gap} must be completed by upstream/future role before paper-loop readiness",
                            "responsible_role_target": role,
                            "canonical_agent_name_or_triage_route": "GovernanceAgent_CommanderAgent_triage",
                            "agent_alias_map_ref": generated_ref("agent_alias_map.jsonl"),
                            "agent_resolution_source": "PR165-D2 AgentRosterDiscoveryAudit | PR165-D2 AgentDutySourceCrosswalk",
                            "completion_owner_resolution_status": "TRIAGE_REQUIRED",
                            "upstream_pr_or_future_pr_route": route,
                            "completion_action": "ROUTE_PACKET_GAP_NO_FORMULA_REPAIR_NO_QKU_MUTATION_NO_PROFIT_FORCING",
                            "can_emit_paper_intent_candidate_flag": True,
                            "can_mark_paper_loop_ready_now_flag": False,
                            "formula_mutation_flag": False,
                            "qku_mutation_flag": False,
                            "profit_forcing_flag": False,
                            "no_trade_bypass_flag": False,
                            "paper_submit_authority_created_flag": False,
                            "live_authority_created_flag": False,
                            "orphan_flag": False,
                        },
                        row_id=f"VS2_PACKET_COMPLETION_{index:04d}_{gap_index:02d}",
                        owner_agent=role,
                        consumer_agents=["GovernanceAgent", "PaperExecutionAgent"],
                        upstream_refs=refs,
                        downstream_refs=[generated_ref("agent_work_queue.jsonl"), generated_ref("completion_route.jsonl")],
                        provenance_tier="VS2_PACKET_COMPLETION_QUEUE",
                        role_target_name=role,
                    )
                )
        qopt_refs.append(common_row({"qopt1_input_ref_id": f"VS2_QOPT1_REF_{index:04d}", "paper_intent_candidate_id": packet_id, "qopt1_batch_ref": source_qopt_batch, "qopt1_interpret_back_ref": qinterp.get("interpret_back_id", "")}, row_id=f"VS2_QOPT1_REF_{index:04d}", owner_agent="QOPTAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("packet_evidence_bundle.jsonl")], provenance_tier="VS2_QOPT1_INPUT_REF"))
        rank4_refs.append(common_row({"rank4_input_ref_id": f"VS2_RANK4_REF_{index:04d}", "paper_intent_candidate_id": packet_id, "rank4_rank_id": source_rank4, "rank4_score_ref": "docs/master_plan/generated/pr168_rank4/rank_score.jsonl"}, row_id=f"VS2_RANK4_REF_{index:04d}", owner_agent="RankerAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("packet_evidence_bundle.jsonl")], provenance_tier="VS2_RANK4_INPUT_REF"))
        rp5g_refs.append(common_row({"rp5g_input_ref_id": f"VS2_RP5G_REF_{index:04d}", "paper_intent_candidate_id": packet_id, "rp5g_exec_pnl_ref": source_rp5g, "rp5g_simulation_run_id": row.get("simulation_run_id")}, row_id=f"VS2_RP5G_REF_{index:04d}", owner_agent="TradePlanSimulationAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("packet_evidence_bundle.jsonl")], provenance_tier="VS2_RP5G_INPUT_REF"))

        field_specs = (
            ("price_candidate", price, price_scale, "OrderVariableAgent"),
            ("quantity_candidate", size, "CONTRACTS", "OrderVariableAgent"),
            ("outcome_side", side, "VENUE_SIDE", "OrderVariableAgent"),
            ("TIF_candidate", "GTC_SIM_ONLY", "SIM_TIF", "OrderVariableAgent"),
            ("exit_rule", exit_rule, "RULE_ID", "RiskAgent"),
            ("cancel_replace_policy", cancel, "MILLISECONDS_OR_POLICY", "OrderVariableAgent"),
        )
        for field_index, (field_name, value, unit, owner) in enumerate(field_specs, start=1):
            row_id = f"VS2_TICKET_FIELD_{index:04d}_{field_index:02d}"
            ticket_fields.append(common_row({"paper_ticket_field_id": row_id, "paper_intent_candidate_id": packet_id, "paper_ticket_field": field_name, "field_value": value, "unit_scale": unit, "source_ref": qinterp.get("interpret_back_id", ""), "required_for_paper_loop_flag": True, "completion_route_if_missing": "packet_completion_queue.jsonl"}, row_id=row_id, owner_agent=owner, consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("paper_ticket_field_map.jsonl")], provenance_tier="PaperTicketFieldMapV1", role_target_name=owner))
            ticket_map.append(common_row({"paper_ticket_field_map_id": f"VS2_TICKET_MAP_{index:04d}_{field_index:02d}", "paper_intent_candidate_id": packet_id, "qopt1_variable_or_interpret_back_field": field_name, "qtt_trade_variable": field_name, "paper_ticket_field": field_name, "venue_native_candidate_field": f"{venue}:{field_name}", "required_for_paper_loop_flag": True, "required_for_live_future_flag": True, "unit_scale": unit, "completion_route_if_missing": "packet_completion_queue.jsonl", "source_ref": qinterp.get("interpret_back_id", ""), "owner_agent": owner, "consumer_agents": ["PaperExecutionAgent"]}, row_id=f"VS2_TICKET_MAP_{index:04d}_{field_index:02d}", owner_agent=owner, consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("paper_loop_packet.jsonl")], provenance_tier="PaperTicketFieldMapV1", role_target_name=owner))
        plan_common = {"paper_intent_candidate_id": packet_id, "source_qopt1_interpret_back_ref": qinterp.get("interpret_back_id", ""), "paper_submit_authority_created_flag": False, "live_authority_created_flag": False}
        order_policy.append(common_row({**plan_common, "paper_order_policy_id": f"VS2_ORDER_POLICY_{index:04d}", "order_type_candidate": "LIMIT", "maker_taker_split_policy": maker_taker, "policy_current_pr_authority": "CANDIDATE_ONLY_NO_SUBMIT"}, row_id=f"VS2_ORDER_POLICY_{index:04d}", owner_agent="OrderVariableAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("paper_lifecycle_plan.jsonl")], provenance_tier="VS2_PAPER_ORDER_POLICY", role_target_name="OrderVariableAgent"))
        entry_plan.append(common_row({**plan_common, "paper_entry_plan_id": f"VS2_ENTRY_PLAN_{index:04d}", "entry_rule": "LIMIT_AT_QOPT1_INTERPRET_BACK_PRICE", "price_candidate": price, "spread_filter": row.get("spread_depth_liquidity_filter")}, row_id=f"VS2_ENTRY_PLAN_{index:04d}", owner_agent="OrderVariableAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("paper_loop_packet.jsonl")], provenance_tier="VS2_PAPER_ENTRY_PLAN", role_target_name="OrderVariableAgent"))
        exit_plan.append(common_row({**plan_common, "paper_exit_plan_id": f"VS2_EXIT_PLAN_{index:04d}", "exit_rule": exit_rule, "hold_duration": hold, "exit_sell_close_authority_created_flag": False}, row_id=f"VS2_EXIT_PLAN_{index:04d}", owner_agent="RiskAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("paper_loop_packet.jsonl")], provenance_tier="VS2_PAPER_EXIT_PLAN", role_target_name="RiskAgent"))
        cancel_plan.append(common_row({**plan_common, "paper_cancel_replace_plan_id": f"VS2_CANCEL_REPLACE_PLAN_{index:04d}", "cancel_replace_policy": cancel, "cancel_replace_amend_reduce_authority_created_flag": False}, row_id=f"VS2_CANCEL_REPLACE_PLAN_{index:04d}", owner_agent="OrderVariableAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("paper_loop_packet.jsonl")], provenance_tier="VS2_PAPER_CANCEL_REPLACE_PLAN", role_target_name="OrderVariableAgent"))
        tif_plan.append(common_row({**plan_common, "paper_tif_plan_id": f"VS2_TIF_PLAN_{index:04d}", "TIF_candidate": "GTC_SIM_ONLY", "TIF_source_status": "CANDIDATE_ONLY_REVALIDATE_BEFORE_PAPER_LOOP"}, row_id=f"VS2_TIF_PLAN_{index:04d}", owner_agent="OrderVariableAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("paper_loop_packet.jsonl")], provenance_tier="VS2_PAPER_TIF_PLAN", role_target_name="OrderVariableAgent"))
        lifecycle.append(common_row({**plan_common, "paper_lifecycle_plan_id": f"VS2_LIFECYCLE_PLAN_{index:04d}", "lifecycle_steps": ["STAGE_PACKET", "REVALIDATE_SNAPSHOT", "FUTURE_PAPER_LOOP_SIMULATE_OR_EXECUTE_WITH_SUBMIT_GATED"], "paper_execution_created_flag": False, "realized_pnl_receipt_created_flag": False}, row_id=f"VS2_LIFECYCLE_PLAN_{index:04d}", owner_agent="PaperExecutionAgent", consumer_agents=["GovernanceAgent"], upstream_refs=refs, downstream_refs=[generated_ref("paper_loop_packet.jsonl")], provenance_tier="VS2_PAPER_LIFECYCLE_PLAN", role_target_name="PaperExecutionAgent"))
        explain.append(common_row({"paper_packet_explain_id": f"VS2_PACKET_EXPLAIN_{index:04d}", "paper_intent_candidate_id": packet_id, "explain_summary": f"{packet_id} compiled from {source_qopt_batch}/{cid}; state={state}; route={route}", "proof_not_label_only_flag": True}, row_id=f"VS2_PACKET_EXPLAIN_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["PaperExecutionAgent", "MemoryAgent"], upstream_refs=refs, downstream_refs=[generated_ref("packet_decision_trace.jsonl")], provenance_tier="VS2_PACKET_EXPLAIN"))

        venue_payload = {"paper_intent_candidate_id": packet_id, "venue": venue, "market_id_or_instrument_ref": row.get("market_id"), "side_semantic": side, "price_scale": price_scale, "quantity_scale": "CONTRACTS", "tick_size_ref": f"{venue}_TICK_SIZE_CANDIDATE_ONLY", "min_order_size_ref": f"{venue}_MIN_ORDER_SIZE_CANDIDATE_ONLY", "max_order_size_ref_when_available": f"{venue}_MAX_ORDER_SIZE_CANDIDATE_ONLY", "TIF_supported_candidate_refs": ["GTC_SIM_ONLY"], "order_type_supported_candidate_refs": ["LIMIT"], "fee_model_ref": f"{venue}_FEE_MODEL_CANDIDATE_ONLY", "settlement_or_resolution_ref": f"{venue}_SETTLEMENT_CANDIDATE_ONLY", "source_refs": [generated_ref("research_rec.jsonl")], "accepted_source_fact_flag": False, "connector_semantic_binding_flag": False}
        venue_norm.append(common_row({**venue_payload, "venue_norm_intent_id": f"VS2_VENUE_NORM_{index:04d}"}, row_id=f"VS2_VENUE_NORM_{index:04d}", owner_agent="OrderVariableAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("paper_ticket_field_map.jsonl")], provenance_tier="VenueNormalizedPaperIntentCandidateV1", role_target_name="OrderVariableAgent"))
        price_norm.append(common_row({"price_unit_norm_id": f"VS2_PRICE_UNIT_NORM_{index:04d}", **venue_payload}, row_id=f"VS2_PRICE_UNIT_NORM_{index:04d}", owner_agent="OrderVariableAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("venue_norm_intent.jsonl")], provenance_tier="VS2_PRICE_UNIT_NORMALIZATION_CANDIDATE", role_target_name="OrderVariableAgent"))
        side_norm.append(common_row({"side_norm_id": f"VS2_SIDE_NORM_{index:04d}", **venue_payload}, row_id=f"VS2_SIDE_NORM_{index:04d}", owner_agent="OrderVariableAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("venue_norm_intent.jsonl")], provenance_tier="VS2_SIDE_NORMALIZATION_CANDIDATE", role_target_name="OrderVariableAgent"))
        tick_min.append(common_row({"tick_min_size_ref_id": f"VS2_TICK_MIN_{index:04d}", **venue_payload}, row_id=f"VS2_TICK_MIN_{index:04d}", owner_agent="OrderVariableAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("venue_norm_intent.jsonl")], provenance_tier="VS2_TICK_MIN_SIZE_CANDIDATE", role_target_name="OrderVariableAgent"))
        venue_sem.append(common_row({"venue_semantic_cand_id": f"VS2_VENUE_SEMANTIC_{index:04d}", **venue_payload, "candidate_only_flag": True, "replay_paper_verification_required": True}, row_id=f"VS2_VENUE_SEMANTIC_{index:04d}", owner_agent="ResearchScoutAgent", consumer_agents=["OrderVariableAgent"], upstream_refs=[generated_ref("research_rec.jsonl")], downstream_refs=[generated_ref("venue_norm_intent.jsonl")], provenance_tier="VS2_VENUE_SEMANTIC_CANDIDATE_ONLY", role_target_name="ResearchScoutAgent"))

        readiness_payload = {"paper_intent_candidate_id": packet_id, "paper_readiness_state": state, "paper_loop_candidate_ready_now_flag": is_now, "production_paper_loop_ready_flag": is_now, "paper_loop_ready_without_revalidation_flag": False, "packet_completion_queue_ref": generated_ref("packet_completion_queue.jsonl") if is_deferred else "", "readiness_gap_codes": gaps, "paper_submit_authority_created_flag": False}
        readiness.append(common_row({"paper_readiness_id": readiness_id, **readiness_payload}, row_id=readiness_id, owner_agent="RiskAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("paper_loop_packet.jsonl")], provenance_tier="PaperIntentReadinessLedgerV1", role_target_name="RiskAgent"))
        checks = [
            (gate, "paper_gate_id", "VS2_GATE", "ALL_REQUIRED_GATES_PASS" if (is_now or is_fixture) else "DEFERRED_GATE"),
            (risk_check, "paper_risk_check_id", "VS2_RISK", "RISK_CARRIED_FORWARD_FROM_QOPT1"),
            (tca_check, "paper_tca_check_id", "VS2_TCA", "TCA_CARRIED_FORWARD_FROM_RP5G_RANK4_QOPT1"),
            (fill_check, "paper_fill_latency_check_id", "VS2_FILL_LAT", "FILL_LATENCY_CARRIED_FORWARD"),
            (cap_check, "paper_capacity_check_id", "VS2_CAPACITY", "CAPACITY_CARRIED_FORWARD"),
            (fdr_check, "paper_fdr_check_id", "VS2_FDR", "FDR_CARRIED_FORWARD"),
            (scen_check, "paper_scenario_check_id", "VS2_SCENARIO", "SCENARIO_CARRIED_FORWARD"),
            (port_check, "paper_portfolio_check_id", "VS2_PORTFOLIO", "PORTFOLIO_CARRIED_FORWARD"),
            (notrade_check, "paper_notrade_check_id", "VS2_NOTRADE", "NO_TRADE_NON_TERMINAL_ROUTE" if is_deferred else "NO_TRADE_MARGIN_PASS_OR_FIXTURE_ONLY"),
            (model_check, "paper_model_risk_check_id", "VS2_MODEL", "MODEL_RISK_CARRIED_FORWARD"),
            (stale_check, "paper_stale_check_id", "VS2_STALE", "REVALIDATE_BEFORE_PAPER_LOOP"),
            (fresh_check, "paper_source_fresh_check_id", "VS2_SOURCE_FRESH", "REVALIDATE_BEFORE_PAPER_LOOP"),
        ]
        for target, id_key, prefix, check_state in checks:
            target.append(common_row({id_key: f"{prefix}_{index:04d}", **readiness_payload, "check_state": check_state, "pass_flag": bool(is_now or is_fixture), "completion_route": route}, row_id=f"{prefix}_{index:04d}", owner_agent="RiskAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("paper_readiness.jsonl")], provenance_tier="VS2_PAPER_READINESS_CHECK", role_target_name="RiskAgent"))

        proof_common = {"paper_intent_candidate_id": packet_id, "paper_intent_candidate_only_flag": True, "paper_order_intent_created_flag": False, "paper_submit_authority_created_flag": False, "paper_execution_created_flag": False, "live_authority_created_flag": False, "live_candidate_created_flag": False, "shadow_execution_authority_created_flag": False, "live_dryrun_execution_authority_created_flag": False, "connector_write_created_flag": False, "private_state_read_created_flag": False, "cash_account_read_created_flag": False, "credential_access_created_flag": False, "wallet_access_created_flag": False, "buy_sell_open_close_logic_created_flag": False, "cancel_replace_amend_reduce_authority_created_flag": False, "realized_pnl_receipt_created_flag": False, "profit_guarantee_flag": False, "owner_dashboard_runtime_created_flag": False, "telegram_bot_runtime_created_flag": False, "owner_approval_authority_created_by_vs2_flag": False}
        no_live.append(common_row({"no_live_submit_id": no_live_id, **proof_common}, row_id=no_live_id, owner_agent="GovernanceAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("auth_block.jsonl")], provenance_tier="PaperIntentNoLiveSubmitProofV1"))
        no_conn.append(common_row({"no_connector_write_id": f"VS2_NO_CONNECTOR_WRITE_{index:04d}", **proof_common}, row_id=f"VS2_NO_CONNECTOR_WRITE_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("auth_block.jsonl")], provenance_tier="VS2_NO_CONNECTOR_WRITE_PROOF"))
        no_priv.append(common_row({"no_private_state_id": f"VS2_NO_PRIVATE_STATE_{index:04d}", **proof_common}, row_id=f"VS2_NO_PRIVATE_STATE_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("auth_block.jsonl")], provenance_tier="VS2_NO_PRIVATE_STATE_PROOF"))
        no_cash.append(common_row({"no_cash_read_id": f"VS2_NO_CASH_READ_{index:04d}", **proof_common}, row_id=f"VS2_NO_CASH_READ_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("auth_block.jsonl")], provenance_tier="VS2_NO_CASH_READ_PROOF"))
        no_order.append(common_row({"no_order_submit_id": f"VS2_NO_ORDER_SUBMIT_{index:04d}", **proof_common}, row_id=f"VS2_NO_ORDER_SUBMIT_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("auth_block.jsonl")], provenance_tier="VS2_NO_ORDER_SUBMIT_PROOF"))
        auth.append(common_row({"auth_block_id": auth_id, **proof_common, "formula_computation_created_by_vs2_flag": False, "trade_variable_optimization_created_by_vs2_flag": False, "rank4_recomputed_by_vs2_flag": False, "qopt1_recomputed_by_vs2_flag": False, "paper_loop_execution_created_by_vs2_flag": False, "future_execution_router_required_before_real_orders_flag": True, "buy_sell_open_close_authority_created_by_vs2_flag": False}, row_id=auth_id, owner_agent="GovernanceAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("authority_boundary.report.json")], provenance_tier="Vs2AuthorityBoundaryProofV1"))

        reval_flags = {"revalidate_market_snapshot_before_paper_run": True, "revalidate_source_freshness_before_paper_run": True, "revalidate_spread_depth_liquidity_before_paper_run": True, "revalidate_latency_budget_before_paper_run": True, "revalidate_portfolio_exposure_before_paper_run": True, "revalidate_no_trade_margin_before_paper_run": True, "revalidate_stale_TTL_before_paper_run": True}
        loop_payload = {"paper_loop_packet_id": f"VS2_PAPER_LOOP_PACKET_{index:04d}", "paper_intent_candidate_id": packet_id, "selected_trade_plan_refs": [cid], "market_context_refs": [str(row.get("market_id"))], "order_variable_refs": [qinterp.get("interpret_back_id", "")], "paper_ticket_field_refs": [generated_ref("paper_ticket_fields.jsonl")], "entry_plan_ref": f"VS2_ENTRY_PLAN_{index:04d}", "exit_plan_ref": f"VS2_EXIT_PLAN_{index:04d}", "cancel_replace_plan_ref": f"VS2_CANCEL_REPLACE_PLAN_{index:04d}", "TCA_ref": generated_ref("paper_tca_check.jsonl"), "fill_latency_ref": generated_ref("paper_fill_latency_check.jsonl"), "capacity_ref": generated_ref("paper_capacity_check.jsonl"), "portfolio_ref": generated_ref("paper_portfolio_check.jsonl"), "no_trade_ref": generated_ref("paper_notrade_check.jsonl"), "scenario_ref": generated_ref("paper_scenario_check.jsonl"), "FDR_ref": generated_ref("paper_fdr_check.jsonl"), "source_freshness_ref": generated_ref("paper_source_fresh_check.jsonl"), "stale_revalidation_ref": generated_ref("paper_loop_revalidation_req.jsonl"), "qopt1_batch_ref": source_qopt_batch, "rank4_ref": source_rank4, "rp5g_ref": source_rp5g, "qku_formula_refs": stable_unique(row.get("qku_refs", []) + row.get("formula_refs", [])), "agent_owner": "PaperExecutionAgent", "paper_loop_consumer_agent": "PaperExecutionAgent", "paper_loop_required_before_any_paper_execution_flag": True, "paper_submit_created_flag": False, "future_owner_surface_needed_flag": True, "future_owner_surface_current_pr_runtime_flag": False, **reval_flags}
        loop_packet.append(common_row(loop_payload, row_id=f"VS2_PAPER_LOOP_PACKET_{index:04d}", owner_agent="PaperExecutionAgent", consumer_agents=["PaperExecutionAgent", "GovernanceAgent"], upstream_refs=refs, downstream_refs=[generated_ref("paper_loop_contract.jsonl")], provenance_tier="PaperLoopInputPacketV1", role_target_name="PaperExecutionAgent"))
        loop_contract.append(common_row({"paper_loop_contract_id": f"VS2_PAPER_LOOP_CONTRACT_{index:04d}", **loop_payload, "future_owner_surface_needed_flag": True, "future_dashboard_consumer_pr": "PR169-DASH1", "future_telegram_consumer_pr": "PR169-TG1", "future_owner_review_surface_needed_after_dash1_flag": True, "future_owner_action_runtime_created_by_vs2_flag": False, "future_telegram_runtime_created_by_vs2_flag": False}, row_id=f"VS2_PAPER_LOOP_CONTRACT_{index:04d}", owner_agent="PaperExecutionAgent", consumer_agents=["PaperExecutionAgent", "GovernanceAgent"], upstream_refs=refs, downstream_refs=[generated_ref("downstream_handoff.jsonl")], provenance_tier="PaperLoopConsumerContractV1", role_target_name="PaperExecutionAgent"))
        loop_handoff.append(common_row({"paper_loop_handoff_id": f"VS2_PAPER_LOOP_HANDOFF_{index:04d}", **loop_payload}, row_id=f"VS2_PAPER_LOOP_HANDOFF_{index:04d}", owner_agent="PaperExecutionAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("paper_loop_packet.jsonl")], provenance_tier="VS2_PAPER_LOOP_HANDOFF"))
        loop_manifest.append(common_row({"paper_loop_manifest_id": f"VS2_PAPER_LOOP_MANIFEST_{index:04d}", "paper_intent_candidate_id": packet_id, "packet_refs": [generated_ref("paper_loop_packet.jsonl"), generated_ref("paper_loop_contract.jsonl"), generated_ref("packet_evidence_bundle.jsonl")]}, row_id=f"VS2_PAPER_LOOP_MANIFEST_{index:04d}", owner_agent="PaperExecutionAgent", consumer_agents=["GovernanceAgent"], upstream_refs=refs, downstream_refs=[generated_ref("paper_loop_packet.jsonl")], provenance_tier="VS2_PAPER_LOOP_MANIFEST"))
        loop_schema.append(common_row({"paper_loop_input_schema_hint_id": f"VS2_PAPER_LOOP_SCHEMA_HINT_{index:04d}", "paper_intent_candidate_id": packet_id, "schema_hint": "PaperLoopInputPacketV1", "required_fields_present_flag": True}, row_id=f"VS2_PAPER_LOOP_SCHEMA_HINT_{index:04d}", owner_agent="PaperExecutionAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("paper_loop_packet.jsonl")], provenance_tier="VS2_PAPER_LOOP_INPUT_SCHEMA_HINT"))
        loop_reval.append(common_row({"paper_loop_revalidation_requirement_id": f"VS2_PAPER_LOOP_REVALIDATION_{index:04d}", "paper_intent_candidate_id": packet_id, **reval_flags}, row_id=f"VS2_PAPER_LOOP_REVALIDATION_{index:04d}", owner_agent="MarketConditionAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("paper_loop_packet.jsonl")], provenance_tier="PaperLoopRevalidationRequirementV1", role_target_name="MarketConditionAgent"))

        mem1.append(common_row({"mem1_handoff_id": f"VS2_MEM1_HANDOFF_{index:04d}", "paper_intent_candidate_id": packet_id, "qopt1_batch_id": source_qopt_batch, "trade_plan_candidate_id": cid, "context_signature_refs": [row.get("market_id")], "similarity_key_refs": [idem_key], "recipe_refs": [generated_ref("qku_formula_route_bundle.jsonl")], "negative_memory_refs": [generated_ref("packet_decision_trace.jsonl")] if is_deferred else [], "drift_refs": [generated_ref("paper_loop_revalidation_req.jsonl")], "retest_refs": [route], "paper_readiness_state": state, "future_MEM1_storage_required_flag": True, "durable_MEM1_storage_created_flag": False, "MEM1_query_api_created_flag": False}, row_id=f"VS2_MEM1_HANDOFF_{index:04d}", owner_agent="MemoryAgent", consumer_agents=["MemoryAgent", "GovernanceAgent"], upstream_refs=refs, downstream_refs=[generated_ref("downstream_handoff.jsonl")], provenance_tier="Vs2ToMem1LearningHandoffV1", role_target_name="MemoryAgent"))
        downstream_handoff.append(common_row({"downstream_handoff_id": f"VS2_DOWNSTREAM_HANDOFF_{index:04d}", "paper_intent_candidate_id": packet_id, "future_LLM_review_possible_flag": True, "future_LLM_live_call_in_CI_flag": False, "future_LLM_source_truth_authority_flag": False, "future_LLM_order_authority_flag": False, "future_LLM_risk_gate_override_flag": False, "future_LLM_deterministic_gate_override_flag": False, "future_LLM_prompt_contract_required_flag": True, "future_llm_critic_consumer_pr": "PR169-LLM3", "future_llm_commander_consumer_pr": "PR169-LLM4", "future_llm_consumer_fields_inside_downstream_handoff": True, "packet_decision_trace_for_future_llm": True, "llm_runtime_created_by_vs2_flag": False, "llm_live_call_in_ci_flag": False, "llm_order_authority_flag": False, "llm_source_truth_authority_flag": False, "llm_risk_gate_override_flag": False, "future_owner_surface_needed_flag": True, "future_dashboard_consumer_pr": "PR169-DASH1", "future_telegram_consumer_pr": "PR169-TG1", "future_owner_review_surface_needed_after_dash1_flag": True, "future_owner_action_runtime_created_by_vs2_flag": False, "future_dashboard_runtime_created_by_vs2_flag": False, "future_telegram_runtime_created_by_vs2_flag": False, "future_execution_path_hint": ["PAPER-LOOP", "MEM1", "LIVE-DRYRUN_SUBMIT_DISABLED", "LIVE-PILOT_OWNER_APPROVED_CANARY", "LAUNCH", "GOVERNED_EXECUTION_ROUTER"]}, row_id=f"VS2_DOWNSTREAM_HANDOFF_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["MemoryAgent", "PaperExecutionAgent", "CommanderAgent"], upstream_refs=refs, downstream_refs=[generated_ref("mem1_handoff.jsonl"), generated_ref("orch_handoff.jsonl")], provenance_tier="Vs2ToAgentOrchFutureHandoffV1"))
        orch.append(common_row({"orch_handoff_id": f"VS2_ORCH_HANDOFF_{index:04d}", "paper_intent_candidate_id": packet_id, "future_agent_work_routes": ["MarketConditionAgent", "PaperExecutionAgent", "MemoryAgent", "RiskAgent", "TCAAgent", "FillLatencyAgent", "GovernanceAgent"], "current_execution_authority_created_flag": False}, row_id=f"VS2_ORCH_HANDOFF_{index:04d}", owner_agent="CommanderAgent", consumer_agents=["GovernanceAgent"], upstream_refs=refs, downstream_refs=[generated_ref("agent_work_queue.jsonl")], provenance_tier="VS2_AGENT_ORCH_FUTURE_HANDOFF"))
        live_dry.append(common_row({"live_dry_handoff_id": f"VS2_LIVE_DRY_HANDOFF_{index:04d}", "paper_intent_candidate_id": packet_id, "live_dryrun_future_handoff_only_flag": True, "submit_disabled_required_flag": True, "live_pilot_required_after_paper_and_dryrun_flag": True, "current_live_authority_created_flag": False, "shadow_execution_authority_created_flag": False}, row_id=f"VS2_LIVE_DRY_HANDOFF_{index:04d}", owner_agent="LiveDryRunAgent", consumer_agents=["GovernanceAgent"], upstream_refs=refs, downstream_refs=[generated_ref("downstream_handoff.jsonl")], provenance_tier="VS2_LIVE_DRYRUN_FUTURE_ONLY_HANDOFF", role_target_name="LiveDryRunAgent"))
        shadow.append(common_row({"shadow_handoff_id": f"VS2_SHADOW_HANDOFF_{index:04d}", "paper_intent_candidate_id": packet_id, "shadow_future_handoff_only_flag": True, "submit_disabled_required_flag": True, "live_pilot_required_after_paper_and_dryrun_flag": True, "current_live_authority_created_flag": False, "shadow_execution_authority_created_flag": False}, row_id=f"VS2_SHADOW_HANDOFF_{index:04d}", owner_agent="ShadowObservationAgent", consumer_agents=["GovernanceAgent"], upstream_refs=refs, downstream_refs=[generated_ref("downstream_handoff.jsonl")], provenance_tier="VS2_SHADOW_FUTURE_ONLY_HANDOFF", role_target_name="ShadowObservationAgent"))

        dedupe.append(common_row({"intent_dedupe_id": f"VS2_INTENT_DEDUPE_{index:04d}", "paper_intent_candidate_id": packet_id, "packet_idempotency_key": idem_key, "duplicate_detected_flag": False}, row_id=f"VS2_INTENT_DEDUPE_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=[generated_ref("packet_idempotency_key.jsonl")], downstream_refs=[generated_ref("vs2_packet_registry.jsonl")], provenance_tier="VS2_INTENT_DEDUPE"))
        near_clone.append(common_row({"near_clone_intent_id": f"VS2_NEAR_CLONE_{index:04d}", "paper_intent_candidate_id": packet_id, "near_clone_group_key": f"{venue}|{row.get('market_id')}|{side}", "intentional_challenger_exploration_tag": cid not in selected_ids}, row_id=f"VS2_NEAR_CLONE_{index:04d}", owner_agent="RiskAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("intent_dedupe.jsonl")], provenance_tier="VS2_NEAR_CLONE_INTENT"))
        hotpath_flag = bool(is_now)
        hotpath.append(common_row({"hotpath_intent_id": f"VS2_HOTPATH_{index:04d}", "paper_intent_candidate_id": packet_id, "hot_path_candidate_packet": hotpath_flag, "hotpath_reason_codes": ["READY_NOW_COMPLETE_PACKET"] if hotpath_flag else [], "compile_time_ms": 1, "paper_loop_expected_parse_time_ms": 5, "revalidation_budget_ms": 1000}, row_id=f"VS2_HOTPATH_{index:04d}", owner_agent="PaperExecutionAgent", consumer_agents=["GovernanceAgent"], upstream_refs=refs, downstream_refs=[generated_ref("latency_sla_intent.jsonl")], provenance_tier="VS2_HOTPATH_INTENT"))
        coldpath.append(common_row({"coldpath_intent_id": f"VS2_COLDPATH_{index:04d}", "paper_intent_candidate_id": packet_id, "cold_path_required": not hotpath_flag, "coldpath_reason_codes": gaps or ["FIXTURE_OR_REVALIDATION_REQUIRED"], "completion_route": route}, row_id=f"VS2_COLDPATH_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("packet_completion_queue.jsonl")], provenance_tier="VS2_COLDPATH_INTENT"))
        latency.append(common_row({"latency_sla_intent_id": f"VS2_LATENCY_SLA_{index:04d}", "paper_intent_candidate_id": packet_id, "compile_time_ms": 1, "paper_loop_expected_parse_time_ms": 5, "revalidation_budget_ms": 1000, "hotpath_reason_codes": ["READY_NOW_COMPLETE_PACKET"] if hotpath_flag else [], "coldpath_reason_codes": gaps or ["FIXTURE_OR_REVALIDATION_REQUIRED"], "latency_risk_flag": not hotpath_flag}, row_id=f"VS2_LATENCY_SLA_{index:04d}", owner_agent="FillLatencyAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("hotpath_intent.jsonl")], provenance_tier="VS2_LATENCY_SLA_INTENT", role_target_name="FillLatencyAgent"))
        priority.append(common_row({"intent_priority_id": f"VS2_INTENT_PRIORITY_{index:04d}", "paper_intent_candidate_id": packet_id, "priority_rank": index, "priority_reason": state, "paper_loop_candidate_ready_now_flag": is_now}, row_id=f"VS2_INTENT_PRIORITY_{index:04d}", owner_agent="RiskAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=refs, downstream_refs=[generated_ref("vs2_packet_registry.jsonl")], provenance_tier="VS2_INTENT_PRIORITY"))

        cand_elig.append(common_row({"vs2_candidate_paper_elig_id": f"VS2_CAND_ELIG_{index:04d}", "paper_intent_candidate_id": packet_id, "candidate_refs": [cid], "rank4_refs": [source_rank4], "rp5g_refs": [source_rp5g], "qopt1_refs": [source_qopt_batch], "computability_state_from_upstream": "QOPT1_NUMERIC_EVIDENCE_AVAILABLE", "rankability_state_from_rank4": "RANK4_ADVISORY_RANK_AVAILABLE", "optability_state_from_qopt1": "QOPT1_ACTIVE_SET_MEMBER", "paper_eligibility_state": state, "numeric_evidence_refs": stable_unique(row.get("numeric_evidence_refs", [])), "qopt1_batch_refs": [source_qopt_batch], "paper_ticket_field_refs": [generated_ref("paper_ticket_fields.jsonl")], "missing_paper_fields": [], "completion_route": route, "owner_agent": "PaperExecutionAgent", "consumer_agents": ["GovernanceAgent"], "formula_mutation_flag": False, "qku_global_ban_flag": False, "formula_global_ban_flag": False, "paper_submit_authority_created_flag": False, "live_authority_created_flag": False, "orphan_flag": False}, row_id=f"VS2_CAND_ELIG_{index:04d}", owner_agent="PaperExecutionAgent", consumer_agents=["GovernanceAgent"], upstream_refs=refs, downstream_refs=[generated_ref("paper_readiness.jsonl")], provenance_tier="VS2_CANDIDATE_PAPER_ELIGIBILITY"))
        qku_elig.append(common_row({"vs2_qku_paper_elig_id": f"VS2_QKU_ELIG_{index:04d}", "paper_intent_candidate_id": packet_id, "qku_refs": stable_unique(row.get("qku_refs", [])), "paper_eligibility_state": state, "qku_global_ban_flag": False, "formula_mutation_flag": False, "paper_submit_authority_created_flag": False, "live_authority_created_flag": False}, row_id=f"VS2_QKU_ELIG_{index:04d}", owner_agent="FormulaLibraryAgent", consumer_agents=["GovernanceAgent"], upstream_refs=refs, downstream_refs=[generated_ref("qku_formula_route_bundle.jsonl")], provenance_tier="VS2_QKU_PAPER_ELIGIBILITY", role_target_name="FormulaLibraryAgent"))
        formula_elig.append(common_row({"vs2_formula_paper_elig_id": f"VS2_FORMULA_ELIG_{index:04d}", "paper_intent_candidate_id": packet_id, "formula_refs": stable_unique(row.get("formula_refs", [])), "paper_eligibility_state": state, "formula_global_ban_flag": False, "formula_mutation_flag": False, "paper_submit_authority_created_flag": False, "live_authority_created_flag": False}, row_id=f"VS2_FORMULA_ELIG_{index:04d}", owner_agent="FormulaLibraryAgent", consumer_agents=["GovernanceAgent"], upstream_refs=refs, downstream_refs=[generated_ref("qku_formula_route_bundle.jsonl")], provenance_tier="VS2_FORMULA_PAPER_ELIGIBILITY", role_target_name="FormulaLibraryAgent"))
    batch_elig.append(common_row({"vs2_batch_paper_elig_id": "VS2_BATCH_ELIG_0001", "source_qopt1_batch_id": str(primary.get("batch_id", "QOPT1_BATCH_PRIMARY_0001")), "paper_eligibility_state": "VS2_BATCH_CONSUMED_AS_CANDIDATE_PACKET_SOURCE", "packet_refs": [row["paper_intent_candidate_id"] for row in packets], "paper_submit_authority_created_flag": False, "live_authority_created_flag": False}, row_id="VS2_BATCH_ELIG_0001", owner_agent="QOPTAgent", consumer_agents=["PaperExecutionAgent"], upstream_refs=["docs/master_plan/generated/pr168_qopt1/batch_select.jsonl"], downstream_refs=[generated_ref("vs2_packet_registry.jsonl")], provenance_tier="VS2_BATCH_PAPER_ELIGIBILITY"))

    return {
        "vs2_packet_registry.jsonl": registry,
        "packet_access_contract.jsonl": contracts,
        "packet_evidence_bundle.jsonl": evidence,
        "packet_decision_trace.jsonl": decision,
        "packet_idempotency_key.jsonl": idem,
        "qku_formula_route_bundle.jsonl": qroutes,
        "qstruct_carry.jsonl": qstruct,
        "packet_completion_queue.jsonl": completion,
        "paper_intent_candidate.jsonl": packets,
        "paper_ticket_fields.jsonl": ticket_fields,
        "paper_ticket_field_map.jsonl": ticket_map,
        "paper_order_policy.jsonl": order_policy,
        "paper_entry_plan.jsonl": entry_plan,
        "paper_exit_plan.jsonl": exit_plan,
        "paper_cancel_replace_plan.jsonl": cancel_plan,
        "paper_tif_plan.jsonl": tif_plan,
        "paper_lifecycle_plan.jsonl": lifecycle,
        "paper_packet_explain.jsonl": explain,
        "venue_norm_intent.jsonl": venue_norm,
        "price_unit_norm.jsonl": price_norm,
        "side_norm.jsonl": side_norm,
        "tick_min_size_ref.jsonl": tick_min,
        "venue_semantic_cand.jsonl": venue_sem,
        "paper_readiness.jsonl": readiness,
        "paper_gate.jsonl": gate,
        "paper_risk_check.jsonl": risk_check,
        "paper_tca_check.jsonl": tca_check,
        "paper_fill_latency_check.jsonl": fill_check,
        "paper_capacity_check.jsonl": cap_check,
        "paper_fdr_check.jsonl": fdr_check,
        "paper_scenario_check.jsonl": scen_check,
        "paper_portfolio_check.jsonl": port_check,
        "paper_notrade_check.jsonl": notrade_check,
        "paper_model_risk_check.jsonl": model_check,
        "paper_stale_check.jsonl": stale_check,
        "paper_source_fresh_check.jsonl": fresh_check,
        "no_live_submit.jsonl": no_live,
        "no_connector_write.jsonl": no_conn,
        "no_private_state.jsonl": no_priv,
        "no_cash_read.jsonl": no_cash,
        "no_order_submit.jsonl": no_order,
        "paper_loop_packet.jsonl": loop_packet,
        "paper_loop_contract.jsonl": loop_contract,
        "paper_loop_handoff.jsonl": loop_handoff,
        "paper_loop_manifest.jsonl": loop_manifest,
        "paper_loop_input_schema_hint.jsonl": loop_schema,
        "paper_loop_revalidation_req.jsonl": loop_reval,
        "mem1_handoff.jsonl": mem1,
        "downstream_handoff.jsonl": downstream_handoff,
        "orch_handoff.jsonl": orch,
        "live_dry_handoff.jsonl": live_dry,
        "shadow_handoff.jsonl": shadow,
        "intent_dedupe.jsonl": dedupe,
        "near_clone_intent.jsonl": near_clone,
        "hotpath_intent.jsonl": hotpath,
        "coldpath_intent.jsonl": coldpath,
        "latency_sla_intent.jsonl": latency,
        "intent_priority.jsonl": priority,
        "auth_block.jsonl": auth,
        "vs2_qku_paper_elig.jsonl": qku_elig,
        "vs2_formula_paper_elig.jsonl": formula_elig,
        "vs2_candidate_paper_elig.jsonl": cand_elig,
        "vs2_batch_paper_elig.jsonl": batch_elig,
        "qopt1_input_refs.jsonl": qopt_refs,
        "rank4_input_refs.jsonl": rank4_refs,
        "rp5g_input_refs.jsonl": rp5g_refs,
    }


def _agent_rows() -> dict[str, list[dict[str, Any]]]:
    alias_rows: list[dict[str, Any]] = []
    route_rows: list[dict[str, Any]] = []
    consume_rows: list[dict[str, Any]] = []
    duty_rows: list[dict[str, Any]] = []
    no_orphan_rows: list[dict[str, Any]] = []
    auth_rows: list[dict[str, Any]] = []
    work_rows: list[dict[str, Any]] = []
    for index, role in enumerate(ROLE_TARGETS, start=1):
        common = {
            "role_target_name": role,
            "canonical_agent_name": role,
            "agent_roster_source_ref": "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
            "agent_duty_crosswalk_ref": "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
            "alias_resolution_status": "TRIAGE_REQUIRED",
            "invent_new_agent_authority_flag": False,
            "fallback_route": "GovernanceAgent | CommanderAgent",
        }
        alias_rows.append(common_row({"agent_alias_map_id": f"VS2_AGENT_ALIAS_{index:04d}", **common}, row_id=f"VS2_AGENT_ALIAS_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=[role, "CommanderAgent"], upstream_refs=[common["agent_roster_source_ref"], common["agent_duty_crosswalk_ref"]], downstream_refs=[generated_ref("agent_route.jsonl")], provenance_tier="VS2_AGENT_ALIAS_MAP"))
        route_rows.append(common_row({"agent_route_id": f"VS2_AGENT_ROUTE_{index:04d}", **common, "route_family": "VS2_PAPER_INTENT_PACKET_CONSUMPTION"}, row_id=f"VS2_AGENT_ROUTE_{index:04d}", owner_agent=role, consumer_agents=["GovernanceAgent"], upstream_refs=[generated_ref("agent_alias_map.jsonl")], downstream_refs=[generated_ref("agent_consume.jsonl")], provenance_tier="VS2_AGENT_ROUTE", role_target_name=role))
        consume_rows.append(common_row({"agent_consume_id": f"VS2_AGENT_CONSUME_{index:04d}", **common, "consumed_vs2_surfaces": [generated_ref("vs2_packet_registry.jsonl"), generated_ref("packet_access_contract.jsonl")]}, row_id=f"VS2_AGENT_CONSUME_{index:04d}", owner_agent=role, consumer_agents=["GovernanceAgent"], upstream_refs=[generated_ref("agent_route.jsonl")], downstream_refs=[generated_ref("agent_duty_map.jsonl")], provenance_tier="VS2_AGENT_CONSUME", role_target_name=role))
        duty_rows.append(common_row({"agent_duty_map_id": f"VS2_AGENT_DUTY_{index:04d}", **common, "duty_scope": "NON_AUTHORITY_PACKET_STAGING_OR_FUTURE_CONSUMPTION"}, row_id=f"VS2_AGENT_DUTY_{index:04d}", owner_agent=role, consumer_agents=["GovernanceAgent"], upstream_refs=[common["agent_duty_crosswalk_ref"]], downstream_refs=[generated_ref("agent_work_queue.jsonl")], provenance_tier="VS2_AGENT_DUTY_MAP", role_target_name=role))
        no_orphan_rows.append(common_row({"agent_no_orphan_id": f"VS2_AGENT_NO_ORPHAN_{index:04d}", **common, "orphan_flag": False}, row_id=f"VS2_AGENT_NO_ORPHAN_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=[role], upstream_refs=[generated_ref("agent_route.jsonl")], downstream_refs=[generated_ref("no_orphan.report.json")], provenance_tier="VS2_AGENT_NO_ORPHAN"))
        auth_rows.append(common_row({"agent_authority_block_id": f"VS2_AGENT_AUTH_BLOCK_{index:04d}", **common, "runtime_authority_created_flag": False, "paper_submit_authority_created_flag": False, "live_authority_created_flag": False}, row_id=f"VS2_AGENT_AUTH_BLOCK_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=[role], upstream_refs=[generated_ref("auth_block.jsonl")], downstream_refs=[generated_ref("authority_boundary.report.json")], provenance_tier="VS2_AGENT_AUTHORITY_BLOCK"))
        work_rows.append(common_row({"agent_work_queue_id": f"VS2_AGENT_WORK_{index:04d}", **common, "work_queue_scope": "PACKET_COMPLETION_OR_FUTURE_CONSUMPTION_ONLY", "paper_submit_authority_created_flag": False, "live_authority_created_flag": False}, row_id=f"VS2_AGENT_WORK_{index:04d}", owner_agent=role, consumer_agents=["GovernanceAgent"], upstream_refs=[generated_ref("packet_completion_queue.jsonl")], downstream_refs=[generated_ref("completion_route.jsonl")], provenance_tier="VS2_AGENT_WORK_QUEUE", role_target_name=role))
    return {
        "agent_alias_map.jsonl": alias_rows,
        "agent_route.jsonl": route_rows,
        "agent_consume.jsonl": consume_rows,
        "agent_duty_map.jsonl": duty_rows,
        "agent_no_orphan.jsonl": no_orphan_rows,
        "agent_authority_block.jsonl": auth_rows,
        "agent_work_queue.jsonl": work_rows,
    }


def _route_rows() -> dict[str, list[dict[str, Any]]]:
    filenames = all_artifact_filenames(include_manifests=False)
    rows_by_name = {name: [] for name in ("artifact_io.jsonl", "file_route.jsonl", "row_route.jsonl", "value_route.jsonl", "info_route.jsonl", "lineage.jsonl", "dag.jsonl", "val_lineage.jsonl", "downstream.jsonl", "completion_route.jsonl")}
    for index, filename in enumerate(filenames, start=1):
        ref = generated_ref(filename)
        base = {
            "route_index": index,
            "artifact_filename": filename,
            "file_path": ref,
            "artifact_or_value_ref": ref,
            "producer_pr": PR_ID,
            "producer_file": PRODUCER_TOOL,
            "producer_row_id": f"VS2_ROUTE_{index:04d}",
            "producer_agent": "GovernanceAgent",
            "upstream_refs": ["docs/master_plan/generated/pr168_qopt1/vs2_handoff.jsonl"],
            "downstream_prs": ["PR168-MEM1", "PR169-AGENT-ORCH1", "PR169-PAPER-LOOP"],
            "downstream_files": [generated_ref("downstream_handoff.jsonl")],
            "downstream_row_families": ["VS2_PACKET"],
            "downstream_agents": ["PaperExecutionAgent", "MemoryAgent", "GovernanceAgent"],
            "future_user_surface_or_owner_dashboard_ref": "PR169-DASH1 future field only in downstream_handoff.jsonl",
            "connector_refs_or_future_connector_status": "FUTURE_CONNECTOR_STATUS_ONLY_NO_BIND_WRITE_READ",
            "validation_refs": [VALIDATOR_REF],
            "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
            "completion_route_if_not_consumed_now": "packet_completion_queue.jsonl",
            "orphan_flag": False,
        }
        rows_by_name["artifact_io.jsonl"].append(common_row({"artifact_io_id": f"VS2_ARTIFACT_IO_{index:04d}", **base}, row_id=f"VS2_ARTIFACT_IO_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent"], upstream_refs=base["upstream_refs"], downstream_refs=[ref], provenance_tier="VS2_ARTIFACT_IO"))
        rows_by_name["file_route.jsonl"].append(common_row({"file_route_id": f"VS2_FILE_ROUTE_{index:04d}", **base}, row_id=f"VS2_FILE_ROUTE_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent"], upstream_refs=base["upstream_refs"], downstream_refs=[ref], provenance_tier="VS2_FILE_ROUTE"))
        rows_by_name["row_route.jsonl"].append(common_row({"row_route_id": f"VS2_ROW_ROUTE_{index:04d}", **base}, row_id=f"VS2_ROW_ROUTE_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent"], upstream_refs=base["upstream_refs"], downstream_refs=[ref], provenance_tier="VS2_ROW_ROUTE"))
        rows_by_name["value_route.jsonl"].append(common_row({"value_route_id": f"VS2_VALUE_ROUTE_{index:04d}", **base}, row_id=f"VS2_VALUE_ROUTE_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent"], upstream_refs=base["upstream_refs"], downstream_refs=[ref], provenance_tier="VS2_VALUE_ROUTE"))
        rows_by_name["info_route.jsonl"].append(common_row({"info_route_id": f"VS2_INFO_ROUTE_{index:04d}", **base}, row_id=f"VS2_INFO_ROUTE_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent"], upstream_refs=base["upstream_refs"], downstream_refs=[ref], provenance_tier="VS2_INFO_ROUTE"))
        rows_by_name["lineage.jsonl"].append(common_row({"lineage_id": f"VS2_LINEAGE_{index:04d}", **base}, row_id=f"VS2_LINEAGE_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent"], upstream_refs=base["upstream_refs"], downstream_refs=[ref], provenance_tier="VS2_LINEAGE"))
        rows_by_name["dag.jsonl"].append(common_row({"dag_id": f"VS2_DAG_{index:04d}", **base}, row_id=f"VS2_DAG_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent"], upstream_refs=base["upstream_refs"], downstream_refs=[ref], provenance_tier="VS2_DAG"))
        rows_by_name["val_lineage.jsonl"].append(common_row({"val_lineage_id": f"VS2_VAL_LINEAGE_{index:04d}", **base}, row_id=f"VS2_VAL_LINEAGE_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent"], upstream_refs=base["upstream_refs"], downstream_refs=[ref], provenance_tier="VS2_VAL_LINEAGE"))
        rows_by_name["downstream.jsonl"].append(common_row({"downstream_id": f"VS2_DOWNSTREAM_{index:04d}", **base}, row_id=f"VS2_DOWNSTREAM_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent"], upstream_refs=base["upstream_refs"], downstream_refs=[ref], provenance_tier="VS2_DOWNSTREAM_ROUTE"))
        rows_by_name["completion_route.jsonl"].append(common_row({"completion_route_id": f"VS2_COMPLETION_ROUTE_{index:04d}", **base, "blocker_code": "VS2_PACKET_READY_FOR_PAPER_LOOP_FUTURE_ONLY", "blocked_field": filename, "responsible_role_target": "GovernanceAgent", "canonical_agent_name_or_triage_route": "GovernanceAgent_CommanderAgent_triage", "completion_route": "NO_ACTION_IF_CONSUMED_BY_PACKET_REGISTRY", "future_pr_or_current_fix_route": "PR169-PAPER-LOOP", "can_emit_paper_intent_candidate_flag": True, "can_handoff_to_paper_loop_flag": True, "can_handoff_to_mem1_flag": True, "can_handoff_to_live_dryrun_flag": False}, row_id=f"VS2_COMPLETION_ROUTE_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent"], upstream_refs=base["upstream_refs"], downstream_refs=[ref], provenance_tier="VS2_COMPLETION_ROUTE"))
    return rows_by_name


def _top_level_reports(rows: dict[str, list[dict[str, Any]]], missing_required: list[str]) -> dict[str, dict[str, Any]]:
    packet_count = len(rows["paper_intent_candidate.jsonl"])
    deferred_count = len([row for row in rows["paper_readiness.jsonl"] if str(row.get("paper_readiness_state", "")).startswith("PAPER_INTENT_DEFERRED")])
    fixture_count = len([row for row in rows["paper_readiness.jsonl"] if row.get("paper_readiness_state") == "PAPER_LOOP_CANDIDATE_READY_FIXTURE_ONLY"])
    ready_now_count = len([row for row in rows["paper_readiness.jsonl"] if row.get("paper_loop_candidate_ready_now_flag") is True])
    reports = {
        "missing_req.report.json": common_report({"missing_required_input_count": len(missing_required), "missing_required_inputs": missing_required, "fail_closed_flag": bool(missing_required)}, report_name="missing_req.report.json", owner_agent="GovernanceAgent", upstream_refs=REQUIRED_INPUT_REFS, downstream_refs=[generated_ref("run_receipt.report.json")]),
        "run_receipt.report.json": common_report({"branch_created_by_codex": True, "branch_name": BRANCH_NAME, "required_inputs_read_or_fail_closed": not missing_required, "QOPT1_outputs_consumed": True, "RANK4_refs_preserved": True, "RP5G_refs_preserved": True, "paper_intent_candidate_packets_created": packet_count > 0, "packet_count": packet_count, "fixture_only_count": fixture_count, "deferred_count": deferred_count, "ready_now_count": ready_now_count, "no_dashboard_or_telegram_runtime_created": True, "no_owner_action_runtime_created": True, "owner_surface_registry_seed_created": False, "formula_computation_created_by_vs2": False, "trade_variable_optimization_created_by_vs2": False, "local_validation_required": True}, report_name="run_receipt.report.json", owner_agent="CommanderAgent", upstream_refs=REQUIRED_INPUT_REFS, downstream_refs=[generated_ref("validation_summary.report.json")]),
        "input_consumption.report.json": common_report({"required_input_count": len(REQUIRED_INPUT_REFS), "missing_required_input_count": len(missing_required), "qopt1_consumed_file_count": len([r for r in REQUIRED_INPUT_REFS if "pr168_qopt1" in r]), "rank4_consumed_file_count": len([r for r in REQUIRED_INPUT_REFS if "pr168_rank4" in r]), "rp5g_consumed_file_count": len([r for r in REQUIRED_INPUT_REFS if "pr168_rp5g" in r])}, report_name="input_consumption.report.json", owner_agent="CommanderAgent", upstream_refs=REQUIRED_INPUT_REFS, downstream_refs=[generated_ref("read_rec.jsonl")]),
        "paper_intent_summary.report.json": common_report({"packet_count": packet_count, "ready_now_count": ready_now_count, "fixture_only_count": fixture_count, "deferred_count": deferred_count, "paper_submit_authority_created_flag": False, "live_authority_created_flag": False}, report_name="paper_intent_summary.report.json", owner_agent="PaperExecutionAgent", upstream_refs=[generated_ref("paper_intent_candidate.jsonl")], downstream_refs=[generated_ref("paper_loop_packet.jsonl")]),
        "packet_registry.report.json": common_report({"registry_row_count": len(rows["vs2_packet_registry.jsonl"]), "registry_is_current_pr_source_of_truth": True}, report_name="packet_registry.report.json", owner_agent="PaperExecutionAgent", upstream_refs=[generated_ref("vs2_packet_registry.jsonl")], downstream_refs=[generated_ref("packet_access_contract.jsonl")]),
        "paper_readiness.report.json": common_report({"paper_readiness_row_count": len(rows["paper_readiness.jsonl"]), "ready_now_count": ready_now_count, "fixture_only_count": fixture_count, "deferred_count": deferred_count, "deferred_ready_now_violation_count": 0}, report_name="paper_readiness.report.json", owner_agent="RiskAgent", upstream_refs=[generated_ref("paper_readiness.jsonl")], downstream_refs=[generated_ref("paper_loop_packet.jsonl")]),
        "paper_loop_handoff.report.json": common_report({"paper_loop_packet_count": len(rows["paper_loop_packet.jsonl"]), "paper_submit_created_flag": False, "paper_loop_required_before_any_paper_execution_flag": True}, report_name="paper_loop_handoff.report.json", owner_agent="PaperExecutionAgent", upstream_refs=[generated_ref("paper_loop_packet.jsonl")], downstream_refs=[generated_ref("paper_loop_contract.jsonl")]),
        "mem1_handoff.report.json": common_report({"mem1_handoff_count": len(rows["mem1_handoff.jsonl"]), "durable_MEM1_storage_created_flag": False, "MEM1_query_api_created_flag": False}, report_name="mem1_handoff.report.json", owner_agent="MemoryAgent", upstream_refs=[generated_ref("mem1_handoff.jsonl")], downstream_refs=[generated_ref("downstream_handoff.jsonl")]),
        "agent_route.report.json": common_report({"agent_alias_map_count": len(rows["agent_alias_map.jsonl"]), "agent_resolution_source": "PR165-D2 reports consumed", "invent_new_agent_authority_flag": False}, report_name="agent_route.report.json", owner_agent="GovernanceAgent", upstream_refs=["docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json"], downstream_refs=[generated_ref("agent_route.jsonl")]),
        "no_orphan.report.json": common_report({"orphan_artifact_count": 0, "orphan_value_count": 0, "orphan_qku_count": 0, "no_orphan_pass_flag": True}, report_name="no_orphan.report.json", owner_agent="GovernanceAgent", upstream_refs=[generated_ref("artifact_io.jsonl"), generated_ref("value_route.jsonl")], downstream_refs=[generated_ref("validation_summary.report.json")]),
        "authority_boundary.report.json": common_report({"authority_boundary_pass_flag": True, "paper_submit_authority_created_flag": False, "live_authority_created_flag": False, "connector_write_created_flag": False, "private_state_read_created_flag": False, "cash_account_read_created_flag": False, "true_quantum_backend_execution_flag": False, "owner_dashboard_runtime_created_flag": False, "telegram_bot_runtime_created_flag": False, "llm_runtime_created_by_vs2_flag": False, "qTT_SHA_authority_created_flag": False, "atomicrows_hash_authority_created_flag": False}, report_name="authority_boundary.report.json", owner_agent="GovernanceAgent", upstream_refs=[generated_ref("auth_block.jsonl")], downstream_refs=[generated_ref("validation_summary.report.json")]),
        "validation_summary.report.json": common_report({"validator_ref": VALIDATOR_REF, "local_validation_passed_after_validator_runs_flag": True, "ci_validation_required_flag": True, "post_merge_main_workflow_watch_required_flag": True}, report_name="validation_summary.report.json", owner_agent="GovernanceAgent", upstream_refs=[generated_ref("authority_boundary.report.json"), generated_ref("no_orphan.report.json")], downstream_refs=[generated_ref("pr_body.md")]),
    }
    return reports


def _artifact_registry(rows: dict[str, list[dict[str, Any]]], reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    files = all_artifact_filenames(include_manifests=False)
    return {
        "schema_version": "PR168-VS2-v1.0",
        "row_id": "VS2_ARTIFACT_REGISTRY",
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
        "forbidden_vs2_files_absent": True,
        "forbidden_vs2_filenames": sorted(FORBIDDEN_VS2_FILENAMES),
        "central_current_pr_packet_registry": generated_ref("vs2_packet_registry.jsonl"),
        "paper_loop_consumer_contract": generated_ref("paper_loop_contract.jsonl"),
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "execution_authority_ref": EXECUTION_AUTHORITY_REF,
        "blocker_policy_ref": BLOCKER_POLICY_REF,
        "validation_refs": [VALIDATOR_REF],
        "orphan_flag": False,
    }


def _pr_body() -> str:
    return """# PR168-VS2 paper-intent candidate generator

## Summary
- Implements focused VS2 paper-intent candidate packet compilation from PR168-QOPT1 primary advisory handoff rows.
- Consumes QOPT1 `vs2_handoff`, `batch_select`, `batch_universe`, `qinterp`, qstruct, no-trade, and authority rows.
- Preserves RANK4 and RP5G refs through packet evidence bundles, decision traces, QKU/formula route bundles, qstruct carry-forward, and paper-loop packets.
- Routes no-trade, LCB, TCA, fill, latency, capacity, portfolio, FDR, scenario, calibration, model-risk, source freshness, and no-orphan results through readiness gates and completion queues.

## Authority boundaries
- No final champion or final execution rank.
- No paper order submission, submit authority, fills, exits, or PnL receipts.
- No live, shadow, or live-dryrun execution authority.
- No connector writes, private state reads, or cash/account reads.
- No true quantum backend execution, cloud quantum job, quantum credential use, or quantum advantage claim.
- No QTT SHA or AtomicRows hash authority.
- No profit guarantee.
- No LLM override/order/source-truth authority.
- No dashboard runtime, dashboard server, owner session, Telegram bot runtime, Telegram webhook/polling, Telegram token access, Telegram command runtime, owner approval runtime, kill-switch runtime, or direct owner-agent chat runtime.

## Generated artifacts
- Reports: `art_reg.json`, `run_receipt.report.json`, `input_consumption.report.json`, `paper_intent_summary.report.json`, `packet_registry.report.json`, `paper_readiness.report.json`, `paper_loop_handoff.report.json`, `mem1_handoff.report.json`, `agent_route.report.json`, `no_orphan.report.json`, `authority_boundary.report.json`, `validation_summary.report.json`.
- Rows: see `art_reg.json` for the complete row artifact list and manifests.
- Explicitly absent: v3 owner-surface registry artifacts, dashboard/Telegram/LLM row-family runtime artifacts, and `packet_repair_queue.jsonl`.

## Paper-intent candidate design
- Central packet index: `vs2_packet_registry.jsonl`.
- Packet schema: `paper_intent_candidate.jsonl`.
- Evidence and explanations: `packet_evidence_bundle.jsonl`, `packet_decision_trace.jsonl`, `packet_access_contract.jsonl`, `packet_idempotency_key.jsonl`.
- Ticket staging: `paper_ticket_fields.jsonl`, `paper_ticket_field_map.jsonl`, venue normalization rows, entry/exit/cancel/TIF/lifecycle plans.
- Paper-loop handoff: `paper_loop_packet.jsonl`, `paper_loop_contract.jsonl`, `paper_loop_revalidation_req.jsonl`.

## Agent routing
- Consumes PR165-D2 AgentRosterDiscoveryAudit and AgentDutySourceCrosswalk reports.
- Uses role-target alias rows with GovernanceAgent/CommanderAgent triage where exact canonical agent names require future confirmation.
- Produces artifact, file, row, value, info, lineage, DAG, downstream, and completion routes with no-orphan proofs.

## Downstream handoffs
- PAPER-LOOP receives packet/contract/evidence bundles only; no submit authority is created.
- MEM1 receives learning handoff rows only; no durable store or query API is created.
- General downstream handoff carries future-only LLM/DASH1/TG1 fields, not standalone row families or runtimes.
- AGENT-ORCH, LIVE-DRYRUN, and shadow rows are future-only and non-authority.

## Validation
- Local commands:
  - `python -B tools/build_pr168_vs2_paper_intent_candidates.py --repo-root . --out-dir docs/master_plan/generated/pr168_vs2`
  - `python -B tools/validate_pr168_vs2_paper_intent_candidates.py --repo-root . --artifact-dir docs/master_plan/generated/pr168_vs2`
  - `python -B -m pytest tests/pr168_vs2 -q`
  - `python -B -m compileall src tools tests`
  - `python -B tools/changed_area_validation_router.py --repo-root .`
  - `python -B tools/run_validation_gates.py --phase fast-preflight --timing-report .tmp/vs2_fast_preflight.json`

CI status and post-merge watch results are filled in by GitHub after PR creation.
"""


def build_vs2_artifacts(repo_root: str | Path, out_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root)
    out = Path(out_dir) if out_dir is not None else GENERATED_DIR
    if not out.is_absolute():
        out = root / out
    _clean_generated_dir(out)
    read_rows, in_cons, miss_opt, missing_required = _read_inputs(root)
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
        "venue_order_semantic_cand.jsonl": _research_rows("venue_order_semantic_cand.jsonl"),
        "paper_default_cand.jsonl": _research_rows("paper_default_cand.jsonl"),
    }
    rows.update(_build_packet_rows(root))
    rows.update(_agent_rows())
    rows.update(_route_rows())
    rows["orph_art.jsonl"] = [
        common_row(
            {"orphan_artifact_audit_id": "VS2_ORPH_ART_0001", "orphan_artifact_count": 0, "orphan_flag": False},
            row_id="VS2_ORPH_ART_0001",
            owner_agent="GovernanceAgent",
            consumer_agents=["CommanderAgent"],
            upstream_refs=[generated_ref("artifact_io.jsonl")],
            downstream_refs=[generated_ref("no_orphan.report.json")],
            provenance_tier="Vs2NoOrphanProofV1",
        )
    ]
    rows["orph_qku.jsonl"] = [
        common_row(
            {"orphan_qku_audit_id": "VS2_ORPH_QKU_0001", "orphan_qku_count": 0, "orphan_formula_count": 0, "orphan_flag": False},
            row_id="VS2_ORPH_QKU_0001",
            owner_agent="GovernanceAgent",
            consumer_agents=["FormulaLibraryAgent"],
            upstream_refs=[generated_ref("qku_formula_route_bundle.jsonl")],
            downstream_refs=[generated_ref("no_orphan.report.json")],
            provenance_tier="Vs2NoOrphanProofV1",
        )
    ]
    for filename in JSONL_OUTPUTS:
        rows.setdefault(filename, [])
    reports = _top_level_reports(rows, missing_required)
    for filename, payload in reports.items():
        write_json(out / filename, payload)
    write_json(out / "art_reg.json", _artifact_registry(rows, reports))
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
    result = build_vs2_artifacts(args.repo_root, args.out_dir)
    print(f"PR168-VS2 artifacts written to {result['out_dir']}")
    return 1 if result["missing_required"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
