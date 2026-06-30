# PR168-QOPT1 quantum/classical trade-plan batch optimization

## Summary
- Implements deterministic, portfolio-aware advisory batch optimization over RANK4-ranked RP5G TradePlanCandidateV1 evidence.
- Consumes RANK4 rank/score/component/no-trade/TCA/fill/latency/capacity/portfolio/FDR/scenario/memory/QOPT handoff rows and RP5G simulation/economic/quantum structural rows.
- Produces optimized advisory batches, no-trade reoptimization routes, positive-edge mining, profit-gap closure, scenario and latency-profit frontiers, candidate ablation, agent work queues, deterministic classical fallbacks, and canonical quantum structural objects.
- Primary advisory batch: `QOPT1_BATCH_PRIMARY_0001` with candidates `['RP5G_CAND_0001', 'RP5G_CAND_0004']`.

## Authority boundaries
- No final champion, final trade rank for execution, paper order intent, paper submit authority, live/shadow/live-dryrun execution authority, connector writes, private state or cash/account reads, true quantum backend execution, cloud quantum job, quantum credential use, quantum advantage claim, QTT SHA or AtomicRows hash authority, or profit guarantee.

## Generated artifacts
- Reports: 13 compact reports plus `art_reg.json`.
- Row artifacts: 169 JSONL families with manifests.

## Optimization methods
- Deterministic constraint-filtered greedy, bounded beam/frontier search, deterministic local-search fallback, optional-MILP structural route, solver cascade arbitration, robust/stress/control baselines, constraint binding/shadow-price/Lagrangian diagnostics, and hotpath/coldpath budget rows.
- Objective terms include net PnL, LCB, no-trade margin, TCA, fill, latency, capacity, portfolio utility, FDR, scenario, calibration, memory prior, model risk, capital lock, tail proxy, and quantum structural quality.
- No-trade is a capital-preservation comparator and reoptimization trigger, never a terminal dead end.

## Quantum structural readiness
- QUBO/BQM/CQM/QuadraticProgram/Ising structural objects include variables, objective coefficients, constraints, penalties, coefficient scaling, feasibility energy gap, interpret-back maps, and classical fallback references.
- Future backend hints are structural only and require strong classical-baseline dominance in later PRs.

## Agent routing and downstream handoffs
- PR165-D2 agent-duty artifacts are consumed.
- VS2 handoff is candidate-only; MEM1 handoff is memory-prior-only; PAPER/LIVE-DRYRUN/SHADOW handoffs are future-only.

## Validation
- Local commands: `tools/build_pr168_qopt1_batch_optimization.py`, `tools/validate_pr168_qopt1_batch_optimization.py`, `pytest tests/pr168_qopt1`, validation-scope pytest, `compileall`, changed-area router, and fast preflight.
- CI status and post-merge watch are completed after checks pass and merge.
