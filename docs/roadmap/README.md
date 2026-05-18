# QTT Roadmap Artifacts

This folder contains the owner-approved consolidated roadmap artifacts for Codex-readable planning.

## Files

- `QTT_PRs_Roadmap_Consolidated_Static_Runtime_Live_Stage1_to_Stage5_v1_0.md` — Codex-readable roadmap guidance.
- `QTT_PRs_Roadmap_Index_v1_0.json` — machine-readable PR index for deterministic extraction.
- `QTT_PRs_Roadmap_Consolidated_Static_Runtime_Live_Stage1_to_Stage5_v1_0.docx` — owner/human archival copy.
- `QTT_PR_Identity_Roster_v1_0.json` — canonical translator between repo, roadmap, blueprint, and GitHub PR identities.
- `QTT_PR_Identity_Roster_v1_0.md` — explanatory companion for the PR identity roster.

## Authority boundary

These files are forward roadmap guidance only.

Implementation truth remains repository artifacts, schemas, validators, generated reports, authority boundaries, validation evidence, and explicit owner-approved instructions.

Do not treat PR numbers as implementation truth.

Use `QTT_PR_Identity_Roster_v1_0.json` as the canonical translator between repo-canonical labels, roadmap labels, blueprint labels, and GitHub audit numbers. GitHub PR numbers are audit-only; repo-canonical labels and repo artifacts remain implementation truth; roadmap labels remain planning/orchestration labels; blueprint labels remain implementation-scope labels; same-number equality must not be inferred. Future PR prompts must update or reference the roster before functional work proceeds.

Do not edit `docs/master_plan/QTT_MasterPlan_Current.md` unless the owner explicitly approves.

Do not create `docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl` or `docs/master_plan/atomic_rows/AtomicRows.bundle.sha256` unless the exact owner-approved AtomicRows bundle/hash PR authorizes it.

Do not create runtime/live/source/connector/order/profit/quantum-backend authority unless the exact current PR explicitly opens that scope.

## Corrective control-plane overlays

- PR115A merged owner-controlled SHA dormancy non-participation policy.
- PR116A is a corrective architecture/control-plane PR that centralizes active non-SHA Day-1 gate states before any future unblocking.
- PR116A does not unblock any Day-1 gate, does not create final readiness, and does not create runtime/live/order/profit/quantum-backend authority.
- Future PRs must flip only one centralized gate state at a time and materialize or enable only one artifact/capability at a time.
- PR numbers remain delivery labels only; implementation truth remains canonical files, schemas, validators, reports, authority boundaries, validation evidence, and owner-approved instructions.

## Stage-1 priority

Stage 1 prediction-market launch-essential scope runs through PR #151.

- Static launch-essential foundation: PR #83–#104.
- Runtime + Live launch-essential closure: PR #105–#151.
- Stage-1 post-launch robustness / scale-up: PR #152–#168.
- Future-market expansion: PR #169–#224.

Stage-1 platform scope: Kalshi, Polymarket, FORECASTEX_IBKR.

## Required prompt header for PR #83 and later

Codex must read this folder before modifying files for every PR from PR #83 onward.

Use these roadmap files only as forward roadmap guidance. Preserve the current PR scope exactly and do not pull future Runtime or Live work into earlier Static PRs.
