# QTT Roadmap Artifacts

This folder contains the owner-approved consolidated roadmap artifacts for Codex-readable planning.

## Files

- `QTT_PRs_Roadmap_Consolidated_Static_Runtime_Live_Stage1_to_Stage5_v1_0.md` — Codex-readable roadmap guidance.
- `QTT_PRs_Roadmap_Index_v1_0.json` — machine-readable PR index for deterministic extraction.
- `QTT_PRs_Roadmap_Consolidated_Static_Runtime_Live_Stage1_to_Stage5_v1_0.docx` — owner/human archival copy.

## Authority boundary

These files are forward roadmap guidance only.

Implementation truth remains repository artifacts, schemas, validators, generated reports, authority boundaries, validation evidence, and explicit owner-approved instructions.

Do not treat PR numbers as implementation truth.

Do not edit `docs/master_plan/QTT_MasterPlan_Current.md` unless the owner explicitly approves.

Do not create `docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl` or `docs/master_plan/atomic_rows/AtomicRows.bundle.sha256` unless the exact owner-approved AtomicRows bundle/hash PR authorizes it.

Do not create runtime/live/source/connector/order/profit/quantum-backend authority unless the exact current PR explicitly opens that scope.

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
