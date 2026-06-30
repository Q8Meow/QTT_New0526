# PR168-RANK4 execution-adjusted advisory trade-plan ranking

## Summary
- Implements deterministic execution-adjusted advisory ranking over RP5G trade-plan evidence.
- Consumes RP5G candidates, simulation runs, execution-adjusted PnL, TCA, fill/latency/capacity, no-trade, FDR, scenario, portfolio, calibration, quantum structural, and no-orphan routing ledgers.
- Produces advisory rank rows, score components, Pareto/dominance rows, no-trade dominance rows, champion/challenger advisory previews, QOPT/VS2/MEM1/PAPER/ORCH/live-dry/shadow non-authority handoffs, memory-ready recipe handoffs, model-risk/OPE/bandit hints, source-rights rows, and no-orphan/authority proof.
- Top advisory candidate in this deterministic run: `RP5G_CAND_0001`.

## Authority boundaries
- No final champion, final trade rank for execution, paper order intent, paper submit authority, live/shadow/live-dryrun execution authority, connector writes, private state or cash/account reads, QOPT execution, quantum backend execution, quantum advantage claim, QTT SHA or AtomicRows hash authority, or profit guarantee.

## Generated artifacts
- Reports: 13 compact reports plus `art_reg.json`.
- Row artifacts: 124 JSONL families with manifests.

## Agent routing
- Consumes PR165-D2 agent-duty inputs and writes agent alias, duty, consume, no-orphan, value-route, file-route, row-route, lineage, DAG, and user/connector future route proof ledgers.

## Memory-ready recipe handoff
- Context signatures, similarity keys, winning recipe handoffs, winner attribution, negative memory/cooldown/drift/retest hints, recipe prior hints, and batch-policy hints are fast-start priors only.
- Durable MEM1 storage/query APIs are not created in RANK4.
- Exit/sell/close/settlement/realized-PnL receipts are future-stage requirements only.

## v6 model-risk / external-candidate / learning / automatic-path hints
- External values are candidate-only, never source facts or live defaults.
- Source-rights/provenance rows, model-risk and uncertainty-reserve rows, OOS/lockbox hints, contextual-bandit/OPE hints, reward decomposition, latency-SLA, constraint-tightness, recipe TTL, best-next-action, auto-trading path, and shadow-route rows are non-authority.

## Validation
- Local commands: `tools/build_pr168_rank4_advisory_ranking.py`, `tools/validate_pr168_rank4_advisory_ranking.py`, `pytest tests/pr168_rank4`, `compileall`, changed-area router, and fast preflight.
- CI status and post-merge watch are completed after PR checks pass and merge.
