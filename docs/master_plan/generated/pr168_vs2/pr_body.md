# PR168-VS2 paper-intent candidate generator

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
