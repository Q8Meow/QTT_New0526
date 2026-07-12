#!/usr/bin/env python3
"""Centralized narrow changed-path scope registry for validation guards."""

from __future__ import annotations

from fnmatch import fnmatchcase


PR168_GFP_BRANCH = "pr168-gfp-global-formula-discovery-real-computation"
PR168_RP_BRANCH = "pr168-rp-formula-based-replay-paper-recompute"
PR168_RANK_BRANCH = "pr168-rank-evidence-backed-ranking"
PR168_DATA1_BRANCH = "pr168-data1-public-market-data-snapshots"
PR168_DATA1A_BRANCH = "pr168-data1a-focused-audit-gfp2r-readiness"
PR168_GFP2R_BRANCH = "pr168-gfp2r-data1a-gated-candidate-recompute"
PR168_RP2_BRANCH = "pr168-rp2-map2-gfp2r-replay-paper-recompute"
PR168_MAP3_BRANCH = "pr168-map3-qku-formula-id-intake"
PR168_RP3_BRANCH = "pr168-rp3-map3-formula-replay-paper-evidence"
PR168_RANK3_BRANCH = "pr168-rank3-rp3-evidence-stack-ranking"
PR168_RP5A_BRANCH = "pr168-rp5a-legacy-semantic-audit"
PR168_RP5B_BRANCH = "pr168-rp5b-active-registry-safe-legacy-cleanup"
PR168_RP5C_BRANCH = "pr168-rp5c-immutable-qku-formula-library"
PR168_RP5C_POST_MERGE_REPAIR_BRANCH = "pr168-rp5c-postmerge-ci-repair"
PR168_VS1_BRANCH = "pr168-vs1-trading-intelligence-vertical-slice"
PR168_RP5D_BRANCH = "pr168-rp5d-replay-paper-executability-tiers"
PR168_RP5E_BRANCH = "pr168-rp5e-stack-gen"
PR168_RP5D_R1_BRANCH = "pr168-rp5d-r1-exec-now-unlock"
PR168_RP5F_BRANCH = "pr168-rp5f-dynamic-target-order-grid"
PR168_RP5G_BRANCH = "pr168-rp5g-trade-plan-sim-engine"
PR168_RANK4_BRANCH = "pr168-rank4-exec-advisory-ranking"
PR168_QOPT1_BRANCH = "pr168-qopt1-quantum-classical-batch-optimization"
PR168_VS2_BRANCH = "pr168-vs2-paper-intent-candidate-generator"
PR168_MEM1_BRANCH = "pr168-mem1-condition-scoped-outcome-memory"
PR169_DASH1_BRANCH = "pr169-dash1-owner-dashboard-interactive-research-v6"
PR169_DASH1_UI1_BRANCH = "pr169-dash1-ui1-theme-switch-safe-renderer-v9"
PR169_DASH1_UI1_R1_BRANCH = "pr169-dash1-ui1-r1-v3-owner12"
PR169_DASH1_UI1_R2_BRANCH = "pr169-dash1-ui1-r2-guided-owner-coach-v7"
PR169_DASH1_UI1_R2_R1_BRANCH = "pr169-dash1-ui1-r2-r1-interaction-v4"
PR169_DASH1_UI1_R2_R2_BRANCH = "pr169-dash1-ui1-r2-r2-owner-product-ux"
PR169_DASH1_UI1_R2_R3_BRANCH = "pr169-dash1-ui1-r2-r3-owner-product-polish"
PR169_DASH1_UI1_R2_R4_BRANCH = "pr169-dash1-ui1-r2-r4-owner-visual-acceptance-agent-monitoring"
PR169_DASH1_UI1_R2_R5_BRANCH = "pr169-dash1-ui1-r2-r5-owner-visual-qa-truth-repair"
PR169_DASH1_UI1_R2_R6_BRANCH = "pr169-ui1-r2r6"
PR169_READINESS1_BRANCH = "pr169-readiness1"
PR169_PRETRADE1_BRANCH = "pr169-pretrade1"
PR169_SVC1_BRANCH = "pr169-svc1"
PR169_AGENT_ORCH1_BRANCH = "pr169-agent-orch1"
PR169_QKU_FORMULA_EXP1_BRANCH = "pr169-qku-formula-exp1"
PR169_QKU_FORMULA_EXP1_REPAIR_BRANCH = "pr169-qku-formula-exp1-r1"
PR169_VAL1_BRANCH = "pr169-val1"
VALIDATION_FIXTURE_BRANCH = "pr-ci-fastfail-validation-context-preflight"

_PR168_BRANCHES = frozenset(
    {
        PR168_GFP_BRANCH,
        PR168_RP_BRANCH,
        PR168_RANK_BRANCH,
        PR168_DATA1_BRANCH,
        PR168_DATA1A_BRANCH,
        PR168_GFP2R_BRANCH,
        PR168_RP2_BRANCH,
        PR168_MAP3_BRANCH,
        PR168_RP3_BRANCH,
        PR168_RANK3_BRANCH,
        PR168_RP5A_BRANCH,
        PR168_RP5B_BRANCH,
        PR168_RP5C_BRANCH,
        PR168_RP5C_POST_MERGE_REPAIR_BRANCH,
        PR168_VS1_BRANCH,
        PR168_RP5D_BRANCH,
        PR168_RP5E_BRANCH,
        PR168_RP5D_R1_BRANCH,
        PR168_RP5F_BRANCH,
        PR168_RP5G_BRANCH,
        PR168_RANK4_BRANCH,
        PR168_QOPT1_BRANCH,
        PR168_VS2_BRANCH,
        PR168_MEM1_BRANCH,
        PR169_DASH1_BRANCH,
        PR169_DASH1_UI1_BRANCH,
        PR169_DASH1_UI1_R1_BRANCH,
        PR169_DASH1_UI1_R2_BRANCH,
        PR169_DASH1_UI1_R2_R1_BRANCH,
        PR169_DASH1_UI1_R2_R2_BRANCH,
        PR169_DASH1_UI1_R2_R3_BRANCH,
        PR169_DASH1_UI1_R2_R4_BRANCH,
        PR169_DASH1_UI1_R2_R5_BRANCH,
        PR169_DASH1_UI1_R2_R6_BRANCH,
        PR169_READINESS1_BRANCH,
        PR169_PRETRADE1_BRANCH,
        PR169_SVC1_BRANCH,
        PR169_AGENT_ORCH1_BRANCH,
        PR169_QKU_FORMULA_EXP1_BRANCH,
        PR169_QKU_FORMULA_EXP1_REPAIR_BRANCH,
        PR169_VAL1_BRANCH,
        VALIDATION_FIXTURE_BRANCH,
    }
)
_VALIDATION_CONTEXT_BRANCHES = frozenset({VALIDATION_FIXTURE_BRANCH})

_PR168_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/build_pr168_gfp_global_formula_discovery_real_computation.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/stage1_prediction_markets/pr167_open_trade_simulator_integration/test_pr167_idempotence.py",
        "src/qtt/stage1_prediction_markets/atomicrows_semantic_field_coverage_enrichment_plan/report.py",
        "src/qtt/stage1_prediction_markets/atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/report.py",
        "src/qtt/stage1_prediction_markets/atomicrows_semantic_value_materialization_owner_authorization_gate/report.py",
        "src/qtt/stage1_prediction_markets/grand_global_debug_logical_consistency_audit/report.py",
        "src/qtt/stage1_prediction_markets/qtt_owner_global_override_directive_currentization_and_internal_gate_release/report.py",
        "tools/ci_branch_context.py",
        "tools/validate_idempotence_runtime_containment.py",
    }
)

_PR168_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_GFP_*.report.json",
    "docs/master_plan/generated/pr168_gfp_shards/PR168_GFP_*.json",
    "src/qtt/stage1_prediction_markets/pr168_gfp_real_computation/**",
    "tests/pr168_gfp/**",
    "tools/validate_pr168_gfp_*.py",
)

_PR168_RP_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tools/qtt_authority_reason_code_registry.py",
        "tools/validate_qtt_authority_reason_code_registry.py",
        "tests/tools/test_qtt_authority_reason_code_registry.py",
        "tools/validation_inventory.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tools/build_pr168_rp_formula_based_replay_paper_recompute.py",
        "tools/run_validation_gates.py",
    }
)

_PR168_RP_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RP_*.report.json",
    "docs/master_plan/generated/pr168_rp_shards/PR168_RP_*.report.json",
    "tools/pr168_rp_*.py",
    "tools/validate_pr168_rp_*.py",
    "tests/pr168_rp/**",
)

_PR168_RANK_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tools/qtt_authority_reason_code_registry.py",
        "tools/validate_qtt_authority_reason_code_registry.py",
        "tests/tools/test_qtt_authority_reason_code_registry.py",
        "tools/validation_inventory.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tools/run_validation_gates.py",
        "tools/build_pr168_rank_evidence_backed_ranking.py",
    }
)

_PR168_RANK_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RANK_*.report.json",
    "docs/master_plan/generated/pr168_rank_shards/PR168_RANK_*.report.json",
    "tools/pr168_rank_*.py",
    "tools/validate_pr168_rank_*.py",
    "tests/pr168_rank/**",
)

_PR168_DATA1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/build_pr168_data1_public_market_data_snapshots.py",
        "tools/validate_pr168_data1_public_market_data_snapshots.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
    }
)

_PR168_DATA1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_DATA1_*.report.json",
    "docs/master_plan/generated/pr168_data1_snapshots/**/*.jsonl",
    "docs/master_plan/generated/pr168_data1_snapshots/**/*.manifest.json",
    "docs/master_plan/generated/pr168_data1_forward_l2/**/*.jsonl",
    "docs/master_plan/generated/pr168_data1_forward_l2/**/*.manifest.json",
    "docs/master_plan/generated/pr168_data1_historical_replay_candidates/**/*.jsonl",
    "docs/master_plan/generated/pr168_data1_historical_replay_candidates/**/*.manifest.json",
    "tools/pr168_data1_*.py",
    "tests/pr168_data1/**",
)

_PR168_DATA1A_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/build_pr168_data1a_focused_audit.py",
        "tools/validate_pr168_data1a_focused_audit.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_DATA1A_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_DATA1A_*.report.json",
    "docs/master_plan/generated/pr168_data1a_audit/*.jsonl",
    "docs/master_plan/generated/pr168_data1a_audit/*.manifest.json",
    "docs/master_plan/generated/pr168_data1a_audit/**/*.jsonl",
    "docs/master_plan/generated/pr168_data1a_audit/**/*.manifest.json",
    "tools/pr168_data1a_*.py",
    "tests/pr168_data1a/**",
)

_PR168_GFP2R_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/build_pr168_gfp2r_data1a_gated_candidate_recompute.py",
        "tools/validate_pr168_gfp2r_data1a_gated_candidate_recompute.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_GFP2R_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_GFP2R_*.report.json",
    "docs/master_plan/generated/pr168_gfp2r_candidate_compute/*.jsonl",
    "docs/master_plan/generated/pr168_gfp2r_candidate_compute/*.manifest.json",
    "docs/master_plan/generated/pr168_gfp2r_candidate_compute/**/*.jsonl",
    "docs/master_plan/generated/pr168_gfp2r_candidate_compute/**/*.manifest.json",
    "tools/pr168_gfp2r_*.py",
    "tests/pr168_gfp2r/**",
)

_PR168_RP2_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp2_map2.py",
        "tools/validate_pr168_rp2_map2.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_RP2_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RP2_*.report.json",
    "docs/master_plan/generated/rp2p/*.jsonl",
    "docs/master_plan/generated/rp2p/*.manifest.json",
    "docs/master_plan/generated/rp2p/**/*.jsonl",
    "docs/master_plan/generated/rp2p/**/*.manifest.json",
    "tools/pr168_rp2_*.py",
    "tests/pr168_rp2/**",
)

_PR168_MAP3_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_map3.py",
        "tools/validate_pr168_map3.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tools/validation_inventory.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tools/run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)

_PR168_MAP3_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_MAP3_*.report.json",
    "docs/master_plan/generated/map3/*.jsonl",
    "docs/master_plan/generated/map3/*.manifest.json",
    "docs/master_plan/generated/map3/**/*.jsonl",
    "docs/master_plan/generated/map3/**/*.manifest.json",
    "tools/pr168_map3_*.py",
    "tests/pr168_map3/**",
)

_PR168_RP3_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp3.py",
        "tools/validate_pr168_rp3.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_RP3_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RP3_*.report.json",
    "docs/master_plan/generated/rp3/*.jsonl",
    "docs/master_plan/generated/rp3/*.manifest.json",
    "docs/master_plan/generated/rp3/**/*.jsonl",
    "docs/master_plan/generated/rp3/**/*.manifest.json",
    "tools/pr168_rp3_*.py",
    "tests/pr168_rp3/**",
)

_PR168_RANK3_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rank3.py",
        "tools/validate_pr168_rank3.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_RANK3_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RANK3_*.report.json",
    "docs/master_plan/generated/rank3/*.jsonl",
    "docs/master_plan/generated/rank3/*.manifest.json",
    "docs/master_plan/generated/rank3/**/*.jsonl",
    "docs/master_plan/generated/rank3/**/*.manifest.json",
    "tools/pr168_rank3_*.py",
    "tests/pr168_rank3/**",
)

_PR168_RP5A_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp5a_legacy_semantic_audit.py",
        "tools/validate_pr168_rp5a_legacy_semantic_audit.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)

_PR168_RP5A_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RP5A_*.report.json",
    "docs/master_plan/generated/rp5a/*.jsonl",
    "docs/master_plan/generated/rp5a/*.manifest.json",
    "docs/master_plan/generated/rp5a/**/*.jsonl",
    "docs/master_plan/generated/rp5a/**/*.manifest.json",
    "tools/pr168_rp5a_*.py",
    "tests/pr168_rp5a/**",
)

_PR168_RP5B_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp5b_active_registry_safe_cleanup.py",
        "tools/validate_pr168_rp5b_active_registry_safe_cleanup.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)

_PR168_RP5B_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RP5B_*.report.json",
    "docs/master_plan/generated/rp5b/*.jsonl",
    "docs/master_plan/generated/rp5b/*.manifest.json",
    "docs/master_plan/generated/rp5b/**/*.jsonl",
    "docs/master_plan/generated/rp5b/**/*.manifest.json",
    "tools/pr168_rp5b_*.py",
    "tests/pr168_rp5b/**",
)

_PR168_RP5C_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp5c_immutable_qku_formula_library.py",
        "tools/validate_pr168_rp5c_immutable_qku_formula_library.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)

_PR168_RP5C_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RP5C_*.report.json",
    "docs/master_plan/generated/rp5c/*.jsonl",
    "docs/master_plan/generated/rp5c/*.manifest.json",
    "docs/master_plan/generated/rp5c/**/*.jsonl",
    "docs/master_plan/generated/rp5c/**/*.manifest.json",
    "tools/pr168_rp5c_*.py",
    "tests/pr168_rp5c/**",
)

_PR168_VS1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/run_pr168_vs1_trading_intelligence_slice.py",
        "tools/validate_pr168_vs1_trading_intelligence_slice.py",
        "tools/pr168_rp5c_config.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)

_PR168_VS1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_vs1/*.jsonl",
    "docs/master_plan/generated/pr168_vs1/*.manifest.json",
    "docs/master_plan/generated/pr168_vs1/*.report.json",
    "src/qtt/stage1_prediction_markets/pr168_vs1_trading_intelligence/**",
    "tools/pr168_vs1_*.py",
    "tools/*pr168_vs1*.py",
    "tests/pr168_vs1/**",
)

_PR168_RP5D_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp5d_replay_paper_executability_tiers.py",
        "tools/validate_pr168_rp5d_replay_paper_executability_tiers.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)

_PR168_RP5D_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_rp5d/*.jsonl",
    "docs/master_plan/generated/pr168_rp5d/*.manifest.json",
    "docs/master_plan/generated/pr168_rp5d/*.report.json",
    "docs/master_plan/generated/pr168_rp5d/*.json",
    "src/qtt/stage1_prediction_markets/pr168_rp5d_executability/**",
    "tools/*pr168_rp5d*.py",
    "tests/pr168_rp5d/**",
)

_PR168_RP5E_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp5e_stack_gen.py",
        "tools/validate_pr168_rp5e_stack_gen.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_input_consumption.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_input_inventory.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_reading_receipts.jsonl",
    }
)

_PR168_RP5E_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_rp5e/*.jsonl",
    "docs/master_plan/generated/pr168_rp5e/*.manifest.json",
    "docs/master_plan/generated/pr168_rp5e/*.report.json",
    "docs/master_plan/generated/pr168_rp5e/*.json",
    "src/qtt/stage1_prediction_markets/pr168_rp5e_stack_generator/**",
    "tools/*pr168_rp5e*.py",
    "tests/pr168_rp5e/**",
)

_PR168_RP5D_R1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp5d_r1_exec_now_unlock.py",
        "tools/validate_pr168_rp5d_r1_exec_now_unlock.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_validation_scope_registry.py",
        "src/qtt/stage1_prediction_markets/pr168_rp5d_executability/validator.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)

_PR168_RP5D_R1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_rp5d_r1/*.jsonl",
    "docs/master_plan/generated/pr168_rp5d_r1/*.manifest.json",
    "docs/master_plan/generated/pr168_rp5d_r1/*.report.json",
    "docs/master_plan/generated/pr168_rp5d_r1/*.json",
    "src/qtt/stage1_prediction_markets/pr168_rp5d_r1_unlock/**",
    "tools/*pr168_rp5d_r1*.py",
    "tests/pr168_rp5d_r1/**",
)

_PR168_RP5F_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/build_pr168_rp5f_dynamic_targets.py",
        "tools/validate_pr168_rp5f_dynamic_targets.py",
        "tools/pr168_rp5c_config.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/pr168_rp5c/test_rp5c_input_integrity.py",
    }
)

_PR168_RP5F_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_rp5f/*.jsonl",
    "docs/master_plan/generated/pr168_rp5f/*.manifest.json",
    "docs/master_plan/generated/pr168_rp5f/*.report.json",
    "docs/master_plan/generated/pr168_rp5f/*.json",
    "src/qtt/stage1_prediction_markets/pr168_rp5f_dynamic_targets/**",
    "tools/*pr168_rp5f*.py",
    "tests/pr168_rp5f/**",
)

_PR168_RP5G_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/build_pr168_rp5g_trade_plan_sim.py",
        "tools/validate_pr168_rp5g_trade_plan_sim.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_RP5G_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_rp5g/*.jsonl",
    "docs/master_plan/generated/pr168_rp5g/*.manifest.json",
    "docs/master_plan/generated/pr168_rp5g/*.report.json",
    "docs/master_plan/generated/pr168_rp5g/*.json",
    "docs/master_plan/generated/pr168_rp5g/*.md",
    "src/qtt/stage1_prediction_markets/pr168_rp5g_trade_plan_sim/**",
    "tools/*pr168_rp5g*.py",
    "tests/pr168_rp5g/**",
)

_PR168_RANK4_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/ranking/__init__.py",
        "tools/build_pr168_rank4_advisory_ranking.py",
        "tools/validate_pr168_rank4_advisory_ranking.py",
        "tools/pr168_rp5c_config.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_RANK4_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_rank4/*.jsonl",
    "docs/master_plan/generated/pr168_rank4/*.manifest.json",
    "docs/master_plan/generated/pr168_rank4/*.report.json",
    "docs/master_plan/generated/pr168_rank4/*.json",
    "docs/master_plan/generated/pr168_rank4/*.md",
    "src/qtt/ranking/pr168_rank4/**",
    "tools/*pr168_rank4*.py",
    "tests/pr168_rank4/**",
)

_PR168_QOPT1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/optimization/__init__.py",
        "tools/build_pr168_qopt1_batch_optimization.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_pr168_qopt1_batch_optimization.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_QOPT1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_qopt1/*.jsonl",
    "docs/master_plan/generated/pr168_qopt1/*.manifest.json",
    "docs/master_plan/generated/pr168_qopt1/*.report.json",
    "docs/master_plan/generated/pr168_qopt1/*.json",
    "docs/master_plan/generated/pr168_qopt1/*.md",
    "src/qtt/optimization/pr168_qopt1/**",
    "tools/*pr168_qopt1*.py",
    "tests/pr168_qopt1/**",
)

_PR168_VS2_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/paper/__init__.py",
        "tools/build_pr168_vs2_paper_intent_candidates.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_pr168_vs2_paper_intent_candidates.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_VS2_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_vs2/*.jsonl",
    "docs/master_plan/generated/pr168_vs2/*.manifest.json",
    "docs/master_plan/generated/pr168_vs2/*.report.json",
    "docs/master_plan/generated/pr168_vs2/*.json",
    "docs/master_plan/generated/pr168_vs2/*.md",
    "src/qtt/paper/pr168_vs2/**",
    "tools/*pr168_vs2*.py",
    "tests/pr168_vs2/**",
)

_PR168_MEM1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/memory/__init__.py",
        "tools/build_pr168_mem1_condition_scoped_memory.py",
        "tools/query_pr168_mem1_memory.py",
        "tools/validate_pr168_mem1_condition_scoped_memory.py",
        "tools/run_validation_gates.py",
        "tools/pr168_rp5c_config.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_MEM1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_mem1/*.jsonl",
    "docs/master_plan/generated/pr168_mem1/*.manifest.json",
    "docs/master_plan/generated/pr168_mem1/*.report.json",
    "docs/master_plan/generated/pr168_mem1/*.json",
    "docs/master_plan/generated/pr168_mem1/*.md",
    "src/qtt/memory/pr168_mem1/**",
    "tools/*pr168_mem1*.py",
    "tests/pr168_mem1/**",
)

_PR169_DASH1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/dashboard/__init__.py",
        "src/qtt/dashboard/owner_surface_models.py",
        "src/qtt/dashboard/owner_surface_registry.py",
        "src/qtt/dashboard/owner_surface_resolver.py",
        "src/qtt/dashboard/owner_action_registry.py",
        "src/qtt/dashboard/owner_dashboard_packet_builder.py",
        "src/qtt/dashboard/owner_dashboard_projection_builder.py",
        "src/qtt/dashboard/owner_dashboard_validator.py",
        "tools/build_pr168_rp5b_active_registry_safe_cleanup.py",
        "tools/build_pr169_dash1_owner_dashboard.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_pr169_dash1_owner_dashboard.py",
        "tools/validate_no_runtime_artifacts.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_source_fact_binding_connector_semantic_readiness_static.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/fail_closed/test_no_runtime_artifacts_strict.py",
        "tests/pr168_rp5c/test_rp5c_input_integrity.py",
        "tests/source_evidence/test_source_fact_binding_connector_semantic_readiness_static.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR169_DASH1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr169_dash1/**",
    "src/qtt/dashboard/**",
    "tools/*pr169_dash1*.py",
    "tests/pr169_dash1/**",
    "tests/pr169_dash1_ui1/**",
)

_PR169_READINESS1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/readiness/__init__.py",
        "src/qtt/readiness/pr169_readiness1_resolvers.py",
        "tools/build_pr169_readiness1.py",
        "tools/validate_pr169_readiness1.py",
        "tools/changed_area_validation_router.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/pr169_readiness1/test_pr169_readiness1.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR169_READINESS1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr169_readiness1/**",
    "src/qtt/readiness/**",
    "tools/*pr169_readiness1*.py",
    "tests/pr169_readiness1/**",
)

_PR169_PRETRADE1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/pretrade/__init__.py",
        "src/qtt/pretrade/pr169_pretrade1_resolvers.py",
        "tools/build_pr169_pretrade1.py",
        "tools/validate_pr169_pretrade1.py",
        "tools/changed_area_validation_router.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/pr169_pretrade1/test_pr169_pretrade1.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR169_PRETRADE1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr169_pretrade1/**",
    "src/qtt/pretrade/**",
    "tools/*pr169_pretrade1*.py",
    "tests/pr169_pretrade1/**",
)

_PR169_SVC1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/service/__init__.py",
        "src/qtt/service/pr169_svc1_resolvers.py",
        "src/qtt/stage1_prediction_markets/pr168_vs1_trading_intelligence/runner.py",
        "tools/build_pr169_svc1.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_pr169_svc1.py",
        "tools/changed_area_validation_router.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/pr169_svc1/test_pr169_svc1.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR169_SVC1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr169_svc1/**",
    "src/qtt/service/**",
    "tools/*pr169_svc1*.py",
    "tests/pr169_svc1/**",
)

_PR169_AGENT_ORCH1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/agents/__init__.py",
        "src/qtt/agents/pr169_agent_orch1_resolvers.py",
        "tools/build_pr169_agent_orch1.py",
        "tools/validate_pr169_agent_orch1.py",
        "tools/pr168_rp5c_config.py",
        "tools/changed_area_validation_router.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/pr169_agent_orch1/__init__.py",
        "tests/pr169_agent_orch1/conftest.py",
        "tests/pr169_agent_orch1/test_registry_projection_integrity.py",
        "tests/pr169_agent_orch1/test_dag_task_receipts.py",
        "tests/pr169_agent_orch1/test_no_authority.py",
        "tests/pr169_agent_orch1/test_qku_formula_mem_routes.py",
        "tests/pr169_agent_orch1/test_no_orphan_raw_scan.py",
        "tests/pr169_agent_orch1/test_resolvers.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR169_AGENT_ORCH1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr169_agent_orch1/**",
    "src/qtt/agents/**",
    "tools/*pr169_agent_orch1*.py",
    "tests/pr169_agent_orch1/**",
)

_PR169_QKU_FORMULA_EXP1_BASE_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tools/pr168_rp5c_config.py",
        "tests/pr168_rp5c/test_rp5c_input_integrity.py",
    }
)

_PR169_QKU_FORMULA_EXP1_ALLOWED_EXACT_PATHS = frozenset(
    {
        # Exact shared-owner currentization surface admitted after the repair
        # branch's fail-closed PR152 gate demonstrated each required path.
        "docs/master_plan/generated/PR168_MAP3_AgentDAG.report.json",
        "docs/master_plan/generated/PR168_MAP3_BindProof.report.json",
        "docs/master_plan/generated/PR168_MAP3_BindReject.report.json",
        "docs/master_plan/generated/PR168_MAP3_BindingRegistry.report.json",
        "docs/master_plan/generated/PR168_MAP3_CalibFormulas.report.json",
        "docs/master_plan/generated/PR168_MAP3_ComputeRoutes.report.json",
        "docs/master_plan/generated/PR168_MAP3_DataReqs.report.json",
        "docs/master_plan/generated/PR168_MAP3_Dedupe.report.json",
        "docs/master_plan/generated/PR168_MAP3_EdgeFit.report.json",
        "docs/master_plan/generated/PR168_MAP3_EdgeFormulas.report.json",
        "docs/master_plan/generated/PR168_MAP3_EveryValue.report.json",
        "docs/master_plan/generated/PR168_MAP3_ExtIntake.report.json",
        "docs/master_plan/generated/PR168_MAP3_ExtRejects.report.json",
        "docs/master_plan/generated/PR168_MAP3_ExtSources.report.json",
        "docs/master_plan/generated/PR168_MAP3_FamilyMatrix.report.json",
        "docs/master_plan/generated/PR168_MAP3_FinalSummary.report.json",
        "docs/master_plan/generated/PR168_MAP3_FormulaDependencyGraph.report.json",
        "docs/master_plan/generated/PR168_MAP3_FormulaDryRun.report.json",
        "docs/master_plan/generated/PR168_MAP3_FormulaFactory.report.json",
        "docs/master_plan/generated/PR168_MAP3_FormulaMaterialization.report.json",
        "docs/master_plan/generated/PR168_MAP3_FormulaOntology.report.json",
        "docs/master_plan/generated/PR168_MAP3_FormulaProv.report.json",
        "docs/master_plan/generated/PR168_MAP3_FormulaRecoveryFactory.report.json",
        "docs/master_plan/generated/PR168_MAP3_FormulaRepairPlaybook.report.json",
        "docs/master_plan/generated/PR168_MAP3_FormulaRetirementCandidates.report.json",
        "docs/master_plan/generated/PR168_MAP3_FormulaSelectionSurface.report.json",
        "docs/master_plan/generated/PR168_MAP3_HiddenBind.report.json",
        "docs/master_plan/generated/PR168_MAP3_IDCoverage.report.json",
        "docs/master_plan/generated/PR168_MAP3_IDGraph.report.json",
        "docs/master_plan/generated/PR168_MAP3_IDMine.report.json",
        "docs/master_plan/generated/PR168_MAP3_IDSupersede.report.json",
        "docs/master_plan/generated/PR168_MAP3_Input.report.json",
        "docs/master_plan/generated/PR168_MAP3_IntakePriority.report.json",
        "docs/master_plan/generated/PR168_MAP3_Invariants.report.json",
        "docs/master_plan/generated/PR168_MAP3_LifecycleDAG.report.json",
        "docs/master_plan/generated/PR168_MAP3_NegRepairFactory.report.json",
        "docs/master_plan/generated/PR168_MAP3_NegativeToCandidateRepair.report.json",
        "docs/master_plan/generated/PR168_MAP3_NewIDRules.report.json",
        "docs/master_plan/generated/PR168_MAP3_NewIDs.report.json",
        "docs/master_plan/generated/PR168_MAP3_OnlineScout.report.json",
        "docs/master_plan/generated/PR168_MAP3_Operator.report.json",
        "docs/master_plan/generated/PR168_MAP3_PluginContracts.report.json",
        "docs/master_plan/generated/PR168_MAP3_PortfolioFormulas.report.json",
        "docs/master_plan/generated/PR168_MAP3_PropertyTests.report.json",
        "docs/master_plan/generated/PR168_MAP3_QFallback.report.json",
        "docs/master_plan/generated/PR168_MAP3_QFormulaLift.report.json",
        "docs/master_plan/generated/PR168_MAP3_QMap.report.json",
        "docs/master_plan/generated/PR168_MAP3_QObjective.report.json",
        "docs/master_plan/generated/PR168_MAP3_QRepair.report.json",
        "docs/master_plan/generated/PR168_MAP3_Quality.report.json",
        "docs/master_plan/generated/PR168_MAP3_RP2FailureMining.report.json",
        "docs/master_plan/generated/PR168_MAP3_RegimeFormulas.report.json",
        "docs/master_plan/generated/PR168_MAP3_RetestSeeds.report.json",
        "docs/master_plan/generated/PR168_MAP3_RiskControls.report.json",
        "docs/master_plan/generated/PR168_MAP3_SelectFeatures.report.json",
        "docs/master_plan/generated/PR168_MAP3_SourceReview.report.json",
        "docs/master_plan/generated/PR168_MAP3_SourceTriangulation.report.json",
        "docs/master_plan/generated/PR168_MAP3_TCAFormulas.report.json",
        "docs/master_plan/generated/PR168_MAP3_ToDATA1B.report.json",
        "docs/master_plan/generated/PR168_MAP3_ToPR162EQ.report.json",
        "docs/master_plan/generated/PR168_MAP3_ToPR165B.report.json",
        "docs/master_plan/generated/PR168_MAP3_ToRANK2.report.json",
        "docs/master_plan/generated/PR168_MAP3_ToRP2.report.json",
        "docs/master_plan/generated/PR168_MAP3_UnitNorms.report.json",
        "docs/master_plan/generated/PR168_RP5C_AgentQKUAccessContract.report.json",
        "docs/master_plan/generated/PR168_RP5C_CentralSurfaceManifest.report.json",
        "docs/master_plan/generated/PR168_RP5C_DerivedAgentRouteResolutionLedger.report.json",
        "docs/master_plan/generated/PR168_RP5C_DormantFutureMarketQKULedger.report.json",
        "docs/master_plan/generated/PR168_RP5C_FileToDerivedRouteCrosswalk.report.json",
        "docs/master_plan/generated/PR168_RP5C_FinalSummary.report.json",
        "docs/master_plan/generated/PR168_RP5C_FormulaAssignmentLibrary.report.json",
        "docs/master_plan/generated/PR168_RP5C_FormulaOntology.report.json",
        "docs/master_plan/generated/PR168_RP5C_IdentityDeduplicationLedger.report.json",
        "docs/master_plan/generated/PR168_RP5C_IdentityProvenanceTier.report.json",
        "docs/master_plan/generated/PR168_RP5C_ImmutableFormulaLibrary.report.json",
        "docs/master_plan/generated/PR168_RP5C_ImmutableQKUFormulaLibrary.report.json",
        "docs/master_plan/generated/PR168_RP5C_ImmutableQKULibrary.report.json",
        "docs/master_plan/generated/PR168_RP5C_Input.report.json",
        "docs/master_plan/generated/PR168_RP5C_MachineConsumableLibraryAccess.report.json",
        "docs/master_plan/generated/PR168_RP5C_MarketScopeClassificationQualityAudit.report.json",
        "docs/master_plan/generated/PR168_RP5C_MarketScopeFamilyRegistry.report.json",
        "docs/master_plan/generated/PR168_RP5C_NoGlobalBanProof.report.json",
        "docs/master_plan/generated/PR168_RP5C_NoOrphanIdentityProof.report.json",
        "docs/master_plan/generated/PR168_RP5C_NoOrphanSourceArtifactProof.report.json",
        "docs/master_plan/generated/PR168_RP5C_OntologyRoleRegistry.report.json",
        "docs/master_plan/generated/PR168_RP5C_PlatformApplicabilityRegistry.report.json",
        "docs/master_plan/generated/PR168_RP5C_Preflight.report.json",
        "docs/master_plan/generated/PR168_RP5C_QKUFormulaFamilyRegistry.report.json",
        "docs/master_plan/generated/PR168_RP5C_QKUFormulaIdentityLineage.report.json",
        "docs/master_plan/generated/PR168_RP5C_SourceArtifactConsumptionLedger.report.json",
        "docs/master_plan/generated/PR168_RP5C_Stage1AgentComputationUniverseSeed.report.json",
        "docs/master_plan/generated/PR168_RP5C_Stage1PredictionMarketQKUActivationView.report.json",
        "docs/master_plan/generated/PR168_RP5C_StageAgentUniverseResolutionProof.report.json",
        "docs/master_plan/generated/PR168_RP5C_ToRP5DExecutabilityHandoff.report.json",
        "docs/master_plan/generated/PR168_RP5C_ToVS1TradingIntelligenceHandoff.report.json",
        "docs/master_plan/generated/map3/formula_dependency_rows.jsonl",
        "docs/master_plan/generated/map3/formula_dependency_rows.jsonl.manifest.json",
        "docs/master_plan/generated/pr169_agent_orch1/formula_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/no_orphan.report.json",
        "docs/master_plan/generated/pr169_pretrade1/pretrade_manifest.json",
        "docs/master_plan/generated/pr169_pretrade1/pretrade_qku_formula_compute_map.generated.jsonl",
        "docs/master_plan/generated/pr169_readiness1/qku_formula_agent_compute_map.generated.jsonl",
        "docs/master_plan/generated/pr169_readiness1/readiness_manifest.json",
        "docs/master_plan/generated/pr169_svc1/qku_formula_compute_route_views.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/service_manifest.json",
        "docs/master_plan/generated/rp5c/agent_computation_universe_view.jsonl",
        "docs/master_plan/generated/rp5c/agent_qku_access_policy_registry.jsonl",
        "docs/master_plan/generated/rp5c/derived_agent_route_resolution_ledger.jsonl",
        "docs/master_plan/generated/rp5c/derived_agent_route_resolution_ledger.manifest.json",
        "docs/master_plan/generated/rp5c/dormant_future_market_qku_ledger.jsonl",
        "docs/master_plan/generated/rp5c/dormant_future_market_qku_ledger.manifest.json",
        "docs/master_plan/generated/rp5c/file_to_derived_route_crosswalk.jsonl",
        "docs/master_plan/generated/rp5c/formula_assignment_library.jsonl",
        "docs/master_plan/generated/rp5c/formula_assignment_library.manifest.json",
        "docs/master_plan/generated/rp5c/formula_ontology.jsonl",
        "docs/master_plan/generated/rp5c/formula_ontology.manifest.json",
        "docs/master_plan/generated/rp5c/identity_deduplication_ledger.jsonl",
        "docs/master_plan/generated/rp5c/identity_deduplication_ledger.manifest.json",
        "docs/master_plan/generated/rp5c/identity_provenance_tier.jsonl",
        "docs/master_plan/generated/rp5c/identity_provenance_tier.manifest.json",
        "docs/master_plan/generated/rp5c/identity_quality_gap_queue.jsonl",
        "docs/master_plan/generated/rp5c/identity_quality_gap_queue.manifest.json",
        "docs/master_plan/generated/rp5c/immutable_formula_library.jsonl",
        "docs/master_plan/generated/rp5c/immutable_formula_library.manifest.json",
        "docs/master_plan/generated/rp5c/immutable_qku_formula_library.jsonl",
        "docs/master_plan/generated/rp5c/immutable_qku_formula_library.manifest.json",
        "docs/master_plan/generated/rp5c/immutable_qku_library.jsonl",
        "docs/master_plan/generated/rp5c/immutable_qku_library.manifest.json",
        "docs/master_plan/generated/rp5c/input_artifact_to_identity_coverage.jsonl",
        "docs/master_plan/generated/rp5c/library_query_receipts.jsonl",
        "docs/master_plan/generated/rp5c/market_family_reclassification_ledger.jsonl",
        "docs/master_plan/generated/rp5c/market_scope_family_registry.jsonl",
        "docs/master_plan/generated/rp5c/market_specific_qku_pool_registry.jsonl",
        "docs/master_plan/generated/rp5c/no_global_ban_rows.jsonl",
        "docs/master_plan/generated/rp5c/no_global_ban_rows.manifest.json",
        "docs/master_plan/generated/rp5c/no_orphan_identity_rows.jsonl",
        "docs/master_plan/generated/rp5c/no_orphan_identity_rows.manifest.json",
        "docs/master_plan/generated/rp5c/no_orphan_source_artifact_rows.jsonl",
        "docs/master_plan/generated/rp5c/ontology_role_registry.jsonl",
        "docs/master_plan/generated/rp5c/platform_applicability_registry.jsonl",
        "docs/master_plan/generated/rp5c/qku_formula_family_registry.jsonl",
        "docs/master_plan/generated/rp5c/qku_formula_family_registry.manifest.json",
        "docs/master_plan/generated/rp5c/qku_formula_identity_lineage.jsonl",
        "docs/master_plan/generated/rp5c/qku_formula_identity_lineage.manifest.json",
        "docs/master_plan/generated/rp5c/qku_market_applicability_matrix.jsonl",
        "docs/master_plan/generated/rp5c/qku_market_applicability_matrix.manifest.json",
        "docs/master_plan/generated/rp5c/rp5d_executability_handoff.jsonl",
        "docs/master_plan/generated/rp5c/rp5d_executability_handoff.manifest.json",
        "docs/master_plan/generated/rp5c/shared_cross_market_support_pool.jsonl",
        "docs/master_plan/generated/rp5c/source_artifact_consumption_ledger.jsonl",
        "docs/master_plan/generated/rp5c/stage1_agent_computation_universe_seed.jsonl",
        "docs/master_plan/generated/rp5c/stage1_agent_computation_universe_seed.manifest.json",
        "docs/master_plan/generated/rp5c/stage1_prediction_market_qku_activation_view.jsonl",
        "docs/master_plan/generated/rp5c/stage1_prediction_market_qku_activation_view.manifest.json",
        "docs/master_plan/generated/rp5c/stage_agent_qku_universe_resolver.jsonl",
        "docs/master_plan/generated/rp5c/stage_computation_universe_view.jsonl",
        "docs/master_plan/generated/rp5c/vs1_trading_intelligence_handoff.jsonl",
        "docs/master_plan/generated/rp5a/agent_touchpoint_rows.jsonl",
        "docs/master_plan/generated/rp5a/blast_radius_rows.jsonl",
        "docs/master_plan/generated/rp5a/consumer_graph_rows.jsonl",
        "docs/master_plan/generated/rp5a/identity_custody_rows.jsonl",
        "docs/master_plan/generated/rp5a/legacy_file_semantic_rows.jsonl",
        "docs/master_plan/generated/rp5a/qku_formula_identity_dependency_rows.jsonl",
        "docs/master_plan/generated/rp5a/row_field_semantic_hit_rows.jsonl",
        "docs/master_plan/generated/rp5a/validation_dependency_rows.jsonl",
        "docs/master_plan/generated/rp5a/validation_time_risk_rows.jsonl",
        "docs/master_plan/generated/pr168_vs1/context_formula_selection_receipts.jsonl",
        "docs/master_plan/generated/pr168_vs1/expected_cash_pnl_receipts.jsonl",
        "docs/master_plan/generated/pr168_vs1/no_orphan_qku_formula_proof.jsonl",
        "docs/master_plan/generated/pr168_vs1/no_trade_comparator_receipts.jsonl",
        "docs/master_plan/generated/pr168_vs1/portfolio_diversification_receipts.jsonl",
        "docs/master_plan/generated/pr168_vs1/quantum_structural_readiness_receipts.jsonl",
        "docs/master_plan/generated/pr168_vs1/selected_computable_qku_formula_bindings.jsonl",
        "docs/master_plan/generated/pr168_vs1/stage_agent_universe_query_receipts.jsonl",
        "docs/master_plan/generated/pr168_vs1/temporary_stack_candidate_receipts.jsonl",
        "docs/master_plan/generated/pr168_vs1/trade_plan_candidates.jsonl",
        "docs/master_plan/generated/pr168_vs1/vs1_reading_receipts.jsonl",
        "docs/master_plan/generated/pr168_vs1/vs1_run_receipt.report.json",
        # Exact RP5D/R1/RP5E/RP5F owner projections currentized from the
        # expanded RP5C identity and assignment graph.
        "docs/master_plan/generated/pr168_rp5d/rp5d_agent_exec_queries.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_agent_exec_resolver.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_agent_route_queue.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_alpha_queue.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_alpha_queue.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_alpha_readiness.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_alpha_readiness.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_capacity_queue.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_capacity_queue.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_capacity_readiness.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_capacity_readiness.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_champion_queue.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_champion_queue.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_champion_readiness.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_champion_readiness.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_classical_fb_queue.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_classical_fb_queue.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_comp_materialization.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_comp_materialization.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_computable_universe.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_computable_universe.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_contract_bundles.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_contract_bundles.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_crosswalk_discovery_receipts.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_exec_tiers.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_exec_tiers.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_fill_liquidity_queue.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_fill_liquidity_queue.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_formula_pnl_queue.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_formula_pnl_queue.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_hot_path_queue.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_hot_path_queue.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_hot_path_readiness.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_hot_path_readiness.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_input_consumption.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_input_consumption.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_input_inventory.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_input_inventory.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_input_queue.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_input_queue.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_latency_queue.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_latency_queue.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_marginal_utility_readiness.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_marginal_utility_readiness.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_market_data_queue.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_market_data_queue.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_no_mutation_proof.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_no_mutation_proof.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_no_orphan_qku_formula.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_no_orphan_qku_formula.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_no_trade_queue.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_no_trade_queue.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_no_trade_readiness.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_no_trade_readiness.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_optimizer_readiness.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_optimizer_readiness.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_overfit_fdr_queue.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_overfit_fdr_queue.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_overfit_fdr_readiness.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_overfit_fdr_readiness.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_portfolio_queue.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_portfolio_queue.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_portfolio_readiness.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_portfolio_readiness.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_qobj_constraint_ledger.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_qobj_constraint_ledger.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_quantum_compat.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_quantum_compat.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_quantum_map_queue.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_quantum_map_queue.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_rank_queue.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_rank_queue.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_rank_readiness.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_rank_readiness.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_reading_receipts.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_reading_receipts.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_regime_memory_queue.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_regime_memory_queue.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_regime_memory_readiness.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_regime_memory_readiness.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_rp5c_vs1_crosswalk.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_rp5c_vs1_crosswalk.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_run_receipt.report.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_scenario_queue.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_scenario_queue.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_stage1_coverage.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_stage1_coverage.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_stage_agent_exec_view.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_tca_queue.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_tca_queue.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_tca_readiness.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_tca_readiness.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_trade_var_readiness.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_trade_var_readiness.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_unit_queue.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_unit_queue.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_universal_coverage.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_universal_coverage.manifest.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_value_lineage.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/contract_patch.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/contract_patch.manifest.json",
        "docs/master_plan/generated/pr168_rp5d_r1/gap_dedupe.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/gap_family.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/gap_family.manifest.json",
        "docs/master_plan/generated/pr168_rp5d_r1/in_cons.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/marg_unlock.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/promo_diverse.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/read_rec.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/run_receipt.report.json",
        "docs/master_plan/generated/pr168_rp5d_r1/unlock_plan.jsonl",
        "docs/master_plan/generated/pr168_rp5e/alpha_hints.jsonl",
        "docs/master_plan/generated/pr168_rp5e/cand_fam.jsonl",
        "docs/master_plan/generated/pr168_rp5e/capacity.jsonl",
        "docs/master_plan/generated/pr168_rp5e/champ_prev.jsonl",
        "docs/master_plan/generated/pr168_rp5e/classic.jsonl",
        "docs/master_plan/generated/pr168_rp5e/ctx_pools.jsonl",
        "docs/master_plan/generated/pr168_rp5e/ctx_univ.jsonl",
        "docs/master_plan/generated/pr168_rp5e/diverse.jsonl",
        "docs/master_plan/generated/pr168_rp5e/edge_feats.jsonl",
        "docs/master_plan/generated/pr168_rp5e/exec_prev.jsonl",
        "docs/master_plan/generated/pr168_rp5e/fdr_ctrl.jsonl",
        "docs/master_plan/generated/pr168_rp5e/features.jsonl",
        "docs/master_plan/generated/pr168_rp5e/gap_rank.jsonl",
        "docs/master_plan/generated/pr168_rp5e/in_cons.jsonl",
        "docs/master_plan/generated/pr168_rp5e/marg_util.jsonl",
        "docs/master_plan/generated/pr168_rp5e/notrade_hints.jsonl",
        "docs/master_plan/generated/pr168_rp5e/port_div.jsonl",
        "docs/master_plan/generated/pr168_rp5e/prescreen.jsonl",
        "docs/master_plan/generated/pr168_rp5e/q_coeffs.jsonl",
        "docs/master_plan/generated/pr168_rp5e/q_interp.jsonl",
        "docs/master_plan/generated/pr168_rp5e/q_obj.jsonl",
        "docs/master_plan/generated/pr168_rp5e/q_solver.jsonl",
        "docs/master_plan/generated/pr168_rp5e/q_tags.jsonl",
        "docs/master_plan/generated/pr168_rp5e/qku_guard.jsonl",
        "docs/master_plan/generated/pr168_rp5e/queue_dedupe.jsonl",
        "docs/master_plan/generated/pr168_rp5e/read_rec.jsonl",
        "docs/master_plan/generated/pr168_rp5e/regime_mem.jsonl",
        "docs/master_plan/generated/pr168_rp5e/run_receipt.report.json",
        "docs/master_plan/generated/pr168_rp5e/tca_ready.jsonl",
        "docs/master_plan/generated/pr168_rp5e/tmp_previews.jsonl",
        "docs/master_plan/generated/pr168_rp5e/topk.jsonl",
        "docs/master_plan/generated/pr168_rp5e/unlock_pri.jsonl",
        "docs/master_plan/generated/pr168_rp5f/adverse_select.jsonl",
        "docs/master_plan/generated/pr168_rp5f/context_similarity_keys.jsonl",
        "docs/master_plan/generated/pr168_rp5f/ctx_filter.jsonl",
        "docs/master_plan/generated/pr168_rp5f/edge_capture_map.jsonl",
        "docs/master_plan/generated/pr168_rp5f/event_lifecycle.jsonl",
        "docs/master_plan/generated/pr168_rp5f/in_cons.jsonl",
        "docs/master_plan/generated/pr168_rp5f/learning_hooks.jsonl",
        "docs/master_plan/generated/pr168_rp5f/library_query.jsonl",
        "docs/master_plan/generated/pr168_rp5f/liquidity_decay.jsonl",
        "docs/master_plan/generated/pr168_rp5f/port_cap.jsonl",
        "docs/master_plan/generated/pr168_rp5f/qku_access.jsonl",
        "docs/master_plan/generated/pr168_rp5f/qku_compute_route.jsonl",
        "docs/master_plan/generated/pr168_rp5f/qku_target_use.jsonl",
        "docs/master_plan/generated/pr168_rp5f/queue_fill_inputs.jsonl",
        "docs/master_plan/generated/pr168_rp5f/read_rec.jsonl",
        "docs/master_plan/generated/pr168_rp5f/regime_keys.jsonl",
        "docs/master_plan/generated/pr168_rp5f/regime_sim_hints.jsonl",
        "docs/master_plan/generated/pr168_rp5f/retest_policy_hints.jsonl",
        "docs/master_plan/generated/pr168_rp5f/run_receipt.report.json",
        "docs/master_plan/generated/pr168_rp5f/snap_ctx.jsonl",
        "docs/master_plan/generated/pr168_rp5f/target_failure_taxonomy.jsonl",
        "docs/master_plan/generated/pr168_rp5f/target_family.jsonl",
        "docs/master_plan/generated/pr168_rp5f/target_utility.jsonl",
        "docs/master_plan/generated/pr168_rp5f/targets.jsonl",
        "docs/master_plan/generated/pr168_rp5f/trade_seed.jsonl",
        "docs/master_plan/generated/pr168_rp5f/venue_state.jsonl",
        "src/qtt/stage1_prediction_markets/pr162d_r2a_real_formulations/pr169_operator_registry.py",
        # Exact owner registry/manifests/reports changed by canonical SVC and
        # AGENT-ORCH derivation of the PR169 formula rows.
        "docs/master_plan/generated/pr169_agent_orch1/acceptance.report.json",
        "docs/master_plan/generated/pr169_agent_orch1/access_proof.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/agent_ops.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/allow_prep.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/audit_trail.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/calibration_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/capability_routes.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/capacity_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/champion_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/chat_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/clean_room.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/decision_receipts.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/directives.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/dispute_receipts.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/downstream.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/escalation_receipts.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/fallback_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/fdr_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/formula_intake.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/graph_quality.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/graph_routes.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/graph_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/handoff_receipts.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/handoffs.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/hotpath_prep.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/latency_tiers.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/learning_routes.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/library_receipts.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/live_prep.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/mem1_bindings.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/mem_prior_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/metric_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/mode_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/no_direct_submit.report.json",
        "docs/master_plan/generated/pr169_agent_orch1/no_fake_receipts.report.json",
        "docs/master_plan/generated/pr169_agent_orch1/no_full_library.report.json",
        "docs/master_plan/generated/pr169_agent_orch1/no_live_exec.report.json",
        "docs/master_plan/generated/pr169_agent_orch1/no_llm_runtime.report.json",
        "docs/master_plan/generated/pr169_agent_orch1/no_paper_exec.report.json",
        "docs/master_plan/generated/pr169_agent_orch1/no_placeholders.report.json",
        "docs/master_plan/generated/pr169_agent_orch1/no_pr_collapse.report.json",
        "docs/master_plan/generated/pr169_agent_orch1/no_private_cash.report.json",
        "docs/master_plan/generated/pr169_agent_orch1/no_qbackend.report.json",
        "docs/master_plan/generated/pr169_agent_orch1/no_qtt_sha.report.json",
        "docs/master_plan/generated/pr169_agent_orch1/no_raw_scan.report.json",
        "docs/master_plan/generated/pr169_agent_orch1/no_scatter.report.json",
        "docs/master_plan/generated/pr169_agent_orch1/no_source_truth.report.json",
        "docs/master_plan/generated/pr169_agent_orch1/notrade_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/order_policy_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/owned_scope.report.json",
        "docs/master_plan/generated/pr169_agent_orch1/owner_cmd_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/paper_prep.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/plugin_prep.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/portfolio_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/pretrade_bindings.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/pretrade_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/qku_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/qmap_prep.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/quality.report.json",
        "docs/master_plan/generated/pr169_agent_orch1/quantum_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/rank_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/readiness_bindings.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/reality_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/registry.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/retest_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/scenario_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/shadow_prep.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/source_refresh_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/stack_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/svc1_bindings.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/task_env.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/task_queue.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/task_receipts.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/task_registry.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/tca_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/team_queue.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/tournament_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/tradeplan_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/utility_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/value_routes.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/var_tune_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/venue_side_tasks.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/workflows.jsonl",
        "docs/master_plan/generated/pr169_svc1/action_confirmation_policy.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/action_denied_reasons.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/action_eligibility.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/action_request_dedupe_policy.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/action_risk_class_policy.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/action_route_to_agent_responsibility.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/audit_receipt_stream.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/command_action_matrix_bindings.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/event_stream_contracts.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/event_stream_cursor_policy.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/no_orphan.report.json",
        "docs/master_plan/generated/pr169_svc1/owner_action_receipts.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/owner_action_requests.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/owner_chart_manifest.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/owner_chat_route_previews.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/owner_layout_profile_routes.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/owner_next_step_routes.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/owner_plain_english_intent_routes.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/read_model_snapshot_index.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/read_model_snapshots.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/read_model_store_contracts.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/service_registry.jsonl",
        # Additional exact stable outputs emitted by the downstream owners'
        # own repeat-run determinism checks.
        "docs/master_plan/generated/pr168_rp5d_r1/calc_smoke.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/capacity_ready.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/cash_settle.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/champ_carry.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/classic_exec.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/contract_matrix.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/edge_profit_map.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/exec_adj_delta.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/exec_now_proof.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/fdr_carry.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/fee_ready.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/fill_ready.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/fixture_bind.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/input_bind.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/lat_ready.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/marg_carry.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/nonpromote.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/pnl_map.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/port_cap_carry.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/promote.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/promote_audit.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/proof_tier.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/q_interp_carry.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/q_solver_carry.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/q_struct_carry.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/regime_carry.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/rp5e_unlock_in.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/slip_ready.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/source_req.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/spread_ready.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/tca_comp.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/tca_delta.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/tier_overlay.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/unit_adapt.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/unlock_select.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/unlock_tiers.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/unlock_util.jsonl",
        "docs/master_plan/generated/pr168_rp5f/exec_now_delta_hint.jsonl",
        "tests/pr168_rp5c/test_rp5c_machine_consumable_access.py",
        "tests/pr168_rp5e/test_reading_inputs.py",
        "tools/build_pr168_map3.py",
        "tools/build_pr169_agent_orch1.py",
        "tools/build_pr169_pretrade1.py",
        "tools/build_pr169_readiness1.py",
        "tools/build_pr169_svc1.py",
        "tools/pr168_rp5c_validator.py",
        "tools/pr169_formula_owner_rows.py",
        "tools/validate_pr169_agent_orch1.py",
        "tools/validate_pr169_pretrade1.py",
        "tools/validate_pr169_readiness1.py",
        "tools/validate_pr169_svc1.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tools/pr168_rp5c_config.py",
        "tests/pr168_rp5c/test_rp5c_input_integrity.py",
    }
)

_PR169_QKU_FORMULA_EXP1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr169_qku_formula_exp1/**",
    "src/qtt/stage1_prediction_markets/pr169_qku_formula_exp1/**",
    "tools/*pr169_qku_formula_exp1*.py",
    "tests/pr169_qku_formula_exp1/**",
)

_PR169_VAL1_ALLOWED_EXACT_PATHS = frozenset(
    {
        ".github/workflows/qtt_validation.yml",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/pr169_val1/acceptance.report.json",
        "docs/master_plan/generated/pr169_val1/manifest.json",
        "docs/master_plan/generated/pr169_val1/parity.report.json",
        "docs/master_plan/generated/pr169_val1/readability.report.json",
        "docs/master_plan/generated/pr169_val1/shards.report.json",
        "docs/master_plan/generated/pr169_val1/timing.report.json",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_qtt_validation_workflow_matrix.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_validation_readability_guard.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_shard_partition.py",
        "tests/tools/test_validation_timing_artifacts.py",
        "tools/build_pr169_val1.py",
        "tools/pr168_rp5c_config.py",
        "tools/run_validation_gates.py",
        "tools/validate_idempotence_runtime_containment.py",
        "tools/validate_pr169_val1.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
    }
)

_PR169_VAL1_ALLOWED_PATTERNS: tuple[str, ...] = ()

_FORBIDDEN_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "AtomicRows.bundle.sha256",
        "docs/master_plan/generated/AtomicRows.bundle.sha256",
    }
)

_FORBIDDEN_PREFIXES = (
    ".tmp/",
    "src/qtt/live_connectors/",
    "src/qtt/connectors/live/",
    "src/qtt/private_state/",
    "src/qtt/live_order",
    "private-state/",
    "private_state/",
    "cash/",
    "secrets/",
)

_FORBIDDEN_NAME_TOKENS = (
    "live_order",
    "private_state",
    "private-state",
    "cash_account",
    "account_cash",
    "secret",
    "atomicrows.bundle.sha256",
    "qtt_sha",
    "qtt-sha",
    "qtt_freeze",
    "qtt-freeze",
    "qtt_checksum",
    "qtt-checksum",
    "qtt_global_digest",
    "qtt-global-digest",
)

_FORBIDDEN_TOKEN_EXACT_PROOF_REPORT_EXCEPTIONS = frozenset(
    {
        "docs/master_plan/generated/pr169_agent_orch1/no_qtt_sha.report.json",
    }
)


def normalize_changed_path(path: str) -> str:
    """Normalize a changed path into repo-relative POSIX form."""
    normalized = str(path).strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def is_validation_context_branch(branch: str) -> bool:
    return str(branch).strip() in _VALIDATION_CONTEXT_BRANCHES


def is_pr_scoped_changed_path_allowed(branch: str, path: str) -> bool:
    return bool(explain_pr_scope_decision(branch, path)["allowed"])


def _pr168_rp_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rank_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RANK_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RANK",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RANK_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RANK",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_data1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_DATA1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-DATA1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_DATA1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-DATA1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_data1a_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_DATA1A_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-DATA1A",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_DATA1A_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-DATA1A",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_gfp2r_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_GFP2R_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-GFP2R",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_GFP2R_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-GFP2R",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp2_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP2_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP2",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP2_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP2",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_map3_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_MAP3_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-MAP3",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_MAP3_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-MAP3",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp3_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP3_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP3",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP3_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP3",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rank3_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RANK3_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RANK3",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RANK3_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RANK3",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5a_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5A_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5A",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5A_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5A",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5b_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5B_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5B",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5B_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5B",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5c_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5C_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5C",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5C_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5C",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_vs1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_VS1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-VS1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_VS1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-VS1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5d_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5D_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5D",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5D_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5D",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5e_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5E_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5E",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5E_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5E",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5d_r1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5D_R1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5D-R1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5D_R1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5D-R1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5f_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5F_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5F",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5F_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5F",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5g_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5G_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5G",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5G_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5G",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rank4_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RANK4_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RANK4",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RANK4_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RANK4",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_qopt1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_QOPT1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-QOPT1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_QOPT1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-QOPT1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_vs2_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_VS2_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-VS2",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_VS2_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-VS2",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_mem1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_MEM1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-MEM1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_MEM1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-MEM1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr169_readiness1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR169_READINESS1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-READINESS1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR169_READINESS1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR169-READINESS1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr169_pretrade1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR169_PRETRADE1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-PRETRADE1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR169_PRETRADE1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR169-PRETRADE1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr169_svc1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR169_SVC1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-SVC1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR169_SVC1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR169-SVC1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr169_agent_orch1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR169_AGENT_ORCH1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-AGENT-ORCH1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR169_AGENT_ORCH1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR169-AGENT-ORCH1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr169_qku_formula_exp1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR169_QKU_FORMULA_EXP1_ALLOWED_EXACT_PATHS:
        if (
            branch_name == PR169_QKU_FORMULA_EXP1_BRANCH
            and normalized not in _PR169_QKU_FORMULA_EXP1_BASE_EXACT_PATHS
        ):
            return None
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-QKU-FORMULA-EXP1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path_after_fail_closed_scope_proof",
        }
    for pattern in _PR169_QKU_FORMULA_EXP1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR169-QKU-FORMULA-EXP1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_semantic_owned_prefix_after_fail_closed_scope_proof",
            }
    return None


def _pr169_val1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR169_VAL1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-VAL1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR169_VAL1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR169-VAL1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr169_dash1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR169_DASH1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-DASH1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR169_DASH1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR169-DASH1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def explain_pr_scope_decision(branch: str, path: str) -> dict[str, object]:
    normalized = normalize_changed_path(path)
    branch_name = str(branch).strip()
    forbidden_reason = _forbidden_reason(normalized)
    if forbidden_reason:
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": None,
            "matched_rule": forbidden_reason,
            "reason": "forbidden_path",
        }
    if branch_name not in _PR168_BRANCHES:
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": None,
            "matched_rule": "branch_not_registered_for_pr_scope",
            "reason": "branch_not_registered",
        }
    if branch_name == PR168_RP_BRANCH:
        rp_decision = _pr168_rp_scope_decision(branch_name, normalized)
        if rp_decision:
            return rp_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP",
            "matched_rule": "no_pr168_rp_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RANK_BRANCH:
        rank_decision = _pr168_rank_scope_decision(branch_name, normalized)
        if rank_decision:
            return rank_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RANK",
            "matched_rule": "no_pr168_rank_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_DATA1_BRANCH:
        data1_decision = _pr168_data1_scope_decision(branch_name, normalized)
        if data1_decision:
            return data1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-DATA1",
            "matched_rule": "no_pr168_data1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_DATA1A_BRANCH:
        data1a_decision = _pr168_data1a_scope_decision(branch_name, normalized)
        if data1a_decision:
            return data1a_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-DATA1A",
            "matched_rule": "no_pr168_data1a_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_GFP2R_BRANCH:
        gfp2r_decision = _pr168_gfp2r_scope_decision(branch_name, normalized)
        if gfp2r_decision:
            return gfp2r_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-GFP2R",
            "matched_rule": "no_pr168_gfp2r_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP2_BRANCH:
        rp2_decision = _pr168_rp2_scope_decision(branch_name, normalized)
        if rp2_decision:
            return rp2_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP2",
            "matched_rule": "no_pr168_rp2_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_MAP3_BRANCH:
        map3_decision = _pr168_map3_scope_decision(branch_name, normalized)
        if map3_decision:
            return map3_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-MAP3",
            "matched_rule": "no_pr168_map3_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP3_BRANCH:
        rp3_decision = _pr168_rp3_scope_decision(branch_name, normalized)
        if rp3_decision:
            return rp3_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP3",
            "matched_rule": "no_pr168_rp3_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RANK3_BRANCH:
        rank3_decision = _pr168_rank3_scope_decision(branch_name, normalized)
        if rank3_decision:
            return rank3_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RANK3",
            "matched_rule": "no_pr168_rank3_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP5A_BRANCH:
        rp5a_decision = _pr168_rp5a_scope_decision(branch_name, normalized)
        if rp5a_decision:
            return rp5a_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5A",
            "matched_rule": "no_pr168_rp5a_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP5B_BRANCH:
        rp5b_decision = _pr168_rp5b_scope_decision(branch_name, normalized)
        if rp5b_decision:
            return rp5b_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5B",
            "matched_rule": "no_pr168_rp5b_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name in {PR168_RP5C_BRANCH, PR168_RP5C_POST_MERGE_REPAIR_BRANCH}:
        rp5c_decision = _pr168_rp5c_scope_decision(branch_name, normalized)
        if rp5c_decision:
            return rp5c_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5C",
            "matched_rule": "no_pr168_rp5c_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_VS1_BRANCH:
        vs1_decision = _pr168_vs1_scope_decision(branch_name, normalized)
        if vs1_decision:
            return vs1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-VS1",
            "matched_rule": "no_pr168_vs1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP5D_BRANCH:
        rp5d_decision = _pr168_rp5d_scope_decision(branch_name, normalized)
        if rp5d_decision:
            return rp5d_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5D",
            "matched_rule": "no_pr168_rp5d_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP5E_BRANCH:
        rp5e_decision = _pr168_rp5e_scope_decision(branch_name, normalized)
        if rp5e_decision:
            return rp5e_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5E",
            "matched_rule": "no_pr168_rp5e_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP5D_R1_BRANCH:
        rp5d_r1_decision = _pr168_rp5d_r1_scope_decision(branch_name, normalized)
        if rp5d_r1_decision:
            return rp5d_r1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5D-R1",
            "matched_rule": "no_pr168_rp5d_r1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP5F_BRANCH:
        rp5f_decision = _pr168_rp5f_scope_decision(branch_name, normalized)
        if rp5f_decision:
            return rp5f_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5F",
            "matched_rule": "no_pr168_rp5f_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP5G_BRANCH:
        rp5g_decision = _pr168_rp5g_scope_decision(branch_name, normalized)
        if rp5g_decision:
            return rp5g_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5G",
            "matched_rule": "no_pr168_rp5g_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RANK4_BRANCH:
        rank4_decision = _pr168_rank4_scope_decision(branch_name, normalized)
        if rank4_decision:
            return rank4_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RANK4",
            "matched_rule": "no_pr168_rank4_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_QOPT1_BRANCH:
        qopt1_decision = _pr168_qopt1_scope_decision(branch_name, normalized)
        if qopt1_decision:
            return qopt1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-QOPT1",
            "matched_rule": "no_pr168_qopt1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_VS2_BRANCH:
        vs2_decision = _pr168_vs2_scope_decision(branch_name, normalized)
        if vs2_decision:
            return vs2_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-VS2",
            "matched_rule": "no_pr168_vs2_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_MEM1_BRANCH:
        mem1_decision = _pr168_mem1_scope_decision(branch_name, normalized)
        if mem1_decision:
            return mem1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-MEM1",
            "matched_rule": "no_pr168_mem1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR169_READINESS1_BRANCH:
        readiness1_decision = _pr169_readiness1_scope_decision(branch_name, normalized)
        if readiness1_decision:
            return readiness1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-READINESS1",
            "matched_rule": "no_pr169_readiness1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR169_PRETRADE1_BRANCH:
        pretrade1_decision = _pr169_pretrade1_scope_decision(branch_name, normalized)
        if pretrade1_decision:
            return pretrade1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-PRETRADE1",
            "matched_rule": "no_pr169_pretrade1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR169_SVC1_BRANCH:
        svc1_decision = _pr169_svc1_scope_decision(branch_name, normalized)
        if svc1_decision:
            return svc1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-SVC1",
            "matched_rule": "no_pr169_svc1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR169_AGENT_ORCH1_BRANCH:
        agent_orch1_decision = _pr169_agent_orch1_scope_decision(branch_name, normalized)
        if agent_orch1_decision:
            return agent_orch1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-AGENT-ORCH1",
            "matched_rule": "no_pr169_agent_orch1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name in {PR169_QKU_FORMULA_EXP1_BRANCH, PR169_QKU_FORMULA_EXP1_REPAIR_BRANCH}:
        qku_formula_decision = _pr169_qku_formula_exp1_scope_decision(branch_name, normalized)
        if qku_formula_decision:
            return qku_formula_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-QKU-FORMULA-EXP1",
            "matched_rule": "no_pr169_qku_formula_exp1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR169_VAL1_BRANCH:
        val1_decision = _pr169_val1_scope_decision(branch_name, normalized)
        if val1_decision:
            return val1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-VAL1",
            "matched_rule": "no_pr169_val1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name in {
        PR169_DASH1_BRANCH,
        PR169_DASH1_UI1_BRANCH,
        PR169_DASH1_UI1_R1_BRANCH,
        PR169_DASH1_UI1_R2_BRANCH,
        PR169_DASH1_UI1_R2_R1_BRANCH,
        PR169_DASH1_UI1_R2_R2_BRANCH,
        PR169_DASH1_UI1_R2_R3_BRANCH,
        PR169_DASH1_UI1_R2_R4_BRANCH,
        PR169_DASH1_UI1_R2_R5_BRANCH,
        PR169_DASH1_UI1_R2_R6_BRANCH,
    }:
        dash1_decision = _pr169_dash1_scope_decision(branch_name, normalized)
        if dash1_decision:
            return dash1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-DASH1",
            "matched_rule": "no_pr169_dash1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == VALIDATION_FIXTURE_BRANCH:
        rp_decision = _pr168_rp_scope_decision(branch_name, normalized)
        if rp_decision:
            return rp_decision
        rank_decision = _pr168_rank_scope_decision(branch_name, normalized)
        if rank_decision:
            return rank_decision
        data1_decision = _pr168_data1_scope_decision(branch_name, normalized)
        if data1_decision:
            return data1_decision
        data1a_decision = _pr168_data1a_scope_decision(branch_name, normalized)
        if data1a_decision:
            return data1a_decision
        gfp2r_decision = _pr168_gfp2r_scope_decision(branch_name, normalized)
        if gfp2r_decision:
            return gfp2r_decision
        rp2_decision = _pr168_rp2_scope_decision(branch_name, normalized)
        if rp2_decision:
            return rp2_decision
        map3_decision = _pr168_map3_scope_decision(branch_name, normalized)
        if map3_decision:
            return map3_decision
        rp3_decision = _pr168_rp3_scope_decision(branch_name, normalized)
        if rp3_decision:
            return rp3_decision
        rank3_decision = _pr168_rank3_scope_decision(branch_name, normalized)
        if rank3_decision:
            return rank3_decision
        rank4_decision = _pr168_rank4_scope_decision(branch_name, normalized)
        if rank4_decision:
            return rank4_decision
        rp5a_decision = _pr168_rp5a_scope_decision(branch_name, normalized)
        if rp5a_decision:
            return rp5a_decision
        rp5b_decision = _pr168_rp5b_scope_decision(branch_name, normalized)
        if rp5b_decision:
            return rp5b_decision
        rp5c_decision = _pr168_rp5c_scope_decision(branch_name, normalized)
        if rp5c_decision:
            return rp5c_decision
        vs1_decision = _pr168_vs1_scope_decision(branch_name, normalized)
        if vs1_decision:
            return vs1_decision
        rp5d_decision = _pr168_rp5d_scope_decision(branch_name, normalized)
        if rp5d_decision:
            return rp5d_decision
        rp5e_decision = _pr168_rp5e_scope_decision(branch_name, normalized)
        if rp5e_decision:
            return rp5e_decision
        rp5d_r1_decision = _pr168_rp5d_r1_scope_decision(branch_name, normalized)
        if rp5d_r1_decision:
            return rp5d_r1_decision
        rp5f_decision = _pr168_rp5f_scope_decision(branch_name, normalized)
        if rp5f_decision:
            return rp5f_decision
        rp5g_decision = _pr168_rp5g_scope_decision(branch_name, normalized)
        if rp5g_decision:
            return rp5g_decision
        qopt1_decision = _pr168_qopt1_scope_decision(branch_name, normalized)
        if qopt1_decision:
            return qopt1_decision
        vs2_decision = _pr168_vs2_scope_decision(branch_name, normalized)
        if vs2_decision:
            return vs2_decision
        mem1_decision = _pr168_mem1_scope_decision(branch_name, normalized)
        if mem1_decision:
            return mem1_decision
        readiness1_decision = _pr169_readiness1_scope_decision(branch_name, normalized)
        if readiness1_decision:
            return readiness1_decision
        pretrade1_decision = _pr169_pretrade1_scope_decision(branch_name, normalized)
        if pretrade1_decision:
            return pretrade1_decision
        svc1_decision = _pr169_svc1_scope_decision(branch_name, normalized)
        if svc1_decision:
            return svc1_decision
        agent_orch1_decision = _pr169_agent_orch1_scope_decision(branch_name, normalized)
        if agent_orch1_decision:
            return agent_orch1_decision
        qku_formula_decision = _pr169_qku_formula_exp1_scope_decision(branch_name, normalized)
        if qku_formula_decision:
            return qku_formula_decision
        dash1_decision = _pr169_dash1_scope_decision(branch_name, normalized)
        if dash1_decision:
            return dash1_decision

    if normalized in _PR168_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-GFP",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-GFP",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return {
        "allowed": False,
        "branch": branch_name,
        "normalized_path": normalized,
        "pr_id": "PR168-GFP",
        "matched_rule": "no_pr168_scope_rule",
        "reason": "path_not_registered_for_pr_scope",
    }


def _forbidden_reason(normalized: str) -> str | None:
    lowered = normalized.lower()
    if lowered in _FORBIDDEN_TOKEN_EXACT_PROOF_REPORT_EXCEPTIONS:
        return None
    if lowered.startswith("docs/master_plan/generated/pr168_vs2/no_private_state.") or lowered in {
        "docs/master_plan/generated/pr168_vs2/no_private_state.jsonl",
        "docs/master_plan/generated/pr168_vs2/no_private_state.manifest.json",
    }:
        return None
    if normalized in _FORBIDDEN_EXACT_PATHS:
        return f"forbidden_exact:{normalized}"
    if lowered.endswith("/atomicrows.bundle.sha256") or lowered == "atomicrows.bundle.sha256":
        return "forbidden_atomicrows_bundle_sha"
    for prefix in _FORBIDDEN_PREFIXES:
        if lowered.startswith(prefix):
            return f"forbidden_prefix:{prefix}"
    for token in _FORBIDDEN_NAME_TOKENS:
        if token in lowered:
            if (
                token == "live_order"
                and lowered.startswith("tests/")
                and "/test_no_live_order" in lowered
            ):
                continue
            if (
                token in {"qtt_sha", "qtt-sha"}
                and lowered.startswith("tests/pr169_dash1/")
                and "/test_dash1_no_qtt_sha" in lowered
            ):
                continue
            return f"forbidden_token:{token}"
    return None
