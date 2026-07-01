# PR168-MEM1 condition-scoped outcome memory

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
