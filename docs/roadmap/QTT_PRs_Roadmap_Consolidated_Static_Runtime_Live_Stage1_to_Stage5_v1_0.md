# QTT PRs Roadmap — Consolidated Static / Runtime / Live Architecture
Stage‑1 Prediction-Market Launch First; Future Stages for Crypto, Equities, Options/Futures, and Cross-Market Automation

| Field | Value |
| --- | --- |
| Roadmap version | v1.0_CONSOLIDATED_STATIC_RUNTIME_LIVE_STAGE1_PRIORITY |
| Created | 2026-05-12 |
| Owner authority | Owner remains sole final authority for QTT internal workflow behavior. |
| Primary launch focus | Stage 1 prediction markets: Kalshi, Polymarket, FORECASTEX_IBKR. |
| Current active next PR | PR #83 — Owner quantum priority policy registry. |
| Launch-essential estimate after PR #104 | 47 additional PRs for Stage‑1 launch closure: PR #105–#151. |
| Total roadmap through cross-market reserve | PR #63–#224, with PR #105–#224 added as new sequential expansion. |

This roadmap is guidance for owner/Codex planning. Implementation truth remains repository artifacts, schemas, validators, generated reports, authority boundaries, validation evidence, and owner-approved instructions. This document does not edit the master plan, create AtomicRows bundle/hash authority, retrieve or accept source facts, bind connector semantics, execute runtime/live trading, or claim profit/quantum advantage.

## 1. Source integration result
- Integrated the original post-repair roadmap after PR #76, including the delivery-label shift that made EDGE packet schema PR #77 and preserved PR numbers as delivery labels rather than implementation truth.
- Integrated the post-PR82 safe-architecture roadmap, especially PR #82–#92 ordering and disambiguation: quantum applicability, owner quantum priority, scoring policy, scoring/ranking contract, optimizer-arbitration contract, candidate generation, static selection, handoff, replay/paper static foundations, dual-result review, and owner live-promotion review.
- Integrated the 2nd roadmap updates that separate Static PRs, Runtime PRs, and Live PRs, and expanded them into a complete post-PR104 sequence instead of leaving QTT in a static-only state.
- Checked the current master plan alignment for Stage‑1 three-venue prediction-market scope, source-evidence gating, connector semantic binding, runtime cash receipts, replay/paper separation, owner review, limited live canary, low-latency live path, quantum no-direct-order authority, and future market sleeves.

## 2. Controlling architecture doctrine

| Category | Meaning | Examples | Boundary |
| --- | --- | --- | --- |
| Static PRs | Build verified contracts, schemas, policies, routing, scoring logic, candidate selection, and review gates. | PR #83–#104 plus earlier PR #77–#82 foundations. | No runtime execution, no live connector, no accepted source facts unless explicitly scoped, no order authority, no profit/advantage claim. |
| Runtime PRs | Implement replay, paper, source-evidence, connector-binding, market-data, cash, risk, quantum-precompute, dashboard, and monitoring engines that consume verified contracts. | PR #105–#140 and selected post-launch PRs. | May create runtime receipts only in its approved scope. Still no live order writes unless explicitly in Live PRs. |
| Live PRs | Connect venue APIs, submit/cancel/reduce orders, reconcile fills/cash, enforce kill switches, and run owner-approved canary/live trading. | PR #141–#151 for Stage‑1 launch; later live PRs for future markets. | Requires owner approval, accepted sources, connector bindings, runtime cash, risk gates, kill switch, venue health, and order lifecycle receipts. |

## 3. Master-plan alignment constraints that this roadmap preserves
- Stage‑1 prediction-market scope is Kalshi + Polymarket + FORECASTEX_IBKR. Parallel eligibility is not parallel live execution authority, and no venue may borrow another venue’s connector, cash, source, risk, or order-state gate.
- Later market sleeves remain dormant until owner-approved future stages: cryptocurrency, equities/stocks, options/futures, and cross-market automation. The roadmap uses Stage 2, Stage 3, Stage 4, and Stage 5 expansion blocks for those scopes.
- Source evidence remains upstream: retrieval target is not retrieval; retrieval is not accepted source evidence; accepted source packets still do not populate connector semantics by themselves.
- Connector values remain SOURCE_REQUIRED until accepted target-field source packet plus connector binding receipt exist. No venue fee, tick, payout, order, balance, cash, lifecycle, fill, PnL, latency, finality, reconciliation, or cross-venue normalization fact may be invented.
- Runtime cash without receipt blocks new or increased exposure. Unknown source, cash, or revalidation state blocks new or increased exposure.
- Replay and paper remain concurrent separate lanes after shared input lock. Replay/paper results cannot merge into owner approval, live eligibility, or profit proof automatically.
- Owner review is non-delegable. Limited live canary requires explicit owner command and all gates. Day‑1 launch readiness is not Day‑1 execution.
- Low-latency live path may consume only precomputed source-change, cash, market, and quantum artifact snapshots; it may not call source retrieval, source acceptance, LLM reasoning, external research, dashboard review, or quantum backend selection.
- Quantum may rank or propose replay/paper candidates and precomputed artifacts, but quantum agents/optimizers may not directly submit orders. Execution router remains final order submission authority.
- Owner override may satisfy internal QTT workflow policy only. It must not fabricate external facts, accepted source packets, connector facts, runtime cash receipts, order/fill receipts, replay/paper results, backend execution, quantum advantage evidence, latency/execution superiority evidence, alpha evidence, or profit evidence.

## 4. Market-stage rollout model

| Stage | Primary scope | Launch posture | Roadmap PR range |
| --- | --- | --- | --- |
| Stage 1 | Prediction markets: Kalshi, Polymarket, FORECASTEX_IBKR | Prioritized now. Build static → runtime → live canary → Day‑1 launch closure. | PR #83–#151 launch-essential; PR #152–#168 post-launch scale. |
| Stage 2 | Cryptocurrency market sleeve | Dormant until owner opens future-stage scope. Source/connector/custody/replay/live canary sequence required. | PR #169–#183. |
| Stage 3 | Equities / stock market sleeve | Dormant until owner opens future-stage scope. Broker/cash/margin/compliance gates required. | PR #184–#198. |
| Stage 4 | Options / futures / derivatives sleeve | Dormant until owner opens future-stage scope. Greeks, margin, assignment, settlement, and complex-order gates required. | PR #199–#216. |
| Stage 5 | Cross-market automation and capital allocation | Only after earlier sleeves are receipt-proven and owner-approved. | PR #217–#224. |

## 5. Current launch-readiness estimate

| Question | Roadmap answer |
| --- | --- |
| If Codex finishes PR #83–#104 only, is Stage‑1 live trading ready? | No. PR #83–#104 remain static/gated foundations, owner dashboard/approval foundations, AtomicRows preparation, and coverage expansion. |
| What is the minimum new Stage‑1 launch closure after PR #104? | 47 additional PRs: PR #105–#151. |
| What is the launch-essential count from current next PR #83? | 69 PRs: PR #83–#151. |
| What is the post-launch Stage‑1 robustness block? | 17 PRs: PR #152–#168. |
| What is the full staged expansion through future markets? | 142 PRs from current PR #83 through PR #224; 120 of those are post‑PR104 expansion PRs. |

## 6. Completed and current baseline summary through PR #82

| Delivery label | Title | Status |
| --- | --- | --- |
| PR #63 | AtomicRows parameter-agent binding command matrix | Completed before current checkpoint |
| PR #64 | QTT agent role duty and operating charter registry | Completed before current checkpoint |
| PR #65 | QTT algorithm and formula family registry | Completed before current checkpoint |
| PR #66 | QTT agent-algorithm binding registry | Completed before current checkpoint |
| PR #67 | QTT agent-algorithm consumer gate | Completed before current checkpoint |
| PR #68 | QTT agent-role and algorithm cumulative readiness gate | Completed before current checkpoint |
| PR #69 | QTT agent-role and algorithm command matrix | Merged |
| PR #70 | AtomicRows research provenance and evidence-tier classification | Merged |
| PR #71 | Owner-submitted research source intake registry | Merged |
| PR #72 | Research-source-to-AtomicRows candidate family gate | Merged |
| PR #73 | AtomicRows parameter-stack role taxonomy | Merged |
| PR #74 | AtomicRows parameter-stack completeness gate | Merged |
| PR #75 | AtomicRows parameter-stack compatibility gate | Merged |
| PR #76 | Pre-EDGE debug repair: shorten runtime resolver allowlist test path | Merged repair-only; no roadmap semantics changed |
| PR #77 | EDGE parameter stack selection packet schema | Completed in active sequence |
| PR #78 | QTT trade-context packet schema | Completed in active sequence |
| PR #79 | AtomicRows parameter selection universe registry | Completed in active sequence |
| PR #80 | Parameter selection universe consumer gate | Completed in active sequence |
| PR #81 | Trade-context-to-selection-universe routing gate | Completed in active sequence |
| PR #82 | Quantum applicability classification registry | Completed in active sequence; current next PR is #83 |

## 7. PR #83–#104 — Static launch-essential foundation sequence
These PRs are launch-essential static work. They make future runtime/live work safe and explicit, but they do not create live-trading readiness by themselves.

| PR | Category | Stage / priority | Title | Branch |
| --- | --- | --- | --- | --- |
| #83 | Static | S1 launch-essential static | Owner quantum priority policy registry | pr83-owner-quantum-priority-policy-registry |
| #84 | Static | S1 launch-essential static | Parameter and algorithm scoring policy registry | pr84-parameter-algorithm-scoring-policy-registry |
| #85 | Static | S1 launch-essential static | Parameter-stack scoring and ranking gate | pr85-parameter-stack-scoring-ranking-gate |
| #86 | Static | S1 launch-essential static | Quantum/classical optimizer arbitration gate | pr86-quantum-classical-optimizer-arbitration-gate |
| #87 | Static | S1 launch-essential static | Candidate parameter-stack generation gate | pr87-candidate-parameter-stack-generation-gate |
| #88 | Static | S1 launch-essential static | Trade-context parameter-stack selection gate | pr88-trade-context-parameter-stack-selection-gate |
| #89 | Static | S1 launch-essential static | Selected parameter-stack handoff packet | pr89-selected-parameter-stack-handoff-packet |
| #90 | Static | S1 launch-essential static | Replay/paper candidate stack competition gate | pr90-replay-paper-candidate-stack-competition-gate |
| #91 | Static | S1 launch-essential static | Dual-result review for parameter stacks | pr91-dual-result-review-parameter-stack-gate |
| #92 | Static | S1 launch-essential static | Owner live-promotion review for parameter stacks | pr92-owner-live-promotion-review-parameter-stack-gate |
| #93 | Static | S1 launch-essential static | Owner approval request queue registry | pr93-owner-approval-request-queue-registry |
| #94 | Static | S1 launch-essential static | Owner override receipt authoring gate | pr94-owner-override-receipt-authoring-gate |
| #95 | Static | S1 launch-essential static | Owner dashboard approval menu schema | pr95-owner-dashboard-approval-menu-schema |
| #96 | Static | S1 launch-essential static | Owner dashboard approval static screen contract | pr96-owner-dashboard-approval-static-screen-contract |
| #97 | Static | S1 launch-essential static | AtomicRows full bundle row expansion plan | pr97-atomicrows-full-bundle-row-expansion-plan |
| #98 | Static | S1 launch-essential static | AtomicRows bundle row-family source files | pr98-atomicrows-bundle-row-family-source-files |
| #99 | Static | S1 launch-essential static | AtomicRows bundle builder | pr99-atomicrows-bundle-builder |
| #100 | Static | S1 launch-essential static | AtomicRows bundle SHA/freeze authority | pr100-atomicrows-bundle-sha-freeze-authority |
| #101 | Static | S1 launch-essential static | AtomicRows full bundle final readiness gate | pr101-atomicrows-full-bundle-final-readiness-gate |
| #102 | Static | S1 launch-essential static | Master-plan section coverage triage expansion I | pr102-master-plan-section-coverage-triage-expansion-i |
| #103 | Static | S1 launch-essential static | Master-plan section coverage parent-capability consolidation | pr103-master-plan-section-coverage-parent-capability-consolidation |
| #104 | Static | S1 launch-essential static | Master-plan section coverage command matrix | pr104-master-plan-section-coverage-command-matrix |

### 7A. Detailed static PR definitions

#### PR #83 — Owner quantum priority policy registry
Category: Static | Stage: Stage 1 prediction-market foundation | Priority: S1 launch-essential static | Branch: pr83-owner-quantum-priority-policy-registry | Marker: QTT_OWNER_QUANTUM_PRIORITY_POLICY_REGISTRY_OK

| Purpose | Create deterministic owner-controlled quantum prioritization policy metadata for future scoring, ranking, and optimizer-arbitration gates. |
| --- | --- |
| Must prove | Owner priority is explicit, internal-only, deterministic, and bounded by future gates. |
| Must not create | Optimizer execution, backend/simulator execution, scoring, ranking, selection, source acceptance, connector binding, replay/paper/live/order authority, profit or advantage evidence. |
| Quantum / latency emphasis | Use QUANTUM_NEUTRAL, QUANTUM_PREFERRED, QUANTUM_STRONGLY_PREFERRED, QUANTUM_FIRST, OWNER_FORCED_QUANTUM, and HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK as static modes. |


#### PR #84 — Parameter and algorithm scoring policy registry
Category: Static | Stage: Stage 1 prediction-market foundation | Priority: S1 launch-essential static | Branch: pr84-parameter-algorithm-scoring-policy-registry | Marker: QTT_PARAMETER_AND_ALGORITHM_SCORING_POLICY_REGISTRY_OK

| Purpose | Define deterministic scoring formulas that consume PR #82 quantum applicability and PR #83 owner quantum priority. |
| --- | --- |
| Must prove | Formula registry only; quantum boost is deterministic and owner-policy-gated. |
| Must not create | Scoring execution, ranking, stack selection, optimizer arbitration, replay/paper/live execution, profit claims. |
| Quantum / latency emphasis | Formula includes quantum_applicability_score, owner_quantum_priority_boost, and quantum_boost, but no backend execution or advantage claim. |


#### PR #85 — Parameter-stack scoring and ranking gate
Category: Static | Stage: Stage 1 prediction-market foundation | Priority: S1 launch-essential static | Branch: pr85-parameter-stack-scoring-ranking-gate | Marker: QTT_PARAMETER_STACK_SCORING_AND_RANKING_GATE_OK

| Purpose | Define scoring/ranking contract over static candidate descriptors and fixtures. |
| --- | --- |
| Must prove | No random ranking; quantum-applicable stacks rank higher only when owner quantum priority permits it. |
| Must not create | Final selected stacks, optimizer arbitration, real generated-candidate claim, replay/paper/live execution, profit evidence. |
| Quantum / latency emphasis | Treat quantum weight as traceable policy metadata, not proof of quantum advantage. |


#### PR #86 — Quantum/classical optimizer arbitration gate
Category: Static | Stage: Stage 1 prediction-market foundation | Priority: S1 launch-essential static | Branch: pr86-quantum-classical-optimizer-arbitration-gate | Marker: QTT_QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_GATE_OK

| Purpose | Define static arbitration grammar for CLASSICAL_BASELINE, QUANTUM_CHALLENGER, HYBRID_COMPARE_THEN_SELECT, QUANTUM_FIRST, OWNER_FORCED_QUANTUM, and OWNER_FORCED_CLASSICAL. |
| --- | --- |
| Must prove | Classical and quantum outputs can be represented and compared in fixture form only. |
| Must not create | Classical optimizer execution, quantum backend/simulator execution, QAOA/VQE/annealing/QUBO/Ising execution, live routing, orders, profit calculation. |
| Quantum / latency emphasis | Prevents “quantum optimizer chose X” artifacts before verified runtime, replay/paper, and source gates exist. |


#### PR #87 — Candidate parameter-stack generation gate
Category: Static | Stage: Stage 1 prediction-market foundation | Priority: S1 launch-essential static | Branch: pr87-candidate-parameter-stack-generation-gate | Marker: QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE_OK

| Purpose | Generate deterministic candidate stack packets from routed universes, scoring policy metadata, and valid family memberships. |
| --- | --- |
| Must prove | Multiple candidate stacks exist deterministically before replay/paper competition. |
| Must not create | Final selection, replay/paper execution, live/order authority, random candidate generation, profit claims. |
| Quantum / latency emphasis | Include quantum-applicable candidate families and classical comparator candidates side by side. |


#### PR #88 — Trade-context parameter-stack selection gate
Category: Static | Stage: Stage 1 prediction-market foundation | Priority: S1 launch-essential static | Branch: pr88-trade-context-parameter-stack-selection-gate | Marker: QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE_OK

| Purpose | Select a deterministic static trade-context stack from generated candidates and ranking/arbitration metadata. |
| --- | --- |
| Must prove | selected_stack_id, score_breakdown, quantum_priority_applied, blocked_candidates, and reason_codes are traceable. |
| Must not create | Runtime orders, replay/paper execution, live routing, profit evidence, quantum advantage evidence. |
| Quantum / latency emphasis | Selection may prefer quantum metadata only through owner-approved policy and transparent score breakdown. |


#### PR #89 — Selected parameter-stack handoff packet
Category: Static | Stage: Stage 1 prediction-market foundation | Priority: S1 launch-essential static | Branch: pr89-selected-parameter-stack-handoff-packet | Marker: QTT_SELECTED_PARAMETER_STACK_HANDOFF_PACKET_OK

| Purpose | Carry selected-stack lineage to replay/paper and order-intent-adjacent layers while keeping order intent non-authoritative. |
| --- | --- |
| Must prove | Handoff is static and non-live; replay/paper and owner review remain downstream. |
| Must not create | Order submission, live routing, live reachability, replay/paper execution, profit claims. |
| Quantum / latency emphasis | Carry quantum lineage and comparator lineage for downstream testing. |


#### PR #90 — Replay/paper candidate stack competition gate
Category: Static | Stage: Stage 1 prediction-market foundation | Priority: S1 launch-essential static | Branch: pr90-replay-paper-candidate-stack-competition-gate | Marker: QTT_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE_OK

| Purpose | Define static replay/paper competition contracts for selected stacks. |
| --- | --- |
| Must prove | Replay and paper lanes are separate; competition metadata does not create results or pass/fail proof. |
| Must not create | Runtime replay/paper execution, live use, order authority, profit evidence. |
| Quantum / latency emphasis | Require quantum candidates and classical baselines to compete under equal replay/paper schema once runtime lanes exist. |


#### PR #91 — Dual-result review for parameter stacks
Category: Static | Stage: Stage 1 prediction-market foundation | Priority: S1 launch-essential static | Branch: pr91-dual-result-review-parameter-stack-gate | Marker: QTT_DUAL_RESULT_REVIEW_FOR_PARAMETER_STACKS_OK

| Purpose | Define static dual-result review contract for replay and paper outputs. |
| --- | --- |
| Must prove | No automatic live promotion; owner handoff remains required; synthetic fixtures may validate schema only. |
| Must not create | Fabricated replay/paper results, live promotion, owner approval, runtime order authority, alpha/profit/execution superiority evidence. |
| Quantum / latency emphasis | Review must preserve classical comparator results and not label quantum superiority without receipts. |


#### PR #92 — Owner live-promotion review for parameter stacks
Category: Static | Stage: Stage 1 prediction-market foundation | Priority: S1 launch-essential static | Branch: pr92-owner-live-promotion-review-parameter-stack-gate | Marker: QTT_OWNER_LIVE_PROMOTION_REVIEW_FOR_PARAMETER_STACKS_OK

| Purpose | Define owner-review input/output contracts for promotion requests. |
| --- | --- |
| Must prove | Agents may request; owner decides; no auto-promotion. |
| Must not create | Live order execution, source/connector/risk/runtime-cash/order-router bypass, automatic owner approval. |
| Quantum / latency emphasis | Owner can approve quantum-prioritized candidates internally, but this still creates no backend execution or live order. |


#### PR #93 — Owner approval request queue registry
Category: Static | Stage: Owner approval foundation | Priority: S1 launch-essential static | Branch: pr93-owner-approval-request-queue-registry | Marker: QTT_OWNER_APPROVAL_REQUEST_QUEUE_REGISTRY_OK

| Purpose | Canonical queue for QTT agents to request approval or override from the owner. |
| --- | --- |
| Must prove | Requests are typed, ordered, deterministic, and non-self-approving. |
| Must not create | Agent self-approval, live authority, fabricated owner decision. |
| Quantum / latency emphasis | Quantum-related promotion requests must show comparator lineage and no claimed advantage without evidence. |


#### PR #94 — Owner override receipt authoring gate
Category: Static | Stage: Owner approval foundation | Priority: S1 launch-essential static | Branch: pr94-owner-override-receipt-authoring-gate | Marker: QTT_OWNER_OVERRIDE_RECEIPT_AUTHORING_GATE_OK

| Purpose | File-based owner override receipt creation and validation for internal workflow requirements. |
| --- | --- |
| Must prove | Owner override can satisfy internal QTT workflow policy only. |
| Must not create | External fact invention, cash/order/fill receipt fabrication, source packet fabrication, backend execution fabrication. |
| Quantum / latency emphasis | Owner may force a quantum path internally but cannot fabricate backend output, replay/paper evidence, or profit evidence. |


#### PR #95 — Owner dashboard approval menu schema
Category: Static | Stage: Owner approval foundation | Priority: S1 launch-essential static | Branch: pr95-owner-dashboard-approval-menu-schema | Marker: QTT_OWNER_DASHBOARD_APPROVAL_MENU_SCHEMA_OK

| Purpose | Static schema for owner approval menu options and gate-visible requests. |
| --- | --- |
| Must prove | Menu options are typed and do not mutate runtime facts. |
| Must not create | Dashboard runtime service, trading authority, source fact rewriting. |
| Quantum / latency emphasis | Include quantum candidate/comparator review slots with no live-order authority. |


#### PR #96 — Owner dashboard approval static screen contract
Category: Static | Stage: Owner approval foundation | Priority: S1 launch-essential static | Branch: pr96-owner-dashboard-approval-static-screen-contract | Marker: QTT_OWNER_DASHBOARD_APPROVAL_STATIC_SCREEN_CONTRACT_OK

| Purpose | Static screen contract for owner-visible approvals, block reasons, and receipts. |
| --- | --- |
| Must prove | Screen payload is deterministic and traceable. |
| Must not create | Runtime dashboard service, live trading, fact mutation, Telegram trading authority. |
| Quantum / latency emphasis | Show quantum mode, quantum lineage, classical comparator status, and no-advantage-evidence flags. |


#### PR #97 — AtomicRows full bundle row expansion plan
Category: Static | Stage: AtomicRows bundle preparation | Priority: S1 launch-essential static | Branch: pr97-atomicrows-full-bundle-row-expansion-plan | Marker: QTT_ATOMICROWS_FULL_BUNDLE_ROW_EXPANSION_PLAN_OK

| Purpose | Plan full AtomicRows bundle expansion without creating bundle/hash authority. |
| --- | --- |
| Must prove | Row-family expansion is explicit and traceable. |
| Must not create | AtomicRows.bundle.jsonl, AtomicRows.bundle.sha256, SHA/freeze authority, live authority. |
| Quantum / latency emphasis | Ensure quantum advisory, QUBO/Ising/QAOA/VQE/annealing, and classical comparator families are represented. |


#### PR #98 — AtomicRows bundle row-family source files
Category: Static | Stage: AtomicRows bundle preparation | Priority: S1 launch-essential static | Branch: pr98-atomicrows-bundle-row-family-source-files | Marker: QTT_ATOMICROWS_BUNDLE_ROW_FAMILY_SOURCE_FILES_OK

| Purpose | Create row-family source files that can feed a later approved bundle builder. |
| --- | --- |
| Must prove | Source files preserve family provenance and compatibility gates. |
| Must not create | Canonical bundle/hash creation unless explicitly approved. |
| Quantum / latency emphasis | Quantum family rows remain inventory, not trading authority. |


#### PR #99 — AtomicRows bundle builder
Category: Static | Stage: AtomicRows bundle preparation | Priority: S1 launch-essential static | Branch: pr99-atomicrows-bundle-builder | Marker: QTT_ATOMICROWS_BUNDLE_BUILDER_OK

| Purpose | Create deterministic bundle builder mechanics under owner-controlled bundle policy. |
| --- | --- |
| Must prove | Builder deterministic; row inventory not a trader or source of authority. |
| Must not create | Bundle/hash authority unless the PR is explicitly scoped for it; no live authority. |
| Quantum / latency emphasis | Preserve quantum/classical inventory traceability for candidate generation. |


#### PR #100 — AtomicRows bundle SHA/freeze authority
Category: Static | Stage: AtomicRows bundle preparation | Priority: S1 launch-essential static | Branch: pr100-atomicrows-bundle-sha-freeze-authority | Marker: QTT_ATOMICROWS_BUNDLE_SHA_FREEZE_AUTHORITY_OK

| Purpose | Owner-approved bundle SHA/freeze authority surface if owner explicitly opens the bundle PR. |
| --- | --- |
| Must prove | Single JSONL bundle and SHA model are controlled and non-runtime. |
| Must not create | Unapproved freeze, unapproved SHA, source fact acceptance, live/order/profit authority. |
| Quantum / latency emphasis | Freeze quantum inventory only as parameter/algorithm inventory, not backend evidence. |


#### PR #101 — AtomicRows full bundle final readiness gate
Category: Static | Stage: AtomicRows bundle preparation | Priority: S1 launch-essential static | Branch: pr101-atomicrows-full-bundle-final-readiness-gate | Marker: QTT_ATOMICROWS_FULL_BUNDLE_FINAL_READINESS_GATE_OK

| Purpose | Validate AtomicRows bundle readiness before runtime/live phases consume selection inventory. |
| --- | --- |
| Must prove | Bundle readiness is explicit and fail-closed. |
| Must not create | Trading readiness, live execution, profit claims, automatic runtime unlock. |
| Quantum / latency emphasis | Quantum rows pass completeness/compatibility before optimizer/ranking consumers use them. |


#### PR #102 — Master-plan section coverage triage expansion I
Category: Static | Stage: Master-plan coverage expansion | Priority: S1 launch-essential static | Branch: pr102-master-plan-section-coverage-triage-expansion-i | Marker: QTT_MASTER_PLAN_SECTION_COVERAGE_TRIAGE_EXPANSION_I_OK

| Purpose | Map more master-plan sections into explicit capability, policy, source, replay, runtime, owner, quarantine, and retirement routes. |
| --- | --- |
| Must prove | Coverage routing improves without reintroducing old coverage ledger. |
| Must not create | Old coverage-ledger reintroduction, source fact acceptance, live authority. |
| Quantum / latency emphasis | Route quantum sections to quantum metadata, runtime, or backend scopes explicitly. |


#### PR #103 — Master-plan section coverage parent-capability consolidation
Category: Static | Stage: Master-plan coverage expansion | Priority: S1 launch-essential static | Branch: pr103-master-plan-section-coverage-parent-capability-consolidation | Marker: QTT_MASTER_PLAN_SECTION_COVERAGE_PARENT_CAPABILITY_CONSOLIDATION_OK

| Purpose | Group related default-routed sections under parent capabilities where logically correct. |
| --- | --- |
| Must prove | Traceability is preserved; no over-grouping. |
| Must not create | Loss of traceability, weakened owner authority, ambiguous runtime scope. |
| Quantum / latency emphasis | Keep quantum capability groups distinct: applicability, priority, optimizer, backend, artifact cache, comparator, no-live-submit. |


#### PR #104 — Master-plan section coverage command matrix
Category: Static | Stage: Master-plan coverage expansion | Priority: S1 launch-essential static | Branch: pr104-master-plan-section-coverage-command-matrix | Marker: QTT_MASTER_PLAN_SECTION_COVERAGE_COMMAND_MATRIX_OK

| Purpose | Command matrix for section coverage workstream and future PR planning. |
| --- | --- |
| Must prove | Codex can route section coverage commands without ambiguity. |
| Must not create | Old active coverage ledger, runtime/live/source/order/profit authority. |
| Quantum / latency emphasis | Command matrix separates quantum policy from backend execution and live trading. |


## 8. PR #105–#151 — Stage‑1 runtime/live launch closure
This is the new missing roadmap block. These PRs turn static contracts into executable non-live runtime systems and then into owner-approved, gate-proven live canary and Day‑1 launch mechanics for Kalshi, Polymarket, and FORECASTEX_IBKR.

| PR | Category | Priority | Title | Branch |
| --- | --- | --- | --- | --- |
| #105 | Runtime | S1 launch-essential runtime | Source-evidence retrieval executor | pr105-source-evidence-retrieval-executor |
| #106 | Runtime | S1 launch-essential runtime | Accepted source-evidence acceptance executor and ledger | pr106-accepted-source-evidence-acceptance-executor-and-ledger |
| #107 | Runtime | S1 launch-essential runtime | Source revalidation, supersession, and materiality scheduler | pr107-source-revalidation-supersession-and-materiality-scheduler |
| #108 | Runtime | S1 launch-essential runtime | Connector semantic binding implementation gate | pr108-connector-semantic-binding-implementation-gate |
| #109 | Runtime | S1 launch-essential runtime | Per-venue execution lifecycle model builder | pr109-per-venue-execution-lifecycle-model-builder |
| #110 | Runtime | S1 launch-essential runtime | Cross-venue execution normalization binding | pr110-cross-venue-execution-normalization-binding |
| #111 | Runtime | S1 launch-essential runtime | Runtime cash component field-map executor | pr111-runtime-cash-component-field-map-executor |
| #112 | Runtime | S1 launch-essential runtime | Account, wallet, balance, and private-state read receipt gate | pr112-account-wallet-balance-and-private-state-read-receipt-gate |
| #113 | Runtime | S1 launch-essential runtime | Credential alias and secret no-capture readiness gate | pr113-credential-alias-and-secret-no-capture-readiness-gate |
| #114 | Runtime | S1 launch-essential runtime | Venue market-data ingest adapters | pr114-venue-market-data-ingest-adapters |
| #115 | Runtime | S1 launch-essential runtime | Orderbook and event-state snapshot builder | pr115-orderbook-and-event-state-snapshot-builder |
| #116 | Runtime | S1 launch-essential runtime | Runtime resolver snapshot executor | pr116-runtime-resolver-snapshot-executor |
| #117 | Runtime | S1 launch-essential runtime | Historical dataset digest and loader | pr117-historical-dataset-digest-and-loader |
| #118 | Runtime | S1 launch-essential runtime | Replay engine executor | pr118-replay-engine-executor |
| #119 | Runtime | S1 launch-essential runtime | Paper trading engine executor | pr119-paper-trading-engine-executor |
| #120 | Runtime | S1 launch-essential runtime | Fill, cost, slippage, fee, tick, and latency simulator | pr120-fill-cost-slippage-fee-tick-and-latency-simulator |
| #121 | Runtime | S1 launch-essential runtime | Replay/paper result packet writer and immutable ledger | pr121-replay-paper-result-packet-writer-and-immutable-ledger |
| #122 | Runtime | S1 launch-essential runtime | Dual-result runtime comparator and promotion blocker | pr122-dual-result-runtime-comparator-and-promotion-blocker |
| #123 | Runtime | S1 launch-essential runtime | Prediction-market microstructure feature calibration runtime | pr123-prediction-market-microstructure-feature-calibration-runtime |
| #124 | Runtime | S1 launch-beneficial runtime | Neural signal walk-forward, calibration, and drift runtime | pr124-neural-signal-walk-forward-calibration-and-drift-runtime |
| #125 | Runtime | S1 launch-essential quantum runtime | Quantum provider capability receipts | pr125-quantum-provider-capability-receipts |
| #126 | Runtime | S1 launch-essential quantum runtime | Quantum problem compiler for QUBO, Ising, and portfolio/candidate-set representations | pr126-quantum-problem-compiler-for-qubo-ising-and-portfolio-candidate |
| #127 | Runtime | S1 launch-essential quantum runtime | Quantum-inspired and simulator challenger runner | pr127-quantum-inspired-and-simulator-challenger-runner |
| #128 | Runtime | S1 launch-beneficial quantum runtime | True quantum backend execution wrapper | pr128-true-quantum-backend-execution-wrapper |
| #129 | Runtime | S1 launch-essential quantum runtime | Quantum artifact cache, freshness, cost, noise, and latency model | pr129-quantum-artifact-cache-freshness-cost-noise-and-latency-model |
| #130 | Runtime | S1 launch-essential quantum runtime | Quantum-vs-classical comparator and regret ledger | pr130-quantum-vs-classical-comparator-and-regret-ledger |
| #131 | Runtime | S1 launch-essential quantum runtime | Low-latency quantum pretrade exclusion gate | pr131-low-latency-quantum-pretrade-exclusion-gate |
| #132 | Runtime | S1 launch-essential quantum runtime | Quantum fallback, rollback, and no-advantage-safe arbitration gate | pr132-quantum-fallback-rollback-and-no-advantage-safe-arbitration-gate |
| #133 | Runtime | S1 launch-essential runtime | Risk limit policy runtime validator | pr133-risk-limit-policy-runtime-validator |
| #134 | Runtime | S1 launch-essential runtime | Position, open-order, and exposure-lock ledger | pr134-position-open-order-and-exposure-lock-ledger |
| #135 | Runtime | S1 launch-essential runtime | Trade-intent compiler to non-live order-intent packet | pr135-trade-intent-compiler-to-non-live-order-intent-packet |
| #136 | Runtime | S1 launch-essential runtime | Pretrade gate matrix for source, cash, risk, latency, owner, and venue readiness | pr136-pretrade-gate-matrix-for-source-cash-risk-latency-owner-and-venu |
| #137 | Runtime | S1 launch-essential runtime | Runtime owner approval queue service and dashboard shell | pr137-runtime-owner-approval-queue-service-and-dashboard-shell |
| #138 | Runtime | S1 launch-essential runtime | Kill-switch runtime executor and emergency halt receipts | pr138-kill-switch-runtime-executor-and-emergency-halt-receipts |
| #139 | Runtime | S1 launch-essential runtime | Telemetry, latency, reject, throttle, and health monitor | pr139-telemetry-latency-reject-throttle-and-health-monitor |
| #140 | Runtime | S1 launch-essential runtime | Day-1 drill and canary rehearsal executor | pr140-day-1-drill-and-canary-rehearsal-executor |
| #141 | Live | S1 launch-essential live | Kalshi live connector binding and read-write surface | pr141-kalshi-live-connector-binding-and-read-write-surface |
| #142 | Live | S1 launch-essential live | Polymarket live connector binding and read-write surface | pr142-polymarket-live-connector-binding-and-read-write-surface |
| #143 | Live | S1 launch-essential live | FORECASTEX_IBKR live connector binding and read-write surface | pr143-forecastex-ibkr-live-connector-binding-and-read-write-surface |
| #144 | Live | S1 launch-essential live | Runtime live order command gate and venue enablement matrix | pr144-runtime-live-order-command-gate-and-venue-enablement-matrix |
| #145 | Live | S1 launch-essential live | Idempotent order lifecycle state machine | pr145-idempotent-order-lifecycle-state-machine |
| #146 | Live | S1 launch-essential live | Cancel, replace, reduce, close, and forced-exit safety state machine | pr146-cancel-replace-reduce-close-and-forced-exit-safety-state-machine |
| #147 | Live | S1 launch-essential live | Fill, cash, order, and settlement/finality reconciliation executor | pr147-fill-cash-order-and-settlement-finality-reconciliation-executor |
| #148 | Live | S1 launch-essential live | Limited live canary order router | pr148-limited-live-canary-order-router |
| #149 | Live | S1 launch-essential live | Post-canary safety review, kill-switch, rollback, and incident report | pr149-post-canary-safety-review-kill-switch-rollback-and-incident-repo |
| #150 | Live | S1 launch-essential live | Day-1 launch readiness gate and three-venue runbook | pr150-day-1-launch-readiness-gate-and-three-venue-runbook |
| #151 | Live | S1 launch-essential live | Stage-1 launch completion report and scale-up handoff | pr151-stage-1-launch-completion-report-and-scale-up-handoff |

### 8A. Detailed Stage‑1 runtime/live PR definitions

#### PR #105 — Source-evidence retrieval executor
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr105-source-evidence-retrieval-executor | Marker: QTT_SOURCE_EVIDENCE_RETRIEVAL_EXECUTOR_OK

| Purpose | Retrieve official source targets for Kalshi, Polymarket, and FORECASTEX_IBKR using owner-approved source classes; create candidate retrieval receipts only. |
| --- | --- |
| Must prove | Retrieval manifests, digests, quote/machine-field locators, and redaction rules are deterministic. |
| Must not create | Accepted source facts, connector semantics, live reachability, orders, profit claims. |
| Quantum / latency emphasis | Keep quantum backend/provider facts retrieval-gated; no provider capability invented. |


#### PR #106 — Accepted source-evidence acceptance executor and ledger
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr106-accepted-source-evidence-acceptance-executor-and-ledger | Marker: QTT_ACCEPTED_SOURCE_EVIDENCE_ACCEPTANCE_EXECUTOR_AND_LEDGER_OK

| Purpose | Convert complete retrieval packets into accepted source-evidence packets and target-field ledger rows only when exact scope, digest, locator, conflict, and revalidation fields pass. |
| --- | --- |
| Must prove | Accepted ledger rows are target-field-specific and conflict-checked. |
| Must not create | Connector semantic population, runtime cash claims, live reachability, replay/paper results, order authority. |
| Quantum / latency emphasis | Accepted quantum provider facts may label capability, not advantage or live output. |


#### PR #107 — Source revalidation, supersession, and materiality scheduler
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr107-source-revalidation-supersession-and-materiality-scheduler | Marker: QTT_SOURCE_REVALIDATION_SUPERSESSION_AND_MATERIALITY_SCHEDULER_OK

| Purpose | Enforce P1D live-critical, P7D low-risk, and event-triggered immediate source revalidation policy. |
| --- | --- |
| Must prove | Stale, superseded, conflicted, or material source changes block new binding/live use. |
| Must not create | Silent reuse of stale facts, connector rebinding without revalidation. |
| Quantum / latency emphasis | Quantum provider/backend capability packets get freshness and cost/noise revalidation hooks. |


#### PR #108 — Connector semantic binding implementation gate
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr108-connector-semantic-binding-implementation-gate | Marker: QTT_CONNECTOR_SEMANTIC_BINDING_IMPLEMENTATION_GATE_OK

| Purpose | Bind accepted target-field source packets into per-venue connector semantic records. |
| --- | --- |
| Must prove | Values remain SOURCE_REQUIRED until exact accepted packet and binding receipt exist. |
| Must not create | Invented venue fee/tick/order/balance/cash/lifecycle/fill/PnL/latency/finality/reconciliation facts. |
| Quantum / latency emphasis | Quantum-related connector use remains separate from order routing; no backend execution. |


#### PR #109 — Per-venue execution lifecycle model builder
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr109-per-venue-execution-lifecycle-model-builder | Marker: QTT_PER_VENUE_EXECUTION_LIFECYCLE_MODEL_BUILDER_OK

| Purpose | Build Kalshi, Polymarket, and FORECASTEX_IBKR execution lifecycle models from accepted source packets. |
| --- | --- |
| Must prove | Each venue has own submission, ack, match, fill, cancel/replace, settlement, cash, position, PnL, error/reject/throttle states. |
| Must not create | Borrowing Polymarket mechanics into Kalshi/FORECASTEX_IBKR or generic lifecycle as venue fact. |
| Quantum / latency emphasis | Enable fair latency and fill modeling for quantum/classical candidates. |


#### PR #110 — Cross-venue execution normalization binding
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr110-cross-venue-execution-normalization-binding | Marker: QTT_CROSS_VENUE_EXECUTION_NORMALIZATION_BINDING_OK

| Purpose | Create normalized comparison layer across the three prediction-market venues after per-venue bindings exist. |
| --- | --- |
| Must prove | Cross-venue comparability has per-venue semantic binding lineage. |
| Must not create | Arbitrage classification from apparent price gaps without execution normalization. |
| Quantum / latency emphasis | Allows optimizer to compare venues without assuming risk-free arbitrage. |


#### PR #111 — Runtime cash component field-map executor
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr111-runtime-cash-component-field-map-executor | Marker: QTT_RUNTIME_CASH_COMPONENT_FIELD_MAP_EXECUTOR_OK

| Purpose | Turn accepted account/balance/cash source semantics into runtime usable-cash component receipts. |
| --- | --- |
| Must prove | Unknown cash blocks new or increased exposure. |
| Must not create | Cash receipt fabrication, private-state fetch without authorized connector binding. |
| Quantum / latency emphasis | Quantum candidate sizing consumes only precomputed cash snapshots. |


#### PR #112 — Account, wallet, balance, and private-state read receipt gate
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr112-account-wallet-balance-and-private-state-read-receipt-gate | Marker: QTT_ACCOUNT_WALLET_BALANCE_AND_PRIVATE_STATE_READ_RECEIPT_GATE_OK

| Purpose | Create read-only account/wallet/balance/position/open-order receipt framework for each Stage-1 venue. |
| --- | --- |
| Must prove | Private-state reads are source-gated, credential-alias-gated, and receipt-bound. |
| Must not create | Order writes, secret capture, cash reuse before finality. |
| Quantum / latency emphasis | Latency-sensitive decisions use cached/precomputed state; no quantum backend in read path. |


#### PR #113 — Credential alias and secret no-capture readiness gate
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr113-credential-alias-and-secret-no-capture-readiness-gate | Marker: QTT_CREDENTIAL_ALIAS_AND_SECRET_NO_CAPTURE_READINESS_GATE_OK

| Purpose | Validate credential alias readiness without raw secret capture and without enabling live writes by default. |
| --- | --- |
| Must prove | Secret-like values are redacted; owner-controlled enablement is required per venue. |
| Must not create | Raw secret storage, accidental live write activation, credential-driven launch readiness claim. |
| Quantum / latency emphasis | Backend/API keys for quantum providers remain owner-enabled and non-live-trading. |


#### PR #114 — Venue market-data ingest adapters
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr114-venue-market-data-ingest-adapters | Marker: QTT_VENUE_MARKET_DATA_INGEST_ADAPTERS_OK

| Purpose | Implement read-only market data ingest for Kalshi, Polymarket, and FORECASTEX_IBKR after source/connector semantics are bound. |
| --- | --- |
| Must prove | Market-state timestamps, sequence/heartbeat, stale-data blocks, and venue-specific schemas exist. |
| Must not create | Trading decisions from stale or unbound data, order submission. |
| Quantum / latency emphasis | Quantum candidate precompute consumes snapshots, never live raw facts. |


#### PR #115 — Orderbook and event-state snapshot builder
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr115-orderbook-and-event-state-snapshot-builder | Marker: QTT_ORDERBOOK_AND_EVENT_STATE_SNAPSHOT_BUILDER_OK

| Purpose | Build immutable candidate market-state snapshots for replay/paper/runtime resolver. |
| --- | --- |
| Must prove | Snapshot identity, freshness, venue, market, orderbook, and event state are locked. |
| Must not create | Live orders, source retrieval, or LLM reasoning inside snapshot creation. |
| Quantum / latency emphasis | Snapshot is the low-latency input for classical/quantum comparison. |


#### PR #116 — Runtime resolver snapshot executor
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr116-runtime-resolver-snapshot-executor | Marker: QTT_RUNTIME_RESOLVER_SNAPSHOT_EXECUTOR_OK

| Purpose | Create resolver snapshots only after connector semantic bindings and input identity lock. |
| --- | --- |
| Must prove | Resolver cannot exist without per-venue bound semantics and locked market/cash/source inputs. |
| Must not create | Live order authority, source acceptance inside live path, unbound connector facts. |
| Quantum / latency emphasis | Resolver output can feed quantum/classical precompute but not direct backend/live calls. |


#### PR #117 — Historical dataset digest and loader
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr117-historical-dataset-digest-and-loader | Marker: QTT_HISTORICAL_DATASET_DIGEST_AND_LOADER_OK

| Purpose | Load and digest historical prediction-market datasets for replay lanes. |
| --- | --- |
| Must prove | Dataset identity, source lineage, schema, and immutability are explicit. |
| Must not create | Data leakage, unverified external repo live dependency, source fact invention. |
| Quantum / latency emphasis | Supports classical/quantum strategy comparison on the same historical basis. |


#### PR #118 — Replay engine executor
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr118-replay-engine-executor | Marker: QTT_REPLAY_ENGINE_EXECUTOR_OK

| Purpose | Run replay engine on locked historical inputs and selected stacks. |
| --- | --- |
| Must prove | Replay receipts are immutable and separate from paper receipts. |
| Must not create | Paper/live orders, owner approval, profit guarantee, auto-promotion. |
| Quantum / latency emphasis | Replay quantum candidates against classical baselines with identical costs/fill assumptions. |


#### PR #119 — Paper trading engine executor
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr119-paper-trading-engine-executor | Marker: QTT_PAPER_TRADING_ENGINE_EXECUTOR_OK

| Purpose | Run paper trading against live-like data without live orders or secrets in paper mode. |
| --- | --- |
| Must prove | Paper receipts are immutable and separate from replay receipts. |
| Must not create | Live write secrets, real orders, real fills, profit guarantee. |
| Quantum / latency emphasis | Paper test quantum-precomputed candidates without backend calls on live pretrade path. |


#### PR #120 — Fill, cost, slippage, fee, tick, and latency simulator
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr120-fill-cost-slippage-fee-tick-and-latency-simulator | Marker: QTT_FILL_COST_SLIPPAGE_FEE_TICK_AND_LATENCY_SIMULATOR_OK

| Purpose | Model venue-specific costs, ticks, fills, queue, latency, rejects, and settlement from accepted source and runtime observations. |
| --- | --- |
| Must prove | Simulation model version and source lineage are explicit. |
| Must not create | Venue fact invention, risk-free arbitrage wording, unverified fees/ticks. |
| Quantum / latency emphasis | Quantum candidates are penalized for latency/cost/noise if slower or uncertain. |


#### PR #121 — Replay/paper result packet writer and immutable ledger
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr121-replay-paper-result-packet-writer-and-immutable-ledger | Marker: QTT_REPLAY_PAPER_RESULT_PACKET_WRITER_AND_IMMUTABLE_LEDGER_OK

| Purpose | Write replay and paper result packets with deterministic IDs and no merge into approval. |
| --- | --- |
| Must prove | Result immutability and separate lanes are enforced. |
| Must not create | Fabricated results, live eligibility, profit proof, automatic owner approval. |
| Quantum / latency emphasis | Record quantum/classical comparator result lineage and uncertainty. |


#### PR #122 — Dual-result runtime comparator and promotion blocker
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr122-dual-result-runtime-comparator-and-promotion-blocker | Marker: QTT_DUAL_RESULT_RUNTIME_COMPARATOR_AND_PROMOTION_BLOCKER_OK

| Purpose | Compare accepted replay/paper result packets and produce owner-review inputs with blocks. |
| --- | --- |
| Must prove | Disagreements, stale data, excessive drawdown, latency risk, or missing receipts block promotion. |
| Must not create | Auto live promotion, profit guarantee, order authority. |
| Quantum / latency emphasis | Quantum outperformance must be compared with classical and marked uncertain unless receipts prove it. |


#### PR #123 — Prediction-market microstructure feature calibration runtime
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr123-prediction-market-microstructure-feature-calibration-runtime | Marker: QTT_PREDICTION_MARKET_MICROSTRUCTURE_FEATURE_CALIBRATION_RUNTIME_OK

| Purpose | Calibrate price-bucket, maker/taker, YES/NO asymmetry, liquidity, maturity, trade-size, and hourly features as replay/paper candidates. |
| --- | --- |
| Must prove | Features remain candidate-only until replay/paper pass. |
| Must not create | Hardcoded live defaults, external repo direct live signals. |
| Quantum / latency emphasis | Quantum stack generation may use calibrated feature candidates but not live source authority. |


#### PR #124 — Neural signal walk-forward, calibration, and drift runtime
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-beneficial runtime | Branch: pr124-neural-signal-walk-forward-calibration-and-drift-runtime | Marker: QTT_NEURAL_SIGNAL_WALK_FORWARD_CALIBRATION_AND_DRIFT_RUNTIME_OK

| Purpose | Implement stationarity, leakage, purged walk-forward, calibration, and drift checks for neural signals. |
| --- | --- |
| Must prove | No raw price prediction becomes direct order authority. |
| Must not create | Random splits, unadjusted accuracy promotion, neural direct live order submission. |
| Quantum / latency emphasis | Neural signals may feed candidate scoring, not quantum/live order authority. |


#### PR #125 — Quantum provider capability receipts
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential quantum runtime | Branch: pr125-quantum-provider-capability-receipts | Marker: QTT_QUANTUM_PROVIDER_CAPABILITY_RECEIPTS_OK

| Purpose | Record quantum provider, simulator, and local backend capability receipts after owner-approved source/provider enablement. |
| --- | --- |
| Must prove | Capabilities are evidence-gated and cost/latency/noise-aware. |
| Must not create | Backend execution as live authority, provider fact invention, quantum advantage claims. |
| Quantum / latency emphasis | Establish true quantum / quantum-inspired / classical backend registry. |


#### PR #126 — Quantum problem compiler for QUBO, Ising, and portfolio/candidate-set representations
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential quantum runtime | Branch: pr126-quantum-problem-compiler-for-qubo-ising-and-portfolio-candidate | Marker: QTT_QUANTUM_PROBLEM_COMPILER_FOR_QUBO_ISING_AND_PORTFOLIO_CANDIDATE_SET_REPRESENTATIONS_OK

| Purpose | Compile prediction-market candidate selection and sizing problems into QUBO/Ising/hybrid forms where suitable. |
| --- | --- |
| Must prove | Compiler output is deterministic and audit-stable. |
| Must not create | Live order authority, backend execution, unsupported problem transformations. |
| Quantum / latency emphasis | Map candidate choice, capital constraints, venue mask, owner-disabled venues, cash locks, and risk caps into feasible optimization form. |


#### PR #127 — Quantum-inspired and simulator challenger runner
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential quantum runtime | Branch: pr127-quantum-inspired-and-simulator-challenger-runner | Marker: QTT_QUANTUM_INSPIRED_AND_SIMULATOR_CHALLENGER_RUNNER_OK

| Purpose | Run approved non-live quantum-inspired/simulator challengers against selected snapshots. |
| --- | --- |
| Must prove | Runner emits deterministic receipts and never touches live order path. |
| Must not create | True quantum live calls, live routing, profit guarantee. |
| Quantum / latency emphasis | Benchmark QUBO/Ising/QAOA-like candidates versus classical baseline with equal constraints. |


#### PR #128 — True quantum backend execution wrapper
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-beneficial quantum runtime | Branch: pr128-true-quantum-backend-execution-wrapper | Marker: QTT_TRUE_QUANTUM_BACKEND_EXECUTION_WRAPPER_OK

| Purpose | If owner enables it, run true quantum backend jobs only for precomputed non-live candidate artifacts. |
| --- | --- |
| Must prove | Backend job receipt includes provider, queue latency, shots, noise/cost fields, and expiry. |
| Must not create | Backend call in live pretrade path, direct live order submission, advantage claim without comparator. |
| Quantum / latency emphasis | Use true quantum only when latency budget and artifact freshness allow safe precomputation. |


#### PR #129 — Quantum artifact cache, freshness, cost, noise, and latency model
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential quantum runtime | Branch: pr129-quantum-artifact-cache-freshness-cost-noise-and-latency-model | Marker: QTT_QUANTUM_ARTIFACT_CACHE_FRESHNESS_COST_NOISE_AND_LATENCY_MODEL_OK

| Purpose | Cache quantum outputs with freshness and validity masks. |
| --- | --- |
| Must prove | Expired or costly/noisy artifacts are downgraded or blocked. |
| Must not create | Live backend dependency, stale artifact use. |
| Quantum / latency emphasis | Minimize latency by using only precomputed artifacts in live pretrade path. |


#### PR #130 — Quantum-vs-classical comparator and regret ledger
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential quantum runtime | Branch: pr130-quantum-vs-classical-comparator-and-regret-ledger | Marker: QTT_QUANTUM_VS_CLASSICAL_COMPARATOR_AND_REGRET_LEDGER_OK

| Purpose | Compare quantum, quantum-inspired, hybrid, and classical candidates over replay/paper/canary evidence. |
| --- | --- |
| Must prove | Ledger records wins, ties, losses, uncertainty, cost, latency, and regret. |
| Must not create | Quantum advantage claim, profit claim, or live authority from comparison alone. |
| Quantum / latency emphasis | Quantum remains preferred only when net evidence survives fees, latency, risk, and uncertainty. |


#### PR #131 — Low-latency quantum pretrade exclusion gate
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential quantum runtime | Branch: pr131-low-latency-quantum-pretrade-exclusion-gate | Marker: QTT_LOW_LATENCY_QUANTUM_PRETRADE_EXCLUSION_GATE_OK

| Purpose | Prove live pretrade path does not call quantum backend, simulator, LLM, source retrieval, dashboard review, or external research. |
| --- | --- |
| Must prove | Only precomputed source-change, cash, market, and quantum artifact snapshots may enter live path. |
| Must not create | Live backend selection, runtime source acceptance, LLM reasoning in order path. |
| Quantum / latency emphasis | Protects latency while preserving quantum precompute benefits. |


#### PR #132 — Quantum fallback, rollback, and no-advantage-safe arbitration gate
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential quantum runtime | Branch: pr132-quantum-fallback-rollback-and-no-advantage-safe-arbitration-gate | Marker: QTT_QUANTUM_FALLBACK_ROLLBACK_AND_NO_ADVANTAGE_SAFE_ARBITRATION_GATE_OK

| Purpose | Force fallback to classical/no-trade when quantum artifacts fail freshness, cost, latency, risk, or comparator checks. |
| --- | --- |
| Must prove | No-trade and classical baseline are valid outcomes. |
| Must not create | Owner-forced quantum fabricating evidence or bypassing gates. |
| Quantum / latency emphasis | Prevents slower or weaker quantum choices from degrading net performance. |


#### PR #133 — Risk limit policy runtime validator
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr133-risk-limit-policy-runtime-validator | Marker: QTT_RISK_LIMIT_POLICY_RUNTIME_VALIDATOR_OK

| Purpose | Implement runtime enforcement for owner-approved risk caps, exposure, drawdown, market, venue, and strategy limits. |
| --- | --- |
| Must prove | Risk state is receipt-bound and blocks unsafe new/increased exposure. |
| Must not create | Capital/risk expansion without owner, live order bypass. |
| Quantum / latency emphasis | Risk masks feed classical and quantum optimizers before candidate construction. |


#### PR #134 — Position, open-order, and exposure-lock ledger
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr134-position-open-order-and-exposure-lock-ledger | Marker: QTT_POSITION_OPEN_ORDER_AND_EXPOSURE_LOCK_LEDGER_OK

| Purpose | Maintain authoritative internal ledger for positions, pending orders, fills, cash locks, and exposure. |
| --- | --- |
| Must prove | Capital cannot be reused until finality/release receipts exist. |
| Must not create | Duplicate exposure, hidden open orders, fabricated fills. |
| Quantum / latency emphasis | Optimizer sees locked exposure and cannot double-spend capital. |


#### PR #135 — Trade-intent compiler to non-live order-intent packet
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr135-trade-intent-compiler-to-non-live-order-intent-packet | Marker: QTT_TRADE_INTENT_COMPILER_TO_NON_LIVE_ORDER_INTENT_PACKET_OK

| Purpose | Compile selected stack and pretrade context into non-authoritative order-intent packets. |
| --- | --- |
| Must prove | Order intent is typed and remains non-live until live command gate. |
| Must not create | Order submission, live routing, owner approval fabrication. |
| Quantum / latency emphasis | Quantum-selected candidates become order intents only after all non-live gates pass. |


#### PR #136 — Pretrade gate matrix for source, cash, risk, latency, owner, and venue readiness
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr136-pretrade-gate-matrix-for-source-cash-risk-latency-owner-and-venu | Marker: QTT_PRETRADE_GATE_MATRIX_FOR_SOURCE_CASH_RISK_LATENCY_OWNER_AND_VENUE_READINESS_OK

| Purpose | Aggregate all pretrade conditions into a fail-closed matrix. |
| --- | --- |
| Must prove | Any unknown source/cash/revalidation/risk/venue state blocks new/increased exposure. |
| Must not create | Silent fallback, partial venue launch without owner override. |
| Quantum / latency emphasis | Matrix must include quantum artifact freshness and classical fallback status. |


#### PR #137 — Runtime owner approval queue service and dashboard shell
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr137-runtime-owner-approval-queue-service-and-dashboard-shell | Marker: QTT_RUNTIME_OWNER_APPROVAL_QUEUE_SERVICE_AND_DASHBOARD_SHELL_OK

| Purpose | Implement runtime owner approval queue without trading authority. |
| --- | --- |
| Must prove | Owner can review requests, receipts, blocks, and candidate evidence. |
| Must not create | Dashboard rewriting facts or submitting orders. |
| Quantum / latency emphasis | Expose quantum/classical comparison and no-advantage blockers clearly. |


#### PR #138 — Kill-switch runtime executor and emergency halt receipts
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr138-kill-switch-runtime-executor-and-emergency-halt-receipts | Marker: QTT_KILL_SWITCH_RUNTIME_EXECUTOR_AND_EMERGENCY_HALT_RECEIPTS_OK

| Purpose | Implement emergency halt, pause, rollback, and resume gates by venue, market, account, and strategy. |
| --- | --- |
| Must prove | Kill switch off is required before exposure; red gates halt affected scopes. |
| Must not create | Unsafe resume, silent continued trading, missing receipts. |
| Quantum / latency emphasis | Quantum artifacts and optimizers are invalidated or quarantined on halt. |


#### PR #139 — Telemetry, latency, reject, throttle, and health monitor
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr139-telemetry-latency-reject-throttle-and-health-monitor | Marker: QTT_TELEMETRY_LATENCY_REJECT_THROTTLE_AND_HEALTH_MONITOR_OK

| Purpose | Monitor venue health, reject/throttle rates, sequence freshness, latency, and runtime service health. |
| --- | --- |
| Must prove | Health degradation creates block/rollback receipts. |
| Must not create | Ignoring stale data, over-pacing, unbounded retries. |
| Quantum / latency emphasis | Latency metrics penalize slow quantum/route choices and protect live path. |


#### PR #140 — Day-1 drill and canary rehearsal executor
Category: Runtime | Stage: Stage 1 prediction markets | Priority: S1 launch-essential runtime | Branch: pr140-day-1-drill-and-canary-rehearsal-executor | Marker: QTT_DAY_1_DRILL_AND_CANARY_REHEARSAL_EXECUTOR_OK

| Purpose | Run full Day-1 rehearsal in paper/non-live mode across all three venues. |
| --- | --- |
| Must prove | Drill exercises source, connector, cash, risk, resolver, replay/paper, dashboard, kill switch, and runbook. |
| Must not create | Live orders, live write secrets in paper mode, launch claim. |
| Quantum / latency emphasis | Measures quantum-precompute latency without backend live-path calls. |


#### PR #141 — Kalshi live connector binding and read-write surface
Category: Live | Stage: Stage 1 prediction markets | Priority: S1 launch-essential live | Branch: pr141-kalshi-live-connector-binding-and-read-write-surface | Marker: QTT_KALSHI_LIVE_CONNECTOR_BINDING_AND_READ_WRITE_SURFACE_OK

| Purpose | Implement owner-enabled Kalshi live connector read/write surface after accepted source and connector binding gates. |
| --- | --- |
| Must prove | Venue-specific source, cash, order, risk, kill switch, and health gates are enforced. |
| Must not create | Live enablement from connector compile alone, unapproved orders. |
| Quantum / latency emphasis | Quantum candidates route only through execution router after precomputed gates. |


#### PR #142 — Polymarket live connector binding and read-write surface
Category: Live | Stage: Stage 1 prediction markets | Priority: S1 launch-essential live | Branch: pr142-polymarket-live-connector-binding-and-read-write-surface | Marker: QTT_POLYMARKET_LIVE_CONNECTOR_BINDING_AND_READ_WRITE_SURFACE_OK

| Purpose | Implement owner-enabled Polymarket live connector surface with wallet/collateral/signing semantics from accepted sources. |
| --- | --- |
| Must prove | Polymarket-specific mechanics remain Polymarket-only and receipt-bound. |
| Must not create | Copying Polymarket mechanics to other venues, unapproved wallet movement/orders. |
| Quantum / latency emphasis | Quantum candidate uses Polymarket only when venue mask and cost/latency/finality gates pass. |


#### PR #143 — FORECASTEX_IBKR live connector binding and read-write surface
Category: Live | Stage: Stage 1 prediction markets | Priority: S1 launch-essential live | Branch: pr143-forecastex-ibkr-live-connector-binding-and-read-write-surface | Marker: QTT_FORECASTEX_IBKR_LIVE_CONNECTOR_BINDING_AND_READ_WRITE_SURFACE_OK

| Purpose | Implement owner-enabled FORECASTEX_IBKR connector surface with account/session/order-state semantics from accepted sources. |
| --- | --- |
| Must prove | Client/session/order acknowledgement, pacing, cash, position, and order-state gates are enforced. |
| Must not create | Bypassing ack/reply/order-state/cash/session gates. |
| Quantum / latency emphasis | Quantum selection respects serialized writer latency and event-contract constraints. |


#### PR #144 — Runtime live order command gate and venue enablement matrix
Category: Live | Stage: Stage 1 prediction markets | Priority: S1 launch-essential live | Branch: pr144-runtime-live-order-command-gate-and-venue-enablement-matrix | Marker: QTT_RUNTIME_LIVE_ORDER_COMMAND_GATE_AND_VENUE_ENABLEMENT_MATRIX_OK

| Purpose | Open live command boundary only for exact owner-approved venue, market, account, session, and strategy scope. |
| --- | --- |
| Must prove | Effective live-write state is green per venue and scope. |
| Must not create | Silent single-venue fallback, live orders from static owner review alone. |
| Quantum / latency emphasis | Quantum-preferred path still passes live command gate and no-backend-live-path rule. |


#### PR #145 — Idempotent order lifecycle state machine
Category: Live | Stage: Stage 1 prediction markets | Priority: S1 launch-essential live | Branch: pr145-idempotent-order-lifecycle-state-machine | Marker: QTT_IDEMPOTENT_ORDER_LIFECYCLE_STATE_MACHINE_OK

| Purpose | Submit, acknowledge, fill, partial-fill, cancel, replace, reject, throttle, and finality states with idempotency/client-order IDs. |
| --- | --- |
| Must prove | Duplicate submit suppression and receipt ordering are enforced. |
| Must not create | Untracked orders, duplicate submits, capital reuse before finality. |
| Quantum / latency emphasis | Quantum candidates cannot skip order lifecycle receipts. |


#### PR #146 — Cancel, replace, reduce, close, and forced-exit safety state machine
Category: Live | Stage: Stage 1 prediction markets | Priority: S1 launch-essential live | Branch: pr146-cancel-replace-reduce-close-and-forced-exit-safety-state-machine | Marker: QTT_CANCEL_REPLACE_REDUCE_CLOSE_AND_FORCED_EXIT_SAFETY_STATE_MACHINE_OK

| Purpose | Implement safe order modifications and owner exit policy handling. |
| --- | --- |
| Must prove | Cancel/reduce/close actions are venue-bound, idempotent, and receipt-backed. |
| Must not create | Forced close without owner exit policy, unsafe retry loops. |
| Quantum / latency emphasis | Fallback can reduce/exit quantum-originated positions only under safety policy. |


#### PR #147 — Fill, cash, order, and settlement/finality reconciliation executor
Category: Live | Stage: Stage 1 prediction markets | Priority: S1 launch-essential live | Branch: pr147-fill-cash-order-and-settlement-finality-reconciliation-executor | Marker: QTT_FILL_CASH_ORDER_AND_SETTLEMENT_FINALITY_RECONCILIATION_EXECUTOR_OK

| Purpose | Reconcile fills, cash movement, positions, PnL, finality, and account state after each live action. |
| --- | --- |
| Must prove | Post-trade ledger agrees with venue receipts or blocks next exposure. |
| Must not create | Profit claims without reconciliation, stale cash reuse. |
| Quantum / latency emphasis | Quantum/classical attribution uses reconciled realized data only. |


#### PR #148 — Limited live canary order router
Category: Live | Stage: Stage 1 prediction markets | Priority: S1 launch-essential live | Branch: pr148-limited-live-canary-order-router | Marker: QTT_LIMITED_LIVE_CANARY_ORDER_ROUTER_OK

| Purpose | Route owner-approved small-scope canary orders across enabled Stage-1 venues. |
| --- | --- |
| Must prove | Only green exact scopes receive orders; no expansion without owner approval. |
| Must not create | Full-scale live, arbitrage live, unclassified trading. |
| Quantum / latency emphasis | Canary prioritizes high-confidence, low-latency, low-risk candidates; quantum may participate only through precomputed artifacts. |


#### PR #149 — Post-canary safety review, kill-switch, rollback, and incident report
Category: Live | Stage: Stage 1 prediction markets | Priority: S1 launch-essential live | Branch: pr149-post-canary-safety-review-kill-switch-rollback-and-incident-repo | Marker: QTT_POST_CANARY_SAFETY_REVIEW_KILL_SWITCH_ROLLBACK_AND_INCIDENT_REPORT_OK

| Purpose | Evaluate canary result, reconcile state, classify incidents, pause/rollback if required. |
| --- | --- |
| Must prove | No repeat/scale unless review passes and owner approves. |
| Must not create | Auto scale-up, profit guarantee, missing incident ledger. |
| Quantum / latency emphasis | Quantum candidates require comparator review before further promotion. |


#### PR #150 — Day-1 launch readiness gate and three-venue runbook
Category: Live | Stage: Stage 1 prediction markets | Priority: S1 launch-essential live | Branch: pr150-day-1-launch-readiness-gate-and-three-venue-runbook | Marker: QTT_DAY_1_LAUNCH_READINESS_GATE_AND_THREE_VENUE_RUNBOOK_OK

| Purpose | Produce final launch readiness matrix and runbook for Kalshi, Polymarket, and FORECASTEX_IBKR. |
| --- | --- |
| Must prove | Launch readiness is distinct from execution; partial venue scope requires explicit owner risk-reduction override. |
| Must not create | Day-1 execution claim without live command gate and owner command. |
| Quantum / latency emphasis | Runbook preserves no-backend-live quantum path and classical fallback. |


#### PR #151 — Stage-1 launch completion report and scale-up handoff
Category: Live | Stage: Stage 1 prediction markets | Priority: S1 launch-essential live | Branch: pr151-stage-1-launch-completion-report-and-scale-up-handoff | Marker: QTT_STAGE_1_LAUNCH_COMPLETION_REPORT_AND_SCALE_UP_HANDOFF_OK

| Purpose | Report canary/live results, receipts, PnL with no guarantee, incidents, blocks, and next scale eligibility. |
| --- | --- |
| Must prove | Post-launch evidence is reconciled and does not fabricate profit. |
| Must not create | Profit guarantee, automatic venue/strategy expansion. |
| Quantum / latency emphasis | Quantum regret ledger and comparator evidence determine next quantum weighting. |


## 9. PR #152–#168 — Stage‑1 post-launch advanced robustness and scale-up
These PRs are beneficial after initial Stage‑1 canary/live launch. They should not delay first limited canary launch unless the owner decides to make some of them pre-launch blockers.

| PR | Category | Priority | Title | Branch |
| --- | --- | --- | --- | --- |
| #152 | Runtime | S1 post-launch advanced | Cross-venue arbitrage dry-run executor | pr152-cross-venue-arbitrage-dry-run-executor |
| #153 | Live | S1 post-launch advanced | Limited live arbitrage gate | pr153-limited-live-arbitrage-gate |
| #154 | Runtime | S1 post-launch advanced | Triggered live concurrent comparison lane | pr154-triggered-live-concurrent-comparison-lane |
| #155 | Live | S1 post-launch advanced | Full/scaled live promotion gate | pr155-full-scaled-live-promotion-gate |
| #156 | Runtime | S1 post-launch advanced | Smart order and venue routing optimizer | pr156-smart-order-and-venue-routing-optimizer |
| #157 | Runtime | S1 post-launch advanced | Inventory, exposure, and net-PnL optimizer | pr157-inventory-exposure-and-net-pnl-optimizer |
| #158 | Runtime | S1 post-launch advanced | Low-latency shortcut path with precomputed snapshots only | pr158-low-latency-shortcut-path-with-precomputed-snapshots-only |
| #159 | Runtime | S1 post-launch advanced | Agent KPI self-healing, retry, reroute, and quarantine runtime | pr159-agent-kpi-self-healing-retry-reroute-and-quarantine-runtime |
| #160 | Runtime | S1 post-launch advanced | Dashboard runtime source, cash, order, position, and quantum panels | pr160-dashboard-runtime-source-cash-order-position-and-quantum-panels |
| #161 | Runtime | S1 post-launch advanced | Post-launch research, news, and social ingestion | pr161-post-launch-research-news-and-social-ingestion |
| #162 | Runtime | S1 post-launch advanced | External research repo and bot-pattern quarantine runtime | pr162-external-research-repo-and-bot-pattern-quarantine-runtime |
| #163 | Runtime | S1 post-launch advanced | Local LLM hotswap, tournament, and routing dashboard | pr163-local-llm-hotswap-tournament-and-routing-dashboard |
| #164 | Runtime | S1 post-launch advanced | Quantum artifact refresh scheduler and periodic benchmark | pr164-quantum-artifact-refresh-scheduler-and-periodic-benchmark |
| #165 | Runtime | S1 post-launch advanced | Strategy retirement, reactivation, and parameter rehabilitation lifecycle | pr165-strategy-retirement-reactivation-and-parameter-rehabilitation-li |
| #166 | Runtime | S1 post-launch advanced | Regulatory and compliance audit ledger by venue | pr166-regulatory-and-compliance-audit-ledger-by-venue |
| #167 | Runtime | S1 post-launch advanced | Disaster recovery, credential rotation, and environment cutover drill | pr167-disaster-recovery-credential-rotation-and-environment-cutover-dr |
| #168 | Runtime | S1 post-launch advanced | Stage-1 scale-ready final audit | pr168-stage-1-scale-ready-final-audit |

#### PR #152 — Cross-venue arbitrage dry-run executor
Category: Runtime | Stage: Stage 1 prediction markets post-launch | Priority: S1 post-launch advanced | Branch: pr152-cross-venue-arbitrage-dry-run-executor | Marker: QTT_CROSS_VENUE_ARBITRAGE_DRY_RUN_EXECUTOR_OK
Purpose: Run non-live cross-venue arbitrage dry-run using normalized execution semantics. | Gate: Arbitrage reports require execution normalization, fees, latency, cash locks, and settlement finality. | No-create: Risk-free wording, live arbitrage before canary/dry-run pass.

#### PR #153 — Limited live arbitrage gate
Category: Live | Stage: Stage 1 prediction markets post-launch | Priority: S1 post-launch advanced | Branch: pr153-limited-live-arbitrage-gate | Marker: QTT_LIMITED_LIVE_ARBITRAGE_GATE_OK
Purpose: Open owner-approved limited live arbitrage only after canary and dry-run reports. | Gate: Owner approval, exact venue scopes, cash locks, execution normalization, and kill switches are green. | No-create: Unapproved arbitrage, full-scale live, apparent gap trading.

#### PR #154 — Triggered live concurrent comparison lane
Category: Runtime | Stage: Stage 1 prediction markets post-launch | Priority: S1 post-launch advanced | Branch: pr154-triggered-live-concurrent-comparison-lane | Marker: QTT_TRIGGERED_LIVE_CONCURRENT_COMPARISON_LANE_OK
Purpose: Observe live candidates beside live activity without new order authority. | Gate: Triggered comparison is observe-only and cannot auto-promote. | No-create: New orders, repeat/scale authority.

#### PR #155 — Full/scaled live promotion gate
Category: Live | Stage: Stage 1 prediction markets post-launch | Priority: S1 post-launch advanced | Branch: pr155-full-scaled-live-promotion-gate | Marker: QTT_FULL_SCALED_LIVE_PROMOTION_GATE_OK
Purpose: Define owner-approved promotion from limited canary/arbitrage to larger live envelopes. | Gate: Promotion uses reconciled realized evidence, drawdown, latency, incidents, and owner command. | No-create: Capital/risk ceiling expansion without owner.

#### PR #156 — Smart order and venue routing optimizer
Category: Runtime | Stage: Stage 1 prediction markets post-launch | Priority: S1 post-launch advanced | Branch: pr156-smart-order-and-venue-routing-optimizer | Marker: QTT_SMART_ORDER_AND_VENUE_ROUTING_OPTIMIZER_OK
Purpose: Optimize venue/order choice using precomputed snapshots and execution router constraints. | Gate: No route chosen without source/cash/risk/order-state green. | No-create: Direct order submission by optimizer.

#### PR #157 — Inventory, exposure, and net-PnL optimizer
Category: Runtime | Stage: Stage 1 prediction markets post-launch | Priority: S1 post-launch advanced | Branch: pr157-inventory-exposure-and-net-pnl-optimizer | Marker: QTT_INVENTORY_EXPOSURE_AND_NET_PNL_OPTIMIZER_OK
Purpose: Optimize exposure rotation, capital utilization, and net PnL after fees and locks. | Gate: Uses reconciled ledger and owner-approved risk bands. | No-create: Treasury movement or capital envelope expansion.

#### PR #158 — Low-latency shortcut path with precomputed snapshots only
Category: Runtime | Stage: Stage 1 prediction markets post-launch | Priority: S1 post-launch advanced | Branch: pr158-low-latency-shortcut-path-with-precomputed-snapshots-only | Marker: QTT_LOW_LATENCY_SHORTCUT_PATH_WITH_PRECOMPUTED_SNAPSHOTS_ONLY_OK
Purpose: Streamline live path to consume only precomputed source/cash/market/quantum snapshots. | Gate: No source retrieval, LLM reasoning, dashboard review, or backend selection in live path. | No-create: Unverified freshness shortcuts.

#### PR #159 — Agent KPI self-healing, retry, reroute, and quarantine runtime
Category: Runtime | Stage: Stage 1 prediction markets post-launch | Priority: S1 post-launch advanced | Branch: pr159-agent-kpi-self-healing-retry-reroute-and-quarantine-runtime | Marker: QTT_AGENT_KPI_SELF_HEALING_RETRY_REROUTE_AND_QUARANTINE_RUNTIME_OK
Purpose: Measure agent duty quality, missed duties, output trust, reroute/quarantine actions. | Gate: Agents retry/reroute inside bounded authority only. | No-create: Permission expansion or live authority grant by agent.

#### PR #160 — Dashboard runtime source, cash, order, position, and quantum panels
Category: Runtime | Stage: Stage 1 prediction markets post-launch | Priority: S1 post-launch advanced | Branch: pr160-dashboard-runtime-source-cash-order-position-and-quantum-panels | Marker: QTT_DASHBOARD_RUNTIME_SOURCE_CASH_ORDER_POSITION_AND_QUANTUM_PANELS_OK
Purpose: Implement runtime dashboard panels for owner visibility. | Gate: Panels display receipts and current blocks without rewriting facts. | No-create: Trading authority or fact mutation from dashboard.

#### PR #161 — Post-launch research, news, and social ingestion
Category: Runtime | Stage: Stage 1 prediction markets post-launch | Priority: S1 post-launch advanced | Branch: pr161-post-launch-research-news-and-social-ingestion | Marker: QTT_POST_LAUNCH_RESEARCH_NEWS_AND_SOCIAL_INGESTION_OK
Purpose: Ingest research inputs as scouting signals only. | Gate: Inputs can seed retrieval targets or candidate hypotheses. | No-create: Accepted source facts, live direct signals, trading authority.

#### PR #162 — External research repo and bot-pattern quarantine runtime
Category: Runtime | Stage: Stage 1 prediction markets post-launch | Priority: S1 post-launch advanced | Branch: pr162-external-research-repo-and-bot-pattern-quarantine-runtime | Marker: QTT_EXTERNAL_RESEARCH_REPO_AND_BOT_PATTERN_QUARANTINE_RUNTIME_OK
Purpose: Quarantine external code, dependencies, credentials, and strategy patterns. | Gate: External patterns may seed QTT-native candidates only after review. | No-create: Clone/run/secrets/direct live dependency.

#### PR #163 — Local LLM hotswap, tournament, and routing dashboard
Category: Runtime | Stage: Stage 1 prediction markets post-launch | Priority: S1 post-launch advanced | Branch: pr163-local-llm-hotswap-tournament-and-routing-dashboard | Marker: QTT_LOCAL_LLM_HOTSWAP_TOURNAMENT_AND_ROUTING_DASHBOARD_OK
Purpose: Manage local model candidates and owner-approved hotswaps. | Gate: LLMs remain outside live pretrade and final order release. | No-create: LLM final order authority or cloud primary runtime by default.

#### PR #164 — Quantum artifact refresh scheduler and periodic benchmark
Category: Runtime | Stage: Stage 1 prediction markets post-launch | Priority: S1 post-launch advanced | Branch: pr164-quantum-artifact-refresh-scheduler-and-periodic-benchmark | Marker: QTT_QUANTUM_ARTIFACT_REFRESH_SCHEDULER_AND_PERIODIC_BENCHMARK_OK
Purpose: Refresh quantum artifacts and benchmark against classical baselines. | Gate: Refresh cadence respects cost, freshness, queue latency, and owner policy. | No-create: Live backend dependency or advantage claim.

#### PR #165 — Strategy retirement, reactivation, and parameter rehabilitation lifecycle
Category: Runtime | Stage: Stage 1 prediction markets post-launch | Priority: S1 post-launch advanced | Branch: pr165-strategy-retirement-reactivation-and-parameter-rehabilitation-li | Marker: QTT_STRATEGY_RETIREMENT_REACTIVATION_AND_PARAMETER_REHABILITATION_LIFECYCLE_OK
Purpose: Retire weak strategies and reactivate only with evidence. | Gate: Reactivation requires normalized bounds, source/currentness, replay/paper or live evidence. | No-create: Silent strategy resurrection.

#### PR #166 — Regulatory and compliance audit ledger by venue
Category: Runtime | Stage: Stage 1 prediction markets post-launch | Priority: S1 post-launch advanced | Branch: pr166-regulatory-and-compliance-audit-ledger-by-venue | Marker: QTT_REGULATORY_AND_COMPLIANCE_AUDIT_LEDGER_BY_VENUE_OK
Purpose: Record compliance, rulebook, settlement, fee, and operational receipts by venue. | Gate: Compliance blocks are visible and owner-reviewable. | No-create: Legal/rule assumptions without source evidence.

#### PR #167 — Disaster recovery, credential rotation, and environment cutover drill
Category: Runtime | Stage: Stage 1 prediction markets post-launch | Priority: S1 post-launch advanced | Branch: pr167-disaster-recovery-credential-rotation-and-environment-cutover-dr | Marker: QTT_DISASTER_RECOVERY_CREDENTIAL_ROTATION_AND_ENVIRONMENT_CUTOVER_DRILL_OK
Purpose: Exercise backup, rollback, credential rotation, failover, and restore. | Gate: Recovery drill receipts and blocked-live states are explicit. | No-create: Live restart without owner/kill-switch gates.

#### PR #168 — Stage-1 scale-ready final audit
Category: Runtime | Stage: Stage 1 prediction markets post-launch | Priority: S1 post-launch advanced | Branch: pr168-stage-1-scale-ready-final-audit | Marker: QTT_STAGE_1_SCALE_READY_FINAL_AUDIT_OK
Purpose: Close Stage-1 advanced readiness and prepare future-market expansion. | Gate: All receipts, incidents, evidence, quantum comparators, and owner decisions are summarized. | No-create: Automatic Stage-2 launch.

## 10. PR #169–#224 — Future market-stage expansion roadmap
These PRs cover crypto, equities/stocks, options/futures, and cross-market automation. They are intentionally future-stage surfaces and must not be interpreted as Stage‑1 launch blockers unless owner explicitly reorders the roadmap.

| PR | Category | Stage | Title | Branch |
| --- | --- | --- | --- | --- |
| #169 | Static | Stage 2 crypto | Crypto market source-evidence target pack | pr169-crypto-market-source-evidence-target-pack |
| #170 | Runtime | Stage 2 crypto | Crypto connector semantic binding | pr170-crypto-connector-semantic-binding |
| #171 | Runtime | Stage 2 crypto | Crypto custody, wallet, and balance receipt gate | pr171-crypto-custody-wallet-and-balance-receipt-gate |
| #172 | Runtime | Stage 2 crypto | Crypto market-data snapshot and stale-data gate | pr172-crypto-market-data-snapshot-and-stale-data-gate |
| #173 | Runtime | Stage 2 crypto | Crypto replay and paper execution | pr173-crypto-replay-and-paper-execution |
| #174 | Runtime | Stage 2 crypto | Crypto quantum portfolio optimizer | pr174-crypto-quantum-portfolio-optimizer |
| #175 | Runtime | Stage 2 crypto | Crypto risk, leverage, and liquidity gate | pr175-crypto-risk-leverage-and-liquidity-gate |
| #176 | Live | Stage 2 crypto | Crypto live order lifecycle | pr176-crypto-live-order-lifecycle |
| #177 | Live | Stage 2 crypto | Crypto limited live canary | pr177-crypto-limited-live-canary |
| #178 | Live | Stage 2 crypto | Crypto reconciliation and post-trade audit | pr178-crypto-reconciliation-and-post-trade-audit |
| #179 | Runtime | Stage 2 crypto | Crypto cross-exchange arbitrage dry-run | pr179-crypto-cross-exchange-arbitrage-dry-run |
| #180 | Live | Stage 2 crypto | Crypto limited live arbitrage gate | pr180-crypto-limited-live-arbitrage-gate |
| #181 | Runtime | Stage 2 crypto | Crypto dashboard panels | pr181-crypto-dashboard-panels |
| #182 | Live | Stage 2 crypto | Crypto launch readiness gate | pr182-crypto-launch-readiness-gate |
| #183 | Live | Stage 2 crypto | Crypto launch report and Stage-3 handoff | pr183-crypto-launch-report-and-stage-3-handoff |
| #184 | Static | Stage 3 equities/stocks | Equities source-evidence target pack | pr184-equities-source-evidence-target-pack |
| #185 | Runtime | Stage 3 equities/stocks | Broker account, cash, margin, and permission semantics | pr185-broker-account-cash-margin-and-permission-semantics |
| #186 | Runtime | Stage 3 equities/stocks | Equity market-data snapshots | pr186-equity-market-data-snapshots |
| #187 | Static | Stage 3 equities/stocks | Equity strategy and parameter universe | pr187-equity-strategy-and-parameter-universe |
| #188 | Runtime | Stage 3 equities/stocks | Equity replay and paper execution | pr188-equity-replay-and-paper-execution |
| #189 | Runtime | Stage 3 equities/stocks | Equity quantum portfolio construction | pr189-equity-quantum-portfolio-construction |
| #190 | Runtime | Stage 3 equities/stocks | Equity risk, compliance, and trading restriction gate | pr190-equity-risk-compliance-and-trading-restriction-gate |
| #191 | Live | Stage 3 equities/stocks | Equity live order lifecycle | pr191-equity-live-order-lifecycle |
| #192 | Live | Stage 3 equities/stocks | Equity limited live canary | pr192-equity-limited-live-canary |
| #193 | Live | Stage 3 equities/stocks | Equity reconciliation and PnL attribution | pr193-equity-reconciliation-and-pnl-attribution |
| #194 | Runtime | Stage 3 equities/stocks | Corporate action and calendar gate | pr194-corporate-action-and-calendar-gate |
| #195 | Runtime | Stage 3 equities/stocks | Equity smart routing latency and cost optimizer | pr195-equity-smart-routing-latency-and-cost-optimizer |
| #196 | Runtime | Stage 3 equities/stocks | Equity dashboard panels | pr196-equity-dashboard-panels |
| #197 | Live | Stage 3 equities/stocks | Equity launch readiness gate | pr197-equity-launch-readiness-gate |
| #198 | Live | Stage 3 equities/stocks | Equity launch report and Stage-4 handoff | pr198-equity-launch-report-and-stage-4-handoff |
| #199 | Static | Stage 4 options/futures | Derivatives source-evidence target pack | pr199-derivatives-source-evidence-target-pack |
| #200 | Runtime | Stage 4 options/futures | Option chain, greeks, and symbol semantics binding | pr200-option-chain-greeks-and-symbol-semantics-binding |
| #201 | Runtime | Stage 4 options/futures | Margin, assignment, exercise, and settlement semantics | pr201-margin-assignment-exercise-and-settlement-semantics |
| #202 | Runtime | Stage 4 options/futures | Derivatives market-data snapshots | pr202-derivatives-market-data-snapshots |
| #203 | Static | Stage 4 options/futures | Derivatives strategy universe | pr203-derivatives-strategy-universe |
| #204 | Runtime | Stage 4 options/futures | Volatility model calibration and walk-forward validation | pr204-volatility-model-calibration-and-walk-forward-validation |
| #205 | Runtime | Stage 4 options/futures | Quantum combinatorial spread optimizer | pr205-quantum-combinatorial-spread-optimizer |
| #206 | Runtime | Stage 4 options/futures | Derivatives replay and paper execution | pr206-derivatives-replay-and-paper-execution |
| #207 | Runtime | Stage 4 options/futures | Greeks, scenario, assignment, and tail-risk gate | pr207-greeks-scenario-assignment-and-tail-risk-gate |
| #208 | Live | Stage 4 options/futures | Derivatives order lifecycle and spread net-price gate | pr208-derivatives-order-lifecycle-and-spread-net-price-gate |
| #209 | Live | Stage 4 options/futures | Derivatives limited live canary | pr209-derivatives-limited-live-canary |
| #210 | Live | Stage 4 options/futures | Derivatives reconciliation, assignment, and exercise audit | pr210-derivatives-reconciliation-assignment-and-exercise-audit |
| #211 | Runtime | Stage 4 options/futures | Futures contract roll, expiry, and carrying-cost gate | pr211-futures-contract-roll-expiry-and-carrying-cost-gate |
| #212 | Live | Stage 4 options/futures | Futures limited live canary | pr212-futures-limited-live-canary |
| #213 | Runtime | Stage 4 options/futures | Cross-derivative hedging optimizer | pr213-cross-derivative-hedging-optimizer |
| #214 | Runtime | Stage 4 options/futures | Derivatives dashboard panels | pr214-derivatives-dashboard-panels |
| #215 | Live | Stage 4 options/futures | Derivatives launch readiness gate | pr215-derivatives-launch-readiness-gate |
| #216 | Live | Stage 4 options/futures | Derivatives launch report and Stage-5 handoff | pr216-derivatives-launch-report-and-stage-5-handoff |
| #217 | Runtime | Stage 5 cross-market automation | Global source and connector currentness monitor | pr217-global-source-and-connector-currentness-monitor |
| #218 | Runtime | Stage 5 cross-market automation | Cross-market portfolio exposure and risk engine | pr218-cross-market-portfolio-exposure-and-risk-engine |
| #219 | Runtime | Stage 5 cross-market automation | Quantum resource scheduler across markets | pr219-quantum-resource-scheduler-across-markets |
| #220 | Runtime | Stage 5 cross-market automation | Cross-market capital allocation optimizer | pr220-cross-market-capital-allocation-optimizer |
| #221 | Live | Stage 5 cross-market automation | Global kill switch and market-sleeve pause controller | pr221-global-kill-switch-and-market-sleeve-pause-controller |
| #222 | Runtime | Stage 5 cross-market automation | Global owner dashboard and evidence board | pr222-global-owner-dashboard-and-evidence-board |
| #223 | Runtime | Stage 5 cross-market automation | Autonomous operation graduation gates | pr223-autonomous-operation-graduation-gates |
| #224 | Static | Stage 5 cross-market automation | Roadmap coverage closure and future PR reserve | pr224-roadmap-coverage-closure-and-future-pr-reserve |

### 10A. Future market PR definitions

#### PR #169 — Crypto market source-evidence target pack
Category: Static | Stage: Stage 2 crypto | Priority: Future-stage static | Branch: pr169-crypto-market-source-evidence-target-pack | Marker: QTT_CRYPTO_MARKET_SOURCE_EVIDENCE_TARGET_PACK_OK
Purpose: Define official source targets for crypto venues/exchanges, custody, fees, order types, settlement, wallet, and market data. | Gate: Future-stage source targets are explicit. | No-create: Source fact acceptance or connector semantics.

#### PR #170 — Crypto connector semantic binding
Category: Runtime | Stage: Stage 2 crypto | Priority: Future-stage runtime | Branch: pr170-crypto-connector-semantic-binding | Marker: QTT_CRYPTO_CONNECTOR_SEMANTIC_BINDING_OK
Purpose: Bind accepted crypto venue/exchange source packets into connector semantics. | Gate: Fees, order types, balances, wallet/custody, and market data are source-bound. | No-create: Invented exchange facts or live trading.

#### PR #171 — Crypto custody, wallet, and balance receipt gate
Category: Runtime | Stage: Stage 2 crypto | Priority: Future-stage runtime | Branch: pr171-crypto-custody-wallet-and-balance-receipt-gate | Marker: QTT_CRYPTO_CUSTODY_WALLET_AND_BALANCE_RECEIPT_GATE_OK
Purpose: Implement custody/wallet/balance receipts after accepted source and credentials. | Gate: Wallet/custody state blocks exposure when unknown. | No-create: Unverified token/cash/custody reuse.

#### PR #172 — Crypto market-data snapshot and stale-data gate
Category: Runtime | Stage: Stage 2 crypto | Priority: Future-stage runtime | Branch: pr172-crypto-market-data-snapshot-and-stale-data-gate | Marker: QTT_CRYPTO_MARKET_DATA_SNAPSHOT_AND_STALE_DATA_GATE_OK
Purpose: Implement crypto market data snapshots and stale-data blocks. | Gate: Freshness/sequence/venue health are explicit. | No-create: Live orders from stale data.

#### PR #173 — Crypto replay and paper execution
Category: Runtime | Stage: Stage 2 crypto | Priority: Future-stage runtime | Branch: pr173-crypto-replay-and-paper-execution | Marker: QTT_CRYPTO_REPLAY_AND_PAPER_EXECUTION_OK
Purpose: Run crypto replay/paper lanes with cost, slippage, funding, and latency models. | Gate: Replay/paper separated and immutable. | No-create: Live orders or auto-promotion.

#### PR #174 — Crypto quantum portfolio optimizer
Category: Runtime | Stage: Stage 2 crypto | Priority: Future-stage quantum runtime | Branch: pr174-crypto-quantum-portfolio-optimizer | Marker: QTT_CRYPTO_QUANTUM_PORTFOLIO_OPTIMIZER_OK
Purpose: Compile and test crypto allocation/rebalance candidate sets. | Gate: Quantum/classical comparison and risk masks are explicit. | No-create: Direct live order submission.

#### PR #175 — Crypto risk, leverage, and liquidity gate
Category: Runtime | Stage: Stage 2 crypto | Priority: Future-stage runtime | Branch: pr175-crypto-risk-leverage-and-liquidity-gate | Marker: QTT_CRYPTO_RISK_LEVERAGE_AND_LIQUIDITY_GATE_OK
Purpose: Enforce crypto exposure, liquidity, drawdown, and leverage policy. | Gate: Leverage/margin disabled unless owner and source-gated policy explicitly allow. | No-create: Unbounded leverage or venue risk bypass.

#### PR #176 — Crypto live order lifecycle
Category: Live | Stage: Stage 2 crypto | Priority: Future-stage live | Branch: pr176-crypto-live-order-lifecycle | Marker: QTT_CRYPTO_LIVE_ORDER_LIFECYCLE_OK
Purpose: Implement crypto order submit/cancel/fill/finality after owner enablement. | Gate: Idempotent live order lifecycle and reconciliation. | No-create: Unapproved live writes.

#### PR #177 — Crypto limited live canary
Category: Live | Stage: Stage 2 crypto | Priority: Future-stage live | Branch: pr177-crypto-limited-live-canary | Marker: QTT_CRYPTO_LIMITED_LIVE_CANARY_OK
Purpose: Owner-approved limited crypto canary. | Gate: Small-scope canary with kill switch and receipts. | No-create: Full live or arbitrage by default.

#### PR #178 — Crypto reconciliation and post-trade audit
Category: Live | Stage: Stage 2 crypto | Priority: Future-stage live | Branch: pr178-crypto-reconciliation-and-post-trade-audit | Marker: QTT_CRYPTO_RECONCILIATION_AND_POST_TRADE_AUDIT_OK
Purpose: Reconcile fills, balances, PnL, fees, transfers, and custody. | Gate: Ledger and venue state agree or block. | No-create: Profit claim without reconciliation.

#### PR #179 — Crypto cross-exchange arbitrage dry-run
Category: Runtime | Stage: Stage 2 crypto | Priority: Future-stage runtime | Branch: pr179-crypto-cross-exchange-arbitrage-dry-run | Marker: QTT_CRYPTO_CROSS_EXCHANGE_ARBITRAGE_DRY_RUN_OK
Purpose: Dry-run arbitrage after execution normalization. | Gate: Fees, latency, settlement, custody and transfer risk modeled. | No-create: Risk-free wording or live arbitrage.

#### PR #180 — Crypto limited live arbitrage gate
Category: Live | Stage: Stage 2 crypto | Priority: Future-stage live | Branch: pr180-crypto-limited-live-arbitrage-gate | Marker: QTT_CRYPTO_LIMITED_LIVE_ARBITRAGE_GATE_OK
Purpose: Owner-approved limited crypto arbitrage only after dry-run and canary. | Gate: Exact venues/scopes green and owner-approved. | No-create: Unapproved arbitrage.

#### PR #181 — Crypto dashboard panels
Category: Runtime | Stage: Stage 2 crypto | Priority: Future-stage runtime | Branch: pr181-crypto-dashboard-panels | Marker: QTT_CRYPTO_DASHBOARD_PANELS_OK
Purpose: Source, wallet, order, position, and risk panels. | Gate: Dashboard displays receipts only. | No-create: Fact mutation/trading authority.

#### PR #182 — Crypto launch readiness gate
Category: Live | Stage: Stage 2 crypto | Priority: Future-stage live | Branch: pr182-crypto-launch-readiness-gate | Marker: QTT_CRYPTO_LAUNCH_READINESS_GATE_OK
Purpose: Stage-2 launch readiness gate and runbook. | Gate: Launch readiness distinct from execution. | No-create: Execution without owner command.

#### PR #183 — Crypto launch report and Stage-3 handoff
Category: Live | Stage: Stage 2 crypto | Priority: Future-stage live | Branch: pr183-crypto-launch-report-and-stage-3-handoff | Marker: QTT_CRYPTO_LAUNCH_REPORT_AND_STAGE_3_HANDOFF_OK
Purpose: Report live results and next-stage readiness. | Gate: No guarantee; evidence only. | No-create: Auto Stage-3 launch.

#### PR #184 — Equities source-evidence target pack
Category: Static | Stage: Stage 3 equities/stocks | Priority: Future-stage static | Branch: pr184-equities-source-evidence-target-pack | Marker: QTT_EQUITIES_SOURCE_EVIDENCE_TARGET_PACK_OK
Purpose: Define broker/venue/regulatory/order/market-data source targets for equities. | Gate: Source targets explicit. | No-create: Source acceptance or live trading.

#### PR #185 — Broker account, cash, margin, and permission semantics
Category: Runtime | Stage: Stage 3 equities/stocks | Priority: Future-stage runtime | Branch: pr185-broker-account-cash-margin-and-permission-semantics | Marker: QTT_BROKER_ACCOUNT_CASH_MARGIN_AND_PERMISSION_SEMANTICS_OK
Purpose: Bind accepted broker/account/cash/margin facts. | Gate: Cash/margin permissions block unsafe exposure. | No-create: Margin assumptions without source.

#### PR #186 — Equity market-data snapshots
Category: Runtime | Stage: Stage 3 equities/stocks | Priority: Future-stage runtime | Branch: pr186-equity-market-data-snapshots | Marker: QTT_EQUITY_MARKET_DATA_SNAPSHOTS_OK
Purpose: Implement equity quote, trade, corporate action, and session snapshots. | Gate: Market data freshness and session rules explicit. | No-create: Live orders from stale data.

#### PR #187 — Equity strategy and parameter universe
Category: Static | Stage: Stage 3 equities/stocks | Priority: Future-stage static | Branch: pr187-equity-strategy-and-parameter-universe | Marker: QTT_EQUITY_STRATEGY_AND_PARAMETER_UNIVERSE_OK
Purpose: Define equities strategy/parameter universe. | Gate: Universe deterministic and non-live. | No-create: Order authority.

#### PR #188 — Equity replay and paper execution
Category: Runtime | Stage: Stage 3 equities/stocks | Priority: Future-stage runtime | Branch: pr188-equity-replay-and-paper-execution | Marker: QTT_EQUITY_REPLAY_AND_PAPER_EXECUTION_OK
Purpose: Run equity replay/paper with costs, slippage, borrow/margin if source-approved. | Gate: Results separate and immutable. | No-create: Live promotion.

#### PR #189 — Equity quantum portfolio construction
Category: Runtime | Stage: Stage 3 equities/stocks | Priority: Future-stage quantum runtime | Branch: pr189-equity-quantum-portfolio-construction | Marker: QTT_EQUITY_QUANTUM_PORTFOLIO_CONSTRUCTION_OK
Purpose: Compile long-only or owner-approved equity portfolio optimization candidates. | Gate: Risk/cash/position masks enforced. | No-create: Live orders/direct portfolio changes.

#### PR #190 — Equity risk, compliance, and trading restriction gate
Category: Runtime | Stage: Stage 3 equities/stocks | Priority: Future-stage runtime | Branch: pr190-equity-risk-compliance-and-trading-restriction-gate | Marker: QTT_EQUITY_RISK_COMPLIANCE_AND_TRADING_RESTRICTION_GATE_OK
Purpose: Handle PDT, margin, shorting, concentration, and session restrictions when source-gated. | Gate: Restrictions block orders. | No-create: Compliance assumptions.

#### PR #191 — Equity live order lifecycle
Category: Live | Stage: Stage 3 equities/stocks | Priority: Future-stage live | Branch: pr191-equity-live-order-lifecycle | Marker: QTT_EQUITY_LIVE_ORDER_LIFECYCLE_OK
Purpose: Implement broker live order lifecycle after owner enablement. | Gate: Idempotent order and fill receipts. | No-create: Unapproved live writes.

#### PR #192 — Equity limited live canary
Category: Live | Stage: Stage 3 equities/stocks | Priority: Future-stage live | Branch: pr192-equity-limited-live-canary | Marker: QTT_EQUITY_LIMITED_LIVE_CANARY_OK
Purpose: Owner-approved equity canary. | Gate: Small-scope live execution with rollback. | No-create: Scale-up by default.

#### PR #193 — Equity reconciliation and PnL attribution
Category: Live | Stage: Stage 3 equities/stocks | Priority: Future-stage live | Branch: pr193-equity-reconciliation-and-pnl-attribution | Marker: QTT_EQUITY_RECONCILIATION_AND_PNL_ATTRIBUTION_OK
Purpose: Reconcile fills, cash, positions, fees, corporate actions. | Gate: Post-trade accuracy blocks next exposure if unknown. | No-create: Profit fabrication.

#### PR #194 — Corporate action and calendar gate
Category: Runtime | Stage: Stage 3 equities/stocks | Priority: Future-stage runtime | Branch: pr194-corporate-action-and-calendar-gate | Marker: QTT_CORPORATE_ACTION_AND_CALENDAR_GATE_OK
Purpose: Handle splits, dividends, halts, sessions, and calendars. | Gate: Events block or adjust trading. | No-create: Calendar assumptions.

#### PR #195 — Equity smart routing latency and cost optimizer
Category: Runtime | Stage: Stage 3 equities/stocks | Priority: Future-stage runtime | Branch: pr195-equity-smart-routing-latency-and-cost-optimizer | Marker: QTT_EQUITY_SMART_ROUTING_LATENCY_AND_COST_OPTIMIZER_OK
Purpose: Optimize route/order type within broker constraints. | Gate: Cost/latency evidence required. | No-create: Direct live order by optimizer.

#### PR #196 — Equity dashboard panels
Category: Runtime | Stage: Stage 3 equities/stocks | Priority: Future-stage runtime | Branch: pr196-equity-dashboard-panels | Marker: QTT_EQUITY_DASHBOARD_PANELS_OK
Purpose: Equity-specific source/cash/order/risk panels. | Gate: Receipts visible to owner. | No-create: Trading authority.

#### PR #197 — Equity launch readiness gate
Category: Live | Stage: Stage 3 equities/stocks | Priority: Future-stage live | Branch: pr197-equity-launch-readiness-gate | Marker: QTT_EQUITY_LAUNCH_READINESS_GATE_OK
Purpose: Stage-3 launch readiness and runbook. | Gate: Owner command required. | No-create: Execution by readiness alone.

#### PR #198 — Equity launch report and Stage-4 handoff
Category: Live | Stage: Stage 3 equities/stocks | Priority: Future-stage live | Branch: pr198-equity-launch-report-and-stage-4-handoff | Marker: QTT_EQUITY_LAUNCH_REPORT_AND_STAGE_4_HANDOFF_OK
Purpose: Report results and future derivative readiness. | Gate: No guarantee. | No-create: Auto derivatives launch.

#### PR #199 — Derivatives source-evidence target pack
Category: Static | Stage: Stage 4 options/futures | Priority: Future-stage static | Branch: pr199-derivatives-source-evidence-target-pack | Marker: QTT_DERIVATIVES_SOURCE_EVIDENCE_TARGET_PACK_OK
Purpose: Define option/future source targets for chains, greeks, margin, exercise, assignment, settlement, expiry, contract specs. | Gate: Source targets explicit. | No-create: Source facts/live orders.

#### PR #200 — Option chain, greeks, and symbol semantics binding
Category: Runtime | Stage: Stage 4 options/futures | Priority: Future-stage runtime | Branch: pr200-option-chain-greeks-and-symbol-semantics-binding | Marker: QTT_OPTION_CHAIN_GREEKS_AND_SYMBOL_SEMANTICS_BINDING_OK
Purpose: Bind option chain, greeks, expiration, OCC/symbol, and quote semantics. | Gate: Greeks and chains are source-bound. | No-create: Invented greeks/chain facts.

#### PR #201 — Margin, assignment, exercise, and settlement semantics
Category: Runtime | Stage: Stage 4 options/futures | Priority: Future-stage runtime | Branch: pr201-margin-assignment-exercise-and-settlement-semantics | Marker: QTT_MARGIN_ASSIGNMENT_EXERCISE_AND_SETTLEMENT_SEMANTICS_OK
Purpose: Bind margin, assignment/exercise, settlement, and futures expiry/roll semantics. | Gate: Unknown assignment/margin blocks exposure. | No-create: Unbounded derivatives risk.

#### PR #202 — Derivatives market-data snapshots
Category: Runtime | Stage: Stage 4 options/futures | Priority: Future-stage runtime | Branch: pr202-derivatives-market-data-snapshots | Marker: QTT_DERIVATIVES_MARKET_DATA_SNAPSHOTS_OK
Purpose: Snapshot chains, greeks, implied volatility, futures curves, and sessions. | Gate: Freshness/session/expiry locks explicit. | No-create: Live orders from stale chain.

#### PR #203 — Derivatives strategy universe
Category: Static | Stage: Stage 4 options/futures | Priority: Future-stage static | Branch: pr203-derivatives-strategy-universe | Marker: QTT_DERIVATIVES_STRATEGY_UNIVERSE_OK
Purpose: Define spreads, hedges, options/futures strategies and allowed constraints. | Gate: Universe deterministic. | No-create: Live authority.

#### PR #204 — Volatility model calibration and walk-forward validation
Category: Runtime | Stage: Stage 4 options/futures | Priority: Future-stage runtime | Branch: pr204-volatility-model-calibration-and-walk-forward-validation | Marker: QTT_VOLATILITY_MODEL_CALIBRATION_AND_WALK_FORWARD_VALIDATION_OK
Purpose: Calibrate IV/skew/volatility features with purged validation. | Gate: No leakage and drift monitored. | No-create: Direct order authority.

#### PR #205 — Quantum combinatorial spread optimizer
Category: Runtime | Stage: Stage 4 options/futures | Priority: Future-stage quantum runtime | Branch: pr205-quantum-combinatorial-spread-optimizer | Marker: QTT_QUANTUM_COMBINATORIAL_SPREAD_OPTIMIZER_OK
Purpose: Compile option/future spread selection to QUBO/Ising/hybrid forms. | Gate: Risk/margin/assignment masks enforced. | No-create: Live order submission.

#### PR #206 — Derivatives replay and paper execution
Category: Runtime | Stage: Stage 4 options/futures | Priority: Future-stage runtime | Branch: pr206-derivatives-replay-and-paper-execution | Marker: QTT_DERIVATIVES_REPLAY_AND_PAPER_EXECUTION_OK
Purpose: Run derivatives replay/paper with assignment, exercise, margin, and expiry models. | Gate: Results immutable and separate. | No-create: Live promotion.

#### PR #207 — Greeks, scenario, assignment, and tail-risk gate
Category: Runtime | Stage: Stage 4 options/futures | Priority: Future-stage runtime | Branch: pr207-greeks-scenario-assignment-and-tail-risk-gate | Marker: QTT_GREEKS_SCENARIO_ASSIGNMENT_AND_TAIL_RISK_GATE_OK
Purpose: Enforce greeks, scenario, stress, assignment, expiry, and liquidity constraints. | Gate: Risk blocks unsafe strategies. | No-create: Risk bypass.

#### PR #208 — Derivatives order lifecycle and spread net-price gate
Category: Live | Stage: Stage 4 options/futures | Priority: Future-stage live | Branch: pr208-derivatives-order-lifecycle-and-spread-net-price-gate | Marker: QTT_DERIVATIVES_ORDER_LIFECYCLE_AND_SPREAD_NET_PRICE_GATE_OK
Purpose: Implement live complex order lifecycle when owner-enabled. | Gate: Net price, legs, acknowledgments, fills, and cancels tracked. | No-create: Unapproved complex orders.

#### PR #209 — Derivatives limited live canary
Category: Live | Stage: Stage 4 options/futures | Priority: Future-stage live | Branch: pr209-derivatives-limited-live-canary | Marker: QTT_DERIVATIVES_LIMITED_LIVE_CANARY_OK
Purpose: Owner-approved limited derivatives canary. | Gate: Small-scope and hedged where required. | No-create: Scale-up by default.

#### PR #210 — Derivatives reconciliation, assignment, and exercise audit
Category: Live | Stage: Stage 4 options/futures | Priority: Future-stage live | Branch: pr210-derivatives-reconciliation-assignment-and-exercise-audit | Marker: QTT_DERIVATIVES_RECONCILIATION_ASSIGNMENT_AND_EXERCISE_AUDIT_OK
Purpose: Reconcile legs, fees, margin, cash, assignment/exercise events, and PnL. | Gate: Post-trade risk accurately updated. | No-create: Profit fabrication.

#### PR #211 — Futures contract roll, expiry, and carrying-cost gate
Category: Runtime | Stage: Stage 4 options/futures | Priority: Future-stage runtime | Branch: pr211-futures-contract-roll-expiry-and-carrying-cost-gate | Marker: QTT_FUTURES_CONTRACT_ROLL_EXPIRY_AND_CARRYING_COST_GATE_OK
Purpose: Handle futures roll, expiry, carrying cost, and contract calendar semantics. | Gate: Roll/expiry risks are source-gated. | No-create: Blind futures roll.

#### PR #212 — Futures limited live canary
Category: Live | Stage: Stage 4 options/futures | Priority: Future-stage live | Branch: pr212-futures-limited-live-canary | Marker: QTT_FUTURES_LIMITED_LIVE_CANARY_OK
Purpose: Owner-approved futures canary if owner opens futures live scope. | Gate: Exact venue/account/contract gates green. | No-create: Unapproved futures live.

#### PR #213 — Cross-derivative hedging optimizer
Category: Runtime | Stage: Stage 4 options/futures | Priority: Future-stage runtime | Branch: pr213-cross-derivative-hedging-optimizer | Marker: QTT_CROSS_DERIVATIVE_HEDGING_OPTIMIZER_OK
Purpose: Optimize hedges across options/futures/equities after source/gate readiness. | Gate: Hedges are risk-reducing and receipt-backed. | No-create: Unapproved cross-market exposure.

#### PR #214 — Derivatives dashboard panels
Category: Runtime | Stage: Stage 4 options/futures | Priority: Future-stage runtime | Branch: pr214-derivatives-dashboard-panels | Marker: QTT_DERIVATIVES_DASHBOARD_PANELS_OK
Purpose: Expose chain, greeks, margin, assignment, order, and quantum spread panels. | Gate: Dashboard facts are receipt-only. | No-create: Trading authority.

#### PR #215 — Derivatives launch readiness gate
Category: Live | Stage: Stage 4 options/futures | Priority: Future-stage live | Branch: pr215-derivatives-launch-readiness-gate | Marker: QTT_DERIVATIVES_LAUNCH_READINESS_GATE_OK
Purpose: Stage-4 derivatives launch readiness and runbook. | Gate: Owner command required. | No-create: Readiness as execution.

#### PR #216 — Derivatives launch report and Stage-5 handoff
Category: Live | Stage: Stage 4 options/futures | Priority: Future-stage live | Branch: pr216-derivatives-launch-report-and-stage-5-handoff | Marker: QTT_DERIVATIVES_LAUNCH_REPORT_AND_STAGE_5_HANDOFF_OK
Purpose: Report derivatives results and cross-market readiness. | Gate: No guarantee. | No-create: Auto cross-market launch.

#### PR #217 — Global source and connector currentness monitor
Category: Runtime | Stage: Stage 5 cross-market automation | Priority: Future-stage runtime | Branch: pr217-global-source-and-connector-currentness-monitor | Marker: QTT_GLOBAL_SOURCE_AND_CONNECTOR_CURRENTNESS_MONITOR_OK
Purpose: Monitor all market sleeves for source, connector, semantic, cash, and health currentness. | Gate: Stale scopes block expansion. | No-create: Silent stale use.

#### PR #218 — Cross-market portfolio exposure and risk engine
Category: Runtime | Stage: Stage 5 cross-market automation | Priority: Future-stage runtime | Branch: pr218-cross-market-portfolio-exposure-and-risk-engine | Marker: QTT_CROSS_MARKET_PORTFOLIO_EXPOSURE_AND_RISK_ENGINE_OK
Purpose: Aggregate exposure across prediction markets, crypto, equities, and derivatives. | Gate: Global risk limits and correlations are visible. | No-create: Capital expansion without owner.

#### PR #219 — Quantum resource scheduler across markets
Category: Runtime | Stage: Stage 5 cross-market automation | Priority: Future-stage quantum runtime | Branch: pr219-quantum-resource-scheduler-across-markets | Marker: QTT_QUANTUM_RESOURCE_SCHEDULER_ACROSS_MARKETS_OK
Purpose: Schedule quantum jobs by value, latency, cost, queue, and freshness. | Gate: Quantum resources used only where net utility survives comparator checks. | No-create: Live backend dependency.

#### PR #220 — Cross-market capital allocation optimizer
Category: Runtime | Stage: Stage 5 cross-market automation | Priority: Future-stage runtime | Branch: pr220-cross-market-capital-allocation-optimizer | Marker: QTT_CROSS_MARKET_CAPITAL_ALLOCATION_OPTIMIZER_OK
Purpose: Optimize capital allocation across enabled market sleeves. | Gate: Allocation stays inside owner-approved capital/risk bands. | No-create: Treasury movement or risk expansion.

#### PR #221 — Global kill switch and market-sleeve pause controller
Category: Live | Stage: Stage 5 cross-market automation | Priority: Future-stage live | Branch: pr221-global-kill-switch-and-market-sleeve-pause-controller | Marker: QTT_GLOBAL_KILL_SWITCH_AND_MARKET_SLEEVE_PAUSE_CONTROLLER_OK
Purpose: Implement global and sleeve-specific halt/pause/resume controls. | Gate: Owner emergency sovereignty preserved. | No-create: Uncontrolled restart.

#### PR #222 — Global owner dashboard and evidence board
Category: Runtime | Stage: Stage 5 cross-market automation | Priority: Future-stage runtime | Branch: pr222-global-owner-dashboard-and-evidence-board | Marker: QTT_GLOBAL_OWNER_DASHBOARD_AND_EVIDENCE_BOARD_OK
Purpose: Unify source, risk, cash, order, PnL, quantum, and agent panels across sleeves. | Gate: Owner sees all gates and evidence. | No-create: Dashboard trading authority.

#### PR #223 — Autonomous operation graduation gates
Category: Runtime | Stage: Stage 5 cross-market automation | Priority: Future-stage runtime | Branch: pr223-autonomous-operation-graduation-gates | Marker: QTT_AUTONOMOUS_OPERATION_GRADUATION_GATES_OK
Purpose: Define evidence gates for higher automation stages while preserving owner sovereignty. | Gate: Automation stage transitions require evidence and owner approval. | No-create: Owner replacement or unsupervised expansion.

#### PR #224 — Roadmap coverage closure and future PR reserve
Category: Static | Stage: Stage 5 cross-market automation | Priority: Future-stage static | Branch: pr224-roadmap-coverage-closure-and-future-pr-reserve | Marker: QTT_ROADMAP_COVERAGE_CLOSURE_AND_FUTURE_PR_RESERVE_OK
Purpose: Close coverage for current roadmap and reserve future PR namespace. | Gate: All future market expansions are owner-approved and sequential unless owner reorders. | No-create: Automatic launch of dormant sleeves.

## 11. Quantum optimization architecture and Day‑1 latency doctrine
- Quantum is prioritized where it is suitable and beneficial, but never as direct live order authority. QTT must always preserve classical baselines as valid comparators.
- PR #82 defines quantum applicability metadata. PR #83 defines owner quantum priority. PR #84 defines formulas. PR #85 ranks candidate descriptors. PR #86 defines arbitration grammar. PR #87–#89 generate/select/handoff static candidate stacks. PR #125–#132 are the first runtime quantum-precompute block.
- True-quantum, quantum-inspired, hybrid, and classical paths must be compared on net edge after fees, slippage, latency, uncertainty, queue delay, cost, and risk. No quantum advantage claim is allowed without evidence receipts.
- Live low-latency path cannot call a quantum backend, simulator, LLM reasoning, source retrieval, source acceptance, external research, or dashboard review. It may consume only precomputed, fresh, validated snapshots and artifacts.
- No-trade and classical fallback are valid optimal outputs when source/cash/latency/risk/quantum-freshness states are not green.

| Quantum policy mode | Priority multiplier | Family multiplier | Static meaning |
| --- | --- | --- | --- |
| QUANTUM_NEUTRAL | 1.00 | 1.00 | No preference; classical comparator remains equal. |
| QUANTUM_PREFERRED | 1.10 | 1.05 | Default preferred mode; mild quantum boost for future scoring only. |
| QUANTUM_STRONGLY_PREFERRED | 1.25 | 1.10 | Stronger boost, still internal-only and evidence-gated. |
| QUANTUM_FIRST | 1.35 | 1.15 | Try quantum-applicable path first in future gates, but not live backend/order authority. |
| OWNER_FORCED_QUANTUM | 1.50 | 1.20 | Owner-forced internal quantum path with owner_override_basis; cannot fabricate facts/evidence. |
| HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK | 1.15 | 1.05 | Requires classical comparator; quantum may win deterministic tie-break only. |

- Multiplier bounds for PR #83 static policy: priority_multiplier must be 1.00–1.50; quantum_applicable_family_multiplier must be 1.00–1.20.
- Determinism requirements: no random, no generated UUID/timestamp at validation time, no nondeterministic set iteration, no environment-dependent output, no network calls, no external source reads, no quantum backend calls, no simulator calls, no optimizer calls, no live connector calls, and no account/private-state reads in static policy PRs.
- Runtime quantum PRs must record provider, shots, queue latency, noise/error, cost, artifact freshness, classical comparator, regret, and fallback status. These values must come from runtime receipts or accepted source/provider evidence, not guesses.

## 12. Standard Codex PR prompt and validation rules
- Every PR prompt must state delivery label, branch, semantic task ID, expected baseline, exact scope, explicit non-authority boundaries, required files, validators, tests, commands, success markers, and handoff report format.
- Codex must not commit, push, open PRs, merge, edit docs/master_plan/QTT_MasterPlan_Current.md, create AtomicRows.bundle.jsonl, create AtomicRows.bundle.sha256, or create runtime/live/source/connector/order/profit/quantum-backend artifacts unless that exact future owner-approved PR opens the scope.
- Each PR must run focused validator, focused tests, cumulative validation gates, fresh pytest, compileall, git diff --check, master-plan diff check, bundle/hash absence checks where applicable, and status report.
- If any required validation fails, Codex must stop and report exact file/path/error. It must not claim success.
- Treat “no bug” as coding discipline and validation target, not a mathematical guarantee. Use deterministic pure functions, explicit error messages, sorted outputs, standard library unless existing repo convention permits otherwise, and fail-closed behavior.
Required handoff facts for every PR:
1. Branch name.
2. Base HEAD short SHA.
3. Files created.
4. Files modified.
5. Validator marker emitted.
6. Exact commands run.
7. Exact pass/fail results.
8. Compileall / short-pycache compileall status.
9. docs/master_plan/QTT_MasterPlan_Current.md diff status.
10. AtomicRows.bundle.jsonl absence or scoped bundle status.
11. AtomicRows.bundle.sha256 absence or scoped SHA status.
12. Confirmation of no unauthorized runtime/live/order/source/connector/profit/quantum-backend artifacts.
13. Confirmation of no unauthorized optimizer/scoring/ranking/selection/replay/paper artifacts.
14. Explicit statement: no commit, no push, no PR opened, no merge performed.

## 13. Canonical stage-1 launch sequence after PR #104
Build source-evidence retrieval and acceptance runtime tools for the three Stage‑1 venues.
Bind per-venue connector semantics only from accepted target-field source packets.
Create runtime cash/account/private-state read receipts and block unknown cash.
Create market-data snapshots, runtime resolver snapshots, replay engine, paper engine, and immutable result ledgers.
Run quantum/classical candidate precompute and comparator ledger outside the live low-latency path.
Create risk, exposure, owner approval, kill switch, telemetry, and Day‑1 drill runtime infrastructure.
Open live connector write surfaces only per venue after exact source/cash/risk/kill-switch/order-state gates are green.
Run limited live canary using explicit owner command and exact venue/account/market/session scope.
Reconcile fills/cash/orders/positions/finality and report result with no profit guarantee.
Only after canary review may owner approve post-launch advanced scale, live arbitrage, or future-market expansion.

## 14. Sequential numbering audit

| Audit item | Result |
| --- | --- |
| Sequential PR numbering from #63 to #224 | PASS — PR #63 through PR #224 are sequential and sorted in this roadmap. |
| Existing static completion through PR #82 preserved | PASS |
| Current next PR after PR #82 | PR #83 — Owner quantum priority policy registry |
| New Stage‑1 launch closure after PR #104 | PR #105–#151 |
| Future market expansion after Stage‑1 | PR #169–#224 |

## 15. Final roadmap verdict
- The prior roadmap through PR #104 is necessary but not sufficient for Stage‑1 live trading. It should remain static/gated.
- The missing work is now explicitly represented as PR #105–#151 for Stage‑1 launch closure, with PR #152–#168 reserved for post-launch robustness and scale-up.
- The roadmap now separates Static, Runtime, and Live PRs canonically so Codex can build verified contracts first, then runtime engines, then owner-approved live canary/live trading.
- The roadmap preserves master-plan constraints: no fabricated source facts, no connector semantic invention, no runtime cash without receipt, no live order without owner command and all gates, no direct quantum order submission, and no profit/quantum-advantage guarantees.
- Recommended planning number: after PR #104, expect 47 Stage‑1 launch-essential PRs before limited live Day‑1 launch closure. From current next PR #83, expect 69 PRs through Stage‑1 launch closure.