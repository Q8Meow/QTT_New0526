# PR168-RP5G: Trade-plan replay/paper simulation engine

## Summary
This PR implements PR168-RP5G replay/paper trade-plan simulation evidence.
It does not create paper submit authority, live order authority, source-fact acceptance, connector writes, private-state reads, cash-account reads, final ranking, final champion selection, QOPT execution, quantum backend execution, quantum advantage proof, QTT SHA authority, AtomicRows SHA/hash authority, or profit guarantees.

RP5G is the next PR after RP5F because RP5F produced snapshot-conditioned targets, grids, trade seeds, edge-input surfaces, stale/revalidation policies, and non-authority handoffs. RP5G consumes those rows and computes replay/paper simulation evidence without mutating immutable QKUs or formulas.

## Files Changed
- New package: `src/qtt/stage1_prediction_markets/pr168_rp5g_trade_plan_sim/`
- New tools: `tools/build_pr168_rp5g_trade_plan_sim.py`, `tools/validate_pr168_rp5g_trade_plan_sim.py`
- New tests: `tests/pr168_rp5g/`
- Validation routing updates: `tools/run_validation_gates.py`, `tools/validation_inventory.py`, `tools/validation_scope_registry.py`
- Generated artifacts: `docs/master_plan/generated/pr168_rp5g/`

## Generated Artifact Families
- Owner question proof: `owner_q1_edge.jsonl`, `owner_q2_route.jsonl`, `owner_q3_auto_path.jsonl`
- Numeric simulation evidence: `trade_candidate.jsonl`, `exec_pnl.jsonl`, `tca_decomp.jsonl`, `fill_latency_cap.jsonl`, `scenario_ladder.jsonl`, `notrade_cmp.jsonl`
- Edge attribution and objective decomposition: `edge_attr.jsonl`, `obj_decomp.jsonl`, `topk_sim.jsonl`
- Quantum structural readiness: `qstruct_problem.jsonl`, `qobj_coeff.jsonl`, `q_constraints.jsonl`, `q_interp.jsonl`, `q_classic_fb.jsonl`
- No-orphan routing: `value_route.jsonl`, `row_route.jsonl`, `file_route.jsonl`, `no_orphan.report.json`
- Order automation non-authority handoffs: `order_auto_path.jsonl`, `live_shadow_handoff.jsonl`, `auth_block.jsonl`, `order_ready_prev.jsonl`

## Upstream Inputs Consumed
RP5G consumes RP5F targets, grids, seeds, TCA/fill/latency/capacity inputs, QKU compute routes, quantum grid routes, and no-stale/pre-submit revalidation rows. It also consumes RP5C/VS1/RP5D/RP5E/RP5D-R1 generated surfaces and PR165-D2 agent-duty artifacts.

## Downstream Handoffs Created
RP5G emits non-authority handoffs to RANK4, QOPT1, VS2, MEM1, AGENT-ORCH1, PAPER-LOOP, PR170 LIVE-DRYRUN, and triggered shadow observation. Every handoff keeps `paper_authority_flag`, `live_authority_flag`, `shadow_authority_flag`, `order_authority_flag`, `connector_write_flag`, `private_state_fetch_flag`, and `cash_account_read_flag` false.

## Agent Routing and PR165-D2 Consumption Proof
`agent_duty_map.jsonl`, `agent_alias_map.jsonl`, `agent_route.jsonl`, `agent_consume.jsonl`, `agent_intel.jsonl`, and `agent_task.jsonl` map RP5G work to discovered PR165-D2-compatible roles. `owner_q2_route.jsonl` and `no_orphan.report.json` prove owner, consumer, validator, authority-boundary, and completion routes for files, rows, values, QKUs, formulas, connectors, and handoffs.

## Computability State Proof
`qku_compute_state.jsonl`, `formula_compute_state.jsonl`, `stack_compute_state.jsonl`, `trade_compute_state.jsonl`, `qku_comp.jsonl`, `formula_comp.jsonl`, `stack_comp.jsonl`, and `compute_completion_route.jsonl` show computability states and deterministic compute receipts. Classification alone is not used as proof.

## Execution-Adjusted Numeric Evidence Proof
- RP5F trade seeds consumed: 5
- TradePlanCandidate rows: 5
- Simulation result rows: 5
- Proxy simulated positives: 2
- Proxy simulated negatives: 3
- Candidates beating no-trade by provenance tier: 2 `SYNTHETIC_PROXY_FIXTURE`, 0 real replay/current-market
- Candidates failing no-trade by provenance tier: 3 `SYNTHETIC_PROXY_FIXTURE`
- Real replay/current-market labels: 0, because RP5G uses repo-local deterministic fixture/proxy provenance only in this PR.
- Proxy-only candidates forbidden from real profit proof: 5

## TCA / Fill / Latency / Capacity Proof
`tca_decomp.jsonl` computes fees, spread, slippage, latency, market impact, opportunity cost, cancel/replace cost, and cashflow/settlement capital-lock cost. `fill_latency_cap.jsonl`, `queue_fill_result.jsonl`, `adverse_select_result.jsonl`, `latency_decay.jsonl`, `capacity_crowding.jsonl`, and `cash_settle_result.jsonl` compute fill probability, partial-fill ratio, queue penalties, adverse selection, latency decay, capacity, crowding, and settlement adjustments for every candidate.

## Overfit/FDR / Calibration / Scenario Ladder Proof
`overfit_fdr.jsonl`, `search_family_fdr.jsonl`, `false_discovery_audit.jsonl`, `wf_purge.jsonl`, `lockbox.jsonl`, `trial_count.jsonl`, and `model_risk.jsonl` materialize search-family trial counts, effective trial counts, purged walk-forward, lockbox, and model-risk controls. `calibration_result.jsonl`, `calibration_bucket.jsonl`, and `scenario_ladder.jsonl` compute calibration gaps and required scenario families for every candidate.

## Portfolio Utility / Capacity/Crowding Proof
`port_marg_util.jsonl`, `portfolio_utility.jsonl`, `marg_util.jsonl`, `cap_crowd.jsonl`, `capacity_limit.jsonl`, `crowding_limit.jsonl`, `clone_cluster.jsonl`, `near_clone_cluster.jsonl`, `exposure_budget.jsonl`, and `exposure_delta.jsonl` compute marginal utility, capacity consumption, capital consumption, concentration penalties, near-clone penalties, and exposure deltas without private account reads.

## Quantum Structural Readiness Proof
`qstruct_problem.jsonl`, `qobj_coeff.jsonl`, `q_constraints.jsonl`, `q_interp.jsonl`, `q_classic_fb.jsonl`, `q_quality.jsonl`, `q_penalty.jsonl`, `q_scale.jsonl`, `q_counterfactual.jsonl`, and `q_influence_handoff.jsonl` include objective coefficients, constraints, penalty weights, coefficient scale, interpret-back maps, classical fallback, and future QOPT1 handoffs. QOPT execution, quantum backend execution, and quantum advantage claims are all false.

## No-Orphan Proof
`artifact_io.jsonl`, `file_route.jsonl`, `lineage.jsonl`, `dag.jsonl`, `value_route.jsonl`, `row_route.jsonl`, `info_route.jsonl`, `user_route.jsonl`, `conn_route.jsonl`, `handoff_route.jsonl`, `orph_art.jsonl`, `orph_qku.jsonl`, and `no_orphan.report.json` show zero orphan artifacts, QKUs, formulas, values, and handoffs.

## No-Authority / No-SHA / No-Live Proof
All paper/live/shadow/order/connector/private-state/cash/source-fact/QOPT/quantum backend/advantage/profit authority counts remain zero. Formula and QKU mutation/global-ban counts remain zero.
`no_auth.jsonl`, `auth_block.jsonl`, `agent_authority_block.jsonl`, `no_sha.jsonl`, `no_mut.jsonl`, `no_meta.jsonl`, `outcome_proof.jsonl`, and `run_receipt.report.json` enforce the boundary. Git/GitHub SHAs are VCS metadata only and are not QTT, AtomicRows, checksum, freeze, digest, or artifact authority.

## Validation Commands and Results
- PASS: `.\.venv\Scripts\python.exe -B tools\build_pr168_rp5g_trade_plan_sim.py --out docs/master_plan/generated/pr168_rp5g --timeout-ms 3600000`
- PASS: `.\.venv\Scripts\python.exe -B tools\validate_pr168_rp5g_trade_plan_sim.py --generated docs/master_plan/generated/pr168_rp5g --timeout-ms 3600000`
- PASS: `.\.venv\Scripts\python.exe -m pytest tests\pr168_rp5g -q`
- PASS: `.\.venv\Scripts\python.exe -m compileall -q src\qtt\stage1_prediction_markets\pr168_rp5g_trade_plan_sim tools\build_pr168_rp5g_trade_plan_sim.py tools\validate_pr168_rp5g_trade_plan_sim.py`
- PASS: `.\.venv\Scripts\python.exe -m pytest tests\tools\test_validation_scope_registry.py tests\tools\test_validation_inventory.py tests\tools\test_changed_area_validation_router.py -q`
- PASS: `.\.venv\Scripts\python.exe -B tools\run_validation_gates.py --phase fast-preflight --timing-report .tmp\qtt-validation-timing\fast-preflight-rp5g.json --router-report .tmp\qtt-validation-routing\fast-preflight-rp5g.json`
- PASS: `.\.venv\Scripts\python.exe -B tools\run_validation_gates.py --phase deterministic-validators --timing-report .tmp\qtt-validation-timing\deterministic-rp5g.json --router-report .tmp\qtt-validation-routing\deterministic-rp5g.json`

## CI Debug Actions If Any
CI repair commits updated validation-router temp-output handling for RP5G `--out` and `--generated` paths, made RP5G generator/validator deterministic against routed temp directories, made deterministic branch-scope routing recognize GitHub Actions detached PR head refs, currentized the PR152 global consistency audit, and reran the failed affected-scope checks.

## Post-Merge Main Workflow Watch Result
Pending until the PR is merged. `run_receipt.report.json` records that the post-merge main workflow watch is required.
